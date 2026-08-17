from __future__ import annotations

import re
from datetime import UTC
from typing import Any

from learnloop.clock import SystemClock, parse_utc
from learnloop.db.repositories import GradingEvidenceRecord, Repository
from learnloop.services.confusable_concepts import learner_observed_confusable_concepts
from learnloop.services.grading import resolved_rubric
from learnloop.services.mastery import display_mastery, sigmoid
from learnloop.services.mastery_step_attribution import explain_mastery_step
from learnloop.services.scheduler import (
    _FOLLOWUP_REASONS,
    ScheduledItem,
    dominant_scheduler_reason,
    explain_practice_item,
)
from learnloop.services.source_refs import source_ref_display_dto
from learnloop.services.source_review import resolve_source_refs
from learnloop.services.tutor_qa import hint_equivalents_for_attempt
from learnloop.vault.models import ErrorType, LearningObject, LoadedVault, PracticeItem, Rubric
from learnloop_sidecar.context import mastery_dto
from learnloop_sidecar.dto import to_camel, versioned
from learnloop_sidecar.errors import SidecarError


#: Reverse of the scheduler's follow-up reason table, kept only as a FALLBACK.
#: ``_insert_pending_followups`` routes three distinct ``action_type`` lanes onto
#: one ``intervention_followup`` component, and ``ScheduledItem.followup_kind``
#: now carries the originating lane directly. Queue rows built by other paths --
#: notably tests and the TUI, which construct ``ScheduledItem`` by hand -- may
#: still arrive without the field, and for those the plain-English reason the
#: scheduler puts first is the only surviving carrier of the lane. That matters:
#: a §5.7 certification cold probe is a held-out validity check on something
#: already certified, not a repair retry, and collapsing the two makes the UI
#: narrate a validity check as an intervention.
_FOLLOWUP_KIND_BY_REASON: dict[str, str] = {
    reason: kind for kind, reason in _FOLLOWUP_REASONS.items()
}


def _followup_kind(scheduled: ScheduledItem) -> str:
    # Direct read: the scheduler stamps the lane it actually inserted under.
    if scheduled.followup_kind is not None:
        return scheduled.followup_kind
    for reason in scheduled.plain_english:
        kind = _FOLLOWUP_KIND_BY_REASON.get(reason)
        if kind is not None:
            return kind
    if scheduled.components.get("negative_surprise_followup", 0.0) > 0.0:
        return "negative_surprise_followup"
    return "intervention_followup"


def scheduled_item_dto(vault: LoadedVault, repository: Repository, scheduled: ScheduledItem) -> dict[str, Any]:
    item = _require_item(vault, scheduled.practice_item_id)
    learning_object = vault.learning_objects.get(scheduled.learning_object_id)
    state = repository.practice_item_state(scheduled.practice_item_id)
    mastery = repository.mastery_state(scheduled.learning_object_id)
    mastery_display = display_mastery(mastery) if mastery is not None else None
    is_followup = (
        scheduled.components.get("negative_surprise_followup", 0.0) > 0.0
        or scheduled.components.get("intervention_followup", 0.0) > 0.0
    )
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
            "is_followup": is_followup,
            # Which follow-up lane, so the surface can say what the item is FOR
            # instead of assuming every insertion is a repair.
            "followup_kind": _followup_kind(scheduled) if is_followup else None,
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


#: Kinds of block a serving surface may have to render. Closed on purpose: a new
#: instrument class whose stimulus lives on a new contract has to be added HERE,
#: which is the one edit that makes every consumer of :func:`item_presentation`
#: render it — instead of each surface growing its own private list of fields to
#: remember. Ordering within a served payload is the list's, not this tuple's.
PRESENTATION_BLOCK_KINDS = (
    "laddered_stem_stimulus",
    "prompt",
    "error_hunt_worked_solution",
)


