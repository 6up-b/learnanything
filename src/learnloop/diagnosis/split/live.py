"""The live split's read paths and settings (Slice 1 M2, spec §6.3, §11, §12).

* :func:`settings_from_config` maps the ``[diagnosis]`` section onto M1's
  :class:`~learnloop.diagnosis.split.settings.DiagnosisSettings`, so the
  defaults stay in one place.
* :func:`live_history_store` is M1's vault store with every persisted blind
  grade as its overlay: blind attempts are read from their validated blind
  record, joint ones from the stored grade stripped of causal fields (S3).
* :func:`build_causal_view` is the §4.2 mapping in reverse, computed ONCE when
  a diagnosis is persisted: which error event gets which candidate causes,
  misconception statement, operation, postdictive claims and registry match,
  and which instructional repairs (each joined to the blind repaired trace it
  builds on) the feedback metadata now carries. The repository lays it over the
  raw rows on read; replay reads the same stored view and never re-derives it.
* :func:`diagnosis_for_attempt` is the single read path (§6.3): the latest
  completed live diagnosis, else the legacy view of a joint grade, else None.
"""

from __future__ import annotations

import hashlib
from typing import Any, Mapping, Sequence

from learnloop.attempts.blind_grading import GRADER_MODE_BLIND
from learnloop.attempts.grading import resolved_rubric
from learnloop.db.repositories import Repository
from learnloop.diagnosis.split.context import CurrentAttempt, current_attempt_from
from learnloop.diagnosis.split.history import VaultHistoryStore
from learnloop.diagnosis.split.legacy_view import LEGACY_VIEW_MODE, stored_legacy_view
from learnloop.diagnosis.split.settings import DiagnosisSettings
from learnloop.vault.models import LoadedVault

CAUSAL_VIEW_VERSION = "causal-view-v1"
#: Joint ``cause_scope`` for a blind attribution's validity (the grader owns
#: validity; the diagnoser's causal class applies only to valid measurements).
_SCOPE_FOR_VALIDITY = {
    "item_contract": "item_contract",
    "grader_interpretation": "grader_interpretation",
    "interaction_context": "interaction_context",
    "unknown": "unknown",
}
_REPAIR_FIELDS = (
    "practice_mode",
    "rationale",
    "learning_object_id",
    "target_evidence_families",
    "target_criterion_ids",
    "operator",
    "target_refs",
    "preserve_refs",
    "expected_minutes",
    "answer_reveal_budget",
    "eliciting_question",
    "expected_response_contract",
    "verification_request",
)
_TRACE_FIELDS = (
    "learner_work_prefix",
    "repair_insertion_point",
    "minimal_edit",
    "regenerated_work",
    "repaired_answer_md",
    "changed_latent_claims",
    "changed_checkpoint_ids",
)


def settings_from_config(vault: LoadedVault) -> DiagnosisSettings:
    config = getattr(vault.config, "diagnosis", None)
    if config is None:
        return DiagnosisSettings()
    return DiagnosisSettings(
        history_mode=config.history_mode,
        full_history_token_budget=int(config.full_history_token_budget),
        history_error_limit=int(config.history_error_limit),
        history_success_limit=int(config.history_success_limit),
        exact_history_token_budget=int(config.exact_history_token_budget),
        sample_count=int(config.sample_count),
        correct_answer_sample_rate=float(config.correct_answer_sample_rate),
        knn_limit=int(config.knn_limit),
        hybrid_keep=int(config.hybrid_keep),
        rrf_k=int(config.rrf_k),
    )


def live_history_store(vault: LoadedVault, repository: Repository) -> VaultHistoryStore:
    """M1's store with every persisted blind grade as the overlay."""

    blind = {
        attempt_id: dict(row.get("record") or {})
        for attempt_id, row in repository.latest_blind_grade_records().items()
    }
    return VaultHistoryStore(vault, repository, blind_grades=blind)


def joint_grade_record(vault: LoadedVault, repository: Repository, attempt: Mapping[str, Any]) -> dict[str, Any]:
    """A stored JOINT grade in the blind-record shape, causal fields stripped.

    Shadow diagnosis on a joint vault needs a current-attempt grade to show.
    It carries only measurement fields (criteria, fatal errors, divergence,
    targets, validity) and an empty local analysis: the joint ``diagnosis_md``
    is causal prose the diagnoser must not anchor on (S3).
    """

    item = vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
    rubric = resolved_rubric(vault, item) if item is not None else None
    evidence = repository.fetch_grading_evidence(str(attempt["id"]))
    events = repository.raw_error_events_for_attempt(str(attempt["id"]))
    metadata = repository.raw_attempt_feedback_metadata(str(attempt["id"])) or {}
    attributions = []
    for index, event in enumerate(events):
        plan = event.get("repair_plan") if isinstance(event.get("repair_plan"), Mapping) else {}
        scope = str(plan.get("cause_scope") or "")
        attributions.append(
            {
                "index": index,
                "error_type": event.get("error_type"),
                "severity": event.get("severity"),
                "evidence": plan.get("evidence"),
                "target_evidence_families": list(plan.get("target_evidence_families") or []),
                "target_criterion_ids": list(plan.get("target_criterion_ids") or []),
                "target_ref": plan.get("target_ref"),
                "resolution_status": plan.get("resolution_status"),
                "validity_scope": (
                    scope
                    if scope in {"item_contract", "grader_interpretation", "interaction_context"}
                    else "valid_measurement"
                ),
                "first_divergence": plan.get("first_divergence"),
                "repaired_trace_id": None,
            }
        )
    return {
        "grader_mode": "joint_stripped",
        "rubric_score": attempt.get("rubric_score"),
        "max_points": float(rubric.max_points) if rubric is not None else None,
        "criteria": [
            {
                "criterion_id": row.criterion_id,
                "points_awarded": row.points_awarded,
                "evidence": row.evidence,
            }
            for row in evidence
        ],
        "fatal_errors": list(metadata.get("fatal_errors") or []),
        "local_analysis_md": "",
        "repaired_traces": [],
        "error_attributions": attributions,
    }


