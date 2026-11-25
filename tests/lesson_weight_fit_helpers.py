"""Shared by the lesson-weight fit's tests: a graded answer with a chosen id (``tests/test_lesson_weight_fit_reads.py``,
``tests/test_lesson_weight_facts.py``)."""

from __future__ import annotations

from learnloop.vault.loader import load_vault


def apply_with_id(paths, repository, item_id, points, *, attempt_id, when, primed=False):
    """A self-graded answer with a chosen id, through the shared attempt step."""

    from learnloop.attempts.attempts import (
        ApplyAttemptInput,
        AttemptDraft,
        ResolvedGrade,
        apply_attempt,
        calculate_rubric_score,
    )
    from learnloop.attempts.grading import resolved_rubric
    from learnloop.clock import FrozenClock

    vault = load_vault(paths.root)
    rubric = resolved_rubric(vault, vault.practice_items[item_id])
    criterion = {"correctness": float(points)}
    stamp = when.isoformat().replace("+00:00", "Z")
    return apply_attempt(vault, repository, ApplyAttemptInput(
        draft=AttemptDraft(practice_item_id=item_id, learner_answer_md="an answer", attempt_type="independent_attempt",
                           primed=primed),
        attempt_id=attempt_id,
        grade=ResolvedGrade(
            rubric_score=calculate_rubric_score(rubric, criterion, []), criterion_points=criterion,
            evidence_rows=[{"id": f"ge_{attempt_id}", "criterion_id": "correctness", "points_awarded": float(points),
                            "evidence": "self", "notes": None, "local_grader_id": "self", "grader_tier": 1,
                            "created_at": stamp}],
            error_attributions=[], grader_confidence=1.0, confidence=3, manual_review_reason=None,
            feedback_md="self-graded"),
        grading_source="self"), clock=FrozenClock(when))


def record_text(name: str) -> str:
    """A review record under ``docs/reviews`` (the owner-copy queries the tests run are read from it)."""

    from pathlib import Path

    return (Path(__file__).resolve().parents[1] / "docs/reviews" / name).read_text()


def owner_copy_window_query(record: str = "algorithm-mvp-0.72.md") -> str:
    """The first query of a record's owner-copy procedure (the fitted windows' coverage)."""

    body = record_text(record)
    body = body[body.index("PRAGMA query_only = ON;\n") + len("PRAGMA query_only = ON;\n"):]
    return body[:body.index("SELECT count(*) AS foreign_key_violations")]


def owner_copy_label_queries(record: str, marker: str) -> list[str]:
    """A record's owner-copy label query (several statements), the first ``<<'SQL'`` block after ``marker``."""

    text = record_text(record)
    start = text.index(marker)
    body = text[text.index("<<'SQL'\n", start) + len("<<'SQL'\n"):]
    return [statement.strip() for statement in body[:body.index("\nSQL\n")].split(";") if statement.strip()]
