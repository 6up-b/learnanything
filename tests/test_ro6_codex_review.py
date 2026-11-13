"""Router objective RO6, Codex review (job 20261105-125456-EfabRp): each finding reproduced by a test that fails on the
pre-fix source.

* **F1**: a randomized cohort whose forced-arm returns go unobserved after the coin is kept whole; the forced arm's
  observed returns are weighted by that arm's observed share, so an arm difference in observation alone is not a
  contrast (balanced arms, identical returns, half of one arm censored: ``ŵ`` stays near zero, not 0.5), and an arm
  with no observed return leaves the contrast unidentified (no contrast, said);
* **F2**: an exam later the same day as a decision falls in that decision's interval: its result enters the reward,
  and with no import the transition is censored ``no_result``;
* **F3**: the backup values the next state at the decision's own cutoff; without a value there the transition is
  censored ``cutoff_unmatched``, never moved back by an average terminal rate (the re-review replaced the trim with
  the candidates valued at the carried cutoff: tests/test_ro6_codex_rereview.py);
* **F4**: the residual's mutable inputs (pending reports, mastery) are read at the decision's moment, before the
  prefetch job runs: a diagnosis queued after it never enters the features;
* **F5**: the contrasts' return reader admits an imported result only once it was known at its cutoff;
* **F6**: a window's partial-history product runs over every decision in it, its own window open or not, and a
  decision with no ratio censors the window.

Fakes only; no model request.
"""

from __future__ import annotations

import math
import random

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.router_objective import learned_tail as LT
from learnloop.router_objective import scores as S
from learnloop.router_objective import stop_coin as SC
from learnloop.router_objective import tail_data as TD
from learnloop.router_objective import value as V
from tests.ro6_codex_review_helpers import (
    CFG,
    FAR,
    STOP,
    _logged,
    _quiet,
    _row,
    _trace,
    _value_actions,
    _value_inputs,
)
from tests.ro6_codex_review_helpers import utc  # noqa: F401 - fixtures, used by parameter name

# -- F2 -------------------------------------------------------------------------------------------------------


def _same_day_pair(*, cutoff_second: float = 90.0) -> list[TD.Logged]:
    exam = [{"goal_id": "g1", "lo": "lo1", "at_days": 8.0 / 24.0, "due_at": "2026-10-01T18:00:00Z", "omega": 1.0}]
    # One shared cutoff (the first decision's 90 days and 9 hours ends where the second's 90 days does).
    first = _logged(_row("d1", "2026-10-01T10:00:00Z"),
                    _trace(q={STOP: 0.0, "a": 0.0}, cutoff_days=90.0 + 9.0 / 24.0, dated=exam))
    second = _logged(_row("d2", "2026-10-01T19:00:00Z"), _trace(q={STOP: 0.0, "a": 0.0}, cutoff_days=cutoff_second))
    return [first, second]


def test_f2_a_same_day_exam_after_the_decision_enters_its_reward(monkeypatch, utc):
    _quiet(monkeypatch, {"d1": "d2"}, exam=1.0)
    steps = TD.transitions(None, CFG, _same_day_pair(), at=FAR)
    assert [step.decision_id for step in steps.transitions] == ["d1"]
    assert steps.transitions[0].reward == pytest.approx(1.0)  # ω·Y with zero cost; 0 before the fix


def test_f2_a_same_day_exam_with_no_import_censors_the_transition(monkeypatch, utc):
    _quiet(monkeypatch, {"d1": "d2"}, exam=None)
    steps = TD.transitions(None, CFG, _same_day_pair(), at=FAR)
    assert steps.transitions == () and steps.censored.get(TD.NO_RESULT) == 1


def test_f2_the_use_moment_is_the_goals_due_at_else_the_exact_delay():
    from datetime import UTC, datetime

    created = datetime(2026, 10, 1, 10, 0, tzinfo=UTC)
    assert TD.use_moment({}, created, {"due_at": "2026-10-01T18:00:00Z"}) == datetime(2026, 10, 1, 18, 0, tzinfo=UTC)
    goals = {"inputs_sources": {"goals": {"g": {"due_at": "2026-10-03T08:00:00+00:00"}}}}
    assert TD.use_moment(goals, created, {"goal_id": "g"}) == datetime(2026, 10, 3, 8, 0, tzinfo=UTC)
    assert TD.use_moment({}, created, {"at_days": 0.5}) == datetime(2026, 10, 1, 22, 0, tzinfo=UTC)


