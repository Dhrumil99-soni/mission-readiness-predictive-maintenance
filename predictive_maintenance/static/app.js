/**
 * app.js — Mission Readiness & Predictive Maintenance Dashboard
 *
 * Polls the Python server every 5 seconds, renders equipment cards,
 * sensor tiles, anomaly list, recommendations, and Chart.js trend charts.
 * No external JS libraries except Chart.js (loaded via CDN in index.html).
 */

"use strict";

// ── Config ────────────────────────────────────────────────────────────────
const POLL_INTERVAL_MS = 5000;
const BASE_URL = "";          // same origin as the server

// ── State ─────────────────────────────────────────────────────────────────
let selectedEquipId = null;
let pollTimer = null;
let chartInstances = {};      // { chartId: Chart instance }

// ── Utility helpers ───────────────────────────────────────────────────────

function classLabel(c) {
  return c ? c.toLowerCase() : "healthy";
}

function statusIcon(c) {
  if (c === "Critical") return "🔴";
  if (c === "Warning")  return "⚠️";
  return "✅";
}

function healthColor(score) {
  if (score >= 75) return "var(--healthy)";
  if (score >= 45) return "var(--warning)";
  return "var(--critical)";
}

function formatTs(ts) {
  return new Date(ts * 1000).toLocaleTimeString();
}

function el(id) { return document.getElementById(id); }

function clearCharts() {
  Object.values(chartInstances).forEach(c => c.destroy());
  chartInstances = {};
}

