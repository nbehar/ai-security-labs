/**
 * core.js — Shared framework for all AI Security Lab workshops
 * Provides: DOM helpers, API fetch, tab rendering, info page pattern,
 * leaderboard, level briefing cards.
 */

// =============================================================================
// DOM HELPERS
// =============================================================================

export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

export function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// =============================================================================
// API
// =============================================================================

export async function fetchJSON(url, opts = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 120000);
  try {
    const res = await fetch(url, { ...opts, signal: controller.signal });
    clearTimeout(timeout);
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `HTTP ${res.status}`);
    }
    return res.json();
  } catch (err) {
    clearTimeout(timeout);
    if (err.name === "AbortError") throw new Error("Request timed out. Try again.");
    throw err;
  }
}

// =============================================================================
// TAB RENDERING
// =============================================================================

/**
 * Render horizontal tabs into a container.
 * @param {HTMLElement} container - The tabs nav element
 * @param {Array<{mode: string, label: string}>} tabDefs - Tab definitions
 * @param {string} activeMode - Currently active mode
 * @param {function} onSwitch - Callback when tab is clicked (receives mode string)
 */
export function renderTabs(container, tabDefs, activeMode, onSwitch) {
  container.innerHTML = tabDefs.map((t) =>
    `<button class="tab${t.mode === activeMode ? " tab--active" : ""}" data-mode="${t.mode}">${t.label}</button>`
  ).join("");
  $$(`tab`, container).forEach((btn) => {
    btn.addEventListener("click", () => onSwitch(btn.dataset.mode));
  });
}

// =============================================================================
// LEVEL BRIEFING CARDS
// =============================================================================

/**
 * Render a level briefing card with collapsible suggestion.
 * @param {object} briefing - {title, icon, fields: [{label, value}], tryThis}
 * @param {string} accentColor - CSS color for the left border and suggestion toggle
 */
export function renderLevelBriefing(briefing, accentColor = "var(--blue)") {
  if (!briefing) return "";
  const fieldsHtml = (briefing.fields || [])
    .map((f) => `<strong>${f.label}:</strong> ${f.value}`)
    .join("<br>");

  return `
    <div class="card" style="margin-bottom:16px;border-left:3px solid ${accentColor};">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
        <span style="font-size:20px;">${briefing.icon || "ℹ️"}</span>
        <span class="card__title">${briefing.title}</span>
      </div>
      <div style="font-size:13px;color:var(--text-sec);line-height:1.7;">
        ${fieldsHtml}
      </div>
      ${briefing.tryThis ? `
      <details style="margin-top:10px;">
        <summary style="font-size:12px;color:${accentColor};cursor:pointer;font-weight:500;">Show suggestion</summary>
        <div style="margin-top:8px;padding:10px 14px;background:${accentColor}10;border-radius:var(--radius-sm);font-size:13px;color:var(--text-sec);">
          ${briefing.tryThis}
        </div>
      </details>` : ""}
    </div>`;
}

// =============================================================================
// LEADERBOARD RENDERING
// =============================================================================

/**
 * Render a leaderboard table.
 * @param {HTMLElement} container - Main element to render into
 * @param {string} endpoint - API endpoint (e.g., "/api/leaderboard")
 * @param {Array<{key: string, label: string}>} columns - Score columns to show
 * @param {string} accentColor - Color for the total score
 */
export async function renderLeaderboard(container, endpoint, columns, accentColor = "var(--blue)") {
  container.innerHTML = '<div style="padding:40px;text-align:center;color:var(--text-muted);"><span class="spinner"></span> Loading…</div>';

  try {
    const data = await fetchJSON(endpoint);
    const colHeaders = columns.map((c) => `<th>${c.label}</th>`).join("");
    const rows = data.leaderboard.map((e) => {
      const colCells = columns.map((c) => `<td>${e[c.key] || 0}</td>`).join("");
      return `<tr>
        <td style="font-weight:600;">#${e.rank}</td>
        <td>${escapeHtml(e.name)}</td>
        ${colCells}
        <td style="font-weight:700;color:${accentColor};">${e.total}</td>
      </tr>`;
    }).join("");

    container.innerHTML = `
      <div class="fade-in">
        <h2 style="font-size:18px;font-weight:600;color:var(--text);margin-bottom:16px;">🏆 Leaderboard</h2>
        ${data.leaderboard.length === 0
          ? '<div class="card"><div class="card__text">No scores yet. Be the first!</div></div>'
          : `<table class="scorecard-table">
              <caption class="sr-only">Attack leaderboard — top scores</caption>
              <thead><tr><th>Rank</th><th>Name</th>${colHeaders}<th>Total</th></tr></thead>
              <tbody>${rows}</tbody>
            </table>`}
      </div>`;
  } catch (err) {
    container.innerHTML = `<div class="card"><div class="card__text" style="color:var(--red);">Error: ${escapeHtml(err.message)}</div></div>`;
  }
}

