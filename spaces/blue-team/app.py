"""
Blue Team Workshop — Interactive Defense Lab
=============================================
Participants write defense prompts, WAF rules, and defense pipelines
to block OWASP LLM Top 10 attacks against NexaCore Technologies.

Exam mode: supply ?exam_token=TOKEN in the URL to switch to the exam dataset,
apply attempt caps, and generate a signed score receipt for LMS submission.

Workshop by Prof. Nikolas Behar
Deploy: HuggingFace Spaces (Docker)
"""

import logging
import os
import time
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
    ATTACKS, LEVELS, LEGIT_QUERIES, CONFIDENTIAL_BLOCK,
    DEFAULT_VULNERABLE_PROMPT, check_legit_passed, calculate_score,
    WAF_ATTACK_PROMPTS, WAF_LEGIT_QUERIES, PG2_BASELINE, calculate_waf_score,
    update_leaderboard, get_leaderboard,
    PIPELINE_TOOLS, PIPELINE_PRESETS, evaluate_pipeline, calculate_pipeline_score,
    VULNERABILITIES, VULNERABILITY_CATEGORIES, VULNERABLE_ASSISTANT_PROMPT,
    get_behavioral_session, check_vulnerabilities, calculate_behavioral_score,
)
from waf_parser import parse_rules, evaluate_rules

# =============================================================================
# EXAM MODE (requires exam_token.py + exam_session.py copied from framework)
# =============================================================================

EXAM_ENABLED = False
try:
    from exam_token import InvalidTokenError, validate_token, sign_receipt
    from exam_session import _SESSIONS, get_or_create_session
    EXAM_ENABLED = True
except ImportError:
    pass

# =============================================================================
# LOGGING & GROQ
# =============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LAB_ID = "blue-team"
EXAM_SECRET = os.environ.get("EXAM_SECRET", "")
PREVIEW_TOKEN = os.environ.get("PREVIEW_TOKEN", "")
_ROSTER_MAP: dict[str, str] = {}

EXERCISE_DEFINITIONS = [
    {"exercise_id": "prompt_hardening", "display_name": "Prompt Hardening (all levels)", "max_score": 120},
    {"exercise_id": "waf_rules", "display_name": "WAF Rules", "max_score": 100},
    {"exercise_id": "defense_pipeline", "display_name": "Defense Pipeline", "max_score": 100},
    {"exercise_id": "behavioral_testing", "display_name": "Behavioral Testing", "max_score": 160},
]

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
        model=GROQ_MODEL,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return completion.choices[0].message.content.strip()


# =============================================================================
# REQUEST MODELS
# =============================================================================

class ScoreRequest(BaseModel):
    challenge_id: str  # "prompt_hardening" or "waf_rules"
    level: int = 1
    participant_name: str = "Anonymous"
    system_prompt: Optional[str] = None
    rules_text: Optional[str] = None
    exam_token: Optional[str] = None


class ExamValidateRequest(BaseModel):
    token: str


class TheorySubmission(BaseModel):
    token: str
    mcq_answers: dict[str, str] = {}
    short_answers: list[dict] = []


class PipelineRequest(BaseModel):
    participant_name: str = "Anonymous"
    pipeline: dict[str, bool]  # {"input": true, "context": false, ...}


class BehavioralTestRequest(BaseModel):
    test_prompt: str
    category: str  # "bias", "toxicity", "pii", "instruction", "refusal", "accuracy"
    session_id: str
    participant_name: str = "Anonymous"


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
# FASTAPI APP
# =============================================================================

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Blue Team Workshop")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# =============================================================================
# EXAM HELPERS
# =============================================================================

def _get_exam_data(variant: str):
    """Return exam challenges module for the given dataset variant."""
    if variant == "exam_v1":
        try:
            import exam_challenges_v1
            return exam_challenges_v1
        except ImportError:
            pass
    elif variant == "exam_v2":
        try:
            import exam_challenges_v2
            return exam_challenges_v2
        except ImportError:
            pass
    return None


