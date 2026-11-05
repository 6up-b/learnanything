"""Router objective RO6 §10, the pure parts: the features, the fitted Q evaluation, ``ŵ`` and the cross-check.

* **A planted residual is recovered** on synthetic trajectories whose rewards satisfy the logger's Bellman equation
  with ``Q̂ = Q_tail + ρ*``: the fit's contrasts between candidates match ``ρ*``'s;
* with no transition the fit is its prior (a zero residual);
* **ŵ stays at zero with no randomized contrast** and **moves toward the planted slope with them**; a residual that
  predicts nothing leaves it near zero; a window still open never enters it (no peeking);
* the partial-history weights are one at the logger and estimate zero there.

Numbers only; no vault, no model.
"""

from __future__ import annotations

import math
import random

import numpy as np
import pytest

from learnloop.router_objective import learned_tail as LT


def _phi(rng: random.Random) -> tuple[float, ...]:
    return tuple(rng.gauss(0.0, 1.0) for _ in LT.NAMES)


def _planted(rng: random.Random) -> np.ndarray:
    return np.asarray([rng.choice([-1.0, 1.0]) * rng.uniform(0.004, 0.02) for _ in LT.NAMES])


def _trajectory(n: int, theta: np.ndarray, *, noise: float, seed: int = 7, generator: str = "g") -> list[LT.Transition]:
    """Transitions of a logger whose value is ``Q_tail + θᵀφ``: the reward closes the Bellman equation exactly, up to
    ``noise``, whatever the tail's own values are."""

    rng = random.Random(seed)
    out = []
    for i in range(n):
        phi, nxt = _phi(rng), _phi(rng)
        q_taken = rng.uniform(1.0, 3.0)
        next_v = rng.uniform(1.0, 3.0)
        rho, rho_next = float(np.dot(theta, phi)), float(np.dot(theta, nxt))
        reward = (q_taken + rho) - (next_v + rho_next) + rng.gauss(0.0, noise)
        out.append(LT.Transition(decision_id=f"d{i}", generator=generator, decided_at=f"2026-11-{1 + i % 28:02d}T10:00:00Z",
                                 phi=phi, next_phi=nxt, reward=reward, q_taken=q_taken, next_v_tail=next_v))
    return out


def test_a_planted_residual_is_recovered_on_synthetic_trajectories():
    rng = random.Random(3)
    theta = _planted(rng)
    fit = LT.fit(_trajectory(4000, theta, noise=0.002), prior_sd=0.01, generator="g")
    assert fit.n == 4000 and fit.source == "fqe_fixed_point_with_prior" and fit.generator == "g"
    pairs = [(_phi(rng), _phi(rng)) for _ in range(200)]
    planted = [float(np.dot(theta, a) - np.dot(theta, b)) for a, b in pairs]
    fitted = [fit.value(a) - fit.value(b) for a, b in pairs]
    assert np.corrcoef(planted, fitted)[0, 1] > 0.99
    assert np.max(np.abs(np.asarray(planted) - np.asarray(fitted))) < 0.01
    # The coefficients on the raw scale are θ (the fit standardizes; dividing back recovers them).
    raw = np.asarray(fit.coef) / np.asarray(fit.sd)
    assert np.allclose(raw, theta, atol=2e-3)


def test_the_prior_shrinks_a_short_noisy_trajectory_toward_no_residual():
    rng = random.Random(5)
    theta = _planted(rng)
    short = LT.fit(_trajectory(12, theta, noise=0.5), prior_sd=0.01)
    assert max(abs(c) for c in short.coef) < 0.02
    assert LT.fit([], prior_sd=0.01).coef == (0.0,) * len(LT.NAMES)
    assert LT.prior_fit(0.01).value(_phi(rng)) == 0.0


def test_the_fit_round_trips_through_its_trace_record():
    fit = LT.fit(_trajectory(200, _planted(random.Random(1)), noise=0.01), prior_sd=0.01, generator="g")
    again = LT.Fit.from_dict(fit.as_dict())
    phi = _phi(random.Random(2))
    assert again.value(phi) == pytest.approx(fit.value(phi))


def test_the_features_are_numbers_from_the_belief_and_the_candidate():
    topic = LT.TopicNumbers(eta=0.4, eta_var=0.3, practiced=True, stability=4.0, elapsed_days=2.0)
    belief = LT.belief(session_minutes=10.0, remembered=20.0, nearest_goal_days=9.0, horizon_days=90.0,
                       pending_reports=3, mastery=[(0.0, 0.5), (1.0, 0.1)], topics=[topic])
    assert belief.session_load == 0.5 and belief.days_to_go == pytest.approx(math.exp(-0.1))
    assert belief.pending_reports == pytest.approx(math.log(4)) and belief.mastery_var == pytest.approx(0.3)
    block = LT.vector(belief, LT.ActionView("b", "review", 5.0, (topic,)), remembered=20.0)
    stop = LT.vector(belief, LT.ActionView("s", "stop", 0.0, ()), remembered=20.0)
    named = dict(zip(LT.NAMES, block))
    assert named["minutes"] == 0.25 and named["topic_lag"] == pytest.approx(math.log1p(0.5)) and named["stop"] == 0.0
    assert named["minutes_x_load"] == pytest.approx(0.125)
    assert dict(zip(LT.NAMES, stop))["stop_x_load"] == 0.5 and dict(zip(LT.NAMES, stop))["topic_p"] == 0.0
    # With no mastery recorded the decision's frozen belief numbers stand in.
    fallback = LT.belief(session_minutes=0.0, remembered=20.0, nearest_goal_days=None, horizon_days=90.0,
                         pending_reports=None, mastery=[], topics=[topic])
    assert fallback.mastery_var == pytest.approx(0.3) and fallback.days_to_go == 0.0


