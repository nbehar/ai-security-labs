"""
Red Team Workshop — Progressive AI Attack Lab
==============================================
Participants write attack prompts against progressively hardened LLMs.
Discover jailbreak techniques, extract secrets, and climb the leaderboard.

Workshop by Prof. Nikolas Behar
Deploy: HuggingFace Spaces (Docker)
"""

import logging
import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from groq import Groq
from pydantic import BaseModel

from challenges import (
    LEVELS, JAILBREAKS, JAILBREAK_TARGET_PROMPT, JAILBREAK_SECRETS,
    check_secret_found, update_leaderboard, get_leaderboard,
    scan_input, redact_output, record_jailbreak_result, get_heatmap,
)

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
# REQUEST MODELS
# =============================================================================

class RedTeamAttempt(BaseModel):
    level: int
    attack_prompt: str
    participant_name: str = "Anonymous"


class JailbreakTest(BaseModel):
    technique_id: str
    custom_prompt: Optional[str] = None
    participant_name: str = "Anonymous"


# =============================================================================
# STATE — per-session attempt tracking
# =============================================================================

_attempts: dict[str, dict[int, int]] = {}  # name -> {level: attempts}
_scores: dict[str, dict[int, int]] = {}    # name -> {level: score}


# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(title="Red Team Workshop")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


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
async def red_team_attempt(req: RedTeamAttempt):
    """Submit an attack prompt against a hardened level."""
    if req.level not in LEVELS:
        raise HTTPException(400, f"Invalid level: {req.level}")

    level = LEVELS[req.level]

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
            # Input blocked — don't even call the model
            hint = None
            if attempt_num >= 3:
                hints = level.get("hints", [])
                if hints:
                    hint = hints[min(attempt_num - 3, len(hints) - 1)]

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

        # Use potentially redacted output
        final_output = output_result["output"]
        was_redacted = output_result.get("redacted", False)

        # Check if secret was extracted (use original output for detection, but show redacted)
        found_in_original = secret.lower() in output.lower()
        found = found_in_original and not was_redacted

        # Score: max 100 on first attempt, decreasing
        score = 0
        if found:
            score = max(0, (6 - attempt_num) * 20)  # 100, 80, 60, 40, 20, 0
            if req.participant_name not in _scores:
                _scores[req.participant_name] = {}
            _scores[req.participant_name][req.level] = score
            update_leaderboard(req.participant_name, "red_team", sum(_scores[req.participant_name].values()))

        # Hint after 3 failed attempts
        hint = None
        if not found and attempt_num >= 3:
            hints = level.get("hints", [])
            if hints:
                hint = hints[min(attempt_num - 3, len(hints) - 1)]

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
            "blocked_by": "Output Redaction" if was_redacted and found_in_original else None,
        }
    except Exception as e:
        logger.exception(f"Error in red team attempt")
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
            }
            for jb_id, jb in JAILBREAKS.items()
        ],
    }


@app.post("/api/jailbreak-test")
async def test_jailbreak(req: JailbreakTest):
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

        # Track for heatmap
        record_jailbreak_result(req.technique_id, success)

        if success:
            score = len(found) * 25  # 25 pts per secret found
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
    """Get jailbreak technique effectiveness heatmap."""
    return {"techniques": get_heatmap()}


@app.get("/api/leaderboard")
async def leaderboard():
    return {"leaderboard": get_leaderboard()}


@app.get("/health")
async def health():
    has_key = bool(os.environ.get("GROQ_API_KEY"))
    return {"status": "ok" if has_key else "missing_api_key", "model": GROQ_MODEL}