def _resolve_exam_session(exam_token_value: str, exercise_id: str):
    """Validate token + check attempt cap. Returns (session, None) or (None, error_response)."""
    if not EXAM_ENABLED:
        return None, JSONResponse(status_code=503, content={"error": "Exam infrastructure not deployed"})
    try:
        payload = validate_token(exam_token_value, EXAM_SECRET, LAB_ID)
    except InvalidTokenError as e:
        return None, JSONResponse(status_code=401, content={"error": str(e)})

    session = _SESSIONS.get(exam_token_value)
    if not session:
        return None, JSONResponse(
            status_code=403,
            content={"error": "Exam session not initialized. POST /api/exam/validate first."},
        )

    if session.is_paused():
        return None, JSONResponse(status_code=403, content={"error": "Exam is paused by instructor"})

    cap = session.attempt_caps.get(exercise_id)
    if cap is not None and session.attempt_count(exercise_id) >= cap:
        return None, JSONResponse(
            status_code=429,
            content={
                "error": "Attempt cap reached",
                "exercise_id": exercise_id,
                "cap": cap,
                "used": session.attempt_count(exercise_id),
            },
        )
    return session, payload


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/challenges")
async def list_challenges():
    return {
        "challenges": [
            {
                "id": "prompt_hardening",
                "name": "Prompt Hardening",
                "description": "Write a system prompt that blocks attacks without breaking legitimate queries",
                "levels": len(LEVELS),
                "max_score": 120,
            },
            {
                "id": "waf_rules",
                "name": "WAF Rules",
                "description": "Write detection rules that catch attack payloads with minimal false positives",
                "max_score": 100,
            },
            {
                "id": "defense_pipeline",
                "name": "Defense Pipeline Builder",
                "description": "Assemble a defense pipeline — maximize coverage with minimum overhead",
                "max_score": 100,
            },
            {
                "id": "behavioral_testing",
                "name": "Model Behavioral Testing",
                "description": "Find 12 hidden vulnerabilities in a deployed AI assistant",
                "max_score": 160,
            },
        ],
        "default_prompt": DEFAULT_VULNERABLE_PROMPT,
        "pipeline_tools": PIPELINE_TOOLS,
        "vulnerability_categories": VULNERABILITY_CATEGORIES,
    }


@app.post("/api/score")
async def score_challenge(request: Request, req: ScoreRequest):
    """Run challenge scoring (prompt hardening or WAF rules)."""
    if req.challenge_id == "waf_rules":
        return await score_waf(request, req)
    return await score_prompt_hardening(request, req)


async def score_waf(request: Request, req: ScoreRequest):
    """Score WAF rules against attack + legit queries."""
    if not req.rules_text:
        raise HTTPException(400, "rules_text is required for waf_rules challenge")

    rules, errors = parse_rules(req.rules_text)
    if errors and not rules:
        raise HTTPException(400, f"No valid rules: {'; '.join(errors)}")

    # Evaluate against attacks
    tp, fn = 0, 0
    attack_details = []
    for i, prompt in enumerate(WAF_ATTACK_PROMPTS):
        blocked, matched = evaluate_rules(rules, prompt)
        if blocked:
            tp += 1
        else:
            fn += 1
        atk_name = list(ATTACKS.values())[i]["name"] if i < len(ATTACKS) else f"Attack {i+1}"
        attack_details.append({
            "query": prompt[:80] + "..." if len(prompt) > 80 else prompt,
            "type": "attack",
            "blocked": blocked,
            "correct": blocked,
            "matched_rule": f'Line {matched["line"]}: {matched["action"]} if {matched["mode"]} "{matched["pattern"][:30]}"' if matched else None,
        })

    # Evaluate against legit queries
    tn, fp = 0, 0
    legit_details = []
    for prompt in WAF_LEGIT_QUERIES:
        blocked, matched = evaluate_rules(rules, prompt)
        if blocked:
            fp += 1
        else:
            tn += 1
        legit_details.append({
            "query": prompt,
            "type": "legitimate",
            "blocked": blocked,
            "correct": not blocked,
            "matched_rule": f'Line {matched["line"]}: {matched["action"]} if {matched["mode"]} "{matched["pattern"][:30]}"' if matched else None,
        })

    scoring = calculate_waf_score(tp, fp, tn, fn)
    preview = _is_preview(request)
    rank = None if preview else update_leaderboard(req.participant_name, "waf_rules", scoring["total"])

    result = {
        "challenge_id": "waf_rules",
        "score": scoring["total"],
        "breakdown": scoring,
        "baseline": PG2_BASELINE,
        "beat_baseline": scoring["f1"] > PG2_BASELINE["f1"],
        "rules_count": len(rules),
        "parse_errors": errors,
        "details": attack_details + legit_details,
        "preview_mode": preview,
    }
    if rank is not None:
        result["leaderboard_rank"] = rank
    return result


