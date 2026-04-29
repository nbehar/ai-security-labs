"""Data Poisoning Lab — FastAPI app (Phase 4a: full API surface).

v1 scope: RP.1 — RP.6 RAG poisoning attacks anchored in the NexaCore Knowledge
Hub scenario. Stack: Groq LLaMA 3.3 70B + sentence-transformers MiniLM-L6
in-process embeddings + in-memory cosine retrieval. See `specs/` for the
full design.

Phase 1 + 3 + 4a endpoints (the full 9 specced):
  GET  /                        - placeholder shell with Luminex master nav
  GET  /health                  - readiness probe
  GET  /api/attacks             - list 6 RP attack defs
  GET  /api/queries             - list 6 employee queries
  GET  /api/corpus              - list all corpus docs (metadata)
  GET  /api/corpus/{doc_id}     - full markdown body for one doc
  POST /api/attack              - run a canned or uploaded RAG attack with optional defenses
  POST /api/score               - record a participant score
  GET  /api/leaderboard         - aggregated participant rankings (in-memory; instructor inspection)

Phase 4b ships the full SPA (4 tabs).

Workshop by Prof. Nikolas Behar.
Tracking: issue #22.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from typing import Literal, Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from attacks import ATTACKS, QUERIES
from corpus import CORPUS, EMBEDDING_MODEL, Document
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
# Upload validation (Phase 4a). Inlined per Multimodal Lab precedent.
# ---------------------------------------------------------------------------

UPLOAD_MAX_BYTES = 16 * 1024  # 16 KB cap per spec
UPLOAD_MAX_WORDS = 1500       # word-count cap per spec
ALLOWED_CONTENT_TYPES = {
    "text/plain",
    "text/markdown",
    "application/pdf",
    "application/octet-stream",  # browsers sometimes send this for .md
}


def _validate_uploaded_doc(content: bytes, content_type: str | None, filename: str | None) -> str:
    """Validate an uploaded document and return its text body.

    Raises HTTPException(400) on validation failure. In-memory only — never
    writes to disk. PDFs are text-extracted via `pypdf`; Markdown / plain text
    are decoded as UTF-8 with a BOM-tolerant fallback.
    """
    if len(content) > UPLOAD_MAX_BYTES:
        raise HTTPException(
            400,
            f"Uploaded doc exceeds {UPLOAD_MAX_BYTES} bytes ({len(content)} bytes received)",
        )
    if not content:
        raise HTTPException(400, "Uploaded doc is empty")

    ct = (content_type or "").lower()
    fname = (filename or "").lower()
    is_pdf = content.startswith(b"%PDF-") or ct == "application/pdf" or fname.endswith(".pdf")

    if is_pdf:
        # Magic-bytes guard: if content-type says PDF but bytes don't, reject.
        if not content.startswith(b"%PDF-"):
            raise HTTPException(400, "PDF upload failed magic-bytes check (file does not start with %PDF-)")
        try:
            from pypdf import PdfReader
            from io import BytesIO
            reader = PdfReader(BytesIO(content))
            text = "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()
        except Exception as e:
            raise HTTPException(400, f"PDF text extraction failed: {type(e).__name__}: {e}")
        if not text:
            raise HTTPException(400, "PDF contained no extractable text")
    else:
        # Plain text or Markdown — decode as UTF-8, tolerate BOM.
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as e:
            raise HTTPException(400, f"Uploaded doc is not valid UTF-8: {e}")
        # Reject if content-type is set to something we don't accept.
        if ct and ct not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                400,
                f"Unsupported content-type: {ct}. Allowed: text/plain, text/markdown, application/pdf",
            )

    word_count = len(text.split())
    if word_count > UPLOAD_MAX_WORDS:
        raise HTTPException(
            400,
            f"Uploaded doc exceeds {UPLOAD_MAX_WORDS} words ({word_count} received)",
        )
    return text


# ---------------------------------------------------------------------------
# In-memory leaderboard (Phase 4a). Same shape as Multimodal Lab; resets on
# Space restart. Phase 6 will route scores through Canvas LMS instead.
# ---------------------------------------------------------------------------

# participant_name -> {"by_attack": {RP.x: int}, "attacks_completed": int}
_LEADERBOARD: dict[str, dict] = {}
_LEADERBOARD_LOCK = threading.Lock()


def _attack_score(attempts: int, succeeded: bool, defenses_applied: list[str]) -> int:
    """Per-attack score per spec.

    100 first try, -20 per retry, floor 20. +50 bonus when a defense blocked
    an attack that would have succeeded.
    """
    base = max(20, 100 - 20 * (attempts - 1))
    if not succeeded and defenses_applied:
        base += 50
    return base


def _record_score(participant: str, attack_id: str, score_added: int) -> tuple[int, int]:
    """Add a score to the leaderboard; return (running_total, rank)."""
    with _LEADERBOARD_LOCK:
        entry = _LEADERBOARD.setdefault(
            participant, {"by_attack": {}, "attacks_completed": 0}
        )
        is_new_attack = attack_id not in entry["by_attack"]
        entry["by_attack"][attack_id] = entry["by_attack"].get(attack_id, 0) + score_added
        if is_new_attack:
            entry["attacks_completed"] += 1
        running_total = sum(entry["by_attack"].values())
        # Rank by total score descending; ties broken by attacks_completed descending.
        sorted_entries = sorted(
            _LEADERBOARD.items(),
            key=lambda kv: (-sum(kv[1]["by_attack"].values()), -kv[1]["attacks_completed"], kv[0]),
        )
        rank = next(i + 1 for i, (n, _) in enumerate(sorted_entries) if n == participant)
    return running_total, rank


# ---------------------------------------------------------------------------
# Pydantic schemas (Phase 4a) — verbatim from `specs/api_spec.md`.
# ---------------------------------------------------------------------------

class ScoreRequest(BaseModel):
    participant_name: str = Field(..., min_length=1, max_length=64)
    attack_id: str
    succeeded: bool
    defenses_applied: list[str] = []
    attempts: int = Field(default=1, ge=1)


class ScoreResponse(BaseModel):
    score_added: int
    running_total: int
    rank: int


# ---------------------------------------------------------------------------
# App + static + templates + rate limiter
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Data Poisoning Lab", version="0.4-phase4a")
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
        # Don't crash the app on startup if MiniLM fails to load - /health
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
        "phase": 4,
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


@app.get("/api/queries")
async def list_queries():
    """Return the 6 legitimate employee queries each attack targets."""
    return {
        "queries": [
            {
                "id": q["id"],
                "text": q["text"],
                "department": q["department"],
                "expected_legit_doc_id": q["expected_legit_doc_id"],
            }
            for q in QUERIES.values()
        ]
    }


@app.get("/api/corpus")
async def list_corpus():
    """Return metadata for every corpus doc (legit + canned attack)."""
    return {"documents": [d.metadata() for d in CORPUS.all_documents()]}


@app.get("/api/corpus/{doc_id}")
async def get_corpus_doc(doc_id: str):
    """Return the full markdown body of one corpus doc; 404 if unknown."""
    doc = CORPUS.get(doc_id)
    if doc is None:
        raise HTTPException(404, f"Unknown document: {doc_id}")
    return {
        "id": doc.id,
        "title": doc.title,
        "department": doc.department,
        "kind": doc.kind,
        "body_markdown": doc.body_markdown,
    }


@app.post("/api/attack")
@limiter.limit("10/minute")
async def post_attack(
    request: Request,
    attack_id: str = Form(...),
    doc_source: str = Form("canned"),
    defenses: Optional[str] = Form(None),
    participant_name: str = Form("Anonymous"),
    target_query_id: Optional[str] = Form(None),
    doc_file: Optional[UploadFile] = File(None),
):
    """Run a canned or uploaded RAG poisoning attack with optional defenses.

    `doc_source=canned`: `attack_id` must be RP.1—RP.6.
    `doc_source=uploaded`: `attack_id` must be `"custom"`, `target_query_id`
    must be one of the 6 employee query IDs, `doc_file` is a PDF/Markdown/
    plain-text upload (<=16KB, <=1500 words; in-memory only). With
    `provenance_check` enabled, every uploaded attack is BLOCKED at ingestion
    by design (uploaded source `(user upload)` fails the trusted-sources
    allowlist).
    """
    # Conditional attack_id guard (Phase 4a reviewer fix #2 — must dispatch on
    # doc_source before validating attack_id, otherwise upload mode 400s).
    if doc_source == "canned":
        if attack_id not in ATTACKS:
            raise HTTPException(400, f"Unknown attack: {attack_id}")
    elif doc_source == "uploaded":
        if attack_id != "custom":
            raise HTTPException(
                400,
                "Upload mode requires attack_id='custom' (got %r)" % attack_id,
            )
        if not target_query_id:
            raise HTTPException(400, "Upload mode requires target_query_id")
        if target_query_id not in QUERIES:
            raise HTTPException(
                400,
                f"Unknown target_query_id: {target_query_id}. "
                f"Valid: {sorted(QUERIES.keys())}",
            )
        if doc_file is None:
            raise HTTPException(400, "Upload mode requires doc_file")
    else:
        raise HTTPException(400, f"Unknown doc_source: {doc_source}")

    if not GROQ_API_KEY:
        raise HTTPException(503, "GROQ_API_KEY is not configured on this Space")

    parsed_defenses: list[str] = []
    if defenses:
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

    # Build optional uploaded-doc kwarg
    uploaded_doc: Optional[Document] = None
    if doc_source == "uploaded":
        content = await doc_file.read()
        text = _validate_uploaded_doc(content, doc_file.content_type, doc_file.filename)
        uploaded_doc = Document.create_uploaded(text, title=doc_file.filename or "(user upload)")

    try:
        result = run_attack(
            attack_id,
            get_groq_client(),
            defenses=parsed_defenses,
            uploaded_doc=uploaded_doc,
            query_id=target_query_id if doc_source == "uploaded" else None,
        )
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))

    result["participant_name"] = participant_name
    result["phase"] = 4
    return result


@app.post("/api/score", response_model=ScoreResponse)
async def post_score(req: ScoreRequest):
    """Record a participant score. Returns running total + rank."""
    score_added = _attack_score(req.attempts, req.succeeded, req.defenses_applied)
    running_total, rank = _record_score(req.participant_name, req.attack_id, score_added)
    return ScoreResponse(score_added=score_added, running_total=running_total, rank=rank)


@app.get("/api/leaderboard")
async def get_leaderboard():
    """Aggregated participant rankings. In-memory; resets on Space restart.

    Frontend doesn't render this (no leaderboard tab per `frontend_spec.md`);
    preserved for instructor inspection during workshops + Phase 6 Canvas
    integration.
    """
    with _LEADERBOARD_LOCK:
        entries = []
        for name, data in _LEADERBOARD.items():
            total = sum(data["by_attack"].values())
            entries.append({
                "participant_name": name,
                "total_score": total,
                "attacks_completed": data["attacks_completed"],
                "by_attack": dict(data["by_attack"]),
            })
        entries.sort(key=lambda e: (-e["total_score"], -e["attacks_completed"], e["participant_name"]))
    return {"entries": entries}