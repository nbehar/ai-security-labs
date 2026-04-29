/**
 * corpus_browser.js — Renders the Corpus Browser tab.
 *
 * Shows all corpus documents (legitimate + attack) with:
 *   - Filter by department or kind (All / HR / IT / Finance / Legal / Attacks)
 *   - Query selector to surface cosine similarity scores from the last attack
 *   - Click-to-expand full document body preview
 *
 * XSS posture: all interpolated values escaped via escapeHtml.
 */

import { fetchJSON, escapeHtml } from "/static/js/core.js";
import { setHtml } from "/static/js/app.js";

const DEPARTMENTS = ["All", "Finance", "HR", "IT", "Legal", "Attacks"];

export async function renderCorpusBrowserTab(container, state) {
  setHtml(container, `
    <div class="card"><div class="card-body muted">
      <span class="spinner"></span> Loading corpus…
    </div></div>
  `);

  let docs = state.corpus;
  if (!docs) {
    try {
      const data = await fetchJSON("/api/corpus");
      docs = data.documents;
      state.corpus = docs;
    } catch (e) {
      setHtml(container, `<div class="banner banner-danger">Could not load corpus: ${escapeHtml(e.message)}</div>`);
      return;
    }
  }

  renderBrowser(container, docs, state);
}

function renderBrowser(container, docs, state) {
  const localState = {
    filter: "All",
    selectedDocId: null,
    queryId: null,
    simScores: {},
    loadingDoc: false,
  };

  const filterBtns = DEPARTMENTS.map((dept) =>
    `<button class="corpus-filter-btn" data-filter="${escapeHtml(dept)}" aria-pressed="${dept === "All" ? "true" : "false"}">${escapeHtml(dept)}</button>`
  ).join("");

  const queries = state.queries || [];
  const queryOptions = [
    `<option value="">— Show similarity scores for query —</option>`,
    ...queries.map((q) => `<option value="${escapeHtml(q.id)}">${escapeHtml(q.id)}: ${escapeHtml(q.text)}</option>`),
  ].join("");

  setHtml(container, `
    <section class="card">
      <h2 class="card-title">NexaCore Knowledge Hub Corpus</h2>
      <div class="card-body muted" style="font-size:var(--text-sm);margin-bottom:var(--space-3);">
        ${docs.length} documents total — ${docs.filter(d => d.kind === "legitimate").length} legitimate + ${docs.filter(d => d.kind === "attack").length} poisoned attack docs.
        Red border = poisoned document (ATTACK badge). Click any document to read its full content.
      </div>

      <div class="corpus-controls">
        <div style="display:flex;gap:var(--space-2);flex-wrap:wrap;" role="group" aria-label="Filter by department">
          ${filterBtns}
        </div>
        <select id="query-select" class="corpus-query-select" aria-label="Select query to show similarity scores">
          ${queryOptions}
        </select>
      </div>

      <div id="corpus-grid" class="corpus-grid"></div>
    </section>

    <div id="doc-detail"></div>
  `);

  const gridEl   = container.querySelector("#corpus-grid");
  const detailEl = container.querySelector("#doc-detail");
  const querySelect = container.querySelector("#query-select");

  // Pre-load similarity scores for the last-run attack query, if available
  const lastResult = getLastResult(state);
  if (lastResult && lastResult.retrieval) {
    const resultsByDocId = {};
    for (const r of (lastResult.retrieval.results || [])) {
      resultsByDocId[r.doc_id] = r.score;
    }
    localState.simScores = resultsByDocId;
    if (lastResult.query) {
      const matchedQuery = queries.find((q) => q.text === lastResult.query);
      if (matchedQuery) localState.queryId = matchedQuery.id;
    }
  }

  function filteredDocs() {
    if (localState.filter === "All") return docs;
    if (localState.filter === "Attacks") return docs.filter((d) => d.kind === "attack");
    return docs.filter((d) => d.department === localState.filter);
  }

  function renderGrid() {
    const visible = filteredDocs();
    if (visible.length === 0) {
      setHtml(gridEl, `<div class="muted" style="padding:var(--space-4);">No documents match this filter.</div>`);
      return;
    }

    const cards = visible.map((doc) => {
      const isAttack = doc.kind === "attack";
      const simScore = localState.simScores[doc.id];
      const simHtml = simScore !== undefined
        ? `<div class="corpus-sim-score">cosine: ${Number(simScore).toFixed(3)}</div>`
        : "";

      return `
        <div class="corpus-doc-card${isAttack ? " kind-attack" : ""}"
          data-doc-id="${escapeHtml(doc.id)}"
          tabindex="0"
          role="button"
          aria-selected="${localState.selectedDocId === doc.id ? "true" : "false"}"
          aria-label="${escapeHtml(isAttack ? "Attack doc" : "Legitimate doc")}: ${escapeHtml(doc.title || doc.id)}">
          <div class="corpus-doc-header">
            <div class="corpus-doc-title">${escapeHtml(doc.title || doc.id)}</div>
            <span class="kind-badge ${isAttack ? "kind-badge-attack" : "kind-badge-legit"}">${isAttack ? "ATTACK" : "LEGIT"}</span>
          </div>
          <div class="corpus-doc-meta">
            ${escapeHtml(doc.department || "")}
            ${doc.word_count ? `· ${doc.word_count} words` : ""}
            ${doc.attack_id ? `· <span style="color:var(--color-danger-light);">${escapeHtml(doc.attack_id)}</span>` : ""}
          </div>
          <div class="corpus-doc-preview">${escapeHtml(doc.preview || "")}</div>
          ${simHtml}
        </div>
      `;
    }).join("");

    setHtml(gridEl, cards);

    for (const card of gridEl.querySelectorAll(".corpus-doc-card")) {
      card.addEventListener("click", () => openDoc(card.dataset.docId));
      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") openDoc(card.dataset.docId);
      });
    }
  }

  async function openDoc(docId) {
    if (localState.selectedDocId === docId) {
      // Toggle close
      localState.selectedDocId = null;
      setHtml(detailEl, "");
      for (const c of gridEl.querySelectorAll(".corpus-doc-card")) {
        c.setAttribute("aria-selected", "false");
      }
      return;
    }

    localState.selectedDocId = docId;
    for (const c of gridEl.querySelectorAll(".corpus-doc-card")) {
      c.setAttribute("aria-selected", c.dataset.docId === docId ? "true" : "false");
    }

    setHtml(detailEl, `<div class="corpus-doc-detail"><span class="spinner"></span> Loading…</div>`);

    try {
      const doc = await fetchJSON(`/api/corpus/${encodeURIComponent(docId)}`);
      const isAttack = doc.kind === "attack";
      setHtml(detailEl, `
        <div class="corpus-doc-detail" style="${isAttack ? "border-left:3px solid var(--color-danger);" : ""}">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:var(--space-2);">
            <h3>${escapeHtml(doc.title || doc.id)}</h3>
            <span class="kind-badge ${isAttack ? "kind-badge-attack" : "kind-badge-legit"}">${isAttack ? "ATTACK" : "LEGIT"}</span>
          </div>
          <div class="corpus-doc-detail-meta">
            id: ${escapeHtml(doc.id)} · kind: ${escapeHtml(doc.kind)}
          </div>
          <pre>${escapeHtml(doc.body_markdown || "")}</pre>
        </div>
      `);
    } catch (e) {
      setHtml(detailEl, `<div class="banner banner-danger">Could not load document: ${escapeHtml(e.message)}</div>`);
    }
  }

  async function loadSimilarityForQuery(queryId) {
    if (!queryId) {
      localState.simScores = {};
      localState.queryId = null;
      renderGrid();
      return;
    }
    localState.queryId = queryId;
    // Run a no-defense attack for the target query of the selected query's attack, just to get retrieval scores.
    // Find an attack that targets this query:
    const atk = (state.attacks || []).find((a) => a.target_query_id === queryId);
    if (!atk) { renderGrid(); return; }

    try {
      const fd = new FormData();
      fd.append("attack_id", atk.id);
      fd.append("doc_source", "canned");
      fd.append("defenses", JSON.stringify([]));
      fd.append("participant_name", "corpus-browser");
      const result = await fetchJSON("/api/attack", { method: "POST", body: fd });
      const scores = {};
      for (const r of (result.retrieval && result.retrieval.results) || []) {
        scores[r.doc_id] = r.score;
      }
      localState.simScores = scores;
    } catch {
      localState.simScores = {};
    }
    renderGrid();
  }

  // Filter buttons
  for (const btn of container.querySelectorAll(".corpus-filter-btn")) {
    btn.addEventListener("click", () => {
      localState.filter = btn.dataset.filter;
      for (const b of container.querySelectorAll(".corpus-filter-btn")) {
        b.setAttribute("aria-pressed", b.dataset.filter === localState.filter ? "true" : "false");
      }
      renderGrid();
    });
  }

  querySelect.addEventListener("change", () => {
    loadSimilarityForQuery(querySelect.value);
  });

  // Pre-select the last query if we have data
  if (localState.queryId) {
    querySelect.value = localState.queryId;
  }

  renderGrid();
}

function getLastResult(state) {
  // We don't persist last result in state directly; this just returns null.
  // The similarity scores come from the last runAttack in attack_runner.
  // For the corpus browser's query selector, we re-run a canned attack.
  return null;
}
