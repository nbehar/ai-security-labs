/**
 * exam_mode.js — Exam layer for AI Security Labs
 *
 * Exports:
 *   detectExamToken, initExamMode, isExamActive, getExamToken,
 *   getExamContext, getExamStatus, getRemainingAttempts, wrapPayload,
 *   refreshStatus, mountExamBanner, renderTheoryTab, renderReceiptTab
 */
import { escapeHtml, fetchJSON } from "./core.js";

// ---------------------------------------------------------------------------
// Module-level singleton
// ---------------------------------------------------------------------------
const _exam = {
  active: false,
  token: null,
  ctx: null,         // ExamContext from /api/exam/validate
  status: null,      // ExamStatus from /api/exam/status
  questions: null,   // { mcq: [...], short_answers: [...] }
  mcqIndex: 0,
  mcqAnswers: {},    // { question_id: "A" }
  shortAnswers: {},  // { question_id: "text..." }
  theorySubmitted: false,
  timerHandle: null,
  remainingSeconds: 0,
};

// ---------------------------------------------------------------------------
// Public read-only accessors
// ---------------------------------------------------------------------------
export function detectExamToken() {
  return new URLSearchParams(window.location.search).get("exam_token");
}
export function isExamActive()             { return _exam.active; }
export function getExamToken()             { return _exam.token; }
export function getExamContext()           { return _exam.ctx; }
export function getExamStatus()            { return _exam.status; }

export function getRemainingAttempts(exerciseId) {
  if (!_exam.status) return null;
  const ex = (_exam.status.exercises || []).find(e => e.exercise_id === exerciseId);
  return ex ? ex.remaining_attempts : null;
}

