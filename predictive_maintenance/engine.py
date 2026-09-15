"""
engine.py — Deterministic predictive maintenance analysis engine.

This module applies threshold-based anomaly detection to sensor readings
and produces an explainable health score, failure-probability estimate,
equipment classification, and prioritised maintenance recommendations.

NOTE: This is a rule-based heuristic model, NOT a trained ML model.
All thresholds and weights are documented below and can be tuned.

───────────────────────────────────────────────────────────────────────────
SENSOR THRESHOLDS
───────────────────────────────────────────────────────────────────────────
Each sensor has three zones:

  NORMAL   → no penalty
  WARNING  → moderate penalty, informational alert
  CRITICAL → high penalty, urgent alert

Thresholds:
  temperature (°C):  normal ≤ 80  |  warning 80–95  |  critical > 95
  vibration (mm/s):  normal ≤ 2.5 |  warning 2.5–4  |  critical > 4
  pressure (bar):    normal ≤ 8   |  warning 8–10   |  critical > 10
  voltage (V):       normal 210–250|  warning 200–210 or 250–260 | critical < 200 or > 260
  current (A):       normal ≤ 15  |  warning 15–20  |  critical > 20
  error_codes:       0 codes=normal|  1–2 codes=warning | ≥3 codes=critical

WEAR FACTOR:
  operating_hours ≥ 8000  → adds up to 10 extra failure-probability points

───────────────────────────────────────────────────────────────────────────
HEALTH SCORE (0–100)
───────────────────────────────────────────────────────────────────────────
Starts at 100.  Each anomalous sensor subtracts a direct point penalty:

  sensor          warning_penalty   critical_penalty
  temperature          15                30
  vibration            18                40
  pressure             12                25
  voltage              10                22
  current              10                22
  error_codes           8                20

  health_score = 100 − Σ(penalty for each triggered sensor)
  Clamped to [0, 100].

───────────────────────────────────────────────────────────────────────────
FAILURE PROBABILITY (0–100 %)
───────────────────────────────────────────────────────────────────────────
  base = (100 − health_score)   ← inverted health
  wear = min(10, operating_hours / 800)  if hours ≥ 8000 else 0
  failure_probability = min(100, base + wear)

───────────────────────────────────────────────────────────────────────────
CLASSIFICATION
───────────────────────────────────────────────────────────────────────────
  health_score 75–100  →  Healthy
  health_score 45–74   →  Warning
  health_score  0–44   →  Critical
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Threshold constants
# ---------------------------------------------------------------------------

THRESHOLDS: dict[str, dict] = {
    "temperature": {
        "unit": "°C",
        "normal_max": 80.0,
        "warning_max": 95.0,
        # no normal_min — 0 is fine for temperature
    },
    "vibration": {
        "unit": "mm/s",
        "normal_max": 2.5,
        "warning_max": 4.0,
    },
    "pressure": {
        "unit": "bar",
        "normal_max": 8.0,
        "warning_max": 10.0,
    },
    "voltage": {
        "unit": "V",
        "normal_min": 210.0,
        "normal_max": 250.0,
        "warning_min": 200.0,
        "warning_max": 260.0,
    },
    "current": {
        "unit": "A",
        "normal_max": 15.0,
        "warning_max": 20.0,
    },
}

# Direct health-score deductions (points subtracted from 100).
# WARNING + CRITICAL deductions are applied at the triggered level only.
#
# Design target so profiles land in expected bands:
#   PUMP-01  (0 anomalies)                          → ~100     Healthy
#   MOTOR-02 (temp warn + 1 err warn)               → ~70-77   Warning
#   COMPRESSOR-03 (temp warn, vib crit, pres warn,
#                  curr warn, 3 err crit)            → ~25-40   Critical
#   GENERATOR-04  (voltage warn + 1 err warn)        → ~78-82   Healthy

WARNING_PENALTY  = {"temperature": 15, "vibration": 18, "pressure": 12,
                    "voltage": 10,     "current": 10,   "error_codes":  8}
CRITICAL_PENALTY = {"temperature": 30, "vibration": 40, "pressure": 25,
                    "voltage": 22,     "current": 22,   "error_codes": 20}

WEAR_HOUR_THRESHOLD = 8000   # hours above which wear factor kicks in
WEAR_SCALE          = 800    # divisor to convert excess hours to points
WEAR_MAX_POINTS     = 10     # cap on wear contribution

# ---------------------------------------------------------------------------
# Recommendation catalogue  (sensor → severity → message)
# ---------------------------------------------------------------------------

RECOMMENDATIONS: dict[str, dict[str, str]] = {
    "temperature": {
        "warning":  "Inspect cooling system and clean heat exchangers; temperature is trending high.",
        "critical": "URGENT: Shut down and inspect for coolant loss or blocked airflow — thermal damage risk.",
    },
    "vibration": {
        "warning":  "Schedule bearing and coupling inspection within the next maintenance window.",
        "critical": "URGENT: Stop equipment immediately — excessive vibration indicates bearing failure or imbalance.",
    },
    "pressure": {
        "warning":  "Check pressure relief valves and inspect for partial blockages in the system.",
        "critical": "URGENT: Over-pressure condition detected — risk of seal failure or rupture. Reduce load and inspect.",
    },
    "voltage": {
        "warning":  "Investigate power supply quality; check for loose connections or upstream regulator drift.",
        "critical": "URGENT: Voltage out of safe operating range — risk of motor/controller damage. Disconnect and inspect.",
    },
    "current": {
        "warning":  "Monitor load carefully; check for increased mechanical resistance or partial winding fault.",
        "critical": "URGENT: Overcurrent detected — possible winding insulation failure or locked rotor. Trip and inspect.",
    },
    "error_codes": {
        "warning":  "Review active fault codes in maintenance log and clear resolved faults.",
        "critical": "URGENT: Multiple concurrent fault codes — system instability. Perform full diagnostic sweep.",
    },
    "wear": {
        "warning":  "Equipment has exceeded recommended service interval (8 000 h). Schedule preventive overhaul.",
    },
}


# ---------------------------------------------------------------------------
# Core analysis function
# ---------------------------------------------------------------------------

def analyze(reading: dict) -> dict:
    """
    Analyse a sensor reading and return a full diagnostic result dict.

    Parameters
    ----------
    reading : dict
        Must contain: temperature, vibration, pressure, voltage, current,
        operating_hours, error_codes (list).

    Returns
    -------
    dict with keys:
        health_score        int  0–100
        failure_probability int  0–100
        classification      str  'Healthy' | 'Warning' | 'Critical'
        sensor_status       dict  sensor → {'value', 'unit', 'level', 'anomaly'}
        anomalies           list of dicts with details on each triggered anomaly
        recommendations     list of str  (prioritised, critical first)
        wear_factor         int  additional failure-probability points from age
        methodology_note    str  disclaimer about the calculation method
    """
    anomalies: list[dict] = []
    sensor_status: dict[str, dict] = {}
    total_penalty = 0.0
    recommendations: list[dict] = []  # {'priority': 0|1, 'text': str}

    # ── Continuous sensors ──────────────────────────────────────────────
    for sensor in ("temperature", "vibration", "pressure", "voltage", "current"):
        value = float(reading.get(sensor, 0))
        cfg   = THRESHOLDS[sensor]
        unit  = cfg["unit"]
        level = _classify_continuous(value, cfg)

        sensor_status[sensor] = {
            "value":   value,
            "unit":    unit,
            "level":   level,
            "anomaly": level != "normal",
        }

        if level == "warning":
            total_penalty += WARNING_PENALTY[sensor]
            anomalies.append({
                "sensor":  sensor,
                "value":   value,
                "unit":    unit,
                "level":   "warning",
                "message": f"{sensor.capitalize()} is elevated at {value} {unit}",
            })
            recommendations.append({
                "priority": 1,
                "text": RECOMMENDATIONS[sensor]["warning"],
            })
        elif level == "critical":
            total_penalty += CRITICAL_PENALTY[sensor]
            anomalies.append({
                "sensor":  sensor,
                "value":   value,
                "unit":    unit,
                "level":   "critical",
                "message": f"{sensor.capitalize()} is critically high at {value} {unit}",
            })
            recommendations.append({
                "priority": 0,
                "text": RECOMMENDATIONS[sensor]["critical"],
            })

    # ── Error codes ──────────────────────────────────────────────────────
    error_codes: list[str] = reading.get("error_codes", [])
    n_errors = len(error_codes)
    if n_errors == 0:
        err_level = "normal"
    elif n_errors <= 2:
        err_level = "warning"
    else:
        err_level = "critical"

    sensor_status["error_codes"] = {
        "value":   n_errors,
        "unit":    "faults",
        "level":   err_level,
        "anomaly": err_level != "normal",
        "codes":   error_codes,
    }

    if err_level == "warning":
        total_penalty += WARNING_PENALTY["error_codes"]
        anomalies.append({
            "sensor":  "error_codes",
            "value":   n_errors,
            "unit":    "faults",
            "level":   "warning",
            "message": f"{n_errors} active fault code(s): {', '.join(error_codes)}",
        })
        recommendations.append({"priority": 1, "text": RECOMMENDATIONS["error_codes"]["warning"]})
    elif err_level == "critical":
        total_penalty += CRITICAL_PENALTY["error_codes"]
        anomalies.append({
            "sensor":  "error_codes",
            "value":   n_errors,
            "unit":    "faults",
            "level":   "critical",
            "message": f"{n_errors} concurrent fault codes: {', '.join(error_codes)}",
        })
        recommendations.append({"priority": 0, "text": RECOMMENDATIONS["error_codes"]["critical"]})

    # ── Health score ──────────────────────────────────────────────────────
    health_score = max(0, min(100, round(100 - total_penalty)))

    # ── Wear factor ───────────────────────────────────────────────────────
    op_hours = int(reading.get("operating_hours", 0))
    wear_factor = 0
    if op_hours >= WEAR_HOUR_THRESHOLD:
        wear_factor = min(WEAR_MAX_POINTS, round(op_hours / WEAR_SCALE))
        recommendations.append({"priority": 1, "text": RECOMMENDATIONS["wear"]["warning"]})

    # ── Failure probability ───────────────────────────────────────────────
    failure_probability = min(100, max(0, (100 - health_score) + wear_factor))

    # ── Classification ────────────────────────────────────────────────────
    if health_score >= 75:
        classification = "Healthy"
    elif health_score >= 45:
        classification = "Warning"
    else:
        classification = "Critical"

    # ── Sort recommendations (critical first, then warning, deduplicated) ─
    seen: set[str] = set()
    sorted_recs: list[str] = []
    for rec in sorted(recommendations, key=lambda r: r["priority"]):
        if rec["text"] not in seen:
            seen.add(rec["text"])
            sorted_recs.append(rec["text"])

    if not sorted_recs:
        sorted_recs = ["No immediate maintenance actions required. Continue routine monitoring."]

    return {
        "health_score":        health_score,
        "failure_probability": failure_probability,
        "classification":      classification,
        "sensor_status":       sensor_status,
        "anomalies":           anomalies,
        "recommendations":     sorted_recs,
        "wear_factor":         wear_factor,
        "operating_hours":     op_hours,
        "methodology_note": (
            "This assessment uses rule-based threshold analysis, NOT a trained ML model. "
            "Health score = 100 minus direct point penalties for each sensor outside its safe range. "
            "Failure probability = inverted health score plus an operating-hours wear factor. "
            "All thresholds and penalty values are documented in engine.py."
        ),
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _classify_continuous(value: float, cfg: dict) -> str:
    """Return 'normal' | 'warning' | 'critical' for a scalar sensor value."""
    # Voltage has both lower and upper bounds
    if "normal_min" in cfg:
        if value < cfg.get("warning_min", cfg["normal_min"]) or \
           value > cfg.get("warning_max", cfg["normal_max"]):
            return "critical"
        if value < cfg["normal_min"] or value > cfg["normal_max"]:
            return "warning"
        return "normal"

    # All other sensors: upper-bound only
    if value > cfg["warning_max"]:
        return "critical"
    if value > cfg["normal_max"]:
        return "warning"
    return "normal"