# -- F3 -------------------------------------------------------------------------------------------------------


def test_f3_a_later_cutoff_with_no_value_at_the_earlier_one_is_censored(monkeypatch, utc):
    _quiet(monkeypatch, {"d1": "d2"})
    first = _logged(_row("d1", "2026-10-01T10:00:00Z"), _trace(q={STOP: 0.0, "a": 1.0}))
    # The next decision a day later: its cutoff a day later, and nothing valued at the first one's cutoff.
    second = _logged(_row("d2", "2026-10-02T10:00:00Z"), _trace(q={STOP: 2.0, "a": 3.0}, terminal=9.0))
    steps = TD.transitions(None, CFG, [first, second], at=FAR)
    assert steps.transitions == () and steps.censored.get(TD.CUTOFF_UNMATCHED) == 1


# The next state valued at the decision's own cutoff: re-review F3 replaced the trim (``q − past_trim``) with the
# candidates valued at the carried cutoff; its tests are in tests/test_ro6_codex_rereview.py.


def test_f3_a_shared_cutoff_needs_no_trim(monkeypatch, utc):
    _quiet(monkeypatch, {"d1": "d2"}, exam=1.0)
    steps = TD.transitions(None, CFG, _same_day_pair(), at=FAR)
    assert steps.transitions[0].detail["cutoff"] == "same_cutoff"
    assert steps.transitions[0].next_v_tail == 0.0


def test_f3_no_carried_cutoff_leaves_the_rollouts_as_ro4s():
    inputs, actions = _value_inputs(), _value_actions()
    plain = V.evaluate(inputs, actions, draws=8, seed="trim")
    own = V.evaluate(inputs, actions, draws=8, seed="trim", cutoff=inputs.cutoff)
    for ref, row in plain.by_ref().items():
        assert own.by_ref()[ref].q_draws == row.q_draws and own.by_ref()[ref].terms == row.terms
        assert "past_trim" not in row.terms


# -- F4 -------------------------------------------------------------------------------------------------------


def test_f4_a_diagnosis_queued_after_the_decisions_moment_never_enters_its_features(tmp_path, monkeypatch):
    from learnloop.daily_plan import objective_chooser as OC
    from learnloop.db.stores import router_objective as store
    from learnloop.router_objective import decision_state as DS

    from tests.router_mixture_helpers import mixture_env, run
    from tests.router_model_fakes import FakeLLM, fake_runtime
    from tests.ro4_objective_serving_helpers import policy_answer

    state = {"queued": 0}
    real_pending, real_job = DS._pending_reports, OC._objective_job

    def pending(connection, now_iso):
        found = dict(real_pending(connection, now_iso))
        found["diagnosis_jobs"] = int(found.get("diagnosis_jobs") or 0) + state["queued"]
        return found

    def job(entry, **kwargs):
        # A diagnosis queued after the decision froze its moment, before the prefetch job computes anything.
        state["queued"] = 1
        try:
            return real_job(entry, **kwargs)
        finally:
            state["queued"] = 0

    monkeypatch.setattr(DS, "_pending_reports", pending)
    monkeypatch.setattr(OC, "_objective_job", job)
    env = mixture_env(tmp_path, fake_runtime(llm=FakeLLM(answer=policy_answer)),
                      version=LATEST_ALGORITHM_VERSION)
    run(env, steps=4)
    with env.repository.connection() as connection:
        traces = [store.trace(connection, row["decision_id"])["trace"] for row in store.traces(connection)
                  if row["decision_kind"] == "plan_block"]
    applied = [trace["residual"] for trace in traces if (trace.get("residual") or {}).get("status") == "applied"]
    assert applied
    at = LT.NAMES.index("pending_reports")
    for record in applied:
        assert record["basis"]["pending_reports"] == 0
        assert all(float(entry["features"][at]) == 0.0 for entry in record["candidates"].values())


