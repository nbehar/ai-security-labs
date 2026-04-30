"""
app.py — Detection & Monitoring Lab (Space 6)
FastAPI application with 9 endpoints for D1/D2/D3 labs.
Model-free v1: all data served from detection_data.py.
"""

import math
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import detection_data as data
import waf_parser

app = FastAPI(title="Detection & Monitoring Lab", version="1.0.0")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ─────────────────────────────────────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────────────────────────────────────

class LogClassification(BaseModel):
    id: str
    label: Literal["ATTACK", "LEGITIMATE"]

class ClassifyRequest(BaseModel):
    classifications: list[LogClassification]
    session_id: str | None = None

class ThresholdValue(BaseModel):
    high: float | None = None
    low:  float | None = None

class AnomalyRequest(BaseModel):
    thresholds: dict[str, ThresholdValue]
    session_id: str | None = None

class OutputEvalRequest(BaseModel):
    rules: str = Field(max_length=4096)
    session_id: str | None = None

class ScoreSubmit(BaseModel):
    session_id: str
    d1_score: float = Field(ge=0, le=100)
    d2_score: float = Field(ge=0, le=100)
    d3_score: float = Field(ge=0, le=100)
    nickname: str | None = None

# ─────────────────────────────────────────────────────────────────────────────
# In-memory leaderboard
# ─────────────────────────────────────────────────────────────────────────────

_leaderboard: list[dict] = []

VALID_METRICS = {"response_length", "refusal_rate", "query_rate", "confidence"}

# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "lab": "detection-monitoring",
        "version": "1.0.0",
        "d1_log_count": data.D1_LOG_COUNT,
        "d2_window_count": data.D2_WINDOW_COUNT,
        "d3_output_count": data.D3_OUTPUT_COUNT,
    }


@app.get("/api/logs")
async def get_logs():
    public_logs = []
    for entry in data.D1_LOGS:
        public_logs.append({
            "id": entry["id"],
            "system": entry["system"],
            "timestamp": entry["timestamp"],
            "user_query": entry["user_query"],
            "model_response": entry["model_response"],
            "metadata": entry["metadata"],
        })
    return {"logs": public_logs}


