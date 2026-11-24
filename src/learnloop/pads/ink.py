"""The learner's ink (spec §10.10, §15.1): ``ink.save``, the ``erase_ink`` pad op and the reads that return an owner's
strokes as they stand.

An owner is a pad block of kind ``ink`` (a freewrite line) or a source annotation (a handwritten margin note). Each
save is one row of ``ink_strokes`` with a client-minted ``ink_id``: the strokes the client flushed, each with a
client-minted ``stroke_id`` and its points ``[x, y, t, pressure, tilt_x, tilt_y]`` (CSS pixels of the surface the
pen drew on, milliseconds, and the Pointer Events ranges: pressure 0 to 1, tilt -90 to 90 degrees). An erase is a row
naming earlier strokes' ids (the pen's barrel button). An owner's ink as it stands is every save's strokes in write
order without the erased ones; its ``content_hash`` names exactly those strokes, and a transcription is keyed by it.

Storage is lossless: the points are kept as the client sent them (``zlib-json-v1``: zlib over their canonical JSON),
so nothing here rounds or thins a stroke. ``ink.save`` follows the write protocol (``learnloop.desks.protocol``) and
shares the client's one batch numbering with ``desk.apply`` and ``pad.apply`` (spec §3.5: one outbox); its receipt
is a pad-channel receipt, filed under the owning block's pad ('' for a margin note's ink). Workflow data and the
learner's own writing, never evidence.
"""
from __future__ import annotations

import hashlib
import json
import zlib
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from learnloop.db.stores import ink_strokes as store
from learnloop.db.stores import pad_reads
from learnloop.db.stores.workspace_batches import PAD
from learnloop.desks.content_ref import WireModel
from learnloop.desks.protocol import OpRefused, apply_batch, run_op
from learnloop.ids import new_ulid

ENCODING = "zlib-json-v1"
BLOCK, ANNOTATION, SOURCE = "block", "annotation", "source"
STROKES, ERASE = "strokes", "erase"
#: The Pointer Events ranges a point's pressure and tilts are given in.
PRESSURE_RANGE = (0.0, 1.0)
TILT_RANGE = (-90.0, 90.0)


