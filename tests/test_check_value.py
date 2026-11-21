"""The check-credit rollout path (``router_objective.check_value``; every decision's rollouts from mvp-0.62): a
lesson's typed committed check happens only on a simulated return, on or after its date and inside the window, is
charged its minutes on the session's clock, and draws its delivery and outcome from streams of its own. Every action
without typed checks is valued exactly as the rollouts value it. Pure numerics; no vault.
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pytest

from learnloop.daily_plan import engine
from learnloop.router_objective import check_value as CV
from learnloop.router_objective import diagnostic_payload as DP
from learnloop.router_objective import diagnostic_value as DV
from learnloop.router_objective import rollouts as ROL
from learnloop.router_objective import types as OT

from tests.check_credit_helpers import (
    CHECK_MINUTES,
    DRAWS,
    GAMMA,
    LESSON_MINUTES,
    LO,
    SEED,
    fixture_inputs,
    lesson,
    nine_topics,
    typed,
    typed_offer,
)
from tests.ro4_value_helpers import _inputs as ro4_inputs
from tests.rospeed_ad_link_helpers import OPTIONS, _actions, _inputs as linked_inputs, _rows

LESSON_END = LESSON_MINUTES / ROL.MINUTES_PER_DAY


def _cost(inputs: OT.Inputs, start: float, length: float) -> float:
    k0, mbar = float(inputs.price.kappa0), float(inputs.price.remembered)
    return k0 * ((start + length) ** 2 - start ** 2) / (2.0 * mbar)


def _priced(**overrides) -> OT.Inputs:
    """The worked fixture with an attention price and one tail block per session (overrides on top)."""

    base = dict(price=OT.Price(kappa0=0.01, remembered=10.0, remembered_source="test"))
    base.update(overrides)
    return fixture_inputs(**base)


def _path(inputs: OT.Inputs, *checks: OT.CheckCommitment, draws: int = DRAWS, seed: str = SEED):
    return CV.simulate(inputs, lesson("lesson", accept=None, checks=tuple(checks)), draws=draws, seed=seed)


# --- nothing else moves ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("option", sorted(OPTIONS))
def test_actions_without_typed_checks_are_valued_identically_on_both_paths(option):
    """Every action kind (stop, review, an offer of practice, a probe with its repair, reading, a lesson, a
    sequence), on AD's link with each rollout option, and the reference row: the same bytes on both paths."""

    inputs, actions = linked_inputs(12), _actions(12)
    old = ROL.evaluate(inputs, actions, draws=8, seed="both-paths", **OPTIONS[option])
    new = CV.evaluate(inputs, actions, draws=8, seed="both-paths", **OPTIONS[option])
    assert _rows(new) == _rows(old)


def test_a_lesson_offer_without_checks_and_the_eve_of_exam_case_are_unchanged():
    gamma = math.log(0.79 / 0.21) - math.log(0.78 / 0.22)
    inputs = ro4_inputs(dated=(OT.DatedUse(goal_id="exam", lo="lo_a", at_days=1.0, weight=1.0),),
                        learning=OT.Learning(gamma=(gamma, 0.0), gbar=((0.0, 0.0), (0.0, 0.0))))
    actions = [OT.Action(ref="cram", kind=OT.NEW_PRACTICE, item_los=("lo_a",), minutes=10.0),
               OT.Action(ref="stop_for_today", kind=OT.STOP),
               OT.Action(ref="offer", kind=OT.LESSON, item_los=("lo_a",), minutes=15.0, mass=0.5, accept=(2.0, 3.0))]
    assert _rows(CV.evaluate(inputs, actions, draws=4, seed="eve")) == _rows(
        ROL.evaluate(inputs, actions, draws=4, seed="eve"))


