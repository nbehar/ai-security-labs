/**
 * attack_runner.js — Renders the P1 + P5 lab tabs.
 *
 * Composition per frontend_spec.md:
 *   1. Level briefing card (collapsible "What to try" suggestion)
 *   2. Attack picker (which attack you're working on)
 *   3. Mode toggle: pre-canned gallery vs upload
 *   4. Run panel: image preview + defense toggles + Run Attack button
 *   5. Result panels: Cause / Effect / Impact (Cause shows OCR layer on P5)
 *   6. Why-this-works card
 *   7. Per-student inline score banner (no leaderboard tab)
 *
 * Backend integration: POST /api/attack (multipart) and POST /api/score (json).
 * Per CLAUDE.md, the running total is shown inline only — never as a leaderboard.
 *
 * XSS posture: all interpolated values escaped via escapeHtml; renders go through
 * setHtml (Range.createContextualFragment).
 */

import { fetchJSON, escapeHtml } from "/static/js/core.js";
import { setHtml } from "/static/js/app.js";
import { buildGalleryFor, renderGallery } from "/static/js/image_gallery.js";
import { renderUploadPanel } from "/static/js/image_upload.js";

const DEFENSE_LABELS = {
  ocr_prescan: { name: "OCR Pre-Scan", help: "Tesseract OCRs the image and rejects keyword hits before model inference." },
  output_redaction: { name: "Output Redaction", help: "Scans the model response for the canary phrase and redacts." },
  boundary_hardening: { name: "Boundary Hardening", help: "Strengthens the system prompt to treat image text as untrusted content, not instructions." },
  confidence_threshold: { name: "Confidence Threshold", help: "Rejects images where Tesseract's mean confidence is below 60." },
};

const BRIEFINGS = {
  image_prompt_injection: {
    title: "P1 — Image Prompt Injection",
    summary: "Vision LLMs follow text-in-images as if it were a user instruction. The injection sits in plain sight; the model's failure is treating image content as authoritative.",
    analogy: "Traditional analogy: input validation failure across a new modality — like XSS in a stored field, but the field is pixels.",
    deployed: "Qwen2.5-VL-72B via HF Inference Providers (OVH cloud). No defenses are on by default.",
    tryThis: "Run P1.1 with no defenses. Then turn on Output Redaction and run it again — note the canary disappears, but the model's reasoning didn't change.",
  },
  ocr_poisoning: {
    title: "P5 — OCR Poisoning",
    summary: "Hidden text — white-on-white, microprint, near-color, layered — is invisible to humans but extracted by OCR pipelines and acted on by the model.",
    analogy: "The SQL injection of vision pipelines: what looks legitimate to the eye carries executable instructions for the machine.",
    deployed: "Same Qwen2.5-VL-72B route. The Cause panel shows the OCR-extracted text so you can see what the model actually saw.",
    tryThis: "Run P5.1 (white-on-white) with Confidence Threshold off, then on. Watch the OCR layer in the Cause panel reveal the hidden payload.",
  },
};

// ---------------------------------------------------------------------------
// Public entry — renders one of the two lab tabs (P1 or P5).
// ---------------------------------------------------------------------------

