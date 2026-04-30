// admin.js — exam-admin instructor verification and grading tool

const API = {
  verify:       '/api/verify',
  batchVerify:  '/api/batch-verify',
  rubric:       (lab) => `/api/rubric/${lab}`,
  ltiGrade:     '/api/lti/grade',
  health:       '/health',
  adminProxy:   '/api/admin/proxy',
  generateTokens: '/api/admin/generate-tokens',
};

// Known lab space URLs (auto-populated by lab_id from receipt)
const LAB_URLS = {
  'red-team':             'https://nikobehar-red-team-workshop.hf.space',
  'detection-monitoring': 'https://nikobehar-ai-sec-lab6-detection.hf.space',
  'blue-team':            'https://nikobehar-blue-team-workshop.hf.space',
  'owasp-top-10':         'https://nikobehar-llm-top-10.hf.space',
};

// =========================================================================
// Init
// =========================================================================

let _rosterTimer = null;

async function init() {
  try {
    const h = await fetchJSON(API.health);
    if (!h.exam_secret_configured) {
      document.getElementById('config-warning').classList.remove('hidden');
      const gw = document.getElementById('generate-warning');
      if (gw) gw.classList.remove('hidden');
    }
    const navStatus = document.getElementById('nav-status');
    if (navStatus) navStatus.textContent = h.lti_configured ? 'LTI enabled' : 'LTI disabled';
  } catch (_) { /* server cold-starting */ }

  setupViewNav();
  setupDropZone('drop-zone', 'file-input', false);
  setupDropZone('batch-drop-zone', 'batch-file-input', true);
  setupRosterView();
  setupGenerateView();
}

async function fetchJSON(url, opts = {}) {
  const resp = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
    ...opts,
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || data.error || resp.statusText);
  return data;
}

// =========================================================================
// View nav
// =========================================================================

const VIEWS = ['verify', 'batch', 'roster', 'generate'];

function setupViewNav() {
  document.querySelectorAll('.view-nav__btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.view-nav__btn').forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
      });
      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');
      const active = btn.dataset.view;
      VIEWS.forEach(v => {
        const el = document.getElementById(`view-${v}`);
        if (el) el.classList.toggle('hidden', v !== active);
      });
      if (active !== 'roster' && _rosterTimer) {
        clearInterval(_rosterTimer);
        _rosterTimer = null;
      }
    });
  });
}

// =========================================================================
// Drop zones (shared helper)
// =========================================================================

function setupDropZone(zoneId, inputId, multiple) {
  const zone  = document.getElementById(zoneId);
  const input = document.getElementById(inputId);
  if (!zone || !input) return;

  const trigger = () => input.click();
  zone.addEventListener('click', e => { if (!e.target.matches('button')) trigger(); });
  zone.querySelector('button')?.addEventListener('click', e => { e.stopPropagation(); trigger(); });
  zone.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') trigger(); });
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    handleFiles(Array.from(e.dataTransfer.files), multiple);
  });
  input.addEventListener('change', () => {
    handleFiles(Array.from(input.files), multiple);
    input.value = '';
  });
}

function handleFiles(files, multiple) {
  if (!files.length) return;
  if (multiple) processBatchFiles(files);
  else processSingleFile(files[0]);
}

// =========================================================================
// Single verify
// =========================================================================

async function processSingleFile(file) {
  const errorEl  = document.getElementById('verify-error');
  const resultEl = document.getElementById('verify-result');
  errorEl.classList.add('hidden');
  resultEl.innerHTML = '<p style="color:var(--color-text-muted);padding:16px 0">Verifying…</p>';

  let receipt;
  try {
    receipt = JSON.parse(await file.text());
  } catch {
    showError(errorEl, 'Not a valid JSON file.');
    resultEl.innerHTML = '';
    return;
  }

  if (!receipt.receipt_version && !receipt.student_id) {
    showError(errorEl, 'File does not look like an AI Security Labs receipt.');
    resultEl.innerHTML = '';
    return;
  }

  try {
    const result = await fetchJSON(API.verify, { method: 'POST', body: JSON.stringify({ receipt }) });
    resultEl.innerHTML = renderVerifyResult(result);
    bindVerifyActions(result);
  } catch (e) {
    showError(errorEl, `Verification failed: ${e.message}`);
    resultEl.innerHTML = '';
  }
}

