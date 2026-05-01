"""
app_auth.py — Firebase token-verification middleware for AI Security Labs.

Attach to each space's FastAPI app:
    from app_auth import add_auth_middleware
    add_auth_middleware(app)

Also add a /api/firebase-config route to serve the public Firebase config:
    from app_auth import firebase_config_route
    app.add_api_route("/api/firebase-config", firebase_config_route)

Environment variables:
    FIREBASE_CREDENTIALS  — base64-encoded service-account JSON (secret)
    FIREBASE_API_KEY      — public web API key (safe to expose)
    FIREBASE_AUTH_DOMAIN  — e.g. your-project.firebaseapp.com
    FIREBASE_PROJECT_ID   — e.g. your-project

Auth is automatically disabled (all requests pass through) when
FIREBASE_CREDENTIALS is not set — safe for local development.
"""

import os
import json
import base64
import logging
from functools import lru_cache

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

FIREBASE_AUTH_ENABLED = bool(os.environ.get("FIREBASE_CREDENTIALS", "").strip())

try:
    import firebase_admin
    from firebase_admin import credentials as fb_creds, auth as fb_auth
    _SDK_OK = True
except ImportError:
    _SDK_OK = False
    if FIREBASE_AUTH_ENABLED:
        raise RuntimeError(
            "FIREBASE_CREDENTIALS is set but firebase-admin is not installed. "
            "Auth cannot be enforced. Add firebase-admin to requirements.txt."
        )


@lru_cache(maxsize=1)
def _firebase_app():
    raw = os.environ.get("FIREBASE_CREDENTIALS", "").strip()
    if not raw:
        return None
    try:
        creds_json = json.loads(base64.b64decode(raw).decode())
    except Exception:
        try:
            creds_json = json.loads(raw)
        except Exception:
            logger.error("FIREBASE_CREDENTIALS: could not parse (expected base64 JSON or raw JSON)")
            return None
    cred = fb_creds.Certificate(creds_json)
    if firebase_admin._apps:
        return firebase_admin.get_app()
    return firebase_admin.initialize_app(cred)


def add_auth_middleware(app) -> None:
    """Attach Firebase token-verification middleware to a FastAPI app."""

    @app.middleware("http")
    async def _firebase_auth(request: Request, call_next):
        if not FIREBASE_AUTH_ENABLED or not _SDK_OK:
            return await call_next(request)

        path = request.url.path

        # Pass through: root, health, static files, and the config endpoint
        if (path in ("/", "/health", "/api/firebase-config")
                or path.startswith("/static/")):
            return await call_next(request)

        # EventSource (SSE) cannot set headers — accept token as query param fallback
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ")
        else:
            token = request.query_params.get("firebase_token", "")

        if not token:
            return JSONResponse(
                {"error": "Unauthorized", "detail": "Missing Bearer token"},
                status_code=401,
            )
        try:
            _firebase_app()  # ensure initialized
            decoded = fb_auth.verify_id_token(token)
            request.state.firebase_user = decoded
        except Exception as exc:
            logger.debug("Token verification failed: %s", exc)
            return JSONResponse(
                {"error": "Unauthorized", "detail": "Invalid or expired token"},
                status_code=401,
            )

        return await call_next(request)


async def firebase_config_route():
    """GET /api/firebase-config — returns public Firebase config for the client SDK."""
    api_key = os.environ.get("FIREBASE_API_KEY", "").strip()
    if not api_key:
        return {"enabled": False}
    return {
        "enabled": True,
        "apiKey": api_key,
        "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN", ""),
        "projectId": os.environ.get("FIREBASE_PROJECT_ID", ""),
    }