@pytest.mark.parametrize("delivery", [(0.0, 1.0), (0.0, 20.0)])
def test_an_undelivered_check_is_no_event(delivery):
    """A check whose delivery is zero (no question, and the legacy sample's 19 missing on top) adds no dose, no
    information and no minutes: the lesson alone, draw for draw, on both paths."""

    inputs = _priced(return_gaps_days=(1.0,))
    checked = CV.evaluate(inputs, [typed_offer("offer", typed(delivery=delivery))], draws=DRAWS, seed=SEED)
    plain_new = CV.evaluate(inputs, [lesson("offer")], draws=DRAWS, seed=SEED)
    plain_old = ROL.evaluate(inputs, [lesson("offer")], draws=DRAWS, seed=SEED)
    assert _rows(checked) == _rows(plain_new) == _rows(plain_old)


# --- when a check happens ----------------------------------------------------------------------------------------


@pytest.mark.parametrize(("gaps", "days", "answered"), [
    ((1.0,), 3.0, 4.0),        # due 3.0104: waits for the day-4 return, not the day-3 one
    ((1.0,), 2.9, 3.0),        # due 2.9104: answered on the day-3 return
    ((7.0,), 3.0, 7.0),        # the first return on or after its date is day 7: answered then, not on day 4
    ((100.0,), 3.0, math.nan),  # no return inside the window: never answered
])
def test_a_check_is_answered_on_the_first_return_on_or_after_its_date(gaps, days, answered):
    _ledger, state, (when,) = _path(fixture_inputs(return_gaps_days=gaps), typed(days=days))
    expected = answered + CHECK_MINUTES / ROL.MINUTES_PER_DAY
    if math.isnan(answered):
        assert np.all(np.isnan(when)) and not np.any(state.practiced[:, 0])
    else:
        assert np.allclose(when, expected, rtol=0, atol=1e-12) and np.all(state.practiced[:, 0])


def test_an_answered_check_is_a_graded_attempt_at_its_end_and_displaces_the_tail_block():
    """The day-7 return's session is the check alone (the remembered minutes are its 3.5): one FSRS review, the
    learning ``γ`` at mass 1 (``η``: −γ/2 + the lesson's γ/2 + γ), a belief update, the last-practice time at its end
    and the lesson window reset. Undelivered, the same session is one tail block instead, ending 10 minutes in."""

    inputs = fixture_inputs(return_gaps_days=(7.0,), price=OT.Price(kappa0=0.0, remembered=CHECK_MINUTES))
    _ledger, checked, (when,) = _path(inputs, typed())
    _ledger, plain, _none = _path(inputs, typed(delivery=(0.0, 1.0)))
    end = 7.0 + CHECK_MINUTES / ROL.MINUTES_PER_DAY
    assert np.allclose(when, end, rtol=0, atol=1e-12) and np.allclose(checked.last[:, 0], end, rtol=0, atol=1e-12)
    assert np.allclose(plain.last[:, 0], 7.0 + 10.0 / ROL.MINUTES_PER_DAY, rtol=0, atol=1e-12)
    assert np.all(checked.practiced[:, 0]) and np.allclose(checked.eta[:, 0], GAMMA, atol=1e-12)
    assert np.all(checked.s[:, 0] > 0.0) and np.all(checked.lesson[:, 0] == 0.0)
    assert np.all(checked.bel_var[:, 0] <= 1e-12)


def test_two_checks_that_do_not_fit_one_session_wait_for_the_next_return():
    """Two six-minute checks against ten remembered minutes, daily returns: the first answered on day 4, the second
    deferred to day 5 (never free); each costs its minutes from the session's start and pushes that day's tail block
    later on the rising price."""

    inputs = _priced(return_gaps_days=(1.0,))
    first, second = typed(key="c0", minutes=6.0), typed(key="c1", minutes=6.0)
    ledger, _state, (when_first, when_second) = _path(inputs, first, second)
    plain, _s, _w = _path(inputs, replace(first, delivery=(0.0, 1.0)), replace(second, delivery=(0.0, 1.0)))
    assert np.allclose(when_first, 4.0 + 6.0 / ROL.MINUTES_PER_DAY, rtol=0, atol=1e-12)
    assert np.allclose(when_second, 5.0 + 6.0 / ROL.MINUTES_PER_DAY, rtol=0, atol=1e-12)
    per_day = _cost(inputs, 0.0, 6.0) + _cost(inputs, 6.0, 10.0) - _cost(inputs, 0.0, 10.0)
    added = (ledger.tail_cost + ledger.terminal_cost) - (plain.tail_cost + plain.terminal_cost)
    assert np.allclose(added, 2 * per_day, rtol=0, atol=1e-12)
    # The return draws are the rollouts' own.
    assert np.array_equal(CV._CheckModel(inputs, DRAWS, SEED).theta.return_days,
                          ROL._Model(inputs, DRAWS, SEED).theta.return_days)


