"""
app.py — Detection & Monitoring Lab (Space 6)
FastAPI application with 9 workshop endpoints + 4 exam endpoints for D1/D2/D3 labs.
Model-free: all data served from detection_data.py (workshop) or exam_data_v*.py (exam mode).
"""

import math
import os
import time
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import detection_data as data
import waf_parser

try:
    from exam_token import validate_token, InvalidTokenError, sign_receipt
    from exam_session import _SESSIONS, get_or_create_session, get_session, AttemptCapError
    EXAM_ENABLED = True
except ImportError:
    EXAM_ENABLED = False

EXAM_SECRET = os.environ.get("EXAM_SECRET", "")
LAB_ID = "detection-monitoring"

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
    exam_token: str | None = None

class ThresholdValue(BaseModel):
    high: float | None = None
    low:  float | None = None

class AnomalyRequest(BaseModel):
    thresholds: dict[str, ThresholdValue]
    session_id: str | None = None
    exam_token: str | None = None

class OutputEvalRequest(BaseModel):
    rules: str = Field(max_length=4096)
    session_id: str | None = None
    exam_token: str | None = None

class ScoreSubmit(BaseModel):
    session_id: str
    d1_score: float = Field(ge=0, le=100)
    d2_score: float = Field(ge=0, le=100)
    d3_score: float = Field(ge=0, le=100)
    nickname: str | None = None

class ExamValidateRequest(BaseModel):
    token: str

class MCQAnswer(BaseModel):
    question_id: str
    answer: str

class ShortAnswer(BaseModel):
    question_id: str
    response: str

class TheorySubmitRequest(BaseModel):
    exam_token: str
    mcq_answers: list[MCQAnswer] = []
    short_answers: list[ShortAnswer] = []

# ─────────────────────────────────────────────────────────────────────────────
# In-memory leaderboard + constants
# ─────────────────────────────────────────────────────────────────────────────

_leaderboard: list[dict] = []
_ROSTER_MAP: dict[str, str] = {}  # student_id → token (populated by POST /api/admin/load-roster)

VALID_METRICS = {"response_length", "refusal_rate", "query_rate", "confidence"}

EXERCISE_DEFINITIONS = [
    {"exercise_id": "D1", "display_name": "D1: Log Analysis",          "max_score": 100},
    {"exercise_id": "D2", "display_name": "D2: Anomaly Detection",     "max_score": 100},
    {"exercise_id": "D3", "display_name": "D3: Output Sanitization",   "max_score": 100},
]

