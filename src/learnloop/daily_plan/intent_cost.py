"""The intent control's projected cost (spec §5.2): "about N min/day of reviews".

§6.4's estimate of each covered item with memory state, at its recall target
after the choice (§5.3's effective due), as §6.3's review-load projection
counts reviews over the plan's horizon. Pause, Reference and Let go cost no
reviews; "Check once" costs one check. Display only: nothing here is stored
or served. Lives with the plan (its estimator and projection) and is handed
to ``learnloop.intent.control`` as a function, so intent never imports the
plan.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from learnloop.clock import Clock, SystemClock
from learnloop.daily_plan.admission import ReviewItem, projected_review_load
from learnloop.daily_plan.estimates import Estimator, load_duration_evidence
from learnloop.intent.control import CostFunction
from learnloop.scheduling.intent.model import CHOICE_DISPOSITION
from learnloop.scheduling.intent.recall_targets import effective_due, load_anchors
from learnloop.scheduling.intent.resolution import ItemIntent


@dataclass
class CostContext:
    """What the cost reads, loaded once for every choice of one scope."""

    states: Mapping[str, Any]
    anchors: Mapping[str, tuple[str, str]]
    weights: tuple[float, ...]
    estimator: Estimator
    now: datetime
    horizon_days: int


def load_cost_context(vault: Any, repository: Any, *, clock: Clock | None = None) -> CostContext:
    from learnloop.params.fitted_params import resolve_fsrs_weights

    plan = vault.config.plan
    with repository.connection() as connection:
        anchors = load_anchors(connection)
    return CostContext(
        states=repository.practice_item_states(),
        anchors=anchors,
        weights=tuple(resolve_fsrs_weights(repository)),
        estimator=Estimator(
            evidence=load_duration_evidence(repository, latency_cap_minutes=float(plan.latency_cap_minutes)),
            read_words_per_minute=int(plan.read_words_per_minute),
        ),
        now=(clock or SystemClock()).now(),
        horizon_days=int(plan.load_horizon_days),
    )


def projected_cost(
    vault: Any, context: CostContext, choice: str, after: Mapping[str, ItemIntent]
) -> tuple[float | None, str]:
    if choice in CHOICE_DISPOSITION:
        return 0.0, "no reviews"
    if choice == "check_once":
        minutes = min(
            (context.estimator.item_minutes(vault, item_id) for item_id in after if item_id in vault.practice_items),
            default=None,
        )
        if minutes is None:
            return None, "one check"
        return float(minutes), f"one check, about {max(1, round(minutes))} min"
    recall_on = bool(vault.config.intent.recall_targets_enabled)
    reviews = []
    for item_id, intent in after.items():
        state = context.states.get(item_id)
        if state is None or not getattr(state, "active", True) or state.due_at is None or state.stability is None:
            continue
        if intent.excluded:
            continue
        target = intent.recall_target if recall_on else 0.90
        anchor = context.anchors.get(item_id)
        due = effective_due(
            due_at=state.due_at, anchor_at=anchor[0] if anchor else None, target=target, weights=context.weights
        ).due
        reviews.append(
            ReviewItem(
                practice_item_id=item_id,
                due_at=due.strftime("%Y-%m-%dT%H:%M:%SZ") if due is not None else state.due_at,
                last_review_at=state.last_attempt_at,
                est_minutes=context.estimator.item_minutes(vault, item_id),
            )
        )
    if not reviews:
        return 0.0, "no reviews yet"
    load = projected_review_load(reviews, now=context.now, horizon_days=context.horizon_days)
    if load < 0.5:
        return load, "under 1 min/day of reviews"
    return load, f"about {round(load)} min/day of reviews"


def cost_function(vault: Any, repository: Any, *, clock: Clock | None = None) -> CostFunction:
    """The control's cost function for one read (its context loaded once)."""

    context = load_cost_context(vault, repository, clock=clock)
    return lambda choice, after: projected_cost(vault, context, choice, after)


__all__ = ["CostContext", "cost_function", "load_cost_context", "projected_cost"]