/** Returns payload with exam_token injected when exam is active. */
export function wrapPayload(payload) {
  return _exam.active ? { ...payload, exam_token: _exam.token } : payload;
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
export async function initExamMode(token, labId) {
  const ctx = await fetchJSON("/api/exam/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  _exam.active = true;
  _exam.token = token;
  _exam.ctx = ctx;
  _exam.remainingSeconds = Math.max(
    0,
    (ctx.time_limit_seconds || 7200) - (ctx.elapsed_seconds || 0)
  );
  _exam.theorySubmitted = !!ctx.theory_submitted;

  // Best-effort: load theory questions (may 404 on labs without them)
  try {
    _exam.questions = await fetchJSON(
      `/api/exam/questions?token=${encodeURIComponent(token)}&lab_id=${encodeURIComponent(labId)}`
    );
  } catch (_) { /* theory questions optional */ }

  await refreshStatus();
  return ctx;
}

// ---------------------------------------------------------------------------
// Status refresh
// ---------------------------------------------------------------------------
export async function refreshStatus() {
  if (!_exam.active) return null;
  try {
    _exam.status = await fetchJSON(
      `/api/exam/status?token=${encodeURIComponent(_exam.token)}`
    );
  } catch (_) {}
  return _exam.status;
}

// ---------------------------------------------------------------------------
// Exam banner (fixed position, countdown timer)
// ---------------------------------------------------------------------------
export function mountExamBanner() {
  if (document.getElementById("exam-banner")) return;
  const div = document.createElement("div");
  div.id = "exam-banner";
  div.style.cssText = [
    "position:fixed", "top:0", "left:0", "right:0", "z-index:9999",
    "background:var(--color-warning,#d97706)", "color:#000",
    "display:flex", "align-items:center", "justify-content:space-between",
    "padding:6px 20px", "font-size:0.85rem", "font-weight:600",
    "box-shadow:0 2px 8px rgba(0,0,0,.4)",
  ].join(";");

  const ctx = _exam.ctx;
  const examLabel = escapeHtml(ctx.exam_id || "Exam");
  const studentLabel = escapeHtml(ctx.student_id || "");
  div.innerHTML = [
    `<span>\u{1F393} EXAM MODE &nbsp;&bull;&nbsp; ${examLabel}`,
    studentLabel ? ` &nbsp;&bull;&nbsp; ${studentLabel}` : "",
    `</span>`,
    `<span>Time remaining: <strong id="exam-timer">--:--:--</strong></span>`,
  ].join("");

  document.body.insertBefore(div, document.body.firstChild);

  // Push content down so banner doesn't overlap
  document.body.style.paddingTop = "36px";

  _startTimer();
}

function _startTimer() {
  clearInterval(_exam.timerHandle);
  _updateTimerDisplay();
  _exam.timerHandle = setInterval(() => {
    if (_exam.remainingSeconds > 0) {
      _exam.remainingSeconds--;
      _updateTimerDisplay();
    } else {
      clearInterval(_exam.timerHandle);
      _onTimeExpired();
    }
  }, 1000);
}

function _updateTimerDisplay() {
  const el = document.getElementById("exam-timer");
  if (!el) return;
  const s = _exam.remainingSeconds;
  const hh = String(Math.floor(s / 3600)).padStart(2, "0");
  const mm = String(Math.floor((s % 3600) / 60)).padStart(2, "0");
  const ss = String(s % 60).padStart(2, "0");
  el.textContent = `${hh}:${mm}:${ss}`;
  if (s < 300) el.style.color = "#dc2626"; // red under 5 min
}

function _onTimeExpired() {
  const el = document.getElementById("exam-timer");
  if (el) { el.textContent = "EXPIRED"; el.style.color = "#dc2626"; }
  // Disable all interactive exam inputs
  document.querySelectorAll(".exam-input, .exam-submit").forEach(el => {
    el.disabled = true;
  });
}

// ---------------------------------------------------------------------------
// Theory tab: MCQ + short answers
// ---------------------------------------------------------------------------
export function renderTheoryTab(container, onComplete) {
  if (_exam.theorySubmitted) {
    _renderTheoryComplete(container);
    return;
  }
  if (!_exam.questions) {
    container.innerHTML = `<p style="color:var(--color-muted)">Theory questions unavailable for this exam.</p>`;
    return;
  }
  _renderMcqQuestion(container, onComplete);
}

function _renderMcqQuestion(container, onComplete) {
  const mcqs = _exam.questions.mcq || [];
  const idx = _exam.mcqIndex;

  if (idx >= mcqs.length) {
    _renderShortAnswers(container, onComplete);
    return;
  }

  const q = mcqs[idx];
  const total = mcqs.length;
  const dots = mcqs.map((_, i) => {
    const answered = _exam.mcqAnswers[mcqs[i].question_id] !== undefined;
    const isCurrent = i === idx;
    const bg = isCurrent ? "var(--color-accent,#7c3aed)"
             : answered  ? "var(--color-success,#16a34a)"
             : "var(--color-surface,#2a2a2e)";
    return `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${bg};margin:0 2px"></span>`;
  }).join("");

  const options = (q.options || []).map(opt => {
    const key = opt.key || opt[0];
    const text = opt.text || (typeof opt === "string" ? opt : String(opt));
    return `<button class="exam-input exam-mcq-opt" data-key="${escapeHtml(key)}"
      style="display:block;width:100%;text-align:left;margin:6px 0;padding:10px 14px;
             border:2px solid var(--color-border,#3a3a3e);border-radius:6px;
             background:var(--color-surface,#1e1e22);color:var(--color-text,#e5e5e5);
             cursor:pointer;font-size:0.95rem">
      <strong>${escapeHtml(key)}.</strong> ${escapeHtml(text)}
    </button>`;
  }).join("");

  container.innerHTML = `
    <div style="max-width:720px;margin:0 auto">
      <div style="margin-bottom:16px">${dots}</div>
      <p style="font-size:0.8rem;color:var(--color-muted)">
        Question ${idx + 1} of ${total} &nbsp;&bull;&nbsp;
        Bloom&rsquo;s Level ${escapeHtml(String(q.bloom_level || ""))} &nbsp;&bull;&nbsp;
        ${escapeHtml(String(q.points || 5))} pts
      </p>
      <div style="background:var(--color-surface,#1e1e22);border:1px solid var(--color-border,#3a3a3e);
                  border-radius:8px;padding:20px;margin-bottom:20px">
        <p style="line-height:1.6;margin:0">${escapeHtml(q.scenario || "")}</p>
      </div>
      <p style="font-weight:600">${escapeHtml(q.question || q.stem || "")}</p>
      <div>${options}</div>
    </div>`;

  container.querySelectorAll(".exam-mcq-opt").forEach(btn => {
    btn.addEventListener("click", () => {
      _exam.mcqAnswers[q.question_id] = btn.dataset.key;
      _exam.mcqIndex++;
      _renderMcqQuestion(container, onComplete);
    });
  });
}

function _renderShortAnswers(container, onComplete) {
  const sas = _exam.questions.short_answers || [];
  if (!sas.length) {
    _submitTheory(container, onComplete);
    return;
  }

  const fields = sas.map(q => `
    <div style="margin-bottom:32px">
      <div style="background:var(--color-surface,#1e1e22);border:1px solid var(--color-border,#3a3a3e);
                  border-radius:8px;padding:16px;margin-bottom:12px">
        <p style="font-size:0.8rem;color:var(--color-muted);margin:0 0 8px">
          Short Answer &bull; ${escapeHtml(String(q.points || 20))} pts (instructor-graded)
        </p>
        <p style="margin:0;line-height:1.6">${escapeHtml(q.question || q.stem || "")}</p>
      </div>
      <textarea id="sa-${escapeHtml(q.question_id)}" class="exam-input"
        rows="7" placeholder="Your answer (100–200 words recommended)"
        data-qid="${escapeHtml(q.question_id)}"
        style="width:100%;box-sizing:border-box;padding:10px;border-radius:6px;
               background:var(--color-surface,#1e1e22);color:var(--color-text,#e5e5e5);
               border:2px solid var(--color-border,#3a3a3e);font-size:0.9rem;
               resize:vertical;line-height:1.5"></textarea>
      <p id="wc-${escapeHtml(q.question_id)}"
         style="font-size:0.75rem;color:var(--color-muted);margin:4px 0 0;text-align:right">
        0 words
      </p>
    </div>`).join("");

  container.innerHTML = `
    <div style="max-width:720px;margin:0 auto">
      <h3 style="margin:0 0 8px">Short Answer Questions</h3>
      <p style="color:var(--color-muted);font-size:0.85rem;margin:0 0 24px">
        Graded by your instructor using a 5-criterion rubric. Aim for 100–200 words each.
      </p>
      ${fields}
      <button id="sa-submit" class="exam-submit"
        style="padding:10px 28px;border-radius:6px;border:none;
               background:var(--color-accent,#7c3aed);color:#fff;
               font-size:1rem;font-weight:600;cursor:pointer">
        Submit Theory Assessment
      </button>
    </div>`;

  // Live word counts
  container.querySelectorAll("textarea[data-qid]").forEach(ta => {
    const wcEl = container.querySelector(`#wc-${ta.dataset.qid}`);
    ta.addEventListener("input", () => {
      const wc = ta.value.trim() ? ta.value.trim().split(/\s+/).length : 0;
      if (wcEl) wcEl.textContent = `${wc} words`;
      _exam.shortAnswers[ta.dataset.qid] = ta.value;
    });
  });

  container.querySelector("#sa-submit").addEventListener("click", () => {
    _submitTheory(container, onComplete);
  });
}

async function _submitTheory(container, onComplete) {
  container.innerHTML = `<p style="color:var(--color-muted)">Submitting&hellip;</p>`;
  try {
    await fetchJSON("/api/exam/theory", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        token: _exam.token,
        mcq_answers: _exam.mcqAnswers,
        short_answers: _exam.shortAnswers,
      }),
    });
    _exam.theorySubmitted = true;
    _renderTheoryComplete(container);
    if (typeof onComplete === "function") onComplete();
  } catch (err) {
    container.innerHTML = `
      <p style="color:var(--color-error,#ef4444)">Submission failed: ${escapeHtml(String(err))}. Please try again.</p>
      <button onclick="location.reload()" style="margin-top:8px;padding:6px 14px;cursor:pointer">Reload</button>`;
  }
}

