"""Operations, security, and governance engine for Phase 9."""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _generate_id() -> str:
    return uuid.uuid4().hex[:16]


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    return max(min_val, min(max_val, value))


# =============================================================================
# G9.1 Observability and SLOs
# =============================================================================


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Component(Enum):
    INGESTION = "ingestion"
    RETRIEVAL = "retrieval"
    GENERATION = "generation"
    ORCHESTRATION = "orchestration"
    FRONTEND = "frontend"


@dataclass(frozen=True)
class StructuredLogEntry:
    """Structured log entry with correlation IDs."""

    timestamp: str
    level: LogLevel
    component: Component
    message: str
    request_id: str | None = None
    job_id: str | None = None
    branch_id: str | None = None
    correlation_id: str | None = None
    context: dict[str, str] = field(default_factory=dict)
    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None


@dataclass(frozen=True)
class TraceSpan:
    """Distributed trace span."""

    trace_id: str
    span_id: str
    parent_span_id: str | None
    operation: str
    component: Component
    start_time: str
    end_time: str | None = None
    status: str = "ok"
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SLODefinition:
    """Service Level Objective definition."""

    name: str
    description: str
    target: float  # 0.0 - 1.0
    threshold: float  # e.g., latency in ms, error rate as decimal
    window_minutes: int
    metric_type: str  # "latency", "availability", "success_rate"


@dataclass(frozen=True)
class SLOMeasurement:
    """SLO measurement result."""

    slo_name: str
    measured_value: float
    target_value: float
    is_breached: bool
    window_start: str
    window_end: str
    sample_count: int


DEFAULT_SLOS: tuple[SLODefinition, ...] = (
    SLODefinition(
        name="ingestion_latency",
        description="P95 ingestion processing latency",
        target=0.95,
        threshold=5000.0,  # 5 seconds
        window_minutes=60,
        metric_type="latency",
    ),
    SLODefinition(
        name="retrieval_latency",
        description="P95 retrieval query latency",
        target=0.95,
        threshold=200.0,  # 200ms
        window_minutes=60,
        metric_type="latency",
    ),
    SLODefinition(
        name="generation_success_rate",
        description="Generation job success rate",
        target=0.99,
        threshold=0.99,
        window_minutes=60,
        metric_type="success_rate",
    ),
    SLODefinition(
        name="sync_success_rate",
        description="Dual-view sync success rate",
        target=0.995,
        threshold=0.995,
        window_minutes=60,
        metric_type="success_rate",
    ),
)


class ObservabilityManager:
    """G9.1: Structured logging, tracing, and SLO monitoring."""

    def __init__(self) -> None:
        self._logs: list[StructuredLogEntry] = []
        self._spans: list[TraceSpan] = []
        self._active_spans: dict[str, TraceSpan] = {}
        self._slo_definitions: dict[str, SLODefinition] = {
            slo.name: slo for slo in DEFAULT_SLOS
        }
        self._slo_measurements: dict[str, list[SLOMeasurement]] = {
            slo.name: [] for slo in DEFAULT_SLOS
        }
        self._latency_samples: dict[str, list[tuple[str, float]]] = {
            slo.name: [] for slo in DEFAULT_SLOS
        }

    def log(
        self,
        level: LogLevel,
        component: Component,
        message: str,
        *,
        request_id: str | None = None,
        job_id: str | None = None,
        branch_id: str | None = None,
        context: dict[str, str] | None = None,
    ) -> StructuredLogEntry:
        """Emit a structured log entry."""
        # Generate correlation ID from available IDs
        correlation_id = request_id or job_id or branch_id or _generate_id()

        # Get current trace context if available
        trace_id = None
        span_id = None
        parent_span_id = None
        if self._active_spans:
            # Use most recent active span
            latest_span = list(self._active_spans.values())[-1]
            trace_id = latest_span.trace_id
            span_id = latest_span.span_id
            parent_span_id = latest_span.parent_span_id

        entry = StructuredLogEntry(
            timestamp=_timestamp(),
            level=level,
            component=component,
            message=message,
            request_id=request_id,
            job_id=job_id,
            branch_id=branch_id,
            correlation_id=correlation_id,
            context=context or {},
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
        )
        self._logs.append(entry)
        return entry

    def start_span(
        self,
        operation: str,
        component: Component,
        parent_span_id: str | None = None,
        attributes: dict[str, str] | None = None,
    ) -> TraceSpan:
        """Start a new trace span."""
        trace_id = _generate_id() if parent_span_id is None else None
        if parent_span_id and self._active_spans:
            # Find parent to get trace_id
            for span in self._active_spans.values():
                if span.span_id == parent_span_id:
                    trace_id = span.trace_id
                    break

        if trace_id is None:
            trace_id = _generate_id()

        span = TraceSpan(
            trace_id=trace_id,
            span_id=_generate_id(),
            parent_span_id=parent_span_id,
            operation=operation,
            component=component,
            start_time=_timestamp(),
            attributes=attributes or {},
        )
        self._active_spans[span.span_id] = span
        return span

    def end_span(self, span_id: str, status: str = "ok") -> TraceSpan | None:
        """End a trace span."""
        span = self._active_spans.pop(span_id, None)
        if span is None:
            return None

        ended_span = replace(span, end_time=_timestamp(), status=status)
        self._spans.append(ended_span)
        return ended_span

    def record_latency(self, slo_name: str, latency_ms: float) -> None:
        """Record a latency sample for SLO tracking."""
        if slo_name in self._latency_samples:
            self._latency_samples[slo_name].append((_timestamp(), latency_ms))
            # Clean old samples outside window
            self._clean_old_samples(slo_name)

    def _clean_old_samples(self, slo_name: str) -> None:
        """Remove samples outside the SLO window."""
        slo = self._slo_definitions.get(slo_name)
        if slo is None:
            return

        cutoff = datetime.now(UTC) - timedelta(minutes=slo.window_minutes)
        cutoff_str = cutoff.isoformat()

        samples = self._latency_samples[slo_name]
        self._latency_samples[slo_name] = [
            (ts, val) for ts, val in samples if ts >= cutoff_str
        ]

    def measure_slo(self, slo_name: str) -> SLOMeasurement | None:
        """Measure current SLO compliance."""
        slo = self._slo_definitions.get(slo_name)
        if slo is None:
            return None

        samples = self._latency_samples.get(slo_name, [])
        if not samples:
            return None

        if slo.metric_type == "latency":
            # Calculate P95 latency
            sorted_values = sorted(val for _, val in samples)
            p95_index = int(len(sorted_values) * 0.95)
            measured = sorted_values[min(p95_index, len(sorted_values) - 1)]
        else:
            # For success rates, assume all samples are successes for now
            # In practice, you'd track failures separately
            measured = 1.0

        is_breached = (
            measured > slo.threshold
            if slo.metric_type == "latency"
            else measured < slo.threshold
        )

        measurement = SLOMeasurement(
            slo_name=slo_name,
            measured_value=measured,
            target_value=slo.threshold,
            is_breached=is_breached,
            window_start=samples[0][0],
            window_end=samples[-1][0],
            sample_count=len(samples),
        )
        self._slo_measurements[slo_name].append(measurement)
        return measurement

    def get_breached_slos(self) -> list[SLOMeasurement]:
        """Get all currently breached SLOs."""
        breached = []
        for slo_name in self._slo_definitions:
            measurement = self.measure_slo(slo_name)
            if measurement and measurement.is_breached:
                breached.append(measurement)
        return breached

    def query_logs(
        self,
        *,
        level: LogLevel | None = None,
        component: Component | None = None,
        correlation_id: str | None = None,
        since: str | None = None,
    ) -> list[StructuredLogEntry]:
        """Query logs with filters."""
        results = self._logs

        if level:
            results = [e for e in results if e.level == level]
        if component:
            results = [e for e in results if e.component == component]
        if correlation_id:
            results = [e for e in results if e.correlation_id == correlation_id]
        if since:
            results = [e for e in results if e.timestamp >= since]

        return results


