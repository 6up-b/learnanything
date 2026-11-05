"""RO4 §3.2, §8.1, §8.10 "Form": the value estimator on hand-computed cases. Pure; no vault, no model."""

from __future__ import annotations

import math
import random

import numpy as np
import pytest

from learnloop.router_objective import memory as M
from learnloop.router_objective import value as V
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS, MemoryState, Rating, apply_review, forgetting_curve

W = tuple(FSRS6_DEFAULT_WEIGHTS)
EXACT = M.Combiner(mean=(0.0, 1.0, 0.0), variance=(0.0, 0.0, 0.0), source="test")
FIXED = V.Learning(gamma=(0.0, 0.0), gbar=((0.0, 0.0), (0.0, 0.0)))


def _logit(p: float) -> float:
    return math.log(p / (1 - p))


def _inputs(**overrides):
    base = dict(
        topics=(V.Topic(lo="lo_a", eta_mean=_logit(0.78), eta_var=0.0, undated_density=0.0),),
        dated=(), session_minutes=10.0,
        price=V.Price(kappa0=0.02 * 2 * 10 / ((10 + 10) ** 2 - 10 ** 2), remembered=10.0, remembered_source="test"),
        tail_block_minutes=10.0, tail_block_items=1, horizon_days=1.0, fsrs_weights=W,
        return_gaps_days=(2.0,), stop_accept=(1e6, 1e-6), combiner=EXACT, learning=FIXED,
    )
    base.update(overrides)
    return V.Inputs(**base)


def test_the_eve_of_exam_regression():
    """T1's case (spec §3.4): cramming that adds .01 to exam performance at a block price of .02 has a
    continue-vs-stop advantage of −.010, not +.780; stopping keeps the exam's whole value."""

    gamma = _logit(0.79) - _logit(0.78)
    inputs = _inputs(dated=(V.DatedUse(goal_id="exam", lo="lo_a", at_days=1.0, weight=1.0),),
                     learning=V.Learning(gamma=(gamma, 0.0), gbar=((0.0, 0.0), (0.0, 0.0))))
    block = V.Action(ref="cram", kind=V.NEW_PRACTICE, item_los=("lo_a",), minutes=10.0)
    stop = V.Action(ref="stop_for_today", kind=V.STOP)
    out = V.evaluate(inputs, [block, stop], draws=4, seed="eve").by_ref()
    assert out["cram"].terms["kappa_integral"] == pytest.approx(0.02)
    assert out["stop_for_today"].q - out["stop_for_today"].terms["terminal"] == pytest.approx(0.780, abs=1e-9)
    assert out["cram"].q - out["cram"].terms["terminal"] == pytest.approx(0.770, abs=1e-9)
    assert out["cram"].q - out["stop_for_today"].q == pytest.approx(-0.010, abs=1e-9)


def test_a_date_inside_a_long_action_is_scored_at_the_date_on_the_state_before_it():
    gamma = 1.0
    learning = V.Learning(gamma=(gamma, 0.0), gbar=((0.0, 0.0), (0.0, 0.0)))
    long_block = V.Action(ref="long", kind=V.NEW_PRACTICE, item_los=("lo_a",), minutes=2 * 1440.0)
    inside = _inputs(dated=(V.DatedUse("exam", "lo_a", 1.0, 1.0),), learning=learning, horizon_days=5.0)
    after = _inputs(dated=(V.DatedUse("exam", "lo_a", 3.0, 1.0),), learning=learning, horizon_days=5.0)
    crossed = V.evaluate(inside, [long_block], draws=2, seed="x").by_ref()["long"]
    later = V.evaluate(after, [long_block], draws=2, seed="x").by_ref()["long"]
    assert crossed.terms["crossed_date_reward"] == pytest.approx(0.78)
    assert later.terms["crossed_date_reward"] == 0.0
    # After the action the exam is scored on the state after its effect (and the tail's sessions before it).
    assert later.terms["tail_reward"] >= M.sigmoid(_logit(0.78) + gamma).item() - 1e-9