function _renderTheoryComplete(container) {
  container.innerHTML = `
    <div style="max-width:480px;margin:40px auto;text-align:center">
      <p style="font-size:2rem;margin:0 0 12px">✅</p>
      <h3>Theory Assessment Submitted</h3>
      <p style="color:var(--color-muted)">
        Your MCQ answers have been machine-scored. Short answers will be reviewed by your instructor.
        Download your receipt from the Receipt tab to submit to your instructor.
      </p>
    </div>`;
}

// ---------------------------------------------------------------------------
// Receipt tab: score summary + download
// ---------------------------------------------------------------------------
export async function renderReceiptTab(container) {
  container.innerHTML = `<p style="color:var(--color-muted)">Loading receipt&hellip;</p>`;
  try {
    const receipt = await fetchJSON(
      `/api/exam/receipt?token=${encodeURIComponent(_exam.token)}`
    );
    _renderReceiptUI(container, receipt);
  } catch (err) {
    container.innerHTML = `<p style="color:var(--color-error,#ef4444)">Could not load receipt: ${escapeHtml(String(err))}</p>`;
  }
}

function _renderReceiptUI(container, receipt) {
  const practical = receipt.practical || {};
  const theory = receipt.theory || {};
  const timing = receipt.timing || {};

  const practicalRows = (practical.exercises || []).map(ex => `
    <tr>
      <td style="padding:6px 10px">${escapeHtml(ex.display_name || ex.exercise_id)}</td>
      <td style="padding:6px 10px;text-align:right">${escapeHtml(String(ex.earned_score ?? "—"))}</td>
      <td style="padding:6px 10px;text-align:right">${escapeHtml(String(ex.max_score ?? "—"))}</td>
      <td style="padding:6px 10px;text-align:right">${escapeHtml(String(ex.attempts?.length ?? 0))}</td>
    </tr>`).join("");

  const mcqScore   = theory.mcq_score ?? "—";
  const mcqMax     = theory.mcq_max ?? 50;
  const saMax      = theory.short_answer_max ?? 60;
  const practTotal = practical.total_practical_score ?? "—";
  const practMax   = practical.max_practical_score ?? "—";

  const elapsed = timing.total_elapsed_seconds;
  const elapsedStr = elapsed != null
    ? `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`
    : "—";

  container.innerHTML = `
    <div style="max-width:680px;margin:0 auto">
      <h3 style="margin:0 0 4px">Exam Receipt</h3>
      <p style="color:var(--color-muted);font-size:0.85rem;margin:0 0 24px">
        ${escapeHtml(receipt.exam_id || "")} &nbsp;&bull;&nbsp; ${escapeHtml(receipt.student_id || "")}
        &nbsp;&bull;&nbsp; Time: ${elapsedStr}
      </p>

      <h4 style="margin:0 0 8px">Practical Exercises</h4>
      <table style="width:100%;border-collapse:collapse;font-size:0.9rem;margin-bottom:24px">
        <thead>
          <tr style="background:var(--color-surface,#1e1e22)">
            <th style="padding:8px 10px;text-align:left">Exercise</th>
            <th style="padding:8px 10px;text-align:right">Score</th>
            <th style="padding:8px 10px;text-align:right">Max</th>
            <th style="padding:8px 10px;text-align:right">Attempts</th>
          </tr>
        </thead>
        <tbody>${practicalRows}</tbody>
        <tfoot>
          <tr style="font-weight:600;border-top:2px solid var(--color-border,#3a3a3e)">
            <td style="padding:8px 10px">Total Practical</td>
            <td style="padding:8px 10px;text-align:right">${escapeHtml(String(practTotal))}</td>
            <td style="padding:8px 10px;text-align:right">${escapeHtml(String(practMax))}</td>
            <td></td>
          </tr>
        </tfoot>
      </table>

      <h4 style="margin:0 0 8px">Theory Assessment</h4>
      <table style="width:100%;border-collapse:collapse;font-size:0.9rem;margin-bottom:24px">
        <tbody>
          <tr>
            <td style="padding:6px 10px">MCQ (machine-scored)</td>
            <td style="padding:6px 10px;text-align:right">${escapeHtml(String(mcqScore))}</td>
            <td style="padding:6px 10px;text-align:right">${escapeHtml(String(mcqMax))} max</td>
          </tr>
          <tr>
            <td style="padding:6px 10px">Short Answers (instructor-graded)</td>
            <td style="padding:6px 10px;text-align:right;color:var(--color-muted)">pending</td>
            <td style="padding:6px 10px;text-align:right">${escapeHtml(String(saMax))} max</td>
          </tr>
        </tbody>
      </table>

      <div style="margin-bottom:24px;padding:12px 16px;background:var(--color-surface,#1e1e22);
                  border-radius:8px;border:1px solid var(--color-border,#3a3a3e)">
        <p style="margin:0 0 4px;font-size:0.8rem;color:var(--color-muted)">HMAC integrity</p>
        <p style="margin:0;font-size:0.75rem;font-family:monospace;word-break:break-all">
          ${escapeHtml(receipt.hmac_sha256 || "not yet signed")}
        </p>
      </div>

      <button id="receipt-download" class="exam-submit"
        style="padding:10px 28px;border-radius:6px;border:none;
               background:var(--color-accent,#7c3aed);color:#fff;
               font-size:1rem;font-weight:600;cursor:pointer;margin-right:12px">
        Download Receipt (.json)
      </button>
    </div>`;

  container.querySelector("#receipt-download").addEventListener("click", async () => {
    const btn = container.querySelector("#receipt-download");
    btn.disabled = true;
    btn.textContent = "Signing…";
    try {
      const signed = await _signReceipt(receipt);
      _downloadJson(
        signed,
        `nexacore_exam_${(receipt.student_id || "student").replace(/[^a-z0-9]/gi, "_")}_${(receipt.exam_id || "exam").replace(/[^a-z0-9]/gi, "_")}.json`
      );
      btn.textContent = "Downloaded";
    } catch (e) {
      btn.textContent = "Download Receipt (.json)";
      btn.disabled = false;
      alert("Signing failed: " + e.message);
    }
  });
}