async def score_prompt_hardening(request: Request, req: ScoreRequest):
    """Run attacks against participant's hardened prompt and score results."""
    if req.challenge_id != "prompt_hardening":
        raise HTTPException(400, "Only prompt_hardening is available")

    preview = _is_preview(request)

    # Resolve exam session and dataset
    exam_session = None
    exam_data = None
    if req.exam_token and EXAM_ENABLED and not preview:
        exam_session, result_or_payload = _resolve_exam_session(req.exam_token, "prompt_hardening")
        if exam_session is None:
            return result_or_payload
        exam_data = _get_exam_data(exam_session.dataset_variant)

    active_levels = exam_data.EXAM_LEVELS if exam_data else LEVELS
    active_legit = exam_data.EXAM_LEGIT_QUERIES if exam_data else LEGIT_QUERIES
    active_conf_block = exam_data.EXAM_CONFIDENTIAL_BLOCK if exam_data else CONFIDENTIAL_BLOCK
    active_attacks_dict = exam_data.EXAM_ATTACKS_V1 if exam_data and hasattr(exam_data, "EXAM_ATTACKS_V1") else (
        exam_data.EXAM_ATTACKS_V2 if exam_data and hasattr(exam_data, "EXAM_ATTACKS_V2") else ATTACKS
    )

    if req.level not in active_levels:
        raise HTTPException(400, f"Invalid level: {req.level}. Valid: 1-{len(active_levels)}")

    level = active_levels[req.level]
    attack_ids = level["attacks"]
    start_time = time.time()

    # Build the full system prompt: participant's prompt + confidential block
    full_system = req.system_prompt + "\
" + active_conf_block

    # Run attacks
    attack_results = []
    attacks_blocked = 0

    for atk_id in attack_ids:
        atk = active_attacks_dict.get(atk_id) or ATTACKS.get(atk_id, {})
        try:
            messages = [{"role": "system", "content": full_system}]

            # Add context if attack has it (indirect injection)
            if "context" in atk:
                messages[0]["content"] += "\
\
Retrieved context:\
" + atk["context"]

            messages.append({"role": "user", "content": atk["prompt"]})

            output = generate_response(messages)
            succeeded = atk["check"](output)
            blocked = not succeeded
            if blocked:
                attacks_blocked += 1

            attack_results.append({
                "id": atk_id,
                "name": atk["name"],
                "type": "attack",
                "blocked": blocked,
                "prompt": atk["prompt"][:100] + "..." if len(atk["prompt"]) > 100 else atk["prompt"],
                "model_output": output[:300] + "..." if len(output) > 300 else output,
                "why": atk.get("why_blocked" if blocked else "why_failed", ""),
            })
        except Exception as e:
            logger.exception(f"Error running attack {atk_id}")
            attack_results.append({
                "id": atk_id,
                "name": atk["name"],
                "type": "attack",
                "blocked": False,
                "prompt": atk["prompt"][:100],
                "model_output": f"Error: {e}",
            })

    # Run legitimate queries
    legit_results = []
    legit_passed = 0

    for query in active_legit:
        try:
            messages = [
                {"role": "system", "content": full_system},
                {"role": "user", "content": query["prompt"]},
            ]
            output = generate_response(messages)
            passed = check_legit_passed(output, query)
            if passed:
                legit_passed += 1

            legit_results.append({
                "id": query["id"],
                "type": "legitimate",
                "passed": passed,
                "prompt": query["prompt"],
                "model_output": output[:300] + "..." if len(output) > 300 else output,
            })
        except Exception as e:
            legit_results.append({
                "id": query["id"],
                "type": "legitimate",
                "passed": False,
                "prompt": query["prompt"],
                "model_output": f"Error: {e}",
            })

    elapsed = time.time() - start_time

    # Calculate score
    scoring = calculate_score(
        attacks_blocked=attacks_blocked,
        attacks_total=len(attack_ids),
        legit_passed=legit_passed,
        legit_total=len(active_legit),
        elapsed_seconds=elapsed,
    )

    # Check if next level unlocked
    pct = round((attacks_blocked / max(len(attack_ids), 1)) * 100)
    next_level = req.level + 1 if pct >= level["unlock_threshold"] and req.level < len(active_levels) else req.level

    # Record exam attempt (skipped in preview mode)
    if exam_session is not None and not preview:
        exam_session.record_attempt(
            "prompt_hardening",
            success=scoring["total"] > 0,
            score=scoring["total"],
            metadata={
                "level": req.level,
                "attacks_blocked": attacks_blocked,
                "attacks_total": len(attack_ids),
            },
        )

    # Update leaderboard (workshop mode only, not in preview mode)
    rank = None
    if not exam_session and not preview:
        rank = update_leaderboard(req.participant_name, req.challenge_id, scoring["total"])

    # Get hint if score is low
    hint = None
    if pct < level["unlock_threshold"]:
        hints = level.get("hints", [])
        if hints:
            hint = hints[attacks_blocked % len(hints)]

    result = {
        "challenge_id": req.challenge_id,
        "level": req.level,
        "level_name": level["name"],
        "score": scoring["total"],
        "breakdown": {
            "attacks_blocked": attacks_blocked,
            "attacks_total": len(attack_ids),
            "legit_passed": legit_passed,
            "legit_total": len(active_legit),
            **scoring,
        },
        "details": attack_results + legit_results,
        "level_unlocked": next_level,
        "hint": hint,
        "elapsed_seconds": round(elapsed, 1),
        "preview_mode": preview,
    }
    if rank is not None:
        result["leaderboard_rank"] = rank
    if exam_session is not None and not preview:
        result["attempts_used"] = exam_session.attempt_count("prompt_hardening")
        result["attempts_cap"] = exam_session.attempt_caps.get("prompt_hardening")
    return result


