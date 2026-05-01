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
from fastapi.responses import HTMLResponse, JSONResponse
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

EXAM_ENABLED = False
try:
    from exam_token import InvalidTokenError, validate_token, sign_receipt
    from exam_session import AttemptCapError, _SESSIONS, get_or_create_session
    EXAM_ENABLED = True
except ImportError:
    pass

LAB_ID = "data-poisoning"
EXAM_SECRET = os.environ.get("EXAM_SECRET", "")
PREVIEW_TOKEN = os.environ.get("PREVIEW_TOKEN", "")
_ROSTER_MAP: dict[str, str] = {}

EXERCISE_DEFINITIONS = [
    {"exercise_id": f"rp{i}_v1", "display_name": f"RP{i} Exam A", "max_score": 100}
    for i in range(1, 7)
]

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

def _is_preview(request: Request) -> bool:
    if not PREVIEW_TOKEN:
        return False
    header = request.headers.get("X-Preview-Token", "")
    query = request.query_params.get("preview", "")
    return (header == PREVIEW_TOKEN) or (query == PREVIEW_TOKEN)


limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Data Poisoning Lab", version="0.4-phase4a")
from app_auth import add_auth_middleware, firebase_config_route
add_auth_middleware(app)
app.add_api_route("/api/firebase-config", firebase_config_route)
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
        "exam_enabled": EXAM_ENABLED and bool(EXAM_SECRET),
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
    attack_id: str = Form(default=""),
    exam_attack_id: Optional[str] = Form(None),
    exam_token: Optional[str] = Form(None),
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
    preview = _is_preview(request)

    # ---- Exam mode ----
    exam_session = None
    exam_attack = None
    if exam_token and exam_attack_id and EXAM_ENABLED and not preview:
        res = _resolve_exam_session(exam_token, exam_attack_id)
        if not isinstance(res, tuple):
            return res
        exam_session, active_data = res
        exam_attack = active_data.EXAM_ATTACKS.get(exam_attack_id)
        if not exam_attack:
            raise HTTPException(400, f"Unknown exam attack: {exam_attack_id}")
        # Override attack_id and doc_source for exam routing below
        attack_id = "exam_bypass"
        doc_source = "exam"
    # ---- End exam mode ----

    # Conditional attack_id guard (Phase 4a reviewer fix #2 — must dispatch on
    # doc_source before validating attack_id, otherwise upload mode 400s).
    if doc_source == "exam":
        pass  # validated above
    elif doc_source == "canned":
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
    elif doc_source == "exam" and exam_attack:
        d = exam_attack["doc"]
        uploaded_doc = Document(
            id=d["id"], title=d["title"], department=d["department"],
            source=d["source"], kind=d["kind"], body_markdown=d["body_markdown"],
            attack_id=exam_attack["id"],
        )

    try:
        effective_query_id = (
            exam_attack["target_query_id"] if doc_source == "exam"
            else (target_query_id if doc_source == "uploaded" else None)
        )
        effective_attack_id = "custom" if doc_source == "exam" else attack_id
        result = run_attack(
            effective_attack_id,
            get_groq_client(),
            defenses=parsed_defenses,
            uploaded_doc=uploaded_doc,
            query_id=effective_query_id,
        )
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))

    if doc_source == "exam" and exam_attack:
        exam_canary = exam_attack["canary"]
        result["canary"] = exam_canary
        result["succeeded"] = (
            result.get("blocked_by") is None
            and exam_canary.lower() in result.get("model_response", "").lower()
        )
        if exam_session is not None and not preview:
            prior = exam_session.attempt_count(exam_attack_id)
            score = _attack_score(prior + 1, result["succeeded"], parsed_defenses)
            exam_session.record_attempt(exam_attack_id, success=result["succeeded"], score=score)

    result["participant_name"] = participant_name
    result["phase"] = 4
    result["preview_mode"] = preview
    return result


@app.post("/api/score")
async def post_score(request: Request, req: ScoreRequest):
    """Record a participant score. Returns running total + rank."""
    preview = _is_preview(request)
    score_added = _attack_score(req.attempts, req.succeeded, req.defenses_applied)
    if not preview:
        running_total, rank = _record_score(req.participant_name, req.attack_id, score_added)
    else:
        running_total, rank = score_added, None
    return {"score_added": score_added, "running_total": running_total, "rank": rank, "preview_mode": preview}


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

# ---------------------------------------------------------------------------
# Exam helpers
# ---------------------------------------------------------------------------

def _get_exam_data(dataset_variant: str):
    if dataset_variant == "exam_v1":
        try:
            import exam_attacks_v1
            return exam_attacks_v1
        except ImportError:
            pass
    elif dataset_variant == "exam_v2":
        try:
            import exam_attacks_v2
            return exam_attacks_v2
        except ImportError:
            pass
    return None


def _resolve_exam_session(exam_token: str, exercise_id: str):
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


# ---------------------------------------------------------------------------
# Routes — exam
# ---------------------------------------------------------------------------

class ExamValidateRequest(BaseModel):
    token: str

class MCQAnswer(BaseModel):
    question_id: str
    answer: str

