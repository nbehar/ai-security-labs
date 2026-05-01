"""
Red Team Workshop — Progressive AI Attack Lab + Exam Mode
=========================================================
Participants write attack prompts against progressively hardened LLMs.
Discover jailbreak techniques, extract secrets, and climb the leaderboard.

Exam mode: supply ?exam_token=TOKEN in the URL to switch to the exam dataset,
apply attempt caps, and generate a signed score receipt for LMS submission.

Workshop by Prof. Nikolas Behar
Deploy: HuggingFace Spaces (Docker)
"""

import logging
import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from groq import Groq
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from challenges import (
    JAILBREAK_SECRETS,
    JAILBREAK_TARGET_PROMPT,
    JAILBREAKS,
    LEVELS,
    check_secret_found,
    get_heatmap,
    get_leaderboard,
    guardrail_evaluate,
    record_jailbreak_result,
    redact_output,
    scan_input,
    update_leaderboard,
)

# Exam mode (requires exam_token.py + exam_session.py copied from framework at deploy time)
EXAM_ENABLED = False
try:
    from exam_token import InvalidTokenError, validate_token
    from exam_session import _SESSIONS, get_or_create_session
    EXAM_ENABLED = True
except ImportError:
    pass

# =============================================================================
# LOGGING & GROQ
# =============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GROQ_MODEL = "llama-3.3-70b-versatile"
_groq_client: Optional[Groq] = None


def _get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set")
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def generate_response(messages: list[dict], max_tokens: int = 1024) -> str:
    client = _get_groq_client()
    completion = client.chat.completions.create(
        model=GROQ_MODEL, messages=messages, max_tokens=max_tokens, temperature=0.7,
    )
    return completion.choices[0].message.content.strip()


# =============================================================================
# EXAM MODE CONSTANTS
# =============================================================================

EXAM_SECRET = os.environ.get("EXAM_SECRET", "")
PREVIEW_TOKEN = os.environ.get("PREVIEW_TOKEN", "")
LAB_ID = "red-team"
EXERCISE_DEFINITIONS = [
    {"exercise_id": f"level_{i}", "display_name": f"Level {i}", "max_score": 100}
    for i in range(1, 6)
]

# =============================================================================
# PREVIEW MODE
# =============================================================================

def _is_preview(request: Request) -> bool:
    if not PREVIEW_TOKEN:
        return False
    header = request.headers.get("X-Preview-Token", "")
    query = request.query_params.get("preview", "")
    return (header == PREVIEW_TOKEN) or (query == PREVIEW_TOKEN)


# =============================================================================
# RATE LIMITING
# =============================================================================

limiter = Limiter(key_func=get_remote_address)

# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(title="Red Team Workshop")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# =============================================================================
# REQUEST MODELS
# =============================================================================

class RedTeamAttempt(BaseModel):
    level: int
    attack_prompt: str
    participant_name: str = "Anonymous"
    exam_token: Optional[str] = None


class JailbreakTest(BaseModel):
    technique_id: str
    custom_prompt: Optional[str] = None
    participant_name: str = "Anonymous"


class ExamValidateRequest(BaseModel):
    token: str


class TheorySubmission(BaseModel):
    token: str
    mcq_answers: dict          # {question_id: selected_option_key}
    short_answers: list        # [{question_id, response, points_possible?}]


# =============================================================================
# STATE — per-session attempt tracking
# =============================================================================

_attempts: dict[str, dict[int, int]] = {}  # name -> {level: attempts}
_scores: dict[str, dict[int, int]] = {}    # name -> {level: score}
_ROSTER_MAP: dict[str, str] = {}           # student_id → token (populated by POST /api/admin/load-roster)


# =============================================================================
# EXAM HELPERS
# =============================================================================

def _get_exam_levels(variant: str) -> dict:
    """Return the LEVELS dict for the given dataset variant."""
    if variant == "exam_v1":
        from exam_challenges_v1 import EXAM_LEVELS_V1
        return EXAM_LEVELS_V1
    if variant == "exam_v2":
        from exam_challenges_v2 import EXAM_LEVELS_V2
        return EXAM_LEVELS_V2
    return LEVELS


def _resolve_exam_session(exam_token_value: str, exercise_id: str):
    """Returns (session, active_levels) or (None, JSONResponse-with-error)."""
    if not EXAM_ENABLED:
        return None, JSONResponse({"error": "Exam mode not available"}, status_code=503)
    try:
        payload = validate_token(exam_token_value, EXAM_SECRET, LAB_ID)
    except InvalidTokenError as e:
        return None, JSONResponse({"error": str(e)}, status_code=401)

    session = _SESSIONS.get(exam_token_value)
    if session is None:
        return None, JSONResponse(
            {"error": "Exam session not initialized. POST /api/exam/validate first."},
            status_code=403,
        )

    cap = session.attempt_caps.get(exercise_id)
    if cap is not None and session.attempt_count(exercise_id) >= cap:
        return None, JSONResponse(
            {
                "error": "Attempt cap reached",
                "exercise_id": exercise_id,
                "cap": cap,
                "used": session.attempt_count(exercise_id),
            },
            status_code=429,
        )

    active_levels = _get_exam_levels(payload.get("dataset_variant", "workshop"))
    return session, active_levels