@app.post("/api/pipeline-eval")
async def pipeline_eval(request: Request, req: PipelineRequest):
    """Evaluate a defense pipeline against all attacks using the effectiveness matrix."""
    eval_result = evaluate_pipeline(req.pipeline)
    scoring = calculate_pipeline_score(
        eval_result["attacks_blocked"],
        eval_result["attacks_total"],
        eval_result["total_latency_ms"],
        eval_result["cost_per_request"],
    )

    # Compare with presets
    comparison = {}
    for preset_name, preset_config in PIPELINE_PRESETS.items():
        preset_eval = evaluate_pipeline(preset_config)
        preset_score = calculate_pipeline_score(
            preset_eval["attacks_blocked"], preset_eval["attacks_total"],
            preset_eval["total_latency_ms"], preset_eval["cost_per_request"],
        )
        comparison[preset_name] = {
            "coverage": preset_eval["coverage"],
            "score": preset_score["total"],
        }
    comparison["participant"] = {
        "coverage": eval_result["coverage"],
        "score": scoring["total"],
    }

    preview = _is_preview(request)
    rank = None if preview else update_leaderboard(req.participant_name, "defense_pipeline", scoring["total"])

    return {
        "challenge_id": "defense_pipeline",
        "score": scoring["total"],
        "max_score": 100,
        "breakdown": {
            "attacks_blocked": eval_result["attacks_blocked"],
            "attacks_total": eval_result["attacks_total"],
            "coverage": eval_result["coverage"],
            **scoring,
        },
        "pipeline_summary": {
            "tools_enabled": eval_result["tools_enabled"],
            "stages_active": eval_result["stages_active"],
            "total_latency_ms": eval_result["total_latency_ms"],
            "cost_per_request": eval_result["cost_per_request"],
        },
        "attack_results": eval_result["attack_results"],
        "comparison": comparison,
        "leaderboard_rank": rank,
        "preview_mode": preview,
    }


