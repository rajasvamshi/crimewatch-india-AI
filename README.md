# 🛰️ CrimeWatch India – AI Crime Intelligence Command Center

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Transform fragmented NCRB crime data into proactive, decision-support intelligence for public safety.

## 🎯 Overview

CrimeWatch India is an AI-driven Crime Intelligence Command Center that:
- ✅ Identifies where crimes happen (heatmaps, geo-clustering)
- ✅ Detects when crimes spike (early warning engine)
- ✅ Prioritizes patrol deployment (resource-constrained optimization)
- ✅ Enables preventive strategies (category-specific recommendations)
- ✅ Ensures ethical AI use (audit logging, human-in-the-loop)

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/crimewatch-india.git
cd crimewatch-india

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run dashboard
streamlit run app/dashboard.py

# Open browser to http://localhost:8501

📊 Key Features
Feature
Description
🔥 Risk Scoring
Volume + Growth + Volatility weighted risk levels (CRITICAL/HIGH/MEDIUM/LOW)
🚨 Early Warning
Rule-based spike detection with YoY % and absolute thresholds
📈 Forecasting
ARIMA (Advanced) with Linear (Fast) fallback + 95% confidence intervals
🧨 Anomaly Detection
IsolationForest with sensitivity scaling
🗺️ Geo-Clustering
KMeans (centroids) + DBSCAN (noise-aware) hotspot grouping
🧠 Risk Prediction
RandomForest/XGBoost supervised prediction of next-year risk bucket
🚓 Patrol Prioritization
Unit allocation under resource constraints
🛡️ Prevention Strategy
Category-specific action recommendations by risk level
📝 Executive Reports
Auto-generated Markdown reports for leadership
🔒 Governance
Audit logging, export guards, drift detection, fairness placeholders


🎨 UI/UX
Cinematic tactical HUD theme with glassmorphism
15 interactive tabs: Overview, Hotspots, Drilldown, Heatmaps, Forecast...
Live pulse simulation for streaming feed emulation
Required CSS classes preserved for enterprise integration
🔐 Security & Ethics
All actions logged to crimewatch_audit.log with audit IDs
Export guards prevent bulk data exfiltration
Aggregated data only – no PII collected or stored
Human-in-the-loop required for CRITICAL risk flags
Quarterly drift/fairness audits mandated for production


crimewatch/
├── app/
│   └── dashboard.py          # Main application (~4,500 lines)
├── assets/
│   └── india_states.geojson  # Geospatial data
├── data/
│   ├── raw/                  # NCRB CSVs (production)
│   └── processed/            # master_crime_long.csv
├── src/
│   ├── build_master_dataset_v2.py  # Production preprocessing
│   └── geojson_builder.py
├── requirements.txt
├── .gitignore
├── README.md
└── crimewatch_audit.log      # Auto-generated

# Run with synthetic data (default)
streamlit run app/dashboard.py

# Test with specific seed
# (Modify load_crime_data(seed=...) in main())

# Check audit log
tail -f crimewatch_audit.log

🚢 Deployment
See DEPLOYMENT.md for Docker, AWS, GCP, and Azure guides.
🤝 Contributing
Fork the repository
Create a feature branch (git checkout -b feature/amazing-feature)
Commit changes (git commit -m 'Add amazing feature')
Push to branch (git push origin feature/amazing-feature)
Open a Pull Request
📄 License
Distributed under the MIT License. See LICENSE for more information.
🙏 Acknowledgments
National Crime Records Bureau (NCRB) for open data
Streamlit community for the amazing framework
Plotly for interactive visualizations
Scikit-learn, XGBoost, Statsmodels for ML capabilities


---

# 12. FUTURE ROADMAP

## 12.1 Immediate Next Steps (Priority 1 – 0-4 Weeks)

| Feature | Description | Effort | Impact | Status | Dependencies |
|---------|-------------|--------|--------|--------|-------------|
| Connect Real NCRB Data | Replace synthetic generator with production pipeline from `src/build_master_dataset_v2.py` | Medium | High | ⏳ Pending | NCRB data access, schema validation |
| Production Data Pipeline | Implement schema validation, error handling, incremental loads | High | High | ⏳ Pending | Real NCRB data, testing framework |
| Docker Containerization | Finalize Dockerfile + docker-compose for reproducible deployment | Low | Medium | ⏳ Pending | None |
| Cloud Deployment (AWS/GCP) | Deploy to Elastic Beanstalk or Cloud Run with monitoring | Medium | High | ⏳ Pending | Cloud account, CI/CD setup |

