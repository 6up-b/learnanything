"""Deterministic validators for ``DiagnosisProposal`` (Slice 1 §5.4, §5.5).

Every failure is recorded in the ``validation_report``; nothing is silently
dropped. The validated proposal keeps only what passed:

* **closed-world ids** - unknown attempt, hypothesis, registry, LO, facet and
  repaired-trace ids are removed and counted (``unknown_id_count`` is M1's
  per-arm "invented history" metric);
* **evidence ids** - ``evidence_attempt_ids`` must be known; a pattern citation
  missing from them is recorded, not rejected;
* **verbatim quotes** - each citation re-anchors against the cited attempt's
  answer with the grader's first-divergence anchoring; a failure drops it;
* **citation validity (S4)** - a citation counts toward recurrence only when
  the cited attempt's BLIND grade shows a non-pass overlapping the hypothesis'
  targets and is a valid measurement; validated citations are grouped by
  surface group for independence;
* **passed-facet firewall** - diagnoser targets protected by the current blind
  grade's clean passes are stripped, exactly as for grader targets;
* **scope firewall** - a causal class on an event whose blind validity scope
  is not ``valid_measurement`` is rejected;
* **repairs** - ``validate_repair_candidate`` plus a repaired-trace id check;
* **registry match** - the id must be one of the provided candidates; ``new``
  needs a statement; ``abstain`` is always allowed.

``anchoring_suspect`` (§5.5) is set when the primary cause is not supported by
the blind grader's history-free reading, the diagnoser did not say the cause
changed, and it reused a prior hypothesis.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from learnloop.attempts.grading import enforce_passed_target_firewall, resolve_quote_anchor
from learnloop.diagnosis.causal_attribution import validate_repair_candidate
from learnloop.diagnosis.split.context import AssembledContext, CurrentAttempt, KnownIds
from learnloop.diagnosis.split.contract import CAUSE_REF_PREFIX, DiagnosisProposal
from learnloop.diagnosis.split.history import HistoryAttempt, HistoryStore
from learnloop.vault.models import LoadedVault, PracticeItem, Rubric

_WORD = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    """
    the a an and or of to in on for with that this these those is are was were be been
    being it its as at by from not no but than then so into out up down over under
    learner learners answer answers student their they them which what when where who
    does did done do has have had will would should could may might can uses used use
    """.split()
)
#: §5.5 heuristic: the primary cause counts as supported by the blind local
#: reading when at least this share of its content words appear there.
LOCAL_SUPPORT_THRESHOLD = 0.2


@dataclass(frozen=True)
class _FacetProbe:
    """A stand-in attribution, so the grader's firewall rule decides protection."""

    target_evidence_families: list[str]
    target_criterion_ids: list[str] = field(default_factory=list)
    target_ref: Any = None
    facet_contrast: Any = None
    resolution_status: str | None = None


def protected_targets(
    item: PracticeItem,
    rubric: Rubric,
    vault: LoadedVault,
    *,
    criterion_points: Mapping[str, float],
    facets: Iterable[str],
    criteria: Iterable[str],
) -> tuple[frozenset[str], frozenset[str]]:
    """(protected facets, passed criteria) by the passed-target firewall."""

    facet_list = sorted(set(facets))
    criterion_list = sorted(set(criteria))
    filtered, _repairs, _audit = enforce_passed_target_firewall(
        item,
        rubric,
        criterion_points=criterion_points,
        error_attributions=[_FacetProbe(facet_list, criterion_list)],
        vault=vault,
    )
    kept = filtered[0]
    return (
        frozenset(facet_list) - set(kept.target_evidence_families),
        frozenset(criterion_list) - set(kept.target_criterion_ids),
    )


def _content_words(text: str) -> set[str]:
    return {
        word
        for word in _WORD.findall((text or "").casefold())
        if len(word) >= 4 and word not in _STOPWORDS
    }


def local_support(statement: str, local_texts: Sequence[str]) -> float:
    """Share of the cause's content words present in the blind local reading."""

    words = _content_words(statement)
    if not words:
        return 0.0
    local = set().union(*(_content_words(text) for text in local_texts)) if local_texts else set()
    return round(len(words & local) / len(words), 6)


