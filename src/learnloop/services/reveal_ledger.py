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
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository

logger = logging.getLogger(__name__)

REVEAL_SOURCE_KINDS = ("tutor_answer", "repair_display", "guided_redo", "source_review")


def reveal_episode_id(repository: Repository, practice_item_id: str | None) -> str | None:
    """The live repair episode an exposure on this item belongs to, if any."""

    if not practice_item_id:
        return None
    try:
        from learnloop.services.remediation import open_episode_for_practice_item

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
) -> ProductionAdmissibility:
    """Admit a learner production unless a reveal preceded it in its window.

    The window is ``(since, produced_at]`` over reveals on this ITEM or anywhere
    in this LEARNING OBJECT — the same OR-widened target the coldness receipt
    scans, because a solution shown on a sibling item of the same LO is material
    exposure too. ``since`` defaults to open-ended: any reveal at all before the
    production contaminates it, which is the fail-closed reading.

    Best-effort by construction. A lookup that fails ADMITS, because refusing
    evidence on the strength of a database error would silently starve the lane
    while looking like a finding.
    """

    if not produced_at or not (practice_item_id or learning_object_id):
        return ProductionAdmissibility(True, None)
    try:
        reveals = repository.reveal_events_for_target(
            practice_item_id=practice_item_id,
            learning_object_id=learning_object_id,
            since=since,
            until=produced_at,
        )
    except Exception:  # pragma: no cover - defensive
        logger.warning(
            "reveal admissibility lookup failed for item %s",
            practice_item_id,
            exc_info=True,
        )
        return ProductionAdmissibility(True, None)
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
