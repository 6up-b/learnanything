"""Router objective RO6, Codex re-review (job 20261105-140523-n40uvz): each finding reproduced by a test that fails on
the pre-fix source (``02a3ee8563``).

* **F1 (reopened)**: observation that depends on a pre-coin feature is not corrected by any share of observed
  returns, pooled or by arm. Every window's return is read complete (the bracket over the uses a check could
  observe, a dated use with no known result left out of every window holding it alike), and a forced draw that
  still has no return leaves the contrast unidentified;
* **F3 (reopened)**: the backup's next value is the next decision's candidates valued with every rollout run at
  the earlier decision's cutoff (the tail's ranking, a probe's branch choice, the quadrature's boundaries and the
  end), never this cutoff's rollouts trimmed; its next features are taken at that cutoff;
* **F7**: a trace frozen by an earlier RO6 build (thirteen features) is rebuilt with this build's function, and the
  features version its residual served with is part of its generator version.

Fakes only; no model request.
"""

from __future__ import annotations

import random

import pytest

from learnloop.router_objective import learned_tail as LT
from learnloop.router_objective import scores as S
from learnloop.router_objective import stop_coin as SC
from learnloop.router_objective import tail_data as TD
from learnloop.router_objective import tail_serve as TS
from learnloop.router_objective import value as V

from tests.test_ro6_codex_review import (CFG, FAR, STOP, _logged, _quiet, _row, _trace, _value_actions,  # noqa: F401
                                         _value_inputs, utc)

AT = "2026-11-01T00:00:00Z"


# -- F1 -------------------------------------------------------------------------------------------------------


def _feature_censored(n: int, *, seed: int = 11, rate: float = 0.05, censor: float = 0.6) -> list[LT.CoinDraw]:
    """Codex's reproduction: a balanced coin, identical potential returns in both arms (``G = 1 + x``, ``x`` the
    residual's predicted contrast: it tracks the return's level, never the arm's effect), and observation that
    depends on the pre-coin ``x`` (offer stop loses low-``x`` returns, present next high-``x`` ones)."""

    rng = random.Random(seed)
    draws = []
    for i in range(n):
        x = rng.gauss(0.0, 1.0)
        u = rng.random()
        arm = SC.OFFER_STOP if u < rate else (SC.PRESENT_NEXT if u < 2 * rate else SC.POLICY)
        lost = (arm == SC.OFFER_STOP and x < 0) or (arm == SC.PRESENT_NEXT and x > 0)
        value = None if lost and rng.random() < censor else 1.0 + x
        draws.append(LT.CoinDraw(decision_id=f"c{i:05d}", decided_at="2026-10-01T10:00:00Z",
                                 window_closes_at="2026-10-15T10:00:00Z", arm=arm, rate=rate, value=value,
                                 reason="no_result" if value is None else None, tail=rng.gauss(0.0, 1.0), residual=x))
    return draws


def test_f1_observation_on_a_pre_coin_feature_leaves_the_contrast_unidentified():
    draws = _feature_censored(8000)
    found, record = LT.coin_contrasts(draws)
    # Before the fix: status "identified" (pooled shares 0.683 and 0.673) and ŵ = 0.493 (slope 0.493, sd 0.121) from
    # the observation pattern alone.
    assert record["status"] == LT.UNIDENTIFIED and found == []
    assert "no justified observation probability" in record["why"]
    assert record["unobserved"][SC.OFFER_STOP]["no_result"] == record["assigned"][SC.OFFER_STOP] - record["observed"][SC.OFFER_STOP]
    assert LT.residual_weight(found, prior_sd=1.0, at=AT).w_hat == 0.0


def test_f1_complete_returns_with_identical_arms_give_no_contrast():
    draws = [LT.CoinDraw(**{**draw.__dict__, "value": 1.0 + draw.residual, "reason": None})
             for draw in _feature_censored(8000)]
    found, record = LT.coin_contrasts(draws)
    assert record["status"] == "identified" and len(found) == len(draws)
    weight = LT.residual_weight(found, prior_sd=1.0, at=AT)
    assert weight.w_hat < 0.15 and abs(weight.slope_mean) < 3 * weight.slope_sd + 1e-9


def test_f1_the_contrasts_read_every_window_complete(monkeypatch):
    seen = {}

    def returns(_connection, _config, *, at, rows, complete=False):
        seen["complete"] = complete
        return {}

    monkeypatch.setattr(TD, "_with_traces", lambda _connection, found: [])
    monkeypatch.setattr(TD.S, "observed_returns", returns)
    TD.contrasts(None, CFG, [], at=AT)
    assert seen == {"complete": True}