@dataclass(frozen=True)
class ValidatedCitation:
    claim_index: int
    attempt_id: str
    quote: str
    surface_group: str
    anchor_basis: str
    char_start: int | None
    char_end: int | None


@dataclass(frozen=True)
class ValidatedDiagnosis:
    status: str  # completed | validation_rejected
    proposal: dict[str, Any]
    report: dict[str, Any]
    anchoring_suspect: bool
    validated_citations: tuple[ValidatedCitation, ...]

    @property
    def unknown_id_count(self) -> int:
        return int(self.report.get("unknown_id_count") or 0)

    def cited_attempt_ids(self) -> list[str]:
        ids: dict[str, None] = {}
        for claim in self.proposal.get("pattern_claims") or []:
            for citation in claim.get("cited") or []:
                ids.setdefault(str(citation.get("attempt_id")), None)
        for gap in self.proposal.get("prerequisite_gap_hypotheses") or []:
            for value in gap.get("cited_attempt_ids") or []:
                ids.setdefault(str(value), None)
        for value in self.proposal.get("evidence_attempt_ids") or []:
            ids.setdefault(str(value), None)
        return list(ids)

    def citations_as_dicts(self) -> list[dict[str, Any]]:
        return [
            {
                "claim_index": citation.claim_index,
                "attempt_id": citation.attempt_id,
                "quote": citation.quote,
                "surface_group": citation.surface_group,
                "anchor_basis": citation.anchor_basis,
                "char_start": citation.char_start,
                "char_end": citation.char_end,
            }
            for citation in self.validated_citations
        ]


class _Report:
    def __init__(self) -> None:
        self.unknown: dict[str, list[str]] = {
            "attempts": [],
            "hypotheses": [],
            "registry": [],
            "learning_objects": [],
            "facets": [],
            "repaired_traces": [],
            "event_indexes": [],
        }
        self.issues: list[dict[str, Any]] = []

    def unknown_id(self, kind: str, value: Any, where: str) -> None:
        self.unknown[kind].append(str(value))
        self.issues.append({"rule": "closed_world", "kind": kind, "id": str(value), "where": where})

    def issue(self, rule: str, **detail: Any) -> None:
        self.issues.append({"rule": rule, **detail})

    def as_dict(self) -> dict[str, Any]:
        return {
            "unknown_id_count": sum(len(values) for values in self.unknown.values()),
            "unknown_ids": {key: sorted(set(values)) for key, values in self.unknown.items() if values},
            "issues": list(self.issues),
        }


def _facet_of(ref: Any) -> str | None:
    if isinstance(ref, Mapping) and ref.get("kind") == "facet_capability" and ref.get("facet_id"):
        return str(ref["facet_id"])
    return None


def _criterion_of(ref: Any) -> str | None:
    if isinstance(ref, Mapping) and ref.get("kind") == "criterion" and ref.get("criterion_id"):
        return str(ref["criterion_id"])
    return None


