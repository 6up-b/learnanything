"""Reader workbench v2 RPCs: ``companion.ask``, ``companion.ask_job`` and ``companion.ask_cancel``
(spec §3.4, §8.6): the companion's question as a polled job.

``companion.ask`` takes the ``reader.ask`` input plus where it was asked (``request_id``, the desk,
the surface, selected pad blocks, a notebook). On the request it gates the question and builds its
context exactly as ``reader.ask`` does (one core: ``reader.prepare_reader_ask``), so every refusal
comes back at once, then answers with a job. The model call, the exchange it records and the reply
(``reader.generate_reader_answer``, ``reader.reader_ask_reply``) run on a thread the context owns,
outside the serial loop, so the learner's edits and reads are answered while the answer is written.
Once the exchange is recorded, where it was asked is recorded with it (``companion_exchange_context``);
its passages are written through by the Ask itself, as for every Reader exchange.

**Idempotent by ``request_id``.** A repeat with the same input answers the same job (running,
finished or, dropped from memory, ``expired`` with the exchange it recorded); the same id with other
input is refused (``request_reused``). Ids live as long as the sidecar: after a restart the job is
gone (``job_not_found``), and an exchange it finished is in ``companion.history``.

**Polling** (``companion.ask_job``) answers at once: ``{status, done, partial_md, citations,
streamed_pieces, question_event_id, answer, error, kept}``. No transport streams answer text today
(answers arrive whole, as structured output), so ``partial_md`` is empty until the answer is done and
then holds it whole; ``streamed_pieces`` counts the output pieces of the request in flight where the
transport streams.

**Cancelling** (``companion.ask_cancel``) refuses the job's next model request before it is sent. A
request already sent finishes: its exchange is recorded and kept in the history (``kept`` true), and
the job still reads ``cancelled``, with no answer delivered.

Desktop only (pinned in tests/test_mobile_allowlist.py).
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Literal

from pydantic import Field

from learnloop.companion.asks import CompanionAskError, MAX_PAD_BLOCKS, ask_context
from learnloop.companion.history import record_exchange_context
from learnloop_sidecar import polled_jobs as PJ
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.reader import (
    ReaderAskInput,
    generate_reader_answer,
    prepare_reader_ask,
    reader_ask_reply,
)
from learnloop_sidecar.registry import method

LOG = logging.getLogger(__name__)

#: Every RPC this module registers (pinned desktop-only).
COMPANION_ASK_RPCS: tuple[str, ...] = ("companion.ask", "companion.ask_job", "companion.ask_cancel")
KIND = "companion.ask"
_REGISTRY = "companion_ask_jobs"
NOT_FOUND_MESSAGE = ("This answer isn't being written any more (LearnLoop restarted since it was asked). "
                     "If it finished, it is in your history.")


class CompanionAskInput(ReaderAskInput):
    #: Client-minted: a retry with the same id never asks twice.
    request_id: str = Field(min_length=1, max_length=128)
    desk_id: str | None = Field(default=None, min_length=1)
    surface: Literal["desk", "reader", "lesson", "notebook"]
    pad_block_ids: list[str] = Field(default_factory=list, max_length=MAX_PAD_BLOCKS)
    notebook_ref: str | None = Field(default=None, min_length=1, max_length=512)


class CompanionAskJobInput(ParamsModel):
    request_id: str = Field(min_length=1, max_length=128)


def _jobs(ctx: SidecarContext) -> PJ.PolledJobs:
    return PJ.registry(ctx, _REGISTRY)


def _digest(params: CompanionAskInput) -> str:
    return hashlib.sha256(json.dumps(params.model_dump(mode="json"), sort_keys=True).encode()).hexdigest()


def _reader_params(params: CompanionAskInput) -> ReaderAskInput:
    return ReaderAskInput.model_validate(params.model_dump(include=set(ReaderAskInput.model_fields)))


def _payload(request_id: str, state: dict[str, Any]) -> dict[str, Any]:
    status = state["status"]
    result = state["result"] if status == PJ.DONE else None
    error = state["error"] if status == PJ.FAILED else None
    question_event_id = state["notes"].get("question_event_id")
    return versioned({
        "request_id": request_id,
        "status": status,
        # Cancelled: done once the thread has finished, so a poller that wants to know whether the
        # answer was kept reads until then.
        "done": bool(state["finished"]) or status == PJ.EXPIRED,
        "partial_md": str((result or {}).get("answer_md") or ""),
        "citations": list((result or {}).get("citations") or []),
        "streamed_pieces": int(state.get("streamed_pieces") or 0),
        "question_event_id": question_event_id,
        "kept": status == PJ.CANCELLED and question_event_id is not None,
        "answer": result,
        "error": None if error is None else {"code": error.code, "message": error.message,
                                             "retryable": error.retryable, "details": error.details},
    })


def _job_payload(job: PJ.PolledJob) -> dict[str, Any]:
    from learnloop.ai import plan_fallback

    state = job.state()
    if state["finished"]:
        plan_fallback.relay_job_offer(job)
    return _payload(job.job_id, state)


def _receipt_payload(receipt: PJ.Receipt) -> dict[str, Any]:
    status = PJ.CANCELLED if receipt.status == PJ.CANCELLED else PJ.EXPIRED
    return _payload(receipt.job_id, {"status": status, "finished": True, "result": None, "error": None,
                                     "streamed_pieces": 0, "notes": receipt.notes})


@method("companion.ask", CompanionAskInput)
def companion_ask(ctx: SidecarContext, params: CompanionAskInput) -> dict[str, Any]:
    """Ask the companion; answers at once with the job (see the module docstring)."""

    jobs = _jobs(ctx)
    digest = _digest(params)
    known = jobs.get(params.request_id) or jobs.receipt(params.request_id)
    if known is not None:
        if known.request_hash != digest:
            raise SidecarError("request_reused", "That request id was already used for another question.",
                               details={"request_id": params.request_id})
        return _job_payload(known) if isinstance(known, PJ.PolledJob) else _receipt_payload(known)
    _vault, repository = ctx.require_vault()
    try:
        where = ask_context(repository, surface=params.surface, desk_id=params.desk_id,
                            pad_block_ids=params.pad_block_ids, notebook_ref=params.notebook_ref)
    except CompanionAskError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    call = prepare_reader_ask(ctx, _reader_params(params))

    def work(job: PJ.PolledJob) -> dict[str, Any]:
        result = generate_reader_answer(call)
        question_event_id = str(result["event_id"])
        job.note(question_event_id=question_event_id)
        try:
            record_exchange_context(call.repository, question_event_id=question_event_id, **where.record())
        except Exception:  # noqa: BLE001 - the answer stands; the history then reads it as before desks
            LOG.warning("could not record where exchange %s was asked", question_event_id, exc_info=True)
        return reader_ask_reply(ctx, call, result)

    job = jobs.start(ctx, kind=KIND, job_id=params.request_id, work=work, request_hash=digest,
                     foreground_kind="tutor")
    return _job_payload(job)


@method("companion.ask_job", CompanionAskJobInput)
def companion_ask_job(ctx: SidecarContext, params: CompanionAskJobInput) -> dict[str, Any]:
    """The job's state, at once (never a wait on the request path)."""

    ctx.require_vault()
    jobs = _jobs(ctx)
    job = jobs.get(params.request_id)
    if job is not None:
        return _job_payload(job)
    receipt = jobs.receipt(params.request_id)
    if receipt is not None:
        return _receipt_payload(receipt)
    raise SidecarError("job_not_found", NOT_FOUND_MESSAGE, details={"request_id": params.request_id})


@method("companion.ask_cancel", CompanionAskJobInput)
def companion_ask_cancel(ctx: SidecarContext, params: CompanionAskJobInput) -> dict[str, Any]:
    """Cancel the job: its next model request is refused; a finished job keeps its outcome."""

    ctx.require_vault()
    jobs = _jobs(ctx)
    job = jobs.cancel(params.request_id)
    if job is not None:
        return _job_payload(job)
    receipt = jobs.receipt(params.request_id)
    if receipt is not None:
        return _receipt_payload(receipt)
    raise SidecarError("job_not_found", NOT_FOUND_MESSAGE, details={"request_id": params.request_id})


__all__ = ["COMPANION_ASK_RPCS", "CompanionAskInput"]
