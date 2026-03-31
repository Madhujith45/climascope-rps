"""
ClimaScope – Rate Limiter Middleware
Simple in-memory rate limiting for auth-sensitive endpoints.
"""

import time
import logging
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import HTTPException, status, Request

logger = logging.getLogger(__name__)


class RateLimiter:
    """In-memory sliding-window rate limiter.

    Tracks requests per client key (IP or email) within a configurable
    time window. Raises HTTP 429 when the limit is exceeded.
    """

    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # key -> list of timestamps
        self._store: Dict[str, list] = defaultdict(list)

    def _cleanup(self, key: str) -> None:
        """Remove timestamps outside the current window."""
        cutoff = time.time() - self.window_seconds
        self._store[key] = [t for t in self._store[key] if t > cutoff]

    def check(self, key: str) -> Tuple[bool, int]:
        """Check if a request is allowed.

        Returns (allowed, remaining_requests).
        """
        self._cleanup(key)
        current = len(self._store[key])
        remaining = max(0, self.max_requests - current)
        return current < self.max_requests, remaining

    def record(self, key: str) -> None:
        """Record a request timestamp."""
        self._store[key].append(time.time())

    def check_and_record(self, key: str) -> int:
        """Check rate limit and record request. Raises HTTP 429 if exceeded.

        Returns remaining requests.
        """
        allowed, remaining = self.check(key)
        if not allowed:
            logger.warning("Rate limit exceeded for key=%s", key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Try again in {self.window_seconds} seconds.",
            )
        self.record(key)
        return remaining


# ── Pre-configured limiters ──────────────────────────────────────────────────

# OTP requests: max 10 per minute
otp_limiter = RateLimiter(max_requests=10, window_seconds=60)

# Login attempts: max 30 per minute
login_limiter = RateLimiter(max_requests=30, window_seconds=60)

# Data ingestion: max 120 per minute
data_limiter = RateLimiter(max_requests=120, window_seconds=60)


def get_client_ip(request: Request) -> str:
    """Extract client IP from the request (handles proxied requests)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
