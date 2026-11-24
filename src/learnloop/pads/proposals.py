"""LearnLoop's suggested connections for a pad block, and what the learner did with them (spec §10.6, §14).

A proposal is a gutter marker on one committed block of the learner's own words: "<source> p.<page> takes this to
the next step". It is computed when the block's words are committed (never while typing), for the learner's own
blocks only, at most one per block version (the marker density is the attention budget's), and kept as a receipt
(``pad_proposals``). "Not this", "dismiss", "opened" and an ignored marker are labels (``proposal_labels``): ranking
and offline evaluation, never evidence.

What finds one is the menus' machinery (``learnloop.passage_union.elsewhere``, the promoted rows' too), best first:
a passage the cue judge tied to the same learner problem as a passage the block is linked to (ranked for this
learner, with the link's relation as the reason and its quote); else another book's section the coverage judge says
treats the same topic; else a passage found for the block's words by keyword ("found by search, not checked"). None
of them calls a model at the commit; meaning search and its verification are the menu job's.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from learnloop.clock import utc_now_iso
from learnloop.content.sources.span_aliases import reading_source
from learnloop.db.stores import pad_ledgers as store
from learnloop.db.stores import pad_reads as reads
from learnloop.ids import new_ulid
from learnloop.passage_union.elsewhere import RELATION_REASONS
from learnloop.pads.emission import emittable, lineage, passages_of, words_version

PAD_PROPOSAL, PROMOTED_ROW = "pad_proposal", "promoted_row"
LABELS = ("opened", "not_this", "dismiss", "ignored")
PASSAGE_LINK = "passage_link"
#: The reason each passage-link relation gives, in the learner's words.
#: What each passage-link relation says (one table, the menus' too).
REASONS = RELATION_REASONS


class ProposalRefused(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code, self.message = code, message


def _table(connection: Any, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                              (name,)).fetchone() is not None


def _block_places(connection: Any, head: dict[str, Any]) -> set[tuple[str, str]]:
    return {(extraction_id, span_id) for extraction_id, span_id in passages_of(connection, head)}


def _findings(vault: Any, repository: Any, connection: Any, head: dict[str, Any]) -> list[Any]:
    """The candidates for one block, best first: a passage the cue judge tied to the same learner problem (ranked for
    this learner), else another book's section the coverage judge says treats the same topic, else a passage found for
    the block's words by keyword ("found by search, not checked"). The last two need the vault; neither calls a model
    (a commit never waits on one)."""

    from learnloop.passage_union import elsewhere as E

    if vault is None:
        # Whether a passage is protected is the vault's to say: without it, nothing is proposed.
        return []
    places = sorted(_block_places(connection, head))
    found = E.by_passage_links(vault, repository, connection, places)
    if found:
        return found
    if places:
        found = [finding for finding in E.by_correspondents(vault, repository, places, search_fallback=False)
                 if finding.checked]
        if found:
            return found
    if E.withheld_places(vault, repository, places):
        # A block about exam or held-out material: its words are not searched by.
        return []
    sources = sorted({source for extraction_id, _span in places
                      if (source := reading_source(repository, extraction_id)) is not None})
    return E.by_search(vault, repository, str(head["body_md"] or ""), exclude_sources=sources, exclude_places=places,
                       deep=False, verify=False, owner_id=f"pad_proposal:{head['block_id']}", pick_at_most=1)


def propose_for_blocks(repository: Any, block_ids: Iterable[str], *, vault: Any = None,
                       clock: Any = None) -> list[dict[str, Any]]:
    """After a pad batch: one proposal for each block whose newly committed words have none yet and a candidate
    (:func:`_findings`). Idempotent (one per words version). Returns the proposals written."""

    from learnloop.passage_union.elsewhere import as_proposal

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
            findings = _findings(vault, repository, connection, head)
            if not findings:
                continue
            row = {"proposal_id": new_ulid(), "block_version_id": str(words["version_id"]), "block_id": block_id,
                   "pad_id": str(head["pad_id"]), **as_proposal(findings[0]), "created_at": utc_now_iso(clock)}
            store.insert_proposal(connection, row)
            written.append(row)
    return written


def _out(row: dict[str, Any], labels: list[dict[str, Any]], current: bool) -> dict[str, Any]:
    return {"proposal_id": row["proposal_id"], "block_id": row["block_id"], "block_version_id": row["block_version_id"],
            "found_by": row["found_by"], "target": row["target_spec"], "reason_md": row["reason_md"],
            "quote": row["quote"], "judgment_ref": row["judgment_ref"], "created_at": row["created_at"],
            "current": current, "labels": [{"label": label["label"], "at": label["at"]} for label in labels],
            "shown": current and not any(label["label"] in ("not_this", "dismiss") for label in labels)}


def _protected(vault: Any, repository: Any, rows: list[dict[str, Any]],
               origins: dict[str, set[tuple[str, str]]]) -> set[str]:
    """The proposals that name exam or held-out material now: their target, or a passage their block is about
    (``origins``, by words version; marked after the proposal was made, or since its words were lifted)."""

    from learnloop.passage_union.elsewhere import withheld_places

    def target(row: dict[str, Any]) -> tuple[str, str]:
        spec = row.get("target_spec") or {}
        return (str((spec.get("content") or {}).get("extraction_id") or ""),
                str((spec.get("target") or {}).get("span_id") or ""))

    def about(row: dict[str, Any]) -> set[tuple[str, str]]:
        return origins.get(str(row["block_version_id"]), set())

    withheld = withheld_places(vault, repository, {target(row) for row in rows} | {
        place for row in rows for place in about(row)})
    return {str(row["proposal_id"]) for row in rows if target(row) in withheld or about(row) & withheld}


def pad_proposals(repository: Any, pad_id: str, *, vault: Any) -> dict[str, Any]:
    """``pad.proposals``: each standing block's proposal for its current words, with its labels (``shown`` false
    once dismissed or marked "not this"). A proposal that names exam or held-out material now (by the one predicate,
    read at each call) is left out whole: its target, reason and quote never reach the gutter."""

    with repository.connection() as connection:
        if reads.pad(connection, pad_id) is None:
            raise ProposalRefused("pad_not_found", f"No pad {pad_id!r}.")
        current: dict[str, str] = {}
        origins: dict[str, set[tuple[str, str]]] = {}
        for head in reads.heads(connection, pad_id):
            words = words_version(lineage(connection, str(head["block_id"]))) if emittable(head) else None
            if words is not None:
                current[str(words["version_id"])] = str(head["block_id"])
                origins[str(words["version_id"])] = _block_places(connection, head)
        rows = reads.proposals_for_versions(connection, current)
        hidden = _protected(vault, repository, rows, origins)
        rows = [row for row in rows if str(row["proposal_id"]) not in hidden]
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
