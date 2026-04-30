/**
 * output_sanitizer.js — D3 Output Sanitization tab.
 *
 * Security note: all API string values are passed through escapeHtml() before
 * rendering. HTML fragments are built in named functions and assigned to
 * innerHTML only after escaping is complete. This matches the platform pattern
 * used in blue-team/static/js/app.js.
 */
import { fetchJSON, escapeHtml } from './core.js';

const DEFAULT_RULES = 'BLOCK \\b\\d{3}-\\d{2}-\\d{4}\\b\nBLOCK (?i)password\\s*[=:]\\s*\\S+';

let _outputs = null;

export async function renderOutputSanitizerTab(container) {
  _outputs = null;

  container.innerHTML = `
    <div class="info-card" style="margin-bottom:var(--space-4)">
      <strong>D3: Output Sanitization</strong> — Write <code>BLOCK regex</code> rules to catch dangerous model outputs.
      Same DSL as Blue Team WAF. Score = F1 × 100.
    </div>
    <div class="d3-layout">
      <div class="d3-rule-editor">
        <div class="d3-rule-editor__title">Rule Editor</div>
        <div style="font-size:var(--text-xs);color:var(--color-text-muted);margin-bottom:var(--space-3)">
          One rule per line: <code>BLOCK regex</code> or <code>ALLOW regex</code>
        </div>
        <textarea id="d3-rules" spellcheck="false"></textarea>
        <div style="margin-top:var(--space-3)">
          <button id="d3-test-btn" class="btn-primary">Test Rules</button>
        </div>
        <div id="d3-error" style="color:var(--color-danger-light);font-size:var(--text-xs);margin-top:var(--space-2)"></div>
        <div id="d3-score-area"></div>
      </div>
      <div class="d3-results-panel" id="d3-output-list">
        <div style="color:var(--color-text-muted);font-size:var(--text-sm);padding:var(--space-4)">
          Loading outputs…
        </div>
      </div>
    </div>
  `;

  const rulesTA = document.getElementById('d3-rules');
  if (rulesTA) rulesTA.value = DEFAULT_RULES;

  try {
    const data = await fetchJSON('/api/outputs');
    _outputs = data.outputs;
  } catch {
    document.getElementById('d3-output-list').innerHTML =
      '<p style="color:var(--color-danger-light)">Failed to load outputs.</p>';
    return;
  }

  populateOutputList(_outputs);
  document.getElementById('d3-test-btn').addEventListener('click', runRules);
}

function populateOutputList(outputs) {
  const el = document.getElementById('d3-output-list');
  if (!el) return;
  el.innerHTML = buildInitialCards(outputs);
}

function buildInitialCards(outputs) {
  let html = '';
  for (const o of outputs) {
    const id   = escapeHtml(o.id);
    const sys  = escapeHtml(o.system);
    const text = escapeHtml(o.text);
    html += `<div class="d3-output-card" id="out-${id}">
      <div class="d3-output-card__header">
        <span class="d3-output-card__id">${id}</span>
        <span style="font-size:var(--text-xs);color:var(--color-text-secondary)">${sys}</span>
      </div>
      <div class="d3-output-card__text">${text}</div>
    </div>`;
  }
  return html;
}

async function runRules() {
  const rules = document.getElementById('d3-rules')?.value || '';
  const errEl = document.getElementById('d3-error');
  if (errEl) errEl.textContent = '';

  try {
    const raw = await fetchJSON('/api/outputs/evaluate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ rules, session_id: getSessionId() }),
    });
    populateScoreBanner(raw);
    populateResultCards(raw.outputs);
    submitToLeaderboard(raw.score);
  } catch (err) {
    if (errEl) errEl.textContent = String(err.message || 'Evaluation failed');
  }
}

