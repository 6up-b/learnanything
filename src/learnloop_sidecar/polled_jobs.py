"""Jobs the workbench polls (spec_reader_workbench_v2 §3.4: "long work is a job").

The sidecar answers one request at a time, so work that waits on a model (the companion's answer, a
search by meaning) runs on a thread the context owns (:mod:`learnloop_sidecar.background_jobs`) and
the request that started it answers at once with the job. A poll reads the job's state at once and
never waits: a wait would hold every request queued behind it.

What a job guarantees:

* **Its own receipts and offers.** Model calls are recorded under the method and the job's id, as the
  serial loop records an RPC's; a plan-first fallback offer the job's requests make is relayed by the
  poll that finds it finished (``plan_fallback.relay_job_offer``).
* **Honest cancellation.** A cancelled job's next physical model request is refused before it is sent
  (``SpendCancelled``, the refusal every paid path stops on). A request already sent finishes and
  whatever it records is kept; the poll says the job was cancelled and whether its work was kept.
* **Honest failure.** Every failure ends the job with its error (a sidecar error as raised, anything
  else as ``internal``); a thread that ended without finishing reads as ``failed`` (``interrupted``),
  never as running forever. A context close or a vault switch cancels the job's epoch
  (``BackgroundJobs``): its next request is refused and it ends ``interrupted``.
* **Bounded memory.** Finished jobs beyond :data:`MAX_KEPT_JOBS` are dropped oldest first, leaving a
  small receipt (status and notes) so a repeat of the same id is answered as ``expired``, never run
  again.
"""
from __future__ import annotations

import logging
import sqlite3
import threading
import time
from collections import OrderedDict
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from typing import Any

from learnloop.ai.spend import SpendCancelled
from learnloop_sidecar.background_jobs import background_jobs
from learnloop_sidecar.errors import SidecarError, waiting_for_ok_error

LOG = logging.getLogger(__name__)

#: Finished jobs kept for reading back, per registry (oldest finished dropped first; running jobs stay).
MAX_KEPT_JOBS = 64
#: Receipts of dropped jobs, so a repeated id is answered, never run twice (a memory bound).
MAX_RECEIPTS = 1024

QUEUED = "queued"
RUNNING = "running"
DONE = "done"
FAILED = "failed"
CANCELLED = "cancelled"
EXPIRED = "expired"

INTERRUPTED_MESSAGE = "This stopped before it finished (LearnLoop closed the work or switched vaults). Try again."
INTERNAL_MESSAGE = "LearnLoop couldn't finish this. Try again."


@dataclass
class PolledJob:
    job_id: str
    kind: str
    #: What the request asked, compared when the same id comes again (never persisted, never hashed).
    request_key: Any
    started: float
    status: str = QUEUED
    result: Any = None
    error: SidecarError | None = None
    cancelled: bool = False
    #: Output pieces the model request in flight has streamed (a progress measure; 0 for a transport that
    #: does not stream).
    streamed_pieces: int = 0
    #: Facts the work records as it goes (the companion's question event, once the exchange is recorded).
    notes: dict[str, Any] = field(default_factory=dict)
    #: A key that supersedes: a newer job with the same key cancels this one (a search typed further).
    supersede_key: str | None = None
    done: threading.Event = field(default_factory=threading.Event)
    lock: threading.Lock = field(default_factory=threading.Lock)
    thread: threading.Thread | None = None
    #: The plan-first fallback offer the job's requests made, relayed by the poll that finds it done.
    fallback_offer: dict[str, Any] | None = None

    def note(self, **values: Any) -> None:
        with self.lock:
            self.notes.update(values)

    def state(self) -> dict[str, Any]:
        """A consistent reading of the job: ``status`` as a poll reports it, and what it holds."""

        with self.lock:
            finished = self.done.is_set()
            status = self.status
            if self.cancelled:
                status = CANCELLED
            elif finished:
                status = FAILED if self.error is not None else DONE
            elif self.thread is not None and not self.thread.is_alive():
                # The thread ended without reaching its finally (it cannot, short of the interpreter
                # dying under it): said as a failure, never left reading as running.
                status = FAILED
            error = self.error
            if status == FAILED and error is None:
                error = SidecarError("interrupted", INTERRUPTED_MESSAGE, retryable=True)
            return {"status": status, "finished": finished or status == FAILED, "result": self.result,
                    "error": error, "streamed_pieces": self.streamed_pieces, "notes": dict(self.notes)}


