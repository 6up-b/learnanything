"""The follow-up batch's landing ruling R11: AD's probabilities are drawn from directly, and the combiner reads a
numerically stable probability-logit of its own.

R9's ``logit_and_slope`` reused ``memory.logit``, FSRS's retrievability logit, which floors a probability at 1e-4:
``σ`` of it is not ``F`` near zero, while the returned derivative described the unclipped ``F`` (Codex's N2). Codex's
reproduction: an unpractised topic at ``η = −14`` (``F = 1.34e-6``), the combiner at its prior mean, ``u = 5e-5``:
the graded attempt succeeded, the probe failed, and the forecast read 1e-4. Now an unpractised attempt and a probe
draw from ``F`` itself, the combiner's input is a log-space logit of ``F`` with the matching derivative, and FSRS's
retrievability keeps its own clip. Fakes only.
"""

from __future__ import annotations

import numpy as np
import pytest

from learnloop.adaptive_difficulty import model as ADM
from learnloop.adaptive_difficulty import priors as ADP
from learnloop.router_objective import memory as M
from learnloop.router_objective import value as V
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS

LINK = V.AdLink(lapse=ADP.LAPSE, spread=ADP.A * ADP.TAU0, nodes=tuple(ADM.X32), weights=tuple(ADM.W32))


def _model(consistent: bool) -> V._Model:
    topic = V.Topic(lo="x", eta_mean=0.0, eta_var=0.0, eta_latent=(-14.0, 0.0))
    inputs = V.Inputs(topics=(topic,), dated=(), session_minutes=0.0, price=V.Price(kappa0=0.0, remembered=30.0),
                      tail_block_minutes=10.0, tail_block_items=3, horizon_days=10.0,
                      fsrs_weights=tuple(FSRS6_DEFAULT_WEIGHTS), ad_link=LINK, combiner=M.Combiner().at_mean())
    return V._Model(inputs, 4, "stable", consistent_review_draw=consistent)


@pytest.mark.parametrize("consistent", [False, True])
def test_codexs_case_gives_one_outcome_on_every_path_all_at_f(consistent):
    model = _model(consistent)
    state = model.initial()
    f = float(ADM.residual_success(np.array(-14.0)))
    assert f == pytest.approx(1.3435349e-6, rel=1e-6)
    assert np.allclose(state.eta[:, 0], -14.0) and np.allclose(state.bel[:, 0], -14.0)
    u = np.full(model.k, 5e-5)
    good, _bel, _var = model._graded(state.eta[:, 0], state.bel[:, 0], state.bel_var[:, 0], state.s[:, 0],
                                     state.practiced[:, 0], np.zeros(model.k), model.theta.coef, u)
    seen = model._observe(state.copy(), 0, u, np.ones(model.k, dtype=bool))
    forecast = model.performance(state, 0.0)[:, 0]
    believed = model.performance(state, 0.0, belief=True)[:, 0]
    assert not good.any() and not seen.any()
    assert np.allclose(forecast, f, rtol=1e-9, atol=0.0) and np.allclose(believed, f, rtol=1e-9, atol=0.0)


def test_the_logit_is_stable_and_its_slope_matches_the_transformation():
    grid = np.concatenate([np.linspace(-40, -10, 31), np.linspace(-6, 6, 25), np.linspace(10, 60, 11)])
    logit_f, slope = LINK.logit_and_slope(grid)
    f = ADM.residual_success(grid)
    assert np.all(np.isfinite(logit_f)) and np.all(np.isfinite(slope))
    assert np.allclose(M.sigmoid(logit_f), f, rtol=1e-9, atol=0.0)
    assert np.allclose(LINK.logit_p(grid), logit_f, rtol=0.0, atol=1e-12)
    # the derivative of the logit actually applied (central differences of logit F itself)
    h = 1e-5
    numeric = (LINK.logit_and_slope(grid + h)[0] - LINK.logit_and_slope(grid - h)[0]) / (2 * h)
    assert np.allclose(slope, numeric, rtol=1e-5, atol=1e-9)
    # FSRS's own logit still clips (its retrievability's numerical floor is FSRS's)
    assert float(M.logit(np.array(1e-9))) == pytest.approx(float(M.logit(np.array(1e-4))))
