"""Authentication and role-based access control (framework independent).

Roles follow the least-privilege principle:

* ``viewer``      - read dashboards for their jurisdiction.
* ``analyst``     - viewer + export filtered data and download reports.
* ``supervisor``  - analyst + run simulations (Live Pulse) and see model governance.
* ``admin``       - everything, including bulk-export override and user administration.

Passwords are stored as salted ``scrypt`` hashes (Python standard library, no extra
dependency). The users file is JSON::

    {
      "users": [
        {"username": "sp.hyderabad", "display_name": "SP Hyderabad",
         "role": "supervisor", "states": ["Telangana"], "email": "sp@example.gov.in",
         "password_hash": "scrypt$16384$8$1$<salt-hex>$<hash-hex>"}
      ]
    }

``states`` omitted or ``["*"]`` means all-India access. For OIDC logins the same file
maps an e-mail address to a role and jurisdiction; unknown OIDC users get ``viewer``
with *no* states, i.e. no data until an admin assigns them.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import threading
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Role(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"

    @classmethod
    def values(cls) -> list[str]:
        return [r.value for r in cls]


class Permission(str, Enum):
    VIEW_DASHBOARD = "view_dashboard"
    EXPORT_DATA = "export_data"
    DOWNLOAD_REPORTS = "download_reports"
    RUN_SIMULATION = "run_simulation"
    VIEW_MODEL_GOVERNANCE = "view_model_governance"
    EXPORT_OVERRIDE = "export_override"
    MANAGE_USERS = "manage_users"


_VIEWER = frozenset({Permission.VIEW_DASHBOARD})
_ANALYST = _VIEWER | {Permission.EXPORT_DATA, Permission.DOWNLOAD_REPORTS}
_SUPERVISOR = _ANALYST | {Permission.RUN_SIMULATION, Permission.VIEW_MODEL_GOVERNANCE}
_ADMIN = frozenset(Permission)

ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.VIEWER: _VIEWER,
    Role.ANALYST: frozenset(_ANALYST),
    Role.SUPERVISOR: frozenset(_SUPERVISOR),
    Role.ADMIN: _ADMIN,
}

ALL_STATES = "*"


@dataclass(frozen=True)
class User:
    username: str
    role: Role
    display_name: str = ""
    email: str = ""
    # None = all states; empty tuple = no data access.
    states: tuple[str, ...] | None = None
    auth_method: str = "local"

    def can(self, permission: Permission) -> bool:
        return permission in ROLE_PERMISSIONS[self.role]

    def can_see_state(self, state: str) -> bool:
        return self.states is None or state in self.states

    @property
    def label(self) -> str:
        return self.display_name or self.username


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS[role]


# ----------------------------------------------------------------------------
# Password hashing (scrypt, RFC 7914)
# ----------------------------------------------------------------------------
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
MIN_PASSWORD_LENGTH = 12


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=32)
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_hex, hash_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(hash_hex) // 2,
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), hash_hex)


# Used to spend equal time on unknown usernames (prevents user enumeration by timing).
_DUMMY_HASH = hash_password("dummy-password-not-used", salt=b"\x00" * 16)


# ----------------------------------------------------------------------------
# User store
# ----------------------------------------------------------------------------
def _parse_states(raw: object) -> tuple[str, ...] | None:
    if raw is None:
        return None
    if not isinstance(raw, list) or not all(isinstance(s, str) for s in raw):
        raise ValueError("'states' must be a list of state names")
    if ALL_STATES in raw:
        return None
    return tuple(raw)


@dataclass
class _Record:
    user: User
    password_hash: str = ""


@dataclass
class UserStore:
    records: dict[str, _Record] = field(default_factory=dict)
    by_email: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: Path) -> UserStore:
        if not path.exists():
            return cls()
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))

    @classmethod
    def from_dict(cls, data: dict) -> UserStore:
        store = cls()
        for entry in data.get("users", []):
            username = str(entry["username"]).strip().lower()
            if not username:
                raise ValueError("username must not be empty")
            if username in store.records:
                raise ValueError(f"duplicate username {username!r}")
            role = Role(str(entry.get("role", "viewer")).lower())
            user = User(
                username=username,
                role=role,
                display_name=str(entry.get("display_name", "")),
                email=str(entry.get("email", "")).strip().lower(),
                states=_parse_states(entry.get("states")),
            )
            store.records[username] = _Record(user=user, password_hash=str(entry.get("password_hash", "")))
            if user.email:
                store.by_email[user.email] = username
        return store

    def __len__(self) -> int:
        return len(self.records)

    def authenticate(self, username: str, password: str) -> User | None:
        rec = self.records.get(username.strip().lower())
        if rec is None or not rec.password_hash:
            verify_password(password, _DUMMY_HASH)
            return None
        return rec.user if verify_password(password, rec.password_hash) else None

    def resolve_oidc(self, email: str, name: str = "") -> User:
        """Map an identity-provider login to a CrimeWatch user (unknown = no data)."""
        email_n = email.strip().lower()
        username = self.by_email.get(email_n)
        if username:
            u = self.records[username].user
            return User(u.username, u.role, u.display_name or name, email_n, u.states, auth_method="oidc")
        return User(email_n or "unknown", Role.VIEWER, name, email_n, states=(), auth_method="oidc")


# ----------------------------------------------------------------------------
# Brute-force protection
# ----------------------------------------------------------------------------
class LoginThrottle:
    """Locks a username for ``lockout_seconds`` after ``max_attempts`` failures."""

    def __init__(self, max_attempts: int = 5, lockout_seconds: int = 900):
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        self._failures: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _recent(self, key: str, now: float) -> list[float]:
        window = [t for t in self._failures.get(key, []) if now - t < self.lockout_seconds]
        self._failures[key] = window
        return window

    def is_locked(self, username: str, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        with self._lock:
            return len(self._recent(username.lower(), now)) >= self.max_attempts

    def record_failure(self, username: str, now: float | None = None) -> None:
        now = time.time() if now is None else now
        with self._lock:
            self._recent(username.lower(), now).append(now)

    def reset(self, username: str) -> None:
        with self._lock:
            self._failures.pop(username.lower(), None)


def scope_states(user: User, states: Iterable[str]) -> list[str]:
    """Return only the states this user may see, preserving order."""
    return [s for s in states if user.can_see_state(s)]