def test_an_action_crossing_the_cutoff_carries_its_commitment_into_t_c():
    inputs = _inputs(horizon_days=5.0 / 1440.0, session_minutes=0.0)
    block = V.Action(ref="b", kind=V.REVIEW, item_los=("lo_a",), minutes=10.0)
    row = V.evaluate(inputs, [block], draws=2, seed="c").by_ref()["b"]
    k0, mbar = inputs.price.kappa0, inputs.price.remembered
    assert row.terms["kappa_integral"] == pytest.approx(k0 * 5.0 ** 2 / (2 * mbar))
    total = k0 * 10.0 ** 2 / (2 * mbar)
    # T_C carries the minutes past C (and the tail past it): the action's whole cost is counted once.
    assert row.terms["terminal"] <= -(total - row.terms["kappa_integral"]) + 1e-12


def test_one_cutoff_for_every_candidate_and_it_is_the_latest_goal_date_when_further():
    inputs = _inputs(horizon_days=3.0, dated=(V.DatedUse("g", "lo_a", 7.5, 1.0),))
    assert inputs.cutoff == 7.5 == V.cutoff_for(3.0, inputs.dated)
    out = V.evaluate(inputs, [V.Action(ref="a", kind=V.REVIEW, item_los=("lo_a",), minutes=5.0),
                              V.Action(ref="stop_for_today", kind=V.STOP)], draws=2, seed="one")
    assert out.cutoff == 7.5


def test_the_same_theta_draw_is_used_across_candidates():
    inputs = _inputs(topics=(V.Topic("lo_a", 0.3, 0.5, practiced=True, stability=3.0, elapsed_days=2.0,
                                     undated_density=1 / 90),
                             V.Topic("lo_b", -0.2, 0.5, undated_density=1 / 90)),
                     combiner=M.Combiner(), learning=V.Learning(), horizon_days=20.0)
    a = V.Action(ref="a", kind=V.REVIEW, item_los=("lo_a",), minutes=5.0, minutes_log_sd=0.3)
    twin = V.Action(ref="twin", kind=V.REVIEW, item_los=("lo_a",), minutes=5.0, minutes_log_sd=0.3)
    out = V.evaluate(inputs, [a, twin], draws=8, seed="crn").by_ref()
    assert out["a"].q_draws == out["twin"].q_draws
    assert len(set(out["a"].q_draws)) > 1  # the draws differ from one another


def test_offer_branches_match_a_hand_computed_case():
    """``Q = p·E[R+V | acc] + (1−p)·E[R+V | dec]``; the expected cost exceeds the cost at the mean duration
    by ``κ0/(2m̄)·p(1−p)d²``."""

    # At the remembered minutes, so the declined branch ends the session (no block of its own to cost).
    p, d, m = 0.3, 10.0, 10.0
    inputs = _inputs(session_minutes=m, stop_accept=(1.0, 1.0), horizon_days=1.0)
    offer = V.Action(ref="offer", kind=V.NEW_PRACTICE, item_los=("lo_a",), minutes=d, accept=(p * 1e6, (1 - p) * 1e6))
    taken = V.Action(ref="taken", kind=V.NEW_PRACTICE, item_los=("lo_a",), minutes=d)
    out = V.evaluate(inputs, [offer, taken], draws=4, seed="offer").by_ref()
    k0, mbar = inputs.price.kappa0, inputs.price.remembered
    accepted = out["taken"]
    assert out["offer"].extra["branches"]["accepted"] == pytest.approx(accepted.q)
    declined = out["offer"].extra["branches"]["declined"]
    # The uptake is a draw from its Beta (here concentrated at p); the branches are mixed by the draws' p.
    p_bar = out["offer"].extra["branches"]["p_accept"]
    assert p_bar == pytest.approx(p, abs=1e-3)
    assert out["offer"].q == pytest.approx(p_bar * accepted.q + (1 - p_bar) * declined, rel=1e-6)
    assert out["offer"].terms["kappa_integral"] == pytest.approx(p_bar * k0 * ((m + d) ** 2 - m ** 2) / (2 * mbar),
                                                                 rel=1e-6)
    expected_cost = p * k0 * ((m + d) ** 2 - m ** 2) / (2 * mbar)
    at_mean = k0 * ((m + p * d) ** 2 - m ** 2) / (2 * mbar)
    assert expected_cost - at_mean == pytest.approx(k0 / (2 * mbar) * p * (1 - p) * d ** 2)


