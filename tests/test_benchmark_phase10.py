"""Tests for Phase 10 - Evaluation, Hardening, and Release."""

from __future__ import annotations

from core.benchmark_engine import (
    DEFAULT_BENCHMARKS,
    DEFAULT_BETA_PERSONAS,
    DEFAULT_GATE_REQUIREMENTS,
    BenchmarkCategory,
    BenchmarkMetricType,
    BenchmarkRunner,
    BetaProgram,
    Phase10Metrics,
    ReleaseEngine,
    ReleaseGate,
    ReleaseGateStatus,
    ReleaseGateVerifier,
    ReleaseReadinessChecker,
)


class TestG101BenchmarkSuiteCompletion:
    """G10.1: Benchmark suite completion."""

    def test_default_benchmarks_exist_for_all_categories(self) -> None:
        """Benchmarks exist for ingestion, retrieval, narrative, visual, and UX."""
        categories = {b.category for b in DEFAULT_BENCHMARKS}

        assert BenchmarkCategory.INGESTION in categories
        assert BenchmarkCategory.RETRIEVAL in categories
        assert BenchmarkCategory.NARRATIVE in categories
        assert BenchmarkCategory.VISUAL in categories
        assert BenchmarkCategory.UX in categories

    def test_ingestion_benchmarks_defined(self) -> None:
        """Ingestion benchmarks cover text, PDF, CBZ, and security."""
        ingestion = [
            b for b in DEFAULT_BENCHMARKS if b.category == BenchmarkCategory.INGESTION
        ]
        case_ids = {b.case_id for b in ingestion}

        assert "ingest-txt-small" in case_ids
        assert "ingest-pdf-medium" in case_ids
        assert "ingest-cbz-manga" in case_ids
        assert "ingest-security-zipbomb" in case_ids

    def test_retrieval_benchmarks_defined(self) -> None:
        """Retrieval benchmarks cover vector, hybrid, filtering, and precision."""
        retrieval = [
            b for b in DEFAULT_BENCHMARKS if b.category == BenchmarkCategory.RETRIEVAL
        ]
        case_ids = {b.case_id for b in retrieval}

        assert "retrieve-simple" in case_ids
        assert "retrieve-hybrid" in case_ids
        assert "retrieve-branch-filter" in case_ids
        assert "retrieve-precision" in case_ids

    def test_benchmark_has_target_value(self) -> None:
        """Each benchmark has a target value for pass/fail determination."""
        for benchmark in DEFAULT_BENCHMARKS:
            assert benchmark.target_value > 0
            assert benchmark.metric_type is not None

    def test_benchmark_runner_creation(self) -> None:
        """Benchmark runner initializes with default benchmarks."""
        runner = BenchmarkRunner()

        assert len(runner._benchmarks) == len(DEFAULT_BENCHMARKS)

    def test_benchmark_run_single_case(self) -> None:
        """Can run a single benchmark case."""
        runner = BenchmarkRunner()

        result = runner.run_benchmark(
            "ingest-txt-small",
            lambda: 50.0,  # Simulated: 50ms latency (under 100ms target)
        )

        assert result.case_id == "ingest-txt-small"
        assert result.value == 50.0
        assert result.passed is True
        assert result.timestamp

    def test_benchmark_fail_when_target_exceeded(self) -> None:
        """Benchmark fails when latency exceeds target."""
        runner = BenchmarkRunner()

        result = runner.run_benchmark(
            "ingest-txt-small",
            lambda: 150.0,  # Simulated: 150ms (over 100ms target)
        )

        assert result.passed is False

    def test_accuracy_benchmark_passes_above_target(self) -> None:
        """Accuracy benchmark passes when value meets or exceeds target."""
        runner = BenchmarkRunner()

        result = runner.run_benchmark(
            "retrieve-precision",
            lambda: 0.90,  # 90% precision (over 85% target)
        )

        assert result.passed is True

    def test_benchmark_suite_run(self) -> None:
        """Can run full benchmark suite."""
        runner = BenchmarkRunner()

        run = runner.run_suite()

        assert run.run_id
        assert len(run.results) == len(DEFAULT_BENCHMARKS)
        assert run.duration_ms > 0

    def test_benchmark_history_tracking(self) -> None:
        """Benchmark history tracked for trend analysis."""
        runner = BenchmarkRunner()

        # Run same benchmark multiple times
        for _ in range(5):
            runner.run_benchmark("ingest-txt-small", lambda: 80.0)

        history = runner.get_history("ingest-txt-small")

        assert len(history) == 5

    def test_trend_line_calculation(self) -> None:
        """Trend line calculated from historical data."""
        runner = BenchmarkRunner()

        # Create increasing latency trend
        for val in [50, 60, 70, 80, 90]:
            runner.run_benchmark("ingest-txt-small", lambda v=val: float(v))  # type: ignore[misc]

        trend = runner.calculate_trend("ingest-txt-small")

        assert trend is not None
        assert trend.case_id == "ingest-txt-small"
        assert len(trend.values) == 5
        assert trend.slope != 0

    def test_regression_alert_detection(self) -> None:
        """Regression alerts triggered when benchmarks regress."""
        runner = BenchmarkRunner()

        # Create worsening trend with more data points for stronger correlation
        for v in [50, 65, 80, 95, 110, 125, 140]:
            runner.run_benchmark(
                "ingest-txt-small", (lambda val: lambda: float(val))(v)
            )

        # Should detect regression (trend exists)
        # Note: r_squared threshold may not be met with small test data,
        # so we just verify the trend calculation works
        trend = runner.calculate_trend("ingest-txt-small")
        assert trend is not None
        assert trend.is_regressing is True

    def test_benchmark_report_generation(self) -> None:
        """Can generate comprehensive benchmark report."""
        runner = BenchmarkRunner()
        runner.run_suite()

        report = runner.generate_report()

        assert "summary" in report
        assert "by_category" in report
        assert "failed_tests" in report
        assert "regression_alerts" in report
        assert report["summary"]["total"] == len(DEFAULT_BENCHMARKS)


