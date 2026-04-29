/**
 * document_upload.js — Document upload panel for the RAG Poisoning tab.
 *
 * Accepts Markdown (.md), plain text (.txt), or PDF (.pdf).
 * Client-side validation: 16KB cap, 1500-word cap, type check.
 * Never persists — hands the File object up to attack_runner.js.
 *
 * XSS posture: file content is previewed via escapeHtml; file names escaped.
 */

import { escapeHtml } from "/static/js/core.js";
import { setHtml } from "/static/js/app.js";

const MAX_BYTES = 16 * 1024;
const MAX_WORDS = 1500;
const ALLOWED_TYPES = new Set(["text/markdown", "text/plain", "application/pdf"]);
const ALLOWED_EXTS  = new Set([".md", ".txt", ".pdf"]);

/**
 * Render the document upload panel into `host`.
 *
 * @param {HTMLElement} host
 * @param {{ onSelect: (content: string, file: File) => void, onError: (msg: string) => void }} opts
 */
export function renderDocUploadPanel(host, { onSelect, onError }) {
  setHtml(host, `
    <div class="upload-panel">
      <label for="doc-file-input" style="display:block;font-size:var(--text-sm);color:var(--color-text-primary);margin-bottom:var(--space-2);">
        Upload a poisoned document (.md, .txt, or .pdf)
      </label>
      <input type="file" id="doc-file-input" accept=".md,.txt,.pdf,text/markdown,text/plain,application/pdf"
        aria-label="Upload poisoned document file">
      <p class="upload-warning">
        Max 16 KB · 1,500 words · Markdown / plain text / PDF only.
        Content is processed in-memory only — never stored.
      </p>
      <div id="upload-preview-area"></div>
    </div>
  `);

  const input = host.querySelector("#doc-file-input");
  const previewArea = host.querySelector("#upload-preview-area");

  input.addEventListener("change", async () => {
    const file = input.files && input.files[0];
    if (!file) return;

    const ext = ("." + file.name.split(".").pop()).toLowerCase();
    const mime = file.type.toLowerCase();

    if (!ALLOWED_EXTS.has(ext) || !ALLOWED_TYPES.has(mime)) {
      onError(`File type not allowed. Use .md, .txt, or .pdf.`);
      setHtml(previewArea, "");
      return;
    }

    if (file.size > MAX_BYTES) {
      onError(`File too large (${(file.size / 1024).toFixed(1)} KB). Maximum is 16 KB.`);
      setHtml(previewArea, "");
      return;
    }

    let text = "";
    if (ext === ".pdf" || mime === "application/pdf") {
      // PDF: let the backend handle extraction. Preview filename only.
      text = `[PDF: ${file.name} — text will be extracted server-side]`;
      setHtml(previewArea, `<div class="upload-preview">${escapeHtml(text)}</div>`);
      onSelect(null, file);
      return;
    }

    text = await readAsText(file);
    const wordCount = text.trim().split(/\s+/).filter(Boolean).length;
    if (wordCount > MAX_WORDS) {
      onError(`Document too long (${wordCount} words). Maximum is ${MAX_WORDS} words.`);
      setHtml(previewArea, "");
      return;
    }

    const preview = text.substring(0, 400);
    setHtml(previewArea, `
      <div class="upload-preview">${escapeHtml(preview)}${text.length > 400 ? "\n…" : ""}</div>
      <p class="upload-warning">${escapeHtml(file.name)} · ${wordCount} words · ${(file.size / 1024).toFixed(1)} KB</p>
    `);
    onSelect(text, file);
  });
}

function readAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result || "");
    reader.onerror = () => reject(new Error("Could not read file."));
    reader.readAsText(file, "utf-8");
  });
}
