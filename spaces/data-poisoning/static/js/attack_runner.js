/**
 * attack_runner.js — Renders the RAG Poisoning tab.
 *
 * Composition per frontend_spec.md:
 *   1. Per-student score banner (running total, 6 stars)
 *   2. Level briefing card (collapsible "What to try" suggestion)
 *   3. Participant name input
 *   4. Attack picker (6 RP attacks, difficulty stars)
 *   5. Doc preview side-by-side (poisoned doc vs expected legit doc)
 *   6. Defense toggles (4 checkboxes, ?-tooltip)
 *   7. Run button + spinner + status line
 *   8. Result panels: Cause / Effect / Impact
 *   9. Why-this-works card
 *
 * XSS posture: all interpolated values escaped via escapeHtml.
 */

import { fetchJSON, escapeHtml } from "/static/js/core.js";
import { setHtml } from "/static/js/app.js";
import { renderDocUploadPanel } from "/static/js/document_upload.js";

const DEFENSE_LABELS = {
  provenance_check:    { name: "Provenance Check",      help: "Allowlist-based: blocks any doc whose source is outside trusted-policies/." },
  adversarial_filter:  { name: "Adversarial Filter",    help: "Regex scan for overt injection patterns (ATTENTION ALL, AS APPROVED BY, etc.)." },
  retrieval_diversity: { name: "Retrieval Diversity",   help: "Blocks retrieval if any single source contributes >1 doc to the top-k (catches RP.6)." },
  output_grounding:    { name: "Output Grounding",      help: "Post-LLM check: rejects response if it cites doc IDs not in the corpus (catches RP.4)." },
};

