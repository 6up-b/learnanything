from __future__ import annotations

from datetime import UTC
from typing import Any

from learnloop.clock import SystemClock, parse_utc
from learnloop.db.repositories import GradingEvidenceRecord, Repository
from learnloop.services.grading import resolved_rubric
from learnloop.services.mastery import display_mastery, sigmoid
from learnloop.services.scheduler import (
    ScheduledItem,
    dominant_scheduler_reason,
    explain_practice_item,
)
from learnloop.services.source_review import resolve_source_refs
from learnloop.services.tutor_qa import hint_equivalents_for_attempt
from learnloop.vault.models import ErrorType, LearningObject, LoadedVault, PracticeItem, Rubric
from learnloop_sidecar.context import mastery_dto
from learnloop_sidecar.dto import to_camel, versioned
from learnloop_sidecar.errors import SidecarError


def scheduled_item_dto(vault: LoadedVault, repository: Repository, scheduled: ScheduledItem) -> dict[str, Any]:
    item = _require_item(vault, scheduled.practice_item_id)
    learning_object = vault.learning_objects.get(scheduled.learning_object_id)
    state = repository.practice_item_state(scheduled.practice_item_id)
    mastery = repository.mastery_state(scheduled.learning_object_id)
    mastery_display = display_mastery(mastery) if mastery is not None else None
    return to_camel(
        {
            "practice_item_id": scheduled.practice_item_id,
            "learning_object_id": scheduled.learning_object_id,
            "learning_object_title": learning_object.title if learning_object else scheduled.learning_object_id,
            "subject": _primary_subject(vault, item),
            "practice_mode": item.practice_mode,
            "selected_mode": scheduled.selected_mode,
            "priority": scheduled.priority,
            "components": scheduled.components,
            "readiness_factor": scheduled.readiness_factor,
            "plain_english": scheduled.plain_english,
            "dominant_reason": dominant_scheduler_reason(
                scheduled.components, vault.config
            ),
            "mastery": mastery_display.mastery_mean if mastery_display is not None else None,
            "mastery_variance": mastery_display.mastery_variance if mastery_display is not None else None,
            "due_at": state.due_at if state is not None else None,
            "due_status": _due_status(scheduled, state.due_at if state is not None else None),
            # A positive EIG marks a ranking-time candidate. Only the item with
            # a durable scheduler-backed presentation is a diagnostic probe.
            "is_probe": scheduled.components.get("probe_committed", 0.0) > 0.0,
            "is_followup": (
                scheduled.components.get("negative_surprise_followup", 0.0) > 0.0
                or scheduled.components.get("intervention_followup", 0.0) > 0.0
            ),
        }
    )


def scheduler_explanation_dto(scheduled: ScheduledItem) -> dict[str, Any]:
    return versioned(
        {
            "practice_item_id": scheduled.practice_item_id,
            "selected_mode": scheduled.selected_mode,
            "priority": scheduled.priority,
            "components": scheduled.components,
            "readiness_factor": scheduled.readiness_factor,
            "expected_information_gain": scheduled.components.get("probe_eig", 0.0),
            "plain_english": scheduled.plain_english,
        }
    )


def latest_scheduler_explanation_dto(record: dict[str, Any]) -> dict[str, Any]:
    return versioned(
        {
            "practice_item_id": record["practice_item_id"],
            "selected_mode": record["selected_mode"],
            "priority": record["priority"],
            "components": record["components"],
            "readiness_factor": record["readiness_factor"],
            "expected_information_gain": record.get("expected_information_gain", 0.0),
            "plain_english": record.get("plain_english") or [],
        }
    )


