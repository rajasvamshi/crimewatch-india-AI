"""Daily ingester for Delhi Police press releases ("police announcements").

What this is
------------
Delhi Police publish press releases every day at https://delhipolice.gov.in/newpressrelease,
each tagged with a police district (or unit such as Crime Branch / Special Cell) and often a
police station. They are the most frequent official, public, location-tagged crime signal
in India, but they are **announcements, not crime statistics**: police choose which cases to
publicise (mostly arrests, busts and recoveries). The dashboard therefore shows them in a
separate "Police announcements" panel and never adds them to case counts.

What is stored
--------------
Only release date, district/unit, police station, a keyword-derived category and the
official release URL (see ``live_store.announcements``). Titles are read in memory to pick
a category and then discarded, so no names of accused, victims or addresses are kept.

Politeness
----------
robots.txt is checked before every host, requests are spaced ``delay`` seconds apart, a
descriptive User-Agent is sent, and paging stops as soon as releases are older than
``--days``.

Run daily (cron / GitHub Actions / systemd timer)::

    python -m src.crimewatch.delhi_police --days 3
    python -m src.crimewatch.delhi_police --html-file saved_page.html   # offline parse
"""

from __future__ import annotations

import argparse
import hashlib
import re
import time
import urllib.request
import urllib.robotparser
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

from .live_store import Announcement, LiveStore
from .settings import Settings

INDEX_URL = "https://delhipolice.gov.in/newpressrelease"
PUBLIC_CSV = Path(__file__).resolve().parents[2] / "data/public/delhi_police_announcements.csv"
SOURCE = "delhi_police_press_releases"
STATE = "Delhi"
USER_AGENT = "CrimeWatchIndia-DataBot/0.2 (+https://github.com/rajasvamshi/crimewatch-india-AI)"

# Territorial districts and specialised units as they appear on the site.
DISTRICTS = [
    "North West", "North East", "North", "South West", "South East", "South", "New Delhi", "Central",
    "Outer North", "Outer", "West", "East", "Shahdara", "Dwarka", "Rohini",
    "Crime Branch", "Special Cell", "IGI Airport", "Metro", "Railways", "EOW", "IFSO",
]
_DISTRICT_RE = [
    (d, re.compile(r"\b" + d.replace(" ", r"[\s\-]*") + r"\b(\s*district)?", re.I))
    for d in sorted(DISTRICTS, key=len, reverse=True)
]

# First matching rule wins; order puts specific heads before generic ones.
CATEGORY_RULES: list[tuple[str, re.Pattern]] = [
    # Not crimes: tracing missing people (Operation MILAP) and public-awareness notes.
    ("Missing persons traced", re.compile(r"\b(operation mil+a+p|reunit\w*|traced)\b", re.I)),
    ("Awareness", re.compile(r"\b(awareness|advisory|campaign|workshop|felicitat\w*)\b", re.I)),
    ("Murder", re.compile(r"\b(murder|homicide|killed|killing)\b", re.I)),
    ("Kidnapping", re.compile(r"\b(kidnap\w*|abduct\w*|traffick\w*|missing child)", re.I)),
    ("Cyber Crime", re.compile(r"\b(cyber|online|phishing|sextortion|digital arrest|IFSO|hack\w*)\b", re.I)),
    ("Drug Offense", re.compile(r"\b(ndps|drugs?|narcotic\w*|heroin|smack|ganja|cocaine|mdma|charas|opium)\b", re.I)),
    ("Snatching", re.compile(r"\b(snatch\w*)\b", re.I)),
    ("Robbery", re.compile(r"\b(robber\w*|robbed|dacoit\w*|loot\w*|extortion)\b", re.I)),
    ("Burglary", re.compile(r"\b(burglar\w*|house[- ]?break\w*|break[- ]?in)\b", re.I)),
    ("Theft", re.compile(r"\b(theft|thie\w+|stolen|vehicle lifter|auto[- ]?lifter|pickpocket\w*)\b", re.I)),
    ("Fraud", re.compile(r"\b(fraud\w*|cheat\w*|duped|scam\w*|forg\w*|counterfeit|fake)\b", re.I)),
    ("Domestic Violence", re.compile(r"\b(dowry|domestic violence|cruelty)\b", re.I)),
    ("Assault", re.compile(r"\b(assault\w*|attack\w*|stabb\w*|shot|firing|hurt|rape|molest\w*|pocso)\b", re.I)),
    ("Arms Act", re.compile(r"\b(arms act|pistol|firearm\w*|cartridges?|country[- ]made)\b", re.I)),
    ("Gambling", re.compile(r"\b(betting|gambl\w*|satta)\b", re.I)),
]
NOT_CRIME = {"Missing persons traced", "Awareness"}

