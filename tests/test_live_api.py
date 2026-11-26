import json
from datetime import date, timedelta

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.crimewatch.api import create_app, hash_key
from src.crimewatch.live_store import LiveStore, to_dashboard_rows
from src.crimewatch.settings import Settings

INGEST, READ, GOA_ONLY = "cw_ingest_key", "cw_read_key", "cw_goa_key"


@pytest.fixture
def client(tmp_path):
    keys = tmp_path / "api_keys.json"
    keys.write_text(json.dumps({"keys": [
        {"id": "partner", "key_hash": hash_key(INGEST), "scopes": ["ingest"], "states": ["*"]},
        {"id": "reader", "key_hash": hash_key(READ), "scopes": ["read"], "states": ["*"]},
        {"id": "goa-police", "key_hash": hash_key(GOA_ONLY), "scopes": ["ingest", "read"], "states": ["Goa"]},
    ]}))
    s = Settings.from_env({
        "CW_LIVE_DB": str(tmp_path / "live.db"),
        "CW_API_KEYS_FILE": str(keys),
        "CW_AUDIT_LOG_PATH": str(tmp_path / "audit.jsonl"),
    })
    c = TestClient(create_app(s))
    c.tmp = tmp_path
    return c


def _rec(**kw):
    base = {"day": (date.today() - timedelta(days=1)).isoformat(), "state_name": "Goa",
            "district_name": "North Goa", "category": "Theft", "crime_count": 4}
    base.update(kw)
    return base


def _auth(k):
    return {"Authorization": f"Bearer {k}"}


def test_health_is_public(client):
    r = client.get("/v1/health")
    assert r.status_code == 200 and r.headers["X-Frame-Options"] == "DENY"


def test_ingest_requires_valid_key_and_scope(client):
    assert client.post("/v1/ingest/daily", json={"records": [_rec()]}).status_code == 401
    assert client.post("/v1/ingest/daily", json={"records": [_rec()]}, headers=_auth("nope")).status_code == 401
    assert client.post("/v1/ingest/daily", json={"records": [_rec()]}, headers=_auth(READ)).status_code == 403


def test_ingest_upserts_and_is_audited(client):
    r = client.post("/v1/ingest/daily", json={"records": [_rec(), _rec(category="Murder", crime_count=1)]},
                    headers=_auth(INGEST))
    assert r.status_code == 200 and r.json() == {"accepted": 2, "source": "partner"}
    # resending a corrected day replaces, not duplicates
    client.post("/v1/ingest/daily", json={"records": [_rec(crime_count=6)]}, headers=_auth(INGEST))
    status = client.get("/v1/live/status", headers=_auth(READ)).json()
    assert status["records"] == 2
    events = [json.loads(line)["event"] for line in (client.tmp / "audit.jsonl").read_text().splitlines()]
    assert events.count("live_ingest") == 2


def test_state_bound_key_cannot_write_other_states(client):
    r = client.post("/v1/ingest/daily", json={"records": [_rec(state_name="Kerala")]}, headers=_auth(GOA_ONLY))
    assert r.status_code == 403
    assert client.post("/v1/ingest/daily", json={"records": [_rec()]}, headers=_auth(GOA_ONLY)).status_code == 200


@pytest.mark.parametrize("bad", [
    {"category": "Jaywalking"},
    {"crime_count": -1},
    {"day": (date.today() + timedelta(days=1)).isoformat()},
    {"day": "2001-01-01"},
    {"district_name": "<script>"},
])
def test_invalid_records_rejected(client, bad):
    r = client.post("/v1/ingest/daily", json={"records": [_rec(**bad)]}, headers=_auth(INGEST))
    assert r.status_code == 422


def test_summary_reads_official_data_scoped_by_key(client):
    r = client.get("/v1/summary", params={"year": 2022}, headers=_auth(GOA_ONLY))
    assert r.status_code == 200
    rows = r.json()["rows"]
    assert rows and {row["state_name"] for row in rows} == {"Goa"}
    assert client.get("/v1/summary", params={"state": "Kerala"}, headers=_auth(GOA_ONLY)).status_code == 403


def test_live_rows_never_overlap_official_years(tmp_path):
    from src.crimewatch.live_store import DailyCount

    store = LiveStore(tmp_path / "l.db")
    store.upsert([DailyCount(date(2022, 5, 1), "Goa", "North Goa", "Theft", 5),
                  DailyCount(date(2026, 5, 1), "Goa", "North Goa", "Theft", 7),
                  DailyCount(date(2026, 5, 2), "Goa", "North Goa", "Theft", 1)], source="p")
    rows = to_dashboard_rows(store.frame(), after_year=2022)
    assert rows.to_dict("records") == [{"year": 2026, "state_name": "Goa", "district_name": "North Goa",
                                        "category": "Theft", "crime_type": "Property Crime",
                                        "crime_count": 8, "arrests": 0}]
    assert to_dashboard_rows(pd.DataFrame(), 2022).empty
