# 🚀 Mission Readiness & Predictive Maintenance

## 🎯 Problem Statement

Industrial equipment such as pumps, motors, compressors, and generators can develop faults due to abnormal temperature, vibration, pressure, and voltage conditions. Unexpected equipment failures can cause downtime, maintenance costs, and reduced operational efficiency.

Our project provides a Mission Readiness & Predictive Maintenance dashboard that monitors equipment health, detects abnormal sensor readings, and provides health scores and failure-risk indicators to help maintenance teams identify potential issues early.

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
