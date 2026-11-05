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
import time
from types import SimpleNamespace

import pytest

from learnloop.router_objective import learned_tail as LT
from learnloop.router_objective import scores as S
from learnloop.router_objective import stop_coin as SC
from learnloop.router_objective import tail_data as TD
from learnloop.router_objective import value as V

STOP = SC.STOP
CFG = SimpleNamespace(router_objective=SimpleNamespace(session_gap_minutes=30.0, residual_prior_sd=0.01,
                                                       residual_weight_prior_sd=1.0, evaluation_window_days=14))
FAR = "2100-01-01T00:00:00Z"


@pytest.fixture
def utc(monkeypatch):
    monkeypatch.setenv("TZ", "UTC")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def _trace(*, q: dict[str, float], mu: dict[str, float] | None = None, chosen: str = "a", cutoff_days: float = 90.0,
           residual: dict[str, float] | None = None, past_trim: dict[str, float] | None = None,
           previous: dict | None = None, coin: dict | None = None, dated: list[dict] | None = None,
           terminal: float = 0.0, features: dict[str, list[float]] | None = None) -> dict:
    support = list(q)
    mu = mu or {ref: 1.0 / len(support) for ref in support}
    width = len(LT.NAMES)
    candidates = {ref: {"kind": "stop" if ref == STOP else "review", "minutes": 0.0 if ref == STOP else 5.0,
                        "sensors": {}, "terms": {"q": value, **({"past_trim": past_trim[ref]} if past_trim else {})}}
                  for ref, value in q.items()}
    frozen = {ref: {"features": (features or {}).get(ref) or [0.0] * width,
                    "v_residual": (residual or {}).get(ref, 0.0)} for ref in support}
    record = {"status": "applied", "features_version": LT.FEATURES_VERSION, "candidates": frozen,
              **({"previous": previous} if previous else {})}
    return {"candidates": candidates, "mixing": {"mu": mu, "chosen": chosen, "effective": {"numeric": 0.5},
                                                 "epsilon": 0.0, "seeds": {}},
            "versions": {"horizon_days": 90.0}, "cutoff_days": cutoff_days, "reference": {"terms": {"terminal": terminal}},
            "residual": record, "policies": {"numeric": {"choice": chosen}},
            **({"stop_coin": coin} if coin else {}), **({"goal_dates": {"uses": dated}} if dated else {})}


def _row(decision_id: str, created_at: str, *, closes: str | None = None) -> dict:
    return {"id": f"t-{decision_id}", "decision_id": decision_id, "created_at": created_at,
            "local_date": created_at[:10], "window_closes_at": closes, "algorithm_version": "mvp-0.49",
            "kappa0": 0.0, "remembered_minutes": 20.0, "llm_status": "answered", "numeric_status": "answered"}


def _logged(row: dict, trace: dict) -> TD.Logged:
    return TD._logged(None, row, trace, CFG, FAR, False)


def _quiet(monkeypatch, links: dict[str, str | None], *, exam: float | None = 1.0) -> None:
    """``transitions``' reads replaced: the chain's links, no checks, no attention cost, ``exam`` for every import."""

    monkeypatch.setattr(TD, "_next_links", lambda _connection, ids: ({key: links.get(key) for key in ids}, {}))
    monkeypatch.setattr(TD.C, "resolve", lambda _connection, through: [])
    monkeypatch.setattr(TD.C, "administered", lambda _connection: {})
    monkeypatch.setattr(TD.S, "_day_prices", lambda _connection: {})
    monkeypatch.setattr(TD.S, "window_cost", lambda *_a, **_k: 0.0)
    monkeypatch.setattr(TD, "_exam_result_known", lambda _connection, _config, _lo, _on, _at: exam)


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


def _value_inputs():
    from tests.test_ro4_value import _inputs

    return _inputs(topics=(V.Topic(lo="lo_a", eta_mean=0.4, eta_var=0.2, undated_density=0.2, practiced=True,
                                   stability=3.0, elapsed_days=2.0),
                           V.Topic(lo="lo_b", eta_mean=-0.3, eta_var=0.1, undated_density=0.1)),
                   horizon_days=6.0, return_gaps_days=(1.0, 2.0), stop_accept=(2.0, 2.0),
                   dated=(V.DatedUse("g", "lo_b", 3.5, 1.0),))


def _value_actions():
    return [V.Action(ref="a", kind=V.REVIEW, item_los=("lo_a",), minutes=5.0),
            V.Action(ref="p", kind=V.PROBE, item_los=("lo_b",), minutes=4.0),
            V.Action(ref="stop_for_today", kind=V.STOP)]


def test_f3_no_carried_cutoff_leaves_the_rollouts_as_ro4s():
    inputs, actions = _value_inputs(), _value_actions()
    plain = V.evaluate(inputs, actions, draws=8, seed="trim")
    own = V.evaluate(inputs, actions, draws=8, seed="trim", cutoff=inputs.cutoff)
    for ref, row in plain.by_ref().items():
        assert own.by_ref()[ref].q_draws == row.q_draws and own.by_ref()[ref].terms == row.terms
        assert "past_trim" not in row.terms


# -- F4 -------------------------------------------------------------------------------------------------------


def test_f4_a_diagnosis_queued_after_the_decisions_moment_never_enters_its_features(tmp_path, monkeypatch):
    from learnloop.algorithm_versions import ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
    from learnloop.daily_plan import objective_chooser as OC
    from learnloop.db.stores import router_objective as store
    from learnloop.router_objective import decision_state as DS

    from tests.router_mixture_helpers import mixture_env, run
    from tests.router_model_fakes import FakeLLM, fake_runtime
    from tests.test_ro4_objective_serving import policy_answer

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
                      version=ROUTER_LEARNED_TAIL_ALGORITHM_VERSION)
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

    from tests.test_ro1_availability_reads import AFTER, CUTOFF, LO, _seeded

    vault, repository = _seeded(tmp_path, ROUTER_LEARNED_TAIL_ALGORITHM_VERSION, None)
    trace = {"evaluation": {"window_days": 9, "c0": 0.0, "uses": {"topics": [], "dated": [
        {"goal_id": "g", "lo": LO, "due_at": "2026-05-01T09:00:00Z", "omega": 1.0, "m0": 0.0}]}}}
    row = {**_row("d1", "2026-04-25T10:00:00Z", closes="2026-05-04T10:00:00Z"), "trace": trace}
    with repository.connection() as connection:
        before = S.observed_returns(connection, vault.config, at=CUTOFF, rows=[row])
        after = S.observed_returns(connection, vault.config, at=AFTER, rows=[row])
        known = TD._exam_result_known(connection, vault.config, LO, "2026-05-01", CUTOFF)
    assert known is None
    assert before["d1"] == (None, "no_result")  # imported May 19: no return on May 5
    assert after["d1"][0] is not None


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
