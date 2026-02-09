"""Story graph and branching core engine for The Loom."""

from __future__ import annotations

import hashlib
import json
import re
from collections import deque
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any, cast

_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
_WORD_PATTERN = re.compile(r"[A-Za-z0-9']+")
_CAPITALIZED_PATTERN = re.compile(r"\b[A-Z][a-zA-Z0-9']+\b")

_ACTION_LEXICON = {
    "attack",
    "attacks",
    "betray",
    "betrays",
    "confess",
    "confesses",
    "discover",
    "discovers",
    "escape",
    "escapes",
    "fight",
    "fights",
    "find",
    "finds",
    "kill",
    "kills",
    "reveal",
    "reveals",
    "save",
    "saves",
}

_HIGH_IMPACT_ACTIONS = {
    "attack",
    "betray",
    "confess",
    "kill",
    "reveal",
}

_DEPENDENCY_RELATION_TYPES = {"depends_on", "before", "causes"}


def _now_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _clamp(value: float, *, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _WORD_PATTERN.findall(text)]


def _slugify(text: str) -> str:
    lowered = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    return slug or "entity"


def _normalized_event_text(text: str) -> str:
    lowered = text.lower().strip()
    return re.sub(r"[^a-z0-9\s]+", "", lowered)


@dataclass(frozen=True)
class EventRecord:
    """Normalized event extracted from narrative text."""

    event_id: str
    scene_index: int
    sentence_index: int
    source_order: int
    text: str
    normalized_text: str
    actors: tuple[str, ...]
    action: str
    objects: tuple[str, ...]
    confidence: float


@dataclass(frozen=True)
class EventExtractionResult:
    """Event extraction output with duplicate merge accounting."""

    events: tuple[EventRecord, ...]
    duplicate_merge_count: int
    schema_version: str = "event-v1"


@dataclass(frozen=True)
class RelationEdge:
    """Directed relation between two events."""

    source_event_id: str
    target_event_id: str
    relation_type: str
    confidence: float
    reason: str


@dataclass(frozen=True)
class RelationExtractionResult:
    """Extracted relation set and relation counts."""

    relations: tuple[RelationEdge, ...]
    causal_count: int
    dependency_count: int


@dataclass(frozen=True)
class EntityStateConflict:
    """Entity contradiction found during state consistency checks."""

    entity_id: str
    state_key: str
    expected_value: str
    observed_value: str
    first_event_id: str
    conflicting_event_id: str
    reason: str


@dataclass(frozen=True)
class TemporalOrderResult:
    """Temporal ordering result and contradiction diagnostics."""

    ordered_event_ids: tuple[str, ...]
    contradictions: tuple[str, ...]
    used_edges: tuple[RelationEdge, ...]
    removed_edges: tuple[RelationEdge, ...] = ()


@dataclass(frozen=True)
class BranchBudgetPolicy:
    """Branch lifecycle budget controls."""

    max_active_branches: int = 8
    max_archived_branches: int = 32


DEFAULT_BRANCH_BUDGET_POLICY = BranchBudgetPolicy()


@dataclass(frozen=True)
class BranchRecord:
    """Tracked branch node with lineage metadata."""

    branch_id: str
    parent_branch_id: str | None
    divergence_event_id: str | None
    label: str
    created_at: str
    status: str
    lineage: tuple[str, ...]
    merged_into: str | None = None
    archive_reason: str | None = None
    merge_reason: str | None = None


@dataclass(frozen=True)
class BranchRecommendation:
    """System recommendation for high-impact divergence points."""

    event_id: str
    impact_score: float
    reason: str


@dataclass(frozen=True)
class CanonConstraint:
    """Hard canon rule applied during consequence simulation."""

    entity_id: str
    state_key: str
    required_value: str


@dataclass(frozen=True)
class ConsequenceSimulationResult:
    """Incremental simulation output with consistency diagnostics."""

    affected_event_ids: tuple[str, ...]
    recomputed_scores: dict[str, float]
    baseline_scores: dict[str, float]
    constraint_violations: tuple[str, ...]
    consistency_score: float
    used_incremental: bool


@dataclass(frozen=True)
class GraphSnapshot:
    """Serializable graph snapshot for persistence and migration."""

    schema_version: int
    story_id: str
    events: tuple[EventRecord, ...]
    relations: tuple[RelationEdge, ...]
    branches: tuple[BranchRecord, ...]
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class MigrationCheckpoint:
    """Migration checkpoint used for rollback and replay."""

    from_version: int
    payload: dict[str, Any]


@dataclass(frozen=True)
class MigrationReplayResult:
    """Migration replay output with checkpoints and migrated payload."""

    migrated_payload: dict[str, Any]
    checkpoints: tuple[MigrationCheckpoint, ...]
    applied_versions: tuple[int, ...]


class GraphMigrationError(RuntimeError):
    """Raised when graph migration fails and rollback payload is needed."""

    def __init__(
        self,
        message: str,
        *,
        rollback_payload: dict[str, Any],
        checkpoints: tuple[MigrationCheckpoint, ...],
    ) -> None:
        super().__init__(message)
        self.rollback_payload = rollback_payload
        self.checkpoints = checkpoints


