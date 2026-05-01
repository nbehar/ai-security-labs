"""
exam-admin — AI Security Labs instructor receipt verification and grading tool.

Routes:
  GET  /
  GET  /health
  POST /api/verify
  POST /api/batch-verify
  GET  /api/rubric/{lab_id}
  GET  /api/lti/jwks
  POST /api/lti/grade
  POST /api/lti/batch-grade
  POST /api/admin/proxy            forward admin commands to lab spaces
  POST /api/admin/generate-tokens  generate exam tokens for a student roster
"""

import copy
import logging
import os
import time as _time

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from lti import get_jwks, post_grade_to_lti

# Framework modules copied from framework/ at deploy time
EXAM_TOKEN_AVAILABLE = False
try:
    from exam_token import generate_token, verify_receipt
    EXAM_TOKEN_AVAILABLE = True
except ImportError:
    pass

QUESTIONS_AVAILABLE = False
QUESTION_BANKS: dict = {}
try:
    from exam_questions import QUESTION_BANKS
    QUESTIONS_AVAILABLE = True
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EXAM_SECRET = os.environ.get("EXAM_SECRET", "")
LTI_VARS = ["EXAM_LTI_CLIENT_ID", "EXAM_LTI_PLATFORM_URL",
            "EXAM_LTI_LINEITEM_URL", "EXAM_LTI_PRIVATE_KEY_PEM"]

# Known lab space base URLs for token generation and proxy routing
LAB_URLS: dict[str, str] = {
    "red-team": "https://nikobehar-red-team-workshop.hf.space",
    "detection-monitoring": "https://nikobehar-ai-sec-lab6-detection.hf.space",
    "blue-team": "https://nikobehar-blue-team-workshop.hf.space",
    "owasp-top-10": "https://nikobehar-llm-top-10.hf.space",
}

# Default attempt caps per lab used by token generator
DEFAULT_CAPS: dict[str, dict] = {
    "red-team": {f"level_{i}": 3 for i in range(1, 6)},
    "detection-monitoring": {"D1": 1, "D2": 3, "D3": 3},
    "blue-team": {"challenge_1": 3, "challenge_2": 3, "challenge_3": 3, "challenge_4": 3},
    "owasp-top-10": {},
}

SECTION_TO_VARIANT: dict[str, str] = {"A": "exam_v1", "B": "exam_v2", "C": "exam_v3"}

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="exam-admin")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# =============================================================================
# Pydantic schemas
# =============================================================================

class VerifyRequest(BaseModel):
    receipt: dict


class BatchVerifyRequest(BaseModel):
    receipts: list[dict]


class GradeRequest(BaseModel):
    student_id: str
    lab_id: str
    practical_score: int
    max_practical_score: int
    mcq_score: int
    mcq_max: int
    sa_score: int
    sa_max: int
    total_score: int
    total_max: int
    exam_id: str


class BatchGradeRequest(BaseModel):
    grades: list[GradeRequest]


class AdminProxyRequest(BaseModel):
    lab_url: str           # base URL of the target lab space
    endpoint: str          # e.g. "/api/admin/extend-time"
    method: str = "POST"   # POST or GET
    payload: dict = {}


class GenerateTokensRequest(BaseModel):
    exam_id: str
    student_ids: list[str]
    lab_ids: list[str]
    section: str = "A"
    duration_hours: int = 3
    opens_at: int           # Unix timestamp
    expires_at: int         # Unix timestamp


# =============================================================================
# Helpers
# =============================================================================