function populateScoreBanner(raw) {
  const el = document.getElementById('d3-score-area');
  if (!el) return;

  const score   = Number(raw.score);
  const f1pct   = (Number(raw.f1) * 100).toFixed(1);
  const prec    = (Number(raw.precision) * 100).toFixed(1);
  const rec     = (Number(raw.recall) * 100).toFixed(1);
  const tp      = Number(raw.tp);
  const fp      = Number(raw.fp);
  const fn      = Number(raw.fn);
  const beat    = Boolean(raw.beat_baseline);
  const blPct   = (Number(raw.baseline_f1) * 100).toFixed(1);

  const beatHtml = beat
    ? '<span class="d3-beat-baseline">&#10003; Beat the baseline!</span>'
    : `<span style="font-size:var(--text-xs);color:var(--color-text-muted)">Baseline F1: ${blPct}%</span>`;

  el.innerHTML = buildScoreBannerHtml(score, f1pct, prec, rec, tp, fp, fn, beatHtml);
}

function buildScoreBannerHtml(score, f1pct, prec, rec, tp, fp, fn, beatHtml) {
  return `<div class="d3-score-banner" style="margin-top:var(--space-4)">
    <div>
      <div class="d3-score-banner__score">${score}</div>
      <div style="font-size:var(--text-xs);color:var(--color-text-muted)">Score (F1×100)</div>
    </div>
    <div>
      <div style="font-size:var(--text-lg);font-weight:var(--font-bold);font-family:var(--font-mono)">${f1pct}%</div>
      <div style="font-size:var(--text-xs);color:var(--color-text-muted)">F1</div>
    </div>
    <div style="font-size:var(--text-xs);color:var(--color-text-secondary)">
      Prec ${prec}% · Rec ${rec}%<br>TP:${tp} FP:${fp} FN:${fn}
    </div>
    ${beatHtml}
  </div>`;
}

function populateResultCards(outputs) {
  const listEl = document.getElementById('d3-output-list');
  if (!listEl) return;
  listEl.innerHTML = buildResultCards(outputs);
}

function buildResultCards(outputs) {
  let html = '';
  const verdictLabels = { TP: 'Blocked &#10003;', FP: 'Blocked &#10007;',
                          FN: 'Not Blocked &#10007;', TN: 'Not Blocked &#10003;' };

  for (const o of outputs) {
    const blocked = Boolean(o.blocked);
    const should  = Boolean(o.should_block);
    let verdict = 'TN';
    if (blocked && should)  verdict = 'TP';
    if (blocked && !should) verdict = 'FP';
    if (!blocked && should) verdict = 'FN';

    const idSafe   = escapeHtml(o.id);
    const origText = _outputs?.find(x => x.id === o.id)?.text || '';
    const textSafe = escapeHtml(origText);
    const whySafe  = escapeHtml(o.why || '');
    const ruleSafe = o.matched_rule ? escapeHtml(o.matched_rule) : '';
    const vLabel   = verdictLabels[verdict] || verdict;
    const vcls     = `d3-output-card__verdict--${verdict.toLowerCase()}`;

    const ruleHtml = ruleSafe
      ? `<div style="font-family:var(--font-mono);font-size:var(--text-xs);color:var(--color-text-muted);margin-bottom:var(--space-1)">matched: ${ruleSafe}</div>`
      : '';

    html += `<div class="d3-output-card">
      <div class="d3-output-card__header">
        <span class="d3-output-card__id">${idSafe}</span>
        <span class="d3-output-card__verdict ${vcls}">${vLabel}</span>
      </div>
      <div class="d3-output-card__text">${textSafe}</div>
      ${ruleHtml}
      <div class="d3-output-card__why">${whySafe}</div>
    </div>`;
  }
  return html;
}

async function submitToLeaderboard(d3Score) {
  try {
    await fetchJSON('/api/score', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ session_id: getSessionId(), d1_score: 0, d2_score: 0, d3_score: Number(d3Score) }),
    });
  } catch {}
}

function getSessionId() {
  let sid = sessionStorage.getItem('d6-session');
  if (!sid) { sid = crypto.randomUUID(); sessionStorage.setItem('d6-session', sid); }
  return sid;
}
