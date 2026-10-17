"""Reader workbench RW1b: active reading's acts that write more than the question row
(spec_reader_workbench_v1 §4.2).

* **A missed answer is learner text** (W1 tier 2). A next-step, why-step or
  assumption answer the learner marks *partly* or *no* is queued for
  learner-text gaps as a ``reader_formative`` text (:func:`queue_formative`),
  so the pipeline can name what was missing exactly as it does for reader
  questions; a match writes nothing new. It is never an attempt, evidence,
  mastery, certification or FSRS.
* **Reconstruct this later.** The question (``reconstruct`` style) is
  escalated through the quick check's own escalation into an ordinary
  practice item, and one ``test_me_later`` commitment on that item is added,
  dated ``RECONSTRUCT_DAYS`` ahead (``due_hint``), so the daily loop's "Check
  once" (DL2, when it lands) serves it as a delayed, cold rebuild.
  :func:`reconstruct_commit` is idempotent, and crash-idempotent too: the
  item is named by the question, so a retry after any interrupted write
  finishes the same item and commitment (Codex review F5).
  :func:`reconstruct_undo` retires both, as a capture's undo does, and an
  undone reconstruction stays undone (:class:`ReconstructUndone`, F6; open
  question 6's default: a second try is not offered).
* **A self-check and its learner text are one write** (:func:`record_action`):
  a missed self-check and its ``reader_formative`` job commit together, so a
  stop between them can't leave a recorded miss that never reaches
  learner-text gaps (F7); the backlog sweep recovers older ones.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.content.authoring.item_authoring import retire_item
from learnloop.curriculum import commitments as C
from learnloop.diagnosis.text_gaps.jobs import enqueue_reader_formative
from learnloop.reader import reader_quick_check as RQC

#: "In a few days": the commitment's due hint (a display and timing default
#: that DL2's dated check reads; never a learning threshold).
RECONSTRUCT_DAYS = 3
RECONSTRUCT_REASON = "reader_reconstruct"


class ActiveReadingError(ValueError):
    """Domain error for RW1b's active-reading acts."""


class ReconstructUndone(ActiveReadingError):
    """The learner undid this reconstruction: it is not made again."""


def queue_formative(vault: Any, repository: Any, row: dict[str, Any], *, clock: Clock | None = None) -> str | None:
    """Queue a missed formative answer for learner-text gaps (or nothing)."""

    if not RQC.is_missed(row):
        return None
    return enqueue_reader_formative(vault, repository, question_id=str(row["id"]), clock=clock)


def record_action(
    vault: Any, repository: Any, *, question_id: str, action: str, response_md: str | None = None,
    self_check: str | None = None, clock: Clock | None = None,
) -> tuple[dict[str, Any], str | None]:
    """The learner's act on an active-reading question and, for a missed
    self-check, its learner-text job, in one transaction (F7). Returns the
    row and the job id (or None). The caller wakes the worker after it."""

    with repository.atomic():
        row = RQC.record_selection_action(repository, question_id=question_id, action=action,
                                          response_md=response_md, self_check=self_check, clock=clock)
        job = queue_formative(vault, repository, row, clock=clock) if action == "self_checked" else None
    return row, job


def _key(question_id: str) -> str:
    return f"reader_reconstruct:{question_id}"


def _commitment_for(repository: Any, question_id: str) -> str | None:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT id FROM commitments WHERE created_action = 'test_me_later' AND idempotency_key = ?",
            (_key(question_id),),
        ).fetchone()
    return str(row[0]) if row is not None else None


def reconstruct_commit(
    root: Path, repository: Any, *, question_id: str, learning_object_id: str, clock: Clock | None = None,
) -> dict[str, Any]:
    """Escalate a reconstruct question into one practice item and add one
    ``test_me_later`` commitment on it. Idempotent on the question."""

    row = repository.get_reader_authored_question(question_id)
    if row is None or row.get("scope_kind") != "selection" or row.get("question_style") != "reconstruct":
        raise ActiveReadingError("not a reconstruct question")
    if row["status"] == "dismissed":
        raise ActiveReadingError("this reconstruction was undone")
    existing = _commitment_for(repository, question_id)
    if existing is not None and C.resolve_disposition(repository, existing) == "stopped":
        raise ReconstructUndone("You undid this reconstruction, so it won't be asked.")
    escalated = RQC.escalate(root, repository, question_id=question_id, learning_object_id=learning_object_id,
                             clock=clock)
    item_id = str(escalated["practice_item_id"])
    due = (parse_utc(utc_now_iso(clock)) + timedelta(days=RECONSTRUCT_DAYS)).strftime("%Y-%m-%d")
    commitment = C.create_commitment(
        repository,
        action="test_me_later",
        intent_text=f"rebuild without the book: {row['question_md']}",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": item_id, "role": "required"}],
        depth_preset="keep_in_touch",
        client_idempotency_key=_key(question_id),
        due_hint=due,
        reason=RECONSTRUCT_REASON,
        provenance={"reader_authored_question_id": question_id, "extraction_id": row["extraction_id"]},
        clock=clock,
    )
    return {"practice_item_id": item_id, "commitment_id": commitment.id, "due_hint": due,
            "question": repository.get_reader_authored_question(question_id)}


def reconstruct_undo(root: Path, repository: Any, *, question_id: str, vault: Any = None,
                     clock: Clock | None = None) -> dict[str, Any]:
    """Undo "reconstruct this later": retire its commitment and its item."""

    row = repository.get_reader_authored_question(question_id)
    if row is None or row.get("question_style") != "reconstruct":
        raise ActiveReadingError("not a reconstruct question")
    commitment_id = _commitment_for(repository, question_id)
    retired_commitment = None
    if commitment_id is not None:
        if C.resolve_disposition(repository, commitment_id) != "stopped":
            retired_commitment = C.retire(repository, commitment_id=commitment_id, clock=clock)
        else:
            retired_commitment = "stopped"
    item_id = row.get("practice_item_id")
    retired_item = None
    if item_id:
        result = retire_item(root, repository, practice_item_id=str(item_id), reason="no_longer_relevant",
                             note="undone from the Reader (reconstruct this later)", clock=clock,
                             loaded_vault=vault)
        retired_item = result.get("item")
    return {"practice_item_id": item_id, "commitment_id": commitment_id, "commitment": retired_commitment,
            "item": retired_item}


__all__ = [
    "ActiveReadingError",
    "RECONSTRUCT_DAYS",
    "ReconstructUndone",
    "queue_formative",
    "record_action",
    "reconstruct_commit",
    "reconstruct_undo",
]
