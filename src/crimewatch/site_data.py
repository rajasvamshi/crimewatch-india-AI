"""Build the JSON files the public website reads (``web/public/data/``).

Each run:
1. loads the incidents already published (from the live site, or a local file);
2. adds new news incidents from GDELT for the window since the last run;
3. adds Delhi Police press releases (placed at their police district's centre);
4. drops anything older than ``--keep-days``;
5. writes ``incidents.json`` (map points), ``summary.json`` (counts for charts and
   headline numbers), ``official.json`` (NCRB yearly totals) and ``meta.json``.

Run: ``python -m src.crimewatch.site_data --out web/public/data --previous <url-or-path>``
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import gdelt_feed, ncrb_official
from .delhi_police import NOT_CRIME, PoliteFetcher, classify, crawl

# Approximate centre of each Delhi Police district / unit headquarters (lat, lon).
DELHI_DISTRICTS = {
    "New Delhi": (28.6139, 77.2090), "Central": (28.6510, 77.2310), "North": (28.6810, 77.2050),
    "North West": (28.7040, 77.1310), "North East": (28.6920, 77.2890), "Shahdara": (28.6730, 77.2890),
    "East": (28.6230, 77.2950), "South": (28.5290, 77.2100), "South East": (28.5600, 77.2620),
    "South West": (28.5830, 77.0720), "West": (28.6500, 77.1000), "Outer": (28.6890, 77.0660),
    "Outer North": (28.8020, 77.1020), "Rohini": (28.7380, 77.1100), "Dwarka": (28.5920, 77.0460),
    "IGI Airport": (28.5562, 77.1000), "Metro": (28.6328, 77.2197), "Railways": (28.6430, 77.2190),
    "Crime Branch": (28.6280, 77.2400), "Special Cell": (28.5900, 77.2200), "EOW": (28.6280, 77.2400),
    "IFSO": (28.5900, 77.2200), "Unspecified": (28.6280, 77.2400),
}


def _load_previous(src: str | None) -> list[dict]:
    if not src:
        return []
    try:
        if src.startswith("http"):
            req = urllib.request.Request(src, headers={"User-Agent": gdelt_feed.USER_AGENT})  # noqa: S310
            with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310  # nosec B310
                return json.loads(r.read())["incidents"]
        p = Path(src)
        return json.loads(p.read_text())["incidents"] if p.exists() else []
    except (OSError, ValueError, KeyError):
        return []


def delhi_incidents(days: int) -> list[dict]:
    try:
        releases = crawl(PoliteFetcher(delay=3.0), days=days, max_pages=3)
    except (OSError, PermissionError):
        return []
    out = []
    for r in releases:
        cat = classify(f"{r.site_category or ''} {r.title}")
        if cat in NOT_CRIME:
            continue
        lat, lon = DELHI_DISTRICTS.get(r.district or "Unspecified", DELHI_DISTRICTS["Unspecified"])
        place = f"{r.police_station + ', ' if r.police_station else ''}{r.district or 'Delhi'} district, Delhi"
        out.append({
            "id": "dp-" + gdelt_feed.hashlib.sha256(r.url.encode()).hexdigest()[:13],
            "ts": f"{r.day.isoformat()}T12:00:00Z",
            "category": cat if cat != "Other" else "Other crime",
            "place": place, "state": "Delhi", "lat": lat, "lon": lon, "precision": "district",
            "title": None,  # releases name accused; the PDF link carries the details
            "source": "delhipolice.gov.in", "url": r.url, "origin": "police",
        })
    return out


def summarise(incidents: list[dict], now: datetime) -> dict:
    day = lambda i: i["ts"][:10]  # noqa: E731
    last24 = [i for i in incidents if i["ts"] >= (now - timedelta(hours=24)).isoformat()[:19]]
    by_day = defaultdict(Counter)
    for i in incidents:
        by_day[day(i)][i["category"]] += 1
    return {
        "generated_at": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "total": len(incidents),
        "last_24h": len(last24),
        "states_last_24h": len({i["state"] for i in last24 if i["state"]}),
        "by_category": Counter(i["category"] for i in incidents).most_common(),
        "by_category_24h": Counter(i["category"] for i in last24).most_common(),
        "by_state": Counter(i["state"] for i in incidents if i["state"]).most_common(40),
        "by_place": Counter(i["place"] for i in incidents).most_common(25),
        "by_day": [{"day": d, **c, "total": sum(c.values())} for d, c in sorted(by_day.items())],
        "by_origin": Counter(i["origin"] for i in incidents).most_common(),
    }


def official() -> dict:
    df = ncrb_official.load()
    prov = ncrb_official.load_provenance()
    return {
        "rows": json.loads(df.to_json(orient="records")),
        "sources": prov.get("sources", {}),
        "not_yet_loaded": prov.get("not_yet_loaded", []),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=Path("web/public/data"))
    ap.add_argument("--previous", help="URL or path of the incidents.json already published")
    ap.add_argument("--hours", type=float, default=2.0, help="news window to fetch when there is no history")
    ap.add_argument("--keep-days", type=int, default=30)
    ap.add_argument("--no-delhi", action="store_true")
    ap.add_argument("--max-hours", type=float, default=48.0, help="cap on catch-up after a gap")
    a = ap.parse_args(argv)

    now = datetime.now(timezone.utc)
    prev = _load_previous(a.previous)
    last = max((i["ts"] for i in prev if i["origin"].startswith("news")), default=None)
    start = (datetime.fromisoformat(last.replace("Z", "+00:00")) - timedelta(minutes=30)) if last else \
        now - timedelta(hours=a.hours)
    start = max(start, now - timedelta(hours=a.max_hours))
    news = gdelt_feed.as_dicts(gdelt_feed.fetch(start, now))
    police = [] if a.no_delhi else delhi_incidents(days=3)

    merged: dict[str, dict] = {i["id"]: i for i in prev}
    for i in news + police:
        merged[i["id"]] = i
    cutoff = (now - timedelta(days=a.keep_days)).isoformat()[:19]
    incidents = sorted((i for i in merged.values() if i["ts"] >= cutoff), key=lambda i: i["ts"], reverse=True)

    a.out.mkdir(parents=True, exist_ok=True)
    meta = {
        "generated_at": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "window": {"from": start.isoformat(timespec="minutes"), "to": now.isoformat(timespec="minutes")},
        "new_news": len(news), "new_police": len(police), "kept_days": a.keep_days,
        "sources": {
            "news": "GDELT 2.0 Global Knowledge Graph (gdeltproject.org), English + translated Indian-language news",
            "police": "Delhi Police press releases (delhipolice.gov.in/newpressrelease)",
            "official": "NCRB Crime in India 2023 and 2024",
        },
    }
    (a.out / "incidents.json").write_text(json.dumps({"generated_at": meta["generated_at"], "incidents": incidents},
                                                     separators=(",", ":"), ensure_ascii=False))
    (a.out / "summary.json").write_text(json.dumps(summarise(incidents, now), ensure_ascii=False, indent=1))
    (a.out / "official.json").write_text(json.dumps(official(), ensure_ascii=False, indent=1))
    (a.out / "meta.json").write_text(json.dumps(meta, indent=1))
    print(f"{len(news)} new news, {len(police)} police, {len(incidents)} incidents kept "
          f"(window {start:%Y-%m-%d %H:%M} to {now:%H:%M} UTC)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
