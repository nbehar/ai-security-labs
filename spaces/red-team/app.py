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
    from exam_session import ExamSession, _SESSIONS
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
LAB_ID = "red-team"
EXERCISE_DEFINITIONS = [
    {"exercise_id": f"level_{i}", "display_name": f"Level {i}", "max_score": 100}
    for i in range(1, 6)
]

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
    answers: dict


# =============================================================================
# STATE — per-session attempt tracking
# =============================================================================

_attempts: dict[str, dict[int, int]] = {}  # name -> {level: attempts}
_scores: dict[str, dict[int, int]] = {}    # name -> {level: score}


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
    """Returns (ExamSession, active_levels) or (None, JSONResponse-with-error)."""
    if not EXAM_ENABLED:
        return None, JSONResponse({"error": "Exam mode not available"}, status_code=503)
    try:
        payload = validate_token(exam_token_value, EXAM_SECRET)
    except InvalidTokenError as e:
        return None, JSONResponse({"error": str(e)}, status_code=401)

    session_key = f"{payload['student_id']}:{payload['exam_id']}"
    session = _SESSIONS.get(session_key)
    if session is None:
        return None, JSONResponse(
            {"error": "Exam session not initialized. POST /api/exam/validate first."},
            status_code=403,
        )

    cap = payload.get("attempt_caps", {}).get(exercise_id)
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
    # Resolve dataset: exam mode uses alternate levels, workshop uses LEVELS
    active_levels = LEVELS
    exam_session = None
    if req.exam_token and EXAM_ENABLED:
        exam_session, result_or_levels = _resolve_exam_session(
            req.exam_token, f"level_{req.level}"
        )
        if exam_session is None:
            return result_or_levels  # JSONResponse with error
        active_levels = result_or_levels

    if req.level not in active_levels:
        raise HTTPException(400, f"Invalid level: {req.level}")

    level = active_levels[req.level]

    # Track attempts
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
            }

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
            result = {
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
            }
            if exam_session is not None:
                exam_session.record_attempt(
                    f"level_{req.level}", 0,
                    {"attempt": attempt_num, "success": False, "blocked_by": "Input Scanner"},
                )
            return result

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

        if exam_session is not None:
            exam_session.record_attempt(
                f"level_{req.level}", score,
                {
                    "attempt": attempt_num,
                    "success": found,
                    "participant_name": req.participant_name,
                    "blocked_by": (
                        "Guardrail Model" if guardrail_blocked
                        else "Output Redaction" if was_redacted and found_in_original
                        else "Prompt Hardening" if not found and req.level >= 2
                        else None
                    ),
                },
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
            "blocked_by": (
                "Guardrail Model" if guardrail_blocked
                else "Output Redaction" if was_redacted and found_in_original
                else "Prompt Hardening" if not found and req.level >= 2
                else None
            ),
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
        payload = validate_token(req.token, EXAM_SECRET)
    except InvalidTokenError as e:
        raise HTTPException(401, str(e))

    session_key = f"{payload['student_id']}:{payload['exam_id']}"
    if session_key not in _SESSIONS:
        _SESSIONS[session_key] = ExamSession(
            student_id=payload["student_id"],
            exam_id=payload["exam_id"],
            lab_id=LAB_ID,
            time_limit_seconds=payload.get("time_limit_seconds", 7200),
            attempt_caps=payload.get("attempt_caps", {}),
            dataset_variant=payload.get("dataset_variant", "workshop"),
        )
    session = _SESSIONS[session_key]

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
        payload = validate_token(req.token, EXAM_SECRET)
    except InvalidTokenError as e:
        raise HTTPException(401, str(e))

    session_key = f"{payload['student_id']}:{payload['exam_id']}"
    session = _SESSIONS.get(session_key)
    if not session:
        raise HTTPException(403, "Session not initialized")

    mcq_results: dict = {}
    try:
        from exam_questions import score_mcq
        mcq_results = score_mcq(LAB_ID, req.answers)
    except ImportError:
        pass

    session.record_theory(req.answers, mcq_results)
    return {
        "status": "received",
        "mcq_scored": mcq_results,
        "short_answer_count": sum(
            1 for k, v in req.answers.items()
            if isinstance(v, str) and len(v.split()) > 10
        ),
    }


@app.get("/api/exam/questions")
async def exam_questions_route(token: str, lab_id: str = LAB_ID):
    """Return theory questions with answer keys stripped (safe for client)."""
    if not EXAM_ENABLED:
        raise HTTPException(503, "Exam mode not available")
    try:
        validate_token(token, EXAM_SECRET)
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
        payload = validate_token(token, EXAM_SECRET)
    except InvalidTokenError as e:
        raise HTTPException(401, str(e))

    session_key = f"{payload['student_id']}:{payload['exam_id']}"
    session = _SESSIONS.get(session_key)
    if not session:
        raise HTTPException(403, "Session not initialized")

    return session.build_receipt(payload)


@app.get("/api/exam/status")
async def exam_status(token: str):
    """Return per-exercise attempt counts, best scores, and remaining time."""
    if not EXAM_ENABLED:
        raise HTTPException(503, "Exam mode not available")
    try:
        payload = validate_token(token, EXAM_SECRET)
    except InvalidTokenError as e:
        raise HTTPException(401, str(e))

    session_key = f"{payload['student_id']}:{payload['exam_id']}"
    session = _SESSIONS.get(session_key)
    if not session:
        raise HTTPException(403, "Session not initialized")

    return session.status_summary(EXERCISE_DEFINITIONS)
