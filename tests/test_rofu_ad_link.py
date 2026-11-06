"""The follow-up batch's landing ruling R9: where the rollouts read AD's predicted success, AD's own ``F(η)``.

AD predicts success as ``F(η) = g + (1 − g − λ)·E_ε[σ(η − a·τ0·ε)]`` (``adaptive_difficulty.model.residual_success``;
lapse ``λ`` 0.02, so ``F`` tops out at 0.98), on its latent ability, to which practice adds ``γ``. mvp-0.49's
rollouts read ``σ(η)`` on ``η = logit p̄``. At the batch's tag with ``[router_objective] ad_predictive_link``
(``value.AdLink``): the decision's ``p̄`` enters as ``F⁻¹(p̄)``, so practice's ``γ`` adds where AD adds it; an
unpractised topic's attempt and a probe read ``F(η)``; the combiner's ``η`` input (``logit p̄``) is ``logit F(η)``;
the belief's Laplace step uses the same prediction and its slope. Off, or below the tag, mvp-0.49's ``σ``. Fakes only.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from learnloop.adaptive_difficulty import model as ADM
from learnloop.adaptive_difficulty import priors as ADP
from learnloop.algorithm_versions import ROUTER_FOLLOWUPS_ALGORITHM_VERSION, ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
from learnloop.router_objective import memory as M
from learnloop.router_objective import value as V
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS

LINK = V.AdLink(lapse=ADP.LAPSE, spread=ADP.A * ADP.TAU0, nodes=tuple(ADM.X32), weights=tuple(ADM.W32))


def test_the_link_is_ads_own_predictive_and_inverts_it():
    grid = np.linspace(-10, 45, 111)
    assert np.allclose(LINK.p(grid), ADM.residual_success(grid), rtol=0.0, atol=1e-15)
    assert float(LINK.p(np.array([45.0]))[0]) <= 1.0 - ADP.LAPSE  # bounded where σ(45) is not
    inside = np.linspace(-8, 8, 33)
    assert np.allclose(LINK.inverse(LINK.p(inside)), inside, atol=1e-9)
    h = 1e-6
    assert np.allclose(LINK.slope(inside), (LINK.p(inside + h) - LINK.p(inside - h)) / (2 * h), atol=1e-8)


def _inputs(*, link: V.AdLink | None, practiced: bool = False) -> V.Inputs:
    topics = tuple(V.Topic(lo=f"lo{i}", eta_mean=float(m), eta_var=0.2, practiced=practiced, difficulty=5.0,
                           stability=10.0 if practiced else 0.0, elapsed_days=2.0 if practiced else 0.0,
                           undated_density=1 / 90) for i, m in enumerate((-1.0, 0.3, 1.2, 2.5)))
    return V.Inputs(topics=topics, dated=(), session_minutes=0.0, price=V.Price(kappa0=0.0, remembered=30.0),
                    tail_block_minutes=10.0, tail_block_items=3, horizon_days=10.0,
                    fsrs_weights=tuple(FSRS6_DEFAULT_WEIGHTS), ad_link=link)


def test_a_decisions_p_bar_enters_as_ads_latent_and_reads_back_as_itself():
    inputs = _inputs(link=LINK)
    model = V._Model(inputs, 16, "link")
    p_bar = M.sigmoid(np.array([t.eta_mean for t in inputs.topics]))
    # R10: the variance-integrated predictive at the model's latent mean and variance is p̄
    assert np.allclose(LINK.p_integrated(np.array(model.eta_means), np.array(model.eta_vars)), p_bar, atol=1e-10)
    # with no variance, the combiner at its prior mean (a0 0, aA 1) on an unpractised topic reads AD's predictive
    # alone at the point: F(η) = p̄
    sharp = replace(inputs, topics=tuple(replace(t, eta_var=0.0) for t in inputs.topics),
                    combiner=M.Combiner().at_mean())
    believed = V._Model(sharp, 16, "link")
    assert np.allclose(LINK.p(np.array(believed.eta_means)), p_bar, atol=1e-10)
    assert np.allclose(believed.performance(believed.initial(), 0.0, belief=True), p_bar[None, :], atol=1e-10)


@pytest.mark.parametrize("consistent", [False, True])
def test_an_unpractised_attempt_and_a_probe_are_drawn_from_ads_own_predictive(consistent):
    model = V._Model(_inputs(link=LINK), 4096, "draw", consistent_review_draw=consistent)
    state = model.initial()
    u = np.random.default_rng(7).random(model.k)
    for lo in range(model.n):
        good, _bel, _var = model._graded(state.eta[:, lo], state.bel[:, lo], state.bel_var[:, lo], state.s[:, lo],
                                         state.practiced[:, lo], np.zeros(model.k), model.theta.coef, u)
        assert np.array_equal(good, u < LINK.p(state.eta[:, lo])), lo
        probe_state = state.copy()
        seen = model._observe(probe_state, lo, u, np.ones(model.k, dtype=bool))
        assert np.array_equal(seen, u < LINK.p(state.eta[:, lo])), lo


def test_the_beliefs_step_is_the_laplace_step_under_ads_predictive():
    model = V._Model(_inputs(link=LINK), 256, "belief")
    state = model.initial()
    u = np.random.default_rng(8).random(model.k)
    lo = 2
    good, bel, var = model._graded(state.eta[:, lo], state.bel[:, lo], state.bel_var[:, lo], state.s[:, lo],
                                   state.practiced[:, lo], np.zeros(model.k), model.theta.coef, u)
    b = state.bel[:, lo]
    p, dp = LINK.p(b), LINK.slope(b)
    info = dp ** 2 / (p * (1 - p))
    want_var = 1.0 / (1.0 / state.bel_var[:, lo] + info)
    assert np.allclose(var, want_var, rtol=1e-10)
    assert np.allclose(bel, b + want_var * dp / (p * (1 - p)) * (good - p), rtol=1e-10, atol=1e-12)


def test_without_the_link_the_rollouts_are_mvp049s_bitwise():
    for practiced in (False, True):
        a = V.evaluate(_inputs(link=None, practiced=practiced),
                       [V.Action(ref="stop_for_today", kind=V.STOP),
                        V.Action(ref="p", kind=V.PROBE, item_los=("lo1",), minutes=4.0)], draws=8, seed="s")
        model = V._Model(_inputs(link=None, practiced=practiced), 8, "s")
        assert model.eta_means == [t.eta_mean for t in _inputs(link=None).topics]
        assert a.complete


# -- R1's probe: R1's draw and R6's combiner, σ (before) and AD's F (after) ---------------------------------------

PROBE_CASES = ((-0.5, 40.0), (0.5, 40.0), (1.5, 40.0), (0.5, 2.0), (1.5, 2.0))

#: G(0), G(30), G(40) per case with AD's F; the σ side is test_rofu_monotone's "monotone" pins. Moved by landing
#: ruling R10 (the latent mean is the variance-integrated inverse: η's variance is 0.3 here); R9's own values are in
#: its commit 8a19c2698b and the review record.
PROBE_AFTER = {
    64: {(-0.5, 40.0): (14.93333931874283, 14.95244338284236, 14.955931650899817),
         (0.5, 40.0): (15.060551132781987, 15.074471158417024, 15.08039999738742),
         (1.5, 40.0): (15.142255555818418, 15.152633328578993, 15.155520510015782),
         (0.5, 2.0): (15.01139033677842, 15.035324623431599, 15.037341906877352),
         (1.5, 2.0): (15.098567420654335, 15.115735146532781, 15.119170677356228)},
    512: {(-0.5, 40.0): (14.873997865626462, 14.89102602822088, 14.894582514783757),
          (0.5, 40.0): (15.014200142630242, 15.027989654568888, 15.032036879723488),
          (1.5, 40.0): (15.109772159625608, 15.121911257751687, 15.124715750252323),
          (0.5, 2.0): (14.959923288620274, 14.978412179794862, 14.982492745241842),
          (1.5, 2.0): (15.063988344635199, 15.077597114406466, 15.08071502466796)},
}


@pytest.mark.parametrize("draws", sorted(PROBE_AFTER))
def test_the_probe_with_ads_own_predictive_is_pinned(draws):
    for eta, stability in PROBE_CASES:
        topics = tuple(V.Topic(lo=f"lo{i}", eta_mean=eta, eta_var=0.3, practiced=True, difficulty=5.0,
                               stability=stability, elapsed_days=1.0, undated_density=1 / 90) for i in range(8))
        inputs = V.Inputs(topics=topics, dated=(), session_minutes=0.0, price=V.Price(kappa0=0.0, remembered=30.0),
                          tail_block_minutes=10.0, tail_block_items=3, horizon_days=90.0,
                          fsrs_weights=tuple(FSRS6_DEFAULT_WEIGHTS), combiner=M.monotone_prior(), ad_link=LINK)
        curve = V.gain(inputs, [0.0, 30.0, 40.0], draws=draws, seed="k", consistent_review_draw=True)
        got = (curve[0.0], curve[30.0], curve[40.0])
        assert got == pytest.approx(PROBE_AFTER[draws][(eta, stability)], rel=1e-12, abs=0.0), (eta, stability)


# -- serving -------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("version,switch,expected", [(ROUTER_FOLLOWUPS_ALGORITHM_VERSION, True, True),
                                                     (ROUTER_FOLLOWUPS_ALGORITHM_VERSION, False, False),
                                                     (ROUTER_LEARNED_TAIL_ALGORITHM_VERSION, True, False)])
def test_the_numeric_policy_reads_ads_own_predictive_only_at_the_tag_with_its_switch(tmp_path, monkeypatch, version,
                                                                                      switch, expected):
    from learnloop.daily_plan import objective_chooser as OC
    from learnloop.db.stores import router_objective as store

    from tests.router_mixture_helpers import mixture_env, run
    from tests.router_model_fakes import block_drawing_seed, fake_runtime

    seen: list[bool] = []
    real = V.evaluate

    def spy(inputs, *args, **kwargs):
        seen.append(inputs.ad_link is not None)
        return real(inputs, *args, **kwargs)

    monkeypatch.setattr(OC.V, "evaluate", spy)
    env = mixture_env(tmp_path, fake_runtime(seed=block_drawing_seed()), version=version,
                      toml=f"[router_objective]\nad_predictive_link = {'true' if switch else 'false'}\n")
    run(env, steps=4)
    assert seen and all(flag is expected for flag in seen), seen
    with env.repository.connection() as connection:
        traces = [store.trace(connection, row["decision_id"]) for row in store.traces(connection)]
    blocks = [entry["trace"] for entry in traces if entry["decision_kind"] == "plan_block"]
    assert blocks
    for trace in blocks:
        assert (trace["versions"].get("ad_link") == V.AD_LINK_VERSION) is expected