def test_durations_are_sampled_and_their_spread_costs():
    inputs = _inputs(session_minutes=5.0)
    sd = 0.5
    sampled = V.Action(ref="s", kind=V.REVIEW, item_los=("lo_a",), minutes=10.0, minutes_log_sd=sd)
    out = V.evaluate(inputs, [sampled], draws=256, seed="dur").by_ref()["s"]
    k0, mbar, m = inputs.price.kappa0, inputs.price.remembered, 5.0
    mean = 10.0 * math.exp(sd ** 2 / 2)
    var = (math.exp(sd ** 2) - 1) * math.exp(sd ** 2) * 100.0
    analytic = k0 * ((m + mean) ** 2 - m ** 2) / (2 * mbar) + k0 / (2 * mbar) * var
    assert out.terms["kappa_integral"] == pytest.approx(analytic, rel=0.15)
    assert out.terms["kappa_integral"] > k0 * ((m + mean) ** 2 - m ** 2) / (2 * mbar)


def test_v_recomputed_from_the_logged_rows_is_the_tails_next_action():
    inputs = _inputs(topics=(V.Topic("lo_a", 0.3, 0.2, undated_density=1 / 90),), session_minutes=0.0,
                     combiner=M.Combiner(), horizon_days=10.0)
    rows = [V.Action(ref="a", kind=V.REVIEW, item_los=("lo_a",), minutes=10.0),
            V.Action(ref="stop_for_today", kind=V.STOP)]
    out = V.evaluate(inputs, rows, draws=4, seed="v")
    assert out.reference is not None and not out.reference.choosable
    pi_tail = {row.ref: (1.0 if row.ref == out.reference.ref else 0.0) for row in (*out.valued, out.reference)}
    recomputed = sum(pi_tail[row.ref] * row.q for row in (*out.valued, out.reference))
    assert recomputed == pytest.approx(out.v)


def test_the_numeric_policy_is_argmax_with_ties_by_support_order():
    def row(ref, draws):
        return V.Valued(ref=ref, kind=V.REVIEW, q_draws=tuple(draws), terms={}, extra={}, choosable=True)

    evaluation = V.Evaluation(valued=(row("staged", [1.0, 1.2, 0.8, 1.0]), row("other", [1.05, 1.1, 0.9, 1.05]),
                                      row("worse", [0.1, 0.1, 0.1, 0.1])), draws=4, cutoff=1.0, seed="t",
                              elapsed_ms=0, complete=True)
    chosen, record = V.numeric_choice(evaluation, ["staged", "other", "worse"])
    assert record["argmax"] == "other" and chosen == "staged" and "staged" in record["tied"]
    clear = V.Evaluation(valued=(row("staged", [0.0, 0.0, 0.0, 0.0]), row("other", [1.0, 1.0, 1.0, 1.0])), draws=4,
                         cutoff=1.0, seed="t", elapsed_ms=0, complete=True)
    assert V.numeric_choice(clear, ["staged", "other"])[0] == "other"


def test_a_probe_is_scored_through_its_repair_branches():
    inputs = _inputs(topics=(V.Topic("lo_a", 0.0, 2.0, undated_density=0.5),), session_minutes=0.0,
                     combiner=M.Combiner(mean=(0.0, 1.0, 0.0), variance=(0.0, 0.0, 0.0)),
                     learning=V.Learning(gamma=(0.6, 0.0), gbar=((0.0, 0.0), (0.0, 0.0))), horizon_days=10.0)
    probe = V.Action(ref="probe", kind=V.PROBE, item_los=("lo_a",), minutes=2.0,
                     repair=V.Action(ref="repair", kind=V.REPAIR, item_los=("lo_a", "lo_a"), minutes=6.0))
    out = V.evaluate(inputs, [probe], draws=32, seed="probe").by_ref()["probe"]
    branches = out.extra["branches"]
    assert set(branches) >= {"none", "repair", "repair_share"}
    assert 0.0 <= branches["repair_share"] <= 1.0
    assert "information" in out.extra


