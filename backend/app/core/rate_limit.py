"""Minimal in-memory per-IP rate limiting for expensive endpoints.

Single-process, in-memory sliding window. Sufficient for a hackathon demo
running one backend process; it does not coordinate across multiple worker
processes/instances (would need a shared store such as Redis for that —
intentionally out of scope here).
"""

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

_DEFAULT_WINDOW_SECONDS = 60.0

# key -> list of monotonic timestamps within the current window
_hits: dict[str, list[float]] = defaultdict(list)


def rate_limit(key_prefix: str, limit: int, window_seconds: float = _DEFAULT_WINDOW_SECONDS):
    """Build a FastAPI dependency limiting a client IP to `limit` calls per window."""

    async def _dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"{key_prefix}:{client_ip}"
        now = time.monotonic()
        cutoff = now - window_seconds

        hits = _hits[key]
        while hits and hits[0] < cutoff:
            hits.pop(0)

        if len(hits) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please wait a moment and try again.",
            )
        hits.append(now)

    return _dependency