@dataclass(frozen=True)
class Receipt:
    """What is kept of a dropped job: enough to answer a repeat of its id."""

    job_id: str
    kind: str
    request_key: Any
    status: str
    notes: dict[str, Any]


class _CancelGate:
    """Refuses a cancelled job's physical model requests before they are sent; an outer gate (the
    context's closing gate) is admitted first and settled on a refusal, so nothing it reserved is
    kept for a request never sent."""

    def __init__(self, job: PolledJob, outer: Any) -> None:
        self._job = job
        self._outer = outer

    def admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> Any:
        admission = None if self._outer is None else self._outer.admit(client, purpose=purpose, prompt=prompt,
                                                                       budget=budget)
        if self._job.cancelled:
            if self._outer is not None:
                self._outer.settle(admission, {})
            raise SpendCancelled(f"{purpose} not sent: the job was cancelled")
        return admission

    def settle(self, admission: Any, usage: dict[str, Any]) -> None:
        if self._outer is not None:
            self._outer.settle(admission, usage)


def as_job_error(exc: BaseException, *, cancelled: bool) -> SidecarError:
    """A job's failure as the poll reports it."""

    from learnloop.ai.model_use import ModelUseNotAccepted

    if isinstance(exc, SidecarError) and isinstance(exc.__cause__, SpendCancelled):
        # A provider failure mapped by the work (the Ask's "provider unavailable") whose cause is the
        # job's own refusal: said as the cancellation or interruption it was.
        exc = exc.__cause__
    if isinstance(exc, SidecarError):
        return exc
    if isinstance(exc, ModelUseNotAccepted):
        return waiting_for_ok_error()
    if isinstance(exc, SpendCancelled):
        if cancelled:
            return SidecarError("cancelled", "Cancelled before the request was sent.")
        return SidecarError("interrupted", INTERRUPTED_MESSAGE, retryable=True)
    if isinstance(exc, sqlite3.OperationalError) and str(exc).lower().startswith(("database is locked",
                                                                                  "database is busy")):
        return SidecarError("database_busy", "The vault database was busy with another write. Try again.",
                            retryable=True)
    LOG.warning("polled job failed: %s", type(exc).__name__, exc_info=exc)
    return SidecarError("internal", INTERNAL_MESSAGE, retryable=True)


@contextmanager
def _job_scope(job: PolledJob, repository: Any, owner_id: str, foreground_kind: str | None) -> Iterator[None]:
    from learnloop.ai.execution import active_request_gate, gate_model_requests, observe_model_output, \
        record_model_calls
    from learnloop.figures.foreground import foreground

    def streamed(_parent: Any, pieces: int) -> None:
        with job.lock:
            job.streamed_pieces = int(pieces)

    with ExitStack() as stack:
        # Receipts are owned as the serial loop owns an RPC's (server._observed_model_calls).
        stack.enter_context(record_model_calls(repository, owner_kind="sidecar_rpc", owner_id=owner_id))
        stack.enter_context(gate_model_requests(_CancelGate(job, active_request_gate())))
        stack.enter_context(observe_model_output(streamed))
        if foreground_kind is not None:
            # Background figure prebuilds yield while the learner waits on this (as for the RPC it replaces).
            stack.enter_context(foreground(foreground_kind))
        yield