class EntityAliasGraph:
    """Canonical entity id registry with alias resolution."""

    def __init__(self) -> None:
        self._canonical_by_alias: dict[str, str] = {}
        self._aliases_by_canonical: dict[str, set[str]] = {}

    def register_entity(self, name: str, aliases: tuple[str, ...] = ()) -> str:
        canonical_id = f"ent_{_slugify(name)}"
        self._aliases_by_canonical.setdefault(canonical_id, set())
        all_aliases = {name, *aliases}
        for alias in all_aliases:
            alias_key = alias.lower().strip()
            if alias_key:
                self._canonical_by_alias[alias_key] = canonical_id
                self._aliases_by_canonical[canonical_id].add(alias)
        return canonical_id

    def add_alias(self, canonical_id: str, alias: str) -> None:
        if canonical_id not in self._aliases_by_canonical:
            self._aliases_by_canonical[canonical_id] = set()
        alias_key = alias.lower().strip()
        if alias_key:
            self._canonical_by_alias[alias_key] = canonical_id
            self._aliases_by_canonical[canonical_id].add(alias)

    def resolve(self, name: str) -> str:
        alias_key = name.lower().strip()
        canonical_id = self._canonical_by_alias.get(alias_key)
        if canonical_id is not None:
            return canonical_id
        return self.register_entity(name)

    def aliases_for(self, canonical_id: str) -> tuple[str, ...]:
        aliases = sorted(self._aliases_by_canonical.get(canonical_id, set()))
        return tuple(aliases)

    def canonical_entities(self) -> tuple[str, ...]:
        return tuple(sorted(self._aliases_by_canonical.keys()))


def _split_scenes(raw_text: str) -> list[str]:
    normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []
    return [scene.strip() for scene in normalized.split("\n\n") if scene.strip()]


def _split_sentences(scene_text: str) -> list[str]:
    candidates = _SENTENCE_SPLIT_PATTERN.split(scene_text.strip())
    return [sentence.strip() for sentence in candidates if sentence.strip()]


def _extract_actors(sentence_text: str) -> tuple[str, ...]:
    actor_candidates = _CAPITALIZED_PATTERN.findall(sentence_text)
    unique_actors = sorted({candidate for candidate in actor_candidates})
    return tuple(unique_actors)


def _extract_action(tokens: list[str]) -> str:
    for token in tokens:
        if token in _ACTION_LEXICON:
            return token
    for token in tokens:
        if token.endswith("ed") or token.endswith("ing"):
            return token
    if len(tokens) >= 2:
        return tokens[1]
    if tokens:
        return tokens[0]
    return "unknown"


def _extract_objects(
    tokens: list[str],
    actor_names: tuple[str, ...],
    action: str,
) -> tuple[str, ...]:
    actor_tokens = {name.lower() for name in actor_names}
    object_tokens = [
        token
        for token in tokens
        if token not in actor_tokens and token != action and len(token) > 3
    ]
    return tuple(sorted(set(object_tokens[:5])))


def _event_confidence(
    sentence_text: str,
    tokens: list[str],
    actors: tuple[str, ...],
    action: str,
    objects: tuple[str, ...],
) -> float:
    confidence = 0.2
    confidence += 0.2 if actors else 0.0
    confidence += 0.15 if action != "unknown" else 0.0
    confidence += 0.1 if objects else 0.0
    confidence += min(0.2, len(tokens) / 40.0)
    if any(
        marker in sentence_text.lower()
        for marker in ("because", "after", "before", "therefore")
    ):
        confidence += 0.1
    return _clamp(confidence)


def _event_key(event: EventRecord) -> str:
    payload = (
        event.normalized_text,
        event.actors,
        event.action,
        event.objects,
    )
    return json.dumps(payload, sort_keys=True)


def _merge_event(existing: EventRecord, incoming: EventRecord) -> EventRecord:
    merged_actors = tuple(sorted(set(existing.actors) | set(incoming.actors)))
    merged_objects = tuple(sorted(set(existing.objects) | set(incoming.objects)))
    preferred = incoming if incoming.confidence > existing.confidence else existing
    return replace(
        preferred,
        actors=merged_actors,
        objects=merged_objects,
        confidence=max(existing.confidence, incoming.confidence),
    )


def extract_events_hybrid(
    raw_text: str,
    *,
    alias_graph: EntityAliasGraph | None = None,
) -> EventExtractionResult:
    """Extract normalized events from text using lexical + structural heuristics."""

    entity_graph = alias_graph or EntityAliasGraph()
    events: list[EventRecord] = []

    source_order = 0
    scenes = _split_scenes(raw_text)
    for scene_index, scene_text in enumerate(scenes):
        sentences = _split_sentences(scene_text)
        for sentence_index, sentence_text in enumerate(sentences):
            tokens = _tokenize(sentence_text)
            actor_names = _extract_actors(sentence_text)
            canonical_actors = tuple(
                sorted({entity_graph.resolve(actor_name) for actor_name in actor_names})
            )
            action = _extract_action(tokens)
            objects = _extract_objects(tokens, actor_names, action)
            confidence = _event_confidence(
                sentence_text,
                tokens,
                canonical_actors,
                action,
                objects,
            )

            event_seed = (
                f"{scene_index}|{sentence_index}|{sentence_text}|"
                f"{canonical_actors}|{action}|{objects}"
            )
            event_id = hashlib.sha1(event_seed.encode("utf-8")).hexdigest()[:14]

            events.append(
                EventRecord(
                    event_id=event_id,
                    scene_index=scene_index,
                    sentence_index=sentence_index,
                    source_order=source_order,
                    text=sentence_text,
                    normalized_text=_normalized_event_text(sentence_text),
                    actors=canonical_actors,
                    action=action,
                    objects=objects,
                    confidence=confidence,
                )
            )
            source_order += 1

    deduped: dict[str, EventRecord] = {}
    duplicate_merge_count = 0
    for event in events:
        key = _event_key(event)
        if key in deduped:
            deduped[key] = _merge_event(deduped[key], event)
            duplicate_merge_count += 1
        else:
            deduped[key] = event

    normalized_events = tuple(
        sorted(deduped.values(), key=lambda event: event.source_order)
    )
    return EventExtractionResult(
        events=normalized_events,
        duplicate_merge_count=duplicate_merge_count,
    )


