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
diagnosed attempt, only hypotheses/registry rows whose source attempt
precedes it, and repair classes aggregated from only the owning hypotheses
and cold verifications that precede it. In a vault every such record must
also have been WRITTEN before the diagnosed attempt (its ``created_at``), so
a record about an old attempt but written later never shows; a versioned
causal hypothesis is shown in its latest version written before the cutoff.
The status of mutable rows (factors, misconceptions, candidates) is read as
of now (their status history is not versioned; the receipt discloses
``lagged_attempts``), and their ``last_updated`` never shows a later time.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any, Iterable, Mapping, Protocol, Sequence

from learnloop.attempts.grading import resolved_rubric
from learnloop.clock import parse_utc
from learnloop.db.repositories import Repository
from learnloop.substrate.canonical_projection import (
    UNVERIFIED_CRITERION_BLOCK,
    held_for_review_attempts,
    surface_group_id,
    unverified_evidence_row,
)
from learnloop.vault.models import LoadedVault, PracticeItem
from learnloop.db.stores.answered_contracts import answered_contracts
from learnloop.vault.required_method import answered_prompt

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
    #: Facets the FAILED criteria measure (their authored targets, else the
    #: item's facets). With ``target_facets`` this is what S4 checks.
    failed_criterion_facets: tuple[str, ...] = ()
    assisted: bool = False
    primed: bool = False
    grader_mode: str = "joint"
    #: Divergence-recipe input for hybrid retrieval only; never rendered into
    #: a context (it is grader prose, and only blind grades carry it).
    local_analysis_md: str | None = None
    #: Per error attribution, aligned with ``validity_scopes``: the facets it
    #: bears on (its facet targets plus the facets its target criteria
    #: measure) and its target criteria. S4 keeps every target WITH its own
    #: validity scope instead of unioning targets and scopes separately.
    attribution_facets: tuple[tuple[str, ...], ...] = ()
    attribution_criteria: tuple[tuple[str, ...], ...] = ()
    #: Per failed criterion, aligned with ``failed_criteria``: its facets.
    failed_criterion_facet_sets: tuple[tuple[str, ...], ...] = ()

    def key(self) -> tuple[str, str]:
        return (self.completed_at, self.attempt_id)

    def evidence_units(self) -> list[tuple[frozenset[str], bool]]:
        """Each non-pass observation as (facets it bears on, valid measurement?).

        An attribution is valid only under ``valid_measurement``. A failed
        criterion or fatal error is valid unless a grader-flagged attribution
        (``item_contract``, ``grader_interpretation``, ...) targets that
        criterion or overlaps its facets. An attempt built without the
        per-attribution alignment collapses to one unit that is valid only when
        every attribution is.
        """

        scopes = list(self.validity_scopes)
        if len(self.attribution_facets) != len(scopes):
            facets = frozenset((*self.target_facets, *self.failed_criterion_facets))
            return [(facets, all(scope == "valid_measurement" for scope in scopes))]
        criteria = (
            list(self.attribution_criteria)
            if len(self.attribution_criteria) == len(scopes)
            else [tuple(self.target_criteria)] * len(scopes)
        )
        units: list[tuple[frozenset[str], bool]] = []
        flagged: list[tuple[frozenset[str], frozenset[str]]] = []
        for facets, targeted, scope in zip(self.attribution_facets, criteria, scopes):
            valid = scope == "valid_measurement"
            units.append((frozenset(facets), valid))
            if not valid:
                flagged.append((frozenset(facets), frozenset(targeted)))

        def unflagged(criterion: str | None, facets: frozenset[str]) -> bool:
            return not any(
                (criterion is not None and criterion in targeted) or (facets & flagged_facets)
                for flagged_facets, targeted in flagged
            )

        sets = (
            list(self.failed_criterion_facet_sets)
            if len(self.failed_criterion_facet_sets) == len(self.failed_criteria)
            else [tuple(self.failed_criterion_facets)] * len(self.failed_criteria)
        )
        for criterion, facets in zip(self.failed_criteria, sets):
            unit = frozenset(facets)
            units.append((unit, unflagged(criterion, unit)))
        if self.fatal_errors:
            unit = frozenset(self.item_facets)
            units.append((unit, unflagged(None, unit)))
        return units

    def recurrence_invalid_reason(self, targets: Iterable[str]) -> str | None:
        """S4 on the overlapping target itself; ``None`` when a citation counts.

        The cited attempt needs a non-pass that overlaps ``targets`` AND is a
        valid measurement - the same observation, not a valid slip elsewhere
        next to a flagged failure here. Empty ``targets`` accepts any valid
        non-pass.
        """

        if not self.non_pass:
            return "cited_attempt_passed"
        wanted = frozenset(targets)
        overlapping = [valid for facets, valid in self.evidence_units() if not wanted or facets & wanted]
        if wanted and not overlapping:
            return "no_target_overlap"
        if not any(overlapping):
            return "not_valid_measurement"
        return None

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

    def failure_facets(self) -> frozenset[str]:
        """Where this attempt's blind grade shows a non-pass (S4 overlap)."""

        return frozenset((*self.target_facets, *self.failed_criterion_facets))


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


