/**
 * image_gallery.js — Thumbnail grid for canned attack + legitimate images.
 *
 * Backend: GET /api/images/{attack_id} returns the matched attack image and
 * the lab-aware legitimate-image set for false-positive checking.
 *
 * Selection model: a single thumbnail is selected at a time (aria-selected="true").
 * The caller passes onSelect(item) and reads the latest selection from the
 * GalleryController.getSelection() helper.
 *
 * XSS posture: every dynamic value is escaped via escapeHtml; setHtml uses
 * Range.createContextualFragment per the security hook convention.
 */

import { fetchJSON, escapeHtml } from "/static/js/core.js";
import { setHtml } from "/static/js/app.js";

export async function buildGalleryFor(attackId) {
  return fetchJSON(`/api/images/${encodeURIComponent(attackId)}`);
}

export function renderGallery(container, payload, { onSelect } = {}) {
  const items = [
    payload.attack_image,
    ...(payload.legitimate_images || []),
  ];

  const html = items.map((item, idx) => {
    const isAttack = item.kind === "attack";
    const kindLabel = isAttack ? "Attack" : "Legit";
    const kindClass = isAttack ? "kind-badge-attack" : "kind-badge-legit";
    const stars = isAttack ? "★" : "";

    return `
      <button type="button"
              class="gallery-item"
              role="option"
              aria-selected="${idx === 0 ? "true" : "false"}"
              data-filename="${escapeHtml(item.filename)}"
              data-url="${escapeHtml(item.url)}"
              data-kind="${escapeHtml(item.kind)}">
        <span class="kind-badge ${kindClass}">${escapeHtml(kindLabel)}</span>
        ${stars ? `<span class="difficulty-badge" aria-hidden="true">${stars}</span>` : ""}
        <img src="${escapeHtml(item.url)}" alt="${escapeHtml(item.alt || item.filename)}" loading="lazy">
        <div class="gallery-item-meta">
          <div class="gallery-item-id">${escapeHtml(item.filename)}</div>
          <div class="gallery-item-desc">${escapeHtml(item.alt || "")}</div>
        </div>
      </button>
    `;
  }).join("");

  setHtml(container, `<div class="gallery" role="listbox" aria-label="Attack and legitimate images">${html}</div>`);

  const buttons = [...container.querySelectorAll(".gallery-item")];
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach((b) => b.setAttribute("aria-selected", "false"));
      btn.setAttribute("aria-selected", "true");
      if (onSelect) {
        onSelect({
          filename: btn.dataset.filename,
          url: btn.dataset.url,
          kind: btn.dataset.kind,
        });
      }
    });
  });

  // Default-select the attack image (first) so a click on Run Attack works
  // immediately even if the student hasn't tapped a thumbnail yet.
  if (items.length && onSelect) {
    onSelect({
      filename: items[0].filename,
      url: items[0].url,
      kind: items[0].kind,
    });
  }
}
