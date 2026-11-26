
import pandas as pd

from src.crimewatch import ncrb_official as no


def test_committed_reference_builds_and_is_consistent():
    df, prov = no.build()
    nat = df[df.level == "national"].set_index("year")
    assert nat.loc[2024, "total_cases"] == 5885867
    assert nat.loc[2023, "total_cases"] == 6241569
    # IPC/BNS + SLL split is kept from Table 1.1, not overwritten by the state file's total row
    assert nat.loc[2024, "ipc_bns_cases"] + nat.loc[2024, "sll_cases"] == 5885867
    states = df[(df.level == "state") & (df.year == 2023)]
    assert len(states) == 36 and states.total_cases.sum() == 6241569
    assert prov["latest_national_year"] == 2024
    assert all(len(m["sha256"]) == 64 for m in prov["sources"].values())


def test_state_names_match_dashboard_dataset():
    df, _ = no.build()
    names = set(df.loc[df.level == "state", "name"])
    dash = set(pd.read_parquet(no.PROJECT_ROOT / "data/processed/dashboard_dataset.parquet",
                               columns=["state_name"])["state_name"])
    assert names == dash


def test_processed_file_is_up_to_date():
    df, _ = no.build()
    committed = no.load()
    assert len(committed) == len(df)
    assert committed["total_cases"].sum() == df["total_cases"].sum()


def test_parse_ncrb_state_table_layout(tmp_path):
    p = tmp_path / "cii2024_table_1a1.csv"
    p.write_text(
        "TABLE 1A.1,,,,,,\n"
        "Incidence & Rate of Cognizable Crimes (IPC + SLL) State/UT-wise during 2022-2024,,,,,,\n"
        "Sl. No.,State/UT,2022,2023,2024,Rate of Total Cognizable Crimes (2024),Charge-sheeting Rate (2024)\n"
        "1,Andhra Pradesh,\"1,58,547\",\"1,84,293\",\"1,70,000\",318.5,90.1\n"
        "2,A & N Islands,1500,1873,1700,420.0,93.0\n"
        ",Total (States),\"1,60,047\",\"1,86,166\",\"1,71,700\",,\n"
        ",Total (All India),\"1,60,047\",\"1,86,166\",\"1,71,700\",400.0,85.0\n"
    )
    out = no.parse_state_table(p, 2024)
    assert list(out.name) == ["Andhra Pradesh", "Andaman And Nicobar Islands", "India"]
    assert list(out.total_cases) == [170000, 1700, 171700]
    assert list(out.level) == ["state", "state", "national"]
    assert out.iloc[0].crime_rate == 318.5 and out.iloc[0].chargesheet_rate == 90.1


def test_consistency_check_catches_bad_transcription():
    df, _ = no.build()
    bad = df.copy()
    i = bad[(bad.level == "state") & (bad.name == "Kerala")].index[0]
    bad.loc[i, "total_cases"] += 10
    assert any("sum to" in p for p in no.check_consistency(bad))
