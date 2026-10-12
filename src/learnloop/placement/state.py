"""Placement state (learner field §5.2): what is assumed known, and what happened.

Everything here is read from immutable rows: ``assumption_decisions`` and
``assumption_returns`` (RECEIPT), ``practice_attempts``, ``reveal_events`` and
``coldness_receipts``. An assumption's outcome is never written back:

- an answer on the LO after the decision that the learner did not answer
  cleanly (partial marks, hints, priming, "don't know", assistance) fails it,
  early or on schedule: the LO quietly returns to learning;
- a clean answer before ``first_review_due`` is early practice (an explicit,
  learner-requested exception to the review interval): recorded, never the
  check;
- from ``first_review_due`` on, the first clean answer that the existing
  independence rule admits (``production_admissibility`` over the window since
  the item's previous attempt or the decision, whichever is later, plus any
  final coldness receipt) passes it; a clean answer the rule rejects is
  ineligible and the check waits;
- an "I don't know this" before any of that returns it.

Each LO's current placement intent is derived from its decisions, returns and
answers in time order (:class:`LearningObjectIntent`): ``assumed`` while an
assumption is open, ``maintenance`` after a passed check until a later miss or
"I don't know this", ``learning`` after a miss, a lapse or "I don't know this"
(with or without an assumption) until a later explicit "I know this".
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import nullcontext
from dataclasses import asdict, dataclass, field, replace
import json
from typing import Any

from learnloop.algorithm_versions import PLACEMENT_VERSIONS
from learnloop.attempts.reveal_ledger import production_admissibility
from learnloop.db.repositories import Repository
from learnloop.field.types import LearnerPredictor
from learnloop.placement.rules import (
    CHECK_PASS,
    AnswerFacts,
    answer_facts,
    check_verdict,
    new_material_key,
    prerequisite_layers,
)
from learnloop.vault.models import LoadedVault

#: Placement intents (field §5.2): the routing an LO is under right now.
INTENT_ASSUMED = "assumed"
INTENT_MAINTENANCE = "maintenance"
INTENT_LEARNING = "learning"

PLACEMENT_TABLES = ("assumption_decisions", "assumption_returns", "placement_quick_checks")


def placement_active(vault: LoadedVault) -> bool:
    """F2 serves only at a placement version with the kill switch on."""

    return (
        vault.config.algorithms.algorithm_version in PLACEMENT_VERSIONS
        and bool(vault.config.placement.enabled)
    )


def initial_probes_enabled(vault: LoadedVault) -> bool:
    """Whether state sync opens an opening diagnostic episode per new LO."""

    return not placement_active(vault) or bool(vault.config.placement.initial_probes)


def placement_tables_present(connection: Any) -> bool:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN (?,?,?)", PLACEMENT_TABLES,
    ).fetchall()
    return len(rows) == len(PLACEMENT_TABLES)


@dataclass(frozen=True)
class Assumption:
    id: str
    learning_object_id: str
    source: str
    trigger_kind: str
    trigger_ref: str | None
    p: float | None
    q_used: float | None
    predictor: str
    predictor_version: str
    first_review_due: str
    quick_check_session_id: str | None
    algorithm_version: str
    created_at: str
    status: str = "open"  # open | passed | failed | returned
    resolved_at: str | None = None
    resolving_attempt_id: str | None = None
    #: Clean answers before ``first_review_due`` (explicit practice): never the check.
    early_answers: int = 0
    #: Clean answers from the due date on that the independence rule rejected.
    ineligible_answers: int = 0

    @property
    def is_open(self) -> bool:
        return self.status == "open"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LearningObjectIntent:
    """An LO's current placement routing, derived in time order (never stored)."""

    learning_object_id: str
    intent: str  # assumed | maintenance | learning
    since: str
    #: assumed | check_passed | check_missed | missed_in_maintenance | i_dont_know_this
    reason: str
    assumption_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PlacementState:
    active: bool
    assumptions: tuple[Assumption, ...] = ()
    returned_learning_object_ids: frozenset[str] = frozenset()
    answers_by_lo: Mapping[str, tuple[AnswerFacts, ...]] = field(default_factory=dict)
    intent_by_lo: Mapping[str, LearningObjectIntent] = field(default_factory=dict)

    @property
    def open_by_lo(self) -> dict[str, Assumption]:
        return {a.learning_object_id: a for a in self.assumptions if a.is_open}

    @property
    def latest_by_lo(self) -> dict[str, Assumption]:
        latest: dict[str, Assumption] = {}
        for assumption in self.assumptions:  # ordered by (created_at, id)
            latest[assumption.learning_object_id] = assumption
        return latest

    @property
    def decided_learning_object_ids(self) -> frozenset[str]:
        return frozenset(a.learning_object_id for a in self.assumptions)

    def _with_intent(self, intent: str) -> frozenset[str]:
        return frozenset(lo for lo, entry in self.intent_by_lo.items() if entry.intent == intent)

    @property
    def back_to_learning_learning_object_ids(self) -> frozenset[str]:
        """LOs back to learning: a missed check, a miss in maintenance, or "I
        don't know this" (with or without an assumption). New items are served
        again until a later explicit "I know this"."""

        return self._with_intent(INTENT_LEARNING)

    @property
    def maintained_learning_object_ids(self) -> frozenset[str]:
        """LOs whose check passed: in maintenance, remaining learning items withheld."""

        return self._with_intent(INTENT_MAINTENANCE)

    def due_learning_object_ids(self, now_iso: str) -> frozenset[str]:
        return frozenset(lo for lo, a in self.open_by_lo.items() if a.first_review_due <= now_iso)


