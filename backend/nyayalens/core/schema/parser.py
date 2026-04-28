"""CSV / XLSX parser + type inference.

Pure I/O on a `BinaryIO` stream from an upload endpoint. Returns a
`ParsedDataset` dataclass holding the dataframe and per-column structural
summary. Never sends user-row content downstream — that is the
PrivacyFilter's responsibility.

Imported by:
- `core/schema/detector.py` orchestrator (forthcoming)
- `core/schema/__init__.py` re-exports
- `api/datasets.py` upload endpoint (forthcoming)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any, BinaryIO, Literal

import numpy as np
import pandas as pd

ColumnType = Literal["numeric", "categorical", "datetime", "text", "boolean"]


@dataclass(frozen=True, slots=True)
class ColumnInfo:
    name: str
    dtype: ColumnType
    null_count: int
    unique_count: int
    sample_values: list[str]
    top_values: list[dict[str, Any]] = field(default_factory=list)
    numeric_summary: dict[str, float] | None = None


@dataclass(frozen=True, slots=True)
class DataQuality:
    """Aggregate data-quality stats surfaced on the upload response.

    Field semantics:
      - ``missing_cell_pct``: fraction of NaN cells across the whole frame, in [0, 1].
      - ``duplicate_row_pct``: duplicate rows divided by total rows, in [0, 1].
      - ``type_consistency_pct``: share of columns whose inferred dtype is
        coercible without error on every non-null cell. Range [0, 1].
      - ``overall_score``: ``1 - max(missing, duplicates, 1 - type_consistency)``
        clamped to [0, 1]. A single dashboard number; the three components
        above give the diagnostic detail.
      - ``warnings``: human-readable strings the UI renders as chips.
    """

    row_count: int
    column_count: int
    missing_cell_pct: float
    duplicate_row_pct: float
    type_consistency_pct: float
    overall_score: float
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ParsedDataset:
    df: pd.DataFrame
    columns: list[ColumnInfo]
    row_count: int
    sample_rows: list[dict[str, Any]]
    quality: DataQuality | None = None


_TEXT_THRESHOLD: int = 50  # avg string length above which a column reads as free text
_MIN_ROW_COUNT_FOR_RELIABILITY: int = 30  # mirrors core.bias.metrics.MIN_GROUP_SIZE
_DATE_LIKE_RE = re.compile(r"^\s*(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s*$")


def _looks_datetime_like(sample: pd.Series) -> bool:
    values = sample.dropna().astype(str).str.strip()
    if values.empty:
        return False
    matches = values.str.match(_DATE_LIKE_RE)
    return bool(matches.mean() >= 0.8)


def _infer_column_type(series: pd.Series) -> ColumnType:
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        non_null = series.dropna().unique()
        if set(non_null.tolist()).issubset({0, 1}):
            return "boolean"
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if series.dtype == object:
        sample = series.dropna().head(20)
        if not sample.empty and _looks_datetime_like(sample):
            try:
                parsed = pd.to_datetime(sample, errors="raise", utc=False)
                if parsed.notna().all():
                    return "datetime"
            except (ValueError, TypeError):
                pass
        avg_len = series.dropna().astype(str).str.len().mean()
        if not pd.isna(avg_len) and avg_len > _TEXT_THRESHOLD:
            return "text"
    return "categorical"


def _column_info(name: str, series: pd.Series) -> ColumnInfo:
    dtype = _infer_column_type(series)
    sample_raw = series.dropna().astype(str).head(5).tolist()
    top_values: list[dict[str, Any]] = []
    numeric_summary: dict[str, float] | None = None

    if dtype in ("categorical", "boolean"):
        vc = series.value_counts(dropna=True).head(5)
        top_values = [{"value": str(k), "count": int(v)} for k, v in vc.items()]
    elif dtype == "numeric":
        numeric = pd.to_numeric(series, errors="coerce").dropna()
        if not numeric.empty:
            numeric_summary = {
                "min": float(numeric.min()),
                "max": float(numeric.max()),
                "mean": float(numeric.mean()),
                "median": float(numeric.median()),
                "std": float(numeric.std(ddof=0)),
            }

    return ColumnInfo(
        name=name,
        dtype=dtype,
        null_count=int(series.isna().sum()),
        unique_count=int(series.nunique(dropna=True)),
        sample_values=sample_raw,
        top_values=top_values,
        numeric_summary=numeric_summary,
    )


def parse_dataset(
    buffer: BinaryIO | bytes,
    *,
    filename: str,
    sample_rows: int = 10,
) -> ParsedDataset:
    """Read CSV or XLSX bytes into a typed `ParsedDataset`.

    File format inferred from `filename`. Encoding tries UTF-8 first then
    cp1252 (common in Indian institutional exports). NaN cells in
    `sample_rows` come back as ``None`` so JSON serialisation never emits NaN.
    """
    if isinstance(buffer, bytes):
        bio: BinaryIO = BytesIO(buffer)
    else:
        bio = buffer

    lower = filename.lower()
    raw = bio.read()
    if lower.endswith((".xlsx", ".xls")):
        df = pd.read_excel(BytesIO(raw))
    else:
        try:
            df = pd.read_csv(BytesIO(raw), encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(BytesIO(raw), encoding="cp1252")

    df.columns = [str(c).strip() for c in df.columns]
    columns = [_column_info(c, df[c]) for c in df.columns]
    sample = df.head(sample_rows).replace({np.nan: None}).to_dict(orient="records")
    quality = _compute_quality(df, columns)

    return ParsedDataset(
        df=df,
        columns=columns,
        row_count=len(df),
        sample_rows=sample,
        quality=quality,
    )


def _is_type_consistent(series: pd.Series, dtype: ColumnType) -> bool:
    """True iff every non-null cell in `series` can be coerced to `dtype`."""
    cleaned = series.dropna()
    if cleaned.empty:
        return True
    if dtype == "numeric":
        coerced = pd.to_numeric(cleaned, errors="coerce")
        return bool(coerced.notna().all())
    if dtype == "datetime":
        try:
            coerced = pd.to_datetime(cleaned, errors="coerce", utc=False)
        except (ValueError, TypeError):
            return False
        return bool(coerced.notna().all())
    if dtype == "boolean":
        allowed = {True, False, "true", "false", "yes", "no", "0", "1"}
        return bool(cleaned.astype(str).str.lower().isin({str(v).lower() for v in allowed}).all())
    # categorical and text are always "consistent" — they're the catch-alls.
    return True


def _compute_quality(df: pd.DataFrame, columns: list[ColumnInfo]) -> DataQuality:
    n_rows = len(df)
    n_cols = len(columns)
    if n_rows == 0 or n_cols == 0:
        return DataQuality(
            row_count=n_rows,
            column_count=n_cols,
            missing_cell_pct=0.0,
            duplicate_row_pct=0.0,
            type_consistency_pct=1.0,
            overall_score=0.0,
            warnings=["Dataset is empty."] if n_rows == 0 else ["Dataset has no columns."],
        )

    total_cells = float(n_rows * n_cols)
    missing_cells = float(df.isna().sum().sum())
    missing_cell_pct = missing_cells / total_cells if total_cells > 0 else 0.0

    duplicates = int(df.duplicated().sum())
    duplicate_row_pct = duplicates / float(n_rows) if n_rows > 0 else 0.0

    consistent = sum(1 for c in columns if _is_type_consistent(df[c.name], c.dtype))
    type_consistency_pct = consistent / float(n_cols) if n_cols > 0 else 1.0

    overall = 1.0 - max(missing_cell_pct, duplicate_row_pct, 1.0 - type_consistency_pct)
    overall_score = float(max(0.0, min(1.0, overall)))

    warnings: list[str] = []
    if n_rows < _MIN_ROW_COUNT_FOR_RELIABILITY:
        warnings.append(
            f"Only {n_rows} rows — below the n={_MIN_ROW_COUNT_FOR_RELIABILITY} "
            f"reliability threshold for fairness metrics."
        )
    if missing_cell_pct >= 0.10:
        warnings.append(f"{missing_cell_pct:.0%} of cells are missing.")
    if duplicate_row_pct >= 0.05:
        warnings.append(f"{duplicate_row_pct:.0%} of rows are duplicates.")
    if type_consistency_pct < 1.0:
        warnings.append(
            f"{(1.0 - type_consistency_pct):.0%} of columns failed strict type coercion."
        )

    return DataQuality(
        row_count=n_rows,
        column_count=n_cols,
        missing_cell_pct=float(missing_cell_pct),
        duplicate_row_pct=float(duplicate_row_pct),
        type_consistency_pct=float(type_consistency_pct),
        overall_score=overall_score,
        warnings=warnings,
    )


__all__ = ["ColumnInfo", "ColumnType", "DataQuality", "ParsedDataset", "parse_dataset"]
