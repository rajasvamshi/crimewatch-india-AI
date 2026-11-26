import pandas as pd
import pytest

from src.build_master_dataset_v2 import coerce_standard_schema, data_quality_checks, detect_category, load_and_melt


@pytest.mark.parametrize(
    "name, cat",
    [
        ("districtwise-crime-against-women-2017.csv", "crime_against_women"),
        ("districtwise-cyber-crimes.csv", "cyber_crime"),
        ("districtwise-ipc-crimes-2017-onwards.csv", "ipc_total"),
        ("districtwise-missing-persons.csv", "missing_persons"),
    ],
)
def test_detect_category(name, cat):
    assert detect_category(name) == cat


def test_schema_coercion_and_melt(tmp_path):
    p = tmp_path / "districtwise-ipc-crimes.csv"
    pd.DataFrame(
        {"Year": [2020], "State": ["Goa"], "District": ["North Goa"], "id": [7], "murder": [3], "theft": [0]}
    ).to_csv(p, index=False)
    assert set(coerce_standard_schema(pd.read_csv(p)).columns) >= {"year", "state_name", "district_name"}
    long_df = load_and_melt(str(p))
    assert set(long_df["crime_type"]) == {"murder"}  # id excluded, all-zero theft dropped
    assert long_df["category"].iloc[0] == "ipc_total"


def test_quality_gate_rejects_negative_counts():
    df = pd.DataFrame(
        {
            "year": [2020],
            "state_name": ["Goa"],
            "district_name": ["North Goa"],
            "crime_type": ["murder"],
            "crime_count": [-1],
            "category": ["ipc_total"],
            "source_file": ["f.csv"],
        }
    )
    with pytest.raises(ValueError):
        data_quality_checks(df)
