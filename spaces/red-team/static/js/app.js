/**
 * Red Team Workshop — Main App Logic
 * Attack-focused: participants write prompts to extract secrets from hardened LLMs.
 */

const state = {
  mode: "info",
  level: 1,
  running: false,
  lastResult: null,
  participantName: "Anonymous",
  jailbreaks: [],
  selectedJB: null,
  jbResult: null,
};

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function fetchJSON(url, opts = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 120000);
  try {
    const res = await fetch(url, { ...opts, signal: controller.signal });
    clearTimeout(timeout);
    if (!res.ok) { const b = await res.json().catch(() => ({})); throw new Error(b.detail || `HTTP ${res.status}`); }
    return res.json();
  } catch (err) { clearTimeout(timeout); throw err; }
}

// =============================================================================
// TABS
// =============================================================================

function renderTabs() {
  const tabs = [
    { mode: "info", label: "Info" },
    { mode: "redteam", label: "Red Team Levels" },
    { mode: "jailbreak", label: "Jailbreak Lab" },
    { mode: "leaderboard", label: "Leaderboard" },
  ];
  $("#tabs-nav").innerHTML = tabs.map((t) =>
    `<button class="tab${t.mode === state.mode ? " tab--active" : ""}" data-mode="${t.mode}">${t.label}</button>`
  ).join("");
  $$(".tab").forEach((btn) => {
    btn.addEventListener("click", () => { state.mode = btn.dataset.mode; renderTabs(); renderMain(); });
  });
}

function renderMain() {
  const main = $("#main");
  switch (state.mode) {
    case "info": renderInfo(main); break;
    case "redteam": renderRedTeam(main); break;
    case "jailbreak": renderJailbreak(main); break;
    case "leaderboard": renderLeaderboard(main); break;
  }
}

// =============================================================================
// INFO TAB
// =============================================================================

function renderInfo(main) {
  main.innerHTML = `
    <div class="fade-in">
      <h1 class="attack-header__title" style="margin-bottom:16px;">Welcome to the Red Team Workshop</h1>

      <div class="card" style="margin-bottom:16px;">
        <div class="card__header"><span class="card__title">Your Mission</span></div>
        <div class="card__text" style="line-height:1.8;">
          NexaCore has deployed <strong>5 AI systems</strong> with progressively stronger defenses. Each system has a <strong>secret codename</strong> hidden in its configuration. Your job: <strong>extract every secret</strong> using prompt injection, social engineering, and creative attack techniques.
        </div>
      </div>

      <div class="card" style="margin-bottom:16px;">
        <div class="card__header"><span class="card__title">Red Team Levels</span></div>
        <div class="card__text" style="line-height:1.8;">
          <strong>Level 1:</strong> No defenses \u2014 warmup<br>
          <strong>Level 2:</strong> Basic refusal rules<br>
          <strong>Level 3:</strong> XML boundary tags + prompt hardening<br>
          <strong>Level 4:</strong> Hardening + input keyword scanning<br>
          <strong>Level 5:</strong> Maximum security \u2014 everything blocked<br><br>
          <strong>Scoring:</strong> First-try extraction = 100 pts. Each extra attempt costs 20 pts. 0 pts after 5 attempts.
        </div>
      </div>

      <div class="card" style="margin-bottom:16px;">
        <div class="card__header"><span class="card__title">Jailbreak Lab</span></div>
        <div class="card__text" style="line-height:1.8;">
          15 pre-loaded jailbreak techniques across 5 categories: Direct Override, Encoding, Role-Play, Social Engineering, and Advanced. Select a technique, customize the payload, and see if it works against a hardened target.
        </div>
      </div>

      <div style="text-align:center;margin-top:24px;">
        <button class="btn btn--primary" style="max-width:400px;background:var(--red);" id="btn-start">
          \u2694\ufe0f Start Attacking
        </button>
      </div>
    </div>`;

  $("#btn-start")?.addEventListener("click", () => {
    state.mode = "redteam";
    renderTabs();
    renderMain();
  });
}

// =============================================================================
// RED TEAM LEVELS
// =============================================================================

