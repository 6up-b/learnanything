"""What other test files use from ``tests/test_teacher_te1_review_fixes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
from typing import Any

from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault

from tests.teacher_fakes import TeacherFake, build_teacher_vault, clients
from tests.ux_phase1_support import set_config


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _turn(paths, repository, lesson_id, fake, action="reply", **payload):
    payload = payload or {"text": "go"}
    return S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action=action, payload=payload,
                       clients=clients(fake))


class MeteredTeacher(TeacherFake):
    """A teacher and grader on a metered route: each physical request goes through ``model_call`` (the
    real providers' seam, where the request gate admits it) and reports no usage (its reservation stands)."""

    provider_name = "openrouter_test"
    provider_type = "fake"  # the settings gate stays open; the spend gate still meters it (not a subscription)

    def complete(self, request: Any) -> Any:
        from learnloop.ai.execution import model_call

        with model_call(self, purpose=request.purpose, prompt=request.prompt):
            return super().complete(request)

    def run_blind_grading_proposal(self, context: Any) -> Any:
        from learnloop.ai.execution import model_call

        with model_call(self, purpose="grading", prompt=json.dumps(str(context))):
            return super().run_blind_grading_proposal(context)


def _spend(repository):
    return [json.loads(row[0]) for row in _rows(
        repository, "SELECT p.payload_json FROM lesson_turns t JOIN lesson_turn_payloads p ON p.turn_id = t.id "
                    "WHERE t.action = 'spend' ORDER BY t.seq")]


def _metered(tmp_path, turns, *, cap_factor: float):
    """Open on a metered route with a price and no cap, then cap the lesson at what it spent plus
    ``cap_factor`` times the opening request's reservation."""

    paths, repository = build_teacher_vault(tmp_path / "vault")
    set_config(paths.root, {("teacher", "metered_price_per_million"): 1.0})
    fake = MeteredTeacher([{"message": "Welcome."}])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake))
    first = _spend(repository)
    assert len(first) == 1 and first[0]["usd"] > 0
    spent = sum(row["usd"] for row in first)
    cap = spent + cap_factor * first[0]["estimated_usd"]
    set_config(paths.root, {("teacher", "max_lesson_cost_usd"): cap})
    fake.turns = list(turns)
    return paths, repository, fake, view["lesson_id"], cap
