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
  $$(`.tab`, container).forEach((btn) => {
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
        <span style="font-size:20px;">${briefing.icon || "\u2139\ufe0f"}</span>
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
  container.innerHTML = '<div style="padding:40px;text-align:center;color:var(--text-muted);"><span class="spinner"></span> Loading\u2026</div>';

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
        <h2 style="font-size:18px;font-weight:600;color:var(--text);margin-bottom:16px;">\ud83c\udfc6 Leaderboard</h2>
        ${data.leaderboard.length === 0
          ? '<div class="card"><div class="card__text">No scores yet. Be the first!</div></div>'
          : `<table class="scorecard-table">
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
    if (score >= 80) { icon = "\u2b50"; color = "var(--amber)"; }       // star = great
    else if (score >= 60) { icon = "\u2705"; color = "var(--green)"; }   // check = passed
    else if (score > 0) { icon = "\u26a0\ufe0f"; color = "var(--amber)"; } // warning = attempted
    else if (isLocked) { icon = "\ud83d\udd12"; color = "var(--text-muted)"; }
    else { icon = "\u25cb"; color = "var(--text-muted)"; }               // empty circle

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
  const icon = success ? "\ud83d\udca1" : "\ud83d\udee1\ufe0f";
  const label = success ? "Why this got through" : "Why this was blocked";

  return `
    <div style="margin-top:6px;padding:8px 12px;background:${bgColor};border-left:2px solid ${color};border-radius:0 var(--radius-xs) var(--radius-xs) 0;font-size:12px;color:var(--text-sec);line-height:1.5;">
      ${icon} <strong style="color:${color};">${label}:</strong> ${whyText}
    </div>`;
}