def extract_relations(events: tuple[EventRecord, ...]) -> RelationExtractionResult:
    """Extract causal and dependency relations across normalized events."""

    relations: list[RelationEdge] = []
    for event_index, event in enumerate(events):
        if event_index == 0:
            continue

        previous_event = events[event_index - 1]
        shared_actors = set(previous_event.actors) & set(event.actors)
        shared_objects = set(previous_event.objects) & set(event.objects)

        if shared_actors or shared_objects:
            relations.append(
                RelationEdge(
                    source_event_id=previous_event.event_id,
                    target_event_id=event.event_id,
                    relation_type="depends_on",
                    confidence=0.48,
                    reason="shared actors/objects",
                )
            )

        lowered_text = event.text.lower()
        if any(
            marker in lowered_text for marker in ("because", "therefore", "thus", "so ")
        ):
            relations.append(
                RelationEdge(
                    source_event_id=previous_event.event_id,
                    target_event_id=event.event_id,
                    relation_type="causes",
                    confidence=0.74,
                    reason="causal connective",
                )
            )

        if any(marker in lowered_text for marker in ("after", "then")):
            relations.append(
                RelationEdge(
                    source_event_id=previous_event.event_id,
                    target_event_id=event.event_id,
                    relation_type="before",
                    confidence=0.66,
                    reason="temporal connective",
                )
            )

    deduped: dict[tuple[str, str, str], RelationEdge] = {}
    for relation in relations:
        key = (
            relation.source_event_id,
            relation.target_event_id,
            relation.relation_type,
        )
        existing = deduped.get(key)
        if existing is None or relation.confidence > existing.confidence:
            deduped[key] = relation

    normalized_relations = tuple(deduped.values())
    causal_count = sum(
        1 for relation in normalized_relations if relation.relation_type == "causes"
    )
    dependency_count = sum(
        1
        for relation in normalized_relations
        if relation.relation_type in {"depends_on", "before"}
    )

    return RelationExtractionResult(
        relations=normalized_relations,
        causal_count=causal_count,
        dependency_count=dependency_count,
    )


def _extract_state_values(event: EventRecord) -> dict[str, str]:
    lowered_text = event.text.lower()
    states: dict[str, str] = {}
    if any(term in lowered_text for term in (" dies", "dead", "is dead", "was killed")):
        states["alive"] = "false"
    if any(term in lowered_text for term in (" alive", "survives", "is alive")):
        states["alive"] = "true"
    if any(term in lowered_text for term in ("has key", "holds key", "keeps key")):
        states["has_key"] = "true"
    if any(term in lowered_text for term in ("loses key", "drops key", "without key")):
        states["has_key"] = "false"
    return states


def detect_entity_state_conflicts(
    events: tuple[EventRecord, ...],
) -> tuple[EntityStateConflict, ...]:
    """Detect contradictions for canonical entity state assertions."""

    state_index: dict[tuple[str, str], tuple[str, str]] = {}
    conflicts: list[EntityStateConflict] = []

    for event in events:
        state_values = _extract_state_values(event)
        if not state_values:
            continue

        for actor in event.actors:
            for state_key, state_value in state_values.items():
                state_ref = (actor, state_key)
                prior_state = state_index.get(state_ref)
                if prior_state is not None and prior_state[0] != state_value:
                    conflicts.append(
                        EntityStateConflict(
                            entity_id=actor,
                            state_key=state_key,
                            expected_value=prior_state[0],
                            observed_value=state_value,
                            first_event_id=prior_state[1],
                            conflicting_event_id=event.event_id,
                            reason="state contradiction detected across event sequence",
                        )
                    )
                state_index[state_ref] = (state_value, event.event_id)

    return tuple(conflicts)


