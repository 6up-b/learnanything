"""Router objective RO5 §9 items 3, 4, 5 and 7, and the calibration report. Fakes only.

* **Item 7 (RO4's follow-ups)**: the rollouts read AD's fitted ``γ`` and reading curve (the subject view's posterior
  moments) at the tag with ``fitted_models``, RO4's priors off or below it; the memory combiner is fitted on resolved
  randomized checks (their frozen sensors against §6.2's label), its labelled prior with none.
* **Item 3, the goal-date read**: the pool forecast's recalibration moves with planted overconfident checks; the
  transfer slope is its wide prior with no imported result; "Am I ready?" reads are flagged self-selected.
* **Item 4**: ``S``'s ``α`` is labelled provisional; a randomized check's presentation is never a block decision's
  action in the router's outcomes.
* **Item 5**: the probe-versus-continue contrast from FG1's ``no_intervention`` floor, and the follow-up rule.
* **The first week** on the copy-shaped synthetic vault: the coin's draws and offers, the checks assigned,
  administered and completed per day, each arm's minutes, and whether ``w`` moved.
"""

from __future__ import annotations

import json
import sqlite3

import pytest

from learnloop.algorithm_versions import ROUTER_CALIBRATION_ALGORITHM_VERSION, ROUTER_OBJECTIVE_ALGORITHM_VERSION
from learnloop.daily_plan import objective_inputs as OI
from learnloop.daily_plan.policy import policy_for
from learnloop.router import outcomes as RO
from learnloop.router_objective import calibration_report as CR
from learnloop.router_objective import checks as C
from learnloop.router_objective import goal_read as G
from learnloop.router_objective import memory as M

from tests.daily_plan_fakes import iso
from tests.router_mixture_helpers import mixture_env, run
from tests.router_model_fakes import FakeLLM, fake_runtime
from tests.test_ro4_objective_serving import policy_answer

TAG = ROUTER_CALIBRATION_ALGORITHM_VERSION


# -- item 7 ----------------------------------------------------------------------------------------------


def test_the_rollouts_read_ads_fitted_learning_posterior_at_the_tag_and_priors_otherwise():
    from learnloop.adaptive_difficulty.priors import DOSE_SCALES, GAMMA_PRIOR, READING_PRIORS

    moments = {"learning": {"gamma": [0.31, 0.002], "gbar:1": [0.12, 0.001], "gbar:2": [0.25, 0.003]}}
    fitted = OI._learning(moments, True, GAMMA_PRIOR, READING_PRIORS, DOSE_SCALES)
    assert fitted.gamma == (0.31, 0.002) and fitted.gbar == ((0.12, 0.001), (0.25, 0.003))
    assert "fitted" in fitted.source
    prior = OI._learning(moments, False, GAMMA_PRIOR, READING_PRIORS, DOSE_SCALES)
    assert prior.gamma == (GAMMA_PRIOR[1], GAMMA_PRIOR[2]) and "prior" in prior.source
    partial = OI._learning({"learning": {"gamma": [0.3, 0.01]}}, True, GAMMA_PRIOR, READING_PRIORS, DOSE_SCALES)
    assert partial.gbar[0] == (READING_PRIORS[0][1], READING_PRIORS[0][2])


def test_ad_exposes_the_subject_views_learning_moments(tmp_path):
    from learnloop.adaptive_difficulty.readiness import decision_state_fields

    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    fields = decision_state_fields(env.vault, env.repository, ["lo_m1"], reading_doses=True, learning_moments=True)
    if fields.get("status") != "live":
        pytest.skip("AD's subject view is not live on this vault")
    learning = fields["learning"]
    assert set(learning) <= {"gamma", "gbar:1", "gbar:2"} and "gamma" in learning
    assert all(len(value) == 2 and value[1] >= 0 for value in learning.values())
    plain = decision_state_fields(env.vault, env.repository, ["lo_m1"], reading_doses=True)
    assert "learning" not in plain


def test_the_combiner_is_fitted_on_resolved_checks_and_is_its_prior_with_none(tmp_path, monkeypatch):
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    prior = OI._combiner(env.repository, env.now_iso())
    assert prior.mean == M.COMBINER_PRIOR_MEAN and prior.n == 0
    planted = [C.Resolved(assignment_id=f"a{i}", local_date="2026-01-01", topic="L", r=0.2, status="completed",
                          outcome=float(i % 4 != 0), sensors={"eta": 2.0, "retrievability": None}) for i in range(40)]
    seen: list = []

    def resolve(_connection, *, closure):
        seen.append(closure)
        return planted

    monkeypatch.setattr(C, "resolve", resolve)
    fitted = OI._combiner(env.repository, env.now_iso())
    # Landing ruling R1: the checks as of the decision itself.
    assert seen and seen[0] == C.Closure.at(env.now_iso())
    assert fitted.n == 40 and "resolved randomized checks" in fitted.source
    assert fitted.mean != M.COMBINER_PRIOR_MEAN


