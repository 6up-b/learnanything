"""Router objective RO2: ``llm_history_v1`` (spec_router_objective_v1 §6.1-6.3, §6.5).

Each test failed before RO2 for the reason its docstring names (no such forecaster, kind, draw,
card or resolver). Fakes only: no network, no paid call.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock, parse_utc
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad_fakes import ITEMS, LO, ForecastLLM, ad_plan_vault, plan_env, rows

HISTORY_OFF = '[adaptive_difficulty]\noutside_forecasters = ["llm_v1:item", "llm_v3:llm", "llm_v3:decider"]\n'


def _stamp(clock, **delta) -> str:
    return (clock.now() + timedelta(**delta)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _served(tmp_path, *, config: str = "", before=None):
    paths = ad_plan_vault(tmp_path, config=config)
    env, clock = plan_env(paths)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    if before is not None:
        before(paths, clock)
    _record, step = advance(env, serve=True)
    assert step["kind"] == "item" and step["presentation_id"]
    return paths, env, clock, step


def _attempt(paths, attempt_id, item, created_at, *, correctness=1.0, received_at=None, attempt_type="independent_attempt",
             answer="x = 2", hints=0, lo=LO):
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "correctness, hints_used, learner_answer_md, created_at, received_at) VALUES (?, ?, ?, 'short_answer', ?, "
            "?, ?, ?, ?, ?)", (attempt_id, item, lo, attempt_type, correctness, hints, answer, created_at, received_at))


def _forecast(paths, presentation_id, clock, llm=None, *, minutes=10):
    from learnloop.adaptive_difficulty.history_forecast import forecast_history_presentation
    from learnloop.adaptive_difficulty.outside import Clients

    vault = load_vault(paths.root)
    return forecast_history_presentation(vault, Repository(paths.sqlite_path), presentation_id,
                                         clients=Clients(llm=llm or ForecastLLM(p_correct=0.4)),
                                         clock=FrozenClock(clock.now() + timedelta(minutes=minutes)))


def _frozen(paths, presentation_id):
    found = rows(paths.sqlite_path, "SELECT * FROM item_forecast_payloads WHERE owner_key LIKE ?",
                 (f"ad_llm_history_state:plan_presentation:{presentation_id}:%",))
    return {row["owner_key"].rsplit(":", 1)[1]: json.loads(row["content_json"]) for row in found}


def _history_receipts(paths):
    return rows(paths.sqlite_path, "SELECT * FROM forecast_receipts WHERE forecaster LIKE 'llm_history_v1:%' "
                                   "ORDER BY receipt_key")


def test_the_serve_freezes_the_draw_and_two_rungs(tmp_path):
    """The serve transaction writes the seeded draw (H3 plus one lower rung, its propensity 1/3) and the
    two frozen cards (fails before RO2: no draw table, no card)."""

    from learnloop.adaptive_difficulty.history_forecast import draw

    paths, _env, _clock, step = _served(tmp_path)
    pid = step["presentation_id"]
    draws = rows(paths.sqlite_path, "SELECT * FROM ad_history_forecast_draws")
    assert len(draws) == 1 and draws[0]["plan_presentation_id"] == pid
    expected = draw(pid)
    assert (draws[0]["anchor_rung"], draws[0]["drawn_rung"]) == ("H3", expected["drawn_rung"])
    assert draws[0]["propensity"] == pytest.approx(1 / 3) and draws[0]["seed"] == expected["seed"]
    assert json.loads(draws[0]["propensities_json"]) == pytest.approx({"H0": 1 / 3, "H1": 1 / 3, "H2": 1 / 3})
    frozen = _frozen(paths, pid)
    assert set(frozen) == {"H3", expected["drawn_rung"]}
    for rung, content in frozen.items():
        assert content["state"]["card"] == "ad-forecast-state-v3" and content["state"]["rung"] == rung
        assert content["inputs_as_of"] == draws[0]["served_at"]
        assert isinstance(content["protection_epoch"], str)
    # H3's card holds every rung's sections.
    assert {"recent_attempts", "whole_answers", "help", "reading", "other_topics", "goals"} <= set(
        frozen["H3"]["state"]["history"])
    # The draw is uniform over the three lower rungs across presentations.
    drawn = {draw(f"pp_{index}")["drawn_rung"] for index in range(60)}
    assert drawn == {"H0", "H1", "H2"}


def test_forecaster_off_gives_no_row_and_no_call(tmp_path):
    """With llm_history_v1 off: no draw, no frozen card, no receipt and no model call (§6.5)."""

    paths, _env, clock, step = _served(tmp_path, config=HISTORY_OFF)
    assert rows(paths.sqlite_path, "SELECT * FROM ad_history_forecast_draws") == []
    assert _frozen(paths, step["presentation_id"]) == {}
    llm = ForecastLLM()
    assert _forecast(paths, step["presentation_id"], clock, llm) == []
    assert llm.prompts == [] and _history_receipts(paths) == []


def test_the_background_job_sends_each_rung_as_frozen_and_writes_receipts(tmp_path):
    """Each frozen rung is sent exactly as frozen; p_now is an item_unassisted_success receipt bound to the
    presentation, p_cold_L three lo_cold_success receipts with the whole curve; accepted verdicts are
    judgments; the rationale is cut to three sentences and kept for the trace (fails before RO2)."""

    from learnloop.adaptive_difficulty.history_forecast import prompt_for

    paths, _env, clock, step = _served(tmp_path, before=lambda p, c: _attempt(p, "att_old", "pi_m1c",
                                                                              _stamp(c, days=-2)))
    pid = step["presentation_id"]
    frozen = _frozen(paths, pid)
    llm = ForecastLLM(p_correct=0.42)
    outcomes = _forecast(paths, pid, clock, llm)
    assert sorted((o.forecaster, o.status) for o in outcomes) == sorted(
        (f"llm_history_v1:{rung}", "ok") for rung in frozen)
    assert sorted(llm.prompts) == sorted(prompt_for(content["state"]) for content in frozen.values())
    receipts = _history_receipts(paths)
    assert len(receipts) == 8
    served_at = rows(paths.sqlite_path, "SELECT served_at FROM plan_presentations WHERE id = ?", (pid,))[0]["served_at"]
    for receipt in receipts:
        assert receipt["inputs_as_of"] == served_at and receipt["status"] == "ok"
        assert 0.0 < receipt["p"] < 1.0
        forecast = json.loads(receipt["forecast_json"])
        assert forecast["rationale_unvalidated"]["text"].count(".") <= 3
        assert forecast["rationale_unvalidated"]["truncated"] is True
        if receipt["kind"] == "item_unassisted_success":
            assert receipt["binding_kind"] == "plan_presentation" and receipt["p"] == pytest.approx(0.42)
        else:
            assert receipt["kind"] == "lo_cold_success" and receipt["binding_kind"] == "lo_cold_after_block"
            assert forecast["curve"] == {"1": 0.7, "7": 0.6, "30": 0.5}
    judgments = rows(paths.sqlite_path, "SELECT * FROM judgment_ledger WHERE right_id LIKE 'llm_history_v1:%'")
    assert len(judgments) == 8
    # Each rung is forecast once.
    assert _forecast(paths, pid, clock, ForecastLLM(), minutes=20) == []


def test_a_skipped_forecast_is_censored_with_its_reason(tmp_path):
    """Under the spend cap, a plan usage pause or an invalid answer, each rung writes censored receipts
    (no p, no binding, censor_reason skipped:<reason>), never an imputed number (§6.1)."""

    from learnloop.ai.chatgpt_plan.session import ChatGPTPlanUsageExhausted
    from learnloop.ai.spend import SpendLimitExceeded

    paths, _env, clock, step = _served(tmp_path)
    pid = step["presentation_id"]
    outcomes = _forecast(paths, pid, clock, ForecastLLM(fail=ChatGPTPlanUsageExhausted("ChatGPT plan usage exhausted")))
    assert {o.status for o in outcomes} == {"failed"}
    receipts = _history_receipts(paths)
    assert len(receipts) == 8
    assert {r["censor_reason"] for r in receipts} == {"skipped:plan_paused"}
    assert all(r["p"] is None and r["binding_kind"] == "none" for r in receipts)
    # A later run retries the censored rungs (the canonical keys stay open).
    paths2, _env2, clock2, step2 = _served(tmp_path / "b")
    outcomes = _forecast(paths2, step2["presentation_id"], clock2, ForecastLLM(fail=SpendLimitExceeded("cap")))
    assert {o.status for o in outcomes} == {"refused_spend"}
    assert {r["censor_reason"] for r in _history_receipts(paths2)} == {"skipped:spend_cap"}
    outcomes = _forecast(paths2, step2["presentation_id"], clock2, ForecastLLM(p_correct=0.5), minutes=30)
    assert {o.status for o in outcomes} == {"ok"}


def test_invalid_probabilities_are_censored(tmp_path):
    paths, _env, clock, step = _served(tmp_path)
    outcomes = _forecast(paths, step["presentation_id"], clock, ForecastLLM(p_correct=1.0))
    assert {o.status for o in outcomes} == {"failed"}
    assert {r["censor_reason"] for r in _history_receipts(paths)} == {"skipped:invalid_output"}
