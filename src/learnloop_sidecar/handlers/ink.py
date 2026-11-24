"""Reader workbench v2 RPCs: pen and ink (spec §3.4, §10.10). ``ink.save`` (a write batch), ``ink.list`` (the ink of a
pad or of a source's margin notes) and ``ink.transcribe`` / ``ink.transcribe_job`` / ``ink.transcribe_cancel`` (a
reading of an owner's standing strokes as a polled job).

**Saving** follows the write protocol (``learnloop.desks.protocol``): ``{client_id, seq, owner, ink_id, strokes,
pointer_meta}``, numbered in the client's one sequence with ``desk.apply`` and ``pad.apply``; a retried batch returns
its stored reply, and a retried ``ink_id`` with the same strokes is a no-op (``duplicate``). Erasing is ``pad.apply``'s
``erase_ink``.

**Reading** (``learnloop.pads.ink_transcribe``) runs on a thread the context owns (``learnloop_sidecar.polled_jobs``),
off the serial loop. ``ink.transcribe {ink_id}`` reads the strokes that ink's owner holds now: strokes already read
answer at once with their reading (``done``, nothing sent, nothing spent); strokes being read answer with that job;
otherwise a job starts. A poll (``ink.transcribe_job {job_id}``) reads at once and never waits; cancelling refuses the
job's next model request before it is sent. Jobs belong to the vault they started in: a poll from another vault does
not find them, and switching vaults interrupts them (their next request is refused).

Desktop only (pinned in tests/test_mobile_allowlist.py). The learner's ink and LearnLoop's reading of it are workflow
data and learner text, never evidence.
"""
from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Any

from pydantic import Field, field_validator, model_validator

from learnloop.desks.protocol import ProtocolError
from learnloop.pads import emission
from learnloop.pads import ink as ink_core
from learnloop.pads import ink_transcribe as reading
from learnloop.pads import proposals as proposal_core
from learnloop.pads.ink_render import InkTooLarge
from learnloop.ids import new_ulid
from learnloop_sidecar import polled_jobs as PJ
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.desks import protocol_error
from learnloop_sidecar.registry import method

LOG = logging.getLogger(__name__)

#: Every RPC this module registers (pinned desktop-only).
INK_RPCS: tuple[str, ...] = ("ink.save", "ink.erase", "ink.list", "ink.transcribe", "ink.transcribe_job", "ink.transcribe_cancel")
KIND = "ink.transcribe"
NOT_FOUND_MESSAGE = "Handwriting conversion stopped. Try again."


class InkSaveInput(ParamsModel):
    client_id: str = Field(min_length=1)
    seq: int = Field(ge=1)
    owner: ink_core.InkOwner
    ink_id: str = Field(min_length=1, max_length=128)
    strokes: list[ink_core.InkStroke] = Field(min_length=1)
    pointer_meta: ink_core.PointerMeta

    @field_validator("strokes")
    @classmethod
    def _distinct_ids(cls, strokes: list[ink_core.InkStroke]) -> list[ink_core.InkStroke]:
        ids = [stroke.stroke_id for stroke in strokes]
        if len(set(ids)) != len(ids):
            raise ValueError("Draw the mark again.")
        return strokes


class InkEraseInput(ParamsModel):
    client_id: str = Field(min_length=1)
    seq: int = Field(ge=1)
    owner: ink_core.InkOwner
    erase_id: str = Field(min_length=1, max_length=128)
    stroke_ids: list[str] = Field(min_length=1)


class InkListInput(ParamsModel):
    pad_id: str | None = Field(default=None, min_length=1)
    source_id: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _exactly_one(self) -> "InkListInput":
        if (self.pad_id is None) == (self.source_id is None):
            raise ValueError("Reopen the pad or source and draw the mark again.")
        return self


class InkTranscribeInput(ParamsModel):
    ink_id: str = Field(min_length=1, max_length=128)


class InkJobInput(ParamsModel):
    job_id: str = Field(min_length=1, max_length=128)


@method("ink.save", InkSaveInput)
def ink_save(ctx: SidecarContext, params: InkSaveInput) -> dict[str, Any]:
    """One save of strokes to one owner: ``{applied_seq, ink_id, results: [ok{duplicate} | refused{code}]}``."""

    _vault, repository = ctx.require_vault()
    try:
        reply = ink_core.save_ink(repository, client_id=params.client_id, seq=params.seq, owner=params.owner,
                                  ink_id=params.ink_id, strokes=list(params.strokes), pointer_meta=params.pointer_meta)
    except ProtocolError as exc:
        raise protocol_error(exc) from exc
    return versioned(reply)


