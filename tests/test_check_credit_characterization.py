"""How the router prices a lesson offer's committed delayed check today, and what the fix must change.

Today (pinned, passing): the rollout answers a committed check at the first day boundary at or past its date as a full
graded practice attempt (mass 1.0), before it asks whether the simulated learner returns, and charges it no minutes;
the offer builder attaches one retention check whether or not any question exists; the ninth commitment reuses the
first one's outcome draw. The design's worked fixture (``tests/check_credit_helpers.py``) gives the accepted branch
0.600000000 where it should give 0.500000000, and the mixed offer 0.524744871 where it should give 0.474744871.

The intended behaviour: a check happens only on a simulated return; it is charged its minutes on the session's clock;
each commitment draws its own outcome (each asserted on both paths: today's on the rollouts, the intended on the
unserved check-credit path); and an offer whose topic has no eligible question credits no check (a strict expected
failure until the activation attaches the offer's sensors: it fails on an assertion about the named defect, and a
broken setup raises something else and fails the test). Last, the owner-copy finding: removing the phantom check can
raise a lesson's value, and the two mechanisms that do it.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.daily_plan import lesson_offer as LO_OFFER
from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.daily_plan import objective_inputs as OI
from learnloop.delayed_checks import attempted_items
from learnloop.learner_protection import withheld_items
from learnloop.router import lesson_suggestions as LS
from learnloop.router_objective import check_value as CV
from learnloop.router_objective import memory as M
from learnloop.router_objective import rollouts as ROL
from learnloop.router_objective import types as OT
from learnloop.teacher import te2 as T2

from tests.check_credit_helpers import (
    CHECK_DAYS,
    DECLINED,
    DRAWS,
    FIXED_ACCEPTED,
    FIXED_MIXED,
    GAMMA,
    LESSON_MINUTES,
    LO,
    PHANTOM_INCREMENT,
    SEED,
    TODAY_ACCEPTED,
    TODAY_MIXED,
    check_minutes_cost,
    fixture_inputs,
    lesson,
    minutes_inputs,
    nine_topics,
    offer_with_check,
    old_tail_state,
    typed,
    typed_offer,
)
from tests.daily_plan_fakes import record_attempt
from tests.router_mixture_helpers import mixture_env
from tests.ro4_value_helpers import W
from tests.router_model_fakes import fake_runtime

LESSON_END = LESSON_MINUTES / ROL.MINUTES_PER_DAY
NINE = tuple((f"lo_{i}", CHECK_DAYS) for i in range(9))


def _branches(inputs: OT.Inputs, *actions: OT.Action) -> dict[str, OT.Action]:
    return ROL.evaluate(inputs, list(actions), draws=DRAWS, seed=SEED).by_ref()


# --- today, pinned ----------------------------------------------------------------------------------------------


def test_today_the_fixtures_accepted_branch_credits_its_check_as_free_practice():
    """The design's worked fixture to nine decimals: the accepted branch 0.6 with its check (the lesson alone 0.5),
    the declined branch ``σ(−γ/2)``, each branch's terms, and the offer the acceptance mixture of the two."""

    out = _branches(fixture_inputs(), offer_with_check(), lesson("plain"))
    checked, plain = out["offer"], out["plain"]
    branches = checked.extra["branches"]
    assert branches["accepted"] == pytest.approx(TODAY_ACCEPTED, abs=1e-9)
    assert branches["declined"] == pytest.approx(DECLINED, abs=1e-9)
    assert plain.extra["branches"]["accepted"] == pytest.approx(FIXED_ACCEPTED, abs=1e-9)
    assert plain.extra["branches"]["declined"] == branches["declined"]
    assert branches["accepted"] - plain.extra["branches"]["accepted"] == pytest.approx(2 * PHANTOM_INCREMENT, abs=1e-9)
    # Every draw values each branch alike (no spread in γ, η or the combiner), so the offer is the mixture at p̄ ...
    p = branches["p_accept"]
    assert checked.q == pytest.approx(p * branches["accepted"] + (1 - p) * branches["declined"], abs=1e-12)
    # ... and at the design's p = 0.5 the two offers are worth the design's numbers.
    assert 0.5 * branches["accepted"] + 0.5 * branches["declined"] == pytest.approx(TODAY_MIXED, abs=1e-9)
    assert (0.5 * plain.extra["branches"]["accepted"] + 0.5 * plain.extra["branches"]["declined"]
            == pytest.approx(FIXED_MIXED, abs=1e-9))
    assert TODAY_MIXED - FIXED_MIXED == pytest.approx(PHANTOM_INCREMENT, abs=1e-9)  # the phantom check's share
    # The ledgers: all of each branch's value is the day-5 use, scored in the tail; no price, no tail practice.
    terms = checked.extra["branch_terms"]
    for name, value in (("accepted", TODAY_ACCEPTED), ("declined", DECLINED)):
        assert terms[name]["tail_reward"] == pytest.approx(value, abs=1e-9)
        assert terms[name]["crossed_date_reward"] == 0.0 and terms[name]["undated_reward"] == 0.0
        assert terms[name]["kappa_integral"] == 0.0 and terms[name]["tail_cost"] == 0.0
        assert terms[name]["terminal"] == 0.0