export function renderRagPoisoningTab(container, state) {
  const attacks = state.attacks || [];
  if (attacks.length === 0) {
    setHtml(container, `<div class="card"><div class="card-body muted">No attacks loaded.</div></div>`);
    return;
  }

  const localState = {
    selectedAttackId: attacks[0].id,
    defenses: new Set(),
    mode: "canned",
    uploadedFile: null,
    uploadedContent: null,
    running: false,
    lastResult: null,
    attempts: {},
    corpusCache: {},
  };

  // Pre-select a defense if navigated from the Defenses tab
  const preselectDefense = sessionStorage.getItem("data-poisoning:preselect-defense");
  if (preselectDefense) {
    localState.defenses.add(preselectDefense);
    sessionStorage.removeItem("data-poisoning:preselect-defense");
  }

  const attackOptions = attacks.map((a) =>
    `<option value="${escapeHtml(a.id)}">${escapeHtml(a.id)} — ${escapeHtml(a.name)} ${"★".repeat(a.difficulty || 1)}</option>`
  ).join("");

  const defenseRow = Object.entries(DEFENSE_LABELS).map(([id, { name, help }]) => `
    <label class="defense-toggle">
      <input type="checkbox" data-defense="${escapeHtml(id)}"${localState.defenses.has(id) ? " checked" : ""}>
      <span>${escapeHtml(name)}</span>
      <span class="help" title="${escapeHtml(help)}" aria-label="${escapeHtml(help)}">?</span>
    </label>
  `).join("");

  setHtml(container, `
    <section class="score-banner" id="score-banner">
      <div>
        <div class="score-label">Your RP score</div>
        <div class="score-value" id="score-value">0</div>
      </div>
      <div class="score-stars" id="score-stars" aria-label="Attempts completed"></div>
      <div class="score-detail muted">100 first try · −20 per retry · floor 20 · +50 if a defense blocks</div>
    </section>

    <section class="card card-accent">
      <div class="card-eyebrow">RAG Poisoning — Level Briefing</div>
      <div class="card-body">
        <p>RAG corpus poisoning is the supply-chain attack of the LLM era. The attacker doesn't touch the model — they corrupt the source the model trusts.</p>
        <p class="muted" style="font-size:var(--text-sm);">Traditional analogy: inject a malicious package into npm and every downstream app that installs it runs attacker-controlled code. Same shape: corrupt the upstream, let the system pull it in.</p>
        <p class="muted" style="font-size:var(--text-sm);">Deployed: LLaMA 3.3 70B via Groq · MiniLM-L6 embeddings · in-memory cosine retrieval · top-3. No defenses on by default.</p>
        <details>
          <summary style="cursor:pointer;color:var(--color-accent-aisl-highlight);font-size:var(--text-sm);font-family:var(--font-mono);">What to try</summary>
          <p style="margin-top:var(--space-2);font-size:var(--text-sm);">Run RP.1 (Direct Injection) with no defenses. Observe how a single poisoned doc shows up in the top-k retrieval results and the LLM emits the canary phrase. Then turn on Provenance Check and run again — watch it block at ingestion before any retrieval or LLM call.</p>
        </details>
      </div>
    </section>

    <section class="card">
      <div class="participant-row">
        <label class="participant-label" for="participant-input">Your name (for scoring):</label>
        <input type="text" id="participant-input" class="participant-input"
          value="${escapeHtml(state.participantName)}" maxlength="64"
          placeholder="Anonymous" aria-label="Participant name">
      </div>

      <h2 class="card-title">Pick an attack</h2>
      <div class="attack-select-row">
        <select id="attack-select" class="btn btn-secondary" style="flex:1;min-width:280px;" aria-label="Select an attack">
          ${attackOptions}
        </select>
      </div>

      <div id="attack-description" class="muted" style="font-size:var(--text-sm);margin-bottom:var(--space-3);"></div>

      <div id="doc-previews" class="run-preview-row"></div>

      <div style="margin-bottom:var(--space-3);">
        <label style="display:inline-flex;align-items:center;gap:var(--space-2);font-size:var(--text-sm);cursor:pointer;">
          <input type="radio" name="doc-mode" value="canned" checked> Use pre-canned poisoned document
        </label>
        &nbsp;&nbsp;
        <label style="display:inline-flex;align-items:center;gap:var(--space-2);font-size:var(--text-sm);cursor:pointer;">
          <input type="radio" name="doc-mode" value="uploaded"> Upload my own document
        </label>
      </div>

      <div id="upload-panel-host" class="hidden"></div>
    </section>

    <section class="run-panel">
      <h2 class="card-title">Run</h2>
      <div class="defense-toggles" role="group" aria-label="Defenses">
        ${defenseRow}
      </div>
      <div class="run-actions">
        <button class="btn btn-primary" id="btn-run" type="button">Run Attack</button>
        <span class="status-line" id="status-line"></span>
      </div>
    </section>

    <div id="results"></div>
    <div id="reflection-card" style="display:none;margin-top:var(--space-4);"></div>
  `);

  // Wire up elements
  const attackSelect  = container.querySelector("#attack-select");
  const descEl        = container.querySelector("#attack-description");
  const docPreviewsEl = container.querySelector("#doc-previews");
  const uploadHost    = container.querySelector("#upload-panel-host");
  const runBtn        = container.querySelector("#btn-run");
  const statusLine    = container.querySelector("#status-line");
  const resultsEl     = container.querySelector("#results");
  const participantInput = container.querySelector("#participant-input");

  function showStatus(html) { setHtml(statusLine, html); }
  function clearStatus()    { setHtml(statusLine, ""); }

  participantInput.addEventListener("input", () => {
    const v = participantInput.value.trim() || "Anonymous";
    state.participantName = v;
    localStorage.setItem("data-poisoning:participant", v);
  });

  async function refreshAttackView() {
    const attackId = localState.selectedAttackId;
    const atk = (state.attacks || []).find((a) => a.id === attackId);
    if (!atk) return;

    descEl.textContent = atk.description || "";

    // Load both docs in parallel
    const [poisonedDoc, legitDoc] = await Promise.all([
      fetchDocCached(localState, atk.poisoned_doc_id),
      fetchDocCached(localState, atk.expected_legit_doc_id),
    ]);

    const makePreview = (doc, kind, label) => {
      if (!doc) return `<div class="doc-preview doc-preview-${kind}"><div class="doc-preview-label">${escapeHtml(label)}</div><span class="muted">Loading…</span></div>`;
      const preview = (doc.body_markdown || "").substring(0, 600);
      return `
        <div class="doc-preview doc-preview-${kind}" aria-label="${escapeHtml(label)}: ${escapeHtml(doc.title || doc.id)}">
          <div class="doc-preview-label">${escapeHtml(label)}</div>
          <div style="font-weight:var(--font-semibold);font-size:var(--text-xs);color:var(--color-text-primary);margin-bottom:var(--space-1);">${escapeHtml(doc.title || doc.id)}</div>
          <pre style="margin:0;font-size:11px;max-height:160px;overflow-y:auto;">${escapeHtml(preview)}${(doc.body_markdown || "").length > 600 ? "…" : ""}</pre>
        </div>
      `;
    };

    setHtml(docPreviewsEl, makePreview(poisonedDoc, "attack", "Poisoned doc") + makePreview(legitDoc, "legit", "Expected legit doc"));
  }

  async function fetchDocCached(ls, docId) {
    if (ls.corpusCache[docId]) return ls.corpusCache[docId];
    try {
      const d = await fetchJSON(`/api/corpus/${encodeURIComponent(docId)}`);
      ls.corpusCache[docId] = d;
      return d;
    } catch { return null; }
  }

  attackSelect.addEventListener("change", () => {
    localState.selectedAttackId = attackSelect.value;
    refreshAttackView();
  });

  for (const radio of container.querySelectorAll("input[name='doc-mode']")) {
    radio.addEventListener("change", () => {
      localState.mode = radio.value;
      if (radio.value === "uploaded") {
        uploadHost.classList.remove("hidden");
        renderDocUploadPanel(uploadHost, {
          onSelect: (content, file) => {
            localState.uploadedContent = content;
            localState.uploadedFile = file;
          },
          onError: (msg) => { showStatus(escapeHtml(msg)); },
        });
      } else {
        uploadHost.classList.add("hidden");
        localState.uploadedFile = null;
        localState.uploadedContent = null;
      }
    });
  }

  for (const cb of container.querySelectorAll(".defense-toggle input")) {
    cb.addEventListener("change", () => {
      const id = cb.dataset.defense;
      if (cb.checked) localState.defenses.add(id);
      else localState.defenses.delete(id);
    });
  }

  runBtn.addEventListener("click", async () => {
    if (localState.running) return;
    if (localState.mode === "uploaded" && !localState.uploadedFile) {
      showStatus("Choose a file to upload first.");
      return;
    }

    const atk = (state.attacks || []).find((a) => a.id === localState.selectedAttackId);
    if (!atk) return;

    state.participantName = (participantInput.value.trim() || "Anonymous");
    localState.running = true;
    runBtn.setAttribute("disabled", "true");
    showStatus(`<span class="spinner"></span> Composing answer… (1–3s on Groq LLaMA)`);
    setHtml(resultsEl, "");

    try {
      const result = await runAttack(localState, atk, state.participantName);
      const atkId = result.attack_id;
      localState.lastResult = result;
      localState.attempts[atkId] = (localState.attempts[atkId] || 0) + 1;
      renderResult(resultsEl, result, atk);
      await postScore(state, localState, result, container);
      clearStatus();
    } catch (e) {
      const detail = e && e.message ? e.message : String(e);
      const friendly = /timed out/i.test(detail)
        ? "Groq call timed out. Try again — the platform may be rate-limited or briefly unavailable."
        : /rate.?limit|429/i.test(detail)
          ? "Rate limit hit (10/min). Wait a moment and try again."
          : `Attack failed: ${detail}`;
      setHtml(resultsEl, `<div class="banner banner-danger">${escapeHtml(friendly)}</div>`);
      clearStatus();
    } finally {
      localState.running = false;
      runBtn.removeAttribute("disabled");
    }
  });

  // Initial render
  refreshAttackView();
  updateScoreBanner(container, state, localState);
}

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------

