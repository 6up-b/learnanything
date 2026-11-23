"""A scratchpad's words as learner text (spec §10.11, the contract per review F4; mvp-0.68).

The one exit from the pads to the learner-text gap pipeline (import fence 1, ``pyproject.toml``): nothing that
writes evidence reads a pad, and this module hands the pipeline a frozen snapshot instead. What it does, per block:

* **Emits only the learner's own words**: a ``text`` or ``note`` block of provenance ``learner``, an ``ink`` block's
  transcription (``ink_transcription``) or its correction (``learner_correction``), not removed, not blank. Quoted
  source, tutor and figure blocks, sketches, cells, check cells and lift-out stubs emit nothing, so a pad of quotes
  emits nothing.
* **Once per wording**: the source id is the version where the block's current words were written (a move, or a
  lift into a pad of its own, keeps the words and so keeps their reading). The snapshot rides in the gap job's
  payload (:data:`SNAPSHOT_KEY`): the words, whether they were transcribed, whether they include a quote, and the
  passages the block was linked to.
* **Corrections supersede**: when a block's words change, every gap read from its earlier words gets one
  ``superseded`` reversal, and a reading of earlier words still queued is set aside unread.
* **Tombstones retract**: a removed block's gaps get one ``retracted`` reversal (rows stay; every reader that leaves
  out a reversed gap leaves them out).

All of it is idempotent: :func:`settle_blocks` after a pad batch, and :func:`reconcile` (every block) when a vault
opens and after the gap worker drains, so a reading that finished while its words were being replaced is set aside
on the next pass. Emission waits for the tag (``pad_text_on``) and the pipeline's switch; reversals never wait,
because a gap read from words that no longer stand must not keep steering routing. Never a model call.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from learnloop.algorithm_versions import pad_text_on
from learnloop.clock import utc_now_iso
from learnloop.db.stores import learner_gaps as gap_store
from learnloop.db.stores import pad_reads as reads
from learnloop.pads.quoting import includes_quote

LOG = logging.getLogger(__name__)

PAD_TEXT = "pad_text"
#: The gap job payload key holding the emitted snapshot (the gap pipeline's ``pad_text`` adapter reads it there).
SNAPSHOT_KEY = gap_store.PAD_TEXT_SNAPSHOT
#: Which provenances make each block kind the learner's own words.
EMITTED: Mapping[str, frozenset[str]] = {
    "text": frozenset({"learner"}),
    "note": frozenset({"learner"}),
    "ink": frozenset({"ink_transcription", "learner_correction"}),
}
#: The blocks whose words are someone else's (the quote check reads them).
QUOTE_KINDS = frozenset({"source_quote", "source_piece", "tutor_quote"})
SUPERSEDED, RETRACTED = "superseded", "retracted"
#: A lift-out can chain (a lifted block lifted again); deeper than any real pad, so a corrupt cycle stops.
_MAX_LIFTS = 64


def emittable(version: Mapping[str, Any] | None) -> bool:
    """A version of the learner's own, standing words (spec §10.11 "What is emitted")."""

    return (version is not None and not version["tombstone"] and version["provenance"] in EMITTED.get(version["kind"], ())
            and bool(str(version["body_md"] or "").strip()))


def _lineage_until(connection: Any, block_id: str, stop: int | None, depth: int) -> list[dict[str, Any]]:
    chain = reads.chain(connection, block_id)
    chain = chain if stop is None else chain[:stop]
    stubs = [index for index, version in enumerate(chain) if version["kind"] == "lifted"]
    own = chain[stubs[-1] + 1:] if stubs else chain
    if stubs or depth >= _MAX_LIFTS:
        return own
    origin = reads.lift_stub_for(connection, block_id)
    if origin is None:
        return own
    source_chain = reads.chain(connection, origin["block_id"])
    at = next((index for index, version in enumerate(source_chain) if version["version_id"] == origin["version_id"]),
              None)
    return (_lineage_until(connection, origin["block_id"], at, depth + 1) if at is not None else []) + own


