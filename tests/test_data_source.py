import pandas as pd
import pytest

from src.crimewatch.data_source import DataValidationError, load_dashboard_file, validate_dashboard_frame


def _good():
    return pd.DataFrame(
        {
            "year": [2021, 2022],
            "state_name": ["Kerala", "Kerala"],
            "district_name": ["Kochi", "Kochi"],
            "category": ["Theft", "Theft"],
            "crime_count": [120, 130],
            "arrests": [40, 50],
        }
    )


def test_valid_frame_passes():
    assert validate_dashboard_frame(_good()) == []


@pytest.mark.parametrize(
    "mutate, expected",
    [
        (lambda d: d.drop(columns=["year"]), "missing required columns"),
        (lambda d: d.assign(crime_count=[-1, 5]), "negative values in crime_count"),
        (lambda d: d.assign(year=["x", 2022]), "non-numeric year"),
        (lambda d: d.assign(year=[1800, 2022]), "year outside"),
        (lambda d: d.assign(district_name=["", "Kochi"]), "blank district_name"),
        (lambda d: d.assign(year=[2022, 2022]), "duplicate"),
        (lambda d: d.assign(arrests=[4000, 1]), "more than 5x"),
        (lambda d: d.iloc[0:0], "no rows"),
    ],
)
def test_invalid_frames_flagged(mutate, expected):
    errors = validate_dashboard_frame(mutate(_good()))
    assert any(expected in e for e in errors), errors


def test_load_csv_roundtrip(tmp_path):
    p = tmp_path / "d.csv"
    _good().drop(columns=["arrests"]).to_csv(p, index=False)
    df, info = load_dashboard_file(p)
    assert info.rows == 2 and info.year_min == 2021 and len(info.sha256) == 64
    assert (df["arrests"] == 0).all() and "crime_type" in df.columns


def test_lfs_pointer_explained(tmp_path):
    p = tmp_path / "big.csv"
    p.write_text("version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 1\n")
    with pytest.raises(DataValidationError, match="git lfs pull"):
        load_dashboard_file(p)


def test_missing_and_bad_type(tmp_path):
    with pytest.raises(DataValidationError):
        load_dashboard_file(tmp_path / "nope.csv")
    bad = tmp_path / "d.xlsx"
    bad.write_bytes(b"x")
    with pytest.raises(DataValidationError, match="unsupported"):
        load_dashboard_file(bad)
