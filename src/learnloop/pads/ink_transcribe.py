"""Reading the learner's ink (spec §10.10 "Transcription"): one image of an owner's standing strokes, sent to the
model routed for ``ink_transcription``, read as Markdown with LaTeX.

**The route.** ``ai.routing.ink_transcription`` (empty: the active provider, the ChatGPT plan), planned and resolved
like every paid role (``learnloop.practice_index.paid``): a ready plan serves first; with the plan unavailable the
learner is asked about OpenRouter and only their "Use OpenRouter instead" routes there (``learnloop.ai.plan_fallback``
enforces it in the planning, server-side); every request is held to the learner's one OK to use AI
(``learnloop.ai.model_use``, at admission). A route whose model cannot read images is refused before anything is sent
(``cannot_read_images``). A metered route is held to the workbench's price and daily envelope
(``workbench.price_per_million``, ``workbench.max_daily_cost_usd``), whose envelope counts these calls with the step
checks'.

**Sent:** the image and the instructions, nothing else (an isolated turn: no files, tools, vault or learner history).
The prompt names the image's sha256, so a paid answer's checkpoint never answers another image.

**Kept:** the reading, once per owner and standing strokes (``ink_transcriptions``, keyed by the strokes' hash): the
same strokes are never read twice and a retry spends nothing. ``confidence_label`` is ``may_be_wrong`` for every
reading (the spec's own words, "transcription may be wrong · fix it": a model's reading is never checked, and no
calibrated confidence exists to grade it by) and ``nothing_read`` when the model read no writing. A block owner's
reading also becomes the block's next version, provenance ``ink_transcription``, unless the block stands removed or
its words are the learner's correction of these same strokes (the learner's words are never overwritten); the
learner's later edit is a version of provenance ``learner_correction`` (``pads.blocks``). A margin note's reading is
returned and kept; the note's text is the annotation's own (the client writes it through the annotation's edit).

Help, never evidence: a reading is the learner's own words as LearnLoop read them, emitted as learner text marked as
transcribed (``pads.emission``), never graded.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from pydantic import Field

from learnloop.ai.execution import call_labels
from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendBudget, SpendCaps, spend_envelopes
from learnloop.ai.transport import IMAGE_INPUT, render_structured_prompt
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores import ink_strokes as store
from learnloop.db.stores import pad_reads
from learnloop.db.stores import pads as pad_store
from learnloop.ids import new_ulid
from learnloop.pads import ink as ink_core
from learnloop.pads import ink_render
from learnloop.practice_index.paid import PaidCalls, PaidRoute, plan_route, resolve_client
from learnloop.workbench import check as workbench_check

ROUTE_TASK = "ink_transcription"
OWNER_KIND = "ink_transcription"
PROMPT_VERSION = "ink_transcription.v1"
MAY_BE_WRONG, NOTHING_READ = "may_be_wrong", "nothing_read"
#: The client id on a block version LearnLoop wrote (a reading), never a client's.
SERVER_CLIENT_ID = "learnloop:ink_transcription"

INSTRUCTIONS = (
    "The attached image is one piece of a learner's handwriting, drawn with a pen on a tablet: a line of a "
    "derivation, a formula, words, or a mix. Write out exactly what is written, as Markdown with LaTeX math between "
    "$ signs ($$ for a displayed equation). Keep the learner's own notation, symbols, order and mistakes: never "
    "correct, complete, simplify or explain the writing. Where a mark cannot be read, write what it most likely is. "
    "If the image holds no writing, return an empty string."
)


class InkTranscriptionV1(WireModel):
    #: The writing as Markdown with LaTeX; empty when no writing can be read.
    latex_md: str = Field(max_length=20_000)


def build_prompt(image_sha256: str) -> str:
    return render_structured_prompt(
        "Transcribe handwriting", PROMPT_VERSION,
        # The image's digest goes last (the envelope puts "context" last), after the fixed instructions.
        {"instructions": INSTRUCTIONS, "context": {"image": {"media_type": ink_render.MEDIA_TYPE, "sha256": image_sha256}}},
    )


class InkUnavailable(Exception):
    """Nothing was read. ``reason``: ``models_off`` | ``unrouted`` | ``unpriced`` | ``capped`` | ``unavailable`` |
    ``cannot_read_images``; ``message`` is the learner's line."""

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


