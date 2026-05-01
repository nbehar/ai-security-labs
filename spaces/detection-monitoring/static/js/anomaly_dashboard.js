/**
 * anomaly_dashboard.js — D2 Anomaly Detection tab.
 *
 * Security: All data from the API that is interpolated into HTML is either
 * numeric (safe) or passed through escapeHtml(). API result fields are
 * pre-assigned to local variables before interpolation per platform convention.
 */
import { fetchJSON, escapeHtml } from './core.js';

const METRICS = [
  { key: 'response_length', label: 'Response Length', unit: 'tokens', defaultHigh: 468, defaultLow: null },
  { key: 'refusal_rate',    label: 'Refusal Rate',    unit: '',        defaultHigh: null, defaultLow: 0.04 },
  { key: 'query_rate',      label: 'Query Rate',      unit: 'req/min', defaultHigh: 27,   defaultLow: null },
  { key: 'confidence',      label: 'Confidence',      unit: '',        defaultHigh: null, defaultLow: 0.61 },
];

let _windows = null;
let _baseline = null;

export async function renderAnomalyTab(container) {
  _windows = null;
  _baseline = null;

  container.innerHTML = `
    <div class="info-card" style="margin-bottom:var(--space-4)">
      <strong>D2: Anomaly Detection</strong> — 24 hours of NexaCore Finance Chatbot telemetry.
      Four metrics are tracked per hour. Configure alert thresholds —
      catch all 3 attack windows with as few false alarms as possible.
      <br><br>
      <strong>Scoring:</strong> (attacks detected ÷ 3) × 100 − (false alarms × 10). Max 100 pts.
    </div>
    <div id="d2-charts"></div>
    <div id="d2-thresholds-section"></div>
    <div style="margin-top:var(--space-4);text-align:center">
      <button id="d2-evaluate-btn" class="btn-primary" disabled>Evaluate Thresholds</button>
    </div>
    <div id="d2-results"></div>
  `;

  try {
    const data = await fetchJSON('/api/anomaly/data');
    _windows = data.windows;
    _baseline = data.baseline;
  } catch {
    container.innerHTML += '<p style="color:var(--color-danger-light)">Failed to load anomaly data.</p>';
    return;
  }

  buildCharts();
  buildThresholds();

  const evalBtn = document.getElementById('d2-evaluate-btn');
  evalBtn.disabled = false;
  evalBtn.addEventListener('click', runEvaluate);
}

// ─── Charts ──────────────────────────────────────────────────────────────────

function buildCharts() {
  const el = document.getElementById('d2-charts');
  if (!el) return;
  el.innerHTML = `<div class="d2-charts-grid">${METRICS.map(buildSparkCard).join('')}</div>`;
}

