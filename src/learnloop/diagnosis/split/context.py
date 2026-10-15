"""Deterministic ``DiagnosisContext`` assembly (Slice 1 §5.2).

The same inputs always produce the same context bytes and hash. Four history
modes select the past differently but share the as-of cutoff, the typed
records of :mod:`.history` and the closed-world id set the validators check:

* ``exact``: at most ``history_error_limit`` failures and
  ``history_success_limit`` successes chosen by the exact filters (same LO or
  one-hop neighbour, facet overlap, any surface family), most recent first,
  under a fixed token budget;
* ``full``: every prior attempt on the LO and its one-hop neighbours, failures
  and successes, chronological with timestamps, failed attempts with their
  answer text, under ``full_history_token_budget`` (oldest attempts drop
  first; hypotheses never drop before attempts);
* ``snapshot``: the ``exact`` context inline plus a read-only export (§5.6);
* ``hybrid``: ``exact`` failures fused with kNN over the same filtered
  population by reciprocal rank (§9.4).

From S1.4a (``embedding.enabled``), every mode's registry block also takes a
kNN shortlist over the WHOLE vault registry as of the cutoff (§5.2, §9.4),
next to the exact neighbourhood set, with its provenance in the receipt; a
failing or incomplete index falls back to the exact set. The shortlist only
offers candidates: the diagnoser still decides identity (``registry_match``).

Layout for caching: the stable blocks come first in a fixed order, the
chronological history last among them, and the current attempt at the very
end. Two consecutive diagnoses on one LO therefore share a byte-identical
prefix through the older attempt's history.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Protocol, Sequence

from learnloop.attempts.grading import resolved_rubric
from learnloop.diagnosis.split.history import (
    AttemptRef,
    HistoryAttempt,
    HistoryStore,
    HypothesisRecord,
    Neighborhood,
    RegistryRecord,
    RepairRecord,
    learning_object_neighborhood,
)
from learnloop.diagnosis.split.settings import (
    DIAGNOSIS_CONTEXT_VERSION,
    DiagnosisSettings,
    HistoryMode,
)
from learnloop.substrate.canonical_projection import surface_group_id
from learnloop.vault.models import LoadedVault, PracticeItem, learning_object_facet_union
from learnloop.vault.required_method import answered_prompt

#: Rendering order (cache layout, §5.2): the stable part - neighbourhood,
#: registry and the history, chronological in ``full`` - first; then the blocks
#: that change whenever a diagnosis mints something (typed hypotheses, repair
#: outcomes, disclosures); the current attempt last. A later diagnosis on the
#: same LO therefore extends the history in place and shares the whole prefix
#: before its newest row.
CACHEABLE_BLOCKS: tuple[str, ...] = (
    "neighborhood",
    "registry_candidates",
    "success_history",
    "failure_history",
    "history",
)
STABLE_BLOCKS: tuple[str, ...] = (
    *CACHEABLE_BLOCKS,
    "prior_hypotheses",
    "repair_history",
    "disclosures",
)
CURRENT_BLOCK = "current_attempt"


def estimate_tokens(text: str) -> int:
    """Conservative token estimate: UTF-8 bytes / 4, rounded up."""

    return math.ceil(len(text.encode("utf-8")) / 4)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


@dataclass(frozen=True)
class CurrentAttempt:
    """The attempt being diagnosed, with its blind grade (§5.2 "current")."""

    attempt_id: str
    learning_object_id: str
    practice_item_id: str
    completed_at: str
    surface_group: str
    item_prompt: str
    reference_solution: str
    rubric: tuple[dict[str, Any], ...]
    trace_contract: dict[str, Any] | None
    learner_answer_md: str
    blind_grade: Mapping[str, Any]
    item_facets: tuple[str, ...] = ()

    def ref(self) -> AttemptRef:
        return AttemptRef(self.attempt_id, self.completed_at)

    def target_facets(self) -> frozenset[str]:
        """The blind grade's facet targets, else the item's own facets."""

        targets: set[str] = set()
        for row in self.blind_grade.get("error_attributions") or []:
            targets.update(str(value) for value in row.get("target_evidence_families") or [])
            ref = row.get("target_ref")
            if isinstance(ref, Mapping) and ref.get("kind") == "facet_capability" and ref.get("facet_id"):
                targets.add(str(ref["facet_id"]))
        return frozenset(targets or self.item_facets)

    def render(self) -> dict[str, Any]:
        grade = self.blind_grade
        rendered = self._render(grade)
        reading = grade.get("stuck_reading")
        if isinstance(reading, Mapping):
            # mvp-0.13: the answer came from "I'm stuck" ("Write what you can,
            # or what's confusing you"); the blind grader's reading of it is
            # part of THIS attempt's evidence. Absent for every other attempt,
            # so their contexts render and hash exactly as before.
            rendered["blind_grade"]["stuck_reading"] = {
                "answer_prompt": "I'm stuck: Write what you can, or what's confusing you",
                "attempts_answer": bool(reading.get("attempts_answer")),
                "describes_confusion": bool(reading.get("describes_confusion")),
                "confusion_quote": str(reading.get("confusion_quote") or ""),
            }
        return rendered

    def _render(self, grade: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "date": self.completed_at,
            "learning_object_id": self.learning_object_id,
            "practice_item_id": self.practice_item_id,
            "surface_group": self.surface_group,
            "item_prompt": self.item_prompt,
            "reference_solution": self.reference_solution,
            "rubric": list(self.rubric),
            "trace_contract": self.trace_contract,
            "item_facets": list(self.item_facets),
            "learner_answer_md": self.learner_answer_md,
            "blind_grade": {
                "score": grade.get("rubric_score"),
                "max_points": grade.get("max_points"),
                "criteria": [
                    {
                        "criterion_id": row.get("criterion_id"),
                        "points_awarded": row.get("points_awarded"),
                        "evidence": row.get("evidence"),
                    }
                    for row in grade.get("criteria") or []
                ],
                "fatal_errors": list(grade.get("fatal_errors") or []),
                "local_analysis_md": grade.get("local_analysis_md"),
                "error_attributions": [
                    {
                        "index": row.get("index", position),
                        "error_type": row.get("error_type"),
                        "severity": row.get("severity"),
                        "evidence": row.get("evidence"),
                        "first_divergence": row.get("first_divergence"),
                        "target_evidence_families": list(row.get("target_evidence_families") or []),
                        "target_criterion_ids": list(row.get("target_criterion_ids") or []),
                        "target_ref": row.get("target_ref"),
                        "resolution_status": row.get("resolution_status"),
                        "validity_scope": row.get("validity_scope"),
                        "repaired_trace_id": row.get("repaired_trace_id"),
                    }
                    for position, row in enumerate(grade.get("error_attributions") or [])
                ],
                "repaired_traces": [
                    {
                        "id": trace.get("id"),
                        "minimal_edit": trace.get("minimal_edit"),
                        "repaired_answer_md": trace.get("repaired_answer_md"),
                    }
                    for trace in grade.get("repaired_traces") or []
                ],
            },
        }


def current_attempt_from(
    vault: LoadedVault,
    item: PracticeItem,
    *,
    attempt_id: str,
    completed_at: str,
    learner_answer_md: str,
    blind_grade: Mapping[str, Any],
    contract: Mapping[str, Any] | None = None,
) -> CurrentAttempt:
    """The attempt being diagnosed. ``contract`` (method-explicit-3 review
    F3) is the assessment contract its answer was graded under: a
    method-explicit answer is explained against the question it was given
    (``answered_prompt``), never today's item."""

    rubric = resolved_rubric(vault, item)
    expected = item.expected_answer
    return CurrentAttempt(
        attempt_id=attempt_id,
        learning_object_id=item.learning_object_id,
        practice_item_id=item.id,
        completed_at=completed_at,
        surface_group=surface_group_id(item),
        item_prompt=answered_prompt(item, contract) or "",
        reference_solution=expected if isinstance(expected, str) else canonical_json(expected),
        rubric=tuple(
            {
                "id": criterion.id,
                "points": criterion.points,
                "description": criterion.description,
                "facets": sorted(
                    {vault.canonical_facet_id(str(target.facet)) for target in criterion.targets}
                ),
            }
            for criterion in rubric.criteria
        ),
        trace_contract=(
            item.trace_contract.model_dump(mode="json", exclude_none=True)
            if item.trace_contract is not None
            else None
        ),
        learner_answer_md=learner_answer_md,
        blind_grade=dict(blind_grade),
        item_facets=tuple(vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets),
    )


