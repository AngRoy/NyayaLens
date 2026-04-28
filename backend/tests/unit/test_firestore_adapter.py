"""Tests for the Firestore + Cloud Storage adapter shapes.

Uses the in-process test seam ``set_firestore_for_tests`` so we never
touch real GCP. The integration test that exercises the real emulator
lives at ``tests/integration/test_firestore_persistence.py`` and is
skipped unless ``FIRESTORE_EMULATOR_HOST`` is set in the environment.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from nyayalens.adapters.firestore import (
    FirestoreAuditSink,
    FirestoreStorage,
    set_firestore_for_tests,
)
from nyayalens.core._contracts.audit import AuditEvent

# --- Tiny in-process fakes -------------------------------------------------


class _FakeDoc:
    def __init__(self, store: dict[str, dict[str, Any]], doc_id: str) -> None:
        self._store = store
        self.doc_id = doc_id

    def set(self, payload: dict[str, Any]) -> None:
        self._store[self.doc_id] = dict(payload)


class _FakeCollection:
    def __init__(self, store: dict[str, dict[str, Any]]) -> None:
        self._store = store

    def document(self, doc_id: str) -> _FakeDoc:
        return _FakeDoc(self._store, doc_id)


class _FakeBatch:
    def __init__(self, store: dict[str, dict[str, Any]]) -> None:
        self._store = store
        self._pending: list[tuple[str, dict[str, Any]]] = []

    def set(self, ref: _FakeDoc, payload: dict[str, Any]) -> None:
        self._pending.append((ref.doc_id, dict(payload)))

    def commit(self) -> None:
        for doc_id, payload in self._pending:
            self._store[doc_id] = payload
        self._pending.clear()


class _FakeFirestoreClient:
    def __init__(self) -> None:
        self.audit_trail: dict[str, dict[str, Any]] = {}

    def collection(self, name: str) -> _FakeCollection:
        assert name == "audit_trail", "fake only knows audit_trail"
        return _FakeCollection(self.audit_trail)

    def batch(self) -> _FakeBatch:
        return _FakeBatch(self.audit_trail)


class _FakeBlob:
    def __init__(self, bucket: _FakeBucket, path: str) -> None:
        self._bucket = bucket
        self._path = path

    def upload_from_string(self, data: bytes, content_type: str | None = None) -> None:
        self._bucket.store[self._path] = bytes(data)

    def upload_from_file(self, fileobj: Any, content_type: str | None = None) -> None:
        self._bucket.store[self._path] = fileobj.read()

    def download_as_bytes(self) -> bytes:
        return self._bucket.store[self._path]

    def exists(self) -> bool:
        return self._path in self._bucket.store

    def delete(self) -> None:
        self._bucket.store.pop(self._path, None)

    def generate_signed_url(self, *, version: str, expiration: Any) -> str:
        return f"https://signed.example/{self._bucket.name}/{self._path}?v={version}"


class _FakeBucket:
    def __init__(self, name: str) -> None:
        self.name = name
        self.store: dict[str, bytes] = {}

    def blob(self, path: str) -> _FakeBlob:
        return _FakeBlob(self, path)


class _FakeStorageClient:
    def __init__(self) -> None:
        self._buckets: dict[str, _FakeBucket] = {}

    def bucket(self, name: str) -> _FakeBucket:
        if name not in self._buckets:
            self._buckets[name] = _FakeBucket(name)
        return self._buckets[name]


# --- Fixtures --------------------------------------------------------------


@pytest.fixture
def fake_clients() -> Iterator[tuple[_FakeFirestoreClient, _FakeStorageClient]]:
    fs = _FakeFirestoreClient()
    storage = _FakeStorageClient()
    set_firestore_for_tests(firestore_client=fs, storage_client=storage)
    try:
        yield fs, storage
    finally:
        set_firestore_for_tests(firestore_client=None, storage_client=None)


def _make_event(action: str = "schema_confirmed") -> AuditEvent:
    return AuditEvent(
        event_id=uuid4(),
        audit_id="audit-1",
        organization_id="demo-org",
        action=action,  # type: ignore[arg-type]
        user_id="demo-uid",
        user_name="Demo Reviewer",
        user_role="admin",
        timestamp=datetime.now(UTC),
        details={"k": "v"},
    )


# --- FirestoreAuditSink ----------------------------------------------------


async def test_audit_sink_writes_single_event(
    fake_clients: tuple[_FakeFirestoreClient, _FakeStorageClient],
) -> None:
    fs, _ = fake_clients
    sink = FirestoreAuditSink()
    event = _make_event("schema_confirmed")

    await sink.write(event)

    stored = fs.audit_trail[str(event.event_id)]
    assert stored["action"] == "schema_confirmed"
    assert stored["organization_id"] == "demo-org"
    assert stored["details"] == {"k": "v"}


async def test_audit_sink_writes_batch(
    fake_clients: tuple[_FakeFirestoreClient, _FakeStorageClient],
) -> None:
    fs, _ = fake_clients
    sink = FirestoreAuditSink()
    events = [_make_event("recourse_filed"), _make_event("recourse_resolved")]

    await sink.write_batch(events)

    assert {e["action"] for e in fs.audit_trail.values()} == {
        "recourse_filed",
        "recourse_resolved",
    }


# --- FirestoreStorage ------------------------------------------------------


async def test_storage_upload_then_download_round_trip(
    fake_clients: tuple[_FakeFirestoreClient, _FakeStorageClient],
) -> None:
    _, _ = fake_clients
    s = FirestoreStorage(bucket="demo-bucket")

    uri = await s.upload("reports/demo/audit.pdf", b"%PDF-FAKE", content_type="application/pdf")
    assert uri == "gs://demo-bucket/reports/demo/audit.pdf"
    assert await s.exists("reports/demo/audit.pdf") is True
    body = await s.download("reports/demo/audit.pdf")
    assert body == b"%PDF-FAKE"


async def test_storage_download_missing_raises_filenotfound(
    fake_clients: tuple[_FakeFirestoreClient, _FakeStorageClient],
) -> None:
    _, _ = fake_clients
    s = FirestoreStorage(bucket="demo-bucket")
    with pytest.raises(FileNotFoundError):
        await s.download("does/not/exist.pdf")


async def test_storage_delete_is_idempotent(
    fake_clients: tuple[_FakeFirestoreClient, _FakeStorageClient],
) -> None:
    _, _ = fake_clients
    s = FirestoreStorage(bucket="demo-bucket")
    await s.upload("k.bin", b"x")
    await s.delete("k.bin")
    await s.delete("k.bin")  # second call must not raise
    assert await s.exists("k.bin") is False


async def test_storage_signed_url_includes_bucket_and_path(
    fake_clients: tuple[_FakeFirestoreClient, _FakeStorageClient],
) -> None:
    _, _ = fake_clients
    s = FirestoreStorage(bucket="demo-bucket")
    url = await s.signed_url("reports/x.pdf")
    assert "demo-bucket" in url
    assert "reports/x.pdf" in url


def test_storage_constructor_rejects_empty_bucket() -> None:
    with pytest.raises(ValueError):
        FirestoreStorage(bucket="")