def test_f4_no_snapshot_leaves_the_residual_out():
    from learnloop.router_objective import tail_serve as TS

    record = TS.residual(None, CFG, inputs=None, actions=(), now_iso="2026-10-01T10:00:00Z", generator_now="g",
                         frozen=None)
    assert record["status"] == "no_snapshot" and not TS.applied(record)
    stale = {"at": "2026-10-01T09:00:00Z", "pending_reports": {}, "los": {}}
    assert TS.residual(None, CFG, inputs=None, actions=(), now_iso="2026-10-01T10:00:00Z", generator_now="g",
                       frozen=stale)["status"] == "no_snapshot"


# -- F5 -------------------------------------------------------------------------------------------------------


def test_f5_the_contrasts_return_reader_admits_an_import_only_once_known(tmp_path):
    from learnloop.algorithm_versions import ROUTER_LEARNED_TAIL_ALGORITHM_VERSION

    from tests.ro1_availability_reads_helpers import AFTER, CUTOFF, LO, _seeded

    vault, repository = _seeded(tmp_path, ROUTER_LEARNED_TAIL_ALGORITHM_VERSION, None)
    trace = {"evaluation": {"window_days": 9, "c0": 0.0, "uses": {"topics": [], "dated": [
        {"goal_id": "g", "lo": LO, "due_at": "2026-05-01T09:00:00Z", "omega": 1.0, "m0": 0.0}]}}}
    row = {**_row("d1", "2026-04-25T10:00:00Z", closes="2026-05-04T10:00:00Z"), "trace": trace}
    # RO6's landing (ruling R4 on RO5's R1 and R10): a window reads as of its own closure, so the import (received
    # May 19) is d1's never (its window closed May 4) and d2's, whose window closes after it, once read after that.
    late = {**_row("d2", "2026-05-10T10:00:00Z", closes="2026-05-19T20:00:00Z"), "trace": trace}
    with repository.connection() as connection:
        before = S.observed_returns(connection, vault.config, at=CUTOFF, rows=[row])
        after = S.observed_returns(connection, vault.config, at=AFTER, rows=[row, late])
        known = TD._exam_result_known(connection, vault.config, LO, "2026-05-01", CUTOFF)
    assert known is None
    assert before["d1"] == (None, "no_result")  # imported May 19: no return on May 5
    assert after["d1"] == (None, "no_result")  # a closed window never moves with a later import
    assert after["d2"][0] is not None


# -- F6 -------------------------------------------------------------------------------------------------------


def _windowed(monkeypatch, ratios: dict[str, float | None]) -> list[TD.Logged]:
    rows = [_logged(_row("d1", "2026-10-01T10:00:00Z", closes="2026-10-15T10:00:00Z"), _trace(q={STOP: 0.0, "a": 0.0})),
            _logged(_row("d2", "2026-10-10T10:00:00Z", closes="2026-10-24T10:00:00Z"), _trace(q={STOP: 0.0, "a": 0.0}))]
    monkeypatch.setattr(TD, "improvement_ratio", lambda row: ratios[row.decision_id])
    monkeypatch.setattr(TD, "_with_traces", lambda _connection, found: [dict(row.row) for row in found])
    monkeypatch.setattr(TD.S, "observed_returns",
                        lambda _connection, _config, *, at, rows: {row["decision_id"]: (1.0, None) for row in rows
                                                                    if row["window_closes_at"] < at})
    return rows


def test_f6_a_windows_product_includes_a_decision_whose_own_window_is_open(monkeypatch):
    rows = _windowed(monkeypatch, {"d1": 1.0, "d2": 2.0})
    report = TD.cross_check(None, CFG, rows, at="2026-10-20T00:00:00Z")
    assert report["n"] == 1
    assert report["window"]["estimate"] == pytest.approx(1.0)  # (1·2 − 1)·1; 0 before the fix
    assert report["one_step"]["estimate"] == pytest.approx(0.0)


def test_f6_a_window_with_a_decision_of_unknown_ratio_is_censored(monkeypatch):
    rows = _windowed(monkeypatch, {"d1": 1.0, "d2": None})
    report = TD.cross_check(None, CFG, rows, at="2026-10-20T00:00:00Z")
    assert report["window"] is None and report["window_censored"] == {LT.INCOMPLETE_HISTORY: 1}
    assert report["one_step"]["n"] == 1


