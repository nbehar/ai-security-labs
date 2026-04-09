"""
Blue Team Workshop — Interactive Defense Lab
=============================================
Participants write defense prompts, WAF rules, and defense pipelines
to block OWASP LLM Top 10 attacks against NexaCore Technologies.

Workshop by Prof. Nikolas Behar
Deploy: HuggingFace Spaces (Docker)
"""

import logging
import os
import time
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from groq import Groq
from pydantic import BaseModel

from challenges import (
    ATTACKS, LEVELS, LEGIT_QUERIES, CONFIDENTIAL_BLOCK,
    DEFAULT_VULNERABLE_PROMPT, check_legit_passed, calculate_score,
    update_leaderboard, get_leaderboard,
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
    challenge_id: str  # "prompt_hardening"
    level: int = 1
    participant_name: str = "Anonymous"
    system_prompt: str


# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(title="Blue Team Workshop")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


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
        ],
        "default_prompt": DEFAULT_VULNERABLE_PROMPT,
    }


@app.post("/api/score")
async def score_challenge(req: ScoreRequest):
    """Run attacks against participant's hardened prompt and score results."""
    if req.challenge_id != "prompt_hardening":
        raise HTTPException(400, "Only prompt_hardening is available")

    if req.level not in LEVELS:
        raise HTTPException(400, f"Invalid level: {req.level}. Valid: 1-{len(LEVELS)}")

    level = LEVELS[req.level]
    attack_ids = level["attacks"]
    start_time = time.time()

    # Build the full system prompt: participant's prompt + confidential block
    full_system = req.system_prompt + "\n" + CONFIDENTIAL_BLOCK

    # Run attacks
    attack_results = []
    attacks_blocked = 0

    for atk_id in attack_ids:
        atk = ATTACKS[atk_id]
        try:
            messages = [{"role": "system", "content": full_system}]

            # Add context if attack has it (indirect injection)
            if "context" in atk:
                messages[0]["content"] += "\n\nRetrieved context:\n" + atk["context"]

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

    for query in LEGIT_QUERIES:
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
        legit_total=len(LEGIT_QUERIES),
        elapsed_seconds=elapsed,
    )

    # Check if next level unlocked
    pct = round((attacks_blocked / max(len(attack_ids), 1)) * 100)
    next_level = req.level + 1 if pct >= level["unlock_threshold"] and req.level < len(LEVELS) else req.level

    # Update leaderboard
    rank = update_leaderboard(req.participant_name, req.challenge_id, scoring["total"])

    # Get hint if score is low
    hint = None
    if pct < level["unlock_threshold"]:
        hints = level.get("hints", [])
        if hints:
            hint = hints[attacks_blocked % len(hints)]

    return {
        "challenge_id": req.challenge_id,
        "level": req.level,
        "level_name": level["name"],
        "score": scoring["total"],
        "breakdown": {
            "attacks_blocked": attacks_blocked,
            "attacks_total": len(attack_ids),
            "legit_passed": legit_passed,
            "legit_total": len(LEGIT_QUERIES),
            **scoring,
        },
        "details": attack_results + legit_results,
        "level_unlocked": next_level,
        "hint": hint,
        "leaderboard_rank": rank,
        "elapsed_seconds": round(elapsed, 1),
    }


@app.get("/api/leaderboard")
async def leaderboard():
    return {"leaderboard": get_leaderboard()}


@app.get("/health")
async def health():
    has_key = bool(os.environ.get("GROQ_API_KEY"))
    return {"status": "ok" if has_key else "missing_api_key", "model": GROQ_MODEL}
