"""The optional Today headline (``spec_daily_loop_v1.md`` §6.7, D7).

    14 demonstrated · 3 assumed · 9 learning · 6 untested — expected recall today 87%

It counts active LOs in non-excluded intents (DL1: every active LO), each in
exactly one class, in this order:

- **assumed:** an open Phase 6 assumption whose first review hasn't resolved
  (main's diagnosis-decided placement: a check miss whose diagnosis is still
  pending leaves the assumption open, so the LO stays assumed until the
  diagnosis decides it, within ``placement.rules.DIAGNOSIS_WAIT_DAYS`` of the
  headline's own time);
- **demonstrated:** the whole LO is certified, never just part of it. An LO
  with authored blueprints uses ``lo_certification(...).demonstrated``; any
  other LO needs every required capability of every one of its facets
  demonstrated (a ``demonstrated_mass`` of 1 for every facet);
- **learning:** direct evidence but not demonstrated as a whole;
- **untested:** no direct evidence.

**Expected recall today** is the mean FSRS retrievability now over items with
memory state: a model estimate, not a test (L1). Before Phase 6 the "assumed"
class is omitted rather than shown as 0. Read-only: nothing here is evidence.

**Intent** (daily-loop DL2, Codex review F10): the population is what the
plan can serve. An item whose resolved intent excludes it (Pause, Reference,
Let go, an answered "Check once") leaves expected recall; an LO leaves the
counts when every item of it is excluded (an LO without items, when its own
intent excludes it). With intent changing nothing (``intent.enabled`` off,
or no commitment) the population is DL1's exactly.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from learnloop.daily_plan.reentry import retrievability
from learnloop.goals.certification import is_demonstrated_credit
from learnloop.goals.goal_certification import lo_certification, required_capabilities_for_facet
from learnloop.learner.facet_diagnostics import scope_facets
from learnloop.learner.facet_state_reader import is_canonical_state_vault
from learnloop.params.fitted_params import resolve_fsrs_weights
from learnloop.placement.state import load_placement_state, placement_active

HEADLINE_CLASSES = ("demonstrated", "assumed", "learning", "untested")
EXPECTED_RECALL_TOOLTIP = "a model estimate, not a test"


def classify_learning_objects(
    vault: Any, repository: Any, *, now: datetime | None = None, learning_object_ids: Iterable[str] | None = None,
) -> dict[str, str]:
    """Each active LO in exactly one headline class.

    ``now`` is the headline's time. Placement state is read at it, never the
    wall clock, because whether a pending diagnosis still holds a check miss
    depends on the time (the wait is bounded). ``learning_object_ids`` limits
    the answer to those LOs (router R2a's card, review F7: the same predicate
    over the card's topics only); the classes do not depend on it.
    """

    wanted = None if learning_object_ids is None else frozenset(learning_object_ids)

    assumed_ids: set[str] = set()
    placement_on = placement_active(vault)
    if placement_on:
        now_iso = None if now is None else now.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        state = load_placement_state(vault, repository, now_iso=now_iso)
        assumed_ids = set(state.open_by_lo)
    canonical = is_canonical_state_vault(vault)
    cells_by_facet: dict[str, list[Any]] = defaultdict(list)
    if canonical:
        for cell in repository.facet_capability_evidence_all():
            cells_by_facet[vault.canonical_facet_id(cell.facet_id)].append(cell)
    mastery = repository.mastery_states()
    classes: dict[str, str] = {}
    for learning_object in sorted(vault.learning_objects.values(), key=lambda lo: lo.id):
        if learning_object.status != "active" or (wanted is not None and learning_object.id not in wanted):
            continue
        lo_id = learning_object.id
        if lo_id in assumed_ids:
            classes[lo_id] = "assumed"
            continue
        facets = sorted({vault.canonical_facet_id(str(f)) for f in scope_facets(vault, lo_id, repository)})
        if _demonstrated(vault, repository, learning_object, facets, cells_by_facet, canonical):
            classes[lo_id] = "demonstrated"
            continue
        if _has_direct_evidence(facets, cells_by_facet, mastery.get(lo_id), canonical):
            classes[lo_id] = "learning"
        else:
            classes[lo_id] = "untested"
    return classes


def _demonstrated(
    vault: Any,
    repository: Any,
    learning_object: Any,
    facets: list[str],
    cells_by_facet: dict[str, list[Any]],
    canonical: bool,
) -> bool:
    if not canonical:
        return False
    if learning_object.blueprints:
        return bool(lo_certification(vault, repository, learning_object).demonstrated)
    if not facets:
        return False
    for facet_id in facets:
        required, _legacy = required_capabilities_for_facet(vault, learning_object, facet_id)
        if not required:
            return False
        demonstrated = {
            cell.capability
            for cell in cells_by_facet.get(facet_id, [])
            if is_demonstrated_credit(cell.certification_credit)
        }
        if not set(required) <= demonstrated:
            return False
    return True


def _has_direct_evidence(
    facets: list[str], cells_by_facet: dict[str, list[Any]], mastery: Any, canonical: bool
) -> bool:
    if canonical:
        for facet_id in facets:
            for cell in cells_by_facet.get(facet_id, []):
                if float(cell.direct_positive_mass) + float(cell.direct_negative_mass) > 0.0:
                    return True
        return False
    return mastery is not None and mastery.last_evidence_at is not None


def expected_recall_today(
    vault: Any, repository: Any, *, now: datetime, excluded_item_ids: Iterable[str] = (),
) -> tuple[float | None, int]:
    """Mean FSRS retrievability now over items with memory state, and their
    count; ``excluded_item_ids`` (DL2: intent) are left out."""

    weights = resolve_fsrs_weights(repository)
    excluded = frozenset(excluded_item_ids)
    values: list[float] = []
    for item_id, state in repository.practice_item_states().items():
        item = vault.practice_items.get(item_id)
        if item is None or item.status != "active" or not state.active or item_id in excluded:
            continue
        learning_object = vault.learning_object_for_item(item)
        if learning_object is None or learning_object.status != "active":
            continue
        value = retrievability(state.stability, state.last_attempt_at, now, weights)
        if value is not None:
            values.append(value)
    if not values:
        return None, 0
    return sum(values) / len(values), len(values)


def intent_exclusions(vault: Any, repository: Any, *, now: datetime) -> tuple[frozenset[str], frozenset[str]]:
    """``(excluded LO ids, excluded item ids)`` by resolved intent (F10);
    both empty when intent changes nothing."""

    from learnloop.scheduling.intent.serving import intent_serving

    intent = intent_serving(vault, repository, now=now)
    if intent is None:
        return frozenset(), frozenset()
    items_by_lo: dict[str, list[str]] = defaultdict(list)
    excluded_items: set[str] = set()
    for item in vault.practice_items.values():
        lo_id = getattr(item, "learning_object_id", None)
        if lo_id is not None:
            items_by_lo[str(lo_id)].append(item.id)
        if intent.intent(item.id).excluded:
            excluded_items.add(item.id)
    excluded_los: set[str] = set()
    for lo_id in vault.learning_objects:
        items = items_by_lo.get(lo_id)
        if items:
            if all(item_id in excluded_items for item_id in items):
                excluded_los.add(lo_id)
        elif intent.resolution.for_learning_object(lo_id).excluded:
            excluded_los.add(lo_id)
    return frozenset(excluded_los), frozenset(excluded_items)


def today_headline(vault: Any, repository: Any, *, now: datetime) -> dict[str, Any]:
    excluded_los, excluded_items = intent_exclusions(vault, repository, now=now)
    classes = classify_learning_objects(vault, repository, now=now)
    if excluded_los:
        classes = {lo_id: value for lo_id, value in classes.items() if lo_id not in excluded_los}
    counts = {name: 0 for name in HEADLINE_CLASSES}
    for value in classes.values():
        counts[value] += 1
    show_assumed = placement_active(vault)
    recall, recall_items = expected_recall_today(vault, repository, now=now, excluded_item_ids=excluded_items)
    parts = [f"{counts['demonstrated']} demonstrated"]
    if show_assumed:
        parts.append(f"{counts['assumed']} assumed")
    parts.extend([f"{counts['learning']} learning", f"{counts['untested']} untested"])
    line = " · ".join(parts)
    if recall is not None:
        line += f" — expected recall today {round(recall * 100)}%"
    return {
        "counts": counts if show_assumed else {k: v for k, v in counts.items() if k != "assumed"},
        "show_assumed": show_assumed,
        "expected_recall": recall,
        "expected_recall_percent": round(recall * 100) if recall is not None else None,
        "expected_recall_items": recall_items,
        "expected_recall_tooltip": EXPECTED_RECALL_TOOLTIP,
        "learning_object_classes": classes,
        "line": line,
    }


__all__ = [
    "EXPECTED_RECALL_TOOLTIP",
    "HEADLINE_CLASSES",
    "classify_learning_objects",
    "expected_recall_today",
    "intent_exclusions",
    "today_headline",
]
