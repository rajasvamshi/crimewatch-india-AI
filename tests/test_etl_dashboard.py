from pathlib import Path

import pandas as pd

from src.crimewatch.data_source import load_dashboard_file, validate_dashboard_frame
from src.crimewatch.etl_dashboard import CATEGORY_MAP, CRIME_TYPE, build
from src.crimewatch.live_store import DASHBOARD_CATEGORIES

ROOT = Path(__file__).resolve().parents[1]


def test_every_category_is_known_and_typed():
    assert set(CATEGORY_MAP.values()) == set(DASHBOARD_CATEGORIES) == set(CRIME_TYPE)


def test_build_maps_aggregates_and_excludes():
    master = pd.DataFrame(
        [
            # two registration circles of the same district are summed
            (2021, "Goa", "North Goa", "ipc_crimes", "murder", 2),
            (2021, "Goa", "North Goa", "ipc_crimes", "murder", 3),
            (2021, "Goa", "North Goa", "ipc_crimes", "other_thefts", 10),
            (2021, "Goa", "North Goa", "sll_crimes", "information_technology_act", 4),
            # unmapped head and double-counting tables are ignored
            (2021, "Goa", "North Goa", "ipc_crimes", "rash_driving_pub_way", 99),
            (2021, "Goa", "North Goa", "cyber_crimes", "identity_theft", 50),
            (2021, "The Dadra And Nagar Haveli And Daman And Diu", "Daman", "ipc_crimes", "robbery", 1),
        ],
        columns=["year", "state_name", "district_name", "category", "crime_type", "crime_count"],
    )
    out = build(master)
    got = {(r.state_name, r.category): r.crime_count for r in out.itertuples()}
    assert got == {
        ("Goa", "Murder"): 5,
        ("Goa", "Theft"): 10,
        ("Goa", "Cyber Crime"): 4,
        ("Dadra And Nagar Haveli And Daman And Diu", "Robbery"): 1,
    }
    assert validate_dashboard_frame(out) == []


def test_committed_dataset_is_valid():
    df, info = load_dashboard_file(ROOT / "data/processed/dashboard_dataset.parquet")
    assert info.year_min == 2017 and info.year_max == 2022
    assert df["state_name"].nunique() == 36
    assert set(df["category"]) == set(DASHBOARD_CATEGORIES)