def test_today_a_check_is_a_full_graded_attempt_at_the_first_boundary_without_a_return():
    """With no return before day 100, the check due at day 3.0104 is still answered, at the day-4 boundary: an FSRS
    review, the learning ``γ`` at mass 1, a belief update, the last-practice time and the lesson window reset."""

    inputs = fixture_inputs()
    due = LESSON_END + CHECK_DAYS
    checked, _ledger = old_tail_state(inputs, [(LO, due)], after=LESSON_END)
    plain, _plain_ledger = old_tail_state(inputs, [], after=LESSON_END)
    assert np.all(checked.last[:, 0] == 4.0) and np.all(plain.last[:, 0] == 0.0)
    assert np.all(checked.practiced[:, 0]) and not np.any(plain.practiced[:, 0])
    assert np.allclose(checked.eta[:, 0] - plain.eta[:, 0], GAMMA, atol=1e-12)
    assert np.all(checked.s[:, 0] > 0.0) and np.all(plain.s[:, 0] == 0.0)
    assert np.all(checked.bel_var[:, 0] < plain.bel_var[:, 0])
    assert np.all(checked.lesson[:, 0] == 0.0)


def test_today_a_check_charges_no_minutes():
    """With an attention price and a return on day 6, the accepted branch's costs are the same with the check as
    without it: the check is answered free, on day 4, outside any session."""

    inputs = minutes_inputs()
    out = _branches(inputs, offer_with_check(), lesson("plain"))
    with_check = out["offer"].extra["branch_terms"]["accepted"]
    without = out["plain"].extra["branch_terms"]["accepted"]
    assert with_check["kappa_integral"] == without["kappa_integral"] > 0.0
    # No undated use, so the tail's whole cost (before C and past it) is its reward less its net value.
    cost = with_check["tail_reward"] - with_check["after"]
    assert cost == pytest.approx(without["tail_reward"] - without["after"], abs=1e-12) and cost > 0.0
    assert with_check["tail_reward"] > without["tail_reward"]  # the free check still moved the day-5 use


def test_today_the_ninth_commitment_reuses_the_first_ones_outcome_draw():
    """Eight outcome columns: on nine identical topics checked at once, the ninth topic's review is the first one's,
    draw for draw, while the second's differs."""

    state, _ledger = old_tail_state(nine_topics(), [(lo, CHECK_DAYS) for lo, _days in NINE], after=0.0, draws=64)
    assert np.array_equal(state.s[:, 0], state.s[:, 8]) and np.array_equal(state.d[:, 0], state.d[:, 8])
    assert np.array_equal(state.bel[:, 0], state.bel[:, 8])
    assert not np.array_equal(state.s[:, 0], state.s[:, 1])


