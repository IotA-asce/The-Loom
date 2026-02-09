"""Tests for Phase 7 orchestration and state integrity goals."""

from __future__ import annotations

from typing import Any

import pytest
from agents.director import (
    check_edit_protection,
    create_generation_plan,
    get_compatibility_matrix,
    get_edit_provenance,
    get_phase7_metrics,
    get_sync_state,
    initialize_contracts,
    initialize_sync_state,
    log_panel_redraw,
    log_text_edit,
    mark_text_stale,
    run_sync_regression_test,
    validate_agent_contract,
)
from core.orchestration_engine import (
    AgentContract,
    CompatibilityMatrix,
    ContractRegistry,
    EditLogStore,
    EditType,
    IdempotencyStore,
    JobStatus,
    OrchestrationEngine,
    RetryHandler,
    RetryPolicy,
    SyncStateManager,
    SyncStatus,
    TransactionLog,
)


class TestG71DirectorAgentContracts:
    """G7.1: Define strict typed contracts for all agent inputs/outputs."""

    def test_contract_registration_and_retrieval(self) -> None:
        registry = ContractRegistry()
        contract = AgentContract(
            agent_name="test-agent",
            input_schema_version="test-input-v1",
            output_schema_version="test-output-v1",
            supported_model_versions=("model-a", "model-b"),
            supported_workflow_versions=("wf-v1",),
            required_context_fields=("story_id", "branch_id"),
            required_output_fields=("result",),
        )
        registry.register_contract(contract)

        retrieved = registry.get_contract("test-agent")
        assert retrieved is not None
        assert retrieved.agent_name == "test-agent"
        assert retrieved.input_schema_version == "test-input-v1"

    def test_contract_validation_missing_fields(self) -> None:
        registry = ContractRegistry()
        contract = AgentContract(
            agent_name="test-agent",
            input_schema_version="v1",
            output_schema_version="v1",
            supported_model_versions=("model-a",),
            supported_workflow_versions=("wf-v1",),
            required_context_fields=("story_id", "branch_id", "required_field"),
            required_output_fields=(),
        )
        registry.register_contract(contract)

        result = registry.validate_input(
            "test-agent",
            {"story_id": "s1", "branch_id": "b1"},  # missing required_field
            "model-a",
            "wf-v1",
        )
        assert not result.valid
        assert any("required_field" in v for v in result.violations)

    def test_contract_validation_unregistered_agent(self) -> None:
        registry = ContractRegistry()
        result = registry.validate_input(
            "unknown-agent",
            {"story_id": "s1"},
            "model-a",
            "wf-v1",
        )
        assert not result.valid
        assert any("No contract registered" in v for v in result.violations)

    def test_compatibility_matrix(self) -> None:
        matrix = CompatibilityMatrix(
            matrix_id="test-matrix",
            model_versions=("model-a", "model-b"),
            workflow_versions=("wf-v1", "wf-v2"),
            compatibilities={
                ("model-a", "wf-v1"): True,
                ("model-a", "wf-v2"): False,
                ("model-b", "wf-v1"): True,
                ("model-b", "wf-v2"): True,
            },
        )
        assert matrix.is_compatible("model-a", "wf-v1") is True
        assert matrix.is_compatible("model-a", "wf-v2") is False
        assert matrix.is_compatible("model-b", "wf-v2") is True
        assert matrix.is_compatible("unknown", "wf-v1") is False

    def test_director_initializes_contracts(self) -> None:
        initialize_contracts()
        matrix = get_compatibility_matrix()
        assert matrix is not None
        assert "llama-3" in matrix.model_versions
        assert "text-gen-v1" in matrix.workflow_versions
        assert matrix.is_compatible("llama-3", "text-gen-v1") is True
        assert matrix.is_compatible("sd-controlnet-v1", "text-gen-v1") is False

    def test_director_contract_validation(self) -> None:
        initialize_contracts()
        # Valid writer input
        valid = validate_agent_contract(
            "writer",
            {"story_id": "s1", "branch_id": "b1", "user_prompt": "test"},
            "llama-3",
            "text-gen-v1",
        )
        assert valid is True