@method("ink.erase", InkEraseInput)
def ink_erase(ctx: SidecarContext, params: InkEraseInput) -> dict[str, Any]:
    """The barrel over an annotation's or a reading's ink: ``{applied_seq, erase_id, results: [ok{duplicate} |
    refused{code}]}`` (a block's ink is erased in its pad batch)."""

    _vault, repository = ctx.require_vault()
    try:
        reply = ink_core.erase_ink(repository, client_id=params.client_id, seq=params.seq, owner=params.owner,
                                   erase_id=params.erase_id, stroke_ids=list(params.stroke_ids))
    except ProtocolError as exc:
        raise protocol_error(exc) from exc
    return versioned(reply)


@method("ink.list", InkListInput)
def ink_list(ctx: SidecarContext, params: InkListInput) -> dict[str, Any]:
    """The ink of a pad's standing ink blocks, or of a source's listed annotations: per owner its standing strokes,
    their hash and its latest reading (``current`` when it read exactly these strokes)."""

    _vault, repository = ctx.require_vault()
    try:
        owners = (ink_core.ink_for_pad(repository, params.pad_id) if params.pad_id is not None
                  else ink_core.ink_for_source(repository, params.source_id))
    except ink_core.InkError as exc:
        raise SidecarError(exc.code, exc.message) from exc
    return versioned({"pad_id": params.pad_id, "source_id": params.source_id, "owners": owners})


# -- reading ---------------------------------------------------------------------------------------------------------


_REGISTRY = "ink_transcribe_jobs"
#: How often a reading waiting on a cancelled one's request checks that it was not itself stopped (a poll
#: interval, not a bound: the wait lasts as long as that request does).
_WAIT_STEP_SECONDS = 0.05
_READING_LOCK = threading.Lock()


def _jobs(ctx: SidecarContext) -> PJ.PolledJobs:
    """The context's reading jobs (by vault and id; a vault switch interrupts that vault's)."""

    return PJ.registry(ctx, _REGISTRY)


def _error(error: SidecarError | None) -> dict[str, Any] | None:
    if error is None:
        return None
    return {"code": error.code, "message": error.message, "retryable": error.retryable, "details": error.details}


def _payload(job_id: str | None, status: str, *, finished: bool, result: dict[str, Any] | None,
             error: SidecarError | None) -> dict[str, Any]:
    return versioned({"job_id": job_id, "status": status, "done": finished, "result": result,
                      "error": _error(error)})


def _job_payload(job: PJ.PolledJob) -> dict[str, Any]:
    from learnloop.ai import plan_fallback

    state = job.state()
    if state["finished"]:
        plan_fallback.relay_job_offer(job)
    status = state["status"]
    return _payload(job.job_id, status, finished=bool(state["finished"]),
                    result=state["result"] if status == PJ.DONE else None,
                    error=state["error"] if status == PJ.FAILED else None)


def _receipt_payload(receipt: PJ.Receipt) -> dict[str, Any]:
    status = PJ.CANCELLED if receipt.status == PJ.CANCELLED else PJ.EXPIRED
    return _payload(receipt.job_id, status, finished=True, result=None, error=None)


def _after_reading(ctx: SidecarContext, vault: Any, repository: Any, result: dict[str, Any],
                   live: Callable[[], bool]) -> None:
    """A reading written into its block is committed learner text: emitted and given its proposals, as a pad batch's
    blocks are. Never fails the reading (the reconcile on the next open settles what this could not). The facts stay
    in the reading's own vault; the context's worker is woken only while the job's epoch is open (``live``): after a
    vault switch or a shutdown, a wake would restart a stopped worker or start the next vault's."""

    if not result.get("applied") or result.get("owner_kind") != ink_core.BLOCK:
        return
    block_ids = [str(result["owner_id"])]
    try:
        if emission.settle_blocks(vault, repository, block_ids).queued and live():
            ctx.post_attempt_worker.notify()
    except Exception:  # noqa: BLE001 - the reading already committed
        LOG.warning("could not emit the transcribed ink", exc_info=True)
    try:
        proposal_core.propose_for_blocks(repository, block_ids)
    except Exception:  # noqa: BLE001 - a suggestion never fails a reading
        LOG.warning("could not compute the transcribed ink's proposals", exc_info=True)


