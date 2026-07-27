"""A8 clarification channel — one question that resolves a hedged grade.

Spec: ``spec_measurement_efficiency_v1.md`` §3.A8, authorized by the
``spec_causal_attribution_v1.md`` §1 principle-8 amendment; implementation plan
item 6.3. Store: migration 142.

**This is not primarily a coverage win.** Three of the six regression shapes in
augmentation §3 B1's eval set — notation typo over valid reasoning, missing
step, correct answer from invalid reasoning — are exactly this uncertainty, and
no amount of machine effort resolves them because *the information is not in the
machine's possession*.

**The epistemic argument.** Today abstaining forfeits the measurement entirely,
so there is standing pressure on the grader to fill in a guess — the disease
P0–P2 exists to cure. If an abstention can be repaired by one question, honest
uncertainty stops costing anything and the over-fill incentive drops at its
source. A8 is a reinforcement of the abstention discipline, not an addition to
it.

**Principle 8 is not weakened.** *Machine-resident* uncertainty — grader
flakiness, a missing item contract, symbolic correctness the CAS could settle,
an unmapped repair class — is still resolved with machine effort, never learner
effort. What A8 buys is *learner-resident* uncertainty, which exists only in the
learner's head. The line is drawn at the licensing check in
``grading._validated_clarification``: a confident grade can never produce a
question, and :func:`clarification_rate` is the standing watch on the boundary
being misdrawn — "a clarification rate above a small fraction of attempts is
evidence of machine-resident uncertainty misclassified as learner-resident, and
must be fixed machine-side."

**Lifecycle**, all four states derived rather than stored (migration 142's
rationale):

``pending`` -> ``answered`` -> the re-grade supersedes the provisional grade, or
``pending`` -> ``timed_out`` -> the provisional grade stands *as the abstention
that triggered it*. That last arm needs no code that writes a grade, and that is
the point: there is no path from "the learner ignored the question" to a filled
-in diagnosis.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.grading import PROVISIONAL_PENDING_CLARIFICATION
from learnloop.vault.models import LoadedVault

#: How long a question stays askable. Long enough to survive a day off, short
#: enough that the grade does not sit provisional forever — a stale question
#: about work the learner no longer remembers doing is worse than no question,
#: because the answer would be a reconstruction rather than a report.
DEFAULT_CLARIFICATION_TTL_HOURS = 48

#: §3.A8's revert criterion: "clarification rate exceeds a small fraction of
#: attempts — that is a grader problem or an item-contract problem masquerading
#: as learner-resident uncertainty, and it must be fixed machine-side per the
#: unamended half of principle 8." The threshold is the tripwire, not a cap: the
#: channel is never throttled by it, because throttling would hide the signal
#: the threshold exists to surface.
CLARIFICATION_RATE_WARN_THRESHOLD = 0.15

#: Below this many graded attempts a rate is noise, and reporting one would be
#: exactly the confident wrongness the program exists to prevent.
CLARIFICATION_RATE_MIN_ATTEMPTS = 20

#: Outcomes that mean the exchange is FINISHED. `regrade_failed` is deliberately
#: absent: it is a recoverable state, not a terminal one, and treating it as
#: terminal is what stranded the learner's answer. `None` (the answer landed, the
#: re-grade has not run) is absent for the same reason.
RESOLVED_OUTCOMES: frozenset[str] = frozenset({"resolved", "abstained"})


@dataclass(frozen=True)
class Clarification:
    """One clarification request, with its derived status."""

    id: str
    attempt_id: str
    criterion_id: str | None
    reason: str
    trigger: str
    question_md: str
    expires_at: str
    created_at: str
    answer_md: str | None = None
    answered_at: str | None = None
    outcome: str | None = None
    resolved_grading_revision: int | None = None

    def status(self, *, now: str) -> str:
        """``pending`` | ``awaiting_regrade`` | ``answered`` | ``timed_out``.

        ``awaiting_regrade`` is the state an earlier version could not
        represent, and its absence was a defect rather than a simplification: the
        learner's answer is persisted BEFORE the re-grade is attempted (the
        answer is the un-backfillable half, the re-grade can always be re-run),
        so a provider outage left a clarification that read ``answered`` with no
        resolved grade behind it. The learner could not resubmit — an answer
        exists — and nothing retried, because every retry route looks for
        *pending* work. The exchange sat complete and unconsumed.

        Deriving the state from the outcome instead of the mere existence of an
        answer is what makes that recoverable: ``awaiting_regrade`` is a queue,
        and :func:`resolve_awaiting_regrades` drains it.
        """

        if self.answer_md is not None:
            return "answered" if self.outcome in RESOLVED_OUTCOMES else "awaiting_regrade"
        return "timed_out" if now > self.expires_at else "pending"

    def as_dict(self, *, now: str) -> dict[str, Any]:
        return {
            "id": self.id,
            "attempt_id": self.attempt_id,
            "criterion_id": self.criterion_id,
            "reason": self.reason,
            "trigger": self.trigger,
            "question_md": self.question_md,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
            "answer_md": self.answer_md,
            "answered_at": self.answered_at,
            "outcome": self.outcome,
            "status": self.status(now=now),
        }


def _row_to_clarification(row: Any) -> Clarification:
    return Clarification(
        id=str(row["id"]),
        attempt_id=str(row["attempt_id"]),
        criterion_id=row["criterion_id"],
        reason=str(row["reason"]),
        trigger=str(row["trigger"]),
        question_md=str(row["question_md"]),
        expires_at=str(row["expires_at"]),
        created_at=str(row["created_at"]),
        answer_md=row["answer_md"] if "answer_md" in row.keys() else None,
        answered_at=row["answered_at"] if "answered_at" in row.keys() else None,
        outcome=row["outcome"] if "outcome" in row.keys() else None,
        resolved_grading_revision=(
            row["resolved_grading_revision"] if "resolved_grading_revision" in row.keys() else None
        ),
    )


def record_clarification(
    repository: Repository,
    *,
    attempt_id: str,
    clarification: dict[str, Any],
    agent_run_id: str | None = None,
    grading_prompt_version: str | None = None,
    ttl_hours: int = DEFAULT_CLARIFICATION_TTL_HOURS,
    clock: Clock | None = None,
) -> str | None:
    """Persist an accepted clarification request; returns its id (or None).

    Returns None when the attempt already carries one — the schema's
    ``UNIQUE(attempt_id)`` is §3.A8's "one question per attempt" bound, and a
    second request is dropped rather than raised because losing a bonus question
    must never take a graded attempt down.
    """

    if not clarification:
        return None
    now = parse_utc(utc_now_iso(clock))
    assert now is not None
    expires_at = (now + timedelta(hours=ttl_hours)).isoformat().replace("+00:00", "Z")
    return repository.insert_grading_clarification(
        {
            "id": new_ulid(),
            "attempt_id": attempt_id,
            "criterion_id": clarification.get("criterion_id"),
            "reason": clarification.get("reason") or "other",
            "trigger": clarification["trigger"],
            "question_md": clarification["question_md"],
            "expires_at": expires_at,
            "agent_run_id": agent_run_id,
            "grading_prompt_version": grading_prompt_version,
        },
        clock=clock,
    )


def pending_clarification(
    repository: Repository, attempt_id: str, *, clock: Clock | None = None
) -> Clarification | None:
    """The attempt's clarification if it is still askable, else None.

    A timed-out question is not returned: the grade it was provisional over now
    stands as the abstention that triggered it, and continuing to show the
    question would invite an answer that can no longer change anything.
    """

    row = repository.grading_clarification_for_attempt(attempt_id)
    if row is None:
        return None
    record = _row_to_clarification(row)
    return record if record.status(now=utc_now_iso(clock)) == "pending" else None


def answer_clarification(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    answer_md: str,
    runtime=None,
    client=None,
    grading_source: str = "codex",
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record the learner's answer and re-grade the attempt with it in hand.

    Order matters and is the opposite of the convenient one: the answer is
    persisted **before** the re-grade is attempted. The answer is the
    un-backfillable half of the exchange (standing constraint 6) and the regrade
    can always be re-run, so a provider outage must lose the second and never
    the first.

    A re-grade that fails leaves ``outcome='regrade_failed'`` — a real,
    observable state that must not be indistinguishable from "never answered".
    The provisional grade stands until it is retried.
    """

    row = repository.grading_clarification_for_attempt(attempt_id)
    if row is None:
        raise ValueError(f"attempt {attempt_id} has no clarification request")
    record = _row_to_clarification(row)
    now = utc_now_iso(clock)
    status = record.status(now=now)
    if record.answer_md is not None:
        # Keyed on the ANSWER, not on the resolved status. A clarification whose
        # re-grade has not run yet is `awaiting_regrade`, and the pending work
        # there is the system's, not the learner's — they already said what they
        # meant. Letting them answer again would suggest their first answer was
        # lost (it is not; it is queued) and the response store is one row per
        # clarification by design.
        raise ValueError(f"clarification {record.id} is already answered")
    if status == "timed_out":
        # Deliberately an error rather than a silent accept: the grade has
        # already resolved to the abstention that triggered the question, and
        # quietly re-opening it would make the timeout arm meaningless.
        raise ValueError(f"clarification {record.id} expired at {record.expires_at}")

    repository.insert_grading_clarification_response(
        {
            "id": new_ulid(),
            "clarification_id": record.id,
            "answer_md": answer_md,
        },
        clock=clock,
    )

    if client is None:
        # The answer is recorded and the clarification is now `awaiting_regrade`,
        # NOT `answered`: no grade has moved, and `resolve_awaiting_regrades`
        # will pick this up when a grader is available again.
        return {
            "clarification_id": record.id,
            "outcome": None,
            "regraded": False,
            "status": "awaiting_regrade",
        }

    from learnloop.services.regrade import _regrade_attempt

    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        raise ValueError(f"attempt {attempt_id} does not exist")
    try:
        validated = _regrade_attempt(
            vault,
            repository,
            dict(attempt),
            runtime=runtime,
            client=client,
            grading_source=grading_source,
            clock=clock,
            clarification_exchange={
                "question_md": record.question_md,
                "answer_md": answer_md,
                "criterion_id": record.criterion_id or "",
                "reason": record.reason,
            },
            purpose="grading_clarification_resolution",
        )
    except Exception as exc:
        repository.stamp_grading_clarification_outcome(
            record.id, outcome="regrade_failed", resolved_grading_revision=None
        )
        return {
            "clarification_id": record.id,
            "outcome": "regrade_failed",
            "regraded": False,
            "error": str(exc),
        }

    # `abstained` is first-class: a learner may answer and the grader may STILL
    # be unable to name a cause. Recording that as unresolved is what stops A8
    # from becoming a machine for manufacturing resolutions.
    still_abstaining = any(
        attribution.resolution_status == "abstained"
        for attribution in validated.error_attributions
    )
    outcome = "abstained" if still_abstaining else "resolved"
    repository.stamp_grading_clarification_outcome(
        record.id,
        outcome=outcome,
        # The revision the regrade actually landed on, read back from the
        # ledger. Migration 142 says a NULL here means "the re-grade has not
        # completed", so writing NULL on the success path would make that
        # distinction unreachable and the column's contract a lie.
        resolved_grading_revision=_latest_grading_revision(repository, attempt_id),
    )
    return {"clarification_id": record.id, "outcome": outcome, "regraded": True}