@app.post("/api/behavioral-test")
async def behavioral_test(request: Request, req: BehavioralTestRequest):
    """Run a behavioral test prompt against the vulnerable NexaCore assistant."""
    if req.category not in VULNERABILITY_CATEGORIES:
        raise HTTPException(400, f"Invalid category: {req.category}. Valid: {list(VULNERABILITY_CATEGORIES.keys())}")

    session = get_behavioral_session(req.session_id)
    session["queries"] += 1

    # Call Groq with the vulnerable system prompt
    try:
        messages = [
            {"role": "system", "content": VULNERABLE_ASSISTANT_PROMPT},
            {"role": "user", "content": req.test_prompt},
        ]
        model_output = generate_response(messages)
    except Exception as e:
        logger.exception("Behavioral test Groq call failed")
        raise HTTPException(500, f"Model call failed: {e}")

    # Check for triggered vulnerabilities in the selected category
    triggered = check_vulnerabilities(model_output, req.category)

    # Filter to only new discoveries
    new_discoveries = [v for v in triggered if v["id"] not in session["found"]]
    for v in new_discoveries:
        session["found"].append(v["id"])

    # Build category progress
    category_progress = {}
    for cat_id in VULNERABILITY_CATEGORIES:
        total_in_cat = sum(1 for v in VULNERABILITIES.values() if v["category"] == cat_id)
        found_in_cat = sum(1 for vid in session["found"] if VULNERABILITIES[vid]["category"] == cat_id)
        category_progress[cat_id] = [found_in_cat, total_in_cat]

    scoring = calculate_behavioral_score(len(session["found"]), session["queries"])

    # Update leaderboard if score improved (skip in preview mode)
    if scoring["total"] > 0 and not _is_preview(request):
        update_leaderboard(req.participant_name, "behavioral_testing", scoring["total"])

    # Get hint if no vulnerability found
    hint = None
    if not triggered:
        # Find unfound vulns in this category
        unfound = [v for vid, v in VULNERABILITIES.items()
                    if v["category"] == req.category and vid not in session["found"]]
        if unfound:
            hint = unfound[0]["hint"]

    return {
        "model_output": model_output,
        "vulnerabilities_found": [{"id": v["id"], "name": v["name"], "is_new": v["id"] not in [d["id"] for d in new_discoveries]} for v in triggered],
        "new_discoveries": [{"id": v["id"], "name": v["name"]} for v in new_discoveries],
        "total_found": len(session["found"]),
        "total_queries": session["queries"],
        "category_progress": category_progress,
        "score": scoring,
        "hint": hint,
        "preview_mode": _is_preview(request),
    }


@app.get("/api/behavioral-progress/{session_id}")
async def behavioral_progress(session_id: str):
    """Get current progress for a behavioral testing session."""
    session = get_behavioral_session(session_id)
    category_progress = {}
    for cat_id in VULNERABILITY_CATEGORIES:
        total_in_cat = sum(1 for v in VULNERABILITIES.values() if v["category"] == cat_id)
        found_in_cat = sum(1 for vid in session["found"] if VULNERABILITIES[vid]["category"] == cat_id)
        category_progress[cat_id] = [found_in_cat, total_in_cat]

    scoring = calculate_behavioral_score(len(session["found"]), session["queries"])
    return {
        "total_found": len(session["found"]),
        "total_queries": session["queries"],
        "category_progress": category_progress,
        "score": scoring,
    }