# -- ŵ --------------------------------------------------------------------------------------------------


def _contrasts(n: int, slope: float, *, noise: float, rate: float = 0.05, seed: int = 11) -> list[LT.Contrast]:
    """Stop-coin decisions: arms at (p, p, 1 − 2p); the realized contrast the coin's IPW of a return whose arm
    difference is ``ΔV_tail_true + slope·ΔV_residual``."""

    rng = random.Random(seed)
    out = []
    for i in range(n):
        tail, residual = rng.gauss(0.0, 0.01), rng.gauss(0.0, 0.01)
        effect = 0.5 * tail + slope * residual
        u = rng.random()
        arm = "offer_stop" if u < rate else ("present_next" if u < 2 * rate else "policy")
        base = rng.gauss(0.0, noise)
        value = base + (effect / 2 if arm == "offer_stop" else -effect / 2 if arm == "present_next" else 0.0)
        out.append(LT.Contrast(decision_id=f"c{i}", decided_at="2026-10-01T10:00:00Z",
                               window_closes_at="2026-10-15T10:00:00Z",
                               realized=LT.coin_contrast(arm, rate) * value, tail=tail, residual=residual,
                               forced=arm != "policy", forced_probability=2 * rate))
    return out


def test_w_hat_is_zero_with_no_randomized_contrast():
    fit = LT.residual_weight([], prior_sd=1.0, at="2026-11-05T00:00:00Z")
    assert fit.w_hat == 0.0 and fit.n == 0 and fit.source.startswith("prior")


def test_w_hat_moves_toward_the_planted_slope_with_randomized_contrasts():
    few = LT.residual_weight(_contrasts(200, 0.6, noise=0.001), prior_sd=1.0, at="2026-11-05T00:00:00Z")
    many = LT.residual_weight(_contrasts(40000, 0.6, noise=0.001), prior_sd=1.0, at="2026-11-05T00:00:00Z")
    assert 0.0 <= few.w_hat <= 1.0
    assert abs(many.w_hat - 0.6) < 0.1 and many.p_rank > 0.99 and many.rank is not None and many.rank > 0
    assert abs(many.w_hat - 0.6) <= abs(few.w_hat - 0.6) + 1e-9
    assert many.tail_slope == pytest.approx(0.5, abs=0.1)


def test_a_residual_that_predicts_nothing_keeps_w_hat_near_zero():
    null = LT.residual_weight(_contrasts(40000, 0.0, noise=0.001), prior_sd=1.0, at="2026-11-05T00:00:00Z")
    assert null.w_hat < 0.1


def test_w_hat_reads_no_window_still_open_at_the_decision():
    rows = _contrasts(500, 0.6, noise=0.001)
    assert LT.residual_weight(rows, prior_sd=1.0, at="2026-10-15T10:00:00Z").n == 0  # closes at, not before
    assert LT.residual_weight(rows, prior_sd=1.0, at="2026-10-15T10:00:01Z").n == 500


def test_the_coin_contrast_and_the_predicted_contrast():
    assert LT.coin_contrast("offer_stop", 0.05) == pytest.approx(20.0)
    assert LT.coin_contrast("present_next", 0.05) == pytest.approx(-20.0)
    assert LT.coin_contrast("policy", 0.05) == 0.0 and LT.coin_contrast("offer_stop", 0.0) == 0.0
    values = {"stop_for_today": 1.0, "a": 2.0, "b": 4.0}
    mu = {"stop_for_today": 0.5, "a": 0.25, "b": 0.25}
    assert LT.predicted_contrast(values, mu, "stop_for_today") == pytest.approx(1.0 - 3.0)
    assert LT.predicted_contrast({"a": 1.0}, mu, "stop_for_today") is None


# -- the cross-check ----------------------------------------------------------------------------------------


def test_the_partial_history_weights_are_one_at_the_logger():
    rows = [LT.WeightedRow(decision_id=f"d{i}", decided_at=f"2026-10-{1 + i:02d}T10:00:00Z", ratio=1.0,
                           realized=float(i)) for i in range(20)]
    report = LT.partial_history(rows, window_days=14)
    assert report["one_step"]["estimate"] == 0.0 and report["window"]["estimate"] == 0.0
    assert report["one_step"]["ess"] == pytest.approx(20.0)
    tilted = [LT.WeightedRow(row.decision_id, row.decided_at, 1.5 if i % 2 else 0.5, 1.0) for i, row in enumerate(rows)]
    report = LT.partial_history(tilted, window_days=1)
    assert report["one_step"]["estimate"] == pytest.approx(0.0) and report["one_step"]["ess"] < 20.0
    assert LT.partial_history([], window_days=14)["n"] == 0
