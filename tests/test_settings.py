import pytest

from src.crimewatch.settings import Settings, SettingsError


def test_defaults_are_development():
    s = Settings.from_env({})
    assert s.app_env == "development" and s.auth_mode == "local"
    assert s.data_source == "file" and s.allow_live_pulse
    assert s.session_timeout_min == 30


def test_production_refuses_no_auth():
    with pytest.raises(SettingsError):
        Settings.from_env({"CW_APP_ENV": "production", "CW_AUTH_MODE": "none"})


def test_production_disables_live_pulse_by_default():
    s = Settings.from_env({"CW_APP_ENV": "production", "CW_AUTH_MODE": "oidc"})
    assert s.is_production and not s.allow_live_pulse


@pytest.mark.parametrize(
    "env",
    [
        {"CW_APP_ENV": "staging"},
        {"CW_AUTH_MODE": "basic"},
        {"CW_DATA_SOURCE": "s3"},
        {"CW_DEV_ROLE": "superuser"},
        {"CW_SESSION_TIMEOUT_MIN": "0"},
        {"CW_ALLOW_LIVE_PULSE": "maybe"},
    ],
)
def test_invalid_values_rejected(env):
    with pytest.raises(SettingsError):
        Settings.from_env(env)


def test_relative_paths_resolve_to_project_root():
    s = Settings.from_env({"CW_AUDIT_LOG_PATH": "logs/x.jsonl"})
    assert s.audit_log_path.is_absolute() and s.audit_log_path.name == "x.jsonl"