def test_a_check_crossing_C_splits_its_cost_and_a_use_it_crosses_sees_the_state_before_it():
    """C is 2.88 minutes into the day-6 session: the check's first 2.88 minutes are the tail's cost, the rest
    ``T_C``'s; the dated use at day 6.001 (inside the check) is scored on the state before the answer."""

    inputs = _priced(return_gaps_days=(6.0,), horizon_days=6.002,
                     dated=(OT.DatedUse(goal_id="goal", lo=LO, at_days=6.001, weight=1.0),))
    ledger, _state, (when,) = _path(inputs, typed())
    plain, _s, _w = _path(inputs, typed(delivery=(0.0, 1.0)))
    before_c = (6.002 - 6.0) * ROL.MINUTES_PER_DAY
    assert np.allclose(when, 6.0 + CHECK_MINUTES / ROL.MINUTES_PER_DAY, rtol=0, atol=1e-12)
    session = _cost(inputs, CHECK_MINUTES, 10.0) - _cost(inputs, 0.0, 10.0)  # day 6 starts before C: the tail's
    assert np.allclose(ledger.tail_cost - plain.tail_cost, _cost(inputs, 0.0, before_c) + session, rtol=0, atol=1e-12)
    assert np.allclose(ledger.terminal_cost - plain.terminal_cost,
                       _cost(inputs, before_c, CHECK_MINUTES - before_c), rtol=0, atol=1e-12)
    # The use is crossed by the check's end: scored at 0.5 (the lesson's state), not 0.6 (after the check).
    assert np.allclose(ledger.tail_reward, 0.5, rtol=0, atol=1e-9)
    assert np.array_equal(ledger.tail_reward, plain.tail_reward)


def test_a_check_ending_past_the_horizon_is_charged_its_in_window_minutes_and_answers_nothing():
    """``C + H`` is 6.002 days: a check started at day 6 would end 3.5 minutes later, past it; only its 2.88
    in-window minutes are charged (past C, so ``T_C``'s) and it has no answer effect."""

    inputs = _priced(return_gaps_days=(6.0,), horizon_days=3.001, dated=())
    ledger, state, (when,) = _path(inputs, typed())
    plain, plain_state, _w = _path(inputs, typed(delivery=(0.0, 1.0)))
    inside = (6.002 - 6.0) * ROL.MINUTES_PER_DAY
    assert np.all(np.isnan(when))
    assert np.array_equal(state.eta, plain_state.eta)  # the session after it is the tail's either way: no answer effect
    assert np.array_equal(ledger.tail_cost, plain.tail_cost)
    session = _cost(inputs, inside, 10.0) - _cost(inputs, 0.0, 10.0)
    assert np.allclose(ledger.terminal_cost - plain.terminal_cost, _cost(inputs, 0.0, inside) + session, rtol=0,
                       atol=1e-12)


# --- streams -----------------------------------------------------------------------------------------------------


NINE = tuple(typed(lo=f"lo_{i}", key=f"c{i}", minutes=0.5) for i in range(9))


def test_each_commitment_draws_its_own_outcome_and_insertion_or_order_moves_none():
    """Nine checks on nine identical topics (the tail's blocks go to a tenth, valued topic, so each of the nine moves
    only by its check): the ninth draws its own outcome; adding it, or reversing the order they are listed in, moves
    none of the others."""

    topics = (*nine_topics().topics, OT.Topic(lo="lo_tail", eta_mean=0.0, eta_var=0.0, undated_density=1.0))
    inputs = nine_topics(topics=topics, return_gaps_days=(1.0,))
    _l, eight, _w = _path(inputs, *NINE[:8], draws=64)
    _l, nine, _w = _path(inputs, *NINE, draws=64)
    _l, shuffled, _w = _path(inputs, *reversed(NINE), draws=64)
    assert not np.array_equal(nine.s[:, 0], nine.s[:, 8])
    for i in range(8):
        assert np.array_equal(eight.s[:, i], nine.s[:, i]) and np.array_equal(eight.bel[:, i], nine.bel[:, i])
    for field in ("s", "d", "bel", "bel_var", "eta", "last"):
        assert np.array_equal(getattr(nine, field), getattr(shuffled, field)), field


