"""Rate limiting module for The Loom.

Provides:
- Token bucket rate limiting
- Per-endpoint rate limits
- Per-user and per-IP tracking
- Redis-compatible storage (with in-memory fallback)
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 60
    burst_size: int = 10
    window_seconds: int = 60


@dataclass
class RateLimitStatus:
    """Current rate limit status for a client."""

    allowed: bool
    remaining: int
    reset_at: float
    retry_after: float | None
    limit: int

    def to_headers(self) -> dict[str, str]:
        """Convert to HTTP response headers."""
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(int(self.reset_at)),
        }
        if self.retry_after:
            headers["Retry-After"] = str(int(self.retry_after))
        return headers


class TokenBucket:
    """Token bucket for rate limiting."""

    def __init__(
        self,
        capacity: int,
        refill_rate: float,  # tokens per second
    ) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket."""
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def get_remaining(self) -> int:
        """Get remaining tokens."""
        self._refill()
        return int(self.tokens)

    def get_reset_time(self) -> float:
        """Get timestamp when bucket will be full."""
        tokens_needed = self.capacity - self.tokens
        seconds_needed = tokens_needed / self.refill_rate
        return time.time() + seconds_needed


class RateLimiter:
    """Rate limiter with multiple strategies."""

    # Default rate limits by endpoint category
    DEFAULT_LIMITS: dict[str, RateLimitConfig] = {
        "default": RateLimitConfig(requests_per_minute=60, burst_size=10),
        "auth": RateLimitConfig(
            requests_per_minute=10, burst_size=5
        ),  # Stricter for auth
        "generate": RateLimitConfig(
            requests_per_minute=20, burst_size=5
        ),  # Generation endpoints
        "api": RateLimitConfig(requests_per_minute=120, burst_size=20),  # API endpoints
        "websocket": RateLimitConfig(
            requests_per_minute=300, burst_size=50
        ),  # WebSocket messages
    }

    def __init__(self) -> None:
        # In-memory storage for buckets
        # Structure: {category: {client_id: TokenBucket}}
        self._buckets: dict[str, dict[str, TokenBucket]] = defaultdict(dict)
        self._configs: dict[str, RateLimitConfig] = dict(self.DEFAULT_LIMITS)
        self._last_access: dict[str, float] = {}  # For cleanup

    def configure(
        self, category: str, requests_per_minute: int, burst_size: int
    ) -> None:
        """Configure rate limit for a category."""
        self._configs[category] = RateLimitConfig(
            requests_per_minute=requests_per_minute,
            burst_size=burst_size,
            window_seconds=60,
        )

    def check_rate_limit(
        self,
        client_id: str,
        category: str = "default",
        cost: int = 1,
    ) -> RateLimitStatus:
        """Check if a request is allowed under rate limits."""
        config = self._configs.get(category, self._configs["default"])

        # Get or create bucket
        bucket = self._get_bucket(client_id, category, config)

        # Try to consume tokens
        allowed = bucket.consume(cost)

        # Update last access
        self._last_access[f"{category}:{client_id}"] = time.time()

        # Calculate retry after
        retry_after = None
        if not allowed:
            tokens_needed = cost - bucket.tokens
            retry_after = tokens_needed / config.requests_per_minute * 60

        return RateLimitStatus(
            allowed=allowed,
            remaining=bucket.get_remaining(),
            reset_at=bucket.get_reset_time(),
            retry_after=retry_after,
            limit=config.burst_size,
        )

    def _get_bucket(
        self,
        client_id: str,
        category: str,
        config: RateLimitConfig,
    ) -> TokenBucket:
        """Get or create a token bucket for a client."""
        if client_id not in self._buckets[category]:
            refill_rate = config.requests_per_minute / 60.0
            self._buckets[category][client_id] = TokenBucket(
                capacity=config.burst_size,
                refill_rate=refill_rate,
            )

        return self._buckets[category][client_id]

    def cleanup_old_buckets(self, max_age_seconds: float = 3600) -> int:
        """Remove buckets that haven't been accessed recently.

        Returns number of buckets removed.
        """
        now = time.time()
        removed = 0

        keys_to_remove = [
            key
            for key, last_access in self._last_access.items()
            if now - last_access > max_age_seconds
        ]

        for key in keys_to_remove:
            category, client_id = key.split(":", 1)
            if category in self._buckets:
                self._buckets[category].pop(client_id, None)
            del self._last_access[key]
            removed += 1

        return removed

    def get_client_stats(self, client_id: str) -> dict[str, Any]:
        """Get rate limit stats for a client across all categories."""
        stats = {}
        for category in self._configs:
            bucket = self._buckets[category].get(client_id)
            if bucket:
                stats[category] = {
                    "remaining": bucket.get_remaining(),
                    "reset_at": bucket.get_reset_time(),
                    "limit": bucket.capacity,
                }
        return stats


class RateLimitMiddleware:
    """Middleware-style rate limiting for FastAPI."""

    def __init__(self, limiter: RateLimiter | None = None) -> None:
        self._limiter = limiter or RateLimiter()

        # Endpoint to category mapping
        self._endpoint_categories: dict[str, str] = {
            # Auth endpoints
            "/api/auth/login": "auth",
            "/api/auth/register": "auth",
            "/api/auth/refresh": "auth",
            # Generation endpoints
            "/api/writer/generate": "generate",
            "/api/artist/generate": "generate",
            "/api/artist/generate-panels": "generate",
            "/api/lora/train": "generate",
            # WebSocket
            "/api/ws/": "websocket",
        }

    def get_category(self, path: str) -> str:
        """Get rate limit category for a path."""
        # Check exact matches first
        if path in self._endpoint_categories:
            return self._endpoint_categories[path]

        # Check prefixes
        for prefix, category in self._endpoint_categories.items():
            if path.startswith(prefix):
                return category

        return "default"

    def is_exempt(self, path: str) -> bool:
        """Check if a path is exempt from rate limiting."""
        exempt_prefixes = [
            "/health",
            "/api/ops/health",
            "/api/ops/metrics/prometheus",
        ]
        return any(path.startswith(p) for p in exempt_prefixes)

    def check_request(
        self,
        client_id: str,
        path: str,
        method: str = "GET",
    ) -> RateLimitStatus:
        """Check rate limit for a request."""
        if self.is_exempt(path):
            return RateLimitStatus(
                allowed=True,
                remaining=999999,
                reset_at=time.time() + 3600,
                retry_after=None,
                limit=999999,
            )

        category = self.get_category(path)

        # Different costs for different methods
        cost = 1
        if method in ["POST", "PUT", "DELETE"]:
            cost = 2
        if category == "generate":
            cost = 5  # Generation is expensive

        return self._limiter.check_rate_limit(client_id, category, cost)


# Global rate limiter instance
_rate_limiter: RateLimiter | None = None
_rate_limit_middleware: RateLimitMiddleware | None = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def get_rate_limit_middleware() -> RateLimitMiddleware:
    """Get the global rate limit middleware."""
    global _rate_limit_middleware
    if _rate_limit_middleware is None:
        _rate_limit_middleware = RateLimitMiddleware(get_rate_limiter())
    return _rate_limit_middleware