class ShortAnswerItem(BaseModel):
    question_id: str
    response: str

class TheorySubmitRequest(BaseModel):
    exam_token: str
    mcq_answers: list[MCQAnswer] = []
    short_answers: list[ShortAnswerItem] = []


@app.post("/api/exam/validate")
@limiter.limit("20/minute")
async def exam_validate(request: Request, body: ExamValidateRequest):
    if not EXAM_ENABLED:
        return JSONResponse(status_code=503, content={"detail": "Exam mode not available."})
    if not EXAM_SECRET:
        return JSONResponse(status_code=503, content={"detail": "Exam mode not configured (EXAM_SECRET missing)."})
    try:
        payload = validate_token(body.token, EXAM_SECRET, LAB_ID)
    except InvalidTokenError as e:
        return JSONResponse(status_code=401, content={"detail": e.reason})
    session = get_or_create_session(body.token, payload)
    variant = session.dataset_variant
    active_data = _get_exam_data(variant)
    exercises = active_data.EXERCISE_DEFINITIONS if active_data else EXERCISE_DEFINITIONS
    return {
        "valid": True,
        "exam_id": payload.get("exam_id"),
        "student_id": payload.get("student_id"),
        "lab_id": LAB_ID,
        "dataset_variant": variant,
        "time_limit_seconds": payload.get("time_limit_seconds"),
        "elapsed_seconds": session.elapsed_seconds(),
        "remaining_seconds": session.remaining_seconds(),
        "exercises": [
            {
                **ex,
                "attempts_used": session.attempt_count(ex["exercise_id"]),
                "attempt_cap": session.attempt_caps.get(ex["exercise_id"]),
            }
            for ex in exercises
        ],
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
    session = _SESSIONS.get(body.exam_token)
    if not session:
        return JSONResponse(status_code=404, content={"detail": "Exam session not found. Call /api/exam/validate first."})
    if session.theory_submitted():
        return JSONResponse(status_code=409, content={"detail": "Theory already submitted."})

    try:
        from exam_questions import QUESTION_BANKS
        lab_questions = QUESTION_BANKS.get(LAB_ID, {})
    except ImportError:
        lab_questions = {}

    mcq_bank = {q["id"]: q for q in lab_questions.get("mcq", [])}
    scored_mcq: list[dict] = []
    for ans in body.mcq_answers:
        q = mcq_bank.get(ans.question_id)
        if not q:
            continue
        correct = ans.answer.upper() == q.get("answer", "").upper()
        scored_mcq.append({
            "question_id": ans.question_id,
            "student_answer": ans.answer,
            "correct": correct,
            "bloom_level": q.get("bloom_level", 4),
            "points_earned": q.get("points", 5) if correct else 0,
        })

    short_answers_payload = [
        {"question_id": sa.question_id, "response": sa.response, "word_count": len(sa.response.split())}
        for sa in body.short_answers
    ]
    session.record_theory(scored_mcq, short_answers_payload)
    return session.to_theory_receipt(scored_mcq)


@app.get("/api/exam/receipt")
async def exam_receipt(exam_token: str):
    if not EXAM_ENABLED or not EXAM_SECRET:
        return JSONResponse(status_code=503, content={"detail": "Exam mode not configured."})
    try:
        validate_token(exam_token, EXAM_SECRET, LAB_ID)
    except InvalidTokenError as e:
        return JSONResponse(status_code=401, content={"detail": e.reason})
    session = _SESSIONS.get(exam_token)
    if not session:
        return JSONResponse(status_code=404, content={"detail": "Exam session not found. Call /api/exam/validate first."})
    active_data = _get_exam_data(session.dataset_variant)
    exercises = active_data.EXERCISE_DEFINITIONS if active_data else EXERCISE_DEFINITIONS
    receipt_payload = {
        "receipt_version": "1",
        "lab_id": LAB_ID,
        "practical": session.to_practical_receipt(exercises),
        "theory": session.to_theory_receipt([]) if not session.theory_submitted() else None,
        "timing": {
            "total_elapsed_seconds": session.elapsed_seconds(),
            "time_limit_seconds": session.token_payload.get("time_limit_seconds"),
        },
        "exam_id": session.token_payload.get("exam_id"),
        "student_id": session.token_payload.get("student_id"),
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
    session = _SESSIONS.get(exam_token)
    if not session:
        return JSONResponse(status_code=404, content={"detail": "Exam session not found. Call /api/exam/validate first."})
    active_data = _get_exam_data(session.dataset_variant)
    exercises = active_data.EXERCISE_DEFINITIONS if active_data else EXERCISE_DEFINITIONS
    return {
        "exam_id": session.token_payload.get("exam_id"),
        "student_id": session.token_payload.get("student_id"),
        "elapsed_seconds": session.elapsed_seconds(),
        "remaining_seconds": session.remaining_seconds(),
        "is_expired": session.is_expired(),
        "is_paused": session.is_paused(),
        "theory_submitted": session.theory_submitted(),
        "exercises": [
            {
                **ex,
                "attempts_used": session.attempt_count(ex["exercise_id"]),
                "attempt_cap": session.attempt_caps.get(ex["exercise_id"]),
                "score": session._scores.get(ex["exercise_id"], 0),
            }
            for ex in exercises
        ],
    }


@app.get("/api/exam/questions")
async def exam_questions_route(exam_token: str):
    if not EXAM_ENABLED or not EXAM_SECRET:
        return JSONResponse(status_code=503, content={"detail": "Exam mode not configured."})
    try:
        validate_token(exam_token, EXAM_SECRET, LAB_ID)
    except InvalidTokenError as e:
        return JSONResponse(status_code=401, content={"detail": e.reason})
    try:
        from exam_questions import QUESTION_BANKS
        lab_qs = QUESTION_BANKS.get(LAB_ID, {})
    except ImportError:
        lab_qs = {}
    mcq_client = [
        {"id": q["id"], "bloom_level": q.get("bloom_level", 4),
         "scenario": q.get("scenario", ""), "stem": q["stem"],
         "options": q["options"], "points": q.get("points", 5)}
        for q in lab_qs.get("mcq", [])
    ]
    sa_client = [
        {"id": q["id"], "bloom_level": q.get("bloom_level", 5),
         "prompt": q["prompt"], "word_limit": q.get("word_limit", 200),
         "points": q.get("points", 20)}
        for q in lab_qs.get("short_answers", [])
    ]
    return {"lab_id": LAB_ID, "mcq": mcq_client, "short_answers": sa_client}


# ---------------------------------------------------------------------------
# Routes — admin
# ---------------------------------------------------------------------------

def _check_admin_auth(request: Request) -> None:
    if not EXAM_SECRET:
        raise HTTPException(503, "EXAM_SECRET not configured")
    if request.headers.get("X-Exam-Secret", "") != EXAM_SECRET:
        raise HTTPException(401, "Invalid or missing X-Exam-Secret header")


class AdminTokenBody(BaseModel):
    token: str


class RosterRow(BaseModel):
    student_id: str
    token: str = ""


class LoadRosterBody(BaseModel):
    rows: list[RosterRow]


class ExtendTimeBody(BaseModel):
    token: str
    additional_seconds: int


class ResetAttemptsBody(BaseModel):
    token: str
    exercise_id: str


@app.get("/api/admin/roster")
async def admin_roster(request: Request):
    _check_admin_auth(request)
    rows = []
    for student_id, tok in _ROSTER_MAP.items():
        session = _SESSIONS.get(tok) if tok else None
        active_data = _get_exam_data(session.dataset_variant) if session else None
        exercises = active_data.EXERCISE_DEFINITIONS if active_data else EXERCISE_DEFINITIONS
        rows.append({
            "student_id": student_id,
            "token_set": bool(tok),
            "session_active": session is not None,
            "elapsed_seconds": session.elapsed_seconds() if session else None,
            "remaining_seconds": session.remaining_seconds() if session else None,
            "is_expired": session.is_expired() if session else None,
            "is_paused": session.is_paused() if session else None,
            "scores": {ex["exercise_id"]: session._scores.get(ex["exercise_id"], 0) for ex in exercises} if session else {},
        })
    return {"roster": rows}


@app.post("/api/admin/load-roster")
async def admin_load_roster(request: Request, body: LoadRosterBody):
    global _ROSTER_MAP
    _check_admin_auth(request)
    _ROSTER_MAP = {row.student_id: row.token for row in body.rows if row.student_id}
    return {"loaded": len(_ROSTER_MAP)}


@app.post("/api/admin/extend-time")
async def admin_extend_time(request: Request, body: ExtendTimeBody):
    _check_admin_auth(request)
    if not EXAM_ENABLED:
        raise HTTPException(503, "Exam mode not available.")
    session = _SESSIONS.get(body.token)
    if not session:
        raise HTTPException(404, "Session not found")
    return session.extend_time(body.additional_seconds)


@app.post("/api/admin/reset-attempts")
async def admin_reset_attempts(request: Request, body: ResetAttemptsBody):
    _check_admin_auth(request)
    if not EXAM_ENABLED:
        raise HTTPException(503, "Exam mode not available.")
    session = _SESSIONS.get(body.token)
    if not session:
        raise HTTPException(404, "Session not found")
    count = session.reset_exercise(body.exercise_id, reason="Admin reset")
    return {"reset": True, "attempts_cleared": count}


@app.post("/api/admin/pause-exam")
async def admin_pause_exam(request: Request, body: AdminTokenBody):
    _check_admin_auth(request)
    if not EXAM_ENABLED:
        raise HTTPException(503, "Exam mode not available.")
    session = _SESSIONS.get(body.token)
    if not session:
        raise HTTPException(404, "Session not found")
    return session.pause()


@app.post("/api/admin/resume-exam")
async def admin_resume_exam(request: Request, body: AdminTokenBody):
    _check_admin_auth(request)
    if not EXAM_ENABLED:
        raise HTTPException(503, "Exam mode not available.")
    session = _SESSIONS.get(body.token)
    if not session:
        raise HTTPException(404, "Session not found")
    return session.resume()