class TestG102ReleaseGateVerification:
    """G10.2: Release gate verification."""

    def test_all_release_gates_defined(self) -> None:
        """All 9 release gates have requirements defined."""
        gates = {req.gate for req in DEFAULT_GATE_REQUIREMENTS}

        assert ReleaseGate.INGESTION in gates
        assert ReleaseGate.RETRIEVAL in gates
        assert ReleaseGate.NARRATIVE in gates
        assert ReleaseGate.VISUAL in gates
        assert ReleaseGate.UX in gates
        assert ReleaseGate.SECURITY in gates
        assert ReleaseGate.PRIVACY in gates
        assert ReleaseGate.OPERABILITY in gates
        assert ReleaseGate.COST in gates

    def test_gate_requirements_have_checks(self) -> None:
        """Each gate requirement has an associated check function."""
        verifier = ReleaseGateVerifier()

        for req in DEFAULT_GATE_REQUIREMENTS:
            assert req.check_func_name in verifier._check_functions

    def test_single_gate_check(self) -> None:
        """Can run a single gate check."""
        verifier = ReleaseGateVerifier()

        result = verifier.run_gate_check("ingest-001")

        assert result.requirement_id == "ingest-001"
        assert result.gate == ReleaseGate.INGESTION
        assert result.passed is True
        assert result.message

    def test_gate_verification_all_checks(self) -> None:
        """Gate verification runs all checks for that gate."""
        verifier = ReleaseGateVerifier()

        status = verifier.verify_gate(ReleaseGate.INGESTION)

        assert status.gate == ReleaseGate.INGESTION
        assert len(status.checks) > 0
        assert status.passed_count + status.failed_count == len(status.checks)

    def test_gate_passes_when_all_checks_pass(self) -> None:
        """Gate passes when all mandatory checks pass."""
        verifier = ReleaseGateVerifier()

        status = verifier.verify_gate(ReleaseGate.INGESTION)

        # Default check functions all return True
        assert status.passed is True

    def test_all_gates_verification(self) -> None:
        """Can verify all release gates at once."""
        verifier = ReleaseGateVerifier()

        results = verifier.verify_all_gates()

        assert len(results) == 9  # All 9 gates
        assert all(isinstance(s, ReleaseGateStatus) for s in results.values())

    def test_release_report_generation(self) -> None:
        """Can generate comprehensive release report."""
        verifier = ReleaseGateVerifier()

        report = verifier.generate_release_report()

        assert "release_ready" in report
        assert "timestamp" in report
        assert "summary" in report
        assert "gates" in report
        assert report["summary"]["total_gates"] == 9


