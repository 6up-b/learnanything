"""The valuer ``find_practice`` is given for the value intents (spec §8.3; S2a).

``find_practice`` never imports the service (SC12): the adapters inject
:func:`make_valuer`'s callable. For one request it reads the rival-hypothesis
spaces (one problem each), builds every kept candidate's tables per problem
(items through the item-EIG adapters, unimported exercises through the
discrimination screen, retention checks on the pinned grader channel), applies
the exposure rule for the independent intents, and returns the valuation
receipt: per problem, the valued, bounded and unvalued groups, the checks that
clear the stop (no count cap) and the verdict translated as the decision-value
spec's §6.5 translates it.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.instructional.exposure import independent_check_eligibility
from learnloop.instructional.screen import screen_exercises
from learnloop.instructional.valuation import (
    exercise_input,
    item_input,
    open_hypotheses,
    value_candidates,
)
from learnloop.vault.models import LoadedVault

#: What a system-initiated caller gets for each verdict (decision-value §6.5).
TRANSLATION = {
    "act": "the checks, in order",
    "measure": "the checks, in order",
    "stop": "no check: the receipt names the action to apply",
    "abstain": "no check: hold the branch-specific action; take the stronger-instrument or review path",
    "no_discriminating_instrument": "no evaluable candidate",
}


def make_valuer(*, estimator: Callable[..., Any] | None = None, screen_client: Any | None = None,
                judge_client: Any | None = None,
                channel_resolver: Callable[..., Any] | None = None) -> Callable[..., dict[str, Any]]:
    """A valuer for ``find_practice(valuer=...)``."""

    def valuer(vault: LoadedVault, repository: Repository, constraints: Any, *, items: Sequence[str],
               exercises: Sequence[Mapping[str, Any]], caller_kind: str = "learner",
               system_initiated: bool = False, picked_proposal_id: str | None = None,
               pending_decision: Mapping[str, Any] | None = None) -> dict[str, Any]:
        return value_request(vault, repository, constraints, items=items, exercises=exercises,
                             caller_kind=caller_kind, system_initiated=system_initiated, estimator=estimator,
                             screen_client=screen_client, judge_client=judge_client,
                             channel_resolver=channel_resolver, pending_decision=pending_decision)

    valuer.estimator = estimator  # type: ignore[attr-defined]
    return valuer


def value_request(vault: LoadedVault, repository: Repository, constraints: Any, *, items: Sequence[str],
                  exercises: Sequence[Mapping[str, Any]], caller_kind: str = "learner",
                  system_initiated: bool = False, estimator: Callable[..., Any] | None = None,
                  screen_client: Any | None = None, judge_client: Any | None = None,
                  channel_resolver: Callable[..., Any] | None = None,
                  pending_decision: Mapping[str, Any] | None = None) -> dict[str, Any]:
    intent = constraints.intent
    repair = dict((pending_decision or {}).get("action_by_slot") or {}) or None
    problems, unavailable = open_hypotheses(
        vault, repository, facet_ids=list(constraints.facet_ids),
        learning_object_ids=list(constraints.learning_object_ids), refs=list(constraints.target_hypotheses),
        intent=intent, repair_class_by_hypothesis=repair)
    eligibility: dict[str, dict[str, Any]] = {}
    kept_items, kept_exercises = list(items), list(exercises)
    if intent in ("discriminate", "retention"):
        kept_items, kept_exercises = [], []
        for item_id in items:
            verdict = independent_check_eligibility(vault, repository, {"practice_item_id": item_id},
                                                    intent=intent, judge_client=judge_client)
            eligibility[item_id] = verdict
            if verdict["eligible"]:
                kept_items.append(item_id)
        for exercise in exercises:
            verdict = independent_check_eligibility(vault, repository, exercise, intent=intent,
                                                    judge_client=judge_client)
            eligibility[str(exercise["key"])] = verdict
            if verdict["eligible"]:
                kept_exercises.append(exercise)
    inputs: dict[str, list[Any]] = {}
    screens: dict[str, Any] = {}
    for problem in problems:
        channel = None
        if problem.space_kind == "retention" and channel_resolver is not None:
            try:
                channel = channel_resolver(repository, learning_object_id=problem.context["learning_object_id"])
            except Exception as exc:  # noqa: BLE001 - no channel is a typed missing reason
                problem.context["channel_error"] = type(exc).__name__
        entries = [item_input(vault, repository, problem, vault.practice_items[item_id], estimator=estimator,
                              channel=channel) for item_id in kept_items if item_id in vault.practice_items]
        if kept_exercises:
            if intent == "discriminate" and problem.space_kind in ("hypothesis_set", "facet_marginal", "episode"):
                screened = screen_exercises(vault, repository, problem, kept_exercises, client=screen_client)
                screens[problem.key] = {"status": screened["status"]}
                for exercise in kept_exercises:
                    entries.append(exercise_input(problem, exercise, screened["screens"].get(str(exercise["key"])),
                                                  estimator=estimator))
            else:
                for exercise in kept_exercises:
                    entry = exercise_input(problem, exercise, None, estimator=estimator)
                    entry.missing = ["not_imported: valued once imported (its rubric and profiles are authored then)"]
                    entries.append(entry)
        inputs[problem.key] = entries
    receipt = value_candidates(problems, inputs, caller_kind=caller_kind, system_initiated=system_initiated,
                               unavailable=unavailable)
    receipt["intent"] = intent
    receipt["eligibility"] = eligibility
    receipt["screens"] = screens
    receipt["translation"] = {section["problem"]["key"]: TRANSLATION.get(section.get("verdict"), section.get("reason"))
                              for section in receipt["problems"]}
    if not problems:
        receipt["verdict"] = "no_open_hypotheses"
    return receipt


__all__ = ["TRANSLATION", "make_valuer", "value_request"]