def _topological_order(
    events: tuple[EventRecord, ...],
    edges: tuple[RelationEdge, ...],
) -> tuple[list[str], set[str]]:
    event_ids = [event.event_id for event in events]
    source_order_map = {event.event_id: event.source_order for event in events}
    in_degree = {event_id: 0 for event_id in event_ids}
    adjacency: dict[str, list[str]] = {event_id: [] for event_id in event_ids}

    for edge in edges:
        if (
            edge.source_event_id not in in_degree
            or edge.target_event_id not in in_degree
        ):
            continue
        adjacency[edge.source_event_id].append(edge.target_event_id)
        in_degree[edge.target_event_id] += 1

    ready = [event_id for event_id, degree in in_degree.items() if degree == 0]
    ready.sort(key=lambda event_id: source_order_map[event_id])
    queue = deque(ready)

    ordered: list[str] = []
    while queue:
        event_id = queue.popleft()
        ordered.append(event_id)
        for neighbor_id in adjacency[event_id]:
            in_degree[neighbor_id] -= 1
            if in_degree[neighbor_id] == 0:
                queue.append(neighbor_id)

    if len(ordered) == len(event_ids):
        return ordered, set()

    cyclic_nodes = {event_id for event_id, degree in in_degree.items() if degree > 0}
    remaining_nodes = [event_id for event_id in event_ids if event_id not in ordered]
    remaining_nodes.sort(key=lambda event_id: source_order_map[event_id])
    ordered.extend(remaining_nodes)
    return ordered, cyclic_nodes


def infer_temporal_order(
    events: tuple[EventRecord, ...],
    relations: tuple[RelationEdge, ...],
) -> TemporalOrderResult:
    """Infer chronology from event relations and detect ordering contradictions."""

    temporal_edges = tuple(
        relation
        for relation in relations
        if relation.relation_type in _DEPENDENCY_RELATION_TYPES
    )
    ordered_event_ids, cyclic_nodes = _topological_order(events, temporal_edges)

    contradictions: list[str] = []
    if cyclic_nodes:
        contradictions.append(
            "cycle detected in temporal constraints: " + ", ".join(sorted(cyclic_nodes))
        )

    source_order_map = {event.event_id: event.source_order for event in events}
    for relation in temporal_edges:
        if relation.relation_type in {"before", "causes"}:
            if (
                source_order_map[relation.source_event_id]
                > source_order_map[relation.target_event_id]
            ):
                contradictions.append(
                    "impossible source order for edge "
                    f"{relation.source_event_id} -> {relation.target_event_id}"
                )

    return TemporalOrderResult(
        ordered_event_ids=tuple(ordered_event_ids),
        contradictions=tuple(contradictions),
        used_edges=temporal_edges,
    )


def repair_temporal_order(
    events: tuple[EventRecord, ...],
    relations: tuple[RelationEdge, ...],
) -> TemporalOrderResult:
    """Repair temporal ordering by removing low-confidence cycle edges."""

    active_edges = [
        relation
        for relation in relations
        if relation.relation_type in _DEPENDENCY_RELATION_TYPES
    ]
    removed_edges: list[RelationEdge] = []

    while True:
        ordered_event_ids, cyclic_nodes = _topological_order(
            events, tuple(active_edges)
        )
        if not cyclic_nodes:
            return TemporalOrderResult(
                ordered_event_ids=tuple(ordered_event_ids),
                contradictions=(),
                used_edges=tuple(active_edges),
                removed_edges=tuple(removed_edges),
            )

        cycle_edges = [
            edge
            for edge in active_edges
            if edge.source_event_id in cyclic_nodes
            and edge.target_event_id in cyclic_nodes
        ]
        if not cycle_edges:
            return TemporalOrderResult(
                ordered_event_ids=tuple(ordered_event_ids),
                contradictions=("cycle unresolved after edge analysis",),
                used_edges=tuple(active_edges),
                removed_edges=tuple(removed_edges),
            )

        edge_to_remove = min(cycle_edges, key=lambda edge: edge.confidence)
        active_edges.remove(edge_to_remove)
        removed_edges.append(edge_to_remove)


