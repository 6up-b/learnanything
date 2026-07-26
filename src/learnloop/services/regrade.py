from __future__ import annotations

from dataclasses import dataclass

from learnloop.ai.client import AIProviderClient
from learnloop.ai.runtime import AIRuntimeReport
from learnloop.clock import Clock, utc_now_iso
from learnloop.codex.client import CodexClient, CodexUnavailable
from learnloop.codex.prompts import GRADING_PROMPT_VERSION
from learnloop.codex.runtime import CodexRuntimeReport
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.agent_runs import finish_agent_run
from learnloop.services.attempts import GradeAttribution
from learnloop.services.grading import (
    GradingValidationError,
    build_grading_context,
    grading_context_hash,
    resolved_rubric,
    validate_codex_grading_proposal,
)
from learnloop.services.error_taxonomy import persist_unknown_error_type_proposals
from learnloop.services.replay import replay_learning_object
from learnloop.services.teach_back import (
    TEACH_BACK_ATTEMPT_TYPE,
    asked_rubric_score,
    core_criteria,
    restrict_grading_context_to_criteria,
)
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
    return _run_deferred_agent_regrades(
        vault,
        repository,
        runtime=runtime,
        client=codex_client,
        missing_client_reason="codex_client_missing",
        grading_source="codex",
        clock=clock,
        limit=limit,
    )


def run_deferred_ai_regrades(
    vault: LoadedVault,
    repository: Repository,
    *,
    runtime: AIRuntimeReport,
    ai_client: AIProviderClient | None,
    limit: int | None = None,
    clock: Clock | None = None,
) -> DeferredRegradeResult:
    return _run_deferred_agent_regrades(
        vault,
        repository,
        runtime=runtime,
        client=ai_client,
        missing_client_reason="ai_client_missing",
        grading_source="ai",
        clock=clock,
        limit=limit,
    )