class InkRoute:
    """The reading's pinned route for one request (the step check's pattern: ``workbench.check.CheckRoute``)."""

    def __init__(self, vault: Any, repository: Repository, *, client: Any | None, envelope: Any, owner_id: str) -> None:
        self.vault = vault
        self.repository = repository
        self.injected = client
        self.envelope = envelope
        self.owner_id = owner_id
        self.route: PaidRoute = plan_route(vault, ROUTE_TASK, client)  # type: ignore[arg-type]
        self.client: Any | None = None
        self.calls: PaidCalls | None = None

    @property
    def subscription(self) -> bool:
        return self.route.billing == "subscription"

    def problem(self) -> InkUnavailable | None:
        section = self.vault.config.workbench
        if self.injected is None and workbench_check.models_off():
            return InkUnavailable("models_off", f"{workbench_check.MODELS_ENV}=off: no workbench model is reached.")
        if self.injected is None and not self.route.available:
            return InkUnavailable("unrouted", "No provider is routed to read handwriting (ai.routing.ink_transcription).")
        if not self.subscription and section.price_per_million is None:
            return InkUnavailable("unpriced", "A metered route needs workbench.price_per_million before it reads ink.")
        if not self.subscription and self.envelope is not None and self.envelope.remaining() <= 0:
            return InkUnavailable(
                "capped", f"Today's workbench budget (${float(section.max_daily_cost_usd):.2f}) is used.")
        return None

    def ask(self, prompt: str, image: bytes) -> InkTranscriptionV1:
        problem = self.problem()
        if problem is not None:
            raise problem
        if self.injected is not None:
            self.client = self.injected
        else:
            self.client, message = resolve_client(self.vault, self.route)
            if self.client is None:
                raise InkUnavailable("unavailable", message or "the handwriting model is not ready")
        if not self.client.supports(IMAGE_INPUT):
            raise InkUnavailable(
                "cannot_read_images",
                f"The model routed to read handwriting ({self.route.provider}) cannot read images, so nothing was sent.")
        budget = SpendBudget(SpendCaps(max_estimated_usd=None, **workbench_check.CALL_CAPS),
                             subscription=self.subscription)
        self.calls = PaidCalls(route=self.route, budget=budget, price_per_million=self.vault.config.workbench.price_per_million,
                               repository=self.repository, owner_kind=OWNER_KIND, owner_id=self.owner_id)
        with spend_envelopes(self.envelope):
            return self.calls.call(self.client, purpose=ROUTE_TASK, prompt=prompt, result_model=InkTranscriptionV1,
                                   output_tokens=self.route.output_tokens,
                                   metadata={"prompt_version": PROMPT_VERSION},
                                   images=((ink_render.MEDIA_TYPE, image),), isolated=True)

    @property
    def model(self) -> str | None:
        if self.calls is not None and self.calls.last_resolved_model:
            return self.calls.last_resolved_model
        return getattr(self.client, "model", None) or self.route.model


def _result(connection: Any, row: dict[str, Any], *, applied: bool | None = None, reason: str | None = None) -> dict[str, Any]:
    head_version_id = None
    if row["owner_kind"] == ink_core.BLOCK:
        head = pad_reads.head(connection, row["owner_id"])
        head_version_id = head["version_id"] if head is not None else None
        if applied is None:
            reading = ((head or {}).get("payload") or {}).get("ink_transcription") or {}
            applied = (head is not None and head["provenance"] == "ink_transcription"
                       and reading.get("transcription_id") == row["transcription_id"])
    return {
        "transcription_id": row["transcription_id"], "owner_kind": row["owner_kind"], "owner_id": row["owner_id"],
        "content_hash": row["content_hash"], "latex_md": row["latex_md"],
        "confidence_label": row["confidence_label"], "model": row["model"], "created_at": row["created_at"],
        "applied": bool(applied), "reason": reason, "head_version_id": head_version_id,
    }


def _apply_to_block(connection: Any, row: dict[str, Any], now: str) -> tuple[bool, str | None]:
    """Write the reading as the block's next version, or say why not (the caller's transaction)."""

    head = pad_reads.head(connection, row["owner_id"])
    if head is None or head["tombstone"]:
        return False, "block_removed"
    reading = (head.get("payload") or {}).get("ink_transcription") or {}
    if reading.get("content_hash") == row["content_hash"]:
        if head["provenance"] == "learner_correction":
            return False, "kept_your_correction"
        return True, None
    if head["provenance"] == "learner_correction":
        # The learner's words stand; the new reading is kept and returned for the client to offer.
        return False, "kept_your_correction"
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


def transcribe(vault: Any, repository: Repository, prepared: Prepared, *, client: Any | None = None,
               clock: Clock | None = None) -> dict[str, Any]:
    """Read the strokes (or return their reading, spending nothing) and keep it. Raises ``InkUnavailable`` when
    nothing could be read, ``ink_render.InkTooLarge`` when the strokes cannot be drawn."""

    earlier = stored(repository, prepared)
    if earlier is not None:
        return earlier
    image = render(prepared)
    digest = hashlib.sha256(image).hexdigest()
    route = InkRoute(vault, repository, client=client, envelope=workbench_check.daily_envelope(vault, repository, clock=clock),
                     owner_id=f"{prepared.owner_kind}:{prepared.owner_id}:{prepared.content_hash}")
    with call_labels(judge="llm", question_set_version=PROMPT_VERSION):
        output = route.ask(build_prompt(digest), image)
    latex_md = output.latex_md.strip()
    now = utc_now_iso(clock)
    row = {
        "transcription_id": "it_" + new_ulid(), "owner_kind": prepared.owner_kind, "owner_id": prepared.owner_id,
        "content_hash": prepared.content_hash, "latex_md": latex_md,
        "confidence_label": MAY_BE_WRONG if latex_md else NOTHING_READ, "task": ROUTE_TASK,
        "provider": route.route.provider, "model": route.model, "prompt_version": PROMPT_VERSION, "created_at": now,
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


__all__ = ["INSTRUCTIONS", "InkRoute", "InkTranscriptionV1", "InkUnavailable", "MAY_BE_WRONG", "NOTHING_READ",
           "OWNER_KIND", "PROMPT_VERSION", "Prepared", "ROUTE_TASK", "build_prompt", "prepare", "render", "stored",
           "transcribe"]
