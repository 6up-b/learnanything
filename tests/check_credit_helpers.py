"""What the committed-check credit tests share: the design's worked fixture and the old path's state-level runs.

The worked fixture (one topic, performance ``σ(η)`` with no retention term, ``γ = ln 1.5`` fixed, ``η₀ = −γ/2``, a
15-minute lesson at mass 0.5 with one check three days after it, one dated use of weight 1 at day 5, no undated use,
no attention price, no tail practice, a return gap of 100 days, beyond the window): the lesson leaves ``η = 0``
(performance 0.5); a check credited as practice adds ``γ`` (0.6); declining leaves ``σ(−γ/2)``.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np

from learnloop.daily_plan.estimates import DEFAULT_FEEDBACK_MINUTES, FALLBACK_PRIOR_MINUTES
from learnloop.router_objective import rollouts as ROL
from learnloop.router_objective import types as OT
from learnloop.router_objective.objective import _Ledger

from tests.ro4_value_helpers import EXACT, W

GAMMA = math.log(1.5)
LO = "lo_a"
LESSON_MINUTES = 15.0
LESSON_MASS = 0.5
CHECK_DAYS = 3.0
DRAWS = 8
SEED = "check-credit"
#: The acceptance posterior: symmetric and tight, so ``p̄`` is near the design's 0.5 (the mixture is checked at the
#: drawn ``p`` and, separately, at exactly 0.5).
ACCEPT = (1e6, 1e6)

#: The design's numbers (nine decimals).
TODAY_ACCEPTED = 0.600000000
FIXED_ACCEPTED = 0.500000000
DECLINED = 0.449489743
TODAY_MIXED = 0.524744871
FIXED_MIXED = 0.474744871
PHANTOM_INCREMENT = 0.050000000

#: One check's minutes with no duration evidence and no authored estimate: the plan estimator's own priors (the
#: answer prior plus the feedback prior), not a new constant.
CHECK_MINUTES = FALLBACK_PRIOR_MINUTES + DEFAULT_FEEDBACK_MINUTES


def fixture_inputs(**overrides: Any) -> OT.Inputs:
    """The worked fixture's frozen belief (``overrides`` replace fields)."""

    base: dict[str, Any] = dict(
        topics=(OT.Topic(lo=LO, eta_mean=-GAMMA / 2, eta_var=0.0),),
        dated=(OT.DatedUse(goal_id="goal", lo=LO, at_days=5.0, weight=1.0),),
        session_minutes=10.0, price=OT.Price(kappa0=0.0, remembered=10.0, remembered_source="test"),
        tail_block_minutes=10.0, tail_block_items=1, horizon_days=7.0, fsrs_weights=W,
        return_gaps_days=(100.0,), combiner=EXACT,
        learning=OT.Learning(gamma=(GAMMA, 0.0), gbar=((0.0, 0.0), (0.0, 0.0))))
    base.update(overrides)
    return OT.Inputs(**base)


def lesson(ref: str = "lesson", *, accept: tuple[float, float] | None = ACCEPT,
           commitments: tuple[tuple[str, float], ...] = (), lo: str = LO, **fields: Any) -> OT.Action:
    """The fixture's lesson (an offer when ``accept`` is given), with the old path's untyped commitments."""

    return OT.Action(ref=ref, kind=OT.LESSON, item_los=(lo,), minutes=LESSON_MINUTES, mass=LESSON_MASS, accept=accept,
                     commitments=commitments, **fields)


def offer_with_check(ref: str = "offer", **fields: Any) -> OT.Action:
    return lesson(ref, commitments=((LO, CHECK_DAYS),), **fields)


def minutes_inputs(**overrides: Any) -> OT.Inputs:
    """The fixture with an attention price and one return inside the window (day 6, after the day-5 use, so the check
    moves no valued use and only its minutes can differ), one tail block per session."""

    base: dict[str, Any] = dict(price=OT.Price(kappa0=0.01, remembered=10.0, remembered_source="test"),
                                horizon_days=5.0, return_gaps_days=(6.0,))
    base.update(overrides)
    return fixture_inputs(**base)


def check_minutes_cost(inputs: OT.Inputs, minutes: float = CHECK_MINUTES) -> float:
    """What a check of ``minutes`` answered at the start of a return session adds to that session's attention cost:
    its own interval from minute 0, plus the tail block it pushes later on the rising price, against the block alone
    (one block of the tail's minutes either way, since the check leaves less than a block of the remembered minutes)."""

    k0, mbar, d = float(inputs.price.kappa0), float(inputs.price.remembered), float(inputs.tail_block_minutes)

    def cost(start: float, length: float) -> float:
        return k0 * ((start + length) ** 2 - start ** 2) / (2.0 * mbar)

    return cost(0.0, minutes) + cost(minutes, d) - cost(0.0, d)


def old_tail_state(inputs: OT.Inputs, commitments: Sequence[tuple[str, float]], *, after: float,
                   draws: int = DRAWS, seed: str = SEED) -> tuple[Any, _Ledger]:
    """The old path's tail from ``after`` (days; the session already at its remembered minutes) with ``commitments``
    as ``(LO, due day)``: the state and ledger the rollout leaves (its private model, read for the state effects a
    value alone cannot show)."""

    model = ROL._Model(inputs, draws, seed)
    state, ledger = model.initial(), _Ledger.zeros(model.k)
    due = [(model.index[lo], np.full(model.k, float(day))) for lo, day in commitments]
    model.run_tail(state, ledger, today_minutes=None, after=np.full(model.k, float(after)),
                   dated_done=np.zeros((model.k, len(model.dated)), dtype=bool), commitments=due)
    return state, ledger


def nine_topics(**overrides: Any) -> OT.Inputs:
    """Nine identical unpractised topics (lo_0 .. lo_8), no valued use: what a commitment's outcome does shows only
    in each topic's FSRS state."""

    topics = overrides.pop("topics", tuple(OT.Topic(lo=f"lo_{i}", eta_mean=0.0, eta_var=0.0) for i in range(9)))
    return fixture_inputs(topics=topics, dated=(), **overrides)


def typed(lo: str = LO, days: float = CHECK_DAYS, *, key: str = "c0", minutes: float = CHECK_MINUTES,
          delivery: tuple[float, float] = (1.0, 0.0), group: str = "retention") -> OT.CheckCommitment:
    """A typed committed check (certain delivery by default: the return and minutes rules alone)."""

    return OT.CheckCommitment(lo=lo, days=days, minutes=minutes, delivery=delivery, key=key, group=group)


def typed_offer(ref: str = "offer", *checks: OT.CheckCommitment, **fields: Any) -> OT.Action:
    return lesson(ref, checks=checks or (typed(),), **fields)
