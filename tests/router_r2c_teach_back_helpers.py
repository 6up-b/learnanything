"""What other test files use from ``tests/test_router_r2c_teach_back.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.router_model_fakes import FakeLLM


TRANSCRIPT = (
    "# Teach-back transcript\n\n## Opening explanation\n\nA basis spans the space and is independent.\n\n"
    "## Follow-up 1 (criterion: c_independence)\n\n**Student asked:** Why independent?\n\n"
    "**Learner answered:** So no vector is redundant, I think.\n"
)


def _summary_llm(calls):
    def answer(request):
        calls.append(request)
        return {"explained_correctly": ["a basis spans the space"],
                "missing_or_wrong": ["why independence makes the coordinates unique"],
                "learner_words": ["no vector is redundant"]}

    return FakeLLM(answer=answer)


def _teach_back(env, attempt_id="att_tb_1", item="pi_m1a", lo="lo_m1", at="2026-10-11T09:00:00Z"):
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "correctness, hints_used, primed, latency_seconds, created_at, session_id, learner_answer_md) "
            "VALUES (?, ?, ?, 'teach_back', 'teach_back', 0.5, 0, 0, 300, ?, 's0', ?)",
            (attempt_id, item, lo, at, TRANSCRIPT),
        )
        connection.commit()
    return attempt_id
