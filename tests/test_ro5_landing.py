"""Router objective RO5, landing rulings (docs/reviews/router-ro5.md, "Landing onto main"): each reproduced by a test
that fails on the pre-fix source (``5f02be6eb2``). Fakes, in-memory SQLite and synthetic vaults only; no model is
asked.

* R2 (Codex final verify F11): the return slope's integration adapts to the posterior: its grid covers the prior's
  and the likelihood's peaks and the region between, its bounds widen until the tail mass beyond them is negligible,
  and it converges only when both the spacing and the tail mass pass; a planted slope is recovered at a narrow prior
  and at a wide one.
"""

from __future__ import annotations

import random

import pytest

from learnloop.algorithm_versions import ROUTER_CALIBRATION_ALGORITHM_VERSION
from learnloop.router_objective import assignments as A
from learnloop.router_objective import mix
from learnloop.router_objective import stop_coin as SC

from tests.router_mixture_helpers import mixture_env, rows, run
from tests.router_model_fakes import fake_runtime

TAG = ROUTER_CALIBRATION_ALGORITHM_VERSION
SUPPORT = ("a", "b", SC.STOP)


# -- R2 (F11) ------------------------------------------------------------------------------------------------


def _planted(slope: float, *, n: int, p: float, seed: int, noise: float = 0.002) -> list[SC.ReturnRow]:
    """Sessions whose randomized coin moves the minutes (``z``) and whose return gap follows them at ``slope``."""

    rng = random.Random(seed)
    rows = []
    for i in range(n):
        u = rng.random()
        weight = 1 / p if u < p else (-1 / p if u < 2 * p else 0.0)
        z = -0.1 * weight + rng.gauss(0, 0.01)
        arm = SC.OFFER_STOP if weight > 0 else SC.PRESENT_NEXT if weight < 0 else SC.POLICY
        rows.append(SC.ReturnRow(str(i), str(i), arm, weight, (0.0, 1.0), z, slope * z + rng.gauss(0, noise)))
    return rows


def test_r2_f11_the_dominant_posterior_peak_outside_the_priors_reach_is_integrated():
    # Codex's reproduction (verify 20261105-104749-57ysh9): prior sd 0.01, coin probability 0.45, the likelihood's
    # peak at 0.4197, 42 prior sds out. Pre-fix: mean 0.000275, variance 1.0e-4, labelled posterior_randomized_coin
    # (the integration stopped at 40 prior sds and declared convergence on the prior's side alone).
    fitted = SC.fit_return_slope(_planted(0.42, n=3000, p=0.45, seed=8), 0.01)
    assert fitted.source == "posterior_randomized_coin"
    assert fitted.mean == pytest.approx(0.4196, abs=2e-3) and 0 < fitted.variance < 1e-6


@pytest.mark.parametrize("prior_sd", [0.01, 1.0], ids=["narrow", "wide"])
def test_r2_a_planted_slope_is_recovered_at_a_narrow_and_at_a_wide_prior(prior_sd):
    fitted = SC.fit_return_slope(_planted(0.3, n=4000, p=0.3, seed=21), prior_sd)
    assert fitted.source == "posterior_randomized_coin"
    assert fitted.mean == pytest.approx(0.3, abs=5e-3) and 0 < fitted.variance < 1e-5


def test_r2_a_weak_instrument_keeps_the_priors_resolution_and_bounds():
    # The other side (a guard, passing before and after): little information, the posterior near the prior, still
    # integrated with its tails (the bounded statistic can leave the posterior a little wider than the prior).
    rng = random.Random(5)
    rows = []
    for i in range(40):
        u = rng.random()
        weight = 1 / 0.3 if u < 0.3 else (-1 / 0.3 if u < 0.6 else 0.0)
        arm = SC.OFFER_STOP if weight > 0 else SC.PRESENT_NEXT if weight < 0 else SC.POLICY
        z = rng.gauss(0, 1) - 0.05 * weight
        rows.append(SC.ReturnRow(str(i), str(i), arm, weight, (0.0, 1.0), z, rng.gauss(0, 1)))
    fitted = SC.fit_return_slope(rows, 0.5)
    assert fitted.source == "posterior_randomized_coin"
    assert abs(fitted.mean) < 0.5 and 0.01 < fitted.variance < 0.5


def test_r2_an_integration_that_cannot_converge_leaves_the_labelled_prior(monkeypatch):
    monkeypatch.setattr(SC, "_WIDENINGS", 0)
    fitted = SC.fit_return_slope(_planted(0.42, n=3000, p=0.45, seed=8), 0.01)
    assert fitted.source == "prior_integration_unconverged" and fitted.mean == 0.0
    assert fitted.variance == pytest.approx(0.01 ** 2)


# -- R4: the stop coin skips the session's opening boundary ---------------------------------------------------


def _offer_seed(rate: float):
    """A seed whose stop-coin uniform lands on ``offer_stop`` (every decision would offer stop)."""

    from learnloop.router.mixture import uniform

    seed = next(f"offer-{i}" for i in range(10_000) if uniform(f"offer-{i}", "stop_coin") < rate)
    return lambda _key, _decision_id: seed


def test_r4_the_coin_is_not_drawn_before_any_active_minute_of_the_session(tmp_path):
    # The synthetic week's case: an offer at minute 0 that ended the day before any question. Pre-fix the day's first
    # decision drew offer_stop and the plan closed with nothing served.
    env = mixture_env(tmp_path, fake_runtime(seed=_offer_seed(0.45)), version=TAG,
                      toml="[router_objective]\nstop_coin = 0.45\ncheck_rate = \"off\"\npick_open_share = 0.0\n")
    run(env)
    decided = [row for row in rows(env) if row["policy"] == mix.POLICY]
    with env.repository.connection() as connection:
        coins = {row["unit_id"]: row for row in A.rows(connection, A.STOP_COIN)}
        attempts = connection.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()[0]
    assert decided, "the day had policy decisions"
    first = decided[0]
    assert first["id"] not in coins and "stop_coin" not in first["detail_json"]["mixture"]
    assert attempts >= 1, "the opening boundary served a question"
    # Every coin drawn was at a boundary with active minutes in the session (structural: the eligibility asks it).
    assert coins and all(row["detail"]["availability"]["session_minutes"] > 0 for row in coins.values())
    assert not SC.eligible([*SUPPORT], session_minutes=0.0) and SC.eligible([*SUPPORT], session_minutes=0.5)
    assert not SC.eligible([*SUPPORT], session_minutes=None)