class InkError(LookupError):
    """An ink request that cannot be served (``code`` names why)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class InkStroke(WireModel):
    stroke_id: str = Field(min_length=1, max_length=128)
    #: ``[x, y, t, pressure, tilt_x, tilt_y]`` per point, in drawing order.
    points: tuple[tuple[float, float, float, float, float, float], ...] = Field(min_length=1)

    @field_validator("points")
    @classmethod
    def _finite_and_in_range(cls, points: tuple[tuple[float, ...], ...]) -> tuple[tuple[float, ...], ...]:
        for point in points:
            if any(value != value or value in (float("inf"), float("-inf")) for value in point):
                raise ValueError("a point's values are finite numbers")
            if not PRESSURE_RANGE[0] <= point[3] <= PRESSURE_RANGE[1]:
                raise ValueError("pressure is between 0 and 1")
            if not all(TILT_RANGE[0] <= tilt <= TILT_RANGE[1] for tilt in point[4:6]):
                raise ValueError("tilt is between -90 and 90 degrees")
        return points


class PointerMeta(WireModel):
    """How the strokes were drawn: the pointer (touch never draws, spec §10.10) and the screen's device pixel ratio
    (the resolution the learner saw them at, which the server renders them at; unknown, one device pixel per CSS
    pixel)."""

    pointer_type: Literal["pen", "mouse"]
    device_pixel_ratio: float = Field(default=1.0, gt=0, allow_inf_nan=False)


class InkOwner(WireModel):
    """One block, one annotation, or one reading of a source (``extraction_id``: ink drawn on the page that became
    no mark; it is the learner's marks, never read or emitted)."""

    block_id: str | None = Field(default=None, min_length=1)
    annotation_id: str | None = Field(default=None, min_length=1)
    extraction_id: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _exactly_one(self) -> "InkOwner":
        if sum(value is not None for value in (self.block_id, self.annotation_id, self.extraction_id)) != 1:
            raise ValueError("ink belongs to one block, one annotation or one reading")
        return self

    @property
    def kind(self) -> str:
        return BLOCK if self.block_id is not None else ANNOTATION if self.annotation_id is not None else SOURCE

    @property
    def id(self) -> str:
        return str(self.block_id or self.annotation_id or self.extraction_id)

    @staticmethod
    def of(owner_kind: str, owner_id: str) -> "InkOwner":
        return InkOwner(**{{BLOCK: "block_id", ANNOTATION: "annotation_id", SOURCE: "extraction_id"}[owner_kind]: owner_id})


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def content_hash(value: Any) -> str:
    """The sha256 of ``value``'s canonical JSON: what a save's retry and a reading's reuse compare."""

    return hashlib.sha256(canonical(value)).hexdigest()


def encode(value: Any) -> bytes:
    return zlib.compress(canonical(value))


def decode(blob: bytes) -> Any:
    return json.loads(zlib.decompress(bytes(blob)).decode("utf-8"))


def _strokes_value(strokes: list[InkStroke]) -> list[dict[str, Any]]:
    return [{"stroke_id": stroke.stroke_id, "points": [list(point) for point in stroke.points]} for stroke in strokes]


def standing(saves: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], float]:
    """An owner's strokes as they stand (each with the ``ink_id`` that saved it) and the finest device pixel ratio
    they were drawn at."""

    strokes: list[dict[str, Any]] = []
    erased: set[str] = set()
    ratio = 0.0
    for row in saves:
        if row["kind"] == ERASE:
            erased.update(str(stroke_id) for stroke_id in decode(row["strokes_blob"]))
            continue
        ratio = max(ratio, float((row.get("pointer_meta") or {}).get("device_pixel_ratio") or 1.0))
        strokes.extend({**stroke, "ink_id": row["ink_id"]} for stroke in decode(row["strokes_blob"]))
    kept = [stroke for stroke in strokes if stroke["stroke_id"] not in erased]
    return kept, ratio or 1.0


def strokes_hash(strokes: list[dict[str, Any]]) -> str:
    """The hash of standing strokes (ids and points, in order): a reading of them is keyed by it."""

    return content_hash([{"stroke_id": s["stroke_id"], "points": s["points"]} for s in strokes])


def _owner_pad(connection: Any, owner: InkOwner) -> str:
    """The pad of a block owner ('' for an annotation), checking the owner can take ink."""

    if owner.kind == ANNOTATION:
        if not store.annotation_exists(connection, owner.id):
            raise OpRefused("annotation_not_found", f"No annotation {owner.id!r}.")
        return ""
    if owner.kind == SOURCE:
        if not store.extraction_exists(connection, owner.id):
            raise OpRefused("reading_not_found", f"No reading {owner.id!r}.")
        return ""
    head = pad_reads.head(connection, owner.id)
    if head is None:
        raise OpRefused("block_not_found", f"No block {owner.id!r}.")
    if head["tombstone"]:
        raise OpRefused("block_removed", "That block was removed.")
    if head["kind"] != "ink":
        raise OpRefused("not_an_ink_block", "Ink goes in an ink block.")
    pad = pad_reads.pad(connection, head["pad_id"])
    if pad is not None and pad["archived_at"] is not None:
        raise OpRefused("pad_archived", "That pad is archived.")
    return str(head["pad_id"])


def _receipt_pad(repository: Any, owner: InkOwner) -> str:
    if owner.kind != BLOCK:
        return ""
    with repository.connection() as connection:
        head = pad_reads.head(connection, owner.id)
    return str(head["pad_id"]) if head is not None else ""


