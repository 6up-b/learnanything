"""Typed, blind-grade-equivalent history for the diagnoser (Slice 1 §5.2).

Everything the diagnoser may see about the past passes through these records.
They carry only measurement fields: date, surface group, score, failed and
passed criteria, first-divergence quotes, error types, targets, validity
scope, assisted/primed flags and (for ``full``/``snapshot``) the answer text.
Prior hypotheses appear only as typed records with a lifecycle status and an
evidence count (S3). There is deliberately no field for prior diagnosis prose,
candidate causes, misconception statements or repair rationales, so a legacy
joint-graded attempt is stripped of its causal fields simply by being read.

Two stores implement :class:`HistoryStore`:

* :class:`VaultHistoryStore` reads a vault database (normally a scratch copy)
  and overlays fresh blind grades where the caller has them;
* :class:`StaticHistoryStore` holds an explicit history, used for planted
  learners whose whole past is constructed.

Both apply the same as-of cutoff: only attempts completed strictly before the
diagnosed attempt, and only hypotheses/registry rows whose source attempt
precedes it. Status is read as of now (status history is not versioned; the
receipt discloses ``lagged_attempts``).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from typing import Any, Iterable, Mapping, Protocol, Sequence

from learnloop.attempts.grading import resolved_rubric
from learnloop.db.repositories import Repository
from learnloop.substrate.canonical_projection import surface_group_id
from learnloop.vault.models import LoadedVault, PracticeItem

#: Attempt types that measure nothing and never appear as history.
NON_MEASURING_ATTEMPT_TYPES = frozenset({"skip", "self_report", "guided_walkthrough"})
ASSISTED_ATTEMPT_TYPES = frozenset(
    {"hinted_attempt", "guided_walkthrough", "reconstruction_after_walkthrough"}
)
#: Joint ``cause_scope`` values that are validity judgements; any other value
#: (a causal class or ``unknown``) means the joint grader did NOT flag the
#: measurement, i.e. it treated it as valid.
_VALIDITY_FROM_JOINT = {
    "item_contract": "item_contract",
    "grader_interpretation": "grader_interpretation",
    "interaction_context": "interaction_context",
}
#: S3 lifecycle vocabulary shown to the diagnoser.
_HYPOTHESIS_LIFECYCLE = {
    "candidate": "candidate",
    "open_set": "candidate",
    "validated": "probe_confirmed",
    "demoted": "refuted",
    "retired": "withdrawn",
}
_FACTOR_LIFECYCLE = {"open": "candidate", "resolved": "resolved", "retired": "withdrawn"}
_MISCONCEPTION_LIFECYCLE = {
    "active": "durable_active",
    "resolving": "durable_resolving",
    "resolved": "durable_resolved",
}


@dataclass(frozen=True)
class AttemptRef:
    """Where an attempt sits on the global chronological axis."""

    attempt_id: str
    completed_at: str

    def key(self) -> tuple[str, str]:
        return (self.completed_at, self.attempt_id)


@dataclass(frozen=True)
class HistoryAttempt:
    """One prior attempt, rendered from blind-grade-equivalent fields only."""

    attempt_id: str
    learning_object_id: str
    practice_item_id: str
    completed_at: str
    surface_group: str
    item_prompt: str
    learner_answer_md: str
    attempt_type: str
    score: float | None
    max_points: float | None
    failed_criteria: tuple[str, ...] = ()
    passed_criteria: tuple[str, ...] = ()
    fatal_errors: tuple[str, ...] = ()
    first_divergence_quotes: tuple[str, ...] = ()
    error_types: tuple[str, ...] = ()
    target_facets: tuple[str, ...] = ()
    target_criteria: tuple[str, ...] = ()
    validity_scopes: tuple[str, ...] = ()
    item_facets: tuple[str, ...] = ()
    assisted: bool = False
    primed: bool = False
    grader_mode: str = "joint"
    #: Divergence-recipe input for hybrid retrieval only; never rendered into
    #: a context (it is grader prose, and only blind grades carry it).
    local_analysis_md: str | None = None

    def key(self) -> tuple[str, str]:
        return (self.completed_at, self.attempt_id)

    @property
    def non_pass(self) -> bool:
        """Any non-full criterion, fatal error or error attribution."""

        return bool(self.failed_criteria or self.fatal_errors or self.error_types)

    @property
    def cold_unassisted(self) -> bool:
        return not self.assisted and not self.primed

    @property
    def valid_measurement(self) -> bool:
        """S4: at least one attribution is a valid measurement (or none flagged)."""

        if not self.validity_scopes:
            return True
        return any(scope == "valid_measurement" for scope in self.validity_scopes)

    def facets(self) -> frozenset[str]:
        return frozenset((*self.target_facets, *self.item_facets))


@dataclass(frozen=True)
class HypothesisRecord:
    """A typed prior hypothesis, factor or durable misconception (no prose)."""

    id: str
    kind: str  # causal_hypothesis | unresolved_factor | misconception
    statement: str
    scope: str
    status: str
    lifecycle: str
    learning_object_id: str | None
    source_attempt_id: str | None
    validated_evidence_count: int
    last_updated: str | None
    target_facets: tuple[str, ...] = ()
    repair_class_id: str | None = None


@dataclass(frozen=True)
class RegistryRecord:
    """A durable misconception or a holding-pen candidate the diagnoser may match."""

    id: str
    kind: str  # durable | candidate
    statement: str
    learning_object_id: str | None
    status: str
    facet_ids: tuple[str, ...] = ()
    occurrence_count: int = 0
    source_attempt_id: str | None = None


@dataclass(frozen=True)
class RepairRecord:
    """A repair tried on these facets and how its cold verifications went."""

    repair_class_id: str
    operator: str
    target_facets: tuple[str, ...]
    hypothesis_ids: tuple[str, ...]
    cold_successes: int
    cold_failures: int
    source_attempt_id: str | None = None


@dataclass(frozen=True)
class Neighborhood:
    """The LO and its one-hop prerequisite / confusable neighbours (§5.2)."""

    learning_object_id: str
    prerequisite_ids: tuple[str, ...] = ()
    dependent_ids: tuple[str, ...] = ()
    confusable_ids: tuple[str, ...] = ()
    same_concept_ids: tuple[str, ...] = ()

    def all_ids(self) -> tuple[str, ...]:
        ordered: dict[str, None] = {self.learning_object_id: None}
        for value in (
            *self.same_concept_ids,
            *self.prerequisite_ids,
            *self.dependent_ids,
            *self.confusable_ids,
        ):
            ordered.setdefault(value, None)
        return tuple(ordered)

    def relation(self, learning_object_id: str) -> str:
        if learning_object_id == self.learning_object_id:
            return "same_lo"
        if learning_object_id in self.same_concept_ids:
            return "same_concept"
        if learning_object_id in self.prerequisite_ids:
            return "prerequisite"
        if learning_object_id in self.dependent_ids:
            return "dependent"
        if learning_object_id in self.confusable_ids:
            return "confusable"
        return "other"


def learning_object_neighborhood(vault: LoadedVault, learning_object_id: str) -> Neighborhood:
    """One hop over prerequisite and confusable edges, both directions.

    LO ``prerequisites`` / ``confusables`` name concepts (or, in some vaults,
    LO ids); concept edges add typed relations. LOs sharing the concept are
    listed separately: they are the same node of the concept graph.
    """

    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        return Neighborhood(learning_object_id=learning_object_id)
    by_concept: dict[str, list[str]] = {}
    for lo in sorted(vault.learning_objects.values(), key=lambda value: value.id):
        by_concept.setdefault(lo.concept, []).append(lo.id)
    concept = learning_object.concept

    def los_for(names: Iterable[str]) -> list[str]:
        found: list[str] = []
        for name in names:
            if name in vault.learning_objects:
                found.append(name)
            found.extend(by_concept.get(name, []))
        return found

    prerequisite_concepts = set(learning_object.prerequisites)
    dependent_concepts: set[str] = set()
    confusable_concepts = set(learning_object.confusables)
    for edge in vault.edges:
        if edge.relation_type == "prerequisite":
            if edge.target == concept:
                prerequisite_concepts.add(edge.source)
            elif edge.source == concept:
                dependent_concepts.add(edge.target)
        elif edge.relation_type == "confusable_with":
            if edge.source == concept:
                confusable_concepts.add(edge.target)
            elif edge.target == concept:
                confusable_concepts.add(edge.source)
    for lo in vault.learning_objects.values():
        if concept in lo.prerequisites or learning_object.id in lo.prerequisites:
            dependent_concepts.add(lo.id)
        if concept in lo.confusables or learning_object.id in lo.confusables:
            confusable_concepts.add(lo.id)

    def clean(values: Iterable[str], *exclude: Iterable[str]) -> tuple[str, ...]:
        skip = {learning_object_id}
        for group in exclude:
            skip.update(group)
        return tuple(sorted({value for value in values if value not in skip}))

    same = clean(by_concept.get(concept, []))
    prerequisites = clean(los_for(prerequisite_concepts), same)
    dependents = clean(los_for(dependent_concepts), same, prerequisites)
    confusables = clean(los_for(confusable_concepts), same, prerequisites, dependents)
    return Neighborhood(
        learning_object_id=learning_object_id,
        prerequisite_ids=prerequisites,
        dependent_ids=dependents,
        confusable_ids=confusables,
        same_concept_ids=same,
    )


class HistoryStore(Protocol):
    """What the context assembler reads; every method applies ``before``."""

    def attempt(self, attempt_id: str) -> HistoryAttempt | None:
        ...

    def attempts_before(
        self, before: AttemptRef, learning_object_ids: Sequence[str] | None = None
    ) -> list[HistoryAttempt]:
        """Prior attempts in chronological order; ``None`` = the whole vault."""
        ...

    def hypotheses_before(
        self, before: AttemptRef, learning_object_ids: Sequence[str]
    ) -> list[HypothesisRecord]:
        ...

    def registry_before(
        self, before: AttemptRef, learning_object_ids: Sequence[str] | None
    ) -> list[RegistryRecord]:
        ...

    def repairs_before(
        self, before: AttemptRef, facets: Iterable[str] | None
    ) -> list[RepairRecord]:
        ...

    def lagged_attempts(self, before: AttemptRef) -> int:
        """Attempts that exist after the cutoff (async lag disclosure)."""
        ...


def _decode_json(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _max_points_by_criterion(vault: LoadedVault, item: PracticeItem | None) -> tuple[dict[str, float], float | None]:
    if item is None:
        return {}, None
    try:
        rubric = resolved_rubric(vault, item)
    except Exception:  # noqa: BLE001 - a broken rubric must not hide history
        return {}, None
    return {criterion.id: float(criterion.points) for criterion in rubric.criteria}, float(rubric.max_points)


def _target_facets_from(attribution: Mapping[str, Any], vault: LoadedVault) -> list[str]:
    facets = [
        vault.canonical_facet_id(str(value))
        for value in attribution.get("target_evidence_families") or []
    ]
    ref = attribution.get("target_ref")
    if isinstance(ref, Mapping) and ref.get("kind") == "facet_capability" and ref.get("facet_id"):
        facets.append(vault.canonical_facet_id(str(ref["facet_id"])))
    return facets


def _quote_from(first_divergence: Any) -> str | None:
    if not isinstance(first_divergence, Mapping):
        return None
    quote = first_divergence.get("quote") or first_divergence.get("normalized_quote")
    return str(quote).strip() if quote and str(quote).strip() else None


def history_attempt_from_blind_record(
    vault: LoadedVault,
    *,
    attempt_id: str,
    item: PracticeItem | None,
    learning_object_id: str,
    practice_item_id: str,
    completed_at: str,
    learner_answer_md: str,
    attempt_type: str,
    record: Mapping[str, Any],
    hints_used: int = 0,
    primed: bool = False,
) -> HistoryAttempt:
    """Blind-grade-equivalent fields from a validated blind grade record."""

    maxima, max_points = _max_points_by_criterion(vault, item)
    failed: list[str] = []
    passed: list[str] = []
    for row in record.get("criteria") or []:
        criterion_id = str(row.get("criterion_id") or "")
        points = float(row.get("points_awarded") or 0.0)
        maximum = maxima.get(criterion_id)
        if maximum is not None and points + 1e-9 >= maximum:
            passed.append(criterion_id)
        else:
            failed.append(criterion_id)
    attributions = [row for row in record.get("error_attributions") or [] if isinstance(row, Mapping)]
    return HistoryAttempt(
        attempt_id=attempt_id,
        learning_object_id=learning_object_id,
        practice_item_id=practice_item_id,
        completed_at=completed_at,
        surface_group=surface_group_id(item) if item is not None else f"item:{practice_item_id}",
        item_prompt=item.prompt if item is not None else "",
        learner_answer_md=learner_answer_md or "",
        attempt_type=attempt_type,
        score=float(record["rubric_score"]) if record.get("rubric_score") is not None else None,
        max_points=float(record.get("max_points") or max_points or 0.0) or max_points,
        failed_criteria=tuple(failed),
        passed_criteria=tuple(passed),
        fatal_errors=tuple(str(value) for value in record.get("fatal_errors") or []),
        first_divergence_quotes=tuple(
            quote
            for row in attributions
            if (quote := _quote_from(row.get("first_divergence"))) is not None
        ),
        error_types=tuple(str(row.get("error_type") or "") for row in attributions if row.get("error_type")),
        target_facets=tuple(
            dict.fromkeys(facet for row in attributions for facet in _target_facets_from(row, vault))
        ),
        target_criteria=tuple(
            dict.fromkeys(str(value) for row in attributions for value in row.get("target_criterion_ids") or [])
        ),
        validity_scopes=tuple(str(row.get("validity_scope") or "unknown") for row in attributions),
        item_facets=tuple(
            vault.canonical_facet_id(str(facet)) for facet in (item.evidence_facets if item else [])
        ),
        assisted=bool(hints_used) or attempt_type in ASSISTED_ATTEMPT_TYPES,
        primed=bool(primed),
        grader_mode="blind",
        local_analysis_md=str(record.get("local_analysis_md") or "") or None,
    )


class VaultHistoryStore:
    """History read from a vault database, with an optional blind-grade overlay.

    The overlay maps attempt id -> validated blind grade record
    (:meth:`ValidatedBlindGrade.as_record`). Attempts without one are read
    from the stored joint grade and stripped to the same fields.
    """

    def __init__(
        self,
        vault: LoadedVault,
        repository: Repository,
        *,
        blind_grades: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> None:
        self.vault = vault
        self.repository = repository
        self._blind = dict(blind_grades or {})
        self._loaded = False
        self._attempts: list[HistoryAttempt] = []
        self._by_id: dict[str, HistoryAttempt] = {}
        self._order: dict[str, tuple[str, str]] = {}
        self._error_event_attempt: dict[str, str] = {}
        self._hypotheses: list[HypothesisRecord] = []
        self._registry: list[RegistryRecord] = []
        self._repairs: list[RepairRecord] = []

    def with_blind_grades(self, blind_grades: Mapping[str, Mapping[str, Any]]) -> "VaultHistoryStore":
        merged = {**self._blind, **dict(blind_grades)}
        return VaultHistoryStore(self.vault, self.repository, blind_grades=merged)

    # -- loading ------------------------------------------------------------

    def _load(self) -> None:
        if self._loaded:
            return
        vault = self.vault
        with self.repository.connection() as connection:
            attempts = [dict(row) for row in connection.execute(
                "SELECT id, practice_item_id, learning_object_id, attempt_type, "
                "learner_answer_md, rubric_score, correctness, hints_used, primed, "
                "created_at FROM practice_attempts ORDER BY created_at, id"
            )]
            evidence: dict[str, dict[str, float]] = {}
            for row in connection.execute(
                "SELECT attempt_id, criterion_id, points_awarded FROM grading_evidence "
                "WHERE superseded_at IS NULL ORDER BY created_at, criterion_id"
            ):
                evidence.setdefault(str(row[0]), {})[str(row[1])] = float(row[2] or 0.0)
            events: dict[str, list[dict[str, Any]]] = {}
            for row in connection.execute(
                "SELECT id, attempt_id, error_type, repair_plan_json FROM error_events "
                "ORDER BY created_at, id"
            ):
                if row[1] is None:
                    continue
                self._error_event_attempt[str(row[0])] = str(row[1])
                events.setdefault(str(row[1]), []).append(
                    {"error_type": str(row[2]), "repair_plan": _decode_json(row[3], {}) or {}}
                )
            fatal: dict[str, list[str]] = {
                str(row[0]): [str(value) for value in _decode_json(row[1], [])]
                for row in connection.execute(
                    "SELECT attempt_id, fatal_errors_json FROM attempt_feedback_metadata"
                )
            }
            hypotheses = [dict(row) for row in connection.execute(
                "SELECT h.* FROM causal_hypotheses h WHERE h.version = ("
                "SELECT MAX(head.version) FROM causal_hypotheses head "
                "WHERE head.episode_key = h.episode_key) ORDER BY h.created_at, h.id"
            )]
            factors = [dict(row) for row in connection.execute(
                "SELECT * FROM unresolved_cause_factors ORDER BY created_at, id"
            )]
            misconceptions = [dict(row) for row in connection.execute(
                "SELECT * FROM misconceptions ORDER BY created_at, id"
            )]
            candidates = [dict(row) for row in connection.execute(
                "SELECT * FROM misconception_candidates ORDER BY created_at, id"
            )]
            cold = [dict(row) for row in connection.execute(
                "SELECT source_attempt_id, repair_class_id, success FROM causal_cold_verifications"
            )]
        repair_ids = sorted({str(row["repair_class_id"]) for row in hypotheses if row.get("repair_class_id")})
        definitions = self.repository.causal_repair_class_definitions(repair_ids) if repair_ids else {}

        for row in attempts:
            attempt_type = str(row.get("attempt_type") or "")
            if attempt_type in NON_MEASURING_ATTEMPT_TYPES:
                continue
            attempt_id = str(row["id"])
            item = vault.practice_items.get(str(row["practice_item_id"]))
            completed_at = str(row["created_at"])
            self._order[attempt_id] = (completed_at, attempt_id)
            if attempt_id in self._blind:
                record = history_attempt_from_blind_record(
                    vault,
                    attempt_id=attempt_id,
                    item=item,
                    learning_object_id=str(row["learning_object_id"]),
                    practice_item_id=str(row["practice_item_id"]),
                    completed_at=completed_at,
                    learner_answer_md=str(row.get("learner_answer_md") or ""),
                    attempt_type=attempt_type,
                    record=self._blind[attempt_id],
                    hints_used=int(row.get("hints_used") or 0),
                    primed=bool(row.get("primed")),
                )
            else:
                record = self._from_stored(
                    row, item, evidence.get(attempt_id, {}), events.get(attempt_id, []),
                    fatal.get(attempt_id, []),
                )
            self._attempts.append(record)
            self._by_id[attempt_id] = record

        for row in hypotheses:
            target_ref = _decode_json(row.get("target_ref_json"), None)
            facets: tuple[str, ...] = ()
            if isinstance(target_ref, Mapping) and target_ref.get("kind") == "facet_capability":
                facets = (vault.canonical_facet_id(str(target_ref.get("facet_id") or "")),)
            evidence_rows = _decode_json(row.get("evidence_json"), [])
            status = str(row.get("status") or "candidate")
            self._hypotheses.append(
                HypothesisRecord(
                    id=str(row["id"]),
                    kind="causal_hypothesis",
                    statement=str(row.get("statement") or ""),
                    scope=str(row.get("cause_scope") or "unknown"),
                    status=status,
                    lifecycle=_HYPOTHESIS_LIFECYCLE.get(status, status),
                    learning_object_id=str(row.get("learning_object_id") or "") or None,
                    source_attempt_id=str(row.get("attempt_id") or "") or None,
                    validated_evidence_count=len(evidence_rows) if isinstance(evidence_rows, list) else 0,
                    last_updated=str(row.get("created_at") or "") or None,
                    target_facets=facets,
                    repair_class_id=str(row.get("repair_class_id") or "") or None,
                )
            )
        for row in factors:
            causes = _decode_json(row.get("candidate_causes_json"), [])
            statements = [
                str(cause.get("statement") or "").strip()
                for cause in causes
                if isinstance(cause, Mapping) and str(cause.get("statement") or "").strip()
            ]
            attempt_id = str(row.get("attempt_id") or "")
            source = self._by_id.get(attempt_id)
            status = str(row.get("status") or "open")
            self._hypotheses.append(
                HypothesisRecord(
                    id=str(row["id"]),
                    kind="unresolved_factor",
                    statement=" | ".join(statements),
                    scope="learner_state",
                    status=status,
                    lifecycle=_FACTOR_LIFECYCLE.get(status, status),
                    learning_object_id=source.learning_object_id if source else None,
                    source_attempt_id=attempt_id or None,
                    validated_evidence_count=len(_decode_json(row.get("resolution_observation_ids_json"), []) or []),
                    last_updated=str(row.get("updated_at") or row.get("created_at") or "") or None,
                )
            )
        for row in misconceptions:
            sources = [str(value) for value in _decode_json(row.get("source_error_event_ids_json"), []) or []]
            status = str(row.get("status") or "active")
            record = HypothesisRecord(
                id=str(row["id"]),
                kind="misconception",
                statement=str(row.get("statement") or ""),
                scope="learner_state",
                status=status,
                lifecycle=_MISCONCEPTION_LIFECYCLE.get(status, status),
                learning_object_id=str(row.get("learning_object_id") or "") or None,
                source_attempt_id=self._earliest_source(sources),
                validated_evidence_count=len(sources),
                last_updated=str(row.get("updated_at") or row.get("created_at") or "") or None,
                target_facets=tuple(
                    vault.canonical_facet_id(str(value))
                    for value in _decode_json(row.get("facet_ids_json"), []) or []
                ),
            )
            self._hypotheses.append(record)
            self._registry.append(
                RegistryRecord(
                    id=record.id,
                    kind="durable",
                    statement=record.statement,
                    learning_object_id=record.learning_object_id,
                    status=status,
                    facet_ids=record.target_facets,
                    occurrence_count=len(sources),
                    source_attempt_id=record.source_attempt_id,
                )
            )
        for row in candidates:
            if str(row.get("status") or "candidate") != "candidate":
                continue
            sources = [str(value) for value in _decode_json(row.get("source_error_event_ids_json"), []) or []]
            self._registry.append(
                RegistryRecord(
                    id=str(row["id"]),
                    kind="candidate",
                    statement=str(row.get("statement") or ""),
                    learning_object_id=str(row.get("learning_object_id") or "") or None,
                    status="candidate",
                    facet_ids=tuple(
                        vault.canonical_facet_id(str(value))
                        for value in _decode_json(row.get("facet_ids_json"), []) or []
                    ),
                    occurrence_count=int(row.get("occurrence_count") or 0),
                    source_attempt_id=self._earliest_source(sources),
                )
            )
        outcomes: dict[str, list[int]] = {}
        for row in cold:
            outcomes.setdefault(str(row["repair_class_id"]), []).append(int(row["success"] or 0))
        by_class: dict[str, list[HypothesisRecord]] = {}
        for record in self._hypotheses:
            if record.repair_class_id:
                by_class.setdefault(record.repair_class_id, []).append(record)
        for repair_class_id, owners in sorted(by_class.items()):
            definition = definitions.get(repair_class_id) or {}
            refs = definition.get("target_refs") or []
            facets = tuple(
                dict.fromkeys(
                    vault.canonical_facet_id(str(ref.get("facet_id")))
                    for ref in refs
                    if isinstance(ref, Mapping) and ref.get("kind") == "facet_capability" and ref.get("facet_id")
                )
            ) or tuple(dict.fromkeys(facet for owner in owners for facet in owner.target_facets))
            results = outcomes.get(repair_class_id, [])
            sources = [owner.source_attempt_id for owner in owners if owner.source_attempt_id]
            self._repairs.append(
                RepairRecord(
                    repair_class_id=repair_class_id,
                    operator=str(definition.get("operator") or ""),
                    target_facets=facets,
                    hypothesis_ids=tuple(owner.id for owner in owners),
                    cold_successes=sum(results),
                    cold_failures=len(results) - sum(results),
                    source_attempt_id=min(sources, key=lambda value: self._order.get(value, ("~", value)), default=None),
                )
            )
        self._loaded = True

    def _earliest_source(self, error_event_ids: Sequence[str]) -> str | None:
        attempts = [
            self._error_event_attempt[value]
            for value in error_event_ids
            if value in self._error_event_attempt
        ]
        if not attempts:
            return None
        return min(attempts, key=lambda value: self._order.get(value, ("~", value)))

    def _from_stored(
        self,
        row: Mapping[str, Any],
        item: PracticeItem | None,
        points: Mapping[str, float],
        events: Sequence[Mapping[str, Any]],
        fatal: Sequence[str],
    ) -> HistoryAttempt:
        """A stored joint grade, reduced to blind-grade-equivalent fields (S3)."""

        vault = self.vault
        maxima, max_points = _max_points_by_criterion(vault, item)
        failed: list[str] = []
        passed: list[str] = []
        for criterion_id, awarded in points.items():
            maximum = maxima.get(criterion_id)
            if maximum is not None and awarded + 1e-9 >= maximum:
                passed.append(criterion_id)
            else:
                failed.append(criterion_id)
        attempt_type = str(row.get("attempt_type") or "")
        if attempt_type == "dont_know" and not failed:
            failed = sorted(maxima) or ["dont_know"]
        plans = [event.get("repair_plan") or {} for event in events]
        validity = []
        for plan in plans:
            scope = str(plan.get("cause_scope") or "")
            validity.append(_VALIDITY_FROM_JOINT.get(scope, "valid_measurement"))
        return HistoryAttempt(
            attempt_id=str(row["id"]),
            learning_object_id=str(row["learning_object_id"]),
            practice_item_id=str(row["practice_item_id"]),
            completed_at=str(row["created_at"]),
            surface_group=surface_group_id(item) if item is not None else f"item:{row['practice_item_id']}",
            item_prompt=item.prompt if item is not None else "",
            learner_answer_md=str(row.get("learner_answer_md") or ""),
            attempt_type=attempt_type,
            score=float(row["rubric_score"]) if row.get("rubric_score") is not None else None,
            max_points=max_points,
            failed_criteria=tuple(sorted(failed)),
            passed_criteria=tuple(sorted(passed)),
            fatal_errors=tuple(fatal),
            first_divergence_quotes=tuple(
                quote for plan in plans if (quote := _quote_from(plan.get("first_divergence"))) is not None
            ),
            error_types=tuple(str(event.get("error_type") or "") for event in events if event.get("error_type")),
            target_facets=tuple(
                dict.fromkeys(facet for plan in plans for facet in _target_facets_from(plan, vault))
            ),
            target_criteria=tuple(
                dict.fromkeys(str(value) for plan in plans for value in plan.get("target_criterion_ids") or [])
            ),
            validity_scopes=tuple(validity),
            item_facets=tuple(
                vault.canonical_facet_id(str(facet)) for facet in (item.evidence_facets if item else [])
            ),
            assisted=bool(row.get("hints_used")) or attempt_type in ASSISTED_ATTEMPT_TYPES,
            primed=bool(row.get("primed")),
            grader_mode="joint",
        )

    # -- HistoryStore -------------------------------------------------------

    def attempt(self, attempt_id: str) -> HistoryAttempt | None:
        self._load()
        return self._by_id.get(attempt_id)

    def ref(self, attempt_id: str) -> AttemptRef | None:
        self._load()
        order = self._order.get(attempt_id)
        return AttemptRef(attempt_id, order[0]) if order else None

    def all_attempts(self) -> list[HistoryAttempt]:
        self._load()
        return list(self._attempts)

    def attempts_before(
        self, before: AttemptRef, learning_object_ids: Sequence[str] | None = None
    ) -> list[HistoryAttempt]:
        self._load()
        wanted = set(learning_object_ids) if learning_object_ids is not None else None
        return [
            attempt
            for attempt in self._attempts
            if attempt.key() < before.key()
            and (wanted is None or attempt.learning_object_id in wanted)
        ]

    def _source_before(self, source_attempt_id: str | None, before: AttemptRef) -> bool:
        if source_attempt_id is None:
            return False
        order = self._order.get(source_attempt_id)
        return order is not None and order < before.key()

    def hypotheses_before(
        self, before: AttemptRef, learning_object_ids: Sequence[str]
    ) -> list[HypothesisRecord]:
        self._load()
        wanted = set(learning_object_ids)
        return [
            record
            for record in self._hypotheses
            if record.learning_object_id in wanted
            and self._source_before(record.source_attempt_id, before)
        ]

    def registry_before(
        self, before: AttemptRef, learning_object_ids: Sequence[str] | None
    ) -> list[RegistryRecord]:
        self._load()
        wanted = set(learning_object_ids) if learning_object_ids is not None else None
        return [
            record
            for record in self._registry
            if (wanted is None or record.learning_object_id in wanted)
            and self._source_before(record.source_attempt_id, before)
        ]

    def repairs_before(
        self, before: AttemptRef, facets: Iterable[str] | None
    ) -> list[RepairRecord]:
        self._load()
        wanted = set(facets) if facets is not None else None
        return [
            record
            for record in self._repairs
            if self._source_before(record.source_attempt_id, before)
            and (wanted is None or not record.target_facets or wanted & set(record.target_facets))
        ]

    def lagged_attempts(self, before: AttemptRef) -> int:
        self._load()
        return sum(1 for attempt in self._attempts if attempt.key() > before.key())


@dataclass
class StaticHistoryStore:
    """An explicit history, e.g. a planted learner's whole constructed past."""

    attempts: list[HistoryAttempt] = field(default_factory=list)
    hypotheses: list[HypothesisRecord] = field(default_factory=list)
    registry: list[RegistryRecord] = field(default_factory=list)
    repairs: list[RepairRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.attempts = sorted(self.attempts, key=lambda attempt: attempt.key())
        self._order = {attempt.attempt_id: attempt.key() for attempt in self.attempts}

    def add(self, attempt: HistoryAttempt) -> None:
        self.attempts = sorted([*self.attempts, attempt], key=lambda value: value.key())
        self._order[attempt.attempt_id] = attempt.key()

    def replace_attempt(self, attempt: HistoryAttempt) -> None:
        self.attempts = [
            attempt if existing.attempt_id == attempt.attempt_id else existing
            for existing in self.attempts
        ]

    def attempt(self, attempt_id: str) -> HistoryAttempt | None:
        return next((value for value in self.attempts if value.attempt_id == attempt_id), None)

    def ref(self, attempt_id: str) -> AttemptRef | None:
        order = self._order.get(attempt_id)
        return AttemptRef(attempt_id, order[0]) if order else None

    def all_attempts(self) -> list[HistoryAttempt]:
        return list(self.attempts)

    def attempts_before(
        self, before: AttemptRef, learning_object_ids: Sequence[str] | None = None
    ) -> list[HistoryAttempt]:
        wanted = set(learning_object_ids) if learning_object_ids is not None else None
        return [
            attempt
            for attempt in self.attempts
            if attempt.key() < before.key()
            and (wanted is None or attempt.learning_object_id in wanted)
        ]

    def _before(self, source: str | None, before: AttemptRef) -> bool:
        order = self._order.get(source or "")
        return order is not None and order < before.key()

    def hypotheses_before(
        self, before: AttemptRef, learning_object_ids: Sequence[str]
    ) -> list[HypothesisRecord]:
        wanted = set(learning_object_ids)
        return [
            record
            for record in self.hypotheses
            if record.learning_object_id in wanted and self._before(record.source_attempt_id, before)
        ]

    def registry_before(
        self, before: AttemptRef, learning_object_ids: Sequence[str] | None
    ) -> list[RegistryRecord]:
        wanted = set(learning_object_ids) if learning_object_ids is not None else None
        return [
            record
            for record in self.registry
            if (wanted is None or record.learning_object_id in wanted)
            and self._before(record.source_attempt_id, before)
        ]

    def repairs_before(
        self, before: AttemptRef, facets: Iterable[str] | None
    ) -> list[RepairRecord]:
        wanted = set(facets) if facets is not None else None
        return [
            record
            for record in self.repairs
            if self._before(record.source_attempt_id, before)
            and (wanted is None or not record.target_facets or wanted & set(record.target_facets))
        ]

    def lagged_attempts(self, before: AttemptRef) -> int:
        return sum(1 for attempt in self.attempts if attempt.key() > before.key())


def with_blind_overlay(attempt: HistoryAttempt, **changes: Any) -> HistoryAttempt:
    return replace(attempt, **changes)


__all__ = [
    "ASSISTED_ATTEMPT_TYPES",
    "AttemptRef",
    "HistoryAttempt",
    "HistoryStore",
    "HypothesisRecord",
    "Neighborhood",
    "NON_MEASURING_ATTEMPT_TYPES",
    "RegistryRecord",
    "RepairRecord",
    "StaticHistoryStore",
    "VaultHistoryStore",
    "history_attempt_from_blind_record",
    "learning_object_neighborhood",
]