def item_presentation(item: PracticeItem) -> dict[str, Any]:
    """Everything the learner must SEE to answer ``item``, as ONE structure.

    Spec: ``spec_measurement_efficiency_v1.md`` §3.A2/§3.A3, and the Stage 6
    adversarial review that found two instrument classes shipped through the
    vault, wire, service and persistence layers with no renderer at all.

    WHY THIS IS A LIST OF TYPED BLOCKS AND NOT THREE MORE DTO FIELDS. The defect
    ``services/instrument_serving`` exists to contain is a *presentation* gap:
    ``prompt`` was the only thing any surface carried, so an error hunt served
    its instruction ("repair the worked solution below") with no solution beneath
    it and a laddered-stem part served a question about a setup the learner never
    saw. Two independent renderers (practice and exams) each reading item fields
    they happened to know about is exactly how that happened, and adding
    ``workedSolutionMd`` beside ``prompt`` would reproduce it the next time an
    instrument class arrives. A surface that renders ``blocks`` in order cannot
    forget a member it has never heard of.

    NONBLANK, OR A TYPED REFUSAL. ``laddered_stem.stimulus_md`` is Optional on
    the model and ``worked_solution_md`` can be the empty string, so "renderable"
    is not implied by "present". An empty stimulus rendered as an empty div is
    the *silent* failure again — the learner cannot answer, the grader (which
    receives the solution through its own path) marks every planted error missed,
    and the projection banks negative facet mass for a repair nobody was shown
    the material to make. Refusing here is louder than that and strictly safer:
    the serve fails with a reason instead of manufacturing harmful evidence.

    The refusal is a data-level check and stays after rendering support lands: it
    is the arm ``instrument_serving.unservable_reason`` cannot make, because that
    predicate answers "can the app render this class at all", not "does this item
    carry the content".
    """

    blocks: list[dict[str, Any]] = []

    stem = getattr(item, "laddered_stem", None)
    if stem is not None:
        stimulus = (getattr(stem, "stimulus_md", None) or "").strip()
        if not stimulus:
            raise SidecarError(
                "item_stimulus_unrenderable",
                f"Practice Item {item.id} is one part of laddered stem "
                f"{stem.stem_id} but carries no stimulus, so the part cannot be "
                "answered. Author `laddered_stem.stimulus_md` on this part.",
                details={
                    "reason": "laddered_stem_stimulus_blank",
                    "practice_item_id": item.id,
                    "stem_id": stem.stem_id,
                },
            )
        blocks.append(
            {
                "kind": "laddered_stem_stimulus",
                "markdown": stem.stimulus_md,
                # Named as the SHARED setup so a learner meeting part 3 knows the
                # text is the same one parts 1-2 climbed, not a new scenario.
                "label": (
                    f"Shared setup · part {stem.part_index + 1} of {stem.part_count}"
                ),
                "stem_id": stem.stem_id,
            }
        )

    blocks.append({"kind": "prompt", "markdown": item.prompt, "label": None})

    hunt = getattr(item, "error_hunt", None)
    if hunt is not None:
        solution = (getattr(hunt, "worked_solution_md", None) or "").strip()
        if not solution:
            raise SidecarError(
                "item_stimulus_unrenderable",
                f"Practice Item {item.id} is an error hunt with no worked "
                "solution, so the learner would be asked to repair work they "
                "cannot see. Author `error_hunt.worked_solution_md`.",
                details={
                    "reason": "error_hunt_worked_solution_blank",
                    "practice_item_id": item.id,
                },
            )
        blocks.append(
            {
                "kind": "error_hunt_worked_solution",
                "markdown": hunt.worked_solution_md,
                # Deliberately says nothing about how many errors are in it, or
                # whether there are any: §3.A3 forbids declaring the error count,
                # and the clean rotation ("a rotation that sometimes presents
                # correct work") is what kills the "there is always an error"
                # strategy. A label reading "find the mistakes" would leak both.
                "label": "Worked solution",
            }
        )

    return {"practice_item_id": item.id, "blocks": blocks}


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
    active_cold_retry = repository.active_followup_task_for_item(
        item.id, kind="cold_retry"
    )
    if active_cold_retry is not None:
        # Migration 149 stage 1: serving the detail for an item carrying an
        # active cold-retry task IS the administration open — record the
        # coldness snapshot (window state, surface eligibility, selection
        # basis, render-time exposure scan). Idempotent per task, and a
        # bookkeeping failure must never block the serve.
        try:
            from learnloop.services.coldness_receipt import (
                record_administration_snapshot,
            )

            record_administration_snapshot(
                vault, repository, task=active_cold_retry
            )
        except Exception:  # pragma: no cover - serve must not fail on receipts
            import logging

            logging.getLogger(__name__).warning(
                "coldness administration snapshot failed for %s",
                item.id,
                exc_info=True,
            )
    active_certification_probe = repository.active_followup_task_for_item(
        item.id, kind="certification_cold_probe"
    )
    if active_certification_probe is not None:
        try:
            from learnloop.services.coldness_receipt import (
                record_certification_administration_snapshot,
            )

            record_certification_administration_snapshot(
                vault, repository, task=active_certification_probe
            )
        except Exception:  # pragma: no cover - serve must not fail on receipts
            import logging

            logging.getLogger(__name__).warning(
                "certification coldness administration snapshot failed for %s",
                item.id,
                exc_info=True,
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
            "teach_back_source": (
                item.teach_back_source.model_dump(mode="json")
                if item.teach_back_source is not None
                else None
            ),
            "evidence_facets": item.evidence_facets,
            "evidence_weights": item.evidence_weights,
            "prompt": item.prompt,
            # The shared §3.A2/§3.A3 presentation payload. `prompt` above stays
            # for the surfaces that legitimately want only the question text
            # (the inspector's one-line preview, retire dialogs, card controls);
            # anything ASKING the learner to answer must render `presentation`,
            # which carries the prompt as one of its blocks.
            "presentation": item_presentation(item),
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
            "source_refs": [
                source_ref_display_dto(vault, repository, source_ref)
                for source_ref in item.provenance.source_refs
            ],
            "state": practice_item_state_dto(repository, item.id),
            "mastery": mastery_dto(repository, learning_object.id, vault),
            "scheduler": scheduler_explanation_dto(scheduler) if scheduler is not None else None,
            "attempts": practice_item_attempts(repository, item.id, max_points),
            "assessment_contract_version_id": assessment_contract_version_id,
            # Which delayed follow-up lane (if any) this item currently serves.
            # A `cold_retry` / `certification_cold_probe` must be answered
            # unassisted and unprimed (apply_attempt hard-rejects otherwise), so
            # the practice surface needs to WARN before the learner burns the
            # one measurement on a hint.
            "active_followup_kind": (
                active_cold_retry.get("kind")
                if active_cold_retry is not None
                else (
                    active_certification_probe.get("kind")
                    if active_certification_probe is not None
                    else None
                )
            ),
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
    prerequisite_concepts = [
        {**concept_reference_dto(vault, value), "source": "authored"}
        for value in learning_object.prerequisites
    ]
    confusable_concepts = _learning_object_confusable_concepts(vault, repository, learning_object_id)
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
            "prerequisite_concepts": prerequisite_concepts,
            "confusable_concepts": confusable_concepts,
            "difficulty_prior": learning_object.difficulty_prior,
            "tags": learning_object.tags,
            "mastery": mastery_dto(repository, learning_object.id, vault),
            # Raw on-disk requirement recipes (§7.2) so the recipe-tree editor can
            # seed and round-trip the exact all_of/any_of/integration/modality
            # structure; to_camel camelCases the keys (all_of -> allOf).
            "blueprints": list(learning_object.blueprints),
        }
    )