def _verify_one(receipt: dict) -> dict:
    student_id = receipt.get("student_id", "")
    exam_id = receipt.get("exam_id", "")
    lab_id = receipt.get("lab_id", "")

    if not EXAM_TOKEN_AVAILABLE or not EXAM_SECRET:
        return {
            "hmac_valid": False,
            "error": "EXAM_SECRET not configured — cannot verify.",
            "student_id": student_id,
            "exam_id": exam_id,
        }

    # verify_receipt pops/restores hmac_sha256 in place — work on a copy
    receipt_copy = copy.deepcopy(receipt)
    is_valid = verify_receipt(receipt_copy, EXAM_SECRET)

    if not is_valid:
        return {
            "hmac_valid": False,
            "error": "HMAC signature mismatch — receipt may have been tampered.",
            "student_id": student_id,
            "exam_id": exam_id,
        }

    return {
        "hmac_valid": True,
        "receipt_version": receipt.get("receipt_version", "1"),
        "exam_id": exam_id,
        "student_id": student_id,
        "lab_id": lab_id,
        "practical": receipt.get("practical", {}),
        "theory": receipt.get("theory", {}),
        "timing": receipt.get("timing", {}),
    }


def _check_admin_auth(request: Request) -> None:
    """Raise 401 if the X-Exam-Secret header doesn\'t match EXAM_SECRET."""
    if not EXAM_SECRET:
        raise HTTPException(503, "EXAM_SECRET not configured")
    if request.headers.get("X-Exam-Secret", "") != EXAM_SECRET:
        raise HTTPException(401, "Invalid or missing X-Exam-Secret header")


# =============================================================================
# Routes
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "exam_secret_configured": bool(EXAM_SECRET),
        "lti_configured": all(os.environ.get(v) for v in LTI_VARS),
    }


@app.post("/api/verify")
@limiter.limit("10/minute")
async def verify(request: Request, req: VerifyRequest):
    if not isinstance(req.receipt, dict):
        raise HTTPException(400, "receipt must be a JSON object")
    if "receipt_version" not in req.receipt and "student_id" not in req.receipt:
        raise HTTPException(400, "File does not look like an AI Security Labs receipt")
    return _verify_one(req.receipt)


@app.post("/api/batch-verify")
@limiter.limit("10/minute")
async def batch_verify(request: Request, req: BatchVerifyRequest):
    if len(req.receipts) > 100:
        raise HTTPException(400, "Maximum 100 receipts per request")
    results = []
    valid_count = 0
    for i, receipt in enumerate(req.receipts):
        result = _verify_one(receipt)
        result["index"] = i
        if result["hmac_valid"]:
            valid_count += 1
            practical = receipt.get("practical", {})
            theory = receipt.get("theory", {})
            timing = receipt.get("timing", {})
            result["practical_score"] = practical.get("total_practical_score", 0)
            result["max_practical_score"] = practical.get("max_practical_score", 0)
            result["mcq_score"] = theory.get("mcq_score", 0) if isinstance(theory, dict) else 0
            result["mcq_max"] = theory.get("mcq_max", 0) if isinstance(theory, dict) else 0
            result["theory_submitted"] = theory.get("submitted", False) if isinstance(theory, dict) else False
            result["elapsed_seconds"] = timing.get("total_elapsed_seconds", 0)
            result["time_limit_seconds"] = timing.get("time_limit_seconds", 0)
        results.append(result)
    return {
        "results": results,
        "total": len(req.receipts),
        "valid_count": valid_count,
        "invalid_count": len(req.receipts) - valid_count,
    }


@app.get("/api/rubric/{lab_id}")
async def rubric(lab_id: str):
    if not QUESTIONS_AVAILABLE:
        raise HTTPException(503, "Exam questions module not installed")
    if lab_id not in QUESTION_BANKS:
        raise HTTPException(404, f"No rubric found for lab '{lab_id}'")
    short_answers = [
        {
            "question_id": sa["id"],
            "bloom_level": sa.get("bloom_level"),
            "points": sa.get("points", 20),
            "word_limit": sa.get("word_limit", 200),
            "question": sa.get("question", ""),
            "rubric": sa.get("rubric", {}),
        }
        for sa in QUESTION_BANKS[lab_id].get("short_answers", [])
    ]
    return {"lab_id": lab_id, "short_answers": short_answers}


@app.get("/api/lti/jwks")
async def lti_jwks():
    return get_jwks()


