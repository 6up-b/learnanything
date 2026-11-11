"""What other test files use from ``tests/test_teacher_te0_confidence_events.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from contextlib import closing

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.router.card import CardInputs
from learnloop.vault.loader import load_vault

from tests.approach_map_fakes import ITEM, LO, map_vault


def _attempt(sqlite_path, attempt_id: str, *, at: str, correctness: float | None, tap: int | None = None,
             hedge: str | None = None, attempt_type: str = "independent_attempt", item_id: str = ITEM,
             lo_id: str = LO, local_grader_id: str | None = None, answer: str = "my answer") -> None:
    with closing(connect(sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO practice_attempts (id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, correctness, rubric_score, created_at, answer_confidence) "
            "VALUES (?, ?, ?, 'short_answer', ?, ?, ?, ?, ?, ?)",
            (attempt_id, item_id, lo_id, attempt_type, answer, correctness,
             None if correctness is None else correctness * 4, at, tap))
        if hedge is not None:
            connection.execute(
                "INSERT INTO grading_evidence (id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
                "learner_confidence, local_grader_id) VALUES (?, ?, 'correctness', ?, 3, ?, ?, ?)",
                (f"ge_{attempt_id}", attempt_id, (correctness or 0) * 4, at, hedge, local_grader_id))
        connection.commit()


def _vault(tmp_path):
    paths = map_vault(tmp_path)
    return paths, load_vault(paths.root), Repository.attach(paths.sqlite_path)


def _card_inputs(**extra) -> CardInputs:
    entries = [{"attempt_id": f"a{i}", "at": f"2026-10-{i + 1:02d}T09:00:00Z", "learning_object_id": "lo",
                "topic": "Bases", "kind": "short_answer", "result": ["correct", "incorrect", "held_for_review"][i % 3],
                "hints_used": i % 2, "key_status": None, "stem": "What is a basis?",
                "answer": "a spanning independent set"} for i in range(4)]
    work = extra.pop("work", None)
    if work:
        for entry, event in zip(entries, work, strict=False):
            if event:
                entry["confidence"] = event
    return CardInputs(
        decision={"surface": "daily_plan", "decided_at": "2026-10-12T09:00:00Z"},
        session={"plan_kind": "normal", "minutes_left": 10, "minutes_budget": 25},
        candidates=[{"ref": "maintain:1", "kind": "maintain", "est_minutes": 4, "topics": ["Bases"],
                     "reversible": True, "reason_code": "review"}],
        learning_objects={"lo": {"title": "Bases", "status": "demonstrated", "evidence": {"graded": 3}}},
        interaction_7d={"attempts": 3, "hints_used": 1}, unknowns=["never tested: Spans"], recent_work=entries,
        **extra,
    )


def _gathered_card(tmp_path, monkeypatch, attempts):
    from tests.router_card_helpers import _card, _card_world

    env = _card_world(tmp_path, monkeypatch)
    for row in attempts:
        _attempt(env.repository.sqlite_path, **row)
    return _card(env)


def _tutor_context(vault, repository, context: str):
    from learnloop.tutor.tutor_qa import _build_context

    return _build_context(vault, repository, context=context, question_md="Why is F(1/2) the answer?",
                          candidates=[], thread=[], item=vault.practice_items[ITEM], attempt=None, note=None,
                          note_id=None, now_iso="2027-01-01T00:00:00Z")