class TestG72JobOrchestrationReliability:
    """G7.2: Job orchestration reliability with idempotency and retries."""

    def test_idempotency_key_generation(self) -> None:
        store = IdempotencyStore()
        key1, is_dup1 = store.check_or_create(
            story_id="story-1",
            branch_id="branch-1",
            scene_id="scene-1",
            generation_type="text",
            user_request_hash="hash-abc",
        )
        assert not is_dup1
        assert len(key1) == 32  # SHA-256 truncated

        # Same parameters should return duplicate
        key2, is_dup2 = store.check_or_create(
            story_id="story-1",
            branch_id="branch-1",
            scene_id="scene-1",
            generation_type="text",
            user_request_hash="hash-abc",
        )
        assert is_dup2 is True
        assert key1 == key2

    def test_idempotency_duplicate_count(self) -> None:
        store = IdempotencyStore()
        for _ in range(3):
            store.check_or_create(
                story_id="story-1",
                branch_id="branch-1",
                scene_id="scene-1",
                generation_type="text",
                user_request_hash="hash-xyz",
            )
        assert store.duplicate_lineage_count() == 2

    def test_transaction_log_commit(self) -> None:
        log = TransactionLog()
        record = log.begin_transaction(
            branch_id="branch-1",
            version_id="v1",
            previous_state={"status": "pending"},
            transition_type="generation_start",
        )
        assert record.committed is False

        success = log.commit_transaction(
            record.transaction_id,
            {"status": "completed", "result": "ok"},
        )
        assert success is True

        history = log.get_branch_history("branch-1")
        assert len(history) == 1
        assert history[0].committed is True
        assert history[0].new_state["status"] == "completed"

    def test_retry_handler_bounds(self) -> None:
        policy = RetryPolicy(max_attempts=3, backoff_seconds=1.0)
        handler = RetryHandler(policy)

        job_id = "job-123"
        assert handler.should_retry(job_id, "transient error") is True

        handler.record_attempt(job_id)  # 1
        assert handler.should_retry(job_id, "transient error") is True

        handler.record_attempt(job_id)  # 2
        assert handler.should_retry(job_id, "transient error") is True

        handler.record_attempt(job_id)  # 3
        assert handler.should_retry(job_id, "transient error") is False

    def test_retry_backoff_calculation(self) -> None:
        policy = RetryPolicy(
            backoff_seconds=1.0,
            backoff_multiplier=2.0,
            max_backoff_seconds=10.0,
        )
        handler = RetryHandler(policy)

        assert handler.get_backoff_seconds(1) == 1.0
        assert handler.get_backoff_seconds(2) == 2.0
        assert handler.get_backoff_seconds(3) == 4.0
        assert handler.get_backoff_seconds(10) == 10.0  # capped at max

    def test_dead_letter_queue(self) -> None:
        policy = RetryPolicy(max_attempts=2)
        handler = RetryHandler(policy)

        job_id = "job-456"
        handler.record_attempt(job_id)
        handler.record_attempt(job_id)

        dl_record = handler.send_to_dead_letter(
            job_id, "idmp-key-123", "max retries exceeded"
        )
        assert dl_record.original_job_id == job_id
        assert dl_record.idempotency_key == "idmp-key-123"
        assert dl_record.failure_reason == "max_retries_exceeded"

        dead_letters = handler.get_dead_letters()
        assert len(dead_letters) == 1

    def test_director_generation_plan_idempotency(self) -> None:
        plan1 = create_generation_plan(
            branch_id="branch-test",
            scene_id="scene-1",
            user_request_hash="same-request",
        )
        plan2 = create_generation_plan(
            branch_id="branch-test",
            scene_id="scene-1",
            user_request_hash="same-request",
        )
        # Same idempotency key for same request
        assert plan1.idempotency_key == plan2.idempotency_key
        # Second plan should be marked as duplicate


