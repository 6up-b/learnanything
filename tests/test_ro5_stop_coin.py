"""Router objective RO5 §9 item 1: the stop coin, κ0's hand-over and stop's return model. Fakes only.

* **The coin** is drawn on its own uniform, independent of the mix's draw and of either policy's output; its
  three arms have exact probabilities ``p, p, 1 − 2p``; the served distribution is exact (Monte Carlo agrees);
  every coin is one ``policy_experiment_assignments`` row with the availability frozen before the draw.
* **Off** (``stop_coin = 0``) at the tag, with every other arm off, Today is mvp-0.47's exactly.
* **κ0**: with no randomized response the daily seed stands; the posterior with no observation is the seed
  exactly; an override lowers the price and an acceptance raises it.
* **The return model**: a planted slope is recovered; in ``V`` the stop branch shows its return effect, and a
  shift that never moves a day of return drops out.
"""

from __future__ import annotations

from dataclasses import replace
import math

import pytest

from learnloop.algorithm_versions import ROUTER_CALIBRATION_ALGORITHM_VERSION, ROUTER_OBJECTIVE_ALGORITHM_VERSION
from learnloop.db.stores import router_objective as store
from learnloop.router_objective import assignments as A
from learnloop.router_objective import mix
from learnloop.router_objective import stop_coin as SC
from learnloop.router_objective import value as V

from tests.router_mixture_helpers import mixture_env, rows, run
from tests.router_model_fakes import fake_runtime
from tests.test_ro4_value import W

TAG = ROUTER_CALIBRATION_ALGORITHM_VERSION
OLD = ROUTER_OBJECTIVE_ALGORITHM_VERSION
ARMS_OFF = ("[router_objective]\nstop_coin = 0.0\ncheck_rate = \"off\"\npick_open_share = 0.0\n"
            "fitted_models = false\n")
SUPPORT = ["a", "b", SC.STOP]
MU = {"a": 0.5, "b": 0.3, SC.STOP: 0.2}


def test_the_arms_have_exact_probabilities_and_the_served_distribution_is_exact():
    assert SC.arm_probabilities(0.05) == pytest.approx({SC.OFFER_STOP: 0.05, SC.PRESENT_NEXT: 0.05, SC.POLICY: 0.9})
    served = SC.served_distribution(MU, 0.05, SUPPORT)
    assert sum(served.values()) == pytest.approx(1.0)
    assert served[SC.STOP] == pytest.approx(0.05 + 0.9 * 0.2)
    assert served["a"] == pytest.approx(0.05 * 0.5 / 0.8 + 0.9 * 0.5)
    # Monte Carlo over seeds: the coin and the mix's draw together serve what the formula says.
    counts = {ref: 0 for ref in SUPPORT}
    n = 6000
    from learnloop.router import mixture as mx

    for i in range(n):
        seed = f"seed-{i}"
        drawn = mx._pick(SUPPORT, MU, mx.uniform(seed, "candidate"))
        coin = SC.flip(seed, 0.05, support=SUPPORT, mu=MU, drawn=drawn, availability={})
        counts[coin.served] += 1
        assert coin.served_propensity == pytest.approx(served[coin.served])
    for ref in SUPPORT:
        assert counts[ref] / n == pytest.approx(served[ref], abs=0.02)


def test_the_coin_never_depends_on_the_mix_or_either_policy():
    for i in range(200):
        seed = f"s{i}"
        a = SC.flip(seed, 0.05, support=SUPPORT, mu=MU, drawn="a", availability={})
        b = SC.flip(seed, 0.05, support=SUPPORT, mu={"a": 0.1, "b": 0.1, SC.STOP: 0.8}, drawn=SC.STOP,
                    availability={"x": 1})
        assert (a.arm, a.u) == (b.arm, b.u)
    assert not SC.eligible(["a", "b"], session_minutes=5.0) and not SC.eligible([SC.STOP], session_minutes=5.0)
    assert SC.eligible(SUPPORT, session_minutes=5.0)
    # Landing ruling R4: the session's opening boundary (no active minute) is not a stop decision.
    assert not SC.eligible(SUPPORT, session_minutes=0.0)


def test_present_next_overrides_only_a_drawn_stop():
    seed = next(f"p{i}" for i in range(10_000) if 0.05 <= __import__("learnloop.router.mixture", fromlist=["x"])
                .uniform(f"p{i}", "stop_coin") < 0.10)
    coin = SC.flip(seed, 0.05, support=SUPPORT, mu=MU, drawn=SC.STOP, availability={})
    assert coin.arm == SC.PRESENT_NEXT and coin.served in {"a", "b"} and coin.u_next is not None
    kept = SC.flip(seed, 0.05, support=SUPPORT, mu=MU, drawn="b", availability={})
    assert kept.served == "b" and kept.u_next is None


