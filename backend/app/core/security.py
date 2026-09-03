"""Minimal shared-secret API authentication.

A single server-side secret (``API_SHARED_SECRET``) is compared against the
``X-API-Key`` request header. This is intentionally not a user/session or
RBAC system — it exists to stop unauthenticated internet access to the
investigation API for the hackathon demo. Case-level ownership/authorization
is a documented follow-up (see README), not implemented here.
"""

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str | None = Depends(_api_key_header)) -> None:
    """Reject the request unless it presents the configured shared secret.

    Fails closed: an unset ``API_SHARED_SECRET`` is treated as a server
    misconfiguration, never as "authentication disabled".
    """
    expected = settings.API_SHARED_SECRET
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured on the server.",
        )
    if not api_key or not secrets.compare_digest(api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API credential.",
        )
