"""Latest official NCRB "Crime in India" totals (national, state/UT and metro level).

The district-level dashboard dataset (``etl_dashboard``) stops at 2022 because NCRB's
district tables are published later than the annual report. The annual report itself
(Crime in India 2023, released Sept 2025; Crime in India 2024, released May 2026) gives
state/UT and metro-city totals. This module loads those totals so the dashboard can show
the newest official year next to the district analytics without mixing the two.

Inputs live in ``data/reference/ncrb_cii/`` (small, committed, every file listed with its
source in ``sources.json``). When the NCRB tables are downloaded with
``scripts/fetch_ncrb_cii.py``, :func:`parse_state_table` reads NCRB's own State/UT table
(Table 1A.1 layout: State/UT, cases for three years, rate, charge-sheet rate) and
:func:`build` prefers it over any secondary copy.

Run: ``python -m src.crimewatch.ncrb_official`` to rebuild the processed file.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .data_source import file_sha256
from .settings import PROJECT_ROOT

REFERENCE_DIR = PROJECT_ROOT / "data/reference/ncrb_cii"
OUT_PATH = PROJECT_ROOT / "data/processed/ncrb_official_totals.csv"

COLUMNS = [
    "year", "level", "name", "total_cases", "ipc_bns_cases", "sll_cases",
    "crime_rate", "chargesheet_rate", "source_file", "source_tier",
]

# NCRB spellings -> names used by the dashboard dataset / GeoJSON
NAME_FIXES = {
    "a&n islands": "Andaman And Nicobar Islands",
    "a & n islands": "Andaman And Nicobar Islands",
    "andaman & nicobar islands": "Andaman And Nicobar Islands",
    "d&n haveli and daman & diu": "Dadra And Nagar Haveli And Daman And Diu",
    "dnh and dd": "Dadra And Nagar Haveli And Daman And Diu",
    "jammu & kashmir": "Jammu And Kashmir",
    "delhi ut": "Delhi",
    "nct of delhi": "Delhi",
}
NAN = float("nan")
TOTAL_ROW = re.compile(r"^(total|all[ -]?india|india)\b", re.I)
SUBTOTAL_ROW = re.compile(r"^total\s*\((states|uts?)\)", re.I)


def canonical_name(raw: str) -> str:
    s = re.sub(r"\s+", " ", str(raw)).strip()
    s = NAME_FIXES.get(s.lower(), s)
    # dashboard dataset capitalises every word ("Jammu And Kashmir")
    return " ".join(w[:1].upper() + w[1:] for w in s.split(" "))


def _num(v) -> float | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).replace(",", "").strip()
    if s in {"", "-", "NA", "N.A.", "nan"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_state_table(path: Path, year: int) -> pd.DataFrame:
    """Parse an NCRB State/UT-wise table (CSV or Excel) into tidy rows for ``year``.

    Tolerant of NCRB's layout: a few title rows, then a header containing "State/UT" and
    one column per year (e.g. "2022", "2023", "2024"), followed by "Rate of Total
    Cognizable Crimes" and "Charge-sheeting Rate" columns. Section/subtotal rows are
    dropped; the all-India total becomes a ``national`` row.
    """
    raw = pd.read_excel(path, header=None) if path.suffix.lower() in {".xls", ".xlsx"} else pd.read_csv(
        path, header=None, dtype=str
    )
    is_header = re.compile(r"\s*states?\s*/\s*uts?\s*", re.I)
    header_idx = next((i for i, row in raw.iterrows() if any(is_header.fullmatch(str(c)) for c in row)), None)
    if header_idx is None:
        raise ValueError(f"{path.name}: no 'State/UT' header row found")
    header = [str(c).strip() for c in raw.iloc[header_idx]]
    body = raw.iloc[header_idx + 1:].reset_index(drop=True)

    def col(pattern: str) -> int | None:
        return next((i for i, h in enumerate(header) if re.search(pattern, h, re.I)), None)

    name_col = col(r"^states?\s*/\s*uts?$")
    cases_col = col(rf"^{year}$|\b{year}\b(?!.*rate)")
    if cases_col is None:
        cases_col = col(r"total.*(crimes|cases)")
    rate_col = col(r"(crime\s*)?rate(?!.*charge)")
    cs_col = col(r"charge.?sheet")
    if cases_col is None:
        raise ValueError(f"{path.name}: no column for {year} cases in header {header}")

    rows = []
    for _, r in body.iterrows():
        name = str(r.iloc[name_col]).strip()
        if not name or name.lower() == "nan" or SUBTOTAL_ROW.match(name):
            continue
        total = _num(r.iloc[cases_col])
        if total is None:
            continue  # section headers ("States:", "UTs:") and footnotes
        national = bool(TOTAL_ROW.match(name))
        rows.append({
            "year": year,
            "level": "national" if national else "state",
            "name": "India" if national else canonical_name(name),
            "total_cases": int(total),
            "ipc_bns_cases": None,
            "sll_cases": None,
            "crime_rate": _num(r.iloc[rate_col]) if rate_col is not None else None,
            "chargesheet_rate": _num(r.iloc[cs_col]) if cs_col is not None else None,
            "source_file": path.name,
            "source_tier": "primary",
        })
    return pd.DataFrame(rows, columns=COLUMNS)


def _wide_state_file(path: Path, year: int, tier: str) -> pd.DataFrame:
    """Secondary copy: columns 'State/UT', 'Total Crimes (IPC+SLL) <year>', 'Crime Rate ...'."""
    df = pd.read_csv(path)
    total = next(c for c in df.columns if c.lower().startswith("total crimes"))
    rate = next(c for c in df.columns if c.lower().startswith("crime rate"))
    cs = next((c for c in df.columns if c.lower().startswith("charge-sheet")), None)
    out = pd.DataFrame({
        "year": year,
        "level": ["national" if TOTAL_ROW.match(n) else "state" for n in df["State/UT"]],
        "name": [("India" if TOTAL_ROW.match(n) else canonical_name(n)) for n in df["State/UT"]],
        "total_cases": df[total].astype(int),
        "ipc_bns_cases": NAN,
        "sll_cases": NAN,
        "crime_rate": df[rate].astype(float),
        "chargesheet_rate": df[cs].astype(float) if cs else NAN,
        "source_file": path.name,
        "source_tier": tier,
    })
    return out[COLUMNS]


def _national_file(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    return pd.DataFrame({
        "year": df["year"], "level": "national", "name": "India",
        "total_cases": df["total_cases"], "ipc_bns_cases": df["ipc_bns_cases"], "sll_cases": df["sll_cases"],
        "crime_rate": df["total_rate"], "chargesheet_rate": NAN,
        "source_file": path.name, "source_tier": "primary",
    })[COLUMNS]


def _metro_file(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    return pd.DataFrame({
        "year": df["year"], "level": "metro_aggregate", "name": [f"{c} metropolitan cities" for c in df["cities"]],
        "total_cases": df["total_cases"], "ipc_bns_cases": df["ipc_bns_cases"], "sll_cases": df["sll_cases"],
        "crime_rate": NAN, "chargesheet_rate": df["ipc_bns_chargesheet_rate_pct"],
        "source_file": path.name, "source_tier": "primary",
    })[COLUMNS]


def check_consistency(df: pd.DataFrame) -> list[str]:
    """State/UT rows of a year must add up to that year's national total (NCRB tables do)."""
    problems = []
    for year, g in df.groupby("year"):
        states = g[g["level"] == "state"]
        national = g[(g["level"] == "national")]
        if states.empty or national.empty:
            continue
        s, n = int(states["total_cases"].sum()), int(national["total_cases"].iloc[0])
        if s != n:
            problems.append(f"{year}: state/UT rows sum to {s:,} but national total is {n:,}")
        if len(states) != 36:
            problems.append(f"{year}: expected 36 states/UTs, found {len(states)}")
    return problems


