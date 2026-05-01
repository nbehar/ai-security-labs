# Deployment Spec — Detection & Monitoring Lab (Space 6)

## HuggingFace Space

| Parameter | Value |
|-----------|-------|
| Space name | `nikobehar/ai-sec-lab6-detection` |
| SDK | `docker` |
| Hardware | `cpu-basic` (free tier) |
| Visibility | Private (workshop access control) |
| Port | 7860 |

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System deps (no Tesseract, no apt extras needed — model-free v1)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
```

## requirements.txt (pinned)

```
fastapi==0.115.0
uvicorn==0.30.6
jinja2==3.1.4
python-multipart==0.0.12
pydantic==2.9.2
slowapi==0.1.9
```

No Groq, no HuggingFace Hub, no Pillow, no pytesseract — v1 is fully model-free.

## Environment Variables

| Variable | Required? | Purpose |
|----------|-----------|---------|
| None | — | No secrets needed for v1; all labs use pre-labeled datasets |

**Note:** `GROQ_API_KEY` is NOT required for v1. If added in a future phase (live model output generation for D3), it must be stored as a HF Space secret and never committed or logged.

## HuggingFace README frontmatter (README.md)

```yaml
---
title: AI Security Labs — Detection & Monitoring
emoji: 🛡
colorFrom: purple
colorTo: violet
sdk: docker
app_port: 7860
pinned: false
---
```

## File Layout (at deploy time)

```
/app/
  app.py                   FastAPI routes
  detection_data.py        Pre-labeled datasets: D1 logs, D2 time-series, D3 outputs
  waf_parser.py            Reused from blue-team (D3 rule evaluation)
  scoring.py               Copied from framework at deploy time
  groq_client.py           Copied from framework (unused in v1; available for future phases)
  Dockerfile
  requirements.txt
  README.md
  CLAUDE.md
  templates/
    index.html
  static/
    css/
      styles.css           Framework copy (gitignored; deploy-time)
      luminex-tokens.css   Vendored brand tokens
      luminex-bridge.css   Framework variable remapping to Luminex tokens
      luminex-nav.css      Master nav stylesheet
      detection.css        Space-specific styles
    js/
      core.js              Framework copy (gitignored; deploy-time)
      app.js               SPA entry: tab routing, Info tab, Leaderboard tab
      log_viewer.js        D1 Log Analysis tab: card rendering, classification, WHY
      anomaly_dashboard.js D2 Anomaly Detection tab: charts, sliders, timeline
      output_sanitizer.js  D3 Output Sanitization tab: rule editor, results table
    images/                (empty in v1 — no image assets needed)
  specs/
  docs/
```

## Deploy Command

```bash
op run --env-file=.env.op -- ./scripts/deploy.sh detection-monitoring
```

(No secrets needed for v1 but the pattern is preserved for consistency.)

## Cold Start Behavior

- No model loading (no ZeroGPU, no HF Inference Providers)
- Container start time: ~5–10s
- First request: <500ms (dataset loaded at startup via `detection_data.py`)
- Subsequent requests: <100ms

The cold-start banner pattern from Phase B pedagogical improvements should be implemented: if `/health` returns non-200 on page load, show a "Lab is waking up (~10 seconds)" toast.

## Deploy Verification Checklist

After deploying to `nikobehar/ai-sec-lab6-detection`:

- [ ] `GET /health` returns 200 with `d1_log_count: 20, d2_window_count: 24, d3_output_count: 15`
- [ ] All 5 tabs render without JS errors
- [ ] D1: classify all 20 correctly → score 100
- [ ] D2: set thresholds so all 3 windows alert → score 100
- [ ] D3: `BLOCK \b\d{3}-\d{2}-\d{4}\b` catches D3.01 → score > 0
- [ ] Leaderboard records a composite score after completing D1
- [ ] No secrets appear in logs (`grep -i "password\|api_key\|token" uvicorn.log`)

## Acceptance Checks (Deployment)

- [ ] HF Space status: `RUNNING` within 60s of push
- [ ] `/health` returns 200 (smoke test)
- [ ] Cold-start time measured: < 30s from space wake to first `/health` 200
- [ ] All three datasets load: counts match expected (20 / 24 / 15)
