"""Reader workbench v2 RPCs: ``companion.ask``, ``companion.ask_job`` and ``companion.ask_cancel``
(spec §3.4, §8.6): the companion's question as a polled job.

``companion.ask`` takes the ``reader.ask`` input plus where it was asked (``request_id``, the desk,
the surface, selected pad blocks, a notebook). On the request it gates the question and builds its
context exactly as ``reader.ask`` does (one core: ``reader.prepare_reader_ask``), so every refusal
comes back at once, then answers with a job. The model call, the exchange it records and the reply
(``reader.generate_reader_answer``, ``reader.reader_ask_reply``) run on a thread the context owns,
outside the serial loop, so the learner's edits and reads are answered while the answer is written.

**Where it was asked** is recorded as the question is (``companion_exchange_context``, from the
tutor's ``on_question_recorded``), before its answer is asked for, so a question whose answer failed
or was cancelled keeps its desk too. A failed write is retried when the job ends and on every later
poll, and the poll says whether it is recorded (``context_recorded``), never hiding a failure.

**One vault, one epoch.** A job, its request id and its record belong to the vault open when it
started: a poll, repeat or cancel under another vault does not find it. A close or vault switch ends
the job's epoch: it sends nothing more, ends ``interrupted``, and its completion queues its gap
reading in its own vault without waking the context's workers.

**Idempotent by ``request_id``.** A repeat with the same input answers the same job (running,
finished or, its result dropped from memory, ``expired`` with the exchange it recorded); the same id
with other input is refused (``request_reused``). Every id is remembered for the sidecar's life,
apart from the results; after a restart the job is gone (``job_not_found``), and an exchange it
recorded is in ``companion.history``. At most four asks run at once (``jobs_busy``, retryable).

**Polling** (``companion.ask_job``) answers at once: ``{status, done, partial_md, citations,
streamed_pieces, question_event_id, sent, context_recorded, answer, error, kept}``. No transport
streams answer text today, so ``partial_md`` is empty until the answer is done and then holds it
whole. ``sent``: a model request of this job went out (a cancel after that cannot unsend it).

**Cancelling** (``companion.ask_cancel``) refuses the job's next model request before it is sent. A
request already sent finishes: its exchange is kept in the history (``kept`` true once the answer is
recorded), and the job still reads ``cancelled``, with no answer delivered.

Desktop only (pinned in tests/test_mobile_allowlist.py).
"""
from __future__ import annotations

import logging
import threading
from dataclasses import replace
from typing import Any, Literal

from pydantic import Field

from learnloop.companion.asks import AskContext, CompanionAskError, MAX_PAD_BLOCKS, ask_context
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
from learnloop_sidecar.workbench_protection import block_places, reading_places, refuse_protected

LOG = logging.getLogger(__name__)

#: Every RPC this module registers (pinned desktop-only).
COMPANION_ASK_RPCS: tuple[str, ...] = ("companion.ask", "companion.ask_job", "companion.ask_cancel")
KIND = "companion.ask"
_REGISTRY = "companion_ask_jobs"
#: Asks generating at once (each holds a thread and a model request).
MAX_RUNNING_ASKS = 4
NOT_FOUND_MESSAGE = ("This answer isn't being written any more (LearnLoop restarted since it was asked). "
                     "If it finished, it is in your history.")


class CompanionAskInput(ReaderAskInput):
    #: Client-minted: a retry with the same id never asks twice.
    request_id: str = Field(min_length=1, max_length=128)
    desk_id: str | None = Field(default=None, min_length=1)
    surface: Literal["desk", "reader", "lesson", "notebook"]
    pad_block_ids: list[str] = Field(default_factory=list, max_length=MAX_PAD_BLOCKS)
    notebook_ref: str | None = Field(default=None, min_length=1, max_length=512)
    #: The goal in view on the desk (the goal lens's: the desk's goal, else the vault's primary one, unless the
    #: learner turned the lens off), sent to the tutor as its sentence and depth (owner decision 2026-11-23).
    goal_id: str | None = Field(default=None, min_length=1)


class CompanionAskJobInput(ParamsModel):
    request_id: str = Field(min_length=1, max_length=128)


