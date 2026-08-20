from __future__ import annotations

import logging

from dataclasses import dataclass, replace

from learnloop.ai.client import AIProviderClient
from learnloop.ai.runtime import AIRuntimeReport
from learnloop.clock import Clock, utc_now_iso
from learnloop.ai.errors import CodexUnavailable
from learnloop.attempts.ai_contracts import GRADING_PROMPT_VERSION
from learnloop.ai.providers.codex import CodexRuntimeReport
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.ai.runs import finish_agent_run
from learnloop.attempts.attempts import GradeAttribution
from learnloop.attempts.grading import (
    GradingValidationError,
    ValidatedCodexGrade,
    build_grading_context,
    grading_context_hash,
    request_grading_proposal,
    resolved_rubric,
    validate_codex_grading_proposal,
)
from learnloop.diagnosis.error_taxonomy import persist_unknown_error_type_proposals
from learnloop.substrate.replay import replay_learning_object
from learnloop.tutor.teach_back import (
    TEACH_BACK_ATTEMPT_TYPE,
    asked_rubric_score,
    core_criteria,
    restrict_grading_context_to_criteria,
)
from learnloop.vault.models import LoadedVault


LOGGER = logging.getLogger(__name__)


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
    codex_client: AIProviderClient | None,
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
    client: AIProviderClient | None,
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
            regrade_attempt(
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


def regrade_attempt(
    vault: LoadedVault,
    repository: Repository,
    attempt: dict,
    *,
    runtime,
    client: AIProviderClient,
    grading_source: str,
    clock: Clock | None,
    clarification_exchange: dict[str, str] | None = None,
    purpose: str = "grading_regrade",
) -> "ValidatedCodexGrade":
    """Re-grade one attempt, superseding its evidence and replaying the LO.

    ``clarification_exchange`` is Meas §3.A8's resolution path: the question and
    the learner's answer travel in the grading context (and therefore in
    ``grading_context_hash``, so the resolved grade is attributable to the
    exchange that produced it) rather than being spliced into the learner's
    answer text. Everything else about the regrade is unchanged, deliberately —
    A8 resolves a grade through the door that already exists rather than
    building a second grading path whose semantics could drift."""
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
    if clarification_exchange:
        context = replace(context, clarification_exchange=dict(clarification_exchange))
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
            "purpose": purpose,
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
        proposal = request_grading_proposal(client, context)
        validated = validate_codex_grading_proposal(
            proposal,
            attempt_id=attempt["id"],
            item=item,
            vault=vault,
            learner_answer_md=attempt.get("learner_answer_md") or "",
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
        # or the replay log would carry both gradings of the same criteria. A
        # clarification resolution (Meas §3.A8) supersedes for the same reason:
        # the grade it replaces was itself a model grade, and leaving it live
        # would put two gradings of one criterion in the replay log — the
        # provisional one the question existed to fix, and the resolved one.
        supersede_tiers=(
            (1, 3) if graded_criteria is not None or clarification_exchange else (1,)
        ),
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
    # Meas §3.A6/§3.A8: a re-grade reads the same trace and can see facets the
    # first pass missed, and can ask a question the first pass did not. Neither
    # is recorded by the attempt path here (that runs only inside `apply_attempt`),
    # so without these two calls a re-grade's observations vanish and — worse — a
    # re-grade's clarification request stamps `provisional_pending_clarification`
    # on the attempt with no row behind it, leaving a question the learner can
    # never be shown. Both writers are idempotent and swallow their own failures.
    from learnloop.attempts.ai_contracts import GRADING_PROMPT_VERSION as _grading_version
    from learnloop.attempts.clarification import record_clarification

    if validated.exercised_facets:
        try:
            repository.insert_trace_exercised_facets(
                attempt["id"],
                [
                    {
                        "facet_id": observation.facet,
                        "evidence": observation.evidence,
                        "observation_scope": observation.observation_scope,
                        "criterion_id": observation.criterion_id,
                        "agent_run_id": agent_run_id,
                        "grading_prompt_version": _grading_version,
                    }
                    for observation in validated.exercised_facets
                ],
                clock=clock,
            )
        except Exception:  # pragma: no cover - a bonus channel never fails a regrade
            LOGGER.warning(
                "failed to record trace-exercised facets on regrade of %s",
                attempt["id"],
                exc_info=True,
            )
    if validated.clarification:
        try:
            record_clarification(
                repository,
                attempt_id=attempt["id"],
                clarification=validated.clarification,
                agent_run_id=agent_run_id,
                grading_prompt_version=_grading_version,
                clock=clock,
            )
        except Exception:  # pragma: no cover - same discipline
            LOGGER.warning(
                "failed to record clarification on regrade of %s",
                attempt["id"],
                exc_info=True,
            )
    finish_agent_run(repository, agent_run_id, client, clock=clock)
    return validated


def _agent_run_provider_fields(client: AIProviderClient, runtime) -> dict[str, str | None]:
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