def test_two_checks_on_one_topic_are_two_commitments():
    inputs = fixture_inputs(return_gaps_days=(1.0,))
    _l, state, (first, second) = _path(inputs, typed(key="c0", days=1.0, minutes=1.0),
                                       typed(key="c1", days=3.0, minutes=1.0))
    _l, one, _w = _path(inputs, typed(key="c0", days=1.0, minutes=1.0))
    assert np.allclose(first, 2.0 + 1.0 / ROL.MINUTES_PER_DAY, rtol=0, atol=1e-12)
    assert np.allclose(second, 4.0 + 1.0 / ROL.MINUTES_PER_DAY, rtol=0, atol=1e-12)
    assert np.allclose(state.eta[:, 0] - one.eta[:, 0], GAMMA, atol=1e-12)
    assert not np.array_equal(CV.uniforms(SEED, "noise:commit_outcome:c0", 64),
                              CV.uniforms(SEED, "noise:commit_outcome:c1", 64))


def test_delivery_and_outcome_streams_are_apart_and_keep_their_prefixes():
    names = ["noise:commit_outcome:c0", "noise:commit_delivery:c0", "theta:commit_delivery:retention"]
    arrays = [CV.uniforms(SEED, name, 16) for name in names]
    assert all(not np.array_equal(a, b) for i, a in enumerate(arrays) for b in arrays[i + 1:])
    for name in names:
        assert np.array_equal(CV.uniforms(SEED, name, 32)[:16], CV.uniforms(SEED, name, 16))
    # The rollouts' own streams are untouched (none of these names is theirs).
    assert not {"noise:commitments", "noise:outcome", "noise:action_outcome"} & set(names)


def test_refining_the_draws_keeps_every_earlier_draws_value():
    """``K`` to ``2K``: each of the first ``K`` draws of an offer with checks is valued exactly as before."""

    inputs = _priced(return_gaps_days=(1.0, 2.0, 4.0), horizon_days=10.0)
    offer = typed_offer("offer", typed(key="c0", delivery=(2.0, 3.0)), typed(key="c1", days=5.0, delivery=(1.0, 1.0)))
    small = CV.evaluate(inputs, [offer], draws=8, seed=SEED).by_ref()["offer"]
    large = CV.evaluate(inputs, [offer], draws=16, seed=SEED).by_ref()["offer"]
    assert large.q_draws[:8] == small.q_draws


def test_the_delivery_posterior_is_sampled_once_per_path_and_shared_within_its_group():
    u = CV.uniforms(SEED, "theta:commit_delivery:retention", 4000)
    assert np.array_equal(CV.propensity(u, (0.0, 3.0)), np.zeros(4000))
    assert np.array_equal(CV.propensity(u, (2.0, 0.0)), np.ones(4000))
    assert CV.propensity(np.array([0.5]), (2.0, 2.0))[0] == pytest.approx(0.5, abs=1e-9)
    inputs = fixture_inputs(return_gaps_days=(1.0,), topics=(OT.Topic(lo=LO, eta_mean=0.0, eta_var=0.0),
                                                             OT.Topic(lo="lo_b", eta_mean=0.0, eta_var=0.0)))
    a, b = typed(key="c0", delivery=(1.0, 1.0), minutes=1.0), typed(lo="lo_b", key="c1", delivery=(1.0, 1.0),
                                                                    minutes=1.0)
    _l, _s, (when_a, when_b) = _path(inputs, a, b, draws=400)
    delivered_a, delivered_b = ~np.isnan(when_a), ~np.isnan(when_b)
    p = CV.propensity(CV.uniforms(SEED, "theta:commit_delivery:retention", 400), (1.0, 1.0))
    assert np.array_equal(delivered_a, CV.uniforms(SEED, "noise:commit_delivery:c0", 400) < p)
    assert np.array_equal(delivered_b, CV.uniforms(SEED, "noise:commit_delivery:c1", 400) < p)
    assert not np.array_equal(delivered_a, delivered_b)  # one propensity, two Bernoullis
    assert 0.35 < delivered_a.mean() < 0.65