def _offer_env(tmp_path, monkeypatch, lo: str = "lo_m2", item: str = "pi_m2a"):
    """A vault whose offered topic's only question was already attempted, and the offer built at its boundary."""

    env = mixture_env(tmp_path, fake_runtime(), version=LATEST_ALGORITHM_VERSION)
    record_attempt(env.repository, item, lo, env.clock.now(), session_id=env.session_id)
    candidate = LS.Candidate(ref=LS.lesson_ref(lo), learning_object_ids=(lo,), reason="new_goal",
                             predicted_success=0.3, title=lo)
    monkeypatch.setattr(SG, "build_candidates", lambda vault, repository, *, now_iso: ([candidate], {}))
    words = T2.delayed_check_words(env.vault, env.repository, lo, withheld=withheld_items(env.vault, env.repository),
                                   attempted=attempted_items(env.repository))
    offer = LO_OFFER.build(env.vault, env.repository, today=env.today(), now_iso=env.now_iso(), local_hour=9.0,
                           minutes_left=30.0, reentry=False, forced=False)
    return env, words, offer


def test_today_an_offer_is_built_with_a_check_whether_or_not_a_question_exists(tmp_path, monkeypatch):
    env, words, offer = _offer_env(tmp_path, monkeypatch)
    assert words == T2.UNSEEN_NONE
    assert offer.candidate is not None
    checks = LO_OFFER.card(offer.candidate)["checks"]
    assert [(check["lo"], check["purpose"], check["days"]) for check in checks] == [("lo_m2", "retention", 3.0)]
    action = OI.action_for(env.vault, env.repository, offer.candidate, practiced=set(), spread=0.0)
    assert action.commitments == (("lo_m2", 3.0),)


# --- the intended rule, on both paths ------------------------------------------------------------------------------
# The check-credit path (``router_objective.check_value``, unserved until the activation) prices a typed check; the
# rollouts every served decision uses keep today's pricing, pinned beside it.


def test_both_paths_a_check_happens_only_on_a_simulated_return():
    """The worked fixture: today's path credits the check with no return (0.6); the new path, the same check certain
    to be delivered, never answers it before the day-100 return (0.5): the lesson alone, draw for draw."""

    old = _branches(fixture_inputs(), offer_with_check())["offer"].extra["branches"]
    new = CV.evaluate(fixture_inputs(), [typed_offer("offer"), lesson("plain")], draws=DRAWS, seed=SEED).by_ref()
    assert old["accepted"] == pytest.approx(TODAY_ACCEPTED, abs=1e-9)
    assert new["offer"].extra["branches"]["accepted"] == pytest.approx(FIXED_ACCEPTED, abs=1e-9)
    assert new["offer"].q_draws == new["plain"].q_draws
    branches = new["offer"].extra["branches"]
    assert 0.5 * branches["accepted"] + 0.5 * branches["declined"] == pytest.approx(FIXED_MIXED, abs=1e-9)


def test_both_paths_a_check_is_charged_its_minutes_on_the_session_clock():
    """A return on day 6: today's path charges the check nothing; the new path charges its minutes from the start of
    that session and the tail block it pushes later (``check_minutes_cost``)."""

    inputs = minutes_inputs()

    def added(evaluation, with_ref: str, without_ref: str) -> float:
        rows = evaluation.by_ref()
        with_check = rows[with_ref].extra["branch_terms"]["accepted"]
        without = rows[without_ref].extra["branch_terms"]["accepted"]
        return (with_check["tail_reward"] - with_check["after"]) - (without["tail_reward"] - without["after"])

    old = ROL.evaluate(inputs, [offer_with_check(), lesson("plain")], draws=DRAWS, seed=SEED)
    new = CV.evaluate(inputs, [typed_offer("offer"), lesson("plain")], draws=DRAWS, seed=SEED)
    assert added(old, "offer", "plain") == pytest.approx(0.0, abs=1e-12)
    assert added(new, "offer", "plain") == pytest.approx(check_minutes_cost(inputs), abs=1e-12)