def lineage(connection: Any, block_id: str) -> list[dict[str, Any]]:
    """The versions whose words this block carries, oldest first: its own versions since its last lift-out stub
    (earlier ones went to the lifted block), after the versions of the block it was lifted from, if it was."""

    return _lineage_until(connection, block_id, None, 0)


def words_version(versions: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The version where the head's words were written: the earliest of the run of versions, ending at the head,
    with the head's kind and words."""

    if not versions or not emittable(versions[-1]):
        return None
    head = versions[-1]
    found = head
    for version in reversed(versions[:-1]):
        if version["kind"] != head["kind"] or version["body_md"] != head["body_md"] or version["tombstone"]:
            break
        found = version
    return found


def context_blocks(connection: Any, head: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    """The blocks and pads whose links and quotes a block's words carry: the block itself, every block of its lift
    lineage (a lifted block's words came from there, and a lift made before anchors moved with the words left its
    links on the stub), and the block each of them is a note under; the pads all of these sit in. One definition for
    the emission's snapshot, the submission's quote check, the proposals and the pad's own read."""

    versions = lineage(connection, str(head["block_id"])) or [dict(head)]
    blocks: list[str] = [str(head["block_id"])]
    pads: list[str] = [str(head["pad_id"])]
    for version in [head, *versions]:
        for block_id in (version["block_id"], (version.get("payload") or {}).get("parent_block_id")):
            if block_id and str(block_id) not in blocks:
                blocks.append(str(block_id))
        if str(version["pad_id"]) not in pads:
            pads.append(str(version["pad_id"]))
    for block_id in blocks[1:]:
        parent = reads.head(connection, block_id)
        if parent is not None and str(parent["pad_id"]) not in pads:
            pads.append(str(parent["pad_id"]))
    return blocks, pads


def passages_of(connection: Any, head: Mapping[str, Any]) -> list[list[str]]:
    """The passages a block's words are linked to, through :func:`context_blocks`, in written order."""

    blocks, _pads = context_blocks(connection, head)
    seen: list[list[str]] = []
    for anchor in reads.standing_anchors_for_blocks(connection, blocks):
        place = [str(anchor["extraction_id"]), str(anchor["span_id"])]
        if place not in seen:
            seen.append(place)
    return seen


def quotes_of(connection: Any, repository: Any, head: Mapping[str, Any],
              passages: list[list[str]] | None = None) -> list[str]:
    """Someone else's words a block of the learner's might carry: the quote blocks of every pad its words passed
    through (:func:`context_blocks`) and the text of the passages it is linked to."""

    _blocks, pads = context_blocks(connection, head)
    quotes = [str(other["body_md"] or "") for pad_id in pads for other in reads.heads(connection, pad_id)
              if not other["tombstone"] and other["kind"] in QUOTE_KINDS]
    by_extraction: dict[str, set[str]] = {}
    for extraction_id, span_id in (passages if passages is not None else passages_of(connection, head)):
        by_extraction.setdefault(extraction_id, set()).add(span_id)
    for extraction_id, spans in by_extraction.items():
        try:
            ir = repository.load_document_ir(extraction_id)
        except Exception:  # noqa: BLE001 - a reading that cannot be loaded quotes nothing here
            ir = None
        for block in getattr(ir, "blocks", ()) or ():
            if getattr(block, "span_id", None) in spans:
                quotes.append(str(getattr(block, "text", "") or ""))
    return quotes


def snapshot(connection: Any, repository: Any, head: Mapping[str, Any], words: Mapping[str, Any]) -> dict[str, Any]:
    """What the gap pipeline is handed for one wording: the learner's words and the facts about them, frozen."""

    pad = reads.pad(connection, str(head["pad_id"])) or {}
    passages = passages_of(connection, head)
    text = str(words["body_md"] or "")
    return {
        "version_id": str(words["version_id"]), "block_id": str(head["block_id"]), "pad_id": str(head["pad_id"]),
        "block_kind": str(words["kind"]), "provenance": str(words["provenance"]), "text": text,
        "transcribed": words["kind"] == "ink",
        "quoted_by_learner": includes_quote(text, quotes_of(connection, repository, head, passages)),
        "passages": passages, "pad_kind": str(pad.get("kind") or ""),
        "workbench_session_id": pad.get("workbench_session_id"), "written_at": str(words["created_at"]),
    }


@dataclass
class Settled:
    """What one pass did: jobs queued, readings set aside before they ran, gaps reversed."""

    queued: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    reversed: list[tuple[str, str]] = field(default_factory=list)

    def merge(self, other: "Settled") -> None:
        self.queued += other.queued
        self.skipped += other.skipped
        self.reversed += other.reversed


def _settle_block(connection: Any, repository: Any, block_id: str, *, emit: bool, gaps: Mapping[str, Mapping[str, Any]],
                  reversed_ids: set[str], now: str) -> Settled:
    done = Settled()
    head = reads.head(connection, block_id)
    if head is None or head["kind"] == "lifted":
        # A lift-out stub: the words it held now belong to the lifted block, which settles them.
        return done
    versions = lineage(connection, block_id)
    words = words_version(versions)
    standing = str(words["version_id"]) if words is not None else None
    if words is not None and emit and gaps.get(standing) is None:
        if gap_store.job_for_source(connection, PAD_TEXT, standing) is None:
            job = gap_store.enqueue_job(connection, source_kind=PAD_TEXT, source_id=standing, now=now,
                                        payload={SNAPSHOT_KEY: snapshot(connection, repository, head, words)})
            if job:
                done.queued.append(standing)
    reversal = RETRACTED if head["tombstone"] else SUPERSEDED
    why = "the block was removed" if head["tombstone"] else "the block's words changed"
    for version in versions:
        version_id = str(version["version_id"])
        if version_id == standing:
            continue
        if gap_store.skip_queued_job(connection, source_kind=PAD_TEXT, source_id=version_id, now=now,
                                     reason=f"set aside unread: {why}"):
            done.skipped.append(version_id)
        gap = gaps.get(version_id)
        if gap is not None and str(gap["id"]) not in reversed_ids:
            if gap_store.insert_reversal(connection, gap_id=str(gap["id"]), reversal=reversal, actor="learner",
                                         created_at=now, detail={"block_id": block_id, "version_id": version_id,
                                                                 "standing_version_id": standing, "why": why}):
                done.reversed.append((str(gap["id"]), reversal))
                reversed_ids.add(str(gap["id"]))
    return done


def _settle(vault: Any, repository: Any, block_ids: Iterable[str] | None, clock: Any) -> Settled:
    emit = pad_text_on(vault.config) and bool(vault.config.learner_text_gaps.enabled)
    done = Settled()
    with repository.atomic():
        connection = repository.connection()
        if not gap_store.gap_tables_present(connection):
            return done
        rows = gap_store.gaps(connection, source_kind=PAD_TEXT)
        gaps = {str(row["source_id"]): row for row in rows}
        reversed_ids = {str(row["gap_id"]) for row in gap_store.reversals(connection, [row["id"] for row in rows])
                        if row["reversal"] in (SUPERSEDED, RETRACTED)}
        wanted = reads.block_ids(connection) if block_ids is None else sorted(set(block_ids))
        now = utc_now_iso(clock)
        for block_id in wanted:
            done.merge(_settle_block(connection, repository, block_id, emit=emit, gaps=gaps,
                                     reversed_ids=reversed_ids, now=now))
    if done.reversed:
        repository.bump_queue_revision(clock=clock)
    return done


def settle_blocks(vault: Any, repository: Any, block_ids: Iterable[str], *, clock: Any = None) -> Settled:
    """After a pad batch: emit the blocks' new words, supersede what they replaced, retract what was removed."""

    return _settle(vault, repository, block_ids, clock)


def reconcile(vault: Any, repository: Any, *, clock: Any = None) -> Settled:
    """Every block, the same way (a vault's open, after the gap worker drains): words committed while emission
    could not run are queued, and a reading that finished after its words were replaced is set aside."""

    return _settle(vault, repository, None, clock)


__all__ = [
    "EMITTED", "PAD_TEXT", "QUOTE_KINDS", "RETRACTED", "SNAPSHOT_KEY", "SUPERSEDED", "Settled", "context_blocks",
    "emittable", "lineage", "passages_of", "quotes_of", "reconcile", "settle_blocks", "snapshot", "words_version",
]
