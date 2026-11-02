"""Follow-ups batch 6 (G2): ``learnloop router report``, teacher TE1b's split by randomized arm.

The lesson-suggestion decisions by randomized arm (card shown or not): offered,
accepted, opened, completed, and R_cold on the drawn topic, weighted by the logged arm propensity,
read-only from the ledgers.

Every model is a fake; no network.
"""

from __future__ import annotations

import hashlib
import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.router import lesson_suggestions as LS
from learnloop.router import suggestion_report as SR
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import TeacherFake, clients, plan_turn
from tests.test_teacher_te1b_landing_r2 import _start, _today
from tests.test_teacher_te1b_suggestions import _clock, _vault, no_network, shown  # noqa: F401


# --- (2) the ITT split: the pure core ------------------------------------------------------------------


def _decision(decision_id: str, *, shown: bool, arm_propensity, lo: str = "lo_det") -> dict:
    return {"id": decision_id, "detail": {"shown": shown, "arm_propensity": arm_propensity,
                                          "drawn_learning_object_ids": [lo]}}


def test_the_split_weights_each_arm_by_its_logged_propensity():
    decisions = [_decision("d1", shown=True, arm_propensity=0.8), _decision("d2", shown=True, arm_propensity=0.5),
                 _decision("d3", shown=True, arm_propensity=0.9), _decision("d4", shown=False, arm_propensity=0.2),
                 _decision("d5", shown=False, arm_propensity=0.1), _decision("d6", shown=True, arm_propensity=None)]
    responses = [{"decision_id": "d1", "response": "accepted", "lesson_id": "les_1"},
                 {"decision_id": "d2", "response": "chose_alternative", "lesson_id": "les_2"},
                 {"decision_id": "d3", "response": "declined", "lesson_id": None}]
    releases = [{"decision_id": "d2", "response": "released"}]
    lessons = {"les_1": {"origin_ref": "d1", "close_reason": "goal_reached"},
               "les_2": {"origin_ref": "elsewhere", "close_reason": None}}  # not this decision's lesson
    outcomes = {"d1": {"s_status": "final", "s_value": 1.0}, "d3": {"s_status": "final", "s_value": 0.0},
                "d4": {"s_status": "final", "s_value": 0.0}, "d5": {"s_status": "final", "s_value": 1.0},
                "d2": {"s_status": "pending", "s_value": None}}
    split = SR.itt_split(decisions, responses, releases, lessons, outcomes)
    card, none = split["arms"]["card"], split["arms"]["no_card"]
    assert split["decisions"] == 6 and card["decisions"] == 4 and none["decisions"] == 2
    assert card["funnel"] == {"offered": 4, "accepted": 2, "opened": 1, "completed": 1}
    assert card["responses"] == {"accepted": 1, "chose_alternative": 1, "declined": 1, "ignored": 0,
                                 "unanswered": 1, "released": 1, "expired": 0}
    assert card["unweighted"] == 1 and none["unweighted"] == 0
    w1, w2, w3 = 1 / 0.8, 1 / 0.5, 1 / 0.9
    assert card["weighted_rates"]["taken"] == round((w1 + w2) / (w1 + w2 + w3), 6)
    assert card["weighted_rates"]["opened"] == round(w1 / (w1 + w2 + w3), 6)
    assert card["outcome"] == {"observed": 2, "pending": 2, "observed_share": 0.5,
                               "weighted_mean_r_cold": round(w1 / (w1 + w3), 6)}
    w4, w5 = 1 / 0.2, 1 / 0.1
    assert none["outcome"]["weighted_mean_r_cold"] == round(w5 / (w4 + w5), 6)
    assert none["funnel"] == {"offered": 0, "accepted": 0, "opened": 0, "completed": 0}
    assert split["observed_difference_r_cold"] == round(round(w1 / (w1 + w3), 6) - round(w5 / (w4 + w5), 6), 6)
    text = "\n".join(SR.lines(split))
    assert "card shown: 4" in text and "no card: 2" in text and "among observed outcomes only" in text
    assert "(1 without a logged arm propensity, unweighted)" in text


def test_an_empty_ledger_reports_zeros_and_no_difference():
    split = SR.itt_split([], [], [], {}, {})
    assert split["decisions"] == 0 and split["observed_difference_r_cold"] is None
    assert split["arms"]["card"]["weighted_rates"] == {"taken": None, "opened": None, "completed": None}
    assert SR.lines(split)[-1].startswith(
        "Difference in mean R_cold among observed outcomes only (card - no card): - (an arm has no observed")


# --- (2) the ITT split: `learnloop router report` on logged decisions ------------------------------------


def _digest(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_router_report_prints_the_split_from_the_ledgers_read_only(tmp_path, shown, no_network, monkeypatch):
    paths, repository = _vault(tmp_path)
    # Day 0: a card, a Start, the lesson opens and reaches its goal.
    card, lesson = _start(paths, repository)
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object", clients=clients(TeacherFake([plan_turn])),
                  origin="router", origin_ref=card["decision_id"], lesson_id=lesson["lesson_id"], clock=_clock(hours=2))
    with repository.connection() as connection:
        connection.execute("UPDATE lessons SET closed_at = ?, close_reason = 'goal_reached' WHERE id = ?",
                           ("2026-11-02T12:00:00Z", lesson["lesson_id"]))
        connection.commit()
    # Day 1: drawn, no card (the show coin above P(accept)).
    monkeypatch.setattr(LS, "_uniforms", lambda seed: (0.5, 0.0, 0.999999))
    assert _today(load_vault(paths.root), repository, _clock(days=1)) is None
    # Day 2: a card, "Not now".
    monkeypatch.setattr(LS, "_uniforms", lambda seed: (0.5, 0.0, 0.0))
    declined = _today(load_vault(paths.root), repository, _clock(days=2))
    SG.respond(load_vault(paths.root), repository, decision_id=declined["decision_id"], response="declined",
               clock=_clock(days=2, hours=1))
    database = repository.sqlite_path
    before = _digest(database)
    result = CliRunner().invoke(app, ["router", "report", "--vault", str(paths.root), "--json"])
    assert result.exit_code == 0, result.output
    split = json.loads(result.output)["lesson_suggestions"]
    assert split["decisions"] == 3
    assert split["arms"]["card"]["funnel"] == {"offered": 2, "accepted": 1, "opened": 1, "completed": 1}
    assert split["arms"]["card"]["responses"]["declined"] == 1
    assert split["arms"]["no_card"]["decisions"] == 1
    assert all(split["arms"][arm]["mean_arm_propensity"] for arm in SR.ARMS)
    text = CliRunner().invoke(app, ["router", "report", "--vault", str(paths.root)])
    assert text.exit_code == 0 and text.output.startswith("Lesson suggestions (teacher TE1b): 3 decisions")
    assert _digest(database) == before  # read-only


def test_router_report_on_a_database_before_lesson_suggestions_is_refused(tmp_path, monkeypatch):
    from learnloop.db.stores import router_suggestions

    paths, _repository = _vault(tmp_path)
    monkeypatch.setattr(router_suggestions, "tables_present", lambda connection: False)
    result = CliRunner().invoke(app, ["router", "report", "--vault", str(paths.root), "--json"])
    assert result.exit_code == 1 and "migration 236" in json.loads(result.output)["reason"]
