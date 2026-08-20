"""Structured traces for long-form probes (spec_probe_eig_redesign.md §8.2).

A proof, derivation, or extended case is ONE structured multi-channel
instrument, not a bag of independent full-strength attempts. The trace MUST
preserve the correct prefix, identify the first divergent step or claim when
possible, mark dependent downstream obligations unassessable, and divide a
fixed task evidence mass across the assessable elements — so eight dependent
proof obligations can never exceed one task's total evidence (§16 tests 23/24).

Everything here is pure and deterministic: obligations are declared on the
Instrument Card bindings, per-obligation outcomes come from persisted
criterion-level grading evidence, and the assessed trace is stored as a
logged-only observation feature (never re-derived by replay from a live call).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

# Fraction of a criterion's points that counts the obligation as met.
_CORRECT_POINTS_RATIO = 0.75

OUTCOME_CORRECT = "correct"
OUTCOME_INVALID = "invalid"
OUTCOME_UNASSESSABLE = "unassessable"
OUTCOME_UNASSESSED = "unassessed"


@dataclass(frozen=True)
class TraceObligation:
    """One declared proof/derivation obligation, ordered as authored.

    ``kind`` distinguishes the strategy/subgoal selection obligation
    (``selection``) from execution steps (``step``) so a failed selection maps
    to the procedure-without-selection signature rather than a generic slip.
    """

    id: str
    criterion_id: str | None = None
    depends_on: tuple[str, ...] = ()
    kind: str = "step"

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "criterion_id": self.criterion_id,
            "depends_on": list(self.depends_on),
            "kind": self.kind,
        }


@dataclass(frozen=True)
class ObligationAssessment:
    id: str
    outcome: str  # correct | invalid | unassessable | unassessed
    evidence_share: float  # fraction of the task's total evidence mass

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "outcome": self.outcome, "evidence_share": self.evidence_share}


@dataclass(frozen=True)
class AssessedTrace:
    """The §8.2 structured trace over one long-form response."""

    obligations: tuple[ObligationAssessment, ...]
    first_invalid_id: str | None
    correct_prefix_ids: tuple[str, ...]
    unassessable_ids: tuple[str, ...]
    total_task_evidence_mass: float

    @property
    def assessable_mass(self) -> float:
        """Evidence mass actually carried by assessed elements — bounded by
        the task's total mass by construction (§7.7/§16 test 23)."""

        return sum(
            entry.evidence_share
            for entry in self.obligations
            if entry.outcome in (OUTCOME_CORRECT, OUTCOME_INVALID)
        )

    @property
    def has_assessable_evidence(self) -> bool:
        return any(
            entry.outcome in (OUTCOME_CORRECT, OUTCOME_INVALID) for entry in self.obligations
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "obligations": [entry.as_dict() for entry in self.obligations],
            "first_invalid_id": self.first_invalid_id,
            "correct_prefix_ids": list(self.correct_prefix_ids),
            "unassessable_ids": list(self.unassessable_ids),
            "total_task_evidence_mass": self.total_task_evidence_mass,
            "assessable_mass": self.assessable_mass,
        }


def obligations_from_bindings(bindings: Mapping[str, Any] | None) -> list[TraceObligation]:
    """Parse the card's declared obligations (``bindings["obligations"]``)."""

    entries = (bindings or {}).get("obligations")
    if not isinstance(entries, list):
        return []
    obligations: list[TraceObligation] = []
    for entry in entries:
        if not isinstance(entry, Mapping) or not entry.get("id"):
            continue
        obligations.append(
            TraceObligation(
                id=str(entry["id"]),
                criterion_id=str(entry["criterion_id"]) if entry.get("criterion_id") else None,
                depends_on=tuple(str(dep) for dep in entry.get("depends_on") or ()),
                kind=str(entry.get("kind") or "step"),
            )
        )
    return obligations


def outcomes_from_grading_evidence(
    obligations: Iterable[TraceObligation],
    evidence_rows: Iterable[Any],
    criteria_max_points: Mapping[str, float],
) -> dict[str, str]:
    """Per-obligation raw outcomes from persisted criterion-level grading.

    An obligation whose criterion was awarded at least ``_CORRECT_POINTS_RATIO``
    of its points is ``correct``; a graded criterion below that is ``invalid``;
    an obligation whose criterion has no (non-superseded) evidence row stays
    ``unassessed`` — the grader could not see it, so it carries no evidence.
    """

    points: dict[str, float] = {}
    for row in evidence_rows:
        superseded = getattr(row, "superseded_at", None)
        if superseded:
            continue
        criterion_id = str(getattr(row, "criterion_id", "") or "")
        if criterion_id:
            points[criterion_id] = float(getattr(row, "points_awarded", 0.0) or 0.0)
    outcomes: dict[str, str] = {}
    for obligation in obligations:
        if obligation.criterion_id is None or obligation.criterion_id not in points:
            outcomes[obligation.id] = OUTCOME_UNASSESSED
            continue
        maximum = float(criteria_max_points.get(obligation.criterion_id, 0.0) or 0.0)
        if maximum <= 0:
            outcomes[obligation.id] = OUTCOME_UNASSESSED
            continue
        ratio = points[obligation.criterion_id] / maximum
        outcomes[obligation.id] = OUTCOME_CORRECT if ratio >= _CORRECT_POINTS_RATIO else OUTCOME_INVALID
    return outcomes