def save_ink(repository: Any, *, client_id: str, seq: int, owner: InkOwner, ink_id: str, strokes: list[InkStroke],
             pointer_meta: PointerMeta, clock: Any = None) -> dict[str, Any]:
    """``ink.save``: one batch holding one save, applied once and in order: ``{applied_seq, ink_id, results}``."""

    value = _strokes_value(strokes)
    digest = content_hash(value)
    request = {"ink_save": {"owner": owner.wire(), "ink_id": ink_id, "content_hash": digest,
                            "pointer_meta": pointer_meta.wire()}}

    def apply(connection: Any, now: str) -> dict[str, Any]:
        def one() -> dict[str, Any]:
            existing = store.save(connection, ink_id)
            if existing is not None:
                if (existing["owner_kind"], existing["owner_id"], existing["kind"], existing["content_hash"]) != (
                        owner.kind, owner.id, STROKES, digest):
                    raise OpRefused("ink_id_reused", f"Ink {ink_id!r} was already saved with other strokes.")
                return {"duplicate": True}
            _owner_pad(connection, owner)
            have = {stroke["stroke_id"] for row in store.owner_saves(connection, owner.kind, owner.id)
                    if row["kind"] == STROKES for stroke in decode(row["strokes_blob"])}
            clash = sorted(have & {stroke["stroke_id"] for stroke in value})
            if clash:
                raise OpRefused("stroke_exists", f"Stroke {clash[0]!r} is already saved for this owner.")
            store.insert_save(connection, {
                "ink_id": ink_id, "owner_kind": owner.kind, "owner_id": owner.id, "kind": STROKES,
                "encoding": ENCODING, "strokes_blob": encode(value), "content_hash": digest,
                "stroke_count": len(value), "pointer_meta": pointer_meta.wire(), "client_id": client_id,
                "created_at": now,
            })
            return {"duplicate": False}

        return {"ink_id": ink_id, "results": [run_op(connection, one)]}

    return apply_batch(repository, channel=PAD, client_id=client_id, seq=seq, request=request, apply_ops=apply,
                       pad_id=_receipt_pad(repository, owner), clock=clock)


def erase_in_batch(connection: Any, *, pad_id: str, block_id: str, erase_id: str | None, stroke_ids: list[str],
                   client_id: str, now: str) -> dict[str, Any]:
    """The ``erase_ink`` pad op, inside the pad batch's transaction: a tombstone over standing strokes of one ink
    block of this pad. Raises ``OpRefused`` when it cannot apply."""

    owner = InkOwner(block_id=block_id)
    if _owner_pad(connection, owner) != pad_id:
        raise OpRefused("block_not_in_pad", "That block belongs to another pad.")
    erase_id = erase_id or new_ulid()
    if store.save(connection, erase_id) is not None:
        raise OpRefused("ink_id_exists", f"Ink {erase_id!r} already exists.")
    strokes, _ratio = standing(store.owner_saves(connection, BLOCK, block_id))
    present = {stroke["stroke_id"] for stroke in strokes}
    missing = [stroke_id for stroke_id in stroke_ids if stroke_id not in present]
    if missing:
        raise OpRefused("stroke_not_found", "That mark is already gone.")
    value = sorted(set(stroke_ids))
    store.insert_save(connection, {
        "ink_id": erase_id, "owner_kind": BLOCK, "owner_id": block_id, "kind": ERASE, "encoding": ENCODING,
        "strokes_blob": encode(value), "content_hash": content_hash(value), "stroke_count": len(value),
        "pointer_meta": {}, "client_id": client_id, "created_at": now,
    })
    return {"erase_id": erase_id, "standing": len(present - set(value))}