def current_attempt_for(
    vault: LoadedVault,
    attempt: Mapping[str, Any],
    record: Mapping[str, Any],
    repository: Any = None,
) -> CurrentAttempt | None:
    """The attempt to diagnose; with ``repository``, its question is the one
    its graded contract froze (method-explicit-3 review F3)."""

    item = vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
    if item is None:
        return None
    contract = None
    if repository is not None:
        from learnloop.db.stores.answered_contracts import answered_contracts

        with repository.connection() as connection:
            contract = answered_contracts(connection, [str(attempt["id"])]).get(str(attempt["id"]))
    return current_attempt_from(
        vault,
        item,
        attempt_id=str(attempt["id"]),
        completed_at=str(attempt.get("created_at") or ""),
        learner_answer_md=str(attempt.get("learner_answer_md") or ""),
        blind_grade=record,
        contract=contract,
    )


def needs_diagnosis(record: Mapping[str, Any]) -> bool:
    """§5.1: a non-pass criterion, a fatal error, or an error attribution.

    PF-c (owner decision 2026-10-12): an unverified criterion is unassessed,
    so it is not a non-pass, and the attributions the gate rescoped onto it
    explain nothing that was measured. When the gate applied, only a fatal
    error or an assessed shortfall (the gate's ``assessed_shortfall``) needs a
    diagnosis; a record without that key reads as before.
    """

    support = record.get("grading_support") or {}
    from learnloop.outcome_contract import grade_held_for_review

    if grade_held_for_review(support):
        # held-grade-evidence: a grade held for review (nothing assessed,
        # nothing validated) is no outcome, so there is nothing to explain;
        # a regrade that releases it writes a record of its own.
        return False
    if record.get("fatal_errors"):
        return True
    if support.get("valid_alternative_gate_applied") and "assessed_shortfall" in support:
        return bool(support["assessed_shortfall"])
    if record.get("error_attributions"):
        return True
    maximum = record.get("max_points")
    score = record.get("rubric_score")
    if maximum is not None and score is not None and float(score) + 1e-9 < float(maximum):
        return True
    return False


