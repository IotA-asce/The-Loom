"""Retrieval and long-form memory engine for The Loom."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from statistics import mean
from time import perf_counter
from typing import Any

_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
_WORD_PATTERN = re.compile(r"[A-Za-z0-9']+")
_CHAPTER_SPLIT_PATTERN = re.compile(r"(?im)(?=^chapter\s+\d+)")

_UNRESOLVED_TOKENS = {
    "who",
    "why",
    "where",
    "how",
    "unknown",
    "mystery",
    "secret",
    "missing",
    "question",
    "unresolved",
}

_RESOLUTION_TOKENS = {
    "revealed",
    "resolved",
    "answer",
    "truth",
    "finally",
    "because",
    "solved",
    "confirmed",
}


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _clamp(value: float, *, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def _normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = "\n".join(line.rstrip() for line in normalized.split("\n"))
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _WORD_PATTERN.findall(text)]


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _vector_from_tokens(tokens: list[str]) -> dict[str, float]:
    if not tokens:
        return {}

    frequency: dict[str, int] = {}
    for token in tokens:
        frequency[token] = frequency.get(token, 0) + 1

    denominator = math.sqrt(sum(count * count for count in frequency.values()))
    if denominator == 0:
        return {}

    return {token: count / denominator for token, count in frequency.items()}


def _cosine_similarity(a_vector: dict[str, float], b_vector: dict[str, float]) -> float:
    if not a_vector or not b_vector:
        return 0.0

    if len(a_vector) > len(b_vector):
        a_vector, b_vector = b_vector, a_vector

    dot_product = 0.0
    for token, value in a_vector.items():
        dot_product += value * b_vector.get(token, 0.0)

    return _clamp(dot_product)


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0

    sorted_values = sorted(values)
    index = int(math.ceil((percentile / 100.0) * len(sorted_values))) - 1
    index = max(0, min(index, len(sorted_values) - 1))
    return sorted_values[index]


def namespace_id(story_id: str, branch_id: str, version_id: str) -> str:
    """Construct canonical namespace key for retrieval partitioning."""

    return f"story:{story_id}::branch:{branch_id}::version:{version_id}"


@dataclass(frozen=True)
class ChunkMetadata:
    """Canonical metadata attached to each chunk in memory index."""

    story_id: str
    branch_id: str
    version_id: str
    created_at: str
    chapter_index: int
    scene_index: int
    sentence_index: int | None
    level: str
    branch_lineage: tuple[str, ...] = ()
    source_id: str = ""


@dataclass(frozen=True)
class NarrativeChunk:
    """Memory chunk unit for sentence/scene/chapter hierarchy."""

    chunk_id: str
    text: str
    level: str
    token_count: int
    metadata: ChunkMetadata
    content_hash: str


@dataclass(frozen=True)
class UnresolvedThread:
    """Tracked unresolved question thread in memory timeline."""

    thread_id: str
    prompt: str
    opened_scene_index: int
    resolved_scene_index: int | None
    status: str


@dataclass(frozen=True)
class HierarchicalMemoryModel:
    """Hierarchical memory output with unresolved thread tracking."""

    story_id: str
    branch_id: str
    version_id: str
    chapter_chunks: tuple[NarrativeChunk, ...]
    scene_chunks: tuple[NarrativeChunk, ...]
    sentence_chunks: tuple[NarrativeChunk, ...]
    unresolved_threads: tuple[UnresolvedThread, ...]

    def all_chunks(self) -> tuple[NarrativeChunk, ...]:
        return (*self.chapter_chunks, *self.scene_chunks, *self.sentence_chunks)


@dataclass(frozen=True)
class RetrievalBudget:
    """Budget controls applied per retrieval query."""

    max_query_tokens: int = 96
    max_candidate_chunks: int = 1_500
    max_cost_per_query: float = 0.08


@dataclass(frozen=True)
class RetrievalQuery:
    """Query request for namespace-aware retrieval."""

    story_id: str
    branch_id: str
    query_text: str
    version_id: str | None = None
    branch_lineage: tuple[str, ...] = ()
    canon_terms: tuple[str, ...] = ()
    top_k: int = 5
    retrieval_mode: str = "hybrid"
    apply_rerank: bool = True
    use_cache: bool = True
    budget: RetrievalBudget = RetrievalBudget()


@dataclass(frozen=True)
class RetrievalHit:
    """Retrieved chunk with score breakdown and canonical metadata."""

    chunk_id: str
    text: str
    score: float
    bm25_score: float
    embedding_score: float
    rerank_score: float
    metadata: ChunkMetadata


@dataclass(frozen=True)
class RetrievalResponse:
    """Retrieval response payload with runtime/cost signals."""

    query: RetrievalQuery
    namespace_ids: tuple[str, ...]
    results: tuple[RetrievalHit, ...]
    candidate_count: int
    latency_ms: float
    estimated_cost: float
    cache_hit: bool


@dataclass(frozen=True)
class NamespaceCompactionReport:
    """Result stats after namespace compaction/dedup maintenance."""

    namespace_id: str
    stale_purged: int
    duplicates_removed: int
    active_count: int


@dataclass(frozen=True)
class RetrievalRuntimeStats:
    """Runtime and cost summary for retrieval operations."""

    query_count: int
    p95_latency_ms: float
    p95_cost: float
    cache_hit_rate: float


@dataclass(frozen=True)
class RetrievalQualityMetrics:
    """Retrieval quality metric bundle for benchmark comparisons."""

    precision_at_k: float
    mrr: float
    ndcg_at_k: float


@dataclass(frozen=True)
class QueryBenchmark:
    """Benchmark query with expected relevant chunk identifiers."""

    query: RetrievalQuery
    relevant_chunk_ids: tuple[str, ...]
    graded_relevance: dict[str, float] = field(default_factory=dict)


@dataclass
class _ChunkRecord:
    chunk: NarrativeChunk
    embedding: dict[str, float]
    token_frequency: dict[str, int]
    revision: int


@dataclass
class _NamespaceIndex:
    namespace_id: str
    story_id: str
    branch_id: str
    version_id: str
    active_records: dict[str, _ChunkRecord] = field(default_factory=dict)
    stale_records: dict[str, list[_ChunkRecord]] = field(default_factory=dict)
    inverted_index: dict[str, set[str]] = field(default_factory=dict)
    document_frequency: dict[str, int] = field(default_factory=dict)
    average_doc_length: float = 0.0

    def active_count(self) -> int:
        return len(self.active_records)


def _split_chapters(raw_text: str) -> list[tuple[str, str]]:
    normalized = _normalize_text(raw_text)
    if not normalized:
        return []

    chapter_blocks = [
        block.strip()
        for block in _CHAPTER_SPLIT_PATTERN.split(normalized)
        if block.strip()
    ]
    if len(chapter_blocks) == 1:
        return [("Chapter 1", chapter_blocks[0])]

    chapters: list[tuple[str, str]] = []
    for chapter_index, block in enumerate(chapter_blocks, start=1):
        chapter_match = re.match(r"(?is)^(chapter\s+\d+[^\n]*)(?:\n(.*))?$", block)
        if chapter_match is not None:
            title = chapter_match.group(1).strip()
            body = (chapter_match.group(2) or "").strip()
        else:
            title = f"Chapter {chapter_index}"
            body = block
        chapters.append((title, body))
    return chapters


def _split_scenes(chapter_body: str) -> list[str]:
    return [scene.strip() for scene in chapter_body.split("\n\n") if scene.strip()]


def _split_sentences(scene_text: str) -> list[str]:
    sentence_candidates = _SENTENCE_SPLIT_PATTERN.split(scene_text.strip())
    return [sentence.strip() for sentence in sentence_candidates if sentence.strip()]


def _build_chunk(
    *,
    level: str,
    text: str,
    metadata: ChunkMetadata,
) -> NarrativeChunk:
    seed = (
        f"{metadata.story_id}|{metadata.branch_id}|{metadata.version_id}|"
        f"{level}|{metadata.chapter_index}|{metadata.scene_index}|{metadata.sentence_index}|{text}"
    )
    chunk_id = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]
    tokens = _tokenize(text)
    return NarrativeChunk(
        chunk_id=chunk_id,
        text=text,
        level=level,
        token_count=len(tokens),
        metadata=metadata,
        content_hash=_content_hash(text),
    )


def _track_unresolved_threads(
    scenes: list[str],
) -> tuple[UnresolvedThread, ...]:
    open_thread_indices: list[int] = []
    threads: list[UnresolvedThread] = []

    for scene_index, scene_text in enumerate(scenes):
        scene_tokens = set(_tokenize(scene_text))
        has_unresolved_signal = ("?" in scene_text) or bool(
            scene_tokens & _UNRESOLVED_TOKENS
        )
        has_resolution_signal = bool(scene_tokens & _RESOLUTION_TOKENS)

        if has_unresolved_signal:
            thread_id = hashlib.sha1(
                f"thread|{scene_index}|{scene_text}".encode()
            ).hexdigest()[:14]
            threads.append(
                UnresolvedThread(
                    thread_id=thread_id,
                    prompt=scene_text,
                    opened_scene_index=scene_index,
                    resolved_scene_index=None,
                    status="open",
                )
            )
            open_thread_indices.append(len(threads) - 1)

        if has_resolution_signal and open_thread_indices:
            target_index = open_thread_indices.pop(0)
            target_thread = threads[target_index]
            threads[target_index] = replace(
                target_thread,
                resolved_scene_index=scene_index,
                status="resolved",
            )

    return tuple(threads)


def build_hierarchical_memory_model(
    raw_text: str,
    *,
    story_id: str,
    branch_id: str,
    version_id: str,
    branch_lineage: tuple[str, ...] = (),
    source_id: str = "",
    created_at: str | None = None,
) -> HierarchicalMemoryModel:
    """Create chapter/scene/sentence memory chunks with canonical metadata."""

    created_at_value = created_at or _timestamp()
    chapter_chunks: list[NarrativeChunk] = []
    scene_chunks: list[NarrativeChunk] = []
    sentence_chunks: list[NarrativeChunk] = []
    all_scenes: list[str] = []

    chapters = _split_chapters(raw_text)
    for chapter_index, (chapter_title, chapter_body) in enumerate(chapters):
        chapter_text = (
            chapter_title if not chapter_body else f"{chapter_title}\n\n{chapter_body}"
        )
        chapter_metadata = ChunkMetadata(
            story_id=story_id,
            branch_id=branch_id,
            version_id=version_id,
            created_at=created_at_value,
            chapter_index=chapter_index,
            scene_index=-1,
            sentence_index=None,
            level="chapter",
            branch_lineage=branch_lineage,
            source_id=source_id,
        )
        chapter_chunks.append(
            _build_chunk(level="chapter", text=chapter_text, metadata=chapter_metadata)
        )

        scenes = _split_scenes(chapter_body)
        for scene_index, scene_text in enumerate(scenes):
            all_scenes.append(scene_text)
            scene_metadata = ChunkMetadata(
                story_id=story_id,
                branch_id=branch_id,
                version_id=version_id,
                created_at=created_at_value,
                chapter_index=chapter_index,
                scene_index=scene_index,
                sentence_index=None,
                level="scene",
                branch_lineage=branch_lineage,
                source_id=source_id,
            )
            scene_chunks.append(
                _build_chunk(level="scene", text=scene_text, metadata=scene_metadata)
            )

            sentences = _split_sentences(scene_text)
            for sentence_index, sentence in enumerate(sentences):
                sentence_metadata = ChunkMetadata(
                    story_id=story_id,
                    branch_id=branch_id,
                    version_id=version_id,
                    created_at=created_at_value,
                    chapter_index=chapter_index,
                    scene_index=scene_index,
                    sentence_index=sentence_index,
                    level="sentence",
                    branch_lineage=branch_lineage,
                    source_id=source_id,
                )
                sentence_chunks.append(
                    _build_chunk(
                        level="sentence",
                        text=sentence,
                        metadata=sentence_metadata,
                    )
                )

    unresolved_threads = _track_unresolved_threads(all_scenes)
    return HierarchicalMemoryModel(
        story_id=story_id,
        branch_id=branch_id,
        version_id=version_id,
        chapter_chunks=tuple(chapter_chunks),
        scene_chunks=tuple(scene_chunks),
        sentence_chunks=tuple(sentence_chunks),
        unresolved_threads=unresolved_threads,
    )


def _bm25_score(
    query_tokens: list[str],
    record: _ChunkRecord,
    namespace_index: _NamespaceIndex,
    *,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    if not query_tokens:
        return 0.0

    total_documents = max(1, namespace_index.active_count())
    avg_doc_length = max(1.0, namespace_index.average_doc_length)
    document_length = max(1, record.chunk.token_count)

    score = 0.0
    unique_query_tokens = set(query_tokens)
    for token in unique_query_tokens:
        term_frequency = record.token_frequency.get(token, 0)
        if term_frequency == 0:
            continue

        document_frequency = namespace_index.document_frequency.get(token, 0)
        idf = math.log(
            1.0
            + (
                (total_documents - document_frequency + 0.5)
                / (document_frequency + 0.5)
            )
        )
        denominator = term_frequency + k1 * (
            1.0 - b + b * (document_length / avg_doc_length)
        )
        score += idf * ((term_frequency * (k1 + 1.0)) / max(denominator, 1e-9))

    return score


def _normalized_bm25(score: float) -> float:
    return _clamp(score / (score + 3.0))


def precision_at_k(
    results: tuple[RetrievalHit, ...], relevant_ids: set[str], k: int
) -> float:
    """Compute precision@k from ranked retrieval hits."""

    if k <= 0:
        return 0.0

    top_hits = results[:k]
    if not top_hits:
        return 0.0

    hit_count = sum(1 for hit in top_hits if hit.chunk_id in relevant_ids)
    return hit_count / len(top_hits)


def mean_reciprocal_rank(
    results: tuple[RetrievalHit, ...], relevant_ids: set[str]
) -> float:
    """Compute reciprocal rank for one query result list."""

    for rank, hit in enumerate(results, start=1):
        if hit.chunk_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(
    results: tuple[RetrievalHit, ...], relevance: dict[str, float], k: int
) -> float:
    """Compute nDCG@k using graded relevance labels."""

    if k <= 0:
        return 0.0

    top_hits = results[:k]
    dcg = 0.0
    for rank, hit in enumerate(top_hits, start=1):
        gain = relevance.get(hit.chunk_id, 0.0)
        denominator = math.log2(rank + 1)
        dcg += gain / denominator

    ideal_gains = sorted(relevance.values(), reverse=True)[:k]
    idcg = 0.0
    for rank, gain in enumerate(ideal_gains, start=1):
        denominator = math.log2(rank + 1)
        idcg += gain / denominator

    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def evaluate_retrieval_quality(
    responses: tuple[RetrievalResponse, ...],
    benchmarks: tuple[QueryBenchmark, ...],
    *,
    k: int,
) -> RetrievalQualityMetrics:
    """Evaluate retrieval quality metrics for multiple benchmark queries."""

    benchmark_by_query = {
        benchmark.query.query_text: benchmark for benchmark in benchmarks
    }

    precision_scores: list[float] = []
    reciprocal_ranks: list[float] = []
    ndcg_scores: list[float] = []

    for response in responses:
        benchmark = benchmark_by_query.get(response.query.query_text)
        if benchmark is None:
            continue

        relevant_ids = set(benchmark.relevant_chunk_ids)
        graded_relevance = (
            benchmark.graded_relevance
            if benchmark.graded_relevance
            else {chunk_id: 1.0 for chunk_id in benchmark.relevant_chunk_ids}
        )

        precision_scores.append(precision_at_k(response.results, relevant_ids, k))
        reciprocal_ranks.append(mean_reciprocal_rank(response.results, relevant_ids))
        ndcg_scores.append(ndcg_at_k(response.results, graded_relevance, k))

    return RetrievalQualityMetrics(
        precision_at_k=mean(precision_scores) if precision_scores else 0.0,
        mrr=mean(reciprocal_ranks) if reciprocal_ranks else 0.0,
        ndcg_at_k=mean(ndcg_scores) if ndcg_scores else 0.0,
    )


class RetrievalIndex:
    """Branch-aware retrieval index with hybrid ranking and incremental updates."""

    def __init__(self) -> None:
        self._namespaces: dict[str, _NamespaceIndex] = {}
        self._query_cache: dict[str, RetrievalResponse] = {}
        self._latency_history_ms: list[float] = []
        self._cost_history: list[float] = []
        self._cache_hits = 0
        self._cache_misses = 0
        self._mutation_counter = 0
        self._embedding_operations = 0

    def _namespace_for(
        self,
        story_id: str,
        branch_id: str,
        version_id: str,
    ) -> _NamespaceIndex:
        key = namespace_id(story_id, branch_id, version_id)
        namespace = self._namespaces.get(key)
        if namespace is None:
            namespace = _NamespaceIndex(
                namespace_id=key,
                story_id=story_id,
                branch_id=branch_id,
                version_id=version_id,
            )
            self._namespaces[key] = namespace
        return namespace

    def _rebuild_namespace_stats(self, namespace: _NamespaceIndex) -> None:
        namespace.inverted_index.clear()
        namespace.document_frequency.clear()

        total_tokens = 0
        for chunk_id, record in namespace.active_records.items():
            total_tokens += record.chunk.token_count
            unique_terms = set(record.token_frequency)
            for token in unique_terms:
                namespace.document_frequency[token] = (
                    namespace.document_frequency.get(token, 0) + 1
                )
            for token in unique_terms:
                namespace.inverted_index.setdefault(token, set()).add(chunk_id)

        if namespace.active_records:
            namespace.average_doc_length = total_tokens / len(namespace.active_records)
        else:
            namespace.average_doc_length = 0.0

    def _invalidate_story_cache(self, story_id: str) -> None:
        if not self._query_cache:
            return

        keys_to_remove: list[str] = []
        for cache_key, response in self._query_cache.items():
            if response.query.story_id == story_id:
                keys_to_remove.append(cache_key)

        for cache_key in keys_to_remove:
            self._query_cache.pop(cache_key, None)

    def upsert_chunks(self, chunks: tuple[NarrativeChunk, ...]) -> int:
        """Upsert chunks with incremental re-embedding and stale tracking."""

        if not chunks:
            return 0

        first_chunk = chunks[0]
        namespace = self._namespace_for(
            first_chunk.metadata.story_id,
            first_chunk.metadata.branch_id,
            first_chunk.metadata.version_id,
        )

        updated_chunks = 0
        for chunk in chunks:
            if (
                chunk.metadata.story_id != namespace.story_id
                or chunk.metadata.branch_id != namespace.branch_id
                or chunk.metadata.version_id != namespace.version_id
            ):
                msg = "All chunks in one upsert call must belong to the same namespace."
                raise ValueError(msg)

            existing_record = namespace.active_records.get(chunk.chunk_id)
            if (
                existing_record is not None
                and existing_record.chunk.content_hash == chunk.content_hash
            ):
                continue

            token_frequency: dict[str, int] = {}
            tokens = _tokenize(chunk.text)
            for token in tokens:
                token_frequency[token] = token_frequency.get(token, 0) + 1

            embedding = _vector_from_tokens(tokens)
            self._embedding_operations += 1

            revision = 1
            if existing_record is not None:
                revision = existing_record.revision + 1
                namespace.stale_records.setdefault(chunk.chunk_id, []).append(
                    existing_record
                )

            namespace.active_records[chunk.chunk_id] = _ChunkRecord(
                chunk=chunk,
                embedding=embedding,
                token_frequency=token_frequency,
                revision=revision,
            )
            updated_chunks += 1

        self._rebuild_namespace_stats(namespace)
        self._mutation_counter += 1
        self._invalidate_story_cache(namespace.story_id)
        return updated_chunks

    def mark_chunks_stale(
        self,
        *,
        story_id: str,
        branch_id: str,
        version_id: str,
        chunk_ids: tuple[str, ...],
    ) -> int:
        """Mark selected chunk ids stale and suppress them from retrieval."""

        namespace = self._namespace_for(story_id, branch_id, version_id)
        stale_count = 0

        for chunk_id in chunk_ids:
            record = namespace.active_records.pop(chunk_id, None)
            if record is None:
                continue
            namespace.stale_records.setdefault(chunk_id, []).append(record)
            stale_count += 1

        if stale_count:
            self._rebuild_namespace_stats(namespace)
            self._mutation_counter += 1
            self._invalidate_story_cache(story_id)

        return stale_count

    def invalidate_branch_version(
        self,
        *,
        story_id: str,
        branch_id: str,
        version_id: str,
    ) -> int:
        """Invalidate all active chunks for one namespace version."""

        namespace_key = namespace_id(story_id, branch_id, version_id)
        namespace = self._namespaces.get(namespace_key)
        if namespace is None:
            return 0

        chunk_ids = tuple(namespace.active_records.keys())
        return self.mark_chunks_stale(
            story_id=story_id,
            branch_id=branch_id,
            version_id=version_id,
            chunk_ids=chunk_ids,
        )

    def compact_namespace(
        self,
        *,
        story_id: str,
        branch_id: str,
        version_id: str,
    ) -> NamespaceCompactionReport:
        """Purge stale records and remove active duplicates by text hash."""

        namespace_key = namespace_id(story_id, branch_id, version_id)
        namespace = self._namespaces.get(namespace_key)
        if namespace is None:
            return NamespaceCompactionReport(
                namespace_id=namespace_key,
                stale_purged=0,
                duplicates_removed=0,
                active_count=0,
            )

        stale_purged = sum(len(records) for records in namespace.stale_records.values())
        namespace.stale_records.clear()

        seen_hashes: dict[str, str] = {}
        duplicates_removed = 0
        chunk_ids_to_remove: list[str] = []
        for chunk_id, record in namespace.active_records.items():
            text_hash = record.chunk.content_hash
            if text_hash in seen_hashes:
                chunk_ids_to_remove.append(chunk_id)
                duplicates_removed += 1
            else:
                seen_hashes[text_hash] = chunk_id

        for chunk_id in chunk_ids_to_remove:
            namespace.active_records.pop(chunk_id, None)

        self._rebuild_namespace_stats(namespace)
        self._mutation_counter += 1
        self._invalidate_story_cache(story_id)

        return NamespaceCompactionReport(
            namespace_id=namespace.namespace_id,
            stale_purged=stale_purged,
            duplicates_removed=duplicates_removed,
            active_count=namespace.active_count(),
        )

    def _allowed_namespaces(self, query: RetrievalQuery) -> tuple[_NamespaceIndex, ...]:
        allowed_branches = set(query.branch_lineage)
        allowed_branches.add(query.branch_id)

        namespaces: list[_NamespaceIndex] = []
        for namespace in self._namespaces.values():
            if namespace.story_id != query.story_id:
                continue
            if namespace.branch_id not in allowed_branches:
                continue
            if query.version_id is not None and namespace.branch_id == query.branch_id:
                if namespace.version_id != query.version_id:
                    continue
            namespaces.append(namespace)

        return tuple(namespaces)

    def _query_cache_key(self, query: RetrievalQuery) -> str:
        key_payload = {
            "mutation": self._mutation_counter,
            "story_id": query.story_id,
            "branch_id": query.branch_id,
            "version_id": query.version_id,
            "lineage": list(query.branch_lineage),
            "canon_terms": list(query.canon_terms),
            "query_text": query.query_text,
            "top_k": query.top_k,
            "mode": query.retrieval_mode,
            "rerank": query.apply_rerank,
            "budget": {
                "max_query_tokens": query.budget.max_query_tokens,
                "max_candidate_chunks": query.budget.max_candidate_chunks,
                "max_cost_per_query": query.budget.max_cost_per_query,
            },
        }
        return hashlib.sha256(
            json.dumps(key_payload, sort_keys=True).encode("utf-8")
        ).hexdigest()

    def _estimate_query_cost(
        self, query_tokens: list[str], candidate_count: int, top_k: int
    ) -> float:
        return (
            len(query_tokens) * 0.00002
            + candidate_count * 0.00008
            + max(top_k, 1) * 0.00004
        )

    def _rerank_bonus(
        self,
        query: RetrievalQuery,
        record: _ChunkRecord,
        query_tokens: list[str],
    ) -> float:
        if not query.apply_rerank:
            return 0.0

        bonus = 0.0
        if record.chunk.metadata.branch_id == query.branch_id:
            bonus += 0.09
        elif record.chunk.metadata.branch_id in query.branch_lineage:
            bonus += 0.04

        if query.canon_terms:
            token_set = set(_tokenize(record.chunk.text))
            canon_hits = sum(
                1 for term in query.canon_terms if term.lower() in token_set
            )
            bonus += (canon_hits / len(query.canon_terms)) * 0.2

        unresolved_hint = bool(set(query_tokens) & _UNRESOLVED_TOKENS)
        if unresolved_hint and "?" in record.chunk.text:
            bonus += 0.05

        return bonus

    def query(self, query: RetrievalQuery) -> RetrievalResponse:
        """Run branch-aware retrieval with hybrid scoring and budget controls."""

        start_time = perf_counter()

        cache_key = self._query_cache_key(query)
        if query.use_cache and cache_key in self._query_cache:
            self._cache_hits += 1
            cached_response = self._query_cache[cache_key]
            latency_ms = (perf_counter() - start_time) * 1000.0
            self._latency_history_ms.append(latency_ms)
            self._cost_history.append(cached_response.estimated_cost)
            return replace(cached_response, cache_hit=True, latency_ms=latency_ms)

        self._cache_misses += 1

        query_tokens = _tokenize(query.query_text)
        if len(query_tokens) > query.budget.max_query_tokens:
            msg = (
                "Query token budget exceeded "
                f"({len(query_tokens)} > {query.budget.max_query_tokens})."
            )
            raise ValueError(msg)

        namespaces = self._allowed_namespaces(query)
        namespace_ids = tuple(namespace.namespace_id for namespace in namespaces)

        candidate_rows: list[tuple[_ChunkRecord, _NamespaceIndex]] = []
        for namespace in namespaces:
            for record in namespace.active_records.values():
                candidate_rows.append((record, namespace))

        if len(candidate_rows) > query.budget.max_candidate_chunks:
            msg = (
                "Candidate chunk budget exceeded "
                f"({len(candidate_rows)} > {query.budget.max_candidate_chunks})."
            )
            raise ValueError(msg)

        estimated_cost = self._estimate_query_cost(
            query_tokens, len(candidate_rows), query.top_k
        )
        if estimated_cost > query.budget.max_cost_per_query:
            msg = (
                "Query cost budget exceeded "
                f"({estimated_cost:.5f} > {query.budget.max_cost_per_query:.5f})."
            )
            raise ValueError(msg)

        query_embedding = _vector_from_tokens(query_tokens)

        hits: list[RetrievalHit] = []
        for record, namespace in candidate_rows:
            bm25_raw = _bm25_score(query_tokens, record, namespace)
            bm25_score = _normalized_bm25(bm25_raw)
            embedding_score = _cosine_similarity(query_embedding, record.embedding)

            retrieval_mode = query.retrieval_mode.lower()
            if retrieval_mode == "bm25":
                base_score = bm25_score
            elif retrieval_mode == "embedding":
                base_score = embedding_score
            else:
                base_score = (bm25_score * 0.58) + (embedding_score * 0.42)

            rerank_score = self._rerank_bonus(query, record, query_tokens)
            score = base_score + rerank_score

            hits.append(
                RetrievalHit(
                    chunk_id=record.chunk.chunk_id,
                    text=record.chunk.text,
                    score=score,
                    bm25_score=bm25_score,
                    embedding_score=embedding_score,
                    rerank_score=rerank_score,
                    metadata=record.chunk.metadata,
                )
            )

        hits.sort(key=lambda hit: hit.score, reverse=True)
        top_hits = tuple(hits[: query.top_k])

        latency_ms = (perf_counter() - start_time) * 1000.0
        self._latency_history_ms.append(latency_ms)
        self._cost_history.append(estimated_cost)

        response = RetrievalResponse(
            query=query,
            namespace_ids=namespace_ids,
            results=top_hits,
            candidate_count=len(candidate_rows),
            latency_ms=latency_ms,
            estimated_cost=estimated_cost,
            cache_hit=False,
        )

        if query.use_cache:
            self._query_cache[cache_key] = response

        return response

    def runtime_stats(self) -> RetrievalRuntimeStats:
        """Return p95 latency/cost and cache hit rate for query operations."""

        total_queries = len(self._latency_history_ms)
        cache_total = self._cache_hits + self._cache_misses
        cache_hit_rate = self._cache_hits / cache_total if cache_total > 0 else 0.0

        return RetrievalRuntimeStats(
            query_count=total_queries,
            p95_latency_ms=_percentile(self._latency_history_ms, 95.0),
            p95_cost=_percentile(self._cost_history, 95.0),
            cache_hit_rate=cache_hit_rate,
        )

    @property
    def embedding_operations(self) -> int:
        return self._embedding_operations

    def stale_chunk_count(
        self,
        *,
        story_id: str,
        branch_id: str,
        version_id: str,
    ) -> int:
        """Return number of stale records currently retained in namespace."""

        namespace = self._namespaces.get(namespace_id(story_id, branch_id, version_id))
        if namespace is None:
            return 0
        return sum(len(records) for records in namespace.stale_records.values())

    def wrong_branch_incidence(
        self,
        response: RetrievalResponse,
        *,
        expected_branches: set[str],
    ) -> float:
        """Compute share of returned hits that violate branch filter expectations."""

        if not response.results:
            return 0.0

        mismatches = sum(
            1
            for hit in response.results
            if hit.metadata.branch_id not in expected_branches
        )
        return mismatches / len(response.results)


# ============ Vector Store Integration for Sprint 23 ============


@dataclass(frozen=True)
class VectorRetrievalResult:
    """Result from vector-based retrieval."""

    chunk_id: str
    text: str
    score: float
    metadata: ChunkMetadata


async def hybrid_search_with_vector_store(
    query: RetrievalQuery,
    vector_store: Any | None = None,  # noqa: ANN401
    index: RetrievalIndex | None = None,
    vector_weight: float = 0.7,
    bm25_weight: float = 0.3,
) -> RetrievalResponse:
    """Hybrid search combining vector store and BM25.

    This function integrates the vector store with the existing RetrievalIndex
    to provide semantic + keyword hybrid search capabilities.
    """
    from time import perf_counter

    from .vector_store import get_vector_store

    start_time = perf_counter()

    # Get vector store
    if vector_store is None:
        vector_store = get_vector_store()

    # Search vector store
    filters = None
    if query.branch_id:
        filters = {"branch_id": query.branch_id}

    vector_results = await vector_store.search(
        query=query.query_text,
        top_k=query.top_k * 2,  # Get more candidates for reranking
        filters=filters,
    )

    # If we have an index, also get BM25 results
    bm25_results: list[RetrievalHit] = []
    if index is not None:
        # Use existing index query but with BM25 only
        bm25_query = replace(query, retrieval_mode="bm25")
        bm25_response = index.query(bm25_query)
        bm25_results = list(bm25_response.results)

    # Merge results with weighted scoring
    all_chunk_ids: set[str] = set()
    vector_scores: dict[str, float] = {}
    bm25_scores: dict[str, float] = {}

    for result in vector_results:
        doc_id = result.document.id
        all_chunk_ids.add(doc_id)
        vector_scores[doc_id] = result.score

    for hit in bm25_results:
        all_chunk_ids.add(hit.chunk_id)
        bm25_scores[hit.chunk_id] = hit.bm25_score

    # Calculate combined scores
    combined_results: list[tuple[float, str, str, ChunkMetadata | None]] = []

    for chunk_id in all_chunk_ids:
        v_score = vector_scores.get(chunk_id, 0.0)
        b_score = bm25_scores.get(chunk_id, 0.0)
        combined_score = vector_weight * v_score + bm25_weight * b_score

        # Get text and metadata
        text = ""
        metadata = None

        # Try to find in vector results
        for r in vector_results:
            if r.document.id == chunk_id:
                text = r.document.text
                # Reconstruct metadata from document
                metadata = ChunkMetadata(
                    story_id=r.document.metadata.get("story_id", query.story_id),
                    branch_id=r.document.metadata.get("branch_id", query.branch_id),
                    version_id=r.document.metadata.get("version_id", "unknown"),
                    created_at=r.document.metadata.get("created_at", _timestamp()),
                    chapter_index=r.document.metadata.get("chapter_index", 0),
                    scene_index=r.document.metadata.get("scene_index", 0),
                    sentence_index=r.document.metadata.get("sentence_index"),
                    level=r.document.metadata.get("level", "sentence"),
                )
                break

        # Try to find in BM25 results
        if metadata is None:
            for hit in bm25_results:
                if hit.chunk_id == chunk_id:
                    text = hit.text
                    metadata = hit.metadata
                    break

        combined_results.append((combined_score, chunk_id, text, metadata))

    # Sort by combined score
    combined_results.sort(reverse=True)

    # Build final hits
    final_hits = []
    for score, chunk_id, text, metadata in combined_results[: query.top_k]:
        if metadata is None:
            continue

        final_hits.append(
            RetrievalHit(
                chunk_id=chunk_id,
                text=text,
                score=score,
                bm25_score=bm25_scores.get(chunk_id, 0.0),
                embedding_score=vector_scores.get(chunk_id, 0.0),
                rerank_score=None,
                metadata=metadata,
            )
        )

    latency_ms = (perf_counter() - start_time) * 1000

    return RetrievalResponse(
        results=tuple(final_hits),
        query_time_ms=latency_ms,
        cache_hit=False,
        tokens_used=0,  # Would track actual tokens
        cost_usd=0.0,
    )


async def index_chunks_to_vector_store(
    chunks: list[NarrativeChunk],
    vector_store: Any | None = None,  # noqa: ANN401
) -> list[str]:
    """Index narrative chunks to vector store for semantic search.

    This function converts NarrativeChunks to VectorDocuments and adds them
    to the vector store.
    """
    from .vector_store import VectorDocument, get_vector_store

    if vector_store is None:
        vector_store = get_vector_store()

    # Convert to VectorDocuments
    documents = []
    for chunk in chunks:
        doc = VectorDocument(
            id=chunk.chunk_id,
            text=chunk.text,
            metadata={
                "story_id": chunk.metadata.story_id,
                "branch_id": chunk.metadata.branch_id,
                "version_id": chunk.metadata.version_id,
                "chapter_index": chunk.metadata.chapter_index,
                "scene_index": chunk.metadata.scene_index,
                "sentence_index": chunk.metadata.sentence_index,
                "level": chunk.metadata.level,
                "source_id": chunk.metadata.source_id,
            },
        )
        documents.append(doc)

    # Add to vector store
    return await vector_store.add_documents(documents)
