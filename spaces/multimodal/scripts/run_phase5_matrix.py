#!/usr/bin/env python3
"""Phase 5 — measured defense matrix vs the deployed Multimodal Space.

For each (attack_id × defense_combination), POST /api/attack and record:
  - succeeded (canary leaked end-to-end)
  - blocked_by (which defense fired, if any)
  - defense_log entries (verdicts: PASSED / BLOCKED / SKIPPED)
  - elapsed time

Defense combinations measured:
  none, ocr_prescan, output_redaction, boundary_hardening, confidence_threshold, all_four

Rate-limit-aware: /api/attack is rate-limited at 10/min/IP. Sleep enough between
calls to stay under that budget (sleep cycles roughly 7s minimum; inference time
typically absorbs more).

Output:
  - docs/phase5-matrix-raw.json — full per-cell record (used by the UI)
  - docs/phase5-matrix-summary.md — markdown table appended to phase3-calibration.md by hand

Usage:
  python3 scripts/run_phase5_matrix.py [--host HOST] [--out-dir DIR]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

import urllib.request
import urllib.parse
import urllib.error

DEFAULT_HOST = "https://nikobehar-ai-sec-lab4-multimodal.hf.space"
ALL_DEFENSES = [
    "ocr_prescan",
    "output_redaction",
    "boundary_hardening",
    "confidence_threshold",
]
CONDITIONS = [
    ("none", []),
    ("ocr_prescan", ["ocr_prescan"]),
    ("output_redaction", ["output_redaction"]),
    ("boundary_hardening", ["boundary_hardening"]),
    ("confidence_threshold", ["confidence_threshold"]),
    ("all_four", list(ALL_DEFENSES)),
]
MIN_SLEEP_SECONDS = 7.0  # 60s / 10 = 6s + safety margin


def hf_token() -> str:
    p = Path.home() / ".cache" / "huggingface" / "token"
    if not p.exists():
        sys.exit(f"HF token not found at {p}. Run `hf auth login` first.")
    return p.read_text().strip()


def get_attacks(host: str, token: str) -> list[dict]:
    req = urllib.request.Request(
        f"{host}/api/attacks",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.loads(r.read())
    return body["attacks"]


def post_multipart(url: str, fields: dict, headers: dict, timeout: int = 90) -> tuple[int, dict]:
    """Encode fields as multipart/form-data and POST. Returns (status, json_body)."""
    boundary = "----phase5matrix" + str(int(time.time() * 1000))
    parts: list[bytes] = []
    for name, value in fields.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        parts.append(str(value).encode())
        parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    headers = {**headers, "Content-Type": f"multipart/form-data; boundary={boundary}"}
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def run_cell(host: str, token: str, attack_id: str, defenses: list[str]) -> dict:
    started = time.monotonic()
    status, body = post_multipart(
        f"{host}/api/attack",
        fields={
            "attack_id": attack_id,
            "image_source": "canned",
            "defenses": json.dumps(defenses),
            "participant_name": "Phase5Matrix",
        },
        headers={"Authorization": f"Bearer {token}"},
        timeout=90,
    )
    elapsed = time.monotonic() - started
    return {
        "attack_id": attack_id,
        "defenses": defenses,
        "status": status,
        "succeeded": body.get("succeeded"),
        "blocked_by": body.get("blocked_by"),
        "defense_log": body.get("defense_log", []),
        "canary": body.get("canary"),
        "elapsed_seconds": round(elapsed, 1),
        "model_response": (body.get("model_response") or "")[:200],
        "error_detail": body.get("detail") if status != 200 else None,
    }


def cell_label(record: dict) -> str:
    """Compact symbol for the matrix: ✓ catches, ✗ misses, ~ partial."""
    if record["status"] != 200:
        return f"err{record['status']}"
    if record["blocked_by"]:
        return "BLK"  # defense blocked
    if record["succeeded"]:
        return "SUC"  # attack succeeded
    return "RFS"  # neither — model refused / didn't comply


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default=DEFAULT_HOST)
    p.add_argument("--out-dir", default="docs")
    p.add_argument("--sleep", type=float, default=MIN_SLEEP_SECONDS)
    args = p.parse_args()

    token = hf_token()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Phase 5 matrix run against {args.host}")
    attacks = get_attacks(args.host, token)
    print(f"Loaded {len(attacks)} attacks")

    results: list[dict] = []
    total = len(attacks) * len(CONDITIONS)
    i = 0
    for attack in attacks:
        attack_id = attack["id"]
        for condition_name, defenses in CONDITIONS:
            i += 1
            print(f"[{i:>3}/{total}] {attack_id} × {condition_name:22} ", end="", flush=True)
            try:
                rec = run_cell(args.host, token, attack_id, defenses)
                rec["condition"] = condition_name
                rec["attack_lab"] = attack["lab"]
                rec["attack_name"] = attack["name"]
                results.append(rec)
                print(f"{cell_label(rec):>5}  {rec['elapsed_seconds']:>5.1f}s  blocked_by={rec['blocked_by']}")
            except Exception as e:
                print(f"FAIL  {type(e).__name__}: {e}")
                results.append({
                    "attack_id": attack_id,
                    "condition": condition_name,
                    "defenses": defenses,
                    "error": f"{type(e).__name__}: {e}",
                })

            # Persist incrementally so a Ctrl-C mid-run still leaves progress
            (out_dir / "phase5-matrix-raw.json").write_text(
                json.dumps({"host": args.host, "results": results}, indent=2)
            )
            time.sleep(args.sleep)

    print(f"\nDone — wrote {out_dir / 'phase5-matrix-raw.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