class BranchLifecycleManager:
    """Manage divergence nodes, lineage, and archive/merge workflows."""

    def __init__(
        self,
        policy: BranchBudgetPolicy | None = None,
    ) -> None:
        self._policy = policy or DEFAULT_BRANCH_BUDGET_POLICY
        self._branches: dict[str, BranchRecord] = {}
        self._counter = 0

    def create_root_branch(self, branch_id: str = "main") -> BranchRecord:
        if branch_id in self._branches:
            return self._branches[branch_id]

        root_branch = BranchRecord(
            branch_id=branch_id,
            parent_branch_id=None,
            divergence_event_id=None,
            label="root",
            created_at=_now_timestamp(),
            status="active",
            lineage=(branch_id,),
        )
        self._branches[branch_id] = root_branch
        return root_branch

    def _active_branch_ids(self) -> list[str]:
        return [
            branch_id
            for branch_id, branch in self._branches.items()
            if branch.status == "active"
        ]

    def archive_candidates(self) -> tuple[str, ...]:
        active_branches = [
            branch
            for branch in self._branches.values()
            if branch.status == "active" and branch.parent_branch_id is not None
        ]
        active_branches.sort(key=lambda branch: branch.created_at)
        return tuple(branch.branch_id for branch in active_branches)

    def create_divergence_node(
        self,
        *,
        parent_branch_id: str,
        divergence_event_id: str,
        label: str,
    ) -> BranchRecord:
        parent_branch = self._branches.get(parent_branch_id)
        if parent_branch is None:
            msg = f"Parent branch '{parent_branch_id}' does not exist."
            raise KeyError(msg)
        if parent_branch.status != "active":
            msg = f"Parent branch '{parent_branch_id}' is not active."
            raise ValueError(msg)

        if len(self._active_branch_ids()) >= self._policy.max_active_branches:
            candidates = ", ".join(self.archive_candidates())
            msg = (
                "Active branch budget exceeded. "
                f"Archive candidates: {candidates if candidates else 'none'}"
            )
            raise ValueError(msg)

        self._counter += 1
        branch_id = f"{parent_branch_id}.b{self._counter:03d}"
        branch = BranchRecord(
            branch_id=branch_id,
            parent_branch_id=parent_branch_id,
            divergence_event_id=divergence_event_id,
            label=label,
            created_at=_now_timestamp(),
            status="active",
            lineage=(*parent_branch.lineage, branch_id),
        )
        self._branches[branch_id] = branch
        return branch

    def archive_branch(self, branch_id: str, *, reason: str) -> BranchRecord:
        branch = self._branches.get(branch_id)
        if branch is None:
            msg = f"Branch '{branch_id}' does not exist."
            raise KeyError(msg)
        if branch.status != "active":
            return branch

        archived_count = sum(
            1
            for existing_branch in self._branches.values()
            if existing_branch.status == "archived"
        )
        if archived_count >= self._policy.max_archived_branches:
            msg = "Archived branch budget exceeded."
            raise ValueError(msg)

        updated_branch = replace(branch, status="archived", archive_reason=reason)
        self._branches[branch_id] = updated_branch
        return updated_branch

    def merge_branch(
        self,
        *,
        source_branch_id: str,
        target_branch_id: str,
        reason: str,
    ) -> BranchRecord:
        source_branch = self._branches.get(source_branch_id)
        target_branch = self._branches.get(target_branch_id)
        if source_branch is None or target_branch is None:
            msg = "Source or target branch does not exist."
            raise KeyError(msg)
        if source_branch.status != "active":
            msg = f"Branch '{source_branch_id}' must be active to merge."
            raise ValueError(msg)

        merged_branch = replace(
            source_branch,
            status="merged",
            merged_into=target_branch_id,
            merge_reason=reason,
        )
        self._branches[source_branch_id] = merged_branch
        return merged_branch

    def get_branch(self, branch_id: str) -> BranchRecord:
        branch = self._branches.get(branch_id)
        if branch is None:
            msg = f"Branch '{branch_id}' does not exist."
            raise KeyError(msg)
        return branch

    def all_branches(self) -> tuple[BranchRecord, ...]:
        return tuple(self._branches[branch_id] for branch_id in sorted(self._branches))

    def recommend_high_impact_nodes(
        self,
        events: tuple[EventRecord, ...],
        relations: tuple[RelationEdge, ...],
        *,
        top_n: int = 3,
    ) -> tuple[BranchRecommendation, ...]:
        outgoing_counts: dict[str, int] = {}
        for relation in relations:
            outgoing_counts[relation.source_event_id] = (
                outgoing_counts.get(relation.source_event_id, 0) + 1
            )

        recommendations: list[BranchRecommendation] = []
        for event in events:
            impact = event.confidence * 0.4
            impact += outgoing_counts.get(event.event_id, 0) * 0.15
            if event.action in _HIGH_IMPACT_ACTIONS:
                impact += 0.25
            if any(
                token in event.normalized_text
                for token in ("blood", "death", "truth", "betray")
            ):
                impact += 0.15

            recommendations.append(
                BranchRecommendation(
                    event_id=event.event_id,
                    impact_score=_clamp(impact),
                    reason="event has high dependency or narrative impact",
                )
            )

        recommendations.sort(key=lambda item: item.impact_score, reverse=True)
        return tuple(recommendations[:top_n])


def _build_predecessor_index(
    relations: tuple[RelationEdge, ...],
) -> dict[str, list[str]]:
    predecessors: dict[str, list[str]] = {}
    for relation in relations:
        if relation.relation_type not in _DEPENDENCY_RELATION_TYPES:
            continue
        predecessors.setdefault(relation.target_event_id, []).append(
            relation.source_event_id
        )
    return predecessors


def _build_successor_index(relations: tuple[RelationEdge, ...]) -> dict[str, list[str]]:
    successors: dict[str, list[str]] = {}
    for relation in relations:
        if relation.relation_type not in _DEPENDENCY_RELATION_TYPES:
            continue
        successors.setdefault(relation.source_event_id, []).append(
            relation.target_event_id
        )
    return successors


def _event_base_score(event: EventRecord) -> float:
    lowered_text = event.normalized_text
    intensity = 0.0
    if any(
        token in lowered_text
        for token in ("blood", "attack", "kill", "betray", "battle")
    ):
        intensity += 0.4
    if any(
        token in lowered_text for token in ("truth", "reveal", "confess", "discover")
    ):
        intensity += 0.2
    if any(token in lowered_text for token in ("laugh", "joke", "cozy")):
        intensity += 0.05

    score = event.confidence * 0.45 + intensity
    score += 0.1 if event.actors else 0.0
    score += 0.05 if event.objects else 0.0
    return _clamp(score)


def _state_value_for_constraint(event: EventRecord, state_key: str) -> str | None:
    states = _extract_state_values(event)
    return states.get(state_key)


