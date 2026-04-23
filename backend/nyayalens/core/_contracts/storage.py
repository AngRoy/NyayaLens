"""Object-store contract.

Backs dataset uploads, generated PDF reports, and heatmap PNGs. Concrete
implementation lives in `adapters.storage.CloudStorageClient`; tests use
an in-memory fake.
"""

from __future__ import annotations

from datetime import timedelta
from typing import BinaryIO, Protocol, runtime_checkable


@runtime_checkable
class StorageClient(Protocol):
    """Blob storage abstraction.

    All paths are logical (e.g. `datasets/<org>/<audit>/raw_upload.csv`);
    adapters are free to map them onto real bucket layouts.
    """

    async def upload(
        self,
        path: str,
        content: BinaryIO,
        *,
        content_type: str | None = None,
    ) -> str:
        """Store bytes at `path`. Return the absolute storage URI."""
        ...

    async def download(self, path: str) -> bytes:
        """Return the bytes stored at `path`. Raises `FileNotFoundError`
        if the object does not exist.
        """
        ...

    async def exists(self, path: str) -> bool:
        """True iff an object exists at `path`."""
        ...

    async def delete(self, path: str) -> None:
        """Remove the object at `path`. Idempotent — no error if missing."""
        ...

    async def signed_url(
        self,
        path: str,
        *,
        expires_in: timedelta = timedelta(minutes=15),
    ) -> str:
        """Return a time-limited pre-signed URL for direct client download."""
        ...


__all__ = ["StorageClient"]
