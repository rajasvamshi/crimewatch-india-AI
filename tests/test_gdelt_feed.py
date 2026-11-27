import io
import zipfile
from datetime import datetime, timezone

from src.crimewatch import gdelt_feed as g


def _row(url, title, themes, loc2, date="20261127050000", source="example.in"):
    r = [""] * 27
    r[0], r[1], r[3], r[4] = "x", date, source, url
    r[7] = ";".join(themes)
    r[10] = loc2
    r[26] = f"<PAGE_TITLE>{title}</PAGE_TITLE>"
    return r


LKO = "4#Lucknow, Uttar Pradesh, India#IN#IN36#IN36a#26.85#80.9167#-2106102#120"
UP = "5#Uttar Pradesh, India#IN#IN36##27.25#80.75#IN36#300"
LONDON = "4#London, London, City of, United Kingdom#UK#UKH9##51.5#-0.1167#-2601889#10"


def test_india_city_incident():
    (i,) = g.parse_rows([_row("https://ex.in/a", "Two held for snatching chain in Lucknow", ["ARREST"], LKO)])
    assert (i.category, i.place, i.state) == ("Snatching", "Lucknow, Uttar Pradesh", "Uttar Pradesh")
    assert i.precision == "city"
    assert i.ts == "2026-11-27T05:00:00Z" and i.title.startswith("Two held")


def test_first_mentioned_place_must_be_india():
    loc = f"{LONDON};{LKO}"
    assert list(g.parse_rows([_row("https://ex.in/b", "Man robbed at knifepoint", [], loc)])) == []


def test_not_incident_and_politics_dropped():
    rows = [
        _row("https://ex.in/c", "Murder mystery film breaks box office records", ["KILL"], LKO),
        _row("https://ex.in/d", "Congress attacks BJP over price rise", [], LKO),
        _row("https://ex.in/e", "Budget session: opposition walkout", ["SOC_GENERALCRIME"], LKO),
    ]
    assert list(g.parse_rows(rows)) == []


def test_theme_fallback_and_private_title():
    (i,) = g.parse_rows([_row("https://ex.in/f", "Woman assaulted, accused absconding", ["RAPE"], UP)])
    assert i.category in {"Assault", "Sexual violence"} and i.precision == "state"
    (j,) = g.parse_rows([_row("https://ex.in/g", "Girl raped in village, two arrested", [], LKO)])
    assert j.category == "Sexual violence" and j.title is None


def test_translated_rows_use_themes():
    row = _row("https://hi.ex.in/h", "लखनऊ में लूट", ["CRIME_COMMON_ROBBERY"], LKO)
    (i,) = g.parse_rows([row], origin="news-translated")
    assert i.category == "Robbery" and i.origin == "news-translated"


def test_dedupe_by_url_and_syndicated_title():
    a = _row("https://ex.in/1", "Two held for snatching chain in Lucknow", [], LKO)
    b = _row("https://other.in/2", "Two held for snatching chain in Lucknow", [], LKO)
    c = _row("https://ex.in/1", "Two held for snatching chain in Lucknow", [], LKO)
    assert len(g.dedupe(g.parse_rows([a, b, c]))) == 1


def test_zip_round_trip_and_file_urls():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("x.gkg.csv", "\t".join(_row("https://ex.in/z", "Drugs worth Rs 2 crore seized", [], LKO)) + "\n")
    rows = list(g._rows(buf.getvalue()))
    assert next(g.parse_rows(rows)).category == "Drug Offense"
    utc = timezone.utc
    urls = g.file_urls(datetime(2026, 11, 27, 4, 50, tzinfo=utc), datetime(2026, 11, 27, 5, 20, tzinfo=utc))
    assert urls[0].endswith("20261127044500.gkg.csv.zip") and len(urls) == 6
