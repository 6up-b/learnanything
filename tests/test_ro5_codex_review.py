"""Router objective RO5, Codex review (job 20261105-084800-81ZdBg): each finding reproduced by a test that fails on
the pre-fix source. Fakes and synthetic data only; no model is asked.

* F1: a check whose grade is held for review, assesses nothing in its current epoch, or has no correctness is no
  observation (never a zero), and does not count as completed.
* F2: the check's administration does not depend on the action: a drawn item the policy also chose is reclassified
  as the check, never dropped.
* F3: the return model is identified by the coin alone: a busy-day confounder that shortens sessions and lengthens
  gaps leaves the slope at zero; a planted causal slope is recovered.
* F4: the comparison score's cost is the objective's own: minutes carried from before the decision and Reader time.
* F5: with the check arm off the weight is RO4's even after scores accumulated.
* F6: a dated use is scored on the goal's own date, never on truncated elapsed days.
* F7: the goal-date read has a frozen forecast for a goal past the evaluation window.
* Closed scores stay closed: the completion rate a score reads is the one at its window's close.
"""

from __future__ import annotations

import json
import random
import sqlite3
from types import SimpleNamespace

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.held_grades import held_for_review_attempts
from learnloop.router_objective import assignments as A
from learnloop.router_objective import checks as C
from learnloop.router_objective import goal_read as G
from learnloop.router_objective import scores as S
from learnloop.router_objective import stop_coin as SC
from learnloop.router_objective import value as V
from learnloop.router_objective import weight as W

from tests.router_mixture_helpers import mixture_env, run
from tests.router_model_fakes import fake_runtime
from tests.ro5_checks_helpers import _env, _row, _trace, grade_checks
from tests.ro5_stop_coin_helpers import ARMS_OFF


# -- F1 ------------------------------------------------------------------------------------------------------


def _completed(env):
    grade_checks(env, 1.0)
    with env.repository.connection() as connection:
        return [entry for entry in C.resolve(connection, through=env.today()) if entry.status == "completed"]


def test_f1_a_held_grade_is_no_check_observation_and_no_completion(tmp_path):
    env = _env(tmp_path)
    run(env)
    done = _completed(env)
    assert done, "the run answered the check"
    entry = done[0]
    held = {"grading_support": {"proof_route_check": {"held_for_review": True, "status": "checked",
                                                      "version": "proof-route-check-v3"}}}
    with env.repository.atomic(), env.repository.connection() as connection:
        before = C.completion(connection, through=env.today())
        connection.execute(
            "INSERT INTO blind_grade_records (id, attempt_id, grading_prompt_version, output_schema_version, "
            "context_hash, record_json, created_at) VALUES ('bgr_ro5', ?, 'v', 'v', 'h', ?, ?)",
            (entry.attempt_id, json.dumps(held, separators=(",", ":")), env.now_iso()))
    with env.repository.connection() as connection:
        assert entry.attempt_id in held_for_review_attempts(connection, (entry.attempt_id,))
        again = {e.assignment_id: e for e in C.resolve(connection, through=env.today())}[entry.assignment_id]
        after = C.completion(connection, through=env.today())
    assert again.status == "excluded:grade_held_for_review" and again.outcome is None
    assert after["completed"] == before["completed"] - 1
    assert after["by_status"].get("excluded:grade_held_for_review") == 1


def test_f1_a_current_epoch_that_assesses_nothing_is_no_observation(tmp_path):
    from learnloop.outcome_contract import (UNASSESSED_INTERPRETATION, UNVERIFIED_CRITERION_BLOCK,
                                            UNVERIFIED_INTERPRETATION_KEY)

    env = _env(tmp_path)
    run(env)
    entry = _completed(env)[0]
    unverified = {"negative_evidence_blocked": UNVERIFIED_CRITERION_BLOCK,
                  UNVERIFIED_INTERPRETATION_KEY: UNASSESSED_INTERPRETATION}
    with env.repository.atomic(), env.repository.connection() as connection:
        connection.execute("UPDATE grading_evidence SET superseded_at = ? WHERE attempt_id = ? AND superseded_at IS NULL",
                           (env.now_iso(), entry.attempt_id))
        connection.execute(
            "INSERT INTO grading_evidence (id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
            "grading_revision, attribution_json) VALUES ('ge_ro5', ?, 'c1', 1.0, 1, ?, 9, ?)",
            (entry.attempt_id, env.now_iso(), json.dumps(unverified)))
    with env.repository.connection() as connection:
        again = {e.assignment_id: e for e in C.resolve(connection, through=env.today())}[entry.assignment_id]
    assert again.status == "excluded:unassessed" and again.outcome is None


