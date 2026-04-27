"""Fairness-metric unit tests.

Each oracle entry in `backend/tests/fixtures/metric_oracles.json` produces a
test. Values were derived from the mathematical definitions of SPD and
Disparate Impact (see NOTICE for attribution to AIF360/Fairlearn).

We use `math.isclose` with a tight tolerance rather than exact equality
because floating-point arithmetic on pandas groupbys produces values that
are within 1e-15 of the "theoretical" result.
"""

from __future__ import annotations

import math
from typing import Any

import pytest

from nyayalens.core.bias.metrics import (
    MIN_GROUP_SIZE,
    disparate_impact_ratio,
    statistical_parity_difference,
)

ABS_TOL = 1e-9


def _approx(actual: float | None, expected: float | None) -> bool:
    if expected is None:
        return actual is None
    if actual is None:
        return False
    return math.isclose(actual, expected, abs_tol=ABS_TOL)


# ---------------------------------------------------------------------------
# SPD
# ---------------------------------------------------------------------------


def test_spd_oracles(metric_oracles: dict[str, Any]) -> None:
    for oracle in metric_oracles["spd"]:
        result = statistical_parity_difference(
            oracle["y_pred"],
            oracle["sensitive"],
            positive_label=oracle["positive_label"],
        )
        expected = oracle["expected"]

        assert _approx(result.value, expected["value"]), (
            f"[{oracle['name']}] SPD value {result.value!r} != {expected['value']!r}"
        )
        assert result.privileged == expected["privileged"], oracle["name"]
        assert result.unprivileged == expected["unprivileged"], oracle["name"]
        assert result.reliable == expected["reliable"], oracle["name"]
        for group, rate in expected["group_values"].items():
            assert _approx(result.group_values[group], rate), (
                f"[{oracle['name']}] group {group} rate mismatch"
            )


def test_spd_on_design_doc_hero_scenario() -> None:
    """The demo narrative depends on specific numbers at S05 in the design doc.

    Women placed at 0.56 rate vs men at ~0.99. Expected SPD ≈ -0.4338.
    Guards against accidental changes that would silently drift the demo.
    """
    y_pred = [1] * 150 + [0] * 1 + [1] * 100 + [0] * 44
    sensitive = ["A"] * 151 + ["B"] * 100 + ["B"] * 44
    assert len(y_pred) == len(sensitive) == 295

    result = statistical_parity_difference(y_pred, sensitive)
    # Exact values: A = 150/151, B = 100/144
    expected = (100 / 144) - (150 / 151)
    assert _approx(result.value, expected)
    assert result.privileged == "A"
    assert result.unprivileged == "B"
    assert result.reliable is True  # both groups > MIN_GROUP_SIZE


# ---------------------------------------------------------------------------
# DIR
# ---------------------------------------------------------------------------


def test_dir_oracles(metric_oracles: dict[str, Any]) -> None:
    for oracle in metric_oracles["dir"]:
        result = disparate_impact_ratio(
            oracle["y_pred"],
            oracle["sensitive"],
            positive_label=oracle["positive_label"],
        )
        expected = oracle["expected"]

        if "value" in expected:
            assert _approx(result.value, expected["value"]), (
                f"[{oracle['name']}] DIR value {result.value!r} != {expected['value']!r}"
            )

        if "group_values" in expected:
            for group, rate in expected["group_values"].items():
                assert _approx(result.group_values[group], rate), (
                    f"[{oracle['name']}] group {group} rate mismatch"
                )
        elif "group_values_approx" in expected:
            # Used for large fixtures where we approve to 1e-4.
            for group, rate in expected["group_values_approx"].items():
                assert math.isclose(result.group_values[group], rate, abs_tol=1e-4), (
                    f"[{oracle['name']}] group {group} approx rate mismatch"
                )

        if "privileged" in expected:
            assert result.privileged == expected["privileged"], oracle["name"]
        if "unprivileged" in expected:
            assert result.unprivileged == expected["unprivileged"], oracle["name"]
        if "reliable" in expected:
            assert result.reliable == expected["reliable"], oracle["name"]


