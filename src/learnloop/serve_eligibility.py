"""One serve/administration eligibility decision (the "one eligibility decision"
stage, ``docs/reviews/serve-eligibility-decision.md``).

Before this module every serve path asked its own question about the reveal
ledger, and they disagreed. Submit's auto-prime counts a non-routine reveal
(a tutor answer, a repair display, a guided redo, a source re-read) from the
item's last attempt, with no lapse; the scheduler's cold deferral counted the
same kinds only from the cold task's creation, for one cold delay. So a cold
retry created after an old tutor answer was served as the cold check, the
learner wrote an answer, and submit refused it as primed; the task stayed due
and every serve walked into the same refusal until it expired.

Now one pure function, :func:`decide`, answers for every path:

* **submit** (``attempts._resolve_attempt_target``; the CLI asks it before it
  prompts): is this draft admissible, and is it primed;
* **a cold check's serve** (the queue's cold lane, the daily plan's pool,
  reconcile and serve, the pick, the session serve, ``open_queue_item``, the
  TUI's open, the CLI's attempt);
* **a probe or placement presentation** (the probe commit, the TUI's probe,
  the causal offer, a precommitted block);
* **a quick-check offer** (the placement quick check's candidates).

Submit's rule is persisted meaning (it decides whether an attempt counts as
cold), so it is kept exactly (:func:`submit_exposure` reproduces
``Repository.total_reveal_amount`` row for row) and serving agrees with it:
an item submit would prime is never served as a measurement. When the
exposure lapses by time alone (only routine displays, ``reveal_coverage``) the
cold check is deferred until it does; when it does not (a non-routine reveal
since the last attempt, which only an attempt absorbs) the item is served as
ordinary practice with an honest reason and the due cold task is re-timed one
cold delay later, so the practice attempt is accepted and absorbs the
exposure, and the cold check comes back cold. Never left due to expire.

Functional core, imperative shell: :func:`decide` and the helpers above it
are pure (inputs in, a :class:`EligibilityDecision` record out, with a reason
code); :func:`gather` reads the inputs from a repository and :func:`retime`
applies a decision's re-times. Dependency free apart from
``learnloop.reveal_coverage`` (stdlib only), so attempts, scheduling,
diagnosis, the daily plan and the adapters can all import it; ``repository``
is duck-typed (a ``Repository``), never imported.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from learnloop.reveal_coverage import (
    ROUTINE_DISPLAY_COVERAGE,
    is_routine_display,
    routine_covered_from,
    routine_released_at,
    routine_row_covers,
)

logger = logging.getLogger(__name__)

# -- the policy constants (one definition; ``attempts`` re-exports them) ---------------------

#: Summed exposure at or above which submit records an attempt as primed
#: (``attempts.AUTO_PRIME_REVEAL_THRESHOLD``, the reasoning is there).
AUTO_PRIME_REVEAL_THRESHOLD = 0.35

#: The delayed follow-up lanes whose claim is an UNASSISTED attempt
#: (``attempts.COLD_FOLLOWUP_TASK_KINDS``).
COLD_FOLLOWUP_TASK_KINDS: frozenset[str] = frozenset({"cold_retry", "certification_cold_probe"})

#: Reveal kinds written only after the attempt they link
#: (``reveal_ledger.POST_ATTEMPT_REVEAL_KINDS``).
POST_ATTEMPT_REVEAL_KINDS: tuple[str, ...] = ("answer_display",)

#: The cold retrieval delay (``diagnosis.remediation.COLD_RETRIEVAL_DELAY``,
#: pinned equal by a test; not imported, so this module stays a leaf).
COLD_RETRIEVAL_DELAY = timedelta(days=1)

#: When a hold's release cannot be read (an unreadable stamp): held, never
#: lifting on its own clock (fail closed; ``scheduler.COLD_CHECK_HOLD_UNKNOWN_RELEASE``).
UNKNOWN_RELEASE = "9999-12-31T23:59:59Z"

# -- what is asked, and the verdicts ------------------------------------------------------------

#: Submit: is this draft admissible (and is it primed)?
SUBMIT = "submit"
#: Serve the item's open cold follow-up (cold_retry, certification_cold_probe).
COLD_CHECK = "cold_check"
#: Commit (or serve) a probe or placement presentation of the item.
PROBE = "probe"
#: Offer the item in the placement quick check.
QUICK_CHECK = "quick_check"

REQUESTS = (SUBMIT, COLD_CHECK, PROBE, QUICK_CHECK)

SERVE = "serve"
SERVE_AS_ORDINARY = "serve_as_ordinary"
DEFER_UNTIL = "defer_until"
REFUSE = "refuse"

# -- reason codes (the decision record's ``reason``) -------------------------------------------

#: Nothing holds the request back: serve it as asked (at submit: admissible).
ELIGIBLE = "eligible"
#: A cold check was asked for, but no open cold task selects the item.
NO_COLD_CHECK = "no_cold_check"
#: A routine display covers the item or its learning object (or primes it at
#: submit): time alone clears it (``reveal_coverage``). Unchanged code.
COLD_CHECK_ROUTINE_DISPLAY = "cold_check_routine_display"
#: A non-routine reveal on the item or its learning object since the task was
#: created, within one cold delay (the scheduler's own deferral).
COLD_CHECK_REVEALED_SINCE_SCHEDULED = "cold_check_revealed_since_scheduled"
#: Submit would prime the item and no lapse of time clears it (a non-routine
#: reveal since the item's last attempt): served as ordinary practice, the due
#: cold task re-timed one cold delay later.
COLD_CHECK_ANSWER_SHOWN = "cold_check_answer_shown"
#: Submit: a cold check answered with hints, as a hinted attempt, or declared primed.
COLD_CHECK_ASSISTED = "cold_check_assisted"
#: Submit: a cold check whose answer the ledger says was shown (primed).
COLD_CHECK_PRIMED = "cold_check_primed"
#: A probe or placement presentation of an item whose answer was shown
#: (``probe_episodes.PROBE_ITEM_ANSWER_SHOWN``, unchanged code).
PROBE_ITEM_ANSWER_SHOWN = "probe_item_answer_shown"
#: A quick-check offer of an item submit would prime.
QUICK_CHECK_ANSWER_SHOWN = "quick_check_answer_shown"

#: The refusal submit has always raised for a cold check (tests match on it).
COLD_CHECK_REFUSAL = "a cold retry must be unassisted and unprimed"


# -- inputs -------------------------------------------------------------------------------------


@dataclass(frozen=True)
class RevealRow:
    """One ``reveal_events`` row (every column the decision reads)."""

    id: str
    practice_item_id: str
    learning_object_id: str | None
    source_kind: str
    basis: str | None
    amount: float
    created_at: str
    attempt_id: str | None = None

    @property
    def routine(self) -> bool:
        return is_routine_display(self.source_kind, self.basis)

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> RevealRow:
        return cls(
            id=str(row.get("id") or ""),
            practice_item_id=str(row.get("practice_item_id") or ""),
            learning_object_id=(str(row["learning_object_id"]) if row.get("learning_object_id") else None),
            source_kind=str(row.get("source_kind") or ""),
            basis=row.get("basis") if isinstance(row.get("basis"), str) else None,
            amount=float(row.get("amount") or 0.0),
            created_at=str(row.get("created_at") or ""),
            attempt_id=(str(row["attempt_id"]) if row.get("attempt_id") else None),
        )


@dataclass(frozen=True)
class FollowupTask:
    """One open (``pending`` or ``served``) follow-up task selecting the item."""

    id: str
    kind: str
    created_at: str
    not_before: str | None
    expires_at: str | None
    case_ref: str | None = None

    @property
    def cold(self) -> bool:
        return self.kind in COLD_FOLLOWUP_TASK_KINDS

    def unexpired(self, at: str) -> bool:
        return not self.expires_at or self.expires_at >= at

    def due(self, at: str) -> bool:
        # SQL's ``not_before <= ?``: a NULL never compares true.
        return self.not_before is not None and self.not_before <= at and self.unexpired(at)

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> FollowupTask:
        return cls(
            id=str(row.get("id") or ""),
            kind=str(row.get("kind") or ""),
            created_at=str(row.get("created_at") or ""),
            not_before=(str(row["not_before"]) if row.get("not_before") else None),
            expires_at=(str(row["expires_at"]) if row.get("expires_at") else None),
            case_ref=(str(row["case_ref"]) if row.get("case_ref") else None),
        )


@dataclass(frozen=True)
class EligibilityInputs:
    """Everything the decision reads, as of one instant.

    ``reveals`` holds the item's rows and its learning object's, at every
    stamp (the decision applies each reader's window itself). ``last_attempt``
    is the item's latest attempt as submit reads it (``(id, created_at)``,
    the latest at or before ``window_until`` when that is set). ``tasks`` are
    the open follow-up tasks of every kind selecting the item, ordered as the
    repository orders them (``not_before, created_at, id``).

    ``window_until`` (Q33): a historical writer (exam seeding, an exam's
    finish, a kept-state sim) bounds its window at its own instant, so a
    reveal stamped after it, and an attempt after it, do not count. None for
    every live caller, where a routine row stamped after the clock (the clock
    went back) still counts (``reveal_coverage``, round 4).
    """

    practice_item_id: str
    learning_object_id: str | None
    at: str
    reveals: tuple[RevealRow, ...] = ()
    last_attempt: tuple[str, str] | None = None
    tasks: tuple[FollowupTask, ...] = ()
    window_until: str | None = None
    #: The submitting draft's own self-grade disclosure rows (exempt, round 5).
    exempt_reveal_ids: frozenset[str] = frozenset()
    #: The draft's own declarations (submit only).
    declared_primed: bool = False
    hints_used: int = 0
    attempt_type: str | None = None


# -- the decision record --------------------------------------------------------------------------


@dataclass(frozen=True)
class EligibilityDecision:
    """What a path may do with the item now, and why (inspectable: callers log
    :meth:`record` where they already record serving decisions)."""

    request: str
    verdict: str
    reason: str
    practice_item_id: str
    at: str
    #: ``defer_until``: the first moment the hold no longer holds (ledger format).
    until: str | None = None
    #: Submit's summed exposure on the item now, and whether it primes.
    reveal_total: float = 0.0
    primed: bool = False
    #: The ledger rows behind the verdict (empty when it serves).
    reveal_event_ids: tuple[str, ...] = ()
    #: The cold task(s) concerned: the one submit answers, or the ones a serve holds.
    task_ids: tuple[str, ...] = ()
    #: ``serve_as_ordinary`` / ``defer_until``: task id -> its new ``not_before``.
    retimes: tuple[tuple[str, str], ...] = ()
    window_until: str | None = None
    #: A plain sentence for a refusal or a label (never jargon).
    message: str | None = None

    @property
    def serves(self) -> bool:
        """Can the path serve the item as it asked?"""

        return self.verdict == SERVE

    def record(self) -> dict[str, Any]:
        return {
            "request": self.request,
            "verdict": self.verdict,
            "reason": self.reason,
            "practice_item_id": self.practice_item_id,
            "at": self.at,
            "until": self.until,
            "reveal_total": round(self.reveal_total, 6),
            "primed": self.primed,
            "reveal_event_ids": list(self.reveal_event_ids),
            "task_ids": list(self.task_ids),
            "retimes": {task_id: not_before for task_id, not_before in self.retimes},
            "window_until": self.window_until,
        }


# -- the pure core ----------------------------------------------------------------------------------


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parsed(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _plus(stamp: str, delta: timedelta) -> str | None:
    moment = _parsed(stamp)
    return _iso(moment + delta) if moment is not None else None


@dataclass(frozen=True)
class SubmitExposure:
    """Submit's reading of the item's exposure at one instant."""

    total: float
    primed_by_ledger: bool
    #: Rows counted (after the exemption), oldest first.
    counted: tuple[RevealRow, ...]
    #: The part no lapse of time clears: non-routine rows since the last attempt.
    standing_total: float
    #: When the ledger stops priming by time alone (routine rows lapse), or
    #: None when it does not prime, or never lapses (standing exposure).
    lapses_at: str | None


def submit_exposure(inputs: EligibilityInputs) -> SubmitExposure:
    """Submit's auto-prime total, exactly as ``Repository.total_reveal_amount``
    computes it in SQL (and ``attempts.reveal_total_for_submission`` subtracts
    the draft's own disclosure), row for row:

    * the item's rows only;
    * a routine display counts by its coverage: stamped at or after
      ``routine_covered_from(until or at)``, whatever attempts came between,
      with no upper bound unless the window is bounded;
    * every other row counts after the last attempt (exclusive), or a
      post-attempt display linked to it in its own second; with no attempt,
      every row;
    * a bounded window (``window_until``) drops every row stamped after it.
    """

    until = inputs.window_until
    covered_from = routine_covered_from(until or inputs.at)
    since, linked = (inputs.last_attempt[1], inputs.last_attempt[0]) if inputs.last_attempt else (None, None)

    def in_window(row: RevealRow) -> bool:
        if since is None:
            return True
        if row.created_at > since:
            return True
        return (
            linked is not None
            and row.attempt_id == linked
            and row.source_kind in POST_ATTEMPT_REVEAL_KINDS
            and row.created_at >= since
        )

    counted: list[RevealRow] = []
    for row in inputs.reveals:
        if row.practice_item_id != inputs.practice_item_id:
            continue
        if until is not None and row.created_at > until:
            continue
        if covered_from is not None and row.routine:
            if row.created_at >= covered_from and row.id not in inputs.exempt_reveal_ids:
                counted.append(row)
        elif in_window(row):
            counted.append(row)
    # Correctly rounded, as SQLite's compensated SUM is: the order rows are
    # read in never moves a total across the threshold.
    total = max(math.fsum(row.amount for row in counted), 0.0)
    standing = [row for row in counted if not (covered_from is not None and row.routine)]
    standing_total = math.fsum(row.amount for row in standing)
    primed = total >= AUTO_PRIME_REVEAL_THRESHOLD
    lapses_at: str | None = None
    if primed and standing_total < AUTO_PRIME_REVEAL_THRESHOLD:
        # Only routine rows keep it primed; they lapse one by one at their
        # release. The first release after which the total is under the
        # threshold is when submit stops priming (an unreadable stamp never
        # releases: fail closed).
        routine = sorted((row for row in counted if row not in standing), key=lambda row: row.created_at)
        remaining = total
        lapses_at = UNKNOWN_RELEASE
        for row in routine:
            released = routine_released_at(row.created_at)
            if released is None:
                break
            remaining -= row.amount
            if remaining < AUTO_PRIME_REVEAL_THRESHOLD:
                lapses_at = released
                break
    return SubmitExposure(
        total=total,
        primed_by_ledger=primed,
        counted=tuple(counted),
        standing_total=standing_total,
        lapses_at=lapses_at,
    )


def active_task(inputs: EligibilityInputs) -> FollowupTask | None:
    """The task submit answers: the first due, unexpired open task of ANY kind
    selecting the item (``Repository.active_followup_task_for_item``, its
    order). Submit's cold guard applies only when that task is a cold one."""

    for task in inputs.tasks:
        if task.due(inputs.at):
            return task
    return None


def cold_task_holds(inputs: EligibilityInputs, task: FollowupTask) -> list[tuple[RevealRow, str, str]]:
    """The serving holds on one cold task now, each ``(row, released_at, reason)``:
    the scheduler's deferral scope, the item or anywhere in its learning object.

    * a non-routine reveal stamped after the task was created (and not after
      now), for one cold delay: reveals before the task were visible to the
      decision that scheduled it;
    * a routine display covering now, whenever stamped, until its coverage ends.
    """

    def in_scope(row: RevealRow) -> bool:
        return row.practice_item_id == inputs.practice_item_id or (
            inputs.learning_object_id is not None and row.learning_object_id == inputs.learning_object_id
        )

    holds: list[tuple[RevealRow, str, str]] = []
    for row in inputs.reveals:
        if not in_scope(row):
            continue
        if inputs.window_until is not None and row.created_at > inputs.window_until:
            continue
        if row.routine:
            if routine_row_covers(row.created_at, inputs.at):
                holds.append((row, routine_released_at(row.created_at) or UNKNOWN_RELEASE, COLD_CHECK_ROUTINE_DISPLAY))
            continue
        # ``reveal_events_for_target(since=created_at or None, until=now)``.
        if (not task.created_at or row.created_at > task.created_at) and row.created_at <= inputs.at:
            released = _plus(row.created_at, COLD_RETRIEVAL_DELAY)
            if released is not None and released > inputs.at:
                holds.append((row, released, COLD_CHECK_REVEALED_SINCE_SCHEDULED))
    return sorted(holds, key=lambda hold: (hold[0].created_at, hold[0].id))


def _ids(rows: Iterable[RevealRow]) -> tuple[str, ...]:
    seen: dict[str, None] = {}
    for row in rows:
        seen.setdefault(row.id, None)
    return tuple(seen)


def _shown(rows: Sequence[RevealRow]) -> str:
    """"its answer was shown (tutor answer at …)" for a refusal."""

    if not rows:
        return "its answer was shown"
    parts = [f"{row.source_kind.replace('_', ' ')} at {row.created_at}" for row in rows[-3:]]
    more = f" and {len(rows) - 3} earlier" if len(rows) > 3 else ""
    return f"its answer was shown ({', '.join(parts)}{more})"


def decide(inputs: EligibilityInputs, request: str) -> EligibilityDecision:
    """THE decision. Pure: the same inputs give the same record."""

    if request not in REQUESTS:
        raise ValueError(f"unknown eligibility request {request!r}")
    exposure = submit_exposure(inputs)
    base = {
        "request": request,
        "practice_item_id": inputs.practice_item_id,
        "at": inputs.at,
        "reveal_total": exposure.total,
        "primed": exposure.primed_by_ledger or inputs.declared_primed,
        "window_until": inputs.window_until,
    }
    if request == SUBMIT:
        return _decide_submit(inputs, exposure, base)
    if request == COLD_CHECK:
        return _decide_cold_check(inputs, exposure, base)
    # A probe, placement presentation or quick-check offer is a measurement
    # of the item alone: never administered on an item submit would prime,
    # nor (probes, the round-6 guard kept) while a routine display covers it.
    covering = [row for row in inputs.reveals
                if row.practice_item_id == inputs.practice_item_id and row.routine
                and (inputs.window_until is None or row.created_at <= inputs.window_until)
                and routine_row_covers(row.created_at, inputs.at)] if request == PROBE else []
    if exposure.primed_by_ledger or covering:
        rows = list(exposure.counted) + [row for row in covering if row not in exposure.counted]
        reason = PROBE_ITEM_ANSWER_SHOWN if request == PROBE else QUICK_CHECK_ANSWER_SHOWN
        return EligibilityDecision(
            **base, verdict=REFUSE, reason=reason, reveal_event_ids=_ids(rows),
            message="You saw this question's answer, so it can't test you yet.",
        )
    return EligibilityDecision(**base, verdict=SERVE, reason=ELIGIBLE)


def _decide_submit(inputs: EligibilityInputs, exposure: SubmitExposure, base: dict[str, Any]) -> EligibilityDecision:
    task = active_task(inputs)
    if task is None or not task.cold:
        return EligibilityDecision(**base, verdict=SERVE, reason=ELIGIBLE, task_ids=(task.id,) if task else ())
    if inputs.declared_primed or inputs.hints_used > 0 or inputs.attempt_type == "hinted_attempt":
        why = (
            "hints were used" if inputs.hints_used > 0
            else "it is a hinted attempt" if inputs.attempt_type == "hinted_attempt"
            else "it was declared primed"
        )
        return EligibilityDecision(
            **base, verdict=REFUSE, reason=COLD_CHECK_ASSISTED, task_ids=(task.id,),
            message=f"{COLD_CHECK_REFUSAL}: {why}",
        )
    if exposure.primed_by_ledger:
        # Every serve path asks the same question first, so a cold check
        # served as one reaches this only when its answer was shown after the
        # serve: the refusal names those rows.
        return EligibilityDecision(
            **base, verdict=REFUSE, reason=COLD_CHECK_PRIMED, task_ids=(task.id,),
            reveal_event_ids=_ids(exposure.counted), until=exposure.lapses_at,
            message=f"{COLD_CHECK_REFUSAL}: {_shown(exposure.counted)}",
        )
    return EligibilityDecision(**base, verdict=SERVE, reason=ELIGIBLE, task_ids=(task.id,))


def _decide_cold_check(inputs: EligibilityInputs, exposure: SubmitExposure, base: dict[str, Any]) -> EligibilityDecision:
    tasks = [task for task in inputs.tasks if task.cold and task.unexpired(inputs.at)]
    if not tasks:
        return EligibilityDecision(**base, verdict=SERVE, reason=NO_COLD_CHECK)
    due = [task for task in tasks if task.due(inputs.at)]
    if exposure.primed_by_ledger and exposure.lapses_at is None:
        # Submit would prime the answer and only an attempt absorbs it. Holding
        # the cold check would starve it until it expires; serving it as one
        # walks into submit's refusal. So the item is ordinary practice now
        # (that attempt absorbs the exposure) and each due cold task is
        # re-timed one cold delay on, when it is cold again.
        retime_to = _plus(inputs.at, COLD_RETRIEVAL_DELAY) or UNKNOWN_RELEASE
        return EligibilityDecision(
            **base, verdict=SERVE_AS_ORDINARY, reason=COLD_CHECK_ANSWER_SHOWN,
            reveal_event_ids=_ids(exposure.counted), task_ids=tuple(task.id for task in due),
            retimes=tuple((task.id, retime_to) for task in due), until=retime_to,
            message="Practice: you've seen this answer, so its check comes a day after you practise it.",
        )
    held: list[tuple[FollowupTask, str]] = []
    rows: list[RevealRow] = []
    reasons: set[str] = set()
    for task in tasks:
        holds = cold_task_holds(inputs, task)
        task_rows = [row for row, _released, _reason in holds]
        releases = [released for _row, released, _reason in holds]
        task_reasons = {reason for _row, _released, reason in holds}
        if exposure.primed_by_ledger and exposure.lapses_at is not None:
            releases.append(exposure.lapses_at)
            task_rows.extend(exposure.counted)
            task_reasons.add(COLD_CHECK_ROUTINE_DISPLAY)
        if not releases:
            continue
        release = max(releases)
        if release <= inputs.at or (task.not_before is not None and task.not_before > release):
            # The hold has lifted, or lifts before the task is due: left alone.
            continue
        held.append((task, release))
        rows.extend(task_rows)
        reasons |= task_reasons
    if not held:
        return EligibilityDecision(**base, verdict=SERVE, reason=ELIGIBLE, task_ids=tuple(task.id for task in due))
    until = max(release for _task, release in held)
    return EligibilityDecision(
        **base, verdict=DEFER_UNTIL,
        reason=COLD_CHECK_ROUTINE_DISPLAY if COLD_CHECK_ROUTINE_DISPLAY in reasons else COLD_CHECK_REVEALED_SINCE_SCHEDULED,
        until=until, reveal_event_ids=_ids(sorted(rows, key=lambda row: (row.created_at, row.id))),
        task_ids=tuple(task.id for task, _release in held),
        # An unreadable stamp holds without a persisted push (fail closed).
        retimes=tuple((task.id, release) for task, release in held if release != UNKNOWN_RELEASE),
        message="Its answer was shown recently, so its check waits until it is cold again.",
    )


# -- the imperative shell ---------------------------------------------------------------------------


def gather(
    repository: Any,
    *,
    practice_item_id: str,
    learning_object_id: str | None,
    at: str,
    window_until: str | None = None,
    own_disclosure: Callable[[Mapping[str, Any]], bool] | None = None,
    declared_primed: bool = False,
    hints_used: int = 0,
    attempt_type: str | None = None,
    reveal_rows: Sequence[Mapping[str, Any]] | None = None,
) -> EligibilityInputs:
    """Read the decision's inputs for one item from ``repository``.

    ``own_disclosure`` marks the submitting draft's own disclosure rows
    (``reveal_ledger.is_own_disclosure``); ``reveal_rows`` lets a batch caller
    pass rows it already read (the quick check reads the ledger once)."""

    rows = (
        reveal_rows
        if reveal_rows is not None
        else repository.reveal_events_for_target(
            practice_item_id=practice_item_id, learning_object_id=learning_object_id,
        )
    )
    reveals = tuple(RevealRow.from_row(row) for row in rows)
    exempt = frozenset(
        str(row.get("id") or "")
        for row in rows
        if own_disclosure is not None
        and str(row.get("practice_item_id") or "") == practice_item_id
        and row.get("source_kind") == "answer_display"
        and own_disclosure(row)
    )
    attempts = repository.list_recent_attempts_by_practice_item(practice_item_id, limit=1, until=window_until)
    last_attempt = (str(attempts[0]["id"]), str(attempts[0]["created_at"])) if attempts else None
    tasks = tuple(FollowupTask.from_row(row) for row in repository.open_followup_tasks_for_item(practice_item_id))
    return EligibilityInputs(
        practice_item_id=practice_item_id,
        learning_object_id=learning_object_id,
        at=at,
        reveals=reveals,
        last_attempt=last_attempt,
        tasks=tasks,
        window_until=window_until,
        exempt_reveal_ids=exempt,
        declared_primed=declared_primed,
        hints_used=int(hints_used or 0),
        attempt_type=attempt_type,
    )


def retime(repository: Any, decision: EligibilityDecision, *, clock: Any = None) -> None:
    """Apply a decision's re-times (monotone pushes of ``not_before``; never
    the expiry, so an episode that keeps being revealed still censors at its
    original end)."""

    for task_id, not_before in decision.retimes:
        repository.defer_followup_task(task_id, not_before=not_before, clock=clock)


def log_decision(decision: EligibilityDecision, *, path: str) -> None:
    """The decision's trace line, at the path that acted on it. Serving
    verdicts other than ``serve`` are info; a serve is debug."""

    level = logging.DEBUG if decision.verdict == SERVE else logging.INFO
    logger.log(level, "eligibility %s at %s: %s", path, decision.at, decision.record())


__all__ = [
    "AUTO_PRIME_REVEAL_THRESHOLD",
    "COLD_CHECK",
    "COLD_FOLLOWUP_TASK_KINDS",
    "COLD_RETRIEVAL_DELAY",
    "DEFER_UNTIL",
    "EligibilityDecision",
    "EligibilityInputs",
    "FollowupTask",
    "PROBE",
    "QUICK_CHECK",
    "REFUSE",
    "RevealRow",
    "ROUTINE_DISPLAY_COVERAGE",
    "SERVE",
    "SERVE_AS_ORDINARY",
    "SUBMIT",
    "active_task",
    "cold_task_holds",
    "decide",
    "gather",
    "log_decision",
    "retime",
    "submit_exposure",
]