def test_both_paths_the_ninth_commitment_draws_its_own_outcome():
    """Today's path: the ninth commitment's review is the first one's, draw for draw. The new path: its own stream,
    on the same nine topics (each check half a minute, so all nine fit one return; the tail's blocks go to a tenth,
    valued topic, so each of the nine moves only by its check)."""

    old, _ledger = old_tail_state(nine_topics(), [(lo, CHECK_DAYS) for lo, _days in NINE], after=0.0, draws=64)
    assert np.array_equal(old.s[:, 0], old.s[:, 8])
    checks = tuple(typed(lo=lo, key=f"c{index}", minutes=0.5) for index, (lo, _days) in enumerate(NINE))
    topics = (*nine_topics().topics, OT.Topic(lo="lo_tail", eta_mean=0.0, eta_var=0.0, undated_density=1.0))
    _ledger, new, _answered = CV.simulate(nine_topics(topics=topics, return_gaps_days=(1.0,)),
                                          lesson("l", accept=None, checks=checks), draws=64, seed=SEED)
    assert not np.array_equal(new.s[:, 0], new.s[:, 8])


# --- intended, a strict expected failure left for the activation ---------------------------------------------------


@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="defect: the offer builder attaches a retention check whether or not any question exists, "
                          "and the rollout credits it")
def test_intended_an_offer_with_no_eligible_question_credits_no_check(tmp_path, monkeypatch):
    env, words, offer = _offer_env(tmp_path, monkeypatch)
    if words != T2.UNSEEN_NONE or offer.candidate is None:
        raise RuntimeError("setup: the offered topic must have no eligible question and an offer must be built")
    action = OI.action_for(env.vault, env.repository, offer.candidate, practiced=set(), spread=0.0)
    lo = action.item_los[0]
    inputs = fixture_inputs(topics=(OT.Topic(lo=lo, eta_mean=-GAMMA / 2, eta_var=0.0),),
                            dated=(OT.DatedUse(goal_id="goal", lo=lo, at_days=5.0, weight=1.0),))
    alone = replace(action, ref="alone", commitments=())
    out = _branches(inputs, action, alone)
    assert out[action.ref].extra["branches"]["accepted"] == pytest.approx(
        out["alone"].extra["branches"]["accepted"], abs=1e-12)


# --- the owner-copy finding: the phantom check can lower a lesson's value ----------------------------------------
# On the owner's copy the report's paired scenario rated lessons higher once the phantom check was gone. The two
# mechanisms below, each on one topic with no return in the window, reproduce that direction; the record
# (docs/reviews/algorithm-mvp-0.62.md) gives their numbers. The combiner here is linear at fixed coefficients
# (a0, aA, aR) = (0, 1, 0.5), so a practised topic's performance is σ(0.5·η + 0.5·logit R) and an unpractised one's
# σ(η), with no forgetting.

PHANTOM_COMBINER = M.Combiner(mean=(0.0, 1.0, 0.5), variance=(0.0, 0.0, 0.0), source="test")
FINDING_SEED = "s"


def _finding_inputs(topic: OT.Topic) -> OT.Inputs:
    return OT.Inputs(topics=(topic,), dated=(), session_minutes=10.0,
                     price=OT.Price(kappa0=0.0, remembered=10.0, remembered_source="test"),
                     tail_block_minutes=10.0, tail_block_items=1, horizon_days=30.0, fsrs_weights=W,
                     return_gaps_days=(100.0,), combiner=PHANTOM_COMBINER,
                     learning=OT.Learning(gamma=(0.2, 0.0), gbar=((0.0, 0.0), (0.0, 0.0))))


def _paired_ledgers(topic: OT.Topic, **options):
    """The accepted branch (the lesson with its check, no acceptance mixing) under the rollouts' old credit and under
    the check-credit path with the topic's check never delivered (no question, 19 failures)."""

    inputs = _finding_inputs(topic)
    old = OT.Action(ref="o", kind=OT.LESSON, item_los=(topic.lo,), minutes=LESSON_MINUTES, mass=0.5,
                    commitments=((topic.lo, CHECK_DAYS),))
    new = replace(old, commitments=(), checks=(typed(lo=topic.lo, delivery=(0.0, 20.0)),))
    before, _effect, _minutes = ROL._Model(inputs, DRAWS, FINDING_SEED, **options)._do(old)
    after, _state, _answered = CV.simulate(inputs, new, draws=DRAWS, seed=FINDING_SEED, **options)
    return before, after