// ---------------------------------------------------------------------------
// WebCrypto signing (client-side integrity layer)
// ---------------------------------------------------------------------------
async function _signReceipt(receipt) {
  const keyMaterial = (_exam.token || "").slice(0, 32).padEnd(32, "0");
  const keyBytes = new TextEncoder().encode(keyMaterial);
  const cryptoKey = await crypto.subtle.importKey(
    "raw", keyBytes, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const canonical = _canonicalJSON(receipt);
  const msgBytes = new TextEncoder().encode(canonical);
  const sigBuffer = await crypto.subtle.sign("HMAC", cryptoKey, msgBytes);
  const sigHex = Array.from(new Uint8Array(sigBuffer))
    .map(b => b.toString(16).padStart(2, "0")).join("");

  return { ...receipt, client_hmac_sha256: sigHex };
}

/** Recursively serializes an object with sorted keys (matches Python sort_keys=True). */
function _canonicalJSON(val) {
  if (val === null || typeof val !== "object") return JSON.stringify(val);
  if (Array.isArray(val)) return "[" + val.map(_canonicalJSON).join(",") + "]";
  const sorted = Object.keys(val).sort().map(k =>
    JSON.stringify(k) + ":" + _canonicalJSON(val[k])
  );
  return "{" + sorted.join(",") + "}";
}

function _downloadJson(obj, filename) {
  const blob = new Blob([JSON.stringify(obj, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
