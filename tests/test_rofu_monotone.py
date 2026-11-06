"""The follow-up batch's landing ruling R6: the memory model's combiner is monotone in ability by construction.

``logit P = a0 + aA·η + aR·(logit R − η)·[practiced]`` (``memory.perform``): ``η``'s slope is ``aA`` for an
unpractised topic and ``aA − aR`` for a practised one. RO4's linear prior (independent ``N(·, 0.25)`` on
``(a0, aA, aR)``) put ``aA − aR`` at ``N(0.5, 0.5)``, negative in about 24% of draws, where higher ability predicts
lower performance. At mvp-0.50 (``memory.FORM_MONOTONE``) both slopes are log-normal, moment-matched to the linear
prior's marginals, in the prior and in the fit (``fit_combiner``, the RO5 checks' fit and item 2's trace-fed one);
``aR = aA − b`` is derived. Below the tag the linear combiner is mvp-0.49's exactly. Fakes only.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from learnloop.algorithm_versions import ROUTER_FOLLOWUPS_ALGORITHM_VERSION, ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
from learnloop.router_objective import memory as M
from learnloop.router_objective import value as V
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS


def _slopes(coefficients: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """η's slope for an unpractised topic (``aA``) and a practised one (``aA − aR``)."""

    return coefficients[:, 1], coefficients[:, 1] - coefficients[:, 2]


def test_the_linear_prior_has_negative_slopes_the_monotone_prior_has_none():
    z = np.random.default_rng(0).standard_normal((200_000, 3))
    _unpractised, practised = _slopes(M.Combiner().coefficients(z))
    assert 0.22 < float((practised < 0).mean()) < 0.26  # the defect: Φ(−0.5/√0.5) ≈ 0.24
    unpractised, practised = _slopes(M.monotone_prior().coefficients(z))
    assert (unpractised > 0).all() and (practised > 0).all()
    # Moment-matched to the linear prior's marginals: aA mean 1, variance 0.25; aA − aR mean 0.5, variance 0.5.
    assert unpractised.mean() == pytest.approx(1.0, rel=0.01) and unpractised.var() == pytest.approx(0.25, rel=0.03)
    assert practised.mean() == pytest.approx(0.5, rel=0.01) and practised.var() == pytest.approx(0.5, rel=0.08)


def test_the_linear_form_is_mvp049s_bitwise():
    z = np.random.default_rng(1).standard_normal((64, 3))
    combiner = M.Combiner(mean=(0.1, 0.9, 0.4), variance=(0.2, 0.3, 0.1))
    m = np.array(combiner.mean)
    sd = np.sqrt(np.maximum(np.array(combiner.variance), 0.0))
    assert np.array_equal(combiner.coefficients(z), m[None, :] + sd[None, :] * z)
    assert combiner.at_mean() == M.Combiner(mean=combiner.mean, variance=(0.0, 0.0, 0.0))
    assert "form" not in combiner.as_dict()


def _rows(rng: np.random.Generator, n: int, slope_sign: float) -> list[tuple[float, float | None, int]]:
    """Synthetic (η, R or None, y): outcomes rising with η (``slope_sign`` 1) or, adversarially, falling."""

    rows = []
    for _ in range(n):
        eta = float(rng.normal(0.0, 1.5))
        practiced = rng.random() < 0.6
        r = float(rng.uniform(0.3, 0.99)) if practiced else None
        z = 0.2 + slope_sign * 0.8 * eta + (0.6 * (math.log(r / (1 - r)) - eta) if practiced else 0.0)
        rows.append((eta, r, int(rng.random() < 1 / (1 + math.exp(-z)))))
    return rows


@pytest.mark.parametrize("slope_sign", [1.0, -1.0])
def test_no_draw_of_a_fitted_posterior_has_a_negative_slope(slope_sign):
    rows = _rows(np.random.default_rng(2), 400, slope_sign)
    fitted = M.fit_combiner(rows, prior=M.monotone_prior())
    assert fitted.form == M.FORM_MONOTONE and fitted.n == 400
    assert all(np.isfinite(fitted.mean)) and all(v > 0 for v in fitted.variance)
    unpractised, practised = _slopes(fitted.coefficients(np.random.default_rng(3).standard_normal((100_000, 3))))
    assert (unpractised > 0).all() and (practised > 0).all()
    # the linear fit on the adversarial rows does find a negative slope (what the form now rules out)
    if slope_sign < 0:
        linear = M.fit_combiner(rows)
        assert linear.mean[1] < 0


