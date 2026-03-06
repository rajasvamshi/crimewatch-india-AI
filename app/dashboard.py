from __future__ import annotations

import json
import logging
import re
import secrets
import string
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from importlib.util import find_spec

warnings.filterwarnings("ignore")

DATASET_SCHEMA_VERSION = 4  # CHANGE: cache hardening (+1)


# ============================================================
# 🔐 SECURITY & AUDIT LOGGING SETUP
# ============================================================
logging.basicConfig(
    filename="crimewatch_audit.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def log_action(action: str, user: Optional[str] = None, details: Optional[str] = None) -> None:
    """Log dashboard actions for audit trail."""
    log_entry = f"Action: {action} | User: {user or 'anonymous'} | Details: {details or 'N/A'}"
    logging.info(log_entry)


# ============================================================
# 🎬 CINEMATIC PAGE CONFIG - TACTICAL INTELLIGENCE COMMAND CENTER
# ============================================================
st.set_page_config(
    page_title="CrimeWatch AI | Sovereign Intelligence HUD",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 🎨 EPIC SOVEREIGN INTELLIGENCE HUD THEME
# Must preserve cinematic style and required classes:
# - .clean-header-container
# - .kpi-card
# - .briefing-container
# - .warning-panel
# - .data-stream-ticker
# ============================================================
EPIC_SOVEREIGN_HUD_THEME = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600;700&family=Space+Grotesk:wght@300;400;600;700&family=JetBrains+Mono:wght@300;400;600;700&display=swap');

:root{
  --midnight-void:#020205;
  --tactical-cyan:#00f3ff;
  --deep-cobalt:#0066ff;
  --intelligence-gold:#e0af68;
  --blood-orange:#ff4d00;
  --matrix-green:#00ff41;
  --card-bg:rgba(10,10,18,.72);
  --glass-bg:rgba(10,10,18,.72);
  --neon-trace:rgba(0,243,255,.22);

  --text-primary:#ffffff;
  --text-secondary:#a0a0b8;
  --text-muted:#6b7280;

  --transition-fast:all .25s cubic-bezier(.4,0,.2,1);
  --transition-normal:all .4s cubic-bezier(.4,0,.2,1);
}

/* Anti-blackout */
.stApp{ visibility:visible !important; background:var(--midnight-void) !important; }

/* Zero-gap container */
.block-container{
  padding-top:0rem !important;
  padding-bottom:0rem !important;
  max-width:100% !important;
  margin:0 !important;
}

/* Background */
html, body, [class*="css"]{
  font-family:'Space Grotesk',sans-serif !important;
  background:
    radial-gradient(circle at center, #0a0a12 0%, #020205 100%) !important;
  color:var(--text-primary) !important;
  margin:0 !important;
  padding:0 !important;
  overflow-x:hidden;
}

/* Hex grid overlay */
.stApp::before{
  content:"";
  position:fixed; inset:0;
  pointer-events:none;
  background-image:
    linear-gradient(30deg, rgba(0,243,255,.03) 12%, transparent 12.5%, transparent 87%, rgba(0,243,255,.03) 87.5%, rgba(0,243,255,.03)),
    linear-gradient(150deg, rgba(0,243,255,.03) 12%, transparent 12.5%, transparent 87%, rgba(0,243,255,.03) 87.5%, rgba(0,243,255,.03)),
    linear-gradient(90deg, rgba(0,243,255,.03) 12%, transparent 12.5%, transparent 87%, rgba(0,243,255,.03) 87.5%, rgba(0,243,255,.03));
  background-size:50px 86.6px;
  z-index:-1;
}

/* Scanline effect */
.stApp::after{
  content:"";
  position:fixed; inset:0;
  pointer-events:none;
  background:
    linear-gradient(rgba(18,16,16,0) 50%, rgba(0,0,0,.1) 50%),
    linear-gradient(90deg, rgba(255,0,0,.02), rgba(0,255,0,.01), rgba(0,0,255,.02));
  background-size:100% 3px, 3px 100%;
  z-index:1000;
  opacity:.22;
  animation:scanline .8s linear infinite;
}
@keyframes scanline{0%{background-position:0 0,0 0} 100%{background-position:0 100%,0 100%}}

/* Hide Streamlit chrome */
#MainMenu, header, footer,
[data-testid="stDeployButton"],
[data-testid="stDecoration"],
[data-testid="stToolbar"],
[data-testid="stStatusWidget"],
section[data-testid="stSidebar"]{
  display:none !important;
  visibility:hidden !important;
}

/* Clean header container (required class) */
.clean-header-container{
  background:rgba(5,5,9,.95);
  backdrop-filter:blur(18px);
  -webkit-backdrop-filter:blur(18px);
  border-bottom:2px solid rgba(0,243,255,.28);
  padding:8px 18px !important;
  position:sticky; top:0;
  z-index:10000;
  box-shadow:0 4px 20px rgba(0,0,0,.8);
  margin:0 !important;
  display:flex; align-items:center; justify-content:space-between;
}
.header-left{display:flex; align-items:center; gap:12px;}
.ai-badge{font-size:24px; animation:pulse 2s ease-in-out infinite;}
@keyframes pulse{0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.05);opacity:.82}}
.main-title{
  font-family:'Space Grotesk',sans-serif;
  font-size:18px; font-weight:700;
  color:var(--tactical-cyan);
  text-shadow:0 0 10px rgba(0,243,255,.5);
  margin:0 !important; letter-spacing:.05em;
}
.subtitle{
  font-size:10px; color:var(--text-secondary);
  letter-spacing:.1em; text-transform:uppercase;
  margin:0 !important;
}
.mission-tag{
  background:rgba(0,243,255,.1);
  border:1px solid rgba(0,243,255,.28);
  padding:4px 12px; border-radius:20px;
  font-size:11px; color:var(--text-secondary);
  letter-spacing:.1em; display:inline-block;
}
.status-indicator{display:flex; align-items:center; gap:8px;}
.status-dot{
  width:10px; height:10px; border-radius:50%;
  background:var(--matrix-green);
  box-shadow:0 0 15px var(--matrix-green);
  animation:heartbeat 2s ease-in-out infinite;
}
@keyframes heartbeat{0%,100%{transform:scale(1); box-shadow:0 0 0 0 rgba(0,255,65,.7)}
50%{transform:scale(1.3); box-shadow:0 0 0 8px rgba(0,255,65,0)}}
.status-text{
  font-family:'JetBrains Mono',monospace;
  font-size:11px; color:var(--matrix-green);
  font-weight:600; letter-spacing:.1em; text-transform:uppercase;
}
.header-divider{
  height:1px !important;
  background:linear-gradient(90deg, transparent, var(--tactical-cyan), transparent) !important;
  width:100% !important;
  margin:0 !important;
  box-shadow:0 0 8px rgba(0,243,255,.5);
}

/* Section header (used throughout) */
.section-header{
  font-family:'Space Grotesk',sans-serif;
  font-size:24px; font-weight:700;
  color:var(--tactical-cyan);
  margin:18px 0 14px 0;
  text-shadow:0 0 10px rgba(0,243,255,.5);
  display:flex; align-items:center; gap:12px;
}
.section-header::before{content:"🎯";}

/* Glass cards + required panels */
.glass-card, .control-panel, .briefing-container, .warning-panel, .kpi-card{
  background:var(--glass-bg) !important;
  backdrop-filter:blur(12px) !important;
  -webkit-backdrop-filter:blur(12px) !important;
  border:1px solid transparent !important;
  border-radius:16px !important;
  box-shadow:0 8px 32px rgba(0,0,0,.6), inset 0 0 15px rgba(0,243,255,.08) !important;
  position:relative !important;
  overflow:hidden !important;
  transition:var(--transition-normal) !important;
}
.glass-card::before, .control-panel::before, .briefing-container::before, .warning-panel::before, .kpi-card::before{
  content:"";
  position:absolute; inset:0;
  border-radius:16px;
  padding:1px;
  background:linear-gradient(45deg, #00f3ff, #0066ff, #6600ff, #ff00cc, #ff6600, #ffcc00, #00f3ff);
  background-size:400% 400%;
  -webkit-mask:linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite:xor;
  mask-composite:exclude;
  animation:gradient-border 8s ease infinite;
  pointer-events:none;
}
@keyframes gradient-border{0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%}}
.glass-card:hover, .control-panel:hover, .kpi-card:hover{
  transform:scale(1.01) translateY(-2px) !important;
  box-shadow:0 12px 48px rgba(0,243,255,.28), inset 0 0 25px rgba(0,243,255,.12) !important;
}

/* Control panel */
.control-panel{ padding:16px 22px !important; margin:10px 0 0 0 !important; }
.panel-title{
  font-family:'Space Grotesk',sans-serif;
  font-size:12px; font-weight:700;
  color:var(--tactical-cyan);
  margin-bottom:14px;
  text-transform:uppercase; letter-spacing:.15em;
  display:flex; align-items:center; gap:8px;
}
.panel-title::before{content:"📡";}
.quick-filter-container{
  background:rgba(0,243,255,.08);
  border:1px solid rgba(0,243,255,.2);
  border-radius:12px;
  padding:14px;
  margin-bottom:18px;
}
.quick-filter-title{
  font-family:'Space Grotesk',sans-serif;
  font-size:11px;
  color:var(--tactical-cyan);
  font-weight:600;
  margin-bottom:10px;
  text-transform:uppercase;
  letter-spacing:.15em;
  display:flex; align-items:center; gap:8px;
}
.quick-filter-title::before{content:"⚡";}
.filter-label{
  font-family:'Space Grotesk',sans-serif;
  font-size:11px;
  color:var(--text-muted);
  margin-bottom:6px;
  font-weight:600;
  text-transform:uppercase;
  letter-spacing:.15em;
}

/* KPI card (required class) */
.kpi-card{
  height:160px !important;
  padding:18px !important;
  border-radius:20px !important;
  display:flex !important;
  flex-direction:column !important;
  justify-content:space-between !important;
}
.kpi-card.critical{
  box-shadow:inset 0 0 20px rgba(255,77,0,.4), 0 8px 32px rgba(255,77,0,.3) !important;
  animation:pulse-critical 2s ease-in-out infinite;
}
@keyframes pulse-critical{
  0%,100%{box-shadow:inset 0 0 20px rgba(255,77,0,.4), 0 8px 32px rgba(255,77,0,.3)}
  50%{box-shadow:inset 0 0 30px rgba(255,77,0,.6), 0 12px 48px rgba(255,77,0,.4)}
}
.kpi-label{
  font-size:10px !important;
  color:var(--text-muted) !important;
  text-transform:uppercase !important;
  letter-spacing:.15em !important;
  text-align:center !important;
  margin:0 !important;
  font-weight:600 !important;
}
.kpi-value{
  font-family:'JetBrains Mono',monospace !important;
  font-size:34px !important;
  font-weight:700 !important;
  color:var(--tactical-cyan) !important;
  text-align:center !important;
  margin:auto !important;
  text-shadow:0 0 15px rgba(0,243,255,.6) !important;
  letter-spacing:-1px !important;
}
.kpi-status-pill{
  text-align:center !important;
  margin-top:12px !important;
  padding:6px 14px !important;
  border-radius:20px !important;
  font-family:'JetBrains Mono',monospace !important;
  font-size:11px !important;
  font-weight:600 !important;
  letter-spacing:.1em !important;
  display:inline-block !important;
  width:fit-content !important;
  margin-left:auto !important;
  margin-right:auto !important;
  border:1px solid rgba(255,255,255,.1) !important;
}
.kpi-status-pill.positive{background:rgba(16,185,129,.15) !important; color:#10b981 !important; border-color:rgba(16,185,129,.4) !important;}
.kpi-status-pill.negative{background:rgba(255,77,0,.15) !important; color:var(--blood-orange) !important; border-color:rgba(255,77,0,.4) !important;}
.kpi-status-pill.neutral{background:rgba(100,100,111,.15) !important; color:#94a3b8 !important; border-color:rgba(100,100,111,.4) !important;}

/* Briefing container (required class) */
.briefing-container{
  display:grid !important;
  grid-template-columns:1.2fr 1fr 1fr !important;
  gap:22px !important;
  padding:22px !important;
  border:2px solid var(--intelligence-gold) !important;
  background:rgba(10,10,15,.92) !important;
}
.briefing-title{
  font-family:'Space Grotesk',sans-serif !important;
  font-weight:700 !important;
  color:var(--intelligence-gold) !important;
  font-size:14px !important;
  margin-bottom:12px !important;
  text-transform:uppercase !important;
  letter-spacing:.15em !important;
  border-bottom:1px solid rgba(224,175,104,.28) !important;
  padding-bottom:8px !important;
  display:flex; gap:8px; align-items:center;
}
.briefing-title::before{content:"⚠️";}
.briefing-content{
  font-size:12px !important;
  color:#cbd5e1 !important;
  line-height:1.75 !important;
  letter-spacing:.03em !important;
  font-family:'JetBrains Mono',monospace !important;
}
.briefing-content strong{color:var(--intelligence-gold) !important; font-weight:600 !important; font-family:'Space Grotesk',sans-serif !important;}
@media (max-width: 992px){ .briefing-container{ grid-template-columns: 1fr !important; } }

/* Warning panel (required class) */
.warning-panel{
  background:linear-gradient(135deg, rgba(45,0,0,.8) 0%, rgba(60,0,0,.9) 100%) !important;
  border:1px solid rgba(255,77,0,.4) !important;
  padding:22px !important;
  margin:18px 0 0 0 !important;
}
.warning-title{
  font-weight:700;
  color:#ff884d;
  font-size:18px;
  margin-bottom:12px;
  display:flex; align-items:center; gap:12px;
  font-family:'Space Grotesk',sans-serif;
}
.warning-title::before{content:"⚠️";}
.warning-content{
  line-height:1.7;
  color:#ffaa88;
  font-size:14px;
  font-family:'Space Grotesk',sans-serif;
}
.warning-footer{
  margin-top:14px;
  padding-top:14px;
  border-top:1px solid rgba(255,255,255,.1);
  font-size:13px;
  color:var(--text-muted);
  font-family:'Space Grotesk',sans-serif;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{
  gap:8px; padding:12px 0; margin:0;
  border-bottom:2px solid rgba(0,243,255,.28);
}
.stTabs [data-baseweb="tab"]{
  background:rgba(255,255,255,.03);
  border:1px solid rgba(0,243,255,.2);
  border-radius:12px 12px 0 0;
  padding:10px 18px;
  color:var(--text-muted) !important;
  font-weight:600; font-size:11px;
  transition:var(--transition-fast);
  font-family:'Space Grotesk',sans-serif;
  letter-spacing:.1em;
  text-transform:uppercase;
}
.stTabs [data-baseweb="tab"]:hover{
  background:rgba(0,243,255,.15);
  color:var(--text-primary) !important;
  border-color:var(--tactical-cyan);
  transform:translateY(-2px);
}
.stTabs [aria-selected="true"]{
  color:var(--text-primary) !important;
  background:rgba(0,243,255,.25) !important;
  border-color:var(--tactical-cyan) !important;
  border-bottom-color:var(--midnight-void) !important;
  box-shadow:0 4px 16px rgba(0,243,255,.35);
  transform:translateY(-2px);
}

/* Dataframe */
[data-testid="stDataFrame"]{
  border-radius:12px !important;
  overflow:hidden !important;
  border:1px solid rgba(0,243,255,.2) !important;
  background:rgba(16,16,26,.6) !important;
}
[data-testid="stDataFrame"] th{
  background:rgba(0,243,255,.1) !important;
  color:var(--text-primary) !important;
  font-family:'Space Grotesk',sans-serif !important;
  font-weight:700 !important;
  font-size:11px !important;
  letter-spacing:.1em;
  text-transform:uppercase;
}
[data-testid="stDataFrame"] td{
  color:var(--text-secondary) !important;
  font-family:'JetBrains Mono',monospace !important;
  font-size:11px !important;
  border-bottom:1px solid rgba(255,255,255,.05) !important;
  letter-spacing:.03em;
}

/* Ticker (required class) */
.data-stream-ticker{
  background:rgba(5,5,9,.95);
  backdrop-filter:blur(20px);
  -webkit-backdrop-filter:blur(20px);
  border-top:2px solid rgba(0,243,255,.28);
  padding:12px 0;
  position:fixed;
  bottom:0; left:0; right:0;
  z-index:10000;
  overflow:hidden;
  box-shadow:0 -4px 20px rgba(0,0,0,.8);
}
.ticker-content{
  display:inline-block;
  white-space:nowrap;
  animation:scroll-ticker 45s linear infinite;
  font-family:'JetBrains Mono',monospace;
  font-size:12px;
  color:var(--matrix-green);
  text-shadow:0 0 5px rgba(0,255,65,.5);
}
.stream-item{
  display:inline-block;
  margin-right:40px;
  padding:0 15px;
  border-right:1px solid rgba(0,255,65,.3);
}
.stream-item:last-child{border-right:none;}
@keyframes scroll-ticker{0%{transform:translateX(100%)} 100%{transform:translateX(-100%)}}

/* Footer */
.footer{
  text-align:center;
  padding:22px !important;
  color:var(--text-muted);
  font-size:11px;
  margin-top:60px !important;
  border-top:1px solid rgba(0,243,255,.2);
  background:rgba(5,5,9,.95);
  font-family:'JetBrains Mono',monospace !important;
  letter-spacing:.05em;
}
.footer-title{
  font-family:'Space Grotesk',sans-serif;
  font-weight:700;
  margin-bottom:14px;
  color:var(--tactical-cyan);
  font-size:14px;
  letter-spacing:.15em;
  text-transform:uppercase;
}
.footer-grid{display:flex; justify-content:center; gap:22px; flex-wrap:wrap; margin-bottom:14px;}
.footer-warning{margin-bottom:14px; color:var(--intelligence-gold); font-size:11px;}
.footer-legal{display:flex; justify-content:center; gap:18px; flex-wrap:wrap; font-size:10px; color:var(--text-muted);}
</style>
"""
st.markdown(EPIC_SOVEREIGN_HUD_THEME, unsafe_allow_html=True)

# ============================================================
# 🧠 HELPER FUNCTIONS
# ============================================================


def _has_module(module_name: str) -> bool:
    return find_spec(module_name) is not None


def normalize_name(x: Any) -> str:
    """Normalize text for consistent matching."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return ""
    s = str(x).strip()
    s = " ".join(s.split())
    return s.title()


def format_number(n: Any) -> str:
    """Format large numbers with K/M suffixes."""
    if n is None or (isinstance(n, float) and np.isnan(n)):
        return "—"
    try:
        n = float(n)
    except Exception:
        return str(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return f"{n:,.0f}"


def normalize_series(series: pd.Series) -> pd.Series:
    """Normalize series to 0-100 scale."""
    if series is None or len(series) == 0:
        return pd.Series([], dtype=float)
    s = series.astype(float)
    if np.isclose(s.max(), s.min()):
        return pd.Series([50.0] * len(s), index=series.index, dtype=float)
    return ((s - s.min()) / (s.max() - s.min())) * 100.0


def apply_tactical_theme(fig: go.Figure) -> go.Figure:
    """Apply consistent dark theme to Plotly figures."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0", size=13, family="Space Grotesk"),
        title=dict(font=dict(size=20, color="#ffffff", family="Space Grotesk")),
        margin=dict(l=30, r=30, t=60, b=30),
        legend=dict(
            bgcolor="rgba(30, 30, 45, 0.8)",
            bordercolor="rgba(0, 243, 255, 0.3)",
            borderwidth=1,
            font=dict(size=12),
        ),
        hoverlabel=dict(
            bgcolor="rgba(30, 30, 45, 0.95)",
            font=dict(color="#ffffff", size=13),
            bordercolor="rgba(0, 243, 255, 0.5)",
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.07)",
            zeroline=False,
            title_font=dict(color="#a0a0b8", family="Space Grotesk"),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.07)",
            zeroline=False,
            title_font=dict(color="#a0a0b8", family="Space Grotesk"),
        ),
    )
    return fig


def _stable_hash_int(s: str) -> int:
    """Stable-ish hash independent of Python hash randomisation."""
    # Use a deterministic sum-of-bytes transform (fast, stable).
    b = s.encode("utf-8", errors="ignore")
    return int(sum((i + 1) * b[i] for i in range(len(b))) % (2**31 - 1))


def _stable_jitter_pair(key: str, scale_lat: float = 0.35, scale_lon: float = 0.35) -> Tuple[float, float]:
    h = _stable_hash_int(key)
    rng = np.random.default_rng(h)
    return float(rng.normal(0, scale_lat)), float(rng.normal(0, scale_lon))


# CHANGE: cache hardening helpers (canonical config + stale dataset detection)
def validate_canonical_config() -> Tuple[bool, Dict[str, Any]]:
    """
    Validate canonical dropdown/data-generation configuration.
    Checks (required by patch spec):
      - each state has district mapping
      - no empty district list
      - categories non-empty
    """
    meta: Dict[str, Any] = {"status": "OK"}

    states = list(STATE_CENTROIDS.keys())
    missing_states = [s for s in states if s not in DISTRICTS_BY_STATE]
    empty_district_states = [s for s in states if not DISTRICTS_BY_STATE.get(s)]
    categories_ok = bool(CRIME_CATEGORIES)

    meta.update(
        {
            "states": int(len(states)),
            "district_states": int(len(DISTRICTS_BY_STATE)),
            "missing_states": missing_states,
            "empty_district_states": empty_district_states,
            "categories": int(len(CRIME_CATEGORIES)),
        }
    )

    ok = (not missing_states) and (not empty_district_states) and categories_ok
    if not ok:
        meta["status"] = "INVALID"
    return ok, meta


# CHANGE: cache hardening helper (cached dataset completeness vs canonical config)
def is_cached_dataset_stale(df: pd.DataFrame) -> bool:
    """
    Detect stale/incomplete cached datasets by checking canonical coverage:
      - state coverage
      - district coverage per state
      - category coverage
    """
    if df is None or df.empty:
        return True

    required_cols = {"state_name_norm", "district_name_norm", "category"}
    if not required_cols.issubset(set(df.columns)):
        return True

    # State coverage: df must contain all canonical states (normalised)
    canonical_states_norm = {normalize_name(s) for s in STATE_CENTROIDS.keys()}
    df_states = set(df["state_name_norm"].astype(str).unique().tolist())
    if not canonical_states_norm.issubset(df_states):
        return True

    # District coverage per state
    for state in STATE_CENTROIDS.keys():
        state_norm = normalize_name(state)
        canon_districts_norm = {normalize_name(d) for d in DISTRICTS_BY_STATE.get(state, [])}
        if not canon_districts_norm:
            return True
        have = set(
            df[df["state_name_norm"] == state_norm]["district_name_norm"].astype(str).unique().tolist()
        )
        if not canon_districts_norm.issubset(have):
            return True

    # Category coverage
    canonical_categories_norm = {normalize_name(c) for c in CRIME_CATEGORIES}
    df_categories = set(df["category"].astype(str).unique().tolist())
    if not canonical_categories_norm.issubset(df_categories):
        return True

    return False


# ============================================================
# 🗺️ GEO BASELINES
# ============================================================
STATE_CENTROIDS: Dict[str, Tuple[float, float]] = {
    "Andhra Pradesh": (15.9129, 79.7400),
    "Arunachal Pradesh": (28.2180, 94.7278),
    "Assam": (26.2006, 92.9376),
    "Bihar": (25.0961, 85.3131),
    "Chhattisgarh": (21.2787, 81.8661),
    "Goa": (15.2993, 74.1240),
    "Gujarat": (22.2587, 71.1924),
    "Haryana": (29.0588, 76.0856),
    "Himachal Pradesh": (31.1048, 77.1734),
    "Jharkhand": (23.6102, 85.2799),
    "Karnataka": (15.3173, 75.7139),
    "Kerala": (10.8505, 76.2711),
    "Madhya Pradesh": (22.9734, 78.6569),
    "Maharashtra": (19.7515, 75.7139),
    "Manipur": (24.6637, 93.9063),
    "Meghalaya": (25.4670, 91.3662),
    "Mizoram": (23.1645, 92.9376),
    "Nagaland": (26.1584, 94.5624),
    "Odisha": (20.9517, 85.0985),
    "Punjab": (31.1471, 75.3412),
    "Rajasthan": (27.0238, 74.2179),
    "Sikkim": (27.5330, 88.5122),
    "Tamil Nadu": (11.1271, 78.6569),
    "Telangana": (18.1124, 79.0193),
    "Tripura": (23.9408, 91.9882),
    "Uttar Pradesh": (26.8467, 80.9462),
    "Uttarakhand": (30.0668, 79.0193),
    "West Bengal": (22.9868, 87.8550),
    "Delhi": (28.7041, 77.1025),
}

# CHANGE: canonical districts for dropdowns + data generation (names reused verbatim)
DISTRICTS_BY_STATE: Dict[str, list[str]] = {
    
    "Andhra Pradesh": [
        "Alluri Sitharama Raju", "Anakapalli", "Anantapur", "Annamayya",
        "Bapatla", "Chittoor", "Dr. B.R. Ambedkar Konaseema",
        "East Godavari", "Eluru", "Guntur", "Kakinada", "Krishna",
        "Kurnool", "Nandyal", "Nellore", "NTR",
        "Palnadu", "Parvathipuram Manyam", "Prakasam",
        "Sri Potti Sriramulu Nellore", "Sri Sathya Sai",
        "Srikakulam", "Tirupati", "Visakhapatnam",
        "Vizianagaram", "West Godavari", "YSR Kadapa"
    ],

    "Arunachal Pradesh": [
        "Anjaw", "Changlang", "Dibang Valley", "East Kameng",
        "East Siang", "Kamle", "Kra Daadi", "Kurung Kumey",
        "Lepa Rada", "Lohit", "Longding", "Lower Dibang Valley",
        "Lower Siang", "Lower Subansiri", "Namsai", "Pakke Kessang",
        "Papum Pare", "Shi Yomi", "Siang", "Tawang",
        "Tirap", "Upper Siang", "Upper Subansiri",
        "West Kameng", "West Siang"
    ],

    "Assam": [
        "Baksa", "Barpeta", "Biswanath", "Bongaigaon", "Cachar",
        "Charaideo", "Chirang", "Darrang", "Dhemaji", "Dhubri",
        "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat",
        "Hailakandi", "Hojai", "Jorhat", "Kamrup",
        "Kamrup Metropolitan", "Karbi Anglong", "Karimganj",
        "Kokrajhar", "Lakhimpur", "Majuli", "Morigaon",
        "Nagaon", "Nalbari", "Sivasagar", "Sonitpur",
        "South Salmara-Mankachar", "Tamulpur", "Tinsukia",
        "Udalguri", "West Karbi Anglong"
    ],

    "Bihar": [
        "Araria", "Arwal", "Aurangabad", "Banka", "Begusarai",
        "Bhagalpur", "Bhojpur", "Buxar", "Darbhanga",
        "East Champaran", "Gaya", "Gopalganj",
        "Jamui", "Jehanabad", "Kaimur", "Katihar",
        "Khagaria", "Kishanganj", "Lakhisarai",
        "Madhepura", "Madhubani", "Munger",
        "Muzaffarpur", "Nalanda", "Nawada",
        "Patna", "Purnia", "Rohtas",
        "Saharsa", "Samastipur", "Saran",
        "Sheikhpura", "Sheohar", "Sitamarhi",
        "Siwan", "Supaul", "Vaishali",
        "West Champaran"
    ],

    "Chhattisgarh": [
        "Balod", "Baloda Bazar", "Balrampur", "Bastar",
        "Bemetara", "Bijapur", "Bilaspur", "Dantewada",
        "Dhamtari", "Durg", "Gariaband",
        "Gaurela-Pendra-Marwahi", "Janjgir-Champa", "Jashpur",
        "Kabirdham", "Kanker", "Kondagaon", "Korba",
        "Koriya", "Mahasamund", "Mungeli",
        "Narayanpur", "Raigarh", "Raipur",
        "Rajnandgaon", "Sukma", "Surajpur", "Surguja"
    ],

    "Delhi": [
        "Central Delhi", "East Delhi", "New Delhi",
        "North Delhi", "North East Delhi",
        "North West Delhi", "Shahdara",
        "South Delhi", "South East Delhi",
        "South West Delhi", "West Delhi"
    ],

    "Goa": [
        "North Goa", "South Goa"
    ],

    "Gujarat": [
        "Ahmedabad", "Amreli", "Anand", "Aravalli",
        "Banaskantha", "Bharuch", "Bhavnagar",
        "Botad", "Chhota Udaipur", "Dahod",
        "Dang", "Devbhoomi Dwarka", "Gandhinagar",
        "Gir Somnath", "Jamnagar", "Junagadh",
        "Kheda", "Kutch", "Mahisagar",
        "Mehsana", "Morbi", "Narmada",
        "Navsari", "Panchmahal", "Patan",
        "Porbandar", "Rajkot", "Sabarkantha",
        "Surat", "Surendranagar", "Tapi",
        "Vadodara", "Valsad"
    ],

    "Haryana": [
        "Ambala", "Bhiwani", "Charkhi Dadri",
        "Faridabad", "Fatehabad", "Gurugram",
        "Hisar", "Jhajjar", "Jind",
        "Kaithal", "Karnal", "Kurukshetra",
        "Mahendragarh", "Nuh", "Palwal",
        "Panchkula", "Panipat", "Rewari",
        "Rohtak", "Sirsa", "Sonipat",
        "Yamunanagar"
    ],

    "Himachal Pradesh": [
        "Bilaspur", "Chamba", "Hamirpur",
        "Kangra", "Kinnaur", "Kullu",
        "Lahaul and Spiti", "Mandi",
        "Shimla", "Sirmaur", "Solan", "Una"
    ],

    "Jharkhand": [
        "Bokaro", "Chatra", "Deoghar",
        "Dhanbad", "Dumka", "East Singhbhum",
        "Garhwa", "Giridih", "Godda",
        "Gumla", "Hazaribagh", "Jamtara",
        "Khunti", "Koderma", "Latehar",
        "Lohardaga", "Pakur", "Palamu",
        "Ramgarh", "Ranchi", "Sahebganj",
        "Seraikela-Kharsawan", "Simdega",
        "West Singhbhum"
    ],

    "Karnataka": [
        "Bagalkot", "Ballari", "Belagavi",
        "Bengaluru Rural", "Bengaluru Urban",
        "Bidar", "Chamarajanagar", "Chikballapur",
        "Chikkamagaluru", "Chitradurga",
        "Dakshina Kannada", "Davanagere",
        "Dharwad", "Gadag", "Hassan",
        "Haveri", "Kalaburagi", "Kodagu",
        "Kolar", "Koppal", "Mandya",
        "Mysuru", "Raichur", "Ramanagara",
        "Shivamogga", "Tumakuru",
        "Udupi", "Uttara Kannada",
        "Vijayapura", "Yadgir"
    ],
    "Kerala": [
        "Alappuzha", "Ernakulam", "Idukki", "Kannur",
        "Kasaragod", "Kollam", "Kottayam", "Kozhikode",
        "Malappuram", "Palakkad", "Pathanamthitta",
        "Thiruvananthapuram", "Thrissur", "Wayanad"
    ],

    "Madhya Pradesh": [
        "Agar Malwa", "Alirajpur", "Anuppur", "Ashoknagar",
        "Balaghat", "Barwani", "Betul", "Bhind",
        "Bhopal", "Burhanpur", "Chhatarpur", "Chhindwara",
        "Damoh", "Datia", "Dewas", "Dhar",
        "Dindori", "Guna", "Gwalior", "Harda",
        "Hoshangabad", "Indore", "Jabalpur", "Jhabua",
        "Katni", "Khandwa", "Khargone", "Mandla",
        "Mandsaur", "Morena", "Narsinghpur", "Neemuch",
        "Niwari", "Panna", "Raisen", "Rajgarh",
        "Ratlam", "Rewa", "Sagar", "Satna",
        "Sehore", "Seoni", "Shahdol", "Shajapur",
        "Sheopur", "Shivpuri", "Sidhi", "Singrauli",
        "Tikamgarh", "Ujjain", "Umaria", "Vidisha"
    ],

    "Maharashtra": [
        "Ahmednagar", "Akola", "Amravati", "Aurangabad",
        "Beed", "Bhandara", "Buldhana", "Chandrapur",
        "Dhule", "Gadchiroli", "Gondia", "Hingoli",
        "Jalgaon", "Jalna", "Kolhapur", "Latur",
        "Mumbai City", "Mumbai Suburban", "Nagpur",
        "Nanded", "Nandurbar", "Nashik", "Osmanabad",
        "Palghar", "Parbhani", "Pune", "Raigad",
        "Ratnagiri", "Sangli", "Satara", "Sindhudurg",
        "Solapur", "Thane", "Wardha", "Washim",
        "Yavatmal"
    ],

    "Manipur": [
        "Bishnupur", "Chandel", "Churachandpur", "Imphal East",
        "Imphal West", "Jiribam", "Kakching",
        "Kamjong", "Kangpokpi", "Noney",
        "Pherzawl", "Senapati", "Tamenglong",
        "Tengnoupal", "Thoubal", "Ukhrul"
    ],

    "Meghalaya": [
        "East Garo Hills", "East Jaintia Hills",
        "East Khasi Hills", "North Garo Hills",
        "Ri Bhoi", "South Garo Hills",
        "South West Garo Hills", "South West Khasi Hills",
        "West Garo Hills", "West Jaintia Hills",
        "West Khasi Hills"
    ],

    "Mizoram": [
        "Aizawl", "Champhai", "Hnahthial",
        "Khawzawl", "Kolasib", "Lawngtlai",
        "Lunglei", "Mamit", "Saiha",
        "Saitual", "Serchhip"
    ],

    "Nagaland": [
        "Chumoukedima", "Dimapur", "Kiphire",
        "Kohima", "Longleng", "Mokokchung",
        "Mon", "Niuland", "Noklak",
        "Peren", "Phek", "Shamator",
        "Tseminyu", "Tuensang", "Wokha",
        "Zunheboto"
    ],

    "Odisha": [
        "Angul", "Balangir", "Balasore", "Bargarh",
        "Bhadrak", "Boudh", "Cuttack", "Deogarh",
        "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur",
        "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal",
        "Kendrapara", "Kendujhar", "Khordha",
        "Koraput", "Malkangiri", "Mayurbhanj",
        "Nabarangpur", "Nayagarh", "Nuapada",
        "Puri", "Rayagada", "Sambalpur",
        "Subarnapur", "Sundargarh"
    ],

    "Punjab": [
        "Amritsar", "Barnala", "Bathinda", "Faridkot",
        "Fatehgarh Sahib", "Fazilka", "Ferozepur",
        "Gurdaspur", "Hoshiarpur", "Jalandhar",
        "Kapurthala", "Ludhiana", "Malerkotla",
        "Mansa", "Moga", "Mohali",
        "Muktsar", "Pathankot", "Patiala",
        "Rupnagar", "Sangrur", "Shaheed Bhagat Singh Nagar",
        "Tarn Taran"
    ],

    "Rajasthan": [
        "Ajmer", "Alwar", "Banswara", "Baran",
        "Barmer", "Bharatpur", "Bhilwara", "Bikaner",
        "Bundi", "Chittorgarh", "Churu", "Dausa",
        "Dholpur", "Dungarpur", "Ganganagar", "Hanumangarh",
        "Jaipur", "Jaisalmer", "Jalore", "Jhalawar",
        "Jhunjhunu", "Jodhpur", "Karauli", "Kota",
        "Nagaur", "Pali", "Pratapgarh", "Rajsamand",
        "Sawai Madhopur", "Sikar", "Sirohi", "Tonk",
        "Udaipur"
    ],

    "Sikkim": [
        "East Sikkim", "North Sikkim",
        "South Sikkim", "West Sikkim"
    ],

    "Tamil Nadu": [
        "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore",
        "Cuddalore", "Dharmapuri", "Dindigul", "Erode",
        "Kallakurichi", "Kanchipuram", "Kanniyakumari",
        "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai",
        "Nagapattinam", "Namakkal", "Nilgiris",
        "Perambalur", "Pudukkottai", "Ramanathapuram",
        "Ranipet", "Salem", "Sivaganga",
        "Tenkasi", "Thanjavur", "Theni",
        "Thiruvallur", "Thiruvarur", "Thoothukudi",
        "Tiruchirappalli", "Tirunelveli",
        "Tirupattur", "Tiruppur", "Tiruvannamalai",
        "Vellore", "Viluppuram", "Virudhunagar"
    ],

    "Telangana": [
        "Adilabad", "Bhadradri Kothagudem", "Hanamkonda",
        "Hyderabad", "Jagtial", "Jangaon",
        "Jayashankar Bhupalpally", "Jogulamba Gadwal",
        "Kamareddy", "Karimnagar", "Khammam",
        "Komaram Bheem", "Mahabubabad", "Mahabubnagar",
        "Mancherial", "Medak", "Medchal-Malkajgiri",
        "Mulugu", "Nagarkurnool", "Nalgonda",
        "Narayanpet", "Nirmal", "Nizamabad",
        "Peddapalli", "Rajanna Sircilla",
        "Ranga Reddy", "Sangareddy",
        "Siddipet", "Suryapet",
        "Vikarabad", "Wanaparthy",
        "Warangal", "Yadadri Bhuvanagiri"
    ],

    "Tripura": [
        "Dhalai", "Gomati", "Khowai",
        "North Tripura", "Sepahijala",
        "South Tripura", "Unakoti",
        "West Tripura"
    ],

    "Uttar Pradesh": [
        "Agra", "Aligarh", "Ambedkar Nagar", "Amethi",
        "Amroha", "Auraiya", "Ayodhya", "Azamgarh",
        "Baghpat", "Bahraich", "Ballia", "Balrampur",
        "Banda", "Barabanki", "Bareilly", "Basti",
        "Bhadohi", "Bijnor", "Budaun", "Bulandshahr",
        "Chandauli", "Chitrakoot", "Deoria", "Etah",
        "Etawah", "Farrukhabad", "Fatehpur", "Firozabad",
        "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur",
        "Gonda", "Gorakhpur", "Hamirpur", "Hapur",
        "Hardoi", "Hathras", "Jalaun", "Jaunpur",
        "Jhansi", "Kannauj", "Kanpur Dehat",
        "Kanpur Nagar", "Kasganj", "Kaushambi",
        "Kheri", "Kushinagar", "Lalitpur",
        "Lucknow", "Maharajganj", "Mahoba",
        "Mainpuri", "Mathura", "Mau",
        "Meerut", "Mirzapur", "Moradabad",
        "Muzaffarnagar", "Pilibhit", "Pratapgarh",
        "Prayagraj", "Raebareli", "Rampur",
        "Saharanpur", "Sambhal", "Sant Kabir Nagar",
        "Shahjahanpur", "Shamli", "Shravasti",
        "Siddharthnagar", "Sitapur", "Sonbhadra",
        "Sultanpur", "Unnao", "Varanasi"
    ],

    "Uttarakhand": [
        "Almora", "Bageshwar", "Chamoli",
        "Champawat", "Dehradun", "Haridwar",
        "Nainital", "Pauri Garhwal",
        "Pithoragarh", "Rudraprayag",
        "Tehri Garhwal", "Udham Singh Nagar",
        "Uttarkashi"
    ],

    "West Bengal": [
        "Alipurduar", "Bankura", "Birbhum",
        "Cooch Behar", "Dakshin Dinajpur",
        "Darjeeling", "Hooghly", "Howrah",
        "Jalpaiguri", "Jhargram",
        "Kalimpong", "Kolkata",
        "Malda", "Murshidabad",
        "Nadia", "North 24 Parganas",
        "Paschim Bardhaman", "Paschim Medinipur",
        "Purba Bardhaman", "Purba Medinipur",
        "Purulia", "South 24 Parganas",
        "Uttar Dinajpur"
    ]
}

# CHANGE: canonical categories for dropdowns + data generation (names reused verbatim)
CRIME_CATEGORIES: list[str] = [
    "Theft",
    "Robbery",
    "Burglary",
    "Assault",
    "Kidnapping",
    "Cyber Crime",
    "Fraud",
    "Drug Offense",
    "Domestic Violence",
    "Murder",
]


def _geo_lat_lon(state_name_norm: str, district_name_norm: str) -> Tuple[float, float]:
    base = STATE_CENTROIDS.get(state_name_norm, (22.9734, 78.6569))
    jlat, jlon = _stable_jitter_pair(f"{state_name_norm}|{district_name_norm}")
    lat = float(base[0] + jlat)
    lon = float(base[1] + jlon)
    # Clamp to reasonable India-ish bounds for demo safety.
    lat = float(np.clip(lat, 6.0, 37.0))
    lon = float(np.clip(lon, 68.0, 98.0))
    return lat, lon


# ============================================================
# 📊 DATA LOADING - SYNTHETIC (DEMO)
# ============================================================
@st.cache_data(show_spinner=False, ttl=3600)
def load_crime_data(seed: int = 42, schema_version: int = DATASET_SCHEMA_VERSION) -> pd.DataFrame:
    """
    Synthetic data generator for demo.
    Includes arrests for arrest_ratio and ML features.
    """
    _ = schema_version  # cache-busting/version marker for Streamlit cache
    rng = np.random.default_rng(seed)

    years = list(range(2017, 2023))  # 2017-2022 inclusive
    states = sorted(STATE_CENTROIDS.keys())

    data = []
    for year in years:
        for state in states:
            # CHANGE: use canonical DISTRICTS_BY_STATE and CRIME_CATEGORIES (no inline lists)
            for district in DISTRICTS_BY_STATE.get(state, []):
                for category in CRIME_CATEGORIES:
                    base_count = int(rng.integers(120, 1200))
                    # Trend injection: some states/districts gradually rise over time
                    trend_factor = 1.0 + 0.03 * (year - years[0])
                    hotspot_factor = 1.0
                    if state in ("Uttar Pradesh", "Maharashtra") and district in ("Lucknow", "Mumbai"):
                        hotspot_factor = 1.18 + 0.02 * (year - years[0])

                    category_factor = {
                        "Theft": 1.10,
                        "Robbery": 0.90,
                        "Burglary": 0.96,
                        "Assault": 0.98,
                        "Kidnapping": 0.42,
                        "Cyber Crime": 0.60,
                        "Fraud": 1.14,
                        "Drug Offense": 0.55,
                        "Domestic Violence": 0.82,
                        "Murder": 0.30,
                    }.get(category, 1.0)

                    noise = float(rng.uniform(0.82, 1.22))
                    count = int(base_count * trend_factor * hotspot_factor * category_factor * noise)
                    count = max(count, 0)

                    # Arrests: correlate with crime count but with variability; keep under/over ranges
                    arrest_rate = float(np.clip(rng.normal(0.33, 0.10), 0.05, 0.75))
                    # For certain categories, arrest rate tends to differ (demo)
                    if category in ("Murder", "Assault", "Kidnapping"):
                        arrest_rate = float(np.clip(arrest_rate + 0.10, 0.05, 0.85))
                    if category in ("Fraud", "Cyber Crime"):
                        arrest_rate = float(np.clip(arrest_rate - 0.05, 0.03, 0.70))
                    arrests = int(round(count * arrest_rate))

                    if category in ["Theft", "Robbery", "Burglary", "Fraud"]:
                        crime_type = "Property Crime"
                    elif category in ["Assault", "Kidnapping", "Domestic Violence", "Murder"]:
                        crime_type = "Violent Crime"
                    elif category in ["Cyber Crime", "Drug Offense"]:
                        crime_type = "Special Crime"
                    else:
                        crime_type = "Other Crime"
                    data.append(
                        {
                            "year": year,
                            "state_name": state,
                            "district_name": district,
                            "crime_count": count,
                            "arrests": arrests,
                            "category": category,
                            "crime_type": crime_type,
                        }
                    )

    df = pd.DataFrame(data)
    df["state_name_norm"] = df["state_name"].astype(str).apply(normalize_name)
    df["district_name_norm"] = df["district_name"].astype(str).apply(normalize_name)
    df["category"] = df["category"].astype(str).apply(normalize_name)
    df["crime_type"] = df["crime_type"].astype(str).apply(normalize_name)
    df["district_key"] = df["state_name_norm"] + " | " + df["district_name_norm"]

    # Geo coords
    lat_lon = df.apply(
        lambda r: _geo_lat_lon(str(r["state_name_norm"]), str(r["district_name_norm"])), axis=1
    )
    df["lat"] = [p[0] for p in lat_lon]
    df["lon"] = [p[1] for p in lat_lon]

    log_action("Data Loaded", details=f"Records: {len(df):,} | Years: {df['year'].min()}-{df['year'].max()}")
    return df.reset_index(drop=True)


# ============================================================
# 🧠 SESSION INITIALIZATION
# ============================================================
def init_session_state(df: pd.DataFrame) -> None:
    year_min = int(df["year"].min())
    year_max = int(df["year"].max())

    defaults = {
        "year_range": (year_min, year_max),
        "state": "ALL STATES",
        "district": "ALL DISTRICTS",
        "category": "ALL CATEGORIES",
        "sensitivity": 1.0,
        # Live pulse simulation controls
        "live_pulse": True,
        "pulse_intensity": 0.18,
        # Early warning thresholds
        "ew_pct": 50,
        "ew_abs": 10000,
        "ew_max": 50,
        # Forecast controls
        "forecast_strategy": "ARIMA (Advanced)",
        "forecast_years_ahead": 3,
        # Clustering controls
        "cluster_algo": "KMeans",
        "kmeans_k": 5,
        "dbscan_eps": 0.75,
        "dbscan_min_samples": 6,
        # Anomaly controls
        "anomaly_contamination": 0.08,  # base; sensitivity scales
        # Export hardening
        "export_row_cap": 100000,
        "export_guard_max_results": 200000,
        "export_allow_large": False,
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ============================================================
# ⚡ LIVE PULSE SIMULATION
# ============================================================
def apply_live_pulse(df_in: pd.DataFrame, enabled: bool, intensity: float, sensitivity: float) -> pd.DataFrame:
    """
    Live pulse simulation to emulate a streaming feed.
    Applies a controlled fluctuation to crime_count and arrests, strongest on latest year.
    """
    if df_in.empty:
        return df_in

    if not enabled:
        out = df_in.copy()
        out["pulse_multiplier"] = 1.0
        out["crime_count_pulsed"] = out["crime_count"].astype(int)
        out["arrests_pulsed"] = out["arrests"].astype(int)
        return out

    out = df_in.copy()
    year_max = int(out["year"].max())
    now = datetime.now(timezone.utc)
    phase = (now.timestamp() % 30.0) / 30.0  # 0..1
    # Create a deterministic-ish oscillation, scaled by sensitivity and intensity
    # Add small keyed noise by district_key to avoid uniform scaling.
    base_wave = np.sin(2 * np.pi * phase)

    def _mult(row: pd.Series) -> float:
        key = str(row.get("district_key", ""))
        h = _stable_hash_int(key) % 1000
        local = (h / 1000.0) - 0.5  # -0.5..0.5
        w = base_wave * (0.75 + 0.5 * local)
        yr_boost = 1.0 if int(row["year"]) == year_max else 0.35
        m = 1.0 + (w * float(intensity) * float(sensitivity) * yr_boost)
        return float(np.clip(m, 0.65, 1.55))

    out["pulse_multiplier"] = out.apply(_mult, axis=1)
    out["crime_count_pulsed"] = np.maximum(0, np.round(out["crime_count"] * out["pulse_multiplier"]).astype(int))
    # arrests should remain <= crimes; apply multiplier plus slight damping
    out["arrests_pulsed"] = np.minimum(
        out["crime_count_pulsed"],
        np.maximum(0, np.round(out["arrests"] * (0.92 + 0.08 * out["pulse_multiplier"])).astype(int)),
    )
    return out


# ============================================================
# 📡 FILTERS & CORE TRANSFORMS
# ============================================================
@st.cache_data(show_spinner=False, ttl=600)
def get_filtered_data(
    df: pd.DataFrame,
    year_range: Tuple[int, int],
    state: str,
    district: str,
    category: str,
) -> pd.DataFrame:
    filtered = df.copy()

    filtered = filtered[(filtered["year"] >= year_range[0]) & (filtered["year"] <= year_range[1])]

    if category != "ALL CATEGORIES":
        filtered = filtered[filtered["category"] == category]

    if state != "ALL STATES":
        filtered = filtered[filtered["state_name_norm"] == state]

    if state != "ALL STATES" and district != "ALL DISTRICTS":
        filtered = filtered[filtered["district_name_norm"] == district]

    return filtered


@st.cache_data(show_spinner=False, ttl=600)
def yearly_aggregate(df_in: pd.DataFrame, use_pulsed: bool = False) -> pd.DataFrame:
    if df_in.empty:
        return pd.DataFrame(columns=["year", "crime_count"])
    ccol = "crime_count_pulsed" if use_pulsed and "crime_count_pulsed" in df_in.columns else "crime_count"
    yearly = df_in.groupby("year", as_index=False)[ccol].sum().rename(columns={ccol: "crime_count"})
    return yearly.sort_values("year")


# ============================================================
# 🔥 RISK SCORING ENGINE (ALL YEARS + LATEST)
# ============================================================
RISK_COLOR_MAP = {
    "CRITICAL 🔴": "#ff4d00",  # blood orange
    "HIGH 🟠": "#e0af68",  # intelligence gold
    "MEDIUM 🟡": "#0066ff",  # deep cobalt
    "LOW 🟢": "#00f3ff",  # tactical cyan
}


def _classify_risk(score: float) -> str:
    if score >= 80:
        return "CRITICAL 🔴"
    if score >= 60:
        return "HIGH 🟠"
    if score >= 40:
        return "MEDIUM 🟡"
    return "LOW 🟢"


@st.cache_data(show_spinner=False, ttl=600)
def risk_scoring_engine_all_years(df_in: pd.DataFrame, use_pulsed: bool = False) -> pd.DataFrame:
    """
    Enhanced risk scoring across all years for each district.
    Includes:
      - total_crime
      - arrests
      - arrest_ratio
      - yoy_growth
      - lag_yoy_growth
      - volatility (std of yoy_growth per district)
      - risk_score + bucket
    """
    if df_in.empty:
        return pd.DataFrame()

    ccol = "crime_count_pulsed" if use_pulsed and "crime_count_pulsed" in df_in.columns else "crime_count"
    acol = "arrests_pulsed" if use_pulsed and "arrests_pulsed" in df_in.columns else "arrests"

    agg = (
        df_in.groupby(["year", "state_name_norm", "district_name_norm", "district_key"], as_index=False)
        .agg(
            total_crime=(ccol, "sum"),
            arrests=(acol, "sum"),
            lat=("lat", "mean"),
            lon=("lon", "mean"),
        )
        .sort_values(["state_name_norm", "district_name_norm", "year"])
    )

    agg["arrest_ratio"] = np.where(agg["total_crime"] > 0, agg["arrests"] / agg["total_crime"], 0.0)
    agg["yoy_growth"] = (
        agg.groupby(["state_name_norm", "district_name_norm"])["total_crime"].pct_change() * 100.0
    )
    agg["yoy_growth"] = agg["yoy_growth"].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    agg["lag_yoy_growth"] = (
        agg.groupby(["state_name_norm", "district_name_norm"])["yoy_growth"].shift(1).fillna(0.0)
    )

    volatility = (
        agg.groupby(["state_name_norm", "district_name_norm"], as_index=False)["yoy_growth"].std()
    ).rename(columns={"yoy_growth": "volatility"})
    volatility["volatility"] = volatility["volatility"].fillna(0.0)

    out = agg.merge(volatility, on=["state_name_norm", "district_name_norm"], how="left")

    out["volume_score"] = normalize_series(out["total_crime"])
    out["growth_score"] = normalize_series(out["yoy_growth"].clip(-100, 300))
    out["volatility_score"] = normalize_series(out["volatility"].clip(0, 200))

    out["risk_score"] = 0.55 * out["volume_score"] + 0.30 * out["growth_score"] + 0.15 * out["volatility_score"]
    out["risk_level"] = out["risk_score"].apply(_classify_risk)
    out["risk_color"] = out["risk_level"].map(RISK_COLOR_MAP).fillna("#00f3ff")

    return out


@st.cache_data(show_spinner=False, ttl=600)
def risk_scoring_engine_latest(df_in: pd.DataFrame, use_pulsed: bool = False) -> pd.DataFrame:
    if df_in.empty:
        return pd.DataFrame()
    all_years = risk_scoring_engine_all_years(df_in, use_pulsed=use_pulsed)
    if all_years.empty:
        return pd.DataFrame()
    y = int(all_years["year"].max())
    latest = all_years[all_years["year"] == y].copy()
    return latest.sort_values("risk_score", ascending=False)


# ============================================================
# 🚨 EARLY WARNING ENGINE (RULE-BASED SPIKES)
# ============================================================
@st.cache_data(show_spinner=False, ttl=300)
def early_warning_engine(
    df_in: pd.DataFrame,
    year_max: int,
    spike_threshold_pct: float = 35.0,
    spike_threshold_abs: float = 10000.0,
    use_pulsed: bool = False,
) -> pd.DataFrame:
    if df_in.empty:
        return pd.DataFrame()

    ccol = "crime_count_pulsed" if use_pulsed and "crime_count_pulsed" in df_in.columns else "crime_count"

    dy = (
        df_in.groupby(["state_name_norm", "district_name_norm", "district_key", "year"], as_index=False)[ccol]
        .sum()
        .rename(columns={ccol: "crime_count"})
        .sort_values(["state_name_norm", "district_name_norm", "year"])
    )

    dy["prev"] = dy.groupby(["state_name_norm", "district_name_norm"])["crime_count"].shift(1)
    dy["yoy_delta"] = dy["crime_count"] - dy["prev"]
    dy["yoy_pct"] = np.where(dy["prev"] > 0, (dy["yoy_delta"] / dy["prev"]) * 100.0, np.nan)

    latest = dy[dy["year"] == year_max].copy()
    if latest.empty:
        return pd.DataFrame()

    alerts = latest[
        (latest["yoy_pct"].fillna(0.0) >= float(spike_threshold_pct))
        | (latest["yoy_delta"].fillna(0.0) >= float(spike_threshold_abs))
    ].copy()

    if alerts.empty:
        return alerts

    alerts["alert"] = alerts["yoy_pct"].fillna(0.0).apply(lambda g: "Extreme Spike" if g >= 75 else "Emerging Spike")
    return alerts.sort_values(["yoy_pct", "yoy_delta"], ascending=False)


# ============================================================
# 🚓 PATROL PRIORITIZATION ENGINE
# ============================================================
@st.cache_data(show_spinner=False, ttl=300)
def patrol_prioritization_engine(alerts_df: pd.DataFrame, max_units: int = 20) -> pd.DataFrame:
    if alerts_df.empty:
        return pd.DataFrame()

    patrol = alerts_df.copy()

    max_abs = patrol["yoy_delta"].max() if patrol["yoy_delta"].max() is not None else 0
    max_pct = patrol["yoy_pct"].max() if patrol["yoy_pct"].max() is not None else 0
    max_abs = float(max_abs) if max_abs and max_abs > 0 else 1.0
    max_pct = float(max_pct) if max_pct and max_pct > 0 else 1.0

    patrol["abs_scaled"] = patrol["yoy_delta"].fillna(0.0) / max_abs
    patrol["pct_scaled"] = patrol["yoy_pct"].fillna(0.0) / max_pct
    patrol["risk_score"] = (0.60 * patrol["pct_scaled"]) + (0.40 * patrol["abs_scaled"])

    patrol = patrol.sort_values("risk_score", ascending=False).reset_index(drop=True)
    patrol["priority_rank"] = patrol.index + 1

    patrol["allocated_units"] = 0
    patrol.loc[patrol["priority_rank"] <= 5, "allocated_units"] = 2
    patrol.loc[(patrol["priority_rank"] > 5) & (patrol["priority_rank"] <= 15), "allocated_units"] = 1

    total_units = int(patrol["allocated_units"].sum())
    if total_units > int(max_units):
        scale = float(max_units) / float(total_units)
        patrol["allocated_units"] = np.floor(patrol["allocated_units"] * scale).astype(int)

    out = patrol[
        [
            "priority_rank",
            "state_name_norm",
            "district_name_norm",
            "year",
            "crime_count",
            "yoy_delta",
            "yoy_pct",
            "risk_score",
            "allocated_units",
            "alert",
        ]
    ].rename(
        columns={
            "state_name_norm": "State",
            "district_name_norm": "District",
            "crime_count": "Crimes (Latest Year)",
            "yoy_delta": "YoY Increase",
            "yoy_pct": "YoY % Increase",
            "risk_score": "Risk Score",
        }
    )
    return out


# ============================================================
# 🛡️ PREVENTION STRATEGY ENGINE
# ============================================================
@st.cache_data(show_spinner=False, ttl=600)
def prevention_strategy_engine(
    hotspots_df: pd.DataFrame, base_df: pd.DataFrame, year_min: int, year_max: int, use_pulsed: bool = False
) -> pd.DataFrame:
    if hotspots_df.empty or base_df.empty:
        return pd.DataFrame()

    ccol = "crime_count_pulsed" if use_pulsed and "crime_count_pulsed" in base_df.columns else "crime_count"

    dom = (
        base_df[(base_df["year"] >= year_min) & (base_df["year"] <= year_max)]
        .groupby(["state_name_norm", "district_name_norm", "district_key", "category"], as_index=False)
        .agg(total=(ccol, "sum"))
        .sort_values(["state_name_norm", "district_name_norm", "total"], ascending=[True, True, False])
    )
    dom_top = dom.groupby(["state_name_norm", "district_name_norm", "district_key"], as_index=False).head(1)
    dom_top = dom_top.rename(columns={"category": "dominant_category", "total": "dominant_category_total"})

    out = hotspots_df.merge(dom_top, on=["state_name_norm", "district_name_norm", "district_key"], how="left")

    def build_actions(level: str) -> str:
        if "CRITICAL" in str(level):
            return (
                "Primary: Saturation patrol on hotspot routes; rapid response teams; repeat-offender tracking.\n"
                "Community: Anonymous reporting drives; hotspot-area safety audits.\n"
                "Enforcement: Targeted operations; surveillance; case-backlog clearance."
            )
        if "HIGH" in str(level):
            return (
                "Primary: Increased patrol frequency; CCTV and lighting upgrades.\n"
                "Community: Local awareness campaigns.\n"
                "Enforcement: Targeted checks during peak hours."
            )
        if "MEDIUM" in str(level):
            return (
                "Primary: Periodic patrol/visibility; routine checks.\n"
                "Community: School/college prevention sessions.\n"
                "Enforcement: Intelligence-led monitoring."
            )
        return (
            "Primary: Maintain baseline patrol.\n"
            "Community: Prevention messaging.\n"
            "Enforcement: Monitor changes."
        )

    out["recommended_actions"] = out["risk_level"].apply(build_actions)
    out["generated_on"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    return out


# ============================================================
# 📝 EXECUTIVE REPORT ENGINE
# ============================================================
def executive_report_engine(
    hotspots_df: pd.DataFrame, warnings_df: pd.DataFrame, patrol_df: pd.DataFrame, filtered_df: pd.DataFrame
) -> str:
    lines = []
    lines.append("# CrimeWatch AI — Executive Intelligence Report")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("## Executive Summary")
    if filtered_df.empty:
        lines.append("- Total crimes (filtered): **0** (no rows under current filters).")
    else:
        lines.append(
            f"- Total crimes (filtered): **{int(filtered_df['crime_count'].sum()):,}** from "
            f"**{int(filtered_df['year'].min())}** to **{int(filtered_df['year'].max())}**."
        )
    lines.append("- Objective: identify hotspots, emerging threats, and prioritize proactive patrol and prevention measures.")
    lines.append("")

    lines.append("## Top Hotspots (Highest Risk Districts)")
    if hotspots_df.empty:
        lines.append("No hotspot data available.")
    else:
        for _, r in hotspots_df.head(10).iterrows():
            lines.append(
                f"- **{r['district_name_norm']}**, {r['state_name_norm']} — Risk **{r['risk_score']:.1f}** "
                f"({r['risk_level']}) | Latest-year crimes: **{int(r['total_crime']):,}**"
            )

    lines.append("")
    lines.append("## Emerging Alerts (Early Warning)")
    if warnings_df.empty:
        lines.append("No emerging spikes detected under current thresholds.")
    else:
        for _, r in warnings_df.head(10).iterrows():
            lines.append(
                f"- {r.get('alert','Spike')} — **{r['district_name_norm']}**, {r['state_name_norm']} — "
                f"YoY +{float(r['yoy_pct']):.1f}% (+{int(r['yoy_delta']):,})"
            )

    lines.append("")
    lines.append("## Patrol Prioritization Summary")
    if patrol_df.empty:
        lines.append("No patrol plan generated.")
    else:
        total_units = int(patrol_df["allocated_units"].sum()) if "allocated_units" in patrol_df.columns else 0
        lines.append(f"Total allocated units: **{total_units}**")
        top_alloc = patrol_df.sort_values("allocated_units", ascending=False).head(10)
        for _, r in top_alloc.iterrows():
            lines.append(
                f"- **{r['District']}**, {r['State']} — Units: **{int(r['allocated_units'])}** | "
                f"Risk Score: **{float(r['Risk Score']):.2f}**"
            )

    lines.append("")
    lines.append("## Recommended Actions")
    lines.append("- Deploy patrol and enforcement teams to CRITICAL/HIGH districts first.")
    lines.append("- Increase hotspot visibility and surveillance during peak periods.")
    lines.append("- Coordinate with community partners to reduce under-reporting and strengthen prevention.")
    lines.append("")
    return "\n".join(lines)


# ============================================================
# 📈 FORECASTING UPGRADE (ARIMA + LINEAR FALLBACK)
# ============================================================
def _safe_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = np.maximum(1e-9, np.abs(y_true))
    return float(np.mean(np.abs((y_true - y_pred) / denom)) * 100.0)


def forecast_linear(yearly: pd.DataFrame, years_ahead: int = 3) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Linear (Fast) forecast using np.polyfit.
    Provides backtest metrics computed in-sample.
    """
    meta: Dict[str, Any] = {"model": "Linear (Fast)", "status": "OK"}
    if yearly.empty or yearly["year"].nunique() < 2:
        return pd.DataFrame(), {**meta, "status": "INSUFFICIENT_DATA"}

    y = yearly.sort_values("year").copy()
    x = y["year"].astype(float).to_numpy()
    v = y["crime_count"].astype(float).to_numpy()

    # Fit degree-1 line
    coeff = np.polyfit(x, v, 1)
    p = np.poly1d(coeff)

    # In-sample predictions for quality metrics
    v_hat = p(x)
    v_hat = np.maximum(0.0, v_hat)

    mae = float(np.mean(np.abs(v - v_hat)))
    mape = _safe_mape(v, v_hat)

    # R2
    ss_res = float(np.sum((v - v_hat) ** 2))
    ss_tot = float(np.sum((v - np.mean(v)) ** 2)) if len(v) > 1 else 0.0
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    meta.update({"mae": mae, "mape": mape, "r2": r2})

    last_year = int(y["year"].max())
    future_years = list(range(last_year + 1, last_year + int(years_ahead) + 1))
    future_vals = np.maximum(0.0, p(np.array(future_years, dtype=float)))

    # Simple heuristic CI (not statistical): +/- 1.96 * std(residual)
    resid = v - v_hat
    sigma = float(np.std(resid)) if len(resid) > 1 else 0.0
    lower = np.maximum(0.0, future_vals - 1.96 * sigma)
    upper = np.maximum(0.0, future_vals + 1.96 * sigma)

    fdf = pd.DataFrame({"year": future_years, "crime_count": future_vals, "lower": lower, "upper": upper, "type": "Forecast"})
    meta.update({"ci": True})
    return fdf, meta


def forecast_arima_advanced(yearly: pd.DataFrame, years_ahead: int = 3) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    ARIMA (Advanced) forecast.
    Uses statsmodels ARIMA if available. If unavailable, caller should fallback.
    """
    meta: Dict[str, Any] = {"model": "ARIMA (Advanced)", "status": "OK"}
    if yearly.empty or yearly["year"].nunique() < 4:
        return pd.DataFrame(), {**meta, "status": "INSUFFICIENT_DATA"}

    # Import inside function (no try/except around import lines).
    from statsmodels.tsa.arima.model import ARIMA

    y = yearly.sort_values("year").copy()
    v = y["crime_count"].astype(float).to_numpy()

    # ARIMA on values only; years provide alignment and display.
    model = ARIMA(v, order=(1, 1, 1))
    fit = model.fit()

    # In-sample (levels) forecast for metrics: get fittedvalues are for differenced series; use predict
    pred_in = fit.predict(start=0, end=len(v) - 1)
    pred_in = np.maximum(0.0, np.asarray(pred_in, dtype=float))

    mae = float(np.mean(np.abs(v - pred_in)))
    mape = _safe_mape(v, pred_in)
    aic = float(getattr(fit, "aic", np.nan))
    bic = float(getattr(fit, "bic", np.nan))
    meta.update({"mae": mae, "mape": mape, "aic": aic, "bic": bic})

    last_year = int(y["year"].max())
    future_years = list(range(last_year + 1, last_year + int(years_ahead) + 1))

    fc = fit.get_forecast(steps=int(years_ahead))
    mean = np.maximum(0.0, np.asarray(fc.predicted_mean, dtype=float))
    ci = fc.conf_int(alpha=0.05)
    # conf_int columns vary; assume [lower, upper]
    lower = np.maximum(0.0, np.asarray(ci.iloc[:, 0], dtype=float))
    upper = np.maximum(0.0, np.asarray(ci.iloc[:, 1], dtype=float))

    fdf = pd.DataFrame({"year": future_years, "crime_count": mean, "lower": lower, "upper": upper, "type": "Forecast"})
    meta.update({"ci": True})
    return fdf, meta


def run_forecast(yearly: pd.DataFrame, strategy: str, years_ahead: int) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Strategy selector with graceful fallback to Linear.
    Shows model used + quality metrics.
    """
    years_ahead = int(np.clip(int(years_ahead), 1, 10))
    if yearly.empty:
        return pd.DataFrame(), {"model_used": "None", "status": "EMPTY"}

    if strategy == "ARIMA (Advanced)":
        if not _has_module("statsmodels"):
            fdf, meta = forecast_linear(yearly, years_ahead=years_ahead)
            meta.update(
                {
                    "model_used": "Linear (Fast) (Fallback: statsmodels missing)",
                    "fallback": True,
                    "fallback_reason": "statsmodels not installed",
                }
            )
            return fdf, meta
        try:
            fdf, meta = forecast_arima_advanced(yearly, years_ahead=years_ahead)
            if fdf.empty and meta.get("status") != "OK":
                # Fallback if insufficient data
                ldf, lmeta = forecast_linear(yearly, years_ahead=years_ahead)
                lmeta.update(
                    {
                        "model_used": "Linear (Fast) (Fallback: insufficient ARIMA data)",
                        "fallback": True,
                        "fallback_reason": meta.get("status"),
                    }
                )
                return ldf, lmeta
            meta.update({"model_used": "ARIMA (Advanced)", "fallback": False})
            return fdf, meta
        except Exception as e:
            ldf, lmeta = forecast_linear(yearly, years_ahead=years_ahead)
            lmeta.update(
                {
                    "model_used": "Linear (Fast) (Fallback: ARIMA runtime failure)",
                    "fallback": True,
                    "fallback_reason": str(e)[:200],
                }
            )
            return ldf, lmeta
    else:
        fdf, meta = forecast_linear(yearly, years_ahead=years_ahead)
        meta.update({"model_used": "Linear (Fast)", "fallback": False})
        return fdf, meta


# ============================================================
# 🧨 ANOMALY DETECTION ENGINE (IsolationForest)
# ============================================================
@st.cache_data(show_spinner=False, ttl=300)
def build_anomaly_features(risk_all_years: pd.DataFrame) -> pd.DataFrame:
    """
    Build anomaly features from district-level risk table.
    Features:
      - incidents (total_crime)
      - risk_score
      - arrest_ratio
      - yoy_growth
      - lag_yoy_growth
    """
    if risk_all_years.empty:
        return pd.DataFrame()

    year_max = int(risk_all_years["year"].max())
    latest = risk_all_years[risk_all_years["year"] == year_max].copy()
    if latest.empty:
        return pd.DataFrame()

    cols = [
        "state_name_norm",
        "district_name_norm",
        "district_key",
        "year",
        "total_crime",
        "arrests",
        "arrest_ratio",
        "risk_score",
        "risk_level",
        "yoy_growth",
        "lag_yoy_growth",
        "volatility",
        "lat",
        "lon",
        "risk_color",
    ]
    for c in cols:
        if c not in latest.columns:
            latest[c] = np.nan

    return latest[cols].copy()


def anomaly_detection_isolation_forest(
    feat_df: pd.DataFrame,
    contamination: float = 0.08,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    IsolationForest anomaly detection. Returns:
      - anomaly_score (higher = more anomalous)
      - anomaly_flag (True/False)
    """
    meta: Dict[str, Any] = {"engine": "IsolationForest", "status": "OK"}

    if feat_df.empty:
        return pd.DataFrame(), {**meta, "status": "EMPTY"}

    out = feat_df.copy()
    out["anomaly_score"] = np.nan
    out["anomaly_flag"] = False

    if not _has_module("sklearn"):
        meta.update({"status": "SKLEARN_MISSING"})
        return out, meta

    # Import inside function (no try/except around import lines).
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import RobustScaler

    features = ["total_crime", "risk_score", "arrest_ratio", "yoy_growth", "lag_yoy_growth", "volatility"]
    X = out[features].replace([np.inf, -np.inf], np.nan).fillna(0.0).astype(float).to_numpy()

    # Scale for stability
    scaler = RobustScaler()
    Xs = scaler.fit_transform(X)

    cont = float(np.clip(contamination, 0.01, 0.25))
    model = IsolationForest(
        n_estimators=300,
        contamination=cont,
        random_state=int(random_state),
        n_jobs=-1,
    )
    model.fit(Xs)

    # decision_function: higher = more normal. invert for anomaly_score
    decision = model.decision_function(Xs)
    out["anomaly_score"] = (-decision).astype(float)
    preds = model.predict(Xs)  # -1 anomalies
    out["anomaly_flag"] = preds == -1

    meta.update(
        {
            "contamination": cont,
            "anomalies": int(out["anomaly_flag"].sum()),
            "rows": int(len(out)),
        }
    )
    return out, meta


# ============================================================
# 🧭 CLUSTERING UPGRADE (KMeans + DBSCAN)
# ============================================================
@st.cache_data(show_spinner=False, ttl=600)
def build_cluster_points(risk_latest: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare district points for geo clustering:
      - lat/lon
      - risk_score
      - total_crime
      - labels
    """
    if risk_latest.empty:
        return pd.DataFrame()
    cols = ["state_name_norm", "district_name_norm", "district_key", "lat", "lon", "risk_score", "risk_level", "total_crime"]
    out = risk_latest.copy()
    for c in cols:
        if c not in out.columns:
            out[c] = np.nan
    out = out[cols].dropna(subset=["lat", "lon"]).copy()
    return out


def run_clustering(
    points_df: pd.DataFrame,
    algorithm: str = "KMeans",
    kmeans_k: int = 5,
    dbscan_eps: float = 0.75,
    dbscan_min_samples: int = 6,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Returns:
      - points with cluster_id and cluster_label
      - centroids df (only for KMeans)
      - meta
    """
    meta: Dict[str, Any] = {"algorithm": algorithm, "status": "OK"}
    if points_df.empty:
        return pd.DataFrame(), pd.DataFrame(), {**meta, "status": "EMPTY"}

    out = points_df.copy()
    out["cluster_id"] = -1
    out["cluster_label"] = "UNCLUSTERED"

    centroids = pd.DataFrame()

    if not _has_module("sklearn"):
        meta.update({"status": "SKLEARN_MISSING"})
        return out, centroids, meta

    # Import inside function (no try/except around import lines).
    from sklearn.cluster import DBSCAN, KMeans
    from sklearn.preprocessing import StandardScaler

    # Features: geo + risk for better grouping
    X = out[["lat", "lon", "risk_score"]].fillna(0.0).astype(float).to_numpy()
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    if algorithm == "KMeans":
        k = int(np.clip(int(kmeans_k), 2, min(15, len(out))))
        km = KMeans(n_clusters=k, random_state=int(random_state), n_init="auto")
        labels = km.fit_predict(Xs)
        out["cluster_id"] = labels
        out["cluster_label"] = out["cluster_id"].apply(lambda c: f"CL-{int(c):02d}")

        centers_scaled = km.cluster_centers_
        centers = scaler.inverse_transform(centers_scaled)
        centroids = pd.DataFrame(centers, columns=["lat", "lon", "risk_score_center"])
        centroids["cluster_id"] = np.arange(len(centroids))
        centroids["cluster_label"] = centroids["cluster_id"].apply(lambda c: f"CL-{int(c):02d}")
        meta.update({"k": k, "clusters": int(k), "noise": 0})
        return out, centroids, meta

    # DBSCAN
    eps = float(np.clip(float(dbscan_eps), 0.10, 3.00))
    ms = int(np.clip(int(dbscan_min_samples), 3, 50))
    db = DBSCAN(eps=eps, min_samples=ms)
    labels = db.fit_predict(Xs)
    out["cluster_id"] = labels
    out["cluster_label"] = out["cluster_id"].apply(lambda c: "NOISE" if int(c) == -1 else f"CL-{int(c):02d}")
    meta.update(
        {
            "eps": eps,
            "min_samples": ms,
            "clusters": int(len(set(labels)) - (1 if -1 in labels else 0)),
            "noise": int(np.sum(labels == -1)),
        }
    )
    return out, centroids, meta


def cluster_map_figure(points_clustered: pd.DataFrame, centroids: pd.DataFrame, algorithm: str) -> go.Figure:
    if points_clustered.empty:
        fig = go.Figure()
        fig.update_layout(title="Cluster Map (No Data)")
        return apply_tactical_theme(fig)

    fig = px.scatter_mapbox(
        points_clustered,
        lat="lat",
        lon="lon",
        color="cluster_label",
        size="total_crime",
        size_max=28,
        zoom=3.4,
        center={"lat": 22.9734, "lon": 78.6569},
        mapbox_style="carto-darkmatter",
        hover_name="district_name_norm",
        hover_data={
            "state_name_norm": True,
            "risk_score": ":.1f",
            "risk_level": True,
            "total_crime": ":,.0f",
            "lat": False,
            "lon": False,
        },
        title=f"Hotspot Clustering Map — {algorithm}",
    )

    # Add centroid markers for KMeans
    if algorithm == "KMeans" and not centroids.empty:
        fig.add_trace(
            go.Scattermapbox(
                lat=centroids["lat"],
                lon=centroids["lon"],
                mode="markers+text",
                marker=dict(size=14, color="#00f3ff"),
                text=centroids["cluster_label"],
                textposition="top center",
                name="Centroids",
                hovertext=centroids["cluster_label"],
                hoverinfo="text",
            )
        )

    fig.update_layout(height=650, margin=dict(r=0, t=70, l=0, b=0))
    return apply_tactical_theme(fig)


# ============================================================
# 🧠 SUPERVISED RISK PREDICTION (RandomForest / XGBoost if available)
# ============================================================
@st.cache_data(show_spinner=False, ttl=600)
def build_supervised_dataset(risk_all_years: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, Dict[str, Any]]:
    """
    Train dataset:
      Features at year t -> label risk bucket at year t+1
    """
    meta: Dict[str, Any] = {"status": "OK"}

    if risk_all_years.empty or risk_all_years["year"].nunique() < 3:
        return pd.DataFrame(), pd.Series(dtype=str), {**meta, "status": "INSUFFICIENT_DATA"}

    df = risk_all_years.sort_values(["district_key", "year"]).copy()

    # label is next year's risk_level
    df["label_next"] = df.groupby("district_key")["risk_level"].shift(-1)
    train = df.dropna(subset=["label_next"]).copy()
    if train.empty:
        return pd.DataFrame(), pd.Series(dtype=str), {**meta, "status": "NO_LABELS"}

    features = [
        "total_crime",
        "arrests",
        "arrest_ratio",
        "yoy_growth",
        "lag_yoy_growth",
        "volatility",
        "risk_score",
        "lat",
        "lon",
    ]

    for c in features:
        if c not in train.columns:
            train[c] = 0.0

    X = train[features].replace([np.inf, -np.inf], np.nan).fillna(0.0).astype(float)
    y = train["label_next"].astype(str)

    meta.update({"rows": int(len(train)), "classes": sorted(y.unique().tolist())})
    return X, y, meta


def train_risk_predictor(
    X: pd.DataFrame,
    y: pd.Series,
    model_preference: str = "Auto",
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Trains a supervised model to predict next-period risk bucket.
    Shows accuracy + classification report + confusion matrix + feature importances.
    """
    result: Dict[str, Any] = {"status": "OK", "model_used": "None"}

    if X.empty or y.empty:
        return {**result, "status": "EMPTY"}

    if y.nunique() < 2 or len(y) < 60:
        return {
            **result,
            "status": "INSUFFICIENT_DATA",
            "reason": f"Need >=60 samples and >=2 classes (have {len(y)} samples, {y.nunique()} classes).",
        }

    if not _has_module("sklearn"):
        return {**result, "status": "SKLEARN_MISSING"}

    # Import inside function (no try/except around import lines).
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
    from sklearn.ensemble import RandomForestClassifier

    # Optional XGBoost
    use_xgb = False
    if model_preference in ("Auto", "XGBoost") and _has_module("xgboost"):
        use_xgb = True

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.22, random_state=int(random_state), stratify=y
    )

    model = None
    model_used = "RandomForest"
    if use_xgb:
        # Import inside function (no try/except around import lines).
        from xgboost import XGBClassifier

        model_used = "XGBoost"
        model = XGBClassifier(
            n_estimators=400,
            max_depth=5,
            learning_rate=0.06,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.0,
            random_state=int(random_state),
            n_jobs=-1,
            objective="multi:softprob",
            eval_metric="mlogloss",
        )
    else:
        model = RandomForestClassifier(
            n_estimators=400,
            max_depth=None,
            random_state=int(random_state),
            n_jobs=-1,
            class_weight="balanced_subsample",
        )

    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    acc = float(accuracy_score(y_test, pred))
    report = classification_report(y_test, pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_test, pred, labels=sorted(y.unique().tolist()))

    # Feature importance
    importances = None
    if hasattr(model, "feature_importances_"):
        importances = np.asarray(getattr(model, "feature_importances_"), dtype=float)

    result.update(
        {
            "status": "OK",
            "model_used": model_used,
            "accuracy": acc,
            "report": report,
            "labels": sorted(y.unique().tolist()),
            "confusion_matrix": cm,
            "feature_names": X.columns.tolist(),
            "feature_importances": importances,
        }
    )
    return result


def figure_confusion_matrix(cm: np.ndarray, labels: list[str], title: str) -> go.Figure:
    fig = px.imshow(
        cm,
        x=labels,
        y=labels,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues",
        title=title,
    )
    fig.update_xaxes(title="Predicted")
    fig.update_yaxes(title="Actual")
    fig.update_layout(height=420)
    return apply_tactical_theme(fig)


def figure_feature_importances(feature_names: list[str], importances: np.ndarray, title: str) -> go.Figure:
    if importances is None or len(importances) == 0:
        fig = go.Figure()
        fig.update_layout(title=title)
        return apply_tactical_theme(fig)

    df_imp = pd.DataFrame({"feature": feature_names, "importance": importances})
    df_imp = df_imp.sort_values("importance", ascending=False).head(15)
    fig = px.bar(df_imp, x="importance", y="feature", orientation="h", title=title)
    fig.update_layout(height=430)
    return apply_tactical_theme(fig)


# ============================================================
# 🧪 MODEL GOVERNANCE PANEL UTILITIES
# ============================================================
def psi(expected: np.ndarray, actual: np.ndarray, bins: int = 8) -> float:
    """
    Population Stability Index (PSI) for drift signal.
    Returns scalar PSI; higher implies greater shift.
    """
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)

    if expected.sum() <= 0 or actual.sum() <= 0:
        return 0.0

    expected = expected / expected.sum()
    actual = actual / actual.sum()

    # Smooth to avoid log(0)
    eps = 1e-6
    expected = np.clip(expected, eps, 1.0)
    actual = np.clip(actual, eps, 1.0)

    return float(np.sum((actual - expected) * np.log(actual / expected)))


@st.cache_data(show_spinner=False, ttl=600)
def drift_checks_by_state(df_in: pd.DataFrame, use_pulsed: bool = False) -> pd.DataFrame:
    """
    Basic drift checks by state distribution across time windows.
    Compares first half vs second half in current filter period.
    """
    if df_in.empty or df_in["year"].nunique() < 2:
        return pd.DataFrame()

    ccol = "crime_count_pulsed" if use_pulsed and "crime_count_pulsed" in df_in.columns else "crime_count"

    years = sorted(df_in["year"].unique().tolist())
    mid = years[len(years) // 2]
    a = df_in[df_in["year"] <= mid].groupby("state_name_norm")[ccol].sum()
    b = df_in[df_in["year"] > mid].groupby("state_name_norm")[ccol].sum()

    states = sorted(set(a.index.tolist()) | set(b.index.tolist()))
    expected = np.array([float(a.get(s, 0.0)) for s in states], dtype=float)
    actual = np.array([float(b.get(s, 0.0)) for s in states], dtype=float)
    overall_psi = psi(expected, actual)

    df_out = pd.DataFrame({"State": states, "First_Window": expected, "Second_Window": actual})
    df_out["First_%"] = np.where(expected.sum() > 0, (df_out["First_Window"] / expected.sum()) * 100.0, 0.0)
    df_out["Second_%"] = np.where(actual.sum() > 0, (df_out["Second_Window"] / actual.sum()) * 100.0, 0.0)
    df_out["Delta_%"] = df_out["Second_%"] - df_out["First_%"]
    df_out = df_out.sort_values("Delta_%", ascending=False)
    df_out.attrs["overall_psi"] = overall_psi
    df_out.attrs["mid_year"] = mid
    return df_out


def governance_alert_metrics(spikes_df: pd.DataFrame, anomalies_df: pd.DataFrame) -> Dict[str, Any]:
    """
    If we treat rule-based spikes as pseudo-labels, compute precision/recall for anomaly flags.
    This is NOT ground truth; it is a governance proxy metric.
    """
    out: Dict[str, Any] = {"status": "OK", "precision": np.nan, "recall": np.nan, "f1": np.nan}

    if spikes_df.empty or anomalies_df.empty:
        out["status"] = "EMPTY"
        return out

    spikes = set(spikes_df["district_key"].astype(str).tolist()) if "district_key" in spikes_df.columns else set()
    anomalies = anomalies_df[anomalies_df.get("anomaly_flag", False)].copy()
    preds = set(anomalies["district_key"].astype(str).tolist()) if "district_key" in anomalies.columns else set()

    if not spikes and not preds:
        out.update({"precision": 1.0, "recall": 1.0, "f1": 1.0})
        return out

    tp = len(spikes & preds)
    fp = len(preds - spikes)
    fn = len(spikes - preds)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    out.update({"precision": float(precision), "recall": float(recall), "f1": float(f1), "tp": tp, "fp": fp, "fn": fn})
    return out


# ============================================================
# 🔒 EXPORT & SECURITY HARDENING
# ============================================================
def _export_audit_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    token = secrets.token_hex(4).upper()
    return f"{ts}-{token}"


def validate_export_request(filtered_df: pd.DataFrame, row_cap: int, guard_max_results: int, allow_large: bool) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Security check for export:
      - row cap
      - optional guard on search result count
    """
    meta = {"status": "OK", "row_cap": int(row_cap), "guard_max_results": int(guard_max_results), "truncated": False}
    if filtered_df.empty:
        return filtered_df, {**meta, "status": "EMPTY"}

    n = int(len(filtered_df))
    if n > int(guard_max_results) and not allow_large:
        meta.update({"status": "GUARD_BLOCK", "reason": f"Results {n:,} exceed guard {guard_max_results:,}. Enable override to export."})
        return filtered_df.head(0), meta

    if n > int(row_cap):
        meta.update({"truncated": True, "status": "TRUNCATED", "reason": f"Rows capped at {row_cap:,} (had {n:,})."})
        return filtered_df.head(int(row_cap)).copy(), meta

    return filtered_df.copy(), meta


# ============================================================
# 🎛️ UI RENDERING
# ============================================================
def render_header() -> None:
    st.markdown(
        """
        <div class="clean-header-container">
          <div class="header-left">
            <span class="ai-badge">🤖</span>
            <div>
              <div class="main-title">CrimeWatch AI • Sovereign Intelligence HUD</div>
              <div class="subtitle">Futuristic Mission-Critical Intelligence Platform | Advanced Predictive Analytics</div>
            </div>
          </div>
          <div style="text-align:center;">
            <span class="mission-tag">MISSION: TRANSFORM RAW CRIME DATA INTO ACTIONABLE INTELLIGENCE</span>
          </div>
          <div class="status-indicator">
            <span class="status-dot"></span>
            <span class="status-text">ML ENGINE: SYNCHRONIZED</span>
          </div>
        </div>
        <div class="header-divider"></div>
        """,
        unsafe_allow_html=True,
    )


def render_control_panel(df: pd.DataFrame) -> None:
    st.markdown('<div class="control-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Intelligence Control Panel</div>', unsafe_allow_html=True)

    # Quick filter presets
    YEAR_MIN_GLOBAL = int(df["year"].min())
    YEAR_MAX_GLOBAL = int(df["year"].max())

    preset_filters = {
        "Last 5 Years": (max(YEAR_MIN_GLOBAL, YEAR_MAX_GLOBAL - 4), YEAR_MAX_GLOBAL),
        "Decade View": (max(YEAR_MIN_GLOBAL, YEAR_MAX_GLOBAL - 9), YEAR_MAX_GLOBAL),
        "Full Dataset": (YEAR_MIN_GLOBAL, YEAR_MAX_GLOBAL),
    }

    st.markdown('<div class="quick-filter-container">', unsafe_allow_html=True)
    st.markdown('<div class="quick-filter-title">Quick Filter Presets</div>', unsafe_allow_html=True)

    cols = st.columns(len(preset_filters))
    for idx, (name, year_range) in enumerate(preset_filters.items()):
        with cols[idx]:
            if st.button(name, key=f"preset_{idx}", use_container_width=True):
                st.session_state.year_range = year_range
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    col_year, col_state, col_district, col_category, col_sensitivity = st.columns(5)

    with col_year:
        st.markdown('<div class="filter-label">📅 Operational Period</div>', unsafe_allow_html=True)
        years = sorted(df["year"].unique().tolist())
        st.session_state.year_range = st.slider(
            "Year Range",
            min_value=int(min(years)),
            max_value=int(max(years)),
            value=tuple(st.session_state.year_range),
            step=1,
            key="year_range_slider",
            label_visibility="collapsed",
        )

    with col_state:
        st.markdown('<div class="filter-label">📍 State Sector</div>', unsafe_allow_html=True)
        # CHANGE: state dropdown sourced from STATE_CENTROIDS keys ONLY (canonical, cache-safe)
        states = ["ALL STATES"] + sorted(list(STATE_CENTROIDS.keys()))
        # Ensure value remains valid
        if st.session_state.state not in states:
            st.session_state.state = "ALL STATES"
        st.session_state.state = st.selectbox(
            "State",
            states,
            index=states.index(st.session_state.state),
            key="state_selector",
            label_visibility="collapsed",
        )

    with col_district:
        st.markdown('<div class="filter-label">🎯 District Zone</div>', unsafe_allow_html=True)
        if st.session_state.state != "ALL STATES":
            # CHANGE: district dropdown sourced from DISTRICTS_BY_STATE[selected_state] ONLY
            districts = ["ALL DISTRICTS"] + [normalize_name(d) for d in DISTRICTS_BY_STATE.get(st.session_state.state, [])]
            if st.session_state.district not in districts:
                st.session_state.district = "ALL DISTRICTS"
            st.session_state.district = st.selectbox(
                "District",
                districts,
                index=districts.index(st.session_state.district),
                key="district_selector",
                label_visibility="collapsed",
            )
        else:
            st.session_state.district = "ALL DISTRICTS"
            st.selectbox(
                "District",
                ["SELECT STATE FIRST"],
                index=0,
                disabled=True,
                key="district_disabled",
                label_visibility="collapsed",
            )

    with col_category:
        st.markdown('<div class="filter-label">🔍 Crime Category</div>', unsafe_allow_html=True)
        # CHANGE: category dropdown sourced from CRIME_CATEGORIES ONLY
        categories = ["ALL CATEGORIES"] + [normalize_name(c) for c in CRIME_CATEGORIES]
        if st.session_state.category not in categories:
            st.session_state.category = "ALL CATEGORIES"
        st.session_state.category = st.selectbox(
            "Category",
            categories,
            index=categories.index(st.session_state.category),
            key="category_selector",
            label_visibility="collapsed",
        )

    with col_sensitivity:
        st.markdown('<div class="filter-label">⚙️ AI Sensitivity</div>', unsafe_allow_html=True)
        st.session_state.sensitivity = st.slider(
            "Sensitivity",
            min_value=0.1,
            max_value=2.0,
            value=float(st.session_state.sensitivity),
            step=0.1,
            key="sensitivity_slider",
            label_visibility="collapsed",
            help="Higher values increase anomaly detection sensitivity",
        )

    # Live pulse controls (required main flow)
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.session_state.live_pulse = st.toggle("🔴 Live Pulse", value=bool(st.session_state.live_pulse), help="Simulate live feed fluctuations.")
    with c2:
        st.session_state.pulse_intensity = st.slider(
            "Pulse Intensity",
            min_value=0.00,
            max_value=0.50,
            value=float(st.session_state.pulse_intensity),
            step=0.01,
            help="Controls amplitude of live pulse.",
        )
    with c3:
        st.caption("Live pulse affects latest-year signals most; export is from filtered rows with guards.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_empty_state(df: pd.DataFrame, filtered_df: pd.DataFrame) -> None:
    st.error("🚨 TACTICAL ALERT: No intelligence data available for selected filters")
    st.info(
        f"""
**OPERATIONAL GUIDANCE**:
- Start with "ALL STATES" and "ALL CATEGORIES" to establish baseline
- Verify year range matches available data ({int(df['year'].min())} to {int(df['year'].max())})
- Check district selection only after state is selected
"""
    )
    st.subheader("📊 INTELLIGENCE ASSETS AVAILABLE")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Records", f"{len(df):,}")
    col2.metric("Year Range", f"{int(df['year'].min())}–{int(df['year'].max())}")
    col3.metric("States", f"{df['state_name_norm'].nunique()}")
    col4.metric("Districts", f"{df['district_key'].nunique():,}")
    st.stop()


def render_briefing(
    risk_latest: pd.DataFrame,
    forecast_meta: Dict[str, Any],
    anomaly_meta: Dict[str, Any],
    spikes_df: pd.DataFrame,
) -> None:
    critical_count = int((risk_latest["risk_level"].astype(str).str.contains("CRITICAL")).sum()) if not risk_latest.empty else 0
    spikes_count = int(len(spikes_df)) if spikes_df is not None and not spikes_df.empty else 0
    anom_count = int(anomaly_meta.get("anomalies", 0)) if anomaly_meta else 0

    model_used = str(forecast_meta.get("model_used", "—"))
    mape = forecast_meta.get("mape", None)
    mape_str = f"{float(mape):.1f}%" if mape is not None and not (isinstance(mape, float) and np.isnan(mape)) else "—"

    st.markdown(
        f"""
<div class="briefing-container">
  <div class="briefing-col">
    <div class="briefing-title">Data Integrity</div>
    <div class="briefing-content">
      <strong>Under-reporting:</strong> Rural districts can show materially lower reporting — apparent "low crime" may reflect reporting gaps<br><br>
      <strong>Population not adjusted:</strong> Risk scores are NOT per-capita — high-volume urban districts may have lower per-capita rates
    </div>
  </div>
  <div class="briefing-col">
    <div class="briefing-title">Temporal & Model Logic</div>
    <div class="briefing-content">
      <strong>Forecast engine:</strong> {model_used}<br>
      <strong>Forecast quality:</strong> MAPE {mape_str}<br><br>
      <strong>Alerts:</strong> {spikes_count} spike(s) | <strong>Anomalies:</strong> {anom_count} flag(s)
    </div>
  </div>
  <div class="briefing-col">
    <div class="briefing-title">Operational Protocol</div>
    <div class="briefing-content">
      <strong>Required action:</strong> Cross-verify CRITICAL flags with local SP before operational allocation.<br><br>
      <strong>Live risk:</strong> {critical_count} CRITICAL district(s) under current filters.
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_warning_panel(
    filtered_df: pd.DataFrame,
    spikes_df: pd.DataFrame,
    anomalies_df: pd.DataFrame,
    forecast_meta: Dict[str, Any],
) -> None:
    total = int(filtered_df["crime_count"].sum()) if not filtered_df.empty else 0
    y_min = int(filtered_df["year"].min()) if not filtered_df.empty else 0
    y_max = int(filtered_df["year"].max()) if not filtered_df.empty else 0
    spikes_cnt = int(len(spikes_df)) if spikes_df is not None and not spikes_df.empty else 0
    anom_cnt = int(anomalies_df["anomaly_flag"].sum()) if anomalies_df is not None and not anomalies_df.empty and "anomaly_flag" in anomalies_df.columns else 0

    fallback = bool(forecast_meta.get("fallback", False))
    fallback_reason = str(forecast_meta.get("fallback_reason", ""))

    note = ""
    if fallback:
        note = f"<br><strong>Forecast fallback:</strong> {fallback_reason}"

    st.markdown(
        f"""
<div class="warning-panel">
  <div class="warning-title">Critical Intelligence Limitations</div>
  <div class="warning-content">
    This system reflects <strong>reported</strong> incidents within current filters ({y_min}–{y_max}).
    Automated signals are <strong>decision support</strong> only; enforce human review for deployments.<br><br>
    <strong>Signals:</strong> {spikes_cnt} spike alert(s) detected; {anom_cnt} anomaly flag(s) detected.
    <br><strong>Filtered total incidents:</strong> {total:,}{note}
  </div>
  <div class="warning-footer">
    🔒 All actions logged • Do not use for individual-level targeting • Review fairness and drift signals quarterly
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_kpis(filtered_df: pd.DataFrame, risk_latest: pd.DataFrame) -> Dict[str, Any]:
    YEAR_MAX = int(filtered_df["year"].max()) if not filtered_df.empty else 0
    prev_year = YEAR_MAX - 1

    total_crimes = int(filtered_df["crime_count"].sum()) if not filtered_df.empty else 0
    current_year_total = float(filtered_df[filtered_df["year"] == YEAR_MAX]["crime_count"].sum()) if YEAR_MAX else 0.0
    prev_year_total = float(filtered_df[filtered_df["year"] == prev_year]["crime_count"].sum()) if prev_year in filtered_df["year"].unique() else 0.0
    yoy_change = ((current_year_total - prev_year_total) / prev_year_total * 100.0) if prev_year_total > 0 else 0.0

    avg_risk = float(risk_latest["risk_score"].mean()) if not risk_latest.empty else 0.0
    critical_count = int((risk_latest["risk_level"].astype(str).str.contains("CRITICAL")).sum()) if not risk_latest.empty else 0

    top_state_name = "—"
    if not filtered_df.empty:
        top_state = filtered_df.groupby("state_name_norm")["crime_count"].sum().sort_values(ascending=False)
        if len(top_state) > 0:
            top_state_name = str(top_state.index[0])

    top_district_name = "—"
    if not filtered_df.empty:
        top_dist = filtered_df.groupby("district_name_norm")["crime_count"].sum().sort_values(ascending=False)
        if len(top_dist) > 0:
            top_district_name = str(top_dist.index[0])

    st.markdown('<div style="display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin:14px 0;">', unsafe_allow_html=True)
    cols = st.columns(4)

    with cols[0]:
        st.markdown(
            f"""
<div class="kpi-card {'critical' if yoy_change > 25 else ''}">
  <div class="kpi-label">Total Incidents</div>
  <div class="kpi-value">{format_number(total_crimes)}</div>
  <div class="kpi-status-pill {'positive' if yoy_change >= 0 else 'negative'}">
    {('↑' if yoy_change > 0 else '↓')}{abs(yoy_change):.1f}% YoY
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    with cols[1]:
        risk_text = "CRITICAL" if avg_risk >= 75 else "ELEVATED" if avg_risk >= 55 else "MODERATE"
        risk_color = "#ff4d00" if avg_risk >= 75 else "#e0af68" if avg_risk >= 55 else "#00f3ff"
        st.markdown(
            f"""
<div class="kpi-card {'critical' if avg_risk >= 75 else ''}">
  <div class="kpi-label">AI Risk Level</div>
  <div class="kpi-value" style="color:{risk_color};">{risk_text}</div>
  <div class="kpi-status-pill {'negative' if critical_count > 0 else 'positive'}">
    {critical_count} Critical Districts
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    with cols[2]:
        st.markdown(
            f"""
<div class="kpi-card">
  <div class="kpi-label">Highest Crime State</div>
  <div class="kpi-value">{top_state_name}</div>
  <div class="kpi-status-pill neutral">State Leader</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with cols[3]:
        st.markdown(
            f"""
<div class="kpi-card">
  <div class="kpi-label">Highest Crime District</div>
  <div class="kpi-value">{top_district_name}</div>
  <div class="kpi-status-pill neutral">District Leader</div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    return {
        "YEAR_MAX": YEAR_MAX,
        "total_crimes": total_crimes,
        "critical_count": critical_count,
        "avg_risk": avg_risk,
        "yoy_change": yoy_change,
        "top_state_name": top_state_name,
        "top_district_name": top_district_name,
    }


# ============================================================
# 🧩 ANALYTICS VISUALS
# ============================================================
def correlation_analysis(filtered_df: pd.DataFrame, use_pulsed: bool = False) -> go.Figure:
    if filtered_df.empty:
        fig = go.Figure()
        fig.update_layout(title="Crime Category Correlation Matrix (No Data)")
        return apply_tactical_theme(fig)

    ccol = "crime_count_pulsed" if use_pulsed and "crime_count_pulsed" in filtered_df.columns else "crime_count"

    pivot = filtered_df.pivot_table(
        index=["state_name_norm", "district_name_norm", "year"],
        columns="category",
        values=ccol,
        aggfunc="sum",
        fill_value=0,
    )
    corr = pivot.corr()

    fig = px.imshow(
        corr,
        title="Crime Category Correlation Matrix",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
    )
    fig.update_layout(height=520)
    return apply_tactical_theme(fig)


def seasonality_placeholder(filtered_df: pd.DataFrame) -> go.Figure:
    """
    With yearly synthetic demo data, true month seasonality isn't present.
    This chart is a 'pattern view' placeholder generated deterministically from years.
    """
    if filtered_df.empty:
        fig = go.Figure()
        fig.update_layout(title="Seasonality Pattern (No Data)")
        return apply_tactical_theme(fig)

    yearly = filtered_df.groupby("year")["crime_count"].sum().reset_index()
    # Create a pseudo-month projection from yearly totals for visual pattern (demo only)
    rng = np.random.default_rng(123)
    monthly = []
    for _, r in yearly.iterrows():
        base = float(r["crime_count"])
        for m in range(1, 13):
            wave = 1.0 + 0.10 * np.sin(2 * np.pi * (m / 12.0))
            noise = float(rng.normal(1.0, 0.03))
            monthly.append({"year": int(r["year"]), "month": m, "crime_count": max(0.0, base * wave * noise / 12.0)})
    mdf = pd.DataFrame(monthly)
    agg = mdf.groupby("month")["crime_count"].sum().reset_index()
    fig = px.line(agg, x="month", y="crime_count", markers=True, title="Crime Seasonality Pattern (Synthetic Projection)")
    fig.update_xaxes(tickmode="linear")
    fig.update_layout(height=420)
    return apply_tactical_theme(fig)


# ============================================================
# 🧾 TICKER + FOOTER
# ============================================================
def render_ticker(
    year_range: Tuple[int, int],
    state: str,
    district: str,
    category: str,
    total_crimes: int,
    critical_count: int,
) -> None:
    st.markdown(
        """
<div class="data-stream-ticker">
  <div class="ticker-content">
    <span class="stream-item">📡 LIVE FEED:</span>
    <span class="stream-item">FILTERS: Year {y0}-{y1} | State: {state} | District: {district} | Category: {cat}</span>
    <span class="stream-item">📊 TOTAL CRIMES: {total:,}</span>
    <span class="stream-item">⚠️ CRITICAL DISTRICTS: {crit}</span>
    <span class="stream-item">🤖 ML ENGINE: SYNCHRONIZED</span>
    <span class="stream-item">⏱️ LAST UPDATE: {ts} UTC</span>
    <span class="stream-item">🔒 ALL ACTIONS LOGGED FOR AUDIT</span>
  </div>
</div>
""".format(
            y0=int(year_range[0]),
            y1=int(year_range[1]),
            state=state,
            district=district,
            cat=category,
            total=int(total_crimes),
            crit=int(critical_count),
            ts=datetime.now(timezone.utc).strftime("%H:%M:%S"),
        ),
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        """
<div class="footer">
  <div class="footer-title">CRIMEWATCH INDIA INTELLIGENCE PLATFORM • DEMO SYNTHETIC DATA</div>
  <div class="footer-grid">
    <div><strong>Data Freshness:</strong> Synthetic (demo) • Lag simulation supported</div>
    <div><strong>Next Update:</strong> Depends on upstream data pipeline</div>
    <div><strong>Coverage:</strong> Synthetic districts • Functionality mirrors production</div>
  </div>
  <div class="footer-warning">
    <strong>⚠️ Critical Notice:</strong> This system reflects <em>reported</em> (or simulated) incidents. Always verify with local ground intelligence before operational decisions.
  </div>
  <div class="footer-legal">
    <div>Compliant by design: Human review • Audit logging • Data minimisation</div>
    <div>Unauthorized access may violate organisational policies and applicable law</div>
    <div>© CrimeWatch AI — Intelligence HUD</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# 🧩 TABS (PRESERVE CORE + ADD UPGRADES)
# ============================================================
def render_tabs(
    df_raw: pd.DataFrame,
    df_pulsed: pd.DataFrame,
    filtered_df: pd.DataFrame,
    filtered_pulsed_df: pd.DataFrame,
    use_pulsed: bool,
    risk_all_years: pd.DataFrame,
    risk_latest: pd.DataFrame,
    anomaly_df: pd.DataFrame,
    anomaly_meta: Dict[str, Any],
    spikes_df: pd.DataFrame,
    patrol_df: pd.DataFrame,
    strategy_df: pd.DataFrame,
    yearly: pd.DataFrame,
    forecast_df: pd.DataFrame,
    forecast_meta: Dict[str, Any],
    points_clustered: pd.DataFrame,
    centroids: pd.DataFrame,
    cluster_meta: Dict[str, Any],
    supervised_result: Dict[str, Any],
) -> None:
    tabs = st.tabs(
        [
            "📌 Overview",
            "🔥 Hotspots & Risk",
            "🎯 Drilldown",
            "🧊 Heatmaps",
            "📈 Forecast",
            "🔄 Correlation",
            "🚨 Early Warning",
            "🚓 Patrol Plan",
            "🛡️ Prevention Strategy",
            "🧠 Risk Prediction",
            "🧪 Model Governance",
            "⚖️ Ethical Auditor",
            "📝 Executive Report",
            "🗺️ Map & Clusters",
            "📂 Data & Export",
        ]
    )

    # TAB: Overview
    with tabs[0]:
        st.markdown('<div class="section-header">Temporal Intelligence & Prediction</div>', unsafe_allow_html=True)
        if yearly.empty:
            st.info("No trend data available under current filters.")
        else:
            fig_trend = px.line(yearly, x="year", y="crime_count", markers=True, title="Total Crime Trend (Yearly)")
            fig_trend.update_layout(height=360)
            st.plotly_chart(apply_tactical_theme(fig_trend), use_container_width=True)

        st.markdown('<div class="glass-card" style="padding:14px;">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Crime Category Breakdown</div>', unsafe_allow_html=True)

        base = filtered_pulsed_df if use_pulsed else filtered_df
        ccol = "crime_count_pulsed" if use_pulsed and "crime_count_pulsed" in base.columns else "crime_count"

        if base.empty:
            st.info("No category data available.")
        else:
            category_data = (
                base.groupby("category", as_index=False)
                .agg(total=(ccol, "sum"))
                .sort_values("total", ascending=False)
                .head(10)
            )
            fig_cat = px.pie(category_data, values="total", names="category", title="Top Crime Categories (Filtered)", hole=0.4)
            fig_cat.update_traces(
                textposition="inside",
                textinfo="percent+label",
                hoverinfo="label+value+percent",
                marker=dict(line=dict(color="#0f172a", width=2)),
            )
            fig_cat.update_layout(height=360, showlegend=True)
            st.plotly_chart(apply_tactical_theme(fig_cat), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    # TAB: Hotspots & Risk
    with tabs[1]:
        st.markdown('<div class="section-header">Hotspots & Risk Assessment</div>', unsafe_allow_html=True)
        st.caption("Risk scoring combines volume + growth + volatility. Now includes arrest ratios for anomaly features.")
        if risk_latest.empty:
            st.warning("No hotspot data available.")
        else:
            left_col, right_col = st.columns([1.5, 0.85], gap="large")
            with left_col:
                st.markdown('<div class="glass-card" style="padding:14px;">', unsafe_allow_html=True)
                st.subheader("Highest-Risk Districts (Latest Year)")
                show_n = st.slider("Show top N hotspots", 10, 100, 25, step=5, key="hotspots_topn")
                tbl = risk_latest.head(show_n)[
                    [
                        "state_name_norm",
                        "district_name_norm",
                        "total_crime",
                        "arrests",
                        "arrest_ratio",
                        "yoy_growth",
                        "volatility",
                        "risk_score",
                        "risk_level",
                    ]
                ].rename(
                    columns={
                        "state_name_norm": "State",
                        "district_name_norm": "District",
                        "total_crime": "Latest-Year Total",
                        "arrests": "Arrests (Latest Year)",
                        "arrest_ratio": "Arrest Ratio",
                        "yoy_growth": "YoY Growth %",
                        "volatility": "Volatility",
                        "risk_score": "Risk Score",
                        "risk_level": "Risk Level",
                    }
                )
                st.dataframe(tbl, use_container_width=True, height=520)
                st.markdown("</div>", unsafe_allow_html=True)

            with right_col:
                st.markdown('<div class="glass-card" style="padding:14px;">', unsafe_allow_html=True)
                st.subheader("Risk Drivers (Why this district?)")
                district_list = tbl["District"].tolist()
                if district_list:
                    sel_d = st.selectbox("Select a district", district_list, index=0, key="risk_hotspot_pick")
                    row = risk_latest[risk_latest["district_name_norm"] == sel_d].head(1)
                    if not row.empty:
                        r = row.iloc[0]
                        st.metric("Risk Score", f"{float(r['risk_score']):.1f}", f"{r['risk_level']} risk")
                        st.write(
                            f"- **State:** {r['state_name_norm']}\n"
                            f"- **Latest-Year Crime:** {int(r['total_crime']):,}\n"
                            f"- **YoY Growth:** {float(r['yoy_growth']):+.1f}%\n"
                            f"- **Volatility:** {float(r['volatility']):.1f}\n"
                            f"- **Arrest Ratio:** {float(r['arrest_ratio']):.2f}"
                        )

                        base2 = filtered_pulsed_df if use_pulsed else filtered_df
                        ccol2 = "crime_count_pulsed" if use_pulsed and "crime_count_pulsed" in base2.columns else "crime_count"
                        dom = (
                            base2[base2["district_name_norm"] == sel_d]
                            .groupby("category", as_index=False)[ccol2]
                            .sum()
                            .rename(columns={ccol2: "crime_count"})
                            .sort_values("crime_count", ascending=False)
                            .head(8)
                        )
                        fig_dom = px.bar(dom, x="crime_count", y="category", orientation="h", title="Dominant Categories (within district)")
                        fig_dom.update_layout(height=360)
                        st.plotly_chart(apply_tactical_theme(fig_dom), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

    # TAB: Drilldown
    with tabs[2]:
        st.markdown('<div class="section-header">🎯 Drilldown</div>', unsafe_allow_html=True)
        st.caption("Drill down: State → District → Category → Crime Type")

        base = filtered_pulsed_df if use_pulsed else filtered_df
        ccol = "crime_count_pulsed" if use_pulsed and "crime_count_pulsed" in base.columns else "crime_count"

        if base.empty:
            st.warning("No rows for selected filters.")
        else:
            c1, c2, c3, c4 = st.columns(4)

            with c1:
                states2 = ["(All)"] + sorted(base["state_name_norm"].unique().tolist())
                drill_state = st.selectbox("State", states2, index=0, key="drill_state")
                ddf = base.copy()
                if drill_state != "(All)":
                    ddf = ddf[ddf["state_name_norm"] == drill_state]

            with c2:
                districts2 = ["(All)"] + sorted(ddf["district_name_norm"].unique().tolist())
                drill_district = st.selectbox("District", districts2, index=0, key="drill_district")
                if drill_district != "(All)":
                    ddf = ddf[ddf["district_name_norm"] == drill_district]

            with c3:
                cats2 = ["(All)"] + sorted(ddf["category"].unique().tolist())
                drill_cat = st.selectbox("Category", cats2, index=0, key="drill_cat")
                if drill_cat != "(All)":
                    ddf = ddf[ddf["category"] == drill_cat]

            with c4:
                crime_types2 = ["(All)"] + sorted(ddf["crime_type"].unique().tolist())
                drill_type = st.selectbox("Crime Type", crime_types2, index=0, key="drill_type")
                if drill_type != "(All)":
                    ddf = ddf[ddf["crime_type"] == drill_type]

            if ddf.empty:
                st.warning("No rows for selected drill combination. Switch some filters to (All).")
            else:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Crimes", f"{int(ddf[ccol].sum()):,}")
                col2.metric("Years Covered", f"{int(ddf['year'].min())} – {int(ddf['year'].max())}")
                col3.metric("Unique Districts", f"{ddf['district_key'].nunique():,}")
                col4.metric("Unique Crime Types", f"{ddf['crime_type'].nunique():,}")

                trend = ddf.groupby("year", as_index=False).agg(total=(ccol, "sum"))
                fig = px.line(trend, x="year", y="total", markers=True, title="Crime Trend (Drilldown)")
                fig.update_layout(height=360)
                st.plotly_chart(apply_tactical_theme(fig), use_container_width=True)

    # TAB: Heatmaps
    with tabs[3]:
        st.markdown('<div class="section-header">🧊 Heatmaps</div>', unsafe_allow_html=True)
        st.caption("Heatmaps highlight concentration patterns across district, category, and year.")
        base = filtered_pulsed_df if use_pulsed else filtered_df
        ccol = "crime_count_pulsed" if use_pulsed and "crime_count_pulsed" in base.columns else "crime_count"

        if base.empty:
            st.warning("No data for heatmaps.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="glass-card" style="padding:14px;">', unsafe_allow_html=True)
                st.subheader("District × Year (Top 25)")
                heat = base.groupby(["district_name_norm", "year"], as_index=False)[ccol].sum().rename(columns={ccol: "crime_count"})
                top_districts = (
                    heat.groupby("district_name_norm")["crime_count"].sum().sort_values(ascending=False).head(25).index.tolist()
                )
                heat = heat[heat["district_name_norm"].isin(top_districts)]
                pivot = heat.pivot_table(index="district_name_norm", columns="year", values="crime_count", aggfunc="sum").fillna(0)
                fig_heat = go.Figure(
                    data=go.Heatmap(
                        z=pivot.values,
                        x=pivot.columns.astype(str),
                        y=pivot.index,
                        colorscale="Blues",
                        colorbar=dict(title="Crimes"),
                    )
                )
                fig_heat.update_layout(height=470, title="District × Year Heatmap")
                st.plotly_chart(apply_tactical_theme(fig_heat), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with c2:
                st.markdown('<div class="glass-card" style="padding:14px;">', unsafe_allow_html=True)
                st.subheader("District × Category (Top 25)")
                hc = base.groupby(["district_name_norm", "category"], as_index=False)[ccol].sum().rename(columns={ccol: "crime_count"})
                top_d = hc.groupby("district_name_norm")["crime_count"].sum().sort_values(ascending=False).head(25).index.tolist()
                hc = hc[hc["district_name_norm"].isin(top_d)]
                fig_hc = px.density_heatmap(hc, x="category", y="district_name_norm", z="crime_count", title="District × Category Heatmap")
                fig_hc.update_layout(height=470)
                st.plotly_chart(apply_tactical_theme(fig_hc), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

    # TAB: Forecast
    with tabs[4]:
        st.markdown('<div class="section-header">📈 Crime Forecast</div>', unsafe_allow_html=True)
        st.caption("Forecast strategy selector: ARIMA (Advanced) with Linear (Fast) fallback. Displays model used + quality metrics.")
        if yearly.empty:
            st.warning("Insufficient data for forecasting (no yearly series).")
        else:
            colA, colB, colC = st.columns([1.2, 1, 1])
            with colA:
                st.session_state.forecast_strategy = st.selectbox(
                    "Forecast Strategy",
                    ["Linear (Fast)", "ARIMA (Advanced)"],
                    index=0 if st.session_state.forecast_strategy == "Linear (Fast)" else 1,
                    key="forecast_strategy_selector",
                )
            with colB:
                st.session_state.forecast_years_ahead = st.slider(
                    "Forecast Years Ahead",
                    1,
                    5,
                    int(st.session_state.forecast_years_ahead),
                    key="forecast_years_slider",
                )
            with colC:
                st.caption("If ARIMA fails, system auto-falls back to Linear.")

            # Recompute forecast based on tab controls (cached transforms keep cost low)
            fdf, fmeta = run_forecast(yearly, st.session_state.forecast_strategy, int(st.session_state.forecast_years_ahead))
            if fmeta.get("fallback", False):
                st.warning(f"Forecast fallback engaged: {fmeta.get('fallback_reason','')}")
            st.success(f"✅ Model used: {fmeta.get('model_used','—')}")

            # Combine historical + forecast
            hist = yearly.copy()
            hist["type"] = "Historical"
            comb = pd.concat([hist, fdf[["year", "crime_count", "type"]] if not fdf.empty else hist.head(0)], ignore_index=True)

            fig_forecast = px.line(
                comb,
                x="year",
                y="crime_count",
                color="type",
                markers=True,
                title=f"Crime Trend Forecast ({int(st.session_state.forecast_years_ahead)} Years)",
                line_dash="type",
            )
            fig_forecast.update_layout(height=420)

            # Add confidence band if available
            if not fdf.empty and "lower" in fdf.columns and "upper" in fdf.columns:
                fig_forecast.add_trace(
                    go.Scatter(
                        x=fdf["year"],
                        y=fdf["upper"],
                        mode="lines",
                        line=dict(width=0),
                        showlegend=False,
                        hoverinfo="skip",
                        name="Upper CI",
                    )
                )
                fig_forecast.add_trace(
                    go.Scatter(
                        x=fdf["year"],
                        y=fdf["lower"],
                        mode="lines",
                        line=dict(width=0),
                        fill="tonexty",
                        name="95% CI",
                        hoverinfo="skip",
                    )
                )

            st.plotly_chart(apply_tactical_theme(fig_forecast), use_container_width=True)

            st.markdown('<div class="glass-card" style="padding:14px;">', unsafe_allow_html=True)
            st.subheader("Forecast Quality & Metadata")
            mcols = st.columns(4)
            mcols[0].metric("MAE", f"{float(fmeta.get('mae', np.nan)):.0f}" if fmeta.get("mae") is not None else "—")
            mcols[1].metric("MAPE", f"{float(fmeta.get('mape', np.nan)):.1f}%" if fmeta.get("mape") is not None else "—")
            if "r2" in fmeta:
                mcols[2].metric("R² (Linear)", f"{float(fmeta.get('r2', 0.0)):.2f}")
            else:
                mcols[2].metric("AIC (ARIMA)", f"{float(fmeta.get('aic', np.nan)):.1f}" if fmeta.get("aic") is not None else "—")
            mcols[3].metric("CI Available", "Yes" if bool(fmeta.get("ci", False)) else "No")

            if not fdf.empty:
                st.dataframe(fdf, use_container_width=True, height=260)
            else:
                st.info("No forecast rows generated under current conditions.")
            st.markdown("</div>", unsafe_allow_html=True)

            log_action("Forecast Run", details=json.dumps({k: str(v) for k, v in fmeta.items()}))

    # TAB: Correlation
    with tabs[5]:
        st.markdown('<div class="section-header">🔄 Crime Category Correlation</div>', unsafe_allow_html=True)
        st.caption("Correlation analysis + seasonality pattern view.")
        base = filtered_pulsed_df if use_pulsed else filtered_df
        if base.empty:
            st.info("Need data to analyse correlations.")
        else:
            fig_corr = correlation_analysis(base, use_pulsed=use_pulsed)
            st.plotly_chart(fig_corr, use_container_width=True)
            st.markdown('<div class="glass-card" style="padding:14px;">', unsafe_allow_html=True)
            st.subheader("Seasonality Pattern (Synthetic Projection)")
            fig_season = seasonality_placeholder(filtered_df)
            st.plotly_chart(fig_season, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # TAB: Early Warning (Rule spikes + Anomaly integration)
    with tabs[6]:
        st.markdown('<div class="section-header">🚨 Early Warning</div>', unsafe_allow_html=True)
        st.caption("Rule-based spikes + IsolationForest anomalies (district/state risk spikes).")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.session_state.ew_pct = st.slider("Spike Threshold (YoY %)", 10, 200, int(st.session_state.ew_pct), step=5, key="ew_pct_slider")
        with c2:
            st.session_state.ew_abs = st.slider(
                "Spike Threshold (Absolute)", 1000, 200000, int(st.session_state.ew_abs), step=1000, key="ew_abs_slider"
            )
        with c3:
            st.session_state.ew_max = st.slider("Max Alerts", 10, 200, int(st.session_state.ew_max), step=10, key="ew_max_slider")

        # Recompute spikes with current thresholds
        base = filtered_pulsed_df if use_pulsed else filtered_df
        year_max = int(base["year"].max()) if not base.empty else 0
        spikes_live = early_warning_engine(
            base,
            year_max,
            spike_threshold_pct=float(st.session_state.ew_pct),
            spike_threshold_abs=float(st.session_state.ew_abs),
            use_pulsed=use_pulsed,
        ).head(int(st.session_state.ew_max))

        if spikes_live.empty:
            st.success("No spikes detected under current thresholds.")
        else:
            st.warning(f"{len(spikes_live)} spike alerts detected for {year_max}")
            table = spikes_live[
                ["state_name_norm", "district_name_norm", "year", "crime_count", "yoy_delta", "yoy_pct", "alert"]
            ].rename(
                columns={
                    "state_name_norm": "State",
                    "district_name_norm": "District",
                    "crime_count": "Crimes (Latest Year)",
                    "yoy_delta": "YoY Increase",
                    "yoy_pct": "YoY % Increase",
                }
            )
            st.dataframe(table, use_container_width=True, height=340)

            fig = px.bar(table.head(30), x="YoY % Increase", y="District", orientation="h", title="Top Emerging Districts (YoY % Increase)")
            fig.update_layout(height=520)
            st.plotly_chart(apply_tactical_theme(fig), use_container_width=True)

        # Anomaly table integration
        st.markdown('<div class="glass-card" style="padding:14px; margin-top:16px;">', unsafe_allow_html=True)
        st.subheader("Anomaly Detection (IsolationForest)")
        if anomaly_df.empty:
            st.info("Anomaly engine not available or no feature rows. Ensure sufficient districts and that sklearn is installed.")
        else:
            # Show most anomalous first
            view = anomaly_df.sort_values("anomaly_score", ascending=False).copy()
            view["Anomaly"] = np.where(view["anomaly_flag"], "⚠️ YES", "—")
            show_cols = [
                "state_name_norm",
                "district_name_norm",
                "total_crime",
                "risk_score",
                "arrest_ratio",
                "yoy_growth",
                "lag_yoy_growth",
                "anomaly_score",
                "Anomaly",
                "risk_level",
            ]
            disp = view[show_cols].rename(
                columns={
                    "state_name_norm": "State",
                    "district_name_norm": "District",
                    "total_crime": "Incidents",
                    "risk_score": "Risk Score",
                    "arrest_ratio": "Arrest Ratio",
                    "yoy_growth": "YoY Growth",
                    "lag_yoy_growth": "Lag YoY Growth",
                    "anomaly_score": "Anomaly Score",
                    "risk_level": "Risk Level",
                }
            )
            st.dataframe(disp.head(50), use_container_width=True, height=420)
            st.caption(f"Anomaly meta: {anomaly_meta}")
        st.markdown("</div>", unsafe_allow_html=True)

        log_action("Anomaly Run", details=json.dumps({k: str(v) for k, v in anomaly_meta.items()}))

    # TAB: Patrol Plan
    with tabs[7]:
        st.markdown('<div class="section-header">🚓 Patrol Plan</div>', unsafe_allow_html=True)
        st.caption("Transforms early-warning alerts into a ranked patrol plan with unit allocation.")

        c1, c2 = st.columns(2)
        with c1:
            max_units = st.slider("Total Units Available", 5, 100, 20, step=5, key="pp_units")
        with c2:
            show_top = st.slider("Show top N patrol priorities", 10, 200, 50, step=10, key="pp_top")

        if patrol_df.empty:
            st.info("No patrol plan generated because no alerts were detected.")
        else:
            st.success(f"Patrol plan generated — total allocated units: {int(patrol_df['allocated_units'].sum())}")
            st.dataframe(patrol_df.head(int(show_top)), use_container_width=True, height=450)
            fig = px.bar(
                patrol_df.head(25),
                x="Risk Score",
                y="District",
                orientation="h",
                title="Top Patrol Priorities (Risk Score)",
            )
            fig.update_layout(height=520)
            st.plotly_chart(apply_tactical_theme(fig), use_container_width=True)

    # TAB: Prevention Strategy
    with tabs[8]:
        st.markdown('<div class="section-header">🛡️ Prevention Strategy</div>', unsafe_allow_html=True)
        st.caption("Generates actionable prevention + enforcement recommendations for highest-risk hotspots.")
        if strategy_df.empty:
            st.warning("No strategy generated (no hotspot data).")
        else:
            show_n = st.slider("Show top N hotspot strategies", 10, 150, 25, step=5, key="ps_topn")
            out = strategy_df.head(int(show_n))[
                [
                    "state_name_norm",
                    "district_name_norm",
                    "risk_score",
                    "risk_level",
                    "dominant_category",
                    "dominant_category_total",
                    "recommended_actions",
                    "generated_on",
                ]
            ].rename(
                columns={
                    "state_name_norm": "State",
                    "district_name_norm": "District",
                    "risk_score": "Risk Score",
                    "risk_level": "Risk Level",
                    "dominant_category": "Dominant Category",
                    "dominant_category_total": "Dominant Category Total",
                    "generated_on": "Generated On",
                }
            )
            st.dataframe(out, use_container_width=True, height=470)

            csv_bytes = strategy_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download Prevention Strategy CSV",
                data=csv_bytes,
                file_name="crimewatch_prevention_strategies.csv",
                mime="text/csv",
            )

    # TAB: Risk Prediction
    with tabs[9]:
        st.markdown('<div class="section-header">🧠 Supervised Risk Prediction</div>', unsafe_allow_html=True)
        st.caption("Predict next-period district risk bucket (LOW/MEDIUM/HIGH/CRITICAL) using RandomForest/XGBoost (if available).")
        if supervised_result.get("status") != "OK":
            st.warning(f"Risk predictor unavailable: {supervised_result.get('status')} {supervised_result.get('reason','')}")
        else:
            st.success(f"✅ Model used: {supervised_result.get('model_used')} | Accuracy: {float(supervised_result.get('accuracy', 0.0)):.2f}")

            labels = supervised_result.get("labels", [])
            cm = supervised_result.get("confusion_matrix", None)
            if cm is not None and labels:
                fig_cm = figure_confusion_matrix(cm, labels, "Confusion Matrix (Next Risk Bucket)")
                st.plotly_chart(fig_cm, use_container_width=True)

            report = supervised_result.get("report", {})
            if report:
                # Extract compact summary
                rows = []
                for lab in labels:
                    if lab in report:
                        rows.append(
                            {
                                "Class": lab,
                                "Precision": float(report[lab].get("precision", 0.0)),
                                "Recall": float(report[lab].get("recall", 0.0)),
                                "F1": float(report[lab].get("f1-score", 0.0)),
                                "Support": int(report[lab].get("support", 0)),
                            }
                        )
                df_rep = pd.DataFrame(rows)
                st.markdown('<div class="glass-card" style="padding:14px;">', unsafe_allow_html=True)
                st.subheader("Classification Report (Summary)")
                st.dataframe(df_rep, use_container_width=True, height=240)
                st.markdown("</div>", unsafe_allow_html=True)

            # Feature importances
            importances = supervised_result.get("feature_importances", None)
            feature_names = supervised_result.get("feature_names", [])
            if importances is not None and feature_names:
                fig_imp = figure_feature_importances(feature_names, importances, "Top Feature Importances")
                st.plotly_chart(fig_imp, use_container_width=True)

            log_action(
                "Supervised Model Run",
                details=json.dumps(
                    {
                        "model_used": supervised_result.get("model_used"),
                        "accuracy": supervised_result.get("accuracy"),
                        "labels": supervised_result.get("labels"),
                    }
                ),
            )

    # TAB: Model Governance Panel
    with tabs[10]:
        st.markdown('<div class="section-header">🧪 Model Governance</div>', unsafe_allow_html=True)
        st.caption("Forecast MAE/MAPE, proxy alert precision/recall, drift checks, and fairness placeholder metrics.")

        # Forecast metrics
        st.markdown('<div class="glass-card" style="padding:14px;">', unsafe_allow_html=True)
        st.subheader("Forecast Governance")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Model Used", str(forecast_meta.get("model_used", "—")))
        col2.metric("MAE", f"{float(forecast_meta.get('mae', np.nan)):.0f}" if forecast_meta.get("mae") is not None else "—")
        col3.metric("MAPE", f"{float(forecast_meta.get('mape', np.nan)):.1f}%" if forecast_meta.get("mape") is not None else "—")
        if "aic" in forecast_meta:
            col4.metric("AIC", f"{float(forecast_meta.get('aic', np.nan)):.1f}")
        else:
            col4.metric("R²", f"{float(forecast_meta.get('r2', 0.0)):.2f}")
        st.markdown("</div>", unsafe_allow_html=True)

        # Alert metrics (proxy)
        st.markdown('<div class="glass-card" style="padding:14px; margin-top:12px;">', unsafe_allow_html=True)
        st.subheader("Alert Governance (Proxy)")
        proxy = governance_alert_metrics(spikes_df, anomaly_df)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Proxy Precision", f"{float(proxy.get('precision', np.nan)):.2f}" if proxy.get("status") == "OK" else "—")
        c2.metric("Proxy Recall", f"{float(proxy.get('recall', np.nan)):.2f}" if proxy.get("status") == "OK" else "—")
        c3.metric("Proxy F1", f"{float(proxy.get('f1', np.nan)):.2f}" if proxy.get("status") == "OK" else "—")
        c4.metric("Proxy Status", proxy.get("status", "—"))
        st.caption("Proxy assumes rule-based spikes are pseudo-labels; replace with validated outcome labels when available.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Drift checks
        st.markdown('<div class="glass-card" style="padding:14px; margin-top:12px;">', unsafe_allow_html=True)
        st.subheader("Drift Checks (State Distribution)")
        drift = drift_checks_by_state(filtered_pulsed_df if use_pulsed else filtered_df, use_pulsed=use_pulsed)
        if drift.empty:
            st.info("Not enough data to compute drift checks.")
        else:
            overall_psi = float(drift.attrs.get("overall_psi", 0.0))
            mid_year = drift.attrs.get("mid_year", "—")
            st.metric("Overall PSI", f"{overall_psi:.3f}", help="Low <0.1 | Moderate 0.1–0.25 | High >0.25 (rule-of-thumb)")
            st.caption(f"Window split at year ≤ {mid_year} vs > {mid_year}")
            st.dataframe(drift.head(20), use_container_width=True, height=320)
        st.markdown("</div>", unsafe_allow_html=True)

        # Fairness placeholders (grouped by state/category availability)
        st.markdown('<div class="glass-card" style="padding:14px; margin-top:12px;">', unsafe_allow_html=True)
        st.subheader("Fairness Placeholders")
        if risk_latest.empty:
            st.info("No risk rows available for fairness placeholder metrics.")
        else:
            tmp = risk_latest.copy()
            tmp["critical_or_high"] = tmp["risk_level"].astype(str).str.contains("CRITICAL|HIGH")
            tmp["anomaly_flag"] = False
            if not anomaly_df.empty and "anomaly_flag" in anomaly_df.columns:
                amap = anomaly_df.set_index("district_key")["anomaly_flag"].to_dict()
                tmp["anomaly_flag"] = tmp["district_key"].map(lambda k: bool(amap.get(k, False)))

            fairness = tmp.groupby("state_name_norm", as_index=False).agg(
                districts=("district_key", "nunique"),
                critical_high_rate=("critical_or_high", "mean"),
                anomaly_rate=("anomaly_flag", "mean"),
                avg_arrest_ratio=("arrest_ratio", "mean"),
            )
            fairness["critical_high_rate"] = fairness["critical_high_rate"] * 100.0
            fairness["anomaly_rate"] = fairness["anomaly_rate"] * 100.0
            fairness = fairness.sort_values("critical_high_rate", ascending=False)
            st.dataframe(fairness, use_container_width=True, height=320)
            st.caption("These are placeholders. Add protected attribute proxies ONLY if legally/ethically approved and necessary.")
        st.markdown("</div>", unsafe_allow_html=True)

        log_action(
            "Governance Panel Viewed",
            details=json.dumps(
                {
                    "forecast_model": str(forecast_meta.get("model_used")),
                    "proxy_metrics": {k: proxy.get(k) for k in ("precision", "recall", "f1", "status")},
                }
            ),
        )

    # TAB: Ethical Auditor
    with tabs[11]:
        st.markdown('<div class="section-header">⚖️ Ethical AI Auditor</div>', unsafe_allow_html=True)
        st.caption("Bias / fairness checks and governance reminders (demo-friendly, production-ready hooks).")
        st.markdown(
            """
<div class="warning-panel" style="margin-top:0;">
  <div class="warning-title">Legal & Ethical Compliance Notice</div>
  <div class="warning-content">
    <strong>Prohibited uses:</strong> Individual-level predictions or targeting • Fully automated enforcement actions without human review<br><br>
    <strong>Required safeguards:</strong> Human-in-the-loop review for CRITICAL flags • Quarterly drift/fairness audits • Public transparency reporting (anonymised where applicable)
  </div>
  <div class="warning-footer">This panel provides governance hooks; replace placeholders with validated metrics and approved datasets.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        if risk_latest.empty:
            st.info("No risk rows available for fairness sampling view.")
        else:
            st.markdown('<div class="glass-card" style="padding:14px; margin-top:12px;">', unsafe_allow_html=True)
            st.subheader("Risk Flag Distribution (By State)")
            tmp = risk_latest.copy()
            dist = tmp.groupby(["state_name_norm", "risk_level"], as_index=False).size().rename(columns={"size": "count"})
            fig = px.bar(dist, x="state_name_norm", y="count", color="risk_level", title="Risk Level Counts by State", barmode="group")
            fig.update_layout(height=420)
            st.plotly_chart(apply_tactical_theme(fig), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # TAB: Executive Report
    with tabs[12]:
        st.markdown('<div class="section-header">📝 Executive Report</div>', unsafe_allow_html=True)
        st.caption("Auto-generates a professional intelligence report for decision-makers.")
        report_md = executive_report_engine(risk_latest, spikes_df, patrol_df, filtered_df)
        st.markdown(report_md)
        st.download_button(
            "⬇️ Download Executive Report (Markdown)",
            data=report_md.encode("utf-8"),
            file_name="crimewatch_executive_report.md",
            mime="text/markdown",
        )

    # TAB: Map & Clusters
    with tabs[13]:
        st.markdown('<div class="section-header">🗺️ Map & Hotspot Clustering</div>', unsafe_allow_html=True)
        st.caption("KMeans (centroids) + DBSCAN (noise-aware) clustering. Switch algorithm and parameters below.")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.session_state.cluster_algo = st.selectbox("Clustering Algorithm", ["KMeans", "DBSCAN"], index=0 if st.session_state.cluster_algo == "KMeans" else 1, key="cluster_algo_selector")
        with c2:
            st.session_state.kmeans_k = st.slider("KMeans k", 2, 12, int(st.session_state.kmeans_k), key="kmeans_k_slider")
        with c3:
            st.session_state.dbscan_eps = st.slider("DBSCAN eps", 0.10, 3.00, float(st.session_state.dbscan_eps), step=0.05, key="dbscan_eps_slider")
        with c4:
            st.session_state.dbscan_min_samples = st.slider("DBSCAN min_samples", 3, 30, int(st.session_state.dbscan_min_samples), key="dbscan_min_samples_slider")

        # Recluster with new params (small dataset; acceptable)
        pts = build_cluster_points(risk_latest)
        try:
            cpts, cents, cmeta = run_clustering(
                pts,
                algorithm=st.session_state.cluster_algo,
                kmeans_k=int(st.session_state.kmeans_k),
                dbscan_eps=float(st.session_state.dbscan_eps),
                dbscan_min_samples=int(st.session_state.dbscan_min_samples),
            )
        except Exception as e:
            cpts, cents, cmeta = pts.copy(), pd.DataFrame(), {"status": "FAILED", "error": str(e)[:200]}

        if cpts.empty:
            st.warning("No points available for clustering.")
        else:
            fig_map = cluster_map_figure(cpts, cents, st.session_state.cluster_algo)
            st.plotly_chart(fig_map, use_container_width=True)

            st.markdown('<div class="glass-card" style="padding:14px;">', unsafe_allow_html=True)
            st.subheader("Cluster Table")
            show = cpts[
                ["state_name_norm", "district_name_norm", "cluster_label", "risk_level", "risk_score", "total_crime", "lat", "lon"]
            ].rename(
                columns={
                    "state_name_norm": "State",
                    "district_name_norm": "District",
                    "cluster_label": "Cluster",
                    "risk_level": "Risk Level",
                    "risk_score": "Risk Score",
                    "total_crime": "Latest-Year Total",
                }
            ).sort_values(["Cluster", "Risk Score"], ascending=[True, False])
            st.dataframe(show, use_container_width=True, height=420)
            st.caption(f"Clustering meta: {cmeta}")
            st.markdown("</div>", unsafe_allow_html=True)

            log_action("Clustering Run", details=json.dumps({k: str(v) for k, v in cmeta.items()}))

    # TAB: Data & Export
    with tabs[14]:
        st.markdown('<div class="section-header">📂 Data Explorer & Export</div>', unsafe_allow_html=True)
        st.info("Preview is limited to prevent browser crashes. Export is guarded and logged. Button label preserved: 📥 DOWNLOAD SITREP")

        MAX_ROWS = 5000
        if filtered_df.empty:
            st.warning("No rows to preview/export for current filters.")
        else:
            preview = (filtered_pulsed_df if use_pulsed else filtered_df).head(MAX_ROWS)
            st.caption(f"Showing first {len(preview):,} rows (limit: {MAX_ROWS:,})")
            st.dataframe(preview, use_container_width=True, height=420)

        # Export controls (security hardening)
        st.markdown('<div class="glass-card" style="padding:14px; margin-top:12px;">', unsafe_allow_html=True)
        st.subheader("Export Module (SITREP)")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.session_state.export_row_cap = st.number_input(
                "Export Row Cap",
                min_value=1000,
                max_value=500000,
                value=int(st.session_state.export_row_cap),
                step=1000,
                help="Hard cap on exported rows.",
            )
        with c2:
            st.session_state.export_guard_max_results = st.number_input(
                "Search Result Guard",
                min_value=5000,
                max_value=2000000,
                value=int(st.session_state.export_guard_max_results),
                step=5000,
                help="Blocks export if result size exceeds this threshold unless override is enabled.",
            )
        with c3:
            st.session_state.export_allow_large = st.toggle(
                "Override Guard (Admin)",
                value=bool(st.session_state.export_allow_large),
                help="Enable only for authorised bulk exports.",
            )

        audit_id = _export_audit_id()
        export_df, export_meta = validate_export_request(
            filtered_pulsed_df if use_pulsed else filtered_df,
            row_cap=int(st.session_state.export_row_cap),
            guard_max_results=int(st.session_state.export_guard_max_results),
            allow_large=bool(st.session_state.export_allow_large),
        )

        st.caption(f"Export audit ID (include in SITREP): **{audit_id}**")
        if export_meta.get("status") == "GUARD_BLOCK":
            st.error(f"Export blocked: {export_meta.get('reason','')}")
        elif export_meta.get("status") == "TRUNCATED":
            st.warning(f"Export truncated: {export_meta.get('reason','')}")
        elif export_meta.get("status") == "EMPTY":
            st.warning("Nothing to export.")
        else:
            st.success(f"Export ready: {len(export_df):,} row(s)")

        if not export_df.empty:
            csv_bytes = export_df.to_csv(index=False).encode("utf-8")
            if st.download_button(
                "📥 DOWNLOAD SITREP",
                data=csv_bytes,
                file_name=f"crimewatch_sitrep_{audit_id}.csv",
                mime="text/csv",
            ):
                # Log export with context
                ctx = {
                    "audit_id": audit_id,
                    "filters": {
                        "year_range": st.session_state.year_range,
                        "state": st.session_state.state,
                        "district": st.session_state.district,
                        "category": st.session_state.category,
                        "live_pulse": st.session_state.live_pulse,
                    },
                    "export_meta": export_meta,
                }
                log_action("Export SITREP", details=json.dumps({k: str(v) for k, v in ctx.items()}))

        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# 🧠 MAIN ORCHESTRATION
# Main Flow Requirement:
# 1. load data
# 2. live pulse controls
# 3. filters
# 4. header
# 5. empty-state handling
# 6. intelligence briefing
# 7. KPIs
# 8. visuals (map + cluster + trend + distribution)
# 9. anomaly/warning system
# 10. model governance panel
# 11. export module
# 12. ticker + footer
# 13. audit log summary event
# ============================================================
def main() -> None:
    # CHANGE: validate canonical config before running (required)
    ok, cfg_meta = validate_canonical_config()
    if not ok:
        log_action("Canonical Config Invalid", details=json.dumps({k: str(v) for k, v in cfg_meta.items()}))
        st.error("🚨 CONFIG ERROR: Canonical dropdown configuration is invalid. Fix DISTRICTS_BY_STATE / CRIME_CATEGORIES.")
        st.stop()

    # 1) Load data (load once)
    df = load_crime_data(seed=42, schema_version=DATASET_SCHEMA_VERSION)

    # CHANGE: detect stale cached dataset; clear cache once; reload once
    if is_cached_dataset_stale(df):
        log_action(
            "Cache Cleared",
            details="Cached dataset stale/incomplete vs canonical STATE_CENTROIDS/DISTRICTS_BY_STATE/CRIME_CATEGORIES; reloading.",
        )
        st.cache_data.clear()
        df = load_crime_data(seed=42, schema_version=DATASET_SCHEMA_VERSION)

    init_session_state(df)

    # 4) Header (render early)
    render_header()

    # 3) Filters + 2) Live pulse controls inside control panel
    render_control_panel(df)

    log_action(
        "Filters Applied",
        details=f"Year: {st.session_state.year_range}, State: {st.session_state.state}, "
        f"District: {st.session_state.district}, Category: {st.session_state.category}, "
        f"Pulse: {st.session_state.live_pulse}, Sensitivity: {st.session_state.sensitivity}",
    )

    # Apply pulse globally then filter for pulsed and raw paths
    df_pulsed = apply_live_pulse(
        df,
        enabled=bool(st.session_state.live_pulse),
        intensity=float(st.session_state.pulse_intensity),
        sensitivity=float(st.session_state.sensitivity),
    )

    filtered_df = get_filtered_data(
        df,
        tuple(st.session_state.year_range),
        str(st.session_state.state),
        str(st.session_state.district),
        str(st.session_state.category),
    )
    filtered_pulsed_df = get_filtered_data(
        df_pulsed,
        tuple(st.session_state.year_range),
        str(st.session_state.state),
        str(st.session_state.district),
        str(st.session_state.category),
    )

    # 5) Empty-state handling
    if filtered_df.empty:
        render_empty_state(df, filtered_df)

    use_pulsed = bool(st.session_state.live_pulse)

    # 8) Core visuals data
    yearly = yearly_aggregate(filtered_pulsed_df if use_pulsed else filtered_df, use_pulsed=use_pulsed)

    # Risk scoring
    risk_all_years = risk_scoring_engine_all_years(filtered_pulsed_df if use_pulsed else filtered_df, use_pulsed=use_pulsed)
    risk_latest = risk_scoring_engine_latest(filtered_pulsed_df if use_pulsed else filtered_df, use_pulsed=use_pulsed)

    # Build spikes (rule-based)
    YEAR_MAX = int((filtered_pulsed_df if use_pulsed else filtered_df)["year"].max())
    spikes_df = early_warning_engine(
        filtered_pulsed_df if use_pulsed else filtered_df,
        YEAR_MAX,
        spike_threshold_pct=float(st.session_state.ew_pct),
        spike_threshold_abs=float(st.session_state.ew_abs),
        use_pulsed=use_pulsed,
    )

    # Patrol plan
    patrol_df = patrol_prioritization_engine(spikes_df, max_units=20)

    # Strategies
    YEAR_MIN = int((filtered_pulsed_df if use_pulsed else filtered_df)["year"].min())
    strategy_df = prevention_strategy_engine(risk_latest, filtered_pulsed_df if use_pulsed else filtered_df, YEAR_MIN, YEAR_MAX, use_pulsed=use_pulsed)

    # 9) Anomaly system
    anomaly_features = build_anomaly_features(risk_all_years)
    anomaly_cont = float(np.clip(float(st.session_state.anomaly_contamination) * float(st.session_state.sensitivity), 0.01, 0.25))
    try:
        anomaly_df, anomaly_meta = anomaly_detection_isolation_forest(anomaly_features, contamination=anomaly_cont)
    except Exception as e:
        anomaly_df, anomaly_meta = anomaly_features.copy(), {"status": "FAILED", "error": str(e)[:200]}

    # 8) Clustering (cached points + execution)
    points = build_cluster_points(risk_latest)
    try:
        points_clustered, centroids, cluster_meta = run_clustering(
            points,
            algorithm=str(st.session_state.cluster_algo),
            kmeans_k=int(st.session_state.kmeans_k),
            dbscan_eps=float(st.session_state.dbscan_eps),
            dbscan_min_samples=int(st.session_state.dbscan_min_samples),
        )
    except Exception as e:
        points_clustered, centroids, cluster_meta = points.copy(), pd.DataFrame(), {"status": "FAILED", "error": str(e)[:200]}

    # 10) Forecast (baseline strategy uses session state)
    # forecast strategy selector exists in Forecast tab; here we compute initial forecast for briefing/warnings
    fdf, fmeta = run_forecast(yearly, str(st.session_state.forecast_strategy), int(st.session_state.forecast_years_ahead))

    # 6) Intelligence briefing + Warning panel
    render_briefing(risk_latest, fmeta, anomaly_meta, spikes_df)
    render_warning_panel(filtered_df, spikes_df, anomaly_df, fmeta)

    # 7) KPIs
    kpi = render_kpis(filtered_df, risk_latest)

    # 8) Prepare supervised model (D)
    X, y, ds_meta = build_supervised_dataset(risk_all_years)
    try:
        supervised_result = train_risk_predictor(X, y, model_preference="Auto")
    except Exception as e:
        supervised_result = {"status": "FAILED", "reason": str(e)[:200]}

    # 8/10/11) Tabs include visuals, clustering, governance, export, etc.
    render_tabs(
        df_raw=df,
        df_pulsed=df_pulsed,
        filtered_df=filtered_df,
        filtered_pulsed_df=filtered_pulsed_df,
        use_pulsed=use_pulsed,
        risk_all_years=risk_all_years,
        risk_latest=risk_latest,
        anomaly_df=anomaly_df,
        anomaly_meta=anomaly_meta,
        spikes_df=spikes_df,
        patrol_df=patrol_df,
        strategy_df=strategy_df,
        yearly=yearly,
        forecast_df=fdf,
        forecast_meta=fmeta,
        points_clustered=points_clustered,
        centroids=centroids,
        cluster_meta=cluster_meta,
        supervised_result=supervised_result,
    )

    # 12) Ticker + Footer
    render_ticker(
        year_range=tuple(st.session_state.year_range),
        state=str(st.session_state.state),
        district=str(st.session_state.district),
        category=str(st.session_state.category),
        total_crimes=int(kpi.get("total_crimes", 0)),
        critical_count=int(kpi.get("critical_count", 0)),
    )
    render_footer()

    # 13) Audit summary event
    summary = {
        "filters": {
            "year_range": st.session_state.year_range,
            "state": st.session_state.state,
            "district": st.session_state.district,
            "category": st.session_state.category,
        },
        "live_pulse": st.session_state.live_pulse,
        "kpis": {k: str(v) for k, v in kpi.items()},
        "forecast": {k: str(v) for k, v in fmeta.items()},
        "anomaly": {k: str(v) for k, v in anomaly_meta.items()},
        "clusters": {k: str(v) for k, v in cluster_meta.items()},
        "supervised": {"status": str(supervised_result.get("status")), "model_used": str(supervised_result.get("model_used", ""))},
    }
    log_action("Dashboard Viewed", details=json.dumps(summary))

 
if __name__ == "__main__":
    main()
