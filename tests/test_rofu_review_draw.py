"""The follow-up batch's landing ruling R1: the rollouts' review outcome from the memory model's own ``P(perform)``.

Item 7 of ``docs/reviews/router-followups-nov5.md`` found the rollouts drew a practised topic's practice outcome from
AD's predictive ``σ(η)`` but applied it through FSRS, whose lapse branch resets a strong item's stability, while the
uses were scored on the combiner over ``η`` and FSRS's ``R`` (§8.4): a review FSRS calls a lapse was not one the
model expected. With ``[router_objective] consistent_review_draw`` at the batch's tag, a practised topic's outcome is
drawn from the combiner at that moment and the belief observes it under the same likelihood. Fakes only.

* Switch off (the rollouts' default, below the tag): mvp-0.49's draw for draw. The pinned digests and the probe's
  values were computed on the pre-fix source (``5919b5a08c`` merged with main, before this commit).
* R1's synthetic probe (8 practised topics, ``m̄`` 30, blocks of 10 minutes and 3 items, 64 draws, ``η`` from −0.5 to
  1.5, ``S`` 2 or 40): its numbers before and after, pinned. No sign is asserted as a law.
* The draw itself: a practised topic's result is ``u < P(perform)`` with :func:`memory.perform`'s formula; an
  unpractised topic's first attempt reads AD's predictive either way.
* The numeric policy passes the switch only at the batch's tag with it on (every rollout of a decision or none), and
  only then does the trace name the draw (``versions.review_draw``).
"""

from __future__ import annotations

import hashlib

import numpy as np
import pytest

from learnloop.router_objective import memory as M
from learnloop.router_objective import price as P
from learnloop.router_objective import value as V
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS, retrievability_array

# -- R1's probe ------------------------------------------------------------------------------------------

PROBE_CASES = ((-0.5, 40.0), (0.5, 40.0), (1.5, 40.0), (0.5, 2.0), (1.5, 2.0))

#: G(0), G(30), G(40) per case on the pre-fix source (mvp-0.49's draw): the marginal gain at m̄ is negative in
#: every case at these 64 draws (item 7's finding, reproduced here).
PROBE_BEFORE = {
    (-0.5, 40.0): (13.687576781601404, 13.694478817505939, 13.692286865132617),
    (0.5, 40.0): (13.791721864277037, 13.789375616770158, 13.784707737296825),
    (1.5, 40.0): (13.883109477665858, 13.889132411503937, 13.871376530574057),
    (0.5, 2.0): (13.775257693316622, 13.776940321393417, 13.773520836863819),
    (1.5, 2.0): (13.861678480037368, 13.870806988119881, 13.849218281547419),
}

#: The same with the memory model's own review draw (this commit).
PROBE_AFTER = {
    (-0.5, 40.0): (12.970901411031356, 12.959352448756242, 12.955470959431057),
    (0.5, 40.0): (12.91474611654659, 12.913265745241336, 12.904191046385579),
    (1.5, 40.0): (12.856996079842917, 12.83587477323545, 12.840217009591768),
    (0.5, 2.0): (12.808036339482218, 12.827275424806658, 12.822843211255606),
    (1.5, 2.0): (12.718919547475167, 12.713073503403223, 12.716977556897026),
}

#: κ0's seed from each curve after the fix (``price.seed_from_gain`` with no earlier positive value): how it was
#: set, and whether it is positive. The day's seed (the marginal gain at m̄) is positive in the two η 1.5 cases, a
#: value §8.6's floor would keep; the others fall to the tail's average, positive only at η 0.5, S 2.
SEED_AFTER = {
    (-0.5, 40.0): (P.TAIL_AVERAGE, False), (0.5, 40.0): (P.TAIL_AVERAGE, False), (1.5, 40.0): (P.DAY_SEED, True),
    (0.5, 2.0): (P.TAIL_AVERAGE, True), (1.5, 2.0): (P.DAY_SEED, True),
}