# =============================================================================
# G9.2 Incident Readiness
# =============================================================================


@dataclass(frozen=True)
class Runbook:
    """Incident response runbook."""

    runbook_id: str
    title: str
    category: str  # "parser", "model", "orchestration", "infrastructure"
    symptoms: tuple[str, ...]
    diagnosis_steps: tuple[str, ...]
    resolution_steps: tuple[str, ...]
    escalation_contacts: tuple[str, ...]
    created_at: str
    last_updated: str


@dataclass(frozen=True)
class IncidentScenario:
    """Representative incident scenario for replay."""

    scenario_id: str
    title: str
    description: str
    category: str
    log_pattern: str
    trace_pattern: str | None
    expected_symptoms: tuple[str, ...]
    expected_resolution: str


@dataclass(frozen=True)
class Postmortem:
    """Incident postmortem document."""

    postmortem_id: str
    incident_id: str
    title: str
    severity: str  # "sev1", "sev2", "sev3"
    timeline: list[dict[str, str]]
    root_cause: str
    impact_summary: str
    lessons_learned: tuple[str, ...]
    action_items: tuple[dict[str, str], ...]
    created_at: str
    reviewed_at: str | None = None


DEFAULT_RUNBOOKS: tuple[Runbook, ...] = (
    Runbook(
        runbook_id="rb-parser-001",
        title="PDF Parser Failure",
        category="parser",
        symptoms=("PDF ingestion stuck", "parser timeout", "memory spike"),
        diagnosis_steps=(
            "Check parser logs",
            "Verify PDF integrity",
            "Check memory usage",
        ),
        resolution_steps=("Restart parser worker", "Clear cache", "Retry ingestion"),
        escalation_contacts=("oncall-backend@loom.local",),
        created_at=_timestamp(),
        last_updated=_timestamp(),
    ),
    Runbook(
        runbook_id="rb-model-001",
        title="LLM Model Timeout",
        category="model",
        symptoms=("Generation timeout", "model unresponsive", "queue backlog"),
        diagnosis_steps=("Check model health", "Verify GPU usage", "Check queue depth"),
        resolution_steps=("Restart model service", "Scale replicas", "Enable fallback"),
        escalation_contacts=("oncall-ml@loom.local",),
        created_at=_timestamp(),
        last_updated=_timestamp(),
    ),
    Runbook(
        runbook_id="rb-orchestration-001",
        title="Job Orchestration Failure",
        category="orchestration",
        symptoms=(
            "Jobs not starting",
            "dead letter queue growing",
            "state inconsistency",
        ),
        diagnosis_steps=("Check orchestrator logs", "Verify database", "Check workers"),
        resolution_steps=(
            "Restart orchestrator",
            "Replay dead letters",
            "Repair state",
        ),
        escalation_contacts=("oncall-backend@loom.local",),
        created_at=_timestamp(),
        last_updated=_timestamp(),
    ),
)


