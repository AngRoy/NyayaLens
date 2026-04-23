# ADR 0002 — Custom 5-metric engine; no runtime AIF360/Fairlearn dependency

**Status:** Accepted
**Date:** 2026-04-23
**Design doc reference:** §7.2.2 Bias Service

## Context

AIF360 (Apache 2.0) ships 70+ fairness metrics and 10+ mitigation algorithms;
Fairlearn (MIT) ships ~8 metrics with MetricFrame composition. Both are
battle-tested and authoritative. The tempting path is to wrap them.

However:

1. **Dependency risk.** AIF360 pins older scikit-learn and pandas versions;
   mixing with FastAPI, pydantic 2, and recent pandas produced conflicts in
   preliminary investigation.
2. **Scope mismatch.** We need 5 metrics (SPD, DIR, EOD, Consistency,
   Calibration). Pulling in 70+ is dead weight and complicates auditing
   what actually runs against user data.
3. **Edge-case clarity.** Each library handles small groups, missing labels,
   and zero-denominator cases differently. We must choose explicit,
   documented behavior and surface it in the UI (e.g. "n/a, group below
   30 samples"). Opaque library behavior makes this harder.

## Decision

Implement 5 metrics from scratch in pure NumPy / Pandas under
`backend/nyayalens/core/bias/metrics.py`:

- `statistical_parity_difference(y_pred, sensitive)`
- `disparate_impact_ratio(y_pred, sensitive)`
- `equal_opportunity_difference(y_true, y_pred, sensitive)`
- `consistency_score(features, y_pred, n_neighbors=5)` (Zemel et al. 2013)
- `calibration_difference(y_true, y_prob, sensitive, n_bins=10)`
  (grouped ECE pattern)

Plus one mitigation: `reweighting(y_true, sensitive)` (Kamiran/Calders 2012).

**Validation:** port canonical numerical test fixtures from AIF360 and
Fairlearn as JSON into `backend/tests/fixtures/aif360_oracles.json`. Every
metric function must exact-match the oracle within floating-point tolerance.
This gives us independent implementations with library-grade correctness.

**License cleanliness:** no code is copied. Only test fixture numerical values
(which are not copyrightable — they are results of mathematical computation)
are imported. The `NOTICE` file attributes both projects.

## Consequences

**Positive**
- ~300-400 LoC of pure, tested, self-contained code.
- No version-conflict surface with FastAPI/pydantic 2/pandas 2.
- Edge-case behavior documented per metric and surfaced in UI.
- Zero breakage risk from upstream library releases.

**Negative**
- We do not benefit from upstream fixes or new metrics without porting them.
- Mitigation surface is narrow in MVP (reweighting only). Threshold
  optimization and representation balancing are post-MVP.

## Reference file paths (read-only study material)

- `Y:\SolutionChallenge\holisticai\src\holisticai\bias\metrics\_classification.py`
- `Y:\SolutionChallenge\AIF360\aif360\metrics\binary_label_dataset_metric.py`
- `Y:\SolutionChallenge\AIF360\aif360\algorithms\preprocessing\reweighing.py`
- `Y:\SolutionChallenge\fairlearn\fairlearn\metrics\_metric_frame.py`
- `Y:\SolutionChallenge\aequitas\src\aequitas\fairness.py`