function renderVerifyResult(result) {
  const badge = result.hmac_valid
    ? '<span class="hmac-badge hmac-badge--valid">✓ HMAC VERIFIED</span>'
    : '<span class="hmac-badge hmac-badge--invalid">✗ INVALID HMAC</span>';

  const p = result.practical || {};
  const t = result.theory    || {};
  const timing = result.timing || {};

  const exRows = (p.exercises || []).map(ex =>
    `<div class="score-row">
      <span>${esc(ex.display_name || ex.exercise_id)}</span>
      <span class="score-value">${ex.earned_score} / ${ex.max_score}</span>
    </div>`).join('');

  const elapsed = timing.total_elapsed_seconds
    ? `${Math.floor(timing.total_elapsed_seconds/60)}m ${timing.total_elapsed_seconds%60}s`
    : '—';
  const limit = timing.time_limit_seconds ? `${timing.time_limit_seconds/3600}h` : '—';

  const theoryHtml = t.submitted === false
    ? '<p style="color:var(--color-text-muted);font-size:var(--text-sm)">Student did not submit theory section.</p>'
    : `<div class="score-row"><span>MCQ</span><span class="score-value">${t.mcq_score??'—'} / ${t.mcq_max??'—'}</span></div>
       <div class="score-row"><span>Short answers</span><span class="score-value">pending / ${t.short_answer_max??60}</span></div>
       <div class="score-row score-row--total"><span>Theory so far</span><span class="score-value">${t.mcq_score??0} / ${t.mcq_max??0}</span></div>`;

  const saBtn = t.submitted !== false
    ? '<button class="expand-btn" id="sa-toggle-btn">▼ Short Answers &amp; Rubric</button>' : '';

  const accomBtn = result.hmac_valid
    ? '<button class="expand-btn" id="accom-toggle-btn">⚙ Accommodation Controls</button>' : '';

  const exIds = (p.exercises || []).map(ex => ex.exercise_id);
  const exSelOpts = exIds.map(id => `<option value="${esc(id)}">${esc(id)}</option>`).join('');
  const defaultLabUrl = LAB_URLS[result.lab_id] || '';

  return `
    <div class="result-card">
      <div class="result-card__header">
        ${badge}
        <div class="result-card__meta">
          <strong>${esc(result.student_id||'—')}</strong>
          &nbsp;·&nbsp;${esc(result.exam_id||'—')}
          &nbsp;·&nbsp;${esc(result.lab_id||'—')}
          &nbsp;·&nbsp;v${esc(result.receipt_version||'1')}
        </div>
      </div>
      <div class="result-card__scores">
        <div class="score-panel">
          <div class="score-panel__title">Practical</div>
          ${exRows}
          <div class="score-row score-row--total">
            <span>Total</span>
            <span class="score-value">${p.total_practical_score??0} / ${p.max_practical_score??0}</span>
          </div>
        </div>
        <div class="score-panel">
          <div class="score-panel__title">Theory</div>
          ${theoryHtml}
        </div>
      </div>
      <div style="font-size:var(--text-xs);color:var(--color-text-muted);margin-bottom:var(--space-4)">
        Timing: ${elapsed} used / ${limit} limit
      </div>
      <div class="action-bar">
        ${saBtn}
        <button class="expand-btn" id="csv-export-btn">↓ Export CSV Row</button>
        <button class="expand-btn" id="lti-grade-btn" style="display:none">Submit Grade to Canvas</button>
        ${accomBtn}
      </div>
      <div id="sa-panel" class="sa-panel hidden"></div>
      <div id="accom-panel" class="accom-panel hidden">
        <div class="accom-panel__title">⚙ Accommodation Controls</div>
        <p class="accom-note">These controls reach the live exam session on the lab server.
           The student token comes from your roster CSV.</p>
        <div class="form-row">
          <div class="form-field">
            <label class="form-label" for="accom-lab-url">Lab Space URL</label>
            <input type="url" id="accom-lab-url" class="form-input" value="${esc(defaultLabUrl)}">
          </div>
          <div class="form-field">
            <label class="form-label" for="accom-token">Student Token</label>
            <input type="text" id="accom-token" class="form-input" placeholder="Paste from roster CSV">
          </div>
        </div>
        <div class="accom-actions">
          <div class="accom-action-row">
            <span class="accom-label">Extend time</span>
            <input type="number" id="accom-minutes" class="form-input form-input--narrow" value="60" min="1">
            <span style="font-size:var(--text-sm);color:var(--color-text-secondary)">min</span>
            <button class="expand-btn" id="accom-extend-btn">Add Time</button>
          </div>
          <div class="accom-action-row">
            <span class="accom-label">Reset exercise</span>
            <select id="accom-exercise-sel" class="form-input form-input--narrow">${exSelOpts}</select>
            <input type="text" id="accom-reason" class="form-input" placeholder="reason">
            <button class="expand-btn" id="accom-reset-btn">Reset</button>
          </div>
          <div class="accom-action-row">
            <button class="expand-btn" id="accom-pause-btn">Pause Exam</button>
            <button class="expand-btn" id="accom-resume-btn">Resume Exam</button>
          </div>
        </div>
        <div id="accom-log" class="accom-log hidden"></div>
        <div id="accom-error" class="error-msg hidden" role="alert" style="margin-top:var(--space-3)"></div>
      </div>
    </div>`;
}