def _probe_inputs(eta: float, stability: float) -> V.Inputs:
    topics = tuple(V.Topic(lo=f"lo{i}", eta_mean=eta, eta_var=0.3, practiced=True, difficulty=5.0, stability=stability,
                           elapsed_days=1.0, undated_density=1 / 90) for i in range(8))
    return V.Inputs(topics=topics, dated=(), session_minutes=0.0, price=V.Price(kappa0=0.0, remembered=30.0),
                    tail_block_minutes=10.0, tail_block_items=3, horizon_days=90.0,
                    fsrs_weights=tuple(FSRS6_DEFAULT_WEIGHTS))


def _probe(case: tuple[float, float], **kwargs) -> tuple[float, float, float]:
    curve = V.gain(_probe_inputs(*case), [0.0, 30.0, 40.0], draws=64, seed="k", **kwargs)
    return curve[0.0], curve[30.0], curve[40.0]


@pytest.mark.parametrize("case", PROBE_CASES)
def test_the_probe_with_the_switch_off_is_the_pre_fix_source_exactly(case):
    before = PROBE_BEFORE[case]
    assert _probe(case) == before
    assert _probe(case, consistent_review_draw=False) == before
    assert (before[2] - before[1]) / 10.0 < 0  # item 7's finding at these draws


@pytest.mark.parametrize("case", PROBE_CASES)
def test_the_probe_after_the_fix_pins_its_numbers_and_the_seed(case):
    after = _probe(case, consistent_review_draw=True)
    assert after == pytest.approx(PROBE_AFTER[case], rel=1e-12, abs=0.0)
    curve = dict(zip((0.0, 30.0, 40.0), after, strict=True))
    kappa0, how = P.seed_from_gain(curve, remembered=30.0, block_minutes=10.0, last_positive=None)
    assert (how, kappa0 > 0) == SEED_AFTER[case]


# -- the switch off: mvp-0.49's draw for draw ----------------------------------------------------------------


def _inputs(n: int, *, dated: tuple = ()) -> V.Inputs:
    rng = np.random.default_rng(0)
    topics = tuple(V.Topic(lo=f"lo{i}", eta_mean=float(rng.normal(0, 1)), eta_var=0.5, practiced=bool(i % 3),
                           difficulty=float(rng.uniform(2, 8)), stability=float(rng.uniform(1, 20)) if i % 3 else 0.0,
                           elapsed_days=float(rng.uniform(0, 10)) if i % 3 else 0.0, undated_density=1 / 90,
                           reading_count=float(i % 2)) for i in range(n))
    return V.Inputs(topics=topics, dated=dated, session_minutes=5.0, price=V.Price(kappa0=0.0003, remembered=30.0),
                    tail_block_minutes=10.0, tail_block_items=3, horizon_days=90.0,
                    fsrs_weights=tuple(FSRS6_DEFAULT_WEIGHTS), return_gaps_days=(1.0, 2.0, 1.0))


def _actions(n: int) -> list[V.Action]:
    lo = [f"lo{i}" for i in range(n)]
    return [V.Action(ref="stop_for_today", kind=V.STOP),
            V.Action(ref="a", kind=V.REVIEW, item_los=tuple(lo[1:4]), minutes=10.0, minutes_log_sd=0.3),
            V.Action(ref="b", kind=V.NEW_PRACTICE, item_los=(lo[0],), minutes=8.0),
            V.Action(ref="c", kind=V.PROBE, item_los=(lo[-1],), minutes=4.0,
                     repair=V.Action(ref="c:repair", kind=V.REPAIR, item_los=(lo[-1],), minutes=4.0)),
            V.Action(ref="d", kind=V.READING, item_los=(lo[min(2, n - 1)],), minutes=12.0)]


