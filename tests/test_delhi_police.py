from datetime import date
from pathlib import Path

import pytest

from src.crimewatch import delhi_police as dp
from src.crimewatch.live_store import LiveStore, to_dashboard_rows

FIXTURE = Path(__file__).parent / "fixtures" / "delhi_police_newpressrelease.html"


@pytest.fixture
def releases():
    return dp.parse_index(FIXTURE.read_text(encoding="utf-8"))


def test_parses_table_by_column(releases):
    assert len(releases) == 8
    r = releases[1]
    assert r.day == date(2026, 11, 25)  # "11/25/2026 12:00:00 AM" is month-first
    assert r.district == "East" and r.police_station == "New Ashok Nagar"
    assert r.url.startswith("https://delhipolice.gov.in/Images/newpressrelease/14498_")
    assert releases[0].police_station is None  # empty cell keeps column alignment


def test_categories(releases):
    cats = [a.category for a in dp.to_announcements(releases)]
    assert cats == ["Snatching", "Robbery", "Missing persons traced", "Gambling", "Snatching",
                    "Drug Offense", "Cyber Crime", "Missing persons traced"]
    assert {a.district_name for a in dp.to_announcements(releases)} >= {"North East", "Crime Branch", "Rohini"}


@pytest.mark.parametrize("text,expected", [
    ("11/25/2026 12:00:00 AM", date(2026, 11, 25)),
    ("03/04/2026 12:00:00 AM", date(2026, 3, 4)),
    ("25.11.2026", date(2026, 11, 25)),
    ("25-11-2026", date(2026, 11, 25)),
    ("2026-11-25", date(2026, 11, 25)),
    ("25th November, 2026", date(2026, 11, 25)),
    ("no date", None),
])
def test_parse_date(text, expected):
    assert dp.parse_date(text) == expected


def test_heuristic_fallback_without_header():
    html = """<ul><li><a href="/x/1.pdf">Two held for vehicle theft, PS Sagarpur, South West District</a>
              <span>24.11.2026</span></li></ul>"""
    (r,) = dp.parse_index(html)
    assert r.district == "South West" and r.police_station == "Sagarpur"
    assert dp.classify(r.title) == "Theft"


def test_store_keeps_no_titles_and_never_mixes_with_counts(tmp_path, releases):
    store = LiveStore(tmp_path / "live.db")
    n = store.upsert_announcements(dp.to_announcements(releases), dp.SOURCE)
    store.upsert_announcements(dp.to_announcements(releases), dp.SOURCE)  # idempotent
    ann = store.announcements_frame()
    assert n == 8 and len(ann) == 8
    assert "title" not in ann.columns
    assert not ann.astype(str).apply(lambda c: c.str.contains("ARRESTED|SNATCHER INVOLVED")).any().any()
    assert store.frame().empty and to_dashboard_rows(store.frame(), 2022).empty
    st = store.announcements_status()
    assert st["latest_day"] == "2026-11-25" and st["first_day"] == "2026-11-23"


def test_cli_offline(tmp_path, capsys):
    rc = dp.main(["--html-file", str(FIXTURE), "--db", str(tmp_path / "l.db")])
    assert rc == 0 and "stored 8 releases" in capsys.readouterr().out


def test_robots_respected(monkeypatch):
    f = dp.PoliteFetcher(delay=0)
    monkeypatch.setattr(f, "allowed", lambda url: False)
    with pytest.raises(PermissionError):
        f.get(dp.INDEX_URL)


def test_crawl_stops_when_page_repeats(monkeypatch):
    html = FIXTURE.read_text(encoding="utf-8")
    calls = []

    class Fake(dp.PoliteFetcher):
        def get(self, url):
            calls.append(url)
            return html

    got = dp.crawl(Fake(delay=0), days=30, max_pages=5, today=date(2026, 11, 25))
    assert len(got) == 8 and len(calls) == 2  # page 2 returned nothing new -> stop


def test_csv_history_round_trip(tmp_path):
    csv = tmp_path / "pub.csv"
    assert dp.main(["--html-file", str(FIXTURE), "--db", str(tmp_path / "a.db"), "--csv", str(csv)]) == 0
    # a fresh runner (empty DB) starts from the committed CSV, so history accumulates
    assert dp.main(["--html-file", str(FIXTURE), "--db", str(tmp_path / "b.db"), "--csv", str(csv)]) == 0
    back = dp.read_csv(csv)
    assert len(back) == 8 and back[0].state_name == "Delhi"