def test_f1_a_complete_return_leaves_an_unknown_dated_use_out_and_keeps_a_window_with_no_checkable_use(tmp_path):
    from learnloop.algorithm_versions import ROUTER_LEARNED_TAIL_ALGORITHM_VERSION

    from tests.test_ro1_availability_reads import AFTER, CUTOFF, LO, _seeded

    vault, repository = _seeded(tmp_path, ROUTER_LEARNED_TAIL_ALGORITHM_VERSION, None)
    trace = {"evaluation": {"window_days": 9, "c0": 0.0, "uses": {"topics": [], "dated": [
        {"goal_id": "g", "lo": LO, "due_at": "2026-05-01T09:00:00Z", "omega": 1.0, "m0": 0.0}]}}}
    row = {**_row("d1", "2026-04-25T10:00:00Z", closes="2026-05-04T10:00:00Z"), "trace": trace}
    with repository.connection() as connection:
        default = S.observed_returns(connection, vault.config, at=CUTOFF, rows=[row])
        before = S.observed_returns(connection, vault.config, at=CUTOFF, rows=[row], complete=True)
        after = S.observed_returns(connection, vault.config, at=AFTER, rows=[row], complete=True)
        default_after = S.observed_returns(connection, vault.config, at=AFTER, rows=[row])
        cost = S.window_cost(connection, start=row["created_at"], end="2026-05-04T10:00:00.000000Z",
                             gap_minutes=float(vault.config.router_objective.session_gap_minutes),
                             prices=S._day_prices(connection), own=(0.0, 20.0))
    assert default["d1"] == (None, "no_result")  # RO5's reading and the cross-check's: unchanged
    value, note = before["d1"]
    # The exam imported later is left out; no checkable use: the bracket is the cost term alone (−(C − C⁰)).
    assert value == pytest.approx(-cost) and note == "dated_left_out:1;no_randomized_use"
    later_value, later_note = after["d1"]
    # The import known: the dated use is in the sum (observed, r = 1), as RO6's reader had it.
    assert later_value == pytest.approx(default_after["d1"][0]) and later_note is None


# -- F3 -------------------------------------------------------------------------------------------------------


def test_f3_a_carried_cutoff_runs_every_rollout_at_it(monkeypatch):
    inputs, actions = _value_inputs(), _value_actions()
    own = V.evaluate(inputs, actions, draws=8, seed="carried")
    carried = inputs.cutoff - 0.37  # off the day grid: the quadrature's boundaries move too
    at_carried = V.evaluate(inputs, actions, draws=8, seed="carried", cutoff=carried)
    assert at_carried.cutoff == pytest.approx(carried)
    # An independent route to the same model: the inputs' own cutoff is the carried one (the ranking's remaining
    # span, the probe's branch choice in the belief's world, the boundaries and the end all read it).
    monkeypatch.setattr(V.Inputs, "cutoff", property(lambda self: carried))
    reference = V.evaluate(inputs, actions, draws=8, seed="carried")
    for ref, row in reference.by_ref().items():
        assert at_carried.by_ref()[ref].q_draws == row.q_draws
    assert any(abs(at_carried.by_ref()[ref].q - row.q) > 1e-6 for ref, row in own.by_ref().items())
    assert "branches" in at_carried.by_ref()["p"].extra  # the probe's branch choice ran at the carried cutoff


def _carried_record(q: dict[str, float], features: dict[str, list[float]]) -> dict:
    return {"decision_id": "d1", "cutoff_days": repr(89.0), "horizon_days": 90.0, "status": "carried",
            "q": q, "q_status": "valued", "features": {ref: [repr(v) for v in vector] for ref, vector in features.items()}}


def test_f3_the_backup_reads_the_values_and_features_at_the_carried_cutoff(monkeypatch, utc):
    _quiet(monkeypatch, {"d1": "d2"})
    width = len(LT.NAMES)
    first = _logged(_row("d1", "2026-10-01T10:00:00Z"), _trace(q={STOP: 0.0, "a": 1.0}))
    carried_features = {STOP: [0.25] * width, "a": [0.75] * width}
    second = _logged(_row("d2", "2026-10-02T10:00:00Z"), _trace(
        q={STOP: 2.0, "a": 3.0}, terminal=9.0, features={STOP: [0.5] * width, "a": [0.5] * width},
        previous=_carried_record({STOP: 1.25, "a": 2.5}, carried_features)))
    steps = TD.transitions(None, CFG, [first, second], at=FAR)
    assert len(steps.transitions) == 1  # before the fix: cutoff_unmatched (it read only q − past_trim)
    step = steps.transitions[0]
    assert step.detail["cutoff"] == "previous_cutoff"
    assert step.next_v_tail == pytest.approx(0.5 * 1.25 + 0.5 * 2.5)
    assert step.next_phi == pytest.approx(tuple(0.5 * 0.25 + 0.5 * 0.75 for _ in range(width)))