#: sha256 of every candidate's and the reference's Q draws with the baselines, on the pre-fix source.
DECISIONS = {
    "copy_shaped_22_topics": (dict(n=22), "30ecb2616332b86d4a84252a5f7a2741e2c0669527cbb0c0ae0e67014a3fb5cd"),
    "fewer_topics_than_slots": (dict(n=4), "b6e0fe3605ce5a3d3cd2218a6de2366d30203a7a2c642063bb56ab42f62b1636"),
    "a_dated_use_inside_the_horizon": (
        dict(n=22, dated=(V.DatedUse("g", "lo1", 20.3, 1.0), V.DatedUse("g", "lo5", 3.01, 2.0))),
        "a091e5b7bdabe4af21052b93e6d1fcc137da5ed871e996b9b70c8771e59972b1"),
}


def _digest(n: int, dated: tuple = (), **kwargs) -> str:
    evaluation = V.evaluate(_inputs(n, dated=dated), _actions(n), draws=8, seed="s", **kwargs)
    rows = [(row.ref, row.q_draws) for row in evaluation.valued] + [("ref", evaluation.reference.q_draws)]
    base = V.baselines(_inputs(n, dated=dated), 14, draws=8, seed="s", **kwargs)
    payload = (rows, sorted(base["topics"].items()), sorted(base["dated"].items()))
    return hashlib.sha256(repr(payload).encode()).hexdigest()


@pytest.mark.parametrize("case", sorted(DECISIONS))
def test_with_the_switch_off_every_draw_is_the_pre_fix_sources(case):
    spec, pinned = DECISIONS[case]
    assert _digest(**spec) == pinned
    assert _digest(**spec, consistent_review_draw=False) == pinned
    # with it on, the values move (this decision has practised topics the tail reviews)
    assert _digest(**spec, consistent_review_draw=True) != pinned


# -- the draw ------------------------------------------------------------------------------------------------


def test_a_practised_topics_outcome_is_drawn_from_the_memory_models_own_p_perform():
    inputs = _inputs(6)
    model = V._Model(inputs, 512, "draw", consistent_review_draw=True)
    state = model.initial()
    k = model.k
    rng = np.random.default_rng(11)
    u = rng.random(k)
    at = np.full(k, 0.0)
    for lo in range(model.n):
        elapsed = at - state.last[:, lo]
        good, bel, var = model._graded(state.eta[:, lo], state.bel[:, lo], state.bel_var[:, lo], state.s[:, lo],
                                       state.practiced[:, lo], elapsed, model.theta.coef, u)
        r = retrievability_array(state.s[:, lo], elapsed, model.fsrs.weights)
        practiced = state.practiced[:, lo]
        expected = M.perform(model.theta.coef, state.eta[:, lo][:, None], r[:, None], practiced[:, None])[:, 0]
        expected = np.where(practiced, expected, M.sigmoid(state.eta[:, lo]))
        assert np.array_equal(good, u < expected), lo
        # The belief's one-step Laplace update under the same likelihood (slope aA − aR in η when practised).
        a0, a_eta, a_r = (model.theta.coef[:, j] for j in range(3))
        lr = M.logit(r)
        p_bel = np.where(practiced, M.sigmoid(a0 + a_eta * state.bel[:, lo] + a_r * (lr - state.bel[:, lo])),
                         M.sigmoid(state.bel[:, lo]))
        slope = np.where(practiced, a_eta - a_r, 1.0)
        want_var = 1.0 / (1.0 / state.bel_var[:, lo] + slope ** 2 * p_bel * (1 - p_bel))
        assert np.allclose(var, want_var, rtol=1e-12, atol=0.0)
        assert np.allclose(bel, state.bel[:, lo] + want_var * slope * (good - p_bel), rtol=1e-12, atol=1e-15)
    off = V._Model(inputs, 512, "draw")
    state = off.initial()
    for lo in range(off.n):
        good, _bel, _var = off._graded(state.eta[:, lo], state.bel[:, lo], state.bel_var[:, lo], state.s[:, lo],
                                       state.practiced[:, lo], at - state.last[:, lo], off.theta.coef, u)
        assert np.array_equal(good, u < M.sigmoid(state.eta[:, lo])), lo


