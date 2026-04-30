"""
ExamSession: per-student exam state tracker for AI Security Labs.

One ExamSession is created per validated exam token. It tracks:
  - attempt counts and timing per exercise (enforces caps from the token)
  - theory answers (MCQ + short answer)
  - exam start/end timestamps

Sessions live in-memory keyed by the token string.
On server restart the session is lost; the client caches partial state
in sessionStorage and the receipt endpoint reconstructs from that cache.
"""

import threading
import time


class AttemptCapError(Exception):
    """Raised when a student tries to exceed the attempt cap for an exercise."""
    def __init__(self, exercise_id: str, cap: int):
        super().__init__(f"Attempt cap reached for '{exercise_id}' ({cap}/{cap} attempts used).")
        self.exercise_id = exercise_id
        self.cap = cap


class ExamSession:
    def __init__(self, token: str, exam_context: dict):
        self.token = token
        self.exam_id: str = exam_context["exam_id"]
        self.student_id: str = exam_context["student_id"]
        self.lab_id: str = exam_context.get("lab_ids", ["unknown"])[0]
        self.dataset_variant: str = exam_context.get("dataset_variant", "workshop")
        self.time_limit_seconds: int = exam_context.get("time_limit_seconds", 7200)
        self.attempt_caps: dict[str, int] = exam_context.get("attempt_caps", {})
        self.started_at: int = int(time.time())
        self.ended_at: int | None = None

        # {exercise_id: [attempt_record, ...]}
        self._attempts: dict[str, list[dict]] = {}
        # {exercise_id: best_score}
        self._scores: dict[str, int] = {}
        # Theory answers (set once, on POST /api/exam/theory)
        self._theory: dict | None = None

    # ------------------------------------------------------------------
    # Attempt management
    # ------------------------------------------------------------------

    def attempt_count(self, exercise_id: str) -> int:
        return len(self._attempts.get(exercise_id, []))

    def remaining_attempts(self, exercise_id: str) -> int | None:
        """Returns None if no cap is set (unlimited)."""
        cap = self.attempt_caps.get(exercise_id)
        if cap is None:
            return None
        return max(0, cap - self.attempt_count(exercise_id))

    def check_attempt_cap(self, exercise_id: str) -> None:
        """Raises AttemptCapError if the cap has been reached."""
        cap = self.attempt_caps.get(exercise_id)
        if cap is not None and self.attempt_count(exercise_id) >= cap:
            raise AttemptCapError(exercise_id, cap)

    def record_attempt(
        self,
        exercise_id: str,
        success: bool,
        score: int,
        elapsed_seconds: float = 0.0,
        metadata: dict | None = None,
    ) -> dict:
        """
        Record one attempt. Returns the attempt record.
        Call check_attempt_cap() before this if you want the cap enforced.
        """
        record = {
            "attempt_number": self.attempt_count(exercise_id) + 1,
            "timestamp": int(time.time()),
            "elapsed_seconds": round(elapsed_seconds, 1),
            "success": success,
            "score_awarded": score if success else 0,
            **(metadata or {}),
        }
        self._attempts.setdefault(exercise_id, []).append(record)
        if success:
            prev = self._scores.get(exercise_id, 0)
            self._scores[exercise_id] = max(prev, score)
        return record

    # ------------------------------------------------------------------
    # Theory management
    # ------------------------------------------------------------------

    def record_theory(self, mcq_answers: list[dict], short_answers: list[dict]) -> None:
        """Store theory answers. Can only be submitted once."""
        self._theory = {
            "submitted_at": int(time.time()),
            "mcq_answers": mcq_answers,
            "short_answers": short_answers,
        }

    def theory_submitted(self) -> bool:
        return self._theory is not None

    # ------------------------------------------------------------------
    # Receipt serialization
    # ------------------------------------------------------------------

    def elapsed_seconds(self) -> int:
        end = self.ended_at or int(time.time())
        return end - self.started_at

    def remaining_seconds(self) -> int:
        return max(0, self.time_limit_seconds - self.elapsed_seconds())

    def is_expired(self) -> bool:
        return self.remaining_seconds() == 0

    def finalize(self) -> None:
        if self.ended_at is None:
            self.ended_at = int(time.time())

    def to_practical_receipt(self, exercise_definitions: list[dict]) -> dict:
        """
        Build the practical section of the receipt.

        exercise_definitions: list of {exercise_id, display_name, max_score}
        returned from each lab's endpoint configuration.
        """
        exercises = []
        total_earned = 0
        total_max = 0
        for defn in exercise_definitions:
            eid = defn["exercise_id"]
            attempts = self._attempts.get(eid, [])
            earned = self._scores.get(eid, 0)
            cap = self.attempt_caps.get(eid)
            max_score = defn.get("max_score", 100)
            total_earned += earned
            total_max += max_score
            exercises.append({
                "exercise_id": eid,
                "display_name": defn.get("display_name", eid),
                "max_score": max_score,
                "earned_score": earned,
                "attempt_cap": cap,
                "attempts": [
                    {k: v for k, v in a.items() if k != "model_output"}
                    | ({"model_output": (a["model_output"][:500] + " [...]")
                        if len(a.get("model_output", "")) > 500
                        else a.get("model_output", "")}
                       if "model_output" in a else {})
                    for a in attempts
                ],
            })
        return {
            "exercises": exercises,
            "total_practical_score": total_earned,
            "max_practical_score": total_max,
        }

    def to_theory_receipt(self, scored_mcq: list[dict]) -> dict:
        """
        Build the theory section of the receipt.

        scored_mcq: list of {question_id, question_text, student_answer,
                              correct_answer, correct, bloom_level,
                              points_earned, explanation}
        (server-side scoring adds correct_answer and points_earned)
        """
        if not self._theory:
            return {"submitted": False}

        short_answers = [
            {
                "question_id": sa["question_id"],
                "prompt": sa.get("prompt", ""),
                "student_response": sa["response"],
                "word_count": len(sa["response"].split()),
                "points_possible": sa.get("points_possible", 20),
                "points_earned": None,
                "instructor_comment": None,
            }
            for sa in self._theory["short_answers"]
        ]

        mcq_score = sum(q.get("points_earned", 0) for q in scored_mcq)
        mcq_max = sum(q.get("points_possible", 5) for q in scored_mcq)
        sa_max = sum(sa["points_possible"] for sa in short_answers)

        return {
            "submitted": True,
            "submitted_at": self._theory["submitted_at"],
            "mcq": scored_mcq,
            "short_answers": short_answers,
            "mcq_score": mcq_score,
            "mcq_max": mcq_max,
            "short_answer_max": sa_max,
            "short_answer_requires_instructor_grading": True,
        }


# ------------------------------------------------------------------
# Module-level session registry
# ------------------------------------------------------------------

_SESSIONS: dict[str, "ExamSession"] = {}
_LOCK = threading.Lock()


def get_session(token: str) -> "ExamSession | None":
    with _LOCK:
        return _SESSIONS.get(token)


def create_session(token: str, exam_context: dict) -> "ExamSession":
    with _LOCK:
        session = ExamSession(token, exam_context)
        _SESSIONS[token] = session
        return session


def get_or_create_session(token: str, exam_context: dict) -> "ExamSession":
    with _LOCK:
        if token not in _SESSIONS:
            _SESSIONS[token] = ExamSession(token, exam_context)
        return _SESSIONS[token]
