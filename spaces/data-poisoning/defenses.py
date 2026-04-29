"""Phase 3 — four toggleable defense layers for the RAG poisoning pipeline.

Each defense is a small pure-ish function that returns a `DefenseLogEntry`-shaped
dict (`name`, `verdict`, `detail`) or `None` (skipped because the defense isn't
in the active set). The rag_pipeline runs them at the correct stage:

  1. provenance_check     — pre-retrieval, ingestion-side allowlist
  2. adversarial_filter   — pre-retrieval, ingestion-side keyword/regex
  3. <retrieve top-k>
  4. retrieval_diversity  — post-retrieval, pre-LLM (single-source clustering)
  5. <LLM generate>
  6. output_grounding     — post-LLM, validates cited doc IDs

Defense identifiers (canonical, surfaced in `defenses_applied` form-field):
    DEFENSE_IDS = {"provenance_check", "adversarial_filter",
                   "retrieval_diversity", "output_grounding"}

Design intent (catch-rate matrix, per `docs/phase3-calibration.md`):
- provenance_check    expected 6/6 — universal first-line allowlist
- adversarial_filter  expected 3/6 — RP.1, RP.2, RP.3 (overt narrative cues)
- retrieval_diversity expected 1-2/6 — RP.6 (multi-doc consensus)
- output_grounding    expected 1/6 — RP.4 (fabricated citations)

Phase 5 verification will replace these with measured numbers (Multimodal Lab
precedent — design-intent is the starting point, not the deliverable).
"""

from __future__ import annotations

import re
from typing import Optional

from corpus import Document


DEFENSE_IDS = {
    "provenance_check",
    "adversarial_filter",
    "retrieval_diversity",
    "output_grounding",
}


# ---------------------------------------------------------------------------
# 1. Provenance Check (ingestion-side allowlist)
# ---------------------------------------------------------------------------

TRUSTED_SOURCE_PREFIXES: tuple[str, ...] = ("internal-policies/",)


def provenance_check(active_docs: list[Document]) -> Optional[dict]:
    """BLOCK if any active doc has a source URI outside the trusted allowlist.

    The 8 attack docs all use source `(attack — pre-canned)`, which won't match
    any prefix in `TRUSTED_SOURCE_PREFIXES`. The 6 legit docs all start with
    `internal-policies/`. -> expected 6/6 catches at v1 corpus size.
    """
    bad = [d for d in active_docs if not d.source.startswith(TRUSTED_SOURCE_PREFIXES)]
    if not bad:
        return {
            "name": "provenance_check",
            "verdict": "PASSED",
            "detail": f"all {len(active_docs)} active docs in trusted-sources allowlist",
        }
    sample = ", ".join(d.id for d in bad[:3])
    return {
        "name": "provenance_check",
        "verdict": "BLOCKED",
        "detail": (
            f"{len(bad)} doc(s) not in trusted_sources allowlist (sources must start with "
            f"{TRUSTED_SOURCE_PREFIXES!r}): {sample}"
        ),
    }


# ---------------------------------------------------------------------------
# 2. Adversarial Filter (ingestion-side keyword/regex pre-scan)
# ---------------------------------------------------------------------------

# Patterns chosen to fire on overt authority-spoof / supersession / instruction
# injection language. Deliberately narrow so RP.4 (citation spoof), RP.5
# (keyword-stuffing), and RP.6 (subtle multi-doc) slip past — that's the
# educational point about layered defenses.
ADVERSARIAL_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bATTENTION\s+ALL\s+EMPLOYEES?\b"), "broadcast-style attention call"),
    (re.compile(r"\bAS\s+APPROVED\s+BY\b", re.IGNORECASE), "fake authority assertion"),
    # Note: `auto-onboarded` was tested but produced a false positive on the
    # legit it-001 doc which says "No vendor may be auto-onboarded" (negation
    # context). RP.2 is still caught reliably by "AS APPROVED BY".
    (
        re.compile(r"\bsupersedes?\s+(?:the\s+)?\d{4}\s+(?:version|policy|onboarding|checklist|memo)\b", re.IGNORECASE),
        "explicit year-pinned supersession claim",
    ),
    (re.compile(r"\bskip\s+(?:I-9|the\s+IP\s+assignment)\b", re.IGNORECASE), "policy-skip directive"),
    (re.compile(r"\bignore\s+(?:prior|previous|all|the\s+above)\b", re.IGNORECASE), "ignore-prior instruction"),
    # Note: `effective immediately` was tested but it cross-catches RP.6
    # (rp6-poison-a contains "Effective immediately, contractors..."). Per
    # the layered-defense narrative we want RP.6 to only be caught by
    # retrieval_diversity (its designed-for layer), so the pattern is omitted.
]


