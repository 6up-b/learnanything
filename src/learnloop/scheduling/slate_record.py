"""The slate's decision record (ADR-017): what a queue build put first, what it ranked below, and what never reached it.

``scheduler_slates`` and its candidates already hold every candidate the build
ranked, with its scores. What no row held is the other half of "why x and not
y": the items the build withheld before ranking (an exam reservation, a put-away
learning object, a probe surface held in reserve, a revealed cold task, a
teach-back over the cap) and the items a placement check could not be chosen
from. One ``slate`` record per persisting build carries them, counted by rule
with a few ids each, so ``learnloop why`` can say why an item never reached the
slate (the question of daily-loop bug 2).

:func:`slate_record` is pure: it returns the record and never writes.
:func:`record_slate` is the shell ``build_due_queue`` calls; it never raises, so
a record that cannot be built or written never changes what the build serves.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from learnloop.provenance import DecisionRecord, current_trace, is_code

LOG = logging.getLogger(__name__)

KIND = "slate"
SUBJECT_KIND = "slate"
DETAIL_TABLE = "scheduler_slates"

#: Ids kept per exclusion rule; the rest are only counted. Most rules withhold a
#: large share of a vault on every build (nothing due, retired, put away), so a
#: full list would make this the largest row LearnLoop writes for no answer.
IDS_PER_RULE = 10

#: Alternatives kept when the build recorded a slate: ``scheduler_slate_candidates``
#: already holds every candidate with its rank and scores, so the record keeps the
#: nearest few and counts the rest by rule. Measured on the Nov 9 copies, 50
#: alternatives made the slate record 4.4-8.5 KB a row and up to about 4.4% of a
#: vault's database a month at its busiest week; ten keep it near 2-3 KB.
ALTERNATIVES_WITH_SLATE_ROW = 10

# The rule that put the head first, most specific first (``head_rule``).
RULE_EMPTY = "empty_slate"
RULE_PIN = "presentation_pin"
RULE_FOLLOWUP = "pending_followup"
RULE_CHECK = "check_once"
RULE_EXPLORATION = "seeded_exploration"
RULE_GREEDY = "greedy_order"
RULE_COMPOSITION = "composition_order"

# Why a ranked candidate is not the head.
LOST_RANKED_BELOW = "ranked_below"
LOST_BEYOND_LIMIT = "beyond_limit"

# Exclusions the candidate loop does not see: they are decided around it.
COLD_FOLLOWUP_DEFERRED = "cold_followup_deferred"
TEACH_BACK_SESSION_CAP = "teach_back_session_cap"
TEACH_BACK_VALUE = "teach_back_value_below_minutes_cost"


def by_rule(exclusions: Mapping[str, Iterable[str]], *, ids_per_rule: int = IDS_PER_RULE) -> dict[str, dict[str, Any]]:
    """``{rule: {"n": count, "ids": [the first ids, sorted]}}``, plus ``unnamed`` for ids a record cannot carry."""

    summary: dict[str, dict[str, Any]] = {}
    for rule, ids in sorted(exclusions.items()):
        unique = sorted({str(item_id) for item_id in ids})
        if not unique or not is_code(rule):
            continue
        named = [item_id for item_id in unique if is_code(item_id)]
        entry: dict[str, Any] = {"n": len(unique), "ids": named[:ids_per_rule]}
        if len(named) < len(unique):
            entry["unnamed"] = len(unique) - len(named)
        summary[rule] = entry
    return summary


def merged_exclusions(
    withheld: Mapping[str, Iterable[str]],
    *,
    greedy_ids: Sequence[str],
    considered_ids: Sequence[str],
    teach_back_rule: str,
    cold_deferrals: Iterable[Mapping[str, Any]],
) -> dict[str, list[str]]:
    """Every item the build kept off the slate, by rule: the candidate loop's, then the composition's and the cold lane's.

    A ranked item missing from the composed order was dropped by the teach-back
    rule (the composition only reorders otherwise), as the Today offer's
    decision row reads it (``router.decisions.build_today_offer_decision``).
    """

    merged = {str(rule): [str(item_id) for item_id in ids] for rule, ids in withheld.items()}
    considered = set(considered_ids)
    dropped = [item_id for item_id in greedy_ids if item_id not in considered]
    if dropped:
        merged.setdefault(teach_back_rule, []).extend(dropped)
    deferred = [str(row.get("practice_item_id")) for row in cold_deferrals if row.get("practice_item_id")]
    if deferred:
        merged.setdefault(COLD_FOLLOWUP_DEFERRED, []).extend(deferred)
    return merged


def head_rule(head: Any | None, *, pinned_item_id: str | None, check_item_ids: Iterable[str],
              greedy_head_id: str | None) -> str:
    """The rule that put ``head`` (a ``ScheduledItem``) first."""

    if head is None:
        return RULE_EMPTY
    item_id = head.practice_item_id
    components = head.components or {}
    if pinned_item_id is not None and item_id == pinned_item_id:
        return RULE_PIN
    if components.get("intervention_followup") or components.get("negative_surprise_followup"):
        return RULE_FOLLOWUP
    if item_id in set(check_item_ids):
        return RULE_CHECK
    if components.get("exploration_selected", 0.0) > 0.0:
        return RULE_EXPLORATION
    if item_id == greedy_head_id:
        return RULE_GREEDY
    # The goal quota, the requested floor, the same-day rotation or a contrast pair moved it up.
    return RULE_COMPOSITION


def _number(value: Any) -> float | None:
    try:
        number = round(float(value), 6)
    except (TypeError, ValueError):
        return None
    return number if number == number and abs(number) != float("inf") else None


def slate_record(
    *,
    served: Sequence[Any],
    considered: Sequence[Any],
    greedy: Sequence[Any],
    exclusions: Mapping[str, Iterable[str]],
    placement_check_exclusions: Mapping[str, Iterable[str]],
    propensity: Mapping[str, float],
    limit: int | None,
    slate_id: str | None,
    session_id: str | None,
    pinned_item_id: str | None,
    check_item_ids: Iterable[str],
    probe_block_reason: str | None,
    algorithm_version: str,
    selection_policy: str,
) -> DecisionRecord:
    """The ``slate`` record of one build. Pure.

    ``served`` is the returned queue (after ``limit``), ``considered`` the
    composed order before it, ``greedy`` the ranked order before the draw and
    the composition; ``exclusions`` is :func:`merged_exclusions`.
    Alternatives are the considered candidates after the head, in order, with
    their selection reward and the draw's propensity
    (:func:`learnloop.provenance.write` keeps the first 50 and counts the rest).
    """

    head = served[0] if served else None
    served_ids = {item.practice_item_id for item in served}
    alternatives = []
    for item in considered:
        if head is not None and item.practice_item_id == head.practice_item_id:
            continue
        components = item.components or {}
        alternatives.append({
            "ref": item.practice_item_id if is_code(item.practice_item_id) else None,
            "score": _number(components.get("selection_reward", item.priority)),
            "p": _number(propensity.get(item.practice_item_id, 0.0)),
            "lost_by": LOST_RANKED_BELOW if item.practice_item_id in served_ids else LOST_BEYOND_LIMIT,
        })
    overflow: dict[str, int] = {}
    if slate_id:
        for alternative in alternatives[ALTERNATIVES_WITH_SLATE_ROW:]:
            overflow[alternative["lost_by"]] = overflow.get(alternative["lost_by"], 0) + 1
        alternatives = alternatives[:ALTERNATIVES_WITH_SLATE_ROW]
    excluded = by_rule(exclusions)
    facts: dict[str, Any] = {
        "considered_n": len(considered),
        "served_n": len(served),
        "limit": limit,
        "excluded_n": sum(entry["n"] for entry in excluded.values()),
        "exclusions": excluded,
    }
    if overflow:
        # The key :func:`learnloop.provenance.write` uses for the alternatives past its own cap.
        facts["alternatives_overflow"] = overflow
    greedy_head_id = greedy[0].practice_item_id if greedy else None
    for name, value in (("session_id", session_id), ("greedy_head", greedy_head_id), ("pinned", pinned_item_id),
                        ("probe_block_reason", probe_block_reason)):
        if is_code(value):
            facts[name] = value
    placement = by_rule(placement_check_exclusions)
    if placement:
        facts["placement_check_exclusions"] = placement
    chosen = head.practice_item_id if head is not None else None
    if chosen is not None and not is_code(chosen):
        facts["chosen_unnamed"] = True
        chosen = None
    return DecisionRecord(
        kind=KIND,
        status="chosen",
        subject_kind=SUBJECT_KIND if slate_id else None,
        subject_id=slate_id,
        chosen_ref=chosen,
        decided_by=selection_policy,
        rule=head_rule(head, pinned_item_id=pinned_item_id, check_item_ids=check_item_ids,
                       greedy_head_id=greedy_head_id),
        alternatives=tuple(alternatives),
        facts=facts,
        versions={"algorithm_version": algorithm_version, "selection_policy": selection_policy},
        detail_table=DETAIL_TABLE if slate_id else None,
        detail_id=slate_id,
    )


def item_outcome(record: DecisionRecord, practice_item_id: str) -> str | None:
    """What one slate record says about one item: ``chosen``, the rule it lost or was excluded by, or None.

    A placement-check exclusion reads ``placement_check:<rule>``; it says why the
    item was not its LO's check, not why it missed the slate.
    """

    if record.chosen_ref == practice_item_id:
        return "chosen"
    for alternative in record.alternatives:
        if alternative.get("ref") == practice_item_id:
            return str(alternative.get("lost_by"))
    for key, prefix in (("exclusions", ""), ("placement_check_exclusions", "placement_check:")):
        for rule, entry in sorted((record.facts.get(key) or {}).items()):
            if practice_item_id in (entry.get("ids") or ()):
                return f"{prefix}{rule}"
    return None


def record_slate(
    repository: Any,
    *,
    withheld: Mapping[str, Iterable[str]],
    teach_back_value: bool,
    cold_deferrals: Iterable[Mapping[str, Any]],
    **inputs: Any,
) -> str | None:
    """Build and write the slate's record; its id, or ``None``. Never raises: the build has already decided.

    ``withheld`` is the candidate loop's exclusions by reason; ``teach_back_value``
    says the value rule, not the count cap, drops teach-backs (mvp-0.21's
    ``voi_stopping``); the rest are :func:`slate_record`'s inputs.
    """

    try:
        exclusions = merged_exclusions(
            withheld,
            greedy_ids=[item.practice_item_id for item in inputs["greedy"]],
            considered_ids=[item.practice_item_id for item in inputs["considered"]],
            teach_back_rule=TEACH_BACK_VALUE if teach_back_value else TEACH_BACK_SESSION_CAP,
            cold_deferrals=cold_deferrals,
        )
        record = slate_record(exclusions=exclusions, **inputs)
        # Imported here and called through the module so a rebuild test can refuse it (replay never builds a queue).
        from learnloop.db.stores import provenance as decision_store

        return decision_store.write_decision(repository, record)
    except Exception as exc:  # noqa: BLE001 - a record never changes the decision it describes
        LOG.warning("decision record %r not written (trace %s): %s", KIND, current_trace(), type(exc).__name__)
        return None


__all__ = [
    "IDS_PER_RULE", "KIND", "by_rule", "head_rule", "item_outcome", "merged_exclusions", "record_slate",
    "slate_record",
]