// =============================================================================
// INFO PAGE PATTERN
// =============================================================================

/**
 * Render a standard Info/welcome page with mission, cards, and start button.
 * @param {HTMLElement} container - Main element
 * @param {object} config - {title, cards: [{title, body}], buttonLabel, buttonColor, onStart}
 */
export function renderInfoPage(container, config) {
  const cardsHtml = (config.cards || []).map((card) => `
    <div class="card" style="margin-bottom:16px;">
      <div class="card__header"><span class="card__title">${card.title}</span></div>
      <div class="card__text" style="line-height:1.8;">${card.body}</div>
    </div>
  `).join("");

  container.innerHTML = `
    <div class="fade-in">
      <h1 class="attack-header__title" style="margin-bottom:16px;">${config.title}</h1>
      ${cardsHtml}
      <div style="text-align:center;margin-top:24px;">
        <button class="btn btn--primary" style="max-width:400px;${config.buttonColor ? `background:${config.buttonColor};` : ""}" id="btn-info-start">
          ${config.buttonLabel || "Start"}
        </button>
      </div>
    </div>`;

  $("#btn-info-start")?.addEventListener("click", config.onStart);
}

// =============================================================================
// INSTRUCTOR PREVIEW BANNER
// =============================================================================

/**
 * Render a sticky "INSTRUCTOR PREVIEW" banner at the top of the page.
 * Safe to call multiple times — only inserts once (idempotent).
 */
export function renderPreviewBanner() {
  const existing = document.getElementById('preview-banner');
  if (existing) return;
  const banner = document.createElement('div');
  banner.id = 'preview-banner';
  banner.setAttribute('role', 'status');
  banner.setAttribute('aria-live', 'polite');
  banner.style.cssText = 'position:sticky;top:0;z-index:999;background:var(--color-warning,#b45309);color:#fff;text-align:center;padding:8px 16px;font-size:0.875rem;font-weight:600;';
  banner.textContent = '🔍 INSTRUCTOR PREVIEW — scores are not recorded';
  document.body.prepend(banner);
}

// =============================================================================
// PROGRESS VISUALIZATION
// =============================================================================

/**
 * Render level progress indicators (stars/checkmarks).
 * @param {number} totalLevels
 * @param {object} completedLevels - {1: 95, 2: 80, ...} level -> best score
 * @param {number} currentLevel
 * @param {number} maxUnlocked
 */
export function renderProgress(totalLevels, completedLevels, currentLevel, maxUnlocked) {
  const items = [];
  for (let l = 1; l <= totalLevels; l++) {
    const score = completedLevels[l] || 0;
    const isCurrent = l === currentLevel;
    const isLocked = l > maxUnlocked;
    let icon, color;
    if (score >= 80) { icon = "⭐"; color = "var(--amber)"; }       // star = great
    else if (score >= 60) { icon = "✅"; color = "var(--green)"; }   // check = passed
    else if (score > 0) { icon = "⚠️"; color = "var(--amber)"; } // warning = attempted
    else if (isLocked) { icon = "🔒"; color = "var(--text-muted)"; }
    else { icon = "○"; color = "var(--text-muted)"; }               // empty circle

    const border = isCurrent ? "border-bottom:2px solid var(--blue);" : "";
    items.push(`<span style="display:inline-flex;flex-direction:column;align-items:center;gap:2px;padding:4px 8px;font-size:12px;${border}" title="Level ${l}: ${score > 0 ? score + ' pts' : isLocked ? 'Locked' : 'Not attempted'}"><span style="font-size:16px;">${icon}</span><span style="color:${color};">L${l}</span></span>`);
  }
  return `<div style="display:flex;gap:4px;margin-bottom:12px;justify-content:center;">${items.join("")}</div>`;
}