def sampled_correct_answer(attempt_id: str, rate: float) -> bool:
    """Deterministic shadow sample of correct answers (§5.1, O5)."""

    if rate <= 0.0:
        return False
    digest = hashlib.sha256(f"correct-answer-sample:{attempt_id}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF < rate


# -- the causal view ---------------------------------------------------------------

def _present(value: Any) -> bool:
    return value is not None and value != [] and value != ""


def _event_ids_by_index(
    record: Mapping[str, Any], events: Sequence[Mapping[str, Any]]
) -> dict[int, str]:
    """Blind attribution index -> raw error-event id.

    Error events are written one per validated attribution in order (ULIDs are
    monotonic within a process), so position is the primary key; the error
    type is checked so a regraded or otherwise rewritten event list never
    receives another grade's causes.
    """

    attributions = list(record.get("error_attributions") or [])
    mapping: dict[int, str] = {}
    if len(attributions) == len(events):
        for position, (row, event) in enumerate(zip(attributions, events)):
            mapping[int(row.get("index", position))] = str(event["id"])
        return mapping
    # Counts differ (an event list rewritten since this grade): pair by error
    # type in order, and leave anything ambiguous unmapped rather than guess.
    remaining = list(events)
    for position, row in enumerate(attributions):
        wanted = str(row.get("error_type") or "")
        for offset, event in enumerate(remaining):
            if str(event.get("error_type") or "") == wanted:
                mapping[int(row.get("index", position))] = str(event["id"])
                del remaining[offset]
                break
    return mapping


def build_causal_view(
    *,
    diagnosis_id: str,
    proposal: Mapping[str, Any],
    record: Mapping[str, Any],
    error_events: Sequence[Mapping[str, Any]],
    agent_run_id: str | None = None,
) -> dict[str, Any]:
    """The §4.2 reverse mapping of one validated diagnosis (computed once)."""

    attributions = {
        int(row.get("index", position)): row
        for position, row in enumerate(record.get("error_attributions") or [])
    }
    event_ids = _event_ids_by_index(record, error_events)
    events: dict[str, Any] = {}
    unmapped: list[int] = []
    for event in proposal.get("event_diagnoses") or []:
        index = int(event.get("event_index", -1))
        event_id = event_ids.get(index)
        if event_id is None:
            unmapped.append(index)
            continue
        validity = str((attributions.get(index) or {}).get("validity_scope") or "unknown")
        causal_class = str(event.get("causal_class") or "unknown")
        cause_scope = causal_class if validity == "valid_measurement" else _SCOPE_FOR_VALIDITY.get(validity, "unknown")
        statement = str(event.get("misconception_statement") or "").strip() or None
        plan: dict[str, Any] = {"cause_scope": cause_scope}
        causes = [dict(cause) for cause in event.get("candidate_causes") or [] if isinstance(cause, Mapping)]
        if causes:
            plan["candidate_causes"] = causes
        for key, target in (
            ("operation", "operation"),
            ("postdictive_claims", "postdictive_claims"),
            ("soft_postdictive_claims", "soft_postdictive_claims"),
            ("causal_confidence", "model_reported_causal_confidence"),
        ):
            if _present(event.get(key)):
                plan[target] = event.get(key)
        events[event_id] = {
            "is_misconception": bool(
                statement and causal_class == "learner_state" and validity == "valid_measurement"
            ),
            "misconception_statement": statement,
            "misconception_consistent_answer": (
                str(event.get("misconception_consistent_answer") or "").strip() or None
            ),
            "registry_match": dict(event.get("registry_match") or {"kind": "abstain"}),
            "causal_class": causal_class,
            "repair_plan": plan,
        }
    traces = {
        str(trace.get("id")): trace
        for trace in record.get("repaired_traces") or []
        if isinstance(trace, Mapping) and trace.get("id")
    }
    repairs: list[dict[str, Any]] = []
    for index, repair in enumerate(proposal.get("repair_suggestions") or []):
        suggestion: dict[str, Any] = {
            key: repair[key] for key in _REPAIR_FIELDS if key in repair and _present(repair[key])
        }
        suggestion.setdefault("practice_mode", str(repair.get("practice_mode") or "unspecified"))
        suggestion.setdefault("rationale", str(repair.get("rationale") or ""))
        if "answer_reveal_budget" not in suggestion and repair.get("answer_reveal_budget") is not None:
            suggestion["answer_reveal_budget"] = repair.get("answer_reveal_budget")
        suggestion["id"] = f"diagnosis:{diagnosis_id}:{index}"
        trace = traces.get(str(repair.get("repaired_trace_id") or ""))
        if trace is not None:
            suggestion["repaired_trace"] = {
                key: trace[key] for key in _TRACE_FIELDS if key in trace and trace[key] is not None
            }
            suggestion["repaired_trace_id"] = trace.get("id")
        if isinstance(repair.get("repair_validation"), Mapping):
            suggestion["repair_validation"] = dict(repair["repair_validation"])
        repairs.append(suggestion)
    return {
        "version": CAUSAL_VIEW_VERSION,
        "diagnosis_id": diagnosis_id,
        "agent_run_id": agent_run_id,
        "events": events,
        "unmapped_event_indexes": sorted(unmapped),
        "repair_suggestions": repairs,
    }


# -- the single read path (§6.3) ------------------------------------------------------

def diagnosis_for_attempt(repository: Repository, attempt_id: str) -> dict[str, Any] | None:
    """The diagnosis every reader uses: live, else a joint legacy view, else None.

    "Live" is the diagnosis IN FORCE: the attempt's latest live diagnosis,
    completed, for its current blind grade (the same rule the overlays apply,
    ``Repository.current_live_diagnosis``). A regrade, or a later failed or
    skipped diagnosis, leaves nothing in force until a new one completes; an
    older explanation is never served in its place.
    """

    live = repository.current_live_diagnosis(attempt_id)
    if live is not None and isinstance(live.get("proposal"), Mapping):
        return {
            **dict(live["proposal"]),
            "mode": "live",
            "diagnosis_id": live["id"],
            "history_mode": live.get("history_mode"),
            "created_at": live.get("created_at"),
        }
    if repository.latest_blind_grade_record(attempt_id) is not None:
        # A blind grade never has a legacy view: its causal fields do not exist.
        return None
    view = stored_legacy_view(repository, attempt_id)
    if view is None:
        return None
    return {**view, "mode": LEGACY_VIEW_MODE}


def grader_mode_for(repository: Repository, attempt_id: str) -> str:
    return GRADER_MODE_BLIND if repository.latest_blind_grade_record(attempt_id) is not None else "joint"


__all__ = [
    "CAUSAL_VIEW_VERSION",
    "build_causal_view",
    "current_attempt_for",
    "diagnosis_for_attempt",
    "grader_mode_for",
    "joint_grade_record",
    "live_history_store",
    "needs_diagnosis",
    "sampled_correct_answer",
    "settings_from_config",
]