# -- item 3 ----------------------------------------------------------------------------------------------


def test_the_pool_recalibration_moves_with_overconfident_checks(monkeypatch):
    rows = [(G._logit(0.9), None, float(i % 2), 7) for i in range(60)]
    monkeypatch.setattr(G, "calibration_rows", lambda _connection, *, through: rows)
    fit = G.calibration(None, through="2026-12-31")
    assert fit["n"] == 60 and fit["by_lag"] == {7: 60}
    assert G.calibrated(0.9, fit) < 0.75  # a 90% forecast that came true half the time is pulled down
    monkeypatch.setattr(G, "calibration_rows", lambda _connection, *, through: [])
    assert G.calibrated(0.9, G.calibration(None, through="2026-12-31")) == pytest.approx(0.9)


def test_the_goal_read_on_a_vault_with_no_results_is_its_priors_and_labels_ready_reads(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    run(env)
    with env.repository.connection() as connection:
        read = G.read(connection, env.vault, now=env.now_iso())
    assert read["transfer"]["slopes"]["exam"]["beta"] == pytest.approx(1.0)
    assert read["transfer"]["slopes"]["exam"]["n"] == 0 and read["transfer"]["prior_sd"] == 1.0
    assert "self-selected" in read["ready_reads"]["label"]
    assert read["calibration"]["version"] == G.CALIBRATION_VERSION


# -- items 4 and 5 ---------------------------------------------------------------------------------------


def test_alpha_is_labelled_provisional_and_a_check_is_never_the_blocks_action():
    assert RO.S_ALPHA == 0.75 and RO.S_ALPHA_STATUS == "provisional" and RO.R_COLD_RULE == "provisional_one_day"
    assert RO._RANDOMIZED_CHECK_ORIGIN == C.ORIGIN
    decision = {"decision_kind": "plan_block", "id": "d1"}
    assert not RO._presentation_is_the_decisions(decision, {"origin": C.ORIGIN, "router_decision_id": "d1"})
    assert RO._presentation_is_the_decisions(decision, {"origin": "chooser", "router_decision_id": "d1"})


def _floor_db():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("CREATE TABLE router_decisions (id TEXT, decision_kind TEXT, chosen_ref TEXT, propensity REAL, "
                       "created_at TEXT, candidates_json TEXT)")
    connection.execute("CREATE TABLE router_outcomes (decision_id TEXT, r_cold_value REAL, r_cold_status TEXT)")
    return connection


def test_the_floor_contrast_is_read_from_fg1s_no_intervention_draws():
    connection = _floor_db()
    rows = [("d1", "insert_now", 0.9, "2026-11-01T10:00:00Z", 1.0), ("d2", "no_intervention", 0.05,
                                                                     "2026-11-01T11:00:00Z", 0.0),
            ("d3", "continue_current", 0.8, "2026-11-02T10:00:00Z", 1.0)]
    for decision_id, chosen, propensity, at, cold in rows:
        connection.execute("INSERT INTO router_decisions VALUES (?, 'plan_interrupt', ?, ?, ?, ?)",
                           (decision_id, chosen, propensity, at, json.dumps([{"ref": "no_intervention"}])))
        connection.execute("INSERT INTO router_outcomes VALUES (?, ?, 'observed')", (decision_id, cold))
    floor = CR.floor_section(connection)
    assert floor["decisions"] == 3 and floor["arms"]["no_intervention"]["decisions"] == 1
    assert floor["arms"]["probe"]["mean_r_cold"] == 1.0 and floor["arms"]["no_intervention"]["mean_r_cold"] == 0.0
    assert floor["no_intervention_share"] == pytest.approx(1 / 3, abs=1e-4)
    assert floor["leave_alone_arm"].startswith("not built")
    empty = CR.floor_section(_floor_db())
    assert empty["decisions"] == 0 and empty["higher_no_probe_share"].startswith("follow-up")


# -- the first week ----------------------------------------------------------------------------------------


def _new_session(env, runtime, day: int) -> str:
    session_id = f"s{day}"
    with env.repository.connection() as connection:
        connection.execute("INSERT INTO sessions(id, started_at) VALUES (?, ?)", (session_id, iso(env.clock.now())))
        connection.commit()
    env.session_id = session_id
    env.policy = policy_for(env.vault, env.repository, session_id=session_id, clock=env.clock, runtime=runtime,
                            serve=True)
    return session_id


def _end_session(env, session_id: str) -> None:
    with env.repository.connection() as connection:
        connection.execute("UPDATE sessions SET ended_at = ? WHERE id = ?", (iso(env.clock.now()), session_id))
        connection.commit()


def _week_env(tmp_path, runtime):
    """A copy-shaped vault: six practised topics (each with one item in memory, due or not) and four unseen items
    each, the shape of a real vault where new items wait in the pool."""

    from datetime import timedelta

    from tests.daily_plan_fakes import MovableClock, NOW, make_env, scheduled, seed_due
    from tests.helpers import create_daily_plan_vault

    los = {f"lo_{name}": [(f"pi_{name}{i}", 2.0) for i in range(5)] for name in "abcdef"}
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=los, version=TAG)
    items = []
    for index, (lo, entries) in enumerate(los.items()):
        items.append(scheduled(entries[0][0], lo, forgetting_risk=0.6 - 0.05 * index))
        items += [scheduled(item_id, lo, new_material=1.0) for item_id, _minutes in entries[1:]]
    env = make_env(paths.root, items, clock=MovableClock(), session_id=None)
    for index, (lo, entries) in enumerate(los.items()):
        due = NOW - timedelta(days=1) if index % 2 == 0 else NOW + timedelta(days=3)
        seed_due(env.repository, entries[0][0], due=due, last=NOW - timedelta(days=5))
    env.policy = policy_for(env.vault, env.repository, session_id=None, clock=env.clock, runtime=runtime, serve=True)
    return env