// =============================================================================
// WHY EXPLANATION COMPONENT
// =============================================================================

/**
 * Render a "Why it worked/failed" explanation card.
 * @param {boolean} success - Whether the attack succeeded
 * @param {string} attackName
 * @param {string} whyText - Educational explanation
 */
export function renderWhyCard(success, attackName, whyText) {
  const color = success ? "var(--red)" : "var(--green)";
  const bgColor = success ? "rgba(239,68,68,0.06)" : "rgba(34,197,94,0.06)";
  const icon = success ? "💡" : "🛡️";
  const label = success ? "Why this got through" : "Why this was blocked";

  return `
    <div style="margin-top:6px;padding:8px 12px;background:${bgColor};border-left:2px solid ${color};border-radius:0 var(--radius-xs) var(--radius-xs) 0;font-size:12px;color:var(--text-sec);line-height:1.5;">
      ${icon} <strong style="color:${color};">${label}:</strong> ${whyText}
    </div>`;
}

// =============================================================================
// GUIDED PRACTICE / WALKTHROUGH
// =============================================================================

/**
 * Render a guided practice walkthrough with numbered steps.
 * @param {Array<{step: string, instruction: string, tip: string}>} steps
 * @param {number} currentStep - 0-based index of current step
 * @param {string} accentColor
 * @param {function} onNext - called with next step index
 * @param {function} onStart - called when "Let's go" is clicked on final step
 */
export function renderGuidedPractice(steps, currentStep, accentColor, onNext, onStart) {
  const step = steps[currentStep];
  const isLast = currentStep === steps.length - 1;
  const progress = steps.map((_, i) =>
    `<span style="display:inline-block;width:24px;height:24px;border-radius:50%;text-align:center;line-height:24px;font-size:12px;font-weight:600;${i === currentStep ? `background:${accentColor};color:#fff;` : i < currentStep ? 'background:var(--green);color:#fff;' : 'background:var(--border);color:var(--text-muted);'}">${i + 1}</span>`
  ).join('<span style="display:inline-block;width:16px;height:1px;background:var(--border);vertical-align:middle;"></span>');

  return `
    <div class="card" style="margin-bottom:16px;border-left:3px solid ${accentColor};">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
        <span style="font-size:18px;">🎓</span>
        <span class="card__title">Guided Practice</span>
        <span style="font-size:12px;color:var(--text-muted);margin-left:auto;">Step ${currentStep + 1} of ${steps.length}</span>
      </div>
      <div style="display:flex;gap:4px;justify-content:center;margin-bottom:16px;">${progress}</div>
      <div style="font-size:15px;font-weight:600;color:var(--text);margin-bottom:8px;">${step.step}</div>
      <div style="font-size:13px;color:var(--text-sec);line-height:1.7;margin-bottom:12px;">${step.instruction}</div>
      ${step.tip ? `<div style="padding:8px 12px;background:${accentColor}10;border-radius:var(--radius-sm);font-size:12px;color:var(--text-sec);margin-bottom:12px;"><strong style="color:${accentColor};">💡 Tip:</strong> ${step.tip}</div>` : ""}
      <div style="display:flex;justify-content:flex-end;">
        ${isLast
          ? `<button class="btn btn--primary" style="max-width:200px;background:${accentColor};" data-action="guided-start">→ Start Challenge</button>`
          : `<button class="btn btn--primary" style="max-width:200px;" data-action="guided-next">Next Step →</button>`}
      </div>
    </div>`;
}

// =============================================================================
// KNOWLEDGE CHECK COMPONENT
// =============================================================================

/**
 * Render a collapsible "Check Your Understanding" self-quiz.
 * Returns an HTML string. After insertion call wireKnowledgeCheck(container).
 * @param {Array<{q: string, options: Array<{label: string, correct?: boolean, explanation: string}>}>} questions
 * @param {string} accentColor
 */