def _as_sidecar_error(exc: Exception) -> SidecarError:
    from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable
    from learnloop.ai.spend import SpendLimitExceeded
    from learnloop.ingest.extractors.glm_ocr import GlmOcrConsentRequired, GlmOcrExtractionError

    if isinstance(exc, AIInterrupted):
        # A cancellation or a closed context: the polled job says which (``polled_jobs.as_job_error``).
        raise exc
    if isinstance(exc, AIProviderUnavailable):
        return SidecarError("provider_unavailable", "Couldn’t convert your handwriting. Try again.",
                            retryable=True)
    if isinstance(exc, SpendLimitExceeded):
        return SidecarError("capped", "Handwriting conversion reached its limit. Type what you wrote in the pad or note.", retryable=False)
    if isinstance(exc, reading.InkUnavailable):
        return SidecarError(exc.reason, exc.message, retryable=True)
    if isinstance(exc, GlmOcrConsentRequired):
        return SidecarError("needs_upload_ok", reading.NEEDS_OK_MESSAGE, retryable=True)
    if isinstance(exc, GlmOcrExtractionError):
        # GLM-OCR's own words (transport, provider or shape), never the key or the image.
        return SidecarError("ocr_failed", f"Couldn't read your handwriting just now: {exc}", retryable=True)
    if isinstance(exc, InkTooLarge):
        return SidecarError("ink_too_large", str(exc))
    if isinstance(exc, ink_core.InkError):
        return SidecarError(exc.code, exc.message)
    raise exc


@method("ink.transcribe", InkTranscribeInput)
def ink_transcribe(ctx: SidecarContext, params: InkTranscribeInput) -> dict[str, Any]:
    """Read the strokes ``ink_id``'s owner holds now: ``{job_id, status, done, result, error}`` at once."""

    vault, repository = ctx.require_vault()
    try:
        prepared = reading.prepare(repository, params.ink_id)
    except ink_core.InkError as exc:
        raise SidecarError(exc.code, exc.message) from exc
    earlier = reading.stored(repository, prepared)
    if earlier is not None:
        return _payload(None, PJ.DONE, finished=True, result=earlier, error=None)
    jobs = _jobs(ctx)
    vault_key = PJ.vault_key(ctx)

    def work(job: PJ.PolledJob, before: PJ.PolledJob | None) -> dict[str, Any]:
        if before is not None:
            # A cancelled reading of the same strokes whose request may still be out: its answer is kept when it
            # comes, and this one returns it rather than paying for the same strokes again.
            while not before.done.wait(_WAIT_STEP_SECONDS):
                if job.cancelled or not job.live():
                    from learnloop.ai.errors import AIInterrupted

                    raise AIInterrupted("the reading was stopped")
        try:
            result = reading.transcribe(vault, repository, prepared)
        except Exception as exc:  # noqa: BLE001 - mapped to what the poll says; anything else is the job's ``internal``
            raise _as_sidecar_error(exc) from exc
        _after_reading(ctx, vault, repository, result, job.live)
        return result

    with _READING_LOCK:
        # Which job is reading which strokes now: (vault, owner and strokes) -> job id, the finished ones let go.
        reading_now: dict[tuple[str, str], str] = getattr(ctx, "ink_reading_now", None) or {}
        reading_now = {key: job_id for key, job_id in reading_now.items()
                       if (found := jobs.get(key[0], job_id)) is not None and not found.done.is_set()}
        ctx.ink_reading_now = reading_now
        # A cancelled job stays here until its thread ends: the strokes stay reserved while its request may be out.
        running = jobs.get(vault_key, reading_now.get((vault_key, prepared.key), ""))
        if running is not None and not running.done.is_set() and not running.cancelled:
            return _job_payload(running)
        before = running if running is not None and not running.done.is_set() else None
        job = jobs.start(ctx, kind=KIND, job_id="ink_" + new_ulid(), work=lambda job: work(job, before),
                         request_key=prepared.key)
        reading_now[(vault_key, prepared.key)] = job.job_id
    return _job_payload(job)


def _find(ctx: SidecarContext, job_id: str, *, cancel: bool = False) -> dict[str, Any]:
    ctx.require_vault()
    jobs = _jobs(ctx)
    vault_key = PJ.vault_key(ctx)
    job = jobs.cancel(vault_key, job_id) if cancel else jobs.get(vault_key, job_id)
    if job is not None:
        return _job_payload(job)
    receipt = jobs.receipt(vault_key, job_id)
    if receipt is not None:
        return _receipt_payload(receipt)
    raise SidecarError("job_not_found", NOT_FOUND_MESSAGE, details={"job_id": job_id})


@method("ink.transcribe_job", InkJobInput)
def ink_transcribe_job(ctx: SidecarContext, params: InkJobInput) -> dict[str, Any]:
    """The reading's state, at once (never a wait on the request path)."""

    return _find(ctx, params.job_id)


@method("ink.transcribe_cancel", InkJobInput)
def ink_transcribe_cancel(ctx: SidecarContext, params: InkJobInput) -> dict[str, Any]:
    """Cancel the reading: its next model request is refused; a finished reading keeps its outcome."""

    return _find(ctx, params.job_id, cancel=True)


__all__ = ["INK_RPCS", "InkSaveInput"]