class ConsequenceSimulator:
    """Incremental consequence simulator with canon constraints."""

    def _affected_subgraph(
        self,
        changed_event_ids: tuple[str, ...],
        relations: tuple[RelationEdge, ...],
    ) -> tuple[str, ...]:
        successors = _build_successor_index(relations)
        visited: set[str] = set(changed_event_ids)
        queue = deque(changed_event_ids)

        while queue:
            event_id = queue.popleft()
            for successor_id in successors.get(event_id, []):
                if successor_id not in visited:
                    visited.add(successor_id)
                    queue.append(successor_id)

        return tuple(sorted(visited))

    def _recompute_scores(
        self,
        events: tuple[EventRecord, ...],
        relations: tuple[RelationEdge, ...],
        *,
        target_event_ids: set[str] | None,
        baseline_scores: dict[str, float] | None,
        canon_constraints: tuple[CanonConstraint, ...],
        style_penalty_weight: float,
        changed_event_ids: set[str],
    ) -> tuple[dict[str, float], tuple[str, ...]]:
        event_by_id = {event.event_id: event for event in events}
        predecessors = _build_predecessor_index(relations)
        ordered_event_ids = [
            event.event_id
            for event in sorted(events, key=lambda item: item.source_order)
        ]

        scores = dict(baseline_scores or {})
        violations: list[str] = []

        for event_id in ordered_event_ids:
            if target_event_ids is not None and event_id not in target_event_ids:
                continue

            event = event_by_id[event_id]
            base_score = _event_base_score(event)

            predecessor_scores = [
                scores.get(predecessor_id, 0.0)
                for predecessor_id in predecessors.get(event_id, [])
            ]
            if predecessor_scores:
                base_score += mean(predecessor_scores) * 0.15

            if event_id in changed_event_ids:
                if any(
                    token in event.normalized_text
                    for token in ("joke", "laugh", "smile")
                ):
                    base_score -= style_penalty_weight
                if any(
                    token in event.normalized_text
                    for token in ("blood", "kill", "betray")
                ):
                    base_score += style_penalty_weight * 0.35

            for constraint in canon_constraints:
                if constraint.entity_id not in event.actors:
                    continue
                observed_value = _state_value_for_constraint(
                    event, constraint.state_key
                )
                if observed_value is None:
                    continue
                if observed_value != constraint.required_value:
                    violations.append(
                        f"canon violation at {event.event_id}: "
                        f"{constraint.state_key}={observed_value}, "
                        f"expected {constraint.required_value}"
                    )
                    base_score = min(base_score, 0.15)

            scores[event_id] = _clamp(base_score)

        return scores, tuple(violations)

    def simulate(
        self,
        events: tuple[EventRecord, ...],
        relations: tuple[RelationEdge, ...],
        *,
        changed_event_ids: tuple[str, ...],
        canon_constraints: tuple[CanonConstraint, ...] = (),
        style_penalty_weight: float = 0.15,
    ) -> ConsequenceSimulationResult:
        """Run affected-subgraph recompute and compare to full baseline recompute."""

        changed_set = set(changed_event_ids)
        affected_event_ids = self._affected_subgraph(changed_event_ids, relations)
        affected_set = set(affected_event_ids)

        baseline_scores, baseline_violations = self._recompute_scores(
            events,
            relations,
            target_event_ids=None,
            baseline_scores=None,
            canon_constraints=canon_constraints,
            style_penalty_weight=style_penalty_weight,
            changed_event_ids=changed_set,
        )

        incremental_scores, incremental_violations = self._recompute_scores(
            events,
            relations,
            target_event_ids=affected_set,
            baseline_scores=baseline_scores,
            canon_constraints=canon_constraints,
            style_penalty_weight=style_penalty_weight,
            changed_event_ids=changed_set,
        )

        if affected_event_ids:
            deltas = [
                abs(incremental_scores[event_id] - baseline_scores[event_id])
                for event_id in affected_event_ids
            ]
            consistency_score = _clamp(1.0 - mean(deltas))
        else:
            consistency_score = 1.0

        all_violations = tuple(
            sorted(set((*baseline_violations, *incremental_violations)))
        )

        return ConsequenceSimulationResult(
            affected_event_ids=affected_event_ids,
            recomputed_scores={
                event_id: incremental_scores[event_id]
                for event_id in affected_event_ids
            },
            baseline_scores=baseline_scores,
            constraint_violations=all_violations,
            consistency_score=consistency_score,
            used_incremental=True,
        )


CURRENT_GRAPH_SCHEMA_VERSION = 3