def _assignments(env):
    with env.repository.connection() as connection:
        return A.rows(connection, A.STOP_COIN)


def test_serving_records_each_coin_with_its_exact_probability_and_availability(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(), version=TAG,
                      toml="[router_objective]\nstop_coin = 0.45\ncheck_rate = \"off\"\n")
    run(env)
    decided = [row for row in rows(env) if row["policy"] == mix.POLICY]
    coins = {row["unit_id"]: row for row in _assignments(env)}
    # Every decision but the session's opening one (landing ruling R4: no active minute yet) carries its coin.
    assert decided and decided[0]["id"] not in coins and set(coins) == {row["id"] for row in decided[1:]}
    with env.repository.connection() as connection:
        traces = {row["decision_id"]: store.trace(connection, row["decision_id"]) for row in store.traces(connection)}
    for row in decided[1:]:
        coin = coins[row["id"]]
        assert coin["experiment_id"] == A.STOP_COIN and coin["design"] == "mrt_reversible"
        assert coin["propensity"] == pytest.approx({SC.OFFER_STOP: 0.45, SC.PRESENT_NEXT: 0.45, SC.POLICY: 0.1}
                                                   [coin["variant"]])
        assert coin["detail"]["availability_logged"] == "before_the_draw"
        assert "minutes_left" in coin["detail"]["availability"]
        mixture = row["detail_json"]["mixture"]
        assert row["chosen_ref"] == coin["detail"]["served"] == mixture["served"]
        # The ledger's probability is the served one, exactly; the mix's μ stays beside it.
        served = SC.served_distribution(mixture["mix_pi"], 0.45, mixture["support"])
        assert row["propensity"] == pytest.approx(served[row["chosen_ref"]])
        assert mix.recompute(mixture) == pytest.approx(mixture["mix_pi"])
        trace = traces[row["id"]]["trace"]
        assert trace["stop_coin"]["arm"] == coin["variant"] and trace["mixing"]["chosen"] == row["chosen_ref"]
        if coin["variant"] == SC.OFFER_STOP:
            assert row["chosen_ref"] == SC.STOP and "stop_coin_forced" in trace["evaluation"]["score"]


def _blocks(record) -> list[tuple]:
    return [(block.lane, tuple(item.practice_item_id for item in block.items)) for block in record.blocks]


def _shape(env) -> list[tuple]:
    return [(row["policy"], row["chosen_ref"], row["propensity"], row["propensity_kind"],
             tuple((c["ref"], c.get("propensity")) for c in row["candidates_json"])) for row in rows(env)]


def test_every_arm_off_at_the_tag_is_mvp_047_exactly(tmp_path, monkeypatch):
    # The boundary key names the version, and both the mix's draw and the numeric policy's rollouts are seeded from
    # it, so both runs pin the draw and drop the version from the key (nothing else differs).
    from learnloop.daily_plan import objective_chooser as OC

    real_hash = OC._hash
    monkeypatch.setattr(OC, "_hash", lambda value: real_hash(
        {k: v for k, v in value.items() if k not in ("version", "plan_id")} if isinstance(value, dict) else value))
    # The key also names the plan's id and the newest attempt's id, fresh ULIDs in each run.
    monkeypatch.setattr(OC, "_latest_attempt", lambda _repository: "pinned-attempt")
    pinned = lambda _key, _decision: "pinned-seed"  # noqa: E731
    old = mixture_env(tmp_path / "old", fake_runtime(seed=pinned), version=OLD)
    off = mixture_env(tmp_path / "off", fake_runtime(seed=pinned), version=TAG, toml=ARMS_OFF)
    old_record, off_record = run(old), run(off)
    assert _blocks(old_record) == _blocks(off_record)
    assert _shape(old) == _shape(off)
    assert _assignments(off) == []
    with old.repository.connection() as a, off.repository.connection() as b:
        def bodies(connection):
            return [{key: value for key, value in store.trace(connection, row["decision_id"])["trace"].items()}
                    for row in store.traces(connection)]
        assert [body["candidates"] for body in bodies(a)] == [body["candidates"] for body in bodies(b)]
        assert [body["mixing"]["mu"] for body in bodies(a)] == [body["mixing"]["mu"] for body in bodies(b)]


# -- κ0 -------------------------------------------------------------------------------------------------


def _offer(continued: bool, gain: float = 0.01, cost: float = 1.0, randomized: bool = True) -> SC.Offer:
    return SC.Offer(decision_id="d", randomized=randomized, continued=continued, gain=gain, cost_per_kappa=cost)


