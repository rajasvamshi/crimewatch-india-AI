# D:\crimewatch\src\build_master_dataset_v2.py
from __future__ import annotations

import os
import re
import glob
from pathlib import Path
import pandas as pd


# =========================
# CONFIG
# =========================
PROJECT_ROOT = Path(__file__).resolve().parents[1]   # .../crimewatch
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = OUT_DIR / "master_crime_long.csv"

# Identity columns that should NEVER become crime_type
# (We will keep only those that exist in each file.)
ID_COLS = [
    "year",
    "state_name", "state_code",
    "district_name", "district_code",
    "registration_circles",
]

# Columns that are NOT crimes even if present (must be excluded from melt)
# This is where "id" gets blocked.
NON_CRIME_COLS = set([
    "id", "index", "unnamed: 0", "s_no", "s.no", "sr_no", "sr.no",
    "total", "grand_total", "remarks", "note", "notes",
])

# Columns that often exist but are metadata, not crime types
META_COL_HINTS = [
    "code", "name", "circle", "registration", "police",
    "state", "district", "year",
]

# If a value column is ALL zeros or ALL NaN, we can drop it (optional)
DROP_ALL_ZERO_CRIME_TYPES = True


# =========================
# HELPERS
# =========================
def norm_col(c: str) -> str:
    """Normalize column names to snake_case-ish lower for matching."""
    c = str(c).strip()
    c = re.sub(r"\s+", "_", c)
    c = c.replace("-", "_").replace("/", "_")
    c = c.lower()
    return c


def detect_category(file_path: str) -> str:
    """Category from filename (robust)."""
    name = os.path.basename(file_path).lower()
    if "women" in name:
        return "crime_against_women"
    if "children" in name:
        return "crime_against_children"
    if "cyber" in name:
        return "cyber_crime"
    if "juvenile" in name:
        return "ipc_by_juveniles"
    if "missing" in name:
        return "missing_persons"
    if "sll" in name:
        return "sll_crimes"
    if "ipc" in name:
        return "ipc_total"
    # SC/ST files vary: "sc", "sts", "st", etc.
    if "sc" in name and "st" in name:
        return "crime_against_sc_st"
    if "sc" in name:
        return "crime_against_sc"
    if "sts" in name or "st" in name:
        return "crime_against_st"
    return "unknown"


def is_likely_id_col(col_norm: str) -> bool:
    """Exclude obvious non-crime columns from melt."""
    if col_norm in NON_CRIME_COLS:
        return True
    # Unnamed columns from CSV exports
    if col_norm.startswith("unnamed"):
        return True
    # Anything that looks like an ID/key column
    if col_norm in ("gid", "uuid", "pk"):
        return True
    # If it contains typical metadata hints and is short/identifier-like
    if any(h in col_norm for h in META_COL_HINTS) and col_norm in (
        "state", "district", "year", "state_code", "district_code", "registration_circles"
    ):
        return True
    return False