function buildSparkCard(metric) {
  const values = _windows.map(w => w[metric.key]);
  const minV = Math.min(...values);
  const maxV = Math.max(...values);
  const range = maxV - minV || 1;
  const b = _baseline[metric.key];

  const W = 240, H = 70, PAD = 4;
  const xStep = (W - PAD * 2) / (values.length - 1);

  const bandTop = H - PAD - ((b.mean + b.std - minV) / range) * (H - PAD * 2);
  const bandH   = Math.max(1, ((b.std * 2) / range) * (H - PAD * 2));
  const pts = values.map((v, i) => {
    const x = PAD + i * xStep;
    const y = H - PAD - ((v - minV) / range) * (H - PAD * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  const baseY = H - PAD - ((b.mean - minV) / range) * (H - PAD * 2);

  const dots = values.map((v, i) => {
    const x = (PAD + i * xStep).toFixed(1);
    const y = (H - PAD - ((v - minV) / range) * (H - PAD * 2)).toFixed(1);
    const outlier = Math.abs(v - b.mean) > 2 * b.std;
    const r = outlier ? 3 : 1.5;
    const fill = outlier ? 'var(--color-danger-light)' : 'var(--color-accent-aisl-highlight)';
    return `<circle cx="${x}" cy="${y}" r="${r}" fill="${fill}" />`;
  }).join('');

  const meanLabel = `${b.mean}${metric.unit ? ' ' + metric.unit : ''}`;
  const stdLabel  = String(b.std);

  const chartTitleId = `chart-title-${metric.key}`;
  return `
    <div class="d2-chart-card">
      <div class="d2-chart-card__title">${escapeHtml(metric.label)}</div>
      <div class="d2-chart-card__subtitle">Baseline: ${escapeHtml(meanLabel)} ±${escapeHtml(stdLabel)}</div>
      <svg class="d2-sparkline" viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="${chartTitleId}">
        <title id="${chartTitleId}">${escapeHtml(metric.label)} metric over time</title>
        <rect x="${PAD}" y="${bandTop.toFixed(1)}" width="${W - PAD * 2}" height="${bandH.toFixed(1)}"
              fill="rgba(100,100,120,0.15)" />
        <line x1="${PAD}" y1="${baseY.toFixed(1)}" x2="${W - PAD}" y2="${baseY.toFixed(1)}"
              stroke="rgba(100,100,140,0.4)" stroke-width="1" stroke-dasharray="3,2" />
        <polyline points="${pts}" fill="none"
                  stroke="var(--color-accent-aisl-highlight)" stroke-width="1.5"
                  stroke-linejoin="round" stroke-linecap="round" />
        ${dots}
      </svg>
      <div style="font-size:10px;color:var(--color-text-muted);font-family:var(--font-mono);margin-top:2px">
        min:${minV} · max:${maxV}
      </div>
    </div>
  `;
}

// ─── Thresholds ───────────────────────────────────────────────────────────────

function buildThresholds() {
  const el = document.getElementById('d2-thresholds-section');
  if (!el) return;
  el.innerHTML = `
    <div class="d2-thresholds">
      <div class="d2-thresholds__title">Configure Alert Thresholds</div>
      <div class="d2-threshold-grid">
        ${METRICS.map(buildThreshRow).join('')}
      </div>
    </div>
  `;
}

function buildThreshRow(m) {
  const hId = `thresh-${m.key}-high`;
  const lId = `thresh-${m.key}-low`;
  const hv  = m.defaultHigh !== null ? String(m.defaultHigh) : '';
  const lv  = m.defaultLow  !== null ? String(m.defaultLow)  : '';
  return `
    <div class="d2-threshold-row">
      <div class="d2-threshold-row__label">${escapeHtml(m.key)}</div>
      <div class="d2-threshold-inputs">
        <div class="d2-threshold-field">
          <label for="${hId}">Alert if HIGH &gt;</label>
          <input type="number" id="${hId}" step="any" value="${hv}" placeholder="—" />
        </div>
        <div class="d2-threshold-field">
          <label for="${lId}">Alert if LOW &lt;</label>
          <input type="number" id="${lId}" step="any" value="${lv}" placeholder="—" />
        </div>
      </div>
    </div>
  `;
}

// ─── Evaluate ────────────────────────────────────────────────────────────────

async function runEvaluate() {
  const thresholds = {};
  for (const m of METRICS) {
    const hRaw = document.getElementById(`thresh-${m.key}-high`)?.value.trim() || '';
    const lRaw = document.getElementById(`thresh-${m.key}-low`)?.value.trim()  || '';
    const high = hRaw !== '' ? parseFloat(hRaw) : null;
    const low  = lRaw !== '' ? parseFloat(lRaw) : null;
    if (high !== null || low !== null) {
      thresholds[m.key] = {};
      if (high !== null) thresholds[m.key].high = high;
      if (low  !== null) thresholds[m.key].low  = low;
    }
  }

  try {
    const raw = await fetchJSON('/api/anomaly/evaluate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ thresholds, session_id: getSessionId() }),
    });
    showResults(raw);
    submitToLeaderboard(raw.score);
  } catch (err) {
    console.error('Evaluate error', err);
  }
}

function showResults(raw) {
  const el = document.getElementById('d2-results');
  if (!el) return;

  const score     = Number(raw.score);
  const tp        = Number(raw.tp);
  const fp        = Number(raw.fp);
  const fpPenalty = fp * 10;

  const scoreColor = score >= 80 ? 'var(--color-success-light)' :
                     score >= 40 ? 'var(--color-warning-light)' : 'var(--color-danger-light)';
  const fpColor    = fp > 0 ? 'var(--color-danger-light)' : 'var(--color-success-light)';

  const timelineHtml = raw.windows.map(w => {
    const v = w.verdict.toLowerCase();
    const cls = `d2-window-block--${v}`;
    const hourLabel = String(w.hour).padStart(2, '0');
    const labelText = w.attack_id ? escapeHtml(w.attack_id) : hourLabel;
    const tipText   = escapeHtml(`Hour ${w.hour}: ${w.verdict}${w.why ? ' — ' + w.why : ''}`);
    return `<div class="d2-window-block ${cls}" title="${tipText}">${labelText}</div>`;
  }).join('');

  const missedKeys = Object.keys(raw.missed_why || {});
  const missedHtml = missedKeys.map(wid => {
    const whyText = escapeHtml(raw.missed_why[wid]);
    return `<div class="why-card why-card--incorrect" style="margin-top:var(--space-2)">
      <strong>Missed ${escapeHtml(wid)}:</strong> ${whyText}
    </div>`;
  }).join('');

  el.innerHTML = `
    <div class="d2-score-card">
      <div>
        <div class="d2-score-card__score" style="color:${scoreColor}">${score}</div>
        <div class="d2-score-card__label">D2 Score</div>
      </div>
      <div>
        <div class="d2-score-card__score">${tp} / 3</div>
        <div class="d2-score-card__label">Attacks Detected</div>
      </div>
      <div>
        <div class="d2-score-card__score" style="color:${fpColor}">${fp}</div>
        <div class="d2-score-card__label">False Alarms (−${fpPenalty} pts)</div>
      </div>
    </div>
    <div style="margin-top:var(--space-4)">
      <div style="font-size:var(--text-sm);font-weight:var(--font-semibold);margin-bottom:var(--space-2)">
        24-Hour Timeline — TP=green · FP=red · FN=amber · TN=gray
      </div>
      <div class="d2-timeline">${timelineHtml}</div>
    </div>
    ${missedHtml ? `<div style="margin-top:var(--space-3)">${missedHtml}</div>` : ''}
  `;
}

async function submitToLeaderboard(d2Score) {
  try {
    await fetchJSON('/api/score', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ session_id: getSessionId(), d1_score: 0, d2_score: Number(d2Score), d3_score: 0 }),
    });
  } catch {}
}

function getSessionId() {
  let sid = sessionStorage.getItem('d6-session');
  if (!sid) { sid = crypto.randomUUID(); sessionStorage.setItem('d6-session', sid); }
  return sid;
}
