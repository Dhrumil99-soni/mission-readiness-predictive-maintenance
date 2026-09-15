#!/usr/bin/env python3
"""
server.py — Lightweight HTTP server for the Predictive Maintenance dashboard.

Uses only Python stdlib (http.server, json, urllib).  No pip installs required.

Endpoints:
  GET  /                         → index.html
  GET  /static/<file>            → static assets (CSS, JS)
  GET  /api/equipment            → list of all equipment IDs + current status
  GET  /api/data?id=<equipment>  → latest sensor reading + analysis
  GET  /api/history?id=<equipment> → last 30 readings (for trend charts)
  POST /api/analyze              → analyse arbitrary sensor JSON body
"""

import json
import pathlib
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# Local modules (same package directory)
import mock_data
import engine

STATIC_DIR = pathlib.Path(__file__).resolve().parent / "static"
PORT = 8080


# ---------------------------------------------------------------------------
# MIME types for static serving
# ---------------------------------------------------------------------------
MIME = {
    ".html": "text/html; charset=utf-8",
    ".css":  "text/css; charset=utf-8",
    ".js":   "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".ico":  "image/x-icon",
}


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Terse logging — suppress default noisy output
        print(f"  {self.command} {self.path} → {args[1] if len(args) > 1 else ''}")

    # ── GET ──────────────────────────────────────────────────────────────
    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/") or "/"
        qs     = parse_qs(parsed.query)

        # Root → index.html
        if path in ("/", "/index.html"):
            self._serve_file(STATIC_DIR / "index.html")
            return

        # Static assets
        if path.startswith("/static/"):
            rel = path[len("/static/"):]
            self._serve_file(STATIC_DIR / rel)
            return

        # API: list all equipment with current status
        if path == "/api/equipment":
            payload = []
            for eid in mock_data.list_equipment():
                reading  = mock_data.get_live_reading(eid)
                analysis = engine.analyze(reading)
                payload.append({
                    "id":                  eid,
                    "label":               reading["label"],
                    "classification":      analysis["classification"],
                    "health_score":        analysis["health_score"],
                    "failure_probability": analysis["failure_probability"],
                    "anomaly_count":       len(analysis["anomalies"]),
                })
            self._json(payload)
            return

        # API: single equipment live data + analysis
        if path == "/api/data":
            eid = qs.get("id", [None])[0]
            if not eid or eid not in mock_data.list_equipment():
                self._error(400, f"Unknown or missing equipment id: {eid!r}")
                return
            reading  = mock_data.get_live_reading(eid)
            analysis = engine.analyze(reading)
            self._json({**reading, **analysis})
            return

        # API: history for trend charts
        if path == "/api/history":
            eid = qs.get("id", [None])[0]
            if not eid or eid not in mock_data.list_equipment():
                self._error(400, f"Unknown or missing equipment id: {eid!r}")
                return
            history = mock_data.get_history(eid)
            # Analyse each historical reading and attach health/failure to it
            result = []
            for r in history:
                a = engine.analyze(r)
                result.append({
                    "timestamp":           r["timestamp"],
                    "temperature":         r["temperature"],
                    "vibration":           r["vibration"],
                    "pressure":            r["pressure"],
                    "voltage":             r["voltage"],
                    "current":             r["current"],
                    "health_score":        a["health_score"],
                    "failure_probability": a["failure_probability"],
                })
            self._json(result)
            return

        self._error(404, f"Not found: {path}")

    # ── POST ─────────────────────────────────────────────────────────────
    def do_POST(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/")

        if path == "/api/analyze":
            length = int(self.headers.get("Content-Length", 0))
            if length == 0:
                self._error(400, "Empty request body")
                return
            try:
                body    = json.loads(self.rfile.read(length))
                result  = engine.analyze(body)
                self._json(result)
            except (json.JSONDecodeError, Exception) as exc:
                self._error(400, str(exc))
            return

        self._error(404, f"Not found: {path}")

    # ── Helpers ───────────────────────────────────────────────────────────
    def _json(self, data):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type",  "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, fpath: pathlib.Path):
        if not fpath.exists() or not fpath.is_file():
            self._error(404, f"File not found: {fpath.name}")
            return
        mime = MIME.get(fpath.suffix, "application/octet-stream")
        body = fpath.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type",   mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, code: int, message: str):
        body = json.dumps({"error": message}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type",  "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"╔══════════════════════════════════════════════════════╗")
    print(f"║  Mission Readiness & Predictive Maintenance           ║")
    print(f"║  Server running at  http://localhost:{PORT}            ║")
    print(f"║  Press Ctrl+C to stop                                 ║")
    print(f"╚══════════════════════════════════════════════════════╝")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[server] Shutting down.")
        server.server_close()
        sys.exit(0)