# -- F1 -------------------------------------------------------------------------------------------------------


def _cohort(n: int, *, censor: dict[str, float], seed: int = 3, rate: float = 0.05) -> tuple[list[TD.Logged], dict]:
    """Balanced coin draws, identical potential returns in both arms (``G = ΔV_residual``: the residual tracks the
    return's level, never the arm's effect, so the true contrast is zero), and each arm's return unobserved with
    the probability ``censor`` gives it."""

    rng = random.Random(seed)
    rows, returns = [], {}
    for i in range(n):
        residual = rng.gauss(0.0, 1.0)
        tail = rng.gauss(0.0, 1.0)
        u = rng.random()
        arm = SC.OFFER_STOP if u < rate else (SC.PRESENT_NEXT if u < 2 * rate else SC.POLICY)
        trace = _trace(q={STOP: tail, "a": 0.0}, mu={STOP: 0.5, "a": 0.5}, residual={STOP: residual, "a": 0.0},
                       coin={"arm": arm, "rate": rate})
        decision = f"c{i:05d}"
        rows.append(_logged(_row(decision, "2026-10-01T10:00:00Z", closes="2026-10-15T10:00:00Z"), trace))
        observed = rng.random() >= censor.get(arm, 0.0)
        returns[decision] = (residual, None) if observed else (None, "no_result")
    return rows, returns


def _contrasts(monkeypatch, rows, returns):
    monkeypatch.setattr(TD, "_with_traces", lambda _connection, found: [])
    monkeypatch.setattr(TD.S, "observed_returns", lambda *_a, **_k: returns)
    return TD.contrasts(None, CFG, rows, at="2026-11-01T00:00:00Z")


def test_f1_an_arm_difference_in_observation_alone_is_no_contrast(monkeypatch):
    rows, returns = _cohort(20000, censor={SC.PRESENT_NEXT: 0.5})
    found, record = _contrasts(monkeypatch, rows, returns)
    # About 0.5 before the first fix. Since the re-review (F1) a forced draw with no return leaves the contrast
    # unidentified rather than corrected by an observed share (no observation probability is justified).
    assert LT.residual_weight(found, prior_sd=1.0, at="2026-11-01T00:00:00Z").w_hat == 0.0
    assert record["status"] == LT.UNIDENTIFIED and record["assigned"][SC.OFFER_STOP] == record["observed"][SC.OFFER_STOP]
    complete, record = _contrasts(monkeypatch, *_cohort(20000, censor={}))
    assert len(complete) == len(rows) and record["status"] == "identified"  # the randomized cohort, whole
    weight = LT.residual_weight(complete, prior_sd=1.0, at="2026-11-01T00:00:00Z")
    assert weight.w_hat < 0.15 and abs(weight.slope_mean) < 3 * weight.slope_sd + 1e-9


def test_f1_an_arm_with_no_observed_return_leaves_the_contrast_unidentified(monkeypatch):
    rows, returns = _cohort(2000, censor={SC.OFFER_STOP: 1.0})
    found, record = _contrasts(monkeypatch, rows, returns)
    assert found == [] and record["status"] == LT.UNIDENTIFIED and SC.OFFER_STOP in record["why"]
    assert record["unobserved"][SC.OFFER_STOP] == {"no_result": record["assigned"][SC.OFFER_STOP]}
    assert LT.residual_weight(found, prior_sd=1.0).w_hat == 0.0


def test_f1_the_policy_arm_stays_a_zero_whatever_its_return():
    draws = [LT.CoinDraw(decision_id=f"p{i}", decided_at="2026-10-01T10:00:00Z", window_closes_at="2026-10-15T10:00:00Z",
                         arm=SC.POLICY, rate=0.05, value=None if i % 2 else 3.0, reason="no_result", tail=0.1,
                         residual=0.2) for i in range(4)]
    found, record = LT.coin_contrasts(draws)
    assert [row.realized for row in found] == [0.0] * 4 and record["status"] == "identified"
    assert not any(row.forced for row in found) and math.isclose(found[0].forced_probability, 0.1)
