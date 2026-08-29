"""R2 umbrella for rebuilding every declared derived-state family.

The existing replayers remain independently callable at their historical
startup, upgrade, and maintenance sites.  This module only composes them for an
explicit whole-vault rebuild.  Replayers are ordered, declare their table
ownership, and are checked against :mod:`learnloop.db.table_roles` before the
first write.

Every table classified as ``DERIVED`` is cleared and reconstructed by exactly
one owner.  Captured calibration artifacts and mixed authoritative/projection
rows are deliberately classified outside ``DERIVED`` in
:mod:`learnloop.db.table_roles`; preservation is never disguised as replay.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.learner.assessment_contracts import CANONICAL_STATE_VERSIONS
from learnloop.learner.facet_diagnostics import coverage_denominator_version
from learnloop.learner.identifiability import graph_identifiability_report
from learnloop.learner.mastery import initial_mastery_state_for_learning_object
from learnloop.vault.models import LoadedVault


@dataclass(frozen=True, slots=True)
class DerivedStateReplayer:
    """One ordered replay unit and the derived tables it exclusively owns."""

    name: str
    owned_tables: frozenset[str]
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ReplayerResult:
    """Observable accounting from one replay unit."""

    name: str
    owned_tables: tuple[str, ...]
    rows_processed: int = 0
    accounted_attempt_ids: tuple[str, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "owned_tables": list(self.owned_tables),
            "rows_processed": self.rows_processed,
            "accounted_attempt_ids": list(self.accounted_attempt_ids),
            "details": dict(self.details),
        }


@dataclass(frozen=True, slots=True)
class OrchestratedRebuildResult:
    """Whole-vault rebuild result plus the R3 completeness evidence."""

    algorithm_version: str
    rebuilt_learning_objects: int
    replayed_attempts: int
    learning_object_ids: list[str]
    raw_attempts: int
    accounted_attempt_ids: list[str]
    unaccounted_attempt_ids: list[str]
    replayers: tuple[ReplayerResult, ...]
    marker_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "algorithm_version": self.algorithm_version,
            "rebuilt_learning_objects": self.rebuilt_learning_objects,
            "replayed_attempts": self.replayed_attempts,
            "learning_object_ids": list(self.learning_object_ids),
            "raw_attempts": self.raw_attempts,
            "accounted_attempt_ids": list(self.accounted_attempt_ids),
            "unaccounted_attempt_ids": list(self.unaccounted_attempt_ids),
            "replayers": [result.as_dict() for result in self.replayers],
        }
        if self.marker_id is not None:
            payload["marker_id"] = self.marker_id
        return payload


class ReplayerRegistryError(ValueError):
    """The declarative replayer registry is incomplete or ambiguous."""


class ReplayCompletenessError(RuntimeError):
    """At least one raw attempt was not observed by any registered replayer."""

    def __init__(self, attempt_ids: Sequence[str]):
        self.attempt_ids = tuple(sorted(str(value) for value in attempt_ids))
        super().__init__(
            "raw attempts not accounted for by rebuild replayers: "
            + ", ".join(self.attempt_ids)
        )


# Dependency order is intentionally explicit.  Attempt-derived state is folded
# first, canonical state is projected once over the resulting whole-vault
# ledger, and identifiability consumes that projection.
DERIVED_STATE_REPLAYERS: tuple[DerivedStateReplayer, ...] = (
    # The compatibility backfill materializes missing authoritative activity
    # ledger rows.  It is an ordered rebuild prerequisite but intentionally
    # claims no DERIVED table: the resulting observations are replay inputs.
    DerivedStateReplayer("activity_substrate", frozenset()),
    DerivedStateReplayer(
        "learning_state",
        frozenset(
            {
                "ability_transition_events",
                "attempt_surprise",
                "item_parameter_state",
                "learning_object_mastery",
                "learning_outcome_labels",
                "practice_item_quality_state",
            }
        ),
        ("activity_substrate",),
    ),
    DerivedStateReplayer(
        "canonical_projection",
        frozenset(
            {
                "capability_residual_state",
                "facet_capability_evidence",
                "facet_recall_state",
            }
        ),
        ("learning_state",),
    ),
    DerivedStateReplayer(
        "identifiability",
        frozenset({"subject_identifiability_watermarks"}),
        ("canonical_projection",),
    ),
)

# A shorter public alias is useful to introspection/CI without obscuring the
# more descriptive canonical name.
REPLAYER_REGISTRY = DERIVED_STATE_REPLAYERS


def derived_table_owners(
    replayers: Sequence[DerivedStateReplayer] = DERIVED_STATE_REPLAYERS,
) -> dict[str, tuple[str, ...]]:
    """Return all declared owners, retaining duplicates for validation."""

    owners: dict[str, list[str]] = {}
    for replayer in replayers:
        for table in replayer.owned_tables:
            owners.setdefault(table, []).append(replayer.name)
    return {table: tuple(names) for table, names in sorted(owners.items())}


def validate_replayer_registry(
    replayers: Sequence[DerivedStateReplayer] = DERIVED_STATE_REPLAYERS,
) -> None:
    """Require exact, unique DERIVED ownership and valid dependency order."""

    names = [replayer.name for replayer in replayers]
    duplicate_names = sorted({name for name in names if names.count(name) > 1})
    if duplicate_names:
        raise ReplayerRegistryError(
            "duplicate replayer names: " + ", ".join(duplicate_names)
        )

    owners = derived_table_owners(replayers)
    derived = set(tables_for_role(TableRole.DERIVED))
    declared = set(owners)
    missing = sorted(derived - declared)
    unexpected = sorted(declared - derived)
    duplicate_tables = sorted(
        table for table, table_owners in owners.items() if len(table_owners) != 1
    )
    problems: list[str] = []
    if missing:
        problems.append("unowned DERIVED tables: " + ", ".join(missing))
    if unexpected:
        problems.append("non-DERIVED tables claimed: " + ", ".join(unexpected))
    if duplicate_tables:
        problems.append("multiply owned tables: " + ", ".join(duplicate_tables))

    positions = {name: index for index, name in enumerate(names)}
    for index, replayer in enumerate(replayers):
        for dependency in replayer.depends_on:
            if dependency not in positions:
                problems.append(
                    f"{replayer.name} has unknown dependency {dependency}"
                )
            elif positions[dependency] >= index:
                problems.append(
                    f"{replayer.name} must follow dependency {dependency}"
                )
    if problems:
        raise ReplayerRegistryError("; ".join(problems))


@dataclass(slots=True)
class _ReplayContext:
    vault: LoadedVault
    repository: Repository
    learning_object_ids: list[str] | None
    clock: Clock | None
    learning_result: Any = None


def _rows_in(repository: Repository, table_names: Sequence[str]) -> int:
    with repository.connection() as connection:
        return sum(
            int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
            for table in table_names
        )


def _clear_tables(
    repository: Repository, table_names: Sequence[str]
) -> dict[str, int]:
    """Delete a replayer's whole declared projection family atomically."""

    return repository.clear_derived_projection_tables(table_names)