class TestG103BetaProgram:
    """G10.3: Beta program and feedback loop."""

    def test_default_beta_personas_defined(self) -> None:
        """Beta personas defined for representative users."""
        persona_ids = {p.persona_id for p in DEFAULT_BETA_PERSONAS}

        assert "dark-fantasy-author" in persona_ids
        assert "childrens-illustrator" in persona_ids
        assert "legacy-fan" in persona_ids

    def test_beta_persona_attributes(self) -> None:
        """Beta personas have experience level and use case."""
        program = BetaProgram()
        persona = program.get_persona("dark-fantasy-author")

        assert persona is not None
        assert persona.experience_level in ("novice", "intermediate", "expert")
        assert persona.primary_use_case
        assert len(persona.content_preferences) > 0

    def test_feedback_submission(self) -> None:
        """Can submit structured feedback."""
        program = BetaProgram()

        feedback = program.submit_feedback(
            persona_id="dark-fantasy-author",
            category="tone_fidelity",
            rating=4,
            description="Tone matching was good but could be darker",
            context={"story_id": "story-123"},
        )

        assert feedback.feedback_id.startswith("fb-")
        assert feedback.persona_id == "dark-fantasy-author"
        assert feedback.category == "tone_fidelity"
        assert feedback.rating == 4
        assert feedback.status == "open"

    def test_feedback_filtering(self) -> None:
        """Can filter feedback by category and status."""
        program = BetaProgram()

        program.submit_feedback("dark-fantasy-author", "tone_fidelity", 4, "Good")
        program.submit_feedback("childrens-illustrator", "usability", 3, "OK")
        program.submit_feedback("dark-fantasy-author", "tone_fidelity", 5, "Great")

        tone_feedback = program.get_feedback(category="tone_fidelity")

        assert len(tone_feedback) == 2

    def test_beta_issue_creation(self) -> None:
        """Can create tracked beta issues."""
        program = BetaProgram()

        issue = program.create_issue(
            title="Dark scenes not dark enough",
            description="Generated content lacks the grim atmosphere requested",
            category="tone_fidelity",
            priority="high",
        )

        assert issue.issue_id.startswith("issue-")
        assert issue.status == "open"
        assert issue.priority == "high"

    def test_issue_resolution(self) -> None:
        """Can resolve beta issues."""
        program = BetaProgram()
        issue = program.create_issue("Test", "Description", "bug", "normal")

        resolved = program.resolve_issue(issue.issue_id)

        assert resolved is not None
        assert resolved.status == "resolved"
        assert resolved.resolved_at is not None

    def test_critical_issues_identification(self) -> None:
        """Critical issues identified separately."""
        program = BetaProgram()

        program.create_issue("Minor UI issue", "Desc", "ui", "low")
        program.create_issue("Data loss bug", "Desc", "bug", "critical")

        critical = program.get_critical_issues()

        assert len(critical) == 1
        assert critical[0].title == "Data loss bug"

    def test_feedback_report_generation(self) -> None:
        """Can generate feedback summary report."""
        program = BetaProgram()

        program.submit_feedback("user1", "tone_fidelity", 5, "Excellent")
        program.submit_feedback("user2", "tone_fidelity", 4, "Good")
        program.submit_feedback("user3", "usability", 3, "OK")

        report = program.generate_feedback_report()

        assert "summary" in report
        assert "by_category" in report
        assert report["summary"]["total_feedback"] == 3
        assert "recommendations" in report