def test_the_monotone_fit_recovers_rising_slopes_and_is_the_posterior_mode():
    rows = _rows(np.random.default_rng(4), 3000, 1.0)
    fitted = M.fit_combiner(rows, prior=M.monotone_prior())
    point = fitted.at_mean().coefficients(np.zeros((1, 3)))[0]
    # the rows' z is 0.2 + 0.8·η + 0.6·(logit R − η): aA 0.8, aR 0.6 (η's practised slope 0.2, positive)
    assert point[1] == pytest.approx(0.8, abs=0.15) and point[2] == pytest.approx(0.6, abs=0.15)
    # the mode: the log posterior's gradient vanishes there (finite differences on θ)
    eta = np.array([row[0] for row in rows])
    practiced = np.array([row[1] is not None for row in rows])
    r = np.array([row[1] if row[1] is not None else 0.5 for row in rows])
    y = np.array([row[2] for row in rows], dtype=float)
    m0, p0 = np.array(M.MONOTONE_PRIOR_MEAN), 1 / np.array(M.MONOTONE_PRIOR_VARIANCE)

    def log_post(theta: np.ndarray) -> float:
        coef = M.Combiner(mean=tuple(theta), variance=(0.0, 0.0, 0.0), form=M.FORM_MONOTONE).coefficients(
            np.zeros((1, 3)))
        p = M.perform(coef, eta[None, :], r[None, :], practiced[None, :])[0]
        p = np.clip(p, 1e-15, 1 - 1e-15)
        return float(np.sum(y * np.log(p) + (1 - y) * np.log(1 - p)) - 0.5 * np.sum(p0 * (theta - m0) ** 2))

    theta = np.array(fitted.mean)
    for j in range(3):
        step = np.zeros(3)
        step[j] = 1e-5
        assert abs((log_post(theta + step) - log_post(theta - step)) / 2e-5) < 1e-2, j


def test_the_rollouts_on_the_monotone_prior_never_predict_lower_performance_for_higher_ability():
    """``P(perform)`` per draw against η, on every coefficient draw a decision's rollouts use."""

    inputs = V.Inputs(topics=(V.Topic(lo="x", eta_mean=0.0, eta_var=0.0),), dated=(), session_minutes=0.0,
                      price=V.Price(kappa0=0.0, remembered=30.0), tail_block_minutes=10.0, tail_block_items=3,
                      horizon_days=10.0, fsrs_weights=tuple(FSRS6_DEFAULT_WEIGHTS), combiner=M.monotone_prior())
    coef = V._Model(inputs, 4096, "monotone").theta.coef
    grid = np.linspace(-6, 40, 47)
    for practiced, r in ((False, 0.5), (True, 0.2), (True, 0.97)):
        p = np.stack([M.perform(coef, np.full((coef.shape[0], 1), eta), np.full((coef.shape[0], 1), r),
                                np.full((coef.shape[0], 1), practiced))[:, 0] for eta in grid], axis=1)
        assert (np.diff(p, axis=1) >= 0).all(), practiced


# -- R1's probe: before (the linear combiner) and after (monotone), both with R1's draw ------------------------

PROBE_CASES = ((-0.5, 40.0), (0.5, 40.0), (1.5, 40.0), (0.5, 2.0), (1.5, 2.0))

