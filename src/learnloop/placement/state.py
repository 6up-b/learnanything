"""Placement state (learner field §5.2): what is assumed known, and what happened.

Everything here is read from immutable rows: ``assumption_decisions`` and
``assumption_returns`` (RECEIPT) and ``practice_attempts``. An assumption's
outcome is never written back; it is the first answer on the LO after the
decision (a clean full-marks answer passes, anything else fails), or an
"I don't know this" return, whichever came first.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from learnloop.algorithm_versions import PLACEMENT_VERSIONS
from learnloop.db.repositories import Repository
from learnloop.field.types import LearnerPredictor
from learnloop.placement.rules import (
    AnswerFacts,
    answer_facts,
    check_passed,
    new_material_key,
    prerequisite_layers,
)
from learnloop.vault.models import LoadedVault

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

    @property
    def is_open(self) -> bool:
        return self.status == "open"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PlacementState:
    active: bool
    assumptions: tuple[Assumption, ...] = ()
    returned_learning_object_ids: frozenset[str] = frozenset()
    answers_by_lo: Mapping[str, tuple[AnswerFacts, ...]] = field(default_factory=dict)

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

    @property
    def back_to_learning_learning_object_ids(self) -> frozenset[str]:
        """LOs whose latest assumption failed its check or that the learner
        said they don't know: back to learning, new items served again."""

        return frozenset(
            lo for lo, a in self.latest_by_lo.items() if a.status in {"failed", "returned"}
        )

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


def _resolve(
    decision: Mapping[str, Any],
    returns: Sequence[Mapping[str, Any]],
    answers: Sequence[AnswerFacts],
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
    answer = next((a for a in answers if a.created_at > base.created_at), None)
    if returned is not None and (answer is None or str(returned["created_at"]) <= answer.created_at):
        return _replace(base, status="returned", resolved_at=str(returned["created_at"]))
    if answer is not None:
        return _replace(
            base,
            status="passed" if check_passed(answer) else "failed",
            resolved_at=answer.created_at,
            resolving_attempt_id=answer.attempt_id,
        )
    return base


def _replace(assumption: Assumption, **changes: Any) -> Assumption:
    return Assumption(**{**asdict(assumption), **changes})


def load_placement_state_from_connection(connection: Any, *, active: bool) -> PlacementState:
    if not placement_tables_present(connection):
        return PlacementState(active=active)
    decisions = _rows(connection, "SELECT * FROM assumption_decisions ORDER BY created_at, id")
    returns = _rows(connection, "SELECT * FROM assumption_returns ORDER BY created_at, id")
    los = {str(row["learning_object_id"]) for row in decisions}
    answers = load_answers(connection, los) if los else {}
    assumptions = tuple(
        _resolve(decision, returns, answers.get(str(decision["learning_object_id"]), ()))
        for decision in decisions
    )
    return PlacementState(
        active=active,
        assumptions=assumptions,
        returned_learning_object_ids=frozenset(str(r["learning_object_id"]) for r in returns),
        answers_by_lo=answers,
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
        "returned_learning_object_ids": sorted(state.returned_learning_object_ids),
    }
