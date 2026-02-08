"""Tests for phase-3 retrieval and long-form memory goals."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest
from core.retrieval_engine import (
    QueryBenchmark,
    RetrievalBudget,
    RetrievalIndex,
    RetrievalQuery,
    build_hierarchical_memory_model,
    evaluate_retrieval_quality,
)


def _token_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text))


def _updated_chunk_text(chunk_text: str) -> str:
    return chunk_text.replace("guardian", "warden").replace("city", "citadel")


def test_g31_chunking_metadata_and_unresolved_thread_tracking() -> None:
    raw_text = (
        "Chapter 1\n\n"
        "Who left the blood-marked key beneath the door?\n\n"
        "The archivist writes every clue into memory.\n\n"
        "Chapter 2\n\n"
        "The truth is finally revealed because the captain confesses."
    )

    model = build_hierarchical_memory_model(
        raw_text,
        story_id="loom-story",
        branch_id="main",
        version_id="v1",
        branch_lineage=("root",),
        source_id="fixture://chapter",
    )

    assert len(model.chapter_chunks) == 2
    assert len(model.scene_chunks) >= 3
    assert len(model.sentence_chunks) >= 3
    assert model.scene_chunks[0].metadata.story_id == "loom-story"
    assert model.scene_chunks[0].metadata.branch_id == "main"
    assert model.scene_chunks[0].metadata.version_id == "v1"
    assert model.scene_chunks[0].metadata.branch_lineage == ("root",)
    assert model.scene_chunks[0].metadata.created_at

    statuses = {thread.status for thread in model.unresolved_threads}
    assert "open" in statuses or "resolved" in statuses
    assert any(thread.prompt for thread in model.unresolved_threads)


def test_g32_branch_namespace_filtering_and_compaction() -> None:
    main_model = build_hierarchical_memory_model(
        "Chapter 1\n\nThe guardian protects the city from the eclipse cult.",
        story_id="loom-story",
        branch_id="main",
        version_id="v1",
    )
    alt_model = build_hierarchical_memory_model(
        "Chapter 1\n\nEclipse cult city city city city betrayal.",
        story_id="loom-story",
        branch_id="alt",
        version_id="v1",
    )

    index = RetrievalIndex()
    index.upsert_chunks(main_model.scene_chunks)
    index.upsert_chunks(alt_model.scene_chunks)

    response = index.query(
        RetrievalQuery(
            story_id="loom-story",
            branch_id="main",
            branch_lineage=("main",),
            query_text="guardian protects city",
            top_k=5,
        )
    )

    wrong_branch_incidence = index.wrong_branch_incidence(
        response,
        expected_branches={"main"},
    )
    assert wrong_branch_incidence == 0.0

    duplicate_chunk = main_model.scene_chunks[0]
    duplicate_variant = duplicate_chunk.__class__(
        chunk_id=f"{duplicate_chunk.chunk_id}-dup",
        text=duplicate_chunk.text,
        level=duplicate_chunk.level,
        token_count=duplicate_chunk.token_count,
        metadata=duplicate_chunk.metadata,
        content_hash=duplicate_chunk.content_hash,
    )
    index.upsert_chunks((duplicate_variant,))
    compaction_report = index.compact_namespace(
        story_id="loom-story",
        branch_id="main",
        version_id="v1",
    )
    assert compaction_report.duplicates_removed >= 1


def test_g33_hybrid_retrieval_and_quality_metrics_vs_baseline() -> None:
    main_model = build_hierarchical_memory_model(
        "Chapter 1\n\n"
        "The guardian safeguards the capital from eclipse cult attackers.\n\n"
        "The archivist tracks an unresolved heirloom mystery in memory.",
        story_id="loom-bench",
        branch_id="main",
        version_id="v1",
    )
    alt_model = build_hierarchical_memory_model(
        "Chapter 1\n\n"
        "Eclipse cult city city city attackers attackers attackers.\n\n"
        "Unresolved thread unresolved thread mystery mystery noise.",
        story_id="loom-bench",
        branch_id="alt",
        version_id="v1",
    )

    index = RetrievalIndex()
    index.upsert_chunks(main_model.scene_chunks)
    index.upsert_chunks(alt_model.scene_chunks)

    main_scene_ids = tuple(chunk.chunk_id for chunk in main_model.scene_chunks)

    query_1 = RetrievalQuery(
        story_id="loom-bench",
        branch_id="main",
        branch_lineage=("alt",),
        query_text="guardian capital eclipse cult",
        canon_terms=("guardian", "safeguards"),
        top_k=3,
    )
    query_2 = RetrievalQuery(
        story_id="loom-bench",
        branch_id="main",
        branch_lineage=("alt",),
        query_text="unresolved mystery heirloom thread",
        canon_terms=("heirloom",),
        top_k=3,
    )

    benchmarks = (
        QueryBenchmark(query=query_1, relevant_chunk_ids=(main_scene_ids[0],)),
        QueryBenchmark(query=query_2, relevant_chunk_ids=(main_scene_ids[1],)),
    )

    bm25_responses = (
        index.query(
            query_1.__class__(**{**query_1.__dict__, "retrieval_mode": "bm25"})
        ),
        index.query(
            query_2.__class__(**{**query_2.__dict__, "retrieval_mode": "bm25"})
        ),
    )
    hybrid_responses = (
        index.query(query_1),
        index.query(query_2),
    )

    bm25_quality = evaluate_retrieval_quality(bm25_responses, benchmarks, k=3)
    hybrid_quality = evaluate_retrieval_quality(hybrid_responses, benchmarks, k=3)

    assert hybrid_quality.precision_at_k >= bm25_quality.precision_at_k
    assert hybrid_quality.mrr >= bm25_quality.mrr
    assert hybrid_quality.ndcg_at_k >= bm25_quality.ndcg_at_k


def test_g34_incremental_updates_stale_suppression_and_invalidation() -> None:
    model = build_hierarchical_memory_model(
        "Chapter 1\n\nThe guardian protects the city from ash.",
        story_id="loom-refresh",
        branch_id="main",
        version_id="v1",
    )
    index = RetrievalIndex()
    index.upsert_chunks(model.scene_chunks)

    original_chunk = next(
        chunk for chunk in model.scene_chunks if "guardian" in chunk.text.lower()
    )
    original_ops = index.embedding_operations

    updated_text = _updated_chunk_text(original_chunk.text)
    updated_chunk = original_chunk.__class__(
        chunk_id=original_chunk.chunk_id,
        text=updated_text,
        level=original_chunk.level,
        token_count=_token_count(updated_text),
        metadata=original_chunk.metadata,
        content_hash=hashlib.sha256(updated_text.encode("utf-8")).hexdigest(),
    )
    index.upsert_chunks((updated_chunk,))

    assert index.embedding_operations == original_ops + 1
    assert (
        index.stale_chunk_count(
            story_id="loom-refresh", branch_id="main", version_id="v1"
        )
        == 1
    )

    response = index.query(
        RetrievalQuery(
            story_id="loom-refresh",
            branch_id="main",
            version_id="v1",
            query_text="warden citadel ash",
            top_k=1,
        )
    )
    assert response.results
    assert "warden" in response.results[0].text
    assert "guardian" not in response.results[0].text

    invalidated_count = index.invalidate_branch_version(
        story_id="loom-refresh",
        branch_id="main",
        version_id="v1",
    )
    assert invalidated_count >= 1

    response_after_invalidation = index.query(
        RetrievalQuery(
            story_id="loom-refresh",
            branch_id="main",
            version_id="v1",
            query_text="warden",
            top_k=3,
        )
    )
    assert not response_after_invalidation.results


def test_g35_query_cache_budget_controls_and_runtime_stats() -> None:
    model = build_hierarchical_memory_model(
        "Chapter 1\n\nThe archivist stores every thread and branch memory forever.",
        story_id="loom-cost",
        branch_id="main",
        version_id="v1",
    )
    index = RetrievalIndex()
    index.upsert_chunks(model.scene_chunks)

    query = RetrievalQuery(
        story_id="loom-cost",
        branch_id="main",
        version_id="v1",
        query_text="archivist branch memory",
        top_k=1,
    )

    first_response = index.query(query)
    second_response = index.query(query)
    assert first_response.cache_hit is False
    assert second_response.cache_hit is True

    with pytest.raises(ValueError, match="token budget exceeded"):
        index.query(
            RetrievalQuery(
                story_id="loom-cost",
                branch_id="main",
                version_id="v1",
                query_text="word " * 120,
                budget=RetrievalBudget(max_query_tokens=8),
            )
        )

    with pytest.raises(ValueError, match="cost budget exceeded"):
        index.query(
            RetrievalQuery(
                story_id="loom-cost",
                branch_id="main",
                version_id="v1",
                query_text="archivist memory",
                budget=RetrievalBudget(max_cost_per_query=0.00001),
            )
        )

    stats = index.runtime_stats()
    assert stats.query_count >= 2
    assert stats.p95_latency_ms >= 0.0
    assert stats.p95_cost > 0.0
    assert stats.cache_hit_rate > 0.0


def test_phase3_done_criteria_thresholds_hold() -> None:
    thresholds = json.loads(
        Path("tests/fixtures/golden/retrieval_benchmark_thresholds.json").read_text(
            encoding="utf-8"
        )
    )

    main_text = (
        "Chapter 1\n\n"
        "The guardian safeguards the capital from eclipse cult attackers.\n\n"
        "The archivist tracks an unresolved heirloom mystery in memory."
    )
    alt_text = (
        "Chapter 1\n\n"
        "Eclipse cult city city city attackers attackers attackers.\n\n"
        "Unresolved thread unresolved thread mystery mystery noise."
    )

    main_model = build_hierarchical_memory_model(
        main_text,
        story_id="loom-threshold",
        branch_id="main",
        version_id="v1",
    )
    alt_model = build_hierarchical_memory_model(
        alt_text,
        story_id="loom-threshold",
        branch_id="alt",
        version_id="v1",
    )

    index = RetrievalIndex()
    index.upsert_chunks(main_model.scene_chunks)
    index.upsert_chunks(alt_model.scene_chunks)

    query = RetrievalQuery(
        story_id="loom-threshold",
        branch_id="main",
        branch_lineage=(),
        query_text="guardian capital eclipse cult",
        canon_terms=("guardian",),
        top_k=3,
    )
    response = index.query(query)
    wrong_branch_incidence = index.wrong_branch_incidence(
        response,
        expected_branches={"main"},
    )

    benchmark = (
        QueryBenchmark(
            query=query,
            relevant_chunk_ids=(main_model.scene_chunks[0].chunk_id,),
            graded_relevance={main_model.scene_chunks[0].chunk_id: 1.0},
        ),
    )
    quality = evaluate_retrieval_quality((response,), benchmark, k=3)
    runtime = index.runtime_stats()

    assert quality.precision_at_k >= thresholds["precision_at_3"]
    assert quality.mrr >= thresholds["mrr"]
    assert quality.ndcg_at_k >= thresholds["ndcg_at_3"]
    assert wrong_branch_incidence <= thresholds["max_wrong_branch_incidence"]
    assert runtime.p95_cost <= thresholds["max_p95_cost"]