# ─────────────────────────────────────────────────────────────────────────────
# Routes — workshop
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
        "exam_enabled": EXAM_ENABLED and bool(EXAM_SECRET),
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
    active_data = data
    session = None

    if body.exam_token:
        result = _resolve_exam_session(body.exam_token, "D1")
        if isinstance(result, JSONResponse):
            return result
        session, active_data = result

    if len(classifications) != 20:
        return JSONResponse(
            status_code=422,
            content={"detail": f"Expected exactly 20 classifications, got {len(classifications)}"}
        )

    log_lookup = {entry["id"]: entry for entry in active_data.D1_LOGS}
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

    if session is not None:
        elapsed = float(int(time.time()) - session.started_at)
        session.record_attempt("D1", success=score > 0, score=int(score), elapsed_seconds=elapsed)

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
        **({"exam": {"remaining_attempts": session.remaining_attempts("D1")}} if session else {}),
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
    active_data = data
    session = None

    if body.exam_token:
        result = _resolve_exam_session(body.exam_token, "D2")
        if isinstance(result, JSONResponse):
            return result
        session, active_data = result

    invalid_metrics = [k for k in thresholds if k not in VALID_METRICS]
    if invalid_metrics:
        return JSONResponse(
            status_code=422,
            content={"detail": f"Invalid metric names: {invalid_metrics}. Valid: {sorted(VALID_METRICS)}"}
        )

    attack_hour_map = {v["hour"]: (k, v) for k, v in active_data.D2_ATTACK_WINDOWS.items()}

    tp_windows = []
    fp_count = 0
    missed_windows = []
    window_results = []

    for w in active_data.D2_WINDOWS:
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
            why = _build_window_why(w, thresholds, attack_id, active_data, caught=True)
        elif alerted and not is_attack:
            verdict = "FP"
            fp_count += 1
            why = _build_window_why(w, thresholds, None, active_data, caught=False, is_fp=True)
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

    missed_why = {wid: active_data.D2_MISSED_WHY[wid] for wid in missed_windows}

    if session is not None:
        elapsed = float(int(time.time()) - session.started_at)
        session.record_attempt("D2", success=score > 0, score=int(score), elapsed_seconds=elapsed)

    return {
        "score": score,
        "tp": tp_count,
        "fp": fp_count,
        "attack_windows_detected": tp_windows,
        "attack_windows_missed": missed_windows,
        "windows": window_results,
        "missed_why": missed_why,
        **({"exam": {"remaining_attempts": session.remaining_attempts("D2")}} if session else {}),
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
    active_data = data
    session = None

    if body.exam_token:
        result = _resolve_exam_session(body.exam_token, "D3")
        if isinstance(result, JSONResponse):
            return result
        session, active_data = result

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

    for o in active_data.D3_OUTPUTS:
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

    # Baseline: BLOCK .* catches all 8 dangerous + all 7 legit → f1 ≈ 0.533
    baseline_tp, baseline_fp = 8, 7
    baseline_prec = baseline_tp / (baseline_tp + baseline_fp)
    baseline_recall = 1.0
    baseline_f1 = 2 * baseline_prec * baseline_recall / (baseline_prec + baseline_recall)

    if session is not None:
        elapsed = float(int(time.time()) - session.started_at)
        session.record_attempt("D3", success=score > 0, score=int(score), elapsed_seconds=elapsed)

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
        **({"exam": {"remaining_attempts": session.remaining_attempts("D3")}} if session else {}),
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
# Routes — exam mode
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/exam/validate")
@limiter.limit("20/minute")
async def exam_validate(request: Request, body: ExamValidateRequest):
    if not EXAM_ENABLED:
        return JSONResponse(status_code=503, content={"detail": "Exam infrastructure not available on this server."})
    if not EXAM_SECRET:
        return JSONResponse(status_code=503, content={"detail": "Exam mode not configured (EXAM_SECRET missing)."})

    try:
        payload = validate_token(body.token, EXAM_SECRET, LAB_ID)
    except InvalidTokenError as e:
        return JSONResponse(status_code=401, content={"detail": e.reason})

    session = get_or_create_session(body.token, payload)

    if session.is_expired():
        return JSONResponse(status_code=403, content={"detail": "Exam time limit has expired."})

    return {
        "valid": True,
        "exam_id": session.exam_id,
        "student_id": session.student_id,
        "lab_id": LAB_ID,
        "dataset_variant": session.dataset_variant,
        "time_limit_seconds": session.time_limit_seconds,
        "remaining_seconds": session.remaining_seconds(),
        "attempt_caps": session.attempt_caps,
        "attempts": {
            ex["exercise_id"]: {
                "used": session.attempt_count(ex["exercise_id"]),
                "remaining": session.remaining_attempts(ex["exercise_id"]),
            }
            for ex in EXERCISE_DEFINITIONS
        },
    }


@app.post("/api/exam/theory")
@limiter.limit("10/minute")
async def exam_theory(request: Request, body: TheorySubmitRequest):
    if not EXAM_ENABLED or not EXAM_SECRET:
        return JSONResponse(status_code=503, content={"detail": "Exam mode not configured."})

    try:
        validate_token(body.exam_token, EXAM_SECRET, LAB_ID)
    except InvalidTokenError as e:
        return JSONResponse(status_code=401, content={"detail": e.reason})

    session = get_session(body.exam_token)
    if not session:
        return JSONResponse(status_code=404, content={"detail": "Exam session not found. Call /api/exam/validate first."})

    if session.is_expired():
        return JSONResponse(status_code=403, content={"detail": "Exam time limit has expired."})

    if session.theory_submitted():
        return JSONResponse(status_code=409, content={"detail": "Theory answers already submitted for this session."})

    mcq = [{"question_id": a.question_id, "answer": a.answer} for a in body.mcq_answers]
    sa = [{"question_id": a.question_id, "response": a.response} for a in body.short_answers]
    session.record_theory(mcq_answers=mcq, short_answers=sa)

    return {
        "submitted": True,
        "mcq_count": len(mcq),
        "short_answer_count": len(sa),
        "note": "MCQ auto-scoring available after exam_questions.py is deployed (Phase 4).",
    }


@app.get("/api/exam/receipt")
async def exam_receipt(exam_token: str):
    if not EXAM_ENABLED or not EXAM_SECRET:
        return JSONResponse(status_code=503, content={"detail": "Exam mode not configured."})

    try:
        validate_token(exam_token, EXAM_SECRET, LAB_ID)
    except InvalidTokenError as e:
        return JSONResponse(status_code=401, content={"detail": e.reason})

    session = get_session(exam_token)
    if not session:
        return JSONResponse(status_code=404, content={"detail": "Exam session not found. Call /api/exam/validate first."})

    session.finalize()

    receipt_payload = {
        "receipt_version": "1",
        "exam_id": session.exam_id,
        "student_id": session.student_id,
        "lab_id": LAB_ID,
        "practical": session.to_practical_receipt(EXERCISE_DEFINITIONS),
        "theory": {"submitted": session.theory_submitted()},
        "timing": {
            "total_elapsed_seconds": session.elapsed_seconds(),
            "time_limit_seconds": session.time_limit_seconds,
        },
    }
    receipt_payload["hmac_sha256"] = sign_receipt(receipt_payload, EXAM_SECRET)
    return receipt_payload


@app.get("/api/exam/status")
async def exam_status(exam_token: str):
    if not EXAM_ENABLED or not EXAM_SECRET:
        return JSONResponse(status_code=503, content={"detail": "Exam mode not configured."})

    try:
        validate_token(exam_token, EXAM_SECRET, LAB_ID)
    except InvalidTokenError as e:
        return JSONResponse(status_code=401, content={"detail": e.reason})

    session = get_session(exam_token)
    if not session:
        return JSONResponse(status_code=404, content={"detail": "Exam session not found. Call /api/exam/validate first."})

    return {
        "exam_id": session.exam_id,
        "student_id": session.student_id,
        "remaining_seconds": session.remaining_seconds(),
        "elapsed_seconds": session.elapsed_seconds(),
        "expired": session.is_expired(),
        "theory_submitted": session.theory_submitted(),
        "attempts": {
            ex["exercise_id"]: {
                "used": session.attempt_count(ex["exercise_id"]),
                "cap": session.attempt_caps.get(ex["exercise_id"]),
                "remaining": session.remaining_attempts(ex["exercise_id"]),
                "best_score": session._scores.get(ex["exercise_id"], 0),
            }
            for ex in EXERCISE_DEFINITIONS
        },
    }


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


def _get_exam_data(dataset_variant: str):
    """Return the exam data module for the given variant, falling back to workshop data."""
    if dataset_variant == "exam_v1":
        try:
            import exam_data_v1
            return exam_data_v1
        except ImportError:
            pass
    elif dataset_variant == "exam_v2":
        try:
            import exam_data_v2
            return exam_data_v2
        except ImportError:
            pass
    return data


def _resolve_exam_session(exam_token: str, exercise_id: str):
    """
    Validate an exam token, get/create the session, check attempt cap,
    and return (session, active_data) or a JSONResponse on failure.
    """
    if not EXAM_ENABLED or not EXAM_SECRET:
        return JSONResponse(status_code=503, content={"detail": "Exam mode not configured."})

    try:
        payload = validate_token(exam_token, EXAM_SECRET, LAB_ID)
    except InvalidTokenError as e:
        return JSONResponse(status_code=401, content={"detail": e.reason})

    session = get_or_create_session(exam_token, payload)

    if session.is_expired():
        return JSONResponse(status_code=403, content={"detail": "Exam time limit has expired."})

    try:
        session.check_attempt_cap(exercise_id)
    except AttemptCapError as e:
        return JSONResponse(status_code=429, content={
            "detail": str(e),
            "exercise_id": e.exercise_id,
            "cap": e.cap,
        })

    if session.is_paused():
        return JSONResponse(status_code=423, content={"detail": "Exam is paused by instructor. Please wait."})

    active_data = _get_exam_data(session.dataset_variant)
    return session, active_data


def _build_window_why(window: dict, thresholds: dict, attack_id: str | None,
                      active_data, caught: bool, is_fp: bool = False) -> str:
    if caught and attack_id:
        aw = active_data.D2_ATTACK_WINDOWS[attack_id]
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


# ─────────────────────────────────────────────────────────────────────────────
# Routes — admin (exam-admin proxy target, requires X-Exam-Secret header)
# ─────────────────────────────────────────────────────────────────────────────

def _check_admin_auth(request: Request) -> None:
    if not EXAM_SECRET:
        raise HTTPException(503, "EXAM_SECRET not configured")
    if request.headers.get("X-Exam-Secret", "") != EXAM_SECRET:
        raise HTTPException(401, "Invalid or missing X-Exam-Secret header")


class AdminTokenBody(BaseModel):
    token: str


class ExtendTimeBody(BaseModel):
    token: str
    additional_seconds: int


class ResetAttemptsBody(BaseModel):
    token: str
    exercise_id: str
    reason: str = ""


class LoadRosterBody(BaseModel):
    rows: list[dict]


@app.get("/api/admin/roster")
async def admin_roster(request: Request):
    _check_admin_auth(request)
    if not EXAM_ENABLED:
        return {"sessions": [], "note": "Exam infrastructure not deployed"}
    results = []
    for token, session in _SESSIONS.items():
        row = {
            "student_id": session.student_id,
            "exam_id": session.exam_id,
            "token_prefix": token[:8] + "…",
            "remaining_seconds": session.remaining_seconds(),
            "elapsed_seconds": session.elapsed_seconds(),
            "expired": session.is_expired(),
            "paused": session.is_paused(),
            "theory_submitted": session.theory_submitted(),
            "exercises": {},
        }
        for defn in EXERCISE_DEFINITIONS:
            eid = defn["exercise_id"]
            row["exercises"][eid] = {
                "attempts_used": session.attempt_count(eid),
                "cap": session.attempt_caps.get(eid),
                "best_score": session._scores.get(eid, 0),
            }
        results.append(row)
    return {"sessions": results, "count": len(results)}


@app.post("/api/admin/load-roster")
async def admin_load_roster(request: Request, body: LoadRosterBody):
    _check_admin_auth(request)
    global _ROSTER_MAP
    _ROSTER_MAP = {row["student_id"]: row.get("token", "") for row in body.rows if "student_id" in row}
    return {"loaded": len(_ROSTER_MAP)}


@app.post("/api/admin/extend-time")
async def admin_extend_time(request: Request, body: ExtendTimeBody):
    _check_admin_auth(request)
    if not EXAM_ENABLED:
        raise HTTPException(503, "Exam infrastructure not deployed")
    session = _SESSIONS.get(body.token)
    if not session:
        raise HTTPException(404, "Session not found")
    return session.extend_time(body.additional_seconds)


@app.post("/api/admin/reset-attempts")
async def admin_reset_attempts(request: Request, body: ResetAttemptsBody):
    _check_admin_auth(request)
    if not EXAM_ENABLED:
        raise HTTPException(503, "Exam infrastructure not deployed")
    session = _SESSIONS.get(body.token)
    if not session:
        raise HTTPException(404, "Session not found")
    cleared = session.reset_exercise(body.exercise_id, body.reason)
    return {"cleared": cleared, "exercise_id": body.exercise_id}


@app.post("/api/admin/pause-exam")
async def admin_pause_exam(request: Request, body: AdminTokenBody):
    _check_admin_auth(request)
    if not EXAM_ENABLED:
        raise HTTPException(503, "Exam infrastructure not deployed")
    session = _SESSIONS.get(body.token)
    if not session:
        raise HTTPException(404, "Session not found")
    return session.pause()


@app.post("/api/admin/resume-exam")
async def admin_resume_exam(request: Request, body: AdminTokenBody):
    _check_admin_auth(request)
    if not EXAM_ENABLED:
        raise HTTPException(503, "Exam infrastructure not deployed")
    session = _SESSIONS.get(body.token)
    if not session:
        raise HTTPException(404, "Session not found")
    return session.resume()