def _instant(value: Any) -> datetime | None:
    """A stored timestamp as an aware UTC instant; unparseable -> None."""

    if not value:
        return None
    try:
        return parse_utc(str(value))
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class _Written:
    """A history record with the instant it was written (F5, as of a cutoff).

    ``episode``/``version`` identify a causal hypothesis version: as of a
    cutoff only the latest version written before it is shown.
    ``updated_at`` is a mutable row's last update, shown only when it, too,
    precedes the cutoff.
    """

    record: Any
    written: datetime | None
    episode: str | None = None
    version: int = 1
    created_at: str | None = None
    updated_at: str | None = None
    #: A holding-pen candidate a learner's own text named (learner-text gaps):
    #: it has no source attempt, so it is anchored by the time it was written.
    anchored_by_write: bool = False


def _learner_text_candidate_ids(connection: Any, vault: LoadedVault) -> frozenset[str]:
    """Holding-pen candidates a learner's text named (learner-text gaps), while
    the pipeline and its sightings are switched on."""

    section = getattr(vault.config, "learner_text_gaps", None)
    if section is None or not (section.enabled and section.sightings_enabled):
        return frozenset()
    if connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'learner_text_gaps'"
    ).fetchone() is None:
        return frozenset()
    return frozenset(
        str(row[0]) for row in connection.execute(
            "SELECT target_id FROM learner_text_gaps WHERE action = 'belief_candidate' AND target_kind = 'candidate'"
        )
    )


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


def criterion_facets(vault: LoadedVault, item: PracticeItem | None) -> dict[str, tuple[str, ...]]:
    """Each criterion's measured facets: authored targets, else the item's facets."""

    if item is None:
        return {}
    try:
        rubric = resolved_rubric(vault, item)
    except Exception:  # noqa: BLE001
        return {}
    fallback = tuple(vault.canonical_facet_id(str(value)) for value in item.evidence_facets)
    return {
        criterion.id: (
            tuple(vault.canonical_facet_id(str(target.facet)) for target in criterion.targets)
            if criterion.targets
            else fallback
        )
        for criterion in rubric.criteria
    }


def _failed_facets(vault: LoadedVault, item: PracticeItem | None, failed: Sequence[str]) -> tuple[str, ...]:
    mapping = criterion_facets(vault, item)
    fallback = tuple(vault.canonical_facet_id(str(value)) for value in (item.evidence_facets if item else []))
    return tuple(dict.fromkeys(facet for criterion in failed for facet in mapping.get(criterion, fallback)))


def _criterion_facet_sets(vault: LoadedVault, item: PracticeItem | None, criteria: Sequence[str]) -> tuple[tuple[str, ...], ...]:
    """Per criterion (in order), the facets it measures."""

    mapping = criterion_facets(vault, item)
    fallback = tuple(vault.canonical_facet_id(str(value)) for value in (item.evidence_facets if item else []))
    return tuple(tuple(mapping.get(criterion, fallback)) for criterion in criteria)


