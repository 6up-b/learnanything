"""The cross-channel answer-reveal ledger (migration 154).

Several surfaces can hand a learner part of a graded solution — a tutor answer,
a repair suggestion rendered on the feedback screen, a guided redo, a source
re-read — and before this module each one accounted for that privately or not
at all. The consequence was a real integrity hole: a learner could read the
answer off the feedback screen and the next attempt on the same item was still
recorded as clean unassisted evidence.

Every writer appends one ``reveal_events`` row saying *how much* of the item's
answer was exposed (0..1), by which surface, and which repair episode it
belongs to (when it belongs to one). One reader — the attempt submit path —
sums the ledger over the window since the item's last attempt and forces
``primed`` above ``attempts.AUTO_PRIME_REVEAL_THRESHOLD``.

Two rules hold for every writer here:

- **Best effort.** Ledger bookkeeping never fails the learner's action. A write
  that raises is logged and swallowed; the action it was accounting for still
  completes. Silence is not acceptable, an exception is.
- **Attribution is optional.** ``remediation_episode_id`` is stamped when the
  item is bound to a live repair, and left NULL otherwise. An unattributed
  reveal is still a reveal and still counts against the next attempt.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.repositories import Repository

logger = logging.getLogger(__name__)

REVEAL_SOURCE_KINDS = ("tutor_answer", "repair_display", "guided_redo", "source_review", "answer_display")

#: Kinds written only AFTER the attempt they link (``attempt_id``): the display
#: of that attempt's feedback. Such a row counts against the NEXT attempt even
#: when it is stamped in the linked attempt's own second (timestamps have
#: one-second resolution, and the submit window's lower bound is exclusive).
#: ``answer_display`` (migration 179, mvp-0.13) is the expected answer itself,
#: shown on a feedback screen.
POST_ATTEMPT_REVEAL_KINDS = ("answer_display",)

#: The basis of the full answer the desktop's plain feedback shows (UX Phase 4,
#: Codex review F1), one per exposure (``feedback_full_answer:desktop:<display>``,
#: :func:`record_feedback_answer_display_reveal`), and of the full answer a
#: plain self-grade shows, one per draft retry key
#: (:func:`record_self_grade_disclosure_reveal`).
FEEDBACK_FULL_ANSWER_BASIS = "feedback_full_answer"
SELF_GRADE_DISCLOSURE_BASIS = "self_grade_disclosure"

#: The ROUTINE full-answer displays: the plain surface shows the expected
#: answer on every feedback and every plain self-grade (spec §7.5), not as an
#: exception a learner asked for. An ``answer_display`` row whose basis starts
#: with one of these counts against a later production only within
#: :data:`ROUTINE_ANSWER_DISPLAY_HORIZON`.
ROUTINE_ANSWER_DISPLAY_BASES = (f"{FEEDBACK_FULL_ANSWER_BASIS}:", f"{SELF_GRADE_DISCLOSURE_BASIS}:")

#: How long a routine display counts: the cold retrieval delay
#: (``diagnosis.remediation.COLD_RETRIEVAL_DELAY``, pinned equal by a test; not
#: imported, so this module never loads the diagnosis package at import).
#: Why a horizon (Codex review F1): the two readers here had none. Without
#: one, a display shown on every feedback would prime EVERY later attempt on
#: the item (a review a week later labelled "with help", never certifying)
#: and make every later production on its learning object not independent
#: (probes, placement checks), forever. Every other exposure reader already
#: counts a reveal within this delay: the serving exclusions, the cold-task
#: deferral and the independent-check rule (``instructional.exposure``). A
#: retry or an unaided answer while the answer is fresh is caught; a review
#: after the delay is a retrieval, as it was before the surface showed the
#: answer. Every other reveal keeps its window exactly.
ROUTINE_ANSWER_DISPLAY_HORIZON = timedelta(days=1)

#: How much longer than the horizon a routine display row counts (UX Phase 4,
#: round 3, F1). The screens that show a routine full answer show it only
#: while a committed row stamped at most this long ago exists, and renew it
#: well before (``apps/learnloop-tauri/src/screens/feedback/exposureContract.json``,
#: pinned equal by a test). So a row stamped s counts at every T in
#: [s, s + horizon + grace]: for any moment v the answer was on screen there is
#: a row with s <= v < s + grace, and every read within the horizon after v
#: falls inside that row's coverage, however the screen ended (a crash, a
#: kill, a machine put to sleep) and whatever attempts came between.
ROUTINE_DISPLAY_RENEWAL_GRACE = timedelta(hours=1)
ROUTINE_ANSWER_DISPLAY_COVERAGE = ROUTINE_ANSWER_DISPLAY_HORIZON + ROUTINE_DISPLAY_RENEWAL_GRACE


def is_routine_answer_display(row: Mapping[str, Any]) -> bool:
    """Is this ledger row one of the plain surface's routine full-answer displays?"""

    basis = row.get("basis")
    return (
        row.get("source_kind") == "answer_display"
        and isinstance(basis, str)
        and basis.startswith(ROUTINE_ANSWER_DISPLAY_BASES)
    )


