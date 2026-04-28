"""FastAPI dependency wiring.

Builds singletons (`AppState`, sinks, recognizers, domain plug, LLM client)
once at app startup and exposes them as `Depends(...)` factories.

Imported by every route file.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from nyayalens.adapters.firebase_auth import (
    InvalidIdentityError,
    TokenVerificationError,
    verify_bearer_token,
)
from nyayalens.adapters.inmemory import (
    InMemoryAuditSink,
    InMemoryStorage,
    RegexPIIRecognizer,
)
from nyayalens.adapters.mock_llm import MockLLMClient
from nyayalens.api.state import AppState
from nyayalens.config import Settings, get_settings
from nyayalens.core._contracts.audit import AuditSink
from nyayalens.core._contracts.llm import LLMClient
from nyayalens.core._contracts.pii import PIIRecognizer
from nyayalens.core._contracts.storage import StorageClient
from nyayalens.core.domains.hiring.registry import HiringDomain
from nyayalens.core.govern.audit import AuditWriter
from nyayalens.core.govern.rbac import Role
from nyayalens.core.schema.pii import PrivacyFilter

log = logging.getLogger(__name__)

# ----- Singletons ---------------------------------------------------------

_state: AppState | None = None
_audit_sink: AuditSink | None = None
_storage: StorageClient | None = None
_pii: PIIRecognizer | None = None
_privacy_filter: PrivacyFilter | None = None
_llm: LLMClient | None = None
_domain: HiringDomain | None = None


def _build_audit_sink(settings: Settings) -> AuditSink:
    """Build the audit sink: Firestore in prod (when flagged), InMemory otherwise."""
    if not settings.use_firestore:
        return InMemoryAuditSink()
    try:
        from nyayalens.adapters.firestore import FirestoreAuditSink

        return FirestoreAuditSink(project=settings.google_cloud_project or None)
    except Exception as exc:
        log.warning("Falling back to InMemoryAuditSink (use_firestore=True but %s)", exc)
        return InMemoryAuditSink()


def _build_storage(settings: Settings) -> StorageClient:
    """Build the storage client: Cloud Storage in prod (when flagged + bucket set)."""
    if not settings.use_firestore or not settings.firebase_storage_bucket:
        return InMemoryStorage()
    try:
        from nyayalens.adapters.firestore import FirestoreStorage

        return FirestoreStorage(
            bucket=settings.firebase_storage_bucket,
            project=settings.google_cloud_project or None,
        )
    except Exception as exc:
        log.warning("Falling back to InMemoryStorage (use_firestore=True but %s)", exc)
        return InMemoryStorage()


def _ensure_singletons(settings: Settings) -> None:
    global _state, _audit_sink, _storage, _pii, _privacy_filter, _llm, _domain
    if _state is None:
        _state = AppState()
    if _audit_sink is None:
        _audit_sink = _build_audit_sink(settings)
    if _storage is None:
        _storage = _build_storage(settings)
    if _pii is None:
        _pii = RegexPIIRecognizer()
    if _privacy_filter is None:
        _privacy_filter = PrivacyFilter(_pii)
    if _domain is None:
        _domain = HiringDomain()
    if _llm is None:
        if settings.gemini_api_key:
            try:
                from nyayalens.adapters.gemini import GeminiAdapter

                _llm = GeminiAdapter(
                    api_key=settings.gemini_api_key,
                    text_model=settings.gemini_model_explain,
                    structured_model=settings.gemini_model_schema,
                    temperature=settings.gemini_temperature,
                    audit_sink=_audit_sink,
                )
                return
            except Exception as exc:
                log.info("Falling back to mock LLM after Gemini init failed: %s", exc)
        _llm = MockLLMClient(audit_sink=_audit_sink, backend_name="mock-llm")


# ----- DI factories -------------------------------------------------------


def get_app_state(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AppState:
    _ensure_singletons(settings)
    assert _state is not None
    return _state


def get_audit_sink(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuditSink:
    _ensure_singletons(settings)
    assert _audit_sink is not None
    return _audit_sink


def get_storage(
    settings: Annotated[Settings, Depends(get_settings)],
) -> StorageClient:
    _ensure_singletons(settings)
    assert _storage is not None
    return _storage


def get_privacy_filter(
    settings: Annotated[Settings, Depends(get_settings)],
) -> PrivacyFilter:
    _ensure_singletons(settings)
    assert _privacy_filter is not None
    return _privacy_filter


def get_llm(
    settings: Annotated[Settings, Depends(get_settings)],
) -> LLMClient:
    _ensure_singletons(settings)
    assert _llm is not None
    return _llm


def get_domain(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HiringDomain:
    _ensure_singletons(settings)
    assert _domain is not None
    return _domain


# ----- Current user -------------------------------------------------------


@dataclass
class CurrentUser:
    uid: str
    name: str
    role: Role
    organization_id: str


def _from_demo_headers(
    x_user_id: str | None,
    x_user_name: str | None,
    x_user_role: str | None,
    x_organization_id: str | None,
) -> CurrentUser:
    """Demo-mode identity (only honoured outside production)."""
    if not x_user_id:
        return CurrentUser(
            uid="demo-uid",
            name="Demo User",
            role="admin",
            organization_id="demo-org",
        )
    role = (x_user_role or "viewer").lower()
    if role not in ("admin", "analyst", "reviewer", "viewer"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown role: {role}",
        )
    return CurrentUser(
        uid=x_user_id,
        name=x_user_name or x_user_id,
        role=role,  # type: ignore[arg-type]
        organization_id=x_organization_id or "demo-org",
    )


def get_current_user(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_user_id: Annotated[str | None, Header()] = None,
    x_user_name: Annotated[str | None, Header()] = None,
    x_user_role: Annotated[str | None, Header()] = None,
    x_organization_id: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    """Identify the caller.

    Production (`NYAYALENS_ENV=prod` and no Firebase emulator running):
        Requires a verified Firebase ID token in the
        ``Authorization: Bearer <token>`` header. The token's custom claims
        ``role`` and ``organizationId`` are used verbatim — no header
        spoofing is allowed.

    Dev / staging / emulator-running:
        Accepts the legacy ``X-User-*`` demo headers as a fallback so the
        local demo flow keeps working. If an Authorization header IS
        present we still try to verify it first.
    """
    if authorization:
        try:
            identity = verify_bearer_token(authorization)
        except InvalidIdentityError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(exc),
            ) from exc
        except TokenVerificationError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        return CurrentUser(
            uid=identity.uid,
            name=identity.name,
            role=identity.role,  # type: ignore[arg-type]
            organization_id=identity.organization_id,
        )

    if settings.is_production and not settings.is_using_emulators:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required in production",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _from_demo_headers(x_user_id, x_user_name, x_user_role, x_organization_id)


def get_audit_writer(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    sink: Annotated[AuditSink, Depends(get_audit_sink)],
) -> AuditWriter:
    return AuditWriter(
        sink,
        organization_id=user.organization_id,
        user_id=user.uid,
        user_name=user.name,
        user_role=user.role,
    )


__all__ = [
    "CurrentUser",
    "get_app_state",
    "get_audit_sink",
    "get_audit_writer",
    "get_current_user",
    "get_domain",
    "get_llm",
    "get_privacy_filter",
    "get_storage",
]
