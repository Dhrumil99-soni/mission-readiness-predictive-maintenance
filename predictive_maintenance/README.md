# Mission Readiness & Predictive Maintenance

A web-based predictive maintenance proof-of-concept built for a student hackathon.  
Detects abnormal equipment behaviour, estimates failure probability, and shows prioritised maintenance actions — **no external hardware or cloud services required**.

---

## Problem Statement

Unplanned industrial equipment failure causes costly downtime, safety incidents, and rushed emergency repairs.  
Most small organisations cannot afford enterprise SCADA or IoT platforms, yet even basic sensor monitoring and rule-based alerting can prevent the majority of avoidable failures.

---

## Proposed Solution

A lightweight, single-server web application that:

1. Accepts real-time or mocked sensor readings (temperature, vibration, pressure, voltage, current, operating hours, error codes).
2. Applies **threshold-based anomaly detection** to each sensor.
3. Computes an explainable **Health Score (0–100)** and **Failure Probability (%)**.
4. Classifies each equipment unit as **Healthy**, **Warning**, or **Critical**.
5. Surfaces which sensors are outside safe ranges and why.
6. Generates prioritised, human-readable **maintenance recommendations**.
7. Displays live-updating **trend charts** for all key sensors.

---

## Features

| Feature | Details |
|---|---|
| Equipment overview | Sidebar with health bars and status badges for all units |
| Live sensor tiles | Colour-coded tiles showing current value, level, and threshold band |
| Anomaly list | All triggered threshold violations with severity |
| Health & risk KPIs | Health Score and Failure Probability shown prominently |
| Trend charts | 30-point rolling line charts for 6 sensor streams |
| Maintenance actions | Prioritised, equipment-specific recommendations |
| Custom input form | Enter arbitrary sensor values and get instant analysis |
| Auto-refresh | Dashboard polls every 5 seconds — no page reload needed |

---

## Architecture

```
Browser (HTML + Vanilla JS + Chart.js CDN)
        │
        │  HTTP (localhost:8080)
        ▼
predictive_maintenance/server.py     ← stdlib HTTPServer, routes requests
        │
        ├── mock_data.py             ← generates realistic noisy sensor readings
        └── engine.py                ← threshold analysis, scoring, recommendations
```

All logic runs in a single Python process.  No database, no external API, no npm build step.

### File Layout

```
predictive_maintenance/
├── server.py          — HTTP server and routing
├── engine.py          — analysis engine (anomaly detection, health score, recommendations)
├── mock_data.py       — mock sensor profiles and history generator
└── static/
    ├── index.html     — single-page dashboard shell
    ├── app.js         — dashboard logic (fetch, render, charts)
    └── style.css      — dark-theme styles
```

---

## Risk & Health Calculation Methodology

> **Note:** This is a **rule-based heuristic model, not a trained ML model.**  
> All thresholds and weights are explicitly documented and can be tuned in `engine.py`.

### Sensor Thresholds

| Sensor | Normal | Warning | Critical |
|---|---|---|---|
| Temperature | ≤ 80 °C | 80–95 °C | > 95 °C |
| Vibration | ≤ 2.5 mm/s | 2.5–4 mm/s | > 4 mm/s |
| Pressure | ≤ 8 bar | 8–10 bar | > 10 bar |
| Voltage | 210–250 V | 200–210 / 250–260 V | < 200 or > 260 V |
| Current | ≤ 15 A | 15–20 A | > 20 A |
| Fault codes | 0 | 1–2 | ≥ 3 |

### Health Score (0–100)

```
health_score = 100 − Σ( penalty for each sensor outside its safe range )

  Sensor        Warning penalty   Critical penalty
  temperature       15 pts            30 pts
  vibration         18 pts            40 pts
  pressure          12 pts            25 pts
  voltage           10 pts            22 pts
  current           10 pts            22 pts
  error_codes        8 pts            20 pts
```

### Failure Probability (0–100%)

```
base_risk    = 100 − health_score
wear_factor  = min(10, operating_hours / 800)   if hours ≥ 8 000 else 0
failure_prob = min(100, base_risk + wear_factor)
```

### Classification

| Health Score | Status |
|---|---|
| 75–100 | ✅ Healthy |
| 45–74 | ⚠️ Warning |
| 0–44 | 🔴 Critical |

---

## Mock Equipment Profiles

The four built-in equipment units are designed to produce a spread of health states:

| ID | Unit | Scenario | Expected State |
|---|---|---|---|
| PUMP-01 | Centrifugal Pump 01 | All sensors in normal range | ✅ Healthy |
| MOTOR-02 | Drive Motor 02 | Elevated temperature, one fault code | ⚠️ Warning |
| COMPRESSOR-03 | Air Compressor 03 | High vibration, near-critical temperature, three fault codes | 🔴 Critical |
| GENERATOR-04 | Standby Generator 04 | Slightly high voltage, one fault code | ⚠️ Warning–Healthy border |

Small random noise is added on every poll so readings drift naturally over time.

---

## Technologies Used

| Layer | Technology |
|---|---|
| Backend | Python 3.9+ stdlib (`http.server`, `json`, `urllib`) |
| Frontend | HTML5, Vanilla JS (ES2022), CSS custom properties |
| Charts | [Chart.js 4.4](https://www.chartjs.org/) (CDN, no install) |
| Data | In-memory mock data — no database |

Zero pip installs required.

---

## How to Run

### Prerequisites

- Python 3.9 or later
- Internet connection (for Chart.js CDN on first load)

### Start the server

```bash
cd predictive_maintenance
python server.py
```

Open your browser at **http://localhost:8080**

### Optional: change the port

Edit the `PORT = 8080` constant at the top of `server.py`.

---

## Example Demo Workflow

1. **Open the dashboard** — four equipment cards appear in the sidebar with live health bars.
2. **Notice the spread** — PUMP-01 is green (Healthy), MOTOR-02 amber (Warning), COMPRESSOR-03 red (Critical).
3. **Click COMPRESSOR-03** — see the anomaly list showing high vibration and temperature, three active fault codes.
4. **Read the recommendations** — prioritised actions appear: "Stop equipment immediately — excessive vibration…"
5. **Watch the charts** — Health Score and Failure Probability trend lines update every 5 seconds.
6. **Try the custom form** — expand "Analyse Custom Sensor Values", set temperature to 100 °C and vibration to 5 mm/s, click **Run Analysis** to see the engine's response instantly.
7. **Click Refresh Now** — forces an immediate refresh without waiting for the next poll.

---

## Limitations & Future Improvements

| Limitation | Possible Improvement |
|---|---|
| Rule-based thresholds only | Replace or augment with a trained anomaly-detection model (Isolation Forest, LSTM) |
| In-memory history (resets on restart) | Persist readings to SQLite or a time-series DB |
| Simulated sensor data | Connect to real sensors via MQTT, OPC-UA, or Modbus |
| Fixed thresholds per sensor type | Make thresholds configurable per equipment unit via a settings file |
| No authentication | Add simple API-key or session auth for production use |
| Single-machine deployment | Containerise with Docker; deploy to cloud or edge device |
