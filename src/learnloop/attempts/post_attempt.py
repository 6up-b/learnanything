"""One post-attempt pipeline for every attempt-recording door.

Three doors record graded attempts — the desktop practice handler
(``learnloop_sidecar/handlers/practice.py``), the CLI ``attempt`` command, and
``exam_session.finish_exam`` — and each used to hand-pick its own subset of the
post-attempt obligations. The subsets drifted: exams ran none of them, so exam
failures — the most certification-relevant failures the system collects —
minted no intervention needs, ran no causal hooks, and scheduled no
certification cold probes (measured on ``fixtures/linear_algebra``: an exam
attempt with a validator-passed repair suggestion produced zero
``intervention_needs`` rows and a causal episode with zero hypotheses).

This module is the single composition. Doors differ only in the ``purpose``
they declare and the arguments they can supply — never in which steps exist:

1. certification cold-probe scheduling (idempotent per certificate);
2. attempt feedback metadata persistence (what the feedback/report surfaces
   read back);
3. intervention/causal follow-up evaluation
   (``followups.evaluate_attempt_intervention_followup``, which also runs
   misconception normalization, the re-probe trigger, and the P2 causal
   hooks).

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

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.followups import (
    FollowupDecision,
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
    """Resume local completion exactly once after any provider normalization.

    The applied attempt and its saved result exist before this function runs.
    Normalization may call a provider and keeps its existing idempotent event
    links; it must never hold the transaction used to publish local completion.
    The follow-up writes and the final diagnostic route commit together.
    """
    work = repository.attempt_completion(result.attempt_id)
    if work is not None and work['status'] == 'completed':
        return PostAttemptOutcome(result.attempt_id, None, ('already_completed',))
    if work is not None:
        repository.save_attempt_completion(
            attempt_id=result.attempt_id, submission_id=work['submission_id'],
            session_id=work['session_id'], practice_item_id=result.practice_item_id,
            result=result.as_dict(), clock=clock,
        )
    attempt = repository.fetch_practice_attempt(result.attempt_id) or {}
    episode = repository.open_probe_episode(result.learning_object_id)
    deferred = (
        episode is not None and episode.status == 'in_progress'
        and attempt.get('probe_presentation_id') is not None
    )
    if not deferred:
        normalize_and_resolve_attempt(
            vault, repository, attempt_id=result.attempt_id,
            learning_object_id=result.learning_object_id, ai_client=ai_client,
            clock=clock,
        )
    with repository.atomic():
        current = repository.attempt_completion(result.attempt_id)
        if current is not None and current['status'] == 'completed':
            return PostAttemptOutcome(result.attempt_id, None, ('already_completed',))
        outcome = _run_post_attempt_pipeline(
            vault, repository, result=result, purpose=purpose, session_id=session_id,
            self_grade=self_grade, available_minutes=available_minutes,
            suppress_insertion_reason=suppress_insertion_reason, clock=clock,
        )
        episode = repository.open_probe_episode(result.learning_object_id)
        route = {
            'episode_id': episode.id, 'status': episode.status,
            'feedback_deferred': episode.status == 'in_progress' and result.probe_block_end is None,
        } if episode is not None else None
        repository.complete_attempt_work(
            result.attempt_id, result=result.as_dict(), route=route, clock=clock,
        )
        return outcome


def _run_post_attempt_pipeline(
    vault: LoadedVault,
    repository: Repository,
    *,
    result: Any,
    purpose: str = "practice",
    session_id: str | None = None,
    self_grade: Any = None,
    available_minutes: int | None = None,
    suppress_insertion_reason: str | None = None,
    clock: Clock | None = None,
) -> PostAttemptOutcome:
    """Run the composed post-attempt steps for one applied attempt.

    ``result`` is the :class:`learnloop.attempts.attempts.AttemptResult` the
    door received from grading/apply. Step order is the practice handler's
    historical order and is load-bearing (metadata must exist before the
    follow-up evaluation logs read it back).

    Failure semantics match the door that historically ran each step: the
    steps raise (the practice handler treated them as part of the submit).
    Batch doors that must not abort on one attempt wrap this call — see
    :func:`run_exam_sitting_pipeline`.
    """

    from learnloop.goals.certification_cold_probe import (
        schedule_certification_cold_probes,
    )

    schedule_certification_cold_probes(
        vault,
        repository,
        learning_object_id=result.learning_object_id,
    )
    persist_attempt_feedback_metadata(repository, result, self_grade, clock=clock)
    decision = evaluate_attempt_intervention_followup(
        vault,
        repository,
        result=result,
        available_minutes=available_minutes,
        session_id=session_id,
        normalization_prepared=True,
        suppress_insertion_reason=suppress_insertion_reason,
        clock=clock,
    )
    notes: tuple[str, ...] = ()
    if suppress_insertion_reason is not None:
        notes = (suppress_insertion_reason,)
    if purpose == "exam":
        # Feedback assembly is deliberately absent here: the exam report is
        # the learner-facing surface, and it reads the metadata persisted
        # above. Nothing mid-sitting may reveal a grade.
        pass
    return PostAttemptOutcome(
        attempt_id=result.attempt_id, followup=decision, notes=notes
    )


def persist_attempt_feedback_metadata(
    repository: Repository,
    result: Any,
    self_grade: Any = None,
    *,
    clock: Clock | None = None,
) -> None:
    """Persist the grade's feedback/repair metadata for later surfaces.

    Moved verbatim from the practice handler so every door writes the same
    row the feedback screen and the exam report read back. ``self_grade``
    fills the gaps only when the resolved grade was learner-supplied.
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