function bindVerifyActions(result) {
  const saToggle = document.getElementById('sa-toggle-btn');
  const saPanel  = document.getElementById('sa-panel');
  const csvBtn   = document.getElementById('csv-export-btn');
  const ltiBtn   = document.getElementById('lti-grade-btn');
  const accomBtn = document.getElementById('accom-toggle-btn');
  const accomPanel = document.getElementById('accom-panel');

  if (saToggle && saPanel) {
    saToggle.addEventListener('click', async () => {
      if (!saPanel.classList.contains('hidden')) {
        saPanel.classList.add('hidden');
        saToggle.textContent = '▼ Short Answers & Rubric';
        return;
      }
      saToggle.textContent = '▲ Short Answers & Rubric';
      saPanel.innerHTML = '<p style="color:var(--color-text-muted);font-size:var(--text-sm)">Loading rubric…</p>';
      saPanel.classList.remove('hidden');
      await loadSAPanel(saPanel, result);
    });
  }

  if (csvBtn) csvBtn.addEventListener('click', () => exportCSVRow(result));

  if (ltiBtn && result.hmac_valid && result.lab_id) {
    ltiBtn.style.display = '';
    ltiBtn.addEventListener('click', () => submitLTIGrade(result, ltiBtn));
  }

  if (accomBtn && accomPanel) {
    accomBtn.addEventListener('click', () => {
      const hidden = accomPanel.classList.toggle('hidden');
      accomBtn.textContent = hidden ? '⚙ Accommodation Controls' : '✕ Close Accommodations';
    });
    bindAccomActions(result);
  }
}

// =========================================================================
// Accommodation controls
// =========================================================================