@dataclass(frozen=True)
class KnownIds:
    """The closed world the validators check model-cited ids against (§5.4)."""

    attempt_ids: frozenset[str]
    hypothesis_ids: frozenset[str]
    registry_ids: frozenset[str]
    learning_object_ids: frozenset[str]
    facet_ids: frozenset[str]
    repaired_trace_ids: frozenset[str]

    def union(self, other: "KnownIds") -> "KnownIds":
        return KnownIds(
            attempt_ids=self.attempt_ids | other.attempt_ids,
            hypothesis_ids=self.hypothesis_ids | other.hypothesis_ids,
            registry_ids=self.registry_ids | other.registry_ids,
            learning_object_ids=self.learning_object_ids | other.learning_object_ids,
            facet_ids=self.facet_ids | other.facet_ids,
            repaired_trace_ids=self.repaired_trace_ids | other.repaired_trace_ids,
        )


@dataclass(frozen=True)
class RetrievalMatch:
    attempt_id: str
    score: float
    rank: int


@dataclass(frozen=True)
class RetrievalResult:
    method: str  # knn | exact_fallback
    model_id: str | None = None
    matches: tuple[RetrievalMatch, ...] = ()
    error: str | None = None


@dataclass(frozen=True)
class RegistryNeighbor:
    key: str  # ``<kind>:<id>`` (the ``misconception/statement`` record id)
    score: float
    rank: int