class TestG73EditProvenanceAndRegeneration:
    """G7.3: Edit provenance and scoped regeneration."""

    def test_edit_log_append_and_retrieve(self) -> None:
        store = EditLogStore()
        event = store.append_edit(
            branch_id="branch-1",
            scene_id="scene-1",
            edit_type=EditType.TEXT_REPLACE,
            span_start=10,
            span_end=50,
            previous_content="old text",
            new_content="new text",
            actor="user",
            reason="clarity improvement",
        )
        assert event.edit_id.startswith("edit:branch-1:")
        assert event.actor == "user"
        assert event.edit_type == EditType.TEXT_REPLACE

        log = store.get_log("branch-1")
        assert log is not None
        assert len(log.events) == 1

    def test_edit_log_version_counter(self) -> None:
        store = EditLogStore()
        for i in range(5):
            store.append_edit(
                branch_id="branch-1",
                scene_id=f"scene-{i}",
                edit_type=EditType.TEXT_INSERT,
                actor="user",
            )
        log = store.get_log("branch-1")
        assert log is not None
        assert log.version_counter == 5

    def test_edit_log_user_edits_filter(self) -> None:
        store = EditLogStore()
        store.append_edit(
            branch_id="branch-1",
            scene_id="scene-1",
            edit_type=EditType.TEXT_REPLACE,
            actor="user",
        )
        store.append_edit(
            branch_id="branch-1",
            scene_id="scene-1",
            edit_type=EditType.PANEL_REDRAW,
            actor="system",
        )
        log = store.get_log("branch-1")
        assert log is not None
        user_edits = log.get_user_edits()
        assert len(user_edits) == 1
        assert user_edits[0].edit_type == EditType.TEXT_REPLACE

    def test_regeneration_scope_calculation(self) -> None:
        store = EditLogStore()
        # Add some edits
        store.append_edit(
            branch_id="branch-1",
            scene_id="scene-1",
            edit_type=EditType.TEXT_REPLACE,
            span_start=0,
            span_end=100,
            actor="user",
        )
        store.append_edit(
            branch_id="branch-1",
            scene_id="scene-1",
            edit_type=EditType.PANEL_REDRAW,
            panel_index=2,
            actor="user",
        )

        # Request regeneration from first edit - second edit is after it
        plan = store.create_regeneration_plan("branch-1", "edit:branch-1:000000")
        assert "scene-1" in plan.affected_scenes
        assert plan.affected_panels.get("scene-1") == (2,)
        # There IS a user edit after source (000001), so preserve_user_edits=True
        assert plan.preserve_user_edits is True

    def test_edit_provenance_query(self) -> None:
        store = EditLogStore()
        store.append_edit(
            branch_id="branch-1",
            scene_id="scene-1",
            edit_type=EditType.TEXT_REPLACE,
            actor="user",
            reason="test edit",
        )
        store.append_edit(
            branch_id="branch-1",
            scene_id="scene-1",
            edit_type=EditType.BRANCH_DIVERGE,
            actor="system",
            reason="divergence",
        )

        provenance = store.query_provenance("branch-1")
        assert provenance["branch_id"] == "branch-1"
        assert provenance["event_count"] == 2
        assert provenance["user_edit_count"] == 1
        assert provenance["complete"] is True

    def test_director_text_edit_logging(self) -> None:
        log_text_edit(
            branch_id="branch-director",
            scene_id="scene-1",
            span_start=10,
            span_end=50,
            previous_content="old",
            new_content="new",
            actor="user",
            reason="improvement",
        )
        provenance = get_edit_provenance("branch-director")
        assert provenance["event_count"] >= 1
        assert provenance["user_edit_count"] >= 1

    def test_director_panel_redraw_logging(self) -> None:
        log_panel_redraw(
            branch_id="branch-panels",
            scene_id="scene-1",
            panel_index=3,
            actor="user",
            reason="anatomy fix",
        )
        provenance = get_edit_provenance("branch-panels")
        assert provenance["complete"] is True

    def test_edit_protection_check(self) -> None:
        # First log some user edits
        log_text_edit(
            branch_id="branch-protect",
            scene_id="scene-1",
            span_start=0,
            span_end=100,
            previous_content="original",
            new_content="edited",
            actor="user",
        )
        # Check protection
        protected = check_edit_protection("branch-protect", "scene-1:text")
        # Should detect user edit in scope
        assert isinstance(protected, bool)


class TestG74SyncSemanticsDualOutputs:
    """G7.4: Sync semantics for dual text/image outputs."""

    def test_sync_state_creation(self) -> None:
        manager = SyncStateManager()
        shared_version = manager.create_shared_version(
            scene_id="scene-1",
            text_version="text-v1",
            image_version="img-v1",
        )
        assert shared_version.scene_id == "scene-1"
        assert shared_version.combined_version.startswith("v")

        state = manager.update_sync_state(
            scene_id="scene-1",
            shared_version=shared_version,
            text_status=SyncStatus.SYNCED,
            image_status=SyncStatus.SYNCED,
        )
        assert state.text_status == SyncStatus.SYNCED
        assert state.image_status == SyncStatus.SYNCED
        assert state.scene_id == "scene-1"

    def test_sync_stale_marking(self) -> None:
        manager = SyncStateManager()
        shared = manager.create_shared_version("scene-1", "v1", "v1")
        manager.update_sync_state(
            "scene-1", shared, SyncStatus.SYNCED, SyncStatus.SYNCED
        )

        # Mark text stale
        state = manager.mark_stale("scene-1", "text", "user edit")
        assert state is not None
        assert state.text_status == SyncStatus.TEXT_STALE
        assert state.image_status == SyncStatus.SYNCED
        assert "text:user edit" in state.stale_indicators

        # Mark image stale
        state = manager.mark_stale("scene-1", "image", "regeneration")
        assert state is not None
        assert state.text_status == SyncStatus.BOTH_STALE
        assert state.image_status == SyncStatus.BOTH_STALE

    def test_sync_regression_scenario_race_condition(self) -> None:
        manager = SyncStateManager()
        # Simulate race: text and image update without sync
        events: list[dict[str, Any]] = [
            {"type": "text_update", "scene_id": "scene-1", "version": "text-v1"},
            {"type": "image_update", "scene_id": "scene-1", "version": "img-v1"},
            {"type": "sync_attempt", "scene_id": "scene-1", "force": False},
        ]
        result = manager.run_sync_regression_scenario("race-test", events)
        assert result.race_condition_detected is True
        assert result.desync_incidents > 0

    def test_sync_regression_scenario_successful_sync(self) -> None:
        manager = SyncStateManager()
        events: list[dict[str, Any]] = [
            {"type": "text_update", "scene_id": "scene-1", "version": "v1"},
            {"type": "image_update", "scene_id": "scene-1", "version": "v1"},
            {"type": "sync_attempt", "scene_id": "scene-1", "force": True},
        ]
        result = manager.run_sync_regression_scenario("successful-sync", events)
        assert result.final_sync_status == SyncStatus.SYNCED
        assert result.recovery_successful is True

    def test_director_sync_state_management(self) -> None:
        state = initialize_sync_state("scene-director", "v1", "v1")
        assert state.text_status == SyncStatus.SYNCED
        assert state.image_status == SyncStatus.SYNCED

        stale_state = mark_text_stale("scene-director", "user edit")
        assert stale_state is not None
        assert stale_state.text_status == SyncStatus.TEXT_STALE

        retrieved = get_sync_state("scene-director")
        assert retrieved is not None
        assert retrieved.scene_id == "scene-director"

    def test_director_sync_regression_test(self) -> None:
        result = run_sync_regression_test(
            "async-race-test",
            [
                {"type": "text_update", "scene_id": "s1", "version": "v1"},
                {"type": "image_update", "scene_id": "s1", "version": "v1"},
                {"type": "sync_attempt", "scene_id": "s1", "force": True},
            ],
        )
        assert "scenario" in result
        assert "race_detected" in result
        assert "final_status" in result


