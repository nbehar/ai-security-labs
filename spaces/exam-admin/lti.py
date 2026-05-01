"""
LTI 1.3 helpers for exam-admin.

Provides:
  get_jwks() -> dict             JWKS public key set for Canvas tool registration
  post_grade_to_lti(...)         AGS grade passback via client_credentials JWT

Does not use pylti1p3 — implements the client_credentials OAuth flow directly
using cryptography + httpx. This keeps the dependency set minimal and avoids
the full OIDC launch flow (which we don't need for admin-side grade passback).
"""

import base64
import json
import os
import time
import uuid

import httpx


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _get_private_key():
    pem = os.environ.get("EXAM_LTI_PRIVATE_KEY_PEM", "")
    if not pem:
        return None
    try:
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        return load_pem_private_key(pem.encode(), password=None)
    except Exception:
        return None


def get_jwks() -> dict:
    private_key = _get_private_key()
    if private_key is None:
        return {"keys": []}
    public_key = private_key.public_key()
    pub_numbers = public_key.public_numbers()
    n_bytes = pub_numbers.n.to_bytes((pub_numbers.n.bit_length() + 7) // 8, "big")
    e_bytes = pub_numbers.e.to_bytes((pub_numbers.e.bit_length() + 7) // 8, "big")
    return {
        "keys": [{
            "kty": "RSA",
            "use": "sig",
            "alg": "RS256",
            "kid": "exam-admin-key-1",
            "n": _b64url(n_bytes),
            "e": _b64url(e_bytes),
        }]
    }


def _make_jwt(private_key, claims: dict) -> str:
    from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
    from cryptography.hazmat.primitives.hashes import SHA256
    header = {"alg": "RS256", "typ": "JWT", "kid": "exam-admin-key-1"}
    header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url(json.dumps(claims, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()
    sig = private_key.sign(signing_input, PKCS1v15(), SHA256())
    return f"{header_b64}.{payload_b64}.{_b64url(sig)}"


async def post_grade_to_lti(
    student_id: str,
    total_score: float,
    total_max: float,
    exam_id: str,
) -> dict:
    private_key = _get_private_key()
    if private_key is None:
        raise ValueError("EXAM_LTI_PRIVATE_KEY_PEM not set")

    client_id = os.environ.get("EXAM_LTI_CLIENT_ID", "")
    platform_url = os.environ.get("EXAM_LTI_PLATFORM_URL", "").rstrip("/")
    lineitem_url = os.environ.get("EXAM_LTI_LINEITEM_URL", "")

    if not all([client_id, platform_url, lineitem_url]):
        raise ValueError("Missing one or more EXAM_LTI_* env vars")

    now = int(time.time())
    jwt_claims = {
        "iss": client_id,
        "sub": client_id,
        "aud": f"{platform_url}/login/oauth2/token",
        "iat": now,
        "exp": now + 300,
        "jti": str(uuid.uuid4()),
    }
    client_assertion = _make_jwt(private_key, jwt_claims)

    async with httpx.AsyncClient(timeout=20.0) as client:
        token_resp = await client.post(
            f"{platform_url}/login/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": client_assertion,
                "scope": "https://purl.imsglobal.org/spec/lti-ags/scope/score",
            },
        )
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]

        score_payload = {
            "userId": student_id,
            "scoreGiven": total_score,
            "scoreMaximum": total_max,
            "activityProgress": "Completed",
            "gradingProgress": "FullyGraded",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "comment": f"exam_id={exam_id}",
        }
        grade_resp = await client.post(
            f"{lineitem_url}/scores",
            json=score_payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/vnd.ims.lis.v1.score+json",
            },
        )
        grade_resp.raise_for_status()
        return {"canvas_response_status": grade_resp.status_code}