class PolledJobs:
    """One kind of polled job in one sidecar context: running and recently finished jobs by id."""

    def __init__(self, *, kept: int = MAX_KEPT_JOBS, receipts: int = MAX_RECEIPTS) -> None:
        self._lock = threading.Lock()
        self._jobs: OrderedDict[str, PolledJob] = OrderedDict()
        self._receipts: OrderedDict[str, Receipt] = OrderedDict()
        self._kept = kept
        self._receipt_limit = receipts

    def get(self, job_id: str) -> PolledJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def receipt(self, job_id: str) -> Receipt | None:
        with self._lock:
            return self._receipts.get(job_id)

    def cancel(self, job_id: str) -> PolledJob | None:
        """Cancel a job that has not finished (a finished job keeps its outcome)."""

        job = self.get(job_id)
        if job is not None:
            with job.lock:
                if not job.done.is_set():
                    job.cancelled = True
        return job

    def _drop_finished(self) -> None:
        """Under ``self._lock``: drop the oldest finished jobs beyond the bound, keeping their receipts."""

        finished = [job for job in self._jobs.values() if job.done.is_set()]
        excess = len(self._jobs) - self._kept
        for job in finished[:max(0, excess)]:
            self._jobs.pop(job.job_id, None)
            state = job.state()
            self._receipts[job.job_id] = Receipt(job.job_id, job.kind, job.request_key, state["status"],
                                                 state["notes"])
        while len(self._receipts) > self._receipt_limit:
            self._receipts.popitem(last=False)

    def start(self, ctx: Any, *, kind: str, job_id: str, work: Callable[[PolledJob], Any],
              request_key: Any = None, foreground_kind: str | None = None,
              supersede_key: str | None = None) -> PolledJob:
        """Start ``work(job)`` on a thread the context owns; its return value is the job's result.

        ``supersede_key``: every unfinished job of this registry with the same key is cancelled first."""

        from learnloop.ai import plan_fallback

        vault, repository = ctx.require_vault()
        job = PolledJob(job_id, kind, request_key, time.monotonic(), supersede_key=supersede_key)
        with self._lock:
            if job_id in self._jobs or job_id in self._receipts:
                raise ValueError(f"job {job_id!r} exists")  # callers answer a repeat before starting
            older = [other for other in self._jobs.values()
                     if supersede_key is not None and other.supersede_key == supersede_key]
            self._jobs[job_id] = job
            self._drop_finished()
        for other in older:
            with other.lock:
                if not other.done.is_set():
                    other.cancelled = True
        # The job belongs to the action whose request started it and carries that action's grant (taken
        # here, on the request), as a library job does.
        grant, origin = plan_fallback.unit_token(vault.root), plan_fallback.unit_origin()
        stamp = plan_fallback.unit_stamp(vault.root)
        plan_fallback.note_unit("job", job_id)
        owner_id = f"{kind}:{job_id}"

        def run() -> None:
            with plan_fallback.unit(grant, origin, stamp) as offers:
                try:
                    with job.lock:
                        job.status = RUNNING
                    with _job_scope(job, repository, owner_id, foreground_kind):
                        result = work(job)
                    with job.lock:
                        job.result = result
                except BaseException as exc:  # noqa: BLE001 - every failure answers the job, never the loop
                    error = as_job_error(exc, cancelled=job.cancelled)
                    with job.lock:
                        job.error = error
                finally:
                    job.fallback_offer = offers.hint()
                    job.done.set()

        job.thread = background_jobs(ctx).spawn(run, name=f"{kind}-{job_id}")
        return job


def registry(ctx: Any, name: str) -> PolledJobs:
    """``ctx``'s registry of one kind of polled job (made on first use)."""

    jobs = getattr(ctx, name, None)
    if jobs is None:
        jobs = PolledJobs()
        setattr(ctx, name, jobs)
    return jobs


__all__ = ["CANCELLED", "DONE", "EXPIRED", "FAILED", "MAX_KEPT_JOBS", "MAX_RECEIPTS", "QUEUED", "RUNNING",
           "PolledJob", "PolledJobs", "Receipt", "as_job_error", "registry"]
