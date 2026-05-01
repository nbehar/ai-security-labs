"""
scoring.py — Shared scoring and leaderboard logic for all workshops
===================================================================
"""


def calculate_score(
    blocked: int,
    total: int,
    legit_passed: int = 0,
    legit_total: int = 0,
    elapsed_seconds: float = 0,
    fp_penalty_per: int = 5,
    time_bonus_max: int = 10,
    time_budget_seconds: int = 300,
) -> dict:
    """Calculate challenge score with false positive penalty and time bonus."""
    block_score = round((blocked / max(total, 1)) * 100)
    legit_bonus = round((legit_passed / max(legit_total, 1)) * 20) if legit_total > 0 else 0
    fp_penalty = (legit_total - legit_passed) * fp_penalty_per if legit_total > 0 else 0
    time_bonus = max(0, round((time_budget_seconds - elapsed_seconds) / (time_budget_seconds / time_bonus_max)))

    return {
        "block_score": block_score,
        "legit_bonus": legit_bonus,
        "false_positive_penalty": fp_penalty,
        "time_bonus": min(time_bonus, time_bonus_max),
        "total": max(0, block_score + legit_bonus - fp_penalty + time_bonus),
    }


class Leaderboard:
    """In-memory leaderboard (resets on restart)."""

    def __init__(self, score_keys: list[str]):
        self._entries: list[dict] = []
        self._score_keys = score_keys

    def update(self, name: str, challenge: str, score: int) -> int:
        """Update a participant's score. Returns their rank."""
        entry = next((e for e in self._entries if e["name"] == name), None)
        if not entry:
            entry = {"name": name, **{k: 0 for k in self._score_keys}, "total": 0}
            self._entries.append(entry)

        if challenge in self._score_keys and score > entry.get(challenge, 0):
            entry[challenge] = score

        entry["total"] = sum(entry.get(k, 0) for k in self._score_keys)
        self._entries.sort(key=lambda e: e["total"], reverse=True)
        return next(i + 1 for i, e in enumerate(self._entries) if e["name"] == name)

    def get_all(self) -> list[dict]:
        """Get ranked leaderboard."""
        return [{"rank": i + 1, **e} for i, e in enumerate(self._entries)]
