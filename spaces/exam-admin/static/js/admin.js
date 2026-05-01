// admin.js — exam-admin instructor verification and grading tool

const API = {
  verify:      '/api/verify',
  batchVerify: '/api/batch-verify',
  rubric:      (lab) => `/api/rubric/${lab}`,
  ltiGrade:    '/api/lti/grade',
  health:      '/health',
};

// =========================================================================
// Init
// =========================================================================

async function init() {
  try {
    const h = await fetchJSON(API.health);
    if (!h.exam_secret_configured) {
      document.getElementById('config-warning').classList.remove('hidden');
    }
    const navStatus = document.getElementById('nav-status');
    if (navStatus) navStatus.textContent = h.lti_configured ? 'LTI enabled' : 'LTI disabled';
  } catch (_) { /* server cold-starting */ }

  setupViewNav();
  setupDropZone('drop-zone', 'file-input', false);
  setupDropZone('batch-drop-zone', 'batch-file-input', true);
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

function setupViewNav() {
  document.querySelectorAll('.view-nav__btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.view-nav__btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const active = btn.dataset.view;
      document.getElementById('view-verify').classList.toggle('hidden', active !== 'verify');
      document.getElementById('view-batch').classList.toggle('hidden', active !== 'batch');
    });
  });
}

// =========================================================================
// Drop zones
// =========================================================================

function setupDropZone(zoneId, inputId, multiple) {
  const zone  = document.getElementById(zoneId);
  const input = document.getElementById(inputId);
  if (!zone || !input) return;

  zone.addEventListener('click', () => input.click());
  zone.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') input.click(); });
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
      </div>
      <div id="sa-panel" class="sa-panel hidden"></div>
    </div>`;
}

function bindVerifyActions(result) {
  const saToggle = document.getElementById('sa-toggle-btn');
  const saPanel  = document.getElementById('sa-panel');
  const csvBtn   = document.getElementById('csv-export-btn');
  const ltiBtn   = document.getElementById('lti-grade-btn');

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
      // Switch to verify view and render that receipt's result
      document.querySelector('[data-view="verify"]').click();
      document.getElementById('verify-result').innerHTML = renderVerifyResult(result);
      bindVerifyActions(result);
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
  el.textContent = msg;
  el.classList.remove('hidden');
}

function esc(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

document.addEventListener('DOMContentLoaded', init);
