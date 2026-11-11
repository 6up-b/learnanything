"""RO0 row 10 (spec_router_objective_v1 §4): how a check's delay was chosen, and why one was not served."""

from __future__ import annotations

import json

import pytest

from learnloop.daily_plan.engine import build_plan
from learnloop.router_objective import cold_timing as CT
from tests.data_capture_a2_measurement_helpers import _objectives, _picker, _reading_decision, _reading_env
from tests.router_g4_restraint_helpers import DECIDER_ONLY


@pytest.mark.parametrize(("reason", "expected"), [
    ("no_question", CT.STRUCTURALLY_REFUSED),
    ("no_learning_object", CT.STRUCTURALLY_REFUSED),
    ("check_replaced", CT.POLICY_REFUSED),
    ("candidates_held", CT.POLICY_REFUSED),
    ("arrange_failed", CT.OPERATIONALLY_UNAVAILABLE),
    ("plan_minutes_exhausted", CT.OPERATIONALLY_UNAVAILABLE),
    ("commitment_closed", CT.LEARNER_DECLINED),
    ("answer_not_delayed", CT.ANSWERED_UNREAD),
    ("replacement:answer_other_objective", CT.ANSWERED_UNREAD),
    ("something_new", None),
])
def test_each_reason_has_its_type_and_a_new_one_stays_untyped(reason, expected):
    assert CT.non_service_type(reason) == expected


def test_every_reason_the_measurement_writes_is_typed():
    from learnloop.daily_plan import engine as E
    from learnloop.daily_plan import measurement as M

    for reason in (M.NO_LEARNING_OBJECT, M.NO_QUESTION, M.CHECKS_OFF, M.ARRANGE_FAILED, M.COMMITMENT_CLOSED, M.CHECK_REPLACED,
                   M.ANSWER_NOT_DELAYED, M.ANSWER_OTHER_OBJECTIVE, E.CHECK_MINUTES_EXHAUSTED, E.CHECK_REFUSED_CANDIDATES,
                   E.CHECK_CANDIDATES_HELD, E.CHECK_NOT_IN_POOL, E.CHECK_NO_CANDIDATES):
        assert CT.non_service_type(reason) is not None, reason


def test_an_arranged_check_says_how_its_delay_was_chosen(tmp_path, monkeypatch):
    env = _reading_env(tmp_path, monkeypatch, choice=_picker("reading", "new:"))
    _reading_decision(env)
    arranged = [row for row in _objectives(env).values() if row["measurement"] == "arranged"]
    assert arranged
    with env.repository.connection() as connection:
        stored = connection.execute("SELECT delay_json FROM decision_objectives WHERE decision_id = ?",
                                    (arranged[0]["decision_id"],)).fetchone()[0]
    delay = json.loads(stored)
    config = env.vault.config.teacher.delayed
    assert delay["version"] == CT.DELAY_VERSION and delay["chosen_by"] in {"retrievability", "fallback"}
    assert delay["target_retrievability"] == float(config.target_retrievability)
    assert delay["max_wait_days"] == float(config.max_wait_days) and 0 <= delay["days"] <= delay["max_wait_days"]


def test_off_no_delay_and_no_type_are_written(tmp_path, monkeypatch):
    env = _reading_env(tmp_path, monkeypatch, choice=_picker("reading", "new:"),
                       toml="[router_objective]\nreceipts = false\n" + DECIDER_ONLY)
    _reading_decision(env)
    with env.repository.connection() as connection:
        assert connection.execute("SELECT COUNT(delay_json) FROM decision_objectives").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(non_service_type) FROM decision_measurement_events").fetchone()[0] == 0


def test_no_question_to_ask_is_typed_structural(tmp_path, monkeypatch):
    from learnloop.daily_plan import measurement as M

    env = _reading_env(tmp_path, monkeypatch, choice=_picker("reading", "new:"), los=("lo_with_no_item",))
    monkeypatch.setattr(M.D, "candidates", lambda *_args, **_kwargs: [])
    build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    _reading_decision(env)
    with env.repository.connection() as connection:
        rows = connection.execute(
            "SELECT reason, non_service_type FROM decision_measurement_events WHERE state = 'unavailable'").fetchall()
    assert rows and all(row[1] == CT.non_service_type(row[0]) for row in rows)
