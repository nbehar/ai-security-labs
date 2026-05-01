---
title: AI Security Labs — Detection & Monitoring
emoji: 📊
colorFrom: purple
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Detection & Monitoring Lab

**Space:** `nikobehar/ai-sec-lab6-detection` | **Hardware:** cpu-basic | **Status:** In Development

Practice detecting AI attacks in realistic production telemetry across three detection surfaces.

## Labs

- **D1: Log Analysis** — Classify 20 log entries from NexaCore's AI tools as ATTACK or LEGITIMATE
- **D2: Anomaly Detection** — Configure behavioral alerting thresholds to catch 3 attack windows in 24-hour telemetry
- **D3: Output Sanitization** — Write `BLOCK regex` rules to catch dangerous model outputs (same DSL as Blue Team WAF)

## Scoring

- D1: F1 × 100 (max 100 pts) — false positives reduce score via precision
- D2: (attacks detected / 3) × 100 − (false alarms × 10) — max 100 pts
- D3: F1 × 100 (max 100 pts) — beat the server-side baseline
- Total: max 300 pts

## Stack

- FastAPI + Uvicorn (Python 3.11)
- Vanilla ES6+ frontend — no framework, no build step
- Model-free v1: all datasets are pre-labeled (no API key required)
- Part of [AI Security Labs](https://github.com/nbehar/ai-security-labs) by Prof. Nikolas Behar
