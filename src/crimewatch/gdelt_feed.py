"""Daily India crime incidents from news, via the free GDELT 2.0 Global Knowledge Graph.

GDELT (https://www.gdeltproject.org) reads news worldwide every 15 minutes, in 65 languages
(the "translation" feed covers Hindi, Tamil, Bengali and other Indian-language outlets), and
publishes for each article its themes, the places it mentions with coordinates, and its URL.

This module turns those files into *reported incidents*:

* keep articles whose first-mentioned place is in India (city or state level);
* decide a crime category from the headline (same keyword rules as the Delhi Police feed) or,
  failing that, from strong GDELT crime themes;
* store category, place, coordinates (city/state centroid from GDELT, never an address),
  time, outlet and link. Headlines are kept as the "what happened" line, except for sexual
  violence and crimes against children, where only the category is shown.

These are news reports, not police statistics: one crime can appear in several outlets
(duplicates are merged by URL and headline) and automatic tagging makes mistakes. The site
labels them accordingly.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
import sys
import urllib.request
import zipfile
from collections.abc import Iterable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from html import unescape
from urllib.parse import urlparse

from .delhi_police import NOT_CRIME, classify

BASE = "http://data.gdeltproject.org/gdeltv2/"
USER_AGENT = "CrimeWatchIndia-DataBot/0.3 (+https://github.com/rajasvamshi/crimewatch-india-AI)"

csv.field_size_limit(sys.maxsize)

# GKG 2.1 columns (tab separated, no header)
C_DATE, C_SOURCE, C_URL, C_THEMES, C_LOC1, C_LOC2, C_EXTRAS = 1, 3, 4, 7, 9, 10, 26

# Strong theme evidence when the headline alone does not name a crime (e.g. translated titles).
THEME_CATEGORIES: list[tuple[str, set[str]]] = [
    ("Sexual violence", {"RAPE", "WB_2443_RAPE_AND_SEXUAL_VIOLENCE"}),
    ("Kidnapping", {"KIDNAP", "HUMAN_TRAFFICKING"}),
    ("Robbery", {"CRIME_COMMON_ROBBERY", "CRIME_LOOTING"}),
    ("Drug Offense", {"CRIME_ILLEGAL_DRUGS", "DRUG_TRADE"}),
    ("Cyber Crime", {"CYBER_ATTACK"}),
    ("Domestic Violence", {"WB_2441_DOMESTIC_VIOLENCE"}),
    ("Arson", {"CRM_ARSON"}),
]
CRIME_CONTEXT = {"SOC_GENERALCRIME", "ARREST", "TAX_FNCACT_POLICE", "TAX_FNCACT_CRIMINAL",
                 "WB_2082_LAW_ENFORCEMENT", "UNGP_CRIME_VIOLENCE"}
POLITICAL_OR_WAR = {"TAX_MILITARY_TITLE_SOLDIER", "MILITARY", "ARMEDCONFLICT", "ELECTION"}

# Headline keywords for categories the Delhi Police rules don't cover
EXTRA_RULES: list[tuple[str, re.Pattern]] = [
    ("Sexual violence", re.compile(r"\b(rape\w*|gang[- ]?rape\w*|sexual(ly)? assault\w*|molest\w*|pocso)\b", re.I)),
    ("Murder", re.compile(r"\b(hacked to death|bludgeoned|strangled|found dead|body found|shot dead)\b", re.I)),
    ("Cyber Crime", re.compile(r"\b(digital arrest|online fraud|sextortion)\b", re.I)),
    ("Arson", re.compile(r"\b(arson|set (on )?fire|torched)\b", re.I)),
]
# Headlines that mention crime words but are not crime incident reports: entertainment, sport,
# politics, accidents and disasters, terrorism/insurgency (a different subject), court rulings.
NOT_INCIDENT = re.compile(
    r"\b(film|movie|web series|trailer|box office|review|cricket|ipl|match|election|poll|budget|"
    r"opinion|editorial|explained|quiz|horoscope|stock|shares?|sensex|nifty|recruit\w*|"
    r"accident|collision|crash\w*|rams?|rammed|mishap|drown\w*|electrocut\w*|stampede|landslide|"
    r"flood\w*|blaze|fire broke|terror\w*|naxal\w*|maoist\w*|militant\w*|insurgen\w*|"
    r"anti-terror|26/11|outage|tiger|leopard|elephant)\b", re.I)

# Hindi headline keywords (the translated feed keeps the original-language title)
HINDI_RULES: list[tuple[str, re.Pattern]] = [
    ("Sexual violence", re.compile(r"(बलात्कार|दुष्कर्म|छेड़छाड़|यौन उत्पीड़न|पॉक्सो)")),
    ("Murder", re.compile(r"(हत्या|मर्डर|कत्ल|गोली मारकर|मौत के घाट)")),
    ("Kidnapping", re.compile(r"(अपहरण|अगवा|किडनैप)")),
    ("Robbery", re.compile(r"(लूट|डकैती)")),
    ("Snatching", re.compile(r"(झपटमारी|स्नैचिंग|चेन झपट)")),
    ("Burglary", re.compile(r"(सेंधमारी|नकबजनी)")),
    ("Theft", re.compile(r"(चोरी|चोर)")),
    ("Cyber Crime", re.compile(r"(साइबर|ऑनलाइन ठगी|डिजिटल अरेस्ट)")),
    ("Fraud", re.compile(r"(ठगी|धोखाधड़ी|जालसाजी|फर्जीवाड़ा)")),
    ("Drug Offense", re.compile(r"(ड्रग्स|गांजा|स्मैक|हेरोइन|नशीले|अफीम|चरस)")),
    ("Domestic Violence", re.compile(r"(दहेज|घरेलू हिंसा)")),
    ("Assault", re.compile(r"(मारपीट|हमला|चाकू)")),
]
HINDI_NOT_INCIDENT = re.compile(r"(हादसा|दुर्घटना|सड़क|फिल्म|चुनाव|क्रिकेट|नक्सली|आतंक)")

# Indian outlets only (foreign and legal-database sites are dropped)
INDIAN_DOMAINS = {
    "hindustantimes.com", "thehindu.com", "indianexpress.com", "indiatimes.com", "ndtv.com", "news18.com",
    "rediff.com", "deccanherald.com", "tribuneindia.com", "bhaskar.com", "jagran.com", "amarujala.com",
    "livehindustan.com", "madhyamam.com", "manoramaonline.com", "onmanorama.com", "mathrubhumi.com",
    "dinamalar.com", "dailythanthi.com", "anandabazar.com", "lokmat.com", "loksatta.com", "moneycontrol.com",
    "orissapost.com", "telanganatoday.com", "thehansindia.com", "deccanchronicle.com", "newindianexpress.com",
    "outlookindia.com", "firstpost.com", "abplive.com", "republicworld.com", "mid-day.com", "dnaindia.com",
    "business-standard.com", "livemint.com", "thestatesman.com", "telegraphindia.com", "sentinelassam.com",
    "greaterkashmir.com", "dailyexcelsior.com", "siasat.com", "punemirror.com", "patrika.com",
    "prabhatkhabar.com", "freepressjournal.in", "theprint.in", "scroll.in", "thewire.in", "zeenews.com",
    "webindia123.com", "newsonair.gov.in", "ptinews.com", "uniindia.com", "devdiscourse.com", "etvbharat.com",
    "thehitavada.com", "sangbadpratidin.in", "cgkhabar.com", "theweek.in", "india.com", "oneindia.com",
    "asianetnews.com", "latestly.com", "lokmattimes.com", "thenewsminute.com", "kashmirobserver.net",
    "assamtribune.com", "nagalandpost.com", "arunachaltimes.in", "eastmojo.com", "navhindtimes.in",
    "thecommunemag.com", "organiser.org", "opindia.com", "zeebiz.com", "aajtak.in", "naidunia.com",
}
NOT_NEWS = {"indiankanoon.org", "casemine.com", "livelaw.in", "barandbench.com", "verdictum.in"}

# GDELT uses some historic names
PLACE_FIXES = {"Orissa": "Odisha", "Uttaranchal": "Uttarakhand", "Pondicherry": "Puducherry", "Madras": "Chennai",
               "Bombay": "Mumbai", "Calcutta": "Kolkata", "Palghat": "Palakkad", "Trivandrum": "Thiruvananthapuram",
               "Bangalore": "Bengaluru", "Mysore": "Mysuru", "Gurgaon": "Gurugram", "Poona": "Pune"}
TELANGANA_CITIES = {"Hyderabad", "Secunderabad", "Warangal", "Karimnagar", "Nizamabad", "Khammam", "Ranga Reddy",
                    "Medak", "Nalgonda", "Mahbubnagar", "Adilabad", "Siddipet", "Sangareddy"}


def indian_outlet(domain: str) -> bool:
    d = domain.lower().removeprefix("www.")
    if d in NOT_NEWS:
        return False
    return d.endswith(".in") or d in INDIAN_DOMAINS or any(d.endswith("." + k) for k in INDIAN_DOMAINS)
# "X attacks Y" in politics is not an assault
POLITICAL = re.compile(r"\b(bjp|congress|aap|tmc|dmk|minister|mla|mp|cm|govt|government|party|opposition|"
                       r"parliament|lok sabha|rajya sabha|modi|gandhi|centre)\b", re.I)
PRIVATE_CATEGORIES = {"Sexual violence"}  # headline hidden, category only
CHILD = re.compile(r"\b(minor|child|children|girl,? \d{1,2}|boy,? \d{1,2}|pocso|\d{1,2}-year-old)\b", re.I)


@dataclass(frozen=True)
class Incident:
    id: str
    ts: str           # ISO 8601 UTC, when the article was published/crawled
    category: str
    place: str        # "Lucknow, Uttar Pradesh"
    state: str | None
    lat: float
    lon: float
    precision: str    # "city" | "state"
    title: str | None
    source: str       # outlet domain
    url: str
    origin: str       # "news" | "news-translated" | "police"


def _get(url: str, timeout: float = 60) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310  # nosec B310
            return r.read()
    except OSError:
        return None  # missing slot (GDELT skips some) or network hiccup: next run catches up


def file_urls(start: datetime, end: datetime, translated: bool = True) -> list[str]:
    """15-minute GKG file URLs between start and end (UTC)."""
    t = start.replace(minute=start.minute - start.minute % 15, second=0, microsecond=0)
    out = []
    while t <= end:
        stamp = t.strftime("%Y%m%d%H%M%S")
        out.append(f"{BASE}{stamp}.gkg.csv.zip")
        if translated:
            out.append(f"{BASE}{stamp}.translation.gkg.csv.zip")
        t += timedelta(minutes=15)
    return out


def _rows(blob: bytes) -> Iterator[list[str]]:
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for name in z.namelist():
            text = z.read(name).decode("utf-8", errors="replace")
            yield from csv.reader(io.StringIO(text), delimiter="\t", quoting=csv.QUOTE_NONE)


def _india_location(loc2: str, loc1: str) -> tuple[str, str | None, float, float, str] | None:
    """Primary place of the article if it is in India: (name, state, lat, lon, precision).

    Uses V2 locations (with character offsets) so "first mentioned" is meaningful; the
    article must *lead* with an Indian place, which drops foreign stories that merely
    mention India.
    """
    best = None
    if loc2:
        for part in loc2.split(";"):
            f = part.split("#")
            if len(f) < 9:
                continue
            typ, name, cc, _adm1, _adm2, lat, lon, _fid, off = f[:9]
            try:
                item = (int(off or 0), int(typ), name, cc, float(lat), float(lon))
            except ValueError:
                continue
            if best is None or item[0] < best[0]:
                best = item
    elif loc1:
        f = loc1.split(";")[0].split("#")
        if len(f) >= 7:
            try:
                best = (0, int(f[0]), f[1], f[2], float(f[4]), float(f[5]))
            except ValueError:
                best = None
    if not best:
        return None
    _, typ, name, cc, lat, lon = best
    if cc != "IN" or typ == 1:  # type 1 = whole country, too vague to map
        return None
    if not (6 <= lat <= 37.5 and 68 <= lon <= 97.5):
        return None
    parts = [PLACE_FIXES.get(p.strip(), p.strip()) for p in name.split(",")]
    if "(General)" in name or parts[0] in {"Hindustan", "India"}:
        return None
    state = parts[-2] if len(parts) >= 3 else (parts[0] if typ == 5 else None)
    if state == "Andhra Pradesh" and parts[0] in TELANGANA_CITIES:
        state = parts[-2] = "Telangana"
    place = ", ".join(parts[:-1]) if parts[-1] == "India" else ", ".join(parts)
    return place, state, round(lat, 4), round(lon, 4), ("state" if typ == 5 else "city")


_TITLE = re.compile(r"<PAGE_TITLE>(.*?)</PAGE_TITLE>", re.S)


def categorize(title: str | None, themes: set[str], english: bool = True) -> str | None:
    """Crime category for an article, or None if it is not a crime incident report.

    English headlines decide on their own: GDELT's themes alone are too broad there (an IT
    outage is tagged CYBER_ATTACK, a court ruling KILL). For Indian-language articles, Hindi
    headline keywords are used first, then only the most specific crime themes.
    """
    if english:
        if not title or NOT_INCIDENT.search(title):
            return None
        for cat, rx in EXTRA_RULES:
            if rx.search(title):
                return cat
        cat = classify(title)
        if cat == "Assault" and POLITICAL.search(title):
            return None
        return None if cat in NOT_CRIME or cat in {"Other", "Gambling"} else cat
    if title:
        if HINDI_NOT_INCIDENT.search(title) or NOT_INCIDENT.search(title):
            return None
        for cat, rx in HINDI_RULES:
            if rx.search(title):
                return cat
    if themes & POLITICAL_OR_WAR or "TERROR" in themes:
        return None
    for cat, codes in THEME_CATEGORIES:
        if cat in {"Cyber Crime", "Domestic Violence"}:
            continue  # too broad without a headline
        if themes & codes and themes & CRIME_CONTEXT:
            return cat
    if {"KILL", "ARREST", "TAX_FNCACT_POLICE"} <= themes and "SOC_GENERALCRIME" in themes:
        return "Murder"
    return None


def parse_rows(rows: Iterable[list[str]], origin: str = "news") -> Iterator[Incident]:
    for r in rows:
        if len(r) <= C_LOC2:
            continue
        loc = _india_location(r[C_LOC2], r[C_LOC1])
        if not loc:
            continue
        themes = {t.split(",")[0] for t in r[C_THEMES].split(";") if t}
        m = _TITLE.search(r[C_EXTRAS]) if len(r) > C_EXTRAS else None
        title = unescape(m.group(1)).strip() if m else None
        title = re.sub(r"\s+", " ", title)[:200] if title else None
        url = r[C_URL]
        if not url.startswith("http") or not indian_outlet(r[C_SOURCE] or urlparse(url).netloc):
            continue
        cat = categorize(title, themes, english=(origin == "news"))
        if not cat:
            continue
        place, state, lat, lon, precision = loc
        show_title = title if cat not in PRIVATE_CATEGORIES and not (title and CHILD.search(title)
                                                                    and cat in {"Assault", "Kidnapping"}) else None
        try:
            ts = datetime.strptime(r[C_DATE][:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        yield Incident(
            id=hashlib.sha256(url.encode()).hexdigest()[:16],
            ts=ts.isoformat().replace("+00:00", "Z"),
            category=cat,
            place=place,
            state=state,
            lat=lat,
            lon=lon,
            precision=precision,
            title=show_title,
            source=r[C_SOURCE] or urlparse(url).netloc,
            url=url,
            origin=origin,
        )


def dedupe(items: Iterable[Incident]) -> list[Incident]:
    """One row per URL, and one per (headline, place, day) to merge syndicated copies."""
    by_url: dict[str, Incident] = {}
    seen_titles: set[tuple] = set()
    for i in sorted(items, key=lambda x: x.ts):
        if i.url in by_url:
            continue
        key = (re.sub(r"\W+", " ", (i.title or "").lower()).strip(), i.place, i.ts[:10])
        if i.title and key in seen_titles:
            continue
        seen_titles.add(key)
        by_url[i.url] = i
    return list(by_url.values())


def fetch(start: datetime, end: datetime, workers: int = 8, translated: bool = True) -> list[Incident]:
    urls = file_urls(start, end, translated)
    out: list[Incident] = []

    def one(u: str) -> list[Incident]:
        blob = _get(u)
        if not blob:
            return []
        try:
            return list(parse_rows(_rows(blob), "news-translated" if ".translation." in u else "news"))
        except zipfile.BadZipFile:
            return []

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for res in ex.map(one, urls):
            out.extend(res)
    return dedupe(out)


def as_dicts(items: Iterable[Incident]) -> list[dict]:
    return [asdict(i) for i in items]