# =============================================================================
# ROUTES
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/levels")
async def list_levels():
    return {
        "levels": [
            {
                "id": lvl_id,
                "name": lvl["name"],
                "department": lvl["department"],
                "secret_length": len(lvl["secret"]),
            }
            for lvl_id, lvl in LEVELS.items()
        ],
    }


@app.post("/api/attempt")
@limiter.limit("10/minute")
async def red_team_attempt(request: Request, req: RedTeamAttempt):
    """Submit an attack prompt against a hardened level."""
    preview = _is_preview(request)

    # Resolve dataset: exam mode uses alternate levels, workshop uses LEVELS
    active_levels = LEVELS
    exam_session = None
    if req.exam_token and EXAM_ENABLED and not preview:
        exam_session, result_or_levels = _resolve_exam_session(
            req.exam_token, f"level_{req.level}"
        )
        if exam_session is None:
            return result_or_levels  # JSONResponse with error
        active_levels = result_or_levels
        if exam_session.is_paused():
            return JSONResponse({"error": "Exam is paused by instructor. Please wait."}, status_code=423)

    if req.level not in active_levels:
        raise HTTPException(400, f"Invalid level: {req.level}")

    level = active_levels[req.level]

    # Track attempts (skipped in preview mode)
    if not preview:
        if req.participant_name not in _attempts:
            _attempts[req.participant_name] = {}
        if req.level not in _attempts[req.participant_name]:
            _attempts[req.participant_name][req.level] = 0
        _attempts[req.participant_name][req.level] += 1
        attempt_num = _attempts[req.participant_name][req.level]

        # Check if already solved
        if req.participant_name in _scores and req.level in _scores[req.participant_name]:
            prev_score = _scores[req.participant_name][req.level]
            if prev_score > 0:
                return {
                    "level": req.level,
                    "success": True,
                    "already_solved": True,
                    "score": prev_score,
                    "message": f"You already solved Level {req.level}!",
                    "preview_mode": False,
                }
    else:
        attempt_num = 1

    try:
        secret = level["secret"]
        defense_log = []

        # === DEFENSE LAYER 1: Input Scanning (Level 4+) ===
        input_result = scan_input(req.attack_prompt, req.level)
        defense_log.append(input_result)

        if input_result["verdict"] == "BLOCKED":
            hint = None
            if attempt_num >= 3:
                hints = level.get("hints", [])
                if hints:
                    hint = hints[min(attempt_num - 3, len(hints) - 1)]
            if exam_session is not None and not preview:
                exam_session.record_attempt(
                    f"level_{req.level}",
                    False,
                    0,
                    metadata={"attempt": attempt_num, "blocked_by": "Input Scanner"},
                )
            return {
                "level": req.level,
                "level_name": level["name"],
                "department": level["department"],
                "success": False,
                "model_output": "[Input blocked by defense scanner — your prompt contained flagged patterns]",
                "secret_found": None,
                "attempt": attempt_num,
                "score": 0,
                "hint": hint,
                "max_attempts": 5,
                "defense_log": defense_log,
                "blocked_by": "Input Scanner",
                "preview_mode": preview,
            }

        # === MODEL CALL ===
        messages = [
            {"role": "system", "content": level["system_prompt"]},
            {"role": "user", "content": req.attack_prompt},
        ]
        output = generate_response(messages)

        # === DEFENSE LAYER 2: Output Redaction (Level 5) ===
        output_result = redact_output(output, secret, req.level)
        defense_log.append(output_result)
        final_output = output_result["output"]
        was_redacted = output_result.get("redacted", False)

        # === DEFENSE LAYER 3: Guardrail Evaluation (Level 5 only) ===
        guardrail_result = guardrail_evaluate(final_output, secret, req.level, generate_response)
        defense_log.append(guardrail_result)
        guardrail_blocked = guardrail_result.get("blocked", False)
        if guardrail_blocked:
            final_output = "I'm here to help with executive briefing tasks. How can I assist you?"

        found_in_original = secret.lower() in output.lower()
        found = found_in_original and not was_redacted and not guardrail_blocked

        score = 0
        if found:
            score = max(0, (6 - attempt_num) * 20)  # 100, 80, 60, 40, 20, 0
            if not preview:
                if req.participant_name not in _scores:
                    _scores[req.participant_name] = {}
                _scores[req.participant_name][req.level] = score
                update_leaderboard(
                    req.participant_name, "red_team",
                    sum(_scores[req.participant_name].values())
                )

        hint = None
        if not found and attempt_num >= 3:
            hints = level.get("hints", [])
            if hints:
                hint = hints[min(attempt_num - 3, len(hints) - 1)]

        blocked_by = (
            "Guardrail Model" if guardrail_blocked
            else "Output Redaction" if was_redacted and found_in_original
            else "Prompt Hardening" if not found and req.level >= 2
            else None
        )

        if exam_session is not None and not preview:
            exam_session.record_attempt(
                f"level_{req.level}",
                found,
                score,
                metadata={"attempt": attempt_num, "blocked_by": blocked_by},
            )

        return {
            "level": req.level,
            "level_name": level["name"],
            "department": level["department"],
            "success": found,
            "model_output": final_output,
            "secret_found": secret if found else None,
            "attempt": attempt_num,
            "score": score,
            "hint": hint,
            "max_attempts": 5,
            "defense_log": defense_log,
            "blocked_by": blocked_by,
            "preview_mode": preview,
        }
    except Exception as e:
        logger.exception("Error in red team attempt")
        raise HTTPException(500, str(e))


