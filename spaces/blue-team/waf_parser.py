"""
waf_parser.py — WAF rule parser and evaluator for the Blue Team Workshop
=========================================================================
Supports a simple DSL:
  BLOCK if contains "text"
  BLOCK if regex "pattern"
  ALLOW if contains "text"

Max 30 rules. ALLOW rules are checked first (whitelist), then BLOCK.
"""

import re
from typing import Optional

MAX_RULES = 30

# Pattern to parse a rule line
RULE_PATTERN = re.compile(
    r'^(BLOCK|ALLOW)\s+if\s+(contains|regex)\s+"(.+)"$',
    re.IGNORECASE,
)


def parse_rules(text: str) -> tuple[list[dict], list[str]]:
    """Parse rule text into a list of rule dicts.

    Returns (rules, errors).
    """
    rules = []
    errors = []

    lines = [line.strip() for line in text.strip().split("\n") if line.strip() and not line.strip().startswith("#")]

    if len(lines) > MAX_RULES:
        errors.append(f"Too many rules: {len(lines)} (max {MAX_RULES})")
        lines = lines[:MAX_RULES]

    for i, line in enumerate(lines, 1):
        match = RULE_PATTERN.match(line)
        if not match:
            errors.append(f"Line {i}: Invalid syntax: {line[:60]}")
            continue

        action = match.group(1).upper()
        mode = match.group(2).lower()
        pattern = match.group(3)

        # Validate regex
        if mode == "regex":
            try:
                re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                errors.append(f"Line {i}: Invalid regex: {e}")
                continue

        rules.append({
            "action": action,
            "mode": mode,
            "pattern": pattern,
            "line": i,
        })

    return rules, errors


def evaluate_rules(rules: list[dict], query: str) -> tuple[bool, Optional[dict]]:
    """Evaluate a query against a rule set.

    Returns (blocked: bool, matched_rule: dict or None).

    Logic:
    1. Check ALLOW rules first — if any match, query passes (not blocked)
    2. Check BLOCK rules — if any match, query is blocked
    3. If no rules match, query passes (default allow)
    """
    query_lower = query.lower()

    # Check ALLOW rules first
    for rule in rules:
        if rule["action"] != "ALLOW":
            continue
        if _matches(rule, query, query_lower):
            return False, rule  # Allowed — not blocked

    # Check BLOCK rules
    for rule in rules:
        if rule["action"] != "BLOCK":
            continue
        if _matches(rule, query, query_lower):
            return True, rule  # Blocked

    # Default: not blocked
    return False, None


def _matches(rule: dict, query: str, query_lower: str) -> bool:
    """Check if a rule matches a query."""
    if rule["mode"] == "contains":
        return rule["pattern"].lower() in query_lower
    elif rule["mode"] == "regex":
        try:
            return bool(re.search(rule["pattern"], query, re.IGNORECASE))
        except re.error:
            return False
    return False