class GraphMigrationManager:
    """Schema migration manager with replay checkpoints and rollback state."""

    def __init__(self) -> None:
        self._migrations = {
            1: self._migrate_v1_to_v2,
            2: self._migrate_v2_to_v3,
        }

    def _deep_copy_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(json.dumps(payload)))

    def migrate_payload(
        self,
        payload: dict[str, Any],
        *,
        target_version: int = CURRENT_GRAPH_SCHEMA_VERSION,
        fail_on_version: int | None = None,
    ) -> MigrationReplayResult:
        """Migrate payload to target schema version with checkpoints."""

        working_payload = self._deep_copy_payload(payload)
        current_version = int(working_payload.get("schema_version", 1))

        checkpoints: list[MigrationCheckpoint] = []
        applied_versions: list[int] = []

        while current_version < target_version:
            migration = self._migrations.get(current_version)
            if migration is None:
                msg = f"No migration defined from schema version {current_version}."
                raise GraphMigrationError(
                    msg,
                    rollback_payload=self._deep_copy_payload(working_payload),
                    checkpoints=tuple(checkpoints),
                )

            checkpoint_payload = self._deep_copy_payload(working_payload)
            checkpoints.append(
                MigrationCheckpoint(
                    from_version=current_version,
                    payload=checkpoint_payload,
                )
            )

            next_version = current_version + 1
            if fail_on_version is not None and next_version == fail_on_version:
                msg = f"Forced migration failure at version {next_version}."
                raise GraphMigrationError(
                    msg,
                    rollback_payload=checkpoint_payload,
                    checkpoints=tuple(checkpoints),
                )

            working_payload = migration(working_payload)
            current_version = int(
                working_payload.get("schema_version", current_version + 1)
            )
            applied_versions.append(current_version)

        return MigrationReplayResult(
            migrated_payload=working_payload,
            checkpoints=tuple(checkpoints),
            applied_versions=tuple(applied_versions),
        )

    def rollback_to_checkpoint(
        self,
        replay_result: MigrationReplayResult,
        *,
        checkpoint_from_version: int,
    ) -> dict[str, Any]:
        """Rollback to a specific checkpoint payload from migration replay."""

        for checkpoint in replay_result.checkpoints:
            if checkpoint.from_version == checkpoint_from_version:
                return self._deep_copy_payload(checkpoint.payload)

        msg = f"Checkpoint for version {checkpoint_from_version} not found."
        raise KeyError(msg)

    def _migrate_v1_to_v2(self, payload: dict[str, Any]) -> dict[str, Any]:
        migrated = self._deep_copy_payload(payload)

        events_v2: list[dict[str, Any]] = []
        for index, event in enumerate(migrated.get("events", [])):
            event_text = str(event.get("text", "")).strip()
            event_id = event.get("event_id") or event.get("id") or f"evt_{index:03d}"
            events_v2.append(
                {
                    "event_id": event_id,
                    "scene_index": int(event.get("scene_index", event.get("scene", 0))),
                    "sentence_index": int(event.get("sentence_index", 0)),
                    "source_order": int(
                        event.get("source_order", event.get("order", index))
                    ),
                    "text": event_text,
                    "normalized_text": _normalized_event_text(event_text),
                    "actors": list(event.get("actors", [])),
                    "action": event.get("action", "unknown"),
                    "objects": list(event.get("objects", [])),
                    "confidence": float(event.get("confidence", 0.5)),
                }
            )

        relations_v2: list[dict[str, Any]] = []
        for relation in migrated.get("relations", []):
            relations_v2.append(
                {
                    "source_event_id": relation.get(
                        "source_event_id", relation.get("source")
                    ),
                    "target_event_id": relation.get(
                        "target_event_id", relation.get("target")
                    ),
                    "relation_type": relation.get(
                        "relation_type", relation.get("type", "depends_on")
                    ),
                    "confidence": float(relation.get("confidence", 0.5)),
                    "reason": relation.get("reason", "migrated from v1"),
                }
            )

        branches_v2: list[dict[str, Any]] = []
        for branch in migrated.get("branches", []):
            branch_id = branch.get("branch_id", branch.get("id", "main"))
            branches_v2.append(
                {
                    "branch_id": branch_id,
                    "parent_branch_id": branch.get(
                        "parent_branch_id", branch.get("parent")
                    ),
                    "divergence_event_id": branch.get(
                        "divergence_event_id",
                        branch.get("divergence_event"),
                    ),
                    "label": branch.get("label", "migrated"),
                    "created_at": branch.get("created_at", _now_timestamp()),
                    "status": branch.get("status", "active"),
                    "merged_into": branch.get("merged_into"),
                }
            )

        migrated["events"] = events_v2
        migrated["relations"] = relations_v2
        migrated["branches"] = branches_v2
        migrated["schema_version"] = 2
        migrated.setdefault("metadata", {})
        migrated["metadata"]["migrated_to_v2_at"] = _now_timestamp()
        return migrated

    def _migrate_v2_to_v3(self, payload: dict[str, Any]) -> dict[str, Any]:
        migrated = self._deep_copy_payload(payload)

        branches = migrated.get("branches", [])
        branch_by_id = {branch["branch_id"]: branch for branch in branches}

        def lineage_for(branch_id: str) -> tuple[str, ...]:
            lineage: list[str] = []
            current_id: str | None = branch_id
            safety_counter = 0
            while current_id is not None and safety_counter < 128:
                lineage.append(current_id)
                parent_id = branch_by_id.get(current_id, {}).get("parent_branch_id")
                current_id = parent_id
                safety_counter += 1
            return tuple(reversed(lineage))

        for branch in branches:
            branch_id = branch["branch_id"]
            branch["lineage"] = list(lineage_for(branch_id))
            branch.setdefault("archive_reason", None)
            branch.setdefault("merge_reason", None)

        migrated["schema_version"] = 3
        migrated.setdefault("metadata", {})
        migrated["metadata"]["migrated_to_v3_at"] = _now_timestamp()
        return migrated