def assess_trace(
    obligations: list[TraceObligation],
    outcomes: Mapping[str, str],
    *,
    total_task_evidence_mass: float = 1.0,
) -> AssessedTrace:
    """Assess one long-form response against its declared obligations (§8.2).

    - The first obligation (in authored order) graded ``invalid`` is the first
      divergent step.
    - Obligations transitively depending on it are ``unassessable`` and carry
      zero evidence — their premises are already wrong, so grading them would
      duplicate the first error as fresh evidence.
    - Correct obligations before the first invalid are the preserved correct
      prefix; independent obligations after it stay assessable.
    - The task's fixed evidence mass divides equally across ALL declared
      obligations, so the summed assessable mass can never exceed the task
      total, however many obligations the trace contains (§16 test 23).
    """

    total = max(float(total_task_evidence_mass), 0.0)
    if not obligations:
        return AssessedTrace(
            obligations=(),
            first_invalid_id=None,
            correct_prefix_ids=(),
            unassessable_ids=(),
            total_task_evidence_mass=total,
        )
    per_element_share = total / len(obligations)

    first_invalid_id: str | None = None
    for obligation in obligations:
        if outcomes.get(obligation.id) == OUTCOME_INVALID:
            first_invalid_id = obligation.id
            break

    unassessable: set[str] = set()
    if first_invalid_id is not None:
        dependents: dict[str, set[str]] = {obligation.id: set() for obligation in obligations}
        for obligation in obligations:
            for dependency in obligation.depends_on:
                dependents.setdefault(dependency, set()).add(obligation.id)
        frontier = [first_invalid_id]
        while frontier:
            for child in sorted(dependents.get(frontier.pop(), ())):
                if child not in unassessable:
                    unassessable.add(child)
                    frontier.append(child)

    assessments: list[ObligationAssessment] = []
    correct_prefix: list[str] = []
    before_first_invalid = True
    for obligation in obligations:
        if obligation.id == first_invalid_id:
            before_first_invalid = False
        raw = outcomes.get(obligation.id, OUTCOME_UNASSESSED)
        if obligation.id in unassessable:
            assessments.append(
                ObligationAssessment(id=obligation.id, outcome=OUTCOME_UNASSESSABLE, evidence_share=0.0)
            )
            continue
        if raw not in (OUTCOME_CORRECT, OUTCOME_INVALID):
            assessments.append(
                ObligationAssessment(id=obligation.id, outcome=OUTCOME_UNASSESSED, evidence_share=0.0)
            )
            continue
        assessments.append(
            ObligationAssessment(id=obligation.id, outcome=raw, evidence_share=per_element_share)
        )
        if raw == OUTCOME_CORRECT and before_first_invalid:
            correct_prefix.append(obligation.id)

    return AssessedTrace(
        obligations=tuple(assessments),
        first_invalid_id=first_invalid_id,
        correct_prefix_ids=tuple(correct_prefix),
        unassessable_ids=tuple(sorted(unassessable)),
        total_task_evidence_mass=total,
    )


def classify_trace_outcome(
    trace: AssessedTrace,
    obligations: list[TraceObligation],
    alphabet: tuple[str, ...],
) -> str | None:
    """Map an assessed trace onto a long-form family's outcome alphabet.

    Deterministic, like the v1 signature matcher: only the persisted trace
    decides. Returns None when the alphabet has no matching class so the
    caller falls back to the rubric-score classifier.
    """

    def first_present(preferences: tuple[str, ...]) -> str | None:
        for preference in preferences:
            if preference in alphabet:
                return preference
        return None

    if not trace.has_assessable_evidence:
        return first_present(("unanswered", "hedge"))
    if trace.first_invalid_id is None:
        return first_present(
            ("complete_correct_structure", "correct_strategy_complete", "integrated_correct")
        )
    by_id = {obligation.id: obligation for obligation in obligations}
    first = by_id.get(trace.first_invalid_id)
    if first is not None and first.kind == "selection":
        return first_present(("wrong_strategy_selected", "surface_match_error"))
    if trace.correct_prefix_ids:
        return first_present(
            (
                "valid_prefix_first_invalid",
                "correct_strategy_execution_slip",
                "partial_integration",
                "structure_without_justification",
            )
        )
    return first_present(("no_viable_structure", "surface_match_error", "other_systematic_error"))