def test_the_vectorized_fsrs_is_the_scalar_one():
    fsrs = M.Fsrs(W)
    rng = random.Random(4)
    for _ in range(50):
        d, s, elapsed, good, practiced = rng.uniform(1, 10), rng.uniform(0.1, 60), rng.uniform(0, 90), rng.random() < .6, rng.random() < .8
        prev = MemoryState(difficulty=d, stability=s, retrievability=0.0) if practiced else None
        expected = apply_review(prev, Rating.GOOD if good else Rating.AGAIN, elapsed, W)
        got_d, got_s = fsrs.review(np.array([d]), np.array([s]), np.array([practiced]), np.array([elapsed]),
                                   np.array([good]))
        assert got_d[0] == pytest.approx(expected.difficulty) and got_s[0] == pytest.approx(expected.stability)
        assert fsrs.retrievability(np.array([s]), np.array([elapsed]))[0] == pytest.approx(forgetting_curve(s, elapsed, W))


def test_the_combiner_is_its_prior_without_outcomes_and_learns_with_them():
    assert M.fit_combiner([]) == M.Combiner()
    rng = np.random.default_rng(1)
    rows = []
    for _ in range(400):
        eta = rng.normal()
        r = rng.uniform(0.3, 0.99)
        p = M.sigmoid(0.5 + 1.0 * eta + 0.5 * (M.logit(r) - eta)).item()
        rows.append((float(eta), float(r), int(rng.random() < p)))
    fitted = M.fit_combiner(rows)
    assert fitted.n == 400 and fitted.source == "laplace_fit"
    assert fitted.mean[0] == pytest.approx(0.5, abs=0.35)
    assert all(v < 0.25 for v in fitted.variance)


def test_the_gain_curve_rises_with_todays_minutes():
    inputs = _inputs(topics=(V.Topic("lo_a", -0.5, 0.2, undated_density=1 / 90),
                             V.Topic("lo_b", -0.2, 0.2, undated_density=1 / 90)),
                     combiner=M.Combiner(), learning=V.Learning(), horizon_days=30.0, session_minutes=0.0)
    g = V.gain(inputs, [0.0, 10.0, 20.0], draws=4, seed="g")
    assert g[0.0] < g[10.0] < g[20.0]


# -- Codex review (router-ro4, job 20261105-044310-mIr8Nh): each fails on the pre-fix value estimator ------------


def _probe_case():
    inputs = _inputs(topics=(V.Topic("lo_a", 0.0, 2.0, undated_density=0.5),), session_minutes=0.0,
                     combiner=M.Combiner(mean=(0.0, 1.0, 0.0), variance=(0.0, 0.0, 0.0)),
                     learning=V.Learning(gamma=(0.6, 0.0), gbar=((0.0, 0.0), (0.0, 0.0))), horizon_days=10.0)
    probe = V.Action(ref="probe", kind=V.PROBE, item_los=("lo_a",), minutes=2.0,
                     repair=V.Action(ref="repair", kind=V.REPAIR, item_los=("lo_a", "lo_a"), minutes=6.0))
    return inputs, probe


def test_f2_the_probe_branch_never_sees_the_repairs_future_result():
    """The repair-or-not choice is a function of the probe's result and the posterior after it: flipping every
    outcome the true path draws after the probe (the repair's graded attempts, its duration, the tail's outcomes)
    leaves the choice of every draw unchanged."""

    inputs, probe = _probe_case()
    # A price at which the repair is worth it after some results and not others.
    inputs = replace_inputs(inputs, price=V.Price(kappa0=0.05, remembered=10.0))
    model = V._Model(inputs, 64, "f2")
    _ledger, extra = model.value(probe)
    flipped = V._Model(inputs, 64, "f2")
    flipped.streams.action_u[:, 2, :] = 1.0 - flipped.streams.action_u[:, 2, :]
    flipped.streams.outcome_u[:] = 1.0 - flipped.streams.outcome_u
    flipped.streams.duration_z[:, 2] = -flipped.streams.duration_z[:, 2]
    _again, extra_flipped = flipped.value(probe)
    assert extra["branches"]["repair_share"] == extra_flipped["branches"]["repair_share"]
    assert extra["branches"]["repair_after_miss"] == extra_flipped["branches"]["repair_after_miss"]
    # Still a real choice: it depends on the probe's own result (a miss makes the repair likelier).
    assert 0.0 < extra["branches"]["repair_share"] < 1.0
    assert extra["branches"]["repair_after_miss"] > extra["branches"]["repair_share"]


