"""Tests for Phase 9 - Operations, Security, and Governance."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from core.operations_engine import (
    CapacityManager,
    ComplianceManager,
    Component,
    ContentGovernanceManager,
    IncidentManager,
    LogLevel,
    ObservabilityManager,
    OperationsEngine,
    Phase9Metrics,
    PrivacyManager,
    QueuePriority,
)


class TestG91ObservabilityAndSLOs:
    """G9.1: Observability and SLOs."""

    def test_structured_log_entry_creation(self) -> None:
        """Structured logs include correlation IDs."""
        manager = ObservabilityManager()
        entry = manager.log(
            level=LogLevel.INFO,
            component=Component.INGESTION,
            message="Test log message",
            request_id="req-123",
            job_id="job-456",
            branch_id="branch-789",
            context={"key": "value"},
        )

        assert entry.level == LogLevel.INFO
        assert entry.component == Component.INGESTION
        assert entry.message == "Test log message"
        assert entry.request_id == "req-123"
        assert entry.job_id == "job-456"
        assert entry.branch_id == "branch-789"
        assert entry.correlation_id == "req-123"  # Uses request_id as correlation
        assert entry.context == {"key": "value"}
        assert entry.timestamp

    def test_trace_span_creation(self) -> None:
        """Traces created with proper parent-child relationships."""
        manager = ObservabilityManager()

        # Start root span
        root_span = manager.start_span(
            operation="ingest_story",
            component=Component.INGESTION,
            attributes={"story_id": "story-123"},
        )

        assert root_span.operation == "ingest_story"
        assert root_span.component == Component.INGESTION
        assert root_span.trace_id
        assert root_span.span_id
        assert root_span.parent_span_id is None

        # Start child span
        child_span = manager.start_span(
            operation="parse_pdf",
            component=Component.INGESTION,
            parent_span_id=root_span.span_id,
        )

        assert child_span.trace_id == root_span.trace_id
        assert child_span.parent_span_id == root_span.span_id

    def test_span_end_creates_complete_trace(self) -> None:
        """Ending a span creates complete trace record."""
        manager = ObservabilityManager()
        span = manager.start_span(
            operation="test_op",
            component=Component.GENERATION,
        )

        ended = manager.end_span(span.span_id, status="ok")

        assert ended is not None
        assert ended.end_time is not None
        assert ended.status == "ok"
        assert len(manager._spans) == 1

    def test_slo_default_definitions_exist(self) -> None:
        """Default SLOs defined for latency, failure rate, sync success."""
        manager = ObservabilityManager()

        assert "ingestion_latency" in manager._slo_definitions
        assert "retrieval_latency" in manager._slo_definitions
        assert "generation_success_rate" in manager._slo_definitions
        assert "sync_success_rate" in manager._slo_definitions

    def test_slo_latency_measurement(self) -> None:
        """SLO measurement calculates P95 latency correctly."""
        manager = ObservabilityManager()

        # Record latency samples
        for i in range(100):
            manager.record_latency("ingestion_latency", float(i * 10))

        measurement = manager.measure_slo("ingestion_latency")

        assert measurement is not None
        assert measurement.slo_name == "ingestion_latency"
        assert measurement.sample_count == 100
        assert measurement.measured_value > 0
        assert measurement.is_breached is False  # Should be under 5000ms

    def test_slo_breach_detection(self) -> None:
        """SLO breach detected when threshold exceeded."""
        manager = ObservabilityManager()

        # Record high latency samples that breach threshold
        for _ in range(10):
            manager.record_latency("retrieval_latency", 500.0)  # Above 200ms threshold

        measurement = manager.measure_slo("retrieval_latency")

        assert measurement is not None
        assert measurement.is_breached is True

    def test_log_query_by_level(self) -> None:
        """Logs can be queried by level."""
        manager = ObservabilityManager()
        manager.log(LogLevel.INFO, Component.INGESTION, "Info message")
        manager.log(LogLevel.ERROR, Component.GENERATION, "Error message")

        errors = manager.query_logs(level=LogLevel.ERROR)

        assert len(errors) == 1
        assert errors[0].message == "Error message"

    def test_log_query_by_correlation_id(self) -> None:
        """Logs can be queried by correlation ID."""
        manager = ObservabilityManager()
        manager.log(
            LogLevel.INFO, Component.INGESTION, "Message 1", request_id="req-abc"
        )
        manager.log(
            LogLevel.INFO, Component.GENERATION, "Message 2", request_id="req-xyz"
        )

        logs = manager.query_logs(correlation_id="req-abc")

        assert len(logs) == 1
        assert logs[0].message == "Message 1"


class TestG92IncidentReadiness:
    """G9.2: Incident readiness."""

    def test_default_runbooks_exist(self) -> None:
        """Default runbooks exist for parser, model, orchestration failures."""
        manager = IncidentManager()

        parser_books = manager.find_runbooks(category="parser")
        model_books = manager.find_runbooks(category="model")
        orch_books = manager.find_runbooks(category="orchestration")

        assert len(parser_books) > 0
        assert len(model_books) > 0
        assert len(orch_books) > 0

    def test_runbook_contains_symptoms_diagnosis_resolution(self) -> None:
        """Runbooks contain symptoms, diagnosis, and resolution steps."""
        manager = IncidentManager()
        runbook = manager.get_runbook("rb-parser-001")

        assert runbook is not None
        assert len(runbook.symptoms) > 0
        assert len(runbook.diagnosis_steps) > 0
        assert len(runbook.resolution_steps) > 0
        assert len(runbook.escalation_contacts) > 0

    def test_runbook_symptom_matching(self) -> None:
        """Runbooks can be matched by symptoms."""
        manager = IncidentManager()

        matched = manager.match_runbook(["PDF ingestion stuck", "timeout"])

        assert matched is not None
        assert matched.category == "parser"

    def test_incident_scenario_replay(self) -> None:
        """Incident scenarios can be replayed against logs."""
        manager = IncidentManager()
        observability = ObservabilityManager()

        # Create logs that match the scenario
        observability.log(
            LogLevel.ERROR,
            Component.INGESTION,
            "pdf parser timeout exceeded",
        )

        result = manager.replay_scenario(
            "scn-parser-pdf",
            observability._logs,
            observability._spans,
        )

        assert result["scenario_id"] == "scn-parser-pdf"
        assert result["matched_logs"] > 0
        assert result["detection_rate"] >= 0.0

    def test_postmortem_creation(self) -> None:
        """Postmortems can be created with timeline and action items."""
        manager = IncidentManager()

        postmortem = manager.create_postmortem(
            incident_id="inc-123",
            title="PDF Parser Outage",
            severity="sev2",
            timeline=[
                {"time": "10:00", "event": "Issue detected"},
                {"time": "10:15", "event": "Investigation started"},
            ],
            root_cause="Memory leak in PDF parser",
            impact_summary="2 hour outage affecting 50 users",
            lessons_learned=("Need better memory monitoring",),
            action_items=(
                {"action": "Add memory limits", "owner": "team", "due": "2024-02-01"},
            ),
        )

        assert postmortem.postmortem_id.startswith("pm-")
        assert postmortem.incident_id == "inc-123"
        assert postmortem.severity == "sev2"
        assert len(postmortem.timeline) == 2
        assert postmortem.reviewed_at is None

    def test_postmortem_review_marking(self) -> None:
        """Postmortems can be marked as reviewed."""
        manager = IncidentManager()
        postmortem = manager.create_postmortem(
            incident_id="inc-456",
            title="Test Incident",
            severity="sev3",
            timeline=[],
            root_cause="Test",
            impact_summary="None",
            lessons_learned=(),
            action_items=(),
        )

        reviewed = manager.mark_postmortem_reviewed(postmortem.postmortem_id)

        assert reviewed is not None
        assert reviewed.reviewed_at is not None


class TestG93CapacityAndCostManagement:
    """G9.3: Capacity and cost management."""

    def test_resource_budget_creation(self) -> None:
        """Resource budgets created with token/image/cost limits."""
        manager = CapacityManager()

        budget = manager.create_budget(
            target_id="job-123",
            budget_type="job",
            max_tokens=100000,
            max_images=10,
            max_cost_usd=5.0,
            max_duration_seconds=300,
        )

        assert budget.budget_id.startswith("budget-")
        assert budget.target_id == "job-123"
        assert budget.budget_type == "job"
        assert budget.max_tokens == 100000
        assert budget.max_images == 10
        assert budget.max_cost_usd == 5.0
        assert budget.max_duration_seconds == 300

    def test_resource_usage_tracking(self) -> None:
        """Resource usage tracked against budgets."""
        manager = CapacityManager()
        budget = manager.create_budget(
            target_id="job-123",
            budget_type="job",
            max_tokens=1000,
        )

        usage = manager.record_usage(
            budget.budget_id,
            tokens=500,
            images=5,
            cost_usd=2.5,
            duration_seconds=150.0,
        )

        assert usage is not None
        assert usage.tokens_used == 500
        assert usage.images_generated == 5
        assert usage.cost_usd == 2.5

    def test_budget_exceeded_detection(self) -> None:
        """Budget exceeded when usage passes thresholds."""
        manager = CapacityManager()
        budget = manager.create_budget(
            target_id="job-123",
            budget_type="job",
            max_tokens=100,
        )

        manager.record_usage(budget.budget_id, tokens=150)
        check = manager.check_budget(budget.budget_id)

        assert check["exceeded"] == ["tokens"]
        assert check["target_id"] == "job-123"

    def test_kill_switch_triggering(self) -> None:
        """Kill switches can be triggered for emergency stop."""
        manager = CapacityManager()

        triggered = manager.trigger_kill_switch(
            "kill-ingestion",
            triggered_by="admin",
            reason="Memory leak detected",
        )

        assert triggered is not None
        assert triggered.is_triggered is True
        assert triggered.triggered_by == "admin"
        assert triggered.reason == "Memory leak detected"
        assert triggered.triggered_at is not None

    def test_kill_switch_prevents_operations(self) -> None:
        """Triggered kill switches block affected operations."""
        manager = CapacityManager()
        manager.trigger_kill_switch("kill-ingestion", "admin", "Emergency")

        allowed = manager.is_operation_allowed("ingestion", QueuePriority.NORMAL)

        assert allowed is False

    def test_background_kill_switch_affects_background_only(self) -> None:
        """Background kill switch only affects background priority jobs."""
        manager = CapacityManager()
        manager.trigger_kill_switch("kill-background", "admin", "Overload")

        bg_allowed = manager.is_operation_allowed(
            "generation", QueuePriority.BACKGROUND
        )
        normal_allowed = manager.is_operation_allowed(
            "generation", QueuePriority.NORMAL
        )

        assert bg_allowed is False
        assert normal_allowed is True

    def test_kill_switch_reset(self) -> None:
        """Kill switches can be reset after incident."""
        manager = CapacityManager()
        manager.trigger_kill_switch("kill-ingestion", "admin", "Emergency")

        reset = manager.reset_kill_switch("kill-ingestion", "admin")

        assert reset is not None
        assert reset.is_triggered is False
        assert manager.is_operation_allowed("ingestion", QueuePriority.NORMAL) is True


class TestG94PrivacyAndRetentionControls:
    """G9.4: Privacy and retention controls."""

    def test_local_first_default(self) -> None:
        """Local-first execution enforced by default."""
        manager = PrivacyManager()
        policy = manager.get_policy()

        assert policy.local_first_default is True
        assert manager.is_local_first() is True

    def test_external_provider_opt_in_required(self) -> None:
        """External providers require explicit opt-in."""
        manager = PrivacyManager()

        # Before opt-in, access denied
        assert manager.check_external_provider_access("openai") is False

        # After opt-in, access allowed
        manager.opt_in_external_provider("openai")
        assert manager.check_external_provider_access("openai") is True

        # Can opt out again
        manager.opt_out_external_provider("openai")
        assert manager.check_external_provider_access("openai") is False

    def test_pii_redaction(self) -> None:
        """PII redacted from text when enabled."""
        manager = PrivacyManager()
        text = "Contact john@example.com or call 555-123-4567"

        redacted = manager.redact_pii(text)

        assert "[EMAIL_REDACTED]" in redacted
        assert "[PHONE_REDACTED]" in redacted
        assert "john@example.com" not in redacted
        assert "555-123-4567" not in redacted

    def test_data_retention_record_creation(self) -> None:
        """Data retention records track expiration dates."""
        manager = PrivacyManager()

        record = manager.create_retention_record(
            data_type="story",
            data_id="story-123",
            retention_days=30,
        )

        assert record.record_id.startswith("ret-")
        assert record.data_type == "story"
        assert record.data_id == "story-123"
        assert record.retention_days == 30
        assert record.expires_at > record.created_at
        assert record.is_redacted is False

    def test_retention_expiration_detection(self) -> None:
        """Expired records detected for cleanup."""
        manager = PrivacyManager()

        # Create record with 0 days retention (immediately expired)
        record = manager.create_retention_record(
            data_type="temp",
            data_id="temp-123",
            retention_days=0,
        )

        # Manually expire by adjusting timestamp (hack for testing)
        expired_time = (datetime.now(UTC) - timedelta(days=1)).isoformat()
        from dataclasses import replace

        manager._retention_records[0] = replace(
            record, created_at=expired_time, expires_at=expired_time
        )

        expired = manager.get_expired_records()
        assert len(expired) == 1

    def test_retention_enforcement_redacts_expired(self) -> None:
        """Retention enforcement redacts expired records."""
        manager = PrivacyManager()

        # Create and expire a record
        record = manager.create_retention_record(
            data_type="temp",
            data_id="temp-123",
            retention_days=0,
        )
        expired_time = (datetime.now(UTC) - timedelta(days=1)).isoformat()
        from dataclasses import replace

        manager._retention_records[0] = replace(
            record, created_at=expired_time, expires_at=expired_time
        )

        result = manager.enforce_retention()

        assert result["expired_records"] == 1
        assert result["redacted"] == 1
        assert manager._retention_records[0].is_redacted is True


class TestG95LegalAndLicenseCompliance:
    """G9.5: Legal and license compliance."""

    def test_source_attestation_creation(self) -> None:
        """Source rights attestation created at ingestion."""
        manager = ComplianceManager()

        attestation = manager.attest_source_rights(
            source_path="/stories/book.pdf",
            source_content="story content here",
            has_distribution_rights=True,
            has_derivative_rights=True,
            license_type="cc-by-4.0",
            attribution_required=True,
            attribution_text="Original by Author",
            attested_by="user@example.com",
        )

        assert attestation.attestation_id.startswith("att-")
        assert attestation.source_path == "/stories/book.pdf"
        assert attestation.source_hash
        assert attestation.has_distribution_rights is True
        assert attestation.has_derivative_rights is True
        assert attestation.license_type == "cc-by-4.0"
        assert attestation.attribution_text == "Original by Author"

    def test_attestation_verification_by_hash(self) -> None:
        """Attestation verified by content hash."""
        manager = ComplianceManager()

        attestation = manager.attest_source_rights(
            source_path="/stories/book.pdf",
            source_content="unique content",
            has_distribution_rights=True,
            has_derivative_rights=False,
            license_type="proprietary",
            attribution_required=False,
            attested_by="user",
        )

        # Verify by hash
        verified = manager.verify_source_rights(attestation.source_hash)
        assert verified is not None
        assert verified.attestation_id == attestation.attestation_id

        # Non-existent hash returns None
        not_found = manager.verify_source_rights("nonexistent")
        assert not_found is None

    def test_model_license_registration(self) -> None:
        """Model/checkpoint/adapter licenses registered."""
        manager = ComplianceManager()

        license_record = manager.register_model_license(
            name="Llama-3-8B",
            license_type="llama-3",
            version="3.0",
            commercial_use_allowed=True,
            attribution_required=False,
            source_url="https://example.com/llama",
        )

        assert license_record.license_id.startswith("lic-")
        assert license_record.name == "Llama-3-8B"
        assert license_record.license_type == "llama-3"
        assert license_record.commercial_use_allowed is True

    def test_export_policy_gate_blocks_without_attestation(self) -> None:
        """Export blocked without required source attestation."""
        manager = ComplianceManager()

        result = manager.check_export_policy(
            gate_id="gate-export-standard",
            attestation_id=None,  # Missing attestation
            license_ids=[],
            maturity_band="teen",
            content_preview="safe content",
        )

        assert result["allowed"] is False
        assert "Source attestation required" in result["violations"]

    def test_export_policy_gate_blocks_without_distribution_rights(self) -> None:
        """Export blocked without distribution rights."""
        manager = ComplianceManager()

        # Create attestation without distribution rights
        attestation = manager.attest_source_rights(
            source_path="/stories/protected.pdf",
            source_content="content",
            has_distribution_rights=False,
            has_derivative_rights=True,
            license_type="proprietary",
            attribution_required=False,
            attested_by="user",
        )

        result = manager.check_export_policy(
            gate_id="gate-export-standard",
            attestation_id=attestation.attestation_id,
            license_ids=[],
            maturity_band="teen",
            content_preview="content",
        )

        assert result["allowed"] is False
        assert "No distribution rights for source" in result["violations"]

    def test_export_policy_gate_blocks_by_maturity(self) -> None:
        """Export blocked if maturity band not allowed."""
        manager = ComplianceManager()

        attestation = manager.attest_source_rights(
            source_path="/stories/story.pdf",
            source_content="content",
            has_distribution_rights=True,
            has_derivative_rights=True,
            license_type="cc-0",
            attribution_required=False,
            attested_by="user",
        )

        # explicit not allowed for standard export
        result = manager.check_export_policy(
            gate_id="gate-export-standard",
            attestation_id=attestation.attestation_id,
            license_ids=[],
            maturity_band="explicit",
            content_preview="content",
        )

        assert result["allowed"] is False
        assert "Maturity band 'explicit'" in str(result["violations"])

    def test_export_policy_allows_compliant_content(self) -> None:
        """Export allowed when all requirements met."""
        manager = ComplianceManager()

        attestation = manager.attest_source_rights(
            source_path="/stories/story.pdf",
            source_content="content",
            has_distribution_rights=True,
            has_derivative_rights=True,
            license_type="cc-0",
            attribution_required=False,
            attested_by="user",
        )

        result = manager.check_export_policy(
            gate_id="gate-export-standard",
            attestation_id=attestation.attestation_id,
            license_ids=[],
            maturity_band="teen",
            content_preview="content",
        )

        assert result["allowed"] is True
        assert len(result["violations"]) == 0


class TestG96MatureContentGovernance:
    """G9.6: Mature-content governance."""

    def test_policy_profiles_by_context(self) -> None:
        """Policy profiles exist for different deployment contexts."""
        manager = ContentGovernanceManager()

        enterprise = manager.get_policy_profile("profile-enterprise")
        consumer = manager.get_policy_profile("profile-consumer")
        education = manager.get_policy_profile("profile-education")

        assert enterprise is not None
        assert enterprise.context == "enterprise"
        assert consumer is not None
        assert consumer.context == "consumer"
        assert education is not None
        assert education.context == "education"

    def test_enterprise_profile_restricts_mature_content(self) -> None:
        """Enterprise profile restricts mature content."""
        manager = ContentGovernanceManager()

        result = manager.check_content_against_profile(
            profile_id="profile-enterprise",
            maturity_band="explicit",
            setting_values={},
            detected_labels=[],
        )

        assert result["allowed"] is False
        assert (
            "Maturity band 'explicit' exceeds profile maximum" in result["violations"]
        )

    def test_education_profile_blocks_violence(self) -> None:
        """Education profile blocks violence labels."""
        manager = ContentGovernanceManager()

        result = manager.check_content_against_profile(
            profile_id="profile-education",
            maturity_band="all_ages",
            setting_values={},
            detected_labels=["violence"],
        )

        assert result["allowed"] is False
        assert "Blocked label detected: violence" in result["violations"]

    def test_high_intensity_settings_require_confirmation(self) -> None:
        """High-intensity settings require explicit confirmation."""
        manager = ContentGovernanceManager()

        result = manager.check_content_against_profile(
            profile_id="profile-enterprise",
            maturity_band="teen",
            setting_values={"violence": 0.7},  # Above 0.6 threshold
            detected_labels=[],
        )

        assert result["requires_confirmation"] is True

    def test_extreme_settings_require_review(self) -> None:
        """Extreme settings require review."""
        manager = ContentGovernanceManager()

        result = manager.check_content_against_profile(
            profile_id="profile-enterprise",
            maturity_band="teen",
            setting_values={"violence": 0.9},  # Above 0.8 threshold
            detected_labels=[],
        )

        assert result["requires_review"] is True

    def test_override_logging(self) -> None:
        """High-intensity overrides are logged with confirmation."""
        manager = ContentGovernanceManager()

        override = manager.log_override(
            content_id="content-123",
            setting_type="violence",
            requested_value=0.95,
            original_value=0.5,
            confirmed_by="admin@example.com",
            confirmation_reason="Story requires intense battle scene",
            content_hash="abc123",
        )

        assert override.record_id.startswith("ovr-")
        assert override.content_id == "content-123"
        assert override.setting_type == "violence"
        assert override.confirmed_by == "admin@example.com"
        assert override.confirmation_reason == "Story requires intense battle scene"

    def test_review_queue_submission(self) -> None:
        """Borderline content submitted for review."""
        manager = ContentGovernanceManager()

        item = manager.submit_for_review(
            content_id="content-456",
            content_type="generated_text",
            maturity_score=0.85,
            detected_labels=["mature", "violence"],
            reason="High maturity score with violence label",
            submitted_by="user@example.com",
        )

        assert item.item_id.startswith("rev-")
        assert item.content_id == "content-456"
        assert item.status == "pending"
        assert item.maturity_score == 0.85

    def test_review_approval(self) -> None:
        """Review items can be approved or rejected."""
        manager = ContentGovernanceManager()

        item = manager.submit_for_review(
            content_id="content-789",
            content_type="image",
            maturity_score=0.75,
            detected_labels=[],
            reason="Check image content",
            submitted_by="user",
        )

        reviewed = manager.review_item(
            item_id=item.item_id,
            decision="approved",
            reviewed_by="moderator@example.com",
            notes="Content is acceptable",
        )

        assert reviewed is not None
        assert reviewed.status == "approved"
        assert reviewed.reviewed_by == "moderator@example.com"
        assert reviewed.reviewed_at is not None

    def test_pending_reviews_listing(self) -> None:
        """Pending reviews can be listed for moderators."""
        manager = ContentGovernanceManager()

        manager.submit_for_review(
            content_id="content-1",
            content_type="text",
            maturity_score=0.8,
            detected_labels=[],
            reason="Check",
            submitted_by="user",
        )
        manager.submit_for_review(
            content_id="content-2",
            content_type="image",
            maturity_score=0.9,
            detected_labels=[],
            reason="Check",
            submitted_by="user",
        )

        pending = manager.get_pending_reviews()

        assert len(pending) == 2


class TestPhase9DoneCriteria:
    """Phase 9 done criteria validation."""

    def test_operations_engine_integration(self) -> None:
        """All Phase 9 managers integrated in OperationsEngine."""
        engine = OperationsEngine()

        assert engine.observability is not None
        assert engine.incidents is not None
        assert engine.capacity is not None
        assert engine.privacy is not None
        assert engine.compliance is not None
        assert engine.governance is not None

    def test_phase9_metrics_evaluation(self) -> None:
        """Phase 9 metrics can be evaluated."""
        engine = OperationsEngine()

        # Create a budget to make budget_controls_active true
        engine.capacity.create_budget("test", "job", max_tokens=100)

        metrics = engine.evaluate_phase9_done_criteria()

        assert isinstance(metrics, Phase9Metrics)
        assert isinstance(metrics.security_privacy_compliance_pass, bool)
        assert isinstance(metrics.budget_controls_active, bool)
        assert metrics.breached_slo_count >= 0
        assert metrics.active_kill_switches >= 0

    def test_default_privacy_enables_compliance(self) -> None:
        """Default privacy settings enable compliance."""
        engine = OperationsEngine()

        metrics = engine.evaluate_phase9_done_criteria()

        # Default settings should pass security/privacy
        assert metrics.security_privacy_compliance_pass is True

    def test_kill_switch_triggers_increase_metric(self) -> None:
        """Active kill switches counted in metrics."""
        engine = OperationsEngine()
        engine.capacity.trigger_kill_switch("kill-ingestion", "admin", "Test")

        metrics = engine.evaluate_phase9_done_criteria()

        assert metrics.active_kill_switches == 1
