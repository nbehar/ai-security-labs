/**
 * app.js — Data Poisoning Lab SPA entry (Luminex Learning · AI Security Labs).
 *
 * Tabs: Info → RAG Poisoning → Defenses → Corpus Browser.
 * No leaderboard tab — per-student scoring only (Phase 6 will route to Canvas LMS).
 *
 * XSS posture: every interpolated value is run through `escapeHtml` from
 * core.js. Static template literals are author-trusted. Render uses
 * `Range.createContextualFragment` to keep the platform security hook happy.
 */

import { fetchJSON, escapeHtml, renderKnowledgeCheck, wireKnowledgeCheck } from "/static/js/core.js";
import { renderRagPoisoningTab } from "/static/js/attack_runner.js";
import { renderCorpusBrowserTab } from "/static/js/corpus_browser.js";

const TABS = [
  { id: "info",   label: "Info" },
  { id: "attack", label: "RAG Poisoning" },
  { id: "def",    label: "Defenses" },
  { id: "corpus", label: "Corpus Browser" },
];

const state = {
  activeTab: "info",
  health: null,
  attacks: null,
  queries: null,
  corpus: null,
  scoreByAttack: {},
  participantName: localStorage.getItem("data-poisoning:participant") || "Anonymous",
};

export function setHtml(el, html) {
  const range = document.createRange();
  range.selectNodeContents(el);
  range.deleteContents();
  el.replaceChildren(range.createContextualFragment(html));
}

(async function init() {
  renderTabs();
  await loadHealth();
  await Promise.all([loadAttacks(), loadQueries()]);
  routeFromHash();
  window.addEventListener("hashchange", routeFromHash);
})();