@app.post("/api/logs/classify")
@limiter.limit("10/minute")
async def classify_logs(request: Request, body: ClassifyRequest):
    classifications = body.classifications

    if len(classifications) != 20:
        return JSONResponse(
            status_code=422,
            content={"detail": f"Expected exactly 20 classifications, got {len(classifications)}"}
        )

    log_lookup = {entry["id"]: entry for entry in data.D1_LOGS}
    valid_ids = set(log_lookup.keys())

    submitted_ids = [c.id for c in classifications]
    invalid_ids = [i for i in submitted_ids if i not in valid_ids]
    if invalid_ids:
        return JSONResponse(
            status_code=422,
            content={"detail": f"Invalid log IDs: {invalid_ids}"}
        )

    tp = fp = fn = tn = 0
    entries = []

    for c in classifications:
        entry = log_lookup[c.id]
        correct_label = entry["label"]
        submitted = c.label
        correct = submitted == correct_label

        if correct_label == "ATTACK" and submitted == "ATTACK":
            tp += 1
        elif correct_label == "LEGITIMATE" and submitted == "ATTACK":
            fp += 1
        elif correct_label == "ATTACK" and submitted == "LEGITIMATE":
            fn += 1
        else:
            tn += 1

        if correct:
            if correct_label == "ATTACK":
                why_text = f"Correct — this is a {entry['attack_type']} ({_attack_type_name(entry['attack_type'])}) attack. {entry['why']}"
            else:
                why_text = f"Correct — legitimate query, no attack signals. {entry['why']}"
        else:
            if correct_label == "ATTACK":
                why_text = f"Incorrect — this is an ATTACK ({_attack_type_name(entry['attack_type'])}). {entry['why']}"
            else:
                why_text = f"Incorrect — this is a LEGITIMATE query. {entry['why']}"

        entries.append({
            "id": c.id,
            "submitted_label": submitted,
            "correct_label": correct_label,
            "correct": correct,
            "why": why_text,
        })

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    score = round(f1 * 100, 1)

    return {
        "score": score,
        "f1": round(f1, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "entries": entries,
    }


@app.get("/api/anomaly/data")
async def get_anomaly_data():
    public_windows = []
    for w in data.D2_WINDOWS:
        public_windows.append({
            "hour": w["hour"],
            "response_length": w["response_length"],
            "refusal_rate": w["refusal_rate"],
            "query_rate": w["query_rate"],
            "confidence": w["confidence"],
        })
    return {
        "metrics": ["response_length", "refusal_rate", "query_rate", "confidence"],
        "baseline": data.D2_BASELINE,
        "windows": public_windows,
    }


@app.post("/api/anomaly/evaluate")
@limiter.limit("10/minute")
async def evaluate_anomaly(request: Request, body: AnomalyRequest):
    thresholds = body.thresholds

    invalid_metrics = [k for k in thresholds if k not in VALID_METRICS]
    if invalid_metrics:
        return JSONResponse(
            status_code=422,
            content={"detail": f"Invalid metric names: {invalid_metrics}. Valid: {sorted(VALID_METRICS)}"}
        )

    attack_hour_map = {v["hour"]: (k, v) for k, v in data.D2_ATTACK_WINDOWS.items()}

    tp_windows = []
    fp_count = 0
    missed_windows = []
    window_results = []

    for w in data.D2_WINDOWS:
        is_attack = w["hour"] in attack_hour_map
        attack_id = attack_hour_map[w["hour"]][0] if is_attack else None

        alerted = False
        for metric, thresh in thresholds.items():
            val = w[metric]
            if thresh.high is not None and val > thresh.high:
                alerted = True
                break
            if thresh.low is not None and val < thresh.low:
                alerted = True
                break

        if alerted and is_attack:
            verdict = "TP"
            tp_windows.append(attack_id)
            why = _build_window_why(w, thresholds, attack_id, caught=True)
        elif alerted and not is_attack:
            verdict = "FP"
            fp_count += 1
            why = _build_window_why(w, thresholds, None, caught=False, is_fp=True)
        elif not alerted and is_attack:
            verdict = "FN"
            missed_windows.append(attack_id)
            why = None
        else:
            verdict = "TN"
            why = None

        result = {
            "hour": w["hour"],
            "alerted": alerted,
            "is_attack_window": is_attack,
            "verdict": verdict,
        }
        if attack_id:
            result["attack_id"] = attack_id
        if why:
            result["why"] = why

        window_results.append(result)

    tp_count = len(tp_windows)
    raw_score = (tp_count / 3) * 100 - fp_count * 10
    score = max(0, round(raw_score, 1))

    missed_why = {wid: data.D2_MISSED_WHY[wid] for wid in missed_windows}

    return {
        "score": score,
        "tp": tp_count,
        "fp": fp_count,
        "attack_windows_detected": tp_windows,
        "attack_windows_missed": missed_windows,
        "windows": window_results,
        "missed_why": missed_why,
    }


@app.get("/api/outputs")
async def get_outputs():
    public_outputs = []
    for o in data.D3_OUTPUTS:
        public_outputs.append({
            "id": o["id"],
            "system": o["system"],
            "text": o["text"],
        })
    return {"outputs": public_outputs}


@app.post("/api/outputs/evaluate")
@limiter.limit("10/minute")
async def evaluate_outputs(request: Request, body: OutputEvalRequest):
    rules_text = body.rules.strip()

    if not rules_text:
        return JSONResponse(
            status_code=422,
            content={"detail": "No rules provided"}
        )

    rules, errors = waf_parser.parse_rules(rules_text)

    if errors:
        return JSONResponse(
            status_code=422,
            content={"detail": errors[0]}
        )

    tp = fp = fn = tn = 0
    output_results = []

    for o in data.D3_OUTPUTS:
        blocked, matched_rule = waf_parser.evaluate_rules(rules, o["text"])
        should_block = o["should_block"]

        if blocked and should_block:
            tp += 1
            correct = True
        elif blocked and not should_block:
            fp += 1
            correct = False
        elif not blocked and should_block:
            fn += 1
            correct = False
        else:
            tn += 1
            correct = True

        result = {
            "id": o["id"],
            "blocked": blocked,
            "should_block": should_block,
            "correct": correct,
            "why": o["why"],
        }
        if matched_rule:
            result["matched_rule"] = f"{matched_rule['action']} {matched_rule['pattern']}"

        output_results.append(result)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    score = round(f1 * 100, 1)

    baseline_tp, baseline_fp = 8, 7
    baseline_prec = baseline_tp / (baseline_tp + baseline_fp)
    baseline_recall = 1.0
    baseline_f1 = 2 * baseline_prec * baseline_recall / (baseline_prec + baseline_recall)

    return {
        "score": score,
        "f1": round(f1, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "baseline_f1": round(baseline_f1, 4),
        "beat_baseline": f1 > baseline_f1,
        "outputs": output_results,
    }


@app.post("/api/score")
@limiter.limit("10/minute")
async def submit_score(request: Request, body: ScoreSubmit):
    total = round(body.d1_score + body.d2_score + body.d3_score, 1)
    nickname = body.nickname or f"anon_{body.session_id[:6]}"

    existing = next((e for e in _leaderboard if e["session_id"] == body.session_id), None)
    if existing:
        existing.update({"d1": body.d1_score, "d2": body.d2_score, "d3": body.d3_score,
                         "total": total, "nickname": nickname})
    else:
        _leaderboard.append({
            "session_id": body.session_id,
            "nickname": nickname,
            "d1": body.d1_score,
            "d2": body.d2_score,
            "d3": body.d3_score,
            "total": total,
        })

    sorted_board = sorted(_leaderboard, key=lambda e: e["total"], reverse=True)
    rank = next(i + 1 for i, e in enumerate(sorted_board) if e["session_id"] == body.session_id)

    return {"total": total, "rank": rank}


@app.get("/api/leaderboard")
async def get_leaderboard():
    sorted_board = sorted(_leaderboard, key=lambda e: e["total"], reverse=True)[:20]
    entries = []
    for i, e in enumerate(sorted_board, 1):
        entries.append({
            "rank": i,
            "nickname": e["nickname"],
            "d1": e["d1"],
            "d2": e["d2"],
            "d3": e["d3"],
            "total": e["total"],
        })
    return {"entries": entries}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

_ATTACK_TYPE_NAMES = {
    "A1": "Prompt Injection",
    "A2": "Credential Fishing",
    "A3": "System Prompt Leak",
    "A4": "Jailbreak",
    "A5": "PII Exfiltration",
    "A6": "Data Exfiltration",
    "A7": "Denial of Service",
    "A8": "Role Confusion",
}


def _attack_type_name(code: str | None) -> str:
    return _ATTACK_TYPE_NAMES.get(code, code or "Unknown")


def _build_window_why(window: dict, thresholds: dict, attack_id: str | None,
                      caught: bool, is_fp: bool = False) -> str:
    if caught and attack_id:
        aw = data.D2_ATTACK_WINDOWS[attack_id]
        return f"{aw['name']} ({attack_id}) — {aw['description']} Signature: {aw['signature']}."
    if is_fp:
        triggered = []
        for metric, thresh in thresholds.items():
            val = window[metric]
            if thresh.high is not None and val > thresh.high:
                triggered.append(f"{metric}={val} exceeded high threshold {thresh.high}")
            if thresh.low is not None and val < thresh.low:
                triggered.append(f"{metric}={val} fell below low threshold {thresh.low}")
        reason = "; ".join(triggered) if triggered else "threshold triggered"
        return f"False positive (hour {window['hour']}) — {reason}. This was normal traffic. Loosen your threshold."
    return ""