def _run_deferred_agent_regrades(
    vault: LoadedVault,
    repository: Repository,
    *,
    runtime,
    client: CodexClient | AIProviderClient | None,
    missing_client_reason: str,
    grading_source: str,
    limit: int | None,
    clock: Clock | None,
) -> DeferredRegradeResult:
    if not runtime.ready:
        return DeferredRegradeResult(attempted=0, regraded=0, failed=0, skipped_reason=runtime.status)
    if client is None:
        return DeferredRegradeResult(attempted=0, regraded=0, failed=0, skipped_reason=missing_client_reason)

    attempted = 0
    regraded = 0
    failed = 0
    for attempt in repository.pending_self_grade_regrade_attempts(limit=limit):
        attempted += 1
        try:
            _regrade_attempt(
                vault,
                repository,
                attempt,
                runtime=runtime,
                client=client,
                grading_source=grading_source,
                clock=clock,
            )
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
    runtime,
    client: CodexClient | AIProviderClient,
    grading_source: str,
    clock: Clock | None,
) -> None:
    item = vault.practice_items[attempt["practice_item_id"]]
    learning_object = vault.learning_objects[attempt["learning_object_id"]]
    rubric = resolved_rubric(vault, item)
    old_evidence = repository.fetch_grading_evidence(attempt["id"])
    context = build_grading_context(
        vault,
        item,
        attempt_id=attempt["id"],
        learner_answer_md=attempt.get("learner_answer_md") or "",
    )
    # Teach-back attempts were graded on the ASKED criteria only (the asked
    # set is exactly the criterion ids carrying persisted evidence rows), so a
    # regrade must be restricted the same way — the full rubric would penalize
    # criteria the naive student never asked about and inject unasked-criterion
    # evidence into the replay log.
    graded_criteria = None
    if attempt.get("attempt_type") == TEACH_BACK_ATTEMPT_TYPE:
        evidence_criterion_ids = {row.criterion_id for row in old_evidence}
        graded_criteria = [
            criterion for criterion in rubric.criteria if criterion.id in evidence_criterion_ids
        ]
        if not graded_criteria:
            graded_criteria = core_criteria(rubric)
        context = restrict_grading_context_to_criteria(context, item, rubric, graded_criteria)
    now = utc_now_iso(clock)
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": "grading_regrade",
            **_agent_run_provider_fields(client, runtime),
            "prompt_template": "grading",
            "prompt_version": GRADING_PROMPT_VERSION,
            "input_context_hash": grading_context_hash(context),
            "output_schema": "GradingProposal",
            "started_at": now,
            "status": "running",
        }
    )
    try:
        proposal = client.run_grading_proposal(context)
        validated = validate_codex_grading_proposal(
            proposal,
            attempt_id=attempt["id"],
            item=item,
            vault=vault,
        )
    except Exception as exc:
        finish_agent_run(
            repository, agent_run_id, client,
            status="failed", error_message=str(exc), clock=clock,
        )
        raise

    old_score = int(attempt["rubric_score"] or 0)
    if graded_criteria is not None:
        graded_ids = {criterion.id for criterion in graded_criteria}
        criterion_evidence = [
            evidence for evidence in validated.criterion_evidence if evidence.criterion_id in graded_ids
        ]
        new_score = asked_rubric_score(
            rubric,
            graded_criteria,
            {evidence.criterion_id: evidence.points_awarded for evidence in criterion_evidence},
            list(validated.fatal_errors),
        )
    else:
        criterion_evidence = list(validated.criterion_evidence)
        new_score = validated.rubric_score
    first_new_evidence_id = new_ulid()
    new_evidence_rows = []
    criterion_points = {}
    for index, evidence in enumerate(criterion_evidence):
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

    primary_error_type = (
        max(validated.error_attributions, key=lambda attribution: attribution.severity).error_type
        if validated.error_attributions
        else None
    )
    content_events = []
    if abs(new_score - old_score) >= 2:
        content_events.append(
            {
                "id": new_ulid(),
                "event_type": "regrade_disagreement",
                "subject": attempt.get("subject"),
                "entity_type": "practice_item",
                "entity_id": item.id,
                "origin": grading_source,
                "review_status": "accepted",
                "summary": _disagreement_summary(old_evidence, new_evidence_rows, old_score, new_score),
                "created_at": now,
            }
        )
    repository.insert_regrade_evidence(
        attempt_id=attempt["id"],
        new_evidence_rows=new_evidence_rows,
        superseded_by_evidence_id=first_new_evidence_id,
        # Teach-back originals are tier-3 (AI-graded) rows; supersede them too
        # or the replay log would carry both gradings of the same criteria.
        supersede_tiers=(1, 3) if graded_criteria is not None else (1,),
        clock=clock,
    )
    repository.update_attempt_grade(
        attempt["id"],
        rubric_score=new_score,
        correctness=new_score / max(rubric.max_points, 1),
        grader_confidence=validated.grader_confidence,
        manual_review=_manual_review_reason(validated.manual_review_reason, attempt) is not None,
        manual_review_reason=_manual_review_reason(validated.manual_review_reason, attempt),
        error_type=primary_error_type,
        clock=clock,
    )
    if content_events:
        repository.record_content_events(content_events)
    replay_learning_object(
        vault,
        repository,
        learning_object.id,
        error_attribution_overrides={
            attempt["id"]: [
                GradeAttribution(
                    error_type=attribution.error_type,
                    severity=attribution.severity,
                    evidence=attribution.evidence,
                    is_misconception=attribution.is_misconception,
                    target_evidence_families=list(attribution.target_evidence_families or []),
                )
                for attribution in validated.error_attributions
            ]
        },
    )
    persist_unknown_error_type_proposals(
        vault,
        repository,
        attributions=validated.error_attributions,
        attempt_id=attempt["id"],
        agent_run_id=agent_run_id,
        related_concept_id=learning_object.concept,
        clock=clock,
    )
    finish_agent_run(repository, agent_run_id, client, clock=clock)


def _agent_run_provider_fields(client: CodexClient | AIProviderClient, runtime) -> dict[str, str | None]:
    provider = getattr(client, "provider_name", None) or getattr(runtime, "active_provider", None) or "codex"
    provider_type = getattr(client, "provider_type", None) or getattr(runtime, "provider_type", None)
    model = getattr(client, "model", None) or getattr(runtime, "model", None)
    provider_revision = getattr(runtime, "provider_revision", None) or getattr(runtime, "actual_revision", None)
    fields = {
        "provider": provider,
        "provider_type": provider_type,
        "model": model,
        "provider_revision": provider_revision,
    }
    if provider == "codex" or provider_type == "codex_sdk":
        fields["codex_revision"] = provider_revision
    return fields


def _manual_review_reason(existing: str | None, attempt: dict) -> str | None:
    if existing is not None:
        return existing
    if attempt.get("attempt_type") != "dont_know" and not str(attempt.get("learner_answer_md") or "").strip():
        return "blank_answer"
    return None


def _disagreement_summary(old_evidence, new_evidence_rows, old_score: int, new_score: int) -> str:
    old_ids = ",".join(row.id for row in old_evidence) or "none"
    new_ids = ",".join(str(row["id"]) for row in new_evidence_rows) or "none"
    return f"Deferred regrade changed rubric_score from {old_score} to {new_score}; old evidence {old_ids}; new evidence {new_ids}."