def _rows(connection: Any, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, tuple(params))
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def _contamination_classes(connection: Any, attempt_ids: Iterable[str]) -> dict[str, str]:
    """Latest recorded contamination class per attempt (most contaminated wins)."""

    wanted = sorted(set(attempt_ids))
    if not wanted:
        return {}
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='causal_activity_classification_events'"
    ).fetchone()
    if exists is None:
        return {}
    from learnloop.causal_activity_policy import CONTAMINATION_PRECEDENCE

    result: dict[str, str] = {}
    for start in range(0, len(wanted), 500):
        chunk = wanted[start:start + 500]
        rows = _rows(
            connection,
            "SELECT attempt_id, contamination_class FROM causal_activity_classification_events "
            f"WHERE attempt_id IN ({','.join('?' for _ in chunk)})",
            chunk,
        )
        for row in rows:
            attempt_id = str(row["attempt_id"])
            current = result.get(attempt_id)
            candidate = str(row["contamination_class"] or "verification")
            if candidate not in CONTAMINATION_PRECEDENCE:
                continue
            if current is None or CONTAMINATION_PRECEDENCE.index(candidate) < CONTAMINATION_PRECEDENCE.index(current):
                result[attempt_id] = candidate
    return result


def load_answers(
    connection: Any, learning_object_ids: Iterable[str] | None = None,
) -> dict[str, tuple[AnswerFacts, ...]]:
    """Every recorded answer per LO, in (created_at, id) order. Skips excluded."""

    columns = (
        "id, learning_object_id, practice_item_id, attempt_type, correctness, hints_used, "
        "primed, declared_dont_know, manual_review, created_at"
    )
    if learning_object_ids is None:
        rows = _rows(connection, f"SELECT {columns} FROM practice_attempts ORDER BY created_at, id")
    else:
        wanted = sorted(set(learning_object_ids))
        rows = []
        for start in range(0, len(wanted), 500):
            chunk = wanted[start:start + 500]
            rows.extend(_rows(
                connection,
                f"SELECT {columns} FROM practice_attempts "
                f"WHERE learning_object_id IN ({','.join('?' for _ in chunk)})",
                chunk,
            ))
        rows.sort(key=lambda row: (str(row["created_at"]), str(row["id"])))
    classes = _contamination_classes(connection, (str(row["id"]) for row in rows))
    grouped: dict[str, list[AnswerFacts]] = defaultdict(list)
    for row in rows:
        facts = answer_facts(row, contamination_class=classes.get(str(row["id"])))
        if facts is not None:
            grouped[facts.learning_object_id].append(facts)
    return {lo: tuple(answers) for lo, answers in grouped.items()}


