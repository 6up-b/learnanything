"""Adaptive hints H2a RPCs: hints written for the learner's work (spec_adaptive_hints_v1 §4.1, §5, §7.1).

Desktop only (pinned in tests/test_mobile_allowlist.py); no frontend calls
them until H2b's panel, so the practice screen is unchanged either way.

**Never on the request path.** The sidecar is serial and a written hint takes
seconds (the chooser's 3 s time box, then the writer), so, as RW4a's library
jobs (Codex review F6 there), ``practice.request_hint`` answers at once with a
job, and the draft flushes and other RPCs are answered meanwhile. An
immediate answer (adaptive hints off, a diagnostic block) is ``done`` at once
with no job thread and no model call.

**Shown when delivered.** ``practice.hint_job`` reads a job at once (never a
wait). The read that returns a ready hint DELIVERS it: its prepared
``help_assists`` row becomes ``shown = 1`` (``learnloop.hints.service.deliver``),
and a key overlap writes the ``reveal_events`` ``tutor_answer`` row with basis
``hint:<kind>:L<level>`` (the reveal ledger's writer is the attempt package's,
so it is written here). ``practice.cancel_hint`` before delivery (the screen
took the item's own hint instead) leaves the row ``shown = 0``: it counts
nothing (G-H3). A crash before delivery leaves it unshown too.

**Counted at submit.** ``submit_attempt`` and ``submit_dont_know`` fold the
submission's shown server rows (``learnloop_sidecar.handlers.practice``):
levels 1-3 add to ``hints_used``, levels 4-5 set ``primed``.

``practice.answer_discriminating`` records the learner's answer to a
discriminating question (fire-and-forget safe): an assist row, never part of
the submitted answer; it moves no posterior and writes no probe observation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import threading
import time
from typing import Any, Callable, Literal

from pydantic import Field

from learnloop.hints import service as hint_service
from learnloop.hints.service import HintRequestError, HintRequestV1, adaptive_enabled
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.logging import log_event
from learnloop_sidecar.registry import method

LOG = logging.getLogger(__name__)

#: Every RPC this module registers (pinned desktop-only).
HINT_SERVICE_RPCS: tuple[str, ...] = (
    "practice.request_hint",
    "practice.hint_job",
    "practice.cancel_hint",
    "practice.answer_discriminating",
)
#: The most jobs kept in memory for reading back (oldest dropped first).
MAX_KEPT_JOBS = 32


@dataclass
class _HintJob:
    job_id: str
    practice_item_id: str
    started: float
    #: The vault the job writes to: a read after a vault switch never
    #: delivers it into another vault.
    sqlite_path: str = ""
    done: threading.Event = field(default_factory=threading.Event)
    lock: threading.Lock = field(default_factory=threading.Lock)
    result: dict[str, Any] | None = None
    error: SidecarError | None = None
    cancelled: bool = False
    delivered: bool = False


class HintJobs:
    """Hint jobs in flight and just finished (in memory, per sidecar)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._kept: dict[str, _HintJob] = {}

    def start(self, ctx: SidecarContext, practice_item_id: str,
              work: Callable[[Any, Callable[[], bool]], dict[str, Any]]) -> _HintJob:
        from learnloop.ids import new_ulid

        _vault, repository = ctx.require_vault()
        sqlite_path = repository.sqlite_path
        job = _HintJob(f"hjob_{new_ulid()}", practice_item_id, time.monotonic(), sqlite_path=str(sqlite_path))
        with self._lock:
            self._kept[job.job_id] = job
            while len(self._kept) > MAX_KEPT_JOBS:
                self._kept.pop(next(iter(self._kept)))

        def cancelled() -> bool:
            with job.lock:
                return job.cancelled

        def run() -> None:
            from learnloop.ai.execution import record_model_calls
            from learnloop.db.repositories import Repository

            try:
                worker_repo = Repository.attach(sqlite_path)
                # Receipts are owned as the serial loop owns an RPC's; the
                # chooser's and writer's own observers name their owner kinds.
                with record_model_calls(worker_repo, owner_kind="sidecar_rpc",
                                        owner_id=f"practice.request_hint:{job.job_id}"):
                    job.result = work(worker_repo, cancelled)
            except BaseException as exc:  # noqa: BLE001 - every failure answers the job, never the loop
                job.error = _as_sidecar_error(exc)
            finally:
                job.done.set()

        if getattr(ctx, "hints_inline", False):
            run()
        else:
            threading.Thread(target=run, name=f"hint-{job.job_id}", daemon=True).start()
        return job

    def get(self, job_id: str) -> _HintJob | None:
        with self._lock:
            return self._kept.get(job_id)