@app.get("/api/jailbreaks")
async def list_jailbreaks():
    return {
        "techniques": [
            {
                "id": jb_id,
                "name": jb["name"],
                "category": jb["category"],
                "template": jb["template"],
                "why": jb.get("why", ""),
            }
            for jb_id, jb in JAILBREAKS.items()
        ],
    }


@app.post("/api/jailbreak-test")
@limiter.limit("10/minute")
async def test_jailbreak(request: Request, req: JailbreakTest):
    """Test a jailbreak technique against the hardened target."""
    if req.technique_id not in JAILBREAKS:
        raise HTTPException(400, f"Unknown technique: {req.technique_id}")

    jb = JAILBREAKS[req.technique_id]
    prompt = req.custom_prompt or jb["template"]

    try:
        messages = [
            {"role": "system", "content": JAILBREAK_TARGET_PROMPT},
            {"role": "user", "content": prompt},
        ]
        output = generate_response(messages)
        found = check_secret_found(output, JAILBREAK_SECRETS)
        success = len(found) > 0
        record_jailbreak_result(req.technique_id, success)

        if success:
            score = len(found) * 25
            update_leaderboard(req.participant_name, "jailbreak", score)

        return {
            "technique_id": req.technique_id,
            "technique_name": jb["name"],
            "category": jb["category"],
            "success": success,
            "secrets_found": found,
            "model_output": output,
            "prompt_used": prompt,
        }
    except Exception as e:
        logger.exception("Error in jailbreak test")
        raise HTTPException(500, str(e))


@app.get("/api/heatmap")
async def heatmap():
    return {"techniques": get_heatmap()}


@app.get("/api/leaderboard")
async def leaderboard():
    return {"leaderboard": get_leaderboard()}


@app.get("/health")
async def health():
    has_key = bool(os.environ.get("GROQ_API_KEY"))
    return {"status": "ok" if has_key else "missing_api_key", "model": GROQ_MODEL}


# =============================================================================
# EXAM ROUTES
# =============================================================================

@app.post("/api/exam/validate")
async def exam_validate(req: ExamValidateRequest):
    """Validate an exam token and initialize a session."""
    if not EXAM_ENABLED:
        raise HTTPException(503, "Exam mode not available")
    try:
        payload = validate_token(req.token, EXAM_SECRET, LAB_ID)
    except InvalidTokenError as e:
        raise HTTPException(401, str(e))

    session = get_or_create_session(req.token, payload)

    return {
        "status": "valid",
        "student_id": payload["student_id"],
        "exam_id": payload["exam_id"],
        "lab_id": LAB_ID,
        "time_limit_seconds": payload.get("time_limit_seconds", 7200),
        "expires_at": payload["expires_at"],
        "attempt_caps": payload.get("attempt_caps", {}),
        "dataset_variant": payload.get("dataset_variant", "workshop"),
        "exercises": EXERCISE_DEFINITIONS,
        "elapsed_seconds": session.elapsed_seconds(),
    }


