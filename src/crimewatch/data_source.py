"""Dataset contract between the ETL pipeline and the dashboard.

The dashboard only accepts data that passes :func:`validate_dashboard_frame`. That
gate keeps malformed or tampered files from silently producing wrong risk scores.
A file produced by the ETL (CSV or Parquet) must contain, per row, one
``year x state x district x category`` aggregate.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {
    "year": "int",
    "state_name": "str",
    "district_name": "str",
    "category": "str",
    "crime_count": "number",
}
OPTIONAL_COLUMNS = {"arrests": "number", "crime_type": "str"}

MIN_YEAR, MAX_YEAR = 1950, 2100


class DataValidationError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


@dataclass(frozen=True)
class DatasetInfo:
    path: str
    sha256: str
    rows: int
    year_min: int
    year_max: int


def validate_dashboard_frame(df: pd.DataFrame) -> list[str]:
    """Return a list of human-readable problems (empty list = valid)."""
    errors: list[str] = []
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return [f"missing required columns: {', '.join(missing)}"]
    if df.empty:
        return ["dataset has no rows"]

    years = pd.to_numeric(df["year"], errors="coerce")
    if years.isna().any():
        errors.append(f"{int(years.isna().sum())} row(s) have a non-numeric year")
    elif ((years < MIN_YEAR) | (years > MAX_YEAR)).any():
        errors.append(f"year outside {MIN_YEAR}-{MAX_YEAR}")

    for col in ("crime_count", "arrests"):
        if col not in df.columns:
            continue
        vals = pd.to_numeric(df[col], errors="coerce")
        if vals.isna().any():
            errors.append(f"{int(vals.isna().sum())} row(s) have a non-numeric {col}")
        elif (vals < 0).any():
            errors.append(f"negative values in {col}")

    if "arrests" in df.columns and not errors:
        over = pd.to_numeric(df["arrests"]) > pd.to_numeric(df["crime_count"]) * 5
        if over.any():
            errors.append(f"{int(over.sum())} row(s) report arrests more than 5x crime_count")

    for col in ("state_name", "district_name", "category"):
        blank = df[col].isna() | (df[col].astype(str).str.strip() == "")
        if blank.any():
            errors.append(f"{int(blank.sum())} row(s) have a blank {col}")

    key = ["year", "state_name", "district_name", "category"]
    dups = df.duplicated(subset=key).sum()
    if dups:
        errors.append(f"{int(dups)} duplicate year/state/district/category row(s)")
    return errors


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_dashboard_file(path: Path) -> tuple[pd.DataFrame, DatasetInfo]:
    """Read and validate a dashboard dataset; raise DataValidationError if it is unfit."""
    path = Path(path)
    if not path.exists():
        raise DataValidationError([f"data file not found: {path}"])
    head = path.read_bytes()[:200]
    if head.startswith(b"version https://git-lfs.github.com/spec/"):
        raise DataValidationError([f"{path.name} is a Git LFS pointer; run 'git lfs pull' first"])

    if path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path)
    elif path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        raise DataValidationError([f"unsupported file type {path.suffix!r}; use .csv or .parquet"])

    errors = validate_dashboard_frame(df)
    if errors:
        raise DataValidationError(errors)

    df = df.copy()
    df["year"] = pd.to_numeric(df["year"]).astype(int)
    df["crime_count"] = pd.to_numeric(df["crime_count"]).astype(int)
    if "arrests" not in df.columns:
        df["arrests"] = 0
    df["arrests"] = pd.to_numeric(df["arrests"]).astype(int)
    if "crime_type" not in df.columns:
        df["crime_type"] = "Other Crime"

    info = DatasetInfo(
        path=str(path),
        sha256=file_sha256(path),
        rows=len(df),
        year_min=int(df["year"].min()),
        year_max=int(df["year"].max()),
    )
    return df, info
