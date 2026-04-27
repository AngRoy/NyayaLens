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
class ParsedDataset:
    df: pd.DataFrame
    columns: list[ColumnInfo]
    row_count: int
    sample_rows: list[dict[str, Any]]


_TEXT_THRESHOLD: int = 50  # avg string length above which a column reads as free text
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

    return ParsedDataset(
        df=df,
        columns=columns,
        row_count=len(df),
        sample_rows=sample,
    )


__all__ = ["ColumnInfo", "ColumnType", "ParsedDataset", "parse_dataset"]