export function renderImagePromptInjectionTab(container, opts) {
  const { lab, attacks, labelPrefix, state, showOcrLayer = false } = opts;

  if (!attacks.length) {
    setHtml(container, `<div class="card"><div class="card-body muted">No attacks available for ${escapeHtml(labelPrefix)}.</div></div>`);
    return;
  }

  const briefing = BRIEFINGS[lab];

  // Local state for this tab render. Replaced wholesale on each switch.
  const localState = {
    selectedAttackId: attacks[0].id,
    selectedImage: null,
    mode: "canned",
    defenses: new Set(),
    running: false,
    lastResult: null,
    attempts: {},
  };

  const attackOptions = attacks.map((a) =>
    `<option value="${escapeHtml(a.id)}"${a.known_limitation ? ' data-limited="1"' : ""}>${escapeHtml(a.id)} — ${escapeHtml(a.name)} ${"★".repeat(a.difficulty || 1)}${a.known_limitation ? " ⚠" : ""}</option>`
  ).join("");

  const defenseRow = Object.entries(DEFENSE_LABELS).map(([id, { name, help }]) => `
    <label class="defense-toggle">
      <input type="checkbox" data-defense="${escapeHtml(id)}">
      <span>${escapeHtml(name)}</span>
      <span class="help" title="${escapeHtml(help)}" aria-label="${escapeHtml(help)}">?</span>
    </label>
  `).join("");

  setHtml(container, `
    <section class="card card-accent">
      <div class="card-eyebrow">${escapeHtml(briefing.title)}</div>
      <div class="card-body">
        <p>${escapeHtml(briefing.summary)}</p>
        <p class="muted" style="font-size:var(--text-sm);">${escapeHtml(briefing.analogy)}</p>
        <p class="muted" style="font-size:var(--text-sm);">${escapeHtml(briefing.deployed)}</p>
        <details>
          <summary class="text-mono" style="cursor:pointer;color:var(--color-accent-aisl-highlight);font-size:var(--text-sm);">What to try</summary>
          <p style="margin-top:var(--space-2);font-size:var(--text-sm);">${escapeHtml(briefing.tryThis)}</p>
        </details>
      </div>
    </section>

    <section class="score-banner" id="score-banner-${escapeHtml(labelPrefix)}">
      <div>
        <div class="score-label">Your ${escapeHtml(labelPrefix)} score</div>
        <div class="score-value" id="score-value-${escapeHtml(labelPrefix)}">0</div>
      </div>
      <div class="score-stars" id="score-stars-${escapeHtml(labelPrefix)}" aria-label="Attempts completed"></div>
      <div class="score-detail muted">100 first try · −20 per retry · floor 20 · +50 if a defense blocks</div>
    </section>

    <section class="card">
      <h2 class="card-title">Pick an attack</h2>
      <div class="card-body">
        <label for="attack-select-${escapeHtml(labelPrefix)}" class="muted" style="font-size:var(--text-sm);">Attack</label>
        <select id="attack-select-${escapeHtml(labelPrefix)}" class="btn btn-secondary" style="width:100%;margin-top:var(--space-2);">
          ${attackOptions}
        </select>

        <div id="limitation-banner-${escapeHtml(labelPrefix)}" style="display:none;margin-top:var(--space-3);padding:10px 14px;background:var(--color-warning-subtle);border-left:3px solid var(--color-warning);border-radius:0 var(--radius-sm) var(--radius-sm) 0;font-size:13px;"></div>

        <div class="gallery-mode-toggle" style="margin-top:var(--space-4);">
          <label><input type="radio" name="mode-${escapeHtml(labelPrefix)}" value="canned" checked> Pre-canned image</label>
          <label><input type="radio" name="mode-${escapeHtml(labelPrefix)}" value="uploaded"> Upload my own</label>
        </div>

        <div id="gallery-${escapeHtml(labelPrefix)}"></div>
        <div id="upload-${escapeHtml(labelPrefix)}" class="hidden"></div>
      </div>
    </section>

    <section class="run-panel" aria-label="Run the attack">
      <h2 class="card-title">Run</h2>
      <img id="run-preview-${escapeHtml(labelPrefix)}" class="run-preview hidden" alt="Selected image preview">

      <div class="defense-toggles" role="group" aria-label="Defenses">
        ${defenseRow}
      </div>

      <div class="run-actions">
        <button class="btn btn-primary" id="btn-run-${escapeHtml(labelPrefix)}" type="button">Run Attack</button>
        <span class="status-line" id="status-${escapeHtml(labelPrefix)}"></span>
      </div>
    </section>

    <div id="results-${escapeHtml(labelPrefix)}"></div>
  `);

  const galleryHost = container.querySelector(`#gallery-${labelPrefix}`);
  const uploadHost = container.querySelector(`#upload-${labelPrefix}`);
  const previewImg = container.querySelector(`#run-preview-${labelPrefix}`);
  const runBtn = container.querySelector(`#btn-run-${labelPrefix}`);
  const statusLine = container.querySelector(`#status-${labelPrefix}`);
  const attackSelect = container.querySelector(`#attack-select-${labelPrefix}`);
  const resultsHost = container.querySelector(`#results-${labelPrefix}`);
  const limitationBanner = container.querySelector(`#limitation-banner-${labelPrefix}`);

  function showStatus(html) { setHtml(statusLine, html); }
  function clearStatus() { setHtml(statusLine, ""); }

  function updateLimitationBanner(attackId) {
    const atk = attacks.find((a) => a.id === attackId);
    if (atk && atk.known_limitation) {
      limitationBanner.style.display = "block";
      limitationBanner.textContent = `⚠ Known limitation — ${atk.known_limitation}`;
    } else {
      limitationBanner.style.display = "none";
      limitationBanner.textContent = "";
    }
  }

  function setSelectedImage(item) {
    localState.selectedImage = item;
    if (item && item.url) {
      previewImg.src = item.url;
      previewImg.classList.remove("hidden");
    } else if (item && item.previewUrl) {
      previewImg.src = item.previewUrl;
      previewImg.classList.remove("hidden");
    } else {
      previewImg.classList.add("hidden");
    }
  }

  async function refreshGallery() {
    showStatus(`<span class="spinner"></span> Loading images…`);
    try {
      const payload = await buildGalleryFor(localState.selectedAttackId);
      renderGallery(galleryHost, payload, { onSelect: setSelectedImage });
      clearStatus();
    } catch (e) {
      statusLine.textContent = `Could not load images: ${e.message}`;
    }
  }

  updateLimitationBanner(localState.selectedAttackId);

  attackSelect.addEventListener("change", () => {
    localState.selectedAttackId = attackSelect.value;
    updateLimitationBanner(localState.selectedAttackId);
    if (localState.mode === "canned") refreshGallery();
  });

  for (const radio of container.querySelectorAll(`input[name="mode-${labelPrefix}"]`)) {
    radio.addEventListener("change", () => {
      localState.mode = radio.value;
      if (radio.value === "canned") {
        galleryHost.classList.remove("hidden");
        uploadHost.classList.add("hidden");
        setSelectedImage(null);
        refreshGallery();
      } else {
        galleryHost.classList.add("hidden");
        uploadHost.classList.remove("hidden");
        setSelectedImage(null);
        renderUploadPanel(uploadHost, {
          onSelect: (sel) => setSelectedImage(sel),
          onError: (msg) => { statusLine.textContent = msg; },
        });
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
    if (localState.mode === "canned" && !localState.selectedImage) {
      statusLine.textContent = "Pick an image first.";
      return;
    }
    if (localState.mode === "uploaded" && (!localState.selectedImage || !localState.selectedImage.file)) {
      statusLine.textContent = "Choose a file to upload first.";
      return;
    }

    localState.running = true;
    runBtn.setAttribute("disabled", "true");
    showStatus(`<span class="spinner"></span> Running attack… (10–20s on the 72B model)`);
    setHtml(resultsHost, "");

    try {
      const result = await runAttack(localState);
      localState.lastResult = result;
      localState.attempts[result.attack_id] = (localState.attempts[result.attack_id] || 0) + 1;
      renderResult(resultsHost, result, { showOcrLayer });
      await postScore(state, localState, result, labelPrefix, container);
      clearStatus();
    } catch (e) {
      const detail = e && e.message ? e.message : String(e);
      const friendly = /timed out/i.test(detail)
        ? "Inference Provider call timed out. Try again — the platform may be rate-limited or briefly unavailable."
        : `Attack failed: ${detail}`;
      setHtml(resultsHost, `<div class="banner banner-danger">${escapeHtml(friendly)}</div>`);
      clearStatus();
    } finally {
      localState.running = false;
      runBtn.removeAttribute("disabled");
    }
  });

  refreshGallery();
}

// ---------------------------------------------------------------------------
// Run / score helpers
// ---------------------------------------------------------------------------

async function runAttack(localState) {
  const fd = new FormData();
  fd.append("attack_id", localState.selectedAttackId);
  fd.append("image_source", localState.mode);
  fd.append("defenses", JSON.stringify([...localState.defenses]));
  if (localState.mode === "canned") {
    fd.append("image_filename", localState.selectedImage.filename);
  } else {
    fd.append("image_file", localState.selectedImage.file);
  }
  return fetchJSON("/api/attack", { method: "POST", body: fd });
}

async function postScore(state, localState, result, labelPrefix, root) {
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
    updateScoreBanner(root, labelPrefix, state, localState);
  } catch (e) {
    // Non-fatal — score banner just won't update.
  }
}

function updateScoreBanner(root, labelPrefix, state, localState) {
  const valueEl = root.querySelector(`#score-value-${labelPrefix}`);
  const starsEl = root.querySelector(`#score-stars-${labelPrefix}`);
  if (!valueEl) return;

  let total = 0;
  let completed = 0;
  for (const [id, entry] of Object.entries(state.scoreByAttack)) {
    if (id.startsWith(`${labelPrefix}.`)) {
      total += entry.score_added || 0;
      completed += 1;
    }
  }
  valueEl.textContent = String(total);

  const totalAttacks = 6;
  const stars = Array.from({ length: totalAttacks }, (_, i) =>
    `<span class="${i < completed ? "star-on" : "star-off"}" aria-hidden="true">★</span>`
  ).join("");
  setHtml(starsEl, stars);
}

// ---------------------------------------------------------------------------
// Result panels — Cause / Effect / Impact + Why-card
// ---------------------------------------------------------------------------

function renderResult(host, r, { showOcrLayer }) {
  const blockedBy = r.blocked_by;
  const succeeded = r.succeeded;
  const canary = r.canary || "";
  const responseHtml = canary
    ? highlightCanary(r.model_response || "", canary)
    : escapeHtml(r.model_response || "");

  const ocrBlock = showOcrLayer
    ? `
      <div class="result-section">
        <div class="result-section-label">OCR extraction (what the pipeline saw)</div>
        <pre>${escapeHtml(r.ocr_extraction || "(empty — OCR pre-scan disabled or no text)")}</pre>
      </div>`
    : "";

  const defenseLogHtml = (r.defense_log || []).map((d) => `
    <li>
      <strong>${escapeHtml(d.name)}:</strong>
      <span class="verdict-${escapeHtml((d.verdict || "").toLowerCase())}">${escapeHtml(d.verdict || "")}</span>
      ${d.detail ? ` — ${escapeHtml(d.detail)}` : ""}
    </li>
  `).join("");

  const impactKind = blockedBy ? "impact-blocked" : succeeded ? "impact-success" : "impact-blocked";
  const impactHeader = blockedBy
    ? `Blocked by <span class="defense-pill">${escapeHtml(blockedBy)}</span>`
    : succeeded
      ? "Attack succeeded"
      : "Attack failed (model didn't comply)";

  const impactBody = blockedBy
    ? `<p>The defense fired before the attack could reach the model's downstream actions. In production this would prevent the routing system from acting on the malicious instructions.</p>`
    : succeeded
      ? `<p>The model echoed the canary phrase. In production NexaCore DocReceive, this is the moment a fraudulent expense reimbursement is approved, a vendor onboarded, or a badge provisioned — by the time downstream systems receive the request, it looks legitimate.</p>`
      : `<p>The model didn't follow the injection — but it also didn't trip a defense. This usually means the attack image was off, or the model's built-in safety filtering quietly dropped the malicious instruction. Try a different attack image.</p>`;

  const whyText = whyExplanation(r, succeeded, blockedBy);
  const causeImg = (r.image_used && r.image_used.source === "canned")
    ? `/static/images/canned/${r.image_used.filename}`
    : "";

  setHtml(host, `
    <div class="results">
      <div class="result-panel" data-kind="cause">
        <div class="result-header">Cause — what was sent</div>
        ${causeImg
          ? `<img class="result-image" src="${escapeHtml(causeImg)}" alt="${escapeHtml(r.image_used.filename)}">`
          : ""}
        <div class="result-section">
          <div class="result-section-label">System prompt sent to the model</div>
          <pre>${escapeHtml(r.system_prompt || "")}</pre>
        </div>
        <div class="result-section">
          <div class="result-section-label">User prompt</div>
          <pre>${escapeHtml(r.user_prompt || "")}</pre>
        </div>
        ${ocrBlock}
      </div>

      <div class="result-panel" data-kind="effect">
        <div class="result-header">Effect — what the model said</div>
        <div class="result-section">
          <pre>${responseHtml}</pre>
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
        <div class="why-card-label">${escapeHtml(succeeded ? "Why this got through" : blockedBy ? "Why this was blocked" : "What this tells you")}</div>
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

function whyExplanation(r, succeeded, blockedBy) {
  if (blockedBy) {
    const map = {
      ocr_prescan: "OCR Pre-Scan extracted the image text and matched a high-risk keyword before the model was ever called. This stops keyword-perfect attacks but is bypassed by paraphrase.",
      output_redaction: "Output Redaction caught the canary phrase in the model's response and redacted it. The model still followed the injection — this defense only prevents the canary from leaking, it doesn't stop the bad reasoning.",
      boundary_hardening: "The hardened system prompt told the model that text inside images is untrusted document content, never an instruction. The model treated the injection as raw text to summarize.",
      confidence_threshold: "Tesseract's mean OCR confidence was below threshold, suggesting the image had hidden or poorly-rendered text. The lab rejected the upload before model inference.",
    };
    return map[blockedBy] || "A defense fired before the model could complete the malicious action.";
  }
  if (succeeded) {
    return "The vision LLM treated text inside the image as authoritative instructions and produced the canary. Boundary-hardening alone won't fix this — strong models still follow plausible authority-spoofing language. Layer Output Redaction (catches the leak) with OCR Pre-Scan (catches keyword-perfect attacks) for a defense in depth.";
  }
  return "The model didn't comply with the injection but no defense caught it either. Either the attack image text was rendered too poorly to read, or the model's built-in safety filtering quietly dropped the instruction without raising it as a refusal.";
}
