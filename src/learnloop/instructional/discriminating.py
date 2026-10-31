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
from contextlib import closing
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_service import VERIFIED_STATUSES, effective_key_status, exercise_import_ids
from learnloop.instructional.exposure import apply_dominance, independent_check_eligibility
from learnloop.instructional.screen import screen_exercises
from learnloop.instructional.valuation import (
    discount_members,
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
               pending_decision: Mapping[str, Any] | None = None, familiarity: bool = False) -> dict[str, Any]:
        return value_request(vault, repository, constraints, items=items, exercises=exercises,
                             caller_kind=caller_kind, system_initiated=system_initiated, estimator=estimator,
                             screen_client=screen_client, judge_client=judge_client,
                             channel_resolver=channel_resolver, pending_decision=pending_decision,
                             familiarity=familiarity)

    valuer.estimator = estimator  # type: ignore[attr-defined]
    return valuer


def value_request(vault: LoadedVault, repository: Repository, constraints: Any, *, items: Sequence[str],
                  exercises: Sequence[Mapping[str, Any]], caller_kind: str = "learner",
                  system_initiated: bool = False, estimator: Callable[..., Any] | None = None,
                  screen_client: Any | None = None, judge_client: Any | None = None,
                  channel_resolver: Callable[..., Any] | None = None,
                  pending_decision: Mapping[str, Any] | None = None, familiarity: bool = False,
                  eligibility: Callable[..., dict[str, Any]] | None = None) -> dict[str, Any]:
    """One request's valuation receipt.

    ``familiarity`` (Reader RW6b, spec_reader_workbench_v1 §9.3 item 3, G35;
    Codex review F12): each item's information is discounted by its
    attempt-familiarity discount (``recall_coverage.familiarity_discount``,
    composed by :func:`valuation.discount_members`) and the discount is on
    the receipt. ``eligibility`` replaces the exposure rule's
    ``independent_check_eligibility`` (whose worked-example judge is a model
    call) for a caller that applied the rule itself with no model call (RW6b's
    daily re-valuation, Codex review F5)."""

    intent = constraints.intent
    check = eligibility or (lambda *a, **k: independent_check_eligibility(*a, **k))
    repair = dict((pending_decision or {}).get("action_by_slot") or {}) or None
    problems, unavailable = open_hypotheses(
        vault, repository, facet_ids=list(constraints.facet_ids),
        learning_object_ids=list(constraints.learning_object_ids), refs=list(constraints.target_hypotheses),
        intent=intent, repair_class_by_hypothesis=repair)
    eligibility: dict[str, dict[str, Any]] = {}
    kept_items, kept_exercises = list(items), list(exercises)
    if intent in ("discriminate", "retention"):
        kept_items, kept_exercises = [], []
        key_status = _key_statuses(vault, repository, items)
        for item_id in items:
            verdict = check(vault, repository, {"practice_item_id": item_id}, intent=intent,
                            judge_client=judge_client)
            status = key_status.get(item_id, "not_applicable")
            if status != "not_applicable":
                verdict["key_status"] = status
                if status not in VERIFIED_STATUSES:
                    # G6: only a verified key, bound to the item's current
                    # content, qualifies for the value intents; ordinary
                    # practice keeps it, labelled.
                    verdict["reasons"] = [*verdict["reasons"], "unverified_key"]
                    verdict["eligible"] = False
            eligibility[item_id] = verdict
            if verdict["eligible"]:
                kept_items.append(item_id)
        for exercise in exercises:
            verdict = check(vault, repository, exercise, intent=intent, judge_client=judge_client)
            eligibility[str(exercise["key"])] = verdict
            if verdict["eligible"]:
                kept_exercises.append(exercise)
    inputs: dict[str, list[Any]] = {}
    screens: dict[str, Any] = {}
    familiar: dict[str, Any] = {}
    for problem in problems:
        channel = None
        if problem.space_kind == "retention" and channel_resolver is not None:
            try:
                channel = channel_resolver(repository, learning_object_id=problem.context["learning_object_id"])
            except Exception as exc:  # noqa: BLE001 - no channel is a typed missing reason
                problem.context["channel_error"] = type(exc).__name__
        entries = [item_input(vault, repository, problem, vault.practice_items[item_id], estimator=estimator,
                              channel=channel) for item_id in kept_items if item_id in vault.practice_items]
        if familiarity:
            for entry in entries:
                _discount_familiar(vault, repository, problem, entry, familiar)
        if kept_exercises:
            if intent == "discriminate" and problem.space_kind in ("hypothesis_set", "facet_marginal", "episode",
                                                                   "causal_factor"):
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
    # Hard exclusions, kept apart from the unvalued: final assembly never
    # restores them, on either arm (F7).
    receipt["excluded"] = {ref: list(verdict["reasons"]) for ref, verdict in eligibility.items()
                           if not verdict["eligible"]}
    receipt["order"] = presentation_order(receipt, eligibility)
    receipt["screens"] = screens
    receipt["translation"] = {section["problem"]["key"]: TRANSLATION.get(section.get("verdict"), section.get("reason"))
                              for section in receipt["problems"]}
    if not problems:
        receipt["verdict"] = "no_open_hypotheses"
    return receipt