def _run_activity_substrate(
    spec: DerivedStateReplayer, context: _ReplayContext
) -> ReplayerResult:
    """Backfill the authoritative activity ledger before learner replay."""

    from learnloop.substrate.compat.activity_backfill import backfill_activity_substrate

    report = backfill_activity_substrate(
        context.vault, context.repository, clock=context.clock
    )
    attempts = context.repository.list_all_attempts()
    accounted = tuple(
        sorted(
            str(attempt["id"])
            for attempt in attempts
            if context.repository.observation_by_attempt(str(attempt["id"])) is not None
        )
    )
    return ReplayerResult(
        spec.name,
        (),
        rows_processed=int(report.attempts_replayed),
        accounted_attempt_ids=accounted,
        details=report.as_dict(),
    )


def _run_learning_state(
    spec: DerivedStateReplayer, context: _ReplayContext
) -> ReplayerResult:
    cleared: dict[str, int] = {}
    if context.learning_object_ids is None:
        # A whole-vault rebuild must remove rows whose source attempt/content no
        # longer exists.  The per-LO replay below still performs its historical
        # scoped resets; those are harmless after this family-level clear.
        cleared = _clear_tables(context.repository, tuple(spec.owned_tables))

    from learnloop.substrate.replay import rebuild_derived_state

    result = rebuild_derived_state(
        context.vault,
        context.repository,
        learning_object_ids=context.learning_object_ids,
        clock=context.clock,
        record_receipt=False,
        project_canonical_state=False,
    )
    context.learning_result = result

    # Bootstrap normally creates a cold mastery row for every authored LO.  A
    # full clear must reproduce those zero-attempt projections as well as the
    # attempt-backed rows.  Use a stable baseline timestamp: no event exists
    # from which a meaningful observation time could be derived.
    cold_mastery_rows = 0
    if context.learning_object_ids is None:
        existing = set(context.repository.mastery_states())
        for learning_object_id in sorted(set(context.vault.learning_objects) - existing):
            state = initial_mastery_state_for_learning_object(
                context.vault,
                context.repository,
                learning_object_id,
                "1970-01-01T00:00:00Z",
            )
            context.repository.upsert_mastery_state(state)
            cold_mastery_rows += 1

    rebuilt = set(result.learning_object_ids)
    accounted = tuple(
        sorted(
            str(attempt["id"])
            for attempt in context.repository.list_all_attempts()
            if str(attempt.get("learning_object_id")) in rebuilt
        )
    )
    return ReplayerResult(
        spec.name,
        tuple(sorted(spec.owned_tables)),
        rows_processed=result.replayed_attempts,
        accounted_attempt_ids=accounted,
        details={
            "cleared_rows_by_table": cleared,
            "cold_mastery_rows": cold_mastery_rows,
            "rebuilt_learning_objects": result.rebuilt_learning_objects,
            "learning_object_ids": list(result.learning_object_ids),
        },
    )