INCIDENT_SCENARIOS: tuple[IncidentScenario, ...] = (
    IncidentScenario(
        scenario_id="scn-parser-pdf",
        title="PDF Zip Bomb",
        description="Malicious PDF with compression bomb causes parser hang",
        category="parser",
        log_pattern="pdf.*timeout|parser.*hang|memory.*exceeded",
        trace_pattern="ingestion.*pdf",
        expected_symptoms=("Parser timeout", "Memory spike", "No output"),
        expected_resolution="Kill parser process, add file size check",
    ),
    IncidentScenario(
        scenario_id="scn-model-oom",
        title="Model OOM",
        description="Large generation job causes model to run out of memory",
        category="model",
        log_pattern="cuda.*oom|out.*memory|allocation.*failed",
        trace_pattern="generation.*image",
        expected_symptoms=("Generation failure", "OOM error", "Model restart"),
        expected_resolution="Reduce batch size, enable memory limits",
    ),
    IncidentScenario(
        scenario_id="scn-orchestration-deadlock",
        title="Job Deadlock",
        description="Circular dependencies cause job deadlock",
        category="orchestration",
        log_pattern="deadlock|cycle.*detected|dependency.*error",
        trace_pattern="orchestration.*job",
        expected_symptoms=("Jobs stuck", "No progress", "Dependency errors"),
        expected_resolution="Break cycle, restart with corrected dependencies",
    ),
)


class IncidentManager:
    """G9.2: Incident readiness with runbooks, replay, and postmortems."""

    def __init__(self) -> None:
        self._runbooks: dict[str, Runbook] = {
            rb.runbook_id: rb for rb in DEFAULT_RUNBOOKS
        }
        self._scenarios: dict[str, IncidentScenario] = {
            s.scenario_id: s for s in INCIDENT_SCENARIOS
        }
        self._postmortems: list[Postmortem] = []
        self._incident_counter = 0

    def get_runbook(self, runbook_id: str) -> Runbook | None:
        """Get a runbook by ID."""
        return self._runbooks.get(runbook_id)

    def find_runbooks(self, category: str | None = None) -> list[Runbook]:
        """Find runbooks by category or all."""
        books = list(self._runbooks.values())
        if category:
            books = [rb for rb in books if rb.category == category]
        return books

    def match_runbook(self, symptoms: list[str]) -> Runbook | None:
        """Match symptoms to a runbook."""
        for runbook in self._runbooks.values():
            matches = sum(
                1 for s in symptoms if any(s in rs for rs in runbook.symptoms)
            )
            if matches > 0:
                return runbook
        return None

    def get_scenario(self, scenario_id: str) -> IncidentScenario | None:
        """Get an incident scenario for replay."""
        return self._scenarios.get(scenario_id)

    def list_scenarios(self, category: str | None = None) -> list[IncidentScenario]:
        """List available replay scenarios."""
        scenarios = list(self._scenarios.values())
        if category:
            scenarios = [s for s in scenarios if s.category == category]
        return scenarios

    def replay_scenario(
        self,
        scenario_id: str,
        logs: list[StructuredLogEntry],
        spans: list[TraceSpan],
    ) -> dict[str, Any]:
        """Replay an incident scenario against logs/traces."""
        scenario = self._scenarios.get(scenario_id)
        if scenario is None:
            return {"error": f"Scenario {scenario_id} not found"}

        # Pattern matching
        pattern = re.compile(scenario.log_pattern, re.IGNORECASE)
        matched_logs = [log for log in logs if pattern.search(log.message)]

        matched_spans = []
        if scenario.trace_pattern:
            trace_pattern = re.compile(scenario.trace_pattern, re.IGNORECASE)
            matched_spans = [
                span for span in spans if trace_pattern.search(span.operation)
            ]

        detected_symptoms = set()
        for log in matched_logs:
            for symptom in scenario.expected_symptoms:
                if symptom.lower() in log.message.lower():
                    detected_symptoms.add(symptom)

        return {
            "scenario_id": scenario_id,
            "title": scenario.title,
            "matched_logs": len(matched_logs),
            "matched_spans": len(matched_spans),
            "detected_symptoms": list(detected_symptoms),
            "expected_symptoms": list(scenario.expected_symptoms),
            "detection_rate": (
                len(detected_symptoms) / len(scenario.expected_symptoms)
                if scenario.expected_symptoms
                else 0
            ),
            "expected_resolution": scenario.expected_resolution,
        }

    def create_postmortem(
        self,
        incident_id: str,
        title: str,
        severity: str,
        timeline: list[dict[str, str]],
        root_cause: str,
        impact_summary: str,
        lessons_learned: tuple[str, ...],
        action_items: tuple[dict[str, str], ...],
    ) -> Postmortem:
        """Create a postmortem document."""
        self._incident_counter += 1
        postmortem = Postmortem(
            postmortem_id=f"pm-{self._incident_counter:04d}",
            incident_id=incident_id,
            title=title,
            severity=severity,
            timeline=timeline,
            root_cause=root_cause,
            impact_summary=impact_summary,
            lessons_learned=lessons_learned,
            action_items=action_items,
            created_at=_timestamp(),
        )
        self._postmortems.append(postmortem)
        return postmortem

    def get_postmortems(self, reviewed: bool | None = None) -> list[Postmortem]:
        """Get postmortems, optionally filtered by review status."""
        posts = self._postmortems
        if reviewed is not None:
            posts = [p for p in posts if (p.reviewed_at is not None) == reviewed]
        return posts

    def mark_postmortem_reviewed(self, postmortem_id: str) -> Postmortem | None:
        """Mark a postmortem as reviewed."""
        for i, pm in enumerate(self._postmortems):
            if pm.postmortem_id == postmortem_id:
                updated = replace(pm, reviewed_at=_timestamp())
                self._postmortems[i] = updated
                return updated
        return None


