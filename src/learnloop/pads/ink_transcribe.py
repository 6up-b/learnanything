"""Reading the learner's ink (spec §10.10 "Transcription"): one image of an owner's standing strokes, read by
GLM-OCR, the text recognition ingest uses for page images, and kept as GLM-OCR returns it.

**The reader** (owner decision, 2026-11-23: "this should get passed to glm-ocr then passed as text directly").
GLM-OCR runs where ingest would run it for a page image (``ingest.extractors.glm_ocr.selected_backend`` on
``[ingest.pdf.glm_ocr]``): z.ai's hosted pipeline when a key is set, or the self-hosted server with
``backend = "local"`` when it answers. The image goes through the extractor's one entry for an image
(``GlmOcrDocumentExtractor.recognise_image``): the same request, admission, receipt, retries and price
(``price_per_million_tokens``) as a document page. The text it recognises becomes the reading directly: no model
rewrites, completes or interprets it.

**Admission, as ingest admits a page image.** Hosted: the learner's one OK to use AI (``learnloop.ai.model_use``) and
the separate OK for sending a file to z.ai (``whole_files_zai``, the one a book's card asks for); without it nothing
is sent and the line says how to give it. Local: the self-hosted server reads it and nothing is asked, as for a page
image.
Neither: nothing is sent, and the line says how to turn text recognition on (Settings, under Ingestion).

**Sent:** the image, nothing else. **Kept:** the reading, once per owner and standing strokes
(``ink_transcriptions``, keyed by the strokes' hash): the same strokes are never read twice and a retry spends
nothing. ``confidence_label`` is ``may_be_wrong`` for every reading (the spec's "transcription may be wrong · fix
it": GLM-OCR gives no calibrated confidence) and ``nothing_read`` when it recognised no text. A block owner's reading
also becomes the block's next version, provenance ``ink_transcription``, while its strokes still stand and unless the
block stands removed or its words are the learner's correction (``pads.ink.reading_decision``); the learner's later
edit is a version of provenance ``learner_correction`` (``pads.blocks``). A margin note's reading is returned and
kept; the note's text is the annotation's own (the client writes it through the annotation's edit).

Help, never evidence: a reading is the learner's own words as LearnLoop read them, emitted as learner text marked as
transcribed (``pads.emission``), never graded.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from learnloop.ai import model_use
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores import ink_strokes as store
from learnloop.db.stores import pad_reads
from learnloop.db.stores import pads as pad_store
from learnloop.ids import new_ulid
from learnloop.pads import ink as ink_core
from learnloop.pads import ink_render

#: The reading's task on its kept row (``ink_transcriptions.task``), whoever reads.
TASK = "ink_transcription"
MAY_BE_WRONG, NOTHING_READ = "may_be_wrong", "nothing_read"
#: The client id on a block version LearnLoop wrote (a reading), never a client's.
SERVER_CLIENT_ID = "learnloop:ink_transcription"
#: The upload a hosted reading needs the learner's OK for: z.ai's, the same as a page image's.
UPLOAD_FLOW = "glm_ocr_upload"

TURN_ON_MESSAGE = (
    "Handwriting can't be read yet: text recognition (GLM-OCR) isn't set up. To add it, paste a z.ai API key in "
    "Settings, under Ingestion, or run a local GLM-OCR server."
)
NEEDS_OK_MESSAGE = (
    "Reading your handwriting with GLM-OCR sends a picture of it to z.ai, which needs your OK first. Say OK on a "
    "book's card in the Library (the same OK covers both), or use a local GLM-OCR server (Settings, under Ingestion)."
)


class InkUnavailable(Exception):
    """Nothing was read and nothing was sent. ``reason``: ``unavailable`` (no GLM-OCR set up) | ``needs_upload_ok``
    (hosted, without the learner's OK for z.ai); ``message`` is the learner's line."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason
        self.message = message


@dataclass(frozen=True)
class Prepared:
    """What one reading reads: an owner's standing strokes, their hash and the resolution they were drawn at."""

    owner_kind: str
    owner_id: str
    content_hash: str
    strokes: tuple[dict[str, Any], ...]
    device_pixel_ratio: float

    @property
    def key(self) -> str:
        return f"{self.owner_kind}:{self.owner_id}:{self.content_hash}"


def prepare(repository: Repository, ink_id: str) -> Prepared:
    """The strokes ``ink_id``'s owner holds now (every save of that owner, not only this one), or ``InkError``."""

    with repository.connection() as connection:
        owner = ink_core.owner_of(connection, ink_id)
        if owner.kind == ink_core.SOURCE:
            # Ink on a page is the learner's marks: never read, never learner text, unless they make it a note.
            raise ink_core.InkError("not_read", "Ink drawn on a page is kept as your marks and is not read.")
        if owner.kind == ink_core.BLOCK:
            head = pad_reads.head(connection, owner.id)
            if head is None or head["tombstone"]:
                raise ink_core.InkError("block_removed", "That ink's block was removed.")
        elif not store.annotation_exists(connection, owner.id):
            raise ink_core.InkError("annotation_not_found", "That ink's note is gone.")
        strokes, ratio = ink_core.standing(store.owner_saves(connection, owner.kind, owner.id))
    if not strokes:
        raise ink_core.InkError("nothing_to_read", "Every stroke here was erased; there is nothing to read.")
    return Prepared(owner.kind, owner.id, ink_core.strokes_hash(strokes), tuple(strokes), ratio)


def stored(repository: Repository, prepared: Prepared) -> dict[str, Any] | None:
    with repository.connection() as connection:
        row = store.reading_for(connection, prepared.owner_kind, prepared.owner_id, prepared.content_hash)
        return None if row is None else _result(connection, row)


def render(prepared: Prepared) -> bytes:
    paper = ink_render.PAD_PAPER if prepared.owner_kind == ink_core.BLOCK else ink_render.SOURCE_PAPER
    return ink_render.render_png(list(prepared.strokes), device_pixel_ratio=prepared.device_pixel_ratio, paper=paper)


class InkReader:
    """GLM-OCR as ingest would run it for a page image now: the backend it selects, and its admission."""

    def __init__(self, vault: Any) -> None:
        from learnloop.ingest.extractors.glm_ocr import selected_backend

        self.vault = vault
        self.settings = vault.config.ingest.pdf.glm_ocr.model_dump()
        self.backend = selected_backend(self.settings)
        self.extractor: Any | None = None

    def read(self, image: bytes) -> str:
        """The text GLM-OCR recognises in ``image``, unchanged. Raises ``InkUnavailable`` (nothing sent) when it
        cannot run or may not send, ``model_use.ModelUseNotAccepted`` before the learner's OK to use AI."""

        from learnloop.content.pipeline.add_source import file_upload_allowed
        from learnloop.ingest.extractors.glm_ocr import GlmOcrDocumentExtractor

        if self.backend is None:
            raise InkUnavailable("unavailable", TURN_ON_MESSAGE)
        upload_allowed = True
        if self.backend == "api":
            model_use.require(self.vault.root)
            upload_allowed = file_upload_allowed(self.vault.config, UPLOAD_FLOW)
            if not upload_allowed:
                raise InkUnavailable("needs_upload_ok", NEEDS_OK_MESSAGE)
        self.extractor = GlmOcrDocumentExtractor(config=self.settings, backend=self.backend)
        return self.extractor.recognise_image(image, upload_allowed=upload_allowed)

    @property
    def provider(self) -> str | None:
        return getattr(self.extractor, "provider_name", None)

    @property
    def version(self) -> str:
        """What read it, on the kept row (``prompt_version``: a reader's version; no prompt is sent)."""

        from learnloop.ingest.extractors.glm_ocr import LAYOUT_MODEL, RECOGNITION_MODEL

        return f"glm_ocr:{RECOGNITION_MODEL}+{LAYOUT_MODEL}+{self.backend}"


def _result(connection: Any, row: dict[str, Any], *, applied: bool | None = None, reason: str | None = None) -> dict[str, Any]:
    head_version_id = None
    if row["owner_kind"] == ink_core.BLOCK:
        head = pad_reads.head(connection, row["owner_id"])
        head_version_id = head["version_id"] if head is not None else None
        if applied is None:
            # A reading answered again (kept, or raced): what it does to the block now, and why not.
            decision, reason = ink_core.reading_decision(connection, row)
            applied = decision == "applied"
    return {
        "transcription_id": row["transcription_id"], "owner_kind": row["owner_kind"], "owner_id": row["owner_id"],
        "content_hash": row["content_hash"], "latex_md": row["latex_md"],
        "confidence_label": row["confidence_label"], "model": row["model"], "created_at": row["created_at"],
        "applied": bool(applied), "reason": reason, "head_version_id": head_version_id,
    }


def _apply_to_block(connection: Any, row: dict[str, Any], now: str) -> tuple[bool, str | None]:
    """Write the reading as the block's next version, or say why not (the caller's transaction)."""

    decision, reason = ink_core.reading_decision(connection, row)
    if decision != "write":
        return decision == "applied", reason
    head = pad_reads.head(connection, row["owner_id"])
    pad_store.insert_version(connection, {
        "version_id": new_ulid(), "block_id": head["block_id"], "supersedes_id": head["version_id"],
        "pad_id": head["pad_id"], "position_key": head["position_key"], "day": head["day"], "kind": head["kind"],
        "body_md": row["latex_md"], "provenance": "ink_transcription", "tombstone": False,
        "payload": {**(head.get("payload") or {}), "ink_transcription": {
            "transcription_id": row["transcription_id"], "content_hash": row["content_hash"],
            "confidence_label": row["confidence_label"]}},
        "client_id": SERVER_CLIENT_ID, "created_at": now,
    })
    pad_store.touch_pad(connection, head["pad_id"], now)
    return True, None


def transcribe(vault: Any, repository: Repository, prepared: Prepared, *, clock: Clock | None = None) -> dict[str, Any]:
    """Read the strokes (or return their reading, spending nothing) and keep it. Raises ``InkUnavailable`` when
    nothing could be sent, ``ink_render.InkTooLarge`` when the strokes cannot be drawn, and GLM-OCR's own errors
    (``GlmOcrExtractionError``) when it could not read them."""

    from learnloop.ingest.extractors.glm_ocr import RECOGNITION_MODEL

    earlier = stored(repository, prepared)
    if earlier is not None:
        return earlier
    reader = InkReader(vault)
    # The recognised text is the reading as it is: never rewritten, trimmed or interpreted here.
    latex_md = reader.read(render(prepared))
    now = utc_now_iso(clock)
    row = {
        "transcription_id": "it_" + new_ulid(), "owner_kind": prepared.owner_kind, "owner_id": prepared.owner_id,
        "content_hash": prepared.content_hash, "latex_md": latex_md,
        "confidence_label": MAY_BE_WRONG if latex_md.strip() else NOTHING_READ, "task": TASK,
        "provider": reader.provider, "model": RECOGNITION_MODEL, "prompt_version": reader.version, "created_at": now,
    }
    with repository.atomic():
        connection = repository.connection()
        raced = store.reading_for(connection, prepared.owner_kind, prepared.owner_id, prepared.content_hash)
        if raced is not None:
            return _result(connection, raced)
        store.insert_reading(connection, row)
        applied, reason = (_apply_to_block(connection, row, now) if prepared.owner_kind == ink_core.BLOCK
                           else (False, None))
        return _result(connection, row, applied=applied, reason=reason)


__all__ = ["InkReader", "InkUnavailable", "MAY_BE_WRONG", "NEEDS_OK_MESSAGE", "NOTHING_READ", "Prepared", "TASK",
           "TURN_ON_MESSAGE", "UPLOAD_FLOW", "prepare", "render", "stored", "transcribe"]
