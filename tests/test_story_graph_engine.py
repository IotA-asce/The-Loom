"""Tests for phase-4 story graph and branching core."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from core.story_graph_engine import (
    BranchBudgetPolicy,
    BranchLifecycleManager,
    CanonConstraint,
    ConsequenceSimulator,
    EntityAliasGraph,
    GraphMigrationError,
    GraphPersistenceStore,
    extract_events_hybrid,
    extract_relations,
    infer_temporal_order,
    repair_temporal_order,
)


def test_g41_event_extraction_pipeline_and_duplicate_merge() -> None:
    raw_text = (
        "Captain Arin discovers the hidden key.\n\n"
        "Captain Arin discovers the hidden key.\n\n"
        "Mina reveals the truth because the gate fails."
    )

    result = extract_events_hybrid(raw_text)
    assert result.events
    assert result.duplicate_merge_count >= 1
    assert all(0.0 <= event.confidence <= 1.0 for event in result.events)
    assert all(event.normalized_text for event in result.events)


def test_g42_entity_alias_relation_integrity_and_conflict_detection() -> None:
    alias_graph = EntityAliasGraph()
    arin_id = alias_graph.register_entity("Arin", aliases=("Captain",))

    raw_text = (
        "Captain is alive and holds key.\n\n"
        "Arin is dead after the battle.\n\n"
        "Arin reveals the truth because the archive burns."
    )
    extraction = extract_events_hybrid(raw_text, alias_graph=alias_graph)
    relations = extract_relations(extraction.events)

    assert any(arin_id in event.actors for event in extraction.events)
    assert relations.causal_count >= 1
    assert relations.dependency_count >= 1

    from core.story_graph_engine import detect_entity_state_conflicts

    conflicts = detect_entity_state_conflicts(extraction.events)
    assert conflicts
    assert conflicts[0].entity_id == arin_id
    assert conflicts[0].state_key == "alive"


def test_g43_temporal_order_contradiction_detection_and_repair() -> None:
    raw_text = (
        "Mina finds the map.\n\n"
        "Then Mina opens the gate.\n\n"
        "Mina closes the gate after the alarm sounds."
    )
    extraction = extract_events_hybrid(raw_text)
    relations = list(extract_relations(extraction.events).relations)

    first_event = extraction.events[0]
    second_event = extraction.events[1]
    relations.append(
        relations[0].__class__(
            source_event_id=second_event.event_id,
            target_event_id=first_event.event_id,
            relation_type="before",
            confidence=0.1,
            reason="contradictory edge for repair test",
        )
    )

    order_result = infer_temporal_order(extraction.events, tuple(relations))
    assert order_result.contradictions

    repaired = repair_temporal_order(extraction.events, tuple(relations))
    assert repaired.ordered_event_ids
    assert not repaired.contradictions
    assert repaired.removed_edges


def test_g44_divergence_lifecycle_recommendations_and_budget_workflow() -> None:
    raw_text = (
        "Arin reveals the truth.\n\n"
        "The captain attacks the cult.\n\n"
        "Mina betrays the council."
    )
    extraction = extract_events_hybrid(raw_text)
    relations = extract_relations(extraction.events)

    manager = BranchLifecycleManager(policy=BranchBudgetPolicy(max_active_branches=2))
    root = manager.create_root_branch("main")
    assert root.lineage == ("main",)

    branch_one = manager.create_divergence_node(
        parent_branch_id="main",
        divergence_event_id=extraction.events[0].event_id,
        label="what-if-1",
    )
    assert branch_one.parent_branch_id == "main"
    assert branch_one.lineage[0] == "main"

    with pytest.raises(ValueError, match="Active branch budget exceeded"):
        manager.create_divergence_node(
            parent_branch_id="main",
            divergence_event_id=extraction.events[1].event_id,
            label="what-if-2",
        )

    archived = manager.archive_branch(branch_one.branch_id, reason="inactive branch")
    assert archived.status == "archived"

    branch_two = manager.create_divergence_node(
        parent_branch_id="main",
        divergence_event_id=extraction.events[1].event_id,
        label="what-if-2",
    )
    merged = manager.merge_branch(
        source_branch_id=branch_two.branch_id,
        target_branch_id="main",
        reason="accepted canonical merge",
    )
    assert merged.status == "merged"
    assert merged.merged_into == "main"

    recommendations = manager.recommend_high_impact_nodes(
        extraction.events, relations.relations
    )
    assert recommendations
    assert recommendations[0].impact_score >= recommendations[-1].impact_score


def test_g45_consequence_simulation_consistency_and_constraints() -> None:
    raw_text = (
        "Arin is alive and holds key.\n\n"
        "Arin attacks the cult because the gate collapses.\n\n"
        "Arin is dead after the blast."
    )
    extraction = extract_events_hybrid(raw_text)
    relations = extract_relations(extraction.events)
    simulator = ConsequenceSimulator()

    changed_event_ids = (extraction.events[1].event_id,)
    result = simulator.simulate(
        extraction.events,
        relations.relations,
        changed_event_ids=changed_event_ids,
        canon_constraints=(
            CanonConstraint(
                entity_id=extraction.events[0].actors[0],
                state_key="alive",
                required_value="true",
            ),
        ),
        style_penalty_weight=0.2,
    )

    assert result.affected_event_ids
    assert extraction.events[1].event_id in result.affected_event_ids
    assert result.consistency_score >= 0.8
    assert result.constraint_violations


def test_g46_graph_persistence_migration_replay_and_rollback() -> None:
    store = GraphPersistenceStore()

    payload_v1 = json.loads(
        Path("tests/fixtures/golden/graph_snapshot_v1.json").read_text(encoding="utf-8")
    )
    payload_v2 = json.loads(
        Path("tests/fixtures/golden/graph_snapshot_v2.json").read_text(encoding="utf-8")
    )

    migrated_v1 = store.replay_migration(payload_v1)
    migrated_v2 = store.replay_migration(payload_v2)
    assert migrated_v1.migrated_payload["schema_version"] == 3
    assert migrated_v2.migrated_payload["schema_version"] == 3
    assert migrated_v1.checkpoints

    snapshot = store.from_payload(migrated_v1.migrated_payload)
    assert snapshot.schema_version == 3
    assert snapshot.events
    assert snapshot.branches

    with pytest.raises(GraphMigrationError) as error_info:
        store.replay_migration(payload_v1, fail_on_version=2)

    rollback_payload = error_info.value.rollback_payload
    assert rollback_payload["schema_version"] == 1


def test_phase4_done_criteria_thresholds_hold() -> None:
    thresholds = json.loads(
        Path("tests/fixtures/golden/story_graph_thresholds.json").read_text(
            encoding="utf-8"
        )
    )

    raw_text = (
        "Captain Arin discovers the key and reveals the truth.\n\n"
        "Mina attacks the cult because the gate collapses.\n\n"
        "Arin is alive before Mina is dead."
    )
    extraction = extract_events_hybrid(raw_text)
    relations = extract_relations(extraction.events)
    temporal = infer_temporal_order(extraction.events, relations.relations)
    repaired_temporal = repair_temporal_order(extraction.events, relations.relations)

    simulator = ConsequenceSimulator()
    simulation = simulator.simulate(
        extraction.events,
        relations.relations,
        changed_event_ids=(extraction.events[0].event_id,),
    )

    mean_confidence = sum(event.confidence for event in extraction.events) / len(
        extraction.events
    )

    assert mean_confidence >= thresholds["min_event_confidence_mean"]
    assert len(temporal.contradictions) <= thresholds["max_temporal_contradictions"]
    assert not repaired_temporal.contradictions
    assert simulation.consistency_score >= thresholds["min_consequence_consistency"]
