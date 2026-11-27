from datetime import datetime, timedelta, timezone

from src.crimewatch import prevent as pv

NOW = datetime(2026, 11, 27, 6, 0, tzinfo=timezone.utc)


def inc(days_ago, place="Pune, Maharashtra", lat=18.52, lon=73.86, cat="Robbery", title="Man robbed", state="Maharashtra",  # noqa: E501
        precision="city"):
    ts = (NOW - timedelta(days=days_ago)).isoformat().replace("+00:00", "Z")
    return {"id": f"{place}{days_ago}{cat}{title}", "ts": ts, "category": cat, "place": place, "state": state,
            "lat": lat, "lon": lon, "precision": precision, "title": title, "url": "https://ex.in/x", "origin": "news"}


def test_forecast_ranks_recent_clusters_and_explains():
    data = [inc(d) for d in (0.2, 0.5, 1, 2, 2.5, 6)] + [inc(20, "Nagpur, Maharashtra", 21.15, 79.09)] + \
           [inc(1, "Maharashtra", 19.0, 76.0, precision="state")]
    fc = pv.forecast(data, NOW)
    assert [r["name"] for r in fc] == ["Pune, Maharashtra", "Nagpur, Maharashtra"]  # state centre left out
    top = fc[0]
    assert top["level"] == "high" and top["expected_7d"] > fc[1]["expected_7d"]
    assert any("last 3 days" in r for r in top["reasons"]) and top["top_category"] == "Robbery"


def test_scam_types_and_trend():
    assert pv.scam_type("Retired officer loses Rs 80 lakh in digital arrest scam") == "Digital arrest"
    assert pv.scam_type("Techie duped of Rs 25 lakh in stock trading fraud") == "Investment and trading"
    assert pv.scam_type("Man held for murder") is None
    data = [inc(1, cat="Cyber Crime", title="Woman duped in digital arrest scam"),
            inc(2, cat="Cyber Crime", title="Digital arrest: senior citizen loses Rs 1 crore"),
            inc(10, cat="Fraud", title="Lottery fraud gang busted")]
    radar = {r["type"]: r for r in pv.scam_radar(data, NOW)}
    assert radar["Digital arrest"]["this_week"] == 2 and radar["Digital arrest"]["trend"] == "new"
    assert radar["Lottery and prize"]["trend"] == "down" and len(radar["Digital arrest"]["examples"]) == 2


def test_accuracy_check_needs_a_week_and_compares_with_baseline():
    old = NOW - timedelta(days=8)
    hist = [{"made_at": old.isoformat().replace("+00:00", "Z"), "model": [[18.52, 73.86]], "baseline": [[21.15, 79.09]]}]  # noqa: E501
    data = [inc(d) for d in (1, 2, 3)] + [inc(4, "Nagpur, Maharashtra", 21.15, 79.09)]
    ev = pv.evaluate(hist, data, NOW)
    assert ev["status"] == "ok" and ev["model_hit"] == 0.75 and ev["baseline_hit"] == 0.25 and ev["beats_baseline"]
    assert pv.evaluate([], data, NOW)["status"] == "building"


def test_history_one_per_day_and_rss():
    snap = pv.snapshot(pv.forecast([inc(1)], NOW), NOW)
    h = pv.keep_history([], snap)
    assert len(pv.keep_history(h, snap)) == 1
    out, hist, feed = pv.build([inc(d, cat="Cyber Crime", title="Digital arrest scam") for d in (0.5, 1, 2)] + [inc(0.3)],  # noqa: E501
                               [], NOW, "https://example.org/")
    assert out["forecast"] and hist and feed.startswith("<?xml") and "Digital arrest" in feed and "1930" in feed
    assert "<script" not in feed


def test_state_spike():
    data = [inc(0.1 * k) for k in range(8)] + [inc(1.5), inc(2.5), inc(3.5)]
    sp = pv.state_spikes(data, NOW)
    assert sp and sp[0]["state"] == "Maharashtra" and sp[0]["recent"] == 8


def test_forecast_magnitude_is_a_plausible_weekly_count():
    # one report a day for 30 days at one place: next week should be about 7, not inflated
    data = [inc(d + 0.5) for d in range(30)]
    exp7 = pv.forecast(data, NOW)[0]["expected_7d"]
    assert 5 <= exp7 <= 10.5
    # short history (8 days, 52 reports) stays near the observed weekly pace
    burst = [inc(d * 8 / 52) for d in range(52)]
    assert pv.forecast(burst, NOW)[0]["expected_7d"] < 52 * 1.5


def test_scam_radar_ignores_non_scam_categories():
    data = [inc(1, cat="Murder", title="Matrimonial dispute turns fatal"),
            inc(1, cat="Fraud", title="Matrimonial site fraud: man cheated of Rs 5 lakh")]
    radar = pv.scam_radar(data, NOW)
    assert [r["this_week"] for r in radar] == [1]
