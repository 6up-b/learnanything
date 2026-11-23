"""Scratchpads and their blocks (spec §10, §3.4): ``pad.get``, ``pad.list`` and the ``pad.apply`` ops.

A block's versions form one chain: ``insert_block`` writes its first version, and every later op
(``edit_block``, ``remove_block``, ``move_block``, ``lift_out``) names the head it expects and appends a
version superseding it; the schema refuses a second child of one version, so there is no branching
head. Ids are client-minted (pad, block, version), so a client can chain edits in its outbox before
the server answers, and a retry never mints a second object.

Provenance is never laundered (a P3 invariant): an edit keeps its block's provenance, except an ink
block's transcription, whose edit is the learner's correction; quoted source, tutor and figure blocks
and lifted stubs are not the learner's to edit. Workflow data and the learner's own writing, never
evidence: the explicit exits are ``pads.emission`` (committed words to learner-text gaps) and
``pads.submission`` (a submitted block to the attempt and teach-back entry points).
"""
from __future__ import annotations

import re
from typing import Annotated, Any, Literal, Union

from pydantic import Field

from learnloop.db.stores import pad_reads as reads
from learnloop.db.stores import pads as store
from learnloop.db.stores.workspace_batches import PAD
from learnloop.desks.content_ref import WireModel
from learnloop.desks.protocol import OpConflict, OpRefused, apply_batch, run_op
from learnloop.ids import new_ulid
from learnloop.pads import ink as ink_core
from learnloop.pads.submission import tags as submission_tags

BlockKind = Literal["text", "note", "source_quote", "source_piece", "tutor_quote", "figure", "sketch", "cell", "ink",
                    "lifted", "check_cell"]
Provenance = Literal["learner", "source", "tutor", "learnloop", "ink_transcription", "learner_correction"]
#: The kinds the learner edits in place (spec §10.4's "editable" column); the rest quote someone else.
EDITABLE_KINDS = frozenset({"text", "note", "sketch", "cell", "ink", "check_cell"})
#: A pad listing's page (a paging size, not a cap: the cursor reaches every pad).
PAGE_SIZE = 50


class _Op(WireModel):
    pass


class CreatePad(_Op):
    op: Literal["create_pad"]
    kind: Literal["running", "named", "problem", "ink", "lesson_additions"]
    title: str = ""
    home_desk_id: str | None = None
    workbench_session_id: str | None = None
    lesson_id: str | None = None


class SetTitle(_Op):
    op: Literal["set_title"]
    expected_version: int
    title: str


class Keep(_Op):
    op: Literal["keep"]
    expected_version: int


class Unkeep(_Op):
    op: Literal["unkeep"]
    expected_version: int


class InsertBlock(_Op):
    op: Literal["insert_block"]
    block_id: str = Field(min_length=1)
    version_id: str | None = None
    kind: BlockKind
    provenance: Provenance
    position_key: str = Field(min_length=1)
    day: str | None = None
    body_md: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)


class KeepBoth(WireModel):
    """Where a stale edit's words go instead of being lost (spec §3.5): a new block, client-minted, right after the
    block's current head, marked with what it conflicted with."""

    block_id: str = Field(min_length=1)
    version_id: str | None = None
    #: The client's own words for the mark (spec: "from your other device · <time>"), kept in the payload.
    label: str = ""


class EditBlock(_Op):
    op: Literal["edit_block"]
    block_id: str
    expected_head: str
    version_id: str | None = None
    body_md: str | None = None
    payload: dict[str, Any] | None = None
    #: On a stale head: keep the server's head and put these words in a block of their own after it (one op, so a
    #: retried batch never writes them twice). Absent: a stale head is a conflict, as before.
    keep_both: KeepBoth | None = None


class RemoveBlock(_Op):
    op: Literal["remove_block"]
    block_id: str
    expected_head: str
    version_id: str | None = None


class MoveBlock(_Op):
    op: Literal["move_block"]
    block_id: str
    expected_head: str
    position_key: str = Field(min_length=1)
    version_id: str | None = None


class LiftOut(_Op):
    op: Literal["lift_out"]
    block_id: str
    expected_head: str
    new_pad_id: str = Field(min_length=1)
    new_block_id: str = Field(min_length=1)
    title: str = ""
    new_version_id: str | None = None
    stub_version_id: str | None = None
    position_key: str = "a0"


