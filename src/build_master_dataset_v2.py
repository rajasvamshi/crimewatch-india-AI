from __future__ import annotations

from pathlib import Path
import re
import pandas as pd
import numpy as np


# ============================================================
# CONFIG
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]   # D:\crimewatch
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUT_DIR = PROJECT_ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MASTER_OUT = OUT_DIR / "master_crime_long.csv"

# Columns that are NOT crime measures (must never be melted into crime_type)
# Add more here if your raw files have other technical columns.
NON_MEASURE_COLS = {
    "id", "Id", "ID",
    "unnamed: 0", "Unnamed: 0", "Unnamed:0", "unnamed:0",
    "index",
    # typical dimensions
    "year",
    "state_name", "state", "state_ut", "state/ut", "state_ut_name",
    "state_code",
    "district_name", "district",
    "district_code",
    "registration_circles", "registration_circle", "registration circle",
    "category",
    "source_file",
}

# Output schema columns
OUT_COLS = [
    "year",
    "state_name", "state_code",
    "district_name", "district_code",
    "registration_circles",
    "crime_type",
    "crime_count",
    "category",
    "source_file",
]


# ============================================================
# HELPERS
# ============================================================
def _clean_col(c: str) -> str:
    c = str(c).strip()
    c = re.sub(r"\s+", " ", c)
    return c

def _lower_col(c: str) -> str:
    return _clean_col(c).lower()

def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    # keep original cols but also build lowercase mapping
    df = df.copy()
    df.columns = [_clean_col(c) for c in df.columns]
    return df

def _find_first_existing(col_candidates: list[str], cols_lower: list[str]) -> str | None:
    """Return the actual column name in df (original casing) that matches any candidate (case-insensitive)."""
    lower_map = {c.lower(): c for c in cols_lower}  # cols_lower is already original list; we map lower->original
    for cand in col_candidates:
        key = cand.lower()
        if key in lower_map:
            return lower_map[key]
    return None

def _coerce_year(s: pd.Series) -> pd.Series:
    y = pd.to_numeric(s, errors="coerce")
    return y

def _safe_read_csv(path: Path) -> pd.DataFrame:
    # Many NCRB CSVs are clean with default encoding; if one fails, fallback.
    try:
        return pd.read_csv(path)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin-1")

def _pick_measure_columns(df: pd.DataFrame) -> list[str]:
    """
    Choose crime measure columns:
    - numeric-ish columns
    - excluding NON_MEASURE_COLS (case-insensitive)
    """
    cols = list(df.columns)
    cols_lower = [_lower_col(c) for c in cols]
    non_measure_lower = {_lower_col(c) for c in NON_MEASURE_COLS}

    # Convert all possible numeric columns to numeric (temp) to detect measures
    measure_cols = []
    for c, cl in zip(cols, cols_lower):
        if cl in non_measure_lower:
            continue
        # ignore obvious text fields
        if cl in {"remarks", "note", "notes"}:
            continue

        # consider as measure if it becomes numeric for a decent fraction of rows
        x = pd.to_numeric(df[c], errors="coerce")
        non_na_ratio = x.notna().mean()
        if non_na_ratio >= 0.25:  # threshold; works well for NCRB wide tables
            measure_cols.append(c)

    # If nothing detected, fallback: all columns except non-measures
    if not measure_cols:
        measure_cols = [c for c, cl in zip(cols, cols_lower) if cl not in non_measure_lower]

    # Hard-remove any technical columns even if numeric (like id, unnamed)
    banned = {"id", "unnamed: 0", "unnamed:0", "index"}
    measure_cols = [c for c in measure_cols if _lower_col(c) not in banned]

    return measure_cols