def test_f3_a_trimmed_value_alone_is_no_value_at_the_carried_cutoff(monkeypatch, utc):
    _quiet(monkeypatch, {"d1": "d2"})
    first = _logged(_row("d1", "2026-10-01T10:00:00Z"), _trace(q={STOP: 0.0, "a": 1.0}))
    second = _logged(_row("d2", "2026-10-02T10:00:00Z"), _trace(
        q={STOP: 2.0, "a": 3.0}, past_trim={STOP: 0.5, "a": 0.25},
        previous={"decision_id": "d1", "cutoff_days": repr(89.0), "trim_at_days": 179.0, "status": "covered"}))
    steps = TD.transitions(None, CFG, [first, second], at=FAR)
    assert steps.transitions == () and steps.censored.get(TD.CUTOFF_UNMATCHED) == 1


def test_f3_the_chooser_values_the_candidates_again_at_the_carried_cutoff(tmp_path):
    from learnloop.algorithm_versions import ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
    from learnloop.db.stores import router_objective as store

    from tests.router_mixture_helpers import mixture_env, run
    from tests.router_model_fakes import FakeLLM, fake_runtime
    from tests.test_ro4_objective_serving import policy_answer

    env = mixture_env(tmp_path, fake_runtime(llm=FakeLLM(answer=policy_answer)),
                      version=ROUTER_LEARNED_TAIL_ALGORITHM_VERSION)
    # Enough items for a second block decision whatever the blocks' sizes (the first has no earlier decision).
    run(env, steps=16)
    with env.repository.connection() as connection:
        traces = [store.trace(connection, row["decision_id"])["trace"] for row in store.traces(connection)
                  if row["decision_kind"] == "plan_block"]
    carried = [trace for trace in traces if ((trace.get("residual") or {}).get("previous") or {}).get("status")
               == TS.CARRIED]
    assert carried, [((trace.get("residual") or {}).get("status"), (trace.get("residual") or {}).get("previous"),
                      (trace.get("residual") or {}).get("error")) for trace in traces]
    span_at = LT.NAMES.index("cutoff_span")
    for trace in carried:
        previous = trace["residual"]["previous"]
        support = list(trace["mixing"]["mu"])
        assert previous["q_status"] == "valued" and set(support) <= set(previous["q"])
        assert "past_trim" not in str(trace["candidates"])
        for ref in support:
            vector = [float(v) for v in previous["features"][ref]]
            own = [float(v) for v in trace["residual"]["candidates"][ref]["features"]]
            assert len(vector) == len(LT.NAMES)
            assert vector[span_at] == pytest.approx(float(previous["cutoff_days"]) / 90.0)
            assert [v for k, v in enumerate(vector) if k != span_at] == [v for k, v in enumerate(own) if k != span_at]


# -- F7 -------------------------------------------------------------------------------------------------------


V1 = "ro6_belief_features_v1"


def _v1_trace(q: dict[str, float], cutoff_days: float) -> dict:
    trace = _trace(q=q, cutoff_days=cutoff_days, features={ref: [0.5] * 13 for ref in q})
    trace["residual"].pop("features_version", None)
    trace["residual"]["fit"] = {"features_version": V1}
    return trace


def test_f7_an_earlier_builds_thirteen_features_are_rebuilt(monkeypatch, utc):
    _quiet(monkeypatch, {"d1": "d2"})
    # Two legacy decisions a day apart sharing one absolute cutoff.
    first = _logged(_row("d1", "2026-10-01T10:00:00Z"), _v1_trace({STOP: 0.0, "a": 1.0}, 91.0))
    second = _logged(_row("d2", "2026-10-02T10:00:00Z"), _v1_trace({STOP: 2.0, "a": 3.0}, 90.0))
    steps = TD.transitions(None, CFG, [first, second], at=FAR)  # before the fix: IndexError
    assert len(steps.transitions) == 1
    assert first.features_source.startswith("rebuilt") and second.features_source.startswith("rebuilt")
    assert all(len(vector) == len(LT.NAMES) for row in (first, second) for vector in row.phi.values())
    fitted = TD.fits(None, CFG, at=FAR, rows=[first, second])
    assert all(len(fit.coef) == len(LT.NAMES) for fit in fitted.by_generator.values())


def test_f7_the_served_features_version_is_part_of_the_generator():
    legacy = _v1_trace({STOP: 0.0, "a": 1.0}, 90.0)
    current = _trace(q={STOP: 0.0, "a": 1.0})
    unvalued = {**current, "residual": {"status": "no_snapshot"}}
    assert TD.served_features_version(legacy) == V1
    assert TD.served_features_version(current) == LT.FEATURES_VERSION
    assert TD.served_features_version(unvalued) == LT.FEATURES_VERSION
    assert TD.generator(legacy, "mvp-0.49") != TD.generator(current, "mvp-0.49")
    assert TD.generator(unvalued, "mvp-0.49") == TD.generator(current, "mvp-0.49")
    # This build's frozen fourteen are read as frozen; the legacy ones never are.
    assert _logged(_row("d3", "2026-10-03T10:00:00Z"), current).features_source == "frozen"
    assert _logged(_row("d4", "2026-10-03T11:00:00Z"), legacy).features_source.startswith("rebuilt")