def copy_to_lifted(connection: Any, *, from_block_id: str, to_block_id: str, client_id: str, now: str) -> None:
    """A lifted ink line's handwriting (``lift_out``, inside the pad batch): the standing strokes of the block it was
    lifted from, saved again for the lifted block (the same stroke ids and points, so the same hash), and the
    reading of exactly those strokes kept for it too, so nothing is read or paid for again."""

    strokes, ratio = standing(store.owner_saves(connection, BLOCK, from_block_id))
    if not strokes:
        return
    value = [{"stroke_id": stroke["stroke_id"], "points": stroke["points"]} for stroke in strokes]
    store.insert_save(connection, {
        "ink_id": f"{to_block_id}:lifted", "owner_kind": BLOCK, "owner_id": to_block_id, "kind": STROKES,
        "encoding": ENCODING, "strokes_blob": encode(value), "content_hash": content_hash(value),
        "stroke_count": len(value), "pointer_meta": {"device_pixel_ratio": ratio}, "client_id": client_id,
        "created_at": now,
    })
    digest = strokes_hash(strokes)
    kept = store.reading_for(connection, BLOCK, from_block_id, digest)
    if kept is not None:
        store.insert_reading(connection, {**kept, "transcription_id": f"{kept['transcription_id']}>{to_block_id}",
                                          "owner_id": to_block_id, "created_at": now})


def _insert_erase(connection: Any, owner: InkOwner, erase_id: str, stroke_ids: list[str], client_id: str, now: str) -> None:
    if store.save(connection, erase_id) is not None:
        raise OpRefused("ink_id_exists", f"Ink {erase_id!r} already exists.")
    strokes, _ratio = standing(store.owner_saves(connection, owner.kind, owner.id))
    present = {stroke["stroke_id"] for stroke in strokes}
    missing = [stroke_id for stroke_id in stroke_ids if stroke_id not in present]
    if missing:
        raise OpRefused("stroke_not_found", "That mark is already gone.")
    value = sorted(set(stroke_ids))
    store.insert_save(connection, {
        "ink_id": erase_id, "owner_kind": owner.kind, "owner_id": owner.id, "kind": ERASE, "encoding": ENCODING,
        "strokes_blob": encode(value), "content_hash": content_hash(value), "stroke_count": len(value),
        "pointer_meta": {}, "client_id": client_id, "created_at": now,
    })


def erase_ink(repository: Any, *, client_id: str, seq: int, owner: InkOwner, erase_id: str, stroke_ids: list[str],
              clock: Any = None) -> dict[str, Any]:
    """``ink.erase``: one batch erasing strokes of an annotation's or a reading's ink (a block's ink is erased by
    ``pad.apply``'s ``erase_ink``, in its pad's batch). A retried erase id naming the same strokes is a no-op."""

    value = sorted(set(stroke_ids))
    request = {"ink_erase": {"owner": owner.wire(), "erase_id": erase_id, "stroke_ids": value}}

    def apply(connection: Any, now: str) -> dict[str, Any]:
        def one() -> dict[str, Any]:
            if owner.kind == BLOCK:
                raise OpRefused("erase_in_the_pad", "Open the pad to erase this mark.")
            existing = store.save(connection, erase_id)
            if existing is not None:
                if (existing["owner_kind"], existing["owner_id"], existing["kind"], existing["content_hash"]) != (
                        owner.kind, owner.id, ERASE, content_hash(value)):
                    raise OpRefused("ink_id_reused", f"Ink {erase_id!r} was already used for something else.")
                return {"duplicate": True}
            _owner_pad(connection, owner)
            _insert_erase(connection, owner, erase_id, value, client_id, now)
            return {"duplicate": False}

        return {"erase_id": erase_id, "results": [run_op(connection, one)]}

    return apply_batch(repository, channel=PAD, client_id=client_id, seq=seq, request=request, apply_ops=apply,
                       pad_id="", clock=clock)


def owner_of(connection: Any, ink_id: str) -> InkOwner:
    row = store.save(connection, ink_id)
    if row is None:
        raise InkError("ink_not_found", f"No ink {ink_id!r}.")
    return InkOwner.of(row["owner_kind"], row["owner_id"])