def test_f1_a_missing_label_is_excluded_never_a_zero():
    assert C._label({"correctness": None, "attempt_type": "independent_attempt"}, assisted=False) is None
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE practice_attempts (id TEXT, manual_review_reason TEXT)")
    assert C.exclusion(connection, {"id": "x", "attempt_type": "independent_attempt", "correctness": None}) \
        == C.EXCLUDED_UNGRADED
    assert C.exclusion(connection, {"id": "x", "attempt_type": "self_report", "correctness": 1.0}) == C.EXCLUDED_TYPE
    # An "I don't know" answer is a failure, not an exclusion; help still makes a correct answer a non-success.
    assert C.exclusion(connection, {"id": "x", "attempt_type": "dont_know", "correctness": None}) is None
    assert C._label({"correctness": None, "attempt_type": "dont_know"}, assisted=False) == 0.0
    assert C._label({"correctness": 1.0, "hints_used": 1}, assisted=False) == 0.0


# -- F2 ------------------------------------------------------------------------------------------------------


def test_f2_the_check_is_administered_whatever_the_policy_chose(tmp_path):
    env = _env(tmp_path)
    los = ["L"]
    eligible = {"L": ["a"]}
    day = "2026-02-01"
    C.draw_day(env.vault, env.repository, local_date=day, now_iso=env.now_iso(), topics={"L": 1 / 90},
               eligible_items=lambda _los, exclude: {lo: [i for i in items if i not in exclude]
                                                     for lo, items in eligible.items()})
    pool = [SimpleNamespace(practice_item_id=item_id, lane=None, est_minutes=2.0) for item_id in "abc"]

    def place(chooser):
        return C.place(env.vault, env.repository, local_date=day, session_id=None, pool=pool, planned=(),
                       chooser_items=[item for item in pool if item.practice_item_id in chooser], lane=None,
                       eligible_items=lambda topics, exclude: {lo: [i for i in eligible[lo] if i not in exclude]
                                                               for lo in topics if lo in los})

    chose_it, chose_others = place("ab"), place("bc")
    # The same frozen assignment administers the same item either way.
    assert [p.item.practice_item_id for p in chose_it] == [p.item.practice_item_id for p in chose_others] == ["a"]
    # The collision reclassifies the policy's slot as the check; otherwise the last chooser item is replaced.
    assert chose_it[0].replaced == "a" and chose_it[0].detail["collision"] is True
    assert chose_others[0].replaced == "c" and chose_others[0].detail["collision"] is False


# -- F3 ------------------------------------------------------------------------------------------------------


def _coin_rows(rng, n, *, slope, p=0.1, confounder=1.0, observed_availability=False):
    rows = []
    for i in range(n):
        busy = rng.random() < 0.5
        u = rng.random()
        arm = SC.OFFER_STOP if u < p else (SC.PRESENT_NEXT if u < 2 * p else SC.POLICY)
        z = (-0.6 if busy else 0.4) + rng.gauss(0, 0.2)
        if arm == SC.OFFER_STOP:
            z -= 0.5  # the offer, often accepted, ends the session sooner
        y = slope * z + confounder * (0.8 if busy else -0.4) + rng.gauss(0, 0.3)
        weight = 1 / p if arm == SC.OFFER_STOP else (-1 / p if arm == SC.PRESENT_NEXT else 0.0)
        covariates = (0.0, (0.5 if busy else 1.5) if observed_availability else 1.0)
        rows.append(SC.ReturnRow(decision_id=f"d{i}", session_id=f"s{i}", arm=arm, weight=weight,
                                 covariates=covariates, z=z, y=y))
    return rows


def test_f3_a_confounded_return_is_not_read_as_a_return_effect():
    rows = _coin_rows(random.Random(11), 20_000, slope=0.0)
    # The observational slope (realized minutes as the treatment) is strongly negative on these rows.
    zs, ys = [r.z for r in rows], [r.y for r in rows]
    zbar, ybar = sum(zs) / len(zs), sum(ys) / len(ys)
    naive = sum((z - zbar) * (y - ybar) for z, y in zip(zs, ys, strict=True)) / sum((z - zbar) ** 2 for z in zs)
    assert naive < -0.5
    fitted = SC.fit_return_slope(rows, 0.5)
    assert fitted.source == "posterior_randomized_coin"
    assert abs(fitted.mean) < 0.15 and abs(fitted.mean) < 3 * fitted.variance ** 0.5


def test_f3_a_planted_causal_slope_is_recovered_through_the_coin():
    fitted = SC.fit_return_slope(_coin_rows(random.Random(5), 20_000, slope=0.4, observed_availability=True), 0.5)
    assert fitted.mean == pytest.approx(0.4, abs=0.15)
    # The policy arm alone carries no contrast: the prior stands.
    policy_only = [r for r in _coin_rows(random.Random(5), 500, slope=0.4) if r.arm == SC.POLICY]
    assert SC.fit_return_slope(policy_only, 0.5).source == "prior"