function renderRedTeam(main) {
  const lvl = state.level;
  const levelNames = { 1: "No Defenses (HR)", 2: "Basic Refusal (Finance)", 3: "Prompt Hardening (Legal)", 4: "Hardening + Scanning (DevOps)", 5: "Maximum Security (Executive)" };

  const levelBtns = [1, 2, 3, 4, 5].map((l) =>
    `<button class="tab${l === lvl ? " tab--active" : ""}" data-level="${l}">Level ${l}</button>`
  ).join("");

  const r = state.lastResult;

  main.innerHTML = `
    <div class="fade-in">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
        <h2 style="font-size:18px;font-weight:600;color:var(--text);margin:0;">Red Team Challenge</h2>
        <span style="font-size:13px;color:var(--text-muted);">Level ${lvl}: ${levelNames[lvl]}</span>
      </div>
      <div style="display:flex;gap:4px;margin-bottom:16px;flex-wrap:wrap;">${levelBtns}</div>

      <div class="form-group">
        <label for="rt-name">Your name</label>
        <input type="text" id="rt-name" value="${escapeHtml(state.participantName)}" style="max-width:300px;" />
      </div>

      <div class="form-group">
        <label for="rt-prompt">Your Attack Prompt</label>
        <div style="font-size:12px;color:var(--text-muted);margin-bottom:6px;">Write a prompt that makes the model reveal its secret codename. Be creative!</div>
        <textarea id="rt-prompt" rows="5" placeholder="Try to extract the secret..."></textarea>
      </div>

      <button class="btn btn--primary" id="btn-attack" style="background:var(--red);" ${state.running ? "disabled" : ""}>
        ${state.running ? '<span class="spinner"></span> Attacking\u2026' : '\u2694\ufe0f Launch Attack (Level ' + lvl + ')'}
      </button>

      <div id="rt-results" style="margin-top:20px;">
        ${r && r.level === lvl ? renderRedTeamResult(r) : ""}
      </div>
    </div>`;

  $$("[data-level]").forEach((btn) => {
    btn.addEventListener("click", () => { state.level = parseInt(btn.dataset.level); state.lastResult = null; renderRedTeam(main); });
  });

  $("#btn-attack")?.addEventListener("click", async () => {
    if (state.running) return;
    const prompt = $("#rt-prompt").value;
    const name = $("#rt-name").value || "Anonymous";
    if (!prompt.trim()) return;
    state.participantName = name;
    state.running = true;
    renderRedTeam(main);

    try {
      const result = await fetchJSON("/api/attempt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ level: state.level, attack_prompt: prompt, participant_name: name }),
      });
      state.lastResult = result;
    } catch (err) { alert(err.message); }
    finally { state.running = false; renderRedTeam(main); }
  });
}