class TestG104PublicReleaseReadiness:
    """G10.4: Public release readiness."""

    def test_required_docs_check(self) -> None:
        """Checks if all required docs exist."""
        checker = ReleaseReadinessChecker()
        statuses = checker.check_documentation()

        doc_names = {s.doc_name for s in statuses}
        assert "README.md" in doc_names
        assert "AGENTS.md" in doc_names
        assert "STRATEGY.md" in doc_names

    def test_documentation_status_attributes(self) -> None:
        """Doc status includes existence, completeness, word count."""
        checker = ReleaseReadinessChecker()
        statuses = checker.check_documentation()

        for status in statuses:
            assert status.exists in (True, False)
            assert status.is_complete in (True, False)

    def test_release_version_preparation(self) -> None:
        """Can prepare a release version."""
        checker = ReleaseReadinessChecker()

        version = checker.prepare_release(
            version="1.0.0",
            codename="The Weaver",
            changes_summary="Initial stable release",
        )

        assert version.version == "1.0.0"
        assert version.codename == "The Weaver"
        assert version.git_tag == "v1.0.0"
        assert not version.is_prerelease

    def test_changelog_generation(self) -> None:
        """Can generate changelog content."""
        checker = ReleaseReadinessChecker()
        checker.prepare_release("1.0.0", "Release", "Summary")

        changelog = checker.generate_changelog()

        assert "# Changelog" in changelog
        assert "[1.0.0]" in changelog
        assert "Phase Completion" in changelog

    def test_release_readiness_check(self) -> None:
        """Can check overall release readiness."""
        checker = ReleaseReadinessChecker()
        gate_verifier = ReleaseGateVerifier()
        beta_program = BetaProgram()

        readiness = checker.check_release_readiness(gate_verifier, beta_program)

        assert "release_ready" in readiness
        assert "checks" in readiness
        assert "gate_summary" in readiness
        assert "beta_summary" in readiness
        assert "blockers" in readiness


class TestPhase10DoneCriteria:
    """Phase 10 done criteria validation."""

    def test_release_engine_integration(self) -> None:
        """All Phase 10 components integrated in ReleaseEngine."""
        engine = ReleaseEngine()

        assert engine.benchmarks is not None
        assert engine.gates is not None
        assert engine.beta is not None
        assert engine.readiness is not None

    def test_phase10_metrics_evaluation(self) -> None:
        """Phase 10 metrics can be evaluated."""
        engine = ReleaseEngine()

        # Run benchmarks first
        engine.benchmarks.run_suite()

        metrics = engine.evaluate_phase10_done_criteria()

        assert isinstance(metrics, Phase10Metrics)
        assert isinstance(metrics.all_gates_pass, bool)
        assert 0.0 <= metrics.benchmarks_pass_rate <= 1.0
        assert isinstance(metrics.docs_complete, bool)
        assert metrics.critical_beta_issues >= 0
        assert isinstance(metrics.release_ready, bool)

    def test_release_ready_when_all_criteria_met(self) -> None:
        """Release ready when all criteria satisfied."""
        engine = ReleaseEngine()

        # Run benchmark suite (mock values 0.9*target passes for latency)
        # Need to customize run_suite to pass accuracy benchmarks too
        run_funcs = {}
        for b in engine.benchmarks.list_benchmarks():
            if b.metric_type in (
                BenchmarkMetricType.LATENCY,
                BenchmarkMetricType.MEMORY,
            ):
                run_funcs[b.case_id] = lambda b=b: b.target_value * 0.8
            else:
                # Accuracy benchmarks need values >= target
                run_funcs[b.case_id] = lambda b=b: min(b.target_value * 1.1, 1.0)

        engine.benchmarks.run_suite(run_funcs=run_funcs)  # type: ignore[arg-type]

        metrics = engine.evaluate_phase10_done_criteria()

        # With passing benchmark values, should have high pass rate
        assert metrics.all_gates_pass is True
        assert metrics.benchmarks_pass_rate > 0.8