## 12.2 Short-Term Enhancements (Priority 2 – 1-3 Months)

| Feature | Description | Timeline | Dependencies | Strategic Value |
|---------|-------------|----------|--------------|----------------|
| Monthly/Temporal Data | Add month-level granularity for seasonality analysis | 2-4 weeks | NCRB monthly data access | Improved forecasting accuracy, seasonal patrol planning |
| ML-Based Forecasting | Prophet for seasonality, LSTM for deep learning forecasts | 4-6 weeks | Sufficient temporal data, GPU for LSTM | Higher forecast accuracy, complex pattern detection |
| Role-Based Access Control | Analyst vs Commander views, authentication system | 3-4 weeks | Identity provider integration (Auth0, Cognito) | Security compliance, user-specific workflows |
| Real-Time Data Ingestion | API connectors for live crime reporting feeds | 6-8 weeks | Police department API access, WebSocket support | Near-real-time intelligence, faster response |
| Mobile-Responsive UI | Optimize dashboard for tablet/field commander use | 2-3 weeks | CSS refactoring, touch-friendly controls | Field usability, broader adoption |

## 12.3 Long-Term Vision (Priority 3 – 3-12 Months)

| Feature | Description | Timeline | Strategic Value | Technical Approach |
|---------|-------------|----------|----------------|-------------------|
| Mobile Command App | iOS/Android app for field commanders with offline sync | 3-6 months | Operational reach, field decision support | React Native, offline-first architecture, sync engine |
| Integration with CAD/RMS | Connect to existing police Computer-Aided Dispatch/Records Management Systems | 6-12 months | Workflow integration, reduced manual entry | REST API adapters, data mapping, authentication |
| Predictive Policing ML | Advanced spatiotemporal models (ST-ResNet, Graph Neural Nets) | 6-12 months | Proactive prevention, resource optimization | PyTorch/TensorFlow, graph databases, spatial indexing |
| Multi-Nation Expansion | Adapt canonical mappings for other countries' administrative structures | 12+ months | Scalable platform, global impact | Config-driven mappings, i18n, modular architecture |
| Natural Language Query | "Show me districts with rising cyber crime" → auto-filter + visualization | 4-6 months | Accessibility, non-technical user empowerment | LLM fine-tuning, intent classification, query parser |

## 12.4 Technical Debt Items

| Item | Risk | Mitigation Strategy | Priority | Owner |
|------|------|---------------------|----------|-------|
| Synthetic Data in Demo | May confuse stakeholders about data provenance | Clear labeling in UI, production pipeline toggle, documentation | High | Product |
| Fairness Placeholders | Incomplete compliance for government deployment | Add validated metrics + ethics review before production | High | Ethics Committee |
| Hardcoded Thresholds | May not generalize across regions/time | Make configurable via admin panel + document rationale | Medium | Engineering |
| Single-File Dashboard | Hard to maintain, test, extend | Modularize into packages (engines/, ui/, data/) | Medium | Engineering |
| Limited Error Recovery | Some failures stop entire dashboard | Add granular try/except per engine with fallback UI | Medium | Engineering |

---

# 13. APPENDICES

## Appendix A: Complete Function Index