def reading_decision(connection: Any, row: dict[str, Any]) -> tuple[str, str | None]:
    """What a block's reading does to its block, now: ``applied`` (it is the head's words), ``write`` (it becomes
    them), or ``refused`` with why (the block removed, the learner's words standing, or strokes that changed since
    they were read: a reading finishing after a newer one never replaces it)."""

    head = pad_reads.head(connection, row["owner_id"])
    if head is None or head["tombstone"]:
        return "refused", "block_removed"
    reading = (head.get("payload") or {}).get("ink_transcription") or {}
    if head["provenance"] == "ink_transcription" and reading.get("content_hash") == row["content_hash"]:
        # The head's words are the reading of these strokes (a lifted line's copy of the reading included).
        return "applied", None
    if head["provenance"] == "learner_correction":
        # The learner's words stand; the new reading is kept and returned for the client to offer.
        return "refused", "kept_your_correction"
    strokes, _ratio = standing(store.owner_saves(connection, BLOCK, row["owner_id"]))
    if strokes_hash(strokes) != row["content_hash"]:
        return "refused", "strokes_changed"
    return "write", None


def owner_view(connection: Any, owner_kind: str, owner_id: str) -> dict[str, Any]:
    """One owner's standing strokes, their hash and its reading (``current`` when it read exactly these strokes)."""

    strokes, ratio = standing(store.owner_saves(connection, owner_kind, owner_id))
    digest = strokes_hash(strokes)
    reading = store.latest_reading(connection, owner_kind, owner_id)
    decision, reason = (reading_decision(connection, reading) if reading is not None and owner_kind == BLOCK
                        else (None, None))
    return {
        "owner_kind": owner_kind, "owner_id": owner_id, "content_hash": digest, "device_pixel_ratio": ratio,
        "strokes": [{"stroke_id": s["stroke_id"], "ink_id": s["ink_id"], "points": s["points"]} for s in strokes],
        "transcription": None if reading is None else {
            "transcription_id": reading["transcription_id"], "latex_md": reading["latex_md"],
            "confidence_label": reading["confidence_label"], "content_hash": reading["content_hash"],
            "current": reading["content_hash"] == digest, "created_at": reading["created_at"],
            # Why a block's reading is not its words (the learner's correction standing, ...), so an offer of it
            # survives a reload; None when it is, or for a margin note's reading.
            "applied": decision == "applied", "reason": reason},
    }


def ink_for_pad(repository: Any, pad_id: str) -> list[dict[str, Any]]:
    """The ink of a pad's standing ink blocks, in the pad's block order."""

    with repository.connection() as connection:
        if pad_reads.pad(connection, pad_id) is None:
            raise InkError("pad_not_found", f"No pad {pad_id!r}.")
        blocks = [str(head["block_id"]) for head in pad_reads.heads(connection, pad_id)
                  if not head["tombstone"] and head["kind"] == "ink"]
        with_ink = set(store.owners_with_ink(connection, BLOCK, blocks))
        return [owner_view(connection, BLOCK, block_id) for block_id in blocks if block_id in with_ink]


def ink_for_source(repository: Any, source_id: str) -> list[dict[str, Any]]:
    """The ink of a source's listed annotations (a deleted annotation's ink is not listed), then the ink on its
    readings' pages (owner kind ``source``, one owner per reading, never read)."""

    annotation_ids = [str(head["annotation"]["id"]) for head in repository.annotations_for_source(source_id)]
    with repository.connection() as connection:
        with_ink = set(store.owners_with_ink(connection, ANNOTATION, annotation_ids))
        owners = [owner_view(connection, ANNOTATION, annotation_id) for annotation_id in annotation_ids
                  if annotation_id in with_ink]
        readings = store.source_extraction_ids(connection, source_id)
        on_pages = set(store.owners_with_ink(connection, SOURCE, readings))
        return owners + [owner_view(connection, SOURCE, extraction_id) for extraction_id in readings
                         if extraction_id in on_pages]


__all__ = [
    "ANNOTATION", "BLOCK", "ENCODING", "ERASE", "SOURCE", "erase_ink", "InkError", "InkOwner", "InkStroke", "PointerMeta", "STROKES",
    "canonical", "content_hash", "decode", "encode", "erase_in_batch", "ink_for_pad", "ink_for_source", "owner_of",
    "copy_to_lifted", "owner_view", "reading_decision", "save_ink", "standing", "strokes_hash",
]
