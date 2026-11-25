# CrimeWatch India - production image.
# Secure by default: CW_APP_ENV=production refuses to start without authentication and
# disables the Live Pulse simulation. Mount users/secrets at runtime; never bake them in.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CW_APP_ENV=production \
    CW_AUTH_MODE=local \
    CW_AUDIT_LOG_PATH=/app/logs/audit.jsonl

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY .streamlit/config.toml ./.streamlit/config.toml
COPY src/ ./src/
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY config/users.example.json ./config/users.example.json
COPY data/geo/ ./data/geo/

RUN useradd --create-home --uid 1000 crimewatch \
    && mkdir -p /app/logs /app/data/processed \
    && chown -R crimewatch:crimewatch /app/logs /app/config /app/data/processed
USER crimewatch

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -fsS http://localhost:8501/_stcore/health || exit 1

# XSRF protection and other hardening come from .streamlit/config.toml.
CMD ["streamlit", "run", "app/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
