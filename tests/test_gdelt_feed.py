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


def test_english_needs_crime_headline_and_private_title():
    (i,) = g.parse_rows([_row("https://ex.in/f", "Woman assaulted, accused absconding", ["RAPE"], UP)])
    assert i.category == "Assault" and i.precision == "state"
    # themes alone never make an English article an incident
    outage = _row("https://ex.in/f2", "Microsoft declares Code Red after outage", ["CYBER_ATTACK"], LKO)
    assert list(g.parse_rows([outage])) == []
    assert list(g.parse_rows([_row("https://ex.in/f3", "Tempo rams into bus stop, three killed", ["KILL"], LKO)])) == []
    (j,) = g.parse_rows([_row("https://ex.in/g", "Girl raped in village, two arrested", [], LKO)])
    assert j.category == "Sexual violence" and j.title is None


def test_translated_rows_use_hindi_words_then_strict_themes():
    row = _row("https://hi.ex.in/h", "लखनऊ में दुकान से चोरी", [], LKO)
    (i,) = g.parse_rows([row], origin="news-translated")
    assert i.category == "Theft" and i.origin == "news-translated"
    ml = _row("https://ml.ex.in/m", "തട്ടിക്കൊണ്ടുപോയി", ["KIDNAP", "ARREST"], LKO)
    assert next(g.parse_rows([ml], origin="news-translated")).category == "Kidnapping"
    # an unreadable headline with only a robbery theme is too weak (Gujarati "controversy" stories)
    gu = _row("https://gu.ex.in/r", "જૂનાગઢ વિવાદ", ["CRIME_COMMON_ROBBERY", "ARREST"], LKO)
    assert list(g.parse_rows([gu], origin="news-translated")) == []
    weak = _row("https://ml.ex.in/w", "something", ["CRIME_COMMON_ROBBERY"], LKO)
    assert list(g.parse_rows([weak], origin="news-translated")) == []


def test_outlets_and_place_names():
    foreign = _row("https://mzamin.com/x", "Man robbed at knifepoint", [], LKO, source="mzamin.com")
    court = _row("https://indiankanoon.org/doc/1", "Murder appeal dismissed", [], LKO, source="indiankanoon.org")
    assert list(g.parse_rows([foreign, court])) == []
    hyd = "4#Hyderabad, Andhra Pradesh, India#IN#IN02##17.38#78.47#-1#5"
    (i,) = g.parse_rows([_row("https://ex.in/hy", "Two held for robbery in Hyderabad", [], hyd)])
    assert i.state == "Telangana" and i.place == "Hyderabad, Telangana"
    odi = "5#Orissa, India#IN#IN21##20.5#84.4#IN21#5"
    (j,) = g.parse_rows([_row("https://ex.in/od", "Man held for theft", [], odi)])
    assert j.state == "Odisha"


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


def test_court_followups_medicines_and_political_hindi_dropped():
    rows = [
        _row("https://ex.in/k1", "Delhi HC grants bail to murder accused", ["KILL"], LKO),
        _row("https://ex.in/k2", "Man convicted in 2007 robbery case", [], LKO),
        _row("https://ex.in/k3", "Raid on spurious, adulterated drugs unit", ["CRIME_ILLEGAL_DRUGS"], LKO),
    ]
    assert list(g.parse_rows(rows)) == []
    hi = [
        _row("https://hi.ex.in/p1", "खड़गे बोले, भाजपा का संविधान पर हमला", [], LKO),
        _row("https://hi.ex.in/p2", "जवानों ने हमला करने का अभ्यास किया", [], LKO),
    ]
    assert list(g.parse_rows(hi, origin="news-translated")) == []
    (i,) = g.parse_rows([_row("https://hi.ex.in/p3", "युवक पर चाकू से जानलेवा हमला", [], LKO)], origin="news-translated")
    assert i.category == "Assault"
    # an attack *at* a court is a new incident
    (j,) = g.parse_rows([_row("https://ex.in/k4", "Man attacked with sickles outside Pune court", [], LKO)])
    assert j.category == "Assault"


def test_repeated_place_names_collapsed():
    dl = "4#Delhi, Delhi, India#IN#IN07##28.6#77.2#-1#5"
    (i,) = g.parse_rows([_row("https://ex.in/dl", "Two held for robbery", [], dl)])
    assert i.place == "Delhi" and i.state == "Delhi"


def test_recheck_previous_items():
    old = {"origin": "news", "title": "Delhi HC grants bail", "place": "Delhi"}
    assert g.recheck(old) is None
    kept = g.recheck({"origin": "news", "title": "Two held for robbery", "place": "Delhi, Delhi"})
    assert kept["place"] == "Delhi"
    assert g.recheck({"origin": "police", "title": None, "place": "x"})["place"] == "x"


def test_business_policy_and_political_stories_dropped():
    rows = [
        _row("https://ex.in/b1", "Cipla receives USFDA nod for generic asthma drug", [], LKO),
        _row("https://ex.in/b2", "Smaller cities report higher cyber threat exposure than metros", [], LKO),
        _row("https://ex.in/b3", "People of Tamil Nadu will never forgive TVK govt over fraud: BJP", [], LKO),
        _row("https://ex.in/b4", "FPJ Quick Take: police file FIR against comedian", [], LKO),
    ]
    assert list(g.parse_rows(rows)) == []
    (i,) = g.parse_rows([_row("https://ex.in/b5", "Two held with ganja worth Rs 2 lakh", [], LKO)])
    assert i.category == "Drug Offense"
    (j,) = g.parse_rows([_row("https://ex.in/b6", "Man duped of Rs 25 lakh in online fraud", [], LKO)])
    assert j.category == "Cyber Crime"
    hi = _row("https://hi.ex.in/b7", "भोपाल रेल मंडल में चेतावनी सिस्टम", ["KIDNAP", "ARREST"], LKO)
    assert list(g.parse_rows([hi], origin="news-translated")) == []
