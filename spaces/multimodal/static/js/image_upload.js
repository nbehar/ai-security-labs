/**
 * image_upload.js — File picker + client-side validation for upload mode.
 *
 * Per api_spec.md and frontend_spec.md:
 *   - PNG or JPEG only (Content-Type AND magic-bytes — server enforces too)
 *   - ≤4MB
 *   - Processed in-memory; never written to disk
 *
 * The client-side check is for UX (immediate feedback). Server-side
 * validation in app.py:_validate_image_bytes is the authoritative gate.
 */

import { escapeHtml } from "/static/js/core.js";
import { setHtml } from "/static/js/app.js";

const MAX_BYTES = 4 * 1024 * 1024;
const PNG_HEAD = [0x89, 0x50, 0x4e, 0x47];
const JPEG_HEAD = [0xff, 0xd8, 0xff];

export function renderUploadPanel(container, { onSelect, onError } = {}) {
  setHtml(container, `
    <div class="upload-panel">
      <label for="upload-input" class="muted" style="display:block;margin-bottom:var(--space-2);">
        Upload your own attack image (PNG or JPEG, ≤4MB)
      </label>
      <input type="file" id="upload-input" accept="image/png,image/jpeg">
      <div class="upload-warning">
        Uploaded images are processed in-memory only and discarded after the request.
      </div>
      <img id="upload-preview" class="upload-preview hidden" alt="Upload preview">
      <div id="upload-error" class="muted" style="margin-top:var(--space-2);color:var(--color-danger-light);"></div>
    </div>
  `);

  const input = container.querySelector("#upload-input");
  const preview = container.querySelector("#upload-preview");
  const errBox = container.querySelector("#upload-error");

  input.addEventListener("change", async () => {
    errBox.textContent = "";
    preview.classList.add("hidden");
    const file = input.files && input.files[0];
    if (!file) return;

    if (!["image/png", "image/jpeg"].includes(file.type)) {
      const msg = `File must be PNG or JPEG (got ${file.type || "unknown"})`;
      errBox.textContent = msg;
      if (onError) onError(msg);
      input.value = "";
      return;
    }
    if (file.size > MAX_BYTES) {
      const msg = `File exceeds 4MB cap (${(file.size / 1024 / 1024).toFixed(2)}MB)`;
      errBox.textContent = msg;
      if (onError) onError(msg);
      input.value = "";
      return;
    }

    const buf = await file.arrayBuffer();
    if (!matchesMagicBytes(buf)) {
      const msg = "File bytes don't look like a real PNG or JPEG (magic-bytes mismatch).";
      errBox.textContent = msg;
      if (onError) onError(msg);
      input.value = "";
      return;
    }

    const url = URL.createObjectURL(file);
    preview.src = url;
    preview.classList.remove("hidden");
    if (onSelect) {
      onSelect({ file, previewUrl: url, name: file.name, size: file.size });
    }
  });
}

function matchesMagicBytes(arrayBuffer) {
  const head = new Uint8Array(arrayBuffer.slice(0, 4));
  const isPng = PNG_HEAD.every((b, i) => head[i] === b);
  const isJpeg = JPEG_HEAD.every((b, i) => head[i] === b);
  return isPng || isJpeg;
}