def test_the_posterior_with_no_observation_is_the_seed_and_responses_move_it_both_ways():
    seed = 0.002
    none = SC.kappa_posterior(seed, 0.7, [])
    assert none["kappa0"] == pytest.approx(seed, rel=1e-6)
    overridden = SC.kappa_posterior(seed, 0.7, [_offer(True, gain=0.002)] * 6)
    accepted = SC.kappa_posterior(seed, 0.7, [_offer(False, gain=0.002)] * 6)
    assert overridden["kappa0"] < seed < accepted["kappa0"]
    # An offer with no positive forecast gain says nothing about the price.
    flat = SC.kappa_posterior(seed, 0.7, [_offer(True, gain=-1.0)] * 6)
    assert flat["kappa0"] == pytest.approx(seed, rel=1e-6) and flat["informative"] == 0


def test_kappa_stays_the_seed_until_a_randomized_offer_has_a_response(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(), version=TAG,
                      toml="[router_objective]\nstop_coin = 0.45\ncheck_rate = \"off\"\n")
    run(env)
    with env.repository.connection() as connection:
        assert SC.handed_over(connection, env.vault.config) is None  # no response recorded yet
        regimes = {row["kappa_regime"] for row in store.traces(connection)}
    assert regimes == {"seed"}


# -- the return model -------------------------------------------------------------------------------------


def test_a_planted_return_slope_is_recovered():
    """Through the coin alone (Codex review F3): the offer moves where sessions end, the return follows the
    minutes at a planted slope; ``tests/test_ro5_codex_review.py`` holds the confounded case."""

    import random

    rng = random.Random(7)
    rows_ = []
    for i in range(4000):
        u = rng.random()
        arm = SC.OFFER_STOP if u < 0.25 else (SC.PRESENT_NEXT if u < 0.5 else SC.POLICY)
        z = rng.uniform(-1, 1) - (0.8 if arm == SC.OFFER_STOP else 0.0)
        weight = 4.0 if arm == SC.OFFER_STOP else (-4.0 if arm == SC.PRESENT_NEXT else 0.0)
        rows_.append(SC.ReturnRow(decision_id=f"d{i}", session_id=f"s{i}", arm=arm, weight=weight,
                                  covariates=(0.0, 1.0), z=z, y=0.4 * z + rng.gauss(0, 0.3)))
    fitted = SC.fit_return_slope(rows_, 0.5)
    assert fitted.source == "posterior_randomized_coin" and fitted.mean == pytest.approx(0.4, abs=0.08)
    assert SC.fit_return_slope(rows_[:1], 0.5).source == "prior"


def _return_inputs(**overrides):
    base = dict(
        topics=(V.Topic(lo="L1", eta_mean=0.0, eta_var=0.1, undated_density=1.0 / 90.0),
                V.Topic(lo="L2", eta_mean=-0.5, eta_var=0.1, undated_density=1.0 / 90.0)),
        dated=(), session_minutes=5.0,
        price=V.Price(kappa0=0.0005, remembered=25.0, remembered_source="test"),
        tail_block_minutes=5.0, tail_block_items=2, horizon_days=30.0, fsrs_weights=W,
        return_gaps_days=(1.5, 2.5, 3.5), stop_accept=(1.0, 1.0),
    )
    base.update(overrides)
    return V.Inputs(**base)


def test_the_stop_branch_shows_the_return_effect_and_an_inert_shift_drops_out():
    base = _return_inputs()
    actions = [V.Action(ref="stop", kind=V.STOP), V.Action(ref="b", kind=V.REVIEW, item_los=("L1",), minutes=5.0)]
    plain = V.evaluate(base, actions, draws=8, seed="s").by_ref()
    assert "return_effect" not in plain["stop"].extra
    strong = V.evaluate(replace(base, return_slope=(3.0, 0.01)), actions, draws=8, seed="s").by_ref()["stop"]
    assert strong.extra["return_model"] == "active" and math.isfinite(strong.extra["return_effect"])
    # A short session (5 of 25 minutes) under a positive slope returns sooner: stopping now gains.
    assert strong.extra["return_effect"] > 0
    inert = V.evaluate(replace(base, return_slope=(1e-9, 0.0)), actions, draws=8, seed="s").by_ref()
    assert inert["stop"].extra["return_effect"] == pytest.approx(0.0)
    assert inert["stop"].extra["return_model"].startswith("dropped")
    # A model that moves no day of return changes no value.
    assert inert["stop"].q == pytest.approx(plain["stop"].q) and inert["b"].q == pytest.approx(plain["b"].q)
