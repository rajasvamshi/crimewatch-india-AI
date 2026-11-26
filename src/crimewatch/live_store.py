"""Storage for live (daily) case counts pushed by authorised data partners.

NCRB publishes once a year. Near-real-time figures can only come from a police data
partner (CCTNS export, state police, Dial-112/ERSS) under a data-sharing agreement. This
module stores their daily aggregates in SQLite (swap for PostgreSQL in production via the
same SQL) and turns them into dashboard rows.

Only aggregate counts are accepted: no FIR numbers, names, addresses or other personal data,
which keeps the live feed outside most DPDP Act obligations for personal data.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

DASHBOARD_CATEGORIES = (
    "Theft", "Robbery", "Burglary", "Assault", "Kidnapping",
    "Cyber Crime", "Fraud", "Drug Offense", "Domestic Violence", "Murder",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS daily_counts (
    day           TEXT    NOT NULL,
    state_name    TEXT    NOT NULL,
    district_name TEXT    NOT NULL,
    category      TEXT    NOT NULL,
    source        TEXT    NOT NULL,
    crime_count   INTEGER NOT NULL CHECK (crime_count >= 0),
    arrests       INTEGER CHECK (arrests IS NULL OR arrests >= 0),
    received_at   TEXT    NOT NULL,
    PRIMARY KEY (day, state_name, district_name, category, source)
);

-- Public police announcements (press releases) scraped from official police websites.
-- These are NOT crime counts: police publicise selected cases (mostly arrests and
-- recoveries), so they are kept in their own table and never added to daily_counts.
-- Only the release date, police district/unit, police station, a derived category and
-- the official release URL are stored: no titles, names, addresses or FIR details.
CREATE TABLE IF NOT EXISTS announcements (
    release_id     TEXT    PRIMARY KEY,
    day            TEXT    NOT NULL,
    state_name     TEXT    NOT NULL,
    district_name  TEXT    NOT NULL,
    police_station TEXT,
    category       TEXT    NOT NULL,
    release_url    TEXT    NOT NULL,
    source         TEXT    NOT NULL,
    fetched_at     TEXT    NOT NULL
);
"""


@dataclass(frozen=True)
class Announcement:
    release_id: str
    day: date
    state_name: str
    district_name: str
    police_station: str | None
    category: str
    release_url: str


@dataclass(frozen=True)
class DailyCount:
    day: date
    state_name: str
    district_name: str
    category: str
    crime_count: int
    arrests: int | None = None


class LiveStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._connect() as con:
            con.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path, timeout=10)
        con.execute("PRAGMA journal_mode=WAL")
        return con

    def upsert(self, rows: Iterable[DailyCount], source: str) -> int:
        """Insert or replace rows (a partner may resend a corrected day). Returns row count."""
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        data = [
            (r.day.isoformat(), r.state_name, r.district_name, r.category, source, r.crime_count, r.arrests, now)
            for r in rows
        ]
        with self._lock, self._connect() as con:
            con.executemany(
                "INSERT OR REPLACE INTO daily_counts "
                "(day, state_name, district_name, category, source, crime_count, arrests, received_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                data,
            )
        return len(data)

    def frame(self) -> pd.DataFrame:
        with self._connect() as con:
            return pd.read_sql_query("SELECT * FROM daily_counts", con)

    def status(self) -> dict:
        with self._connect() as con:
            n, last_day, last_received, sources = con.execute(
                "SELECT COUNT(*), MAX(day), MAX(received_at), COUNT(DISTINCT source) FROM daily_counts"
            ).fetchone()
        return {"records": n, "latest_day": last_day, "last_received": last_received, "sources": sources}


    # -- police announcements ------------------------------------------------------------
    def upsert_announcements(self, rows: Iterable[Announcement], source: str) -> int:
        """Insert new releases; a re-scrape of the same release just refreshes it."""
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        data = [
            (a.release_id, a.day.isoformat(), a.state_name, a.district_name, a.police_station, a.category,
             a.release_url, source, now)
            for a in rows
        ]
        with self._lock, self._connect() as con:
            con.executemany(
                "INSERT OR REPLACE INTO announcements (release_id, day, state_name, district_name, "
                "police_station, category, release_url, source, fetched_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                data,
            )
        return len(data)

    def announcements_frame(self) -> pd.DataFrame:
        with self._connect() as con:
            return pd.read_sql_query("SELECT * FROM announcements", con)

    def announcements_status(self) -> dict:
        with self._connect() as con:
            n, first, last, fetched, sources = con.execute(
                "SELECT COUNT(*), MIN(day), MAX(day), MAX(fetched_at), COUNT(DISTINCT source) FROM announcements"
            ).fetchone()
        return {"releases": n, "first_day": first, "latest_day": last, "last_fetched": fetched, "sources": sources}


def to_dashboard_rows(live: pd.DataFrame, after_year: int) -> pd.DataFrame:
    """Aggregate daily counts into yearly dashboard rows for years after the official data.

    Years already covered by NCRB are skipped so the two sources never double-count.
    The current (partial) year is labelled by the dashboard as year-to-date.
    """
    cols = ["year", "state_name", "district_name", "category", "crime_type", "crime_count", "arrests"]
    if live.empty:
        return pd.DataFrame(columns=cols)
    df = live.copy()
    df["year"] = pd.to_datetime(df["day"]).dt.year
    df = df[df["year"] > after_year]
    if df.empty:
        return pd.DataFrame(columns=cols)
    df["arrests"] = df["arrests"].fillna(0)
    out = df.groupby(["year", "state_name", "district_name", "category"], as_index=False)[
        ["crime_count", "arrests"]
    ].sum()
    from .etl_dashboard import CRIME_TYPE

    out["crime_type"] = out["category"].map(CRIME_TYPE)
    return out[cols].astype({"year": int, "crime_count": int, "arrests": int})
