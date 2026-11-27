"""CrimeWatch Prevent: place-based risk forecast, scam-wave radar and alerts.

Everything here predicts *places, times and scam types*, never people:

* ``forecast``: expected reports per place for the next 7 days, from an exponentially
  weighted recent rate plus a near-repeat boost (crime clusters for a few days after an
  incident nearby). Each place gets a level and the reasons behind it.
* ``scam_radar``: scam types named in headlines, this week against last week.
* ``evaluate``: checks forecasts made 7+ days ago against what was reported afterwards,
  next to a naive baseline (last 30 days' busiest places). Published as-is, good or bad.
* ``rss``: an RSS feed of current alerts so anyone can follow them in a reader or app.

Inputs are the site's incident dicts (see ``site_data``). News reports measure what is
reported, not all crime, so the forecast is labelled experimental on the site until police
data from a pilot district is added.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

DAY = 86400.0
HALF_LIFE_DAYS = 7.0
NEAR_REPEAT_DAYS = 3.0
TOP_N = 20  # places in the evaluated "top list"

# Scam types, matched on headlines (English + Hindi). Order matters: first match wins.
SCAMS: list[tuple[str, re.Pattern]] = [
    ("Digital arrest", re.compile(r"digital arrest|डिजिटल अरेस्ट|fake (cbi|ed|police|customs) (officer|call)", re.I)),
    ("Investment and trading", re.compile(r"(stock|share|trading|investment|ipo|crypto\w*)\b.{0,40}\b(scam|fraud|duped|cheated)|"  # noqa: E501
                                          r"(scam|fraud|duped|cheated)\b.{0,40}\b(stock|share|trading|investment|ipo|crypto\w*)|"
                                          r"निवेश|ट्रेडिंग", re.I)),
    ("Job and task", re.compile(r"(job|task|part[- ]time|work from home|like[- ]and[- ]earn|recruit\w*).{0,40}(scam|fraud|duped|cheat)|"  # noqa: E501
                                r"(scam|fraud|duped|cheat).{0,40}(job|task|part[- ]time|work from home)|नौकरी के नाम", re.I)),  # noqa: E501
    ("Cyber slavery abroad", re.compile(r"cyber slave\w*|(myanmar|cambodia|laos).{0,40}(job|scam|trafficked|rescued)", re.I)),  # noqa: E501
    ("Sextortion", re.compile(r"sextortion|nude video call|सेक्सटॉर्शन|अश्लील वीडियो", re.I)),
    ("Loan app", re.compile(r"loan app|instant loan|लोन ऐप", re.I)),
    ("Bank, KYC and OTP", re.compile(r"\bkyc\b|\botp\b|\bupi\b|bank account (frozen|blocked)|credit card|debit card|"
                                     r"sim swap|ओटीपी|केवाईसी", re.I)),
    ("Courier and parcel", re.compile(r"(courier|parcel|fedex|customs).{0,30}(scam|fraud|call)", re.I)),
    ("Matrimonial and romance", re.compile(r"matrimon\w*|romance scam|dating app|honey ?trap|शादी के नाम", re.I)),
    ("Lottery and prize", re.compile(r"lottery|prize|lucky draw|kbc|लॉटरी", re.I)),
    ("Fake government scheme", re.compile(r"(scheme|yojana|subsidy|pm[- ]kisan).{0,30}(fraud|scam|fake)|फर्जी योजना", re.I)),  # noqa: E501
]
SCAM_CATEGORIES = {"Cyber Crime", "Fraud"}
SCAM_WORDS = re.compile(r"scam|fraud|duped|cheat|swindl|con(ned)? |ठगी|धोखाधड़ी|ठग", re.I)


def _ts(i: dict) -> float:
    return datetime.fromisoformat(i["ts"].replace("Z", "+00:00")).timestamp()


def _key(i: dict) -> tuple[float, float]:
    return (round(i["lat"], 2), round(i["lon"], 2))


def scam_type(title: str | None) -> str | None:
    if not title:
        return None
    for name, rx in SCAMS:
        if rx.search(title):
            return name
    return None


def forecast(incidents: list[dict], now: datetime) -> list[dict]:
    """Expected reports per place in the next 7 days, with level and reasons."""
    t_now = now.timestamp()
    places: dict[tuple, dict] = {}
    for i in incidents:
        if i.get("precision") == "state":
            continue  # a state centre is not a place anyone can act on
        age = (t_now - _ts(i)) / DAY
        if age < 0 or age > 30:
            continue
        p = places.setdefault(_key(i), {"name": i["place"], "state": i.get("state"), "lat": i["lat"], "lon": i["lon"],
                                        "w": 0.0, "d7": 0, "d30": 0, "d3": 0, "cats": Counter()})
        p["w"] += math.exp(-age * math.log(2) / HALF_LIFE_DAYS)
        p["d30"] += 1
        p["d7"] += age <= 7
        p["d3"] += age <= NEAR_REPEAT_DAYS
        p["cats"][i["category"]] += 1
    if not places:
        return []
    # Sum of decay weights over the days of history we actually have, so that a steady rate of
    # 1 report a day gives a weighted sum equal to `norm`. Dividing by it turns the sum into a daily rate.
    span = max(1, min(30, math.ceil((t_now - min(_ts(i) for i in incidents)) / DAY)))
    norm = sum(math.exp(-(d + 0.5) * math.log(2) / HALF_LIFE_DAYS) for d in range(span))
    out = []
    for p in places.values():
        rate = p["w"] / norm
        # Near-repeat: more reports in the last 3 days than the rate predicts lifts the forecast, capped at 1.5x.
        excess = p["d3"] - NEAR_REPEAT_DAYS * rate
        boost = min(1.5, 1 + 0.1 * max(0.0, excess))
        exp7 = round(7 * rate * boost, 1)
        top_cat, top_n = p["cats"].most_common(1)[0]
        reasons = [f"{p['d7']} report{'s' * (p['d7'] != 1)} in the last 7 days"]
        if boost > 1.05:
            reasons.append(f"{p['d3']} in the last 3 days (crime often repeats nearby within days)")
        if top_n >= 2:
            reasons.append(f"mostly {top_cat.lower()} ({top_n} of {p['d30']})")
        out.append({"name": p["name"], "state": p["state"], "lat": p["lat"], "lon": p["lon"], "expected_7d": exp7,
                    "reports_7d": p["d7"], "reports_30d": p["d30"], "top_category": top_cat,
                    "categories": p["cats"].most_common(5), "reasons": reasons})
    out.sort(key=lambda r: -r["expected_7d"])
    n = len(out)
    for rank, r in enumerate(out):
        r["level"] = "high" if rank < max(1, n // 20) and r["expected_7d"] >= 3 else \
            "elevated" if rank < max(1, n // 5) and r["expected_7d"] >= 1 else "normal"
    return out


def scam_radar(incidents: list[dict], now: datetime) -> list[dict]:
    t_now = now.timestamp()
    this, last = Counter(), Counter()
    examples: dict[str, list] = defaultdict(list)
    for i in sorted(incidents, key=lambda x: x["ts"], reverse=True):
        title = i.get("title") or ""
        if i["category"] not in SCAM_CATEGORIES and not SCAM_WORDS.search(title):
            continue  # e.g. "matrimonial dispute turns fatal" is a murder, not a scam
        kind = scam_type(title)
        if not kind:
            continue
        age = (t_now - _ts(i)) / DAY
        if age <= 7:
            this[kind] += 1
            if len(examples[kind]) < 3:
                examples[kind].append({"title": i["title"], "url": i["url"], "place": i["place"], "ts": i["ts"]})
        elif age <= 14:
            last[kind] += 1
    rows = [{"type": k, "this_week": this[k], "last_week": last[k],
             "trend": "new" if this[k] and not last[k] else "up" if this[k] > last[k] else
             "down" if this[k] < last[k] else "steady", "examples": examples[k]}
            for k in set(this) | set(last)]
    return sorted(rows, key=lambda r: (-r["this_week"], r["type"]))


def snapshot(fc: list[dict], now: datetime) -> dict:
    """What gets stored to be checked a week later: the top places by forecast and by the naive baseline."""
    by_base = sorted(fc, key=lambda r: -r["reports_30d"])
    return {"made_at": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
            "model": [[r["lat"], r["lon"]] for r in fc[:TOP_N]],
            "baseline": [[r["lat"], r["lon"]] for r in by_base[:TOP_N]]}


def evaluate(history: list[dict], incidents: list[dict], now: datetime) -> dict:
    """Share of reports in the 7 days after each stored forecast that fell in its top places."""
    done = []
    for h in history:
        t0 = datetime.fromisoformat(h["made_at"].replace("Z", "+00:00")).timestamp()
        if now.timestamp() - t0 < 7 * DAY:
            continue
        after = [i for i in incidents if i.get("precision") != "state" and t0 < _ts(i) <= t0 + 7 * DAY]
        if not after:
            continue
        model = {tuple(x) for x in h["model"]}
        base = {tuple(x) for x in h["baseline"]}
        done.append({"made_at": h["made_at"], "reports": len(after),
                     "model_hit": round(sum(_key(i) in model for i in after) / len(after), 3),
                     "baseline_hit": round(sum(_key(i) in base for i in after) / len(after), 3)})
    if not done:
        first = min((h["made_at"] for h in history), default=None)
        return {"status": "building", "checks": [], "first_forecast": first,
                "note": "The first accuracy check runs 7 days after the first stored forecast."}
    m = sum(d["model_hit"] for d in done) / len(done)
    b = sum(d["baseline_hit"] for d in done) / len(done)
    return {"status": "ok", "checks": done[-30:], "model_hit": round(m, 3), "baseline_hit": round(b, 3),
            "beats_baseline": m > b}


def keep_history(history: list[dict], snap: dict, days: int = 45) -> list[dict]:
    """One stored forecast per day (the first of each day), last `days` days."""
    day = snap["made_at"][:10]
    hist = [h for h in history if h.get("made_at")]
    if not any(h["made_at"][:10] == day for h in hist):
        hist.append(snap)
    cutoff = (datetime.fromisoformat(snap["made_at"].replace("Z", "+00:00")) - timedelta(days=days)).isoformat()[:10]
    return [h for h in hist if h["made_at"][:10] >= cutoff]


def rss(fc: list[dict], scams: list[dict], spikes: list[dict], now: datetime, site: str) -> str:
    items = []
    for s in scams:
        if s["trend"] in {"new", "up"} and s["this_week"] >= 2:
            items.append((f"Scam alert: {s['type']} reports rising ({s['this_week']} this week)",
                          f"{s['type']} scams were reported {s['this_week']} times in the last 7 days "
                          f"(last week {s['last_week']}). If you are targeted, call 1930 or report at cybercrime.gov.in.",  # noqa: E501
                          f"{site}#/prevent"))
    for sp in spikes:
        items.append((f"Unusual activity: {sp['state']} ({sp['recent']} reports in 24 hours)",
                      f"{sp['state']} had {sp['recent']} reports in the last 24 hours against a daily average of "
                      f"{sp['base']:.1f}. More reports can mean more coverage, not more crime.",
                      f"{site}#/prevent"))
    for r in fc:
        if r["level"] == "high":
            items.append((f"High risk this week: {r['name']}",
                          f"Expected about {r['expected_7d']:.0f} reports in the next 7 days. " + "; ".join(r["reasons"]) + ".",  # noqa: E501
                          f"{site}#/map?q={r['name'].split(',')[0]}"))
    pub = format_datetime(now)
    body = "".join(
        f"<item><title>{escape(t)}</title><description>{escape(d)}</description><link>{escape(u)}</link>"
        f"<guid isPermaLink=\"false\">{escape(t)}-{now:%Y-%m-%d}</guid><pubDate>{pub}</pubDate></item>"
        for t, d, u in items)
    return ('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
            f"<title>CrimeWatch India alerts</title><link>{escape(site)}</link>"
            "<description>Scam waves, unusual spikes and high-risk places from CrimeWatch India.</description>"
            f"<lastBuildDate>{pub}</lastBuildDate>{body}</channel></rss>")


def state_spikes(incidents: list[dict], now: datetime) -> list[dict]:
    """States with far more reports in the last 24 h than their recent daily average (one-sided Poisson)."""
    t_now = now.timestamp()
    first = min((_ts(i) for i in incidents), default=t_now)
    hist_days = min(7, int((t_now - DAY - first) // DAY))
    if hist_days < 1:
        return []
    recent, before = Counter(), Counter()
    for i in incidents:
        if not i.get("state"):
            continue
        age = (t_now - _ts(i)) / DAY
        if age < 1:
            recent[i["state"]] += 1
        elif age < 1 + hist_days:
            before[i["state"]] += 1
    out = []
    for s, k in recent.items():
        lam = max(before[s] / hist_days, 0.5)
        term, cdf = math.exp(-lam), 0.0
        for n in range(k):
            cdf += term
            term *= lam / (n + 1)
        p = max(0.0, 1 - cdf)
        if k >= 3 and p < 0.05:
            out.append({"state": s, "recent": k, "base": round(before[s] / hist_days, 2), "p": round(p, 4)})
    return sorted(out, key=lambda r: r["p"])


def build(incidents: list[dict], history: list[dict], now: datetime, site: str) -> tuple[dict, list[dict], str]:
    fc = forecast(incidents, now)
    scams = scam_radar(incidents, now)
    spikes = state_spikes(incidents, now)
    hist = keep_history(history, snapshot(fc, now))
    t_now = now.timestamp()
    out = {
        "generated_at": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "forecast": fc[:150],
        "scams": scams,
        "spikes": spikes,
        "accuracy": evaluate(hist, incidents, now),
        "method": {"history_days": round((t_now - min((_ts(i) for i in incidents), default=t_now)) / DAY, 1),
                   "half_life_days": HALF_LIFE_DAYS, "near_repeat_days": NEAR_REPEAT_DAYS, "top_n": TOP_N},
    }
    return out, hist, rss(fc, scams, spikes, now, site)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
