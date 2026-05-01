"""
HMAC-based exam token generation and validation for AI Security Labs.

Token format: base64url(payload_json).base64url(HMAC-SHA256(secret, payload_json))

The token encodes exam configuration (time limit, attempt caps, dataset variant)
and is validated by each lab space using a shared EXAM_SECRET environment variable.
"""

import base64
import hashlib
import hmac
import json
import time


class InvalidTokenError(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _sign(secret: str, payload_json: str) -> bytes:
    return hmac.new(
        secret.encode(),
        payload_json.encode(),
        hashlib.sha256,
    ).digest()


def generate_token(payload: dict, secret: str) -> str:
    """Generate a signed exam token from a payload dict and a shared secret."""
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    sig = _sign(secret, payload_json)
    return _b64url_encode(payload_json.encode()) + "." + _b64url_encode(sig)


def validate_token(token_str: str, secret: str, lab_id: str) -> dict:
    """
    Validate a token string. Returns the payload dict if valid.

    Raises InvalidTokenError with a human-readable .reason if:
      - token is malformed
      - HMAC signature is invalid
      - token is expired
      - lab_id is not in token's lab_ids list
    """
    parts = token_str.split(".")
    if len(parts) != 2:
        raise InvalidTokenError("Token is malformed — expected two dot-separated parts.")

    try:
        payload_json = _b64url_decode(parts[0]).decode()
        received_sig = _b64url_decode(parts[1])
    except Exception:
        raise InvalidTokenError("Token is malformed — base64url decoding failed.")

    expected_sig = _sign(secret, payload_json)
    if not hmac.compare_digest(expected_sig, received_sig):
        raise InvalidTokenError("Token signature is invalid — this token was not issued by this system.")

    try:
        payload = json.loads(payload_json)
    except json.JSONDecodeError:
        raise InvalidTokenError("Token payload is not valid JSON.")

    now = int(time.time())
    if payload.get("expires_at", 0) < now:
        raise InvalidTokenError("Token has expired — contact your instructor for a new token.")

    if payload.get("issued_at", now + 1) > now:
        raise InvalidTokenError("Token is not yet valid — check your system clock.")

    lab_ids = payload.get("lab_ids", [])
    if lab_id not in lab_ids:
        raise InvalidTokenError(
            f"This token is not valid for lab '{lab_id}'. "
            f"Valid labs for this token: {', '.join(lab_ids)}."
        )

    return payload


def derive_receipt_signing_key(secret: str, student_id: str, exam_id: str) -> bytes:
    """
    Derive a per-exam HMAC key for signing score receipts.
    Used by the exam-admin space to verify receipt authenticity.
    The student never has access to EXAM_SECRET, so only the server can derive this key.
    """
    msg = f"{student_id}:{exam_id}".encode()
    return hmac.new(secret.encode(), msg, hashlib.sha256).digest()


def sign_receipt(receipt_payload: dict, secret: str) -> str:
    """
    Generate an HMAC-SHA256 signature over the canonical JSON of a receipt payload.
    The returned hex string is stored in receipt['hmac_sha256'].
    """
    canonical = json.dumps(receipt_payload, separators=(",", ":"), sort_keys=True)
    student_id = receipt_payload.get("student_id", "")
    exam_id = receipt_payload.get("exam_id", "")
    key = derive_receipt_signing_key(secret, student_id, exam_id)
    return hmac.new(key, canonical.encode(), hashlib.sha256).hexdigest()


def verify_receipt(receipt_with_sig: dict, secret: str) -> bool:
    """
    Verify a signed receipt. Extracts and strips hmac_sha256, recomputes, compares.
    Returns True if valid, False otherwise. Does not raise.
    """
    provided_sig = receipt_with_sig.pop("hmac_sha256", None)
    if not provided_sig:
        return False
    try:
        expected_sig = sign_receipt(receipt_with_sig, secret)
        return hmac.compare_digest(expected_sig, provided_sig)
    except Exception:
        return False
    finally:
        receipt_with_sig["hmac_sha256"] = provided_sig