function routeFromHash() {
  const wanted = (location.hash || "").replace(/^#/, "");
  const tab = TABS.find((t) => t.id === wanted) ? wanted : "info";
  setActiveTab(tab);
}

function setActiveTab(id) {
  state.activeTab = id;
  if (location.hash !== `#${id}`) location.hash = id;
  for (const btn of document.querySelectorAll(".tab")) {
    btn.setAttribute("aria-selected", btn.dataset.tab === id ? "true" : "false");
  }
  renderActivePanel();
}

function renderTabs() {
  const nav = document.getElementById("tabs");
  const html = TABS.map((t) =>
    `<button class="tab" role="tab" data-tab="${t.id}" aria-selected="${t.id === state.activeTab ? "true" : "false"}">${escapeHtml(t.label)}</button>`
  ).join("");
  setHtml(nav, html);
  for (const btn of nav.querySelectorAll(".tab")) {
    btn.addEventListener("click", () => setActiveTab(btn.dataset.tab));
  }
}

// ---------------------------------------------------------------------------
// Health + config
// ---------------------------------------------------------------------------

async function loadHealth() {
  try {
    state.health = await fetchJSON("/health");
  } catch (e) {
    showBanner("danger", `Health check failed: ${escapeHtml(e.message)}`);
    return;
  }
  if (!state.health.groq_api_key_set) {
    showBanner(
      "warning",
      "<strong>Groq token not configured.</strong> The lab is offline — contact the workshop instructor."
    );
  }
  if (!state.health.embeddings_loaded) {
    showBanner(
      "info",
      "Embedding model is loading (cold-start). First attack may take a few seconds longer."
    );
  }
}

async function loadAttacks() {
  try {
    const data = await fetchJSON("/api/attacks");
    state.attacks = data.attacks;
  } catch (e) {
    showBanner("danger", `Could not load attack catalog: ${escapeHtml(e.message)}`);
    state.attacks = [];
  }
}

async function loadQueries() {
  try {
    const data = await fetchJSON("/api/queries");
    state.queries = data.queries;
  } catch (e) {
    state.queries = [];
  }
}

function showBanner(kind, html) {
  const wrap = document.getElementById("banners");
  const div = document.createElement("div");
  div.className = `banner banner-${kind}`;
  div.replaceChildren(document.createRange().createContextualFragment(html));
  wrap.appendChild(div);
}

// ---------------------------------------------------------------------------
// Tab routing
// ---------------------------------------------------------------------------

function renderActivePanel() {
  const c = document.getElementById("content");
  switch (state.activeTab) {
    case "info":   return renderInfoTab(c);
    case "attack": return renderRagPoisoningTab(c, state);
    case "def":    return renderDefensesTab(c);
    case "corpus": return renderCorpusBrowserTab(c, state);
  }
}

// ---------------------------------------------------------------------------
// Info tab
// ---------------------------------------------------------------------------

const KC_QUESTIONS_DATA_POISONING = [
  {
    q: "In RP.5 (Embedding Adjacency), the poisoned document retrieves ahead of the legitimate policy because:",
    options: [
      { label: "It contains explicit override instructions like 'IGNORE PREVIOUS DOCUMENTS'", correct: false, explanation: "RP.5 intentionally has no injection language. That's what makes it hard to catch with content filters. It manipulates retrieval, not the model's instruction-following." },
      { label: "Its embedding vector is more similar to the query's embedding than the legitimate policy document", correct: true, explanation: "By repeating keywords from common employee queries, the poisoned doc's meaning-fingerprint (embedding) ends up closer to those queries than the real policy doc. The retriever ranks it #1 — so the model receives it as the authoritative source." },
      { label: "It has a more recent modification timestamp than the legitimate policy", correct: false, explanation: "RP.3 (Outdated-Info Override) uses a recency claim. RP.5 uses keyword stuffing — the retrieval mechanism is semantic similarity, not timestamp." },
    ],
  },
  {
    q: "Which single defense catches RP.5 (Embedding Adjacency)?",
    options: [
      { label: "Adversarial Filter — it detects injection-like patterns in the document text", correct: false, explanation: "Adversarial filter looks for ATTENTION calls, fake authority phrases, year-pinned claims. RP.5 has none of those — keyword stuffing leaves no detectable injection pattern." },
      { label: "Output Grounding — it rejects responses that cite non-existent document IDs", correct: false, explanation: "Output grounding catches RP.4's fabricated citations. RP.5 doesn't fabricate citations — it gets retrieved naturally via keyword stuffing, then cited as a real doc." },
      { label: "Provenance Check — it blocks any document not from a trusted source URI", correct: true, explanation: "The poisoned doc's source is '(attack — pre-canned)', not on the trusted allowlist. Provenance blocks before retrieval, regardless of document content or embedding. Source control is the load-bearing defense." },
    ],
  },
  {
    q: "Provenance in a RAG system is most analogous to:",
    options: [
      { label: "A document's word count or estimated reading level", correct: false, explanation: "Word count is a content property. You can't determine trustworthiness from document length. Provenance is about origin, not content." },
      { label: "Git commit signing — you trust commits from known, cryptographically verified authors", correct: true, explanation: "Just as you only merge commits signed by a verified key, you only index documents from verified source URIs. An attacker who can't spoof a trusted source path can't poison the corpus — regardless of how convincing the document content is." },
      { label: "The cosine similarity score between two embedding vectors", correct: false, explanation: "Cosine similarity measures semantic relatedness — it's how the retriever ranks documents. Provenance is about who supplied the document, not how semantically similar it is to a query." },
    ],
  },
];

const CONCEPTS = [
  {
    name: "RAG (Retrieval-Augmented Generation)",
    def: "LLM pattern where the model retrieves documents from a corpus before generating an answer.",
    analogy: "Like consulting a wiki before answering a customer support ticket — but the wiki can be poisoned.",
  },
  {
    name: "Embedding",
    def: "A vector that represents the semantic meaning of a chunk of text.",
    analogy: "Like a fingerprint for ideas — similar ideas have similar fingerprints.",
  },
  {
    name: "Vector DB",
    def: "A datastore of embeddings supporting nearest-neighbor lookup.",
    analogy: "Like a search engine that searches by meaning, not keywords.",
  },
  {
    name: "Top-K Retrieval",
    def: "Finding the K most-similar embeddings to a query embedding.",
    analogy: "Like Google's 'Did you mean…' but for whole documents.",
  },
  {
    name: "Corpus Poisoning",
    def: "An attack where the attacker introduces a malicious document into the retrieval corpus.",
    analogy: "Like a supply-chain attack on npm packages — corrupt the source the system trusts.",
  },
  {
    name: "Provenance",
    def: "The verifiable history of where a document came from.",
    analogy: "Like Git commit signing for a knowledge base.",
  },
  {
    name: "Grounding",
    def: "Constraining the LLM to cite specific documents in its answer.",
    analogy: "Like requiring footnotes in a research paper — every claim must trace to a source.",
  },
  {
    name: "Canary Phrase",
    def: "Sentinel value placed in poisoned documents to detect successful retrieval and model compliance.",
    analogy: "Like a honeytoken in DLP — invisible to legit users, audible if exfiltrated.",
  },
];

function renderInfoTab(container) {
  const conceptCards = CONCEPTS.map((c) => `
    <article class="concept-card">
      <h3 class="concept-name">${escapeHtml(c.name)}</h3>
      <p class="concept-def">${escapeHtml(c.def)}</p>
      <p class="concept-analogy">${escapeHtml(c.analogy)}</p>
    </article>
  `).join("");

  setHtml(container, `
    <section class="card">
      <h2 class="card-title">What You'll Learn</h2>
      <div class="card-body">
        <p style="color:var(--muted);font-size:13px;margin-bottom:12px;">Assumed knowledge: basic understanding of what a search engine or database index does. No ML expertise required.</p>
        <p style="margin-bottom:8px;">By the end of this workshop you will be able to:</p>
        <ul style="margin:0;padding-left:20px;line-height:1.8;">
          <li><strong>Explain</strong> how the RAG pipeline (embed → retrieve → generate) creates a new attack surface beyond the LLM itself</li>
          <li><strong>Predict</strong> why keyword-stuffing increases a document's cosine similarity to common queries — and why that lets it displace the legitimate policy document</li>
          <li><strong>Distinguish</strong> content-based defenses (adversarial filter, output grounding) from source-based defenses (provenance) and identify which attack class each one cannot catch</li>
          <li><strong>Explain</strong> why provenance is load-bearing: only source control catches RP.5, because content-based filters are blind to documents with no injection language</li>
          <li><strong>Apply</strong> the RAG poisoning threat model to a real-world scenario and identify which single defense to deploy first</li>
        </ul>
      </div>
    </section>

    <section class="card">
      <h2 class="card-title">The NexaCore Knowledge Hub</h2>
      <div class="card-body">
        <p>
          NexaCore's Knowledge Hub is an internal Q&amp;A portal that thousands of employees use every day.
          Staff type natural-language questions — about reimbursement policies, vendor onboarding, badge access,
          onboarding checklists, or litigation holds — and get back a clean, cited answer in seconds.
        </p>
        <p>
          Behind the scenes the system follows the RAG pattern: it embeds the query into a vector, retrieves
          the top-3 most-similar documents from the corpus, and sends those documents plus the query to LLaMA 3.3 70B.
          The model composes an answer that cites the retrieved docs.
        </p>
        <p>
          That's a juicy attack target. If an adversary can insert a document into the corpus that retrieves ahead of
          the legitimate policy, the model will repeat whatever that document says — and every employee who asks that
          question gets the poisoned answer, authenticated by the company's own Knowledge Hub.
        </p>
      </div>

      <div class="arch-flow" aria-label="Knowledge Hub architecture with attack injection point">
        <span class="arch-node">Employee</span>
        <span class="arch-arrow">→</span>
        <span class="arch-node">Query</span>
        <span class="arch-arrow">→</span>
        <span class="arch-node">Embedder</span>
        <span class="arch-arrow">→</span>
        <span class="arch-node">Top-K Retrieval</span>
        <span class="arch-arrow">→</span>
        <span class="arch-node">LLaMA 3.3 70B</span>
        <span class="arch-arrow">→</span>
        <span class="arch-node">Answer + Citations</span>
      </div>
      <div style="font-family:var(--font-mono);font-size:var(--text-xs);color:var(--color-danger-light);margin-top:var(--space-2);">
        Attack injection point: a poisoned document in the corpus is retrieved into the top-k, then the LLM treats it as authoritative.
      </div>
    </section>

    <section class="card">
      <h2 class="card-title">Key Concepts</h2>
      <div class="concepts-grid">${conceptCards}</div>
    </section>

    <section class="card card-accent">
      <h2 class="card-title">Recommended Order</h2>
      <div class="card-body">
        <ol>
          <li>Read this Info tab — understand what RAG does and why it's attackable.</li>
          <li>Open <strong>RAG Poisoning</strong> — run RP.1 (Direct Injection) with no defenses. Watch the canary phrase appear in the answer.</li>
          <li>Toggle defenses one at a time — observe what gets blocked and what slips through.</li>
          <li>Open <strong>Defenses</strong> — study the full attack-vs-defense matrix to understand which defense class catches which attack.</li>
          <li>Open <strong>Corpus Browser</strong> — compare the poisoned documents to the legitimate policy docs they're designed to displace.</li>
        </ol>
        <p class="muted" style="margin-top:var(--space-3);font-size:var(--text-sm);">
          Scored individually as a graduate-course assignment. Your running total is shown inline on the RAG Poisoning tab.
          There is no leaderboard — scores will be submitted to Canvas LMS in a future release.
        </p>
      </div>
    </section>

    <section class="card">
      <h2 class="card-title">Where This Lab Fits</h2>
      <div class="card-body">
        <div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:13px;margin-bottom:12px;">
          <span style="padding:3px 8px;background:var(--surface-2,#1e1e2a);border-radius:4px;color:var(--muted);">OWASP LLM Top 10 →</span>
          <span style="padding:3px 8px;background:var(--surface-2,#1e1e2a);border-radius:4px;color:var(--muted);">Red Team →</span>
          <span style="padding:3px 8px;background:var(--surface-2,#1e1e2a);border-radius:4px;color:var(--muted);">Blue Team →</span>
          <span style="padding:3px 8px;background:var(--surface-2,#1e1e2a);border-radius:4px;color:var(--muted);">Multimodal →</span>
          <span style="padding:3px 8px;background:rgba(139,92,246,0.15);border:1px solid #a78bfa;border-radius:4px;color:#a78bfa;font-weight:600;">Data Poisoning (you are here)</span>
        </div>
        <p><strong>This lab:</strong> Attacks on the retrieval layer — poisoning the knowledge base the AI reads from before it answers. These work even if the model itself is perfectly hardened.</p>
        <p style="color:var(--muted);font-size:13px;margin-top:8px;">You've now covered all four major LLM attack surfaces: prompt injection (Red Team), defense construction (Blue Team), multimodal vectors (Multimodal), and supply-chain poisoning (this lab).</p>
      </div>
    </section>

    ${renderKnowledgeCheck(KC_QUESTIONS_DATA_POISONING, "#a78bfa")}
  `);

  wireKnowledgeCheck(container);
}

// ---------------------------------------------------------------------------
// Defenses tab — measured matrix + detail cards
// ---------------------------------------------------------------------------

const DEFENSES = [
  {
    id: "provenance_check",
    name: "Provenance Check",
    type: "Ingestion-side allowlist",
    mechanism: "Rejects any document whose source URI is not on the trusted-sources allowlist (internal-policies/ prefix). All 8 poisoned docs use source '(attack — pre-canned)' which doesn't match — blocked before retrieval.",
    pros: "Deterministic, zero latency. Catches every attack without reading the document content.",
    cons: "Only as strong as your source registry. An attacker who can inject via a trusted source path bypasses this entirely. No defense against insider threats.",
    tryTab: "attack",
    owasp: "LLM03",
  },
  {
    id: "adversarial_filter",
    name: "Adversarial Filter",
    type: "Ingestion-side content scan",
    mechanism: "Scans document text for known injection patterns: broadcast ATTENTION calls, fake authority assertions ('AS APPROVED BY'), year-pinned supersession claims, and policy-skip directives. Catches RP.1, RP.2, RP.3.",
    pros: "Cheap, deterministic. Catches overt injection language before the model is ever called.",
    cons: "Keyword lists lag real attacks. RP.4 (citation spoof), RP.5 (keyword stuffing), and RP.6 (subtle multi-doc) all slip past — by design.",
    tryTab: "attack",
    owasp: "LLM01",
  },
  {
    id: "retrieval_diversity",
    name: "Retrieval Diversity",
    type: "Post-retrieval rerank",
    mechanism: "Blocks retrieval if any single source URI contributes more than 1 document to the top-k. Catches RP.6 (Multi-Doc Consensus) whose 3 sibling docs all share the same source. Single-doc attacks pass.",
    pros: "Effective specifically against multi-doc consensus attacks. No LLM call cost.",
    cons: "Narrow scope. RP.1–RP.5 are single-doc attacks; only RP.6's sibling docs cluster. Easy to evade by using different source URIs per sibling doc.",
    tryTab: "attack",
    owasp: "LLM04",
  },
  {
    id: "output_grounding",
    name: "Output Grounding",
    type: "Post-LLM citation validation",
    mechanism: "Scans the model's response for doc-ID-shaped tokens and rejects the response if any cited ID isn't in the active corpus. Catches RP.4's fabricated NX-LEGAL-2024-00x citations.",
    pros: "Final-layer catch — works even when every other defense is bypassed, as long as the model cites fabricated IDs.",
    cons: "Useless if the attack succeeds without citing fake IDs (RP.1, RP.2, RP.3, RP.5, RP.6). Requires LLM call — full latency cost before the block fires.",
    tryTab: "attack",
    owasp: "LLM05",
  },
];

// Measured on 2026-04-29 against deployed LLaMA 3.3 70B (Groq).
// Source: docs/phase5-matrix.md / docs/phase5-raw.json.
// ✓ = blocked  ✗ = succeeded (leaked)
const COVERAGE = {
  "RP.1": { provenance_check: "✓", adversarial_filter: "✓", retrieval_diversity: "✗", output_grounding: "✗" },
  "RP.2": { provenance_check: "✓", adversarial_filter: "✓", retrieval_diversity: "✗", output_grounding: "✗" },
  "RP.3": { provenance_check: "✓", adversarial_filter: "✓", retrieval_diversity: "✗", output_grounding: "✗" },
  "RP.4": { provenance_check: "✓", adversarial_filter: "✗", retrieval_diversity: "✗", output_grounding: "✓" },
  "RP.5": { provenance_check: "✓", adversarial_filter: "✗", retrieval_diversity: "✗", output_grounding: "✗" },
  "RP.6": { provenance_check: "✓", adversarial_filter: "✗", retrieval_diversity: "✓", output_grounding: "✗" },
};

function renderDefensesTab(container) {
  const attacks = state.attacks || [];

  const cellClass = (v) => v === "✓" ? "cell-catches" : v === "✗" ? "cell-misses" : "cell-partial";

  const matrixRows = attacks.map((a) => {
    const row = COVERAGE[a.id] || {};
    const cells = DEFENSES.map((d) =>
      `<td class="${cellClass(row[d.id])}">${row[d.id] || "—"}</td>`
    ).join("");
    return `<tr>
      <td class="attack-id">${escapeHtml(a.id)}</td>
      <td>${escapeHtml(a.name)}</td>
      ${cells}
    </tr>`;
  }).join("");

  const detailCards = DEFENSES.map((d) => `
    <article class="card">
      <div class="card-eyebrow">${escapeHtml(d.type)}</div>
      <h3 class="card-title">${escapeHtml(d.name)}</h3>
      <div class="card-body">
        <p>${escapeHtml(d.mechanism)}</p>
        <p><strong>Pros:</strong> ${escapeHtml(d.pros)}</p>
        <p><strong>Cons:</strong> ${escapeHtml(d.cons)}</p>
        <p class="muted" style="font-size:var(--text-xs);">OWASP: <code>${escapeHtml(d.owasp)}</code></p>
      </div>
      <div style="margin-top:var(--space-3);">
        <button class="btn btn-secondary" style="font-size:var(--text-xs);" data-jump-tab="${escapeHtml(d.tryTab)}" data-jump-defense="${escapeHtml(d.id)}">
          Try this defense on the RAG Poisoning tab →
        </button>
      </div>
    </article>
  `).join("");

  setHtml(container, `
    <section class="card">
      <h2 class="card-title">Defense Matrix</h2>
      <div class="card-body muted" style="font-size:var(--text-sm);margin-bottom:var(--space-3);">
        <strong>Measured</strong> against deployed LLaMA 3.3 70B (Groq) on 2026-04-29.
        ✓ defense blocked · ✗ attack succeeded.
        <br>Headline: <code>provenance_check</code> 6/6 · <code>adversarial_filter</code> 3/6 · <code>retrieval_diversity</code> 1/6 · <code>output_grounding</code> 1/6.
        With all four defenses enabled, provenance_check short-circuits everything (6/6). Full data: <code>docs/phase5-raw.json</code>.
      </div>
      <div style="overflow-x:auto;">
        <table class="defense-matrix">
          <thead>
            <tr>
              <th>Attack</th>
              <th>Name</th>
              ${DEFENSES.map((d) => `<th>${escapeHtml(d.name)}</th>`).join("")}
            </tr>
          </thead>
          <tbody>${matrixRows}</tbody>
        </table>
      </div>
      <p class="muted" style="font-size:var(--text-xs);margin-top:var(--space-3);">
        Key finding: RP.5 (Embedding Adjacency) is caught by <code>provenance_check</code> ALONE — keyword stuffing leaves no obvious injection pattern, no fake citations, no sibling docs. Only source-based filtering catches it. This is the lab's sharpest pedagogical point.
      </p>
    </section>

    <h2 class="card-title" style="margin-top:var(--space-6);">Defense Details</h2>
    <div class="defense-detail">${detailCards}</div>
  `);

  for (const btn of container.querySelectorAll("[data-jump-tab]")) {
    btn.addEventListener("click", () => {
      const tabId = btn.dataset.jumpTab;
      const defenseId = btn.dataset.jumpDefense;
      if (defenseId) {
        sessionStorage.setItem("data-poisoning:preselect-defense", defenseId);
      }
      setActiveTab(tabId);
    });
  }
}