def _run_canonical_projection(
    spec: DerivedStateReplayer, context: _ReplayContext
) -> ReplayerResult:
    # The projector replaces these tables for canonical algorithm versions.
    # Clear here as the owner boundary as well, so stale canonical rows are
    # removed when replaying a pre-canonical compatibility version.
    cleared = _clear_tables(context.repository, tuple(spec.owned_tables))
    from learnloop.substrate.canonical_projection import project_canonical_facet_state

    project_canonical_facet_state(
        context.vault, context.repository, clock=context.clock
    )
    rows = _rows_in(context.repository, tuple(spec.owned_tables))
    return ReplayerResult(
        spec.name,
        tuple(sorted(spec.owned_tables)),
        rows_processed=rows,
        details={"cleared_rows_by_table": cleared},
    )


def _run_identifiability(
    spec: DerivedStateReplayer, context: _ReplayContext
) -> ReplayerResult:
    cleared = _clear_tables(context.repository, tuple(spec.owned_tables))
    if (
        context.vault.config.algorithms.algorithm_version
        not in CANONICAL_STATE_VERSIONS
    ):
        return ReplayerResult(
            spec.name,
            tuple(sorted(spec.owned_tables)),
            details={"cleared_rows_by_table": cleared},
        )

    report = graph_identifiability_report(
        context.vault,
        context.repository,
        schedule_probes=False,
        clock=context.clock,
    )
    written = 0
    for subject in report["subjects"]:
        subject_id = subject.get("subject_id")
        if subject_id is None:
            continue
        context.repository.upsert_identifiability_watermark(
            subject_id=str(subject_id),
            registry_hash=str(subject["registry_hash"]),
            finding_count=int(subject["counts"]["findings"]),
            clock=context.clock,
        )
        written += 1
    return ReplayerResult(
        spec.name,
        tuple(sorted(spec.owned_tables)),
        rows_processed=written,
        details={"cleared_rows_by_table": cleared},
    )