# =============================================================================
# G9.3 Capacity and Cost Management
# =============================================================================


class QueuePriority(Enum):
    INTERACTIVE = 1
    HIGH = 2
    NORMAL = 3
    BACKGROUND = 4


@dataclass(frozen=True)
class ResourceBudget:
    """Resource budget for a job or branch."""

    budget_id: str
    target_id: str  # job_id or branch_id
    budget_type: str  # "job" or "branch"
    max_tokens: int | None = None
    max_images: int | None = None
    max_cost_usd: float | None = None
    max_duration_seconds: int | None = None


@dataclass(frozen=True)
class ResourceUsage:
    """Current resource usage."""

    budget_id: str
    tokens_used: int = 0
    images_generated: int = 0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0
    last_updated: str = field(default_factory=_timestamp)


@dataclass(frozen=True)
class KillSwitch:
    """Emergency kill switch configuration."""

    switch_id: str
    name: str
    description: str
    target_component: str
    is_triggered: bool = False
    triggered_at: str | None = None
    triggered_by: str | None = None
    reason: str | None = None


class CapacityManager:
    """G9.3: Capacity and cost management."""

    def __init__(self) -> None:
        self._budgets: dict[str, ResourceBudget] = {}
        self._usage: dict[str, ResourceUsage] = {}
        self._kill_switches: dict[str, KillSwitch] = {
            "kill-ingestion": KillSwitch(
                switch_id="kill-ingestion",
                name="Kill All Ingestion",
                description="Immediately stop all ingestion jobs",
                target_component="ingestion",
            ),
            "kill-generation": KillSwitch(
                switch_id="kill-generation",
                name="Kill All Generation",
                description="Immediately stop all generation jobs",
                target_component="generation",
            ),
            "kill-background": KillSwitch(
                switch_id="kill-background",
                name="Kill Background Jobs",
                description="Stop all background priority jobs",
                target_component="background",
            ),
            "kill-branch": KillSwitch(
                switch_id="kill-branch",
                name="Kill Branch Operations",
                description="Stop all branch operations",
                target_component="branch",
            ),
        }
        self._counter = 0

    def create_budget(
        self,
        target_id: str,
        budget_type: str,
        *,
        max_tokens: int | None = None,
        max_images: int | None = None,
        max_cost_usd: float | None = None,
        max_duration_seconds: int | None = None,
    ) -> ResourceBudget:
        """Create a resource budget."""
        self._counter += 1
        budget = ResourceBudget(
            budget_id=f"budget-{self._counter:04d}",
            target_id=target_id,
            budget_type=budget_type,
            max_tokens=max_tokens,
            max_images=max_images,
            max_cost_usd=max_cost_usd,
            max_duration_seconds=max_duration_seconds,
        )
        self._budgets[budget.budget_id] = budget
        self._usage[budget.budget_id] = ResourceUsage(budget_id=budget.budget_id)
        return budget

    def record_usage(
        self,
        budget_id: str,
        *,
        tokens: int = 0,
        images: int = 0,
        cost_usd: float = 0.0,
        duration_seconds: float = 0.0,
    ) -> ResourceUsage | None:
        """Record resource usage against a budget."""
        current = self._usage.get(budget_id)
        if current is None:
            return None

        updated = ResourceUsage(
            budget_id=budget_id,
            tokens_used=current.tokens_used + tokens,
            images_generated=current.images_generated + images,
            cost_usd=current.cost_usd + cost_usd,
            duration_seconds=current.duration_seconds + duration_seconds,
        )
        self._usage[budget_id] = updated
        return updated

    def check_budget(self, budget_id: str) -> dict[str, Any]:
        """Check if a budget has been exceeded."""
        budget = self._budgets.get(budget_id)
        usage = self._usage.get(budget_id)

        if budget is None or usage is None:
            return {"error": "Budget not found"}

        exceeded: list[str] = []
        remaining: dict[str, float] = {}

        if budget.max_tokens and usage.tokens_used > budget.max_tokens:
            exceeded.append("tokens")
        elif budget.max_tokens:
            remaining["tokens"] = budget.max_tokens - usage.tokens_used

        if budget.max_images and usage.images_generated > budget.max_images:
            exceeded.append("images")
        elif budget.max_images:
            remaining["images"] = budget.max_images - usage.images_generated

        if budget.max_cost_usd and usage.cost_usd > budget.max_cost_usd:
            exceeded.append("cost")
        elif budget.max_cost_usd:
            remaining["cost_usd"] = float(budget.max_cost_usd - usage.cost_usd)

        if (
            budget.max_duration_seconds
            and usage.duration_seconds > budget.max_duration_seconds
        ):
            exceeded.append("duration")
        elif budget.max_duration_seconds:
            remaining["duration_seconds"] = (
                budget.max_duration_seconds - usage.duration_seconds
            )

        return {
            "budget_id": budget_id,
            "target_id": budget.target_id,
            "exceeded": exceeded,
            "remaining": remaining,
            "usage": {
                "tokens": usage.tokens_used,
                "images": usage.images_generated,
                "cost_usd": usage.cost_usd,
                "duration_seconds": usage.duration_seconds,
            },
        }

    def trigger_kill_switch(
        self,
        switch_id: str,
        triggered_by: str,
        reason: str,
    ) -> KillSwitch | None:
        """Trigger an emergency kill switch."""
        switch = self._kill_switches.get(switch_id)
        if switch is None:
            return None

        triggered = replace(
            switch,
            is_triggered=True,
            triggered_at=_timestamp(),
            triggered_by=triggered_by,
            reason=reason,
        )
        self._kill_switches[switch_id] = triggered
        return triggered

    def reset_kill_switch(self, switch_id: str, reset_by: str) -> KillSwitch | None:
        """Reset a kill switch."""
        switch = self._kill_switches.get(switch_id)
        if switch is None:
            return None

        reset = replace(
            switch,
            is_triggered=False,
            triggered_at=None,
            triggered_by=reset_by,
            reason=f"Reset by {reset_by}",
        )
        self._kill_switches[switch_id] = reset
        return reset

    def get_active_kill_switches(self) -> list[KillSwitch]:
        """Get all triggered kill switches."""
        return [s for s in self._kill_switches.values() if s.is_triggered]

    def is_operation_allowed(self, component: str, priority: QueuePriority) -> bool:
        """Check if an operation is allowed given current kill switches."""
        # Check component-specific kill switch
        component_switch = self._kill_switches.get(f"kill-{component}")
        if component_switch and component_switch.is_triggered:
            return False

        # Check background kill switch for background jobs
        if priority == QueuePriority.BACKGROUND:
            bg_switch = self._kill_switches.get("kill-background")
            if bg_switch and bg_switch.is_triggered:
                return False

        return True