def practice_item_detail(vault: LoadedVault, repository: Repository, practice_item_id: str) -> dict[str, Any]:
    item = _require_item(vault, practice_item_id)
    learning_object = vault.learning_object_for_item(item)
    if learning_object is None:
        raise SidecarError("not_found", f"{practice_item_id} references a missing Learning Object.")
    scheduler = explain_practice_item(vault, repository, practice_item_id)
    rubric = _rubric_for_item(vault, item)
    max_points = rubric.max_points if rubric is not None else 4
    assessment_contract_version_id = None
    from learnloop.services.assessment_contracts import (
        KM_ALGORITHM_VERSION,
        snapshot_for_presentation,
    )

    if vault.config.algorithms.algorithm_version == KM_ALGORITHM_VERSION:
        assessment_contract_version_id = snapshot_for_presentation(
            repository, vault, item, rubric=rubric
        )
    return versioned(
        {
            "id": item.id,
            "learning_object_id": learning_object.id,
            "learning_object_title": learning_object.title,
            "subject": _primary_subject(vault, item),
            "subjects": vault.subjects_for_item(item),
            "practice_mode": item.practice_mode,
            "attempt_types_allowed": item.attempt_types_allowed,
            "evidence_facets": item.evidence_facets,
            "evidence_weights": item.evidence_weights,
            "prompt": item.prompt,
            "expected_answer": item.expected_answer,
            "difficulty": item.difficulty,
            "hints": item.hints,
            "hint_policy": {
                "max_useful_hints": item.hint_policy.max_useful_hints,
                "fsrs_rating_cap_by_hint": {str(k): v for k, v in item.hint_policy.fsrs_rating_cap_by_hint.items()},
                "mastery_alpha_dampening_by_hint": {
                    str(k): v for k, v in item.hint_policy.mastery_alpha_dampening_by_hint.items()
                },
            },
            "rubric": rubric_dto(rubric),
            "candidate_error_types": _candidate_error_types(vault, learning_object.concept),
            "tags": item.tags,
            "source_refs": [source_ref.model_dump() for source_ref in item.provenance.source_refs],
            "state": practice_item_state_dto(repository, item.id),
            "mastery": mastery_dto(repository, learning_object.id, vault),
            "scheduler": scheduler_explanation_dto(scheduler) if scheduler is not None else None,
            "attempts": practice_item_attempts(repository, item.id, max_points),
            "assessment_contract_version_id": assessment_contract_version_id,
        }
    )


def practice_item_attempts(
    repository: Repository, practice_item_id: str, max_points: int, limit: int = 10
) -> list[dict[str, Any]]:
    """Recent attempts on a Practice Item, newest first — the inspector's attempt-history table."""

    history: list[dict[str, Any]] = []
    for row in repository.list_recent_attempts_by_practice_item(practice_item_id, limit):
        surprise = repository.latest_attempt_surprise(row["id"]) or {}
        history.append(
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "attempt_type": row["attempt_type"],
                "rubric_score": row["rubric_score"],
                "max_points": max_points,
                "correctness": row["correctness"],
                "hints_used": row["hints_used"],
                "error_type": row["error_type"],
                "surprise_direction": surprise.get("surprise_direction"),
            }
        )
    return history


def learning_object_detail(vault: LoadedVault, repository: Repository, learning_object_id: str) -> dict[str, Any]:
    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        raise SidecarError("not_found", f"Learning Object {learning_object_id} was not found.")
    return to_camel(
        {
            "id": learning_object.id,
            "title": learning_object.title,
            "subjects": learning_object.subjects,
            "concept": learning_object.concept,
            "knowledge_type": learning_object.knowledge_type,
            "status": learning_object.status,
            "summary": learning_object.summary,
            "prerequisites": learning_object.prerequisites,
            "confusables": learning_object.confusables,
            "difficulty_prior": learning_object.difficulty_prior,
            "tags": learning_object.tags,
            "mastery": mastery_dto(repository, learning_object.id, vault),
        }
    )


def attempt_detail(vault: LoadedVault, repository: Repository, attempt_id: str) -> dict[str, Any]:
    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        raise SidecarError("not_found", f"Attempt {attempt_id} was not found.")
    return versioned(
        {
            "id": attempt["id"],
            "practice_item_id": attempt["practice_item_id"],
            "learning_object_id": attempt["learning_object_id"],
            "subject": attempt["subject"],
            "concept": attempt["concept"],
            "practice_mode": attempt["practice_mode"],
            "attempt_type": attempt["attempt_type"],
            "learner_answer_md": attempt["learner_answer_md"],
            "rubric_score": attempt["rubric_score"],
            "correctness": attempt["correctness"],
            "confidence": attempt["confidence"],
            "latency_seconds": attempt["latency_seconds"],
            "hints_used": attempt["hints_used"],
            "error_type": attempt["error_type"],
            "grader_confidence": attempt["grader_confidence"],
            "manual_review": attempt["manual_review"],
            "manual_review_reason": attempt["manual_review_reason"],
            "session_id": attempt.get("session_id"),
            "scheduler_slate_id": attempt.get("scheduler_slate_id"),
            "scheduler_candidate_id": attempt.get("scheduler_candidate_id"),
            "created_at": attempt["created_at"],
            "feedback": feedback_bundle(vault, repository, attempt_id),
        }
    )


