# Instructor Support Package — CCC 200-Level Readiness

Tracking issue: **#37**

This directory tracks the features, content, and compliance work required for a California Community College instructor to use AI Security Labs as a graded, ADA-compliant 200-level course.

The lab mechanic (formative + summative assessment) is already built. This package fills the gaps between "workshop environment" and "deployable course."

---

## Work Items

| # | Feature | Spec | Category | Priority | GitHub Issue |
|---|---------|------|----------|----------|--------------|
| 1 | ADA Accommodation Controls | [spec](specs/ada-accommodations.md) | exam-admin | **Blocker** | #29 |
| 2 | Class Roster Dashboard | [spec](specs/class-dashboard.md) | exam-admin | **Blocker** | #30 |
| 3 | Web-Based Token Generator | [spec](specs/token-generator-ui.md) | exam-admin | UX | #31 |
| 4 | Instructor Preview Mode | [spec](specs/preview-mode.md) | platform | UX | #32 |
| 5 | WCAG 2.1 AA Audit + Remediation | [spec](specs/wcag-audit.md) | platform | Compliance | #33 |
| 6 | Facilitator Guides (3 live labs) | [spec](specs/facilitator-guide.md) | content | Content | #34 |
| 7 | Course Materials Package | [spec](specs/course-materials.md) | content | Content | #35 |
| 8 | Additional Assessment Types | [spec](specs/additional-assessments.md) | assessment | Pedagogy | #36 |

---

## Definition of Done (Package-Level)

Package is "instructor ready" for a Fall 2026 CCC section when all of the following are true:

- [ ] #29 ADA accommodation controls live in exam-admin
- [ ] #30 Class roster dashboard live in exam-admin
- [ ] #33 WCAG 2.1 AA audit complete + all MUST-fix items resolved
- [ ] #34 Facilitator guides published for OWASP Top 10, Blue Team, Red Team
- [ ] #35 Sample syllabus + 16-week pacing guide + pre/post diagnostic published
- [ ] #31 Web token generator live (no CLI required for instructors)

---

## California-Specific Requirements

- **Title 5 § 55204** — Regular Effective Contact requirement for DE sections; facilitator guides must note synchronous check-in points.
- **AB 434** — WCAG 2.1 AA compliance required for all state-funded instructional technology.
- **FERPA** — Student IDs in tokens and receipts must be LMS usernames (not legal names). Already enforced by token schema.
- **ACCJC Program Review** — Pre/post diagnostic learning gain data is required evidence for SLO assessment cycles.
- **Section 504 / ADA** — Exam time extensions and attempt resets are legally required accommodation mechanisms.
