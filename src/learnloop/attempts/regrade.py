from __future__ import annotations

import logging

from dataclasses import dataclass, replace

from learnloop.ai.client import AIProviderClient
from learnloop.ai.runtime import AIRuntimeReport
from learnloop.algorithm_versions import SOURCE_REFERENCE_GATE_VERSIONS
from learnloop.clock import Clock, utc_now_iso
from learnloop.ai.errors import CodexUnavailable
from learnloop.ai.providers.codex import CodexRuntimeReport
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_service import bind_replacement_grade
from learnloop.ids import new_ulid
from learnloop.ai.runs import finish_agent_run
from learnloop.attempts.attempts import (
    GradeAttribution,
    assessed_rubric_score,
    unverified_attribution_json,
)
from learnloop.attempts.grading import (
    GradingValidationError,
    ValidatedCodexGrade,
    build_grading_context,
    request_vault_grading_proposal,
    resolved_rubric,
    validate_codex_grading_proposal,
    vault_grading_calibration_identity,
    vault_grading_run_identity,
)
from learnloop.attempts.blind_grading import split_grading_active
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


def _attempt_required_method(repository: Repository, attempt_id: str) -> dict | None:
    """The required method an attempt was graded under (review F1).

    Read from the assessment contract its evidence rows cite (the one frozen
    when the item was presented, or snapshotted when it was first graded;
    superseded rows included, since a regrade's rows need not cite it). An
    attempt without one, or whose contract froze none, never acquires a
    method from the item's current content.
    """

    from learnloop.learner.assessment_contracts import contract_required_method

    evidence = repository.fetch_grading_evidence(attempt_id, include_superseded=True)
    version_id = next(
        (row.assessment_contract_version_id for row in evidence if row.assessment_contract_version_id is not None),
        None,
    )
    if version_id is None:
        return None
    stored = repository.fetch_assessment_contract_version(version_id)
    return contract_required_method(stored.get("contract") if stored is not None else None)


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
    # Slice 1 §4.1/§6.3: every NEW grading execution in a split vault is
    # learner-blind and runs as an isolated turn (review F2). A practice
    # attempt is regraded through the practice door's blind contract: its new
    # grade appends a blind record (superseding the previous one, if any) and
    # queues its diagnosis in the publication transaction, so a joint or
    # self-graded attempt regraded after the upgrade becomes blind-graded
    # (replay reads the mode from that ledger, never from config). An attempt
    # already graded blind keeps its mode even with the kill switch off.
    # Teach-back, like its first grading, uses the non-practice door (blind
    # and isolated in a split vault, no blind record: it is never diagnosed).
    # A joint vault, or the kill switch, regrades jointly exactly as before.
    prior_blind = repository.latest_blind_grade_record(attempt["id"])
    # held-grade-evidence: is the grade this regrade replaces held for review
    # now (THE predicate over the ledger: the latest record AND the current
    # evidence, so an adjudication's release counts)?
    from learnloop.held_grades import attempt_grade_held

    prior_held = prior_blind is not None and attempt_grade_held(repository, attempt["id"])
    blind_plan = None
    if prior_blind is not None or (
        split_grading_active(vault) and attempt.get("attempt_type") != TEACH_BACK_ATTEMPT_TYPE
    ):
        from learnloop.attempts.attempts import _blind_grading_plan

        # mvp-0.13: a stuck answer is regraded under the same stuck rules, so
        # its new blind record carries a fresh reading (the confusion signal
        # follows the current record). Method-explicit items (review F1): the
        # answer is regraded under the required method its assessment
        # contract froze, never one the item gained afterwards.
        blind_plan = _blind_grading_plan(
            vault, item, context, stuck=bool(attempt.get("declared_stuck")),
            required_method=_attempt_required_method(repository, attempt["id"]),
        )
    if blind_plan is None and attempt.get("declared_stuck"):
        # mvp-0.13 (review F3): a joint regrade of a stuck answer re-reads it
        # under the same stuck rules, as its first joint grade did.
        from learnloop.attempts.stuck import stuck_answer_prompt

        context = replace(context, answer_prompt=stuck_answer_prompt())
    if blind_plan is not None:
        identity = {
            "prompt_version": blind_plan.prompt_version,
            "input_context_hash": blind_plan.context_hash,
            "output_schema": "BlindGradingProposal",
        }
    else:
        identity = vault_grading_run_identity(vault, context)
    now = utc_now_iso(clock)
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": purpose,
            **_agent_run_provider_fields(client, runtime),
            "prompt_template": "grading",
            **identity,
            "started_at": now,
            "status": "running",
        }
    )
    blind_record: dict | None = None
    # mvp-0.13 (review F6): a regrade of a stuck answer re-reads it; that
    # reading is a new judgment superseding the attempt's current one.
    stuck_judgment: dict | None = None
    unverified: set[str] = set()
    # The own-route rule held the new grade (nothing assessed, nothing validated).
    held = False
    try:
        if blind_plan is not None:
            from learnloop.attempts.blind_grading import (
                BLIND_GRADER_OUTPUT_SCHEMA_VERSION,
                validate_blind_grading_proposal,
            )
            from learnloop.attempts.grading_support import (
                request_blind_grading_run,
                revalidated_support,
            )

            # mvp-0.20: the own-route rule runs inside the grading run, over
            # the grader's own output (no second call that could fail apart
            # from the grade: a failed regrade writes nothing, so a hold stays).
            run = request_blind_grading_run(client, blind_plan.context, rubric=rubric)
            validated_blind = validate_blind_grading_proposal(
                run.proposal,
                attempt_id=attempt["id"],
                item=item,
                vault=vault,
                learner_answer_md=attempt.get("learner_answer_md") or "",
                rubric=rubric,
            )
            validated = validated_blind.grade
            # held-grade-evidence F1: the shortfall over the grade validation kept.
            run = replace(
                run,
                grading_support=revalidated_support(run.grading_support, validated_blind.as_record(), rubric),
            )
            blind_record = {
                **validated_blind.as_record(),
                "prompt_version": run.prompt_version,
                "practice_item_id": item.id,
                "calibration_prompt_version": blind_plan.calibration_prompt_version,
                "calibration_output_schema_version": BLIND_GRADER_OUTPUT_SCHEMA_VERSION,
                "samples": run.samples,
                "grading_support": dict(run.grading_support),
                "regrade": True,
            }
            if run.stuck_reading is not None:
                from learnloop.attempts.stuck import STUCK_READING_KEY, verified_stuck_reading

                blind_record[STUCK_READING_KEY] = verified_stuck_reading(
                    run.stuck_reading, attempt.get("learner_answer_md") or ""
                )
                stuck_judgment = {
                    "marker": blind_record[STUCK_READING_KEY],
                    "prompt_version": run.prompt_version,
                    "input_hash": blind_plan.context_hash,
                }
            # PF-c: a criterion the gate recorded unverified is unassessed
            # (owner decision 2026-10-12), exactly as on the live grade: its
            # row is stamped with the block, the grade excludes it below, and
            # replay leaves it out of the facet evidence. The informational
            # reason is recorded only as the grade's sole concern (review F7).
            unverified = {str(value) for value in run.grading_support.get("unverified_criterion_ids") or ()}
            from learnloop.outcome_contract import grade_held_for_review

            # The new blind record carries it, so the replay below keeps (or
            # releases) the hold exactly as this grade decided.
            held = grade_held_for_review(run.grading_support)
            if run.grading_support.get("valid_alternative_gate_applied"):
                from learnloop.attempts.grading_support import gated_review_reason

                validated = replace(
                    validated,
                    manual_review_reason=gated_review_reason(
                        run,
                        attempt_id=attempt["id"],
                        item=item,
                        vault=vault,
                        learner_answer_md=attempt.get("learner_answer_md") or "",
                        rubric=rubric,
                    ),
                )
        else:
            proposal = request_vault_grading_proposal(vault, client, context)
            from learnloop.attempts.ai_contracts import StuckGradingProposal, grading_prompt_version

            if isinstance(proposal, StuckGradingProposal):
                from learnloop.attempts.grading import grading_context_hash
                from learnloop.attempts.stuck import verified_stuck_reading

                stuck_judgment = {
                    "marker": verified_stuck_reading(
                        proposal.stuck_reading, attempt.get("learner_answer_md") or ""
                    ),
                    "prompt_version": grading_prompt_version(context),
                    "input_hash": grading_context_hash(context),
                }
                proposal = proposal.as_grading_proposal()
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
        if unverified:
            new_score = assessed_rubric_score(
                rubric,
                {evidence.criterion_id: evidence.points_awarded for evidence in criterion_evidence},
                validated.fatal_errors,
                unassessed_criterion_ids=unverified,
                answer_validated=not held,
            )
            validated = replace(validated, rubric_score=new_score)
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
                **(
                    {"attribution_json": unverified_attribution_json()}
                    if evidence.criterion_id in unverified
                    else {}
                ),
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
    try:
        # One publication (review F4): the grading revision, the attempt's
        # grade, the superseding blind record (which retires the old
        # diagnosis and queues the re-diagnosis in the same transaction) and
        # the replayed projection commit together or not at all. The blind
        # record goes in BEFORE replay, so replay already reads the new grade
        # and no stale explanation is in force while it runs.
        with repository.atomic():
            _publish_regrade(
                vault,
                repository,
                attempt,
                item=item,
                learning_object=learning_object,
                validated=validated,
                agent_run_id=agent_run_id,
                new_evidence_rows=new_evidence_rows,
                first_new_evidence_id=first_new_evidence_id,
                # held-grade-evidence F4: a regrade of a held grade (release
                # or kept hold) supersedes its AI-graded rows too, so no
                # stale unassessed row outlives the grade that replaced it in
                # any projection. Review F1: so does a regrade INTO a hold:
                # the assessed rows of the grade it replaces would otherwise
                # stay live, the ledger would read the attempt as assessed
                # (not held) while replay holds it, and the ledger's readers
                # would take the held grade's provisional score.
                supersede_tiers=(
                    (1, 3)
                    if graded_criteria is not None or clarification_exchange or prior_held or held
                    else (1,)
                ),
                new_score=new_score,
                rubric=rubric,
                primary_error_type=primary_error_type,
                content_events=content_events,
                blind_record=blind_record,
                prior_blind=prior_blind,
                blind_context_hash=blind_plan.context_hash if blind_plan is not None else None,
                # Review F11: a regrade outside the practice door (teach-back)
                # writes no blind record; its replay takes the identity of the
                # grade it just produced, and stamps it for later rebuilds.
                grader_identity_overrides=(
                    None
                    if blind_plan is not None
                    else {attempt["id"]: vault_grading_calibration_identity(vault)}
                ),
                clock=clock,
            )
            from learnloop.attempts.grading_support import record_route_rule_judgment

            # mvp-0.20 (review F4): the regrade's route verdict supersedes
            # the attempt's current one, in the publication transaction.
            # Review F5: every successful regrade calls it, blind or joint, so
            # a grade the rule did not run over (kill switch, PF-c off, a
            # joint grade) supersedes a current verdict as not checked.
            record_route_rule_judgment(
                repository.connection(),
                attempt_id=attempt["id"],
                grading_support=(blind_record or {}).get("grading_support") or {},
                judge_model=getattr(client, "model", None) or getattr(client, "model_id", None),
                prompt_version=(
                    str(blind_record["prompt_version"]) if blind_record is not None else identity["prompt_version"]
                ),
                input_hash=blind_plan.context_hash if blind_plan is not None else identity["input_context_hash"],
                created_at=now,
            )
            if stuck_judgment is not None:
                from learnloop.attempts.stuck import record_stuck_reading_judgment

                record_stuck_reading_judgment(
                    repository.connection(),
                    attempt_id=attempt["id"],
                    judge_model=getattr(client, "model", None) or getattr(client, "model_id", None),
                    created_at=now,
                    **stuck_judgment,
                )
    except Exception as exc:
        finish_agent_run(
            repository, agent_run_id, client,
            status="failed", error_message=str(exc), clock=clock,
        )
        raise
    finish_agent_run(repository, agent_run_id, client, clock=clock)
    return validated