def _discount_familiar(vault: LoadedVault, repository: Repository, problem: Any, entry: Any,
                       cache: dict[str, Any]) -> None:
    """Compose the item's attempt-familiarity discount into its members (G35)."""

    from learnloop.learner.recall_coverage import familiarity_discount

    item = vault.practice_items.get(entry.ref)
    if item is None:
        return
    found = cache.get(item.id)
    if found is None:
        facets = {vault.canonical_facet_id(str(f)): 1.0 for f in item.evidence_facets}
        result = familiarity_discount(repository, item, learning_object_id=item.learning_object_id,
                                      covered_facets=facets, config=vault.config)
        found = cache[item.id] = {"independent_evidence_discount": round(float(result.independent_evidence_discount), 6),
                                  "trace": {k: round(float(v), 6) for k, v in result.trace.items()}}
    entry.familiarity = dict(found)
    discount = float(found["independent_evidence_discount"])
    if entry.members and discount < 1.0:
        entry.members = discount_members(entry.members, problem.prior, discount)


def _key_statuses(vault: LoadedVault, repository: Repository, item_ids: Sequence[str]) -> dict[str, str]:
    """Each imported item's effective key status for its CURRENT content (§7.3a)."""

    items = [vault.practice_items[item_id] for item_id in item_ids if item_id in vault.practice_items]
    if not items:
        return {}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        imports = exercise_import_ids(connection, items)
        return {item.id: effective_key_status(connection, item) for item in items if item.id in imports}


def presentation_order(receipt: Mapping[str, Any], eligibility: Mapping[str, Mapping[str, Any]]) -> list[str]:
    """Checks that clear the stop (check order), then each problem's valued group
    in value order under the reading-exposure dominance rule (§5.4), then the
    bounded and the unvalued. Nothing is ordered by entropy."""

    order: list[str] = []

    def add(ref: str) -> None:
        if ref not in order:
            order.append(ref)

    sections = list(receipt.get("problems") or ())
    for section in sections:
        for check in section.get("checks") or ():
            add(check["ref"])
    labelled = {ref: verdict for ref, verdict in eligibility.items() if verdict.get("label")}
    for section in sections:
        for entry in apply_dominance(list((section.get("groups") or {}).get("valued") or ()), labelled):
            add(entry["ref"])
    for group in ("bounded", "unvalued"):
        for section in sections:
            for entry in (section.get("groups") or {}).get(group) or ():
                add(entry["ref"])
    return order


__all__ = ["TRANSLATION", "make_valuer", "presentation_order", "value_request"]