@dataclass(frozen=True)
class RegistryShortlist:
    method: str  # knn | exact_fallback
    model_id: str | None = None
    matches: tuple[RegistryNeighbor, ...] = ()
    error: str | None = None


def registry_key(record: RegistryRecord) -> str:
    """A registry record's id in the ``misconception/statement`` index."""

    return f"{record.kind}:{record.id}"


class RegistryRetriever(Protocol):
    """kNN over the whole vault registry (S1.4a shortlist, §5.2)."""

    def registry_knn(
        self,
        current: "CurrentAttempt",
        records: Sequence[RegistryRecord],
        *,
        limit: int,
    ) -> RegistryShortlist:
        ...


class HistoryRetriever(Protocol):
    """kNN over prior failures for the hybrid mode (§9.4)."""

    def knn(
        self,
        current: CurrentAttempt,
        candidates: Sequence[HistoryAttempt],
        *,
        limit: int,
    ) -> RetrievalResult:
        ...


@dataclass(frozen=True)
class AssembledContext:
    """A rendered context plus its audit receipt and closed-world ids."""

    mode: str
    blocks: dict[str, Any]
    current: dict[str, Any]
    known: KnownIds
    receipt: dict[str, Any]
    context_hash: str
    tokens: int
    #: History records the context drew on, for citation validation.
    attempts: dict[str, HistoryAttempt] = field(default_factory=dict)
    #: What the context showed the diagnoser (diagnosis input provenance,
    #: ``provenance.reads_of_context``): recorded with the diagnosis.
    reads: Any = None

    def rendered(self) -> str:
        return render_context(self.blocks, self.current)


def render_context(blocks: Mapping[str, Any], current: Mapping[str, Any]) -> str:
    """Byte-stable rendering: stable blocks in fixed order, current attempt last."""

    parts = [
        f"{json.dumps(key)}: {canonical_json(blocks[key])}"
        for key in STABLE_BLOCKS
        if key in blocks
    ]
    parts.append(f"{json.dumps(CURRENT_BLOCK)}: {canonical_json(current)}")
    return "{" + ", ".join(parts) + "}"


def _status_for(attempts: Sequence[HistoryAttempt]) -> str:
    if any(not attempt.non_pass and attempt.cold_unassisted for attempt in attempts):
        return "demonstrated"
    if attempts:
        return "attempted"
    return "untested"