def routine_display_lapsed_before(at: str | None) -> str | None:
    """The instant (ledger timestamp format) before which a routine display no
    longer counts against a production at ``at`` (its coverage,
    :data:`ROUTINE_ANSWER_DISPLAY_COVERAGE`, has ended); None when ``at`` is
    unknown (nothing lapses: fail closed)."""

    try:
        parsed = parse_utc(at) if at else None
    except ValueError:
        return None
    if parsed is None:
        return None
    cutoff = parsed - ROUTINE_ANSWER_DISPLAY_COVERAGE
    return cutoff.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def own_disclosure_bases(submission_id: str | None) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(exact bases, basis prefixes) of the plain self-grade disclosure rows a
    draft under ``submission_id`` wrote: its settle row and every display row
    (``self_grade_disclosure:<retry key>`` and ``…:<retry key>:<display>``).

    They are that draft's own exposure, shown only AFTER its trace was frozen,
    so they never count against the frozen trace's commit (UX Phase 4, round 3
    F1); they count against every other production."""

    if not submission_id:
        return (), ()
    basis = f"{SELF_GRADE_DISCLOSURE_BASIS}:{submission_id}"
    return (basis,), (f"{basis}:",)


def _disclosure_submission(row: Mapping[str, Any]) -> str | None:
    basis = row.get("basis")
    prefix = f"{SELF_GRADE_DISCLOSURE_BASIS}:"
    if row.get("source_kind") != "answer_display" or not isinstance(basis, str) or not basis.startswith(prefix):
        return None
    return basis[len(prefix):].split(":", 1)[0] or None


def _lapsed_routine_display(row: Mapping[str, Any], cutoff: str | None) -> bool:
    if cutoff is None or not is_routine_answer_display(row):
        return False
    try:
        stamped = parse_utc(str(row.get("created_at") or "")) if row.get("created_at") else None
        limit = parse_utc(cutoff)
    except ValueError:
        return False
    return stamped is not None and limit is not None and stamped < limit


def reveal_episode_id(repository: Repository, practice_item_id: str | None) -> str | None:
    """The live repair episode an exposure on this item belongs to, if any."""

    if not practice_item_id:
        return None
    try:
        from learnloop.diagnosis.remediation import open_episode_for_practice_item

        episode = open_episode_for_practice_item(repository, practice_item_id)
    except Exception:  # pragma: no cover - defensive
        logger.warning(
            "reveal episode lookup failed for %s", practice_item_id, exc_info=True
        )
        return None
    return str(episode["id"]) if episode else None


def record_reveal(
    repository: Repository,
    *,
    practice_item_id: str,
    source_kind: str,
    amount: float,
    learning_object_id: str | None = None,
    remediation_episode_id: str | None = None,
    basis: str | None = None,
    question_event_id: str | None = None,
    attempt_id: str | None = None,
    clock: Clock | None = None,
) -> str | None:
    """Append one reveal. Returns the row id, or None if nothing was recorded.

    A non-positive ``amount`` writes nothing: the ledger records exposures, not
    the absence of them, and a zero row would only dilute later aggregates."""

    if amount <= 0:
        return None
    try:
        return repository.insert_reveal_event(
            {
                "practice_item_id": practice_item_id,
                "learning_object_id": learning_object_id,
                "remediation_episode_id": remediation_episode_id,
                "source_kind": source_kind,
                "amount": amount,
                "basis": basis,
                "question_event_id": question_event_id,
                "attempt_id": attempt_id,
            },
            clock=clock,
        )
    except Exception:  # pragma: no cover - bookkeeping never fails the action
        logger.warning(
            "failed to record %s reveal for item %s",
            source_kind,
            practice_item_id,
            exc_info=True,
        )
        return None


@dataclass(frozen=True)
class ProductionAdmissibility:
    """Whether a learner production counts as INDEPENDENT evidence.

    Independence is a different question from correctness and from whether an
    instrument discriminated. A learner who was shown the answer and then
    reproduces it has demonstrated reading; treating that as discriminating
    evidence about their causal state would let a revealed solution close the
    very factor the reveal contaminated.
    """

    admissible: bool
    reason: str | None
    reveal_event_id: str | None = None
    reveal_amount: float = 0.0


def production_admissibility(
    repository: Repository,
    *,
    practice_item_id: str | None,
    learning_object_id: str | None = None,
    produced_at: str | None,
    since: str | None = None,
    strict: bool = False,
) -> ProductionAdmissibility:
    """Admit a learner production unless a reveal preceded it in its window.

    The window is ``(since, produced_at]`` over reveals on this ITEM or anywhere
    in this LEARNING OBJECT — the same OR-widened target the coldness receipt
    scans, because a solution shown on a sibling item of the same LO is material
    exposure too. ``since`` defaults to open-ended: any reveal at all before the
    production contaminates it, which is the fail-closed reading. The one
    exception is a routine full-answer display (:func:`is_routine_answer_display`),
    which counts only within :data:`ROUTINE_ANSWER_DISPLAY_HORIZON` before the
    production.

    Best-effort by construction. A lookup that fails ADMITS, because refusing
    evidence on the strength of a database error would silently starve the lane
    while looking like a finding. Offline research passes ``strict=True`` to
    propagate lookup failures rather than report an unverified cold opportunity.
    """

    if not produced_at or not (practice_item_id or learning_object_id):
        return ProductionAdmissibility(True, None)
    cutoff = routine_display_lapsed_before(produced_at)
    try:
        reveals = repository.reveal_events_for_target(
            practice_item_id=practice_item_id,
            learning_object_id=learning_object_id,
            since=since,
            until=produced_at,
        )
        if since is not None:
            # A routine display counts by its coverage, whatever window the
            # caller reads (round 3 F1): a full answer still on screen when
            # the window opened is as much an exposure as one shown after.
            seen = {str(row.get("id")) for row in reveals}
            reveals = sorted(
                [
                    *reveals,
                    *(
                        row
                        for row in repository.reveal_events_for_target(
                            practice_item_id=practice_item_id,
                            learning_object_id=learning_object_id,
                            until=produced_at,
                        )
                        if is_routine_answer_display(row) and str(row.get("id")) not in seen
                    ),
                ],
                key=lambda row: (str(row.get("created_at") or ""), str(row.get("id") or "")),
            )
        reveals = [
            row
            for row in reveals
            if not _lapsed_routine_display(row, cutoff)
            and not _own_disclosure_of_production(repository, row, practice_item_id, produced_at)
        ]
    except Exception:  # pragma: no cover - defensive
        if strict:
            raise
        logger.warning(
            "reveal admissibility lookup failed for item %s",
            practice_item_id,
            exc_info=True,
        )
        return ProductionAdmissibility(True, None)
    # A routine full-answer display counts only within its coverage (Codex
    # review F1, round 3): an unaided answer while it is fresh is not
    # independent, one after the cold retrieval delay (and the grace the
    # screens renew within) is again.
    if not reveals:
        return ProductionAdmissibility(True, None)
    # Oldest first; the FIRST reveal is the one that broke independence, and
    # naming it makes the finding auditable back to a row instead of a window.
    first = reveals[0]
    total = sum(float(row.get("amount") or 0.0) for row in reveals)
    return ProductionAdmissibility(
        admissible=False,
        reason="post_reveal_not_independent",
        reveal_event_id=str(first.get("id") or "") or None,
        reveal_amount=total,
    )


def _own_disclosure_of_production(
    repository: Repository, row: Mapping[str, Any], practice_item_id: str | None, produced_at: str
) -> bool:
    """Is ``row`` the plain self-grade disclosure of the very production being
    judged: the attempt that committed that draft's frozen trace (same retry
    key, same item, produced at ``produced_at``, not primed)? Its trace was
    written before the key was shown, so its own disclosure never counts
    against it (round 3 F1)."""

    submission_id = _disclosure_submission(row)
    if submission_id is None or not practice_item_id:
        return False
    attempt = repository.practice_attempt_by_submission_id(submission_id)
    return bool(
        attempt is not None
        and str(attempt.get("practice_item_id") or "") == practice_item_id
        and str(attempt.get("created_at") or "") == produced_at
        and not attempt.get("primed")
    )


def repair_display_amounts(
    repair_suggestions: Sequence[Mapping[str, Any]] | None,
) -> list[tuple[str, float]]:
    """(repair id, declared reveal budget) for suggestions that reveal anything.

    ``answer_reveal_budget`` is what a repair lane *declares* it is licensed to
    show. Displaying the suggestion is when that licence is spent, so the budget
    is the honest debit — it was written by the grader that authored the repair,
    on the same 0..1 scale the ledger uses."""

    out: list[tuple[str, float]] = []
    for suggestion in repair_suggestions or []:
        if not isinstance(suggestion, Mapping):
            continue
        try:
            budget = float(suggestion.get("answer_reveal_budget") or 0.0)
        except (TypeError, ValueError):
            continue
        if budget <= 0:
            continue
        out.append((str(suggestion.get("id") or suggestion.get("repair_class_id") or ""), budget))
    return out


def record_repair_display_reveals(
    repository: Repository,
    *,
    attempt_id: str,
    practice_item_id: str | None,
    learning_object_id: str | None = None,
    repair_suggestions: Sequence[Mapping[str, Any]] | None = None,
    clock: Clock | None = None,
) -> int:
    """Debit the ledger for repair suggestions shown on a feedback screen.

    Called on the FIRST open of an attempt's feedback only. Re-reading the same
    suggestions does not reveal anything new, and charging every reopen would
    make an attentive learner look contaminated. Returns the number of rows
    written."""

    if not practice_item_id:
        return 0
    amounts = repair_display_amounts(repair_suggestions)
    if not amounts:
        return 0
    episode_id = reveal_episode_id(repository, practice_item_id)
    written = 0
    for repair_id, budget in amounts:
        row_id = record_reveal(
            repository,
            practice_item_id=practice_item_id,
            learning_object_id=learning_object_id,
            remediation_episode_id=episode_id,
            source_kind="repair_display",
            amount=budget,
            basis=f"repair_display:{repair_id}" if repair_id else "repair_display",
            attempt_id=attempt_id,
            clock=clock,
        )
        if row_id is not None:
            written += 1
    return written


def record_answer_display_reveal(
    repository: Repository,
    *,
    attempt_id: str,
    practice_item_id: str,
    learning_object_id: str | None = None,
    basis: str,
    clock: Clock | None = None,
) -> str | None:
    """Debit the ledger for the full expected answer shown after an attempt.

    Amount 1.0: the expected answer itself was shown. Linked to the committed
    attempt whose feedback showed it, and charged once per attempt and basis:
    the TUI's worked answer after an empty stuck answer (which never lapses)
    and a plain self-grade's committed disclosure. Once per basis, not per
    attempt, so a routine display that lapses never stands in for one that
    does not (Codex re-review F1). The plain feedback screen, which shows the
    answer on every visit, charges each visit instead
    (:func:`record_feedback_answer_display_reveal`). Best effort, like every
    writer here: a failure is logged and the screen still shows the answer.
    """

    try:
        if any(
            row.get("basis") == basis
            for row in repository.reveal_events(attempt_id=attempt_id, source_kind="answer_display")
        ):
            return None
    except Exception:  # pragma: no cover - defensive
        logger.warning("answer-display reveal lookup failed for %s", attempt_id, exc_info=True)
        return None
    return record_reveal(
        repository,
        practice_item_id=practice_item_id,
        learning_object_id=learning_object_id,
        remediation_episode_id=reveal_episode_id(repository, practice_item_id),
        source_kind="answer_display",
        amount=1.0,
        basis=basis,
        attempt_id=attempt_id,
        clock=clock,
    )


@dataclass(frozen=True)
class DisplayReceipt:
    """A routine display row the ledger holds: its id, its stamp (ledger
    format), and whether it was already there (a retry of the same display)."""

    row_id: str
    recorded_at: str
    already_recorded: bool


class DisplayNotRecorded(Exception):
    """The display row could not be written: the screen must not show the
    answer on its strength, and retries under the same display id."""


def _record_routine_display(
    repository: Repository,
    *,
    basis: str,
    practice_item_id: str,
    learning_object_id: str | None,
    attempt_id: str | None,
    clock: Clock | None,
) -> DisplayReceipt:
    """Write one routine display row, or find it already written; raise
    :class:`DisplayNotRecorded` on any failure (round 3 F1).

    Unlike the best-effort writers above, the screen gates the full answer on
    this row (it shows the answer only while a committed row covers it), so
    a failure is reported, never swallowed: an acknowledgement means a row
    is in the ledger. Idempotent per basis, which names the display."""

    try:
        rows = (
            repository.reveal_events(attempt_id=attempt_id, source_kind="answer_display")
            if attempt_id
            else repository.reveal_events(practice_item_id=practice_item_id, source_kind="answer_display")
        )
        existing = next((row for row in rows if row.get("basis") == basis), None)
        if existing is not None:
            return DisplayReceipt(str(existing["id"]), str(existing["created_at"]), True)
        created_at = utc_now_iso(clock)
        row_id = repository.insert_reveal_event(
            {
                "practice_item_id": practice_item_id,
                "learning_object_id": learning_object_id,
                "remediation_episode_id": reveal_episode_id(repository, practice_item_id),
                "source_kind": "answer_display",
                "amount": 1.0,
                "basis": basis,
                "attempt_id": attempt_id,
                "created_at": created_at,
            },
            clock=clock,
        )
    except Exception as exc:  # noqa: BLE001 - reported, never swallowed
        logger.warning("routine display %s was not recorded for item %s", basis, practice_item_id, exc_info=True)
        raise DisplayNotRecorded(basis) from exc
    return DisplayReceipt(str(row_id), created_at, False)


def record_feedback_answer_display_reveal(
    repository: Repository,
    *,
    attempt_id: str,
    practice_item_id: str,
    display_id: str,
    learning_object_id: str | None = None,
    surface: str = "desktop",
    clock: Clock | None = None,
) -> DisplayReceipt:
    """Record one display of the full answer on a feedback screen.

    The plain surface's feedback shows the expected answer on every visit, and
    it shows it only while a committed row covers it (round 3 F1): the desktop
    writes a row under a new ``display_id`` before the answer first appears,
    whenever it comes back after its row's grace ran out, and at least every
    renewal interval while it stays on screen and in use
    (``apps/learnloop-tauri/src/screens/feedback/answerExposure.ts``). Each
    row counts within :data:`ROUTINE_ANSWER_DISPLAY_COVERAGE` of its stamp. A
    retry of the same display returns the row already written. Linked to the
    attempt, like every feedback display: it counts against the NEXT attempt.
    Raises :class:`DisplayNotRecorded` when nothing could be written.
    """

    return _record_routine_display(
        repository,
        basis=f"{FEEDBACK_FULL_ANSWER_BASIS}:{surface}:{display_id}",
        practice_item_id=practice_item_id,
        learning_object_id=learning_object_id,
        attempt_id=attempt_id,
        clock=clock,
    )


def record_self_grade_disclosure_display(
    repository: Repository,
    *,
    practice_item_id: str,
    submission_id: str,
    display_id: str,
    learning_object_id: str | None = None,
    clock: Clock | None = None,
) -> DisplayReceipt:
    """Record one display of the key on a pending plain self-grade (round 3 F1).

    Written while the draft is still pending, so every other production (an
    attempt in another window, an unaided answer on the learning object) is
    judged against it at once. The frozen trace's own commit is exempt
    (:func:`own_disclosure_bases`): it was written before the key appeared.
    Unlinked (the draft has no attempt yet); idempotent per display; raises
    :class:`DisplayNotRecorded` when nothing could be written.
    """

    return _record_routine_display(
        repository,
        basis=f"{SELF_GRADE_DISCLOSURE_BASIS}:{submission_id}:{display_id}",
        practice_item_id=practice_item_id,
        learning_object_id=learning_object_id,
        attempt_id=None,
        clock=clock,
    )


def record_self_grade_disclosure_reveal(
    repository: Repository,
    *,
    practice_item_id: str,
    submission_id: str,
    learning_object_id: str | None = None,
    attempt_id: str | None = None,
    clock: Clock | None = None,
) -> str | None:
    """Debit the ledger for the full answer a plain self-grade showed.

    The desktop's plain self-grade shows the expected answer beside the
    learner's answer, and only after that whole trace was frozen in the
    session checkpoint (so the answer it grades was written before the answer
    was seen). The exposure is settled when the frozen draft is done with:

    * committed (``attempt_id``): the attempt that answered it links the row
      (:func:`record_answer_display_reveal`, once per retry key), as the
      feedback screen links its displays: it counts against the NEXT
      attempt, never against the trace frozen before it;
    * abandoned (no attempt under its retry key): an unlinked row stamped now,
      so a later attempt on the item, and a later production on the item or
      its learning object, was produced after the answer was seen.

    Either way it is a routine display (:data:`ROUTINE_ANSWER_DISPLAY_BASES`):
    it counts within the cold retrieval delay. Idempotent per retry key; best
    effort, like every writer here.
    """

    basis = f"{SELF_GRADE_DISCLOSURE_BASIS}:{submission_id}"
    if attempt_id:
        return record_answer_display_reveal(
            repository,
            attempt_id=attempt_id,
            practice_item_id=practice_item_id,
            learning_object_id=learning_object_id,
            basis=basis,
            clock=clock,
        )
    try:
        if any(
            row.get("basis") == basis
            for row in repository.reveal_events(practice_item_id=practice_item_id, source_kind="answer_display")
        ):
            return None
    except Exception:  # pragma: no cover - defensive
        logger.warning("self-grade disclosure lookup failed for %s", practice_item_id, exc_info=True)
        return None
    return record_reveal(
        repository,
        practice_item_id=practice_item_id,
        learning_object_id=learning_object_id,
        remediation_episode_id=reveal_episode_id(repository, practice_item_id),
        source_kind="answer_display",
        amount=1.0,
        basis=basis,
        clock=clock,
    )
