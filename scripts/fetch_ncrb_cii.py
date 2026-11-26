"""Download NCRB "Crime in India" files into data/raw/ncrb_cii/ with a hash manifest.

Run this from a machine whose network can reach NCRB / data.gov.in (the cloud build
environment "crimewatch-india-ai" allows ncrb.gov.in and data.gov.in):

    python scripts/fetch_ncrb_cii.py                 # default list below
    python scripts/fetch_ncrb_cii.py URL [URL ...]   # extra files, e.g. a data.gov.in CSV

Then save NCRB's State/UT table as ``data/raw/ncrb_cii/cii<year>_table_1a1.csv`` (or
.xlsx) and run ``python -m src.crimewatch.ncrb_official``; those rows replace the
secondary 2023 copy and add 2024 state/UT figures. robots.txt is honoured and requests
are spaced out.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/raw/ncrb_cii"
USER_AGENT = "CrimeWatchIndia-DataBot/0.2 (+https://github.com/rajasvamshi/crimewatch-india-AI)"
DEFAULT_URLS = [
    "https://www.ncrb.mha.gov.in/uploads/files/11CrimeinIndia2024-VolumeI.pdf",
    "https://www.ncrb.gov.in/uploads/files/9ACII2024Snapshots-StateandUTs.pdf",
]


def allowed(url: str, cache: dict[str, urllib.robotparser.RobotFileParser]) -> bool:
    host = urlparse(url)
    base = f"{host.scheme}://{host.netloc}"
    if base not in cache:
        rp = urllib.robotparser.RobotFileParser(base + "/robots.txt")
        try:
            rp.read()
        except OSError:
            rp = None  # unreachable robots.txt: treat as "no rules", like most crawlers
        cache[base] = rp
    rp = cache[base]
    return True if rp is None else rp.can_fetch(USER_AGENT, url)


def main(urls: list[str]) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    robots: dict = {}
    failed = 0
    for url in urls:
        if not allowed(url, robots):
            print(f"skip (robots.txt): {url}")
            continue
        if urlparse(url).scheme != "https":
            print(f"skip (not https): {url}")
            continue
        name = Path(urlparse(url).path).name
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310
        try:
            with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310  # nosec B310
                data = r.read()
        except OSError as e:
            print(f"FAILED {url}: {e}")
            failed += 1
            continue
        (OUT / name).write_bytes(data)
        manifest[name] = {
            "url": url,
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "retrieved": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        print(f"saved {name} ({len(data):,} bytes)")
        time.sleep(3)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or DEFAULT_URLS))