function bindAccomActions(result) {
  const getToken  = () => (document.getElementById('accom-token')?.value || '').trim();
  const getLabUrl = () => (document.getElementById('accom-lab-url')?.value || '').trim();
  const errEl     = document.getElementById('accom-error');
  const logEl     = document.getElementById('accom-log');

  function logAction(msg) {
    if (!logEl) return;
    logEl.classList.remove('hidden');
    const ts = new Date().toLocaleTimeString();
    logEl.innerHTML += `<div class="accom-log__entry">[${ts}] ${esc(msg)}</div>`;
  }

  async function proxyCmd(endpoint, payload = {}) {
    const token  = getToken();
    const labUrl = getLabUrl();
    if (!token)  { showError(errEl, 'Student token required'); return null; }
    if (!labUrl) { showError(errEl, 'Lab Space URL required'); return null; }
    errEl?.classList.add('hidden');
    return fetchJSON(API.adminProxy, {
      method: 'POST',
      body: JSON.stringify({ lab_url: labUrl, endpoint, payload: { token, ...payload } }),
    });
  }

  document.getElementById('accom-extend-btn')?.addEventListener('click', async () => {
    const mins = parseInt(document.getElementById('accom-minutes')?.value || '60');
    const res  = await proxyCmd('/api/admin/extend-time', { additional_seconds: mins * 60 });
    if (res) logAction(`Added ${mins}min. New limit: ${Math.round(res.new_time_limit_seconds/60)}min, remaining: ${Math.round(res.remaining_seconds/60)}min`);
  });

  document.getElementById('accom-reset-btn')?.addEventListener('click', async () => {
    const exId   = document.getElementById('accom-exercise-sel')?.value;
    const reason = (document.getElementById('accom-reason')?.value || '').trim();
    if (!exId) { showError(errEl, 'Select an exercise'); return; }
    const res = await proxyCmd('/api/admin/reset-attempts', { exercise_id: exId, reason });
    if (res) logAction(`Reset ${res.attempts_cleared} attempt(s) for ${exId}${reason ? ` (${reason})` : ''}`);
  });

  document.getElementById('accom-pause-btn')?.addEventListener('click', async () => {
    const res = await proxyCmd('/api/admin/pause-exam');
    if (res) logAction(res.already_paused ? 'Exam already paused' : `Exam paused at ${new Date(res.paused_at*1000).toLocaleTimeString()}`);
  });

  document.getElementById('accom-resume-btn')?.addEventListener('click', async () => {
    const res = await proxyCmd('/api/admin/resume-exam');
    if (res?.not_paused) { logAction('Exam was not paused'); return; }
    if (res) logAction(`Exam resumed. Pause duration: ${res.pause_duration_seconds}s added back. Remaining: ${Math.round(res.remaining_seconds/60)}min`);
  });
}

// =========================================================================
// SA scoring panel
// =========================================================================

async function loadSAPanel(container, result) {
  const labId       = result.lab_id || '';
  const shortAnswers = (result.theory || {}).short_answers || [];
  const saMap        = {};
  shortAnswers.forEach(sa => { saMap[sa.question_id] = sa; });

  let rubric;
  try {
    rubric = await fetchJSON(API.rubric(labId));
  } catch {
    container.innerHTML = '<p style="color:var(--color-text-muted);font-size:var(--text-sm)">Rubric not available for this lab.</p>';
    return;
  }

  const questions = rubric.short_answers || [];
  if (!questions.length) {
    container.innerHTML = '<p style="color:var(--color-text-muted);font-size:var(--text-sm)">No short-answer questions for this lab.</p>';
    return;
  }

  container.innerHTML = questions.map((q, i) => {
    const sa       = saMap[q.question_id] || {};
    const response = sa.student_response || '';
    const wc       = sa.word_count || (response ? response.split(/\s+/).filter(Boolean).length : 0);
    const criteria = Object.entries(q.rubric || {});
    const rubricRows = criteria.map(([key, crit]) =>
      `<div class="rubric-row">
        <span class="rubric-criterion">${esc(fmtCriterion(key))}</span>
        <span class="rubric-weight">×${crit.weight||1.0}</span>
        <div class="rubric-scores">
          ${[0,1,2,3,4].map(n =>
            `<button class="score-btn" data-q="${i}" data-crit="${esc(key)}" data-val="${n}">${n}</button>`
          ).join('')}
        </div>
      </div>`).join('');

    return `
      <div class="sa-question">
        <div class="sa-question__header">
          <span class="sa-question__id">SA-${i+1} · Bloom L${q.bloom_level||'?'}</span>
          <span class="sa-question__points">${q.points||20} pts</span>
        </div>
        <div class="sa-question__text">${esc(q.question)}</div>
        <div class="sa-response${response?'':' sa-response--empty'}">${response ? esc(response) : 'No response submitted.'}</div>
        ${response ? `<div class="sa-response__word-count">${wc} words</div>` : ''}
        <div>${rubricRows}</div>
        <div class="sa-subtotal">
          <span class="sa-subtotal__label">Subtotal</span>
          <span class="sa-subtotal__value" id="subtotal-${i}">0 / ${q.points||20}</span>
        </div>
      </div>`;
  }).join('');

  container.querySelectorAll('.score-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const q    = btn.dataset.q;
      const crit = btn.dataset.crit;
      container.querySelectorAll(`.score-btn[data-q="${q}"][data-crit="${crit}"]`)
        .forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      const total = [...container.querySelectorAll(`.score-btn[data-q="${q}"].selected`)]
        .reduce((s, b) => s + parseInt(b.dataset.val||0), 0);
      const el = document.getElementById(`subtotal-${q}`);
      if (el) el.textContent = `${total} / ${questions[parseInt(q)]?.points||20}`;
    });
  });
}