class LinkAnchor(_Op):
    op: Literal["link_anchor"]
    block_id: str
    extraction_id: str = Field(min_length=1)
    span_id: str = Field(min_length=1)
    anchor: dict[str, Any] = Field(default_factory=dict)
    annotation_id: str | None = None
    event_id: str | None = None
    #: The newest event between this block and this passage, as the client last saw it; ``None`` (sent
    #: explicitly) means "no event yet". Required: a link change never lands on a head it did not expect.
    expected_anchor_head: str | None


class UnlinkAnchor(_Op):
    op: Literal["unlink_anchor"]
    block_id: str
    extraction_id: str = Field(min_length=1)
    span_id: str = Field(min_length=1)
    event_id: str | None = None
    expected_anchor_head: str | None


class EraseInk(_Op):
    """The pen's barrel button over an ink block's strokes: a tombstone over their ids (``pads.ink``)."""

    op: Literal["erase_ink"]
    block_id: str = Field(min_length=1)
    stroke_ids: list[str] = Field(min_length=1)
    erase_id: str | None = Field(default=None, min_length=1)


PadOp = Annotated[
    Union[CreatePad, SetTitle, Keep, Unkeep, InsertBlock, EditBlock, RemoveBlock, MoveBlock, LiftOut, LinkAnchor,
          UnlinkAnchor, EraseInk],
    Field(discriminator="op"),
]

PAD_OPS: tuple[str, ...] = (
    "create_pad", "set_title", "keep", "unkeep", "insert_block", "edit_block", "remove_block", "move_block",
    "lift_out", "link_anchor", "unlink_anchor", "erase_ink",
)


# -- reads ------------------------------------------------------------------------------------------


def _block_out(head: dict[str, Any], created: str | None) -> dict[str, Any]:
    return {
        "block_id": head["block_id"], "head_version_id": head["version_id"], "kind": head["kind"],
        "body_md": head["body_md"], "payload": head["payload"], "provenance": head["provenance"],
        "position_key": head["position_key"], "day": head["day"], "created_at": created or head["created_at"],
        "updated_at": head["created_at"],
    }


def _pad_out(row: dict[str, Any]) -> dict[str, Any]:
    return {"pad_id": row["pad_id"], "kind": row["kind"], "title": row["title"], "kept": bool(row["kept"]),
            "home_desk_id": row["home_desk_id"], "workbench_session_id": row["workbench_session_id"],
            "lesson_id": row["lesson_id"], "version": int(row["version"]), "created_at": row["created_at"],
            "updated_at": row["updated_at"]}


class PadNotFound(LookupError):
    pass


class _Places:
    """Where a link points, enough to open it with no window of that source open (review finding 13): the source
    the reading belongs to (a ``ContentRef``'s ``source_id``), and on a transcript the cue's start (``t``, a video
    reference's time). Each reading is looked up once."""

    _CUE = re.compile(r"^t=([0-9.]+)-([0-9.]+)$")

    def __init__(self, repository: Any) -> None:
        self.repository = repository
        self.sources: dict[str, str | None] = {}
        self.cues: dict[str, dict[str, float]] = {}

    def where(self, extraction_id: str, span_id: str) -> dict[str, Any]:
        from learnloop.content.sources.span_aliases import reading_source

        if extraction_id not in self.sources:
            self.sources[extraction_id] = reading_source(self.repository, extraction_id)
            ir = self.repository.load_document_ir(extraction_id)
            self.cues[extraction_id] = {
                block.span_id: float(match.group(1)) for block in getattr(ir, "blocks", ()) or ()
                if (match := self._CUE.match(str(getattr(block, "extractor_block_id", "") or "")))}
        return {"source_id": self.sources[extraction_id], "t": self.cues[extraction_id].get(span_id)}


