"""RO4 §8.7, §8.10 "Evaluation": the comparison score D̂ and the weight's posterior, on planted synthetic logs."""

from __future__ import annotations

import math
import random

import pytest

from learnloop.router_objective import weight as W

SEEDS = W.Seeds()


def _mu(pi_l, pi_q, w=0.8, eps=0.02):
    k = len(pi_l)
    return {a: (1 - k * eps) * (w * pi_l[a] + (1 - w) * pi_q[a]) + eps for a in pi_l}


def _expected(pi_l, pi_q, outcome, *, baseline, cost_baseline, cost):
    """E_A[D̂] by enumeration over the drawn action (one use with r = 1, observed)."""

    mu = _mu(pi_l, pi_q)
    total = 0.0
    for a in pi_l:
        use = W.Use(key="L:x:1", weight=1.0, baseline=baseline, r=1.0, observed=True, outcome=outcome[a])
        d = pi_l[a] - pi_q[a]
        total += mu[a] * W.score(d_taken=d, mu_taken=mu[a], uses=[use], cost=cost[a], cost_baseline=cost_baseline)
    return total


def test_sum_d_zero_makes_the_score_invariant_to_the_baselines_levels():
    pi_l = {"a": 0.5, "b": 0.3, "c": 0.2}
    pi_q = {"a": 0.0, "b": 1.0, "c": 0.0}
    outcome = {"a": 0.9, "b": 0.6, "c": 0.4}
    cost = {"a": 0.02, "b": 0.03, "c": 0.01}
    first = _expected(pi_l, pi_q, outcome, baseline=0.0, cost_baseline=0.0, cost=cost)
    second = _expected(pi_l, pi_q, outcome, baseline=0.73, cost_baseline=5.0, cost=cost)
    assert first == pytest.approx(second, abs=1e-12)
    delta = sum((pi_l[a] - pi_q[a]) * (outcome[a] - cost[a]) for a in pi_l)
    assert first == pytest.approx(delta, abs=1e-12)


@pytest.mark.parametrize("planted", ["delta", "null"])
def test_the_scores_mean_matches_a_planted_delta_and_is_zero_under_a_null(planted):
    rng = random.Random(7)
    pi_l = {"a": 0.6, "b": 0.3, "c": 0.1}
    pi_q = {"a": 0.0, "b": 0.0, "c": 1.0} if planted == "delta" else dict(pi_l)
    value = {"a": 0.8, "b": 0.5, "c": 0.3}  # the true mean outcome of each action's use
    r = 0.25  # the randomized check's known observation probability
    mu = _mu(pi_l, pi_q)
    refs, weights = list(mu), list(mu.values())
    delta = sum((pi_l[a] - pi_q[a]) * value[a] for a in pi_l)
    scores = []
    for _ in range(40_000):
        a = rng.choices(refs, weights)[0]
        observed = rng.random() < r
        outcome = 1.0 if rng.random() < value[a] else 0.0
        use = W.Use(key="L:x:3", weight=1.0, baseline=0.5, r=r, observed=observed, outcome=outcome)
        scores.append(W.score(d_taken=pi_l[a] - pi_q[a], mu_taken=mu[a], uses=[use], cost=0.0, cost_baseline=0.0))
    mean = sum(scores) / len(scores)
    sd = math.sqrt(sum((s - mean) ** 2 for s in scores) / (len(scores) - 1))
    assert abs(mean - delta) <= 4 * sd / math.sqrt(len(scores))
    if planted == "null":
        assert delta == 0.0 and all(s == 0.0 for s in scores)


def test_what_carries_no_score():
    useful = [W.Use(key="L:x:1", weight=1.0, baseline=0.5, r=0.2)]
    unchecked = [W.Use(key="L:x:1", weight=1.0, baseline=0.5, r=0.0)]
    d = {"a": 0.3, "b": -0.3}
    assert W.carries_score(uses=useful, failed=["llm"], d_taken=0.3, d_all=d) == W.FALLBACK
    assert W.carries_score(uses=useful, failed=[], d_taken=0.0, d_all={"a": 0.0, "b": 0.0}) == W.AGREE
    assert W.carries_score(uses=unchecked, failed=[], d_taken=0.3, d_all=d) == W.NO_RANDOMIZED_USE
    assert W.carries_score(uses=useful, failed=[], d_taken=0.3, d_all=d) is None


def test_the_prior_gives_w_its_seed_and_w_stays_inside_its_minimum_shares():
    posterior = W.posterior([], SEEDS)
    assert posterior.source == "prior" and posterior.p == pytest.approx(SEEDS.p0)
    assert W.weight(posterior.p, SEEDS) == pytest.approx(0.8)
    assert SEEDS.p0 == pytest.approx(0.875) and SEEDS.m0 == pytest.approx(0.0115034938, rel=1e-6)
    for p in (0.0, 0.3, 1.0):
        assert SEEDS.ell_l <= W.weight(p, SEEDS) <= 1 - SEEDS.ell_q


def test_w_reads_no_score_from_a_window_still_open_and_needs_two_bins():
    def scored(i, value, day):
        return W.Scored(decision_id=f"d{i}", decided_at=f"2026-11-{day:02d}T09:00:00Z",
                        window_closes_at=f"2026-11-{day + 14:02d}T09:00:00Z" if day + 14 <= 30 else "2026-12-30T09:00:00Z",
                        value=value)

    one_bin = [scored(i, 0.5, 1) for i in range(5)]
    assert W.posterior(one_bin, SEEDS, at="2026-11-29T00:00:00Z").source == "prior_fewer_than_two_bins"
    two_bins = one_bin + [scored(10 + i, -0.5, 1 + 28) for i in range(5)]
    at_open = W.posterior(two_bins, SEEDS, at="2026-11-29T00:00:00Z")
    assert at_open.censored.get(W.PENDING) == 5 and at_open.n == 5
    later = W.posterior(two_bins, SEEDS, at="2027-01-01T00:00:00Z")
    assert later.source == "posterior" and later.bins == 2 and later.sd < SEEDS.s0


def test_the_numeric_policy_gains_nothing_from_a_wrong_critic():
    """The score takes no model prediction: on a planted case where the critic is wrong (it loves "c", the worst
    action), π_Q = 1[c] scores below the LLM, whatever the critic said."""

    pi_l = {"a": 0.7, "b": 0.2, "c": 0.1}
    pi_q = {"a": 0.0, "b": 0.0, "c": 1.0}
    outcome = {"a": 0.9, "b": 0.6, "c": 0.2}
    expected = _expected(pi_l, pi_q, outcome, baseline=0.5, cost_baseline=0.0, cost={a: 0.0 for a in pi_l})
    assert expected > 0  # Δ favours the LLM's recommendation
    assert "q" not in W.score.__code__.co_varnames  # no action-value input


def test_a_check_linked_to_ten_decisions_counts_once():
    assert W.unique_assessments([("chk_1", f"d{i}") for i in range(10)] + [("chk_2", "d0")]) == 2