| Function | Category | Lines | Purpose | Key Parameters | Return Type |
|----------|----------|-------|---------|---------------|------------|
| `log_action()` | Security | 5 | Audit logging | action, user, details | None |
| `normalize_name()` | Helper | 6 | Text normalization | x (Any) | str |
| `format_number()` | Helper | 10 | Number formatting (K/M) | n (Any) | str |
| `normalize_series()` | Helper | 8 | 0-100 scaling | series (pd.Series) | pd.Series |
| `apply_tactical_theme()` | Helper | 25 | Plotly theming | fig (go.Figure) | go.Figure |
| `_has_module()` | Helper | 3 | Optional dependency check | module_name (str) | bool |
| `_stable_hash_int()` | Helper | 5 | Deterministic hash for jitter | s (str) | int |
| `_stable_jitter_pair()` | Helper | 6 | Geo-jitter for demo realism | key, scale_lat, scale_lon | Tuple[float, float] |
| `validate_canonical_config()` | Data | 20 | Config validation | None | Tuple[bool, Dict] |
| `is_cached_dataset_stale()` | Data | 35 | Cache integrity check | df (pd.DataFrame) | bool |
| `_geo_lat_lon()` | Data | 10 | Geo-coordinate generation | state_name_norm, district_name_norm | Tuple[float, float] |
| `load_crime_data()` | Data | 80 | Synthetic data generation | seed, schema_version | pd.DataFrame |
| `init_session_state()` | Session | 25 | State initialization | df (pd.DataFrame) | None |
| `apply_live_pulse()` | Data | 35 | Live simulation | df_in, enabled, intensity, sensitivity | pd.DataFrame |
| `get_filtered_data()` | Data | 15 | Filtering | df, year_range, state, district, category | pd.DataFrame |
| `yearly_aggregate()` | Data | 10 | Time aggregation | df_in, use_pulsed | pd.DataFrame |
| `_classify_risk()` | ML | 5 | Risk level classification | score (float) | str |
| `risk_scoring_engine_all_years()` | ML | 45 | Risk calculation | df_in, use_pulsed | pd.DataFrame |
| `risk_scoring_engine_latest()` | ML | 10 | Latest risk snapshot | df_in, use_pulsed | pd.DataFrame |
| `early_warning_engine()` | ML | 30 | Spike detection | df_in, year_max, thresholds, use_pulsed | pd.DataFrame |
| `patrol_prioritization_engine()` | ML | 35 | Unit allocation | alerts_df, max_units | pd.DataFrame |
| `prevention_strategy_engine()` | ML | 40 | Action recommendations | hotspots_df, base_df, year_min, year_max, use_pulsed | pd.DataFrame |
| `executive_report_engine()` | Report | 50 | Markdown report | hotspots_df, warnings_df, patrol_df, filtered_df | str |
| `_safe_mape()` | ML | 5 | MAPE calculation with smoothing | y_true, y_pred | float |
| `forecast_linear()` | ML | 40 | Linear forecasting | yearly, years_ahead | Tuple[pd.DataFrame, Dict] |
| `forecast_arima_advanced()` | ML | 45 | ARIMA forecasting | yearly, years_ahead | Tuple[pd.DataFrame, Dict] |
| `run_forecast()` | ML | 50 | Strategy selector | yearly, strategy, years_ahead | Tuple[pd.DataFrame, Dict] |
| `build_anomaly_features()` | ML | 20 | Feature matrix for anomalies | risk_all_years | pd.DataFrame |
| `anomaly_detection_isolation_forest()` | ML | 40 | Anomaly detection | feat_df, contamination, random_state | Tuple[pd.DataFrame, Dict] |
| `build_cluster_points()` | ML | 15 | Geo-risk points for clustering | risk_latest | pd.DataFrame |
| `run_clustering()` | ML | 60 | Geo-clustering | points_df, algorithm, params | Tuple[pd.DataFrame, pd.DataFrame, Dict] |
| `cluster_map_figure()` | ML | 30 | Map visualization | points_clustered, centroids, algorithm | go.Figure |
| `build_supervised_dataset()` | ML | 30 | Training data for prediction | risk_all_years | Tuple[pd.DataFrame, pd.Series, Dict] |
| `train_risk_predictor()` | ML | 70 | Supervised learning | X, y, model_preference, random_state | Dict |
| `figure_confusion_matrix()` | ML | 15 | Confusion matrix viz | cm, labels, title | go.Figure |
| `figure_feature_importances()` | ML | 20 | Feature importance viz | feature_names, importances, title | go.Figure |
| `psi()` | Governance | 20 | Drift metric | expected, actual, bins | float |
| `drift_checks_by_state()` | Governance | 30 | Drift analysis | df_in, use_pulsed | pd.DataFrame |
| `governance_alert_metrics()` | Governance | 25 | Proxy metrics | spikes_df, anomalies_df | Dict |
| `_export_audit_id()` | Security | 5 | Audit ID generation | None | str |
| `validate_export_request()` | Security | 25 | Export guards | filtered_df, row_cap, guard_max_results, allow_large | Tuple[pd.DataFrame, Dict] |
| `render_header()` | UI | 20 | Header HTML | None | None |
| `render_control_panel()` | UI | 80 | Filter controls | df | None |
| `render_empty_state()` | UI | 15 | Empty state UI | df, filtered_df | None |
| `render_briefing()` | UI | 40 | Intelligence briefing | risk_latest, forecast_meta, anomaly_meta, spikes_df | None |
| `render_warning_panel()` | UI | 30 | Warning panel | filtered_df, spikes_df, anomalies_df, forecast_meta | None |
| `render_kpis()` | UI | 60 | KPI cards | filtered_df, risk_latest | Dict[str, Any] |
| `correlation_analysis()` | UI | 20 | Correlation chart | filtered_df, use_pulsed | go.Figure |
| `seasonality_placeholder()` | UI | 25 | Seasonality chart | filtered_df | go.Figure |
| `render_ticker()` | UI | 20 | Live ticker | year_range, state, district, category, total_crimes, critical_count | None |
| `render_footer()` | UI | 30 | Footer HTML | None | None |
| `render_tabs()` | UI | 500+ | All 15 tabs | All engine outputs | None |
| `main()` | Orchestration | 100+ | Main flow | None | None |

