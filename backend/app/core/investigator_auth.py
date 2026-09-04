"""Investigator identity derived from a verified Supabase Auth token.

This sits alongside — not instead of — the existing ``X-API-Key`` shared
secret. That secret authenticates the *deployment* (browser -> Next proxy ->
FastAPI); this module authenticates the *person*. Both are required to change
anything attributable to an investigator.

Identity is only ever taken from a cryptographically verified token. The
frontend cannot name an investigator in a request body or header and have the
backend believe it, which is what stops one officer impersonating another.

Supabase signs user access tokens with ES256 and publishes the matching public
keys at the project's JWKS endpoint, so verification needs no shared secret and
no service-role key.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.core.config import settings

logger = logging.getLogger(__name__)

# Bearer is optional at the dependency level: endpoints decide whether an
# investigator is required. auto_error=False keeps unauthenticated calls on the
# legacy path instead of turning them into 403s.
_bearer = HTTPBearer(auto_error=False)

# JWKS rarely rotates; refetching per request would add a network round trip to
# every call. PyJWKClient caches keys, and this caches the client itself.
_jwks_client: PyJWKClient | None = None
_jwks_client_url: str | None = None


@dataclass(frozen=True)
class Investigator:
    """An authenticated investigation officer."""

    user_id: str
    email: str | None
    full_name: str

    @property
    def initial(self) -> str:
        """First letter of the display name, for the presence avatar."""
        return (self.full_name or "?").strip()[:1].upper() or "?"


def _supabase_url() -> str:
    return str(getattr(settings, "SUPABASE_URL", "") or "").rstrip("/")


def _jwks_url() -> str:
    configured = getattr(settings, "SUPABASE_JWKS_URL", "")
    if configured:
        return str(configured)
    base = _supabase_url()
    return f"{base}/auth/v1/.well-known/jwks.json" if base else ""


def _get_jwks_client() -> PyJWKClient | None:
    global _jwks_client, _jwks_client_url

    url = _jwks_url()
    if not url:
        return None
    if _jwks_client is None or _jwks_client_url != url:
        _jwks_client = PyJWKClient(url, cache_keys=True, lifespan=3600)
        _jwks_client_url = url
    return _jwks_client


def reset_jwks_cache() -> None:
    """Drop the cached JWKS client (used by tests and after config changes)."""
    global _jwks_client, _jwks_client_url
    _jwks_client = None
    _jwks_client_url = None


def _display_name(claims: dict) -> str:
    """Pick the best available human name, never inventing one."""
    metadata = claims.get("user_metadata") or {}
    for candidate in (
        metadata.get("full_name"),
        metadata.get("name"),
        claims.get("full_name"),
    ):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    email = claims.get("email")
    # Local part of the email is a real fact about the account, unlike a
    # fabricated name; the UI can still render an initial from it.
    if isinstance(email, str) and email.strip():
        return email.split("@", 1)[0]
    return "Unknown investigator"


def verify_supabase_token(token: str) -> Investigator:
    """Verify a Supabase access token and return its investigator.

    Raises:
        HTTPException: 401 when the token is missing, malformed, expired, or
            not signed by the configured Supabase project.
    """
    client = _get_jwks_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Investigator authentication is not configured on the server.",
        )
    try:
        signing_key = client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience=getattr(settings, "SUPABASE_JWT_AUDIENCE", "authenticated"),
            options={"require": ["exp", "sub"]},
        )
    except HTTPException:
        raise
    except Exception as exc:
        # Deliberately opaque: never echo token internals back to the caller.
        logger.info("investigator token rejected: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired investigator session.",
        ) from exc

    subject = claims.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Investigator token is missing a subject.",
        )
    return Investigator(
        user_id=str(subject),
        email=claims.get("email"),
        full_name=_display_name(claims),
    )


async def get_optional_investigator(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Investigator | None:
    """Return the signed-in investigator, or None when no token was sent.

    Endpoints that predate investigator identity keep working unauthenticated;
    a *present but invalid* token is still rejected, so a bad session can never
    be silently downgraded to anonymous.
    """
    if credentials is None or not credentials.credentials:
        return None
    return verify_supabase_token(credentials.credentials)


async def require_investigator(
    investigator: Investigator | None = Depends(get_optional_investigator),
) -> Investigator:
    """Return the signed-in investigator, rejecting anonymous callers."""
    if investigator is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="An investigator session is required for this action.",
        )
    return investigator