TERMS = ("crossed", "undated_action", "kappa_action", "tail_reward", "tail_cost", "terminal_reward", "terminal_cost")


@pytest.mark.parametrize("consistent", [False, True], ids=["mvp-0.49-draw", "served-draw"])
def test_finding_a_first_graded_attempt_switches_an_unpractised_topic_onto_forgetting(consistent):
    """An unpractised topic with AD's ``η = 2``: the phantom check is its first graded attempt. It adds ``γ`` to ``η``
    but sets ``practiced`` and a first-review stability (2.31 days on a success), so from then the topic reads
    ``σ(0.5·η + 0.5·logit R)`` with ``R`` decaying, below the unpractised ``σ(η)`` that never forgets. Removing the
    phantom raises the accepted branch by 3.917, all of it in the undated uses after the action (``tail_reward``
    +1.179, ``terminal_reward`` +2.738), under either review draw (a first attempt reads AD's predictive both ways)."""

    topic = OT.Topic(lo=LO, eta_mean=2.0, eta_var=0.0, undated_density=1.0)
    before, after = _paired_ledgers(topic, consistent_review_draw=consistent)
    moved = {name: float(getattr(after, name).mean() - getattr(before, name).mean()) for name in TERMS}
    assert moved["tail_reward"] == pytest.approx(1.178857, abs=1e-6)
    assert moved["terminal_reward"] == pytest.approx(2.738082, abs=1e-6)
    assert all(moved[name] == 0.0 for name in ("crossed", "undated_action", "kappa_action", "tail_cost",
                                               "terminal_cost"))
    assert float(after.q.mean() - before.q.mean()) == pytest.approx(3.916939, abs=1e-6)
    # The mechanism at state level: the phantom leaves the topic practised with a decaying memory.
    state, _ledger = old_tail_state(_finding_inputs(topic), [(LO, LESSON_END + CHECK_DAYS)], after=LESSON_END)
    assert np.all(state.practiced[:, 0]) and np.all(state.last[:, 0] == 4.0)
    _ledger, unchecked, _answered = CV.simulate(_finding_inputs(topic), replace(
        lesson("l", accept=None), checks=(typed(delivery=(0.0, 20.0)),)), draws=DRAWS, seed=FINDING_SEED)
    assert not np.any(unchecked.practiced[:, 0])


def test_finding_under_the_mvp_0_49_draw_a_phantom_lapse_collapses_a_practised_topics_memory():
    """A practised topic (stability 30, two days since its review) with AD's ``η = −2``. Under the pre-mvp-0.50 review
    draw, which the step-5 report's paired scenario used (it passed no rollout options), the phantom check's outcome
    is drawn from AD's ``σ(η)`` ≈ 0.12, whatever FSRS's ``R`` ≈ 0.99 says: mostly a lapse, and FSRS's lapse update
    cuts the stability, so the topic's long-run ``R`` and performance fall. Removing the phantom raises the accepted
    branch by 8.163. Under the draw decisions have served since mvp-0.50 (the memory model's own ``P(perform)``) the
    check is mostly a success and the phantom inflates the branch instead (removing it lowers it by 0.164): the
    sign the report saw depends on the options it ran with."""

    topic = OT.Topic(lo=LO, eta_mean=-2.0, eta_var=0.0, practiced=True, stability=30.0, elapsed_days=2.0,
                     undated_density=1.0)
    before, after = _paired_ledgers(topic)
    assert float(after.tail_reward.mean() - before.tail_reward.mean()) == pytest.approx(3.913109, abs=1e-6)
    assert float(after.terminal_reward.mean() - before.terminal_reward.mean()) == pytest.approx(4.250329, abs=1e-6)
    assert float(after.q.mean() - before.q.mean()) == pytest.approx(8.163438, abs=1e-6)
    served_before, served_after = _paired_ledgers(topic, consistent_review_draw=True)
    assert float(served_after.q.mean() - served_before.q.mean()) == pytest.approx(-0.164126, abs=1e-6)
