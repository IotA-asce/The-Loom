"""Orchestration engine for Phase 7: state integrity and edit provenance."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class JobStatus(Enum):
    """Job lifecycle states for transactional transitions."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


class EditType(Enum):
    """Types of edits tracked in the event-sourced log."""

    TEXT_INSERT = "text_insert"
    TEXT_DELETE = "text_delete"
    TEXT_REPLACE = "text_replace"
    PANEL_REDRAW = "panel_redraw"
    PANEL_REGENERATE = "panel_regenerate"
    SCENE_REORDER = "scene_reorder"
    BRANCH_DIVERGE = "branch_diverge"


class SyncStatus(Enum):
    """Cross-modal synchronization status."""

    SYNCED = "synced"
    TEXT_STALE = "text_stale"
    IMAGE_STALE = "image_stale"
    BOTH_STALE = "both_stale"
    RECONCILING = "reconciling"


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _clamp(value: float, *, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def _generate_idempotency_key(
    *,
    story_id: str,
    branch_id: str,
    scene_id: str,
    generation_type: str,
    user_request_hash: str,
) -> str:
    """Generate deterministic idempotency key for generation jobs."""
    material = (
        f"{story_id}|{branch_id}|{scene_id}|{generation_type}|{user_request_hash}"
    )
    return _sha256(material)[:32]


@dataclass(frozen=True)
class AgentContract:
    """Strict typed contract for agent inputs/outputs."""

    agent_name: str
    input_schema_version: str
    output_schema_version: str
    supported_model_versions: tuple[str, ...]
    supported_workflow_versions: tuple[str, ...]
    required_context_fields: tuple[str, ...]
    required_output_fields: tuple[str, ...]


@dataclass(frozen=True)
class ContractValidationResult:
    """Result of contract validation check."""

    valid: bool
    violations: tuple[str, ...]
    agent_name: str
    input_schema_match: bool
    output_schema_match: bool
    model_version_compatible: bool
    workflow_version_compatible: bool


@dataclass(frozen=True)
class CompatibilityMatrix:
    """Compatibility matrix for model and workflow versions."""

    matrix_id: str
    model_versions: tuple[str, ...]
    workflow_versions: tuple[str, ...]
    compatibilities: dict[tuple[str, str], bool]  # (model, workflow) -> compatible

    def is_compatible(self, model_version: str, workflow_version: str) -> bool:
        key = (model_version, workflow_version)
        return self.compatibilities.get(key, False)


@dataclass(frozen=True)
class IdempotencyRecord:
    """Tracked idempotency record for job deduplication."""

    idempotency_key: str
    story_id: str
    branch_id: str
    scene_id: str
    generation_type: str
    status: JobStatus
    result_reference: str | None
    created_at: str
    completed_at: str | None


@dataclass(frozen=True)
class TransactionRecord:
    """Transactional state transition record."""

    transaction_id: str
    branch_id: str
    version_id: str
    previous_state: dict[str, Any]
    new_state: dict[str, Any]
    transition_type: str
    timestamp: str
    committed: bool


@dataclass(frozen=True)
class RetryPolicy:
    """Bounded retry policy configuration."""

    max_attempts: int = 3
    backoff_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    max_backoff_seconds: float = 60.0
    retryable_errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class DeadLetterRecord:
    """Dead letter queue entry for failed jobs."""

    dead_letter_id: str
    original_job_id: str
    idempotency_key: str
    failure_reason: str
    failure_count: int
    final_error: str
    archived_at: str


@dataclass(frozen=True)
class EditEvent:
    """Single edit event in the event-sourced log."""

    edit_id: str
    branch_id: str
    scene_id: str
    edit_type: EditType
    span_start: int | None  # Character index for text, panel index for images
    span_end: int | None
    previous_content: str | None
    new_content: str | None
    panel_index: int | None  # For panel-specific edits
    actor: str  # "user" or "system"
    reason: str
    timestamp: str
    parent_edit_id: str | None
    regeneration_scope: tuple[str, ...]  # IDs of affected spans requiring regeneration


@dataclass(frozen=True)
class EditLog:
    """Event-sourced edit log for a branch."""

    branch_id: str
    events: tuple[EditEvent, ...]
    version_counter: int

    def append(self, event: EditEvent) -> EditLog:
        new_events = (*self.events, event)
        return replace(
            self, events=new_events, version_counter=self.version_counter + 1
        )

    def get_user_edits(self) -> tuple[EditEvent, ...]:
        return tuple(e for e in self.events if e.actor == "user")

    def get_regeneration_scope(
        self, from_event_id: str | None = None
    ) -> dict[str, tuple[int, int]]:
        """Get affected span ranges that need regeneration."""
        scope: dict[str, tuple[int, int]] = {}
        for event in self.events:
            if from_event_id and event.edit_id == from_event_id:
                break
            if event.span_start is not None and event.span_end is not None:
                key = f"{event.scene_id}:{event.panel_index or 'text'}"
                if key in scope:
                    existing = scope[key]
                    scope[key] = (
                        min(existing[0], event.span_start),
                        max(existing[1], event.span_end),
                    )
                else:
                    scope[key] = (event.span_start, event.span_end)
        return scope


@dataclass(frozen=True)
class RegenerationPlan:
    """Scoped regeneration plan derived from edit log."""

    branch_id: str
    source_edit_id: str
    affected_scenes: tuple[str, ...]
    affected_panels: dict[str, tuple[int, ...]]  # scene_id -> panel indices
    affected_text_spans: dict[str, tuple[tuple[int, int], ...]]  # scene_id -> spans
    preserve_user_edits: bool
    plan_timestamp: str


@dataclass(frozen=True)
class SharedVersionId:
    """Shared scene/version ID across text and image modalities."""

    scene_id: str
    text_version: str
    image_version: str
    combined_version: str
    created_at: str


@dataclass(frozen=True)
class SyncState:
    """Synchronization state for dual-view outputs."""

    scene_id: str
    shared_version: SharedVersionId
    text_status: SyncStatus
    image_status: SyncStatus
    stale_indicators: tuple[str, ...]
    reconcile_actions: tuple[str, ...]
    last_synced_at: str


@dataclass(frozen=True)
class SyncRegressionResult:
    """Result of sync regression test scenario."""

    scenario_name: str
    race_condition_detected: bool
    desync_incidents: int
    recovery_successful: bool
    final_sync_status: SyncStatus


@dataclass(frozen=True)
class OrchestrationResult:
    """Complete orchestration result with all Phase 7 metadata."""

    job_id: str
    idempotency_key: str
    branch_id: str
    scene_id: str
    status: JobStatus
    lineage_id: str
    duplicate_prevented: bool
    transaction_record: TransactionRecord
    edit_log: EditLog
    sync_state: SyncState
    retry_count: int
    dead_lettered: bool
    metadata: dict[str, str]


class ContractRegistry:
    """Registry of strict agent contracts with validation."""

    def __init__(self) -> None:
        self._contracts: dict[str, AgentContract] = {}
        self._compatibility_matrix: CompatibilityMatrix | None = None

    def register_contract(self, contract: AgentContract) -> None:
        self._contracts[contract.agent_name] = contract

    def get_contract(self, agent_name: str) -> AgentContract | None:
        return self._contracts.get(agent_name)

    def set_compatibility_matrix(self, matrix: CompatibilityMatrix) -> None:
        self._compatibility_matrix = matrix

    def validate_input(
        self,
        agent_name: str,
        input_data: dict[str, Any],
        model_version: str,
        workflow_version: str,
    ) -> ContractValidationResult:
        contract = self._contracts.get(agent_name)
        if contract is None:
            return ContractValidationResult(
                valid=False,
                violations=(f"No contract registered for agent '{agent_name}'",),
                agent_name=agent_name,
                input_schema_match=False,
                output_schema_match=False,
                model_version_compatible=False,
                workflow_version_compatible=False,
            )

        violations: list[str] = []

        # Check required fields
        for field_name in contract.required_context_fields:
            if field_name not in input_data:
                violations.append(f"Missing required field: {field_name}")

        input_schema_match = True  # Simplified - would validate against schema

        # Check compatibility matrix
        matrix = self._compatibility_matrix
        model_compatible = True
        workflow_compatible = True
        if matrix is not None:
            model_compatible = model_version in matrix.model_versions
            workflow_compatible = workflow_version in matrix.workflow_versions
            if not matrix.is_compatible(model_version, workflow_version):
                violations.append(
                    f"Incompatible model {model_version} "
                    f"with workflow {workflow_version}"
                )

        return ContractValidationResult(
            valid=len(violations) == 0,
            violations=tuple(violations),
            agent_name=agent_name,
            input_schema_match=input_schema_match,
            output_schema_match=True,  # Would validate output separately
            model_version_compatible=model_compatible,
            workflow_version_compatible=workflow_compatible,
        )

    def list_contracts(self) -> tuple[AgentContract, ...]:
        return tuple(self._contracts.values())


class IdempotencyStore:
    """Store for idempotency keys with deduplication logic."""

    def __init__(self) -> None:
        self._records: dict[str, IdempotencyRecord] = {}
        self._duplicate_count: int = 0

    def check_or_create(
        self,
        *,
        story_id: str,
        branch_id: str,
        scene_id: str,
        generation_type: str,
        user_request_hash: str,
    ) -> tuple[str, bool]:
        """Check for existing idempotency key. Returns (key, is_duplicate)."""
        key = _generate_idempotency_key(
            story_id=story_id,
            branch_id=branch_id,
            scene_id=scene_id,
            generation_type=generation_type,
            user_request_hash=user_request_hash,
        )

        if key in self._records:
            self._duplicate_count += 1
            return key, True

        record = IdempotencyRecord(
            idempotency_key=key,
            story_id=story_id,
            branch_id=branch_id,
            scene_id=scene_id,
            generation_type=generation_type,
            status=JobStatus.PENDING,
            result_reference=None,
            created_at=_timestamp(),
            completed_at=None,
        )
        self._records[key] = record
        return key, False

    def update_status(
        self,
        idempotency_key: str,
        status: JobStatus,
        result_reference: str | None = None,
    ) -> None:
        record = self._records.get(idempotency_key)
        if record is not None:
            terminal = (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.DEAD_LETTER)
            completed_at = _timestamp() if status in terminal else None
            self._records[idempotency_key] = replace(
                record,
                status=status,
                result_reference=result_reference,
                completed_at=completed_at,
            )

    def get_record(self, idempotency_key: str) -> IdempotencyRecord | None:
        return self._records.get(idempotency_key)

    def duplicate_lineage_count(self) -> int:
        return self._duplicate_count

    def get_all_keys(self) -> tuple[str, ...]:
        return tuple(self._records.keys())


class TransactionLog:
    """Transactional state transition log per branch version."""

    def __init__(self) -> None:
        self._transactions: dict[str, list[TransactionRecord]] = {}

    def begin_transaction(
        self,
        branch_id: str,
        version_id: str,
        previous_state: dict[str, Any],
        transition_type: str,
    ) -> TransactionRecord:
        transaction_id = _sha256(f"{branch_id}|{version_id}|{_timestamp()}")[:16]
        record = TransactionRecord(
            transaction_id=transaction_id,
            branch_id=branch_id,
            version_id=version_id,
            previous_state=previous_state,
            new_state={},  # Will be filled on commit
            transition_type=transition_type,
            timestamp=_timestamp(),
            committed=False,
        )
        self._transactions.setdefault(branch_id, []).append(record)
        return record

    def commit_transaction(
        self,
        transaction_id: str,
        new_state: dict[str, Any],
    ) -> bool:
        for branch_transactions in self._transactions.values():
            for i, record in enumerate(branch_transactions):
                if record.transaction_id == transaction_id:
                    branch_transactions[i] = replace(
                        record, new_state=new_state, committed=True
                    )
                    return True
        return False

    def get_branch_history(self, branch_id: str) -> tuple[TransactionRecord, ...]:
        return tuple(self._transactions.get(branch_id, []))

    def get_latest_version(self, branch_id: str) -> str | None:
        history = self._transactions.get(branch_id, [])
        if not history:
            return None
        return history[-1].version_id


class RetryHandler:
    """Bounded retry policy handler with dead-letter support."""

    def __init__(self, policy: RetryPolicy | None = None) -> None:
        self._policy = policy or RetryPolicy()
        self._attempt_counts: dict[str, int] = {}
        self._dead_letter_queue: list[DeadLetterRecord] = []

    def should_retry(self, job_id: str, error: str) -> bool:
        count = self._attempt_counts.get(job_id, 0)
        if count >= self._policy.max_attempts:
            return False
        if self._policy.retryable_errors:
            if not any(pattern in error for pattern in self._policy.retryable_errors):
                return False
        return True

    def record_attempt(self, job_id: str) -> int:
        count = self._attempt_counts.get(job_id, 0) + 1
        self._attempt_counts[job_id] = count
        return count

    def send_to_dead_letter(
        self,
        job_id: str,
        idempotency_key: str,
        error: str,
    ) -> DeadLetterRecord:
        record = DeadLetterRecord(
            dead_letter_id=_sha256(f"dl:{job_id}:{_timestamp()}")[:16],
            original_job_id=job_id,
            idempotency_key=idempotency_key,
            failure_reason="max_retries_exceeded",
            failure_count=self._attempt_counts.get(job_id, 0),
            final_error=error,
            archived_at=_timestamp(),
        )
        self._dead_letter_queue.append(record)
        return record

    def get_dead_letters(self) -> tuple[DeadLetterRecord, ...]:
        return tuple(self._dead_letter_queue)

    def get_backoff_seconds(self, attempt: int) -> float:
        backoff = self._policy.backoff_seconds * (
            self._policy.backoff_multiplier ** (attempt - 1)
        )
        return min(backoff, self._policy.max_backoff_seconds)


class EditLogStore:
    """Event-sourced edit log store for text and panels."""

    def __init__(self) -> None:
        self._logs: dict[str, EditLog] = {}

    def get_or_create_log(self, branch_id: str) -> EditLog:
        if branch_id not in self._logs:
            self._logs[branch_id] = EditLog(
                branch_id=branch_id, events=(), version_counter=0
            )
        return self._logs[branch_id]

    def append_edit(
        self,
        branch_id: str,
        scene_id: str,
        edit_type: EditType,
        *,
        span_start: int | None = None,
        span_end: int | None = None,
        previous_content: str | None = None,
        new_content: str | None = None,
        panel_index: int | None = None,
        actor: str = "user",
        reason: str = "",
        parent_edit_id: str | None = None,
        regeneration_scope: tuple[str, ...] = (),
    ) -> EditEvent:
        log = self.get_or_create_log(branch_id)
        edit_id = f"edit:{branch_id}:{log.version_counter:06d}"

        event = EditEvent(
            edit_id=edit_id,
            branch_id=branch_id,
            scene_id=scene_id,
            edit_type=edit_type,
            span_start=span_start,
            span_end=span_end,
            previous_content=previous_content,
            new_content=new_content,
            panel_index=panel_index,
            actor=actor,
            reason=reason,
            timestamp=_timestamp(),
            parent_edit_id=parent_edit_id,
            regeneration_scope=regeneration_scope,
        )

        self._logs[branch_id] = log.append(event)
        return event

    def get_log(self, branch_id: str) -> EditLog | None:
        return self._logs.get(branch_id)

    def create_regeneration_plan(
        self,
        branch_id: str,
        source_edit_id: str,
    ) -> RegenerationPlan:
        log = self._logs.get(branch_id)
        if log is None:
            return RegenerationPlan(
                branch_id=branch_id,
                source_edit_id=source_edit_id,
                affected_scenes=(),
                affected_panels={},
                affected_text_spans={},
                preserve_user_edits=True,
                plan_timestamp=_timestamp(),
            )

        affected_scenes: set[str] = set()
        affected_panels: dict[str, list[int]] = {}
        affected_text_spans: dict[str, list[tuple[int, int]]] = {}

        # Collect all affected scenes from events up to and including source_edit_id
        for event in log.events:
            affected_scenes.add(event.scene_id)

            if event.panel_index is not None:
                affected_panels.setdefault(event.scene_id, []).append(event.panel_index)
            elif event.span_start is not None and event.span_end is not None:
                affected_text_spans.setdefault(event.scene_id, []).append(
                    (event.span_start, event.span_end)
                )

        # Check if there are user edits that should be preserved
        user_edits_after = [
            e
            for e in log.events
            if e.actor == "user"
            and (source_edit_id is None or e.edit_id > source_edit_id)
        ]
        preserve_user_edits = len(user_edits_after) > 0

        return RegenerationPlan(
            branch_id=branch_id,
            source_edit_id=source_edit_id,
            affected_scenes=tuple(affected_scenes),
            affected_panels={k: tuple(v) for k, v in affected_panels.items()},
            affected_text_spans={k: tuple(v) for k, v in affected_text_spans.items()},
            preserve_user_edits=preserve_user_edits,
            plan_timestamp=_timestamp(),
        )

    def log_count(self) -> int:
        """Return number of tracked edit logs."""
        return len(self._logs)

    def query_provenance(self, branch_id: str) -> dict[str, Any]:
        """Query complete edit provenance for a branch."""
        log = self._logs.get(branch_id)
        if log is None:
            return {"branch_id": branch_id, "events": [], "complete": True}

        return {
            "branch_id": branch_id,
            "event_count": len(log.events),
            "version_counter": log.version_counter,
            "user_edit_count": len(log.get_user_edits()),
            "events": [
                {
                    "edit_id": e.edit_id,
                    "type": e.edit_type.value,
                    "scene": e.scene_id,
                    "actor": e.actor,
                    "timestamp": e.timestamp,
                }
                for e in log.events
            ],
            "complete": True,
        }


class SyncStateManager:
    """Manages synchronization state for dual-view (text + image) outputs."""

    def __init__(self) -> None:
        self._sync_states: dict[str, SyncState] = {}
        self._version_counter: int = 0

    def create_shared_version(
        self,
        scene_id: str,
        text_version: str,
        image_version: str,
    ) -> SharedVersionId:
        self._version_counter += 1
        return SharedVersionId(
            scene_id=scene_id,
            text_version=text_version,
            image_version=image_version,
            combined_version=f"v{self._version_counter:06d}",
            created_at=_timestamp(),
        )

    def update_sync_state(
        self,
        scene_id: str,
        shared_version: SharedVersionId,
        text_status: SyncStatus,
        image_status: SyncStatus,
        stale_indicators: tuple[str, ...] = (),
        reconcile_actions: tuple[str, ...] = (),
    ) -> SyncState:
        state = SyncState(
            scene_id=scene_id,
            shared_version=shared_version,
            text_status=text_status,
            image_status=image_status,
            stale_indicators=stale_indicators,
            reconcile_actions=reconcile_actions,
            last_synced_at=_timestamp(),
        )
        self._sync_states[scene_id] = state
        return state

    def get_sync_state(self, scene_id: str) -> SyncState | None:
        return self._sync_states.get(scene_id)

    def mark_stale(
        self,
        scene_id: str,
        modality: str,  # "text" or "image"
        reason: str,
    ) -> SyncState | None:
        state = self._sync_states.get(scene_id)
        if state is None:
            return None

        stale_indicators = (*state.stale_indicators, f"{modality}:{reason}")

        if modality == "text":
            # Check if image is already stale
            if state.image_status in (SyncStatus.IMAGE_STALE, SyncStatus.BOTH_STALE):
                new_text_status = SyncStatus.BOTH_STALE
                new_image_status = SyncStatus.BOTH_STALE
            else:
                new_text_status = SyncStatus.TEXT_STALE
                new_image_status = state.image_status
        elif modality == "image":
            # Check if text is already stale
            if state.text_status in (SyncStatus.TEXT_STALE, SyncStatus.BOTH_STALE):
                new_text_status = SyncStatus.BOTH_STALE
                new_image_status = SyncStatus.BOTH_STALE
            else:
                new_text_status = state.text_status
                new_image_status = SyncStatus.IMAGE_STALE
        else:
            return state

        return self.update_sync_state(
            scene_id=scene_id,
            shared_version=state.shared_version,
            text_status=new_text_status,
            image_status=new_image_status,
            stale_indicators=stale_indicators,
        )

    def run_sync_regression_scenario(
        self,
        scenario_name: str,
        events: list[dict[str, Any]],
    ) -> SyncRegressionResult:
        """Run a sync regression test scenario for async race conditions."""
        desync_count = 0
        race_detected = False
        recovery_success = True

        # Simulate event sequence
        scene_states: dict[str, dict[str, Any]] = {}

        for event in events:
            scene_id = event.get("scene_id", "default")
            event_type = event.get("type", "unknown")

            if scene_id not in scene_states:
                scene_states[scene_id] = {
                    "text_version": "v0",
                    "image_version": "v0",
                    "synced": True,
                }

            state = scene_states[scene_id]

            if event_type == "text_update":
                if not state["synced"]:
                    desync_count += 1
                state["text_version"] = event.get("version", "v1")
                state["synced"] = False

            elif event_type == "image_update":
                if not state["synced"]:
                    desync_count += 1
                state["image_version"] = event.get("version", "v1")
                state["synced"] = False

            elif event_type == "sync_attempt":
                if state["text_version"] != state["image_version"]:
                    race_detected = True
                    if event.get("force", False):
                        state["synced"] = True
                    else:
                        recovery_success = False
                else:
                    state["synced"] = True

        final_status = (
            SyncStatus.SYNCED
            if all(s["synced"] for s in scene_states.values())
            else SyncStatus.BOTH_STALE
        )

        return SyncRegressionResult(
            scenario_name=scenario_name,
            race_condition_detected=race_detected,
            desync_incidents=desync_count,
            recovery_successful=recovery_success,
            final_sync_status=final_status,
        )


class OrchestrationEngine:
    """Main orchestration engine for Phase 7 goals."""

    def __init__(self) -> None:
        self.contract_registry = ContractRegistry()
        self.idempotency_store = IdempotencyStore()
        self.transaction_log = TransactionLog()
        self.retry_handler = RetryHandler()
        self.edit_log_store = EditLogStore()
        self.sync_manager = SyncStateManager()

    def register_agent_contract(self, contract: AgentContract) -> None:
        """G7.1: Define strict typed contracts for all agent inputs/outputs."""
        self.contract_registry.register_contract(contract)

    def set_compatibility_matrix(self, matrix: CompatibilityMatrix) -> None:
        """G7.1: Add compatibility matrix for model and workflow versions."""
        self.contract_registry.set_compatibility_matrix(matrix)

    def validate_contract(
        self,
        agent_name: str,
        input_data: dict[str, Any],
        model_version: str,
        workflow_version: str,
    ) -> ContractValidationResult:
        """G7.1: Contract test validation."""
        return self.contract_registry.validate_input(
            agent_name, input_data, model_version, workflow_version
        )

    def create_job(
        self,
        *,
        story_id: str,
        branch_id: str,
        scene_id: str,
        generation_type: str,
        user_request_hash: str,
        previous_state: dict[str, Any],
    ) -> tuple[str, str, bool]:
        """G7.2: Create generation job with idempotency key and transactional state.

        Returns (job_id, idempotency_key, is_duplicate).
        """
        key, is_duplicate = self.idempotency_store.check_or_create(
            story_id=story_id,
            branch_id=branch_id,
            scene_id=scene_id,
            generation_type=generation_type,
            user_request_hash=user_request_hash,
        )

        job_id = _sha256(f"job:{key}:{_timestamp()}")[:16]

        # Begin transaction for state transition
        history_len = len(self.transaction_log.get_branch_history(branch_id))
        version_id = f"v{history_len + 1:04d}"
        self.transaction_log.begin_transaction(
            branch_id=branch_id,
            version_id=version_id,
            previous_state=previous_state,
            transition_type=f"{generation_type}_start",
        )

        self.idempotency_store.update_status(key, JobStatus.RUNNING)

        return job_id, key, is_duplicate

    def complete_job(
        self,
        job_id: str,
        idempotency_key: str,
        new_state: dict[str, Any],
        success: bool = True,
    ) -> TransactionRecord | None:
        """G7.2: Complete job with transactional state commit."""
        status = JobStatus.COMPLETED if success else JobStatus.FAILED
        self.idempotency_store.update_status(
            idempotency_key, status, result_reference=job_id
        )

        # Find and commit the transaction
        branch_id = self.idempotency_store.get_record(idempotency_key)
        if branch_id:
            history = self.transaction_log.get_branch_history(branch_id.branch_id)
            for record in history:
                if not record.committed:
                    if self.transaction_log.commit_transaction(
                        record.transaction_id, new_state
                    ):
                        return replace(record, new_state=new_state, committed=True)
        return None

    def handle_job_failure(
        self,
        job_id: str,
        idempotency_key: str,
        error: str,
    ) -> tuple[JobStatus, DeadLetterRecord | None]:
        """G7.2: Handle job failure with bounded retry and dead-letter."""
        if self.retry_handler.should_retry(job_id, error):
            self.retry_handler.record_attempt(job_id)
            self.idempotency_store.update_status(idempotency_key, JobStatus.RETRYING)
            return JobStatus.RETRYING, None
        else:
            # Send to dead letter queue
            dl_record = self.retry_handler.send_to_dead_letter(
                job_id, idempotency_key, error
            )
            self.idempotency_store.update_status(idempotency_key, JobStatus.DEAD_LETTER)
            return JobStatus.DEAD_LETTER, dl_record

    def log_edit(
        self,
        branch_id: str,
        scene_id: str,
        edit_type: EditType,
        **kwargs: Any,
    ) -> EditEvent:
        """G7.3: Log edit event in event-sourced edit log."""
        return self.edit_log_store.append_edit(
            branch_id=branch_id,
            scene_id=scene_id,
            edit_type=edit_type,
            **kwargs,
        )

    def create_regeneration_plan(
        self,
        branch_id: str,
        source_edit_id: str,
    ) -> RegenerationPlan:
        """G7.3: Scope regeneration to affected spans/panels."""
        return self.edit_log_store.create_regeneration_plan(branch_id, source_edit_id)

    def check_user_edit_protection(self, branch_id: str, span_id: str) -> bool:
        """G7.3: Check if user edits would be overwritten by regeneration."""
        log = self.edit_log_store.get_log(branch_id)
        if log is None:
            return False

        # Check for user edits in the affected span
        for event in log.events:
            if event.actor == "user" and span_id in event.regeneration_scope:
                return True
        return False

    def create_sync_state(
        self,
        scene_id: str,
        text_version: str,
        image_version: str,
    ) -> SyncState:
        """G7.4: Create shared scene/version IDs across modalities."""
        shared_version = self.sync_manager.create_shared_version(
            scene_id, text_version, image_version
        )
        return self.sync_manager.update_sync_state(
            scene_id=scene_id,
            shared_version=shared_version,
            text_status=SyncStatus.SYNCED,
            image_status=SyncStatus.SYNCED,
        )

    def mark_stale(self, scene_id: str, modality: str, reason: str) -> SyncState | None:
        """G7.4: Add stale-state indicators."""
        return self.sync_manager.mark_stale(scene_id, modality, reason)

    def get_sync_state(self, scene_id: str) -> SyncState | None:
        """G7.4: Get current sync state."""
        return self.sync_manager.get_sync_state(scene_id)

    def run_sync_regression_test(
        self,
        scenario_name: str,
        events: list[dict[str, Any]],
    ) -> SyncRegressionResult:
        """G7.4: Add sync regression tests for async race scenarios."""
        return self.sync_manager.run_sync_regression_scenario(scenario_name, events)

    def get_phase7_metrics(self) -> dict[str, Any]:
        """Get Phase 7 done criteria metrics."""
        return {
            "duplicate_lineage_ids": self.idempotency_store.duplicate_lineage_count(),
            "total_idempotency_keys": len(self.idempotency_store.get_all_keys()),
            "dead_letter_count": len(self.retry_handler.get_dead_letters()),
            "registered_contracts": len(self.contract_registry.list_contracts()),
            "edit_logs": self.edit_log_store.log_count(),
        }


# Convenience exports for agent usage
__all__ = [
    "AgentContract",
    "CompatibilityMatrix",
    "ContractRegistry",
    "ContractValidationResult",
    "DeadLetterRecord",
    "EditEvent",
    "EditLog",
    "EditLogStore",
    "EditType",
    "IdempotencyRecord",
    "IdempotencyStore",
    "JobStatus",
    "OrchestrationEngine",
    "OrchestrationResult",
    "RegenerationPlan",
    "RetryHandler",
    "RetryPolicy",
    "SharedVersionId",
    "SyncRegressionResult",
    "SyncState",
    "SyncStateManager",
    "SyncStatus",
    "TransactionLog",
    "TransactionRecord",
]