class _ContextWriter:
    """Records where one question was asked, once, as soon as the question exists; a failed write is kept
    for a retry (at the job's end, then on each poll) and said, never swallowed."""

    def __init__(self, repository: Any, where: AskContext) -> None:
        self._job: PJ.PolledJob | None = None
        self._repository = repository
        self._where = where
        self._lock = threading.Lock()

    def bind(self, job: PJ.PolledJob) -> None:
        self._job = job

    def question_recorded(self, question_event_id: str) -> None:
        if self._job is not None:
            self._job.note(question_event_id=question_event_id)
        self.write()

    def write(self) -> bool:
        """Write the row if the question exists and it is not written yet; whether it is written now."""

        with self._lock:
            if self._job is None:
                return False
            notes = self._job.state()["notes"]
            question_event_id = notes.get("question_event_id")
            if question_event_id is None:
                return False
            if notes.get("context_recorded"):
                return True
            try:
                record_exchange_context(self._repository, question_event_id=str(question_event_id),
                                        **self._where.record())
            except Exception as exc:  # noqa: BLE001 - the question stands; the write is retried and reported
                LOG.warning("could not record where exchange %s was asked", question_event_id, exc_info=True)
                self._job.note(context_recorded=False, context_error=type(exc).__name__)
                return False
            self._job.note(context_recorded=True, context_error=None)
            return True


def goal_in_view(vault: Any, repository: Any, goal_id: str) -> tuple[dict[str, Any] | None, str]:
    """The goal in view as the tutor sees it, and whether it is ``given`` or ``withheld``.

    Only the goal's own sentence (its title when it has none) and the depth the learner chose, with what that
    depth means: never its topics, sections or readiness. While a cold check is due, the goal lens's protection
    holds every topic with a due check, in any goal (``handlers.goal_lens.protection_now``); a goal whose words
    name one is withheld whole, so the tutor can never repeat the held topic back to the learner."""

    from learnloop.source_retrieval import deliverables as DL
    from learnloop.source_retrieval.reading_paths import DEPTH_LABELS, DEPTH_MEANS
    from learnloop_sidecar.handlers.goal_lens import protection_now

    found = next((goal for goal in vault.goals if goal.id == goal_id), None)
    if found is None:
        raise SidecarError("goal_not_found", f"No goal {goal_id!r}.")
    sentence = " ".join(str(found.intent_sentence or found.title or "").split())
    protection, _next_due = protection_now(vault, repository)
    if not sentence or protection.names_held(sentence) or protection.names_held(found.title):
        return None, "withheld"
    depth = DL.depth_of(repository, goal_id)
    view: dict[str, Any] = {"goal_id": goal_id, "sentence": sentence}
    if depth in DEPTH_LABELS:
        view.update(depth=DEPTH_LABELS[depth], depth_means=DEPTH_MEANS[depth])
    return view, "given"


def _jobs(ctx: SidecarContext) -> PJ.PolledJobs:
    return PJ.registry(ctx, _REGISTRY, running=MAX_RUNNING_ASKS, remember_ids=True)


def _request_key(params: CompanionAskInput) -> dict[str, Any]:
    """What a repeat of the request id must ask again to be the same request (compared in memory only)."""

    return params.model_dump(mode="json")


def _reader_params(params: CompanionAskInput) -> ReaderAskInput:
    return ReaderAskInput.model_validate(params.model_dump(include=set(ReaderAskInput.model_fields)))


def _payload(request_id: str, state: dict[str, Any]) -> dict[str, Any]:
    status = state["status"]
    result = state["result"] if status == PJ.DONE else None
    error = state["error"] if status == PJ.FAILED else None
    notes = state["notes"]
    question_event_id = notes.get("question_event_id")
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
        "sent": int(state.get("requests_sent") or 0) > 0,
        # None while no question is recorded yet; false names a write that failed and is being retried.
        "context_recorded": None if question_event_id is None else bool(notes.get("context_recorded")),
        "kept": status == PJ.CANCELLED and bool(notes.get("answered")),
        # The goal in view: "given" to the tutor, "withheld" (its words name a topic whose cold check is due), or
        # None when no goal was in view.
        "goal_in_view": notes.get("goal"),
        "answer": result,
        "error": None if error is None else {"code": error.code, "message": error.message,
                                             "retryable": error.retryable, "details": error.details},
    })