class _BorrowedRepository(Repository):
    """Repository reads inside the caller's connection and snapshot; never commits."""

    def __init__(self, connection: Any):  # noqa: D107 - no store state beyond the handle
        self._borrowed = connection

    def connection(self):  # type: ignore[override]
        return nullcontext(self._borrowed)


_COLD_DIMENSIONS = ("unassisted", "answer_leakage")


def _final_receipt_ok(connection: Any, attempt_id: str) -> bool | None:
    """A final coldness receipt's own independence findings, if there is one.

    The cold lane records explicit unassisted and answer-leakage dimensions; any
    receipt for the attempt that does not pass both makes it non-independent
    (the field's strict rule). None when no receipt exists."""

    rows = connection.execute(
        "SELECT dimensions_json FROM coldness_receipts WHERE cold_attempt_id = ? AND stage = 'final' ORDER BY id",
        (attempt_id,),
    ).fetchall()
    if not rows:
        return None
    for (raw,) in rows:
        dimensions = json.loads(raw or "{}")
        if any((dimensions.get(name) or {}).get("status") != "pass" for name in _COLD_DIMENSIONS):
            return False
    return True


def evaluate_independence(
    connection: Any,
    answers: Iterable[AnswerFacts],
    *,
    since_floor: str | None = None,
) -> tuple[AnswerFacts, ...]:
    """Each answer with its independence facts from the existing rules.

    The window ends at the answer and starts at the item's previous attempt
    (any attempt closes a reveal window, as in the field's coldness rule) or at
    ``since_floor`` (an assumption's decision), whichever is later; with
    neither, any earlier reveal on the item or its LO counts (fail-closed).
    ``production_admissibility`` scans ``reveal_events`` over that window, and a
    final coldness receipt for the attempt must pass its unassisted and
    answer-leakage dimensions.
    """

    repository = _BorrowedRepository(connection)
    evaluated: list[AnswerFacts] = []
    for answer in answers:
        prior = connection.execute(
            "SELECT created_at FROM practice_attempts WHERE practice_item_id = ? "
            "AND (created_at < ? OR (created_at = ? AND id < ?)) ORDER BY created_at DESC, id DESC LIMIT 1",
            (answer.practice_item_id, answer.created_at, answer.created_at, answer.attempt_id),
        ).fetchone()
        bounds = [value for value in (prior[0] if prior else None, since_floor) if value]
        since = max(bounds) if bounds else None
        admissibility = production_admissibility(
            repository,
            practice_item_id=answer.practice_item_id,
            learning_object_id=answer.learning_object_id,
            produced_at=answer.created_at,
            since=since,
        )
        receipt_ok = _final_receipt_ok(connection, answer.attempt_id)
        reason = admissibility.reason
        if reason is None and receipt_ok is False:
            reason = "coldness_receipt_not_independent"
        evaluated.append(replace(
            answer,
            independent=admissibility.admissible and receipt_ok is not False,
            independence_reason=reason,
            reveal_event_id=admissibility.reveal_event_id,
            independence_since=since,
        ))
    return tuple(evaluated)


IndependenceCheck = Callable[[AnswerFacts, str], AnswerFacts]


