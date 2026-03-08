# 🛰️ CrimeWatch AI – Sovereign Intelligence HUD

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org)
[![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://crimewatch-india-ai.streamlit.app)
[![GitHub stars](https://img.shields.io/github/stars/rajasvamshi/crimewatch-india-AI?style=social)](https://github.com/rajasvamshi/crimewatch-india-AI)

> **Live Demo**: [https://crimewatch-india-ai.streamlit.app](https://crimewatch-india-ai.streamlit.app)

---

## 📋 Table of Contents
- [Overview](#-overview)
- [Key Features](#-key-features)
- [Technology Stack](#-technology-stack)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Usage](#-usage)
- [Dataset](#-dataset)
- [Ethical Disclaimer](#-ethical-disclaimer)
- [Future Improvements](#-future-improvements)
- [Contributing](#-contributing)
- [License](#-license)
- [Author](#-author)

---

## 🎯 Overview

**CrimeWatch AI** is an interactive crime intelligence command center that transforms nationwide crime datasets into actionable decision-support analytics for monitoring risk patterns, detecting anomalies, and identifying high-risk regions.

The system simulates a strategic intelligence dashboard used for situational awareness and policy analysis, designed with a cinematic tactical HUD interface for mission-critical decision support.

### What It Does
- 🔍 Processes district-level crime data across 30 Indian states
- 📊 Visualizes temporal trends, regional risk concentration, and anomaly patterns
- 🚨 Detects early warning signals and emerging crime spikes
- 📈 Provides predictive insights using statistical forecasting models
- 🎛️ Offers an intuitive command-center interface for rapid interpretation

---

## ✨ Key Features

### Interactive Intelligence Dashboard
Filter and explore crime data by:
- 📅 Year range (2017-2022)
- 📍 State and district
- 🔍 Crime category (Theft, Assault, Cyber Crime, etc.)

### Analytics & Intelligence Engines
| Feature | Description |
|---------|-------------|
| **Crime Trend Analysis** | Visualize historical trends with interactive Plotly charts |
| **Risk Scoring** | Composite risk scores (Volume + Growth + Volatility) |
| **Early Warning Signals** | Rule-based spike detection + IsolationForest anomaly detection |
| **Forecast Engine** | ARIMA/Linear forecasting with confidence intervals |
| **Patrol Prioritization** | Resource-constrained unit allocation recommendations |
| **Prevention Strategies** | Category-specific actionable recommendations |

### Enterprise-Grade UI
- 🎨 Cinematic tactical HUD theme with glassmorphism effects
- 📡 Live pulse simulation for streaming feed emulation
- 🔒 Audit logging and export guards for governance
- ⚖️ Ethical AI compliance notices and human-in-the-loop reminders

---

## 🛠 Technology Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.10+ |
| **Framework** | Streamlit |
| **Data Processing** | Pandas, NumPy |
| **Machine Learning** | Scikit-learn, Statsmodels, XGBoost |
| **Visualization** | Plotly, Plotly Express |
| **Geospatial** | GeoJSON, PyShp |
| **Deployment** | Streamlit Community Cloud |
| **Version Control** | Git + GitHub |
| **Containerization** | Docker (optional) |

---

```markdown
## 🏗 Architecture

```mermaid
graph TD
    A[Raw NCRB-style Crime Data] --> B[Data Processing Pipeline]
    B --> C[Feature Engineering]
    C --> D[Risk/Forecast Analytics Engines]
    D --> E[Streamlit Intelligence Dashboard]
    E --> F[Interactive Visualization & Decision Support]
    
    subgraph "Analytics Engines"
        D1[Risk Scoring]
        D2[Early Warning]
        D3[Forecasting]
        D4[Anomaly Detection]
        D5[Clustering]
    end
    
    D --> D1 & D2 & D3 & D4 & D5

📁 Project Structure
crimewatch-india-AI/
│
├── app/
│   ├── dashboard.py          # Main Streamlit application (~4,500 lines)
│   ├── assets/               # GeoJSON and static assets
│   └── scripts/              # Utility scripts
│
├── data/
│   ├── geo/                  # Geospatial boundary files
│   ├── processed/            # Cleaned master dataset
│   └── raw/                  # Source NCRB-style CSVs
│
├── src/
│   ├── build_master_dataset.py       # Legacy preprocessing
│   ├── build_master_dataset_v2.py    # Current preprocessing pipeline
│   ├── config.py                     # Configuration constants
│   └── data_loader.py                # Data loading utilities
│
├── notebooks/
│   └── 01_exploration_india.ipynb    # Exploratory data analysis
│
├── Dockerfile                  # Containerization config
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── LICENSE                     # MIT License
├── ETHICAL_USE.md              # Ethical use policy
└── .gitignore                  # Git ignore rules

🚀 Installation
Prerequisites
Python 3.10 or higher
pip (Python package manager)
Git
Step-by-Step Setup

1. Clone the repository
git clone https://github.com/rajasvamshi/crimewatch-india-AI.git
cd crimewatch-india-AI

2.Create a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

3.Install dependencies
pip install -r requirements.txt

4.Run the Streamlit app
streamlit run app/dashboard.py

5.Open your browser
http://localhost:8501

🎮 Usage

Getting Started
Launch the dashboard using the installation steps above
Use the Control Panel to filter by year, state, district, or crime category
Explore the 15 interactive tabs:

📌 Overview: Temporal trends and category breakdown
🔥 Hotspots & Risk: Risk-scoring table with drill-down
🎯 Drilldown: State → District → Category → Crime Type navigation
🧊 Heatmaps: District×Year and District×Category concentration
📈 Forecast: ARIMA/Linear forecasting with confidence intervals
🚨 Early Warning: Spike detection and anomaly flags
🚓 Patrol Plan: Resource-constrained unit allocation
🛡️ Prevention Strategy: Category-specific recommendations
🧠 Risk Prediction: Supervised ML model (RandomForest/XGBoost)
🧪 Model Governance: Forecast metrics, drift checks, fairness proxies
⚖️ Ethical Auditor: Compliance notices and bias checks
📝 Executive Report: Auto-generated Markdown report
🗺️ Map & Clusters: Geo-clustering with KMeans/DBSCAN
📂 Data & Export: Data preview with guarded export

Tips
Toggle Live Pulse to simulate streaming feed fluctuations
Adjust AI Sensitivity to control anomaly detection thresholds
Use Quick Filter Presets for common time ranges
Download reports via the Executive Report or Data & Export tabs

📊 Dataset
Source
The dataset represents aggregated crime statistics across Indian states and districts, derived from publicly available reporting sources (NCRB-style schema).
Schema
Column
Type
Description
year
int
Observation year (2017-2022)
state_name
str
State/UT name
district_name
str
District name
category
str
Crime category (10 canonical types)
crime_type
str
Aggregated type (Property/Violent/Special/Other)
crime_count
int
Number of reported incidents
arrests
int
Number of arrests (derived)
lat, lon
float
Geographic coordinates (for visualization)
Coverage
30 States/UTs (29 states + Delhi)
766+ Districts (canonical mapping)
10 Crime Categories (Theft, Assault, Cyber Crime, etc.)
6 Years of temporal data (2017-2022)

⚠️ Note: This demo uses synthetic data for portability. For production use, connect to validated NCRB data pipelines.

⚖️ Ethical Disclaimer

This project is intended strictly for analytical, educational, and demonstration purposes.
Intended Uses ✅
Research on crime analytics methodologies
Educational demonstrations of AI/ML in public safety
Policy analysis and scenario planning (with validated data)
Technology prototyping and stakeholder engagement
Prohibited Uses ❌
Individual-level predictions or targeting
Fully automated enforcement actions without human review
Profiling based on protected characteristics (caste, religion, gender, ethnicity)
Operational policing decisions without official data governance and validation
Required Safeguards
Human-in-the-loop review for all CRITICAL-risk flags
Quarterly drift/fairness audits for production deployments
Public transparency reporting (anonymized where applicable)
Cross-verification with local authorities before operational use
See ETHICAL_USE.md for the complete ethical use policy.

🚀 Future Improvements
Planned enhancements include:
Geospatial Crime Heatmaps: Interactive choropleth maps with real-time updates
Advanced Forecasting: Prophet, LSTM, or spatiotemporal models for seasonality
Per-Capita Normalization: Population-adjusted risk scores for fairer comparisons
Multi-Year Anomaly Detection: Temporal pattern recognition across longer horizons
User Authentication: Role-based access (Analyst/Commander/Admin)
Database Integration: PostgreSQL/MongoDB for persistent storage and scaling
API Endpoints: FastAPI wrapper for external system integration
Mobile-Responsive UI: Optimized views for tablet/field commander use

🤝 Contributing
Contributions are welcome! Here's how to get started:
Fork the repository
Create a feature branch: git checkout -b feature/amazing-feature
Commit your changes: git commit -m 'Add amazing feature'
Push to the branch: git push origin feature/amazing-feature
Open a Pull Request
Development Guidelines
Follow PEP 8 style guidelines for Python code
Add docstrings to new functions and classes
Include tests for new features (if applicable)
Update documentation for user-facing changes
Issues & Feature Requests
Use the GitHub Issues tab to report bugs or suggest features
Search existing issues before creating a new one
Provide clear steps to reproduce bugs

📄 License
This project is released under the MIT License. See the LICENSE file for details.

MIT License

Copyright (c) 2025 Rajavamshi Samudrala

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

👨‍💻 Author
Rajavamshi Samudrala
🔗 GitHub 
🔗 LinkedIn - RAJAVAMSHI SAMUDRALA
✉️ Email- rajasvamshi@gmail.com
🙏 Acknowledgments
National Crime Records Bureau (NCRB) for open data inspiration
Streamlit community for the amazing framework
Plotly for interactive visualization capabilities
Scikit-learn, Statsmodels, and XGBoost for ML capabilities
Open-source contributors whose libraries made this project possible
