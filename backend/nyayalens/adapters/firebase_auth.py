"""Firebase ID-token verification adapter.

Production callers verify every request's ``Authorization: Bearer <id_token>``
header via this module. The verified identity carries the org_id and role
from the user's Firebase custom claims, so the backend never trusts the
client to declare its own role.

Imported by:
- ``nyayalens.api.deps.get_current_user``
- ``backend/tests/unit/test_auth.py``

Concrete implementation lives here (in ``adapters/``) per ADR 0001 — the
``firebase_admin`` SDK is a third-party dependency that must not bleed into
``core/``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from threading import Lock
from typing import Any

log = logging.getLogger(__name__)

_INIT_LOCK = Lock()
_INITIALIZED = False


@dataclass(frozen=True, slots=True)
class VerifiedIdentity:
    """A Firebase-Auth-verified identity.

    ``role`` and ``organization_id`` come from the user's custom claims; if
    the claims are missing the verifier raises ``InvalidIdentityError`` so
    a half-configured token cannot pass.
    """

    uid: str
    name: str
    email: str
    role: str
    organization_id: str


class TokenVerificationError(RuntimeError):
    """Raised when a bearer token is missing, malformed, or rejected."""


class InvalidIdentityError(RuntimeError):
    """Raised when a verified token lacks the custom claims we require."""


_ALLOWED_ROLES = ("admin", "analyst", "reviewer", "viewer")


def _ensure_app_initialised() -> None:
    """Initialise the default ``firebase_admin`` app once per process.

    Uses ``GOOGLE_APPLICATION_CREDENTIALS`` (or ADC on Cloud Run). Subsequent
    calls are no-ops. Tests bypass initialisation entirely by injecting a
    fake ``verify_id_token`` via ``set_verifier_for_tests``.
    """
    import contextlib

    global _INITIALIZED
    with _INIT_LOCK:
        if _INITIALIZED:
            return
        import firebase_admin

        with contextlib.suppress(ValueError):
            # ValueError when the default app is already registered (e.g.
            # another import ran first) — idempotent.
            firebase_admin.initialize_app()
        _INITIALIZED = True


# Test seam — production code never calls this. Tests assign a callable
# returning the decoded-claims dict to bypass the real Firebase round-trip.
_test_verifier: object | None = None


def set_verifier_for_tests(verifier: object | None) -> None:
    """Install a stand-in for ``firebase_admin.auth.verify_id_token``.

    The verifier must be a callable taking ``(token: str)`` and returning a
    dict with the standard Firebase claims plus our custom ``role`` and
    ``organizationId`` claims. Pass ``None`` to remove.
    """
    global _test_verifier
    _test_verifier = verifier


def verify_bearer_token(authorization_header: str | None) -> VerifiedIdentity:
    """Verify a ``Bearer <token>`` header and return the resulting identity.

    Raises:
        TokenVerificationError: header missing/malformed, or Firebase rejects
            the token.
        InvalidIdentityError: token verifies but is missing the custom claims
            (``role``, ``organizationId``) the API requires.
    """
    if not authorization_header:
        raise TokenVerificationError("missing Authorization header")
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        raise TokenVerificationError("Authorization header must be 'Bearer <token>'")
    token = parts[1]

    try:
        if _test_verifier is not None:
            claims = _test_verifier(token)  # type: ignore[operator]
        else:
            _ensure_app_initialised()
            from firebase_admin import auth as _auth

            claims = _auth.verify_id_token(token)
    except TokenVerificationError:
        raise
    except InvalidIdentityError:
        raise
    except Exception as exc:
        # firebase_admin raises a hierarchy of errors; map them all to a
        # single 401-shaped exception so we never leak internals.
        raise TokenVerificationError(f"token verification failed: {exc}") from exc

    return _identity_from_claims(claims)


def _identity_from_claims(claims: Any) -> VerifiedIdentity:
    if not isinstance(claims, dict):
        raise TokenVerificationError("verifier returned non-dict claims")

    uid = str(claims.get("uid") or claims.get("user_id") or claims.get("sub") or "")
    if not uid:
        raise InvalidIdentityError("token missing uid / user_id / sub")

    role = str(claims.get("role") or "").lower()
    if role not in _ALLOWED_ROLES:
        raise InvalidIdentityError(
            f"token role custom-claim must be one of {_ALLOWED_ROLES!r}; got {role!r}"
        )

    organization_id = str(claims.get("organizationId") or claims.get("organization_id") or "")
    if not organization_id:
        raise InvalidIdentityError("token missing organizationId custom claim")

    name = str(claims.get("name") or claims.get("display_name") or uid)
    email = str(claims.get("email") or "")

    return VerifiedIdentity(
        uid=uid,
        name=name,
        email=email,
        role=role,
        organization_id=organization_id,
    )


__all__ = [
    "InvalidIdentityError",
    "TokenVerificationError",
    "VerifiedIdentity",
    "set_verifier_for_tests",
    "verify_bearer_token",
]
