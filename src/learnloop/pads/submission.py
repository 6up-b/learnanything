"""Submitting a pad block (spec §10.9): the only way a pad's words become evidence, and an explicit act.

This module decides whether a block version may be handed over and freezes its text; the sidecar hands that text to
the existing attempt entry point (``submit_attempt_on``) or teach-back entry point (``submit_teach_back_turn``), so
grading, help counting, the assisted label after worked help and blindness are exactly theirs (no new grading
path), and :func:`record` then writes the ``pad_block_submissions`` row that links the version to what it became.

The rules:

* only the learner's own words: a ``text`` or ``note`` block of provenance ``learner``, an ``ink`` block's
  transcription or correction, or a ``check_cell``'s answer (its body; the check's prompt is its payload);
* a block that includes a quote (a whole sentence of one of the pad's quote blocks or of a passage the block is
  linked to, ``pads.quoting``) is refused: "this includes quoted text · submit only your own words";
* "my answer to <item>" only where the block answers that item: a problem pad's workbench session, or a check cell
  naming it; a teach-back from any of the learner's blocks (the entry point checks the item is a teach-back one);
* the version must carry the block's current words (a move keeps them): an edit made since the client looked is a
  conflict naming the current head, never a submission of words the learner no longer has;
* idempotent by the client-minted ``submission_id``: a retry with the same request finds its row and hands nothing
  over again; the same id with another request is refused.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from learnloop.clock import utc_now_iso
from learnloop.db.stores import pad_ledgers as store
from learnloop.db.stores import pad_reads as reads
from learnloop.pads.emission import lineage, quotes_of, words_version
from learnloop.pads.quoting import includes_quote

ATTEMPT, TEACH_BACK = "attempt", "teach_back"
#: The block kinds whose body is the learner's own words, and the provenances that make it so (a check cell's body is
#: its answer whatever wrote the check).
SUBMITTABLE: dict[str, frozenset[str] | None] = {
    "text": frozenset({"learner"}),
    "note": frozenset({"learner"}),
    "ink": frozenset({"ink_transcription", "learner_correction"}),
    "check_cell": None,
}
#: The attempt's surface (``practice_attempts.entry_surface``): a scratchpad block, graded as every other answer.
ENTRY_SURFACE = "desktop_scratchpad"
QUOTED_MESSAGE = "this includes quoted text · submit only your own words"


class SubmissionRefused(Exception):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code, self.message, self.details = code, message, details or {}


@dataclass(frozen=True)
class Prepared:
    """A block version cleared for hand-off, or the row of a submission already made (``existing``)."""

    submission_id: str
    block_id: str
    version_id: str
    pad_id: str
    submitted_as: str
    practice_item_id: str
    session_id: str
    text: str
    request_hash: str
    existing: dict[str, Any] | None = None


def request_hash(*, block_id: str, version_id: str, submitted_as: str, practice_item_id: str, session_id: str) -> str:
    request = {"block_id": block_id, "version_id": version_id, "as": submitted_as,
               "practice_item_id": practice_item_id, "session_id": session_id}
    return hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()


def _answered_item(connection: Any, pad: dict[str, Any], version: dict[str, Any]) -> str | None:
    """The item this block may be "my answer to": its check cell's, else its problem pad's."""

    if version["kind"] == "check_cell":
        return str((version.get("payload") or {}).get("practice_item_id") or "") or None
    if pad.get("kind") == "problem" and pad.get("workbench_session_id"):
        row = connection.execute("SELECT practice_item_id FROM workbench_sessions WHERE id = ?",
                                 (str(pad["workbench_session_id"]),)).fetchone()
        return str(row[0]) if row is not None and row[0] else None
    return None


def prepare(repository: Any, *, submission_id: str, block_id: str, version_id: str, submitted_as: str,
            practice_item_id: str, session_id: str) -> Prepared:
    """Check one submission and freeze its text (raises :class:`SubmissionRefused`)."""

    digest = request_hash(block_id=block_id, version_id=version_id, submitted_as=submitted_as,
                          practice_item_id=practice_item_id, session_id=session_id)
    base = dict(submission_id=submission_id, block_id=block_id, version_id=version_id, submitted_as=submitted_as,
                practice_item_id=practice_item_id, session_id=session_id, request_hash=digest)
    with repository.connection() as connection:
        existing = reads.submission(connection, submission_id)
        if existing is not None:
            if existing["request_hash"] != digest:
                raise SubmissionRefused("submission_reused", "That submission id was used for another submission.")
            # The words this submission froze: a reserved teach-back whose hand-off never happened hands them over
            # on the retry, whatever the block says now.
            frozen = reads.version(connection, str(existing["version_id"])) or {}
            return Prepared(**base, pad_id=str(existing["pad_id"]), text=str(frozen.get("body_md") or "").strip(),
                            existing=existing)
        version = reads.version(connection, version_id)
        if version is None or version["block_id"] != block_id:
            raise SubmissionRefused("version_not_found", "Reopen the pad and submit the current text.")
        head = reads.head(connection, block_id)
        if head is None or head["tombstone"]:
            raise SubmissionRefused("block_removed", "This line was removed. Choose another line.")
        words = words_version(lineage(connection, block_id)) if head["kind"] != "check_cell" else None
        current = {str(words["version_id"]), str(head["version_id"])} if words is not None else {str(head["version_id"])}
        same_words = head["kind"] == version["kind"] and head["body_md"] == version["body_md"]
        if version_id not in current and not same_words:
            raise SubmissionRefused("stale_version", "This line has changed. Check the latest text and submit again.",
                                    {"block_id": block_id, "head_version_id": str(head["version_id"])})
        allowed = SUBMITTABLE.get(str(version["kind"]), frozenset())
        if allowed is not None and version["provenance"] not in allowed:
            raise SubmissionRefused("not_learners_words", "Write your answer in your own words, then submit it.")
        text = str(version["body_md"] or "").strip()
        if not text:
            raise SubmissionRefused("empty_block", "Write your answer, then submit it.")
        pad = reads.pad(connection, str(version["pad_id"])) or {}
        if submitted_as == ATTEMPT and _answered_item(connection, pad, version) != practice_item_id:
            raise SubmissionRefused(
                "not_an_answer", "Open the pad for the question you’re answering, then submit your answer there.",
                {"practice_item_id": practice_item_id})
        quotes = quotes_of(connection, repository, head)
    if includes_quote(text, quotes):
        raise SubmissionRefused("includes_quote", QUOTED_MESSAGE)
    return Prepared(**base, pad_id=str(version["pad_id"]), text=text)


def record(repository: Any, prepared: Prepared, *, attempt_id: str | None, teach_back_id: str | None,
           clock: Any = None) -> dict[str, Any]:
    """Write the submission's row once (a concurrent retry that wrote it first wins); returns the row."""

    with repository.atomic():
        connection = repository.connection()
        existing = reads.submission(connection, prepared.submission_id)
        if existing is not None:
            return existing
        store.insert_submission(connection, {
            "submission_id": prepared.submission_id, "block_id": prepared.block_id, "version_id": prepared.version_id,
            "pad_id": prepared.pad_id, "submitted_as": prepared.submitted_as,
            "practice_item_id": prepared.practice_item_id, "session_id": prepared.session_id,
            "attempt_id": attempt_id, "teach_back_id": teach_back_id, "request_hash": prepared.request_hash,
            "created_at": utc_now_iso(clock),
        })
        return reads.submission(connection, prepared.submission_id) or {}


def tags(connection: Any, heads: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Each block's submissions for ``pad.get`` (the "submitted · …" tag), each saying whether it froze the
    block's current words or an earlier version."""

    current = {str(head["block_id"]): {str(head["version_id"])} for head in heads}
    for head in heads:
        words = words_version(lineage(connection, str(head["block_id"])))
        if words is not None:
            current[str(head["block_id"])].add(str(words["version_id"]))
    out: dict[str, list[dict[str, Any]]] = {}
    for row in reads.submissions_for_blocks(connection, current):
        out.setdefault(str(row["block_id"]), []).append({
            "submission_id": row["submission_id"], "version_id": row["version_id"], "as": row["submitted_as"],
            "practice_item_id": row["practice_item_id"], "attempt_id": row["attempt_id"],
            "teach_back_id": row["teach_back_id"], "created_at": row["created_at"],
            "current": str(row["version_id"]) in current[str(row["block_id"])],
        })
    return out


__all__ = [
    "ATTEMPT", "ENTRY_SURFACE", "Prepared", "QUOTED_MESSAGE", "SUBMITTABLE", "SubmissionRefused", "TEACH_BACK",
    "prepare", "record", "request_hash", "tags",
]