def _inherited_anchors(connection: Any, heads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Links a lifted block carries from the block it was lifted out of, where a lift made before links moved with
    the words left them on the stub: shown on the lifted block, read-only (``inherited_from_block_id`` names the
    stub's block, whose link events they are)."""

    from learnloop.pads.emission import context_blocks

    out: list[dict[str, Any]] = []
    for head in heads:
        blocks, _pads = context_blocks(connection, head)
        parent = (head.get("payload") or {}).get("parent_block_id")
        ancestors = [block_id for block_id in blocks[1:] if block_id != parent]
        lifted_from = [block_id for block_id in ancestors
                       if (reads.head(connection, block_id) or {}).get("kind") == "lifted"]
        for anchor in reads.standing_anchors_for_blocks(connection, lifted_from):
            out.append({**anchor, "block_id": head["block_id"], "inherited_from_block_id": anchor["block_id"]})
    return out


def pad_view(repository: Any, pad_id: str) -> dict[str, Any]:
    """``pad.get``: the pad, its standing blocks in order (removed blocks left out) and their links."""

    with repository.connection() as connection:
        row = reads.pad(connection, pad_id)
        if row is None:
            raise PadNotFound(pad_id)
        heads = [head for head in reads.heads(connection, pad_id) if not head["tombstone"]]
        created = reads.first_versions(connection, [head["block_id"] for head in heads])
        anchors = [{**anchor, "inherited_from_block_id": None}
                   for anchor in reads.standing_anchors_for_blocks(connection, [head["block_id"] for head in heads])]
        anchors += _inherited_anchors(connection, heads)
        submitted = submission_tags(connection, heads)
    for tags in submitted.values():
        for tag in tags:
            if tag["as"] == "teach_back" and tag["attempt_id"] is None and tag["teach_back_id"]:
                # A teach-back's attempt comes when its conversation finishes, carrying the conversation's id.
                tag["attempt_id"] = repository.find_attempt_id_by_evidence_agent_run(
                    practice_item_id=tag["practice_item_id"], agent_run_id=tag["teach_back_id"],
                    attempt_type="teach_back")
    places = _Places(repository)
    return {
        "pad": _pad_out(row),
        "blocks": [{**_block_out(head, created.get(head["block_id"])),
                    "submissions": submitted.get(str(head["block_id"]), [])} for head in heads],
        "anchors": [{"event_id": a["event_id"], "block_id": a["block_id"], "extraction_id": a["extraction_id"],
                     "span_id": a["span_id"], "anchor": a["anchor"], "annotation_id": a["annotation_id"],
                     "created_at": a["created_at"], "inherited_from_block_id": a["inherited_from_block_id"],
                     **places.where(a["extraction_id"], a["span_id"])}
                    for a in anchors],
    }


def pad_list(repository: Any, *, desk_id: str | None = None, query: str | None = None, kept: bool | None = None,
             cursor: str | None = None) -> dict[str, Any]:
    """``pad.list``: pads most recently changed first, a page at a time, each with its first line."""

    after: tuple[str, str] | None = None
    if cursor:
        stamp, _, last = cursor.partition("|")
        after = (stamp, last)
    with repository.connection() as connection:
        rows = reads.list_pads(connection, desk_id=desk_id, kept=kept, query=(query or "").strip() or None,
                               after=after, page_size=PAGE_SIZE + 1)
        page = rows[:PAGE_SIZE]
        out = []
        for row in page:
            first = next((head for head in reads.heads(connection, row["pad_id"])
                          if not head["tombstone"] and str(head["body_md"] or "").strip()), None)
            out.append({**_pad_out(row),
                        "first_line": str(first["body_md"]).strip().splitlines()[0] if first else ""})
    next_cursor = f"{page[-1]['updated_at']}|{page[-1]['pad_id']}" if len(rows) > PAGE_SIZE else None
    return {"pads": out, "cursor": next_cursor}


# -- ops ----------------------------------------------------------------------------------------------

#: The client's fractional position keys (``F:screens/desks/pads/model.ts`` ``keyBetween``), ported so the server can
#: place a block between two others the same way: keys compare as plain strings and never end in the lowest digit.
_DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def _midpoint(a: str, b: str | None) -> str:
    if b is not None:
        n = 0
        while (a[n] if n < len(a) else _DIGITS[0]) == (b[n] if n < len(b) else None):
            n += 1
        if n > 0:
            if n >= len(b):
                raise ValueError("no key between them")
            return b[:n] + _midpoint(a[n:], b[n:])
    low = _DIGITS.index(a[0]) if a else 0
    high = _DIGITS.index(b[0]) if b is not None else len(_DIGITS)
    if high - low > 1:
        return _DIGITS[round((low + high) / 2)]
    if b is not None and len(b) > 1:
        return b[:1]
    return _DIGITS[low] + _midpoint(a[1:], None)


def key_between(a: str | None, b: str | None) -> str:
    """A position key strictly between ``a`` and ``b`` (either may be None: before or after everything)."""

    if a is not None and b is not None and a >= b:
        raise ValueError(f"no key between {a} and {b}")
    return _midpoint(a or "", b)


def _key_after(connection: Any, pad_id: str, head: dict[str, Any]) -> str:
    """A key right after ``head`` in its pad, before the next block; the head's own key when the next block shares
    it (equal keys order by block id: as close as the keys allow)."""

    here = str(head["position_key"])
    following = [str(other["position_key"]) for other in reads.heads(connection, pad_id)
                 if not other["tombstone"] and other["block_id"] != head["block_id"] and str(other["position_key"]) > here]
    try:
        return key_between(here, min(following) if following else None)
    except ValueError:
        return here


def _keep_both(connection: Any, pad_id: str, client_id: str, op: EditBlock, head: dict[str, Any],
               base: dict[str, Any], now: str, heads: dict[str, str]) -> dict[str, Any]:
    """A stale edit's words as a block of their own right after the current head; the head is left as it is."""

    keep = op.keep_both
    assert keep is not None
    if reads.head(connection, keep.block_id) is not None:
        raise OpRefused("block_exists", f"A block {keep.block_id!r} already exists.")
    payload = dict(op.payload if op.payload is not None else base["payload"])
    payload["conflict"] = {"of_block_id": op.block_id, "expected_head": op.expected_head,
                           "server_head_version_id": head["version_id"], "label": keep.label, "at": now}
    version_id = _version_id(connection, keep.version_id)
    store.insert_version(connection, {
        "version_id": version_id, "block_id": keep.block_id, "supersedes_id": None, "pad_id": pad_id,
        "position_key": _key_after(connection, pad_id, head), "day": head["day"], "kind": base["kind"],
        "body_md": op.body_md if op.body_md is not None else base["body_md"], "payload": payload,
        # An ink block's words typed over are the learner's correction, as an edit of it would be.
        "provenance": "learner_correction" if base["kind"] == "ink" else base["provenance"],
        "tombstone": False, "client_id": client_id, "created_at": now,
    })
    heads[keep.block_id] = version_id
    store.touch_pad(connection, pad_id, now)
    return {"head_version_id": head["version_id"],
            "kept_both": {"block_id": keep.block_id, "head_version_id": version_id}}



def _version_id(connection: Any, minted: str | None) -> str:
    if minted is None:
        return new_ulid()
    if reads.version_exists(connection, minted):
        raise OpRefused("version_exists", f"A block version {minted!r} already exists.")
    return minted


def _current_head(connection: Any, pad_id: str, block_id: str, expected: str | None) -> dict[str, Any]:
    head = reads.head(connection, block_id)
    if head is None:
        raise OpRefused("block_not_found", f"No block {block_id!r}.")
    if head["pad_id"] != pad_id:
        raise OpRefused("block_not_in_pad", "That block belongs to another pad.")
    if expected is not None and expected != head["version_id"]:
        raise OpConflict({"block_id": block_id, "head_version_id": head["version_id"]})
    return head


def _successor(head: dict[str, Any], version_id: str, client_id: str, now: str, **changes: Any) -> dict[str, Any]:
    row = {name: head[name] for name in ("block_id", "pad_id", "position_key", "day", "kind", "body_md", "provenance")}
    row.update(payload=head["payload"], tombstone=False)
    row.update(changes)
    row.update(version_id=version_id, supersedes_id=head["version_id"], client_id=client_id, created_at=now)
    return row


def _apply_pad_op(connection: Any, pad_id: str, client_id: str, op: Any, now: str,
                  heads: dict[str, str], versions: dict[str, int]) -> dict[str, Any] | None:
    pad = reads.pad(connection, pad_id)
    if isinstance(op, CreatePad):
        if pad is not None:
            raise OpConflict({"pad_id": pad_id, "version": int(pad["version"])})
        store.insert_pad(connection, pad_id=pad_id, kind=op.kind, title=op.title, home_desk_id=op.home_desk_id,
                         workbench_session_id=op.workbench_session_id, lesson_id=op.lesson_id, now=now)
        versions[pad_id] = 1
        return None
    if pad is None:
        raise OpRefused("pad_not_found", f"No pad {pad_id!r}.")
    if pad["archived_at"] is not None:
        raise OpRefused("pad_archived", "That pad is archived.")
    if isinstance(op, (SetTitle, Keep, Unkeep)):
        if int(op.expected_version) != int(pad["version"]):
            raise OpConflict({"pad_id": pad_id, "version": int(pad["version"])})
        fields = ({"title": op.title} if isinstance(op, SetTitle)
                  else {"kept": 1 if isinstance(op, Keep) else 0})
        versions[pad_id] = store.update_pad(connection, pad_id, fields, now)
        return None
    if isinstance(op, InsertBlock):
        existing = reads.head(connection, op.block_id)
        if existing is not None:
            raise OpConflict({"block_id": op.block_id, "head_version_id": existing["version_id"]})
        version_id = _version_id(connection, op.version_id)
        store.insert_version(connection, {
            "version_id": version_id, "block_id": op.block_id, "supersedes_id": None, "pad_id": pad_id,
            "position_key": op.position_key, "day": op.day, "kind": op.kind, "body_md": op.body_md,
            "payload": op.payload, "provenance": op.provenance, "tombstone": False, "client_id": client_id,
            "created_at": now,
        })
        heads[op.block_id] = version_id
        store.touch_pad(connection, pad_id, now)
        return {"head_version_id": version_id}
    if isinstance(op, EditBlock) and op.keep_both is not None:
        current = _current_head(connection, pad_id, op.block_id, None)
        if current["version_id"] != op.expected_head:
            # The words were typed over the version the client saw; the block may since have been removed or lifted
            # out, so their kind is that version's.
            seen = reads.version(connection, op.expected_head)
            base = seen if seen is not None and seen["block_id"] == op.block_id else current
            if base["kind"] not in EDITABLE_KINDS:
                raise OpRefused("not_editable", "This block quotes a source, the tutor or a figure; add a note under it.")
            return _keep_both(connection, pad_id, client_id, op, current, base, now, heads)
    if isinstance(op, (EditBlock, RemoveBlock, MoveBlock, LiftOut)):
        head = _current_head(connection, pad_id, op.block_id, op.expected_head)
        if head["tombstone"]:
            raise OpRefused("block_removed", "That block was removed.")
        version_id = _version_id(connection, op.stub_version_id if isinstance(op, LiftOut) else op.version_id)
        if isinstance(op, EditBlock):
            if head["kind"] not in EDITABLE_KINDS:
                raise OpRefused("not_editable", "This block quotes a source, the tutor or a figure; add a note under it.")
            changes: dict[str, Any] = {}
            if op.body_md is not None:
                changes["body_md"] = op.body_md
            if op.payload is not None:
                changes["payload"] = op.payload
            if head["kind"] == "ink":
                changes["provenance"] = "learner_correction"
            store.insert_version(connection, _successor(head, version_id, client_id, now, **changes))
        elif isinstance(op, RemoveBlock):
            store.insert_version(connection, _successor(head, version_id, client_id, now, tombstone=True))
        elif isinstance(op, MoveBlock):
            store.insert_version(connection, _successor(head, version_id, client_id, now, position_key=op.position_key))
        else:
            if reads.pad(connection, op.new_pad_id) is not None:
                raise OpRefused("pad_exists", f"A pad {op.new_pad_id!r} already exists.")
            if reads.head(connection, op.new_block_id) is not None:
                raise OpRefused("block_exists", f"A block {op.new_block_id!r} already exists.")
            if op.new_version_id is not None and op.new_version_id == version_id:
                raise OpRefused("id_collision", "The lifted block and the stub need two different version ids.")
            lifted_version = _version_id(connection, op.new_version_id)
            store.insert_pad(connection, pad_id=op.new_pad_id, kind="named", title=op.title,
                             home_desk_id=pad["home_desk_id"], workbench_session_id=None, lesson_id=None, now=now)
            store.insert_version(connection, {
                "version_id": lifted_version, "block_id": op.new_block_id, "supersedes_id": None,
                "pad_id": op.new_pad_id, "position_key": op.position_key, "day": head["day"], "kind": head["kind"],
                "body_md": head["body_md"], "payload": head["payload"], "provenance": head["provenance"],
                "tombstone": False, "client_id": client_id, "created_at": now,
            })
            store.insert_version(connection, _successor(
                head, version_id, client_id, now, kind="lifted", body_md="", provenance="learnloop",
                payload={"lifted_to_pad_id": op.new_pad_id, "lifted_block_id": op.new_block_id}))
            # The passages the block was linked to go with its words: the lifted block takes each standing link and
            # the stub gives it up, so a later wording's emission, its quote check and the passage's marks all find
            # them on the block that carries the words.
            for anchor in reads.standing_anchors_for_blocks(connection, [op.block_id]):
                for block_id, action in ((op.new_block_id, "link"), (op.block_id, "unlink")):
                    store.insert_anchor_event(
                        connection, event_id=new_ulid(), block_id=block_id, extraction_id=anchor["extraction_id"],
                        span_id=anchor["span_id"], anchor=anchor["anchor"] if action == "link" else {},
                        annotation_id=anchor["annotation_id"] if action == "link" else None, action=action, now=now)
            heads[op.new_block_id] = lifted_version
            versions[op.new_pad_id] = 1
        heads[op.block_id] = version_id
        store.touch_pad(connection, pad_id, now)
        return {"head_version_id": version_id}
    if isinstance(op, (LinkAnchor, UnlinkAnchor)):
        _current_head(connection, pad_id, op.block_id, None)
        latest = reads.latest_anchor_event(connection, op.block_id, op.extraction_id, op.span_id)
        current = latest["event_id"] if latest is not None else None
        if current != op.expected_anchor_head:
            raise OpConflict({"block_id": op.block_id, "extraction_id": op.extraction_id, "span_id": op.span_id,
                              "anchor_head": current})
        if isinstance(op, UnlinkAnchor) and (latest is None or latest["action"] != "link"):
            raise OpRefused("not_linked", "That block is not linked to that passage.")
        if op.event_id is not None and reads.anchor_event_exists(connection, op.event_id):
            raise OpRefused("event_exists", f"An anchor event {op.event_id!r} already exists.")
        event_id = op.event_id or new_ulid()
        store.insert_anchor_event(
            connection, event_id=event_id, block_id=op.block_id, extraction_id=op.extraction_id, span_id=op.span_id,
            anchor=op.anchor if isinstance(op, LinkAnchor) else {},
            annotation_id=op.annotation_id if isinstance(op, LinkAnchor) else None,
            action="link" if isinstance(op, LinkAnchor) else "unlink", now=now)
        store.touch_pad(connection, pad_id, now)
        return {"event_id": event_id}
    if isinstance(op, EraseInk):
        result = ink_core.erase_in_batch(connection, pad_id=pad_id, block_id=op.block_id, erase_id=op.erase_id,
                                         stroke_ids=list(op.stroke_ids), client_id=client_id, now=now)
        store.touch_pad(connection, pad_id, now)
        return result
    raise OpRefused("unknown_op", f"Unknown pad op {getattr(op, 'op', None)!r}.")  # pragma: no cover


def apply_pad_ops(repository: Any, *, client_id: str, seq: int, pad_id: str, ops: list[Any],
                  clock: Any = None) -> dict[str, Any]:
    """``pad.apply``: one batch on one pad, applied once and in order (``learnloop.desks.protocol``)."""

    request = {"pad_id": pad_id, "ops": [op.wire() for op in ops]}

    def apply(connection: Any, now: str) -> dict[str, Any]:
        heads: dict[str, str] = {}
        versions: dict[str, int] = {}
        results = [run_op(connection, lambda op=op: _apply_pad_op(connection, pad_id, client_id, op, now, heads,
                                                                  versions)) for op in ops]
        return {
            "results": results,
            "heads": [{"block_id": block_id, "head_version_id": version} for block_id, version in sorted(heads.items())],
            "pads": [{"pad_id": pad, "version": version} for pad, version in sorted(versions.items())],
        }

    return apply_batch(repository, channel=PAD, client_id=client_id, seq=seq, request=request, apply_ops=apply,
                       pad_id=pad_id, clock=clock)


__all__ = ["EDITABLE_KINDS", "PAD_OPS", "PAGE_SIZE", "PadNotFound", "PadOp", "apply_pad_ops", "pad_list", "pad_view"]
