/**
 * exam_mode.js — Client-side exam infrastructure for AI Security Labs.
 *
 * Security: The client-side WebCrypto HMAC (using first 32 bytes of token as key
 * material) detects casual tampering. The authoritative authenticity check is the
 * server-side EXAM_SECRET HMAC re-derivation in the exam-admin space.
 */
import { fetchJSON, escapeHtml } from './core.js';

// ─── Token detection ──────────────────────────────────────────────────────────

export function detectExamToken() {
  return new URLSearchParams(window.location.search).get('exam_token') || null;
}

export function detectPreviewToken() {
  return new URLSearchParams(window.location.search).get('preview') || '';
}

// ─── Session state ────────────────────────────────────────────────────────────

let _examCtx = null;
let _examToken = null;
let _labId = null;
let _statusCache = null;

// ─── Session initialization ───────────────────────────────────────────────────

export async function initExamMode(token, labId) {
  const ctx = await fetchJSON('/api/exam/validate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token }),
  });
  _examCtx = ctx;
  _examToken = token;
  _labId = labId;
  _statusCache = null;
  return ctx;
}

/** Returns true when a validated exam session is active. */
export function isExamActive() {
  return _examCtx !== null;
}

/** Returns the exam context object from /api/exam/validate. */
export function getExamContext() {
  return _examCtx;
}

/**
 * Returns remaining attempts for an exercise, or null if uncapped / no exam.
 * Uses the status cache (refreshed by refreshStatus()). Falls back to
 * attempt_caps from the initial context on first call.
 */
export function getRemainingAttempts(exerciseId) {
  if (!_examCtx) return null;
  if (_statusCache) {
    const ex = (_statusCache.exercises || []).find(e => e.exercise_id === exerciseId);
    if (ex) return ex.remaining_attempts;
  }
  const cap = _examCtx.attempt_caps?.[exerciseId];
  return cap !== undefined ? cap : null;
}

/**
 * Wraps a fetch payload with the exam_token field so the server can
 * identify the exam session and enforce attempt caps.
 */
export function wrapPayload(payload) {
  if (!_examToken) return payload;
  return { ...payload, exam_token: _examToken };
}

/** Mounts the exam banner inside the page's main layout container. */
export function mountExamBanner() {
  if (!_examCtx) return;
  const container = document.querySelector('.container')
    || document.querySelector('.layout')
    || document.body;
  renderExamBanner(_examCtx, container);
}

/** Refreshes per-exercise attempt counts from /api/exam/status. */
export async function refreshStatus() {
  if (!_examToken) return;
  try {
    _statusCache = await fetchJSON(`/api/exam/status?token=${encodeURIComponent(_examToken)}`);
  } catch (err) {
    console.error('Failed to refresh exam status:', err);
  }
}

/**
 * Renders the theory assessment form into container.
 * onComplete is called after successful submission (use to switch tabs).
 */
export function renderTheoryTab(container, onComplete) {
  renderTheoryAssessment(container, _examToken, _labId, onComplete);
}

/**
 * Renders the receipt download UI into container.
 */
export function renderReceiptTab(container) {
  container.innerHTML = `
    <div class="theory-assessment">
      <div class="theory-header">
        <h2 class="theory-title">Download Exam Receipt</h2>
        <p class="theory-subtitle">
          Your signed exam receipt includes practical scores, MCQ results, and
          short-answer responses. Download it and submit to your LMS.
        </p>
      </div>
      <button id="receipt-download-btn" class="btn-primary">⬇ Download Signed Receipt</button>
      <div id="receipt-status" style="margin-top:12px;min-height:1.5em;"></div>
    </div>`;

  document.getElementById('receipt-download-btn')?.addEventListener('click', async () => {
    const btn = document.getElementById('receipt-download-btn');
    const status = document.getElementById('receipt-status');
    if (btn) { btn.disabled = true; btn.textContent = 'Generating receipt…'; }
    try {
      await signAndDownloadReceipt(_examToken, _labId);
      if (status) status.innerHTML = '<span style="color:var(--green);">Receipt downloaded successfully.</span>';
    } catch (err) {
      if (status) status.innerHTML = `<span style="color:var(--red);">Error: ${escapeHtml(String(err.message || err))}</span>`;
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '⬇ Download Signed Receipt'; }
    }
  });
}

// ─── Exam banner + countdown timer ───────────────────────────────────────────

let _timerInterval = null;

