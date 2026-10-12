"""The stored joint diagnosis, read in the ``DiagnosisProposal`` shape (§6.3).

Before the split, one grading call both measured and explained. Its causal
fields live in ``error_events.repair_plan`` and the instructional repairs in
``attempt_feedback_metadata.repair_suggestions``; the prose ``diagnosis_md``
survives only in that call's model receipt. This module applies the §4.2
mapping in reverse, labelled ``mode='legacy_view'`` and never stored. It is
M1's arm (a) and the seed of M2's ``diagnosis_for_attempt`` legacy path.
"""

from __future__ import annotations

import json
from typing import Any, Iterable, Mapping, Sequence

from learnloop.attempts.ai_contracts import GradingProposal
from learnloop.db.repositories import Repository

LEGACY_VIEW_MODE = "legacy_view"
#: ``model_call_receipts.owner_kind`` of the calls an offline review makes.
REVIEW_RECEIPT_OWNER_KIND = "diagnosis_review"
_CAUSAL_CLASSES = {"learner_state", "transient_execution"}
_INSTRUCTIONAL_FIELDS = (
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


def _decode(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _event_diagnosis(index: int, event: Mapping[str, Any]) -> dict[str, Any]:
    plan = event.get("repair_plan") if isinstance(event.get("repair_plan"), Mapping) else {}
    scope = str(plan.get("cause_scope") or "unknown")
    divergence = plan.get("first_divergence") if isinstance(plan.get("first_divergence"), Mapping) else {}
    misconception_id = event.get("misconception_id")
    return {
        "event_index": index,
        "first_divergence_quote": divergence.get("quote"),
        "causal_class": scope if scope in _CAUSAL_CLASSES else "unknown",
        "candidate_causes": [dict(cause) for cause in plan.get("candidate_causes") or [] if isinstance(cause, Mapping)],
        "misconception_statement": event.get("misconception_statement"),
        "misconception_consistent_answer": event.get("misconception_consistent_answer"),
        "operation": plan.get("operation"),
        "causal_confidence": plan.get("model_reported_causal_confidence"),
        "postdictive_claims": [dict(claim) for claim in plan.get("postdictive_claims") or [] if isinstance(claim, Mapping)],
        "soft_postdictive_claims": [str(claim) for claim in plan.get("soft_postdictive_claims") or []],
        "registry_match": (
            {"kind": "durable", "id": str(misconception_id), "statement": None}
            if misconception_id
            else {"kind": "abstain", "id": None, "statement": None}
        ),
        "prior_hypothesis_id": None,
        "history_changed_cause": {"changed": False, "note": ""},
    }


def _repair(suggestion: Mapping[str, Any]) -> dict[str, Any]:
    payload = {key: suggestion[key] for key in _INSTRUCTIONAL_FIELDS if key in suggestion}
    payload.setdefault("practice_mode", str(suggestion.get("practice_mode") or "unspecified"))
    payload.setdefault("rationale", str(suggestion.get("rationale") or ""))
    payload["repaired_trace_id"] = None
    if isinstance(suggestion.get("repaired_trace"), Mapping):
        payload["legacy_repaired_trace"] = dict(suggestion["repaired_trace"])
    return payload


def legacy_view_from_parts(
    *,
    analysis_md: str | None,
    error_events: Sequence[Mapping[str, Any]],
    repair_suggestions: Iterable[Mapping[str, Any]],
    history_attempt_ids: Sequence[str] = (),
    source: str,
) -> dict[str, Any]:
    events = [_event_diagnosis(index, event) for index, event in enumerate(error_events)]
    if analysis_md and analysis_md.strip():
        analysis = analysis_md.strip()
    else:
        statements = [
            str(event.get("misconception_statement") or "").strip()
            for event in error_events
            if str(event.get("misconception_statement") or "").strip()
        ]
        causes = [
            str(cause.get("statement") or "").strip()
            for event in events
            for cause in event["candidate_causes"]
            if str(cause.get("statement") or "").strip()
        ]
        analysis = " ".join([*statements, *causes]) or ""
    return {
        "mode": LEGACY_VIEW_MODE,
        "source": source,
        "analysis_md": analysis,
        "evidence_attempt_ids": [str(value) for value in history_attempt_ids],
        "event_diagnoses": events,
        "repair_suggestions": [_repair(suggestion) for suggestion in repair_suggestions if isinstance(suggestion, Mapping)],
        "pattern_claims": [],
        "prerequisite_gap_hypotheses": [],
        "abstentions": [],
    }


def legacy_view_from_grading_proposal(
    proposal: GradingProposal,
    *,
    misconception_ids: Sequence[str | None] = (),
    history_attempt_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """The joint grader's fresh output, in the same reverse mapping."""

    events = []
    for index, attribution in enumerate(proposal.error_attributions):
        plan = attribution.model_dump(mode="json", exclude_none=True)
        events.append(
            {
                "repair_plan": {
                    **plan,
                    "model_reported_causal_confidence": attribution.causal_confidence,
                },
                "misconception_statement": attribution.misconception_statement,
                "misconception_consistent_answer": attribution.misconception_consistent_answer,
                "misconception_id": misconception_ids[index] if index < len(misconception_ids) else None,
            }
        )
    return legacy_view_from_parts(
        analysis_md=proposal.diagnosis_md,
        error_events=events,
        repair_suggestions=[
            suggestion.model_dump(mode="json", exclude_none=True)
            for suggestion in proposal.repair_suggestions
        ],
        history_attempt_ids=history_attempt_ids,
        source="joint_grader_rerun",
    )


def _stored_joint_analysis(repository: Repository, attempt_id: str) -> str | None:
    """The joint call's ``diagnosis_md`` from its model receipt, when kept.

    Receipts an offline review wrote into its scratch copy (the joint
    grader's REPEAT) are not the stored diagnosis and are never read here.
    """

    needle = f'%"attempt_id":"{attempt_id}"%'
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT output_text FROM model_call_receipts "
            "WHERE purpose = 'grading' AND status = 'completed' AND output_text LIKE ? "
            "AND owner_kind != ? "
            "ORDER BY started_at DESC, id DESC",
            (needle, REVIEW_RECEIPT_OWNER_KIND),
        ).fetchall()
    for row in rows:
        payload = _decode(row[0], None)
        if isinstance(payload, Mapping) and payload.get("attempt_id") == attempt_id:
            text = payload.get("diagnosis_md")
            if isinstance(text, str) and text.strip():
                return text
    return None


def stored_legacy_view(repository: Repository, attempt_id: str) -> dict[str, Any] | None:
    """Arm (a): the joint diagnosis exactly as stored, or ``None`` if none exists."""

    events = repository.error_events_for_attempt(attempt_id)
    metadata = repository.fetch_attempt_feedback_metadata(attempt_id) or {}
    suggestions = metadata.get("repair_suggestions")
    if suggestions is None:
        suggestions = _decode(metadata.get("repair_suggestions_json"), [])
    if not events and not suggestions:
        return None
    with repository.connection() as connection:
        receipt = connection.execute(
            "SELECT c4_history_attempt_ids_json FROM diagnostic_augmentation_receipts WHERE attempt_id = ?",
            (attempt_id,),
        ).fetchone()
    history = [str(value) for value in _decode(receipt[0], [])] if receipt is not None else []
    return legacy_view_from_parts(
        analysis_md=_stored_joint_analysis(repository, attempt_id),
        error_events=events,
        repair_suggestions=suggestions or [],
        history_attempt_ids=history,
        source="stored_joint_grade",
    )


__all__ = [
    "LEGACY_VIEW_MODE",
    "REVIEW_RECEIPT_OWNER_KIND",
    "legacy_view_from_grading_proposal",
    "legacy_view_from_parts",
    "stored_legacy_view",
]
