from __future__ import annotations

from dataclasses import dataclass

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.codex.client import CodexClient, CodexUnavailable
from learnloop.codex.prompts import GRADING_PROMPT_VERSION
from learnloop.codex.runtime import CodexRuntimeReport
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.grading import (
    GradingValidationError,
    build_grading_context,
    evidence_coverage,
    grading_context_hash,
    validate_codex_grading_proposal,
)
from learnloop.services.mastery import MasteryObservation, initial_mastery_state, update_mastery
from learnloop.vault.models import LoadedVault


@dataclass(frozen=True)
class DeferredRegradeResult:
    attempted: int
    regraded: int
    failed: int
    skipped_reason: str | None = None

    def as_dict(self) -> dict[str, int | str | None]:
        return {
            "attempted": self.attempted,
            "regraded": self.regraded,
            "failed": self.failed,
            "skipped_reason": self.skipped_reason,
        }


def run_deferred_regrades(
    vault: LoadedVault,
    repository: Repository,
    *,
    runtime: CodexRuntimeReport,
    codex_client: CodexClient | None,
    limit: int | None = None,
    clock: Clock | None = None,
) -> DeferredRegradeResult:
    if not runtime.ready:
        return DeferredRegradeResult(attempted=0, regraded=0, failed=0, skipped_reason=runtime.status)
    if codex_client is None:
        return DeferredRegradeResult(attempted=0, regraded=0, failed=0, skipped_reason="codex_client_missing")

    attempted = 0
    regraded = 0
    failed = 0
    for attempt in repository.pending_self_grade_regrade_attempts(limit=limit):
        attempted += 1
        try:
            _regrade_attempt(vault, repository, attempt, runtime=runtime, codex_client=codex_client, clock=clock)
        except (CodexUnavailable, TimeoutError, GradingValidationError, ValueError, KeyError):
            failed += 1
        else:
            regraded += 1
    return DeferredRegradeResult(attempted=attempted, regraded=regraded, failed=failed)


def _regrade_attempt(
    vault: LoadedVault,
    repository: Repository,
    attempt: dict,
    *,
    runtime: CodexRuntimeReport,
    codex_client: CodexClient,
    clock: Clock | None,
) -> None:
    item = vault.practice_items[attempt["practice_item_id"]]
    learning_object = vault.learning_objects[attempt["learning_object_id"]]
    context = build_grading_context(
        vault,
        item,
        attempt_id=attempt["id"],
        learner_answer_md=attempt.get("learner_answer_md") or "",
    )
    now = utc_now_iso(clock)
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": "grading_regrade",
            "provider": "codex",
            "prompt_template": "grading",
            "prompt_version": GRADING_PROMPT_VERSION,
            "codex_revision": runtime.actual_revision,
            "input_context_hash": grading_context_hash(context),
            "output_schema": "GradingProposal",
            "started_at": now,
            "status": "running",
        }
    )
    try:
        proposal = codex_client.run_grading_proposal(context)
        validated = validate_codex_grading_proposal(
            proposal,
            attempt_id=attempt["id"],
            item=item,
            vault=vault,
        )
    except Exception as exc:
        repository.complete_agent_run(agent_run_id, status="failed", error_message=str(exc), clock=clock)
        raise

    old_evidence = repository.fetch_grading_evidence(attempt["id"])
    old_score = int(attempt["rubric_score"] or 0)
    first_new_evidence_id = new_ulid()
    new_evidence_rows = []
    criterion_points = {}
    for index, evidence in enumerate(validated.criterion_evidence):
        evidence_id = first_new_evidence_id if index == 0 else new_ulid()
        criterion_points[evidence.criterion_id] = evidence.points_awarded
        new_evidence_rows.append(
            {
                "id": evidence_id,
                "criterion_id": evidence.criterion_id,
                "points_awarded": evidence.points_awarded,
                "evidence": evidence.evidence,
                "notes": evidence.notes,
                "agent_run_id": agent_run_id,
                "local_grader_id": None,
                "grader_tier": 3,
                "created_at": now,
            }
        )

    prior_mastery = repository.mastery_state(learning_object.id) or initial_mastery_state(
        learning_object.id,
        vault.config.algorithms.algorithm_version,
        now,
    )
    observed_at = parse_utc(now)
    mastery_observation = MasteryObservation(
        rubric_score=validated.rubric_score,
        max_points=item.grading_rubric.max_points,
        evidence_coverage=evidence_coverage(item, criterion_points),
        hint_dampening=1.0,
        grader_confidence=validated.grader_confidence,
        attempt_type=attempt["attempt_type"],
        observed_at=observed_at,
    )
    posterior_mastery = update_mastery(
        prior_mastery,
        mastery_observation,
        vault.config.mastery,
        vault.config.algorithms.algorithm_version,
    )
    primary_error_type = validated.error_attributions[0].error_type if validated.error_attributions else None
    content_events = []
    if abs(validated.rubric_score - old_score) >= 2:
        content_events.append(
            {
                "id": new_ulid(),
                "event_type": "regrade_disagreement",
                "subject": attempt.get("subject"),
                "entity_type": "practice_item",
                "entity_id": item.id,
                "origin": "codex",
                "review_status": "accepted",
                "summary": _disagreement_summary(old_evidence, new_evidence_rows, old_score, validated.rubric_score),
                "created_at": now,
            }
        )
    repository.record_deferred_regrade(
        attempt_id=attempt["id"],
        new_evidence_rows=new_evidence_rows,
        superseded_by_evidence_id=first_new_evidence_id,
        mastery_state=posterior_mastery,
        attempt_update={
            "rubric_score": validated.rubric_score,
            "correctness": validated.rubric_score / max(item.grading_rubric.max_points, 1),
            "grader_confidence": validated.grader_confidence,
            "manual_review": validated.manual_review_reason is not None,
            "manual_review_reason": validated.manual_review_reason,
            "error_type": primary_error_type,
        },
        content_events=content_events,
        clock=clock,
    )
    repository.complete_agent_run(agent_run_id, status="completed", clock=clock)


def _disagreement_summary(old_evidence, new_evidence_rows, old_score: int, new_score: int) -> str:
    old_ids = ",".join(row.id for row in old_evidence) or "none"
    new_ids = ",".join(str(row["id"]) for row in new_evidence_rows) or "none"
    return f"Deferred regrade changed rubric_score from {old_score} to {new_score}; old evidence {old_ids}; new evidence {new_ids}."