def build(reference_dir: Path = REFERENCE_DIR, primary_dir: Path | None = None) -> tuple[pd.DataFrame, dict]:
    """Combine every reference file into one tidy frame plus a provenance record.

    Rows from NCRB's own downloaded tables (``primary_dir``, files named
    ``cii<year>_table_1a1.(csv|xlsx)``) replace secondary rows for the same year and level.
    """
    manifest = json.loads((reference_dir / "sources.json").read_text(encoding="utf-8"))
    frames = []
    for fname, meta in manifest["files"].items():
        path = reference_dir / fname
        if meta["level"] == "national":
            frames.append(_national_file(path))
        elif meta["level"] == "metro_aggregate":
            frames.append(_metro_file(path))
        elif meta["level"] == "state":
            year = int(re.search(r"(20\d\d)", fname).group(1))
            frames.append(_wide_state_file(path, year, meta["tier"]))
    if primary_dir and primary_dir.exists():
        for path in sorted(primary_dir.glob("cii*_table_1a1.*")):
            year = int(re.search(r"cii(20\d\d)", path.name).group(1))
            frames.append(parse_state_table(path, year))
    df = pd.concat(frames, ignore_index=True)

    # Prefer primary over secondary for the same (year, level, name); then the national
    # Table 1.1 row (which carries the IPC/SLL split) over a total row inside a state table.
    df["_rank"] = (df["source_tier"] != "primary").astype(int) * 2 + df["sll_cases"].isna().astype(int)
    df = df.sort_values(["year", "level", "name", "_rank"]).drop_duplicates(["year", "level", "name"])
    df = df.drop(columns="_rank").reset_index(drop=True)

    problems = check_consistency(df)
    if problems:
        raise ValueError("NCRB totals failed consistency checks: " + "; ".join(problems))

    provenance = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "years": sorted(int(y) for y in df["year"].unique()),
        "latest_state_year": int(df.loc[df["level"] == "state", "year"].max()),
        "latest_national_year": int(df.loc[df["level"] == "national", "year"].max()),
        "sources": {
            f: {**m, "sha256": file_sha256(reference_dir / f)} for f, m in manifest["files"].items()
        },
        "not_yet_loaded": manifest.get("not_yet_loaded", []),
    }
    return df, provenance


def load(path: Path = OUT_PATH) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=COLUMNS)
    return pd.read_csv(path)


def load_provenance(path: Path = OUT_PATH) -> dict:
    p = path.with_suffix(".provenance.json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--reference", type=Path, default=REFERENCE_DIR)
    ap.add_argument("--primary", type=Path, default=PROJECT_ROOT / "data/raw/ncrb_cii")
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    a = ap.parse_args(argv)
    df, prov = build(a.reference, a.primary)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out, index=False)
    a.out.with_suffix(".provenance.json").write_text(json.dumps(prov, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(df)} rows to {a.out} (years {prov['years']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
