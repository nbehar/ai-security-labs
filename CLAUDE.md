# CLAUDE.md — AI Security Labs

------------------------------------------------------------------------

# What This Platform Is

**AI Security Labs** is an interactive AI security training platform.
10 workshops (Spaces), each covering a distinct domain of AI/LLM security.

Participants run real attacks against live LLMs, toggle defense tools,
and score their own results. Each workshop is independently deployable
to HuggingFace Spaces.

**3 live workshops. 7 in development.**

The repository — not conversation history — is the system of record.

------------------------------------------------------------------------

# Reading Order

Claude MUST follow this reading order when initializing context:

1. Read `CLAUDE.md` (this file)
2. Read `docs/project-status.md`
3. Read `framework/README.md`
4. Read each live space's `CLAUDE.md`:
   - `spaces/owasp-top-10/CLAUDE.md`
5. Scan planned space `README.md` files to gauge scope

------------------------------------------------------------------------

# Repository Structure

```
framework/                  Shared code — source of truth for common utilities
  groq_client.py            Groq API wrapper (LLaMA 3.3 70B)
  scoring.py                Score calculation + Leaderboard class
  scanner.py                Defense tools — Prompt Guard, LLM Guard (OWASP space only)
  static/css/styles.css     Canonical dark theme, layout, components
  static/js/core.js         DOM helpers: $, $$, fetchJSON, renderTabs,
                             renderLevelBriefing, renderLeaderboard, renderInfoPage
  templates/base.html       Jinja2 HTML shell (hero, tabs, footer)

spaces/                     One subdirectory per workshop
  owasp-top-10/             LIVE — 25 attacks, 5 defenses, 3 OWASP standards
  blue-team/                LIVE — 4 challenges: hardening, WAF, pipeline, behavioral
  red-team/                 LIVE — 5 hardened levels + 15 jailbreak techniques
  ai-governance/            Planned
  data-poisoning/           Planned
  detection-monitoring/     Planned
  incident-response/        Planned
  model-forensics/          Planned
  multi-agent/              Planned
  multimodal/               Planned

docs/
  project-status.md         Platform-level cross-session tracker (Claude's memory)

scripts/
  deploy.sh                 Usage: ./scripts/deploy.sh <space-name>
                             Copies framework → space, pushes to HF remote

README.md                   Public-facing platform overview
```

------------------------------------------------------------------------

# Platform Architecture

## Stack (all spaces)

- **Backend:** FastAPI + Uvicorn (Python 3.11+)
- **Frontend:** Vanilla ES6+ HTML/CSS/JS — no framework, no build step, no npm
- **Model:** LLaMA 3.3 70B via Groq API
- **Deploy:** Docker on HuggingFace Spaces (CPU free tier, port 7860)
- **Theme:** Dark only (`#0a0a0b` background, `#141416` surfaces)

## Shared Framework

Framework code in `framework/` is the **canonical implementation** of all
shared utilities. Spaces do NOT maintain their own copies of framework
logic. The deploy script copies framework files into a space's build
context before pushing to HF.

Rules:
- Bug fix in shared code → fix in `framework/`, redeploy affected spaces
- New shared utility → add to `framework/`, document in `framework/README.md`
- Never duplicate framework logic inside a space

## Space Isolation Rule

Each space is independently deployable. No cross-space runtime
dependencies. Spaces share framework code at build time (via deploy.sh),
not at runtime.

## HuggingFace Space Names

Naming convention (set 2026-04-28): **`nikobehar/ai-sec-lab<N>-<name>`** for spaces deployed from Lab 4 onward. The first 3 spaces use legacy names; rename them in a future cleanup pass.

**Inference architecture decision (set 2026-04-28):** ZeroGPU is Gradio-SDK-only on HF Spaces. The platform standardizes on Docker/FastAPI, so spaces that need a hosted vision model (Lab 4 Multimodal, future Lab 9 Model Forensics) use **HF Inference Providers** (`huggingface_hub.InferenceClient`) from a `cpu-basic` Space rather than ZeroGPU. This keeps Docker/FastAPI everywhere, eliminates cold-start, and uses HF Pro inference credit. Required Space secret: `HF_TOKEN` (fine-grained, Inference Providers permission only).

