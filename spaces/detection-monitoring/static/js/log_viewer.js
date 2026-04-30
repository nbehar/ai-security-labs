/**
 * log_viewer.js — D1 Log Analysis tab for the Detection & Monitoring Lab.
 *
 * Security: All data from the API is passed through escapeHtml() before
 * interpolation into template strings. The innerHTML assignments below use
 * only author-trusted template HTML plus escaped API values — no raw model
 * output is rendered unescaped. This matches the platform-wide pattern in
 * blue-team/static/js/app.js and other spaces.
 */
import { fetchJSON, escapeHtml } from './core.js';

const PAGE_SIZE = 5;

let _logs = [];
let _classifications = {};
let _feedbackMap = {};
let _currentPage = 0;

export async function renderLogAnalysisTab(container) {
  _logs = [];
  _classifications = {};
  _feedbackMap = {};
  _currentPage = 0;

  container.innerHTML = `
    <div class="info-card" style="margin-bottom:var(--space-4)">
      <strong>D1: Log Analysis</strong> — Review the 20 log entries below from NexaCore's AI tools.
      Classify each as <strong>ATTACK</strong> or <strong>LEGITIMATE</strong>.
      Watch for the 8 attack patterns described in the Info tab.
      After each classification, a WHY card explains the decision.
    </div>
    <div id="d1-score-banner"></div>
    <div id="d1-log-cards"></div>
    <div id="d1-pagination"></div>
    <div style="margin-top:var(--space-5);text-align:center">
      <button id="d1-submit-btn" class="btn-primary" disabled>Submit All 20</button>
    </div>
    <div id="d1-final-result"></div>
  `;

  try {
    const data = await fetchJSON('/api/logs');
    _logs = data.logs;
  } catch {
    container.innerHTML += '<p style="color:var(--color-danger-light)">Failed to load logs. Please refresh.</p>';
    return;
  }

  renderScoreBanner();
  renderPage(_currentPage);
  renderPagination();
}

function renderScoreBanner() {
  const total = _logs.length;
  const classified = Object.keys(_classifications).length;
  const pct = total > 0 ? (classified / total) * 100 : 0;
  const attacksClassified = Object.values(_classifications).filter(v => v === 'ATTACK').length;

  const el = document.getElementById('d1-score-banner');
  if (!el) return;
  el.innerHTML = `
    <div class="d1-score-banner">
      <div class="d1-score-banner__stat">
        <div class="d1-score-banner__value">${classified} / ${total}</div>
        <div class="d1-score-banner__label">Classified</div>
      </div>
      <div class="d1-score-banner__stat">
        <div class="d1-score-banner__value">${attacksClassified}</div>
        <div class="d1-score-banner__label">Flagged as Attack</div>
      </div>
      <div style="flex:1">
        <div class="d1-progress-bar">
          <div class="d1-progress-bar__fill" style="width:${pct.toFixed(1)}%"></div>
        </div>
        <div style="font-size:var(--text-xs);color:var(--color-text-muted);margin-top:4px">${Math.round(pct)}% complete</div>
      </div>
    </div>
  `;
}

function renderPage(page) {
  const start = page * PAGE_SIZE;
  const slice = _logs.slice(start, start + PAGE_SIZE);
  const el = document.getElementById('d1-log-cards');
  if (!el) return;

  el.innerHTML = slice.map(log => buildLogCard(log)).join('');

  el.querySelectorAll('[data-classify]').forEach(btn => {
    btn.addEventListener('click', () => classify(btn.dataset.id, btn.dataset.classify));
  });
}

function buildLogCard(log) {
  const selected = _classifications[log.id];
  const feedback = _feedbackMap[log.id];
  const ts = new Date(log.timestamp).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});

  const attackClass = selected === 'ATTACK' ? 'selected' : '';
  const legitClass  = selected === 'LEGITIMATE' ? 'selected' : '';

  const feedbackHtml = feedback ? `
    <div class="why-card ${feedback.correct ? 'why-card--correct' : 'why-card--incorrect'}">
      ${feedback.correct ? '&#10003;' : '&#10007;'} ${escapeHtml(feedback.why)}
    </div>` : '';

  return `
    <div class="log-card" id="card-${escapeHtml(log.id)}">
      <div class="log-card__header">
        <span class="log-card__id">${escapeHtml(log.id)}</span>
        <span class="log-card__system">${escapeHtml(log.system)}</span>
        <span>${escapeHtml(ts)}</span>
        <span style="color:var(--color-text-muted)">uid:${escapeHtml(String(log.metadata.user_id))}</span>
      </div>
      <div class="log-card__body">
        <div>
          <div class="log-card__label">User Query</div>
          <div class="log-card__text log-card__text--query">${escapeHtml(log.user_query)}</div>
        </div>
        <div>
          <div class="log-card__label">Model Response</div>
          <div class="log-card__text log-card__text--response">${escapeHtml(log.model_response)}</div>
        </div>
      </div>
      <div class="log-card__actions">
        <button class="log-card__btn log-card__btn--attack ${attackClass}"
                data-classify="ATTACK" data-id="${escapeHtml(log.id)}">
          &#9888; ATTACK
        </button>
        <button class="log-card__btn log-card__btn--legit ${legitClass}"
                data-classify="LEGITIMATE" data-id="${escapeHtml(log.id)}">
          &#10003; LEGITIMATE
        </button>
      </div>
      ${feedbackHtml}
    </div>
  `;
}

