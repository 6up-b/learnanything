"""Teacher TE1: the lesson lifecycle, the actions and the checks (spec_teacher_v1 §6-§13, §20).

Every model is ``TeacherFake`` (a scripted teacher and a blind grader); no network.
"""

from __future__ import annotations

import pytest

from learnloop.db.repositories import Repository
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import (
    TeacherFake,
    build_teacher_vault,
    check_turn,
    clients,
    close_turn,
    landed_and_close_turn,
    landed_turn,
    plan_turn,
)


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _open(tmp_path, turns, **kwargs):
    paths, repository = build_teacher_vault(tmp_path / "vault", **kwargs)
    fake = TeacherFake(turns)
    vault = load_vault(paths.root)
    view = S.open_lesson(vault, repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake))
    return paths, repository, fake, view


def test_a_whole_lesson_opens_teaches_checks_and_closes_with_delayed_checks(tmp_path):
    paths, repository, fake, view = _open(tmp_path, [plan_turn, check_turn()])
    lesson_id = view["lesson_id"]
    assert [entry["kind"] for entry in view["feed"]][:1] == ["message"]
    assert view["plan"] and view["plan"][0]["id"] == "n1"
    # The learner says go; the teacher poses a check (minted, held, collapsed on screen).
    view = S.turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="reply",
                  payload={"text": "Go ahead."}, clients=clients(fake))
    assert view["open_check"] is not None and "committed_solution" not in str(view["open_check"])
    fake.turns = [landed_and_close_turn()]
    view = S.turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="answer_check",
                  payload={"answer": "det(A - tI) = 0", "tap": 4, "thinking": "THINKINGNOTE char poly"},
                  clients=clients(fake))
    assert view["closed"] and view["close_reason"] == "goal_reached"
    check = _rows(repository, "SELECT status, attempt_id, mass_applied, mass_learned, tap FROM lesson_checks")
    assert len(check) == 1 and check[0][0] == "answered" and check[0][4] == 4
    assert 0.0 < check[0][2] < 1.0 and abs(check[0][2] - check[0][3]) < 1e-12
    attempt = _rows(repository, "SELECT attempt_type, answer_confidence, primed FROM practice_attempts WHERE id = ?",
                    (check[0][1],))
    assert attempt == [("reconstruction_after_walkthrough", 4, 0)]
    # The blind grader saw the answer only: never the thinking note.
    assert fake.grading_contexts and all("THINKINGNOTE" not in str(c) for c in fake.grading_contexts)
    grading_prompts = [p for purpose, p in fake.prompts if purpose != "teacher_turn"]
    assert grading_prompts and all("THINKINGNOTE" not in p for p in grading_prompts)
    # Delayed checks: one retention on the landed node's LO and one transfer, dated, as Check once.
    commitments = _rows(repository, "SELECT created_action, idempotency_key FROM commitments")
    assert len(commitments) == 2 and all(row[0] == "test_me_later" and row[1].startswith("lesson:") for row in commitments)
    receipt = _rows(repository, "SELECT close_reason, receipt_json FROM lesson_receipts")
    assert receipt[0][0] == "goal_reached"
    import json

    data = json.loads(receipt[0][1])
    assert {c["purpose"] for c in data["delayed_checks"]} == {"retention", "transfer"}
    assert data["weight_inputs"][0]["tap"] == 4 and data["stability_inputs"]
    assert any(key.startswith("lesson_step_retained") for key in data["forecasts"])
    close = view["feed"][-1]
    assert close["kind"] == "close" and len(close["delayed_checks"]) == 2


def test_the_minted_check_item_is_held_to_its_lesson(tmp_path):
    from learnloop.vault.lifecycle import LESSON_HOLD, practice_item_serving_block

    paths, repository, fake, view = _open(tmp_path, [plan_turn, check_turn()])
    S.turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply",
           payload={"text": "ok"}, clients=clients(fake))
    vault = load_vault(paths.root)
    minted = [item for item in vault.practice_items.values() if item.id.startswith("pi_lesson_")]
    assert len(minted) == 1
    assert practice_item_serving_block(vault, minted[0]) == LESSON_HOLD
    extra = minted[0].provenance.model_extra
    assert extra["mechanism"] == "teacher_lesson_v1" and extra["lesson_id"] == view["lesson_id"]