function renderRedTeamResult(r) {
  const icon = r.success ? "\ud83c\udf89" : "\ud83d\udeab";
  const color = r.success ? "var(--green)" : "var(--red)";
  const label = r.success ? "SECRET EXTRACTED!" : "BLOCKED";

  return `
    <div class="card fade-in" style="margin-bottom:16px;">
      <div style="font-size:20px;font-weight:700;color:${color};margin-bottom:8px;">${icon} ${label}</div>
      ${r.success ? `<div style="font-size:14px;color:var(--green);margin-bottom:8px;">Secret: <code style="background:rgba(34,197,94,0.15);padding:2px 8px;border-radius:4px;">${escapeHtml(r.secret_found)}</code> \u2014 ${r.score} points (attempt #${r.attempt})</div>` : ""}
      ${r.already_solved ? `<div style="color:var(--text-muted);font-size:13px;">Already solved! Score: ${r.score}</div>` : ""}
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:8px;">Attempt ${r.attempt}/5</div>
      <div class="code-block__label">Model Response</div>
      <div class="model-output" style="max-height:200px;overflow-y:auto;">${escapeHtml(r.model_output || "")}</div>
      ${r.hint ? `<div style="margin-top:12px;padding:10px 14px;background:rgba(245,158,11,0.08);border-left:3px solid var(--amber);border-radius:0 4px 4px 0;font-size:13px;color:var(--text-sec);"><strong style="color:var(--amber);">Hint:</strong> ${escapeHtml(r.hint)}</div>` : ""}
    </div>`;
}

// =============================================================================
// JAILBREAK LAB
// =============================================================================

async function renderJailbreak(main) {
  if (state.jailbreaks.length === 0) {
    try {
      const data = await fetchJSON("/api/jailbreaks");
      state.jailbreaks = data.techniques;
    } catch (err) { console.error(err); }
  }

  const categories = [...new Set(state.jailbreaks.map((j) => j.category))];
  const selected = state.selectedJB ? state.jailbreaks.find((j) => j.id === state.selectedJB) : null;

  main.innerHTML = `
    <div class="fade-in">
      <h2 style="font-size:18px;font-weight:600;color:var(--text);margin-bottom:12px;">Jailbreak Lab</h2>
      <p style="font-size:13px;color:var(--text-sec);margin-bottom:16px;">Select a technique, customize the payload, and test it against a hardened NexaCore assistant. The target has 3 secrets — can you extract them?</p>

      <div class="form-group">
        <label>Select a technique</label>
        <select class="attack-select" id="jb-select">
          <option value="">Choose a jailbreak technique\u2026</option>
          ${categories.map((cat) => `
            <optgroup label="${escapeHtml(cat)}">
              ${state.jailbreaks.filter((j) => j.category === cat).map((j) =>
                `<option value="${j.id}" ${j.id === state.selectedJB ? "selected" : ""}>${escapeHtml(j.name)}</option>`
              ).join("")}
            </optgroup>
          `).join("")}
        </select>
      </div>

      ${selected ? `
        <div class="form-group">
          <label for="jb-prompt">Payload (editable)</label>
          <textarea id="jb-prompt" rows="6">${escapeHtml(selected.template)}</textarea>
        </div>

        <div class="form-group">
          <label for="jb-name">Your name</label>
          <input type="text" id="jb-name" value="${escapeHtml(state.participantName)}" style="max-width:300px;" />
        </div>

        <button class="btn btn--primary" id="btn-jb" style="background:var(--red);" ${state.running ? "disabled" : ""}>
          ${state.running ? '<span class="spinner"></span> Testing\u2026' : '\ud83d\udca5 Test Technique'}
        </button>
      ` : ""}

      <div id="jb-results" style="margin-top:20px;">
        ${state.jbResult ? renderJBResult(state.jbResult) : ""}
      </div>
    </div>`;

  $("#jb-select")?.addEventListener("change", (e) => {
    state.selectedJB = e.target.value || null;
    state.jbResult = null;
    renderJailbreak(main);
  });

  $("#btn-jb")?.addEventListener("click", async () => {
    if (state.running || !state.selectedJB) return;
    const prompt = $("#jb-prompt").value;
    const name = $("#jb-name").value || "Anonymous";
    state.participantName = name;
    state.running = true;
    renderJailbreak(main);

    try {
      const result = await fetchJSON("/api/jailbreak-test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ technique_id: state.selectedJB, custom_prompt: prompt, participant_name: name }),
      });
      state.jbResult = result;
    } catch (err) { alert(err.message); }
    finally { state.running = false; renderJailbreak(main); }
  });
}

function renderJBResult(r) {
  const icon = r.success ? "\ud83d\udca5" : "\ud83d\udee1\ufe0f";
  const color = r.success ? "var(--red)" : "var(--green)";
  const label = r.success ? "JAILBREAK SUCCEEDED" : "JAILBREAK BLOCKED";

  return `
    <div class="card fade-in">
      <div style="font-size:18px;font-weight:700;color:${color};margin-bottom:8px;">${icon} ${label}</div>
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">${escapeHtml(r.technique_name)} (${escapeHtml(r.category)})</div>
      ${r.secrets_found.length > 0 ? `<div style="margin-bottom:8px;">${r.secrets_found.map((s) => `<code style="background:rgba(239,68,68,0.15);color:var(--red);padding:2px 8px;border-radius:4px;margin-right:6px;">${escapeHtml(s)}</code>`).join("")}</div>` : ""}
      <div class="code-block__label">Model Response</div>
      <div class="model-output" style="max-height:200px;overflow-y:auto;">${escapeHtml(r.model_output)}</div>
    </div>`;
}

// =============================================================================
// LEADERBOARD
// =============================================================================

async function renderLeaderboard(main) {
  main.innerHTML = '<div style="padding:40px;text-align:center;color:var(--text-muted);"><span class="spinner"></span> Loading\u2026</div>';
  try {
    const data = await fetchJSON("/api/leaderboard");
    const rows = data.leaderboard.map((e) => `
      <tr>
        <td style="font-weight:600;">#${e.rank}</td>
        <td>${escapeHtml(e.name)}</td>
        <td>${e.red_team}</td>
        <td>${e.jailbreak}</td>
        <td>${e.social_eng}</td>
        <td style="font-weight:700;color:var(--red);">${e.total}</td>
      </tr>`).join("");

    main.innerHTML = `
      <div class="fade-in">
        <h2 style="font-size:18px;font-weight:600;color:var(--text);margin-bottom:16px;">\ud83c\udfc6 Leaderboard</h2>
        ${data.leaderboard.length === 0 ? '<div class="card"><div class="card__text">No scores yet. Be the first to attack!</div></div>' : `
        <table class="scorecard-table">
          <thead><tr><th>Rank</th><th>Name</th><th>Red Team</th><th>Jailbreak</th><th>Social Eng</th><th>Total</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>`}
      </div>`;
  } catch (err) {
    main.innerHTML = `<div class="card"><div class="card__text" style="color:var(--red);">Error: ${escapeHtml(err.message)}</div></div>`;
  }
}

// =============================================================================
// INIT
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {
  renderTabs();
  renderMain();
});