def test_f3_a_date_crossed_by_a_probe_is_scored_on_the_state_before_it_and_its_repair():
    """A ten-minute probe crosses a goal date five minutes away, then a ten-minute repair: the date is scored at
    the pre-action performance (0.5), never on the post-repair state, as an ordinary action's is."""

    learning = V.Learning(gamma=(2.0, 0.0), gbar=((0.0, 0.0), (0.0, 0.0)))
    inputs = _inputs(topics=(V.Topic("lo_a", 0.0, 0.0),), dated=(V.DatedUse("exam", "lo_a", 5.0 / 1440.0, 1.0),),
                     price=V.Price(kappa0=0.0, remembered=10.0), learning=learning, session_minutes=0.0,
                     horizon_days=1.0)
    probe = V.Action(ref="probe", kind=V.PROBE, item_los=("lo_a",), minutes=10.0,
                     repair=V.Action(ref="repair", kind=V.REPAIR, item_los=("lo_a",), minutes=10.0))
    review = V.Action(ref="review", kind=V.REVIEW, item_los=("lo_a",), minutes=10.0)
    out = V.evaluate(inputs, [probe, review], draws=8, seed="f3").by_ref()
    for ref in ("probe", "review"):
        assert out[ref].terms["crossed_date_reward"] == pytest.approx(0.5), ref
        assert out[ref].q == pytest.approx(0.5), ref  # no undated use, no price: the date is all of Q


def test_f3_a_multi_day_action_counts_no_interval_twice_and_no_session_before_its_end():
    """Constant performance 0.5 with density 1 over C + H = 10 days is worth 5.0 whatever the action's length; a
    day-and-a-half action leaves no tail session before it ends."""

    flat = V.Learning(gamma=(0.0, 0.0), gbar=((0.0, 0.0), (0.0, 0.0)))
    topic = V.Topic("lo_a", 0.0, 0.0, undated_density=1.0)
    two_days = V.Action(ref="long", kind=V.REVIEW, item_los=("lo_a",), minutes=1.5 * 1440.0)
    free = _inputs(topics=(topic,), price=V.Price(kappa0=0.0, remembered=10.0), learning=flat, session_minutes=10.0,
                   horizon_days=5.0, return_gaps_days=())
    assert V.evaluate(free, [two_days], draws=2, seed="f3b").by_ref()["long"].q == pytest.approx(5.0)
    priced = replace_inputs(free, price=V.Price(kappa0=0.1, remembered=10.0))
    row = V.evaluate(priced, [two_days], draws=2, seed="f3b").by_ref()["long"]
    per_session = 0.1 * 10.0 ** 2 / (2 * 10.0)
    assert row.terms["tail_cost"] == pytest.approx(3 * per_session)  # days 2, 3 and 4 (C = 5), none on day 1 (it ends at 1.5)


def replace_inputs(inputs, **changes):
    from dataclasses import replace

    return replace(inputs, **changes)


def test_f4_the_return_gap_follows_every_session_end():
    """With an empirical three-day gap, C + H = 6 days holds one tail session (day 3), not one on day 3 and then
    daily ones."""

    flat = V.Learning(gamma=(0.0, 0.0), gbar=((0.0, 0.0), (0.0, 0.0)))
    inputs = _inputs(topics=(V.Topic("lo_a", 0.0, 0.0),), price=V.Price(kappa0=0.1, remembered=10.0),
                     learning=flat, session_minutes=10.0, horizon_days=3.0, return_gaps_days=(3.0,))
    row = V.evaluate(inputs, [V.Action(ref="r", kind=V.REVIEW, item_los=("lo_a",), minutes=1.0)], draws=2,
                     seed="f4").by_ref()["r"]
    per_session = 0.1 * 10.0 ** 2 / (2 * 10.0)
    # Day 3 is at C: its session's cost is T_C's; no undated use, so the terminal term is that cost alone.
    assert row.terms["tail_cost"] == pytest.approx(0.0)
    assert -row.terms["terminal"] == pytest.approx(per_session)


