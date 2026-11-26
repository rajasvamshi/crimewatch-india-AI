"""Build the dashboard dataset from the NCRB-derived master long table.

Input : ``data/processed/master_crime_long.csv`` (output of ``src/build_master_dataset_v2.py``;
        one row per year x state x district x registration circle x NCRB head).
Output: ``data/processed/dashboard_dataset.parquet`` (one row per year x state x district x
        dashboard category) and a ``.provenance.json`` sidecar recording the source file hash,
        mapping version and row counts so every figure can be traced back.

Mapping rules (``CATEGORY_MAP``):

* Each NCRB head maps to **at most one** dashboard category, so categories never double-count.
* IPC heads come from the ``ipc_crimes`` table. Drug offences (NDPS possession heads) and Cyber
  Crime (Information Technology Act cases) come from the ``sll_crimes`` table, which is disjoint
  from IPC. The separate NCRB cyber-crime and crimes-against-women tables are *not* used
  because they re-count cases already registered under IPC/SLL.
* Heads not listed (rioting, negligence deaths, traffic offences, excise, etc.) are excluded,
  so dashboard totals are the sum of the ten categories, not "all IPC crime".
* NCRB district tables carry no arrest counts; ``arrests`` is left empty (NaN → 0 in the
  dashboard, which labels arrest-based figures as unavailable for this source).

Run: ``python -m src.crimewatch.etl_dashboard [--source PATH] [--out PATH]``
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .data_source import file_sha256, validate_dashboard_frame
from .settings import PROJECT_ROOT

MAPPING_VERSION = "2026.11.1"

# (source table, NCRB head) -> dashboard category
_IPC = "ipc_crimes"
_SLL = "sll_crimes"

_GROUPS: dict[str, dict[str, list[str]]] = {
    "Murder": {_IPC: ["murder", "clpbl_hmcrd_not_amt_murder", "dacoity_with_murder", "kidnp_abdctn_murder"]},
    "Assault": {
        _IPC: [
            "atmpt_cmmt_murder", "atmpt_cmmt_clpb_hmcrd", "vlntrly_caus_simple_hurt", "other_simple_hurt",
            "vlntrly_caus_dangers_weapons", "vlntrly_caus_grvus_hurt", "grvus_hrt_dangerous_wepn",
            "other_grievous_hurt", "vlntrly_caus_pub_srvnt_duty", "grvus_hrt_pub_srvnt_duty", "acid_attack",
            "atmpt_acid_attack", "wrngful_rest_cnfm", "criminal_intimidation", "assault_on_women", "rape",
            "atmpt_rape", "sex_hrrsmt_other_places", "sex_hrrsmt_shelter_homes", "sex_hrrsmt_pub_trnsprt_sys",
            "sex_hrrsmt_work_office_prms", "stalking", "voyeurism", "insult_modesty_women", "unnatural_offences",
        ]
    },
    "Kidnapping": {
        _IPC: [
            "kidnp_abdctn_marrg", "other_kidnp_abduc", "other_kidnp_abduc_sec_365_369", "missing_child_kidnpd",
            "kidnapping_for_ransom", "kidnp_abdctn_begging", "human_trafficking", "exp_traf_person",
            "proc_minor_girls", "sell_minors_prost", "buy_minors_prost", "import_girls_frgn_cntry",
        ]
    },
    "Domestic Violence": {
        _IPC: ["crlty_husbnd_relatives", "dowry_deaths"],
        _SLL: ["dowry_prohibition", "women_protection_from_domestic_voilence"],
    },
    "Theft": {_IPC: ["other_thefts", "auto_motor_vehicle_theft", "dsh_hon_rec_deal_stl_prop"]},
    "Burglary": {_IPC: ["night_burglary", "day_time_burglary", "criminal_trespass"]},
    "Robbery": {
        _IPC: ["robbery", "dacoity", "atmpt_dacoity_robbery", "mkng_prprtn_assmbly_cmmttng_dcty",
               "extortion_and_blackmailing"]
    },
    "Fraud": {
        _IPC: [
            "cheating", "cheating_impersonation", "criminal_breach_of_trust", "criminal_misappropriation",
            "other_frauds", "forgery", "atm_fraud", "bank_frauds", "credit_debit_card_fraud",
            "cntrft_curr_bank_notes", "counterfeit_coin", "cntrft_seal_mark", "cntrfte_govt_stamp",
        ]
    },
    "Drug Offense": {_SLL: ["possession_of_drugs_for_personal_use_consumption", "possession_of_drugs_for_trafficking"]},
    "Cyber Crime": {_SLL: ["information_technology_act"]},
}

CATEGORY_MAP: dict[tuple[str, str], str] = {
    (table, head): category
    for category, tables in _GROUPS.items()
    for table, heads in tables.items()
    for head in heads
}

CRIME_TYPE = {
    "Theft": "Property Crime", "Robbery": "Property Crime", "Burglary": "Property Crime", "Fraud": "Property Crime",
    "Assault": "Violent Crime", "Kidnapping": "Violent Crime", "Domestic Violence": "Violent Crime",
    "Murder": "Violent Crime", "Cyber Crime": "Special Crime", "Drug Offense": "Special Crime",
}

# NCRB spellings -> names used by the dashboard and the boundary file.
STATE_ALIASES = {
    "The Dadra And Nagar Haveli And Daman And Diu": "Dadra And Nagar Haveli And Daman And Diu",
}


def build(master: pd.DataFrame) -> pd.DataFrame:
    """Collapse the NCRB long table into the dashboard schema."""
    needed = {"year", "state_name", "district_name", "category", "crime_type", "crime_count"}
    missing = needed - set(master.columns)
    if missing:
        raise ValueError(f"master table missing columns: {sorted(missing)}")

    keys = pd.Series(list(zip(master["category"], master["crime_type"], strict=True)), index=master.index)
    dash_cat = keys.map(CATEGORY_MAP)
    df = master.loc[dash_cat.notna(), ["year", "state_name", "district_name", "crime_count"]].copy()
    df["category"] = dash_cat[dash_cat.notna()]
    df["state_name"] = df["state_name"].astype(str).str.strip().replace(STATE_ALIASES)
    df["district_name"] = df["district_name"].astype(str).str.strip()
    df["crime_count"] = pd.to_numeric(df["crime_count"], errors="coerce").fillna(0).clip(lower=0)

    out = (
        df.groupby(["year", "state_name", "district_name", "category"], as_index=False)["crime_count"]
        .sum()
        .astype({"year": int, "crime_count": int})
    )
    out["crime_type"] = out["category"].map(CRIME_TYPE)
    out["arrests"] = 0
    return out.sort_values(["year", "state_name", "district_name", "category"]).reset_index(drop=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", default=str(PROJECT_ROOT / "data/processed/master_crime_long.csv"))
    ap.add_argument("--out", default=str(PROJECT_ROOT / "data/processed/dashboard_dataset.parquet"))
    args = ap.parse_args(argv)

    src, out = Path(args.source), Path(args.out)
    usecols = ["year", "state_name", "district_name", "category", "crime_type", "crime_count"]
    master = pd.read_csv(src, usecols=usecols)
    data = build(master)
    errors = validate_dashboard_frame(data)
    if errors:
        raise SystemExit("validation failed: " + "; ".join(errors))

    out.parent.mkdir(parents=True, exist_ok=True)
    data.to_parquet(out, index=False)
    provenance = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mapping_version": MAPPING_VERSION,
        "source_file": src.name,
        "source_sha256": file_sha256(src),
        "source_rows": int(len(master)),
        "output_file": out.name,
        "output_sha256": file_sha256(out),
        "output_rows": int(len(data)),
        "years": [int(data["year"].min()), int(data["year"].max())],
        "states": int(data["state_name"].nunique()),
        "districts": int(data[["state_name", "district_name"]].drop_duplicates().shape[0]),
        "category_totals": {k: int(v) for k, v in data.groupby("category")["crime_count"].sum().items()},
        "notes": "Arrests are not published in NCRB district tables; arrests column is 0.",
    }
    out.with_suffix(".provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: provenance[k] for k in ("output_rows", "years", "states", "districts")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
