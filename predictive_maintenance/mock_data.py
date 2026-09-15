"""
mock_data.py — Realistic sensor data for four equipment units.

Each unit has a distinct operating profile so the dashboard always shows
a spread of health states (Healthy, Warning, Critical).  Small random
noise is added on every call to simulate a live sensor stream, but the
base values keep each unit in its intended risk band.
"""

import random
import math
import time

# ---------------------------------------------------------------------------
# Base sensor profiles for each equipment unit
# ---------------------------------------------------------------------------
# Keys must match the sensor names used in engine.py
#
# Profile fields:
#   temperature     °C
#   vibration       mm/s (RMS)
#   pressure        bar
#   voltage         V
#   current         A
#   operating_hours total cumulative hours
#   error_codes     list of active fault codes (empty = no faults)

BASE_PROFILES = {
    "PUMP-01": {
        "label": "Centrifugal Pump 01",
        "description": "Primary coolant circulation pump — well-maintained, nominal operation.",
        "temperature": 52.0,
        "vibration": 1.2,
        "pressure": 4.5,
        "voltage": 232.0,
        "current": 8.5,
        "operating_hours": 2100,
        "error_codes": [],
        # noise scale per sensor
        "_noise": {"temperature": 1.5, "vibration": 0.15, "pressure": 0.3,
                   "voltage": 2.0, "current": 0.5, "operating_hours": 0},
    },
    "MOTOR-02": {
        "label": "Drive Motor 02",
        "description": "Conveyor belt drive motor — elevated temperature trend, bearing wear suspected.",
        "temperature": 84.0,
        "vibration": 2.8,
        "pressure": 6.2,
        "voltage": 228.0,
        "current": 14.0,
        "operating_hours": 6800,
        "error_codes": ["E012"],
        "_noise": {"temperature": 2.0, "vibration": 0.25, "pressure": 0.4,
                   "voltage": 3.0, "current": 0.8, "operating_hours": 0},
    },
    "COMPRESSOR-03": {
        "label": "Air Compressor 03",
        "description": "High-pressure air compressor — high vibration and thermal overload warnings.",
        "temperature": 93.0,
        "vibration": 4.6,
        "pressure": 9.1,
        "voltage": 241.0,
        "current": 19.5,
        "operating_hours": 9500,
        "error_codes": ["E005", "E019", "E031"],
        "_noise": {"temperature": 2.5, "vibration": 0.35, "pressure": 0.5,
                   "voltage": 2.5, "current": 1.0, "operating_hours": 0},
    },
    "GENERATOR-04": {
        "label": "Standby Generator 04",
        "description": "Backup diesel generator — slightly elevated voltage; otherwise healthy.",
        "temperature": 67.0,
        "vibration": 1.9,
        "pressure": 5.8,
        "voltage": 253.0,
        "current": 11.0,
        "operating_hours": 4300,
        "error_codes": ["E002"],
        "_noise": {"temperature": 1.8, "vibration": 0.20, "pressure": 0.35,
                   "voltage": 3.5, "current": 0.6, "operating_hours": 0},
    },
}

# In-memory history store: {equipment_id: [reading, ...]}  (capped at 30)
_history: dict[str, list[dict]] = {eid: [] for eid in BASE_PROFILES}


def _jitter(value: float, scale: float) -> float:
    """Add Gaussian noise to a sensor value; clamp to >= 0."""
    return max(0.0, value + random.gauss(0, scale))


def get_live_reading(equipment_id: str) -> dict:
    """
    Return a fresh sensor reading for *equipment_id* with realistic noise.
    The reading is also appended to the in-memory history (max 30 entries).
    """
    if equipment_id not in BASE_PROFILES:
        raise ValueError(f"Unknown equipment id: {equipment_id!r}")

    profile = BASE_PROFILES[equipment_id]
    noise = profile["_noise"]

    reading = {
        "equipment_id": equipment_id,
        "label": profile["label"],
        "timestamp": time.time(),
        "temperature": round(_jitter(profile["temperature"], noise["temperature"]), 1),
        "vibration":   round(_jitter(profile["vibration"],   noise["vibration"]),   2),
        "pressure":    round(_jitter(profile["pressure"],    noise["pressure"]),    2),
        "voltage":     round(_jitter(profile["voltage"],     noise["voltage"]),     1),
        "current":     round(_jitter(profile["current"],     noise["current"]),     2),
        "operating_hours": profile["operating_hours"],
        "error_codes": list(profile["error_codes"]),
    }

    history = _history[equipment_id]
    history.append(reading)
    if len(history) > 30:
        history.pop(0)

    return reading


def get_history(equipment_id: str) -> list[dict]:
    """Return (up to) the last 30 readings for *equipment_id*."""
    if equipment_id not in BASE_PROFILES:
        raise ValueError(f"Unknown equipment id: {equipment_id!r}")

    # Seed the history on first request so charts have data immediately.
    if len(_history[equipment_id]) < 5:
        for _ in range(20):
            get_live_reading(equipment_id)

    return list(_history[equipment_id])


def list_equipment() -> list[str]:
    """Return all known equipment IDs."""
    return list(BASE_PROFILES.keys())