@app.post("/api/lti/grade")
@limiter.limit("10/minute")
async def lti_grade(request: Request, req: GradeRequest):
    if not all(os.environ.get(v) for v in LTI_VARS):
        raise HTTPException(503, "LTI not configured")
    try:
        result = await post_grade_to_lti(
            student_id=req.student_id,
            total_score=req.total_score,
            total_max=req.total_max,
            exam_id=req.exam_id,
        )
        return {"status": "posted", "student_id": req.student_id, **result}
    except Exception as e:
        logger.error("LTI grade passback failed: %s", e)
        raise HTTPException(502, f"Canvas returned an error: {e}")


@app.post("/api/lti/batch-grade")
@limiter.limit("10/minute")
async def lti_batch_grade(request: Request, req: BatchGradeRequest):
    if len(req.grades) > 100:
        raise HTTPException(400, "Maximum 100 grades per request")
    if not all(os.environ.get(v) for v in LTI_VARS):
        raise HTTPException(503, "LTI not configured")
    results = []
    for grade in req.grades:
        try:
            result = await post_grade_to_lti(
                student_id=grade.student_id,
                total_score=grade.total_score,
                total_max=grade.total_max,
                exam_id=grade.exam_id,
            )
            results.append({"student_id": grade.student_id, "status": "posted", **result})
        except Exception as e:
            results.append({"student_id": grade.student_id, "status": "error", "detail": str(e)})
    return {"results": results}


# =============================================================================
# Admin proxy — forwards commands to lab spaces using server-side EXAM_SECRET
# =============================================================================

@app.post("/api/admin/proxy")
@limiter.limit("30/minute")
async def admin_proxy(request: Request, req: AdminProxyRequest):
    """
    Forward an admin command to a lab space.
    exam-admin adds X-Exam-Secret from its own env — the browser never sees the secret.
    """
    _check_admin_auth(request)
    if not req.lab_url.startswith("https://"):
        raise HTTPException(400, "lab_url must start with https://")
    url = req.lab_url.rstrip("/") + req.endpoint
    headers = {"X-Exam-Secret": EXAM_SECRET, "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            if req.method.upper() == "GET":
                resp = await client.get(url, headers=headers)
            else:
                resp = await client.post(url, json=req.payload, headers=headers)
        return resp.json()
    except httpx.TimeoutException:
        raise HTTPException(504, "Lab space did not respond in time")
    except Exception as e:
        raise HTTPException(502, f"Lab space unreachable: {e}")


# =============================================================================
# Token generator — batch-generate exam tokens for a student roster
# =============================================================================

@app.post("/api/admin/generate-tokens")
@limiter.limit("5/minute")
async def generate_tokens(request: Request, req: GenerateTokensRequest):
    """Generate one signed exam token per student_id. EXAM_SECRET never leaves the server."""
    _check_admin_auth(request)
    if not EXAM_TOKEN_AVAILABLE or not EXAM_SECRET:
        raise HTTPException(503, "EXAM_SECRET not configured — cannot generate tokens")
    if len(req.student_ids) > 200:
        raise HTTPException(400, "Maximum 200 students per request")

    now = int(_time.time())
    variant = SECTION_TO_VARIANT.get(req.section.upper(), "exam_v1")
    caps: dict = {}
    for lab_id in req.lab_ids:
        caps.update(DEFAULT_CAPS.get(lab_id, {}))

    tokens = []
    for student_id in req.student_ids:
        payload = {
            "version": "1",
            "exam_id": req.exam_id,
            "student_id": student_id,
            "lab_ids": req.lab_ids,
            "issued_at": now,
            "expires_at": req.expires_at,
            "time_limit_seconds": req.duration_hours * 3600,
            "attempt_caps": caps,
            "dataset_variant": variant,
        }
        token = generate_token(payload, EXAM_SECRET)
        exam_urls = {
            lab: f"{LAB_URLS[lab]}?exam_token={token}"
            for lab in req.lab_ids
            if lab in LAB_URLS
        }
        tokens.append({
            "student_id": student_id,
            "token": token,
            "exam_urls": exam_urls,
            "primary_exam_url": next(iter(exam_urls.values()), ""),
        })

    return {"tokens": tokens, "count": len(tokens), "exam_id": req.exam_id}