_RUNNERS = {
    "activity_substrate": _run_activity_substrate,
    "learning_state": _run_learning_state,
    "canonical_projection": _run_canonical_projection,
    "identifiability": _run_identifiability,
}


def rebuild_all_derived_state(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_ids: list[str] | None = None,
    clock: Clock | None = None,
    require_complete_attempt_coverage: bool = True,
) -> OrchestratedRebuildResult:
    """Run all registered replayers and append exactly one rebuild receipt.

    Registry validation happens before any write.  Attempt completeness is the
    union of explicit accounting returned by every replay unit.  A completeness
    failure is raised before the receipt is written.
    """

    validate_replayer_registry()
    raw_attempts = repository.list_all_attempts()
    requested = set(learning_object_ids or ())
    raw_attempt_ids = {
        str(attempt["id"])
        for attempt in raw_attempts
        if not requested or str(attempt.get("learning_object_id")) in requested
    }
    context = _ReplayContext(vault, repository, learning_object_ids, clock)
    results: list[ReplayerResult] = []
    for spec in DERIVED_STATE_REPLAYERS:
        results.append(_RUNNERS[spec.name](spec, context))

    accounted = {
        attempt_id
        for result in results
        for attempt_id in result.accounted_attempt_ids
    }
    unaccounted = sorted(raw_attempt_ids - accounted)
    if require_complete_attempt_coverage and unaccounted:
        raise ReplayCompletenessError(unaccounted)

    learning = context.learning_result
    if learning is None:  # pragma: no cover - registry validation/order guards this
        raise ReplayerRegistryError("learning_state replayer did not produce a result")

    # Receipt ownership stays centralized here.  Internal LO replay suppresses
    # its historical marker, while every direct legacy caller keeps that marker.
    from learnloop.substrate.canonical_projection import CANONICAL_PROJECTION_VERSION
    scope = "learning_object" if learning_object_ids else "all"
    marker_id = repository.record_derived_state_rebuild(
        scope=scope,
        learning_object_ids=list(learning.learning_object_ids),
        algorithm_version=vault.config.algorithms.algorithm_version,
        rebuilt_learning_objects=learning.rebuilt_learning_objects,
        replayed_attempts=learning.replayed_attempts,
        canonical_projection_version=CANONICAL_PROJECTION_VERSION,
        coverage_denominator_version=coverage_denominator_version(vault, repository),
        clock=clock,
    )
    return OrchestratedRebuildResult(
        algorithm_version=vault.config.algorithms.algorithm_version,
        rebuilt_learning_objects=learning.rebuilt_learning_objects,
        replayed_attempts=learning.replayed_attempts,
        learning_object_ids=list(learning.learning_object_ids),
        raw_attempts=len(raw_attempt_ids),
        accounted_attempt_ids=sorted(accounted & raw_attempt_ids),
        unaccounted_attempt_ids=unaccounted,
        replayers=tuple(results),
        marker_id=marker_id,
    )


# The proposal and CLI call this concept "rebuild-derived-state".  Keep a
# concise domain alias while retaining the explicit name above in Python APIs.
rebuild_derived_state_umbrella = rebuild_all_derived_state


__all__ = [
    "DERIVED_STATE_REPLAYERS",
    "REPLAYER_REGISTRY",
    "DerivedStateReplayer",
    "OrchestratedRebuildResult",
    "ReplayCompletenessError",
    "ReplayerRegistryError",
    "ReplayerResult",
    "derived_table_owners",
    "rebuild_all_derived_state",
    "rebuild_derived_state_umbrella",
    "validate_replayer_registry",
]
