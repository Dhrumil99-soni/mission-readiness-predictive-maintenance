# 🚀 VYOM 

## 🎯 Problem Statement

Industrial equipment such as pumps, motors, compressors, and generators can develop faults due to abnormal temperature, vibration, pressure, and voltage conditions. Unexpected equipment failures can cause downtime, maintenance costs, and reduced operational efficiency.

Our project provides a Mission Readiness & Predictive Maintenance dashboard that monitors equipment health, detects abnormal sensor readings, and provides health scores and failure-risk indicators to help maintenance teams identify potential issues early.
## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | VYOM |
| **Track** | Open |
| **Team Lead** | PATEL HARSH BHUPENDRA — 24ec102@charusat.edu.in |
| **Members** | DHRUMIL SONI, PATEL OM VIPULKUMAR, PATEL DHRUV DIVYESHKUMAR |

#Solution 
We developed an AI-based predictive maintenance system that analyzes equipment/operational data to identify abnormal patterns and predict potential maintenance requirements. The system helps users take preventive action before a failure occurs, improving equipment availability, reducing unexpected downtime, and supporting mission readiness.

## 🎥 Demo & Presentation

- 📊 [View Project Presentation](https://ap.wps.com/cms/docs/d/cbCaeanGDDctt1Lf?sa=601.1074&refer=copylink)
- 🎬🖥️ [View Demo Video & Screenshots](https://drive.google.com/drive/folders/128teVwtAO06y-rWeGMqOT8_fGlTP8NVS)

#Key Features

Feature 1: AI-based predictive maintenance for identifying potential equipment failures.
Feature 2: Analysis of equipment data to detect abnormal operating patterns.
Feature 3: Early warning of possible maintenance requirements.
Feature 4: Supports proactive maintenance decisions and reduces unexpected downtime.
Feature 5: User-friendly presentation of predictions and maintenance insights.

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Frontend** | Web-based Dashboard |
| **Backend** | Application Backend |
| **Data / Sensors** | Sensor Data |
| **AI / ML** | Predictive Maintenance / Failure-Risk Analysis |
| **Version Control** | Git, GitHub |

#How to Run
# 1. Clone the repository
git clone https://github.com/Dhrumil99-soni/mission-readiness-predictive-maintenance.git

# 2. Enter the project folder
cd mission-readiness-predictive-maintenance

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py

This repository contains two independent projects:

| Project | Description | Location |
|---|---|---|
| **Study Assistant MCP** | AI-powered local study notes server (MCP protocol) | `server.py`, `notes/` |
| **Mission Readiness & Predictive Maintenance** | Web dashboard for equipment health monitoring | `predictive_maintenance/` |

---

> Full documentation: [`predictive_maintenance/README.md`](predictive_maintenance/README.md)

A web-based predictive maintenance system that monitors industrial equipment sensors, detects anomalies, estimates failure probability, and recommends maintenance actions — **no external hardware or cloud services required**.

### Quick Start

```bash
cd predictive_maintenance
python server.py
```

Open **http://localhost:8080** in your browser.

**Requires:** Python 3.9+ · Internet connection for Chart.js CDN

### What You'll See

- **4 equipment units** (Pump, Motor, Compressor, Generator) with realistic sensor profiles
- **Health Score (0–100)** and **Failure Probability (%)** per unit
- **Healthy / Warning / Critical** classification with colour-coded indicators
- **Anomaly detection** highlighting which sensors are out of range
- **Trend charts** updating every 5 seconds
- **Maintenance recommendations** prioritised by severity
- **Custom sensor input** — type in any values and get an instant analysis

---

## Study Assistant MCP Server

An MCP server that exposes your local Markdown study notes to AI assistants like Bob.

### Quick Start

```bash
pip install mcp
python server.py
```

### Tools exposed

| Tool | Description |
|---|---|
| `search_notes` | Keyword search across all `.md`/`.txt` notes |
| `read_note` | Read the full content of a specific note file |
| `ask_study_question` | Semantic search + composed study response |

Study notes live in the `notes/` directory.

---

## Repository Structure

```
study-assistant-mcp/
├── predictive_maintenance/    ← Predictive Maintenance web app
│   ├── server.py
│   ├── engine.py
│   ├── mock_data.py
│   ├── static/
│   │   ├── index.html
│   │   ├── app.js
│   │   └── style.css
│   └── README.md
├── notes/                     ← Study notes (Markdown)
│   ├── calculus.md
│   ├── data-structures.md
│   ├── linear-algebra.md
│   ├── organic-chemistry.md
│   └── physics-newton.md
├── server.py                  ← MCP study assistant server
├── src/index.ts               ← TypeScript stub
└── package.json
```
## ⚠️ Known Limitations

- The accuracy of failure-risk predictions depends on the quality and availability of sensor data.
- The current system is designed as a prototype and may require further testing with real-world industrial equipment.
- The dashboard provides predictive insights to support maintenance decisions but does not replace professional inspection or maintenance procedures.
- Performance may vary when the system is used with equipment or sensor conditions different from the data used during development.

## 🏅 What We're Most Proud Of

We are most proud of building a web-based Mission Readiness & Predictive Maintenance dashboard that turns sensor data into clear, actionable equipment-health insights. The dashboard makes it easy for maintenance teams to identify Healthy, Warning, and Critical equipment and take action before potential failures impact mission readiness.