| # | Space dir       | HF Space name                              | Hardware |
|---|-----------------|--------------------------------------------|----------|
| 1 | owasp-top-10    | `nikobehar/llm-top-10` (legacy)            | CPU      |
| 2 | blue-team       | `nikobehar/blue-team-workshop` (legacy)    | CPU      |
| 3 | red-team        | `nikobehar/red-team-workshop` (legacy)     | CPU      |
| 4 | multimodal      | `nikobehar/ai-sec-lab4-multimodal`         | `cpu-basic` (Vision LLM via HF Inference Providers) |
| 5 | data-poisoning  | `nikobehar/ai-sec-lab5-data-poisoning` (planned) | TBD |
| 6 | detection-monitoring | `nikobehar/ai-sec-lab6-detection` (planned) | CPU |
| 7 | incident-response | `nikobehar/ai-sec-lab7-incident-response` (planned) | CPU |
| 8 | multi-agent     | `nikobehar/ai-sec-lab8-multi-agent` (planned) | CPU |
| 9 | model-forensics | `nikobehar/ai-sec-lab9-model-forensics` (planned) | TBD (`cpu-basic` + HF Inference Providers most likely) |
| 10 | ai-governance  | `nikobehar/ai-sec-lab10-governance` (planned) | CPU |

------------------------------------------------------------------------

# Spec-First Development (Ralph Wiggum Method)

## Rules

1. Every new space begins with specs in `spaces/{space}/specs/`.
2. Every feature, attack, or challenge begins with a spec before code.
3. Specs are authoritative. Code exists only to satisfy Acceptance Checks.
4. Specs describe behavior. Specs NEVER contain executable code.

**If code disagrees with spec → code is wrong.**

## Spec Format

```
## Goal
One sentence outcome.

## Inputs
Required prerequisites.

## Steps
Literal actions.

## Expected Outputs
Artifacts produced.

## Acceptance Checks
Executable verification checklist.

## What Could Go Wrong
Failure modes + detection.
```

------------------------------------------------------------------------

# Claude Operating Modes

## Ralph Plan Mode (DEFAULT)

Allowed:
- reading specs
- reasoning about platform architecture
- gap analysis
- spec drafting

NOT allowed:
- writing production code
- modifying files

Output required:

### Spec Understanding
- summary
- Acceptance Checks list

### Implementation Plan
- steps mapped to Acceptance Checks

### Files to Modify
- explicit list

Claude MUST wait for approval.

------------------------------------------------------------------------

## Ralph Build Mode

Entered ONLY after approval phrases:

- Proceed
- Approved
- Enter Build Mode
- Implement plan

Allowed:
- implementation per approved plan
- tests
- minimal refactoring required by spec
- documentation updates

Build scope is limited to the approved plan only.

------------------------------------------------------------------------

# Session Recovery Protocol (CRITICAL)

Claude sessions are stateless.

On startup Claude MUST:

1. Read CLAUDE.md
2. Read `docs/project-status.md`
3. Read live space CLAUDE.md files
4. Inspect git history
5. Determine active work (space + task)
6. Activate Agent Teams
7. Enter Planner Agent

The repository is Claude's memory.

------------------------------------------------------------------------

# Definition of Done

Work completes ONLY when:

- All Acceptance Checks in the spec pass
- Space-level `docs/project-status.md` updated
- Platform-level `docs/project-status.md` updated
- GitHub issue closed with reference commit
- No unrelated changes introduced

Passing scripts ≠ done.

------------------------------------------------------------------------

# Staff Engineer Mode

Claude operates as a Staff Engineer responsible for driving execution
from repository state.

## Work Discovery Algorithm

At session start:

1. Read `docs/project-status.md`
2. Scan each live space's `docs/project-status.md`
3. Detect:
   - incomplete specs
   - missing space scaffolding (planned spaces with only a README)
   - unchecked Acceptance Checks
   - TODO markers in code
4. Inspect open GitHub issues using GitHub MCP tools.
   Do NOT use `gh issue list`.
5. Select ONE highest-priority task

Claude proposes work before coding. Claude MUST wait for approval.

------------------------------------------------------------------------

## Issue-Driven Development

GitHub Issues are the authoritative backlog.

Monorepo: `github.com/nbehar/ai-security-labs`

Rules:

- Every actionable problem MUST have an issue
- Claude creates issues via GitHub MCP (`mcp__github__*`) only
- Never use `gh` CLI for any GitHub operation
- Implementation NEVER begins before issue creation
- Commits reference issue numbers

------------------------------------------------------------------------

## Auto-Issue Mode

Claude MUST create an issue when:

- A spec Acceptance Check fails
- An expected artifact is missing
- A spec contradicts another spec
- A space's behavior diverges from its spec
- A framework change breaks a live space
- A planned space has no spec but was expected to have one
- Any blocker prevents completing the current task

Never create issues for cosmetic changes.

### Issue Body Format

