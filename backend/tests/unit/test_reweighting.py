"""Unit tests for Kamiran/Calders reweighting (`apply_reweighting`)."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from nyayalens.core.mitigate.reweighting import apply_reweighting, reweighting_weights


def _binary_disparity_frame(
    group_a_pos: int, group_a_neg: int, group_b_pos: int, group_b_neg: int
) -> pd.DataFrame:
    """Build a 2-group DataFrame with the supplied (pos, neg) counts per group."""
    rows = (
        [{"sens": "A", "y": 1}] * group_a_pos
        + [{"sens": "A", "y": 0}] * group_a_neg
        + [{"sens": "B", "y": 1}] * group_b_pos
        + [{"sens": "B", "y": 0}] * group_b_neg
    )
    return pd.DataFrame(rows)


def test_weights_have_one_value_per_row() -> None:
    df = _binary_disparity_frame(75, 25, 30, 70)
    weights = reweighting_weights(df["sens"], df["y"])
    assert len(weights) == len(df)


def test_apply_reweighting_records_before_and_after_rates() -> None:
    df = _binary_disparity_frame(75, 25, 30, 70)
    result = apply_reweighting(df, sensitive_column="sens", outcome_column="y")
    # Before: A = 75/100 = 0.75, B = 30/100 = 0.30
    assert math.isclose(result.rates_before["A"], 0.75, abs_tol=1e-9)
    assert math.isclose(result.rates_before["B"], 0.30, abs_tol=1e-9)


def test_apply_reweighting_equalises_group_rates_after() -> None:
    df = _binary_disparity_frame(75, 25, 30, 70)
    result = apply_reweighting(df, sensitive_column="sens", outcome_column="y")
    # Reweighting under Kamiran/Calders aligns the (group, outcome) joint to
    # the product of marginals — group rates after weighting equal P(y=1).
    p_pos = float((df["y"] == 1).mean())
    assert math.isclose(result.rates_after["A"], p_pos, abs_tol=1e-9)
    assert math.isclose(result.rates_after["B"], p_pos, abs_tol=1e-9)


def test_apply_reweighting_dir_moves_towards_one() -> None:
    df = _binary_disparity_frame(75, 25, 30, 70)
    result = apply_reweighting(df, sensitive_column="sens", outcome_column="y")
    assert result.dir_before < 0.80  # documented disparity in the fixture
    assert result.dir_after == pytest.approx(1.0, abs=1e-9)


def test_apply_reweighting_raises_for_missing_sensitive_column() -> None:
    df = _binary_disparity_frame(10, 10, 10, 10)
    with pytest.raises(ValueError, match="sensitive_column"):
        apply_reweighting(df, sensitive_column="missing", outcome_column="y")


def test_apply_reweighting_raises_for_missing_outcome_column() -> None:
    df = _binary_disparity_frame(10, 10, 10, 10)
    with pytest.raises(ValueError, match="outcome_column"):
        apply_reweighting(df, sensitive_column="sens", outcome_column="missing")


def test_dir_before_is_none_when_privileged_rate_is_zero() -> None:
    """Zero positive-outcome rate makes DIR undefined — must serialise as null,
    not as JSON-invalid NaN.
    """
    df = _binary_disparity_frame(0, 50, 0, 50)
    result = apply_reweighting(df, sensitive_column="sens", outcome_column="y")
    assert result.dir_before is None
    assert result.dir_after is None
