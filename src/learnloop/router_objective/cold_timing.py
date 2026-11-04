"""RO0 row 10 (spec_router_objective_v1 §4): how a cold check's target delay was chosen, and why one was not served.

The chain already holds the dates, states and picks: ``decision_measurement_events``,
``cold_measurement_opportunity_decisions`` (its ``decision`` is already typed), ``lesson_checks`` and commitments, whose
provenance says ``dated_by``. This adds what RO5's lag calibration needs and they lack: the delay's inputs
(:func:`delay_receipt`) and a type for each reason a measurement went unserved (:func:`non_service_type`). A type is
kept beside the reason, which keeps its words. Nothing serving reads either.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
from typing import Any

DELAY_VERSION = "check_delay_v1"
STRUCTURALLY_REFUSED = "structurally_refused"
POLICY_REFUSED = "policy_refused"
OPERATIONALLY_UNAVAILABLE = "operationally_unavailable"
LEARNER_DECLINED = "learner_declined"
ANSWERED_UNREAD = "answered_unread"
#: A replacement check's reason carries this prefix (``daily_plan.measurement.REPLACEMENT``).
_REPLACEMENT_PREFIX = "replacement:"
#: Every reason a measurement states today. One not here stays untyped and the report shows it.
_TYPES: Mapping[str, str] = {
    "no_learning_object": STRUCTURALLY_REFUSED,
    "no_question": STRUCTURALLY_REFUSED,
    "no_candidates": STRUCTURALLY_REFUSED,
    "check_once_off": POLICY_REFUSED,
    "check_replaced": POLICY_REFUSED,
    "refused_candidates": POLICY_REFUSED,
    "candidates_held": POLICY_REFUSED,
    "arrange_failed": OPERATIONALLY_UNAVAILABLE,
    "plan_minutes_exhausted": OPERATIONALLY_UNAVAILABLE,
    "not_in_pool": OPERATIONALLY_UNAVAILABLE,
    "commitment_closed": LEARNER_DECLINED,
    "answer_not_delayed": ANSWERED_UNREAD,
    "answer_other_objective": ANSWERED_UNREAD,
}


def non_service_type(reason: str) -> str | None:
    """The type of an unserved check's reason, or None for one not typed yet."""

    text = str(reason or "")
    if text.startswith(_REPLACEMENT_PREFIX):
        text = text[len(_REPLACEMENT_PREFIX):]
    return _TYPES.get(text)


def delay_receipt(vault: Any, *, days: float, basis: str, purpose: str) -> str:
    """How a check's delay was chosen: the rule, its inputs in force, and whether the cap decided it."""

    config = vault.config.teacher.delayed
    cap = float(config.max_wait_days)
    return json.dumps({
        "version": DELAY_VERSION, "chosen_by": basis, "purpose": purpose, "days": round(float(days), 4),
        "target_retrievability": float(config.target_retrievability),
        "fallback_days": float(config.fallback_retention_days if purpose == "retention" else config.fallback_transfer_days),
        "max_wait_days": cap, "capped": float(days) >= cap,
    }, sort_keys=True, separators=(",", ":"))


__all__ = ["ANSWERED_UNREAD", "DELAY_VERSION", "LEARNER_DECLINED", "OPERATIONALLY_UNAVAILABLE", "POLICY_REFUSED",
           "STRUCTURALLY_REFUSED", "delay_receipt", "non_service_type"]