def _neighborhood_block(
    vault: LoadedVault,
    neighborhood: Neighborhood,
    prior: Sequence[HistoryAttempt],
) -> tuple[dict[str, Any], set[str], list[dict[str, Any]]]:
    by_lo: dict[str, list[HistoryAttempt]] = {}
    for attempt in prior:
        by_lo.setdefault(attempt.learning_object_id, []).append(attempt)
    facets: set[str] = set()
    entries: list[dict[str, Any]] = []
    for learning_object_id in neighborhood.all_ids():
        learning_object = vault.learning_objects.get(learning_object_id)
        lo_facets = (
            [vault.canonical_facet_id(str(value)) for value in learning_object_facet_union(learning_object)]
            if learning_object is not None
            else []
        )
        facets.update(lo_facets)
        entries.append(
            {
                "learning_object_id": learning_object_id,
                "title": learning_object.title if learning_object is not None else learning_object_id,
                "relation": neighborhood.relation(learning_object_id),
                "facets": lo_facets,
                "as_of_status": _status_for(by_lo.get(learning_object_id, [])),
            }
        )
    prerequisites = [entry for entry in entries if entry["relation"] == "prerequisite"]
    block = {
        "learning_object_id": neighborhood.learning_object_id,
        "status_vocabulary": {
            "demonstrated": "a prior cold, unassisted full-credit attempt exists before this attempt",
            "attempted": "attempted before this attempt, never demonstrated cold",
            "untested": "no attempt before this attempt",
        },
        "learning_objects": entries,
    }
    return block, facets, prerequisites


def _render_attempt(
    attempt: HistoryAttempt,
    neighborhood: Neighborhood,
    *,
    with_answer: bool,
) -> dict[str, Any]:
    score = (
        f"{attempt.score:g}/{attempt.max_points:g}"
        if attempt.score is not None and attempt.max_points
        else None
    )
    row: dict[str, Any] = {
        "attempt_id": attempt.attempt_id,
        "date": attempt.completed_at,
        "learning_object_id": attempt.learning_object_id,
        "relation": neighborhood.relation(attempt.learning_object_id),
        "practice_item_id": attempt.practice_item_id,
        "surface_group": attempt.surface_group,
        "outcome": "non_pass" if attempt.non_pass else "pass",
        "score": score,
        "failed_criteria": list(attempt.failed_criteria),
        "fatal_errors": list(attempt.fatal_errors),
        "first_divergence_quotes": list(attempt.first_divergence_quotes),
        "error_types": list(attempt.error_types),
        "target_facets": list(attempt.target_facets),
        "item_facets": list(attempt.item_facets),
        "validity_scopes": list(attempt.validity_scopes),
        "assisted": attempt.assisted,
        "primed": attempt.primed,
        "grader_mode": attempt.grader_mode,
    }
    if with_answer:
        row["item_prompt"] = attempt.item_prompt
        row["learner_answer_md"] = attempt.learner_answer_md
    return row


def _render_hypothesis(record: HypothesisRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "kind": record.kind,
        "statement": record.statement,
        "scope": record.scope,
        "status": record.lifecycle,
        "validated_evidence_count": record.validated_evidence_count,
        "last_updated": record.last_updated,
        "learning_object_id": record.learning_object_id,
        "target_facets": list(record.target_facets),
    }


def _render_registry(record: RegistryRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "kind": record.kind,
        "statement": record.statement,
        "status": record.status,
        "learning_object_id": record.learning_object_id,
        "facet_ids": list(record.facet_ids),
        "occurrence_count": record.occurrence_count,
    }


def _render_repair(record: RepairRecord) -> dict[str, Any]:
    return {
        "repair_class_id": record.repair_class_id,
        "operator": record.operator,
        "target_facets": list(record.target_facets),
        "hypothesis_ids": list(record.hypothesis_ids),
        "cold_verifications": {"succeeded": record.cold_successes, "failed": record.cold_failures},
    }


def _exact_failures(
    prior: Sequence[HistoryAttempt],
    targets: frozenset[str],
    *,
    current_attempt_id: str,
) -> list[HistoryAttempt]:
    """Non-pass, facet-overlapping, any surface family; most recent first."""

    return [
        attempt
        for attempt in reversed(prior)
        if attempt.attempt_id != current_attempt_id
        and attempt.non_pass
        and (not targets or attempt.facets() & targets)
    ]