def _resolve(
    decision: Mapping[str, Any],
    returns: Sequence[Mapping[str, Any]],
    answers: Sequence[AnswerFacts],
    independence: IndependenceCheck,
) -> Assumption:
    base = Assumption(
        id=str(decision["id"]),
        learning_object_id=str(decision["learning_object_id"]),
        source=str(decision["source"]),
        trigger_kind=str(decision["trigger_kind"]),
        trigger_ref=decision.get("trigger_ref"),
        p=decision.get("p"),
        q_used=decision.get("q_used"),
        predictor=str(decision["predictor"]),
        predictor_version=str(decision["predictor_version"]),
        first_review_due=str(decision["first_review_due"]),
        quick_check_session_id=decision.get("quick_check_session_id"),
        algorithm_version=str(decision["algorithm_version"]),
        created_at=str(decision["created_at"]),
    )
    returned = min(
        (r for r in returns if r.get("assumption_id") == base.id),
        key=lambda r: (str(r["created_at"]), str(r["id"])),
        default=None,
    )
    returned_at = str(returned["created_at"]) if returned is not None else None
    early = ineligible = 0
    for answer in answers:
        if answer.created_at <= base.created_at:
            continue
        if returned_at is not None and returned_at <= answer.created_at:
            break
        if not answer.learner_clean:
            # A miss, early or on schedule, quietly returns the LO to learning.
            return replace(
                base, status="failed", resolved_at=answer.created_at, resolving_attempt_id=answer.attempt_id,
                early_answers=early, ineligible_answers=ineligible,
            )
        if answer.created_at < base.first_review_due:
            # Explicit practice inside the review interval is recorded, but it
            # is a repetition, not the delayed check.
            early += 1
            continue
        if check_verdict(independence(answer, base.created_at)) == CHECK_PASS:
            return replace(
                base, status="passed", resolved_at=answer.created_at, resolving_attempt_id=answer.attempt_id,
                early_answers=early, ineligible_answers=ineligible,
            )
        ineligible += 1
    if returned_at is not None:
        return replace(
            base, status="returned", resolved_at=returned_at, early_answers=early, ineligible_answers=ineligible,
        )
    return replace(base, early_answers=early, ineligible_answers=ineligible)


def _intent(
    learning_object_id: str,
    decision: Assumption | None,
    latest_return: Mapping[str, Any] | None,
    answers: Sequence[AnswerFacts],
) -> LearningObjectIntent | None:
    """The LO's current routing from its latest decision and latest return."""

    if latest_return is not None and (decision is None or str(latest_return["created_at"]) >= decision.created_at):
        linked = latest_return.get("assumption_id")
        return LearningObjectIntent(
            learning_object_id, INTENT_LEARNING, str(latest_return["created_at"]), "i_dont_know_this",
            str(linked) if linked else None,
        )
    if decision is None:
        return None
    if decision.status == "open":
        return LearningObjectIntent(learning_object_id, INTENT_ASSUMED, decision.created_at, "assumed", decision.id)
    if decision.status == "returned":
        return LearningObjectIntent(
            learning_object_id, INTENT_LEARNING, str(decision.resolved_at), "i_dont_know_this", decision.id,
        )
    if decision.status == "failed":
        return LearningObjectIntent(
            learning_object_id, INTENT_LEARNING, str(decision.resolved_at), "check_missed", decision.id,
        )
    # Passed: maintenance until a later miss on the LO (a lapse) returns it.
    resolving = next(
        (index for index, answer in enumerate(answers) if answer.attempt_id == decision.resolving_attempt_id), None,
    )
    later = answers[resolving + 1:] if resolving is not None else ()
    lapse = next((answer for answer in later if not answer.learner_clean), None)
    if lapse is not None:
        return LearningObjectIntent(
            learning_object_id, INTENT_LEARNING, lapse.created_at, "missed_in_maintenance", decision.id,
        )
    return LearningObjectIntent(
        learning_object_id, INTENT_MAINTENANCE, str(decision.resolved_at), "check_passed", decision.id,
    )


def load_placement_state_from_connection(connection: Any, *, active: bool) -> PlacementState:
    if not placement_tables_present(connection):
        return PlacementState(active=active)
    decisions = _rows(connection, "SELECT * FROM assumption_decisions ORDER BY created_at, id")
    returns = _rows(connection, "SELECT * FROM assumption_returns ORDER BY created_at, id")
    los = {str(row["learning_object_id"]) for row in decisions} | {
        str(row["learning_object_id"]) for row in returns
    }
    answers = load_answers(connection, los) if los else {}

    def independence(answer: AnswerFacts, since_floor: str) -> AnswerFacts:
        return evaluate_independence(connection, (answer,), since_floor=since_floor)[0]

    assumptions = tuple(
        _resolve(decision, returns, answers.get(str(decision["learning_object_id"]), ()), independence)
        for decision in decisions
    )
    latest_decision: dict[str, Assumption] = {}
    for assumption in assumptions:  # ordered by (created_at, id)
        latest_decision[assumption.learning_object_id] = assumption
    latest_return: dict[str, Mapping[str, Any]] = {}
    for row in returns:  # ordered by (created_at, id)
        latest_return[str(row["learning_object_id"])] = row
    intents = {
        lo: intent
        for lo in sorted(los)
        if (intent := _intent(lo, latest_decision.get(lo), latest_return.get(lo), answers.get(lo, ()))) is not None
    }
    return PlacementState(
        active=active,
        assumptions=assumptions,
        returned_learning_object_ids=frozenset(str(r["learning_object_id"]) for r in returns),
        answers_by_lo=answers,
        intent_by_lo=intents,
    )


