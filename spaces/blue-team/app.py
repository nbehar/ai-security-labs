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
    WAF_ATTACK_PROMPTS, WAF_LEGIT_QUERIES, PG2_BASELINE, calculate_waf_score,
    update_leaderboard, get_leaderboard,
    PIPELINE_TOOLS, PIPELINE_PRESETS, evaluate_pipeline, calculate_pipeline_score,
    VULNERABILITIES, VULNERABILITY_CATEGORIES, VULNERABLE_ASSISTANT_PROMPT,
    get_behavioral_session, check_vulnerabilities, calculate_behavioral_score,
)
from waf_parser import parse_rules, evaluate_rules

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
    challenge_id: str  # "prompt_hardening" or "waf_rules"
    level: int = 1
    participant_name: str = "Anonymous"
    system_prompt: Optional[str] = None
    rules_text: Optional[str] = None


class PipelineRequest(BaseModel):
    participant_name: str = "Anonymous"
    pipeline: dict[str, bool]  # {"input": true, "context": false, ...}


class BehavioralTestRequest(BaseModel):
    test_prompt: str
    category: str  # "bias", "toxicity", "pii", "instruction", "refusal", "accuracy"
    session_id: str
    participant_name: str = "Anonymous"


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
async def score_challenge(req: ScoreRequest):
    """Run challenge scoring (prompt hardening or WAF rules)."""
    if req.challenge_id == "waf_rules":
        return await score_waf(req)
    return await score_prompt_hardening(req)


async def score_waf(req: ScoreRequest):
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
    rank = update_leaderboard(req.participant_name, "waf_rules", scoring["total"])

    return {
        "challenge_id": "waf_rules",
        "score": scoring["total"],
        "breakdown": scoring,
        "baseline": PG2_BASELINE,
        "beat_baseline": scoring["f1"] > PG2_BASELINE["f1"],
        "rules_count": len(rules),
        "parse_errors": errors,
        "details": attack_details + legit_details,
        "leaderboard_rank": rank,
    }


async def score_prompt_hardening(req: ScoreRequest):
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


@app.post("/api/pipeline-eval")
async def pipeline_eval(req: PipelineRequest):
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

    rank = update_leaderboard(req.participant_name, "defense_pipeline", scoring["total"])

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
    }


@app.post("/api/behavioral-test")
async def behavioral_test(req: BehavioralTestRequest):
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

    # Update leaderboard if score improved
    if scoring["total"] > 0:
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
    return {"status": "ok" if has_key else "missing_api_key", "model": GROQ_MODEL}