_DATE_PATTERNS = [
    # The site's "Issue Date" column is US-style with a time: "11/25/2026 12:00:00 AM".
    (re.compile(r"\b(\d{1,2})/(\d{1,2})/(20\d\d)\s+\d{1,2}:\d{2}(?::\d{2})?\s*[AP]M\b", re.I), "mdy"),
    (re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](20\d\d)\b"), "dmy"),
    (re.compile(r"\b(20\d\d)-(\d{1,2})-(\d{1,2})\b"), "ymd"),
    (re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\.?,?\s+(20\d\d)\b"), "dMy"),
]
_PS_RE = re.compile(r"\b(?:PS|P\.S\.|Police Station)[\s:.\-]+([A-Z][A-Za-z.\s]{2,40}?)(?=[,;|)\n]|$|\s{2,})")


@dataclass(frozen=True)
class PressRelease:
    day: date
    title: str
    url: str
    district: str | None
    police_station: str | None
    site_category: str | None = None


def parse_date(text: str) -> date | None:
    for rx, kind in _DATE_PATTERNS:
        m = rx.search(text)
        if not m:
            continue
        try:
            if kind == "mdy":
                return date(int(m[3]), int(m[1]), int(m[2]))
            if kind == "dmy":
                try:
                    return date(int(m[3]), int(m[2]), int(m[1]))
                except ValueError:  # 11/25/2026 without a time: month first
                    return date(int(m[3]), int(m[1]), int(m[2]))
            if kind == "ymd":
                return date(int(m[1]), int(m[2]), int(m[3]))
            return datetime.strptime(f"{m[1]} {m[2][:3]} {m[3]}", "%d %b %Y").date()
        except ValueError:
            continue
    return None


def find_district(text: str) -> str | None:
    for name, rx in _DISTRICT_RE:
        if rx.search(text):
            return name
    return None


def find_police_station(text: str) -> str | None:
    m = _PS_RE.search(text)
    return re.sub(r"\s+", " ", m[1]).strip() if m else None


def _clean_ps(text: str) -> str:
    t = re.sub(r"^(PS|P\.S\.|Police Station)[\s:.\-]+", "", text.strip(), flags=re.I)
    return t.title()


def classify(title: str) -> str:
    for category, rx in CATEGORY_RULES:
        if rx.search(title):
            return category
    return "Other"


class _RowCollector(HTMLParser):
    """Collect table rows (one cell per td/th) and list items / cards (one cell per block)."""

    ROW_TAGS = {"tr", "li", "article"}
    BLOCK_TAGS = {"div", "span", "p", "br"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows: list[tuple[list[str], list[str]]] = []
        self._stack: list[str] = []  # open row tags
        self._cells: list[str] = []
        self._buf: list[str] = []
        self._links: list[str] = []

    def _split_tags(self) -> set[str]:
        return {"td", "th"} if self._stack[0] == "tr" else {"td", "th"} | self.BLOCK_TAGS

    def handle_starttag(self, tag, attrs):
        if tag in self.ROW_TAGS:
            if not self._stack:
                self._cells, self._buf, self._links = [], [], []
            self._stack.append(tag)
            return
        if not self._stack:
            return
        if self._stack[0] == "tr":
            if tag in {"td", "th"}:
                self._buf = []
        elif tag in self._split_tags():
            self._flush()
        if tag == "a":
            href = dict(attrs).get("href")
            if href and not href.startswith(("javascript:", "#", "mailto:")):
                self._links.append(href)

    def handle_endtag(self, tag):
        if not self._stack:
            return
        if tag in self.ROW_TAGS and tag in self._stack:
            while self._stack and self._stack.pop() != tag:
                pass
            if not self._stack:
                if tag != "tr":
                    self._flush()
                if any(self._cells):
                    self.rows.append((self._cells, self._links))
            return
        if self._stack[0] == "tr":
            if tag in {"td", "th"}:
                self._flush(keep_empty=True)  # keep column positions for empty cells
        elif tag in self._split_tags():
            self._flush()

    def handle_data(self, data):
        if self._stack:
            self._buf.append(data)

    def _flush(self, keep_empty: bool = False):
        text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
        if text or keep_empty:
            self._cells.append(text)
        self._buf = []


_HEADER_FIELDS = {
    "title": re.compile(r"^(title|subject)", re.I),
    "district": re.compile(r"^district", re.I),
    "police_station": re.compile(r"^police\s*station|^p\.?s\.?$", re.I),
    "category": re.compile(r"^category", re.I),
    "date": re.compile(r"date", re.I),
}


def _header_map(cells: list[str]) -> dict[str, int] | None:
    found = {}
    for i, c in enumerate(cells):
        for field, rx in _HEADER_FIELDS.items():
            if field not in found and rx.search(c):
                found[field] = i
                break
    return found if {"title", "date"} <= found.keys() else None


def parse_index(html: str, base_url: str = INDEX_URL) -> list[PressRelease]:
    """Extract press releases from a listing page. Rows without a date or link are skipped.

    The live page is a table with columns ``Sl. No. | Title | District | Police Station |
    Category | Issue Date | Download/View``; when that header is present, cells are read
    by column. Otherwise (layout change) the row text is searched heuristically.
    """
    p = _RowCollector()
    p.feed(html)
    out: dict[str, PressRelease] = {}
    header: dict[str, int] | None = None
    for cells, links in p.rows:
        if not links and (hm := _header_map(cells)):
            header = hm
            continue
        if header and len(cells) >= max(header.values()) + 1:
            day = parse_date(cells[header["date"]])
            if day is None or not links:
                continue
            link = next((h for h in links if h.lower().endswith(".pdf")), links[0])
            url = urljoin(base_url, link)

            def cell(field: str, header=header, cells=cells) -> str | None:
                i = header.get(field)
                return cells[i].strip() if i is not None and cells[i].strip() else None

            title = cell("title") or ""
            dist_text = cell("district") or ""
            ps = cell("police_station")
            out[url] = PressRelease(
                day=day, title=title, url=url,
                district=find_district(dist_text) or find_district(title),
                police_station=_clean_ps(ps) if ps else find_police_station(title),
                site_category=cell("category"),
            )
            continue
        joined = " | ".join(cells)
        day = parse_date(joined)
        if day is None or not links:
            continue
        link = next((h for h in links if h.lower().endswith(".pdf")), links[0])
        url = urljoin(base_url, link)
        non_meta = [c for c in cells if parse_date(c) is None and not re.fullmatch(r"\d+\.?", c)]
        title = max(non_meta, key=len) if non_meta else joined
        out[url] = PressRelease(
            day=day, title=title, url=url, district=find_district(joined), police_station=find_police_station(joined)
        )
    return list(out.values())


def to_announcements(releases: list[PressRelease]) -> list[Announcement]:
    return [
        Announcement(
            release_id=hashlib.sha256(r.url.encode("utf-8")).hexdigest()[:16],
            day=r.day,
            state_name=STATE,
            district_name=r.district or "Unspecified",
            police_station=r.police_station,
            category=classify(f"{r.site_category or ''} {r.title}"),
            release_url=r.url,
        )
        for r in releases
    ]


class PoliteFetcher:
    def __init__(self, delay: float = 3.0, timeout: float = 60.0):
        self.delay, self.timeout = delay, timeout
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self._last = 0.0

    def allowed(self, url: str) -> bool:
        u = urlparse(url)
        base = f"{u.scheme}://{u.netloc}"
        if base not in self._robots:
            rp = urllib.robotparser.RobotFileParser(base + "/robots.txt")
            try:
                rp.read()
            except OSError:
                rp = None
            self._robots[base] = rp
        rp = self._robots[base]
        return True if rp is None else rp.can_fetch(USER_AGENT, url)

    def get(self, url: str) -> str:
        if urlparse(url).scheme != "https":
            raise ValueError(f"only https URLs are fetched: {url}")
        if not self.allowed(url):
            raise PermissionError(f"robots.txt disallows {url}")
        wait = self.delay - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})  # noqa: S310
        with urllib.request.urlopen(req, timeout=self.timeout) as r:  # noqa: S310  # nosec B310
            charset = r.headers.get_content_charset() or "utf-8"
            body = r.read().decode(charset, errors="replace")
        self._last = time.monotonic()
        return body