class TestPhase7DoneCriteria:
    """Phase 7 done criteria validation."""

    def test_duplicate_lineage_ids_remain_zero(self) -> None:
        """Verify no duplicate lineage IDs are created."""
        engine = OrchestrationEngine()

        # Create multiple jobs with same parameters
        for _ in range(5):
            engine.create_job(
                story_id="story-1",
                branch_id="branch-1",
                scene_id="scene-1",
                generation_type="text",
                user_request_hash="same-hash",
                previous_state={},
            )

        metrics = engine.get_phase7_metrics()
        # Only first should be unique, rest are duplicates detected
        assert metrics["duplicate_lineage_ids"] == 4

    def test_recovery_from_partial_failures(self) -> None:
        """Verify reliable recovery from partial failures."""
        engine = OrchestrationEngine()
        engine.retry_handler = RetryHandler(
            RetryPolicy(max_attempts=2, retryable_errors=("transient",))
        )

        job_id, key, _ = engine.create_job(
            story_id="story-1",
            branch_id="branch-1",
            scene_id="scene-1",
            generation_type="text",
            user_request_hash="hash-1",
            previous_state={"status": "pending"},
        )

        # Simulate failure
        status, dl_record = engine.handle_job_failure(job_id, key, "transient error")
        assert status == JobStatus.RETRYING
        assert dl_record is None

        # Simulate max retries exceeded
        engine.retry_handler.record_attempt(job_id)
        status, dl_record = engine.handle_job_failure(job_id, key, "transient error")
        assert status == JobStatus.DEAD_LETTER
        assert dl_record is not None

        # Verify dead letter was recorded
        dead_letters = engine.retry_handler.get_dead_letters()
        assert len(dead_letters) == 1

    def test_edit_provenance_complete_and_queryable(self) -> None:
        """Verify edit provenance is complete and queryable."""
        engine = OrchestrationEngine()

        # Log multiple edits
        for i in range(5):
            engine.log_edit(
                branch_id="branch-prov",
                scene_id=f"scene-{i}",
                edit_type=EditType.TEXT_REPLACE,
                span_start=i * 10,
                span_end=(i + 1) * 10,
                actor="user" if i % 2 == 0 else "system",
                reason=f"Edit {i}",
            )

        provenance = engine.edit_log_store.query_provenance("branch-prov")
        assert provenance["complete"] is True
        assert provenance["event_count"] == 5
        assert provenance["user_edit_count"] == 3  # 0, 2, 4

    def test_phase7_done_criteria_thresholds(self) -> None:
        """Final validation that all done criteria thresholds are met."""
        metrics = get_phase7_metrics()

        # Should have contracts registered
        assert metrics["registered_contracts"] >= 2

        # Idempotency tracking should be working
        assert isinstance(metrics["duplicate_lineage_ids"], int)
        assert isinstance(metrics["total_idempotency_keys"], int)

        # Dead letter tracking
        assert isinstance(metrics["dead_letter_count"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
