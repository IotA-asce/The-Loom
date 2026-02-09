"""Director agent for coordinating writer and artist runs with Phase 7 orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.image_generation_engine import ArtistResult
from core.orchestration_engine import (
    AgentContract,
    CompatibilityMatrix,
    EditType,
    JobStatus,
    OrchestrationEngine,
    RegenerationPlan,
    RetryHandler,
    RetryPolicy,
    SharedVersionId,
    SyncState,
)
from core.text_generation_engine import WriterResult


@dataclass(frozen=True)
class GenerationPlan:
    """Generation plan with Phase 7 metadata."""

    branch_id: str
    scene_id: str
    include_text: bool
    include_images: bool
    version_id: str
    idempotency_key: str
    job_id: str
    is_duplicate: bool = False


@dataclass(frozen=True)
class DualGenerationResult:
    """Combined text and image generation result with sync state."""

    job_id: str
    branch_id: str
    scene_id: str
    text_result: WriterResult | None
    image_result: ArtistResult | None
    sync_state: SyncState
    shared_version: SharedVersionId
    status: JobStatus
    edit_log_id: str
    metadata: dict[str, str]


@dataclass
class DirectorState:
    """Internal director state tracking."""

    orchestration: OrchestrationEngine = field(default_factory=OrchestrationEngine)
    contract_initialized: bool = False


_STATE = DirectorState()


def initialize_contracts() -> None:
    """G7.1: Define strict typed contracts for all agent inputs/outputs."""
    if _STATE.contract_initialized:
        return

    # Writer agent contract
    writer_contract = AgentContract(
        agent_name="writer",
        input_schema_version="writer-request-v1",
        output_schema_version="writer-result-v1",
        supported_model_versions=("llama-3", "mistral-v0.3", "gpt-4"),
        supported_workflow_versions=("text-gen-v1", "text-gen-v2"),
        required_context_fields=(
            "story_id",
            "branch_id",
            "user_prompt",
        ),
        required_output_fields=(
            "branch_id",
            "text",
            "prompt_version",
            "style_similarity",
        ),
    )

    # Artist agent contract
    artist_contract = AgentContract(
        agent_name="artist",
        input_schema_version="artist-request-v1",
        output_schema_version="artist-result-v1",
        supported_model_versions=("sd-controlnet-v1", "flux-v1"),
        supported_workflow_versions=("image-gen-v1", "manga-seq-v2"),
        required_context_fields=(
            "story_id",
            "branch_id",
            "scene_prompt",
        ),
        required_output_fields=(
            "branch_id",
            "image_count",
            "panels",
            "continuity_score",
        ),
    )

    _STATE.orchestration.register_agent_contract(writer_contract)
    _STATE.orchestration.register_agent_contract(artist_contract)

    # Set compatibility matrix
    matrix = CompatibilityMatrix(
        matrix_id="loom-compat-v1",
        model_versions=(
            "llama-3",
            "mistral-v0.3",
            "gpt-4",
            "sd-controlnet-v1",
            "flux-v1",
        ),
        workflow_versions=(
            "text-gen-v1",
            "text-gen-v2",
            "image-gen-v1",
            "manga-seq-v2",
        ),
        compatibilities={
            ("llama-3", "text-gen-v1"): True,
            ("llama-3", "text-gen-v2"): True,
            ("mistral-v0.3", "text-gen-v1"): True,
            ("mistral-v0.3", "text-gen-v2"): True,
            ("gpt-4", "text-gen-v1"): True,
            ("gpt-4", "text-gen-v2"): True,
            ("sd-controlnet-v1", "image-gen-v1"): True,
            ("sd-controlnet-v1", "manga-seq-v2"): True,
            ("flux-v1", "image-gen-v1"): True,
            ("flux-v1", "manga-seq-v2"): True,
            # Cross-model incompatibilities
            ("llama-3", "image-gen-v1"): False,
            ("sd-controlnet-v1", "text-gen-v1"): False,
        },
    )
    _STATE.orchestration.set_compatibility_matrix(matrix)
    _STATE.contract_initialized = True


def validate_agent_contract(
    agent_name: str,
    input_data: dict[str, Any],
    model_version: str,
    workflow_version: str,
) -> bool:
    """G7.1: Validate agent contract before execution."""
    initialize_contracts()
    result = _STATE.orchestration.validate_contract(
        agent_name, input_data, model_version, workflow_version
    )
    return result.valid


def get_compatibility_matrix() -> CompatibilityMatrix | None:
    """G7.1: Get the current compatibility matrix."""
    initialize_contracts()
    return _STATE.orchestration.contract_registry._compatibility_matrix


def create_generation_plan(
    branch_id: str,
    scene_id: str = "default",
    *,
    include_text: bool = True,
    include_images: bool = True,
    story_id: str = "default-story",
    user_request_hash: str = "",
) -> GenerationPlan:
    """Create a generation plan with idempotency key."""
    initialize_contracts()

    gen_type = (
        "dual"
        if (include_text and include_images)
        else ("text" if include_text else "image")
    )
    req_hash = user_request_hash or f"{branch_id}:{scene_id}"
    prev_state = {"status": "pending", "branch_id": branch_id}
    job_id, idempotency_key, is_duplicate = _STATE.orchestration.create_job(
        story_id=story_id,
        branch_id=branch_id,
        scene_id=scene_id,
        generation_type=gen_type,
        user_request_hash=req_hash,
        previous_state=prev_state,
    )

    return GenerationPlan(
        branch_id=branch_id,
        scene_id=scene_id,
        include_text=include_text,
        include_images=include_images,
        version_id=f"v{_timestamp_counter():04d}",
        idempotency_key=idempotency_key,
        job_id=job_id,
        is_duplicate=is_duplicate,
    )


_counter: int = 0


def _timestamp_counter() -> int:
    global _counter
    _counter += 1
    return _counter


def log_text_edit(
    branch_id: str,
    scene_id: str,
    span_start: int,
    span_end: int,
    previous_content: str,
    new_content: str,
    *,
    actor: str = "user",
    reason: str = "",
) -> None:
    """G7.3: Log text edit in event-sourced edit log."""
    initialize_contracts()
    _STATE.orchestration.log_edit(
        branch_id=branch_id,
        scene_id=scene_id,
        edit_type=EditType.TEXT_REPLACE,
        span_start=span_start,
        span_end=span_end,
        previous_content=previous_content,
        new_content=new_content,
        actor=actor,
        reason=reason,
        regeneration_scope=(f"{scene_id}:text",),
    )


def log_panel_redraw(
    branch_id: str,
    scene_id: str,
    panel_index: int,
    *,
    actor: str = "user",
    reason: str = "",
) -> None:
    """G7.3: Log panel redraw request."""
    initialize_contracts()
    _STATE.orchestration.log_edit(
        branch_id=branch_id,
        scene_id=scene_id,
        edit_type=EditType.PANEL_REDRAW,
        panel_index=panel_index,
        actor=actor,
        reason=reason,
        regeneration_scope=(f"{scene_id}:panel-{panel_index}",),
    )


def create_regeneration_plan(branch_id: str, source_edit_id: str) -> RegenerationPlan:
    """G7.3: Create scoped regeneration plan from edit log."""
    initialize_contracts()
    return _STATE.orchestration.create_regeneration_plan(branch_id, source_edit_id)


def check_edit_protection(branch_id: str, span_id: str) -> bool:
    """G7.3: Check if user edits would be overwritten."""
    initialize_contracts()
    return _STATE.orchestration.check_user_edit_protection(branch_id, span_id)


def initialize_sync_state(
    scene_id: str,
    text_version: str = "v0",
    image_version: str = "v0",
) -> SyncState:
    """G7.4: Initialize sync state for dual-view."""
    initialize_contracts()
    return _STATE.orchestration.create_sync_state(scene_id, text_version, image_version)


def mark_text_stale(scene_id: str, reason: str) -> SyncState | None:
    """G7.4: Mark text as stale in dual-view."""
    initialize_contracts()
    return _STATE.orchestration.mark_stale(scene_id, "text", reason)


def mark_image_stale(scene_id: str, reason: str) -> SyncState | None:
    """G7.4: Mark images as stale in dual-view."""
    initialize_contracts()
    return _STATE.orchestration.mark_stale(scene_id, "image", reason)


def get_sync_state(scene_id: str) -> SyncState | None:
    """G7.4: Get current sync state."""
    initialize_contracts()
    return _STATE.orchestration.get_sync_state(scene_id)


def run_sync_regression_test(
    scenario_name: str,
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    """G7.4: Run sync regression test for async race scenarios."""
    initialize_contracts()
    result = _STATE.orchestration.run_sync_regression_test(scenario_name, events)
    return {
        "scenario": result.scenario_name,
        "race_detected": result.race_condition_detected,
        "desync_incidents": result.desync_incidents,
        "recovery_successful": result.recovery_successful,
        "final_status": result.final_sync_status.value,
    }


def get_edit_provenance(branch_id: str) -> dict[str, Any]:
    """G7.3: Query complete edit provenance for a branch."""
    initialize_contracts()
    return _STATE.orchestration.edit_log_store.query_provenance(branch_id)


def get_phase7_metrics() -> dict[str, Any]:
    """Get Phase 7 done criteria metrics."""
    initialize_contracts()
    return _STATE.orchestration.get_phase7_metrics()


def set_retry_policy(
    max_attempts: int = 3,
    backoff_seconds: float = 1.0,
    backoff_multiplier: float = 2.0,
) -> None:
    """G7.2: Configure bounded retry policy."""
    initialize_contracts()
    policy = RetryPolicy(
        max_attempts=max_attempts,
        backoff_seconds=backoff_seconds,
        backoff_multiplier=backoff_multiplier,
    )
    _STATE.orchestration.retry_handler = RetryHandler(policy)


__all__ = [
    "DualGenerationResult",
    "GenerationPlan",
    "check_edit_protection",
    "create_generation_plan",
    "create_regeneration_plan",
    "get_compatibility_matrix",
    "get_edit_provenance",
    "get_phase7_metrics",
    "get_sync_state",
    "initialize_contracts",
    "initialize_sync_state",
    "log_panel_redraw",
    "log_text_edit",
    "mark_image_stale",
    "mark_text_stale",
    "run_sync_regression_test",
    "set_retry_policy",
    "validate_agent_contract",
]