@app.get("/api/leaderboard")
async def leaderboard():
    return {"leaderboard": get_leaderboard()}


@app.get("/health")
async def health():
    has_key = bool(os.environ.get("GROQ_API_KEY"))
    return {
        "status": "ok" if has_key else "missing_api_key",
        "model": GROQ_MODEL,
        "exam_enabled": EXAM_ENABLED and bool(EXAM_SECRET),
    }


# =============================================================================
# EXAM ROUTES
# =============================================================================

@app.post("/api/exam/validate")
async def exam_validate(req: ExamValidateRequest):
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

    mcq_scored: dict = {}
    try:
        from exam_questions import score_mcq
        mcq_scored = score_mcq(LAB_ID, req.mcq_answers)
    except ImportError:
        pass

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

    scored_mcq_list: list[dict] = []
    if session.theory_submitted():
        try:
            from exam_questions import QUESTION_BANKS, score_mcq
            stored_mcq = session._theory.get("mcq_answers", [])
            mcq_dict = {item["question_id"]: item["answer"] for item in stored_mcq}
            score_result = score_mcq(LAB_ID, mcq_dict)
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
                    "points_earned": score_result[qid].get("points_earned", 0),
                    "correct": score_result[qid].get("correct", False),
                    "student_answer": mcq_dict.get(qid),
                    "correct_answer": correct_opt.get("key"),
                })
        except ImportError:
            pass

    short_answers_for_receipt = []
    if session.theory_submitted():
        try:
            from exam_questions import QUESTION_BANKS
            bank_sa = {q["id"]: q for q in QUESTION_BANKS.get(LAB_ID, {}).get("short_answers", [])}
            stored_sa = session._theory.get("short_answers", [])
            for item in stored_sa:
                qid = item.get("question_id", "")
                q = bank_sa.get(qid, {})
                short_answers_for_receipt.append({
                    "question_id": qid,
                    "bloom_level": q.get("bloom_level"),
                    "points_possible": q.get("points", 20),
                    "student_response": item.get("response", ""),
                    "word_count": len(item.get("response", "").split()),
                    "points_earned": None,
                })
        except ImportError:
            pass

    receipt_payload = {
        "receipt_version": "1",
        "exam_id": payload["exam_id"],
        "student_id": payload["student_id"],
        "lab_id": LAB_ID,
        "practical": practical,
        "theory": {
            "mcq": scored_mcq_list,
            "short_answers": short_answers_for_receipt,
            "mcq_score": sum(e.get("points_earned", 0) for e in scored_mcq_list),
            "mcq_max": 50,
            "short_answer_max": 60,
            "short_answer_requires_instructor_grading": True,
        },
        "timing": {
            "total_elapsed_seconds": session.elapsed_seconds(),
            "time_limit_seconds": payload.get("time_limit_seconds", 7200),
        },
    }
    receipt_payload["hmac_sha256"] = sign_receipt(receipt_payload, EXAM_SECRET)
    return receipt_payload


@app.get("/api/exam/status")
async def exam_status(token: str):
    if not EXAM_ENABLED:
        raise HTTPException(503, "Exam mode not available")
    try:
        payload = validate_token(token, EXAM_SECRET, LAB_ID)
    except InvalidTokenError as e:
        raise HTTPException(401, str(e))

    session = _SESSIONS.get(token)
    if not session:
        return {"initialized": False}

    exercise_status = {}
    for defn in EXERCISE_DEFINITIONS:
        eid = defn["exercise_id"]
        exercise_status[eid] = {
            "attempts_used": session.attempt_count(eid),
            "cap": session.attempt_caps.get(eid),
            "best_score": session._scores.get(eid, 0),
        }
    return {
        "initialized": True,
        "elapsed_seconds": session.elapsed_seconds(),
        "remaining_seconds": session.remaining_seconds(),
        "paused": session.is_paused(),
        "theory_submitted": session.theory_submitted(),
        "exercises": exercise_status,
    }


# =============================================================================
# ADMIN ROUTES (exam-admin proxy target, requires X-Exam-Secret header)
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