def test_f5_a_sequence_values_its_steps_in_order_with_their_own_kinds():
    """"Follow-up now, then the rest" and the reverse differ when timing matters: a date between the two steps is
    scored after the first step's effect and before the second's."""

    learning = V.Learning(gamma=(1.0, 0.0), gbar=((0.0, 0.0), (0.0, 0.0)))
    inputs = _inputs(topics=(V.Topic("lo_a", 0.0, 0.0), V.Topic("lo_b", 0.0, 0.0)),
                     dated=(V.DatedUse("exam", "lo_a", 15.0 / 1440.0, 1.0),), price=V.Price(kappa0=0.0, remembered=10.0),
                     learning=learning, session_minutes=0.0, horizon_days=1.0)
    follow = V.Action(ref="follow_up", kind=V.REPAIR, item_los=("lo_a",), minutes=10.0)
    rest = V.Action(ref="remaining", kind=V.REVIEW, item_los=("lo_b",), minutes=10.0)
    now = V.Action(ref="now", kind=V.SEQUENCE, steps=(follow, rest), item_los=("lo_a", "lo_b"), minutes=20.0)
    later = V.Action(ref="later", kind=V.SEQUENCE, steps=(rest, follow), item_los=("lo_b", "lo_a"), minutes=20.0)
    out = V.evaluate(inputs, [now, later], draws=4, seed="f5").by_ref()
    assert out["now"].terms["crossed_date_reward"] == pytest.approx(M.sigmoid(1.0).item())
    assert out["later"].terms["crossed_date_reward"] == pytest.approx(0.5)
    assert out["now"].q > out["later"].q
    # A probe step keeps its kind: it observes and changes no ability (its information reaches the tail).
    probe_step = V.Action(ref="p", kind=V.PROBE, item_los=("lo_a",), minutes=10.0)
    observe = V.Action(ref="obs", kind=V.SEQUENCE, steps=(probe_step, rest), item_los=("lo_a", "lo_b"), minutes=20.0)
    assert V.evaluate(inputs, [observe], draws=4, seed="f5").by_ref()["obs"].terms["crossed_date_reward"] == \
        pytest.approx(0.5)
    with pytest.raises(ValueError):
        V.Action(ref="bad", kind=V.SEQUENCE, steps=(now,))


def test_f6_the_effect_feature_is_the_difference_of_forecast_probabilities():
    """§8.4: f = 0.99 − 0.5 and ΔG = α + β·f; with α = 0 and β = 0.2 the correction is 0.098 on the logit scale."""

    inputs = _inputs(effect=V.EffectSlope(alpha=(0.0, 0.0), beta=(0.2, 0.0)), reference_forecast=0.5)
    model = V._Model(inputs, 4, "f6")
    correction = model._effect_correction(V.Action(ref="a", kind=V.REVIEW, item_los=("lo_a",), minutes=5.0,
                                                   forecast=0.99))
    assert correction == pytest.approx(np.full(4, 0.2 * 0.49))


def test_f7_a_refinement_cut_by_the_deadline_keeps_the_last_complete_batch():
    inputs = _inputs(topics=(V.Topic("lo_a", 0.3, 0.2, undated_density=1 / 90),), combiner=M.Combiner(),
                     horizon_days=10.0)
    actions = [V.Action(ref="a", kind=V.REVIEW, item_los=("lo_a",), minutes=5.0), V.Action(ref="stop_for_today",
                                                                                          kind=V.STOP)]
    ticks = {"since_keep": None}

    def clock() -> float:
        if ticks["since_keep"] is None:
            return 0.0
        ticks["since_keep"] += 1
        return 0.0 if ticks["since_keep"] <= 1 else 100.0  # the deadline passes inside the larger batch

    def keep_going() -> bool:
        ticks["since_keep"] = 0
        return True

    seen = []
    out = V.evaluate(inputs, actions, draws=4, seed="f7", max_draws=8, keep_going=keep_going, deadline=50.0,
                     clock=clock, on_complete=seen.append)
    assert out.complete and out.draws == 4 and {row.ref for row in out.valued} == {"a", "stop_for_today"}
    assert out.reference is not None and len(seen) == 1