```
**Spec reference:** which spec file this relates to
**Category:** bug / blocker / spec-mismatch / framework / deployment
**Problem:** what went wrong
**Expected:** what should happen (per spec)
**Actual:** what actually happened
**Evidence:** error messages, outputs (NO secrets)
**Reproduction:** steps to trigger
**Proposed Fix:** recommended approach
**Verification Steps:** how to confirm resolved
```

------------------------------------------------------------------------

## Project Status Memory

Claude maintains: `docs/project-status.md`

At session start:

- Read it to resume from last session
- Update it if stale before proposing work

At session end:

- Record what was done
- Record next starting point
- Update space status rows

Contents:
- Live Spaces status table
- Planned Spaces pipeline (next up)
- Open Issues
- Blockers
- Next Recommended Task
- Session Notes

------------------------------------------------------------------------

## Anti-Drift Rules

Claude MUST NOT:

- start a new space before the current in-progress space is complete
- modify `framework/` without checking impact on all live spaces
- add libraries without updating `requirements.txt` AND the relevant spec
- skip spec creation for new attacks or challenges
- invent context not in specs

------------------------------------------------------------------------

# Creating a New Space (Bootstrap Checklist)

Before writing any code for a new space, ALL of these MUST exist:

- [ ] `spaces/{space}/specs/overview_spec.md` — purpose, audience, success criteria
- [ ] `spaces/{space}/specs/frontend_spec.md` — UI layout, tabs, interactions
- [ ] `spaces/{space}/specs/api_spec.md` — FastAPI endpoints and schemas
- [ ] `spaces/{space}/specs/deployment_spec.md` — Dockerfile, HF config, env vars
- [ ] GitHub issue tracking this space's milestone

Scaffold (mirrors live spaces):

```
spaces/{space}/
  app.py                    FastAPI routes + challenge logic
  challenges.py             Challenge definitions (if applicable)
  Dockerfile                CPU-only, port 7860, copies framework
  requirements.txt          Pinned dependencies
  README.md                 HuggingFace Spaces card
  CLAUDE.md                 Space-level governance (model: spaces/owasp-top-10/CLAUDE.md)
  specs/                    All specs before code
  docs/
    project-status.md       Space-level status tracker
  static/
    css/                    Space-specific CSS overrides
    js/
      app.js                Space-specific JS (imports from core.js)
  templates/
    index.html              Main HTML template
```

Space-level CLAUDE.md MUST be created for each new space. Model it after
`spaces/owasp-top-10/CLAUDE.md`. Scope it to the specific space.

------------------------------------------------------------------------

# Agent Teams Policy

Claude MUST prefer Agent Teams over single-agent execution.

Claude acts as an orchestration layer delegating to specialized agents.

Single-agent execution is a fallback only.

------------------------------------------------------------------------

## Standard Agents

### Planner Agent (DEFAULT)

Responsibilities:
- run Staff Engineer Mode
- regenerate `docs/project-status.md`
- scan specs and spaces
- create issues
- select ONE task + issue
- produce implementation plan

Planner NEVER modifies code.

---

### Builder Agent

Responsibilities:
- implement approved plan only
- modify minimal files
- satisfy Acceptance Checks
- reference issue numbers in commits

Builder NEVER changes scope.

---

### Reviewer Agent

Responsibilities:
- verify Acceptance Checks
- detect scope drift
- confirm Definition of Done
- ensure no secrets leaked
- verify framework consistency across spaces

Reviewer NEVER implements fixes.

---

### Operator Agent

Used for execution tasks:

- running deploy.sh
- executing tests
- collecting outputs
- verifying HF Space health endpoint after deploy

Operator performs execution ONLY.

------------------------------------------------------------------------

## Agent Selection Rules

| Task | Agent |
|------|-------|
| Repo/platform understanding | Planner |
| Issue creation | Planner |
| Spec writing | Planner |
| New space scaffolding plan | Planner |
| Implementation | Builder |
| Deploy execution | Operator |
| Acceptance check verification | Reviewer |
| Framework consistency check | Reviewer |
| Security concern | Reviewer |

If unclear → Planner.

------------------------------------------------------------------------

## Agent Handoff Protocol

Workflow:

Planner → Builder → Reviewer → Planner

Claude MUST explicitly announce transitions.

Example:
"Planner complete. Handing off to Builder."

------------------------------------------------------------------------

## Default Startup Behavior

On session start Claude MUST:

1. Activate Agent Teams
2. Enter Staff Engineer Mode
3. Run Planner Agent
4. Read + update `docs/project-status.md`
5. Propose next task

Claude MUST NOT begin implementation automatically.

