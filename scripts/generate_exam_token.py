#!/usr/bin/env python3
"""
Generate exam tokens for AI Security Labs.

Run under 1Password op run to inject EXAM_SECRET:

  op run --env-file=.env.op -- python scripts/generate_exam_token.py \\
    --exam-id spring2026-final \\
    --student-id jsmith@univ.edu \\
    --lab-ids red-team detection-monitoring \\
    --section A \\
    --duration-hours 3 \\
    --attempt-caps '{"level_1":3,"level_2":3,"level_3":3,"level_4":3,"level_5":3,"D1":1,"D2":3,"D3":2}'

Or generate tokens for all students from a CSV file:

  op run --env-file=.env.op -- python scripts/generate_exam_token.py \\
    --exam-id spring2026-final \\
    --from-csv students.csv \\       # columns: student_id, section
    --lab-ids red-team detection-monitoring \\
    --duration-hours 3

Requires EXAM_SECRET in environment (e.g. via .env.op -> op://keys/<uuid>/exam_secret).
"""

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

# Add repo root to path so we can import framework modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from framework.exam_token import generate_token

SECTION_TO_VARIANT = {
    "A": "exam_v1",
    "B": "exam_v2",
    "C": "exam_v3",
    "D": "exam_v4",
    "1": "exam_v1",
    "2": "exam_v2",
    "3": "exam_v3",
}

DEFAULT_ATTEMPT_CAPS = {
    # Red Team levels
    "level_1": 5, "level_2": 4, "level_3": 4, "level_4": 3, "level_5": 3,
    # Detection & Monitoring
    "D1": 1, "D2": 3, "D3": 2,
    # Data Poisoning
    "RP.1": 2, "RP.2": 2, "RP.3": 2, "RP.4": 2, "RP.5": 2, "RP.6": 2,
    # Blue Team
    "ph_level_1": 3, "ph_level_2": 3, "ph_level_3": 3, "ph_level_4": 3, "ph_level_5": 3,
    "waf_rules": 2, "pipeline": 2, "behavioral": 3,
    # Multimodal
    "P1": 2, "P5": 2,
}


def build_payload(
    student_id: str,
    exam_id: str,
    lab_ids: list[str],
    section: str,
    duration_hours: float,
    attempt_caps: dict | None,
    time_limit_seconds: int | None,
) -> dict:
    now = int(time.time())
    variant = SECTION_TO_VARIANT.get(section.upper(), f"exam_v{section.lower()}")
    caps = attempt_caps if attempt_caps is not None else DEFAULT_ATTEMPT_CAPS
    tl = time_limit_seconds or int(duration_hours * 3600)
    return {
        "version": "1",
        "exam_id": exam_id,
        "student_id": student_id,
        "lab_ids": lab_ids,
        "issued_at": now,
        "expires_at": now + int(duration_hours * 3600),
        "time_limit_seconds": tl,
        "attempt_caps": caps,
        "dataset_variant": variant,
    }


def token_to_url(token: str, lab_id: str) -> str:
    space_map = {
        "red-team": "nikobehar/red-team-workshop",
        "blue-team": "nikobehar/blue-team-workshop",
        "multimodal": "nikobehar/ai-sec-lab4-multimodal",
        "data-poisoning": "nikobehar/ai-sec-lab5-data-poisoning",
        "detection-monitoring": "nikobehar/ai-sec-lab6-detection",
    }
    space = space_map.get(lab_id, lab_id)
    return f"https://huggingface.co/spaces/{space}?exam_token={token}"


def main():
    parser = argparse.ArgumentParser(description="Generate AI Security Labs exam tokens")
    parser.add_argument("--exam-id", required=True, help="Exam identifier (e.g. spring2026-final)")
    parser.add_argument("--lab-ids", nargs="+", required=True,
                        help="Lab(s) to include (e.g. red-team detection-monitoring)")
    parser.add_argument("--section", default="A",
                        help="Course section (A/B/C -> exam_v1/v2/v3). Default: A")
    parser.add_argument("--duration-hours", type=float, default=3.0,
                        help="Token validity window in hours. Default: 3")
    parser.add_argument("--time-limit-seconds", type=int, default=None,
                        help="Countdown timer shown to student (defaults to duration in seconds)")
    parser.add_argument("--attempt-caps", type=json.loads, default=None,
                        help='JSON dict of attempt caps, e.g. \'{"level_1":3,"D1":1}\'')

    # Single student
    parser.add_argument("--student-id", default=None,
                        help="Student LMS identifier (single-student mode)")
    # Bulk mode
    parser.add_argument("--from-csv", default=None,
                        help="CSV file with columns: student_id[,section]. Overrides --student-id and --section.")
    parser.add_argument("--output-csv", default=None,
                        help="Write token URLs to this CSV file (bulk mode). Default: stdout.")

    args = parser.parse_args()

    secret = os.environ.get("EXAM_SECRET")
    if not secret:
        print("ERROR: EXAM_SECRET environment variable not set.", file=sys.stderr)
        print("Run with: op run --env-file=.env.op -- python scripts/generate_exam_token.py ...", file=sys.stderr)
        sys.exit(1)

    if args.from_csv:
        # Bulk mode
        rows = []
        with open(args.from_csv) as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = row["student_id"].strip()
                sec = row.get("section", args.section).strip()
                payload = build_payload(
                    student_id=sid,
                    exam_id=args.exam_id,
                    lab_ids=args.lab_ids,
                    section=sec,
                    duration_hours=args.duration_hours,
                    attempt_caps=args.attempt_caps,
                    time_limit_seconds=args.time_limit_seconds,
                )
                token = generate_token(payload, secret)
                entry = {"student_id": sid, "section": sec}
                for lab_id in args.lab_ids:
                    entry[f"url_{lab_id}"] = token_to_url(token, lab_id)
                entry["token"] = token
                rows.append(entry)

        if args.output_csv:
            with open(args.output_csv, "w", newline="") as f:
                if rows:
                    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                    writer.writeheader()
                    writer.writerows(rows)
            print(f"Wrote {len(rows)} tokens to {args.output_csv}")
        else:
            if rows:
                header = list(rows[0].keys())
                print(",".join(header))
                for r in rows:
                    print(",".join(str(r[k]) for k in header))
    else:
        # Single student mode
        if not args.student_id:
            print("ERROR: --student-id is required in single-student mode.", file=sys.stderr)
            sys.exit(1)

        payload = build_payload(
            student_id=args.student_id,
            exam_id=args.exam_id,
            lab_ids=args.lab_ids,
            section=args.section,
            duration_hours=args.duration_hours,
            attempt_caps=args.attempt_caps,
            time_limit_seconds=args.time_limit_seconds,
        )
        token = generate_token(payload, secret)

        print(f"\nExam Token for: {args.student_id}")
        print(f"Exam ID:        {args.exam_id}")
        print(f"Section:        {args.section} ({payload['dataset_variant']})")
        print(f"Labs:           {', '.join(args.lab_ids)}")
        print(f"Valid for:      {args.duration_hours} hours")
        print(f"Expires:        {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(payload['expires_at']))}")
        print(f"Attempt caps:   {json.dumps(payload['attempt_caps'], separators=(',', ':'))}")
        print()
        print("URLs to distribute (one per lab):")
        for lab_id in args.lab_ids:
            print(f"  {lab_id}: {token_to_url(token, lab_id)}")
        print()
        print(f"Token: {token}")


if __name__ == "__main__":
    main()