def feedback_bundle(vault: LoadedVault, repository: Repository, attempt_id: str) -> dict[str, Any]:
    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        raise SidecarError("not_found", f"Attempt {attempt_id} was not found.")
    item = _require_item(vault, attempt["practice_item_id"])
    learning_object = vault.learning_objects.get(attempt["learning_object_id"])
    metadata = repository.fetch_attempt_feedback_metadata(attempt_id) or _legacy_feedback_metadata(repository, attempt_id)
    state = repository.practice_item_state(item.id)
    surprise = repository.latest_attempt_surprise(attempt_id) or {}
    mastery_after = mastery_dto(repository, attempt["learning_object_id"], vault)
    intervention_need = repository.intervention_need_for_attempt(attempt_id)
    gate_attempt_id = repository.followup_source_attempt(attempt_id)
    rating = repository.followup_rating(attempt_id)
    error_events = repository.error_events_for_attempt(attempt_id)
    matched_misconception = None
    for error_event in error_events:
        misconception_id = error_event.get("misconception_id")
        if not misconception_id:
            continue
        record = repository.misconception(str(misconception_id))
        if (
            record is not None
            and record.status in {"active", "resolving"}
            and record.correction_statement
        ):
            matched_misconception = {
                "id": record.id,
                "statement": record.statement,
                "correction_statement": record.correction_statement,
                "mechanism": record.mechanism,
                "target_facet": record.target_facet,
                "confused_with_facet": record.confused_with_facet,
                "status": record.status,
            }
            break
    # §2.1 regrade ledger fact: when this attempt's grading history carries a
    # persisted regrade (a grading epoch after the original), surface the
    # old→new receipt so the ledger card renders on a fresh load — not only
    # transiently after an in-screen trigger_regrade. Template-rendered fact.
    rubric = _rubric_for_item(vault, item)
    max_points = rubric.max_points if rubric is not None else 4
    regrade_marker = repository.attempt_regrade_marker(attempt_id)
    regrade = None
    if regrade_marker is not None:
        old_score = float(regrade_marker["old_points"])
        new_score = float(regrade_marker["new_points"])
        if new_score < old_score:
            regrade_direction = "down"
        elif new_score > old_score:
            regrade_direction = "up"
        else:
            regrade_direction = "same"
        regrade = {
            "old_score": old_score,
            "new_score": new_score,
            "max_points": max_points,
            "regraded_at": regrade_marker["at"],
            "direction": regrade_direction,
        }
    return versioned(
        {
            "attempt_id": attempt_id,
            "practice_item_id": item.id,
            "learning_object_id": attempt["learning_object_id"],
            "learning_object_title": learning_object.title if learning_object is not None else attempt["learning_object_id"],
            "rubric_score": attempt["rubric_score"] or 0,
            "max_points": max_points,
            "correctness": attempt["correctness"] or 0.0,
            "grader_confidence": attempt["grader_confidence"] or 0.0,
            "grading_source": metadata["grading_source"],
            "fallback_reason": metadata.get("fallback_reason"),
            "manual_review_reason": attempt["manual_review_reason"],
            "fsrs_rating": _rating_from_score(attempt["rubric_score"] or 0, _rubric_for_item(vault, item)),
            "next_due_at": state.due_at if state is not None else attempt["created_at"],
            "criterion_evidence": [
                criterion_evidence_dto(row, _rubric_for_item(vault, item))
                for row in repository.fetch_grading_evidence(attempt_id)
            ],
            "fatal_errors": metadata.get("fatal_errors") or [],
            "error_attributions": [
                error_event_dto(vault, row) for row in error_events
            ],
            "surprise": surprise_dto(surprise, vault.config.scheduler.followup.tau_followup_nats),
            "mastery_before": mastery_before_dto(surprise, mastery_after),
            "mastery_after": mastery_after,
            "feedback_md": metadata.get("feedback_md"),
            "feedback_shown_count": metadata.get("shown_count", 0),
            "feedback_first_shown_at": metadata.get("first_shown_at"),
            "feedback_last_shown_at": metadata.get("last_shown_at"),
            "repair_suggestions": metadata.get("repair_suggestions") or [],
            "intervention_need": intervention_need_dto(intervention_need),
            "primed": bool(attempt.get("primed")),
            # Canonical-source sections that spawned this item, for the
            # source-review panel (text section or video timestamp range).
            "source_refs": resolve_source_refs(vault, item),
            # Non-null when this attempt is itself a follow-up: the rating
            # strip renders and rate_followup joins back to the gate decision.
            "followup_source": ({"gate_attempt_id": gate_attempt_id} if gate_attempt_id is not None else None),
            "followup_rating": (
                {"useful": rating["useful"], "rated_at": rating["rated_at"]} if rating is not None else None
            ),
            "followup_queued": any(
                isinstance(action, str)
                and (
                    action.startswith("negative_surprise_followup:")
                    or action.startswith("intervention_followup:queued:")
                )
                for action in surprise.get("triggered_actions", [])
            ),
            # Tutor questions that counted as hints on this attempt ("N
            # questions counted as hints" in the feedback UI).
            "question_hint_equivalents": hint_equivalents_for_attempt(repository, attempt),
            # KM3 §9.6 unresolved-cause diagnostic card: ambiguous localized
            # failures whose candidate causes imply different repairs. The UI
            # offers a one-tap "run a short diagnostic" targeting the cause set.
            "unresolved_causes": [
                {
                    "id": factor["id"],
                    "observation_id": factor["observation_id"],
                    "candidate_causes": factor["candidate_causes"],
                }
                for factor in repository.unresolved_cause_factors_for_attempt(attempt_id)
            ],
            "matched_misconception": matched_misconception,
            # Persisted regrade ledger fact (None unless the attempt's grading
            # history carries a regrade). Renders the RegradeLedgerCard on load.
            "regrade": regrade,
        }
    )


