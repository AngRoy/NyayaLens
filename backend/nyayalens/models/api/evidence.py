"""Data-provenance type — propagates everywhere downstream.

Required field on every Pydantic model that flows from upload to PDF. The
contract test in `backend/tests/contract/test_provenance_propagation.py`
asserts this is non-null on every public DTO.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProvenanceKind = Literal["real", "benchmark", "synthetic", "llm_generated"]


class DataProvenance(BaseModel):
    """Where a piece of evidence came from. Drives the UI badge colour."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: ProvenanceKind
    label: str = Field(
        description=(
            "Short label for UI display (e.g. 'College placement 2023-25', "
            "'Adult Income (UCI)', 'Synthetic seeded DIR=0.33')."
        )
    )
    note: str = Field(
        default="",
        description="Optional caveat shown alongside the label.",
    )