@app.post("/api/exam/theory")
async def exam_theory(req: TheorySubmission):
    """Submit MCQ + short-answer theory responses."""
    if not EXAM_ENABLED:
        raise HTTPException(503, "Exam mode not available")
    try:
        payload = validate_token(req.token, EXAM_SECRET, LAB_ID)
    except InvalidTokenError as e:
        raise HTTPException(401, str(e))

    session = _SESSIONS.get(req.token)
    if not session:
        raise HTTPException(403, "Session not initialized")
    if session.theory_submitted():
        raise HTTPException(409, "Theory already submitted")

    # Score MCQ server-side
    mcq_scored: dict = {}
    try:
        from exam_questions import score_mcq
        mcq_scored = score_mcq(LAB_ID, req.mcq_answers)
    except ImportError:
        pass

    # Normalise MCQ answers to list[dict] for record_theory
    mcq_answers_list = [
        {"question_id": qid, "answer": answer}
        for qid, answer in req.mcq_answers.items()
    ]
    session.record_theory(mcq_answers_list, req.short_answers)

    mcq_score = sum(v.get("points_earned", 0) for v in mcq_scored.values())
    return {
        "status": "received",
        "mcq_scored": mcq_scored,
        "mcq_score": mcq_score,
        "short_answer_count": len(req.short_answers),
    }


@app.get("/api/exam/questions")
async def exam_questions_route(token: str, lab_id: str = LAB_ID):
    """Return theory questions with answer keys stripped (safe for client)."""
    if not EXAM_ENABLED:
        raise HTTPException(503, "Exam mode not available")
    try:
        validate_token(token, EXAM_SECRET, LAB_ID)
    except InvalidTokenError as e:
        raise HTTPException(401, str(e))
    try:
        from exam_questions import get_client_questions
        return get_client_questions(lab_id)
    except ImportError:
        raise HTTPException(503, "Exam questions module not installed")


@app.get("/api/exam/receipt")
async def exam_receipt(token: str):
    """Build and return the practical score receipt (unsigned; client signs with WebCrypto)."""
    if not EXAM_ENABLED:
        raise HTTPException(503, "Exam mode not available")
    try:
        payload = validate_token(token, EXAM_SECRET, LAB_ID)
    except InvalidTokenError as e:
        raise HTTPException(401, str(e))

    session = _SESSIONS.get(token)
    if not session:
        raise HTTPException(403, "Session not initialized")

    practical = session.to_practical_receipt(EXERCISE_DEFINITIONS)

    # Re-score MCQ from stored theory answers for the receipt
    scored_mcq_list: list[dict] = []
    if session.theory_submitted():
        try:
            from exam_questions import QUESTION_BANKS, score_mcq
            stored_mcq = session._theory.get("mcq_answers", [])
            mcq_dict = {item["question_id"]: item["answer"] for item in stored_mcq}
            score_result = score_mcq(LAB_ID, mcq_dict)
            # Enrich with question metadata for the receipt
            bank_mcq = {q["id"]: q for q in QUESTION_BANKS.get(LAB_ID, {}).get("mcq", [])}
            for qid, result in score_result.items():
                q = bank_mcq.get(qid, {})
                correct_opt = next(
                    (o for o in q.get("options", []) if o.get("correct")), {}
                )
                scored_mcq_list.append({
                    "question_id": qid,
                    "bloom_level": q.get("bloom_level"),
                    "points_possible": q.get("points", 5),
                    "student_answer": mcq_dict.get(qid),
                    "correct_answer": correct_opt.get("key"),
                    "correct": result["correct"],
                    "points_earned": result["points_earned"],
                })
        except (ImportError, Exception):
            pass

    theory = session.to_theory_receipt(scored_mcq_list)

    return {
        "receipt_version": "1",
        "exam_id": payload["exam_id"],
        "student_id": payload["student_id"],
        "lab_id": LAB_ID,
        "practical": practical,
        "theory": theory,
        "timing": {
            "total_elapsed_seconds": session.elapsed_seconds(),
            "time_limit_seconds": session.time_limit_seconds,
        },
    }


@app.get("/api/exam/status")
async def exam_status(token: str):
    """Return per-exercise attempt counts, best scores, and remaining time."""
    if not EXAM_ENABLED:
        raise HTTPException(503, "Exam mode not available")
    try:
        validate_token(token, EXAM_SECRET, LAB_ID)
    except InvalidTokenError as e:
        raise HTTPException(401, str(e))

    session = _SESSIONS.get(token)
    if not session:
        raise HTTPException(403, "Session not initialized")

    exercises = []
    for defn in EXERCISE_DEFINITIONS:
        eid = defn["exercise_id"]
        exercises.append({
            "exercise_id": eid,
            "display_name": defn.get("display_name", eid),
            "attempts_used": session.attempt_count(eid),
            "attempt_cap": session.attempt_caps.get(eid),
            "remaining_attempts": session.remaining_attempts(eid),
            "best_score": session._scores.get(eid, 0),
            "max_score": defn.get("max_score", 100),
        })

    return {
        "exercises": exercises,
        "remaining_seconds": session.remaining_seconds(),
        "elapsed_seconds": session.elapsed_seconds(),
        "time_limit_seconds": session.time_limit_seconds,
        "theory_submitted": session.theory_submitted(),
    }


# =============================================================================
# ADMIN ROUTES (exam-admin proxy target — requires X-Exam-Secret header)
# =============================================================================

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
