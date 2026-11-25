import json

import pytest

from src.crimewatch.auth import (
    LoginThrottle,
    Permission,
    Role,
    User,
    UserStore,
    has_permission,
    hash_password,
    scope_states,
    verify_password,
)

PW = "correct horse battery"


def test_hash_roundtrip_and_salting():
    h1, h2 = hash_password(PW), hash_password(PW)
    assert h1 != h2  # random salt
    assert verify_password(PW, h1) and verify_password(PW, h2)
    assert not verify_password("wrong password!!", h1)


def test_short_password_rejected():
    with pytest.raises(ValueError):
        hash_password("short")


@pytest.mark.parametrize("bad", ["", "plain", "md5$abc", "scrypt$x$8$1$00$00"])
def test_malformed_hash_never_verifies(bad):
    assert verify_password(PW, bad) is False


def test_role_permissions_are_least_privilege():
    assert has_permission(Role.VIEWER, Permission.VIEW_DASHBOARD)
    assert not has_permission(Role.VIEWER, Permission.EXPORT_DATA)
    assert has_permission(Role.ANALYST, Permission.EXPORT_DATA)
    assert not has_permission(Role.ANALYST, Permission.RUN_SIMULATION)
    assert has_permission(Role.SUPERVISOR, Permission.VIEW_MODEL_GOVERNANCE)
    assert not has_permission(Role.SUPERVISOR, Permission.EXPORT_OVERRIDE)
    assert all(has_permission(Role.ADMIN, p) for p in Permission)


def _store():
    return UserStore.from_dict(
        {
            "users": [
                {"username": "Admin", "role": "admin", "states": ["*"], "password_hash": hash_password(PW)},
                {
                    "username": "sp.hyd",
                    "role": "supervisor",
                    "states": ["Telangana"],
                    "email": "SP@Example.gov.in",
                    "password_hash": hash_password(PW),
                },
            ]
        }
    )


def test_authenticate():
    s = _store()
    u = s.authenticate("ADMIN", PW)
    assert u and u.role is Role.ADMIN and u.states is None
    assert s.authenticate("admin", "nope-nope-nope") is None
    assert s.authenticate("ghost", PW) is None


def test_duplicate_usernames_rejected():
    with pytest.raises(ValueError):
        UserStore.from_dict({"users": [{"username": "a"}, {"username": "A"}]})


def test_oidc_mapping_known_and_unknown():
    s = _store()
    known = s.resolve_oidc("sp@example.gov.in", "SP")
    assert known.role is Role.SUPERVISOR and known.states == ("Telangana",)
    assert known.auth_method == "oidc"
    stranger = s.resolve_oidc("someone@else.in")
    assert stranger.role is Role.VIEWER and stranger.states == ()  # no data until assigned


def test_jurisdiction_scoping():
    u = User("x", Role.VIEWER, states=("Kerala", "Goa"))
    assert scope_states(u, ["Goa", "Delhi", "Kerala"]) == ["Goa", "Kerala"]
    assert scope_states(User("y", Role.ADMIN), ["Goa", "Delhi"]) == ["Goa", "Delhi"]


def test_throttle_locks_and_expires():
    t = LoginThrottle(max_attempts=3, lockout_seconds=60)
    for i in range(3):
        assert not t.is_locked("u", now=100 + i)
        t.record_failure("u", now=100 + i)
    assert t.is_locked("U", now=105)
    assert not t.is_locked("u", now=200)  # window passed
    t.record_failure("u", now=300)
    t.reset("u")
    assert not t.is_locked("u", now=301)


def test_store_from_missing_file(tmp_path):
    assert len(UserStore.from_file(tmp_path / "none.json")) == 0
    f = tmp_path / "users.json"
    f.write_text(json.dumps({"users": [{"username": "v", "role": "viewer"}]}))
    assert len(UserStore.from_file(f)) == 1