function fmtCriterion(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// =========================================================================
// LTI grade submit
// =========================================================================

async function submitLTIGrade(result, btn) {
  const p = result.practical || {};
  const t = result.theory    || {};
  const saTotal = [...document.querySelectorAll('.score-btn.selected')]
    .reduce((s, b) => s + parseInt(b.dataset.val||0), 0);
  const total = (p.total_practical_score||0) + (t.mcq_score||0) + saTotal;
  const max   = (p.max_practical_score||0)   + (t.mcq_max||0)   + (t.short_answer_max||60);

  btn.disabled = true;
  btn.textContent = 'Submitting…';
  try {
    await fetchJSON(API.ltiGrade, {
      method: 'POST',
      body: JSON.stringify({
        student_id: result.student_id, lab_id: result.lab_id, exam_id: result.exam_id,
        practical_score: p.total_practical_score||0, max_practical_score: p.max_practical_score||0,
        mcq_score: t.mcq_score||0, mcq_max: t.mcq_max||0,
        sa_score: saTotal, sa_max: t.short_answer_max||60,
        total_score: total, total_max: max,
      }),
    });
    btn.textContent = '✓ Grade submitted to Canvas';
    btn.style.color = 'var(--color-success)';
  } catch (e) {
    btn.disabled = false;
    btn.textContent = 'Submit Grade to Canvas';
    showError(document.getElementById('verify-error'), `LTI grade passback failed: ${e.message}`);
  }
}

// =========================================================================
// Batch verify
// =========================================================================

async function processBatchFiles(files) {
  const errorEl  = document.getElementById('batch-error');
  const resultEl = document.getElementById('batch-result');
  errorEl.classList.add('hidden');
  resultEl.innerHTML = '<p style="color:var(--color-text-muted);padding:16px 0">Processing…</p>';

  const receipts = [];
  for (const file of files) {
    try { receipts.push(JSON.parse(await file.text())); } catch { /* skip invalid */ }
  }
  if (!receipts.length) {
    showError(errorEl, 'No valid JSON files found.');
    resultEl.innerHTML = '';
    return;
  }

  try {
    const resp = await fetchJSON(API.batchVerify, { method: 'POST', body: JSON.stringify({ receipts }) });
    resultEl.innerHTML = renderBatchResult(resp);
    bindBatchActions(resp, receipts);
  } catch (e) {
    showError(errorEl, `Batch verification failed: ${e.message}`);
    resultEl.innerHTML = '';
  }
}

function renderBatchResult(resp) {
  const rows = resp.results.map(r => {
    const badge = r.hmac_valid
      ? '<span style="color:var(--color-success)">✓</span>'
      : '<span style="color:var(--color-danger)">✗</span>';
    return `<tr class="batch-row" data-index="${r.index}">
      <td>${badge}</td>
      <td class="mono">${esc(r.student_id||'—')}</td>
      <td class="mono">${esc(r.exam_id||'—')}</td>
      <td class="mono">${esc(r.lab_id||'—')}</td>
      <td class="mono">${r.hmac_valid ? (r.practical_score??'—') : '—'}</td>
      <td class="mono">${r.hmac_valid ? (r.mcq_score??'—') : '—'}</td>
      <td class="mono">—</td>
    </tr>`;
  }).join('');

  return `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-3)">
      <span style="font-size:var(--text-sm);color:var(--color-text-secondary)">
        ${resp.valid_count} valid &middot; ${resp.invalid_count} invalid &middot; ${resp.total} total
      </span>
      <button class="expand-btn" id="batch-csv-btn">↓ Export CSV</button>
    </div>
    <table class="batch-table">
      <caption class="sr-only">Batch verification results</caption>
      <thead><tr>
        <th>HMAC</th><th>Student</th><th>Exam ID</th><th>Lab</th>
        <th>Practical</th><th>MCQ</th><th>SA</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function bindBatchActions(resp, receipts) {
  const csvBtn = document.getElementById('batch-csv-btn');
  if (csvBtn) csvBtn.addEventListener('click', () => exportBatchCSV(resp));

  document.querySelectorAll('.batch-row').forEach(row => {
    row.addEventListener('click', () => {
      const idx     = parseInt(row.dataset.index);
      const result  = resp.results[idx];
      if (!result) return;
      document.querySelector('[data-view="verify"]').click();
      document.getElementById('verify-result').innerHTML = renderVerifyResult(result);
      bindVerifyActions(result);
    });
  });
}

// =========================================================================
// Roster view
// =========================================================================

function setupRosterView() {
  const btn = document.getElementById('roster-load-btn');
  const autoEl = document.getElementById('roster-auto-refresh');
  if (!btn) return;

  btn.addEventListener('click', () => loadRoster());

  autoEl?.addEventListener('change', () => {
    if (_rosterTimer) clearInterval(_rosterTimer);
    if (autoEl.checked) _rosterTimer = setInterval(loadRoster, 30000);
  });
  // Start auto-refresh when roster tab becomes active
  document.querySelector('[data-view="roster"]')?.addEventListener('click', () => {
    if (document.getElementById('roster-auto-refresh')?.checked) {
      _rosterTimer = setInterval(loadRoster, 30000);
    }
  });
}

async function loadRoster() {
  const labUrl = (document.getElementById('lab-url-input')?.value || '').trim();
  const errEl  = document.getElementById('roster-error');
  const resEl  = document.getElementById('roster-result');
  if (!labUrl) { showError(errEl, 'Enter a Lab Space URL first'); return; }
  errEl?.classList.add('hidden');

  try {
    const data = await fetchJSON(API.adminProxy, {
      method: 'POST',
      body: JSON.stringify({
        lab_url: labUrl,
        endpoint: '/api/admin/roster',
        method: 'GET',
        payload: {},
      }),
    });
    if (resEl) resEl.innerHTML = renderRoster(data);
  } catch (e) {
    showError(errEl, `Could not load roster: ${e.message}`);
  }
}

function renderRoster(data) {
  const students = data.students || [];
  const avgs     = data.class_averages || {};
  const notStarted = data.not_started || [];

  if (!students.length && !notStarted.length) {
    return '<p style="color:var(--color-text-muted);padding:16px 0">No active sessions found.</p>';
  }

  function statusIcon(ex) {
    if (ex.cap_exhausted && ex.best_score < 50) return '<span title="Cap exhausted, low score" style="color:var(--color-danger)">⚠</span>';
    if (ex.cap_exhausted) return '<span title="Complete" style="color:var(--color-success)">✅</span>';
    if (ex.attempts > 0)  return '<span title="In progress" style="color:var(--color-warning)">⏳</span>';
    return '<span title="Not started">—</span>';
  }

  const headers = ['Student', 'Time Left', ...(students[0]?.exercises||[]).map(e => e.exercise_id), 'Theory', 'Total'];
  const hRow = headers.map(h => `<th>${esc(h)}</th>`).join('');

  const rows = students.map(s => {
    const paused = s.paused ? ' ⏸' : '';
    const expired = s.expired ? ' ⏱' : '';
    const exCells = (s.exercises||[]).map(ex =>
      `<td class="roster-cell">${statusIcon(ex)}<span class="roster-score">${ex.best_score}</span></td>`
    ).join('');
    return `<tr>
      <td class="mono">${esc(s.student_id)}${paused}${expired}</td>
      <td class="mono">${s.remaining_minutes}m</td>
      ${exCells}
      <td>${s.theory_submitted ? '✅' : '—'}</td>
      <td class="mono">${s.total_so_far}</td>
    </tr>`;
  }).join('');

  const avgCells = (students[0]?.exercises||[]).map(ex =>
    `<td class="mono">${avgs[ex.exercise_id]??'—'}</td>`
  ).join('');
  const avgRow = `<tr style="font-weight:600;border-top:2px solid var(--color-border)">
    <td>Class avg</td><td>—</td>${avgCells}<td>—</td><td>—</td></tr>`;

  const notStartedHtml = notStarted.length
    ? `<p style="margin-top:var(--space-4);font-size:var(--text-sm);color:var(--color-text-muted)">
        Not started (${notStarted.length}): ${notStarted.map(s => esc(s)).join(', ')}</p>`
    : '';

  return `
    <div style="font-size:var(--text-sm);color:var(--color-text-secondary);margin-bottom:var(--space-3)">
      ${esc(data.lab_id||'')} · ${students.length} active
    </div>
    <div style="overflow-x:auto">
      <table class="batch-table roster-table">
        <caption class="sr-only">Live exam roster</caption>
        <thead><tr>${hRow}</tr></thead>
        <tbody>${rows}${avgRow}</tbody>
      </table>
    </div>
    ${notStartedHtml}`;
}

// =========================================================================
// Generate tokens
// =========================================================================

let _rosterStudentIds = [];

function setupGenerateView() {
  const zone  = document.getElementById('gen-drop-zone');
  const input = document.getElementById('gen-file-input');
  const btn   = document.getElementById('gen-generate-btn');
  if (!zone || !input || !btn) return;

  const trigger = () => input.click();
  zone.addEventListener('click', e => { if (!e.target.matches('button')) trigger(); });
  zone.querySelector('button')?.addEventListener('click', e => { e.stopPropagation(); trigger(); });
  zone.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') trigger(); });
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    if (e.dataTransfer.files[0]) parseRosterCSV(e.dataTransfer.files[0]);
  });
  input.addEventListener('change', () => {
    if (input.files[0]) parseRosterCSV(input.files[0]);
    input.value = '';
  });

  btn.addEventListener('click', runGenerate);
}

async function parseRosterCSV(file) {
  const text = await file.text();
  const lines = text.trim().split('\n');
  if (!lines.length) return;

  const header = lines[0].split(',').map(s => s.trim().replace(/"/g,'').toLowerCase());
  const sidCol = header.indexOf('student_id') >= 0 ? header.indexOf('student_id') : 0;

  _rosterStudentIds = lines.slice(1).map(l => {
    const parts = l.split(',');
    return (parts[sidCol] || '').trim().replace(/"/g,'');
  }).filter(Boolean);

  const preview = document.getElementById('gen-roster-preview');
  if (preview) {
    const sample = _rosterStudentIds.slice(0, 5);
    preview.innerHTML = `<p class="roster-preview__count">${_rosterStudentIds.length} students loaded</p>
      <p class="roster-preview__sample">Preview: ${sample.map(esc).join(', ')}${_rosterStudentIds.length > 5 ? '…' : ''}</p>`;
    preview.classList.remove('hidden');
  }
}

async function runGenerate() {
  const errEl  = document.getElementById('generate-error');
  const resEl  = document.getElementById('gen-result');
  const btn    = document.getElementById('gen-generate-btn');
  errEl?.classList.add('hidden');
  resEl?.classList.add('hidden');

  const examId   = (document.getElementById('gen-exam-id')?.value || '').trim();
  const section  = document.querySelector('input[name="gen-section"]:checked')?.value || 'A';
  const duration = parseInt(document.getElementById('gen-duration')?.value || '3');
  const opensStr = document.getElementById('gen-opens-at')?.value;
  const expStr   = document.getElementById('gen-expires-at')?.value;

  if (!examId)  { showError(errEl, 'Exam ID is required'); return; }
  if (!_rosterStudentIds.length) { showError(errEl, 'Upload a roster CSV first'); return; }
  if (!expStr)  { showError(errEl, 'Closes-at date/time is required'); return; }

  const opensAt  = opensStr ? Math.floor(new Date(opensStr).getTime() / 1000) : Math.floor(Date.now() / 1000);
  const expiresAt = Math.floor(new Date(expStr).getTime() / 1000);

  btn.disabled = true;
  btn.textContent = 'Generating…';
  try {
    const resp = await fetchJSON(API.generateTokens, {
      method: 'POST',
      body: JSON.stringify({
        exam_id: examId,
        student_ids: _rosterStudentIds,
        lab_ids: ['red-team', 'detection-monitoring'],
        section,
        duration_hours: duration,
        opens_at: opensAt,
        expires_at: expiresAt,
      }),
    });
    if (resEl) {
      resEl.innerHTML = renderGenerateResult(resp, examId);
      resEl.classList.remove('hidden');
      bindGenerateActions(resp, examId);
    }
  } catch (e) {
    showError(errEl, `Generation failed: ${e.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate Tokens';
  }
}

function renderGenerateResult(resp, examId) {
  return `
    <div class="gen-result-summary">
      <strong>✓ ${resp.count} tokens generated</strong> for ${esc(examId)}
    </div>
    <div class="action-bar" style="margin-top:var(--space-4)">
      <button class="expand-btn" id="gen-dl-csv-btn">↓ Download Token CSV</button>
      <button class="expand-btn" id="gen-copy-announce-btn">📋 Copy Canvas Announcement</button>
    </div>`;
}

function bindGenerateActions(resp, examId) {
  document.getElementById('gen-dl-csv-btn')?.addEventListener('click', () => {
    const hdr = 'student_id,token,primary_exam_url';
    const rows = resp.tokens.map(t =>
      [csvQ(t.student_id), csvQ(t.token), csvQ(t.primary_exam_url)].join(','));
    dlText(`${examId}_tokens.csv`, [hdr, ...rows].join('\n'));
  });

  document.getElementById('gen-copy-announce-btn')?.addEventListener('click', () => {
    const msg = `Your exam token for ${examId} is in the Feedback column of the assignment. ` +
      `Open the exam URL included with your token to begin. Tokens expire at the exam close time.`;
    navigator.clipboard.writeText(msg).then(() => {
      const btn = document.getElementById('gen-copy-announce-btn');
      if (btn) { btn.textContent = '✓ Copied!'; setTimeout(() => { btn.textContent = '📋 Copy Canvas Announcement'; }, 2000); }
    });
  });
}

// =========================================================================
// CSV export
// =========================================================================

function exportCSVRow(result) {
  const p = result.practical || {};
  const t = result.theory    || {};
  const hdr = 'student_id,lab_id,exam_id,hmac_valid,practical_score,max_practical,mcq_score,mcq_max,theory_submitted';
  const row = [
    csvQ(result.student_id||''), csvQ(result.lab_id||''), csvQ(result.exam_id||''),
    result.hmac_valid ? 'TRUE' : 'FALSE',
    p.total_practical_score??0, p.max_practical_score??0,
    t.mcq_score??0, t.mcq_max??0,
    t.submitted ? 'TRUE' : 'FALSE',
  ].join(',');
  dlText(`receipt_${result.student_id||'unknown'}.csv`, `${hdr}\n${row}`);
}

function exportBatchCSV(resp) {
  const hdr = 'student_id,lab_id,exam_id,hmac_valid,practical_score,max_practical,mcq_score,mcq_max,theory_submitted';
  const rows = resp.results.map(r =>
    [csvQ(r.student_id||''), csvQ(r.lab_id||''), csvQ(r.exam_id||''),
     r.hmac_valid?'TRUE':'FALSE',
     r.practical_score??0, r.max_practical_score??0,
     r.mcq_score??0, r.mcq_max??0,
     r.theory_submitted?'TRUE':'FALSE'].join(','));
  dlText('batch_results.csv', [hdr, ...rows].join('\n'));
}

function csvQ(v) {
  v = String(v);
  return (v.includes(',') || v.includes('"') || v.includes('\n')) ? `"${v.replace(/"/g,'""')}"` : v;
}

function dlText(name, content) {
  const a = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(new Blob([content], { type: 'text/csv' })),
    download: name,
  });
  a.click();
  URL.revokeObjectURL(a.href);
}

// =========================================================================
// Utilities
// =========================================================================

function showError(el, msg) {
  if (!el) return;
  el.textContent = `✕ ${msg}`;
  el.classList.remove('hidden');
}

function esc(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

document.addEventListener('DOMContentLoaded', init);