def _grade_answers(env, day: int) -> None:
    """The fake run records ungraded answers; a real day's are graded. Each answer of the day graded correct or not
    from a seeded draw (a synthetic learner at about 70%), so the checks resolve to labels (Codex review F1: an
    ungraded answer is no label)."""

    import random

    rng = random.Random(f"ro5-week-{day}")
    with env.repository.connection() as connection:
        ids = [row[0] for row in connection.execute(
            "SELECT id FROM practice_attempts WHERE correctness IS NULL ORDER BY created_at, id")]
        for attempt_id in ids:
            connection.execute("UPDATE practice_attempts SET correctness = ? WHERE id = ?",
                               (1.0 if rng.random() < 0.7 else 0.0, attempt_id))
        connection.commit()


def test_the_first_week_on_a_copy_shaped_synthetic_vault(tmp_path):
    """Seven days at the default arms (coin 0.05 each way, one embedded check a day), both policies answering, one
    day with no session. Printed for the stage record; the assertions are the arms' accounting."""

    runtime = fake_runtime(llm=FakeLLM(answer=policy_answer))
    env = _week_env(tmp_path, runtime)
    sessions = 0
    for day in range(7):
        if day != 3:
            session_id = _new_session(env, runtime, day)
            run(env, steps=60)
            _grade_answers(env, day)
            _end_session(env, session_id)
            sessions += 1
        env.clock.advance(24 * 60)
    with env.repository.connection() as connection:
        report = CR.build(connection, env.vault, now=env.now_iso())
    coin, checks, weight = report["stop_coin"], report["checks"], report["weight"]
    summary = {
        "stop_coin": {"draws": coin["draws"], "by_arm": coin["by_arm"], "offer_responses": coin["offer_responses"],
                      "days": coin["days"]},
        "checks": {"days": checks["days"], "completion": checks["completion"], "generation": checks["generation"]},
        "weight": {"w": weight["w"], "moved": weight["moved"], "closed_scores": weight["closed_scores"],
                   "censored": weight["censored"]},
        "price": report["price"]["regime"], "return_model": report["return_model"],
        "floor": {"decisions": report["floor"]["decisions"], "follow_up": report["floor"]["higher_no_probe_share"]},
    }
    print("FIRST_WEEK_REPORT", json.dumps(summary, sort_keys=True, default=str))
    assert sum(day["assigned"] for day in checks["days"].values()) >= sessions
    assert all(day["administered"] <= day["assigned"] for day in checks["days"].values())
    assert checks["completion"]["days_without_session"] >= 1
    # No window has closed inside a week (B = 14 days), so no score forms and w is still its prior.
    assert not weight["moved"] and weight["w"] == pytest.approx(0.8)
    assert coin["draws"] >= 1 and set(coin["by_arm"]) <= {"offer_stop", "present_next", "policy"}
    assert lines_ok(report)


def lines_ok(report) -> bool:
    return all(isinstance(line, str) and line for line in CR.lines(report))


def test_below_the_tag_the_cli_report_has_no_calibration_section(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(), version=ROUTER_OBJECTIVE_ALGORITHM_VERSION)
    run(env)
    from learnloop.router_objective_switches import calibration_tag

    assert not calibration_tag(env.vault.config)