// ── Fetch helpers ─────────────────────────────────────────────────────────

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status} — ${url}`);
  return res.json();
}

// ── Equipment overview (sidebar) ──────────────────────────────────────────

async function refreshSidebar() {
  try {
    const equipment = await fetchJSON(`${BASE_URL}/api/equipment`);
    renderSidebar(equipment);
    el("last-updated").textContent = "Updated " + new Date().toLocaleTimeString();
  } catch (err) {
    console.error("Sidebar refresh failed:", err);
  }
}

function renderSidebar(equipment) {
  const container = el("equip-list");
  container.innerHTML = "";

  equipment.forEach(eq => {
    const cls = classLabel(eq.classification);
    const card = document.createElement("div");
    card.className = "equip-card" + (eq.id === selectedEquipId ? " selected" : "");
    card.dataset.id = eq.id;

    card.innerHTML = `
      <div class="eq-header">
        <span class="eq-id">${eq.id}</span>
        <span class="status-badge ${cls}">
          <span class="dot ${cls}"></span>${eq.classification}
        </span>
      </div>
      <div class="eq-label">${eq.label}</div>
      <div class="eq-score-row">
        <div class="health-bar-wrap">
          <div class="health-bar"
               style="width:${eq.health_score}%;background:${healthColor(eq.health_score)}">
          </div>
        </div>
        <span class="eq-score-num" style="color:${healthColor(eq.health_score)}">
          ${eq.health_score}
        </span>
      </div>
    `;

    card.addEventListener("click", () => selectEquipment(eq.id));
    container.appendChild(card);
  });
}

// ── Equipment detail panel ────────────────────────────────────────────────

async function selectEquipment(id) {
  selectedEquipId = id;
  // Highlight selected card immediately
  document.querySelectorAll(".equip-card").forEach(c => {
    c.classList.toggle("selected", c.dataset.id === id);
  });
  await refreshDetail();
}

async function refreshDetail() {
  if (!selectedEquipId) return;
  try {
    const [data, history] = await Promise.all([
      fetchJSON(`${BASE_URL}/api/data?id=${selectedEquipId}`),
      fetchJSON(`${BASE_URL}/api/history?id=${selectedEquipId}`),
    ]);
    renderDetail(data, history);
  } catch (err) {
    console.error("Detail refresh failed:", err);
  }
}

function renderDetail(data, history) {
  const panel = el("detail");
  panel.innerHTML = "";  // clear

  const cls = classLabel(data.classification);
  const scoreColor = healthColor(data.health_score);

  // ── Header ──────────────────────────────────────────────────────────
  const header = document.createElement("div");
  header.className = "detail-header";
  header.innerHTML = `
    <div>
      <h1>${statusIcon(data.classification)} ${data.label}</h1>
      <div class="desc">${data.equipment_id} &nbsp;·&nbsp; ${
        data.description || "Industrial equipment"
      }</div>
    </div>
    <div class="detail-kpis">
      <div class="kpi-card">
        <div class="kpi-label">Health Score</div>
        <div class="kpi-value" style="color:${scoreColor}">${data.health_score}</div>
        <div class="kpi-sub">out of 100</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Failure Risk</div>
        <div class="kpi-value" style="color:${scoreColor}">${data.failure_probability}%</div>
        <div class="kpi-sub">probability estimate</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Status</div>
        <div class="kpi-value" style="font-size:18px; padding-top:4px">
          <span class="status-badge ${cls}">
            <span class="dot ${cls}"></span>${data.classification}
          </span>
        </div>
        <div class="kpi-sub">${data.operating_hours.toLocaleString()} hrs total</div>
      </div>
    </div>
  `;
  panel.appendChild(header);

  // ── Methodology note ────────────────────────────────────────────────
  const note = document.createElement("div");
  note.className = "methodology";
  note.textContent = data.methodology_note;
  panel.appendChild(note);

  // ── Sensor tiles ────────────────────────────────────────────────────
  panel.appendChild(sectionTitle("Live Sensor Readings"));
  panel.appendChild(renderSensorGrid(data));

  // ── Anomalies ────────────────────────────────────────────────────────
  if (data.anomalies && data.anomalies.length > 0) {
    panel.appendChild(sectionTitle("Detected Anomalies"));
    panel.appendChild(renderAnomalies(data.anomalies));
  }

  // ── Recommendations ──────────────────────────────────────────────────
  panel.appendChild(sectionTitle("Recommended Maintenance Actions"));
  panel.appendChild(renderRecommendations(data.recommendations));

  // ── Charts ───────────────────────────────────────────────────────────
  panel.appendChild(sectionTitle("Sensor Trends (last 30 readings)"));
  clearCharts();
  panel.appendChild(renderCharts(history));

  // ── Custom input ─────────────────────────────────────────────────────
  panel.appendChild(renderCustomForm(data));
}

// ── Sensor grid ───────────────────────────────────────────────────────────

const SENSOR_META = {
  temperature: { label: "Temperature", unit: "°C",    range: "Normal ≤ 80 | Warn ≤ 95 | Crit > 95" },
  vibration:   { label: "Vibration",   unit: "mm/s",  range: "Normal ≤ 2.5 | Warn ≤ 4 | Crit > 4" },
  pressure:    { label: "Pressure",    unit: "bar",   range: "Normal ≤ 8 | Warn ≤ 10 | Crit > 10" },
  voltage:     { label: "Voltage",     unit: "V",     range: "Normal 210–250 | Warn 200–260 | Crit outside" },
  current:     { label: "Current",     unit: "A",     range: "Normal ≤ 15 | Warn ≤ 20 | Crit > 20" },
  error_codes: { label: "Fault Codes", unit: "faults",range: "Normal 0 | Warn 1–2 | Crit ≥ 3" },
};

function renderSensorGrid(data) {
  const grid = document.createElement("div");
  grid.className = "sensor-grid";

  const ss = data.sensor_status || {};

  Object.entries(SENSOR_META).forEach(([key, meta]) => {
    const s = ss[key] || {};
    const level = s.level || "normal";
    const tile = document.createElement("div");
    tile.className = `sensor-tile ${level}`;

    let valueStr, statusLabel, statusColor;
    if (key === "error_codes") {
      const codes = s.codes || data.error_codes || [];
      valueStr   = codes.length === 0 ? "None" : codes.join(", ");
      statusLabel = level === "normal" ? "No faults" :
                    level === "warning" ? `${codes.length} fault(s)` :
                    `${codes.length} faults — CRITICAL`;
      statusColor = level === "normal" ? "var(--healthy)" :
                    level === "warning" ? "var(--warning)" : "var(--critical)";
    } else {
      valueStr    = typeof s.value === "number" ? s.value.toFixed(
        key === "vibration" ? 2 : key === "pressure" ? 2 : 1
      ) : "—";
      statusLabel = level === "normal" ? "Normal"  :
                    level === "warning"? "Warning" : "Critical";
      statusColor = level === "normal" ? "var(--healthy)" :
                    level === "warning"? "var(--warning)" : "var(--critical)";
    }

    tile.innerHTML = `
      <div class="s-name">${meta.label}</div>
      <div class="s-value">${valueStr}</div>
      <div class="s-unit">${key !== "error_codes" ? meta.unit : ""}</div>
      <div class="s-status" style="color:${statusColor}">${statusLabel}</div>
      <div class="s-range">${meta.range}</div>
    `;
    grid.appendChild(tile);
  });

  return grid;
}

// ── Anomaly list ──────────────────────────────────────────────────────────

function renderAnomalies(anomalies) {
  const list = document.createElement("div");
  list.className = "anomaly-list";

  anomalies.forEach(a => {
    const item = document.createElement("div");
    item.className = `anomaly-item ${a.level}`;
    item.innerHTML = `
      <span class="anom-icon">${a.level === "critical" ? "🔴" : "⚠️"}</span>
      <span class="anom-msg">${a.message}</span>
      <span class="anom-badge">
        <span class="status-badge ${a.level}">${a.level.toUpperCase()}</span>
      </span>
    `;
    list.appendChild(item);
  });

  return list;
}

// ── Recommendations ───────────────────────────────────────────────────────

function renderRecommendations(recs) {
  const list = document.createElement("ol");
  list.className = "rec-list";
  recs.forEach(r => {
    const item = document.createElement("li");
    item.className = "rec-item";
    item.textContent = r;
    list.appendChild(item);
  });
  return list;
}

// ── Trend charts ──────────────────────────────────────────────────────────

function renderCharts(history) {
  const grid = document.createElement("div");
  grid.className = "charts-grid";

  const labels = history.map((_, i) => i + 1);

  const chartDefs = [
    { key: "health_score",        label: "Health Score",          color: "#38bdf8", yMin: 0,  yMax: 100 },
    { key: "failure_probability", label: "Failure Probability %",  color: "#f87171", yMin: 0,  yMax: 100 },
    { key: "temperature",         label: "Temperature (°C)",       color: "#fb923c", yMin: null, yMax: null },
    { key: "vibration",           label: "Vibration (mm/s)",       color: "#a78bfa", yMin: 0,  yMax: null },
    { key: "pressure",            label: "Pressure (bar)",         color: "#34d399", yMin: 0,  yMax: null },
    { key: "voltage",             label: "Voltage (V)",            color: "#fbbf24", yMin: null, yMax: null },
  ];

  chartDefs.forEach(def => {
    const card  = document.createElement("div");
    card.className = "chart-card";

    const title = document.createElement("div");
    title.className = "chart-title";
    title.textContent = def.label;

    const canvas = document.createElement("canvas");
    canvas.id     = `chart-${def.key}`;
    canvas.height = 120;

    card.appendChild(title);
    card.appendChild(canvas);
    grid.appendChild(card);

    const values = history.map(h => h[def.key] ?? null);

    const chart = new Chart(canvas, {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: def.label,
          data: values,
          borderColor: def.color,
          backgroundColor: def.color + "22",
          borderWidth: 2,
          pointRadius: 2,
          fill: true,
          tension: 0.3,
        }],
      },
      options: {
        responsive: true,
        animation: false,
        plugins: {
          legend: { display: false },
          tooltip: { mode: "index", intersect: false },
        },
        scales: {
          x: {
            display: true,
            title: { display: true, text: "Reading #", color: "#64748b", font: { size: 10 } },
            ticks: { color: "#64748b", maxTicksLimit: 8 },
            grid:  { color: "#1e293b" },
          },
          y: {
            display: true,
            min: def.yMin !== null ? def.yMin : undefined,
            max: def.yMax !== null ? def.yMax : undefined,
            ticks: { color: "#64748b" },
            grid:  { color: "#334155" },
          },
        },
      },
    });

    chartInstances[def.key] = chart;
  });

  return grid;
}

// ── Custom sensor input form ──────────────────────────────────────────────

function renderCustomForm(prefill) {
  const section = document.createElement("div");
  section.id = "custom-form-section";

  const fields = [
    { id: "c-temperature", label: "Temperature (°C)",    value: prefill.temperature, step: "0.1" },
    { id: "c-vibration",   label: "Vibration (mm/s)",    value: prefill.vibration,   step: "0.01" },
    { id: "c-pressure",    label: "Pressure (bar)",      value: prefill.pressure,    step: "0.1" },
    { id: "c-voltage",     label: "Voltage (V)",         value: prefill.voltage,     step: "0.1" },
    { id: "c-current",     label: "Current (A)",         value: prefill.current,     step: "0.01" },
    { id: "c-ophours",     label: "Operating Hours",     value: prefill.operating_hours, step: "1" },
    { id: "c-errcodes",    label: "Error Codes (comma-separated)", value: (prefill.error_codes||[]).join(", "), step: null },
  ];

  const formGridHtml = fields.map(f => `
    <div class="form-group">
      <label for="${f.id}">${f.label}</label>
      ${f.step
        ? `<input type="number" id="${f.id}" value="${f.value}" step="${f.step}" min="0">`
        : `<input type="text"   id="${f.id}" value="${f.value}" placeholder="e.g. E001, E012">`
      }
    </div>
  `).join("");

  section.innerHTML = `
    <details>
      <summary>Analyse Custom Sensor Values</summary>
      <p style="margin-top:10px; color:var(--muted); font-size:12px;">
        Enter custom sensor readings to see how the analysis engine evaluates them.
        Fields are pre-filled from the current equipment reading.
      </p>
      <div class="form-grid">${formGridHtml}</div>
      <button id="custom-submit">Run Analysis</button>
      <div id="custom-result"></div>
    </details>
  `;

  // Wire up submit after the element is inserted
  setTimeout(() => {
    const btn = el("custom-submit");
    if (btn) btn.addEventListener("click", runCustomAnalysis);
  }, 0);

  return section;
}

async function runCustomAnalysis() {
  const codesRaw = (el("c-errcodes").value || "").trim();
  const codes    = codesRaw ? codesRaw.split(/[\s,]+/).filter(Boolean) : [];

  const payload = {
    temperature:     parseFloat(el("c-temperature").value) || 0,
    vibration:       parseFloat(el("c-vibration").value)   || 0,
    pressure:        parseFloat(el("c-pressure").value)    || 0,
    voltage:         parseFloat(el("c-voltage").value)     || 0,
    current:         parseFloat(el("c-current").value)     || 0,
    operating_hours: parseInt(el("c-ophours").value,10)    || 0,
    error_codes:     codes,
  };

  try {
    const result = await fetch(`${BASE_URL}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(r => r.json());

    const cls = classLabel(result.classification);
    const scoreColor = healthColor(result.health_score);
    const recsHtml = result.recommendations.map((r, i) =>
      `<li class="rec-item">${r}</li>`
    ).join("");

    const resultDiv = el("custom-result");
    resultDiv.style.display = "block";
    resultDiv.innerHTML = `
      <div style="display:flex; gap:12px; flex-wrap:wrap; margin-bottom:14px;">
        <div class="kpi-card">
          <div class="kpi-label">Health Score</div>
          <div class="kpi-value" style="color:${scoreColor}">${result.health_score}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Failure Risk</div>
          <div class="kpi-value" style="color:${scoreColor}">${result.failure_probability}%</div>
        </div>
        <div class="kpi-card" style="display:flex;align-items:center;justify-content:center;">
          <span class="status-badge ${cls}">
            <span class="dot ${cls}"></span>${result.classification}
          </span>
        </div>
      </div>
      ${result.anomalies.length > 0 ? `
        <div class="section-title">Anomalies Detected</div>
        ${result.anomalies.map(a => `
          <div class="anomaly-item ${a.level}" style="margin-bottom:6px">
            <span class="anom-icon">${a.level === "critical" ? "🔴" : "⚠️"}</span>
            <span class="anom-msg">${a.message}</span>
          </div>
        `).join("")}
      ` : `<p style="color:var(--healthy); font-size:13px; margin-bottom:10px;">✅ No anomalies detected.</p>`}
      <div class="section-title" style="margin-top:12px">Recommendations</div>
      <ol class="rec-list">${recsHtml}</ol>
      <div class="methodology" style="margin-top:12px">${result.methodology_note}</div>
    `;
  } catch (err) {
    el("custom-result").style.display = "block";
    el("custom-result").innerHTML = `<p style="color:var(--critical)">Analysis failed: ${err.message}</p>`;
  }
}

// ── Section title helper ──────────────────────────────────────────────────

function sectionTitle(text) {
  const d = document.createElement("div");
  d.className = "section-title";
  d.textContent = text;
  return d;
}

// ── Polling loop ──────────────────────────────────────────────────────────

function startPolling() {
  stopPolling();
  pollTimer = setInterval(async () => {
    await refreshSidebar();
    if (selectedEquipId) await refreshDetail();
  }, POLL_INTERVAL_MS);
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}

// ── Bootstrap ─────────────────────────────────────────────────────────────

async function init() {
  el("refresh-btn").addEventListener("click", async () => {
    await refreshSidebar();
    if (selectedEquipId) await refreshDetail();
  });

  await refreshSidebar();

  // Auto-select first equipment unit
  const first = document.querySelector(".equip-card");
  if (first) await selectEquipment(first.dataset.id);

  startPolling();
}

document.addEventListener("DOMContentLoaded", init);