def _latest_grading_revision(repository: Repository, attempt_id: str) -> int | None:
    """The highest grading revision now live on ``attempt_id``, or None.

    None is honest rather than defensive: legacy and hand-built evidence rows
    carry no revision at all, and inventing a 0 would claim a lineage the ledger
    does not have.
    """

    revisions = [
        row.grading_revision
        for row in repository.fetch_grading_evidence(attempt_id)
        if row.grading_revision is not None
    ]
    return max(revisions) if revisions else None


def resolve_awaiting_regrades(
    vault: LoadedVault,
    repository: Repository,
    *,
    runtime=None,
    client=None,
    grading_source: str = "codex",
    limit: int | None = None,
    clock: Clock | None = None,
) -> list[dict[str, Any]]:
    """Re-drive every clarification whose answer landed but whose re-grade did not.

    The exchange is reconstructed from the STORED question and response, which is
    the whole reason both are persisted separately and immutably (migration 142):
    a retry that had to re-ask the learner would have made the first answer
    worthless, and one that guessed at the question would attribute the resolved
    grade to an exchange that did not happen.

    Runs after the deferred self-grade regrades in ``run_startup_maintenance``,
    on the same principle — grading work that failed for an environmental reason
    is retried when the environment comes back, not abandoned. With no grader
    available it is a no-op that reports the backlog rather than clearing it.

    Idempotent: a clarification whose outcome reaches :data:`RESOLVED_OUTCOMES`
    stops being `awaiting_regrade`, so a second sweep finds nothing.
    """

    if client is None:
        return []
    from learnloop.services.regrade import _regrade_attempt

    now = utc_now_iso(clock)
    results: list[dict[str, Any]] = []
    for row in repository.grading_clarifications_awaiting_regrade(limit=limit):
        record = _row_to_clarification(row)
        if record.status(now=now) != "awaiting_regrade":
            continue
        attempt = repository.fetch_practice_attempt(record.attempt_id)
        if attempt is None:
            results.append({"clarification_id": record.id, "outcome": "attempt_missing"})
            continue
        try:
            validated = _regrade_attempt(
                vault,
                repository,
                dict(attempt),
                runtime=runtime,
                client=client,
                grading_source=grading_source,
                clock=clock,
                clarification_exchange={
                    "question_md": record.question_md,
                    "answer_md": record.answer_md or "",
                    "criterion_id": record.criterion_id or "",
                    "reason": record.reason,
                },
                purpose="grading_clarification_resolution",
            )
        except Exception as exc:  # provider still down, or a bad grade: keep the answer
            results.append(
                {
                    "clarification_id": record.id,
                    "outcome": "regrade_failed",
                    "error": str(exc),
                }
            )
            continue
        still_abstaining = any(
            attribution.resolution_status == "abstained"
            for attribution in validated.error_attributions
        )
        outcome = "abstained" if still_abstaining else "resolved"
        repository.stamp_grading_clarification_outcome(
            record.id,
            outcome=outcome,
            resolved_grading_revision=_latest_grading_revision(
                repository, record.attempt_id
            ),
        )
        results.append({"clarification_id": record.id, "outcome": outcome})
    return results