def test_the_fit_tolerance_is_the_plans():
    assert CV.FIT_TOLERANCE_MINUTES == engine._EPS


# --- the typed inputs, and why no live decision reaches this path ------------------------------------------------


def test_the_typed_check_is_numbers_only_and_validated():
    names = {field for field in OT.CheckCommitment.__dataclass_fields__}
    assert names == {"lo", "days", "minutes", "delivery", "key", "purpose", "group"}
    with pytest.raises(ValueError, match="key"):
        typed(key="")
    with pytest.raises(ValueError, match="both zero"):
        typed(delivery=(0.0, 0.0))
    with pytest.raises(ValueError, match="non-negative"):
        typed(minutes=-1.0)
    with pytest.raises(ValueError, match="only a lesson"):
        OT.Action(ref="r", kind=OT.REVIEW, item_los=(LO,), checks=(typed(),))
    with pytest.raises(ValueError, match="never both"):
        lesson("l", commitments=((LO, 3.0),), checks=(typed(),))
    with pytest.raises(ValueError, match="own key"):
        lesson("l", checks=(typed(key="c"), typed(key="c", days=5.0)))


def test_the_rollouts_refuse_typed_checks_and_this_path_refuses_untyped_ones():
    inputs = fixture_inputs()
    offer = typed_offer("offer")
    with pytest.raises(ValueError, match="typed committed checks"):
        ROL.evaluate(inputs, [offer], draws=DRAWS, seed=SEED)
    with pytest.raises(ValueError, match="typed committed checks"):
        ROL.evaluate(inputs, [OT.Action(ref="n", kind=OT.NEW_PRACTICE, item_los=(LO,), minutes=5.0, accept=(1.0, 1.0),
                                        declined=offer)], draws=DRAWS, seed=SEED)
    with pytest.raises(ValueError, match="untyped commitments"):
        CV.evaluate(inputs, [lesson("old", commitments=((LO, 3.0),))], draws=DRAWS, seed=SEED)
    # The G2 evaluator prices an offer's accepted branch with typed checks through this path's model (the
    # activation's adapter): its accepted value is this path's, not a refusal and not the rollouts' old credit.
    payload = DP.DiagnosticProbe(
        topic=LO, hypotheses=(DP.Hypothesis("h1", 0.9, DP.GAP), DP.Hypothesis(DP.OPEN_HYPOTHESIS, 0.1, DP.UNKNOWN)),
        prior_basis="literal", channel=DP.Channel(results=("a", "b"), rows=(("h1", (0.9, 0.1)),
                                                                            (DP.OPEN_HYPOTHESIS, (0.5, 0.5))),
                                                  version="v", source="literal"),
        repairs=(DP.RepairOption("r1", OT.Action(ref="r1", kind=OT.REPAIR, item_los=(LO,), minutes=5.0),
                                 frozenset({"h1"})),))
    probe = OT.Action(ref="probe", kind=OT.PROBE, item_los=(LO,), minutes=3.0, diagnostic=payload)
    valued = DV.evaluate_probe(inputs, replace(offer, declined=probe), decisions=DP.DESIGN_RECOMMENDATIONS,
                               draws=DRAWS, seed=SEED)
    own, _state, _times = CV.simulate(inputs, offer, draws=DRAWS, seed=SEED)
    assert valued.record["offer"]["accepted"] == pytest.approx(float(own.q.mean()), abs=1e-12)
    old_credit, _s, _t = CV.simulate(inputs, replace(offer, checks=()), draws=DRAWS, seed=SEED)
    assert valued.record["offer"]["accepted"] == pytest.approx(float(old_credit.q.mean()), abs=1e-12)  # no return