def load_placement_state(vault: LoadedVault, repository: Repository) -> PlacementState:
    with repository.connection() as connection:
        return load_placement_state_from_connection(connection, active=placement_active(vault))


# -- serving helpers ---------------------------------------------------------


def prerequisite_learning_objects(vault: LoadedVault, learning_object_id: str) -> set[str]:
    """LOs on the concepts this LO declares as prerequisites (field §5.2 order).

    Declared by the LO's own ``prerequisites`` (concept ids) or by a
    ``prerequisite`` relation edge into its concept. Direction is respected;
    no other relation type orders anything (knowledge model §8.1, G5)."""

    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        return set()
    concepts = set(learning_object.prerequisites)
    concepts.update(
        edge.source for edge in vault.edges
        if edge.relation_type == "prerequisite" and edge.target == learning_object.concept
    )
    concepts.discard(learning_object.concept)
    return {
        lo.id for lo in vault.learning_objects.values() if lo.concept in concepts
    } - {learning_object_id}


def order_new_material(
    vault: LoadedVault,
    predictor: LearnerPredictor,
    items: Sequence[tuple[str, str]],
    *,
    taught_first: Iterable[str] = (),
) -> list[tuple[str, dict[str, float]]]:
    """Order (practice_item_id, learning_object_id) pairs of new material.

    Prerequisite layer first (over the new LOs only), then LOs the learner
    asked confused questions about or needed help on (taught first), then the
    active predictor's predicted success, easiest first; ties by item id.
    Returns each item with the components that explain its place.
    """

    learning_objects = {lo for _item, lo in items}
    layers = prerequisite_layers(
        learning_objects,
        {lo: prerequisite_learning_objects(vault, lo) for lo in learning_objects},
    )
    first = set(taught_first)
    keyed = []
    for item_id, lo in items:
        p = predictor.predict_item(item_id).p_success
        keyed.append((
            new_material_key(
                layer=layers.get(lo, 0), taught_first=lo in first,
                predicted_success=p, practice_item_id=item_id,
            ),
            item_id,
            {
                "placement_layer": float(layers.get(lo, 0)),
                "taught_first": 1.0 if lo in first else 0.0,
                "placement_predicted_success": p,
            },
        ))
    keyed.sort(key=lambda entry: entry[0])
    return [(item_id, components) for _key, item_id, components in keyed]


def choose_check_items(
    predictor: LearnerPredictor,
    candidates: Mapping[str, Sequence[str]],
    *,
    attempted_item_ids: Iterable[str] = (),
) -> dict[str, str]:
    """One first-review item per due assumed LO: a normal cold item.

    Never-attempted items first; among them the median predicted success
    (lower median), so the check is neither the easiest nor the hardest item.
    Ties by item id. Deterministic given the predictor snapshot (G8).
    """

    attempted = set(attempted_item_ids)
    chosen: dict[str, str] = {}
    for lo, item_ids in sorted(candidates.items()):
        pool = sorted(set(item_ids))
        if not pool:
            continue
        fresh = [item_id for item_id in pool if item_id not in attempted]
        pool = fresh or pool
        ranked = sorted(pool, key=lambda item_id: (predictor.predict_item(item_id).p_success, item_id))
        chosen[lo] = ranked[(len(ranked) - 1) // 2]
    return chosen


def assumption_summary(state: PlacementState) -> dict[str, Any]:
    return {
        "active": state.active,
        "open": {lo: a.as_dict() for lo, a in sorted(state.open_by_lo.items())},
        "intents": {lo: entry.as_dict() for lo, entry in sorted(state.intent_by_lo.items())},
        "returned_learning_object_ids": sorted(state.returned_learning_object_ids),
    }