export function renderKnowledgeCheck(questions, accentColor = "var(--blue)") {
  const qs = questions.map((q, qi) => {
    const opts = q.options.map((opt, oi) =>
      `<button class="kc-option" data-qi="${qi}" data-oi="${oi}" data-correct="${opt.correct ? "1" : "0"}"
        data-explanation="${escapeHtml(opt.explanation)}"
        style="display:block;width:100%;text-align:left;margin:3px 0;padding:7px 12px;background:var(--bg);border:1px solid var(--border);border-radius:var(--radius-sm);cursor:pointer;font-size:13px;color:var(--text-sec);">
        ${escapeHtml(opt.label)}
      </button>`
    ).join("");
    return `
      <div class="kc-question" style="margin-bottom:18px;">
        <p style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:6px;">${qi + 1}. ${escapeHtml(q.q)}</p>
        ${opts}
        <div class="kc-feedback" style="display:none;margin-top:6px;padding:8px 12px;border-radius:var(--radius-sm);font-size:12px;line-height:1.5;border-left:3px solid transparent;"></div>
      </div>`;
  }).join("");

  return `
    <details class="kc-block" style="margin-top:20px;border:1px solid var(--border);border-radius:var(--radius-sm);overflow:hidden;">
      <summary style="padding:12px 16px;font-size:13px;font-weight:600;color:${accentColor};cursor:pointer;background:${accentColor}10;list-style:none;display:flex;align-items:center;gap:8px;user-select:none;">
        🎯 Check Your Understanding
        <span style="font-size:11px;color:var(--text-muted);font-weight:400;margin-left:auto;">${questions.length} questions — no grade, just self-check</span>
      </summary>
      <div style="padding:16px 16px 8px;">${qs}</div>
    </details>`;
}

/**
 * Wire click handlers for a rendered knowledge check block.
 * Uses only DOM creation methods — no innerHTML.
 * @param {HTMLElement} container - element containing the rendered kc-block
 */
export function wireKnowledgeCheck(container) {
  container.querySelectorAll(".kc-option").forEach((btn) => {
    btn.addEventListener("click", () => {
      const question = btn.closest(".kc-question");
      if (!question) return;
      const correct = btn.dataset.correct === "1";
      const explanation = btn.dataset.explanation || "";

      question.querySelectorAll(".kc-option").forEach((b) => {
        b.disabled = true;
        b.style.cursor = "default";
        b.style.opacity = b === btn ? "1" : "0.4";
      });

      btn.style.background = correct ? "rgba(34,197,94,0.14)" : "rgba(239,68,68,0.14)";
      btn.style.borderColor = correct ? "var(--green)" : "var(--red)";
      btn.style.color = correct ? "var(--green)" : "var(--red)";
      btn.style.fontWeight = "600";

      const fb = question.querySelector(".kc-feedback");
      if (fb) {
        fb.style.display = "block";
        fb.style.background = correct ? "rgba(34,197,94,0.06)" : "rgba(239,68,68,0.06)";
        fb.style.borderLeftColor = correct ? "var(--green)" : "var(--red)";
        fb.textContent = "";
        const iconSpan = document.createElement("span");
        iconSpan.textContent = correct ? "✅ " : "❌ ";
        const labelStrong = document.createElement("strong");
        labelStrong.style.color = correct ? "var(--green)" : "var(--red)";
        labelStrong.textContent = correct ? "Correct! " : "Not quite. ";
        fb.appendChild(iconSpan);
        fb.appendChild(labelStrong);
        fb.appendChild(document.createTextNode(explanation));
      }
    });
  });
}

// =============================================================================
// PLATFORM GLOSSARY COMPONENT
// =============================================================================

/**
 * Render a collapsible platform-wide glossary panel.
 * Returns an HTML string. Drop after the knowledge check on any Info tab.
 */
