"""The plan's option names that every layer reads: a lesson offer's block subtype and the prefix of its ref, and the
stop option's ref.

Standard library only, and nothing of LearnLoop: the router's log, the stores, the follow-up workflow, the objective
and ``why`` each read these strings, and a cold reader such as ``why`` would otherwise load the objective's numeric
types (NumPy, the FSRS module) for one string. ``router_objective.types`` and ``daily_plan.types`` re-export them.
"""

from __future__ import annotations

#: Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): a lesson offer, a plan block of its own (no items, no reading) whose
#: card the learner answers; its candidate id is ``lesson_offer:<LO>``.
LESSON_OFFER_SUBTYPE = "lesson_offer"
LESSON_OFFER_PREFIX = f"{LESSON_OFFER_SUBTYPE}:"
#: The plan's stop option: offered when minutes_left < 5 or nothing is feasible.
STOP_FOR_TODAY = "stop_for_today"


def is_offer_subtype(subtype: str | None) -> bool:
    """Whether a block subtype is a lesson offer's. Anything but a string or None raises: a candidate passed here
    would otherwise read as "not an offer" without a word (``daily_plan.lesson_offer.is_offer`` takes a candidate)."""

    if subtype is not None and not isinstance(subtype, str):
        raise TypeError(f"is_offer_subtype takes a block subtype (str or None), not {type(subtype).__name__}")
    return subtype == LESSON_OFFER_SUBTYPE


__all__ = ["LESSON_OFFER_PREFIX", "LESSON_OFFER_SUBTYPE", "STOP_FOR_TODAY", "is_offer_subtype"]
