"""The follow-up batch's landing ruling R10: the rollouts start from AD's own latent posterior.

AD's ``p̄`` already integrates the latent's epistemic variance (``adaptive_difficulty.model.expected_success``:
``η_e ~ N(m, v + a²τ0²)``). R9 first took the point inverse ``F⁻¹(p̄)`` and then added the decision's variance when
drawing ``η``, applying the uncertainty twice (Codex's N1). Now the rollouts read AD's latent moments where AD holds
them (``decision_state_fields(eta_moments=True)``, read-only), and otherwise invert the variance-integrated
predictive, so the initial rollout predictive is ``p̄`` again. Fakes only.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from learnloop.adaptive_difficulty import model as ADM
from learnloop.adaptive_difficulty import priors as ADP
from learnloop.router_objective import value as V
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS

LINK = V.AdLink(lapse=ADP.LAPSE, spread=ADP.A * ADP.TAU0, nodes=tuple(ADM.X32), weights=tuple(ADM.W32))


def _model(topic: V.Topic) -> V._Model:
    inputs = V.Inputs(topics=(topic,), dated=(), session_minutes=0.0, price=V.Price(kappa0=0.0, remembered=30.0),
                      tail_block_minutes=10.0, tail_block_items=3, horizon_days=10.0,
                      fsrs_weights=tuple(FSRS6_DEFAULT_WEIGHTS), ad_link=LINK)
    return V._Model(inputs, 8, "latent")


def _initial_predictive(model: V._Model) -> float:
    """The rollouts' initial predictive ``E[F(η)]``, ``η`` drawn from the model's own latent mean and variance,
    by AD's Gauss-Hermite rule (quadrature precision, no Monte Carlo: two nested 32-node rules agree with AD's
    one-rule ``expected_success`` to about 2e-7, hence the tolerance)."""

    m, v = model.eta_means[0], model.eta_vars[0]
    return float((ADM.W32 * LINK.p(m + math.sqrt(v) * ADM.X32)).sum())


@pytest.mark.parametrize("mean", [2.0, -2.0])
def test_codexs_reproductions_start_at_ads_p_bar(mean):
    variance = 4.0
    p_bar = float(ADM.expected_success(np.array(mean), np.array(variance), 0.0))
    # AD's latent posterior read as it holds it
    held = _model(V.Topic(lo="x", eta_mean=math.log(p_bar / (1 - p_bar)), eta_var=variance,
                          eta_latent=(mean, variance)))
    assert held.eta_means == [mean] and held.eta_vars == [variance]
    assert _initial_predictive(held) == pytest.approx(p_bar, abs=1e-6)
    assert float(LINK.p_integrated(np.array(mean), np.array(variance))) == pytest.approx(p_bar, abs=1e-9)
    # only p̄ and a variance: the variance-integrated predictive inverted
    rebuilt = _model(V.Topic(lo="x", eta_mean=math.log(p_bar / (1 - p_bar)), eta_var=variance))
    assert rebuilt.eta_means[0] == pytest.approx(mean, abs=1e-6)
    assert _initial_predictive(rebuilt) == pytest.approx(p_bar, abs=1e-6)
    # R9's point inverse with the variance added again (Codex: 0.6732 against 0.7448 at mean 2; 0.3068 against 0.2352)
    point = float(LINK.inverse(np.array(p_bar)))
    doubled = float((ADM.W32 * LINK.p(point + 2.0 * ADM.X32)).sum())
    assert abs(doubled - p_bar) > 0.05


def test_zero_variance_stays_equal():
    p_bar = float(ADM.residual_success(np.array(1.3)))
    model = _model(V.Topic(lo="x", eta_mean=math.log(p_bar / (1 - p_bar)), eta_var=0.0))
    assert model.eta_means[0] == pytest.approx(1.3, abs=1e-9)
    assert float(LINK.p(np.array(model.eta_means[0]))) == pytest.approx(p_bar, abs=1e-12)


def test_the_integrated_predictive_is_ads_expected_success():
    means = np.linspace(-6, 6, 25)
    for variance in (0.0, 0.5, 4.0, 9.0):
        ours = LINK.p_integrated(means, np.full_like(means, variance))
        assert np.allclose(ours, ADM.expected_success(means, np.full_like(means, variance), 0.0), atol=1e-9), variance


def test_ads_entry_point_hands_the_latent_moments_only_when_asked(tmp_path):
    """AD's read-only entry point: ``eta_at_top`` only with ``eta_moments``; its moments integrate to the LO's p̄
    (to the field's rounding, a one-row bank exactly as the mixture's moments)."""

    from learnloop.adaptive_difficulty.readiness import decision_state_fields

    from tests.router_mixture_helpers import mixture_env
    from tests.router_model_fakes import block_drawing_seed, fake_runtime

    env = mixture_env(tmp_path, fake_runtime(seed=block_drawing_seed()), version=V_TAG)
    los = list(env.vault.learning_objects)[:6]
    plain = decision_state_fields(env.vault, env.repository, los)
    asked = decision_state_fields(env.vault, env.repository, los, eta_moments=True)
    if plain.get("status") != "live":
        pytest.skip("the fixture's subject view is not live")
    assert all("eta_at_top" not in entry for entry in plain["los"].values())
    assert {lo: {k: v for k, v in entry.items() if k != "eta_at_top"} for lo, entry in asked["los"].items()} == \
        plain["los"]
    for entry in asked["los"].values():
        latent = entry["eta_at_top"]
        if latent is None or entry["p_bar_at_top_raw"] is None:
            continue
        integrated = float(ADM.expected_success(np.array(latent["mean"]), np.array(latent["variance"]),
                                                latent["guess"]))
        tolerance = 5e-5 if latent["rows"] == 1 else 2e-2
        assert integrated == pytest.approx(entry["p_bar_at_top_raw"], abs=tolerance)


from learnloop.algorithm_versions import ROUTER_FOLLOWUPS_ALGORITHM_VERSION as V_TAG  # noqa: E402
