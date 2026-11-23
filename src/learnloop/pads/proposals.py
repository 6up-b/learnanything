"""LearnLoop's suggested connections for a pad block, and what the learner did with them (spec §10.6, §14).

A proposal is a gutter marker on one committed block of the learner's own words: "<source> p.<page> takes this to
the next step". It is computed when the block's words are committed (never while typing), for the learner's own
blocks only, at most one per block version (the marker density is the attention budget's), and kept as a receipt
(``pad_proposals``). "Not this", "dismiss", "opened" and an ignored marker are labels (``proposal_labels``): ranking
and offline evaluation, never evidence.

What finds one here is the cheap, model-free part of the machinery the menus' promoted rows share: the passage
links the cue judge already made for this learner (``passage_links``, ranked by their own ``pick_rank``). A block
linked to a passage that a link ties to one of the learner's open problems (a hypothesis, a misconception, a named
gap, a recurrence group, a demonstrated facet, an unchecked claim) gets the best other passage tied to the same
problem, with that link's relation as the reason and its quote. Search and correspondents ("<video> ▶ <time> says
this another way", found by ``search_spans`` and verified by ``verify_spans``) and the learner-history ranking are
the menus' stage (``passage.promoted``): a block with no linked passage gets no proposal until then.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from learnloop.clock import utc_now_iso
from learnloop.content.sources.span_aliases import reading_source
from learnloop.db.stores import pad_ledgers as store
from learnloop.db.stores import pad_reads as reads
from learnloop.ids import new_ulid
from learnloop.pads.emission import emittable, lineage, passages_of, words_version

PAD_PROPOSAL, PROMOTED_ROW = "pad_proposal", "promoted_row"
LABELS = ("opened", "not_this", "dismiss", "ignored")
PASSAGE_LINK = "passage_link"
#: The reason each passage-link relation gives, in the learner's words.
REASONS = {
    "clarifies_distinction": "this passage draws the distinction you are working on",
    "new_application": "this passage takes it to a new application",
    "prerequisite_for": "this passage is what it builds on",
    "try_first": "try this passage first",
}


class ProposalRefused(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code, self.message = code, message


def _table(connection: Any, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                              (name,)).fetchone() is not None


def _block_places(connection: Any, head: dict[str, Any]) -> set[tuple[str, str]]:
    return {(extraction_id, span_id) for extraction_id, span_id in passages_of(connection, head)}


def _candidate(connection: Any, places: set[tuple[str, str]]) -> dict[str, Any] | None:
    """The best passage link to a passage other than ``places`` tied to a problem a link on ``places`` names."""

    if not places or not _table(connection, "passage_links"):
        return None
    targets: set[tuple[str, str]] = set()
    for extraction_id, span_id in sorted(places):
        targets.update((str(row[0]), str(row[1])) for row in connection.execute(
            "SELECT target_kind, target_id FROM passage_links WHERE extraction_id = ? AND span_id = ?",
            (extraction_id, span_id)))
    best: tuple[Any, ...] | None = None
    found: dict[str, Any] | None = None
    for target_kind, target_id in sorted(targets):
        cursor = connection.execute(
            "SELECT id, extraction_id, span_id, target_kind, target_id, relation, quote, pick_rank, ledger_id, "
            "created_at FROM passage_links WHERE target_kind = ? AND target_id = ?", (target_kind, target_id))
        names = [column[0] for column in cursor.description]
        for raw in cursor.fetchall():
            row = dict(zip(names, raw, strict=True))
            if (str(row["extraction_id"]), str(row["span_id"])) in places:
                continue
            key = (int(row["pick_rank"]), str(row["created_at"]), str(row["id"]))
            if best is None or key < best:
                best, found = key, row
    return found


def propose_for_blocks(repository: Any, block_ids: Iterable[str], *, clock: Any = None) -> list[dict[str, Any]]:
    """After a pad batch: one proposal for each block whose newly committed words have none yet and a candidate.
    Idempotent (one per words version). Returns the proposals written."""

    written: list[dict[str, Any]] = []
    with repository.atomic():
        connection = repository.connection()
        if not _table(connection, "pad_proposals"):
            return written
        for block_id in sorted(set(block_ids)):
            head = reads.head(connection, block_id)
            if not emittable(head) or head["provenance"] == "ink_transcription":
                # The learner's own written words only: a machine transcription is not yet what they wrote.
                continue
            words = words_version(lineage(connection, block_id))
            if words is None or reads.proposal_for_version(connection, str(words["version_id"])) is not None:
                continue
            link = _candidate(connection, _block_places(connection, head))
            if link is None:
                continue
            source_id = reading_source(repository, str(link["extraction_id"]))
            if source_id is None:
                continue
            row = {
                "proposal_id": new_ulid(), "block_version_id": str(words["version_id"]), "block_id": block_id,
                "pad_id": str(head["pad_id"]), "found_by": PASSAGE_LINK,
                "target_spec": {"content": {"kind": "source", "source_id": source_id,
                                            "extraction_id": str(link["extraction_id"]), "view": "render"},
                                "target": {"span_id": str(link["span_id"])}},
                "reason_md": REASONS.get(str(link["relation"]), "this passage is tied to what you wrote"),
                "quote": str(link["quote"] or ""), "judgment_ref": str(link["ledger_id"]),
                "created_at": utc_now_iso(clock),
            }
            store.insert_proposal(connection, row)
            written.append(row)
    return written


def _out(row: dict[str, Any], labels: list[dict[str, Any]], current: bool) -> dict[str, Any]:
    return {"proposal_id": row["proposal_id"], "block_id": row["block_id"], "block_version_id": row["block_version_id"],
            "found_by": row["found_by"], "target": row["target_spec"], "reason_md": row["reason_md"],
            "quote": row["quote"], "judgment_ref": row["judgment_ref"], "created_at": row["created_at"],
            "current": current, "labels": [{"label": label["label"], "at": label["at"]} for label in labels],
            "shown": current and not any(label["label"] in ("not_this", "dismiss") for label in labels)}


def pad_proposals(repository: Any, pad_id: str) -> dict[str, Any]:
    """``pad.proposals``: each standing block's proposal for its current words, with its labels (``shown`` false
    once dismissed or marked "not this")."""

    with repository.connection() as connection:
        if reads.pad(connection, pad_id) is None:
            raise ProposalRefused("pad_not_found", f"No pad {pad_id!r}.")
        current: dict[str, str] = {}
        for head in reads.heads(connection, pad_id):
            words = words_version(lineage(connection, str(head["block_id"]))) if emittable(head) else None
            if words is not None:
                current[str(words["version_id"])] = str(head["block_id"])
        rows = reads.proposals_for_versions(connection, current)
        labels = reads.labels_for(connection, PAD_PROPOSAL, [row["proposal_id"] for row in rows])
    by_proposal: dict[str, list[dict[str, Any]]] = {}
    for label in labels:
        by_proposal.setdefault(str(label["proposal_id"]), []).append(label)
    # A lifted block's words keep their proposal: it is shown on the block that carries those words now.
    return {"pad_id": pad_id, "proposals": [{**_out(row, by_proposal.get(str(row["proposal_id"]), []), True),
                                             "block_id": current[str(row["block_version_id"])]} for row in rows]}


def label(repository: Any, *, label_id: str, proposal_kind: str, proposal_id: str, label_value: str,
          clock: Any = None) -> dict[str, Any]:
    """Record one label, idempotent by the client-minted ``label_id``. A pad proposal must exist; a promoted row's
    id is the menus' (not checked here)."""

    if label_value not in LABELS:
        raise ProposalRefused("unknown_label", f"Unknown label {label_value!r}.")
    with repository.atomic():
        connection = repository.connection()
        existing = reads.label(connection, label_id)
        if existing is not None:
            if (existing["proposal_kind"], existing["proposal_id"], existing["label"]) != (
                    proposal_kind, proposal_id, label_value):
                raise ProposalRefused("label_id_reused", "That label id names another label.")
            return {"label_id": label_id, "applied": False, "at": existing["at"]}
        if proposal_kind == PAD_PROPOSAL and reads.proposal(connection, proposal_id) is None:
            raise ProposalRefused("proposal_not_found", f"No proposal {proposal_id!r}.")
        at = utc_now_iso(clock)
        store.insert_label(connection, label_id=label_id, proposal_kind=proposal_kind, proposal_id=proposal_id,
                           label=label_value, at=at)
    return {"label_id": label_id, "applied": True, "at": at}


__all__ = [
    "LABELS", "PAD_PROPOSAL", "PASSAGE_LINK", "PROMOTED_ROW", "ProposalRefused", "REASONS", "label", "pad_proposals",
    "propose_for_blocks",
]
