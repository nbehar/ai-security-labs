"""
waf_parser.py — Output sanitization rule parser for the Detection & Monitoring Lab.

DSL: one rule per line, format: BLOCK <regex> or ALLOW <regex>
Example:
  BLOCK \\b\\d{3}-\\d{2}-\\d{4}\\b
  BLOCK (?i)password\\s*[:=]\\s*\\S+
  ALLOW (?i)example\\.com

ALLOW rules are checked first (whitelist override). If any ALLOW rule matches,
the output is not blocked regardless of BLOCK rules.
"""

import re
from typing import Optional

MAX_RULES = 30

RULE_LINE_RE = re.compile(r'^(BLOCK|ALLOW)\s+(\S.*)$', re.IGNORECASE)


def parse_rules(text: str) -> tuple[list[dict], list[str]]:
    """Parse rule text into rule dicts. Returns (rules, errors)."""
    rules = []
    errors = []

    lines = [line.strip() for line in text.strip().splitlines()
             if line.strip() and not line.strip().startswith("#")]

    if len(lines) > MAX_RULES:
        errors.append(f"Too many rules: {len(lines)} (max {MAX_RULES})")
        lines = lines[:MAX_RULES]

    for i, line in enumerate(lines, 1):
        m = RULE_LINE_RE.match(line)
        if not m:
            errors.append(f"Line {i}: Invalid syntax — expected BLOCK <regex> or ALLOW <regex>: {line[:60]}")
            continue

        action = m.group(1).upper()
        pattern = m.group(2).strip()

        try:
            re.compile(pattern)
        except re.error as e:
            errors.append(f"Line {i}: Invalid regex '{pattern[:40]}': {e}")
            continue

        rules.append({"action": action, "pattern": pattern, "line": i})

    return rules, errors


def evaluate_rules(rules: list[dict], text: str) -> tuple[bool, Optional[dict]]:
    """Evaluate text against rules. Returns (blocked, matched_rule | None)."""
    for rule in rules:
        if rule["action"] == "ALLOW":
            if _matches(rule["pattern"], text):
                return False, rule

    for rule in rules:
        if rule["action"] == "BLOCK":
            if _matches(rule["pattern"], text):
                return True, rule

    return False, None


def _matches(pattern: str, text: str) -> bool:
    try:
        return bool(re.search(pattern, text))
    except re.error:
        return False
