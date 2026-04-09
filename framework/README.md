# Shared Framework

Common code used by all AI Security Lab workshops. Copied into each Space's build context by `scripts/deploy.sh`.

## Files

| File | Purpose | Spaces that use it |
|------|---------|-------------------|
| `static/css/styles.css` | Dark theme, layout, components | All |
| `static/js/core.js` | DOM helpers, fetchJSON, tab rendering, briefing cards, leaderboard, info page | All |
| `scoring.py` | Score calculation + Leaderboard class | Blue Team, Red Team |
| `groq_client.py` | Groq API client wrapper | All |
| `scanner.py` | Defense tools (Prompt Guard, LLM Guard, etc.) | OWASP workshop |
| `templates/base.html` | Jinja2 HTML shell with hero, tabs, footer | Available for new Spaces |

## How it works

1. Framework files are the **source of truth** for shared code
2. `scripts/deploy.sh` copies framework files into each Space before pushing to HF
3. Space-specific files (`app.js`, `app.py`, `challenges.py`) are never overwritten
4. CSS is always overwritten (framework CSS is canonical)
5. `core.js` is copied alongside space-specific `app.js` (imported via ES modules)

## Adding shared functionality

1. Add the code to the appropriate framework file
2. Run `./scripts/deploy.sh <space-name>` for each Space that needs it
3. Update this README

## Creating a new Space

1. `mkdir -p spaces/my-new-lab/static/js spaces/my-new-lab/static/css spaces/my-new-lab/templates`
2. Create `app.py`, `challenges.py`, `app.js` (space-specific)
3. In `app.js`: `import { $, $$, escapeHtml, fetchJSON, renderTabs, renderLevelBriefing, renderLeaderboard, renderInfoPage } from "./core.js";`
4. `./scripts/deploy.sh my-new-lab`