def test_dir_eeoc_80_percent_rule_exactly_on_threshold() -> None:
    """EEOC 80% rule: DIR=0.80 is the threshold. Our metric should return 0.80 exactly."""
    # Group A: 5/5 = 1.0, Group B: 4/5 = 0.80. DIR = 0.80/1.0 = 0.80
    y_pred = [1, 1, 1, 1, 1, 1, 1, 1, 1, 0]
    sensitive = ["A"] * 5 + ["B"] * 5
    result = disparate_impact_ratio(y_pred, sensitive)
    assert _approx(result.value, 0.80)
    assert result.threshold == 0.80
    assert result.threshold_direction == "below"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_edge_case_oracles(metric_oracles: dict[str, Any]) -> None:
    metric_map = {
        "spd": statistical_parity_difference,
        "dir": disparate_impact_ratio,
    }
    for case in metric_oracles["edge_cases"]:
        fn = metric_map[case["expected_metric"]]
        result = fn(case["y_pred"], case["sensitive"], positive_label=case["positive_label"])
        expected = case["expected"]

        assert _approx(result.value, expected["value"]), case["case"]
        assert result.reliable == expected["reliable"], case["case"]
        if "reason_contains" in expected:
            assert expected["reason_contains"].lower() in result.reason.lower(), (
                f"[{case['case']}] reason {result.reason!r} missing {expected['reason_contains']!r}"
            )


def test_dir_all_zero_positive_rate_does_not_divide_by_zero() -> None:
    """When NO record is positive, every group's rate is 0 → DIR is 0/0, undefined.

    We must not raise a ZeroDivisionError; instead return value=None with an
    explanatory reason. A single group with zero rate against a non-zero
    privileged group is *defined* and returns DIR=0.0 — see the
    ``moderate_disparity_dir`` oracle.
    """
    y_pred = [0, 0, 0, 0, 0]
    sensitive = ["A", "A", "A", "B", "B"]
    result = disparate_impact_ratio(y_pred, sensitive)
    assert result.value is None
    assert result.reliable is False
    assert "undefined" in result.reason.lower()


def test_dir_with_zero_unprivileged_rate_is_defined() -> None:
    """Group B has 2/3 positive, group A has 0. DIR = 0 / (2/3) = 0.0."""
    y_pred = [0, 0, 0, 1, 1, 0]
    sensitive = ["A", "A", "A", "B", "B", "B"]
    result = disparate_impact_ratio(y_pred, sensitive)
    assert result.value == pytest.approx(0.0)
    assert result.privileged == "B"
    assert result.unprivileged == "A"


def test_spd_missing_values_are_dropped_not_imputed() -> None:
    """Rows with NaN in any input are dropped — see `_align`."""
    import numpy as np
    import pandas as pd

    y_pred = pd.Series([1, 1, 0, np.nan, 1])
    sensitive = pd.Series(["A", "A", "B", "B", "B"])
    result = statistical_parity_difference(y_pred, sensitive)
    # After drop: y_pred = [1, 1, 0, 1], sensitive = [A, A, B, B]
    # A: 1.0, B: 0.5 → SPD = 0.5 - 1.0 = -0.5
    assert _approx(result.value, -0.5)


def test_min_group_size_constant_matches_design_doc() -> None:
    """Design doc §7.2.2: groups below n=30 flagged as insufficient sample size."""
    assert MIN_GROUP_SIZE == 30


def test_small_group_flag_triggers_unreliable_but_still_computes_value() -> None:
    """We don't hide the number; we attach a warning. Design doc wants both."""
    y_pred = [1, 1, 0, 1, 0, 1, 0, 0]
    sensitive = ["A"] * 4 + ["B"] * 4
    result = statistical_parity_difference(y_pred, sensitive)
    assert result.value is not None
    assert result.reliable is False
    assert "minimum sample size" in result.reason.lower()