def intervention_need_dto(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return to_camel(
        {
            "id": row["id"],
            "attempt_id": row.get("attempt_id"),
            "learning_object_id": row["learning_object_id"],
            "practice_item_id": row.get("practice_item_id"),
            "desired_intent": row["desired_intent"],
            "trigger_reason": row["trigger_reason"],
            "target_facets": row.get("target_facets") or [],
            "error_types": row.get("error_types") or [],
            "priority": row.get("priority"),
            "status": row["status"],
            "blocked_reason": row["blocked_reason"],
            "candidate_requirements": row.get("candidate_requirements") or {},
            "diagnostic_focus": row.get("diagnostic_focus"),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    )


def criterion_evidence_dto(row: GradingEvidenceRecord, rubric: Rubric | None) -> dict[str, Any]:
    criterion = None
    if rubric is not None:
        criterion = next((candidate for candidate in rubric.criteria if candidate.id == row.criterion_id), None)
    return to_camel(
        {
            "criterion_id": row.criterion_id,
            "criterion_description": criterion.description if criterion is not None else row.criterion_id,
            "points_awarded": row.points_awarded,
            "points_possible": criterion.points if criterion is not None else 0,
            "evidence": row.evidence,
            "notes": row.notes,
            "grader_tier": row.grader_tier,
            # Rubric tier ("core" | "transfer") — the feedback UI shows a pill
            # when a rubric actually distinguishes tiers (teach_back items).
            "tier": getattr(criterion, "tier", None) if criterion is not None else None,
        }
    )


def error_event_dto(vault: LoadedVault, row: dict[str, Any]) -> dict[str, Any]:
    error_type = vault.error_types.get(row["error_type"])
    return to_camel(
        {
            "id": row["id"],
            "attempt_id": row["attempt_id"],
            "learning_object_id": row["learning_object_id"],
            "error_type": row["error_type"],
            "error_title": error_type.title if isinstance(error_type, ErrorType) else None,
            "severity": row["severity"],
            "is_misconception": row["is_misconception"],
            "repair_plan": row["repair_plan"],
            "status": row["status"],
            "created_at": row["created_at"],
        }
    )


def mastery_before_dto(
    surprise: dict[str, Any], mastery_after: dict[str, Any] | None
) -> dict[str, Any] | None:
    """Reconstruct the pre-attempt mastery posterior for the Belief-update panel.

    The attempt only persists the *current* (post-update) mastery state, but the
    surprise row records the logit-space prior/posterior in ``posterior_delta``
    (mu_before / P_before). We map ``mu_before``/``P_before`` back to display
    space with the same delta-method conversion as ``display_mastery`` so the
    frontend's before→after bars and surprise badge render. Returns ``None`` when
    no surprise was recorded (e.g. legacy attempts), matching the DTO contract.
    """

    delta = surprise.get("posterior_delta") or {}
    mu_before = delta.get("mu_before")
    var_before = delta.get("P_before")
    if mu_before is None or var_before is None:
        return None
    mean = sigmoid(mu_before)
    variance = (mean * (1 - mean)) ** 2 * var_before
    after_count = mastery_after.get("evidenceCount") if mastery_after else None
    evidence_count = max(0, after_count - 1) if isinstance(after_count, int) else 0
    return to_camel(
        {
            "mean": mean,
            "variance": variance,
            "evidence_count": evidence_count,
            "last_evidence_at": None,
        }
    )


def surprise_dto(row: dict[str, Any], followup_threshold_nats: float | None = None) -> dict[str, Any]:
    # ``followup_threshold_nats`` is one trigger in the broader intervention
    # gate. It travels with the bundle so the feedback UI can render against
    # the live config value instead of a hard-coded constant.
    return to_camel(
        {
            "predictive_surprise": row.get("predictive_surprise"),
            "bayesian_surprise": row.get("bayesian_surprise"),
            "surprise_direction": row.get("surprise_direction"),
            "fsrs_interval_factor": row.get("fsrs_interval_factor"),
            "followup_threshold_nats": followup_threshold_nats,
            "triggered_actions": row.get("triggered_actions") or [],
            "suppressed_actions": row.get("suppressed_actions") or [],
            # Per-attempt record of which trigger/threshold/gate decided the
            # follow-up outcome; the feedback screen renders its decisive signal.
            "gate_diagnostics": row.get("gate_diagnostics"),
        }
    )


def practice_item_state_dto(repository: Repository, practice_item_id: str) -> dict[str, Any] | None:
    state = repository.practice_item_state(practice_item_id)
    if state is None:
        return None
    return to_camel(
        {
            "difficulty": state.difficulty,
            "stability": state.stability,
            "retrievability": state.retrievability,
            "due_at": state.due_at,
            "last_attempt_at": state.last_attempt_at,
            "active": state.active,
        }
    )


def rubric_dto(rubric: Rubric | None) -> dict[str, Any] | None:
    if rubric is None:
        return None
    return to_camel(
        {
            "max_points": rubric.max_points,
            "criteria": [criterion.model_dump() for criterion in rubric.criteria],
            "fatal_errors": [fatal.model_dump() for fatal in rubric.fatal_errors],
        }
    )


def _candidate_error_types(vault: LoadedVault, concept: str | None) -> list[dict[str, Any]]:
    """Error taxonomy the self-grade form offers per under-credited criterion.

    Every vault error type is selectable, but those tied to this item's concept
    (via ``related_concepts``) are flagged ``relevant`` and sorted to the top so
    the picker leads with the most likely attributions (the rest follow, ordered
    by title). Keys stay snake_case; ``versioned`` camel-cases the whole bundle.
    """

    def _relevant(error_type: ErrorType) -> bool:
        return concept is not None and concept in error_type.related_concepts

    ordered = sorted(
        vault.error_types.values(),
        key=lambda error_type: (not _relevant(error_type), error_type.title.lower(), error_type.id),
    )
    return [
        {
            "id": error_type.id,
            "title": error_type.title,
            "is_misconception": error_type.is_misconception,
            "severity_default": error_type.severity_default,
            "relevant": _relevant(error_type),
        }
        for error_type in ordered
    ]


def _require_item(vault: LoadedVault, practice_item_id: str) -> PracticeItem:
    item = vault.practice_items.get(practice_item_id)
    if item is None:
        raise SidecarError("not_found", f"Practice Item {practice_item_id} was not found.")
    return item


def _rubric_for_item(vault: LoadedVault, item: PracticeItem) -> Rubric | None:
    try:
        return resolved_rubric(vault, item)
    except Exception:
        return vault.rubric_for_item(item)


def _primary_subject(vault: LoadedVault, item: PracticeItem) -> str | None:
    subjects = vault.subjects_for_item(item)
    return subjects[0] if subjects else None


def _due_status(scheduled: ScheduledItem, due_at: str | None) -> str:
    if (
        scheduled.components.get("negative_surprise_followup", 0.0) > 0.0
        or scheduled.components.get("intervention_followup", 0.0) > 0.0
    ):
        return "followup"
    if scheduled.components.get("probe_eig", 0.0) > 0.0:
        return "probe"
    parsed_due = parse_utc(due_at)
    now = SystemClock().now().astimezone(UTC)
    if parsed_due is not None and parsed_due <= now:
        return "due"
    return "later"


def _legacy_feedback_metadata(repository: Repository, attempt_id: str) -> dict[str, Any]:
    evidence = repository.fetch_grading_evidence(attempt_id)
    source = "codex" if any(row.grader_tier >= 3 for row in evidence) else "self"
    return {
        "grading_source": source,
        "fallback_reason": None,
        "fatal_errors": [],
        "feedback_md": None,
        "repair_suggestions": [],
    }


def _rating_from_score(score: int, rubric: Rubric | None) -> str:
    max_points = rubric.max_points if rubric is not None else 4
    ratio = score / max(max_points, 1)
    if ratio <= 0.25:
        return "again"
    if ratio <= 0.5:
        return "hard"
    if ratio < 0.85:
        return "good"
    return "easy"
