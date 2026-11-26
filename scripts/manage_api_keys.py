"""Issue and revoke API keys for data partners (live feed) and read-only consumers.

    python scripts/manage_api_keys.py add ts-police --scopes ingest read --states Telangana
    python scripts/manage_api_keys.py list
    python scripts/manage_api_keys.py revoke ts-police

The raw key is printed ONCE; only its SHA-256 hash is stored in config/api_keys.json.
Send it to the partner over a secure channel and rotate it at least every 90 days.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.crimewatch.api import hash_key  # noqa: E402

SCOPES = ("ingest", "read")


def _path(arg: str | None) -> Path:
    p = Path(arg or os.environ.get("CW_API_KEYS_FILE", "config/api_keys.json"))
    return p if p.is_absolute() else ROOT / p


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("id")
    a.add_argument("--scopes", nargs="+", choices=SCOPES, required=True)
    a.add_argument("--states", nargs="*", default=["*"])
    r = sub.add_parser("revoke")
    r.add_argument("id")
    sub.add_parser("list")
    args = ap.parse_args(argv)

    path = _path(args.file)
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"keys": []}
    keys = data["keys"]

    if args.cmd == "list":
        for k in keys:
            states = ','.join(k.get('states', ['*']))
            print(f"{k['id']:<20} {','.join(k['scopes']):<12} {states}  created {k['created']}")
        return 0
    keys[:] = [k for k in keys if k["id"] != args.id]
    if args.cmd == "add":
        raw = "cw_" + secrets.token_urlsafe(32)
        keys.append({
            "id": args.id,
            "key_hash": hash_key(raw),
            "scopes": args.scopes,
            "states": args.states,
            "created": datetime.now(timezone.utc).date().isoformat(),
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(path)
    if args.cmd == "add":
        print(f"API key for {args.id} (shown once, store it securely):\n{raw}")
    else:
        print(f"revoked {args.id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