def _publish_regrade(
    vault: LoadedVault,
    repository: Repository,
    attempt: dict,
    *,
    item,
    learning_object,
    validated: ValidatedCodexGrade,
    agent_run_id: str,
    new_evidence_rows: list[dict],
    first_new_evidence_id: str,
    supersede_tiers: tuple[int, ...],
    new_score: int,
    rubric,
    primary_error_type: str | None,
    content_events: list[dict],
    blind_record: dict | None,
    prior_blind: dict | None,
    blind_context_hash: str | None,
    grader_identity_overrides: dict[str, tuple[str, str] | None] | None,
    clock: Clock | None,
) -> None:
    """Every write of one regrade, in order, inside the caller's transaction."""

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
        supersede_tiers=supersede_tiers,
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
    # C3 (canonical sources §7.3a): the new grade was read against the item as
    # it is now. If that content's key is not verified, the grade certifies
    # nothing; the attempt's status is lowered (never raised) before the replay
    # below reads it.
    bind_replacement_grade(
        repository.connection(),
        attempt_id=attempt["id"],
        item=item,
        gated=vault.config.algorithms.algorithm_version in SOURCE_REFERENCE_GATE_VERSIONS,
        grading="regrade",
        created_at=utc_now_iso(clock),
    )
    if content_events:
        repository.record_content_events(content_events)
    if blind_record is not None and blind_context_hash is not None:
        from learnloop.attempts.blind_grading import BLIND_GRADER_OUTPUT_SCHEMA_VERSION

        # The old diagnosis explained the old grade; it stays a valid ledger
        # row. The record queues the attempt's (re-)diagnosis in this
        # transaction (the store does it), and a re-diagnosis of the new grade
        # supersedes the old one. A first blind record (a joint or
        # self-graded attempt regraded in a split vault) queues its first.
        repository.insert_blind_grade_record(
            attempt_id=attempt["id"],
            agent_run_id=agent_run_id,
            grading_prompt_version=str(blind_record["prompt_version"]),
            output_schema_version=BLIND_GRADER_OUTPUT_SCHEMA_VERSION,
            context_hash=blind_context_hash,
            record=blind_record,
            supersedes_id=str(prior_blind["id"]) if prior_blind is not None else None,
            queue_diagnosis=True,
            clock=clock,
        )
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
        grader_identity_overrides=grader_identity_overrides,
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
    if (
        attempt.get("attempt_type") != "dont_know"
        and not attempt.get("declared_stuck")
        and not str(attempt.get("learner_answer_md") or "").strip()
    ):
        return "blank_answer"
    return None


def _disagreement_summary(old_evidence, new_evidence_rows, old_score: int, new_score: int) -> str:
    old_ids = ",".join(row.id for row in old_evidence) or "none"
    new_ids = ",".join(str(row["id"]) for row in new_evidence_rows) or "none"
    return f"Deferred regrade changed rubric_score from {old_score} to {new_score}; old evidence {old_ids}; new evidence {new_ids}."
