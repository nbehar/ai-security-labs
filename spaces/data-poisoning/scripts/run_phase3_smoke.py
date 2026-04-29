#!/usr/bin/env python3
"""Phase 3 smoke verification — 3 attacks x 3 defense scenarios = 9 calls.

Picks RP.1 (Direct Injection — adversarial_filter target), RP.4 (Citation Spoof —
output_grounding target), RP.6 (Multi-Doc Consensus — retrieval_diversity
target). Runs each under three defense conditions:

  1. none                 — baseline; should leak canary (sanity check)
  2. provenance_check     — universal first-line; should block all 3
  3. all_four             — full layered defense; should block all 3

Verifies `blocked_by` is populated correctly and that the appropriate defense
fires first. Prints a 3x3 matrix to stdout and writes raw cells to
`docs/phase3-smoke-raw.json`.

Usage: python3 scripts/run_phase3_smoke.py [--host HOST]
"""

import argparse
import json
import sys
import time
from pathlib import Path

import urllib.request
import urllib.error


DEFAULT_HOST = "https://nikobehar-ai-sec-lab5-data-poisoning.hf.space"
ATTACK_IDS = ["RP.1", "RP.4", "RP.6"]
SCENARIOS = [
    ("none", []),
    ("provenance_check", ["provenance_check"]),
    ("all_four", ["provenance_check", "adversarial_filter", "retrieval_diversity", "output_grounding"]),
]
SLEEP_SECONDS = 7.0  # respect 10/min/IP rate limit


def hf_token() -> str:
    p = Path.home() / ".cache" / "huggingface" / "token"
    return p.read_text().strip() if p.exists() else ""


def post_multipart(url: str, fields: dict, headers: dict, timeout: int = 60):
    boundary = "----smoke" + str(int(time.time() * 1000))
    parts = []
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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default=DEFAULT_HOST)
    p.add_argument("--out-dir", default="docs")
    args = p.parse_args()

    token = hf_token()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print(f"Phase 3 smoke matrix vs {args.host}\n")
    print(f"  attacks   : {ATTACK_IDS}")
    print(f"  scenarios : {[s[0] for s in SCENARIOS]}\n")

    cells = []
    matrix = {a: {} for a in ATTACK_IDS}
    for attack_id in ATTACK_IDS:
        for scenario_name, defenses in SCENARIOS:
            fields = {
                "attack_id": attack_id,
                "doc_source": "canned",
                "participant_name": "PhaseSmoke",
            }
            if defenses:
                fields["defenses"] = json.dumps(defenses)
            print(f"  {attack_id:<5} x {scenario_name:<18} ...", end=" ", flush=True)
            status, body = post_multipart(
                f"{args.host}/api/attack",
                fields=fields,
                headers=headers,
                timeout=60,
            )
            if status != 200:
                print(f"FAIL {status}: {body}")
                cell = {"attack_id": attack_id, "scenario": scenario_name, "status": status, "error": body}
            else:
                cell = {
                    "attack_id": attack_id,
                    "scenario": scenario_name,
                    "status": 200,
                    "succeeded": body.get("succeeded"),
                    "blocked_by": body.get("blocked_by"),
                    "elapsed_seconds": body.get("elapsed_seconds"),
                    "defenses_applied": body.get("defenses_applied", []),
                    "defense_log": body.get("defense_log", []),
                    "model_response_present": bool(body.get("model_response", "").strip()),
                }
                summary = (
                    f"succeeded={cell['succeeded']!s:<5} blocked_by={cell['blocked_by']!s:<22} "
                    f"elapsed={cell['elapsed_seconds']}s"
                )
                print(summary)
            cells.append(cell)
            matrix[attack_id][scenario_name] = cell
            time.sleep(SLEEP_SECONDS)

    (out_dir / "phase3-smoke-raw.json").write_text(json.dumps({
        "host": args.host,
        "cells": cells,
    }, indent=2))

    # Print 3x3 summary table
    print("\nResult matrix:\n")
    header = f"  {'attack':<6} | " + " | ".join(f"{s[0]:<22}" for s in SCENARIOS)
    print(header)
    print("  " + "-" * (len(header) - 2))
    for attack_id in ATTACK_IDS:
        cells_str = []
        for scenario_name, _ in SCENARIOS:
            c = matrix[attack_id][scenario_name]
            if c.get("status") != 200:
                cells_str.append(f"{'HTTP ' + str(c.get('status')):<22}")
            elif c.get("blocked_by"):
                cells_str.append(f"BLK by {c['blocked_by']:<15}")
            elif c.get("succeeded"):
                cells_str.append(f"{'leaked':<22}")
            else:
                cells_str.append(f"{'no-leak (no block)':<22}")
        print(f"  {attack_id:<6} | " + " | ".join(cells_str))

    print(f"\nWrote {out_dir / 'phase3-smoke-raw.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
