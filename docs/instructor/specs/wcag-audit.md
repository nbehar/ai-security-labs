# Spec: WCAG 2.1 AA Audit + Remediation

**Scope:** All deployed lab spaces + exam-admin
**Category:** Compliance — California AB 434 / Section 508
**Issue:** #33

---

## Goal

Bring all AI Security Labs spaces to WCAG 2.1 Level AA compliance and produce a VPAT (Voluntary Product Accessibility Template) that satisfies California CC procurement requirements.

---

## Audit Scope

Run the audit against all five currently-deployed spaces (OWASP Top 10, Blue Team, Red Team, Detection & Monitoring, exam-admin) plus the framework CSS/JS. Multimodal and Data Poisoning audited before their deploy.

---

## Known Issues (pre-audit findings)

| ID | Location | Issue | WCAG Criterion | Priority |
|----|----------|-------|---------------|----------|
| A1 | D2 `anomaly_dashboard.js` | SVG sparkline charts have no `<title>` or `aria-label` | 1.1.1 Non-text Content | MUST fix |
| A2 | All spaces | Dark-only theme; no way to override contrast or switch to light mode | 1.4.3 Contrast, 1.4.11 Non-text Contrast | MUST fix |
| A3 | All spaces | Tab panels lack `role="tablist"`, `role="tab"`, `aria-selected`, `aria-controls` | 4.1.2 Name/Role/Value | MUST fix |
| A4 | D3 `output_sanitizer.js` | Rule editor textarea has no visible label | 1.3.1 Info and Relationships | MUST fix |
| A5 | All spaces | Keyboard navigation order through modals/cards not tested | 2.1.1 Keyboard | Audit required |
| A6 | exam-admin `admin.js` | Drag-drop upload zones have no keyboard alternative | 2.1.1 Keyboard | MUST fix |
| A7 | All spaces | Error messages use color only (no icon/text pattern) | 1.4.1 Use of Color | MUST fix |
| A8 | Leaderboard table | No `<caption>` or `summary` attribute | 1.3.1 | Should fix |

---

## Steps

1. **Automated scan** — run `axe-core` via Puppeteer against each space URL; capture report as JSON artifact
2. **Manual keyboard audit** — tab through all interactive elements in each space; document focus order and any traps
3. **Screen reader test** — test with VoiceOver (macOS) on Chrome and Safari; document all unlabeled elements
4. **Contrast check** — run all color pairs (text/bg, icon/bg, border/bg) through WCAG contrast algorithm; flag < 4.5:1 (text) or < 3:1 (UI components)
5. **Remediate MUST-fix items** — implement fixes per the remediation notes below
6. **Author VPAT** — complete the VPAT 2.4 template for WCAG 2.1 Level AA; publish at `/accessibility` route on each space

---

## Remediation Notes

**A1 — SVG charts:** Add `<title id="chart-title-{metric}">` inside each `<svg>` and `aria-labelledby` on the svg element. Alt text format: `"Response length over 24 hours. Attack windows at hours 9, 14, 19."`

**A2 — Theme:** Add a `prefers-color-scheme: light` media query block to `luminex-tokens.css` with adjusted token values. Optionally add a manual toggle button in the nav. The dark theme remains default.

**A3 — Tab panels:** Update `renderTabs()` in `framework/static/js/core.js` to output correct ARIA tab roles. This is a single fix that propagates to all spaces via deploy.

**A4 — Rule editor:** Add `<label for="rule-input">WAF rule (e.g. BLOCK .*):</label>` in `templates/index.html` D3 section.

**A6 — Upload zones:** Add `<button>` fallback inside each upload zone: `<button type="button" class="upload-zone__btn">Choose file</button>` that triggers the hidden `<input type="file">`.

**A7 — Error states:** Prepend error messages with an icon character (✕) and add `role="alert"` to error divs so screen readers announce them immediately.

---

## Expected Outputs

- Automated axe-core report for each space (JSON + HTML)
- Manual keyboard audit checklist (markdown, one per space)
- Completed VPAT 2.4 document (published at `/accessibility`)
- All MUST-fix items resolved before any summative exam offering

---

## Acceptance Checks

- [ ] `axe-core` scan returns zero critical or serious violations on each space
- [ ] All interactive elements reachable and operable by keyboard alone
- [ ] All SVG charts have programmatic text alternatives
- [ ] Color is never the sole means of conveying information
- [ ] VPAT 2.4 published at `/accessibility` on exam-admin space
- [ ] `prefers-color-scheme: light` renders legible UI at 4.5:1+ contrast

---

## What Could Go Wrong

- **axe-core misses dynamic content** — SPA tab panels and dynamically injected cards may not be in the DOM at scan time. Mitigation: run axe-core after simulating tab clicks via Puppeteer.
- **VPAT scope creep** — VPAT for all 10 spaces is a large document. Mitigation: produce one VPAT for the platform (covering the framework + common patterns) and note space-specific deviations.