export function renderExamBanner(ctx, container) {
  // Suppress exam timer and attempt counter in preview mode.
  if (detectPreviewToken()) return;

  const banner = document.createElement('div');
  banner.id = 'exam-banner';
  container.insertBefore(banner, container.firstChild);

  const endMs = Date.now() + (ctx.time_limit_seconds - (ctx.elapsed_seconds || 0)) * 1000;

  function tick() {
    const remaining = Math.max(0, Math.floor((endMs - Date.now()) / 1000));
    const h = Math.floor(remaining / 3600);
    const m = Math.floor((remaining % 3600) / 60);
    const s = remaining % 60;
    const timeStr = `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
    const urgencyClass = remaining < 300 ? 'exam-banner--critical'
                       : remaining < 900 ? 'exam-banner--warning' : '';
    banner.className = `exam-banner ${urgencyClass}`;
    banner.innerHTML = `
      <div class="exam-banner__inner">
        <span class="exam-banner__label">EXAM MODE</span>
        <span class="exam-banner__student">${escapeHtml(ctx.student_id)}</span>
        <span class="exam-banner__timer">${timeStr}</span>
        <span class="exam-banner__exam-id">${escapeHtml(ctx.exam_id)}</span>
      </div>`;
    if (remaining === 0) {
      clearInterval(_timerInterval);
      banner.insertAdjacentHTML('beforeend',
        '<div class="exam-banner__expired">TIME EXPIRED — download your receipt now.</div>');
    }
  }

  if (_timerInterval) clearInterval(_timerInterval);
  tick();
  _timerInterval = setInterval(tick, 1000);
}

// ─── Theory assessment ────────────────────────────────────────────────────────

export async function renderTheoryAssessment(container, token, labId, onSuccess) {
  container.innerHTML = '<div class="exam-loading">Loading theory assessment…</div>';

  let questions;
  try {
    questions = await fetchJSON(
      `/api/exam/questions?token=${encodeURIComponent(token)}&lab_id=${encodeURIComponent(labId)}`
    );
  } catch (err) {
    container.innerHTML =
      `<p class="exam-error">Failed to load questions: ${escapeHtml(String(err.message || err))}</p>`;
    return null;
  }

  container.innerHTML = _buildTheoryForm(questions);
  _wireWordCounts(questions);

  document.getElementById('theory-submit-btn')?.addEventListener('click', async () => {
    const btn = document.getElementById('theory-submit-btn');
    const errEl = document.getElementById('theory-error');
    if (errEl) errEl.textContent = '';
    if (btn) { btn.disabled = true; btn.textContent = 'Submitting…'; }

    try {
      const result = await fetchJSON('/api/exam/theory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, answers: _collectAnswers(questions) }),
      });
      _showConfirmation(container, result);
      if (onSuccess) setTimeout(onSuccess, 1200);
    } catch (err) {
      if (btn) { btn.disabled = false; btn.textContent = 'Submit Theory Assessment'; }
      if (errEl) errEl.textContent = String(err.message || 'Submission failed');
    }
  });

  return questions;
}

function _buildTheoryForm(questions) {
  const mcqHtml = (questions.mcq || []).map((q, i) => _buildMcq(q, i + 1)).join('');
  const saHtml  = (questions.short_answers || []).map((q, i) => _buildSa(q, i + 1)).join('');
  const nMcq = (questions.mcq || []).length;
  const nSa  = (questions.short_answers || []).length;
  return `
    <div class="theory-assessment">
      <div class="theory-header">
        <h2 class="theory-title">Theory Assessment</h2>
        <p class="theory-subtitle">
          Part A: ${nMcq} multiple-choice questions · 5 pts each · machine-scored.<br>
          Part B: ${nSa} short-answer questions · 20 pts each · instructor-graded · 100–200 words each.
        </p>
      </div>
      ${mcqHtml ? `<div class="theory-section"><h3 class="theory-section__title">Part A — Multiple Choice</h3>${mcqHtml}</div>` : ''}
      ${saHtml  ? `<div class="theory-section"><h3 class="theory-section__title">Part B — Short Answer</h3>${saHtml}</div>` : ''}
      <div id="theory-error" class="exam-error" style="min-height:1.2em"></div>
      <button id="theory-submit-btn" class="btn-primary">Submit Theory Assessment</button>
    </div>`;
}

function _buildMcq(q, num) {
  const opts = (q.options || []).map(o => `
    <label class="theory-option">
      <input type="radio" name="mcq_${escapeHtml(q.id)}" value="${escapeHtml(o.key)}" />
      <span class="theory-option__key">${escapeHtml(o.key)}.</span>
      <span class="theory-option__text">${escapeHtml(o.text)}</span>
    </label>`).join('');
  return `
    <div class="theory-question" id="tq-${escapeHtml(q.id)}">
      <div class="theory-question__num">Q${num}
        <span class="theory-question__meta">Bloom's L${q.bloom_level} · ${q.points} pts</span>
      </div>
      ${q.scenario ? `<div class="theory-question__scenario">${escapeHtml(q.scenario)}</div>` : ''}
      <div class="theory-question__text">${escapeHtml(q.question)}</div>
      <div class="theory-options">${opts}</div>
    </div>`;
}

function _buildSa(q, num) {
  return `
    <div class="theory-question" id="tq-${escapeHtml(q.id)}">
      <div class="theory-question__num">SA${num}
        <span class="theory-question__meta">Bloom's L${q.bloom_level} · ${q.points} pts · ${escapeHtml(q.word_limit || '100–200 words')}</span>
      </div>
      <div class="theory-question__text">${escapeHtml(q.question)}</div>
      <textarea id="sa_${escapeHtml(q.id)}" class="theory-textarea" rows="8"
        placeholder="Write your response here (100–200 words)…"></textarea>
      <div id="wc_${escapeHtml(q.id)}" class="theory-wordcount">0 words</div>
    </div>`;
}

function _wireWordCounts(questions) {
  for (const q of (questions?.short_answers || [])) {
    const ta = document.getElementById(`sa_${q.id}`);
    const wc = document.getElementById(`wc_${q.id}`);
    if (!ta || !wc) continue;
    ta.addEventListener('input', () => {
      const words = ta.value.trim().split(/\s+/).filter(w => w.length > 0).length;
      wc.textContent = `${words} words`;
      wc.className = `theory-wordcount${
        words >= 100 && words <= 200 ? ' theory-wordcount--ok'
        : words > 0 ? ' theory-wordcount--warn' : ''
      }`;
    });
  }
}

function _collectAnswers(questions) {
  const answers = {};
  for (const q of (questions.mcq || [])) {
    const sel = document.querySelector(`input[name="mcq_${q.id}"]:checked`);
    if (sel) answers[q.id] = sel.value;
  }
  for (const q of (questions.short_answers || [])) {
    const ta = document.getElementById(`sa_${q.id}`);
    if (ta) answers[q.id] = ta.value.trim();
  }
  return answers;
}

function _showConfirmation(container, result) {
  const mcqTotal = result.mcq_scored
    ? Object.values(result.mcq_scored).reduce((s, r) => s + (r.points_earned || 0), 0)
    : null;
  container.innerHTML = `
    <div class="theory-confirmation">
      <div class="theory-confirmation__icon">✓</div>
      <h3>Theory Assessment Submitted</h3>
      ${mcqTotal !== null ? `<p>MCQ auto-score: <strong>${mcqTotal} pts</strong></p>` : ''}
      <p class="theory-confirmation__note">
        Short answers will be reviewed by your instructor.
        Download your signed receipt below to submit to your LMS.
      </p>
    </div>`;
}

// ─── Receipt signing + download ───────────────────────────────────────────────

export async function signAndDownloadReceipt(token, labId) {
  const receipt = await fetchJSON(`/api/exam/receipt?token=${encodeURIComponent(token)}`);

  const keyMaterial = new TextEncoder().encode(token.slice(0, 32).padEnd(32, '0'));
  const dataBytes   = new TextEncoder().encode(JSON.stringify(receipt));

  const cryptoKey = await crypto.subtle.importKey(
    'raw', keyMaterial,
    { name: 'HMAC', hash: 'SHA-256' },
    false, ['sign']
  );
  const sigBuf = await crypto.subtle.sign('HMAC', cryptoKey, dataBytes);
  const sigHex = Array.from(new Uint8Array(sigBuf))
    .map(b => b.toString(16).padStart(2, '0')).join('');

  const signed = { ...receipt, client_hmac_sha256: sigHex };

  const blob = new Blob([JSON.stringify(signed, null, 2)], { type: 'application/json' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = `nexacore_exam_${receipt.student_id || 'student'}_${labId.replace(/[^a-z0-9]/g, '-')}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  return signed;
}
