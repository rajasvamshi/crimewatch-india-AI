"""Manage local CrimeWatch user accounts (scrypt-hashed passwords).

Examples::

    python scripts/manage_users.py add admin --role admin
    python scripts/manage_users.py add sp.hyderabad --role supervisor --states Telangana
    python scripts/manage_users.py list
    python scripts/manage_users.py remove sp.hyderabad

Passwords are read interactively (never from the command line, so they stay out of
shell history). The file defaults to ``config/users.json`` or ``$CW_USERS_FILE``.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.crimewatch.auth import MIN_PASSWORD_LENGTH, Role, UserStore, hash_password  # noqa: E402


def _path(arg: str | None) -> Path:
    p = Path(arg or os.environ.get("CW_USERS_FILE", "config/users.json"))
    return p if p.is_absolute() else ROOT / p


def _load(path: Path) -> dict:
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        UserStore.from_dict(data)  # validate
        return data
    return {"users": []}


def _save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", help="users JSON path")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="add or update a user")
    a.add_argument("username")
    a.add_argument("--role", choices=Role.values(), default="viewer")
    a.add_argument("--states", nargs="*", default=["*"], help="state names, or * for all India")
    a.add_argument("--display-name", default="")
    a.add_argument("--email", default="")
    r = sub.add_parser("remove", help="remove a user")
    r.add_argument("username")
    sub.add_parser("list", help="list users")
    args = ap.parse_args(argv)

    path = _path(args.file)
    data = _load(path)
    users = data["users"]

    if args.cmd == "list":
        for u in users:
            print(f"{u['username']:<24} {u.get('role', 'viewer'):<11} {','.join(u.get('states', ['*']))}")
        return 0

    uname = args.username.strip().lower()
    users[:] = [u for u in users if u["username"].lower() != uname] if args.cmd == "remove" else users
    if args.cmd == "remove":
        _save(path, data)
        print(f"removed {uname}")
        return 0

    pw = getpass.getpass(f"Password for {uname} (min {MIN_PASSWORD_LENGTH} chars): ")
    if pw != getpass.getpass("Repeat password: "):
        print("passwords do not match", file=sys.stderr)
        return 1
    entry = {
        "username": uname,
        "display_name": args.display_name,
        "role": args.role,
        "states": args.states,
        "email": args.email.lower(),
        "password_hash": hash_password(pw),
    }
    users[:] = [u for u in users if u["username"].lower() != uname] + [entry]
    UserStore.from_dict(data)
    _save(path, data)
    print(f"saved {uname} ({args.role}) to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
