"""Router objective RO2 §6.2, §6.4, §6.5: the versioned resolver's two bindings, the report, the audit
and the serve's added cost.

* The resolver: the first qualifying outcome (a graded first attempt on an unseen item of the LO, after
  the block) scored at its realized lag by interpolating in log time; per protocol it is censored
  ``intervening_exposure`` when the learner was exposed to the LO in between (an intervening lesson,
  which reaches the ledger as a reveal, is the case), intention to treat scores it and records the
  exposure; past 30 days ``beyond_measured_lag``; none yet is pending.
* The report compares H3 with the arms and the lower rungs on the same presentations, labelled
  exploratory, with the draw's missing pairs; the audit's dry run calls and writes nothing.

Fakes only; no model call.
"""

from __future__ import annotations

import json
import math
import sqlite3
import time
from contextlib import closing
from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad_fakes import ForecastLLM, ad_plan_vault, plan_env, rows


def _iso(moment) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _setup(tmp_path):
    from learnloop.adaptive_difficulty.history_forecast import forecast_history_presentation
    from learnloop.adaptive_difficulty.outside import Clients

    paths = ad_plan_vault(tmp_path)
    env, clock = plan_env(paths)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    _record, step = advance(env, serve=True)
    pid = step["presentation_id"]
    presentation = rows(paths.sqlite_path, "SELECT * FROM plan_presentations WHERE id = ?", (pid,))[0]
    start = clock.now()
    # The presentation's own answer, in its block.
    _attempt(paths, "att_block", presentation["practice_item_id"], _iso(start + timedelta(minutes=2)), presentation=pid)
    outcomes = forecast_history_presentation(load_vault(paths.root), Repository(paths.sqlite_path), pid,
                                             clients=Clients(llm=ForecastLLM(p_correct=0.4)),
                                             clock=FrozenClock(start + timedelta(minutes=10)))
    assert {o.status for o in outcomes} == {"ok"}
    unseen = [item for item in ("pi_m1a", "pi_m1b", "pi_m1c") if item != presentation["practice_item_id"]]
    return paths, pid, start, unseen


def _attempt(paths, attempt_id, item, created_at, *, correctness=1.0, presentation=None, hints=0):
    """A graded attempt through the real pipeline (AD reads only graded answers), at ``created_at``;
    returns its id (``attempt_id`` names it in the test only)."""

    from learnloop.clock import parse_utc
    from tests.ad23_fakes import answer

    return answer(paths, item, correct=correctness >= 0.8, presentation_id=presentation, hints=hints,
                  clock=FrozenClock(parse_utc(created_at)))


def _resolve(paths, now):
    from learnloop.adaptive_difficulty.history_resolve import resolve

    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return resolve(connection, vault, repository, now=_iso(now))


def _by(found, binding, rung="H3"):
    return [row for row in found if row["binding"] == binding and row["forecaster"] == f"llm_history_v1:{rung}"][0]


def test_log_time_interpolation():
    from learnloop.adaptive_difficulty.history_resolve import interpolate

    curve = {"1": 0.7, "7": 0.6, "30": 0.5}
    assert interpolate(curve, 0.2) == 0.7 and interpolate(curve, 7) == pytest.approx(0.6)
    assert interpolate(curve, 3) == pytest.approx(0.7 - 0.1 * math.log(3) / math.log(7))
    assert interpolate(curve, 14) == pytest.approx(0.6 - 0.1 * math.log(2) / math.log(30 / 7))
    assert interpolate(curve, 30.5) is None


def test_both_bindings_score_an_unexposed_cold_outcome(tmp_path):
    """No exposure between the block and an unseen item's first attempt: both bindings score it at its
    realized lag; the clocks are recorded (fails before RO2: no lo_cold_success receipt, no resolver)."""

    paths, _pid, start, unseen = _setup(tmp_path)
    cold = _attempt(paths, "att_cold", unseen[0], _iso(start + timedelta(days=3)))
    found = _resolve(paths, start + timedelta(days=4))
    for binding in ("per_protocol", "intention_to_treat"):
        row = _by(found, binding)
        assert row["status"] == "scored" and row["y"] == 1.0 and row["attempt_id"] == cold
        assert row["lag_days"] == pytest.approx(3 - 2 / 1440, abs=1e-4)
        assert row["p"] == pytest.approx(0.7 - 0.1 * math.log(row["lag_days"]) / math.log(7))
        assert row["delay_since_exposure_days"] == pytest.approx(row["lag_days"], abs=1e-4)
        assert row["conditional_on_observation"] is True and row["exposures"] == []