def _exact_successes(
    prior: Sequence[HistoryAttempt],
    targets: frozenset[str],
    *,
    current_attempt_id: str,
) -> list[HistoryAttempt]:
    """Prior passes on the same facets, cold and unassisted first, recent first."""

    passes = [
        attempt
        for attempt in reversed(prior)
        if attempt.attempt_id != current_attempt_id
        and not attempt.non_pass
        and (not targets or attempt.facets() & targets)
    ]
    return sorted(passes, key=lambda attempt: not attempt.cold_unassisted)


def _rrf(
    exact: Sequence[HistoryAttempt],
    knn: RetrievalResult,
    *,
    k: int,
    keep: int,
    by_id: Mapping[str, HistoryAttempt],
) -> tuple[list[HistoryAttempt], list[dict[str, Any]]]:
    scores: dict[str, float] = {}
    provenance: dict[str, dict[str, Any]] = {}
    for rank, attempt in enumerate(exact, start=1):
        scores[attempt.attempt_id] = scores.get(attempt.attempt_id, 0.0) + 1.0 / (k + rank)
        provenance.setdefault(attempt.attempt_id, {})["exact_rank"] = rank
    for match in knn.matches:
        if match.attempt_id not in by_id:
            continue
        scores[match.attempt_id] = scores.get(match.attempt_id, 0.0) + 1.0 / (k + match.rank)
        provenance.setdefault(match.attempt_id, {}).update(knn_rank=match.rank, knn_score=round(match.score, 6))
    ordered = sorted(scores, key=lambda value: (-scores[value], value))[:keep]
    rows = []
    for attempt_id in sorted(scores, key=lambda value: (-scores[value], value)):
        info = provenance[attempt_id]
        source = "both" if "exact_rank" in info and "knn_rank" in info else ("exact" if "exact_rank" in info else "knn")
        rows.append(
            {
                "attempt_id": attempt_id,
                "fused_score": round(scores[attempt_id], 8),
                "source": source,
                "kept": attempt_id in ordered,
                **info,
            }
        )
    return [by_id[value] for value in ordered], rows


def _truncate_oldest(
    attempts: list[HistoryAttempt], drop: int
) -> tuple[list[HistoryAttempt], int]:
    """Drop ``drop`` of the OLDEST attempts, keeping the block's display order."""

    if drop <= 0 or not attempts:
        return attempts, 0
    drop = min(drop, len(attempts))
    oldest = sorted(attempts, key=lambda attempt: attempt.key())[:drop]
    doomed = {attempt.attempt_id for attempt in oldest}
    kept = [attempt for attempt in attempts if attempt.attempt_id not in doomed]
    return kept, drop


def _registry_shortlist(
    retriever: RegistryRetriever,
    store: HistoryStore,
    current: "CurrentAttempt",
    before: AttemptRef,
    exact: list[RegistryRecord],
    *,
    limit: int,
) -> tuple[list[RegistryRecord], dict[str, Any]]:
    """The exact set plus up to ``limit`` kNN-only registry records.

    The universe is every registry record visible as of the cutoff, vault
    wide (the as-of view of :meth:`HistoryStore.registry_before`); ranking
    covers it all, and the records the exact filter already offers are kept
    in place. Provenance per match goes to the receipt.
    """

    universe = sorted(store.registry_before(before, None), key=lambda record: (record.kind, record.id))
    exact_keys = {registry_key(record) for record in exact}
    by_key = {registry_key(record): record for record in universe}
    if universe:
        shortlist = retriever.registry_knn(current, universe, limit=limit + len(exact_keys))
    else:
        shortlist = RegistryShortlist(method="knn", model_id=getattr(retriever, "model_id", None))
    added: list[RegistryRecord] = []
    rows: list[dict[str, Any]] = []
    for match in shortlist.matches:
        record = by_key.get(match.key)
        if record is None:
            continue
        in_exact = match.key in exact_keys
        keep = not in_exact and len(added) < limit
        if keep:
            added.append(record)
        rows.append(
            {
                "registry_id": record.id,
                "kind": record.kind,
                "rank": match.rank,
                "score": round(match.score, 6),
                "source": "both" if in_exact else "knn",
                "added": keep,
            }
        )
    receipt = {
        "method": shortlist.method,
        "model_id": shortlist.model_id,
        "error": shortlist.error,
        "universe": len(universe),
        "exact_registry_ids": sorted(exact_keys),
        "matches": rows,
        "knn_only_registry_ids": [registry_key(record) for record in added],
    }
    return [*exact, *added], receipt


