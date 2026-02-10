"""Observability and monitoring layer for The Loom.

Provides:
- Structured logging with correlation IDs
- Metrics collection (latency, throughput, errors)
- SLO (Service Level Objective) tracking
- Health checks
- Prometheus-compatible metrics export
"""

from __future__ import annotations

import asyncio
import functools
import json
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any, TypeVar


class MetricType(Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class SLOStatus(Enum):
    """Status of an SLO."""

    HEALTHY = "healthy"
    WARNING = "warning"
    BREACH = "breach"


@dataclass
class MetricValue:
    """A single metric value."""

    name: str
    value: float
    labels: dict[str, str]
    timestamp: float


@dataclass
class HistogramBucket:
    """A histogram bucket."""

    upper_bound: float
    count: int


@dataclass
class HistogramMetric:
    """Histogram metric data."""

    name: str
    buckets: list[HistogramBucket]
    sum_value: float
    count: int
    labels: dict[str, str]
    timestamp: float


@dataclass
class SLODefinition:
    """Definition of a Service Level Objective."""

    name: str
    description: str
    target: float  # Target value (e.g., 0.99 for 99%)
    threshold: float  # Threshold for warning
    metric_name: str
    metric_type: str  # "latency", "availability", "error_rate"


@dataclass
class SLOResult:
    """Current status of an SLO."""

    definition: SLODefinition
    current_value: float
    status: SLOStatus
    window_minutes: int
    measured_at: str


@dataclass
class HealthStatus:
    """Health check status."""

    component: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    checked_at: str
    response_time_ms: float


@dataclass
class LogEntry:
    """Structured log entry."""

    timestamp: str
    level: str
    message: str
    correlation_id: str
    service: str
    context: dict[str, Any]


class MetricsCollector:
    """Collects and stores metrics."""

    # Default histogram buckets (in seconds for latency)
    DEFAULT_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]

    def __init__(self, max_history: int = 10000) -> None:
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}
        self._histogram_buckets: dict[str, list[float]] = {}
        self._history: deque[MetricValue] = deque(maxlen=max_history)
        self._lock_time = time.time()

    def counter(self, name: str, labels: dict[str, str] | None = None) -> None:
        """Increment a counter metric."""
        key = self._key(name, labels or {})
        self._counters[key] = self._counters.get(key, 0) + 1
        self._history.append(
            MetricValue(
                name=name,
                value=1,
                labels=labels or {},
                timestamp=time.time(),
            )
        )

    def gauge(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ) -> None:
        """Set a gauge metric."""
        key = self._key(name, labels or {})
        self._gauges[key] = value
        self._history.append(
            MetricValue(
                name=name,
                value=value,
                labels=labels or {},
                timestamp=time.time(),
            )
        )

    def histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
        buckets: list[float] | None = None,
    ) -> None:
        """Record a histogram value."""
        key = self._key(name, labels or {})

        if key not in self._histograms:
            self._histograms[key] = []
            self._histogram_buckets[key] = buckets or self.DEFAULT_BUCKETS

        self._histograms[key].append(value)
        self._history.append(
            MetricValue(
                name=name,
                value=value,
                labels=labels or {},
                timestamp=time.time(),
            )
        )

    def get_counter(self, name: str, labels: dict[str, str] | None = None) -> float:
        """Get current counter value."""
        key = self._key(name, labels or {})
        return self._counters.get(key, 0)

    def get_gauge(
        self, name: str, labels: dict[str, str] | None = None
    ) -> float | None:
        """Get current gauge value."""
        key = self._key(name, labels or {})
        return self._gauges.get(key)

    def get_histogram(
        self, name: str, labels: dict[str, str] | None = None
    ) -> HistogramMetric | None:
        """Get histogram data."""
        key = self._key(name, labels or {})
        values = self._histograms.get(key)

        if not values:
            return None

        buckets = self._histogram_buckets.get(key, self.DEFAULT_BUCKETS)
        bucket_counts: list[int] = [0] * len(buckets)

        for value in values:
            for i, bucket in enumerate(buckets):
                if value <= bucket:
                    bucket_counts[i] += 1
                    break

        return HistogramMetric(
            name=name,
            buckets=[
                HistogramBucket(upper_bound=b, count=c)
                for b, c in zip(buckets, bucket_counts, strict=False)
            ],
            sum_value=sum(values),
            count=len(values),
            labels=labels or {},
            timestamp=time.time(),
        )

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all metrics."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histogram_count": {k: len(v) for k, v in self._histograms.items()},
        }

    def _key(self, name: str, labels: dict[str, str]) -> str:
        """Create a unique key for metric lookup."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"


class SLOTracker:
    """Tracks Service Level Objectives."""

    # Default SLOs
    DEFAULT_SLOS: list[SLODefinition] = [
        SLODefinition(
            name="availability",
            description="Service availability",
            target=0.999,  # 99.9%
            threshold=0.99,  # 99%
            metric_name="request_success_rate",
            metric_type="availability",
        ),
        SLODefinition(
            name="latency_p95",
            description="95th percentile latency",
            target=0.5,  # 500ms
            threshold=1.0,  # 1000ms
            metric_name="request_latency_seconds",
            metric_type="latency",
        ),
        SLODefinition(
            name="error_rate",
            description="Error rate",
            target=0.001,  # 0.1%
            threshold=0.01,  # 1%
            metric_name="error_rate",
            metric_type="error_rate",
        ),
    ]

    def __init__(
        self,
        metrics: MetricsCollector,
        window_minutes: int = 60,
    ) -> None:
        self._metrics = metrics
        self._window_minutes = window_minutes
        self._slos: dict[str, SLODefinition] = {
            slo.name: slo for slo in self.DEFAULT_SLOS
        }

    def add_slo(self, slo: SLODefinition) -> None:
        """Add a custom SLO."""
        self._slos[slo.name] = slo

    def check_slo(self, name: str) -> SLOResult | None:
        """Check current status of an SLO."""
        slo = self._slos.get(name)
        if not slo:
            return None

        # Calculate current value based on SLO type
        if slo.metric_type == "availability":
            current = self._calculate_availability()
        elif slo.metric_type == "latency":
            current = self._calculate_latency_percentile(0.95)
        elif slo.metric_type == "error_rate":
            current = self._calculate_error_rate()
        else:
            return None

        # Determine status
        if slo.metric_type in ["availability"]:
            # Higher is better
            if current >= slo.target:
                status = SLOStatus.HEALTHY
            elif current >= slo.threshold:
                status = SLOStatus.WARNING
            else:
                status = SLOStatus.BREACH
        else:
            # Lower is better (latency, error_rate)
            if current <= slo.target:
                status = SLOStatus.HEALTHY
            elif current <= slo.threshold:
                status = SLOStatus.WARNING
            else:
                status = SLOStatus.BREACH

        return SLOResult(
            definition=slo,
            current_value=current,
            status=status,
            window_minutes=self._window_minutes,
            measured_at=datetime.now(UTC).isoformat(),
        )

    def check_all_slos(self) -> list[SLOResult]:
        """Check all SLOs."""
        return [
            result
            for name in self._slos
            if (result := self.check_slo(name)) is not None
        ]

    def _calculate_availability(self) -> float:
        """Calculate availability rate."""
        success = self._metrics.get_counter(
            "http_requests_total", {"status": "success"}
        )
        total = self._metrics.get_counter("http_requests_total")
        return success / total if total > 0 else 1.0

    def _calculate_latency_percentile(self, p: float) -> float:
        """Calculate latency percentile."""
        hist = self._metrics.get_histogram("request_duration_seconds")
        if not hist or not hist.buckets:
            return 0.0
        # Simplified - return bucket upper bound closest to percentile
        target = int(hist.count * p)
        cumulative = 0
        for bucket in hist.buckets:
            cumulative += bucket.count
            if cumulative >= target:
                return bucket.upper_bound
        return hist.buckets[-1].upper_bound if hist.buckets else 0.0

    def _calculate_error_rate(self) -> float:
        """Calculate error rate."""
        errors = self._metrics.get_counter("http_requests_total", {"status": "error"})
        total = self._metrics.get_counter("http_requests_total")
        return errors / total if total > 0 else 0.0


class HealthChecker:
    """Performs health checks on system components."""

    def __init__(self) -> None:
        self._checks: dict[str, Callable[[], HealthStatus]] = {}

    def register_check(
        self,
        component: str,
        check_fn: Callable[[], HealthStatus],
    ) -> None:
        """Register a health check function."""
        self._checks[component] = check_fn

    def check(self, component: str) -> HealthStatus | None:
        """Run a specific health check."""
        if component not in self._checks:
            return None

        start = time.time()
        try:
            result = self._checks[component]()
            result.response_time_ms = (time.time() - start) * 1000
            return result
        except Exception as e:
            return HealthStatus(
                component=component,
                status="unhealthy",
                message=str(e),
                checked_at=datetime.now(UTC).isoformat(),
                response_time_ms=(time.time() - start) * 1000,
            )

    def check_all(self) -> list[HealthStatus]:
        """Run all health checks."""
        results: list[HealthStatus] = []
        for component in self._checks:
            result = self.check(component)
            if result is not None:
                results.append(result)
        return results

    def get_overall_status(self) -> dict[str, Any]:
        """Get overall health status."""
        results = self.check_all()

        unhealthy = [r for r in results if r.status == "unhealthy"]
        degraded = [r for r in results if r.status == "degraded"]

        if unhealthy:
            status = "unhealthy"
        elif degraded:
            status = "degraded"
        else:
            status = "healthy"

        return {
            "status": status,
            "components": [
                {
                    "component": r.component,
                    "status": r.status,
                    "message": r.message,
                    "responseTimeMs": r.response_time_ms,
                }
                for r in results
            ],
            "checkedAt": datetime.now(UTC).isoformat(),
        }


class StructuredLogger:
    """Structured logging with correlation IDs."""

    def __init__(self, service: str = "loom") -> None:
        self._service = service
        self._entries: deque[LogEntry] = deque(maxlen=1000)

    def log(
        self,
        level: str,
        message: str,
        correlation_id: str = "",
        **context: Any,
    ) -> None:
        """Log a message."""
        entry = LogEntry(
            timestamp=datetime.now(UTC).isoformat(),
            level=level,
            message=message,
            correlation_id=correlation_id,
            service=self._service,
            context=context,
        )
        self._entries.append(entry)

        # Also print for console visibility
        context_str = json.dumps(context) if context else ""
        print(f"[{entry.timestamp}] {level}: {message} {context_str}")

    def debug(self, message: str, correlation_id: str = "", **context: Any) -> None:
        self.log("DEBUG", message, correlation_id, **context)

    def info(self, message: str, correlation_id: str = "", **context: Any) -> None:
        self.log("INFO", message, correlation_id, **context)

    def warning(self, message: str, correlation_id: str = "", **context: Any) -> None:
        self.log("WARNING", message, correlation_id, **context)

    def error(self, message: str, correlation_id: str = "", **context: Any) -> None:
        self.log("ERROR", message, correlation_id, **context)

    def get_recent(self, level: str | None = None, limit: int = 100) -> list[LogEntry]:
        """Get recent log entries."""
        entries = list(self._entries)
        if level:
            entries = [e for e in entries if e.level == level]
        return entries[-limit:]


class Observability:
    """Main observability facade."""

    def __init__(self) -> None:
        self.metrics = MetricsCollector()
        self.slo = SLOTracker(self.metrics)
        self.health = HealthChecker()
        self.logger = StructuredLogger()

    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        """Record an HTTP request."""
        labels = {"method": method, "path": path, "status": str(status_code)}

        # Counter for total requests
        self.metrics.counter("http_requests_total", labels)

        # Histogram for latency
        self.metrics.histogram("request_duration_seconds", duration_seconds, labels)

        # Success/error counters
        if 200 <= status_code < 400:
            self.metrics.counter("http_requests_total", {**labels, "status": "success"})
        else:
            self.metrics.counter("http_requests_total", {**labels, "status": "error"})

    def record_generation(
        self,
        generation_type: str,  # "text" or "image"
        success: bool,
        duration_seconds: float,
        tokens_used: int = 0,
    ) -> None:
        """Record a generation operation."""
        status = "success" if success else "failure"
        labels = {"type": generation_type, "status": status}

        self.metrics.counter("generation_total", labels)
        self.metrics.histogram("generation_duration_seconds", duration_seconds, labels)

        if tokens_used > 0:
            self.metrics.counter("tokens_used_total", {"type": generation_type})
            self.metrics.gauge("tokens_per_request", tokens_used, labels)

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []

        # Counters
        for key, value in self.metrics._counters.items():
            lines.append(f"# TYPE {key.split('{')[0]} counter")
            lines.append(f"{key} {value}")

        # Gauges
        for key, value in self.metrics._gauges.items():
            lines.append(f"# TYPE {key.split('{')[0]} gauge")
            lines.append(f"{key} {value}")

        # Histograms
        for key, _hist_data in self.metrics._histograms.items():
            name = key.split("{")[0]
            hist = self.metrics.get_histogram(name)
            if hist:
                lines.append(f"# TYPE {name} histogram")
                for bucket in hist.buckets:
                    lines.append(
                        f'{name}_bucket{{le="{bucket.upper_bound}"}} {bucket.count}'
                    )
                lines.append(f"{name}_sum {hist.sum_value}")
                lines.append(f"{name}_count {hist.count}")

        return "\n".join(lines)


# Type variable for the decorator
T = TypeVar("T", bound=Callable[..., Any])


def timed(
    metric_name: str, observability: Observability | None = None
) -> Callable[[T], T]:
    """Decorator to time function execution."""

    def decorator(func: T) -> T:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start
                obs = observability or _global_observability
                obs.metrics.histogram(metric_name, duration)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start
                obs = observability or _global_observability
                obs.metrics.histogram(metric_name, duration)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return wrapper  # type: ignore

    return decorator


# Global observability instance
_global_observability: Observability = Observability()


def get_observability() -> Observability:
    """Get the global observability instance."""
    return _global_observability