def test_an_intervening_lesson_censors_per_protocol_and_is_recorded_under_itt(tmp_path):
    """A lesson's teaching text on the LO between the block and the outcome (a reveal row, as the teacher
    records it): per protocol censored ``intervening_exposure``; intention to treat scores the same
    outcome and records the exposure."""

    paths, _pid, start, unseen = _setup(tmp_path)
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute(
            "INSERT INTO reveal_events(id, practice_item_id, learning_object_id, source_kind, amount, created_at) "
            "VALUES ('rv_lesson', ?, 'lo_m1', 'tutor_answer', 0.5, ?)",
            (unseen[1], _iso(start + timedelta(days=1))))
    _attempt(paths, "att_cold", unseen[0], _iso(start + timedelta(days=3)), correctness=0.2)
    found = _resolve(paths, start + timedelta(days=4))
    pp, itt = _by(found, "per_protocol"), _by(found, "intention_to_treat")
    assert (pp["status"], pp["reason"]) == ("censored", "intervening_exposure")
    assert itt["status"] == "scored" and itt["y"] == 0.0
    assert [(e["kind"], e["id"]) for e in itt["exposures"]] == [("reveal", "rv_lesson")]
    assert itt["delay_since_exposure_days"] == pytest.approx(2.0, abs=1e-4)


def test_beyond_the_measured_lag_and_pending(tmp_path):
    paths, _pid, start, unseen = _setup(tmp_path)
    found = _resolve(paths, start + timedelta(days=5))
    assert {(row["status"], row["reason"]) for row in found} == {("pending", "no_qualifying_outcome")}
    found = _resolve(paths, start + timedelta(days=40))
    assert {(row["status"], row["reason"]) for row in found} == {("censored", "beyond_measured_lag")}
    _attempt(paths, "att_late", unseen[0], _iso(start + timedelta(days=35)))
    found = _resolve(paths, start + timedelta(days=40))
    assert {(row["status"], row["reason"]) for row in found} == {("censored", "beyond_measured_lag")}


def test_a_seen_item_is_not_a_cold_check(tmp_path):
    paths, _pid, start, _unseen = _setup(tmp_path)
    presentation_item = rows(paths.sqlite_path, "SELECT practice_item_id FROM practice_attempts "
                                                "WHERE plan_presentation_id IS NOT NULL")[0]["practice_item_id"]
    _attempt(paths, "att_again", presentation_item, _iso(start + timedelta(days=2)))
    found = _resolve(paths, start + timedelta(days=3))
    assert {row["status"] for row in found} == {"pending"}


def test_the_report_compares_on_the_same_presentations_and_reports_missing_pairs(tmp_path):
    """``learnloop ad report``'s RO2 block: H3 against mastery_ekf, lo_general+composite and llm_v3 and
    the lower rung on the same presentations, each with its interval, exploratory, and the draw's pairs."""

    from learnloop.adaptive_difficulty.scoring import history_report

    paths, _pid, start, unseen = _setup(tmp_path)
    _attempt(paths, "att_cold", unseen[0], _iso(start + timedelta(days=3)))
    vault = load_vault(paths.root)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        report = history_report(connection, vault, Repository(paths.sqlite_path), now=_iso(start + timedelta(days=4)))
    assert report["exploratory"] is True and report["subject"] == "llm_history_v1:H3"
    assert set(report["comparisons"]["first_attempt"]) == {"mastery_ekf", "lo_general+composite", "llm_v3:llm"}
    assert report["draws"] == {"presentations": 1, "complete_pairs": 1, "missing": {}, "skipped_by_rung": {}}
    assert report["delayed_cold"]["statuses"]["per_protocol"] == {"scored": 2}
    assert report["calibration_slopes"]["prior"]["scale"] == 1.0
    assert any("conditional on observation" in note for note in report["notes"])


def test_calibration_slopes_shrink_a_new_version_to_the_population():
    from learnloop.adaptive_difficulty.scoring import calibration_slopes

    old = [(0.9, 1.0)] * 30 + [(0.9, 0.0)] * 30 + [(0.1, 1.0)] * 30 + [(0.1, 0.0)] * 30
    fitted = calibration_slopes({"m|v1": old, "m|v2": []})
    assert fitted["versions"]["m|v1"]["slope"] < 0.5
    # The new version starts from the population, not from the old version's slope or from 1.
    assert fitted["versions"]["m|v2"]["slope"] == pytest.approx(fitted["population"]["slope"])
    loose = calibration_slopes({"m|v1": old[:4]}, scale=4.0)
    tight = calibration_slopes({"m|v1": old[:4]}, scale=0.25)
    assert abs(tight["population"]["slope"] - 1.0) < abs(loose["population"]["slope"] - 1.0)