# =============================================================================
# G9.4 Privacy and Retention Controls
# =============================================================================


@dataclass(frozen=True)
class PrivacyPolicy:
    """Privacy policy configuration."""

    policy_id: str
    name: str
    local_first_default: bool = True
    external_provider_opt_in_required: bool = True
    log_retention_days: int = 30
    data_retention_days: int = 365
    pii_redaction_enabled: bool = True
    anonymization_enabled: bool = False


@dataclass(frozen=True)
class DataRetentionRecord:
    """Data retention tracking record."""

    record_id: str
    data_type: str
    data_id: str
    created_at: str
    retention_days: int
    expires_at: str
    is_redacted: bool = False
    redacted_at: str | None = None


class PrivacyManager:
    """G9.4: Privacy and retention controls."""

    # PII patterns for redaction
    PII_PATTERNS = {
        "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "phone": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
        "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    }

    def __init__(self) -> None:
        self._policy = PrivacyPolicy(
            policy_id="default",
            name="Default Privacy Policy",
        )
        self._retention_records: list[DataRetentionRecord] = []
        self._external_providers: dict[str, bool] = {}  # provider_id -> is_opted_in
        self._counter = 0

    def get_policy(self) -> PrivacyPolicy:
        """Get current privacy policy."""
        return self._policy

    def update_policy(self, **kwargs: Any) -> PrivacyPolicy:
        """Update privacy policy."""
        self._policy = replace(self._policy, **kwargs)
        return self._policy

    def is_local_first(self) -> bool:
        """Check if local-first execution is enforced."""
        return self._policy.local_first_default

    def check_external_provider_access(self, provider_id: str) -> bool:
        """Check if external provider access is allowed."""
        if not self._policy.external_provider_opt_in_required:
            return True
        return self._external_providers.get(provider_id, False)

    def opt_in_external_provider(self, provider_id: str) -> None:
        """Opt in to using an external provider."""
        self._external_providers[provider_id] = True

    def opt_out_external_provider(self, provider_id: str) -> None:
        """Opt out of using an external provider."""
        self._external_providers[provider_id] = False

    def redact_pii(self, text: str) -> str:
        """Redact PII from text."""
        if not self._policy.pii_redaction_enabled:
            return text

        redacted = text
        for pii_type, pattern in self.PII_PATTERNS.items():
            redacted = pattern.sub(f"[{pii_type.upper()}_REDACTED]", redacted)
        return redacted

    def create_retention_record(
        self,
        data_type: str,
        data_id: str,
        retention_days: int | None = None,
    ) -> DataRetentionRecord:
        """Create a data retention record."""
        self._counter += 1
        retention = retention_days or self._policy.data_retention_days
        created = datetime.now(UTC)
        expires = created + timedelta(days=retention)

        record = DataRetentionRecord(
            record_id=f"ret-{self._counter:04d}",
            data_type=data_type,
            data_id=data_id,
            created_at=created.isoformat(),
            retention_days=retention,
            expires_at=expires.isoformat(),
        )
        self._retention_records.append(record)
        return record

    def get_expired_records(self) -> list[DataRetentionRecord]:
        """Get records that have exceeded retention period."""
        now = datetime.now(UTC).isoformat()
        return [r for r in self._retention_records if r.expires_at < now]

    def redact_record(self, record_id: str) -> DataRetentionRecord | None:
        """Redact a data record."""
        for i, record in enumerate(self._retention_records):
            if record.record_id == record_id:
                updated = replace(
                    record,
                    is_redacted=True,
                    redacted_at=_timestamp(),
                )
                self._retention_records[i] = updated
                return updated
        return None

    def enforce_retention(self) -> dict[str, int]:
        """Enforce retention policy on expired records."""
        expired = self.get_expired_records()
        redacted_count = 0

        for record in expired:
            if not record.is_redacted:
                self.redact_record(record.record_id)
                redacted_count += 1

        return {
            "expired_records": len(expired),
            "redacted": redacted_count,
        }


# =============================================================================
# G9.5 Legal and License Compliance
# =============================================================================


@dataclass(frozen=True)
class SourceAttestation:
    """Source material rights attestation."""

    attestation_id: str
    source_path: str
    source_hash: str
    has_distribution_rights: bool
    has_derivative_rights: bool
    license_type: str
    attribution_required: bool
    attribution_text: str | None
    attested_by: str
    attested_at: str
    notes: str | None = None


@dataclass(frozen=True)
class ModelLicense:
    """Model/checkpoint/adapter license record."""

    license_id: str
    name: str
    license_type: str  # "mit", "apache-2", "cc-by", "proprietary", etc.
    version: str
    commercial_use_allowed: bool
    attribution_required: bool
    share_alike_required: bool
    source_url: str | None
    local_path: str | None
    registered_at: str


@dataclass(frozen=True)
class ExportPolicyGate:
    """Policy gate for export/share workflows."""

    gate_id: str
    workflow_type: str  # "export", "share", "publish"
    requires_attestation: bool
    requires_license_check: bool
    requires_content_review: bool
    allowed_maturity_bands: tuple[str, ...]
    blocked_patterns: tuple[str, ...]


DEFAULT_EXPORT_GATES: tuple[ExportPolicyGate, ...] = (
    ExportPolicyGate(
        gate_id="gate-export-standard",
        workflow_type="export",
        requires_attestation=True,
        requires_license_check=True,
        requires_content_review=False,
        allowed_maturity_bands=("all_ages", "teen"),
        blocked_patterns=(),
    ),
    ExportPolicyGate(
        gate_id="gate-share-collaborative",
        workflow_type="share",
        requires_attestation=True,
        requires_license_check=True,
        requires_content_review=True,
        allowed_maturity_bands=("all_ages", "teen", "mature"),
        blocked_patterns=(),
    ),
    ExportPolicyGate(
        gate_id="gate-publish-public",
        workflow_type="publish",
        requires_attestation=True,
        requires_license_check=True,
        requires_content_review=True,
        allowed_maturity_bands=("all_ages", "teen", "mature", "explicit"),
        blocked_patterns=("copyright", "trademark"),
    ),
)


class ComplianceManager:
    """G9.5: Legal and license compliance."""

    def __init__(self) -> None:
        self._attestations: dict[str, SourceAttestation] = {}
        self._licenses: dict[str, ModelLicense] = {}
        self._export_gates: dict[str, ExportPolicyGate] = {
            g.gate_id: g for g in DEFAULT_EXPORT_GATES
        }
        self._counter = 0

    def attest_source_rights(
        self,
        source_path: str,
        source_content: str,
        has_distribution_rights: bool,
        has_derivative_rights: bool,
        license_type: str,
        attribution_required: bool,
        *,
        attribution_text: str | None = None,
        attested_by: str = "system",
        notes: str | None = None,
    ) -> SourceAttestation:
        """Create source rights attestation at ingestion."""
        self._counter += 1
        attestation = SourceAttestation(
            attestation_id=f"att-{self._counter:04d}",
            source_path=source_path,
            source_hash=_hash_content(source_content),
            has_distribution_rights=has_distribution_rights,
            has_derivative_rights=has_derivative_rights,
            license_type=license_type,
            attribution_required=attribution_required,
            attribution_text=attribution_text,
            attested_by=attested_by,
            attested_at=_timestamp(),
            notes=notes,
        )
        self._attestations[attestation.attestation_id] = attestation
        return attestation

    def get_attestation(self, attestation_id: str) -> SourceAttestation | None:
        """Get attestation by ID."""
        return self._attestations.get(attestation_id)

    def verify_source_rights(self, source_hash: str) -> SourceAttestation | None:
        """Verify rights for a source by its content hash."""
        for attestation in self._attestations.values():
            if attestation.source_hash == source_hash:
                return attestation
        return None

    def register_model_license(
        self,
        name: str,
        license_type: str,
        version: str,
        *,
        commercial_use_allowed: bool = True,
        attribution_required: bool = False,
        share_alike_required: bool = False,
        source_url: str | None = None,
        local_path: str | None = None,
    ) -> ModelLicense:
        """Register a model/checkpoint/adapter license."""
        self._counter += 1
        license_record = ModelLicense(
            license_id=f"lic-{self._counter:04d}",
            name=name,
            license_type=license_type,
            version=version,
            commercial_use_allowed=commercial_use_allowed,
            attribution_required=attribution_required,
            share_alike_required=share_alike_required,
            source_url=source_url,
            local_path=local_path,
            registered_at=_timestamp(),
        )
        self._licenses[license_record.license_id] = license_record
        return license_record

    def get_license(self, license_id: str) -> ModelLicense | None:
        """Get license by ID."""
        return self._licenses.get(license_id)

    def check_export_policy(
        self,
        gate_id: str,
        attestation_id: str | None,
        license_ids: list[str],
        maturity_band: str,
        content_preview: str,
    ) -> dict[str, Any]:
        """Check policy gate before export/share workflow."""
        gate = self._export_gates.get(gate_id)
        if gate is None:
            return {"allowed": False, "reason": "Unknown policy gate"}

        violations = []

        # Check attestation
        if gate.requires_attestation:
            if attestation_id is None:
                violations.append("Source attestation required")
            else:
                attestation = self._attestations.get(attestation_id)
                if attestation is None:
                    violations.append("Invalid attestation")
                elif not attestation.has_distribution_rights:
                    violations.append("No distribution rights for source")

        # Check licenses
        if gate.requires_license_check:
            for license_id in license_ids:
                license_record = self._licenses.get(license_id)
                if license_record is None:
                    violations.append(f"Unknown license: {license_id}")
                elif not license_record.commercial_use_allowed:
                    violations.append(
                        f"License {license_record.name} restricts commercial use"
                    )

        # Check maturity band
        if maturity_band not in gate.allowed_maturity_bands:
            violations.append(
                f"Maturity band '{maturity_band}' not allowed for this workflow"
            )

        # Check blocked patterns
        for pattern in gate.blocked_patterns:
            if pattern.lower() in content_preview.lower():
                violations.append(f"Blocked pattern detected: {pattern}")

        return {
            "allowed": len(violations) == 0,
            "gate_id": gate_id,
            "workflow_type": gate.workflow_type,
            "violations": violations,
            "requires_review": gate.requires_content_review,
        }


# =============================================================================
# G9.6 Mature-Content Governance
# =============================================================================


@dataclass(frozen=True)
class ContentPolicyProfile:
    """Content policy profile by deployment context."""

    profile_id: str
    context: str  # "enterprise", "consumer", "education", "research"
    max_maturity_band: str
    requires_confirmation_above: float
    requires_review_above: float
    blocked_labels: tuple[str, ...]
    warning_labels: tuple[str, ...]


@dataclass(frozen=True)
class ContentOverrideRecord:
    """Explicit confirmation and override logging."""

    record_id: str
    content_id: str
    setting_type: str  # "violence", "romance", "humor"
    requested_value: float
    original_value: float
    confirmed_by: str
    confirmation_reason: str
    timestamp: str
    content_hash: str


@dataclass(frozen=True)
class ReviewQueueItem:
    """Item in the content review queue."""

    item_id: str
    content_id: str
    content_type: str
    maturity_score: float
    detected_labels: tuple[str, ...]
    reason: str
    submitted_at: str
    submitted_by: str
    status: str = "pending"  # "pending", "approved", "rejected"
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    review_notes: str | None = None


DEFAULT_POLICY_PROFILES: tuple[ContentPolicyProfile, ...] = (
    ContentPolicyProfile(
        profile_id="profile-enterprise",
        context="enterprise",
        max_maturity_band="teen",
        requires_confirmation_above=0.6,
        requires_review_above=0.8,
        blocked_labels=("explicit",),
        warning_labels=("mature", "violence"),
    ),
    ContentPolicyProfile(
        profile_id="profile-consumer",
        context="consumer",
        max_maturity_band="explicit",
        requires_confirmation_above=0.8,
        requires_review_above=0.95,
        blocked_labels=(),
        warning_labels=("explicit",),
    ),
    ContentPolicyProfile(
        profile_id="profile-education",
        context="education",
        max_maturity_band="all_ages",
        requires_confirmation_above=0.4,
        requires_review_above=0.6,
        blocked_labels=("mature", "explicit", "violence"),
        warning_labels=("teen",),
    ),
    ContentPolicyProfile(
        profile_id="profile-research",
        context="research",
        max_maturity_band="explicit",
        requires_confirmation_above=0.9,
        requires_review_above=0.99,
        blocked_labels=(),
        warning_labels=(),
    ),
)


class ContentGovernanceManager:
    """G9.6: Mature-content governance."""

    MATURITY_BAND_ORDER = ("all_ages", "teen", "mature", "explicit")

    def __init__(self) -> None:
        self._profiles: dict[str, ContentPolicyProfile] = {
            p.profile_id: p for p in DEFAULT_POLICY_PROFILES
        }
        self._overrides: list[ContentOverrideRecord] = []
        self._review_queue: list[ReviewQueueItem] = []
        self._counter = 0

    def get_policy_profile(self, profile_id: str) -> ContentPolicyProfile | None:
        """Get policy profile by ID."""
        return self._profiles.get(profile_id)

    def set_policy_profile(
        self,
        profile_id: str,
        context: str,
        max_maturity_band: str,
        requires_confirmation_above: float,
        requires_review_above: float,
        blocked_labels: tuple[str, ...],
        warning_labels: tuple[str, ...],
    ) -> ContentPolicyProfile:
        """Set or update a policy profile."""
        profile = ContentPolicyProfile(
            profile_id=profile_id,
            context=context,
            max_maturity_band=max_maturity_band,
            requires_confirmation_above=requires_confirmation_above,
            requires_review_above=requires_review_above,
            blocked_labels=blocked_labels,
            warning_labels=warning_labels,
        )
        self._profiles[profile_id] = profile
        return profile

    def check_content_against_profile(
        self,
        profile_id: str,
        maturity_band: str,
        setting_values: dict[str, float],
        detected_labels: list[str],
    ) -> dict[str, Any]:
        """Check content against policy profile."""
        profile = self._profiles.get(profile_id)
        if profile is None:
            return {"error": "Profile not found"}

        violations = []
        requires_confirmation = False
        requires_review = False

        # Check maturity band
        content_level = self.MATURITY_BAND_ORDER.index(maturity_band)
        max_level = self.MATURITY_BAND_ORDER.index(profile.max_maturity_band)
        if content_level > max_level:
            violations.append(
                f"Maturity band '{maturity_band}' exceeds profile maximum"
            )

        # Check blocked labels
        for label in detected_labels:
            if label in profile.blocked_labels:
                violations.append(f"Blocked label detected: {label}")

        # Check setting values
        max_setting = max(setting_values.values()) if setting_values else 0.0
        if max_setting >= profile.requires_review_above:
            requires_review = True
        elif max_setting >= profile.requires_confirmation_above:
            requires_confirmation = True

        # Check warning labels
        warnings = [
            label for label in detected_labels if label in profile.warning_labels
        ]

        return {
            "profile_id": profile_id,
            "allowed": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "requires_confirmation": requires_confirmation,
            "requires_review": requires_review,
        }

    def log_override(
        self,
        content_id: str,
        setting_type: str,
        requested_value: float,
        original_value: float,
        confirmed_by: str,
        confirmation_reason: str,
        content_hash: str,
    ) -> ContentOverrideRecord:
        """Log an explicit confirmation/override for high-intensity settings."""
        self._counter += 1
        record = ContentOverrideRecord(
            record_id=f"ovr-{self._counter:04d}",
            content_id=content_id,
            setting_type=setting_type,
            requested_value=requested_value,
            original_value=original_value,
            confirmed_by=confirmed_by,
            confirmation_reason=confirmation_reason,
            timestamp=_timestamp(),
            content_hash=content_hash,
        )
        self._overrides.append(record)
        return record

    def submit_for_review(
        self,
        content_id: str,
        content_type: str,
        maturity_score: float,
        detected_labels: list[str],
        reason: str,
        submitted_by: str,
    ) -> ReviewQueueItem:
        """Submit borderline content for review."""
        self._counter += 1
        item = ReviewQueueItem(
            item_id=f"rev-{self._counter:04d}",
            content_id=content_id,
            content_type=content_type,
            maturity_score=maturity_score,
            detected_labels=tuple(detected_labels),
            reason=reason,
            submitted_at=_timestamp(),
            submitted_by=submitted_by,
        )
        self._review_queue.append(item)
        return item

    def review_item(
        self,
        item_id: str,
        decision: str,  # "approved" or "rejected"
        reviewed_by: str,
        notes: str | None = None,
    ) -> ReviewQueueItem | None:
        """Review a queued item."""
        for i, item in enumerate(self._review_queue):
            if item.item_id == item_id:
                updated = replace(
                    item,
                    status=decision,
                    reviewed_by=reviewed_by,
                    reviewed_at=_timestamp(),
                    review_notes=notes,
                )
                self._review_queue[i] = updated
                return updated
        return None

    def get_pending_reviews(self) -> list[ReviewQueueItem]:
        """Get all pending review items."""
        return [item for item in self._review_queue if item.status == "pending"]

    def get_override_log(
        self, content_id: str | None = None
    ) -> list[ContentOverrideRecord]:
        """Get override records, optionally filtered by content."""
        if content_id is None:
            return self._overrides
        return [o for o in self._overrides if o.content_id == content_id]


# =============================================================================
# Main Operations Engine
# =============================================================================


@dataclass(frozen=True)
class Phase9Metrics:
    """Aggregated metrics for Phase 9 done-criteria validation."""

    security_privacy_compliance_pass: bool
    slo_dashboards_active: bool
    budget_controls_active: bool
    breached_slo_count: int
    active_kill_switches: int
    expired_data_records: int
    pending_reviews: int
    policy_violations_24h: int


class OperationsEngine:
    """Main operations engine aggregating all Phase 9 managers."""

    def __init__(self) -> None:
        self.observability = ObservabilityManager()
        self.incidents = IncidentManager()
        self.capacity = CapacityManager()
        self.privacy = PrivacyManager()
        self.compliance = ComplianceManager()
        self.governance = ContentGovernanceManager()

    def evaluate_phase9_done_criteria(self) -> Phase9Metrics:
        """Evaluate Phase 9 done criteria."""
        # Security and privacy compliance
        policy = self.privacy.get_policy()
        security_privacy_pass = (
            policy.pii_redaction_enabled
            and policy.local_first_default
            and policy.external_provider_opt_in_required
        )

        # SLO dashboards (active if we have recent measurements)
        recent_measurements = any(
            self.observability._slo_measurements[slo]
            for slo in self.observability._slo_definitions
        )
        slo_dashboards_active = recent_measurements

        # Budget controls (active if any budgets exist)
        budget_controls_active = len(self.capacity._budgets) > 0

        # Count breached SLOs
        breached_slos = len(self.observability.get_breached_slos())

        # Count active kill switches
        active_kills = len(self.capacity.get_active_kill_switches())

        # Count expired data records
        expired_data = len(self.privacy.get_expired_records())

        # Count pending reviews
        pending_reviews = len(self.governance.get_pending_reviews())

        # Policy violations (would be tracked separately in production)
        policy_violations = 0

        return Phase9Metrics(
            security_privacy_compliance_pass=security_privacy_pass,
            slo_dashboards_active=slo_dashboards_active,
            budget_controls_active=budget_controls_active,
            breached_slo_count=breached_slos,
            active_kill_switches=active_kills,
            expired_data_records=expired_data,
            pending_reviews=pending_reviews,
            policy_violations_24h=policy_violations,
        )


__all__ = [
    "CapacityManager",
    "ComplianceManager",
    "Component",
    "ContentGovernanceManager",
    "ContentOverrideRecord",
    "ContentPolicyProfile",
    "DataRetentionRecord",
    "DEFAULT_EXPORT_GATES",
    "DEFAULT_RUNBOOKS",
    "DEFAULT_SLOS",
    "ExportPolicyGate",
    "IncidentManager",
    "IncidentScenario",
    "KillSwitch",
    "LogLevel",
    "ModelLicense",
    "ObservabilityManager",
    "OperationsEngine",
    "Phase9Metrics",
    "Postmortem",
    "PrivacyManager",
    "PrivacyPolicy",
    "QueuePriority",
    "ResourceBudget",
    "ResourceUsage",
    "ReviewQueueItem",
    "Runbook",
    "SLODefinition",
    "SLOMeasurement",
    "SourceAttestation",
    "StructuredLogEntry",
    "TraceSpan",
]
