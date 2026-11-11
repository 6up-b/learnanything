"""What other test files use from ``tests/test_router_card.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
from learnloop.daily_plan.engine import build_plan
from learnloop.daily_plan.policy import policy_for
from learnloop.router.card import CardInputs

from tests.daily_plan_fakes import MovableClock, iso, make_env, scheduled, seed_due
from tests.helpers import NOW_ISO, create_daily_plan_vault, write_yaml


PAST = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
LAST = datetime(2026, 9, 20, 9, 0, tzinfo=UTC)
A = ROUTER_STAGED_FRAME_ALGORITHM_VERSION
OWN_ANSWER = "MY_OWN_WORDS_1203"


def _item(paths, item_id: str, lo_id: str, *, prompt: str, expected: str, source_refs: list | None = None) -> None:
    write_yaml(
        paths.practice_item_path("linear-algebra", item_id),
        {
            "schema_version": 1, "id": item_id, "learning_object_id": lo_id, "subjects": None,
            "practice_mode": "short_answer", "attempt_types_allowed": ["independent_attempt", "exam_attempt"],
            "evidence_facets": ["recall"], "evidence_weights": {"recall": 1.0},
            "prompt": prompt, "expected_answer": expected, "difficulty": 0.5, "tags": [], "expected_minutes": 2.0,
            "grading_rubric": {"max_points": 4, "criteria": [{"id": "correctness", "points": 4, "description": "Right."}]},
            "provenance": {"origin": "human", "source_refs": source_refs or []},
            "created_at": NOW_ISO, "updated_at": NOW_ISO,
        },
    )


def _attempt(env, attempt_id: str, item_id: str, lo_id: str, at: str, *, answer: str, correctness: float,
             attempt_type: str = "independent_attempt") -> None:
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, correctness, hints_used, created_at, session_id, evidence_origin) "
            "VALUES (?, ?, ?, 'short_answer', ?, ?, ?, 0, ?, 'old', 'human')",
            (attempt_id, item_id, lo_id, attempt_type, answer, correctness, at),
        )
        connection.commit()


def _stored_card(env) -> tuple[dict, dict]:
    with env.repository.connection() as connection:
        row = connection.execute(
            "SELECT * FROM router_decisions WHERE decision_kind = 'plan_block' ORDER BY created_at, id LIMIT 1"
        ).fetchone()
        payload = connection.execute(
            "SELECT * FROM router_decision_payloads WHERE decision_id = ? AND kind = 'card'", (row["id"],)
        ).fetchone()
    return dict(row), dict(payload)


def _inputs(work: int, *, text: str = "x" * 300) -> CardInputs:
    entries = [
        {"attempt_id": f"a{index}", "at": f"2026-10-{(index % 28) + 1:02d}T09:00:00Z", "learning_object_id": "lo",
         "topic": "Bases", "kind": "short_answer", "result": "correct" if index % 2 else "incorrect",
         "hints_used": 0, "key_status": None, "stem": text, "answer": text}
        for index in range(work)
    ]
    return CardInputs(
        decision={"surface": "daily_plan", "decided_at": "2026-10-12T09:00:00Z"},
        session={"plan_kind": "normal", "minutes_left": 10, "minutes_budget": 25},
        candidates=[{"ref": "maintain:1", "kind": "maintain", "est_minutes": 4, "topics": ["Bases"],
                     "reversible": True, "reason_code": "review"}],
        learning_objects={"lo": {"title": "Bases", "status": "demonstrated", "evidence": {"graded": 3}}},
        interaction_7d={"attempts": 3},
        unknowns=["never tested: Spans"],
        recent_work=entries,
    )


OLD_STEM = "OLD_STEM_THE_LEARNER_SAW_3301"
NEW_STEM = "NEW_STEM_NEVER_ATTEMPTED_8812"


def _card_world(tmp_path, monkeypatch):
    """Two candidate topics: lo_m1 (pi_a, answered then edited) and lo_m2 (pi_b)."""

    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_m1": [], "lo_m2": []}, version=A)
    _item(paths, "pi_a", "lo_m1", prompt=NEW_STEM, expected="kept")
    _item(paths, "pi_b", "lo_m2", prompt="Name a basis of R^2.", expected="e1, e2")
    clock = MovableClock()
    env = make_env(paths.root, [scheduled("pi_a", "lo_m1", forgetting_risk=0.6),
                                scheduled("pi_b", "lo_m2", forgetting_risk=0.6)], clock=clock, session_id="s1")
    for item in ("pi_a", "pi_b"):
        seed_due(env.repository, item, due=PAST, last=LAST)
    from learnloop.content.sources import exam_material as EM

    monkeypatch.setattr(EM, "exam_material",
                        lambda _vault, _repo: EM.ExamMaterial(material=EM.Material(), held_out=EM.Material()))
    env.policy = policy_for(env.vault, env.repository, session_id="s1", clock=clock)
    return env


def _card(env) -> dict:
    """The card stored with the plan's first block decision."""

    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    _row, payload = _stored_card(env)
    return {"json": json.loads(payload["content_json"]), "text": payload["content_text"]}


def _hypothesis(env, hypothesis_id: str, *, status: str, statement: str, evidence: dict) -> None:
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO causal_hypotheses(id, episode_key, version, attempt_id, learning_object_id, cause_scope, "
            "statement, statement_normalized, status, evidence_json, created_at) "
            "VALUES (?, ?, 1, 'att_a', 'lo_m1', 'learner_state', ?, ?, ?, ?, ?)",
            (hypothesis_id, f"ep_{hypothesis_id}", statement, statement.lower(), status, json.dumps(evidence),
             iso(LAST)),
        )
        connection.commit()