def _as_sidecar_error(exc: BaseException) -> SidecarError:
    if isinstance(exc, SidecarError):
        return exc
    if isinstance(exc, HintRequestError):
        return SidecarError(exc.code, str(exc), details={"field": exc.field} if exc.field else None)
    LOG.warning("hint job failed: %s", type(exc).__name__, exc_info=exc)
    return SidecarError("internal_error", "LearnLoop couldn't write a hint just now. Try again.", retryable=True)


def _jobs(ctx: SidecarContext) -> HintJobs:
    jobs = getattr(ctx, "hint_jobs", None)
    if jobs is None:
        jobs = HintJobs()
        ctx.hint_jobs = jobs  # type: ignore[attr-defined]
    return jobs


def _immediate(result: dict[str, Any]) -> dict[str, Any]:
    return versioned({"job_id": None, "state": "done", "result": result})


class RequestHintInput(ParamsModel):
    session_id: str = Field(min_length=1)
    practice_item_id: str = Field(min_length=1)
    #: The screen's stable submission key for the attempt in progress: the
    #: hint's row is counted into that submission's attempt and no other.
    submission_id: str = Field(min_length=1)
    #: The draft (the screen flushes it first); absent: the session checkpoint's.
    answer_md: str | None = Field(default=None, max_length=200_000)
    request: Literal["more", "feedback", "book_way", "smaller_step"] = "more"
    answered_assist_id: str | None = None
    feedback_shortcut: Literal["not_where_stuck", "too_big", "learner_route", "notation"] | None = None
    feedback_text: str | None = Field(default=None, max_length=4000)
    feedback_selection: str | None = Field(default=None, max_length=4000)
    #: The worked-help picks only: 4 or 5 (a Hint press serves levels 1-3, D17).
    taken_level: int | None = Field(default=None, ge=4, le=5)
    seconds_on_item: float | None = Field(default=None, ge=0)


@method("practice.request_hint", RequestHintInput)
def request_hint(ctx: SidecarContext, params: RequestHintInput) -> dict[str, Any]:
    """Ask for a hint written for the learner's work (a job; see the module)."""

    from learnloop_sidecar.handlers.practice import _in_diagnostic_block, _require_open_session

    vault, repository = ctx.require_vault()
    if not adaptive_enabled(vault.config):
        return _immediate(hint_service.HintResultV1(
            status=hint_service.DISABLED, reason="adaptive_disabled",
            message="Adaptive hints are off; the item's own hints are shown as before.").as_dict())
    item = vault.practice_items.get(params.practice_item_id)
    if item is None:
        raise SidecarError("not_found", f"Practice item {params.practice_item_id} not found.")
    _require_open_session(repository, params.session_id)
    if _in_diagnostic_block(repository, item):
        # Probe redesign §5.5 (G-H14): no hint during a diagnostic block, and
        # no model is asked.
        return _immediate(hint_service.HintResultV1(
            status=hint_service.REFUSED, reason="diagnostic_block",
            message="Hints are off during a diagnostic check.").as_dict())
    request = HintRequestV1(
        practice_item_id=item.id, session_id=params.session_id, submission_id=params.submission_id.strip(),
        work_md=params.answer_md, request=params.request, answered_assist_id=params.answered_assist_id,
        feedback_shortcut=params.feedback_shortcut, feedback_text=params.feedback_text,
        feedback_selection=params.feedback_selection, taken_level=params.taken_level,
        seconds_on_item=params.seconds_on_item)
    writer_client = getattr(ctx, "hint_writer_client", None)
    chooser_client = getattr(ctx, "hint_chooser_client", None)
    chooser_factory = (lambda: chooser_client) if chooser_client is not None else None
    seed = getattr(ctx, "hint_seed", None)

    def work(worker_repo: Any, cancelled: Callable[[], bool]) -> dict[str, Any]:
        result = hint_service.request_hint(vault, worker_repo, request, writer_client=writer_client,
                                           chooser_client_factory=chooser_factory, seed=seed,
                                           cancelled=cancelled)
        return result.as_dict()

    job = _jobs(ctx).start(ctx, item.id, work)
    return _job_payload(ctx, job)


