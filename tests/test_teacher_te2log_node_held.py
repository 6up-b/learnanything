"""Teacher TE2-log, part 4: ``p_held`` on plan nodes and the ``lesson_node_held`` forecast (spec_teacher_v1 §9, §11.3).

A plan node's ``p_held`` (the teacher's forecast that the learner would answer a cold question on it right now) is
one ``lesson_node_held`` forecast receipt on the node's LO, bound to the first qualifying cold outcome on the LO (as
``lesson_step_retained``), and resolved by the forecast report. Off, the turn has no ``p_held`` and none is written.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from learnloop.clock import FrozenClock
from learnloop.scheduling.forecast_receipts import FORECAST_KINDS, LESSON_COLD_OUTCOME, LESSON_NODE_HELD
from learnloop.teacher import episodes as E
from learnloop.teacher import service as S
from learnloop.teacher.contracts import TeacherTurnV1
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import TeacherFake, build_teacher_vault, clients, plan_turn
from tests.teacher_te2log_node_held_helpers import held_plan

T0 = datetime(2026, 11, 5, 15, 0, tzinfo=UTC)


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _open(tmp_path, turns, *, config=None):
    from tests.ux_phase1_support import set_config

    paths, repository = build_teacher_vault(tmp_path / "vault")
    if config:
        set_config(paths.root, config)
    fake = TeacherFake(turns)
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake), clock=FrozenClock(T0))
    return paths, repository, fake, view


def test_each_p_held_is_a_lesson_node_held_forecast_on_its_lo(tmp_path):
    assert LESSON_NODE_HELD in FORECAST_KINDS
    paths, repository, _fake, view = _open(tmp_path, [held_plan])
    rows = _rows(repository, "SELECT receipt_key, forecaster, forecaster_version, scope, binding_kind, event, p, "
                             "learning_object_id, decision_ref, inputs_json, versions_json FROM forecast_receipts "
                             "WHERE kind = ? ORDER BY receipt_key", (LESSON_NODE_HELD,))
    family = f"{S.DOCTRINE_VERSION}+{E.EPISODES_VERSION}:fake-teacher-model"
    assert [(r[0].rsplit(":", 1)[-1], r[6], r[7]) for r in rows] == [("n0", 0.8, "lo_det"), ("n1", 0.35, "lo_eigen")]
    for row in rows:
        assert row[1:6] == ("teacher", family, "lesson_node", LESSON_COLD_OUTCOME, "cold_success")
        assert row[8] == view["lesson_id"]
        inputs = json.loads(row[9])
        assert inputs["plan_version"] == 1 and inputs["lesson_id"] == view["lesson_id"] and inputs["family"] == family
        assert json.loads(row[10])["episodes"] == E.EPISODES_VERSION
    # The node with no topic writes none; the plan stored keeps every p_held as the teacher wrote it.
    outline = json.loads(_rows(repository, "SELECT outline_json FROM lesson_plans")[0][0])
    assert [node.get("p_held") for node in outline] == [0.8, 0.35, None, 0.5]
    # A revised plan forecasts again under its own version.
    S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply", payload={"text": "?"},
                clients=clients(TeacherFake([held_plan])), clock=FrozenClock(T0 + timedelta(minutes=1)))
    keys = [row[0] for row in _rows(repository, "SELECT receipt_key FROM forecast_receipts WHERE kind = ?",
                                    (LESSON_NODE_HELD,))]
    assert len(keys) == 4 and len({k.split(":")[2] for k in keys}) == 2


def test_the_forecast_report_resolves_it_on_the_first_cold_outcome(tmp_path):
    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.evsi_calibration.forecast_report import resolved_receipts

    paths, repository, _fake, view = _open(tmp_path, [held_plan])
    pending = {r["receipt_key"]: s["state"] for r, s in resolved_receipts(load_vault(paths.root))
               if r["kind"] == LESSON_NODE_HELD}
    assert set(pending.values()) == {"pending"}
    complete_self_graded_attempt(
        load_vault(paths.root), repository,
        AttemptDraft(practice_item_id="pi_det_1", learner_answer_md="minus two", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4), clock=FrozenClock(T0 + timedelta(days=2)))
    resolved = {r["receipt_key"].rsplit(":", 1)[-1]: s for r, s in resolved_receipts(load_vault(paths.root))
                if r["kind"] == LESSON_NODE_HELD}
    assert resolved["n0"]["state"] == "resolved" and resolved["n0"]["emission"] == "success"
    assert resolved["n1"]["state"] == "pending"  # nothing cold on lo_eigen yet


def test_switch_off_has_no_p_held_and_writes_no_forecast(tmp_path):
    assert "p_held" not in json.dumps(TeacherTurnV1.model_json_schema())
    paths, repository, fake, _view = _open(tmp_path, [plan_turn], config={("teacher", "episode_log"): False})
    assert fake.result_models == [TeacherTurnV1]
    assert _rows(repository, "SELECT COUNT(*) FROM forecast_receipts WHERE kind = ?", (LESSON_NODE_HELD,)) == [(0,)]
    outline = json.loads(_rows(repository, "SELECT outline_json FROM lesson_plans")[0][0])
    assert all("p_held" not in node for node in outline)


def test_a_refused_forecast_rolls_back_alone_and_the_plan_stands(tmp_path, monkeypatch):
    from learnloop.db.stores import forecast_receipts as receipt_store

    def refuse(*args, **kwargs):
        raise RuntimeError("refused")

    monkeypatch.setattr(receipt_store, "insert_receipt", refuse)
    _paths, repository, _fake, view = _open(tmp_path, [held_plan])
    assert view["plan"] and len(_rows(repository, "SELECT 1 FROM lesson_plans")) == 1
    assert _rows(repository, "SELECT COUNT(*) FROM forecast_receipts") == [(0,)]


def test_one_refused_node_forecast_leaves_its_siblings(tmp_path, monkeypatch):
    """Codex review F2: three nodes with ``p_held``, only the middle insert refused: both siblings are written."""

    from learnloop.db.stores import forecast_receipts as receipt_store

    original = receipt_store.insert_receipt

    def refuse_middle(connection, **kwargs):
        if kwargs.get("kind") == LESSON_NODE_HELD and kwargs["receipt_key"].endswith(":n1"):
            original(connection, **kwargs)  # its row is written, then refused: the savepoint takes it back
            raise RuntimeError("refused")
        return original(connection, **kwargs)

    def three_held(context):
        turn = held_plan(context)
        turn["requests"][0]["plan"][-1]["lo_id"] = "lo_eigen"
        return turn

    monkeypatch.setattr(receipt_store, "insert_receipt", refuse_middle)
    _paths, repository, _fake, view = _open(tmp_path, [three_held])
    assert view["plan"] and len(_rows(repository, "SELECT 1 FROM lesson_plans")) == 1
    keys = [row[0].rsplit(":", 1)[-1] for row in _rows(
        repository, "SELECT receipt_key FROM forecast_receipts WHERE kind = ? ORDER BY receipt_key",
        (LESSON_NODE_HELD,))]
    assert keys == ["n0", "nx"]