export function renderGlossaryPanel() {
  const terms = [
    ["Adversarial Filter", "A defense that scans document or query text for known injection patterns before they reach the model. Effective against overt injection language; blind to semantic (embedding-level) attacks."],
    ["Canary Token (Honeytoken)", "A secret phrase embedded in a system prompt as a tripwire. If the model outputs the phrase, the attack succeeded in crossing the prompt boundary."],
    ["Cosine Similarity", "A 0–1 measure of how close two embedding vectors are in semantic space. Higher = more similar. Used in RAG retrieval to rank candidate documents against a query."],
    ["Corpus Poisoning", "Injecting malicious documents into a RAG knowledge base so the model retrieves and repeats attacker-controlled content in its answers."],
    ["Defense in Depth", "Using multiple independent defense layers so no single bypass compromises the whole system. The core architectural principle behind hardened AI systems."],
    ["Embedding", "A numerical vector representation of text produced by an encoder model. Texts with similar meaning cluster together — which attackers exploit via keyword stuffing (RP.5)."],
    ["F1 Score", "Harmonic mean of precision (low false positives) and recall (low false negatives). A defense with F1 = 1.0 catches every attack without blocking any legitimate query."],
    ["False Negative", "A missed attack: the defense did not fire on genuinely malicious input. High false-negative rate means attackers get through undetected."],
    ["False Positive", "A wrongly blocked query: the defense fired on a legitimate, benign input. High false-positive rate means real users are being disrupted."],
    ["Grounding (Output Grounding)", "A post-generation defense that checks whether the model's response is supported by the retrieved documents. Catches citation spoofing (RP.4)."],
    ["Jailbreaking", "Bypassing an LLM's safety rules via crafted prompts. Unlike system-level exploits, jailbreaks work per-conversation and manipulate language, not code."],
    ["LLM01 / Prompt Injection", "OWASP LLM Top 10 category #1. Covers direct attacks (user-to-model) and indirect attacks (corpus-to-model via retrieved content)."],
    ["OCR Injection", "An attack where malicious instructions hidden in an image's text layer are extracted by OCR and inserted into the model's context — exploiting the vision-text boundary."],
    ["OWASP LLM Top 10", "The Open Worldwide Application Security Project's list of the most critical security risks for LLM applications. Standard reference for enterprise AI risk management."],
    ["Prompt Injection", "Crafting input that makes the model treat attacker text as trusted developer instructions rather than untrusted user data, bypassing the system prompt boundary."],
    ["Provenance Check", "A defense that verifies a document's source URI against a trusted allowlist. Blocks any document not from a pre-approved origin — effective even against semantic attacks that content-based defenses miss."],
    ["RAG (Retrieval-Augmented Generation)", "An LLM architecture where answers are grounded in documents retrieved from a knowledge base at query time. Adds context, but creates a new attack surface: the corpus."],
    ["Retrieval Diversity", "A defense that penalizes retrieval results where multiple documents share the same source URI. Specifically designed to detect multi-document consensus attacks (RP.6)."],
    ["Semantic Attack", "An attack that exploits embedding proximity rather than injection text. The poisoned document looks clean — it only manipulates its vector. Content-based defenses are blind to it."],
    ["System Prompt", "Hidden developer instructions given to the model before any user message. Controls model behavior and persona but is not visible to end users — making it an extraction target."],
    ["Vision-Text Boundary", "The architectural layer where image content is converted to text (via OCR or a vision model) before entering the LLM context. A primary injection surface in multimodal AI systems."],
    ["WAF (Web Application Firewall)", "A rule-based filter that blocks requests matching known attack signatures before they reach the application. LLM input scanners play an analogous role at the prompt layer."],
  ];

  const rows = terms.map(([term, def]) =>
    `<div style="padding:8px 0;border-bottom:1px solid var(--border);display:grid;grid-template-columns:220px 1fr;gap:12px;align-items:baseline;">
      <span style="font-size:13px;font-weight:600;color:var(--text);">${escapeHtml(term)}</span>
      <span style="font-size:12px;color:var(--text-sec);line-height:1.5;">${escapeHtml(def)}</span>
    </div>`
  ).join("");

  return `
    <details class="glossary-panel" style="margin-top:20px;border:1px solid var(--border);border-radius:var(--radius-sm);overflow:hidden;">
      <summary style="padding:12px 16px;font-size:13px;font-weight:600;color:var(--text);cursor:pointer;background:var(--surface);list-style:none;display:flex;align-items:center;gap:8px;user-select:none;">
        📖 Platform Glossary
        <span style="font-size:11px;color:var(--text-muted);font-weight:400;margin-left:auto;">${terms.length} terms</span>
      </summary>
      <div style="padding:4px 16px 16px;">${rows}</div>
    </details>`;
}
