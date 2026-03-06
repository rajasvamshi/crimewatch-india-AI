import os
import glob
import pandas as pd

RAW_DIR = "data/raw"
OUTPUT_FILE = "data/processed/master_crime_long.csv"

# Identity columns (do NOT melt these)
ID_COLS = [
    "year", "state_name", "state_code",
    "district_name", "district_code",
    "registration_circles"
]


def detect_category(file_path: str) -> str:
    """
    Detect crime dataset category from filename.
    """
    name = os.path.basename(file_path).lower()

    # IMPORTANT: more specific checks first
    if "missing" in name:
        return "missing_persons"
    if "cyber" in name:
        return "cyber_crime"
    if "crime-against-women" in name or "women" in name:
        return "crime_against_women"
    if "crime-against-children" in name or "children" in name:
        return "crime_against_children"
    if "crime-against-sts" in name or "crime-against-st" in name or "-st-" in name:
        return "crime_against_st"
    if "crimes-against-sc" in name or "-sc-" in name:
        return "crime_against_sc"
    if "ipc-crime-by-juveniles" in name or "juveniles" in name:
        return "ipc_by_juveniles"
    if "ipc-crimes" in name:
        return "ipc_total"
    if "sll-crimes" in name:
        return "sll_crimes"

    return "unknown"


def load_and_melt(file_path: str) -> pd.DataFrame:
    """
    Read a raw CSV and convert from wide to long format.
    """
    df = pd.read_csv(file_path)

    # Clean column names (removes accidental spaces)
    df.columns = df.columns.str.strip()

    # Drop unnamed index columns if present
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    # Ensure ID cols exist in this file
    id_cols_present = [c for c in ID_COLS if c in df.columns]

    # Crime columns = everything except ID cols
    crime_cols = [c for c in df.columns if c not in id_cols_present]

    # Melt (wide -> long)
    df_long = df.melt(
        id_vars=id_cols_present,
        value_vars=crime_cols,
        var_name="crime_type",
        value_name="crime_count"
    )

    # Make sure crime_count is numeric
    df_long["crime_count"] = pd.to_numeric(df_long["crime_count"], errors="coerce").fillna(0)

    # Optional: force integer counts (if you want)
    # df_long["crime_count"] = df_long["crime_count"].astype(int)

    # Add metadata columns
    df_long["category"] = detect_category(file_path)
    df_long["source_file"] = os.path.basename(file_path)

    # Reset index (fix duplicate / weird print indices)
    df_long = df_long.reset_index(drop=True)

    return df_long


def build_master_dataset():
    all_files = glob.glob(os.path.join(RAW_DIR, "*.csv"))

    if not all_files:
        raise FileNotFoundError(f"No CSV files found in {RAW_DIR}. Please check your folder.")

    print(f"✅ Found {len(all_files)} raw CSV files")

    long_frames = []
    for file_path in all_files:
        print(f"Processing: {file_path}")
        df_long = load_and_melt(file_path)
        long_frames.append(df_long)

    # Merge into single dataframe
    master = pd.concat(long_frames, ignore_index=True)

    # Remove duplicates (safe; keeps dataset clean)
    master = master.drop_duplicates()

    # Save output
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    master.to_csv(OUTPUT_FILE, index=False)

    print(f"\n✅ MASTER DATASET CREATED: {OUTPUT_FILE}")
    print(master.head())
    print(f"\n✅ Rows: {master.shape[0]} | Columns: {master.shape[1]}")


if __name__ == "__main__":
    build_master_dataset()