async function runAttack(localState, atk, participantName) {
  const fd = new FormData();
  fd.append("participant_name", participantName);
  fd.append("defenses", JSON.stringify([...localState.defenses]));

  if (localState.mode === "uploaded") {
    fd.append("attack_id", "custom");
    fd.append("doc_source", "uploaded");
    fd.append("target_query_id", atk.target_query_id);
    fd.append("doc_file", localState.uploadedFile);
  } else {
    fd.append("attack_id", localState.selectedAttackId);
    fd.append("doc_source", "canned");
  }

  return fetchJSON("/api/attack", { method: "POST", body: fd });
}

async function postScore(state, localState, result, root) {
  try {
    const body = {
      participant_name: state.participantName,
      attack_id: result.attack_id,
      succeeded: result.succeeded,
      defenses_applied: result.defenses_applied || [],
      attempts: localState.attempts[result.attack_id] || 1,
    };
    const scored = await fetchJSON("/api/score", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    state.scoreByAttack[result.attack_id] = scored;
    updateScoreBanner(root, state, localState);
  } catch {
    // Non-fatal
  }
}

function updateScoreBanner(root, state, localState) {
  const valueEl = root.querySelector("#score-value");
  const starsEl = root.querySelector("#score-stars");
  if (!valueEl) return;

  let total = 0;
  let completed = 0;
  for (const [, entry] of Object.entries(state.scoreByAttack)) {
    total += entry.score_added || 0;
    completed += 1;
  }
  valueEl.textContent = String(total);

  const totalAttacks = 6;
  const stars = Array.from({ length: totalAttacks }, (_, i) =>
    `<span class="${i < completed ? "star-on" : "star-off"}" aria-hidden="true">★</span>`
  ).join("");
  setHtml(starsEl, stars);

  if (completed >= totalAttacks) {
    const reflectionEl = root.querySelector("#reflection-card");
    if (reflectionEl && !reflectionEl.dataset.shown) {
      reflectionEl.dataset.shown = "1";
      reflectionEl.style.display = "block";
      setHtml(reflectionEl, `
        <div style="padding:14px 18px;background:var(--color-accent-aisl-subtle);border-left:3px solid var(--color-accent-aisl-highlight);border-radius:0 var(--radius-sm) var(--radius-sm) 0;">
          <div style="font-size:13px;font-weight:700;color:var(--color-accent-aisl-highlight);margin-bottom:6px;">Reflect</div>
          <p style="font-size:13px;color:var(--color-text-secondary);margin:0 0 6px;">If you were building a RAG-based HR assistant at a real company, which single defense would you deploy first?</p>
          <p style="font-size:11px;color:var(--color-text-muted);margin:0;">No answer needed — just think about it. If you want to go deeper, try running each attack with only one defense enabled and compare which one catches the most.</p>
        </div>
      `);
    }
  }
}

// ---------------------------------------------------------------------------
// Result panels — Cause / Effect / Impact + Why-card
// ---------------------------------------------------------------------------

function renderResult(host, r, atk) {
  const blockedBy  = r.blocked_by;
  const succeeded  = r.succeeded;
  const canary     = r.canary || "";
  const responseHtml = canary
    ? highlightCanary(r.model_response || "", canary)
    : escapeHtml(r.model_response || "");

  const retrieval = (r.retrieval && r.retrieval.results) || [];
  const retrievalList = retrieval.map((item, i) => `
    <li>
      <span class="retrieval-rank">#${i + 1}</span>
      <span class="retrieval-kind-${escapeHtml(item.kind)}">[${escapeHtml(item.kind)}]</span>
      <span>${escapeHtml(item.doc_id)}</span>
      <span class="retrieval-score">${Number(item.score).toFixed(3)}</span>
    </li>
  `).join("");

  const defenseLogHtml = (r.defense_log || []).map((d) => `
    <li>
      <strong>${escapeHtml(d.name)}:</strong>
      <span class="verdict-${escapeHtml((d.verdict || "").toLowerCase())}">${escapeHtml(d.verdict || "")}</span>
      ${d.detail ? ` — ${escapeHtml(d.detail)}` : ""}
    </li>
  `).join("");

  const impactKind = (blockedBy || !succeeded) ? "impact-blocked" : "impact-success";
  const impactHeader = blockedBy
    ? `Blocked by <span class="defense-pill">${escapeHtml(blockedBy)}</span>`
    : succeeded
      ? "Attack succeeded — canary leaked"
      : "Attack did not succeed";

  const impactBody = blockedBy
    ? `<p>The defense fired before the attack could influence the model's response. In production NexaCore Knowledge Hub, this would prevent the poisoned answer from reaching the employee — the malicious document never contributed to the answer.</p>`
    : succeeded
      ? `<p>The model echoed the canary phrase from the poisoned document. In production, every NexaCore employee who asked this question would receive the attacker-crafted answer — authenticated by the company's own knowledge system.</p>`
      : `<p>The model did not follow the poisoned document's instructions. This may mean the attack document didn't retrieve highly enough, or the model's internal safety handling quietly dropped the injection.</p>`;

  const whyText = whyExplanation(r, succeeded, blockedBy, atk);

  const rp5CalloutHtml = (r.attack_id === "RP.5" && succeeded) ? `
    <div class="result-panel" style="border-left:3px solid var(--color-accent-aisl-highlight);background:var(--color-accent-aisl-subtle);padding:14px 18px;margin-bottom:var(--space-4);">
      <div class="result-header" style="color:var(--color-accent-aisl-highlight);">Sharpest insight in this lab</div>
      <div class="card-body">
        <p><strong>RP.5 (Embedding Adjacency) has no injection text, no fake citations, no authority spoofing.</strong> The poisoned document contains nothing overtly malicious — it just has keywords that push its embedding vector close to the query vector.</p>
        <p>Content-based defenses (Adversarial Filter, Output Grounding) are completely blind to this. They scan for suspicious patterns — there are none. <strong>Only Provenance Check catches it</strong>, because it doesn't care what the document says — only where it came from.</p>
        <p>This is why source-based filtering is the primary defense in any RAG system. Semantics are easy to manipulate; provenance is not.</p>
      </div>
    </div>` : "";

  setHtml(host, `
    <div class="results">
      ${rp5CalloutHtml}
      <div class="result-panel" data-kind="cause">
        <div class="result-header">Cause — what was sent to the model</div>
        <div class="result-section">
          <div class="result-section-label">Employee query</div>
          <pre>${escapeHtml(r.query || "")}</pre>
        </div>
        <div class="result-section">
          <div class="result-section-label">Top-k retrieved documents (rank / kind / cosine)</div>
          <ul class="retrieval-list">${retrievalList || "<li class='muted'>No retrieval data</li>"}</ul>
        </div>
        <div class="result-section">
          <div class="result-section-label">System prompt sent to the model</div>
          <pre>${escapeHtml((r.system_prompt || "").substring(0, 800))}${(r.system_prompt || "").length > 800 ? "\n…(truncated)" : ""}</pre>
        </div>
        <div class="result-section">
          <div class="result-section-label">Elapsed</div>
          <span class="muted">${Number(r.elapsed_seconds || 0).toFixed(2)}s</span>
        </div>
      </div>

      <div class="result-panel" data-kind="effect">
        <div class="result-header">Effect — what the model said</div>
        <div class="result-section">
          <pre>${responseHtml || "<span class='muted'>(no model response — blocked at ingestion)</span>"}</pre>
        </div>
        ${defenseLogHtml ? `
          <div class="result-section">
            <div class="result-section-label">Defense log</div>
            <ul class="defense-log">${defenseLogHtml}</ul>
          </div>` : ""}
      </div>

      <div class="result-panel" data-kind="${impactKind}">
        <div class="result-header">Impact — ${impactHeader}</div>
        <div class="card-body">${impactBody}</div>
      </div>

      <div class="why-card">
        <div class="why-card-label">${succeeded ? "Why this got through" : blockedBy ? "Why this was blocked" : "What this tells you"}</div>
        <div class="why-card-body">${escapeHtml(whyText)}</div>
      </div>
    </div>
  `);
}

function highlightCanary(text, canary) {
  const escaped = escapeHtml(text);
  const escapedCanary = escapeHtml(canary);
  if (!escapedCanary) return escaped;
  const re = new RegExp(escapedCanary.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi");
  return escaped.replace(re, (m) => `<span class="canary-hit">${m}</span>`);
}

function whyExplanation(r, succeeded, blockedBy, atk) {
  if (blockedBy) {
    const map = {
      provenance_check: "Provenance Check blocked at ingestion — the poisoned document's source URI is not on the trusted-sources allowlist. This fires before any retrieval or LLM call, making it zero-cost to enforce.",
      adversarial_filter: "Adversarial Filter matched an injection pattern in the poisoned document's text (e.g., 'ATTENTION ALL EMPLOYEES', 'AS APPROVED BY', or a year-pinned supersession claim). Blocked at ingestion — no retrieval, no LLM call.",
      retrieval_diversity: "Retrieval Diversity detected that multiple top-k results shared the same source URI — a telltale sign of a Multi-Doc Consensus attack (RP.6). Blocked after retrieval but before the LLM call.",
      output_grounding: "Output Grounding found fabricated citation IDs in the model's response that don't exist in the corpus. Blocked post-LLM — the LLM call happened but the response was suppressed.",
    };
    return map[blockedBy] || "A defense fired and prevented the attack from reaching (or leaking from) the model.";
  }
  if (succeeded) {
    const map = {
      "RP.1": "Direct Injection succeeded because the model treated explicit instructions embedded in the retrieved document as authoritative. Corpus poisoning bypasses all input validation that operates on the user's query — the attack content never touched the user's prompt.",
      "RP.2": "Authority Spoof succeeded because LLMs are sensitive to claimed authority cues ('AS APPROVED BY CISO'). The model had no way to verify the claim — and without provenance checking, there's nothing to verify.",
      "RP.3": "Outdated-Info Override succeeded because the model weighted the poisoned document's 'supersedes 2024 version' claim. LLMs tend to defer to documents that assert temporal priority — this mirrors how humans update beliefs when they see 'revised policy'.",
      "RP.4": "Citation Spoof succeeded because the model followed the poisoned document's fabricated citation chain without checking whether the cited IDs exist in the corpus. Output Grounding would have caught this — but it wasn't enabled.",
      "RP.5": "Embedding Adjacency succeeded because keyword-stuffing drove the poisoned document's cosine similarity above the legitimate policy doc's score. The model retrieved the poisoned doc at rank 1 — and had no reason to distrust it.",
      "RP.6": "Multi-Doc Consensus succeeded because the model treated agreement across multiple retrieved sources as truth. None of the three sibling docs had obvious injection patterns — only their clustering (shared source URI) reveals the attack, and Retrieval Diversity wasn't enabled.",
    };
    return map[atk && atk.id] || "The poisoned document was retrieved ahead of the legitimate policy and the model trusted it.";
  }
  return "The attack did not produce the canary phrase. The poisoned document may not have scored highly enough in retrieval, or the model's response didn't follow the injection. Try a different defense configuration or check the retrieval scores in the Cause panel.";
}
