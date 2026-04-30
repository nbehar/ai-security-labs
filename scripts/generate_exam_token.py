#!/usr/bin/env python3
"""
Generate a signed exam token for an AI Security Labs exam session.

Usage (run under op run to inject EXAM_SECRET):

  op run --env-file=.env.op -- python3 scripts/generate_exam_token.py \\
    --exam-id spring2026-final \\
    --student-id jsmith@univ.edu \\
    --lab-ids red-team detection-monitoring \\
    --duration-hours 3 \\
    --section A

Required env var: EXAM_SECRET
"""

import argparse
import json
import os
import sys
import time

# Add framework dir to path when running from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'framework'))

try:
    from exam_token import generate_token
except ImportError:
    print("ERROR: framework/exam_token.py not found. Run from repo root.", file=sys.stderr)
    sys.exit(1)

# Default attempt caps per lab type
DEFAULT_CAPS = {
    "red-team":            {"level_1": 3, "level_2": 3, "level_3": 3, "level_4": 3, "level_5": 3},
    "detection-monitoring": {"D1": 1, "D2": 3, "D3": 3},
    "blue-team":           {"C1": 3, "C2": 3, "C3": 3, "C4": 3},
    "data-poisoning":      {"E1": 3, "E2": 3, "E3": 3},
    "multimodal":          {"EP1": 3, "EP2": 3, "EP3": 3, "EP4": 3, "EP5": 3},
}

SECTION_TO_VARIANT = {"A": "exam_v1", "B": "exam_v2"}


def main():
    parser = argparse.ArgumentParser(description="Generate a signed exam token")
    parser.add_argument("--exam-id",      required=True,  help="e.g. spring2026-final")
    parser.add_argument("--student-id",   required=True,  help="LMS username / email")
    parser.add_argument("--lab-ids",      required=True,  nargs="+", help="One or more lab IDs")
    parser.add_argument("--duration-hours", type=float, default=3.0, help="Exam duration in hours")
    parser.add_argument("--section",      choices=["A", "B"], default="A",
                        help="Course section (A=exam_v1, B=exam_v2)")
    parser.add_argument("--attempt-caps", default=None,
                        help="JSON string override, e.g. '{\"level_1\":2}'")
    args = parser.parse_args()

    secret = os.environ.get("EXAM_SECRET", "")
    if not secret:
        print("ERROR: EXAM_SECRET env var not set. Run under: op run --env-file=.env.op", file=sys.stderr)
        sys.exit(1)

    # Build attempt caps from defaults for each lab
    caps: dict = {}
    for lab in args.lab_ids:
        caps.update(DEFAULT_CAPS.get(lab, {}))
    if args.attempt_caps:
        try:
            caps.update(json.loads(args.attempt_caps))
        except json.JSONDecodeError as e:
            print(f"ERROR: --attempt-caps is not valid JSON: {e}", file=sys.stderr)
            sys.exit(1)

    now = int(time.time())
    payload = {
        "version":            "1",
        "exam_id":            args.exam_id,
        "student_id":         args.student_id,
        "lab_ids":            args.lab_ids,
        "issued_at":          now,
        "expires_at":         now + int(args.duration_hours * 3600),
        "time_limit_seconds": int(args.duration_hours * 3600),
        "attempt_caps":       caps,
        "dataset_variant":    SECTION_TO_VARIANT[args.section],
    }

    token = generate_token(payload, secret)
    print(token)

    # Print summary to stderr so it doesn't mix with the token on stdout
    print("", file=sys.stderr)
    print("Token generated:", file=sys.stderr)
    print(f"  student_id:       {args.student_id}", file=sys.stderr)
    print(f"  exam_id:          {args.exam_id}", file=sys.stderr)
    print(f"  lab_ids:          {', '.join(args.lab_ids)}", file=sys.stderr)
    print(f"  dataset_variant:  {SECTION_TO_VARIANT[args.section]}", file=sys.stderr)
    print(f"  duration:         {args.duration_hours}h", file=sys.stderr)
    print(f"  expires_at:       {payload['expires_at']} (unix)", file=sys.stderr)
    print(f"  attempt_caps:     {caps}", file=sys.stderr)


if __name__ == "__main__":
    main()
