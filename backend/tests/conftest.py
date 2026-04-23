"""Pytest fixtures shared across test modules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def metric_oracles() -> dict[str, Any]:
    """Load the AIF360/Fairlearn-derived numerical oracles.

    See backend/tests/fixtures/metric_oracles.json and NOTICE for attribution.
    """
    with (FIXTURE_DIR / "metric_oracles.json").open() as f:
        return json.load(f)