#: G(0), G(30), G(40) per case, R1's review draw: (draws, form) -> case -> values. "linear" is the state before R6.
PROBE = {
    (64, "linear"): {
        (-0.5, 40.0): (12.970901411031356, 12.959352448756242, 12.955470959431057),
        (0.5, 40.0): (12.91474611654659, 12.913265745241336, 12.904191046385579),
        (1.5, 40.0): (12.856996079842917, 12.83587477323545, 12.840217009591768),
        (0.5, 2.0): (12.808036339482218, 12.827275424806658, 12.822843211255606),
        (1.5, 2.0): (12.718919547475167, 12.713073503403223, 12.716977556897026)},
    (64, "monotone"): {
        (-0.5, 40.0): (15.55401249500834, 15.577239132171014, 15.583351191042672),
        (0.5, 40.0): (15.676736890595294, 15.692318858522949, 15.699410676444101),
        (1.5, 40.0): (15.76602972483264, 15.780317121623728, 15.785000389414943),
        (0.5, 2.0): (15.63967006483279, 15.666510131176167, 15.671606338506766),
        (1.5, 2.0): (15.737040693811945, 15.756828986864281, 15.761607977128383)},
    (512, "linear"): {
        (-0.5, 40.0): (13.456210823012427, 13.45720379487454, 13.4586614338836),
        (0.5, 40.0): (13.5017141172477, 13.504196928631206, 13.501586152104466),
        (1.5, 40.0): (13.51032206040782, 13.503165086305037, 13.503891885658582),
        (0.5, 2.0): (13.409944717938275, 13.424911439868833, 13.422703721961629),
        (1.5, 2.0): (13.396272665411548, 13.404996027335356, 13.403138733693858)},
    (512, "monotone"): {
        (-0.5, 40.0): (15.493408364515984, 15.51357226768572, 15.518500862286768),
        (0.5, 40.0): (15.625600240276391, 15.642406763655337, 15.648691065356068),
        (1.5, 40.0): (15.725815790625028, 15.740530418197771, 15.745765416615695),
        (0.5, 2.0): (15.585007663920006, 15.607857063332627, 15.613398149209264),
        (1.5, 2.0): (15.695173736999967, 15.711989980156646, 15.717193089812273)},
}


@pytest.mark.parametrize("draws,form", sorted(PROBE))
def test_the_probe_before_and_after_r6_is_pinned(draws, form):
    for eta, stability in PROBE_CASES:
        topics = tuple(V.Topic(lo=f"lo{i}", eta_mean=eta, eta_var=0.3, practiced=True, difficulty=5.0,
                               stability=stability, elapsed_days=1.0, undated_density=1 / 90) for i in range(8))
        inputs = V.Inputs(topics=topics, dated=(), session_minutes=0.0, price=V.Price(kappa0=0.0, remembered=30.0),
                          tail_block_minutes=10.0, tail_block_items=3, horizon_days=90.0,
                          fsrs_weights=tuple(FSRS6_DEFAULT_WEIGHTS),
                          combiner=M.monotone_prior() if form == "monotone" else M.Combiner())
        curve = V.gain(inputs, [0.0, 30.0, 40.0], draws=draws, seed="k", consistent_review_draw=True)
        got = (curve[0.0], curve[30.0], curve[40.0])
        assert got == pytest.approx(PROBE[(draws, form)][(eta, stability)], rel=1e-12, abs=0.0), (eta, stability)


# -- serving: the tag with [router_objective] monotone_combiner --------------------------------------------------


@pytest.mark.parametrize("version,switch,expected", [(ROUTER_FOLLOWUPS_ALGORITHM_VERSION, True, True),
                                                     (ROUTER_FOLLOWUPS_ALGORITHM_VERSION, False, False),
                                                     (ROUTER_LEARNED_TAIL_ALGORITHM_VERSION, True, False)])
def test_the_numeric_policy_reads_the_monotone_combiner_only_at_the_tag_with_its_switch(tmp_path, version, switch,
                                                                                         expected):
    from learnloop.db.stores import router_objective as store

    from tests.router_mixture_helpers import mixture_env, run
    from tests.router_model_fakes import block_drawing_seed, fake_runtime

    env = mixture_env(tmp_path, fake_runtime(seed=block_drawing_seed()), version=version,
                      toml=f"[router_objective]\nmonotone_combiner = {'true' if switch else 'false'}\n")
    run(env, steps=4)
    with env.repository.connection() as connection:
        traces = [store.trace(connection, row["decision_id"]) for row in store.traces(connection)]
    blocks = [entry["trace"] for entry in traces if entry["decision_kind"] == "plan_block"]
    assert blocks
    for trace in blocks:
        memory = trace["versions"]["memory_model"]
        if expected:
            assert memory["form"] == M.FORM_MONOTONE
            point = memory["coefficients_at_mean"]
            assert point["aA"] > 0 and point["aA"] - point["aR"] > 0
        else:
            assert "form" not in memory and "coefficients_at_mean" not in memory