async function classify(id, label) {
  _classifications[id] = label;
  updateSubmitButton();
  renderScoreBanner();

  const partial = _logs.map(l => ({
    id: l.id,
    label: _classifications[l.id] || 'LEGITIMATE',
  }));

  try {
    const result = await fetchJSON('/api/logs/classify', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ classifications: partial }),
    });
    result.entries.forEach(e => {
      if (_classifications[e.id]) {
        _feedbackMap[e.id] = { correct: e.correct, why: e.why };
      }
    });
    if (Object.keys(_classifications).length === _logs.length) {
      showFinalResult(result);
      submitLeaderboard(result.score);
    }
  } catch (err) {
    console.error('Classify error', err);
  }

  renderPage(_currentPage);
}

function updateSubmitButton() {
  const btn = document.getElementById('d1-submit-btn');
  if (!btn) return;
  const done = Object.keys(_classifications).length === _logs.length;
  btn.disabled = !done;
  if (done && !btn._wired) {
    btn._wired = true;
    btn.addEventListener('click', handleSubmitAll);
  }
}

async function handleSubmitAll() {
  const allClassifications = _logs.map(l => ({
    id: l.id,
    label: _classifications[l.id] || 'LEGITIMATE',
  }));
  try {
    const result = await fetchJSON('/api/logs/classify', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ classifications: allClassifications }),
    });
    result.entries.forEach(e => {
      _feedbackMap[e.id] = { correct: e.correct, why: e.why };
    });
    showFinalResult(result);
    submitLeaderboard(result.score);
    renderPage(_currentPage);
  } catch (err) {
    console.error('Submit error', err);
  }
}

function showFinalResult(result) {
  const el = document.getElementById('d1-final-result');
  if (!el) return;

  const color = result.score >= 80 ? 'var(--color-success-light)' :
                result.score >= 50 ? 'var(--color-warning-light)' : 'var(--color-danger-light)';

  el.innerHTML = `
    <div class="d1-score-banner" style="margin-top:var(--space-5);border-color:var(--color-accent-aisl-border)">
      <div class="d1-score-banner__stat">
        <div class="d1-score-banner__value" style="color:${color};font-size:var(--text-3xl)">${result.score}</div>
        <div class="d1-score-banner__label">D1 Score</div>
      </div>
      <div class="d1-score-banner__stat">
        <div class="d1-score-banner__value">${(result.f1 * 100).toFixed(1)}%</div>
        <div class="d1-score-banner__label">F1</div>
      </div>
      <div class="d1-score-banner__stat">
        <div class="d1-score-banner__value">${result.tp}</div>
        <div class="d1-score-banner__label">TP</div>
      </div>
      <div class="d1-score-banner__stat">
        <div class="d1-score-banner__value">${result.fp}</div>
        <div class="d1-score-banner__label">FP</div>
      </div>
      <div class="d1-score-banner__stat">
        <div class="d1-score-banner__value">${result.fn}</div>
        <div class="d1-score-banner__label">FN (missed)</div>
      </div>
    </div>
  `;
}

function renderPagination() {
  const totalPages = Math.ceil(_logs.length / PAGE_SIZE);
  const el = document.getElementById('d1-pagination');
  if (!el) return;

  el.innerHTML = `
    <div class="d1-pagination">
      <button class="d1-page-btn" id="d1-prev" ${_currentPage === 0 ? 'disabled' : ''}>← Prev</button>
      <span class="d1-page-indicator">Page ${_currentPage + 1} of ${totalPages}</span>
      <button class="d1-page-btn" id="d1-next" ${_currentPage >= totalPages - 1 ? 'disabled' : ''}>Next →</button>
    </div>
  `;

  document.getElementById('d1-prev')?.addEventListener('click', () => {
    if (_currentPage > 0) { _currentPage--; renderPage(_currentPage); renderPagination(); }
  });
  document.getElementById('d1-next')?.addEventListener('click', () => {
    if (_currentPage < totalPages - 1) { _currentPage++; renderPage(_currentPage); renderPagination(); }
  });
}

async function submitLeaderboard(d1Score) {
  try {
    await fetchJSON('/api/score', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ session_id: getSessionId(), d1_score: d1Score, d2_score: 0, d3_score: 0 }),
    });
  } catch {}
}

function getSessionId() {
  let sid = sessionStorage.getItem('d6-session');
  if (!sid) { sid = crypto.randomUUID(); sessionStorage.setItem('d6-session', sid); }
  return sid;
}