# -- F4 ------------------------------------------------------------------------------------------------------


def _activity_db(attempts, reader=()):
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE practice_attempts (id TEXT, created_at TEXT, latency_seconds REAL, "
                       "attempt_type TEXT, learning_object_id TEXT, correctness REAL)")
    connection.execute("CREATE TABLE interaction_events (kind TEXT, occurred_at TEXT, created_at TEXT, "
                       "payload_json TEXT)")
    for i, (at, seconds) in enumerate(attempts):
        connection.execute("INSERT INTO practice_attempts VALUES (?, ?, ?, 'independent_attempt', 'L', 1.0)",
                           (f"a{i}", at, seconds))
    for at, active in reader:
        connection.execute("INSERT INTO interaction_events VALUES ('reader_view_closed', ?, ?, ?)",
                           (at, at, json.dumps({"active_seconds": active, "idle_seconds": 0})))
    return connection


def _scored_cost(connection):
    row = {**_row(), "kappa0": 1.0, "remembered_minutes": 25.0}
    detail = S.score_decision(connection, row, _trace(), resolved={}, completion_rate=0.5,
                              r_lookup=lambda day: {"L": 0.25}, prices={}, gap_minutes=60)
    return detail.cost


def test_f4_the_cost_carries_the_minutes_before_the_decision():
    # Decision at 10:00 after 20 active minutes (four 5-minute attempts); 10 more after it. m̄ = 25, κ0 = 1:
    # ((20 + 10)² − 20²)/(2·25) = 10, not 10²/50 = 2.
    before = [("2026-01-01T09:45:00Z", 300), ("2026-01-01T09:50:00Z", 300), ("2026-01-01T09:55:00Z", 300),
              ("2026-01-01T10:00:00Z", 300)]
    after = [("2026-01-01T10:05:00Z", 300), ("2026-01-01T10:10:00Z", 300)]
    assert _scored_cost(_activity_db(before + after)) == pytest.approx(10.0)


def test_f4_the_cost_counts_reader_time_as_the_serving_clock_does():
    # A 30-minute Reader session the next day: 30²/50 = 18 on the serving clock's own activity.
    assert _scored_cost(_activity_db([], reader=[("2026-01-02T12:00:00Z", 1800)])) == pytest.approx(18.0)


# -- F5 ------------------------------------------------------------------------------------------------------


def _planted_scores(*_args, **_kwargs):
    rng = random.Random(5)
    return [S.Detail(scored=W.Scored(decision_id=f"d{i}", decided_at=f"2026-0{1 + i // 30}-{1 + i % 28:02d}T10:00:00Z",
                                     window_closes_at="2026-01-15T10:00:00Z", value=-0.05 + rng.gauss(0, 0.01)))
            for i in range(60)]


def test_f5_the_check_arm_off_restores_ro4s_weight_after_scores_accumulated(tmp_path, monkeypatch):
    from learnloop.daily_plan import objective_chooser as OC

    monkeypatch.setattr(S, "scores", _planted_scores)
    weights = {}
    for name, toml in (("on", "[router_objective]\nstop_coin = 0.0\npick_open_share = 0.0\n"), ("off", ARMS_OFF)):
        env = mixture_env(tmp_path / name, fake_runtime(), version=LATEST_ALGORITHM_VERSION, toml=toml)
        with env.repository.atomic(), env.repository.connection() as connection:
            A.insert(connection, experiment_id=A.CHECK, unit_id="check-day:2026-01-01", variant="day", propensity=1.0,
                     seed="s", draw=None, candidate_refs=[], detail={}, at="2026-01-01T00:00:00Z")
        weights[name] = OC.current_weight(env.repository, env.vault.config, at="2026-06-01T00:00:00Z")
    seeds = W.Seeds.from_config(env.vault.config)
    assert weights["on"][0] < seeds.w0  # the history moves w while the arm is on
    assert weights["off"][0] == pytest.approx(seeds.w0)
    assert "scores_version" not in weights["off"][1]


# -- F6 ------------------------------------------------------------------------------------------------------