def _learning_object_confusable_concepts(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
) -> list[dict[str, Any]]:
    learning_object = vault.learning_objects[learning_object_id]
    rows = [
        {**concept_reference_dto(vault, value), "source": "authored"}
        for value in learning_object.confusables
    ]
    by_concept_id = {
        str(row["concept_id"]): row
        for row in rows
        if row["resolved"] and row["concept_id"] is not None
    }
    for observed in learner_observed_confusable_concepts(vault, repository, learning_object_id):
        metadata = {
            "probability": observed.probability,
            "prior_probability": observed.prior_probability,
            "evidence_count": observed.evidence_count,
            "last_observed_at": observed.last_observed_at,
        }
        existing = by_concept_id.get(observed.concept_id)
        if existing is not None:
            existing.update(metadata)
            existing["source"] = "authored_and_learner_observed"
            continue
        row = {
            **concept_reference_dto(vault, observed.concept_id),
            **metadata,
            "source": "learner_observed",
        }
        rows.append(row)
        by_concept_id[observed.concept_id] = row
    return rows


def resolve_concept_id(vault: LoadedVault, reference: str) -> str | None:
    """Resolve an exact concept id or an unambiguous title/alias reference."""

    if reference in vault.concepts:
        return reference
    needle = _normalize_concept_reference(reference)
    if not needle:
        return None
    matches: set[str] = set()
    for concept_id, concept in vault.concepts.items():
        values = [concept_id, concept.title, *concept.aliases]
        if any(_normalize_concept_reference(value) == needle for value in values):
            matches.add(concept_id)
    return next(iter(matches)) if len(matches) == 1 else None