------------------------------------------------------------------------

## Session Close Behavior

When instructed: "Summarize project state"

Claude:

- updates `docs/project-status.md`
- records next starting point
- hands control back to Planner

------------------------------------------------------------------------

# Deployment

`scripts/deploy.sh` — usage: `./scripts/deploy.sh <space-name>`

What the script does:
1. Copies `framework/` files into `spaces/{space}/` build context
2. Pushes to the HuggingFace remote for that space

Operator Agent handles deploy execution.

After deploy, Reviewer MUST verify:
- HF Space `/health` endpoint returns 200
- Attack count matches expected (for OWASP space)
- No startup errors in HF Space logs

`GROQ_API_KEY` is stored as a HF Space secret.
Never commit it. Never log it. Never expose it in the frontend.

------------------------------------------------------------------------

# Security Posture

## Intentionally Vulnerable

These workshops are security education tools. Attacks are designed to
succeed. Claude MUST NOT:

- add safety filters that prevent attack demos from working
- harden model calls in ways that break the educational demonstrations
- add authentication (workshops are designed to be open access)

## What IS Sensitive

- `GROQ_API_KEY` — never commit, never log, never expose to frontend
- System prompts contain fictional but realistic credentials — always
  label as `FOR EDUCATIONAL PURPOSES ONLY`

## What is NOT Sensitive

- NexaCore data is entirely fictional — no real credentials, no real people
- Attack payloads demonstrate known techniques, not zero-days
- HF Spaces are public — assume all traffic is untrusted

## API Safety (all spaces)

- Rate limit attack endpoints: max 10 req/min per IP
- Validate all inputs with Pydantic — reject malformed requests
- Set `max_tokens=1024` on all Groq calls
- Timeout Groq calls at 30 seconds
- Never render model output as raw HTML — always escape before rendering

------------------------------------------------------------------------

# GitHub App Commit Policy

## Allowed Repository Actions

Claude MAY:

- create commits
- create branches
- open pull requests
- update pull requests
- push changes
- comment on issues
- close issues

ONLY when performed through the GitHub MCP tools.

## Forbidden Commit Methods

Claude MUST NOT perform repository writes using:

- local `git commit`
- `git push`
- GitHub CLI (`gh`) for any GitHub operation
- any workflow that results in commits authored as a human user

All GitHub interactions MUST use the GitHub MCP integration.
If GitHub MCP is unavailable, Claude MUST stop and report.

## Governance Principle

Human developers supervise.
Claude performs repository operations.

Git history must clearly distinguish human decisions from AI execution.

------------------------------------------------------------------------

## GitHub Repo Context

Monorepo: `github.com/nbehar/ai-security-labs`
Owner: `nbehar`
Repo: `ai-security-labs`

All GitHub MCP calls MUST use this owner/repo unless explicitly overridden.

------------------------------------------------------------------------

## GitHub CLI Prohibition (Global)

Claude MUST NOT use the `gh` CLI for any GitHub operations — including
listing issues, viewing issues, creating issues, commenting, branching,
or pushes. All GitHub interactions MUST go through the GitHub MCP
integration (`mcp__github__*` tools).

------------------------------------------------------------------------

# 1Password OP CLI Execution Policy

All commands that depend on secrets MUST run under `op run`.

### Rules

1. Prefer `op run -- <command>` for any command needing secrets.
2. Never use `op read` inline: forbidden: `$(op read "op://...")`.
3. Never paste raw secret values into commands, issues, or logs.
4. Never include `op://` URIs in GitHub Issues or PR descriptions.
5. Prefer env-file injection: `.env.op` (gitignored) with `KEY=op://...` refs.
6. Commands must be single-line whenever possible.
7. If `op run` cannot be used, STOP and create an issue explaining why.

### Standard Execution Pattern

```bash
# .env.op (gitignored)
GROQ_API_KEY=op://keys/<uuid>/groq_api_key

# Execute
op run --env-file=.env.op -- ./scripts/deploy.sh owasp-top-10
```

### Wrapper (Claude Code)

```bash
~/bin/keys-1password.sh op run --env-file=.env.op -- <command>
```

------------------------------------------------------------------------

# Operational Command Safety

Claude MUST avoid commands that trigger execution warnings.

Rules:

- NEVER run multiline shell snippets as a single command
- NEVER use `$(op read ...)` inline
- NEVER export secrets inline
- NEVER embed secrets or `op://` URIs in agent prompts

Instead:

- use wrapper scripts in `scripts/`
- use `op run -- <command>`
- execute ONE command at a time
- prefer Operator Agent for all command execution


<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