def test_f6_a_fractional_delay_is_scored_on_the_goals_own_date():
    connection = _activity_db([])
    connection.execute("INSERT INTO practice_attempts VALUES ('exam1', '2026-01-02T12:00:00Z', 0, 'exam_evidence', "
                       "'L', 1.0)")
    row = {**_row(), "created_at": "2026-01-01T18:00:00Z"}
    trace = _trace()
    trace["evaluation"]["uses"]["dated"] = [{"goal_id": "g1", "lo": "L", "at_days": 0.75, "omega": 1.0, "m0": 0.5}]
    trace["inputs_sources"] = {"goals": {"g1": {"due_at": "2026-01-02T12:00:00Z"}}}
    detail = S.score_decision(connection, row, trace, resolved={}, completion_rate=0.5,
                              r_lookup=lambda day: {"L": 0.25}, prices={}, gap_minutes=60)
    assert detail.scored.reason != W.NO_RESULT and detail.scored.value is not None
    # Without the frozen due_at the exact delay still lands on the goal's date.
    assert S.dated_use_date({}, row, {"goal_id": "g1", "at_days": 0.75}) == "2026-01-02"


# -- F7 ------------------------------------------------------------------------------------------------------


def test_f7_the_trace_freezes_every_dated_goals_forecast_beyond_the_window():
    from learnloop.daily_plan import objective_chooser as OC

    far = V.DatedUse(goal_id="g1", lo="L", at_days=30.0, weight=1.0)
    numeric = OC.NumericPolicy(status="answered", inputs=SimpleNamespace(dated=(far,), horizon_days=90.0),
                               baselines={"dated": {"g1:L": 0.62}},
                               sources={"goals": {"g1": {"due_at": "2026-02-01T12:00:00Z"}}})
    frozen = OC._goal_dates(numeric)
    assert frozen["uses"] == [{"goal_id": "g1", "lo": "L", "at_days": 30.0, "due_at": "2026-02-01T12:00:00Z",
                               "m0": 0.62}]


def test_f7_the_goal_date_read_reads_a_goal_past_the_evaluation_window():
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE router_objective_traces (id TEXT, decision_id TEXT, local_date TEXT, "
                       "created_at TEXT, decision_kind TEXT, trace_json TEXT)")
    connection.execute("CREATE TABLE practice_attempts (id TEXT, created_at TEXT, attempt_type TEXT, "
                       "learning_object_id TEXT, correctness REAL)")
    trace = {"evaluation": {"uses": {"topics": [], "dated": []}},  # the window (B = 14) drops the 30-day goal
             "goal_dates": {"uses": [{"goal_id": "g1", "lo": "L", "at_days": 30.0,
                                      "due_at": "2026-02-01T12:00:00Z", "m0": 0.62}]}}
    connection.execute("INSERT INTO router_objective_traces VALUES ('t1', 'd1', '2026-01-02', '2026-01-02T10:00:00Z', "
                       "'plan_block', ?)", (json.dumps(trace),))
    goal = SimpleNamespace(id="g1", status="active", due_at="2026-02-01T12:00:00Z", exam=None)
    vault = SimpleNamespace(goals=[goal], config=SimpleNamespace(
        router_objective=SimpleNamespace(goal_transfer_prior_sd=1.0)))
    reads = G.read(connection, vault, now="2026-01-02T11:00:00Z")["reads"]
    assert reads[0]["goal_id"] == "g1" and reads[0].get("status") != "no_frozen_forecast"
    assert reads[0]["pool_forecast"] == pytest.approx(0.62, abs=1e-6)


# -- closed scores --------------------------------------------------------------------------------------------


def test_a_closed_scores_completion_rate_is_the_one_at_its_close(tmp_path, monkeypatch):
    seen = []
    real = S.score_decision

    def spy(connection, row, trace, **kwargs):
        seen.append(kwargs["completion_rate"])
        return real(connection, row, trace, **kwargs)

    monkeypatch.setattr(S, "score_decision", spy)
    calls = []
    # Landing ruling R1: the rate is read through the ledger as of the window's closure.
    monkeypatch.setattr(C.Ledger, "completion", lambda self, closure: calls.append(closure.local_date) or {"rate": 0.5})
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("CREATE TABLE router_objective_traces (id TEXT, decision_id TEXT, created_at TEXT, "
                       "window_closes_at TEXT, local_date TEXT, llm_status TEXT, numeric_status TEXT, kappa0 REAL, "
                       "remembered_minutes REAL, trace_json TEXT, decision_kind TEXT)")
    connection.execute("INSERT INTO router_objective_traces VALUES ('t1', 'd1', '2026-01-01T10:00:00Z', "
                       "'2026-01-03T10:00:00Z', '2026-01-01', 'answered', 'answered', 0, 10, ?, 'plan_block')",
                       (json.dumps(_trace()),))
    config = SimpleNamespace(router_objective=SimpleNamespace(session_gap_minutes=60))
    S.scores(connection, config, at="2026-03-01T00:00:00Z")
    # Read at the window's close (local date of 2026-01-03T10:00Z), never at the report's date two months later.
    assert seen == [0.5] and calls and all(day < "2026-02-01" for day in calls)
