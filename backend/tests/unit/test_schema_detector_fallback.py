"""Schema detector fallback tests."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from nyayalens.adapters.inmemory import RegexPIIRecognizer
from nyayalens.adapters.mock_llm import MockLLMClient
from nyayalens.core._contracts.llm import LLMPayload
from nyayalens.core.schema.detector import SchemaDetector
from nyayalens.core.schema.parser import ParsedDataset, parse_dataset
from nyayalens.core.schema.pii import PrivacyFilter


class SlowLLMClient:
    async def generate_structured(
        self,
        payload: LLMPayload,
        json_schema: dict[str, Any],
        *,
        audit_id: str | None = None,
    ) -> dict[str, Any]:
        await asyncio.sleep(1)
        return {}

    async def generate_text(
        self,
        payload: LLMPayload,
        *,
        audit_id: str | None = None,
    ) -> str:
        return ""


def _parsed_demo_shape() -> ParsedDataset:
    return parse_dataset(
        b"Roll_No,Name,Email,Gender,Category,CGPA,Score,Placed\n"
        b"21CS001,Asha Rao,asha@example.test,Female,OBC,8.2,0.91,1\n"
        b"21CS002,Rahul Sen,rahul@example.test,Male,General,7.4,0.41,0\n",
        filename="placement.csv",
    )


@pytest.mark.asyncio
async def test_schema_detector_falls_back_when_llm_has_no_fixture() -> None:
    detector = SchemaDetector(
        MockLLMClient(),
        PrivacyFilter(RegexPIIRecognizer()),
    )

    result = await detector.detect(_parsed_demo_shape(), domain="hiring")

    assert result.raw_response["_source"] == "local_heuristic_fallback"
    assert {s.column for s in result.sensitive_attributes} == {"Gender", "Category"}
    assert result.outcome is not None
    assert result.outcome.column == "Placed"
    assert result.score_column == "Score"
    assert {"Roll_No", "Name", "Email"}.issubset(result.identifier_columns)


@pytest.mark.asyncio
async def test_schema_detector_falls_back_when_llm_times_out() -> None:
    detector = SchemaDetector(
        SlowLLMClient(),
        PrivacyFilter(RegexPIIRecognizer()),
        llm_timeout_seconds=0.01,
    )

    result = await detector.detect(_parsed_demo_shape(), domain="hiring")

    assert result.raw_response["_source"] == "local_heuristic_fallback"
    assert result.outcome is not None
    assert result.outcome.column == "Placed"