def concept_reference_dto(vault: LoadedVault, reference: str) -> dict[str, Any]:
    concept_id = resolve_concept_id(vault, reference)
    concept = vault.concepts.get(concept_id) if concept_id is not None else None
    return {
        "reference": reference,
        "concept_id": concept_id,
        "title": concept.title if concept is not None else reference,
        "resolved": concept is not None,
    }


def concept_detail(vault: LoadedVault, concept_id: str) -> dict[str, Any]:
    concept = vault.concepts.get(concept_id)
    if concept is None:
        raise SidecarError("not_found", f"Concept {concept_id} was not found.")

    relations: list[dict[str, Any]] = []
    for edge in sorted(vault.edges, key=lambda item: (item.relation_type, item.id)):
        if edge.source != concept_id and edge.target != concept_id:
            continue
        other_id = edge.target if edge.source == concept_id else edge.source
        direction = "outgoing" if edge.source == concept_id else "incoming"
        relations.append(
            {
                "id": edge.id,
                "relation_type": edge.relation_type,
                "direction": direction,
                "concept": concept_reference_dto(vault, other_id),
                "strength": edge.strength,
                "rationale": edge.rationale,
            }
        )

    learning_objects = [
        {
            "id": learning_object.id,
            "title": learning_object.title,
            "knowledge_type": learning_object.knowledge_type,
            "status": learning_object.status,
        }
        for learning_object in sorted(vault.learning_objects.values(), key=lambda item: (item.title.lower(), item.id))
        if learning_object.concept == concept_id
    ]
    return to_camel(
        {
            "id": concept_id,
            "title": concept.title,
            "type": concept.type,
            "aliases": concept.aliases,
            "description": concept.description,
            "tags": concept.tags,
            "relations": relations,
            "learning_objects": learning_objects,
        }
    )


def _normalize_concept_reference(value: str) -> str:
    return " ".join(part for part in re.split(r"[^a-z0-9]+", value.lower()) if part)


def attempt_detail(vault: LoadedVault, repository: Repository, attempt_id: str) -> dict[str, Any]:
    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        raise SidecarError("not_found", f"Attempt {attempt_id} was not found.")
    from learnloop.services.causal_attribution import causal_episode_for_attempt

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
            # Debug-only P1 audit surface. The learner-facing feedback bundle
            # receives the narrower claim-checked projection below.
            "causal_episode": causal_episode_for_attempt(repository, attempt_id),
        }
    )