def _process_one_file(path: Path, category: str) -> pd.DataFrame:
    df = _safe_read_csv(path)
    df = _standardize_columns(df)

    cols = list(df.columns)
    cols_lower = [c for c in cols]  # we map using lower inside finder

    # Detect dimension columns
    col_year = _find_first_existing(["year"], cols)
    col_state = _find_first_existing(["state_name", "state", "state/ut", "state_ut", "state_ut_name"], cols)
    col_state_code = _find_first_existing(["state_code"], cols)
    col_dist = _find_first_existing(["district_name", "district"], cols)
    col_dist_code = _find_first_existing(["district_code"], cols)
    col_reg = _find_first_existing(["registration_circles", "registration_circle", "registration circle"], cols)

    # Basic required dims for your dashboard
    required = [col_year, col_state, col_dist]
    if any(x is None for x in required):
        missing = []
        if col_year is None: missing.append("year")
        if col_state is None: missing.append("state_name/state")
        if col_dist is None: missing.append("district_name/district")
        raise ValueError(f"[{path.name}] missing required dimension columns: {missing}. Found: {cols}")

    # Ensure these exist (create if missing)
    if col_state_code is None:
        df["state_code"] = np.nan
        col_state_code = "state_code"
    if col_dist_code is None:
        df["district_code"] = np.nan
        col_dist_code = "district_code"
    if col_reg is None:
        df["registration_circles"] = ""
        col_reg = "registration_circles"

    # Identify measure columns safely (THIS is where id gets excluded)
    measure_cols = _pick_measure_columns(df)

    # Convert year + measures
    df[col_year] = _coerce_year(df[col_year])
    df = df.dropna(subset=[col_year])
    df[col_year] = df[col_year].astype(int)

    for m in measure_cols:
        df[m] = pd.to_numeric(df[m], errors="coerce").fillna(0.0)

    # Melt to long
    long_df = df.melt(
        id_vars=[col_year, col_state, col_state_code, col_dist, col_dist_code, col_reg],
        value_vars=measure_cols,
        var_name="crime_type",
        value_name="crime_count",
    )

    # Add metadata
    long_df["category"] = category
    long_df["source_file"] = path.name

    # Rename to standard schema
    long_df = long_df.rename(columns={
        col_year: "year",
        col_state: "state_name",
        col_state_code: "state_code",
        col_dist: "district_name",
        col_dist_code: "district_code",
        col_reg: "registration_circles",
    })

    # FINAL HARD FILTER: never allow "id"/unnamed to appear
    bad_types = {"id", "unnamed: 0", "unnamed:0", "index"}
    long_df = long_df[~long_df["crime_type"].astype(str).str.strip().str.lower().isin(bad_types)].copy()

    # Clean types
    long_df["crime_type"] = long_df["crime_type"].astype(str).str.strip()
    long_df["crime_count"] = pd.to_numeric(long_df["crime_count"], errors="coerce").fillna(0.0)
    long_df = long_df[long_df["crime_count"] >= 0]

    # Keep only output columns
    for c in OUT_COLS:
        if c not in long_df.columns:
            long_df[c] = "" if c not in {"year", "crime_count"} else 0

    return long_df[OUT_COLS].copy()


# ============================================================
# MAIN: build master dataset
# ============================================================
def main() -> None:
    if not RAW_DIR.exists():
        raise FileNotFoundError(f"Raw data folder not found: {RAW_DIR}")

    # You can keep a manual map if you want.
    # This auto approach is faster + avoids file-not-found errors:
    # category is inferred from filename.
    raw_files = sorted([p for p in RAW_DIR.glob("*.csv") if p.is_file()])

    if not raw_files:
        raise FileNotFoundError(f"No CSV files found in: {RAW_DIR}")

    frames: list[pd.DataFrame] = []
    skipped: list[str] = []

    for f in raw_files:
        # infer category from filename (your files already include meaningful names)
        # example: districtwise-crime-against-children-2017-onwards.csv -> crime_against_children
        name = f.stem.lower()

        # basic cleanup
        name = name.replace("districtwise-", "").replace("districtwise_", "")
        name = name.replace("-2017-onwards", "").replace("_2017_onwards", "")
        name = name.replace("-2017-2020", "").replace("_2017_2020", "")
        name = re.sub(r"[^a-z0-9]+", "_", name).strip("_")

        category = name if name else "unknown"

        try:
            frames.append(_process_one_file(f, category=category))
            print(f"OK  | {f.name} -> category={category} | rows={len(frames[-1]):,}")
        except Exception as e:
            skipped.append(f"{f.name}: {e}")
            print(f"SKIP| {f.name} -> {e}")

    if not frames:
        raise RuntimeError("No files were processed successfully. Check your raw CSV formats.")

    master = pd.concat(frames, ignore_index=True)

    # One more global guard: remove id/unnamed again (belt & suspenders)
    master = master[~master["crime_type"].astype(str).str.strip().str.lower().isin({"id", "unnamed: 0", "unnamed:0", "index"})].copy()

    # Save
    master.to_csv(MASTER_OUT, index=False)
    print(f"\nDONE: {MASTER_OUT}")
    print(f"Rows: {len(master):,} | Cols: {list(master.columns)}")

    if skipped:
        print("\n--- Skipped files (non-fatal) ---")
        for s in skipped:
            print(s)


if __name__ == "__main__":
    main()
