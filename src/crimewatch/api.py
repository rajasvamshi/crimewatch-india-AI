"""CrimeWatch India data API (FastAPI).

Endpoints
---------
``GET  /v1/health``                 liveness, no auth
``POST /v1/ingest/daily``           data partner pushes daily aggregate counts  (scope: ingest)
``GET  /v1/live/status``            what the live feed holds                    (scope: read)
``GET  /v1/summary``                yearly totals by state/category            (scope: read)

Authentication is a per-partner API key sent as ``Authorization: Bearer <key>``. Keys are
stored only as SHA-256 hashes in ``config/api_keys.json`` and are bound to scopes and to
the states the partner may write or read (create them with ``scripts/manage_api_keys.py``).
Every request is written to the same hash-chained audit trail as the dashboard.

Run: ``uvicorn src.crimewatch.api:app --host 0.0.0.0 --port 8000`` (behind TLS in production).
"""


import hashlib
import hmac
import json
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator

from . import __version__
from .audit import AuditLogger
from .live_store import DASHBOARD_CATEGORIES, DailyCount, LiveStore
from .settings import Settings

MAX_RECORDS_PER_REQUEST = 5000
MAX_BACKDATE_DAYS = 400


# ----------------------------------------------------------------------------
# API keys
# ----------------------------------------------------------------------------
class ApiClient(BaseModel):
    id: str
    scopes: frozenset[str]
    states: frozenset[str] | None  # None = all states


def hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_api_keys(path: Path) -> dict[str, ApiClient]:
    """Return {key_hash: client}. Missing file = no keys = every call is refused."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, ApiClient] = {}
    for k in data.get("keys", []):
        states = k.get("states")
        out[k["key_hash"]] = ApiClient(
            id=k["id"],
            scopes=frozenset(k.get("scopes", [])),
            states=None if states is None or "*" in states else frozenset(states),
        )
    return out


# ----------------------------------------------------------------------------
# Request models
# ----------------------------------------------------------------------------
class DailyRecord(BaseModel):
    day: date
    state_name: str = Field(min_length=2, max_length=80)
    district_name: str = Field(min_length=1, max_length=120)
    category: str
    crime_count: int = Field(ge=0, le=100_000)
    arrests: int | None = Field(default=None, ge=0, le=100_000)

    @field_validator("category")
    @classmethod
    def _known_category(cls, v: str) -> str:
        if v not in DASHBOARD_CATEGORIES:
            raise ValueError(f"category must be one of {list(DASHBOARD_CATEGORIES)}")
        return v

    @field_validator("day")
    @classmethod
    def _sane_day(cls, v: date) -> date:
        today = date.today()
        if v > today:
            raise ValueError("day cannot be in the future")
        if v < today - timedelta(days=MAX_BACKDATE_DAYS):
            raise ValueError(f"day is older than {MAX_BACKDATE_DAYS} days; load historical data through the ETL")
        return v

    @field_validator("state_name", "district_name")
    @classmethod
    def _clean(cls, v: str) -> str:
        v = " ".join(v.split())
        if any(ch in v for ch in "<>{}\\"):
            raise ValueError("invalid characters")
        return v


class IngestRequest(BaseModel):
    records: list[DailyRecord] = Field(min_length=1, max_length=MAX_RECORDS_PER_REQUEST)


class IngestResponse(BaseModel):
    accepted: int
    source: str


# ----------------------------------------------------------------------------
# App factory
# ----------------------------------------------------------------------------
def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(
        title="CrimeWatch India API",
        version=__version__,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )
    store = LiveStore(settings.live_db_path)
    audit = AuditLogger(settings.audit_log_path)
    bearer = HTTPBearer(auto_error=False)

    @lru_cache(maxsize=1)
    def _keys(mtime: float) -> dict[str, ApiClient]:
        return load_api_keys(settings.api_keys_file)

    def _client(request: Request, creds: HTTPAuthorizationCredentials | None) -> ApiClient:
        p = settings.api_keys_file
        keys = _keys(p.stat().st_mtime if p.exists() else 0.0)
        if creds is not None:
            presented = hash_key(creds.credentials)
            for stored, client in keys.items():
                if hmac.compare_digest(stored, presented):
                    return client
        audit.log("api_auth", outcome="failure", details={"path": request.url.path})
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or missing API key",
                            headers={"WWW-Authenticate": "Bearer"})

    def require(scope: str):
        def dep(request: Request, creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> ApiClient:
            client = _client(request, creds)
            if scope not in client.scopes:
                audit.log("api_scope", user=client.id, role="api", outcome="denied", details={"scope": scope})
                raise HTTPException(status.HTTP_403_FORBIDDEN, f"key lacks scope {scope!r}")
            return client

        return dep

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.get("/v1/health")
    def health() -> dict:
        return {"status": "ok", "version": __version__}

    @app.post("/v1/ingest/daily", response_model=IngestResponse)
    def ingest(body: IngestRequest, client: Annotated[ApiClient, Depends(require("ingest"))]) -> IngestResponse:
        if client.states is not None:
            bad = sorted({r.state_name for r in body.records} - client.states)
            if bad:
                audit.log("live_ingest", user=client.id, role="api", outcome="denied", details={"states": bad})
                raise HTTPException(status.HTTP_403_FORBIDDEN, f"key may not write data for: {', '.join(bad)}")
        n = store.upsert((DailyCount(**r.model_dump()) for r in body.records), source=client.id)
        days = sorted({r.day.isoformat() for r in body.records})
        audit.log("live_ingest", user=client.id, role="api",
                  details={"records": n, "first_day": days[0], "last_day": days[-1]})
        return IngestResponse(accepted=n, source=client.id)

    @app.get("/v1/live/status")
    def live_status(client: Annotated[ApiClient, Depends(require("read"))]) -> dict:
        return store.status()

    @app.get("/v1/summary")
    def summary(
        client: Annotated[ApiClient, Depends(require("read"))],
        year: Annotated[int | None, Query(ge=1950, le=2100)] = None,
        state: Annotated[str | None, Query(max_length=80)] = None,
    ) -> dict:
        from .data_source import DataValidationError, load_dashboard_file

        if state and client.states is not None and state not in client.states:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "key may not read this state")
        try:
            df, info = load_dashboard_file(settings.data_path)
        except DataValidationError as e:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "official dataset unavailable") from e
        if client.states is not None:
            df = df[df["state_name"].isin(client.states)]
        if year is not None:
            df = df[df["year"] == year]
        if state:
            df = df[df["state_name"] == state]
        totals = df.groupby(["year", "state_name", "category"])["crime_count"].sum().reset_index()
        audit.log("api_summary", user=client.id, role="api", details={"year": year, "state": state})
        return {
            "source": Path(info.path).name,
            "source_sha256": info.sha256,
            "rows": totals.to_dict(orient="records"),
        }

    return app


def __getattr__(name: str):
    # `uvicorn src.crimewatch.api:app` builds the app lazily from the environment.
    if name == "app":
        return create_app()
    raise AttributeError(name)