def test_the_audit_dry_run_calls_and_writes_nothing(tmp_path):
    from learnloop.adaptive_difficulty.history_audit import plan_audit, run_audit
    from learnloop.cli import app
    from typer.testing import CliRunner

    paths = ad_plan_vault(tmp_path)
    env, clock = plan_env(paths)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    advance(env, serve=True)
    vault = load_vault(paths.root)
    before = rows(paths.sqlite_path, "SELECT COUNT(*) AS n FROM forecast_receipts")[0]["n"]
    plan = plan_audit(vault, Repository(paths.sqlite_path), mode="permuted")
    assert plan["status"] == "dry_run" and plan["model_calls"] == 0 and plan["writes"] == 0
    sweep = run_audit(vault, Repository(paths.sqlite_path), mode="prior-sweep")
    assert sweep["model_calls"] == 0 and set(sweep["sweep"]) == {"0.25", "0.5", "1.0", "2.0", "4.0"}
    result = CliRunner().invoke(app, ["ad", "forecast-audit", "--vault", str(paths.root), "--mode", "permuted",
                                      "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["model_calls"] == 0
    assert rows(paths.sqlite_path, "SELECT COUNT(*) AS n FROM forecast_receipts")[0]["n"] == before


def test_the_permuted_run_sends_another_presentations_history(tmp_path):
    """The paid audit (fakes here): each H3 card is resent with the history of a presentation of a similar
    level and another item, served no later; its receipts are ``llm_history_v1:H3_permuted`` on the same
    presentation. The dry run plans exactly those calls."""

    from learnloop.adaptive_difficulty.history_audit import plan_audit, run_audit
    from learnloop.adaptive_difficulty.outside import Clients
    from learnloop.adaptive_difficulty.serve import record_plan_serve

    paths = ad_plan_vault(tmp_path)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    for index, (item, served) in enumerate((("pi_m1a", "2026-10-12T09:00:00Z"), ("pi_m1b", "2026-10-12T10:00:00Z"))):
        with sqlite3.connect(paths.sqlite_path) as connection:
            connection.execute("INSERT INTO attention_blocks(id, action, budget_minutes, content_hash, created_at) "
                               "VALUES (?, 'practice', 10, 'hash', ?)", (f"blk_{index}", served))
            connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at) "
                               "VALUES (?, ?, ?, 'chooser', ?)", (f"pp_{index}", f"blk_{index}", item, served))
        with repository.atomic():
            assert record_plan_serve(vault, repository, presentation_id=f"pp_{index}", practice_item_id=item,
                                     served_at=served).history_draw
    plan = plan_audit(vault, repository, mode="permuted")
    assert [(pair["plan_presentation_id"], pair["donor"]) for pair in plan["pairs"]] == [("pp_1", "pp_0")]
    llm = ForecastLLM(p_correct=0.3)
    result = run_audit(vault, repository, mode="permuted", clients=Clients(llm=llm),
                       clock=FrozenClock(__import__("datetime").datetime(2026, 10, 12, 11, tzinfo=__import__("datetime").UTC)))
    assert result["calls"] == plan["calls"] == len(llm.prompts) == 1
    assert '"permuted_from"' in llm.prompts[0]
    permuted = rows(paths.sqlite_path, "SELECT * FROM forecast_receipts WHERE forecaster = 'llm_history_v1:H3_permuted'")
    assert len(permuted) == 4 and {row["plan_presentation_id"] for row in permuted} == {"pp_1"}


def test_the_serve_transactions_added_cost_is_measured(tmp_path, monkeypatch, record_property):
    """§6.5: the serve transaction's added cost, measured on a synthetic vault (300 earlier attempts with
    answers on the LO, 40 help rows and 40 questions): the time inside ``freeze_history_inputs`` (the
    draw, the bounded reads, both cards and their writes) against the whole serve. The record carries
    the numbers."""

    from learnloop.adaptive_difficulty import serve as ad_serve

    paths = ad_plan_vault(tmp_path)
    with sqlite3.connect(paths.sqlite_path) as connection:
        for index in range(300):
            connection.execute(
                "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, "
                "attempt_type, correctness, learner_answer_md, created_at) VALUES (?, 'pi_m1b', 'lo_m1', "
                "'short_answer', 'independent_attempt', 1.0, ?, ?)",
                (f"att_{index:03d}", "answer " * 40, f"2026-09-{(index % 28) + 1:02d}T09:{index % 60:02d}:00Z"))
        for index in range(40):
            connection.execute(
                "INSERT INTO help_assists(id, surface, assist_kind, practice_item_id, attempt_id, body_md, chooser, "
                "shown, requested_at) VALUES (?, 'practice', 'hint', 'pi_m1b', ?, 'a hint', 'none', 1, ?)",
                (f"ha_{index}", f"att_{index:03d}", "2026-09-20T09:00:00Z"))
            connection.execute(
                "INSERT INTO question_events(id, context, practice_item_id, question_md, created_at) "
                "VALUES (?, 'practice', 'pi_m1b', 'why?', '2026-09-20T09:00:00Z')", (f"qe_{index}",))
    spent: list[float] = []
    original = ad_serve.freeze_history_inputs

    def timed(*args, **kwargs):
        began = time.perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            spent.append(time.perf_counter() - began)

    monkeypatch.setattr(ad_serve, "freeze_history_inputs", timed)
    env, _clock = plan_env(paths)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    began = time.perf_counter()
    advance(env, serve=True)
    whole = time.perf_counter() - began
    assert len(spent) == 1 and rows(paths.sqlite_path, "SELECT COUNT(*) AS n FROM ad_history_forecast_draws")[0]["n"] == 1
    record_property("ro2_freeze_seconds", round(spent[0], 4))
    record_property("serve_seconds", round(whole, 4))
    print(f"RO2 serve cost: freeze {spent[0] * 1000:.1f} ms of a {whole * 1000:.1f} ms serve")
