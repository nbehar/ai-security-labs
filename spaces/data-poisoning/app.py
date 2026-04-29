"""Data Poisoning Lab — FastAPI app (Phase 1: backend skeleton).

v1 scope: RP.1 — RP.6 RAG poisoning attacks anchored in the NexaCore Knowledge
Hub scenario. Stack: Groq LLaMA 3.3 70B + sentence-transformers MiniLM-L6
in-process embeddings + in-memory cosine retrieval. See `specs/` for the
full design.

Phase 1 + Phase 3 endpoints (subset of the 9 specced):
  GET  /                   — placeholder shell with Luminex master nav
  GET  /health             — readiness probe
  GET  /api/attacks        — list 6 RP attack defs
  POST /api/attack         — run a canned RAG attack with optional defenses

Phase 4a will add /api/score, /api/leaderboard, /api/corpus, /api/queries,
and upload mode. Phase 4b ships the full SPA.

Workshop by Prof. Nikolas Behar.
Tracking: issue #22.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from attacks import ATTACKS, QUERIES
from corpus import CORPUS, EMBEDDING_MODEL
from defenses import DEFENSE_IDS
from rag_pipeline import LLM_MODEL, run_attack

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Lazily-constructed Groq client. Created on first use so the import path
# doesn't fail when the secret is missing (the /health endpoint must still
# respond).
_groq_client = None
_groq_lock = threading.Lock()


def get_groq_client():
    global _groq_client
    if _groq_client is None:
        with _groq_lock:
            if _groq_client is None:
                if not GROQ_API_KEY:
                    raise HTTPException(503, "GROQ_API_KEY is not configured on this Space")
                from groq import Groq
                _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client


# ---------------------------------------------------------------------------
# App + static + templates + rate limiter
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Data Poisoning Lab", version="0.3-phase3")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def warm_corpus():
    """Encode the corpus at startup so the first /api/attack is hot."""
    try:
        CORPUS.warm()
    except Exception:
        # Don't crash the app on startup if MiniLM fails to load — /health
        # will surface `embeddings_loaded: false` and the user can debug.
        logger.exception("Corpus warm-encoding failed; continuing without it")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "groq_api_key_set": bool(GROQ_API_KEY),
        "embedding_model": EMBEDDING_MODEL,
        "llm_model": LLM_MODEL,
        "attack_count": len(ATTACKS),
        "corpus_size": len(CORPUS.all_documents()),
        "embeddings_loaded": CORPUS.is_warm(),
        "defenses_available": sorted(DEFENSE_IDS),
        "phase": 3,
    }


@app.get("/api/attacks")
async def list_attacks():
    return {
        "attacks": [
            {
                "id": a["id"],
                "name": a["name"],
                "owasp": a["owasp"],
                "difficulty": a["difficulty"],
                "description": a["description"],
                "success_check": a["success_check"],
                "canary": a["canary"],
                "target_query": QUERIES[a["target_query_id"]]["text"],
                "expected_legit_doc_id": a["expected_legit_doc_id"],
                "poisoned_doc_id": a["poisoned_doc_id"],
            }
            for a in ATTACKS.values()
        ]
    }


@app.post("/api/attack")
@limiter.limit("10/minute")
async def post_attack(
    request: Request,
    attack_id: str = Form(...),
    doc_source: str = Form("canned"),
    defenses: Optional[str] = Form(None),
    participant_name: str = Form("Anonymous"),
):
    """Run a canned RAG poisoning attack with optional toggleable defenses.

    Phase 4a will add `doc_source=uploaded` mode + Pydantic-validated upload.
    """
    if attack_id not in ATTACKS:
        raise HTTPException(400, f"Unknown attack: {attack_id}")
    if doc_source != "canned":
        raise HTTPException(400, "Only 'canned' doc_source supported in Phase 1+3")
    if not GROQ_API_KEY:
        raise HTTPException(503, "GROQ_API_KEY is not configured on this Space")

    parsed_defenses: list[str] = []
    if defenses:
        import json
        try:
            parsed_defenses = json.loads(defenses)
        except json.JSONDecodeError as e:
            raise HTTPException(400, f"Bad defenses field (must be JSON array): {e}")
        if not isinstance(parsed_defenses, list):
            raise HTTPException(400, "defenses must be a JSON array of defense IDs")
        unknown = [d for d in parsed_defenses if d not in DEFENSE_IDS]
        if unknown:
            raise HTTPException(
                400,
                f"Unknown defense ID(s): {unknown}. Valid: {sorted(DEFENSE_IDS)}",
            )

    try:
        result = run_attack(attack_id, get_groq_client(), defenses=parsed_defenses)
    except RuntimeError as e:
        raise HTTPException(503, str(e))

    result["participant_name"] = participant_name
    result["phase"] = 3
    return result