def validate_diagnosis_proposal(
    proposal: DiagnosisProposal,
    *,
    assembled: AssembledContext,
    current: CurrentAttempt,
    vault: LoadedVault,
    item: PracticeItem,
    rubric: Rubric,
    store: HistoryStore,
    snapshot_known: KnownIds | None = None,
) -> ValidatedDiagnosis:
    """Apply every §5.4 rule; return the surviving proposal and the report."""

    report = _Report()
    known = assembled.known.union(snapshot_known) if snapshot_known is not None else assembled.known
    payload = proposal.model_dump(mode="json")
    grade = current.blind_grade
    attributions = list(grade.get("error_attributions") or [])
    criterion_points = {
        str(row.get("criterion_id")): float(row.get("points_awarded") or 0.0)
        for row in grade.get("criteria") or []
    }

    def known_attempt(attempt_id: str) -> bool:
        return attempt_id in known.attempt_ids

    def known_facet(facet_id: str) -> bool:
        return vault.canonical_facet_id(facet_id) in known.facet_ids

    # -- evidence ids ---------------------------------------------------------
    evidence: list[str] = []
    for attempt_id in payload.get("evidence_attempt_ids") or []:
        if attempt_id == current.attempt_id:
            evidence.append(attempt_id)
        elif known_attempt(attempt_id):
            evidence.append(attempt_id)
        else:
            report.unknown_id("attempts", attempt_id, "evidence_attempt_ids")
    payload["evidence_attempt_ids"] = list(dict.fromkeys(evidence))

    # -- firewall inputs ----------------------------------------------------------
    all_target_facets: set[str] = set()
    all_target_criteria: set[str] = set()
    for event in payload.get("event_diagnoses") or []:
        for cause in event.get("candidate_causes") or []:
            facet = _facet_of(cause.get("target_ref"))
            if facet:
                all_target_facets.add(vault.canonical_facet_id(facet))
    for repair in payload.get("repair_suggestions") or []:
        all_target_facets.update(vault.canonical_facet_id(str(value)) for value in repair.get("target_evidence_families") or [])
        all_target_criteria.update(str(value) for value in repair.get("target_criterion_ids") or [])
        for ref in [*(repair.get("target_refs") or [])]:
            facet = _facet_of(ref)
            if facet:
                all_target_facets.add(vault.canonical_facet_id(facet))
            criterion = _criterion_of(ref)
            if criterion:
                all_target_criteria.add(criterion)
    protected_facets, passed_criteria = protected_targets(
        item,
        rubric,
        vault,
        criterion_points=criterion_points,
        facets=all_target_facets,
        criteria=all_target_criteria,
    )

    # -- events: index, scope firewall, ids, registry -----------------------------
    registry_ids = {record_id for record_id in known.registry_ids}
    events: list[dict[str, Any]] = []
    seen_indexes: set[int] = set()
    for event in payload.get("event_diagnoses") or []:
        index = int(event.get("event_index", -1))
        if index < 0 or index >= len(attributions) or index in seen_indexes:
            report.unknown_id("event_indexes", index, "event_diagnoses")
            continue
        seen_indexes.add(index)
        validity = str(attributions[index].get("validity_scope") or "unknown")
        if validity != "valid_measurement" and event.get("causal_class") != "unknown":
            report.issue(
                "scope_firewall",
                event_index=index,
                validity_scope=validity,
                rejected_causal_class=event.get("causal_class"),
            )
            event["causal_class"] = "unknown"
        causes = []
        for cause_index, cause in enumerate(event.get("candidate_causes") or []):
            facet = _facet_of(cause.get("target_ref"))
            if facet is not None:
                canonical = vault.canonical_facet_id(facet)
                if not known_facet(facet):
                    report.unknown_id("facets", facet, f"event:{index}:cause:{cause_index}")
                    cause["target_ref"] = {"kind": "none"}
                elif canonical in protected_facets:
                    report.issue("passed_facet_firewall", where=f"event:{index}:cause:{cause_index}", facet=canonical)
                    cause["target_ref"] = {"kind": "none"}
                else:
                    cause["target_ref"]["facet_id"] = canonical
            causes.append(cause)
        event["candidate_causes"] = causes
        criteria_ids = {str(row.get("id")) for row in current.rubric}
        claims = []
        for claim in event.get("postdictive_claims") or []:
            if str(claim.get("criterion_id")) in criteria_ids:
                claims.append(claim)
            else:
                report.issue("unknown_postdictive_criterion", event_index=index, criterion_id=claim.get("criterion_id"))
        event["postdictive_claims"] = claims
        prior_id = event.get("prior_hypothesis_id")
        if prior_id and prior_id not in known.hypothesis_ids:
            report.unknown_id("hypotheses", prior_id, f"event:{index}:prior_hypothesis_id")
            event["prior_hypothesis_id"] = None
        match = dict(event.get("registry_match") or {"kind": "abstain"})
        kind = match.get("kind")
        if kind in {"durable", "candidate"}:
            if not match.get("id") or match.get("id") not in registry_ids:
                report.unknown_id("registry", match.get("id"), f"event:{index}:registry_match")
                match = {"kind": "abstain", "id": None, "statement": None}
        elif kind == "new":
            if not (match.get("statement") or "").strip():
                report.issue("registry_new_without_statement", event_index=index)
                match = {"kind": "abstain", "id": None, "statement": None}
        event["registry_match"] = match
        events.append(event)
    payload["event_diagnoses"] = sorted(events, key=lambda value: value["event_index"])

    # -- repairs ------------------------------------------------------------------
    repairs = []
    expected = item.expected_answer
    for repair_index, repair in enumerate(payload.get("repair_suggestions") or []):
        trace_id = repair.get("repaired_trace_id")
        if trace_id and trace_id not in known.repaired_trace_ids:
            report.unknown_id("repaired_traces", trace_id, f"repair:{repair_index}")
            repair["repaired_trace_id"] = None
        lo_id = repair.get("learning_object_id")
        if lo_id and lo_id not in known.learning_object_ids:
            report.unknown_id("learning_objects", lo_id, f"repair:{repair_index}")
            repair["learning_object_id"] = None
        families = []
        for value in repair.get("target_evidence_families") or []:
            canonical = vault.canonical_facet_id(str(value))
            if not known_facet(str(value)):
                report.unknown_id("facets", value, f"repair:{repair_index}")
            elif canonical in protected_facets:
                report.issue("passed_facet_firewall", where=f"repair:{repair_index}", facet=canonical)
            else:
                families.append(canonical)
        repair["target_evidence_families"] = families
        rubric_criteria = {str(row.get("id")) for row in current.rubric}
        kept_criteria = []
        for value in repair.get("target_criterion_ids") or []:
            if value not in rubric_criteria:
                report.issue("unknown_criterion", where=f"repair:{repair_index}", criterion=value)
            elif value in passed_criteria:
                report.issue("passed_criterion_firewall", where=f"repair:{repair_index}", criterion=value)
            else:
                kept_criteria.append(value)
        repair["target_criterion_ids"] = kept_criteria
        refs = []
        for ref in repair.get("target_refs") or []:
            facet = _facet_of(ref)
            criterion = _criterion_of(ref)
            if facet is not None:
                canonical = vault.canonical_facet_id(facet)
                if not known_facet(facet):
                    report.unknown_id("facets", facet, f"repair:{repair_index}:target_ref")
                    continue
                if canonical in protected_facets:
                    report.issue("passed_facet_firewall", where=f"repair:{repair_index}:target_ref", facet=canonical)
                    continue
                ref = {**ref, "facet_id": canonical}
            if criterion is not None and criterion in passed_criteria:
                report.issue("passed_criterion_firewall", where=f"repair:{repair_index}:target_ref", criterion=criterion)
                continue
            refs.append(ref)
        repair["target_refs"] = refs
        candidate = dict(repair)
        trace = next(
            (
                dict(value)
                for value in grade.get("repaired_traces") or []
                if repair.get("repaired_trace_id") and value.get("id") == repair.get("repaired_trace_id")
            ),
            None,
        )
        if trace is not None:
            candidate["repaired_trace"] = trace
        repair["repair_validation"] = validate_repair_candidate(
            candidate,
            expected_answer=expected,
            trace_contract=item.trace_contract,
        ).as_dict()
        repairs.append(repair)
    payload["repair_suggestions"] = repairs

    # -- pattern claims: refs, ids, quotes, S4 validity ---------------------------
    evidence_set = set(payload["evidence_attempt_ids"])
    validated: list[ValidatedCitation] = []
    claims_out = []
    current_targets = set(current.target_facets())
    hypothesis_targets: dict[str, set[str]] = {}
    for claim_index, claim in enumerate(payload.get("pattern_claims") or []):
        ref = str(claim.get("hypothesis_ref") or "")
        targets: set[str] = set()
        if ref.startswith(CAUSE_REF_PREFIX):
            parts = ref[len(CAUSE_REF_PREFIX):].split(":")
            try:
                event_index, cause_index = int(parts[0]), int(parts[1])
            except (IndexError, ValueError):
                report.issue("pattern_ref_malformed", claim_index=claim_index, hypothesis_ref=ref)
                continue
            event = next((value for value in events if value["event_index"] == event_index), None)
            if event is None or cause_index >= len(event.get("candidate_causes") or []):
                report.issue("pattern_ref_unknown_cause", claim_index=claim_index, hypothesis_ref=ref)
                continue
            facet = _facet_of(event["candidate_causes"][cause_index].get("target_ref"))
            if facet:
                targets.add(facet)
            attribution = attributions[event_index]
            targets.update(str(value) for value in attribution.get("target_evidence_families") or [])
            attribution_facet = _facet_of(attribution.get("target_ref"))
            if attribution_facet:
                targets.add(attribution_facet)
        elif ref in known.hypothesis_ids:
            if ref not in hypothesis_targets:
                hypothesis_targets[ref] = set()
                for row in assembled.blocks.get("prior_hypotheses") or []:
                    if row.get("id") == ref:
                        hypothesis_targets[ref].update(row.get("target_facets") or [])
            targets.update(hypothesis_targets[ref])
        else:
            report.unknown_id("hypotheses", ref, f"pattern:{claim_index}")
            continue
        targets = {vault.canonical_facet_id(value) for value in (targets or current_targets)}
        cited_out = []
        for citation in claim.get("cited") or []:
            attempt_id = str(citation.get("attempt_id") or "")
            if attempt_id == current.attempt_id:
                report.issue("citation_of_current_attempt", claim_index=claim_index)
                continue
            if not known_attempt(attempt_id):
                report.unknown_id("attempts", attempt_id, f"pattern:{claim_index}:cited")
                continue
            prior = assembled.attempts.get(attempt_id) or store.attempt(attempt_id)
            if prior is None:
                report.unknown_id("attempts", attempt_id, f"pattern:{claim_index}:cited")
                continue
            if attempt_id not in evidence_set:
                report.issue("citation_not_in_evidence", claim_index=claim_index, attempt_id=attempt_id)
            quote = str(citation.get("quote") or "")
            anchor = resolve_quote_anchor(prior.learner_answer_md, quote)
            if anchor.char_start is None:
                anchored_to_divergence = any(
                    " ".join(quote.split()) == " ".join(value.split())
                    for value in prior.first_divergence_quotes
                )
                if not anchored_to_divergence:
                    report.issue(
                        "citation_quote_unanchored", claim_index=claim_index, attempt_id=attempt_id,
                    )
                    continue
            cited_out.append(citation)
            reason = _citation_invalid_reason(prior, targets)
            if reason is not None:
                report.issue("citation_not_valid_for_recurrence", claim_index=claim_index, attempt_id=attempt_id, reason=reason)
                continue
            if claim.get("relation") == "disconfirming":
                continue
            validated.append(
                ValidatedCitation(
                    claim_index=claim_index,
                    attempt_id=attempt_id,
                    quote=quote,
                    surface_group=prior.surface_group,
                    anchor_basis=anchor.basis,
                    char_start=anchor.char_start,
                    char_end=anchor.char_end,
                )
            )
        counter = []
        for attempt_id in claim.get("counterevidence_attempt_ids") or []:
            if known_attempt(str(attempt_id)) and attempt_id != current.attempt_id:
                counter.append(attempt_id)
            else:
                report.unknown_id("attempts", attempt_id, f"pattern:{claim_index}:counterevidence")
        claim["cited"] = cited_out
        claim["counterevidence_attempt_ids"] = counter
        claims_out.append(claim)
    payload["pattern_claims"] = claims_out

    # -- prerequisite gaps ----------------------------------------------------------
    gaps = []
    neighborhood_ids = {
        str(row.get("learning_object_id"))
        for row in (assembled.blocks.get("neighborhood") or {}).get("learning_objects") or []
    }
    for gap_index, gap in enumerate(payload.get("prerequisite_gap_hypotheses") or []):
        ref = str(gap.get("prerequisite_ref") or "")
        if ref not in neighborhood_ids and not known_facet(ref):
            kind = "learning_objects" if ref in vault.learning_objects or ref.startswith("lo_") else "facets"
            report.unknown_id(kind, ref, f"prerequisite:{gap_index}")
            continue
        for field_name in ("cited_attempt_ids", "demonstrated_counterevidence_ids"):
            kept = []
            for attempt_id in gap.get(field_name) or []:
                if known_attempt(str(attempt_id)) and attempt_id != current.attempt_id:
                    kept.append(attempt_id)
                else:
                    report.unknown_id("attempts", attempt_id, f"prerequisite:{gap_index}:{field_name}")
            gap[field_name] = kept
        gaps.append(gap)
    payload["prerequisite_gap_hypotheses"] = gaps

    # -- anchoring (§5.5) ---------------------------------------------------------
    anchoring_suspect, anchoring = _anchoring(payload, grade, known)

    # -- recurrence counts (shadow) ---------------------------------------------------
    groups: dict[int, set[str]] = {}
    for citation in validated:
        groups.setdefault(citation.claim_index, set()).add(citation.surface_group)
    report_dict = report.as_dict()
    report_dict.update(
        anchoring=anchoring,
        validated_recurrence=[
            {"claim_index": index, "independent_surface_groups": len(surfaces)}
            for index, surfaces in sorted(groups.items())
        ],
        protected_facets=sorted(protected_facets),
    )
    status = "completed"
    if not (payload.get("analysis_md") or "").strip():
        status = "validation_rejected"
        report_dict["rejection_reason"] = "empty_analysis"
    elif attributions and not events:
        status = "validation_rejected"
        report_dict["rejection_reason"] = "no_event_diagnosis_survived"
    return ValidatedDiagnosis(
        status=status,
        proposal=payload,
        report=report_dict,
        anchoring_suspect=anchoring_suspect,
        validated_citations=tuple(validated),
    )