def coerce_standard_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Make column names consistent without losing information.
    We try to map common variations to the expected ID_COLS names.
    """
    # Normalize columns for matching
    original_cols = list(df.columns)
    colmap = {c: norm_col(c) for c in original_cols}

    # Reverse index: normalized -> original
    norm_to_orig = {}
    for orig, n in colmap.items():
        norm_to_orig.setdefault(n, []).append(orig)

    # Build rename mapping for known keys
    rename = {}

    # year
    for cand in ["year", "yr"]:
        if cand in norm_to_orig:
            rename[norm_to_orig[cand][0]] = "year"
            break

    # state_name
    for cand in ["state_name", "state", "state_ut", "state_ut_name", "state/ut"]:
        if cand in norm_to_orig:
            rename[norm_to_orig[cand][0]] = "state_name"
            break

    # state_code
    for cand in ["state_code", "st_code", "statecd", "state_id"]:
        if cand in norm_to_orig:
            rename[norm_to_orig[cand][0]] = "state_code"
            break

    # district_name
    for cand in ["district_name", "district", "district_name_", "dist_name", "district/area"]:
        if cand in norm_to_orig:
            rename[norm_to_orig[cand][0]] = "district_name"
            break

    # district_code
    for cand in ["district_code", "dist_code", "districtcd", "district_id"]:
        if cand in norm_to_orig:
            rename[norm_to_orig[cand][0]] = "district_code"
            break

    # registration_circles
    for cand in ["registration_circles", "registration_circle", "circle", "reg_circles", "registrationcircles"]:
        if cand in norm_to_orig:
            rename[norm_to_orig[cand][0]] = "registration_circles"
            break

    df = df.rename(columns=rename)
    return df


def pick_id_cols(df: pd.DataFrame) -> list[str]:
    """Keep only ID_COLS that exist in df."""
    return [c for c in ID_COLS if c in df.columns]


def pick_value_cols(df: pd.DataFrame, id_cols_present: list[str]) -> list[str]:
    """Crime columns = all columns except ID cols and obvious non-crime cols."""
    crime_cols = []
    for c in df.columns:
        if c in id_cols_present:
            continue
        cn = norm_col(c)
        if is_likely_id_col(cn):
            continue
        crime_cols.append(c)
    return crime_cols


def load_and_melt(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)

    # Standardize schema (best-effort)
    df = coerce_standard_schema(df)

    id_cols = pick_id_cols(df)

    # Must have at least year/state/district to be useful
    required_min = {"year", "state_name", "district_name"}
    if not required_min.issubset(set(df.columns)):
        # Skip files that don't match expected district-level format
        missing = required_min - set(df.columns)
        print(f"⚠️ Skipping {os.path.basename(file_path)} (missing {missing})")
        return pd.DataFrame()

    crime_cols = pick_value_cols(df, id_cols)

    if not crime_cols:
        print(f"⚠️ Skipping {os.path.basename(file_path)} (no crime columns after filtering)")
        return pd.DataFrame()

    df_long = df.melt(
        id_vars=id_cols,
        value_vars=crime_cols,
        var_name="crime_type",
        value_name="crime_count",
    ).reset_index(drop=True)

    # Clean types
    df_long["crime_type"] = df_long["crime_type"].astype(str).str.strip()
    df_long["crime_count"] = pd.to_numeric(df_long["crime_count"], errors="coerce").fillna(0.0)

    # HARD BLOCK: ensure crime_type never equals "id"
    df_long = df_long[df_long["crime_type"].str.lower() != "id"].reset_index(drop=True)

    # Add metadata
    df_long["category"] = detect_category(file_path)
    df_long["source_file"] = os.path.basename(file_path)

    # Optional: drop crime types that are entirely zero in this file
    if DROP_ALL_ZERO_CRIME_TYPES:
        sums = df_long.groupby("crime_type")["crime_count"].sum()
        keep_types = sums[sums > 0].index
        df_long = df_long[df_long["crime_type"].isin(keep_types)].reset_index(drop=True)

    return df_long


def data_quality_checks(master: pd.DataFrame) -> None:
    """Fail fast if dataset quality is broken."""
    required = {"year", "state_name", "district_name", "crime_type", "crime_count", "category", "source_file"}
    missing = required - set(master.columns)
    if missing:
        raise ValueError(f"MASTER missing required columns: {missing}")

    # year numeric
    master["year"] = pd.to_numeric(master["year"], errors="coerce")
    if master["year"].isna().any():
        raise ValueError("Some rows have invalid year after coercion.")

    # crime_count numeric + non-negative
    master["crime_count"] = pd.to_numeric(master["crime_count"], errors="coerce").fillna(0.0)
    if (master["crime_count"] < 0).any():
        raise ValueError("Found negative crime_count values (invalid).")

    # THE KEY CHECK YOU ASKED ABOUT:
    bad = set(master["crime_type"].astype(str).str.lower().unique())
    assert "id" not in bad, (
        "DATA QUALITY ERROR: 'id' found in crime_type. "
        "This indicates a parsing/melt issue. Fix ETL before dashboard."
    )

    # sanity: avoid empty dataset
    if len(master) == 0:
        raise ValueError("MASTER is empty after processing. Check raw files.")

    # sanity: must have some categories
    if master["category"].nunique() < 2:
        print("⚠️ Warning: Only 1 category detected. Verify filenames/category detection.")


def build_master_dataset():
    all_files = sorted(glob.glob(str(RAW_DIR / "*.csv")))
    print(f"✅ Found {len(all_files)} raw CSV files in {RAW_DIR}")

    frames = []
    for fp in all_files:
        print(f"Processing: {Path(fp).name}")
        long_df = load_and_melt(fp)
        if not long_df.empty:
            frames.append(long_df)

    if not frames:
        raise RuntimeError("No valid CSVs produced long-format frames. Check your raw CSV folder/files.")

    master = pd.concat(frames, ignore_index=True)

    # Normalize key fields
    master["state_name"] = master["state_name"].astype(str).str.strip()
    master["district_name"] = master["district_name"].astype(str).str.strip()
    master["crime_type"] = master["crime_type"].astype(str).str.strip()
    master["category"] = master["category"].astype(str).str.strip()

    # Remove exact duplicates (safe)
    master = master.drop_duplicates().reset_index(drop=True)

    # Data quality gates
    data_quality_checks(master)

    # Save
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    master.to_csv(OUTPUT_FILE, index=False)

    print(f"\n✅ MASTER DATASET CREATED: {OUTPUT_FILE}")
    print(master.head())
    print(f"\n✅ Rows: {master.shape[0]} | Columns: {master.shape[1]}")
    print("✅ Unique categories:", master["category"].nunique())
    print("✅ Year range:", int(master["year"].min()), "-", int(master["year"].max()))
    print("✅ 'id' present in crime_type? ->", "id" in set(master["crime_type"].str.lower().unique()))


if __name__ == "__main__":
    build_master_dataset()