class GraphPersistenceStore:
    """Persist and load graph snapshots with schema migration support."""

    def __init__(self, migration_manager: GraphMigrationManager | None = None) -> None:
        self._migration_manager = migration_manager or GraphMigrationManager()

    def _event_to_payload(self, event: EventRecord) -> dict[str, Any]:
        return {
            "event_id": event.event_id,
            "scene_index": event.scene_index,
            "sentence_index": event.sentence_index,
            "source_order": event.source_order,
            "text": event.text,
            "normalized_text": event.normalized_text,
            "actors": list(event.actors),
            "action": event.action,
            "objects": list(event.objects),
            "confidence": event.confidence,
        }

    def _event_from_payload(self, payload: dict[str, Any]) -> EventRecord:
        return EventRecord(
            event_id=str(payload["event_id"]),
            scene_index=int(payload["scene_index"]),
            sentence_index=int(payload.get("sentence_index", 0)),
            source_order=int(payload.get("source_order", 0)),
            text=str(payload.get("text", "")),
            normalized_text=str(payload.get("normalized_text", "")),
            actors=tuple(payload.get("actors", [])),
            action=str(payload.get("action", "unknown")),
            objects=tuple(payload.get("objects", [])),
            confidence=float(payload.get("confidence", 0.0)),
        )

    def _relation_to_payload(self, relation: RelationEdge) -> dict[str, Any]:
        return {
            "source_event_id": relation.source_event_id,
            "target_event_id": relation.target_event_id,
            "relation_type": relation.relation_type,
            "confidence": relation.confidence,
            "reason": relation.reason,
        }

    def _relation_from_payload(self, payload: dict[str, Any]) -> RelationEdge:
        return RelationEdge(
            source_event_id=str(payload["source_event_id"]),
            target_event_id=str(payload["target_event_id"]),
            relation_type=str(payload["relation_type"]),
            confidence=float(payload.get("confidence", 0.0)),
            reason=str(payload.get("reason", "")),
        )

    def _branch_to_payload(self, branch: BranchRecord) -> dict[str, Any]:
        return {
            "branch_id": branch.branch_id,
            "parent_branch_id": branch.parent_branch_id,
            "divergence_event_id": branch.divergence_event_id,
            "label": branch.label,
            "created_at": branch.created_at,
            "status": branch.status,
            "lineage": list(branch.lineage),
            "merged_into": branch.merged_into,
            "archive_reason": branch.archive_reason,
            "merge_reason": branch.merge_reason,
        }

    def _branch_from_payload(self, payload: dict[str, Any]) -> BranchRecord:
        return BranchRecord(
            branch_id=str(payload["branch_id"]),
            parent_branch_id=payload.get("parent_branch_id"),
            divergence_event_id=payload.get("divergence_event_id"),
            label=str(payload.get("label", "")),
            created_at=str(payload.get("created_at", _now_timestamp())),
            status=str(payload.get("status", "active")),
            lineage=tuple(payload.get("lineage", [payload.get("branch_id", "main")])),
            merged_into=payload.get("merged_into"),
            archive_reason=payload.get("archive_reason"),
            merge_reason=payload.get("merge_reason"),
        )

    def to_payload(self, snapshot: GraphSnapshot) -> dict[str, Any]:
        return {
            "schema_version": snapshot.schema_version,
            "story_id": snapshot.story_id,
            "events": [self._event_to_payload(event) for event in snapshot.events],
            "relations": [
                self._relation_to_payload(relation) for relation in snapshot.relations
            ],
            "branches": [
                self._branch_to_payload(branch) for branch in snapshot.branches
            ],
            "metadata": dict(snapshot.metadata),
        }

    def from_payload(self, payload: dict[str, Any]) -> GraphSnapshot:
        return GraphSnapshot(
            schema_version=int(
                payload.get("schema_version", CURRENT_GRAPH_SCHEMA_VERSION)
            ),
            story_id=str(payload.get("story_id", "story")),
            events=tuple(
                self._event_from_payload(event) for event in payload.get("events", [])
            ),
            relations=tuple(
                self._relation_from_payload(relation)
                for relation in payload.get("relations", [])
            ),
            branches=tuple(
                self._branch_from_payload(branch)
                for branch in payload.get("branches", [])
            ),
            metadata=dict(payload.get("metadata", {})),
        )

    def save_snapshot(self, snapshot: GraphSnapshot, path: Path) -> None:
        """Persist graph snapshot as JSON payload."""

        payload = self.to_payload(snapshot)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load_snapshot(self, path: Path, *, auto_migrate: bool = True) -> GraphSnapshot:
        """Load snapshot and migrate to current schema when requested."""

        payload = json.loads(path.read_text(encoding="utf-8"))
        schema_version = int(payload.get("schema_version", 1))

        if auto_migrate and schema_version < CURRENT_GRAPH_SCHEMA_VERSION:
            replay_result = self._migration_manager.migrate_payload(payload)
            payload = replay_result.migrated_payload

        return self.from_payload(payload)

    def replay_migration(
        self,
        payload: dict[str, Any],
        *,
        target_version: int = CURRENT_GRAPH_SCHEMA_VERSION,
        fail_on_version: int | None = None,
    ) -> MigrationReplayResult:
        """Replay migration chain for historical snapshots."""

        return self._migration_manager.migrate_payload(
            payload,
            target_version=target_version,
            fail_on_version=fail_on_version,
        )

    def rollback_to_checkpoint(
        self,
        replay_result: MigrationReplayResult,
        *,
        checkpoint_from_version: int,
    ) -> dict[str, Any]:
        """Rollback migrated payload to a prior checkpoint version."""

        return self._migration_manager.rollback_to_checkpoint(
            replay_result,
            checkpoint_from_version=checkpoint_from_version,
        )