def test_a_review_right_after_a_review_is_almost_never_a_lapse_with_the_switch_on():
    """The mechanism of item 7: a session with more slots than topics practises a topic again minutes later, where
    ``R ≈ 1``. AD's predictive alone calls a share of those lapses whatever ``R`` is; the memory model expects them
    far less often at the combiner's prior (``aR`` 0.5 on ``logit R``)."""

    inputs = V.Inputs(topics=(V.Topic(lo="x", eta_mean=0.0, eta_var=1e-9, practiced=True, difficulty=5.0,
                                      stability=40.0, elapsed_days=0.0),),
                      dated=(), session_minutes=0.0, price=V.Price(kappa0=0.0, remembered=30.0),
                      tail_block_minutes=10.0, tail_block_items=3, horizon_days=10.0,
                      fsrs_weights=tuple(FSRS6_DEFAULT_WEIGHTS),
                      combiner=M.Combiner(variance=(1e-12, 1e-12, 1e-12)))
    u = np.random.default_rng(5).random(4096)
    shares = {}
    for on in (False, True):
        model = V._Model(inputs, 4096, "lapse", consistent_review_draw=on)
        state = model.initial()
        elapsed = np.full(model.k, 10.0 / V.MINUTES_PER_DAY)
        good, _bel, _var = model._graded(state.eta[:, 0], state.bel[:, 0], state.bel_var[:, 0], state.s[:, 0],
                                         state.practiced[:, 0], elapsed, model.theta.coef, u)
        shares[on] = 1.0 - float(good.mean())
    assert shares[False] == pytest.approx(0.5, abs=0.03)
    assert shares[True] < 0.02, shares


# -- the numeric policy ----------------------------------------------------------------------------------------


@pytest.mark.parametrize("version,switch,expected", [
    ("tag", True, True), ("tag", False, False), ("below", True, False)])
def test_the_numeric_policy_draws_consistently_only_at_the_tag_with_its_switch(tmp_path, monkeypatch, version, switch,
                                                                               expected):
    from learnloop.algorithm_versions import ROUTER_FOLLOWUPS_ALGORITHM_VERSION, ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
    from learnloop.daily_plan import objective_chooser as OC
    from learnloop.db.stores import router_objective as store

    from tests.router_mixture_helpers import mixture_env, run
    from tests.router_model_fakes import block_drawing_seed, fake_runtime

    seen: dict[str, list[bool]] = {"evaluate": [], "baselines": [], "gain": []}
    for name in seen:
        real = getattr(V, name)

        def spy(*args, _real=real, _name=name, **kwargs):
            seen[_name].append(bool(kwargs.get("consistent_review_draw", False)))
            return _real(*args, **kwargs)

        monkeypatch.setattr(OC.V, name, spy)
    tag = ROUTER_FOLLOWUPS_ALGORITHM_VERSION if version == "tag" else ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
    env = mixture_env(tmp_path, fake_runtime(seed=block_drawing_seed()), version=tag,
                      toml=f"[router_objective]\nconsistent_review_draw = {'true' if switch else 'false'}\n")
    run(env, steps=4)
    assert seen["evaluate"] and seen["baselines"] and seen["gain"], {k: len(v) for k, v in seen.items()}
    assert all(flag is expected for calls in seen.values() for flag in calls), seen
    with env.repository.connection() as connection:
        traces = [store.trace(connection, row["decision_id"]) for row in store.traces(connection)]
    blocks = [entry["trace"] for entry in traces if entry["decision_kind"] == "plan_block"]
    assert blocks
    for trace in blocks:
        if expected:
            assert trace["versions"]["review_draw"] == V.REVIEW_DRAW_VERSION
        else:
            assert "review_draw" not in trace["versions"]
