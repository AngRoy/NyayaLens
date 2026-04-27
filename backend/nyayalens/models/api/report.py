"""PDF report DTOs."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ReportStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: str
    status: Literal["queued", "generating", "ready", "failed"]
    download_url: str | None = None
    generated_at: datetime | None = None
    error: str | None = None
