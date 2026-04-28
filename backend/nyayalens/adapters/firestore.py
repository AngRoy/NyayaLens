"""Firestore + Cloud Storage adapters for production persistence.

Implements:
- ``FirestoreAuditSink`` — `core/_contracts/audit.AuditSink`
- ``FirestoreStorage`` — `core/_contracts/storage.StorageClient`

Wired in `api/deps.py` when ``settings.use_firestore`` is true. Otherwise
the in-memory adapters (`adapters/inmemory.py`) keep working — pytest,
the demo flow, and any environment without GCP creds run unchanged.

The audit-trail collection is service-account-only on the create side
(`shared/firestore.rules` enforces ``allow create: if false`` for clients);
this adapter writes via the backend's service account so the rule is
bypassed by design.

Imported by:
- ``nyayalens.api.deps`` — production wiring (gated by ``use_firestore``)
- ``backend/tests/integration/test_firestore_persistence.py`` — emulator-only

Concrete implementation lives here (in ``adapters/``) per ADR 0001 — the
``firebase_admin`` and ``google.cloud.*`` SDKs are third-party deps that
must not bleed into ``core/``.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from threading import Lock
from typing import Any, BinaryIO, cast

from nyayalens.core._contracts.audit import AuditEvent, AuditSink

log = logging.getLogger(__name__)

_INIT_LOCK = Lock()
_INITIALIZED = False

# Test seams — production code never sets these. Tests inject fakes to
# avoid touching real Firestore / Cloud Storage.
_test_firestore_client: object | None = None
_test_storage_client: object | None = None


def set_firestore_for_tests(
    firestore_client: object | None = None,
    storage_client: object | None = None,
) -> None:
    """Install stand-ins for the Firestore / Storage clients.

    Pass ``None`` for either to remove the override. Tests use this to
    inject the firestore-emulator-backed Client without re-running
    ``firebase_admin.initialize_app``.
    """
    global _test_firestore_client, _test_storage_client
    _test_firestore_client = firestore_client
    _test_storage_client = storage_client


def _ensure_firebase_app_initialised() -> None:
    """Initialise the default ``firebase_admin`` app once per process.

    No-op if already initialised by the auth adapter. Uses
    ``GOOGLE_APPLICATION_CREDENTIALS`` (or ADC on Cloud Run) for auth.
    """
    import contextlib

    global _INITIALIZED
    with _INIT_LOCK:
        if _INITIALIZED:
            return
        import firebase_admin

        with contextlib.suppress(ValueError):
            firebase_admin.initialize_app()
        _INITIALIZED = True


# ---------------------------------------------------------------------------
# Firestore audit sink
# ---------------------------------------------------------------------------


class FirestoreAuditSink(AuditSink):
    """`AuditSink` that writes to ``audit_trail/{event_id}`` in Firestore."""

    def __init__(self, *, project: str | None = None) -> None:
        self._project = project

    def _client(self) -> Any:
        if _test_firestore_client is not None:
            return _test_firestore_client
        _ensure_firebase_app_initialised()
        from google.cloud import firestore

        return firestore.Client(project=self._project) if self._project else firestore.Client()

    @staticmethod
    def _to_dict(event: AuditEvent) -> dict[str, Any]:
        return {
            "event_id": str(event.event_id),
            "audit_id": event.audit_id,
            "organization_id": event.organization_id,
            "action": event.action,
            "user_id": event.user_id,
            "user_name": event.user_name,
            "user_role": event.user_role,
            "timestamp": event.timestamp,
            "ip_address": event.ip_address,
            "details": dict(event.details),
        }

    async def write(self, event: AuditEvent) -> None:
        client = self._client()
        doc_id = str(event.event_id)
        try:
            client.collection("audit_trail").document(doc_id).set(self._to_dict(event))
        except Exception as exc:
            log.warning("Firestore audit write failed (%s): %s", event.action, exc)
            raise

    async def write_batch(self, events: list[AuditEvent]) -> None:
        client = self._client()
        batch = client.batch()
        for event in events:
            ref = client.collection("audit_trail").document(str(event.event_id))
            batch.set(ref, self._to_dict(event))
        try:
            batch.commit()
        except Exception as exc:
            log.warning("Firestore audit batch write failed: %s", exc)
            raise


# ---------------------------------------------------------------------------
# Cloud Storage adapter
# ---------------------------------------------------------------------------


class FirestoreStorage:
    """`StorageClient` backed by Google Cloud Storage.

    The class name retains the ``Firestore*`` prefix so the production
    wiring path is colocated; the underlying API is `google-cloud-storage`,
    not Firestore.
    """

    def __init__(self, *, bucket: str, project: str | None = None) -> None:
        if not bucket:
            raise ValueError("FirestoreStorage requires a non-empty bucket name.")
        self._bucket_name = bucket
        self._project = project

    def _bucket(self) -> Any:
        if _test_storage_client is not None:
            client: Any = _test_storage_client
        else:
            _ensure_firebase_app_initialised()
            from google.cloud import storage  # type: ignore[attr-defined]

            if self._project:
                client = storage.Client(project=self._project)
            else:
                client = storage.Client()
        return client.bucket(self._bucket_name)

    async def upload(
        self,
        path: str,
        content: BinaryIO | bytes,
        *,
        content_type: str | None = None,
    ) -> str:
        blob = self._bucket().blob(path)
        if isinstance(content, bytes | bytearray):
            blob.upload_from_string(bytes(content), content_type=content_type)
        else:
            blob.upload_from_file(content, content_type=content_type)
        return f"gs://{self._bucket_name}/{path}"

    async def download(self, path: str) -> bytes:
        blob = self._bucket().blob(path)
        if not blob.exists():
            raise FileNotFoundError(path)
        return cast(bytes, blob.download_as_bytes())

    async def exists(self, path: str) -> bool:
        return bool(self._bucket().blob(path).exists())

    async def delete(self, path: str) -> None:
        blob = self._bucket().blob(path)
        if blob.exists():
            blob.delete()

    async def signed_url(
        self,
        path: str,
        *,
        expires_in: timedelta = timedelta(minutes=15),
    ) -> str:
        blob = self._bucket().blob(path)
        return cast(str, blob.generate_signed_url(version="v4", expiration=expires_in))


__all__ = [
    "FirestoreAuditSink",
    "FirestoreStorage",
    "set_firestore_for_tests",
]