def adversarial_filter(active_docs: list[Document]) -> Optional[dict]:
    """BLOCK if any active doc body matches a known injection pattern."""
    hits: list[str] = []
    for doc in active_docs:
        for pattern, label in ADVERSARIAL_PATTERNS:
            if pattern.search(doc.body_markdown):
                hits.append(f"{doc.id}: {label}")
                break  # one hit per doc is enough
    if not hits:
        return {
            "name": "adversarial_filter",
            "verdict": "PASSED",
            "detail": f"no injection patterns in {len(active_docs)} active doc(s)",
        }
    sample = "; ".join(hits[:3])
    return {
        "name": "adversarial_filter",
        "verdict": "BLOCKED",
        "detail": f"{len(hits)} doc(s) match injection patterns: {sample}",
    }


# ---------------------------------------------------------------------------
# 3. Retrieval Diversity (post-retrieval, pre-LLM rerank)
# ---------------------------------------------------------------------------

def retrieval_diversity(top_k: list[tuple[Document, float]]) -> Optional[dict]:
    """BLOCK if any single source URI accounts for >1 of the top-k results.

    Catches multi-document consensus attacks (RP.6: 3 sibling docs share source
    `(attack — pre-canned)`). Single-doc attacks (RP.1—RP.5) won't trigger this
    defense — that's deliberate; layered defenses are the educational point.
    """
    source_counts: dict[str, int] = {}
    for doc, _ in top_k:
        source_counts[doc.source] = source_counts.get(doc.source, 0) + 1
    clusters = {src: n for src, n in source_counts.items() if n > 1}
    if not clusters:
        return {
            "name": "retrieval_diversity",
            "verdict": "PASSED",
            "detail": f"top-{len(top_k)} retrieval has {len(source_counts)} distinct source(s); no cluster",
        }
    sample = ", ".join(f"{src} ×{n}" for src, n in clusters.items())
    return {
        "name": "retrieval_diversity",
        "verdict": "BLOCKED",
        "detail": f"single-source cluster detected in top-{len(top_k)}: {sample}",
    }


# ---------------------------------------------------------------------------
# 4. Output Grounding (post-LLM citation validation)
# ---------------------------------------------------------------------------

# Permissive doc-ID candidate pattern: matches doc-ID-shaped tokens in the model
# response. Captures both the legit corpus pattern (`fin-001-reimbursement-2025`,
# `it-002-badge-policy`, `rp1-poison`) and the attacker-fabricated NX pattern
# (`NX-LEGAL-2024-007`).
_DOC_ID_CANDIDATE = re.compile(
    r"\b("
    r"NX-[A-Z]+-\d{4}-\d{3,4}"        # NX-LEGAL-2024-007 (typical attacker-fabricated form)
    r"|[a-z]{2,5}-\d{3}-[a-z0-9-]+"   # fin-001-reimbursement-2025 etc.
    r"|rp\d-poison(?:-[a-c])?"        # rp1-poison, rp6-poison-a
    r")\b",
    re.IGNORECASE,
)


def output_grounding(model_response: str, valid_doc_ids: set[str]) -> Optional[dict]:
    """BLOCK if the response cites any doc ID not in the active corpus.

    Scans the model output for doc-ID-shaped tokens. Any token that doesn't match
    a real doc in the active corpus is a fabricated citation -> BLOCK. Catches
    RP.4 (citation spoof) reliably; passes for attacks where the model cites
    only real (poisoned-but-real) doc IDs.
    """
    if not model_response:
        return {
            "name": "output_grounding",
            "verdict": "SKIPPED",
            "detail": "no model response to ground (likely blocked earlier)",
        }
    candidates = {m.group(1) for m in _DOC_ID_CANDIDATE.finditer(model_response)}
    if not candidates:
        # No citations at all - soft pass; the spec defines BLOCKED as fabricated
        # citation, not as "model failed to cite". Mirrors the v1 lenience the
        # Multimodal Lab takes on output_redaction's "no canary present" case.
        return {
            "name": "output_grounding",
            "verdict": "PASSED",
            "detail": "model response cites no doc IDs; nothing to ground",
        }
    # Case-insensitive membership: the regex uses re.IGNORECASE so candidates
    # may differ in case from the canonical (lowercase) corpus IDs. Without this
    # normalization, a model echoing "FIN-001-REIMBURSEMENT-2025" would be
    # misclassified as a fabricated citation.
    valid_lower = {vid.lower() for vid in valid_doc_ids}
    fabricated = sorted(c for c in candidates if c.lower() not in valid_lower)
    if not fabricated:
        return {
            "name": "output_grounding",
            "verdict": "PASSED",
            "detail": f"all {len(candidates)} cited doc ID(s) match the active corpus",
        }
    sample = ", ".join(fabricated[:3])
    return {
        "name": "output_grounding",
        "verdict": "BLOCKED",
        "detail": f"{len(fabricated)} fabricated citation(s) in response: {sample}",
    }
