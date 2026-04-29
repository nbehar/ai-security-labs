#!/usr/bin/env python3
"""Phase 5 verification — 6 attacks x 6 defense conditions = 36 cells.

Replaces the design-intent defense matrix in `overview_spec.md` with measured
numbers from the deployed HF Space. Mirrors the Multimodal Lab Phase 5
methodology — measured > design-intent.

Defense conditions (6):
  1. `none`               — baseline (no defenses); should leak canary
  2. `provenance_check`   — universal first-line; expected 6/6 catches
  3. `adversarial_filter` — keyword pre-scan; expected 3/6 (RP.1, RP.2, RP.3)
  4. `retrieval_diversity` — single-source cluster block; expected 1/6 (RP.6)
  5. `output_grounding`   — fabricated-citation post-LLM check; expected 1/6 (RP.4)
  6. `all_four`           — full layered defense; expected 6/6 catches

Output:
  docs/phase5-raw.json   — 36 cells with full retrieval / response / defense_log
  docs/phase5-matrix.md  — writeup (authored separately after seeing results)

Usage: python3 scripts/run_phase5_matrix.py [--host HOST]

Wall time: 36 calls x 7s rate-limit sleep + ~2-3s avg per call ~= 5-7 min.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import urllib.request
import urllib.error


DEFAULT_HOST = "https://nikobehar-ai-sec-lab5-data-poisoning.hf.space"
ATTACK_IDS = ["RP.1", "RP.2", "RP.3", "RP.4", "RP.5", "RP.6"]
SCENARIOS = [
    ("none", []),
    ("provenance_check", ["provenance_check"]),
    ("adversarial_filter", ["adversarial_filter"]),
    ("retrieval_diversity", ["retrieval_diversity"]),
    ("output_grounding", ["output_grounding"]),
    ("all_four", ["provenance_check", "adversarial_filter", "retrieval_diversity", "output_grounding"]),
]
SLEEP_SECONDS = 7.0  # respect 10/min/IP rate limit


def hf_token() -> str:
    p = Path.home() / ".cache" / "huggingface" / "token"
    return p.read_text().strip() if p.exists() else ""


def post_multipart(url: str, fields: dict, headers: dict, timeout: int = 60):
    boundary = "----phase5" + str(int(time.time() * 1000))
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


def categorize(rec: dict) -> str:
    """leaked / blocked / failed (no leak, no block — model declined on its own)."""
    if rec.get("blocked_by"):
        return "blocked"
    if rec.get("succeeded"):
        return "leaked"
    return "failed"


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

    print(f"Phase 5 measured matrix vs {args.host}")
    print(f"  attacks   : {ATTACK_IDS}")
    print(f"  scenarios : {[s[0] for s in SCENARIOS]}")
    print(f"  total     : {len(ATTACK_IDS) * len(SCENARIOS)} cells")
    print(f"  est. time : ~{len(ATTACK_IDS) * len(SCENARIOS) * (SLEEP_SECONDS + 2):.0f}s\n")

    cells = []
    matrix = {a: {} for a in ATTACK_IDS}

    for attack_id in ATTACK_IDS:
        for scenario_name, defenses in SCENARIOS:
            fields = {
                "attack_id": attack_id,
                "doc_source": "canned",
                "participant_name": "Phase5",
            }
            if defenses:
                fields["defenses"] = json.dumps(defenses)
            print(f"  {attack_id:<5} x {scenario_name:<22} ...", end=" ", flush=True)
            status, body = post_multipart(
                f"{args.host}/api/attack",
                fields=fields,
                headers=headers,
                timeout=60,
            )
            if status != 200:
                print(f"FAIL {status}: {body}")
                cell = {
                    "attack_id": attack_id,
                    "scenario": scenario_name,
                    "defenses": defenses,
                    "status": status,
                    "error": body,
                }
            else:
                cat = categorize(body)
                cell = {
                    "attack_id": attack_id,
                    "scenario": scenario_name,
                    "defenses": defenses,
                    "status": 200,
                    "category": cat,
                    "succeeded": body.get("succeeded"),
                    "blocked_by": body.get("blocked_by"),
                    "elapsed_seconds": body.get("elapsed_seconds"),
                    "defenses_applied": body.get("defenses_applied", []),
                    "defense_log": body.get("defense_log", []),
                    "model_response_present": bool((body.get("model_response") or "").strip()),
                }
                summary = (
                    f"{cat:<7} blocked_by={cell['blocked_by']!s:<22} "
                    f"elapsed={cell['elapsed_seconds']}s"
                )
                print(summary)
            cells.append(cell)
            matrix[attack_id][scenario_name] = cell
            time.sleep(SLEEP_SECONDS)

    # Persist
    raw_path = out_dir / "phase5-raw.json"
    raw_path.write_text(json.dumps({"host": args.host, "cells": cells}, indent=2))

    # ==========================================================================
    # Summary tables
    # ==========================================================================

    # Per-defense catch rates: for each defense, count cells where it was the
    # ONLY defense active AND the cell ended in 'blocked'.
    print("\n" + "=" * 72)
    print("Per-defense catch rates (single-defense scenarios only):\n")
    header = f"  {'attack':<6} | " + " | ".join(f"{s[0]:<19}" for s in SCENARIOS)
    print(header)
    print("  " + "-" * (len(header) - 2))
    for attack_id in ATTACK_IDS:
        cells_str = []
        for scenario_name, _ in SCENARIOS:
            c = matrix[attack_id][scenario_name]
            if c.get("status") != 200:
                cells_str.append(f"{'HTTP ' + str(c.get('status')):<19}")
            elif c.get("category") == "blocked":
                blocked_by = c.get("blocked_by") or "?"
                cells_str.append(f"BLK {blocked_by[:15]:<15}")
            elif c.get("category") == "leaked":
                cells_str.append(f"{'leaked':<19}")
            elif c.get("category") == "failed":
                cells_str.append(f"{'no-leak (no block)':<19}")
            else:
                cells_str.append(f"{c.get('category','?'):<19}")
        print(f"  {attack_id:<6} | " + " | ".join(cells_str))

    # Per-defense aggregate: for each single-defense scenario, count blocked cells
    print("\nPer-defense aggregate (across 6 attacks):\n")
    print(f"  {'defense':<22} | catches | leaks | failed")
    print(f"  {'-'*22} | {'-'*7} | {'-'*5} | {'-'*6}")
    for scenario_name, _ in SCENARIOS:
        catches = sum(1 for a in ATTACK_IDS if matrix[a][scenario_name].get("category") == "blocked")
        leaks = sum(1 for a in ATTACK_IDS if matrix[a][scenario_name].get("category") == "leaked")
        failed = sum(1 for a in ATTACK_IDS if matrix[a][scenario_name].get("category") == "failed")
        print(f"  {scenario_name:<22} | {catches:>7}/6 | {leaks:>5}/6 | {failed:>5}/6")

    print(f"\nWrote {raw_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