def expire_clarifications(
    repository: Repository, *, clock: Clock | None = None
) -> list[str]:
    """Clear the provisional grade state on every attempt with no live question.

    Writes no grade. The provisional grade already recorded the hedge or
    abstention that triggered the question, so "times out to the abstention that
    triggered it" is achieved by doing nothing to the grade at all — the only
    thing that changes is that the attempt stops advertising itself as pending a
    clarification, because a question nobody can answer any more is not a review
    obligation.

    **The sweep is keyed on the ATTEMPT, not on the clarification row**, and that
    is load-bearing. Two states reach ``provisional_pending_clarification`` with
    no pending row behind them, and a row-driven sweep sees neither:

    * a **deferred regrade** whose proposal carries a licensed clarification
      request — the validator stamps the review reason, but the regrade path
      never records the request, so no row exists to expire;
    * an **answered** clarification whose resolving regrade re-asked — the
      ``UNIQUE(attempt_id)`` key drops the second request, and the surviving row
      is `answered`, so a row-driven sweep skips it.

    In both the attempt reads "provisional · not final" forever with no question
    to answer. Asking "which attempts advertise a question that is not there"
    covers the timed-out case and both of these, because it is the actual
    invariant: the review state exists to point at a pending question.

    Returns the attempt ids cleared.
    """

    cleared: list[str] = []
    for attempt_id in repository.attempts_pending_clarification_review():
        if pending_clarification(repository, attempt_id, clock=clock) is not None:
            continue  # a live question: the state is still true
        attempt = repository.fetch_practice_attempt(attempt_id)
        if attempt is None:
            continue
        repository.update_attempt_grade(
            attempt_id,
            rubric_score=int(attempt["rubric_score"] or 0),
            correctness=float(attempt["correctness"] or 0.0),
            grader_confidence=float(attempt["grader_confidence"] or 0.0),
            manual_review=False,
            manual_review_reason=None,
            error_type=attempt.get("error_type"),
            clock=clock,
        )
        cleared.append(attempt_id)
    return cleared


def clarification_rate(repository: Repository) -> dict[str, Any]:
    """§3.A8's revert criterion, as a metric with an explicit unavailable arm.

    Denominator is model-graded attempts, not all attempts: a self-graded or
    deterministically graded attempt has no grader that could have asked, so
    including them would dilute the rate toward zero and hide exactly the
    over-asking the criterion watches for.
    """

    counts = repository.clarification_rate_counts()
    graded = int(counts["gradeable_attempts"])
    asked = int(counts["clarifications"])
    if graded < CLARIFICATION_RATE_MIN_ATTEMPTS:
        return {
            "available": False,
            "unavailable_reason": "no_data",
            "gradeable_attempts": graded,
            "clarifications": asked,
            "threshold": CLARIFICATION_RATE_WARN_THRESHOLD,
        }
    rate = asked / graded
    return {
        "available": True,
        "rate": rate,
        "gradeable_attempts": graded,
        "clarifications": asked,
        "answered": int(counts["answered"]),
        "threshold": CLARIFICATION_RATE_WARN_THRESHOLD,
        "over_threshold": rate > CLARIFICATION_RATE_WARN_THRESHOLD,
    }