def _job_payload(ctx: SidecarContext, job: _HintJob) -> dict[str, Any]:
    """The job as the wire reads it; the read that returns a ready hint delivers it."""

    base = {"job_id": job.job_id}
    with job.lock:
        if job.cancelled and not job.delivered:
            return versioned({**base, "state": "cancelled", "result": None})
        if not job.done.is_set():
            return versioned({**base, "state": "pending", "result": None})
        if job.error is not None:
            raise job.error
        result = dict(job.result or {})
        if result.get("status") == hint_service.READY and not job.delivered:
            _deliver(ctx, job.practice_item_id, str(result["assist_id"]))
            job.delivered = True
        result["shown"] = job.delivered
    return versioned({**base, "state": "done", "result": result})


def _deliver(ctx: SidecarContext, practice_item_id: str, assist_id: str) -> None:
    """Show the prepared row and write its key overlap to the reveal ledger
    (§5: ``tutor_answer`` with basis ``hint:<kind>:L<level>``; best effort,
    as every reveal writer is)."""

    from learnloop.attempts.reveal_ledger import record_reveal, reveal_episode_id

    vault, repository = ctx.require_vault()
    row = hint_service.deliver(repository, assist_id)
    if row is None:
        return
    item = vault.practice_items.get(practice_item_id)
    if item is None or not row.get("hint_kind") or not row.get("level"):
        return
    try:
        amount = hint_service.reveal_amount(item, hint_service.shown_text(item, row))
        record_reveal(repository, practice_item_id=item.id, learning_object_id=item.learning_object_id,
                      remediation_episode_id=reveal_episode_id(repository, item.id), source_kind="tutor_answer",
                      amount=amount, basis=hint_service.reveal_basis(str(row["hint_kind"]), int(row["level"])))
    except Exception as exc:  # noqa: BLE001 - ledger bookkeeping never fails the delivery
        log_event("hint_reveal_ledger_failed", practice_item_id=practice_item_id, error=type(exc).__name__)


class HintJobInput(ParamsModel):
    job_id: str = Field(min_length=1)


@method("practice.hint_job", HintJobInput)
def hint_job(ctx: SidecarContext, params: HintJobInput) -> dict[str, Any]:
    """A hint job's state, at once (never a wait on the request path)."""

    return _job_payload(ctx, _require_job(ctx, params.job_id))


def _require_job(ctx: SidecarContext, job_id: str) -> _HintJob:
    _vault, repository = ctx.require_vault()
    job = _jobs(ctx).get(job_id)
    if job is None or job.sqlite_path != str(repository.sqlite_path):
        raise SidecarError("not_found", "That hint request is no longer kept; ask again.")
    return job


@method("practice.cancel_hint", HintJobInput)
def cancel_hint(ctx: SidecarContext, params: HintJobInput) -> dict[str, Any]:
    """Cancel a hint request before it is shown: it is never delivered, and
    its row stays ``shown = 0`` (it counts nothing). A delivered hint stays."""

    job = _require_job(ctx, params.job_id)
    with job.lock:
        if job.delivered:
            return versioned({"job_id": job.job_id, "state": "done", "cancelled": False,
                              "reason": "already_shown"})
        job.cancelled = True
    return versioned({"job_id": job.job_id, "state": "cancelled", "cancelled": True, "reason": None})


class DiscriminateAnswerInput(ParamsModel):
    session_id: str = Field(min_length=1)
    practice_item_id: str = Field(min_length=1)
    submission_id: str = Field(min_length=1)
    #: The discriminating question's row (its result's ``assistId``).
    question_assist_id: str = Field(min_length=1)
    #: The one-line answer, typed in the question's own box.
    answer_md: str = Field(max_length=2000)


@method("practice.answer_discriminating", DiscriminateAnswerInput)
def answer_discriminating(ctx: SidecarContext, params: DiscriminateAnswerInput) -> dict[str, Any]:
    """Record the learner's answer to a discriminating question (fire and
    forget: the screen never waits on it). No model call, no evidence."""

    vault, repository = ctx.require_vault()
    if not adaptive_enabled(vault.config):
        return versioned({"recorded": False, "reason": "adaptive_disabled", "assist_id": None})
    try:
        recorded = hint_service.record_discriminate_answer(
            vault, repository, practice_item_id=params.practice_item_id, session_id=params.session_id,
            submission_id=params.submission_id, question_assist_id=params.question_assist_id,
            answer_md=params.answer_md)
    except HintRequestError as exc:
        raise SidecarError(exc.code, str(exc), details={"field": exc.field} if exc.field else None) from exc
    return versioned(recorded)


__all__ = ["HINT_SERVICE_RPCS", "HintJobs"]
