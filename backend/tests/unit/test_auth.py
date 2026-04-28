"""Unit tests for `nyayalens.adapters.firebase_auth.verify_bearer_token`.

The Firebase Admin SDK round-trip is replaced with an in-process verifier
via `set_verifier_for_tests`, so these tests never touch the network.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest

from nyayalens.adapters.firebase_auth import (
    InvalidIdentityError,
    TokenVerificationError,
    set_verifier_for_tests,
    verify_bearer_token,
)


@pytest.fixture(autouse=True)
def _reset_verifier() -> Generator[None, None, None]:
    """Each test installs its own verifier; clear it on teardown."""
    set_verifier_for_tests(None)
    yield
    set_verifier_for_tests(None)


_VALID_CLAIMS = {
    "uid": "u-001",
    "name": "Demo Reviewer",
    "email": "demo@example.test",
    "role": "admin",
    "organizationId": "org-001",
}


def test_returns_verified_identity_for_valid_token() -> None:
    set_verifier_for_tests(lambda _token: dict(_VALID_CLAIMS))

    identity = verify_bearer_token("Bearer fake.jwt.token")

    assert identity.uid == "u-001"
    assert identity.role == "admin"
    assert identity.organization_id == "org-001"
    assert identity.email == "demo@example.test"


def test_missing_header_raises_token_verification_error() -> None:
    with pytest.raises(TokenVerificationError, match="missing"):
        verify_bearer_token(None)


def test_empty_header_raises_token_verification_error() -> None:
    with pytest.raises(TokenVerificationError, match="missing"):
        verify_bearer_token("")


def test_malformed_header_without_bearer_prefix_raises() -> None:
    with pytest.raises(TokenVerificationError, match="Bearer"):
        verify_bearer_token("Basic dXNlcjpwYXNz")


def test_malformed_header_without_token_raises() -> None:
    with pytest.raises(TokenVerificationError, match="Bearer"):
        verify_bearer_token("Bearer ")


def test_verifier_failure_is_wrapped_as_token_verification_error() -> None:
    def boom(_token: str) -> dict[str, str]:
        raise RuntimeError("expired")

    set_verifier_for_tests(boom)

    with pytest.raises(TokenVerificationError, match="expired"):
        verify_bearer_token("Bearer fake.jwt.token")


def test_token_missing_role_claim_raises_invalid_identity() -> None:
    claims = dict(_VALID_CLAIMS)
    del claims["role"]
    set_verifier_for_tests(lambda _t: claims)

    with pytest.raises(InvalidIdentityError, match="role"):
        verify_bearer_token("Bearer fake.jwt.token")


def test_token_with_unknown_role_raises_invalid_identity() -> None:
    claims = dict(_VALID_CLAIMS)
    claims["role"] = "superuser"
    set_verifier_for_tests(lambda _t: claims)

    with pytest.raises(InvalidIdentityError, match="role"):
        verify_bearer_token("Bearer fake.jwt.token")


def test_token_missing_organization_id_raises_invalid_identity() -> None:
    claims = dict(_VALID_CLAIMS)
    del claims["organizationId"]
    set_verifier_for_tests(lambda _t: claims)

    with pytest.raises(InvalidIdentityError, match="organizationId"):
        verify_bearer_token("Bearer fake.jwt.token")


def test_organization_id_falls_back_to_snake_case_claim() -> None:
    claims = dict(_VALID_CLAIMS)
    del claims["organizationId"]
    claims["organization_id"] = "org-002"
    set_verifier_for_tests(lambda _t: claims)

    identity = verify_bearer_token("Bearer fake.jwt.token")

    assert identity.organization_id == "org-002"
