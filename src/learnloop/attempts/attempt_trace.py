"""Attempt trace — the criterion DAG per attempt (KM §9.6, generalizing the
longform trace to every multi-facet item).

For one graded attempt this reconstructs, per assessable branch of the criterion
dependency DAG:

* **demonstrated** work — an assessable criterion that passed;
* the **first localized error** on each branch — the earliest failed criterion
  whose dependencies all passed (§5.3);
* dependent descendants shown as **not judged** — a criterion downstream of a
  failure is unassessable, and MUST render as *not judged*, never *wrong*.

Pure/derived read over persisted rows: the criterion DAG comes from the item's
resolved rubric (``depends_on``), outcomes from the attempt's non-superseded
grading evidence, and the branch classification from
``localize_criterion_outcomes`` — the same localization the KM2 canonical
projection folds. Nothing is written.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from learnloop.db.repositories import Repository
from learnloop.learner.capability_mapping import (
    CriterionOutcome,
    compile_criterion_targets,
    localize_criterion_outcomes,
)
from learnloop.substrate.canonical_projection import FAILURE_THRESHOLD
from learnloop.attempts.grading import resolved_rubric
from learnloop.vault.models import LoadedVault


@dataclass(frozen=True)
class TraceTarget:
    facet: str
    capability: str
    role: str


@dataclass(frozen=True)
class TraceCriterion:
    criterion_id: str
    description: str
    depends_on: tuple[str, ...]
    points_awarded: float | None       # None => no evidence row (ungraded criterion)
    points_possible: float
    passed: bool
    assessable: bool                   # False => descendant of a first error
    first_error: bool                  # earliest failed criterion on its branch
    status: str                        # "demonstrated" | "first_error" | "not_judged" | "partial"
    targets: tuple[TraceTarget, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "criterion_id": self.criterion_id,
            "description": self.description,
            "depends_on": list(self.depends_on),
            "points_awarded": self.points_awarded,
            "points_possible": self.points_possible,
            "passed": self.passed,
            "assessable": self.assessable,
            "first_error": self.first_error,
            "status": self.status,
            "targets": [
                {"facet": t.facet, "capability": t.capability, "role": t.role}
                for t in self.targets
            ],
        }


@dataclass(frozen=True)
class AttemptTrace:
    attempt_id: str
    practice_item_id: str
    learning_object_id: str
    criteria: list[TraceCriterion] = field(default_factory=list)

    @property
    def has_dag(self) -> bool:
        """True when some criterion actually declares a dependency (a real DAG)."""

        return any(c.depends_on for c in self.criteria)

    def as_dict(self) -> dict[str, object]:
        return {
            "attempt_id": self.attempt_id,
            "practice_item_id": self.practice_item_id,
            "learning_object_id": self.learning_object_id,
            "has_dag": self.has_dag,
            "criteria": [c.as_dict() for c in self.criteria],
            "demonstrated_count": sum(1 for c in self.criteria if c.status == "demonstrated"),
            "first_error_count": sum(1 for c in self.criteria if c.first_error),
            "not_judged_count": sum(1 for c in self.criteria if c.status == "not_judged"),
        }


def build_attempt_trace(
    vault: LoadedVault, repository: Repository, attempt_id: str
) -> AttemptTrace | None:
    """Reconstruct the per-branch criterion trace for one attempt (pure/derived)."""

    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        return None
    item = vault.practice_items.get(attempt["practice_item_id"])
    if item is None:
        return None
    try:
        rubric = resolved_rubric(vault, item)
    except Exception:
        rubric = vault.rubric_for_item(item)
    if rubric is None or not rubric.criteria:
        return AttemptTrace(
            attempt_id=attempt_id,
            practice_item_id=item.id,
            learning_object_id=attempt["learning_object_id"],
            criteria=[],
        )

    evidence_by_criterion = {
        row.criterion_id: row for row in repository.fetch_grading_evidence(attempt_id)
    }

    outcomes: list[CriterionOutcome] = []
    fraction_by_criterion: dict[str, float | None] = {}
    for criterion in rubric.criteria:
        row = evidence_by_criterion.get(criterion.id)
        fraction: float | None = None
        if row is not None and criterion.points > 0:
            fraction = max(0.0, min(1.0, float(row.points_awarded) / criterion.points))
        fraction_by_criterion[criterion.id] = fraction
        outcomes.append(
            CriterionOutcome(
                criterion_id=criterion.id,
                passed=(fraction if fraction is not None else 0.0) >= FAILURE_THRESHOLD,
                depends_on=tuple(criterion.depends_on),
            )
        )
    localized = {c.criterion_id: c for c in localize_criterion_outcomes(outcomes)}

    criteria: list[TraceCriterion] = []
    for criterion in rubric.criteria:
        local = localized[criterion.id]
        row = evidence_by_criterion.get(criterion.id)
        fraction = fraction_by_criterion[criterion.id]
        targets = tuple(
            TraceTarget(
                facet=vault.canonical_facet_id(t.facet), capability=t.capability, role=t.role
            )
            for t in compile_criterion_targets(item, criterion, resolved_rubric=rubric)
        )
        if not local.assessable:
            status = "not_judged"
        elif local.first_error:
            status = "first_error"
        elif local.passed:
            status = "demonstrated"
        else:
            # assessable, not a first error, not a full pass: partial credit branch
            status = "partial"
        criteria.append(
            TraceCriterion(
                criterion_id=criterion.id,
                description=criterion.description,
                depends_on=tuple(criterion.depends_on),
                points_awarded=(row.points_awarded if row is not None else None),
                points_possible=float(criterion.points),
                passed=local.passed,
                assessable=local.assessable,
                first_error=local.first_error,
                status=status,
                targets=targets,
            )
        )

    return AttemptTrace(
        attempt_id=attempt_id,
        practice_item_id=item.id,
        learning_object_id=attempt["learning_object_id"],
        criteria=criteria,
    )