def _cold_check_result(
    vault: LoadedVault, repository: Repository, attempt: dict[str, Any]
) -> dict[str, Any] | None:
    """What the cold check this attempt just spent turned out to say.

    Non-null ONLY when the attempt consumed a ``cold_retry`` task — i.e. it was
    the single unassisted measurement an earlier assisted repair scheduled.
    Everything here is read back from records the submit path already wrote (the
    consumed task, the episode it closed, the ``causal_cold_outcomes`` row and
    the final coldness receipt); nothing is derived, decided or persisted, so
    re-opening feedback cannot change a verdict.

    The verdict is deliberately reported in TWO parts. ``passed`` says whether
    the unassisted answer was right. ``claim`` says what the system is licensed
    to conclude from it, which is not the same thing: a receipt whose episode
    spent more of the answer than its budget has its repair claim downgraded, so
    a correct answer can be recorded and still not confirm the repair. Collapsing
    the two would let assistance quietly buy a confirmation.
    """

    attempt_id = str(attempt["id"])
    try:
        task = repository.consumed_followup_task_for_attempt(
            attempt_id, kind="cold_retry"
        )
        if task is None:
            return None
        task_id = str(task["id"])
        context = task.get("context") or {}
        episode_id = str(task.get("remediation_episode_id") or "")
        episode = repository.remediation_episode(episode_id) if episode_id else None
        outcome_row = repository.causal_cold_outcome_for_task(task_id)
        outcome = str((outcome_row or {}).get("outcome") or "") or None
        receipt = repository.coldness_receipt_for_task_stage(task_id, "final")
        derived = (receipt or {}).get("derived") or {}
        downgraded_reason = derived.get("claim_downgraded_reason") or None
        passed = outcome == "cold_success"
        if outcome is None:
            claim = "unmeasured"
        elif downgraded_reason:
            claim = "downgraded"
        elif passed:
            claim = "repair_confirmed"
        elif outcome == "cold_failure":
            claim = "escalated_unrepaired"
        else:
            # right_censored_expired, contaminated_or_assisted, missing_chain …
            # — the check happened but produced no verdict about the repair.
            claim = "unmeasured"
        case_kind = str(task.get("case_kind") or "")
        case_ref = str(task.get("case_ref") or "")
        summary = None
        if case_kind == "misconception" and case_ref:
            record = repository.misconception(case_ref)
            summary = getattr(record, "statement", None) if record is not None else None
        if not summary:
            learning_object = vault.learning_objects.get(
                str(attempt.get("learning_object_id") or "")
            )
            summary = (
                learning_object.title
                if learning_object is not None
                else (case_ref or "this idea")
            )
        return {
            "passed": passed,
            "outcome": outcome,
            "claim": claim,
            "claim_downgraded_reason": downgraded_reason,
            "case_kind": case_kind or None,
            "case_ref": case_ref or None,
            "case_summary": summary,
            "factor_id": (context.get("causal_factor_id") or None),
            "episode_id": episode_id or None,
            # The span the learner recognizes: the day the assisted repair
            # happened, and the day this check answered for it.
            "instructed_at": str(
                (episode or {}).get("created_at") or task.get("created_at") or ""
            )
            or None,
            "checked_at": str(
                (episode or {}).get("completed_at") or attempt.get("created_at") or ""
            )
            or None,
            "reveal_spend": context.get("reveal_spend"),
            "reveal_budget": context.get("reveal_budget"),
        }
    except Exception:  # pragma: no cover - feedback must never fail on a receipt
        import logging

        logging.getLogger(__name__).warning(
            "cold check result unavailable for attempt %s", attempt_id, exc_info=True
        )
        return None


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
    from learnloop.services.causal_attribution import claim_checked_feedback
    from learnloop.services.guided_redo import guided_redo_available

    causal_feedback = claim_checked_feedback(vault, repository, attempt_id)
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
    # Auto-priming (reveal ledger): recorded on the attempt's debug payload at
    # submit time. Absent -- never zero -- when the ledger did not force it.
    debug_payload = repository.attempt_debug_payload(attempt_id) or {}
    raw_auto_primed = debug_payload.get("auto_primed_reveal_total")
    auto_primed_total = (
        float(raw_auto_primed) if isinstance(raw_auto_primed, (int, float)) else None
    )
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
            "mastery_step": mastery_step_dto(repository, attempt_id, attempt["correctness"]),
            "feedback_md": metadata.get("feedback_md"),
            "feedback_shown_count": metadata.get("shown_count", 0),
            "feedback_first_shown_at": metadata.get("first_shown_at"),
            "feedback_last_shown_at": metadata.get("last_shown_at"),
            "repair_suggestions": metadata.get("repair_suggestions") or [],
            # Server truth for the "redo the part you missed" button: computed
            # with the same rule `start_guided_redo` enforces (the SELECTED
            # repair preserves a prefix), so a visible button cannot fail with
            # `guided_redo_unavailable`. Gating on "any suggestion has a
            # prefix" did exactly that whenever the selection differed.
            "guided_redo_available": guided_redo_available(repository, attempt_id),
            "intervention_need": intervention_need_dto(intervention_need),
            "primed": bool(attempt.get("primed")),
            # `primed` alone cannot tell the learner why: they submitted this as
            # an ordinary attempt and the reveal ledger reclassified it, because
            # tutor answers or repair displays had already covered part of the
            # solution. The total is the audit trail for that reclassification.
            "auto_primed": auto_primed_total is not None,
            "auto_primed_reveal_total": auto_primed_total,
            # Non-null only when this attempt WAS the unassisted check for an
            # earlier assisted repair. Announced after the grade, never before.
            "cold_check_result": _cold_check_result(vault, repository, attempt),
            # Canonical-source sections that spawned this item, for the
            # source-review panel (text section or video timestamp range).
            "source_refs": resolve_source_refs(vault, item, repository),
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
                    "self_report": factor.get("self_report"),
                    "self_report_question": (
                        None
                        if factor.get("self_report") is not None
                        else {
                            "prompt": "What best describes what happened?",
                            "options": [
                                {"id": "slipped", "label": "I knew it and slipped"},
                                {"id": "believed_candidate", "label": "I believed one of these"},
                                {"id": "item_unclear", "label": "The item was unclear"},
                                {"id": "notation_confused", "label": "The notation confused me"},
                                {"id": "other_valid_approach", "label": "I used another valid approach"},
                                {"id": "diagnosis_wrong", "label": "The diagnosis is wrong"},
                            ],
                        }
                    ),
                }
                for factor in repository.unresolved_cause_factors_for_attempt(attempt_id)
            ],
            "matched_misconception": matched_misconception,
            # P1 receipt-checked, claim-typed overlay. The original feedback
            # generation remains unchanged; this is the authority/display gate.
            "causal_feedback": causal_feedback,
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