def crawl(
    fetcher: PoliteFetcher, days: int, max_pages: int = 10, index_url: str = INDEX_URL, today: date | None = None
) -> list[PressRelease]:
    """Read listing pages (``?page=0,1,...``) until releases are older than ``days``."""
    since = (today or date.today()) - timedelta(days=days)
    seen: dict[str, PressRelease] = {}
    for page in range(max_pages):
        url = index_url if page == 0 else f"{index_url}?page={page}"
        releases = parse_index(fetcher.get(url), url)
        new = [r for r in releases if r.url not in seen]
        if not new:
            break
        for r in new:
            if r.day >= since:
                seen[r.url] = r
        if min(r.day for r in new) < since:
            break
    return list(seen.values())


CSV_COLUMNS = ["release_id", "day", "state_name", "district_name", "police_station", "category", "release_url"]


def write_csv(store: LiveStore, path: Path) -> None:
    df = store.announcements_frame()
    df = df[df["source"] == SOURCE].sort_values(["day", "release_id"], ascending=[False, True])
    path.parent.mkdir(parents=True, exist_ok=True)
    df[CSV_COLUMNS].to_csv(path, index=False)


def read_csv(path: Path) -> list[Announcement]:
    import pandas as pd

    df = pd.read_csv(path, dtype=str).fillna("")
    return [
        Announcement(r.release_id, date.fromisoformat(r.day), r.state_name, r.district_name,
                     r.police_station or None, r.category, r.release_url)
        for r in df.itertuples()
    ]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Ingest Delhi Police press releases as police announcements.")
    ap.add_argument("--days", type=int, default=3, help="how far back to read (default 3)")
    ap.add_argument("--max-pages", type=int, default=10)
    ap.add_argument("--delay", type=float, default=3.0, help="seconds between requests")
    ap.add_argument("--db", type=Path, default=None, help="live store path (default CW_LIVE_DB)")
    ap.add_argument("--html-file", type=Path, help="parse a saved listing page instead of fetching")
    ap.add_argument("--csv", type=Path, default=None,
                    help="also merge into this CSV (history kept in git for the public dashboard)")
    a = ap.parse_args(argv)

    if a.html_file:
        releases = parse_index(a.html_file.read_text(encoding="utf-8", errors="replace"))
    else:
        releases = crawl(PoliteFetcher(delay=a.delay), a.days, a.max_pages)
    store = LiveStore(a.db or Settings.from_env().live_db_path)
    if a.csv and a.csv.exists():
        store.upsert_announcements(read_csv(a.csv), SOURCE)
    n = store.upsert_announcements(to_announcements(releases), SOURCE)
    if a.csv:
        write_csv(store, a.csv)
    status = store.announcements_status()
    print(f"stored {n} releases; store holds {status['releases']} up to {status['latest_day']}")
    return 0 if releases else 2  # 2 = nothing parsed: layout may have changed, check the page


if __name__ == "__main__":
    raise SystemExit(main())