def _attribution_alignment(
    vault: LoadedVault, item: PracticeItem | None, attributions: Sequence[Mapping[str, Any]]
) -> tuple[tuple[tuple[str, ...], ...], tuple[tuple[str, ...], ...]]:
    """Per attribution: (facets it bears on, criteria it targets)."""

    mapping = criterion_facets(vault, item)
    facets: list[tuple[str, ...]] = []
    criteria: list[tuple[str, ...]] = []
    for row in attributions:
        targeted = tuple(dict.fromkeys(str(value) for value in row.get("target_criterion_ids") or []))
        ref = row.get("target_ref")
        if isinstance(ref, Mapping) and ref.get("kind") == "criterion" and ref.get("criterion_id"):
            targeted = tuple(dict.fromkeys((*targeted, str(ref["criterion_id"]))))
        bearing = list(_target_facets_from(row, vault))
        for criterion in targeted:
            bearing.extend(mapping.get(criterion, ()))
        facets.append(tuple(dict.fromkeys(bearing)))
        criteria.append(targeted)
    return tuple(facets), tuple(criteria)


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
    contract: Mapping[str, Any] | None = None,
) -> HistoryAttempt:
    """Blind-grade-equivalent fields from a validated blind grade record.

    ``contract`` (method-explicit-3 review F3) is the assessment contract the
    answer was graded under: a method-explicit answer's question is the one
    it was given (``answered_prompt``), never today's item."""

    maxima, max_points = _max_points_by_criterion(vault, item)
    # PF-c (review F4): a criterion the valid-alternative gate recorded
    # unverified was never exercised by the learner's route. It is neither a
    # failed nor a passed criterion here, so it is no evidence unit and no
    # recurrence can be cited on it. (A record written before the unassessed
    # rule blocked its negative evidence too, so this holds for both.)
    support = record.get("grading_support") or {}
    unassessed = {str(value) for value in support.get("unverified_criterion_ids") or ()}
    failed: list[str] = []
    passed: list[str] = []
    for row in record.get("criteria") or []:
        criterion_id = str(row.get("criterion_id") or "")
        if criterion_id in unassessed:
            continue
        points = float(row.get("points_awarded") or 0.0)
        maximum = maxima.get(criterion_id)
        if maximum is not None and points + 1e-9 >= maximum:
            passed.append(criterion_id)
        else:
            failed.append(criterion_id)
    attributions = [row for row in record.get("error_attributions") or [] if isinstance(row, Mapping)]
    alignment = _attribution_alignment(vault, item, attributions)
    return HistoryAttempt(
        attempt_id=attempt_id,
        learning_object_id=learning_object_id,
        practice_item_id=practice_item_id,
        completed_at=completed_at,
        surface_group=surface_group_id(item) if item is not None else f"item:{practice_item_id}",
        item_prompt=answered_prompt(item, contract) or "",
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
        failed_criterion_facets=_failed_facets(vault, item, failed),
        assisted=bool(hints_used) or attempt_type in ASSISTED_ATTEMPT_TYPES,
        primed=bool(primed),
        grader_mode="blind",
        local_analysis_md=str(record.get("local_analysis_md") or "") or None,
        attribution_facets=alignment[0],
        attribution_criteria=alignment[1],
        failed_criterion_facet_sets=_criterion_facet_sets(vault, item, failed),
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
        grading_marks: Mapping[str, str] | None = None,
    ) -> None:
        self.vault = vault
        self.repository = repository
        self._blind = dict(blind_grades or {})
        self._loaded = False
        self._attempts: list[HistoryAttempt] = []
        self._by_id: dict[str, HistoryAttempt] = {}
        self._order: dict[str, tuple[str, str]] = {}
        self._error_event_attempt: dict[str, str] = {}
        #: Each attempt's grading identity as this store read it (diagnosis
        #: input provenance, codex re-review F3: ``write_provenance.grading_marks``):
        #: ``grading_marks`` when the caller read them in one snapshot with
        #: the overlay (``live.live_history_store``), else read in one
        #: snapshot with the rows when the store loads. An overlay payload
        #: the caller supplied with no identity (``_unidentified``) matches
        #: no grading as it stands.
        self._captured_marks = dict(grading_marks) if grading_marks is not None else None
        self._unidentified: set[str] = set() if grading_marks is not None else set(self._blind)
        self._grading_marks: dict[str, str] = {}
        #: Every hypothesis record (every causal-hypothesis VERSION) with the
        #: instant it was written; the as-of view is chosen per cutoff.
        self._hypotheses: list[_Written] = []
        self._registry: list[_Written] = []
        self._repair_classes: list[tuple[Any, ...]] = []

    def with_blind_grades(self, blind_grades: Mapping[str, Mapping[str, Any]]) -> "VaultHistoryStore":
        merged = {**self._blind, **dict(blind_grades)}
        store = VaultHistoryStore(self.vault, self.repository, blind_grades=merged,
                                  grading_marks=self._captured_marks)
        # The caller's payloads carry no identity (codex re-review F3).
        store._unidentified = set(merged) if self._captured_marks is None else {*self._unidentified, *blind_grades}
        return store

    def blind_grade(self, attempt_id: str) -> Mapping[str, Any] | None:
        """The overlay's blind record of ``attempt_id`` (read with its
        grading's identity by ``live.live_history_store``), or None."""

        return self._blind.get(str(attempt_id))

    # -- loading ------------------------------------------------------------

    def _load(self) -> None:
        if self._loaded:
            return
        vault = self.vault
        from learnloop.db.stores.write_provenance import (
            UNIDENTIFIED_GRADING,
            grading_marks,
            read_snapshot,
            replaced_error_event_attempts,
        )

        # One snapshot: the rows shown and (unless the caller read them with
        # its overlay) every grading's identity (codex re-review F3).
        with self.repository.connection() as connection, read_snapshot(connection):
            marks = self._captured_marks if self._captured_marks is not None else grading_marks(connection)
            self._grading_marks = {**marks, **{attempt: UNIDENTIFIED_GRADING for attempt in self._unidentified}}
            attempts = [dict(row) for row in connection.execute(
                "SELECT id, practice_item_id, learning_object_id, attempt_type, "
                "learner_answer_md, rubric_score, correctness, hints_used, primed, "
                "created_at FROM practice_attempts ORDER BY created_at, id"
            )]
            evidence: dict[str, dict[str, float]] = {}
            #: Attempts with a PF-c unverified criterion row (review F4): those
            #: rows are neither failures nor passes in the history.
            unassessed_attempts: set[str] = set()
            for row in connection.execute(
                "SELECT attempt_id, criterion_id, points_awarded, attribution_json FROM grading_evidence "
                "WHERE superseded_at IS NULL ORDER BY created_at, criterion_id"
            ):
                if row[3] and UNVERIFIED_CRITERION_BLOCK in str(row[3]) and unverified_evidence_row(row[3]):
                    unassessed_attempts.add(str(row[0]))
                    continue
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
            # Q9: an event a regrade retired (re-minted or not) still names
            # its attempt, so a belief that lists it keeps its source answer.
            for replaced, attempt_id in replaced_error_event_attempts(connection).items():
                self._error_event_attempt.setdefault(replaced, attempt_id)
            fatal: dict[str, list[str]] = {
                str(row[0]): [str(value) for value in _decode_json(row[1], [])]
                for row in connection.execute(
                    "SELECT attempt_id, fatal_errors_json FROM attempt_feedback_metadata"
                )
            }
            # Every version (immutable audit rows): the as-of view picks the
            # latest version written before each cutoff.
            hypotheses = [dict(row) for row in connection.execute(
                "SELECT * FROM causal_hypotheses ORDER BY created_at, id"
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
            learner_text_candidates = _learner_text_candidate_ids(connection, vault)
            # held-grade-evidence: THE held predicate. A held attempt stays in
            # the history (it happened) with no score: its grade is the
            # grader's provisional one, nothing assessed, nothing validated.
            held = held_for_review_attempts(connection)
            # Method-explicit-3 review F3: the question each answer was given
            # (its graded contract), for the method-explicit ones.
            contracts = answered_contracts(connection)
            cold = [dict(row) for row in connection.execute(
                "SELECT source_attempt_id, cold_attempt_id, repair_class_id, success, created_at "
                "FROM causal_cold_verifications ORDER BY created_at, id"
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
                    contract=contracts.get(attempt_id),
                )
            else:
                record = self._from_stored(
                    row, item, evidence.get(attempt_id, {}), events.get(attempt_id, []),
                    fatal.get(attempt_id, []), has_unassessed=attempt_id in unassessed_attempts,
                    contract=contracts.get(attempt_id),
                )
            if attempt_id in held:
                record = replace(record, score=None)
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
                _Written(
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
                    ),
                    _instant(row.get("created_at")),
                    episode=str(row.get("episode_key") or row["id"]),
                    version=int(row.get("version") or 1),
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
                _Written(
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
                    ),
                    _instant(row.get("created_at")),
                    created_at=str(row.get("created_at") or "") or None,
                    updated_at=str(row.get("updated_at") or "") or None,
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
            written = _instant(row.get("created_at"))
            self._hypotheses.append(
                _Written(
                    record, written,
                    created_at=str(row.get("created_at") or "") or None,
                    updated_at=str(row.get("updated_at") or "") or None,
                )
            )
            self._registry.append(
                _Written(
                    RegistryRecord(
                        id=record.id,
                        kind="durable",
                        statement=record.statement,
                        learning_object_id=record.learning_object_id,
                        status=status,
                        facet_ids=record.target_facets,
                        occurrence_count=len(sources),
                        source_attempt_id=record.source_attempt_id,
                    ),
                    written,
                )
            )
        for row in candidates:
            if str(row.get("status") or "candidate") != "candidate":
                continue
            sources = [str(value) for value in _decode_json(row.get("source_error_event_ids_json"), []) or []]
            self._registry.append(
                _Written(
                    anchored_by_write=str(row["id"]) in learner_text_candidates,
                    record=RegistryRecord(
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
                    ),
                    written=_instant(row.get("created_at")),
                )
            )
        # Raw cold observations per class: the as-of view picks the owners
        # (hypotheses as of the cutoff) and the observations written before
        # it in ``repairs_before``, never aggregating across all time.
        observations: dict[str, list[tuple[str, datetime | None, int]]] = {}
        for row in cold:
            observations.setdefault(str(row["repair_class_id"]), []).append(
                (str(row.get("cold_attempt_id") or ""), _instant(row.get("created_at")), int(row["success"] or 0))
            )
        class_ids = sorted({entry.record.repair_class_id for entry in self._hypotheses if entry.record.repair_class_id})
        for repair_class_id in class_ids:
            definition = definitions.get(repair_class_id) or {}
            refs = definition.get("target_refs") or []
            defined_facets = tuple(
                dict.fromkeys(
                    vault.canonical_facet_id(str(ref.get("facet_id")))
                    for ref in refs
                    if isinstance(ref, Mapping) and ref.get("kind") == "facet_capability" and ref.get("facet_id")
                )
            )
            self._repair_classes.append(
                (
                    repair_class_id,
                    str(definition.get("operator") or ""),
                    defined_facets,
                    tuple(observations.get(repair_class_id, [])),
                )
            )
        self._loaded = True

    @staticmethod
    def _written_before(written: datetime | None, before: AttemptRef) -> bool:
        """Whether a record was written strictly before the cutoff attempt.

        An unknown or unparseable time is never "before": as-of history fails
        closed rather than leak a record that may postdate the cutoff.
        """

        cutoff = _instant(before.completed_at)
        return written is not None and cutoff is not None and written < cutoff

    def _visible(self, entry: _Written, before: AttemptRef) -> bool:
        if entry.anchored_by_write and entry.record.source_attempt_id is None:
            return self._written_before(entry.written, before)
        return self._source_before(entry.record.source_attempt_id, before) and self._written_before(entry.written, before)

    def _hypotheses_as_of(self, before: AttemptRef) -> list[HypothesisRecord]:
        """Every hypothesis as it stood at ``before``.

        A record shows only when its source attempt precedes the cutoff AND it
        was written before it; a causal hypothesis shows its latest version
        written before the cutoff; a mutable row's ``last_updated`` falls back
        to its creation time when the last update postdates the cutoff.
        """

        latest: dict[str, tuple[int, _Written]] = {}
        chosen: list[tuple[int, _Written]] = []
        for position, entry in enumerate(self._hypotheses):
            if not self._visible(entry, before):
                continue
            if entry.episode is None:
                chosen.append((position, entry))
                continue
            current = latest.get(entry.episode)
            if current is None or entry.version > current[1].version:
                latest[entry.episode] = (position, entry)
        chosen.extend(latest.values())
        records = []
        for _position, entry in sorted(chosen, key=lambda pair: pair[0]):
            record = entry.record
            if entry.updated_at and not self._written_before(_instant(entry.updated_at), before):
                record = replace(record, last_updated=entry.created_at)
            records.append(record)
        return records

    def _observed_before(self, cold_attempt_id: str, written: datetime | None, before: AttemptRef) -> bool:
        """A cold verification counts as of ``before`` only when it was
        recorded before it AND its cold attempt (when known) precedes it."""

        if not self._written_before(written, before):
            return False
        order = self._order.get(cold_attempt_id)
        return order is None or order < before.key()

    def _repair_as_of(self, entry: tuple[Any, ...], visible_hypotheses: Sequence[HypothesisRecord], before: AttemptRef) -> RepairRecord | None:
        repair_class_id, operator, defined_facets, observations = entry
        visible = [owner for owner in visible_hypotheses if owner.repair_class_id == repair_class_id]
        if not visible:
            return None
        results = [success for cold_attempt_id, written, success in observations if self._observed_before(cold_attempt_id, written, before)]
        facets = defined_facets or tuple(dict.fromkeys(facet for owner in visible for facet in owner.target_facets))
        sources = [owner.source_attempt_id for owner in visible if owner.source_attempt_id]
        return RepairRecord(
            repair_class_id=repair_class_id,
            operator=operator,
            target_facets=facets,
            hypothesis_ids=tuple(owner.id for owner in visible),
            cold_successes=sum(results),
            cold_failures=len(results) - sum(results),
            source_attempt_id=min(sources, key=lambda value: self._order.get(value, ("~", value)), default=None),
        )

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
        *,
        has_unassessed: bool = False,
        contract: Mapping[str, Any] | None = None,
    ) -> HistoryAttempt:
        """A stored joint grade, reduced to blind-grade-equivalent fields (S3).

        ``points`` holds the assessed criteria only; ``has_unassessed`` says
        PF-c unverified rows were left out, so an empty ``points`` is not "no
        criterion rows" (the score-only fallback below).
        """

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
        correctness = row.get("correctness")
        if not points and not has_unassessed and correctness is not None and float(correctness) < 1.0 - 1e-9:
            # No criterion rows (deterministic or legacy grades): the stored
            # score is the only measurement, so the attempt is a non-pass on
            # every criterion rather than silently a pass.
            failed = sorted(maxima) or ["score"]
        plans = [event.get("repair_plan") or {} for event in events]
        alignment = _attribution_alignment(vault, item, plans)
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
            item_prompt=answered_prompt(item, contract) or "",
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
            failed_criterion_facets=_failed_facets(vault, item, failed),
            assisted=bool(row.get("hints_used")) or attempt_type in ASSISTED_ATTEMPT_TYPES,
            primed=bool(row.get("primed")),
            grader_mode="joint",
            attribution_facets=alignment[0],
            attribution_criteria=alignment[1],
            failed_criterion_facet_sets=_criterion_facet_sets(vault, item, sorted(failed)),
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

    def grading_marks(self) -> dict[str, str]:
        """Each attempt's grading identity as this store read it, in one
        snapshot with what it shows (``write_provenance.grading_marks``: the
        payload, the contract and the provenance): a record frozen later
        names every grading replaced since (diagnosis input provenance, codex
        review F3 and re-review F3)."""

        self._load()
        return dict(self._grading_marks)

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
        return [record for record in self._hypotheses_as_of(before) if record.learning_object_id in wanted]

    def registry_before(
        self, before: AttemptRef, learning_object_ids: Sequence[str] | None
    ) -> list[RegistryRecord]:
        self._load()
        wanted = set(learning_object_ids) if learning_object_ids is not None else None
        return [
            entry.record
            for entry in self._registry
            if (wanted is None or entry.record.learning_object_id in wanted)
            and self._visible(entry, before)
        ]

    def repairs_before(
        self, before: AttemptRef, facets: Iterable[str] | None
    ) -> list[RepairRecord]:
        self._load()
        wanted = set(facets) if facets is not None else None
        visible = self._hypotheses_as_of(before)
        records = [record for entry in self._repair_classes if (record := self._repair_as_of(entry, visible, before)) is not None]
        return [
            record
            for record in records
            if wanted is None or not record.target_facets or wanted & set(record.target_facets)
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
    "criterion_facets",
    "history_attempt_from_blind_record",
    "learning_object_neighborhood",
]
