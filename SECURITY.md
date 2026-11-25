# Security Policy

## Reporting a vulnerability

Please **do not open a public GitHub issue** for security problems. Email the maintainer
(see README → Author) with a description, steps to reproduce and the affected version.
You will get an acknowledgement within 3 working days. For deployments run by an Indian
government body, the operating department must also report cyber incidents to CERT-In
within 6 hours as required by the CERT-In directions of 28 April 2022.

## Security model (summary)

| Control | Where |
| --- | --- |
| Authentication: OIDC SSO (`CW_AUTH_MODE=oidc`) or local accounts with scrypt-hashed passwords | `src/crimewatch/auth.py`, `ui_auth.py` |
| Login throttling: account locked 15 minutes after 5 failures (configurable) | `LoginThrottle` |
| Session: new session id on login, idle logout after 30 minutes (configurable) | `ui_auth.py` |
| Role-based access: viewer, analyst, supervisor, admin | `ROLE_PERMISSIONS` |
| Jurisdiction scoping: users only receive rows for their assigned states | `dashboard.main()` |
| Audit trail: JSON Lines, hash-chained, secrets redacted | `src/crimewatch/audit.py` |
| Production guard: `CW_APP_ENV=production` refuses `CW_AUTH_MODE=none` and disables simulations | `settings.py` |
| XSRF protection on, telemetry off, error details hidden from browsers | `.streamlit/config.toml` |
| Data contract: files are validated before the dashboard will load them | `src/crimewatch/data_source.py` |
| Container: non-root user, read-only filesystem, all capabilities dropped | `Dockerfile`, `docker-compose.yml` |
| CI: tests, ruff lint, bandit, pip-audit on every pull request; Dependabot weekly | `.github/` |

Verify the audit trail has not been edited:

```bash
python -c "from src.crimewatch.audit import verify_chain; print(verify_chain(open('logs/audit.jsonl')))"
```

## Never commit

`config/users.json`, `.streamlit/secrets.toml`, `.env`, and anything under `logs/`.
These paths are git-ignored.