## Appendix B: Color Reference (CSS Variables)

```css
:root {
  /* Backgrounds */
  --midnight-void: #020205;          /* Primary background */
  --card-bg: rgba(10,10,18,.72);     /* Glass card background */
  --glass-bg: rgba(10,10,18,.72);    /* Glassmorphism base */
  
  /* Accents */
  --tactical-cyan: #00f3ff;          /* Primary accent, links */
  --deep-cobalt: #0066ff;            /* Secondary accent */
  --intelligence-gold: #e0af68;      /* Warnings, briefing */
  --blood-orange: #ff4d00;           /* Critical alerts */
  --matrix-green: #00ff41;           /* Success, status */
  
  /* Effects */
  --neon-trace: rgba(0,243,255,.22); /* Borders, highlights */
  
  /* Typography */
  --text-primary: #ffffff;           /* Headings, primary text */
  --text-secondary: #a0a0b8;         /* Body text */
  --text-muted: #6b7280;             /* Labels, captions */
  
  /* Transitions */
  --transition-fast: all .25s cubic-bezier(.4,0,.2,1);
  --transition-normal: all .4s cubic-bezier(.4,0,.2,1);
}

Appendix C: Risk Level Reference
Level
Score Range
Color
Visual Indicator
Required Action
SLA
CRITICAL 🔴
≥80
#ff4d00 (Blood Orange)
Pulse animation, red border, .kpi-card.critical
Immediate deployment; SP review within 24h
<24h
HIGH 🟠
60-79
#e0af68 (Intelligence Gold)
Bold highlight, amber border
Priority patrol; enhanced monitoring
<72h
MEDIUM 🟡
40-59
#0066ff (Deep Cobalt)
Standard styling
Routine patrol; intelligence gathering
<1 week
LOW 🟢
<40
#00f3ff (Tactical Cyan)
Dimmed styling
Baseline patrol; periodic review

2025-01-15 14:30:22 - INFO - Action: Data Loaded | User: anonymous | Details: Records: 45,960 | Years: 2017-2022
2025-01-15 14:30:25 - INFO - Action: Filters Applied | User: anonymous | Details: Year: (2020, 2022), State: ALL STATES, District: ALL DISTRICTS, Category: ALL CATEGORIES, Pulse: True, Sensitivity: 1.0
2025-01-15 14:30:30 - INFO - Action: Forecast Run | User: anonymous | Details: {"model": "ARIMA (Advanced)", "mape": "12.5", "status": "OK"}
2025-01-15 14:30:35 - INFO - Action: Export SITREP | User: anonymous | Details: {"audit_id": "20250115T143035Z-A3F7B2C1", "filters": {...}, "export_meta": {"status": "OK"}}
2025-01-15 14:30:40 - INFO - Action: Dashboard Viewed | User: anonymous | Details: {"filters": {...}, "kpis": {...}, "forecast": {...}, "anomaly": {...}}

# Development
streamlit run app/dashboard.py                    # Launch dashboard
streamlit run app/dashboard.py --server.port 8502 # Custom port

# Testing
python -c "from app.dashboard import load_crime_data; df=load_crime_data(); print(df.shape)"  # Test data load
python -c "from app.dashboard import validate_canonical_config; print(validate_canonical_config())"  # Test config

# Docker
docker build -t crimewatch:latest .               # Build image
docker run -p 8501:8501 crimewatch:latest         # Run container
docker-compose up -d                              # Run with compose

# Monitoring
tail -f crimewatch_audit.log                      # View audit log
grep "Export SITREP" crimewatch_audit.log         # Filter export events
grep "CRITICAL" crimewatch_audit.log              # Filter critical events

# Dependencies
pip install -r requirements.txt                   # Install all
pip list --outdated                               # Check for updates
pip install -U scikit-learn statsmodels xgboost   # Update ML libs

# Cache Management
# Clear Streamlit cache (for testing)
# Add to main(): st.cache_data.clear() before load_crime_data()

# Production Deployment (AWS Elastic Beanstalk example)
eb init -p python-3.10 crimewatch-india
eb create crimewatch-prod
eb deploy
eb open

