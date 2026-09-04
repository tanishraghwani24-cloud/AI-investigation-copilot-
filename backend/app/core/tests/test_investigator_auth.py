"""Tests for deriving investigator identity from a Supabase token.

Identity must come only from a verified signature. These tests sign tokens with
a locally generated ES256 key and point the verifier at the matching public key,
so they exercise the real verification path without touching the network.
"""

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException

from app.core import investigator_auth
from app.core.investigator_auth import (
    Investigator,
    verify_supabase_token,
)


@pytest.fixture()
def signing_key():
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture(autouse=True)
def local_jwks(monkeypatch, signing_key):
    """Point the verifier at our test key instead of the live JWKS endpoint."""
    class _Key:
        key = signing_key.public_key()

    class _Client:
        def get_signing_key_from_jwt(self, _token):
            return _Key()

    investigator_auth.reset_jwks_cache()
    monkeypatch.setattr(investigator_auth, "_get_jwks_client", lambda: _Client())
    yield
    investigator_auth.reset_jwks_cache()


def _token(signing_key, **claims):
    payload = {
        "sub": "11111111-2222-3333-4444-555555555555",
        "aud": "authenticated",
        "role": "authenticated",
        "email": "rahul.sharma@hollabank.com",
        "exp": int(time.time()) + 3600,
        "user_metadata": {"full_name": "Rahul Sharma"},
    }
    payload.update(claims)
    return jwt.encode(payload, signing_key, algorithm="ES256")


class TestIdentityExtraction:
    def test_a_valid_token_yields_the_investigator(self, signing_key):
        investigator = verify_supabase_token(_token(signing_key))

        assert investigator.user_id == "11111111-2222-3333-4444-555555555555"
        assert investigator.full_name == "Rahul Sharma"
        assert investigator.email == "rahul.sharma@hollabank.com"

    def test_the_avatar_initial_comes_from_the_name(self, signing_key):
        assert verify_supabase_token(_token(signing_key)).initial == "R"

    def test_initial_is_derived_not_hardcoded(self, signing_key):
        token = _token(signing_key, user_metadata={"full_name": "priya nair"})

        assert verify_supabase_token(token).initial == "P"

    def test_a_name_falls_back_to_the_email_local_part_never_invented(self, signing_key):
        token = _token(signing_key, user_metadata={}, email="dana.ross@hollabank.com")

        investigator = verify_supabase_token(token)

        assert investigator.full_name == "dana.ross"
        assert investigator.initial == "D"

    def test_an_identity_with_neither_name_nor_email_is_explicit(self, signing_key):
        investigator = verify_supabase_token(
            _token(signing_key, user_metadata={}, email=None)
        )

        assert investigator.full_name == "Unknown investigator"


class TestRejection:
    """A caller must not be able to assert an identity it cannot prove."""

    def test_a_token_signed_by_someone_else_is_rejected(self, signing_key):
        attacker = ec.generate_private_key(ec.SECP256R1())
        forged = _token(attacker, user_metadata={"full_name": "Impersonator"})

        with pytest.raises(HTTPException) as exc:
            verify_supabase_token(forged)
        assert exc.value.status_code == 401

    def test_an_expired_token_is_rejected(self, signing_key):
        with pytest.raises(HTTPException) as exc:
            verify_supabase_token(_token(signing_key, exp=int(time.time()) - 10))
        assert exc.value.status_code == 401

    def test_a_token_for_another_audience_is_rejected(self, signing_key):
        with pytest.raises(HTTPException) as exc:
            verify_supabase_token(_token(signing_key, aud="some-other-service"))
        assert exc.value.status_code == 401

    def test_a_token_without_a_subject_is_rejected(self, signing_key):
        payload = {
            "aud": "authenticated", "exp": int(time.time()) + 3600,
            "user_metadata": {"full_name": "No Subject"},
        }
        with pytest.raises(HTTPException) as exc:
            verify_supabase_token(jwt.encode(payload, signing_key, algorithm="ES256"))
        assert exc.value.status_code == 401

    def test_garbage_is_rejected(self):
        with pytest.raises(HTTPException) as exc:
            verify_supabase_token("not-a-token")
        assert exc.value.status_code == 401

    def test_the_error_never_leaks_token_internals(self, signing_key):
        attacker = ec.generate_private_key(ec.SECP256R1())

        with pytest.raises(HTTPException) as exc:
            verify_supabase_token(_token(attacker))
        assert "Invalid or expired investigator session." == exc.value.detail


class TestConfiguration:
    def test_an_unconfigured_server_fails_closed(self, monkeypatch):
        """No JWKS configured must not mean 'accept anything'."""
        monkeypatch.setattr(investigator_auth, "_get_jwks_client", lambda: None)

        with pytest.raises(HTTPException) as exc:
            verify_supabase_token("anything")
        assert exc.value.status_code == 503


class TestDependencies:
    @pytest.mark.asyncio
    async def test_no_credentials_means_anonymous_not_an_error(self):
        assert await investigator_auth.get_optional_investigator(None) is None

    @pytest.mark.asyncio
    async def test_a_present_but_invalid_token_is_not_downgraded_to_anonymous(self):
        """A broken session must fail loudly rather than act unattributed."""
        from fastapi.security import HTTPAuthorizationCredentials

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bogus")
        with pytest.raises(HTTPException):
            await investigator_auth.get_optional_investigator(creds)

    @pytest.mark.asyncio
    async def test_require_investigator_rejects_anonymous(self):
        with pytest.raises(HTTPException) as exc:
            await investigator_auth.require_investigator(None)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_require_investigator_passes_a_verified_identity_through(self):
        identity = Investigator(user_id="u1", email="a@b.com", full_name="Ada Byron")

        assert await investigator_auth.require_investigator(identity) is identity
