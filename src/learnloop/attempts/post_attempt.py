"""One post-attempt pipeline for every attempt-recording door.

This module is the single composition. Doors differ only in the ``purpose``
they declare and the arguments they can supply — never in which steps exist:

1. certification cold-probe scheduling (idempotent per certificate);
2. attempt feedback metadata persistence (what the feedback/report surfaces
   read back, and what misconception normalization reads);
3. misconception normalization and resolution, unless the attempt's
   diagnostic block defers it to the block-end hook;
4. intervention/causal follow-up evaluation
   (``followups.evaluate_attempt_intervention_followup``, which also runs the
   re-probe trigger and the P2 causal hooks), committed together with the
   attempt's completion.

Slice 1 M2 (spec §7.2, §11): for a BLIND-graded attempt this is the sync part
only. Normalization and every diagnosis-dependent hook move to the diagnosis
worker; the grade-keyed hooks still run here, and the last sync step,
committed with the completion mark, enqueues the attempt's ``diagnose`` job
(so a resumed completion re-enqueues it idempotently). The submit request
never calls the diagnoser.

Purpose gating decides *timing*, not *existence*: exam-purpose attempts run
every evidence-side step exactly like practice, but the sitting caps how many
queue/need insertions one batch may produce (``run_exam_sitting_pipeline``),
and learner-facing feedback assembly stays deferred to the post-sitting exam
report — this pipeline produces the data; the report renders it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from learnloop.attempts.completion_lock import attempt_completion_lock
from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.followups import (
    FollowupDecision,
    enqueue_post_attempt_diagnosis,
    enqueue_post_attempt_learner_text,
    evaluate_attempt_intervention_followup,
    normalize_and_resolve_attempt,
)
from learnloop.vault.models import LoadedVault

logger = logging.getLogger(__name__)

#: How many queue/need insertions one exam sitting may produce. An exam is a
#: batch; N failures must not force-feed N follow-ups into the next session.
#: Failures beyond the cap still run normalization and the causal hooks — only
#: the insertion arm is withheld, with the typed suppression reason below.
EXAM_SITTING_INTERVENTION_CAP = 3
EXAM_SITTING_CAP_REASON = "exam_sitting_intervention_cap"


class CompletionRouteUnknown(RuntimeError):
    """A pending completion does not record which probe episode it belongs to.

    Completion work saved before that identity was recorded cannot be routed
    without guessing from whichever episode is open now, so it is not resumed.
    """


@dataclass(frozen=True)
class PostAttemptOutcome:
    attempt_id: str
    followup: FollowupDecision | None
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def inserted(self) -> bool:
        """Did the follow-up evaluation insert queue work or mint a need?"""

        decision = self.followup
        if decision is None:
            return False
        return decision.practice_item_id is not None or decision.need_id is not None


def run_post_attempt_pipeline(
    vault: LoadedVault,
    repository: Repository,
    *,
    result: Any,
    purpose: str = "practice",
    session_id: str | None = None,
    self_grade: Any = None,
    ai_client: Any = None,
    available_minutes: int | None = None,
    suppress_insertion_reason: str | None = None,
    clock: Clock | None = None,
) -> PostAttemptOutcome:
    """Complete one applied attempt; a completed attempt is not completed again.

    ``result`` is the :class:`learnloop.attempts.attempts.AttemptResult` the
    door received from grading/apply; the attempt and its saved completion
    work already exist.

    Normalization may call a provider, so it runs outside any transaction:
    holding the write lock across a model call would block every other writer.
    The cross-process completion lock still serializes it, so two processes
    resuming the same attempt cannot both normalize it. The follow-up writes
    and the final diagnostic route commit together with the completion mark.

    Failure semantics: the steps raise (the practice handler treats them as
    part of the submit). Batch doors that must not abort on one attempt wrap
    this call — see :func:`run_exam_sitting_pipeline`.
    """

    with attempt_completion_lock(repository.sqlite_path):
        work = repository.attempt_completion(result.attempt_id)
        if work is not None and work["status"] == "completed":
            return PostAttemptOutcome(result.attempt_id, None, ("already_completed",))
        applied_episode_id = _applied_probe_episode_id(vault, repository, result, work)
        with repository.atomic():
            if work is not None:
                repository.save_attempt_completion(
                    attempt_id=result.attempt_id, submission_id=work["submission_id"],
                    session_id=work["session_id"], practice_item_id=result.practice_item_id,
                    result=result.as_dict(), clock=clock,
                )
            _record_normalization_inputs(
                vault, repository, result=result, self_grade=self_grade, clock=clock,
            )
        applied_episode = (
            repository.probe_episode(applied_episode_id) if applied_episode_id else None
        )
        blind_row = repository.latest_blind_grade_record(result.attempt_id)
        blind = blind_row is not None
        if suppress_insertion_reason is None:
            from learnloop.attempts.proof_check import HELD_FOR_REVIEW_SUPPRESSION, record_held_for_review

            # mvp-0.17 (re-review F9): a grade held for review schedules
            # nothing, follow-ups included, until it is settled.
            if record_held_for_review(blind_row):
                suppress_insertion_reason = HELD_FOR_REVIEW_SUPPRESSION
        deferred = _defers_to_block_end(repository, result, applied_episode)
        if not deferred and not blind:
            normalize_and_resolve_attempt(
                vault, repository, attempt_id=result.attempt_id,
                learning_object_id=result.learning_object_id, ai_client=ai_client,
                clock=clock,
            )
        with repository.atomic():
            decision = evaluate_attempt_intervention_followup(
                vault,
                repository,
                result=result,
                available_minutes=available_minutes,
                session_id=session_id,
                normalization_prepared=True,
                applied_probe_episode_id=applied_episode_id,
                suppress_insertion_reason=suppress_insertion_reason,
                defer_diagnosis_hooks=blind,
                clock=clock,
            )
            if not deferred and (blind or _shadow_diagnosis_enabled(vault)):
                # A diagnostic block still measuring is diagnosed at block end
                # (``probe_blocks``), exactly as it is normalized there today.
                enqueue_post_attempt_diagnosis(vault, repository, attempt_id=result.attempt_id, clock=clock)
            repository.complete_attempt_work(
                result.attempt_id,
                result=result.as_dict(),
                route=probe_route(repository, result, episode_id=applied_episode_id),
                clock=clock,
            )
        # After the completion commits: a non-empty stuck answer is queued
        # for the learner-text gap reading (never fails the attempt).
        enqueue_post_attempt_learner_text(vault, repository, attempt_id=result.attempt_id, clock=clock)
    notes = (suppress_insertion_reason,) if suppress_insertion_reason is not None else ()
    return PostAttemptOutcome(attempt_id=result.attempt_id, followup=decision, notes=notes)


def _shadow_diagnosis_enabled(vault: LoadedVault) -> bool:
    return bool(getattr(getattr(vault.config, "diagnosis", None), "shadow", False))


def _applied_probe_episode_id(
    vault: LoadedVault, repository: Repository, result: Any, work: dict[str, Any] | None
) -> str | None:
    """The probe episode the attempt was applied under.

    Saved completion work records it at apply time. Attempts without completion
    work are completed in the same call that applied them, so the episode open
    now is still that episode. An unanswered opening episode placement ignores
    is no episode for this purpose (owner decision 2026-10-12): the attempt is
    ordinary new material, so its feedback is never deferred to that episode.
    """

    if work is None:
        from learnloop.placement.state import servable_open_episode

        episode = servable_open_episode(vault, repository, result.learning_object_id)
        return episode.id if episode is not None else None
    if not work["applied_episode_recorded"]:
        raise CompletionRouteUnknown(
            f"Completion work for attempt {result.attempt_id} does not record its probe episode."
        )
    return work["applied_probe_episode_id"]


def _record_normalization_inputs(
    vault: LoadedVault,
    repository: Repository,
    *,
    result: Any,
    self_grade: Any,
    clock: Clock | None,
) -> None:
    """Write what normalization and follow-up evaluation read back.

    Normalization reads the feedback metadata (repair suggestions and the
    grading run) when it materializes causal hypotheses; without the row it
    would append a hypothesis version with no grader provenance. Both writes
    are idempotent, so a resumed completion may repeat them.
    """

    from learnloop.goals.certification_cold_probe import (
        schedule_certification_cold_probes,
    )

    schedule_certification_cold_probes(
        vault,
        repository,
        learning_object_id=result.learning_object_id,
        clock=clock,
    )
    persist_attempt_feedback_metadata(repository, result, self_grade, clock=clock)


def _defers_to_block_end(repository: Repository, result: Any, episode: Any) -> bool:
    """Is this a diagnostic submission inside a block that is still measuring?

    The block-end hook normalizes the whole block; normalizing here would
    duplicate its diagnosis.
    """

    if episode is None or episode.status != "in_progress":
        return False
    attempt = repository.fetch_practice_attempt(result.attempt_id) or {}
    return attempt.get("probe_presentation_id") is not None


def probe_route(
    repository: Repository, result: Any, *, episode_id: str | None
) -> dict[str, Any] | None:
    """The learner route for an attempt applied under ``episode_id``.

    Feedback stays deferred while that episode is still measuring and this
    attempt did not close its block.
    """

    episode = repository.probe_episode(episode_id) if episode_id else None
    if episode is None:
        return None
    return {
        "episode_id": episode.id,
        "status": episode.status,
        "feedback_deferred": episode.status == "in_progress" and result.probe_block_end is None,
    }


def persist_attempt_feedback_metadata(
    repository: Repository,
    result: Any,
    self_grade: Any = None,
    *,
    clock: Clock | None = None,
) -> None:
    """Persist the grade's feedback/repair metadata for later surfaces.

    Every door writes the row the feedback screen and the exam report read
    back. ``self_grade`` fills the gaps only when the resolved grade was
    learner-supplied.
    """

    feedback_md = result.feedback_md
    if feedback_md is None and self_grade is not None and result.grading_source == "self":
        feedback_md = self_grade.notes
    fatal_errors = result.fatal_errors
    if not fatal_errors and self_grade is not None and result.grading_source == "self":
        fatal_errors = self_grade.fatal_errors or []
    repository.upsert_attempt_feedback_metadata(
        attempt_id=result.attempt_id,
        grading_source=result.grading_source,
        fallback_reason=result.fallback_reason,
        agent_run_id=result.agent_run_id,
        fatal_errors=fatal_errors,
        feedback_md=feedback_md,
        repair_suggestions=result.repair_suggestions,
        clock=clock,
    )


def run_exam_sitting_pipeline(
    vault: LoadedVault,
    repository: Repository,
    *,
    results: list[Any],
    intervention_cap: int = EXAM_SITTING_INTERVENTION_CAP,
    clock: Clock | None = None,
) -> list[PostAttemptOutcome]:
    """Run the pipeline for every attempt an exam sitting just applied.

    Attempts are processed worst-first (ascending correctness, then attempt id
    for determinism) so the sitting's insertion budget goes to the most severe
    failures. Once ``intervention_cap`` attempts have inserted queue work or
    minted a need, the remaining attempts run with the insertion arm withheld
    under the typed :data:`EXAM_SITTING_CAP_REASON` — their normalization and
    causal hooks still run.

    Per-attempt failures are logged and skipped rather than raised: the
    attempts are already applied and the report must still be produced; a
    bookkeeping failure must not abort ``finish_exam``.
    """

    ranked = sorted(
        results,
        key=lambda r: (
            r.correctness if r.correctness is not None else 1.0,
            r.attempt_id,
        ),
    )
    outcomes: list[PostAttemptOutcome] = []
    inserted = 0
    for result in ranked:
        reason = EXAM_SITTING_CAP_REASON if inserted >= intervention_cap else None
        try:
            outcome = run_post_attempt_pipeline(
                vault,
                repository,
                result=result,
                purpose="exam",
                suppress_insertion_reason=reason,
                clock=clock,
            )
        except Exception:  # noqa: BLE001 - attempts are applied; report must proceed
            logger.warning(
                "exam post-attempt pipeline failed for %s",
                result.attempt_id,
                exc_info=True,
            )
            outcomes.append(
                PostAttemptOutcome(
                    attempt_id=result.attempt_id,
                    followup=None,
                    notes=("pipeline_failed",),
                )
            )
            continue
        if outcome.inserted:
            inserted += 1
        outcomes.append(outcome)
    return outcomes


def committed_submission_result(repository: Repository, submission_id: str | None) -> Any:
    """The saved result of the attempt a submission id already committed.

    None when no attempt carries this submission id, or when the attempt has no
    saved completion work. A caller that finds one must resume its completion
    instead of grading the answer again.
    """

    from learnloop.attempts.attempts import AttemptResult

    if not submission_id:
        return None
    attempt = repository.practice_attempt_by_submission_id(submission_id)
    if attempt is None:
        return None
    work = repository.attempt_completion(attempt["id"])
    if work is None:
        return None
    return AttemptResult.from_dict(work["result"])