def _job_payload(job: PJ.PolledJob) -> dict[str, Any]:
    from learnloop.ai import plan_fallback

    state = job.state()
    if state["finished"]:
        plan_fallback.relay_job_offer(job)
        writer = job.attachments.get("context")
        if writer is not None and state["notes"].get("question_event_id") and not state["notes"].get(
                "context_recorded"):
            # The job's own write failed: each poll tries again, so a passing fault heals.
            writer.write()
            state = job.state()
    return _payload(job.job_id, state)


def _receipt_payload(receipt: PJ.Receipt) -> dict[str, Any]:
    status = PJ.CANCELLED if receipt.status == PJ.CANCELLED else PJ.EXPIRED
    return _payload(receipt.job_id, {"status": status, "finished": True, "result": None, "error": None,
                                     "streamed_pieces": 0, "notes": receipt.notes,
                                     "requests_sent": receipt.requests_sent})


def _known_payload(known: PJ.PolledJob | PJ.Receipt) -> dict[str, Any]:
    return _job_payload(known) if isinstance(known, PJ.PolledJob) else _receipt_payload(known)


@method("companion.ask", CompanionAskInput)
def companion_ask(ctx: SidecarContext, params: CompanionAskInput) -> dict[str, Any]:
    """Ask the companion; answers at once with the job (see the module docstring)."""

    origin_vault, repository = ctx.require_vault()

    def check_origin() -> None:
        places = reading_places(params.extraction_id, [params.span_id, *params.selection_span_ids])
        places.extend(block_places(origin_vault, repository, params.pad_block_ids))
        refuse_protected(origin_vault, repository, places)

    check_origin()
    jobs = _jobs(ctx)
    vault = PJ.vault_key(ctx)
    key = _request_key(params)
    known = jobs.known(vault, params.request_id)
    if known is not None:
        if known.request_key != key:
            raise SidecarError("request_reused", "That request id was already used for another question.",
                               details={"request_id": params.request_id})
        return _known_payload(known)
    try:
        where = ask_context(repository, surface=params.surface, desk_id=params.desk_id,
                            pad_block_ids=params.pad_block_ids, notebook_ref=params.notebook_ref)
    except CompanionAskError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    call = prepare_reader_ask(ctx, _reader_params(params))
    goal, goal_state = (None, None) if params.goal_id is None else goal_in_view(origin_vault, repository, params.goal_id)
    if params.goal_id is not None:
        # The exchange records the goal it was asked under (the lens's, which may be the vault's primary goal).
        where = replace(where, goal_id=params.goal_id)
    writer = _ContextWriter(call.repository, where)

    def work(job: PJ.PolledJob) -> dict[str, Any]:
        check_origin()
        writer.bind(job)
        job.note(goal=goal_state)
        try:
            result = generate_reader_answer(call, on_question_recorded=writer.question_recorded, goal_in_view=goal)
        finally:
            # A question recorded before a failure keeps its context; a write that failed is tried again.
            writer.write()
        job.note(question_event_id=str(result["event_id"]), answered=True)
        writer.write()
        return reader_ask_reply(ctx, call, result, live=job.live)

    job = jobs.start(ctx, kind=KIND, job_id=params.request_id, work=work, request_key=key,
                     foreground_kind="tutor", attachments={"context": writer})
    return _job_payload(job)


def _require_known(ctx: SidecarContext, request_id: str) -> PJ.PolledJob | PJ.Receipt:
    ctx.require_vault()
    known = _jobs(ctx).known(PJ.vault_key(ctx), request_id)
    if known is None:
        raise SidecarError("job_not_found", NOT_FOUND_MESSAGE, details={"request_id": request_id})
    return known


@method("companion.ask_job", CompanionAskJobInput)
def companion_ask_job(ctx: SidecarContext, params: CompanionAskJobInput) -> dict[str, Any]:
    """The job's state, at once (never a wait on the request path)."""

    return _known_payload(_require_known(ctx, params.request_id))


@method("companion.ask_cancel", CompanionAskJobInput)
def companion_ask_cancel(ctx: SidecarContext, params: CompanionAskJobInput) -> dict[str, Any]:
    """Cancel the job: its next model request is refused; a finished job keeps its outcome."""

    known = _require_known(ctx, params.request_id)
    if isinstance(known, PJ.PolledJob):
        _jobs(ctx).cancel(known.vault_key, known.job_id)
    return _known_payload(known)


__all__ = ["COMPANION_ASK_RPCS", "CompanionAskInput"]
