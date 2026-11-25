"""Streamlit glue for login, session handling, role checks and audit logging."""

from __future__ import annotations

import secrets
import time
from typing import Any

import streamlit as st

from .audit import AuditLogger
from .auth import LoginThrottle, Permission, Role, User, UserStore
from .settings import Settings

_USER_KEY = "cw_user"
_SESSION_KEY = "cw_session_id"
_ACTIVITY_KEY = "cw_last_activity"


@st.cache_resource(show_spinner=False)
def get_settings() -> Settings:
    return Settings.from_env()


@st.cache_resource(show_spinner=False)
def get_audit_logger(path: str) -> AuditLogger:
    from pathlib import Path

    return AuditLogger(Path(path))


@st.cache_resource(show_spinner=False)
def get_user_store(path: str, _mtime: float) -> UserStore:
    from pathlib import Path

    return UserStore.from_file(Path(path))


@st.cache_resource(show_spinner=False)
def get_throttle(max_attempts: int) -> LoginThrottle:
    return LoginThrottle(max_attempts=max_attempts)


def _store(settings: Settings) -> UserStore:
    p = settings.users_file
    mtime = p.stat().st_mtime if p.exists() else 0.0
    return get_user_store(str(p), mtime)


def session_id() -> str:
    if _SESSION_KEY not in st.session_state:
        st.session_state[_SESSION_KEY] = secrets.token_hex(8)
    return st.session_state[_SESSION_KEY]


def current_user() -> User | None:
    return st.session_state.get(_USER_KEY)


def audit(event: str, outcome: str = "success", user: User | None = None, **details: Any) -> None:
    settings = get_settings()
    u = user or current_user()
    get_audit_logger(str(settings.audit_log_path)).log(
        event,
        user=u.username if u else None,
        role=u.role.value if u else None,
        session_id=session_id(),
        outcome=outcome,
        details=details,
    )


def can(permission: Permission) -> bool:
    u = current_user()
    return bool(u and u.can(permission))


def logout(reason: str = "user") -> None:
    u = current_user()
    if u:
        audit("logout", user=u, reason=reason)
    method = u.auth_method if u else ""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    if method == "oidc" and hasattr(st, "logout"):
        st.logout()
    st.rerun()


def _check_idle_timeout(settings: Settings) -> None:
    now = time.time()
    last = st.session_state.get(_ACTIVITY_KEY, now)
    if current_user() and now - last > settings.session_timeout_min * 60:
        logout(reason="idle_timeout")
    st.session_state[_ACTIVITY_KEY] = now


def _login_local(settings: Settings) -> None:
    store = _store(settings)
    throttle = get_throttle(settings.max_login_attempts)

    st.markdown("## Sign in to CrimeWatch India")
    st.caption("Authorised personnel only. All access is recorded in the audit trail.")
    if len(store) == 0:
        st.error(
            "No user accounts are configured. An administrator must create one with "
            "`python scripts/manage_users.py add <username> --role admin`."
        )
        st.stop()

    with st.form("cw_login", clear_on_submit=False):
        username = st.text_input("Username", autocomplete="username")
        password = st.text_input("Password", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Sign in")

    if submitted:
        uname = username.strip().lower()
        if not uname or not password:
            st.error("Enter your username and password.")
        elif throttle.is_locked(uname):
            audit("login", outcome="locked", attempted_user=uname)
            st.error("Too many failed attempts. This account is locked for 15 minutes.")
        else:
            user = store.authenticate(uname, password)
            if user is None:
                throttle.record_failure(uname)
                audit("login", outcome="failure", attempted_user=uname)
                st.error("Invalid username or password.")
            else:
                throttle.reset(uname)
                # New session id on login prevents session fixation.
                st.session_state[_SESSION_KEY] = secrets.token_hex(8)
                st.session_state[_USER_KEY] = user
                st.session_state[_ACTIVITY_KEY] = time.time()
                audit("login", user=user, method="local")
                st.rerun()
    st.stop()


def _login_oidc(settings: Settings) -> None:
    if not hasattr(st, "user") or not hasattr(st, "login"):
        st.error("OIDC login needs Streamlit 1.42 or newer.")
        st.stop()
    if not st.user.is_logged_in:
        st.markdown("## Sign in to CrimeWatch India")
        st.caption("Authorised personnel only. All access is recorded in the audit trail.")
        if st.button("Sign in with government SSO"):
            st.login()
        st.stop()
    user = _store(settings).resolve_oidc(str(st.user.get("email", "")), str(st.user.get("name", "")))
    st.session_state[_SESSION_KEY] = secrets.token_hex(8)
    st.session_state[_USER_KEY] = user
    st.session_state[_ACTIVITY_KEY] = time.time()
    audit("login", user=user, method="oidc")


def require_user() -> User:
    """Return the signed-in user, rendering a login screen and stopping if needed."""
    settings = get_settings()
    session_id()
    _check_idle_timeout(settings)

    user = current_user()
    if user is not None:
        return user

    if settings.auth_mode == "none":
        user = User("developer", Role(settings.dev_role), "Developer (login disabled)", auth_method="none")
        st.session_state[_USER_KEY] = user
        audit("login", user=user, method="none")
        return user
    if settings.auth_mode == "oidc":
        _login_oidc(settings)
    else:
        _login_local(settings)
    return current_user()  # type: ignore[return-value]


def render_user_bar(user: User) -> None:
    settings = get_settings()
    scope = "All India" if user.states is None else (", ".join(user.states) or "No jurisdiction assigned")
    c1, c2 = st.columns([6, 1])
    with c1:
        st.caption(f"Signed in as **{user.label}** · role: **{user.role.value}** · jurisdiction: **{scope}**")
        if settings.auth_mode == "none":
            st.warning("Login is disabled (development mode). Never run this configuration on a server.")
    with c2:
        if user.auth_method != "none" and st.button("Sign out", key="cw_logout"):
            logout()