def mastery_step_dto(
    repository: Repository, attempt_id: str, observed_correctness: float | None
) -> dict[str, Any] | None:
    """Why the posterior moved this far: the observation-weight factor chain.

    Derived from the attempt's persisted debug payload, so it renders for older
    attempts too. ``None`` when the payload is missing or carries no weight --
    the panel then simply omits the strip.
    """

    explanation = explain_mastery_step(
        repository.attempt_debug_payload(attempt_id),
        observed_correctness=observed_correctness,
    )
    if explanation is None:
        return None
    return to_camel(
        {
            "observation_weight": explanation.observation_weight,
            "factors": [
                {
                    "key": factor.key,
                    "label": factor.label,
                    "detail": factor.detail,
                    "multiplier": factor.multiplier,
                }
                for factor in explanation.factors
            ],
            "expected_correctness": explanation.expected_correctness,
            "observed_correctness": explanation.observed_correctness,
            "dominant_factor_key": explanation.dominant_factor_key,
            "at_weight_floor": explanation.at_weight_floor,
            "product_reconciles": explanation.product_reconciles,
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
    """The resolved rubric, criteria dumped WHOLE.

    ``model_dump()`` already carries A1's authored observation contract —
    ``targets`` (facet/capability/role) and ``depends_on`` — and the frontend
    type is what was hiding them. Nothing is filtered here on purpose: a rubric
    the app cannot fully inspect is one whose authored measurement claims can
    only be checked by reading YAML.
    """

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
