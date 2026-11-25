"""End-to-end smoke tests that run the real Streamlit script headlessly."""

import json
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from src.crimewatch.auth import hash_password

APP = str(Path(__file__).resolve().parents[1] / "app" / "dashboard.py")
PW = "a-strong-test-password"

pytestmark = pytest.mark.slow


@pytest.fixture(autouse=True)
def _isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("CW_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    users = tmp_path / "users.json"
    users.write_text(
        json.dumps(
            {
                "users": [
                    {"username": "viewer.goa", "role": "viewer", "states": ["Goa"], "password_hash": hash_password(PW)},
                    {"username": "admin", "role": "admin", "states": ["*"], "password_hash": hash_password(PW)},
                ]
            }
        )
    )
    monkeypatch.setenv("CW_USERS_FILE", str(users))
    st.cache_resource.clear()
    yield tmp_path
    st.cache_resource.clear()


def _audit(tmp_path):
    p = tmp_path / "audit.jsonl"
    return [json.loads(line) for line in p.read_text().splitlines()] if p.exists() else []


def test_login_required(monkeypatch, _isolated):
    monkeypatch.setenv("CW_AUTH_MODE", "local")
    at = AppTest.from_file(APP, default_timeout=300).run()
    assert not at.exception
    assert any("Sign in" in m.value for m in at.markdown)
    assert len(at.tabs) == 0  # dashboard never rendered

    at.text_input[0].input("admin")
    at.text_input[1].input("wrong-password-123")
    at.button[0].click().run()
    assert any("Invalid username or password" in e.value for e in at.error)
    assert _audit(_isolated)[-1]["outcome"] == "failure"


def test_viewer_sees_only_jurisdiction_and_cannot_export(monkeypatch, _isolated):
    monkeypatch.setenv("CW_AUTH_MODE", "local")
    at = AppTest.from_file(APP, default_timeout=300).run()
    at.text_input[0].input("viewer.goa")
    at.text_input[1].input(PW)
    at.button[0].click().run()
    assert not at.exception, at.exception
    assert len(at.tabs) == 15
    state_box = at.selectbox(key="state_selector")
    assert state_box.options == ["ALL STATES", "Goa"]
    infos = " ".join(i.value for i in at.info)
    assert "Data export is available to analysts" in infos
    assert "Model governance is available" in infos
    assert not any("Live Pulse" in t.label for t in at.toggle)
    events = [r["event"] for r in _audit(_isolated)]
    assert "login" in events and "Dashboard Viewed" in events
    assert all(r["user"] == "viewer.goa" for r in _audit(_isolated) if r["event"] == "Dashboard Viewed")


def test_dev_mode_admin_renders_full_dashboard(monkeypatch, _isolated):
    monkeypatch.setenv("CW_AUTH_MODE", "none")
    at = AppTest.from_file(APP, default_timeout=300).run()
    assert not at.exception, at.exception
    assert len(at.tabs) == 15
    assert any("SIMULATED DATA" in w.value for w in at.warning)
    assert any("Override Guard" in t.label for t in at.toggle)


def _write_dataset(path):
    import pandas as pd

    rows = []
    for year in range(2018, 2023):
        for state, district in [("Goa", "North Goa"), ("Goa", "South Goa"), ("Kerala", "Ernakulam")]:
            for cat, n in [("Theft", 300), ("Assault", 120), ("Cyber Crime", 80)]:
                rows.append(
                    {"year": year, "state_name": state, "district_name": district, "category": cat,
                     "crime_type": "Other Crime", "crime_count": n + 10 * (year - 2018), "arrests": n // 3}
                )
    pd.DataFrame(rows).to_csv(path, index=False)


def test_file_data_source_loads_validated_dataset(monkeypatch, _isolated):
    data = _isolated / "dataset.csv"
    _write_dataset(data)
    monkeypatch.setenv("CW_AUTH_MODE", "none")
    monkeypatch.setenv("CW_DATA_SOURCE", "file")
    monkeypatch.setenv("CW_DATA_PATH", str(data))
    at = AppTest.from_file(APP, default_timeout=300).run()
    assert not at.exception, at.exception
    assert not any("SIMULATED DATA" in w.value for w in at.warning)
    assert any("dataset.csv" in c.value for c in at.caption)


def test_file_data_source_rejects_invalid_dataset(monkeypatch, _isolated):
    data = _isolated / "bad.csv"
    data.write_text("year,state_name\n2020,Goa\n")
    monkeypatch.setenv("CW_AUTH_MODE", "none")
    monkeypatch.setenv("CW_DATA_SOURCE", "file")
    monkeypatch.setenv("CW_DATA_PATH", str(data))
    at = AppTest.from_file(APP, default_timeout=300).run()
    assert any("failed validation" in e.value for e in at.error)
    assert len(at.tabs) == 0