def assemble_diagnosis_context(
    vault: LoadedVault,
    store: HistoryStore,
    current: CurrentAttempt,
    settings: DiagnosisSettings,
    *,
    mode: HistoryMode | None = None,
    retriever: HistoryRetriever | None = None,
    snapshot_manifest: Mapping[str, Any] | None = None,
    token_budget: int | None = None,
    registry_retriever: RegistryRetriever | None = None,
) -> AssembledContext:
    """Assemble one context deterministically. ``mode`` overrides the setting.

    ``registry_retriever`` (S1.4a) adds the whole-vault registry shortlist;
    without one the registry block is exactly the neighbourhood set.
    """

    mode = mode or settings.history_mode
    before = current.ref()
    neighborhood = learning_object_neighborhood(vault, current.learning_object_id)
    lo_ids = neighborhood.all_ids()
    prior = store.attempts_before(before, lo_ids)
    by_id = {attempt.attempt_id: attempt for attempt in prior}
    targets = current.target_facets()
    neighborhood_block, neighborhood_facets, prerequisites = _neighborhood_block(vault, neighborhood, prior)
    hypotheses = sorted(
        store.hypotheses_before(before, lo_ids),
        key=lambda record: (record.last_updated or "", record.id),
    )
    registry_scope: Sequence[str] | None
    if mode in ("full", "snapshot"):
        registry_scope = lo_ids
    else:
        registry_scope = (current.learning_object_id, *neighborhood.same_concept_ids, *neighborhood.confusable_ids)
    registry = sorted(
        store.registry_before(before, registry_scope),
        key=lambda record: (record.kind, record.id),
    )
    registry_receipt: dict[str, Any] | None = None
    if registry_retriever is not None:
        registry, registry_receipt = _registry_shortlist(
            registry_retriever, store, current, before, registry, limit=settings.knn_limit
        )
    repair_facets = set(targets) | set(current.item_facets)
    repairs = store.repairs_before(before, repair_facets)

    disclosures: dict[str, Any] = {"history_mode": mode}
    receipt: dict[str, Any] = {
        "context_version": DIAGNOSIS_CONTEXT_VERSION,
        "history_mode": mode,
        "context_as_of_attempt_id": current.attempt_id,
        "lagged_attempts": store.lagged_attempts(before),
        "neighborhood_learning_object_ids": list(lo_ids),
        "prerequisite_refs": [entry["learning_object_id"] for entry in prerequisites],
        "method": mode,
    }
    if registry_receipt is not None:
        receipt["registry_retrieval"] = registry_receipt

    blocks: dict[str, Any] = {"neighborhood": neighborhood_block}
    failure_rows: list[HistoryAttempt] = []
    success_rows: list[HistoryAttempt] = []
    history_rows: list[HistoryAttempt] = []
    if mode == "full":
        history_rows = list(prior)
        budget = token_budget if token_budget is not None else settings.full_history_token_budget
        disclosures["token_budget"] = budget
    else:
        budget = token_budget if token_budget is not None else settings.exact_history_token_budget
        disclosures["token_budget"] = budget
        exact_failures = _exact_failures(prior, targets, current_attempt_id=current.attempt_id)
        exact_successes = _exact_successes(prior, targets, current_attempt_id=current.attempt_id)
        limit = settings.history_error_limit
        failure_rows = exact_failures[:limit]
        success_rows = exact_successes[: settings.history_success_limit]
        disclosures["failures_not_selected"] = max(0, len(exact_failures) - len(failure_rows))
        disclosures["successes_not_selected"] = max(0, len(exact_successes) - len(success_rows))
        if mode == "hybrid":
            population = [
                attempt for attempt in exact_failures if attempt.valid_measurement
            ]
            if retriever is None:
                result = RetrievalResult(method="exact_fallback", error="no_retriever")
            elif not population or not limit:
                # Nothing to rank: kNN ran, and had no candidate to add.
                result = RetrievalResult(method="knn", model_id=getattr(retriever, "model_id", None))
            else:
                result = retriever.knn(current, population, limit=settings.knn_limit)
            receipt["method"] = "hybrid" if result.method == "knn" else "exact_fallback"
            receipt["embedding_model_id"] = result.model_id
            if result.error:
                receipt["retrieval_error"] = result.error
            if result.method == "knn":
                fused, provenance = _rrf(
                    failure_rows,
                    result,
                    k=settings.rrf_k,
                    keep=max(limit, 0),
                    by_id={attempt.attempt_id: attempt for attempt in population + failure_rows},
                )
                receipt["retrieval"] = provenance
                receipt["knn_only_attempt_ids"] = sorted(
                    row["attempt_id"] for row in provenance if row["source"] == "knn" and row["kept"]
                )
                failure_rows = fused
            else:
                receipt["retrieval"] = [
                    {"attempt_id": attempt.attempt_id, "source": "exact", "exact_rank": rank, "kept": True}
                    for rank, attempt in enumerate(failure_rows, start=1)
                ]
                receipt["knn_only_attempt_ids"] = []
        if mode == "snapshot":
            disclosures["snapshot"] = dict(snapshot_manifest or {"available": False})

    hypothesis_rows = list(hypotheses)
    registry_rows = list(registry)

    def build() -> tuple[dict[str, Any], str]:
        built = dict(blocks)
        built["registry_candidates"] = [_render_registry(record) for record in registry_rows]
        built["prior_hypotheses"] = [_render_hypothesis(record) for record in hypothesis_rows]
        built["repair_history"] = [_render_repair(record) for record in repairs]
        if mode == "full":
            built["history"] = [
                _render_attempt(attempt, neighborhood, with_answer=attempt.non_pass)
                for attempt in history_rows
            ]
        else:
            built["success_history"] = [
                _render_attempt(attempt, neighborhood, with_answer=False) for attempt in success_rows
            ]
            built["failure_history"] = [
                _render_attempt(attempt, neighborhood, with_answer=False) for attempt in failure_rows
            ]
        built["disclosures"] = dict(disclosures)
        return built, render_context(built, current.render())

    built, text = build()
    dropped = {"attempts": 0, "hypotheses": 0, "registry": 0}
    # Truncation (§5.2): oldest attempts first; hypotheses only once no
    # attempt is left; the registry last. Each pass re-renders, because the
    # disclosure itself is part of the context.
    while estimate_tokens(text) > budget:
        overflow = estimate_tokens(text) - budget
        if mode == "full" and history_rows:
            per = max(1, estimate_tokens(canonical_json(_render_attempt(history_rows[0], neighborhood, with_answer=True))))
            history_rows, removed = _truncate_oldest(history_rows, max(1, overflow // per))
            dropped["attempts"] += removed
        elif mode != "full" and (failure_rows or success_rows):
            # Oldest first WITHIN each block: trim the larger block first.
            if len(failure_rows) >= len(success_rows) and failure_rows:
                failure_rows, removed = _truncate_oldest(failure_rows, 1)
            else:
                success_rows, removed = _truncate_oldest(success_rows, 1)
            dropped["attempts"] += removed
        elif hypothesis_rows:
            hypothesis_rows = hypothesis_rows[1:]
            dropped["hypotheses"] += 1
        elif registry_rows:
            registry_rows = registry_rows[1:]
            dropped["registry"] += 1
        else:
            break
        disclosures["dropped"] = dict(dropped)
        disclosures["truncated"] = True
        built, text = build()

    shown_attempts = history_rows if mode == "full" else [*failure_rows, *success_rows]
    attempts_map = {attempt.attempt_id: attempt for attempt in shown_attempts}
    facet_ids = set(neighborhood_facets) | set(current.item_facets) | set(targets)
    for attempt in shown_attempts:
        facet_ids.update(attempt.facets())
    for record in hypothesis_rows:
        facet_ids.update(record.target_facets)
    for record in registry_rows:
        facet_ids.update(record.facet_ids)
    for criterion in current.rubric:
        facet_ids.update(str(value) for value in criterion.get("facets") or [])
    known = KnownIds(
        attempt_ids=frozenset({current.attempt_id, *attempts_map}),
        hypothesis_ids=frozenset(record.id for record in hypothesis_rows),
        registry_ids=frozenset(record.id for record in registry_rows),
        learning_object_ids=frozenset(lo_ids),
        facet_ids=frozenset(facet_ids),
        repaired_trace_ids=frozenset(
            str(trace.get("id")) for trace in current.blind_grade.get("repaired_traces") or [] if trace.get("id")
        ),
    )
    context_hash = hashlib.sha256(
        f"{DIAGNOSIS_CONTEXT_VERSION}\n{mode}\n{text}".encode("utf-8")
    ).hexdigest()
    tokens = estimate_tokens(text)
    receipt.update(
        context_hash=context_hash,
        context_tokens=tokens,
        dropped=dict(dropped),
        failure_attempt_ids=[attempt.attempt_id for attempt in failure_rows],
        success_attempt_ids=[attempt.attempt_id for attempt in success_rows],
        history_attempt_ids=[attempt.attempt_id for attempt in history_rows],
        hypothesis_ids=[record.id for record in hypothesis_rows],
        registry_candidate_ids=[record.id for record in registry_rows],
    )
    from learnloop.diagnosis.split.provenance import reads_of_context, shown_titles

    reads = reads_of_context(
        current_attempt_id=current.attempt_id,
        current_item_id=current.practice_item_id,
        current_learning_object_id=current.learning_object_id,
        learning_object_ids=lo_ids,
        attempts=shown_attempts,
        hypotheses=hypothesis_rows,
        registry=registry_rows,
        repairs=repairs,
        # The neighbourhood block names each topic by its title (codex review F2).
        titles=shown_titles(vault, [entry["learning_object_id"] for entry in neighborhood_block["learning_objects"]]),
    )
    return AssembledContext(
        mode=mode,
        blocks={key: built[key] for key in STABLE_BLOCKS if key in built},
        current=current.render(),
        known=known,
        receipt=receipt,
        context_hash=context_hash,
        tokens=tokens,
        attempts=attempts_map,
        reads=reads,
    )


def history_attempt_tokens(attempt: HistoryAttempt, neighborhood: Neighborhood, *, with_answer: bool) -> int:
    """Estimated tokens one attempt adds to a rendered history block."""

    return estimate_tokens(canonical_json(_render_attempt(attempt, neighborhood, with_answer=with_answer)))


def stable_prefix(rendered: str) -> str:
    """Everything before the current attempt."""

    marker = f", {json.dumps(CURRENT_BLOCK)}: "
    index = rendered.rfind(marker)
    return rendered[:index] if index >= 0 else rendered


def cacheable_prefix(blocks: Mapping[str, Any]) -> str:
    """The bytes a later diagnosis on the same LO can share with this one.

    The cacheable blocks rendered exactly as :func:`render_context` renders
    them, with the last block's closing bracket removed, so a history that
    grows by appending rows still starts with this prefix.
    """

    parts = [
        f"{json.dumps(key)}: {canonical_json(blocks[key])}"
        for key in CACHEABLE_BLOCKS
        if key in blocks
    ]
    text = "{" + ", ".join(parts)
    return text[:-1] if text.endswith("]") else text


def facets_overlap(left: Iterable[str], right: Iterable[str]) -> bool:
    return bool(set(left) & set(right))


__all__ = [
    "AssembledContext",
    "CACHEABLE_BLOCKS",
    "CURRENT_BLOCK",
    "CurrentAttempt",
    "HistoryRetriever",
    "KnownIds",
    "RegistryNeighbor",
    "RegistryRetriever",
    "RegistryShortlist",
    "RetrievalMatch",
    "RetrievalResult",
    "STABLE_BLOCKS",
    "assemble_diagnosis_context",
    "cacheable_prefix",
    "canonical_json",
    "current_attempt_from",
    "estimate_tokens",
    "facets_overlap",
    "history_attempt_tokens",
    "registry_key",
    "render_context",
    "stable_prefix",
]