def _citation_invalid_reason(prior: HistoryAttempt, targets: set[str]) -> str | None:
    if not prior.non_pass:
        return "cited_attempt_passed"
    if not prior.valid_measurement:
        return "not_valid_measurement"
    if targets and not (prior.facets() & targets):
        return "no_target_overlap"
    return None


def primary_cause(payload: Mapping[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """(event, cause) with the highest stated prior weight; first on ties."""

    best: tuple[float, int, int] | None = None
    chosen: tuple[dict[str, Any] | None, dict[str, Any] | None] = (None, None)
    for event_position, event in enumerate(payload.get("event_diagnoses") or []):
        for cause_position, cause in enumerate(event.get("candidate_causes") or []):
            weight = float(cause.get("prior_weight") or 0.0)
            key = (-weight, event_position, cause_position)
            if best is None or key < best:
                best = key
                chosen = (event, cause)
    return chosen


def _anchoring(
    payload: Mapping[str, Any],
    grade: Mapping[str, Any],
    known: KnownIds,
) -> tuple[bool, dict[str, Any]]:
    event, cause = primary_cause(payload)
    local_texts = [str(grade.get("local_analysis_md") or "")]
    for row in grade.get("error_attributions") or []:
        local_texts.append(str(row.get("evidence") or ""))
        divergence = row.get("first_divergence")
        if isinstance(divergence, Mapping) and divergence.get("quote"):
            local_texts.append(str(divergence["quote"]))
    if cause is None or event is None:
        return False, {"primary_cause": None}
    support = local_support(str(cause.get("statement") or ""), local_texts)
    changed = bool((event.get("history_changed_cause") or {}).get("changed"))
    reused = bool(event.get("prior_hypothesis_id"))
    match = event.get("registry_match") or {}
    if match.get("kind") in {"durable", "candidate"} and match.get("id") in known.registry_ids:
        reused = True
    for claim in payload.get("pattern_claims") or []:
        if str(claim.get("hypothesis_ref") or "") in known.hypothesis_ids:
            reused = True
    suspect = support < LOCAL_SUPPORT_THRESHOLD and not changed and reused
    return suspect, {
        "primary_cause_event_index": event.get("event_index"),
        "local_support": support,
        "local_support_threshold": LOCAL_SUPPORT_THRESHOLD,
        "history_changed_cause": changed,
        "prior_hypothesis_reused": reused,
    }


__all__ = [
    "LOCAL_SUPPORT_THRESHOLD",
    "ValidatedCitation",
    "ValidatedDiagnosis",
    "local_support",
    "primary_cause",
    "protected_targets",
    "validate_diagnosis_proposal",
]
