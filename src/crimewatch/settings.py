"""Runtime settings loaded from environment variables.

All deployment-specific behaviour is controlled here so the same container image can
run as a developer demo or as a locked-down production service.

Environment variables (all prefixed ``CW_``):

=====================  ==============================  =======================================
Variable               Values                          Default
=====================  ==============================  =======================================
CW_APP_ENV             development | production        development
CW_AUTH_MODE           oidc | local | none             local (none is refused in production)
CW_USERS_FILE          path to users JSON              config/users.json
CW_DEV_ROLE            role used when AUTH_MODE=none   admin
CW_DATA_SOURCE         synthetic | file                file (NCRB-derived parquet)
CW_DATA_PATH           CSV or Parquet path             data/processed/dashboard_dataset.parquet
CW_AUDIT_LOG_PATH      path for JSON-lines audit log   logs/audit.jsonl
CW_ALLOW_LIVE_PULSE    true | false                    true in development, false in production
CW_SESSION_TIMEOUT_MIN idle minutes before logout      30
CW_MAX_LOGIN_ATTEMPTS  failed logins before lockout    5
CW_LIVE_DB             SQLite file for live feed       data/live/live.db
CW_API_KEYS_FILE       API keys for data partners      config/api_keys.json
=====================  ==============================  =======================================
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

VALID_ENVS = {"development", "production"}
VALID_AUTH_MODES = {"oidc", "local", "none"}
VALID_DATA_SOURCES = {"synthetic", "file"}


class SettingsError(ValueError):
    """Raised when the environment describes an unsafe or invalid configuration."""


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None or value.strip() == "":
        return default
    v = value.strip().lower()
    if v in {"1", "true", "yes", "on"}:
        return True
    if v in {"0", "false", "no", "off"}:
        return False
    raise SettingsError(f"Expected a boolean value, got {value!r}")


def _as_int(value: str | None, default: int, name: str, minimum: int = 1) -> int:
    if value is None or value.strip() == "":
        return default
    try:
        n = int(value)
    except ValueError as exc:
        raise SettingsError(f"{name} must be an integer, got {value!r}") from exc
    if n < minimum:
        raise SettingsError(f"{name} must be >= {minimum}, got {n}")
    return n


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else PROJECT_ROOT / p


@dataclass(frozen=True)
class Settings:
    app_env: str
    auth_mode: str
    users_file: Path
    dev_role: str
    data_source: str
    data_path: Path
    audit_log_path: Path
    allow_live_pulse: bool
    session_timeout_min: int
    max_login_attempts: int
    live_db_path: Path = PROJECT_ROOT / "data/live/live.db"
    api_keys_file: Path = PROJECT_ROOT / "config/api_keys.json"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_synthetic(self) -> bool:
        return self.data_source == "synthetic"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        env = os.environ if env is None else env

        app_env = env.get("CW_APP_ENV", "development").strip().lower()
        if app_env not in VALID_ENVS:
            raise SettingsError(f"CW_APP_ENV must be one of {sorted(VALID_ENVS)}, got {app_env!r}")
        production = app_env == "production"

        auth_mode = env.get("CW_AUTH_MODE", "local").strip().lower()
        if auth_mode not in VALID_AUTH_MODES:
            raise SettingsError(f"CW_AUTH_MODE must be one of {sorted(VALID_AUTH_MODES)}, got {auth_mode!r}")
        if production and auth_mode == "none":
            raise SettingsError("CW_AUTH_MODE=none is not allowed when CW_APP_ENV=production")

        data_source = env.get("CW_DATA_SOURCE", "file").strip().lower()
        if data_source not in VALID_DATA_SOURCES:
            raise SettingsError(f"CW_DATA_SOURCE must be one of {sorted(VALID_DATA_SOURCES)}, got {data_source!r}")

        # Imported lazily to avoid a cycle (auth imports nothing from settings).
        from .auth import Role

        dev_role = env.get("CW_DEV_ROLE", "admin").strip().lower()
        if dev_role not in Role.values():
            raise SettingsError(f"CW_DEV_ROLE must be one of {Role.values()}, got {dev_role!r}")

        return cls(
            app_env=app_env,
            auth_mode=auth_mode,
            users_file=_resolve(env.get("CW_USERS_FILE", "config/users.json")),
            dev_role=dev_role,
            data_source=data_source,
            data_path=_resolve(env.get("CW_DATA_PATH", "data/processed/dashboard_dataset.parquet")),
            audit_log_path=_resolve(env.get("CW_AUDIT_LOG_PATH", "logs/audit.jsonl")),
            allow_live_pulse=_as_bool(env.get("CW_ALLOW_LIVE_PULSE"), default=not production),
            session_timeout_min=_as_int(env.get("CW_SESSION_TIMEOUT_MIN"), 30, "CW_SESSION_TIMEOUT_MIN"),
            max_login_attempts=_as_int(env.get("CW_MAX_LOGIN_ATTEMPTS"), 5, "CW_MAX_LOGIN_ATTEMPTS"),
            live_db_path=_resolve(env.get("CW_LIVE_DB", "data/live/live.db")),
            api_keys_file=_resolve(env.get("CW_API_KEYS_FILE", "config/api_keys.json")),
        )
