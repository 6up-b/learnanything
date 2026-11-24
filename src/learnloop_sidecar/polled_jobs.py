"""Jobs the workbench polls (spec_reader_workbench_v2 §3.4: "long work is a job").

The sidecar answers one request at a time, so work that waits on a model (the companion's answer, a
search by meaning) runs on a thread the context owns (:mod:`learnloop_sidecar.background_jobs`) and
the request that started it answers at once with the job. A poll reads the job's state at once and
never waits: a wait would hold every request queued behind it.

What a job guarantees:

* **One vault.** A job and its request id belong to the vault the context had open when it started
  (:func:`vault_key`); every read, repeat and cancel names the vault open now, so another vault's job
  is not found there, and a repeated id is looked up only among this vault's.
* **Its own epoch.** A job captures the context's background epoch, which a close ends; a vault switch
  interrupts the previous vault's polled jobs (:func:`interrupt_vault`; other background jobs keep their
  own vault guards). Either way its next model request is refused, it ends ``interrupted``, and
  :meth:`PolledJob.live` is false, so its completion records its own vault's facts and never wakes the
  context's workers.
* **Its receipts.** Calls the job records itself are owned by ``<kind>:<job_id>``; every root receipt
  started on its thread, whoever records it (a query embedding, a rewrite), carries
  ``owning_job`` in its ``budget_json``, one row per call. A plan-first fallback offer the job's
  requests make is relayed by the poll that finds it finished.
* **Honest cancellation.** A cancelled job's next physical model request is refused before it is sent
  (``SpendCancelled``). A request already sent finishes and whatever it records is kept; the poll says
  the job was cancelled, whether a request was sent, and whether its work was kept.
* **Honest failure.** Every failure ends the job with its error (a sidecar error as raised, anything
  else as ``internal``); a thread that ended without finishing reads as ``failed`` (``interrupted``).
* **Bounds.** At most ``running`` jobs run at once per registry (a further start is refused, retryable);
  finished results beyond :data:`MAX_KEPT_JOBS` are dropped oldest first as each job finishes. A
  registry that remembers ids keeps a small record of every id it admitted for the sidecar's life,
  apart from the results, so a repeat is answered (``expired``) and never run twice; when that record
  is full it refuses new ids rather than forget old ones.
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
from pathlib import Path
from typing import Any

from learnloop.ai.spend import SpendCancelled
from learnloop_sidecar.background_jobs import background_jobs
from learnloop_sidecar.errors import SidecarError, waiting_for_ok_error

LOG = logging.getLogger(__name__)

#: Finished jobs whose results are kept for reading back, per registry (running jobs are never dropped).
MAX_KEPT_JOBS = 64
#: Jobs running at once, per registry, unless the registry names its own bound.
MAX_RUNNING = 4
#: Request ids a remembering registry keeps for the sidecar's life; full, it refuses new ids.
MAX_REMEMBERED_IDS = 10_000
#: Records a forgetting registry (server-minted ids) keeps of dropped jobs, oldest dropped first.
MAX_RECEIPTS = 1024

QUEUED = "queued"
RUNNING = "running"
DONE = "done"
FAILED = "failed"
CANCELLED = "cancelled"
EXPIRED = "expired"

INTERRUPTED_MESSAGE = "This stopped before it finished (LearnLoop closed the work or switched vaults). Try again."
INTERNAL_MESSAGE = "LearnLoop couldn't finish this. Try again."
BUSY_MESSAGE = "LearnLoop is already working on several of these. Try again when one finishes."
IDS_FULL_MESSAGE = ("LearnLoop has answered as many requests as it can remember since it started. "
                    "Restart LearnLoop to ask more.")


def vault_key(ctx: Any) -> str:
    """The vault a job belongs to: the context's open vault, resolved ("" with none open)."""

    root = getattr(ctx, "vault_root", None)
    return str(Path(root).resolve()) if root else ""


@dataclass
class PolledJob:
    job_id: str
    kind: str
    #: What the request asked, compared when the same id comes again (never persisted, never hashed).
    request_key: Any
    started: float
    vault_key: str = ""
    status: str = QUEUED
    result: Any = None
    error: SidecarError | None = None
    cancelled: bool = False
    #: Its vault was switched away from (not the learner's cancel): it ends interrupted.
    interrupted: bool = False
    #: Physical model requests admitted (sent) for this job: a cancel after one says the request went.
    requests_sent: int = 0
    #: Output pieces the model request in flight has streamed (a progress measure; 0 for a transport that
    #: does not stream).
    streamed_pieces: int = 0
    #: Facts the work records as it goes (the companion's question event, as the question is recorded).
    notes: dict[str, Any] = field(default_factory=dict)
    #: A key that supersedes: a newer job with the same key cancels this one (a search typed further).
    supersede_key: str | None = None
    done: threading.Event = field(default_factory=threading.Event)
    lock: threading.Lock = field(default_factory=threading.Lock)
    thread: threading.Thread | None = None
    #: The plan-first fallback offer the job's requests made, relayed by the poll that finds it done.
    fallback_offer: dict[str, Any] | None = None
    #: What a later read of the job needs from its work (never part of a reply): the companion's context
    #: writer, retried by a poll when the job's own write failed.
    attachments: dict[str, Any] = field(default_factory=dict)
    #: Whether the context's epoch the job started in is still open (set by :meth:`PolledJobs.start`).
    _live: Callable[[], bool] = field(default=lambda: True, repr=False)

    def live(self) -> bool:
        """False once the context closed or switched vaults after this job started: its completion then
        touches nothing of the context (no worker woken, no prefetch queued)."""

        return not self.interrupted and bool(self._live())

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
            elif finished and self.interrupted:
                # Its vault was switched away from before it finished: whatever its work returned after that is
                # not delivered when the vault is opened again (a close keeps a sent request's outcome).
                status = FAILED
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
                    "error": error, "streamed_pieces": self.streamed_pieces, "notes": dict(self.notes),
                    "requests_sent": self.requests_sent}


@dataclass
class Receipt:
    """What a registry keeps of a request id apart from its result: enough to answer a repeat of it."""

    job_id: str
    vault_key: str
    kind: str
    request_key: Any
    status: str = RUNNING
    notes: dict[str, Any] = field(default_factory=dict)
    requests_sent: int = 0


class _CancelGate:
    """Refuses a cancelled job's physical model requests before they are sent and counts the ones it
    admits; an outer gate (the context's closing gate) is admitted first and settled on a refusal, so
    nothing it reserved is kept for a request never sent."""

    def __init__(self, job: PolledJob, outer: Any) -> None:
        self._job = job
        self._outer = outer

    def admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> Any:
        admission = None if self._outer is None else self._outer.admit(client, purpose=purpose, prompt=prompt,
                                                                       budget=budget)
        if self._job.cancelled or self._job.interrupted:
            if self._outer is not None:
                self._outer.settle(admission, {})
            raise SpendCancelled(f"{purpose} not sent: the job was cancelled or its vault closed")
        with self._job.lock:
            self._job.requests_sent += 1
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
    from learnloop.ai.execution import active_request_gate, annotate_calls, gate_model_requests, \
        observe_model_output, record_model_calls
    from learnloop.figures.foreground import foreground

    def streamed(_parent: Any, pieces: int) -> None:
        with job.lock:
            job.streamed_pieces = int(pieces)

    with ExitStack() as stack:
        # Receipts are owned as the serial loop owns an RPC's (server._observed_model_calls).
        stack.enter_context(record_model_calls(repository, owner_kind="sidecar_rpc", owner_id=owner_id))
        # A nested recorder (a query embedding's, a rewrite's) replaces that owner with its own; the
        # annotation rides on every root receipt started here, so those calls still name the job.
        stack.enter_context(annotate_calls(owning_job=owner_id))
        stack.enter_context(gate_model_requests(_CancelGate(job, active_request_gate())))
        stack.enter_context(observe_model_output(streamed))
        if foreground_kind is not None:
            # Background figure prebuilds yield while the learner waits on this (as for the RPC it replaces).
            stack.enter_context(foreground(foreground_kind))
        yield


class PolledJobs:
    """One kind of polled job in one sidecar context: running and recently finished jobs, by vault and id.

    ``remember_ids``: the ids are the client's (a retry must never ask twice), so every admitted id is
    remembered for the sidecar's life; otherwise (server-minted ids) records of dropped jobs are kept
    only up to :data:`MAX_RECEIPTS`."""

    def __init__(self, *, kept: int = MAX_KEPT_JOBS, running: int = MAX_RUNNING, remember_ids: bool = True,
                 remembered: int = MAX_REMEMBERED_IDS, receipts: int = MAX_RECEIPTS) -> None:
        self._lock = threading.Lock()
        self._jobs: OrderedDict[tuple[str, str], PolledJob] = OrderedDict()
        self._records: OrderedDict[tuple[str, str], Receipt] = OrderedDict()
        self._kept = kept
        self._running = running
        self._remember_ids = remember_ids
        self._record_limit = remembered if remember_ids else receipts

    def get(self, vault: str, job_id: str) -> PolledJob | None:
        with self._lock:
            return self._jobs.get((vault, job_id))

    def receipt(self, vault: str, job_id: str) -> Receipt | None:
        """The record of an id this registry admitted in ``vault`` whose result is no longer kept."""

        with self._lock:
            if (vault, job_id) in self._jobs:
                return None
            return self._records.get((vault, job_id))

    def known(self, vault: str, job_id: str) -> PolledJob | Receipt | None:
        return self.get(vault, job_id) or self.receipt(vault, job_id)

    def kept_count(self) -> int:
        with self._lock:
            return len(self._jobs)

    def cancel(self, vault: str, job_id: str) -> PolledJob | None:
        """Cancel a job that has not finished (a finished job keeps its outcome)."""

        job = self.get(vault, job_id)
        if job is not None:
            with job.lock:
                if not job.done.is_set():
                    job.cancelled = True
        return job

    def interrupt(self, vault: str) -> None:
        """Interrupt every unfinished job of ``vault`` (its vault was switched away from)."""

        with self._lock:
            jobs = [job for (job_vault, _id), job in self._jobs.items() if job_vault == vault]
        for job in jobs:
            with job.lock:
                if not job.done.is_set():
                    job.interrupted = True

    def supersede(self, vault: str, key: str) -> None:
        """Cancel every unfinished job of ``vault`` with this supersede key (a newer request replaces them)."""

        with self._lock:
            older = [job for (job_vault, _id), job in self._jobs.items()
                     if job_vault == vault and job.supersede_key == key]
        for job in older:
            with job.lock:
                if not job.done.is_set():
                    job.cancelled = True

    def _running_now(self) -> int:
        """Under ``self._lock``: jobs whose thread has not ended (a cancelled one still holds its thread)."""

        return sum(1 for job in self._jobs.values()
                   if not job.done.is_set() or (job.thread is not None and job.thread.is_alive()))

    def _drop_finished(self) -> None:
        """Under ``self._lock``: drop the oldest finished results beyond the bound; their records stay."""

        finished = [job for job in self._jobs.values() if job.done.is_set()]
        for job in finished[:max(0, len(self._jobs) - self._kept)]:
            key = (job.vault_key, job.job_id)
            self._jobs.pop(key, None)
            state = job.state()
            record = self._records.get(key)
            if record is not None:
                record.status, record.notes, record.requests_sent = (state["status"], state["notes"],
                                                                     state["requests_sent"])
        if not self._remember_ids:
            while len(self._records) > self._record_limit:
                oldest = next(iter(self._records))
                if oldest in self._jobs:
                    break
                self._records.pop(oldest)

    def _finished(self) -> None:
        with self._lock:
            self._drop_finished()

    def start(self, ctx: Any, *, kind: str, job_id: str, work: Callable[[PolledJob], Any],
              request_key: Any = None, foreground_kind: str | None = None,
              supersede_key: str | None = None, attachments: dict[str, Any] | None = None) -> PolledJob:
        """Start ``work(job)`` on a thread the context owns; its return value is the job's result.

        ``supersede_key``: every unfinished job of this vault with the same key is cancelled first.
        Refused (``jobs_busy``, retryable) while this registry already runs its bound of jobs, and
        (``request_ids_full``) when a remembering registry has no room for a new id."""

        from learnloop.ai import plan_fallback

        vault, repository = ctx.require_vault()
        key = vault_key(ctx)
        jobs = background_jobs(ctx)
        epoch = jobs.epoch()
        job = PolledJob(job_id, kind, request_key, time.monotonic(), vault_key=key, supersede_key=supersede_key,
                        attachments=dict(attachments or {}), _live=lambda: not jobs.closed_since(epoch))
        if supersede_key is not None:
            self.supersede(key, supersede_key)
        with self._lock:
            if (key, job_id) in self._jobs or (key, job_id) in self._records:
                raise ValueError(f"job {job_id!r} exists")  # callers answer a repeat before starting
            if self._running_now() >= self._running:
                raise SidecarError("jobs_busy", BUSY_MESSAGE, retryable=True, details={"running": self._running})
            if self._remember_ids and len(self._records) >= self._record_limit:
                raise SidecarError("request_ids_full", IDS_FULL_MESSAGE, details={"remembered": self._record_limit})
            self._jobs[(key, job_id)] = job
            self._records[(key, job_id)] = Receipt(job_id, key, kind, request_key)
            self._drop_finished()
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
                        # Work that outlived its vault's turn publishes nothing (the poll says interrupted).
                        job.result = None if job.interrupted else result
                except BaseException as exc:  # noqa: BLE001 - every failure answers the job, never the loop
                    error = as_job_error(exc, cancelled=job.cancelled)
                    with job.lock:
                        job.error = error
                finally:
                    job.fallback_offer = offers.hint()
                    job.done.set()
                    # Pruned as each job finishes, not only when the next starts.
                    self._finished()

        job.thread = jobs.spawn(run, name=f"{kind}-{job_id}", epoch=epoch)
        return job


def registry(ctx: Any, name: str, **kwargs: Any) -> PolledJobs:
    """``ctx``'s registry of one kind of polled job (made on first use with ``kwargs``)."""

    jobs = getattr(ctx, name, None)
    if jobs is None:
        jobs = PolledJobs(**kwargs)
        setattr(ctx, name, jobs)
    # Known to the context, so a vault switch reaches it (whoever set the attribute).
    known = getattr(ctx, "polled_registries", None)
    if known is None:
        known = ctx.polled_registries = {}
    known[name] = jobs
    return jobs


def interrupt_vault(ctx: Any, vault_root: Any) -> None:
    """A vault switch: every unfinished polled job of ``vault_root`` sends no further request, ends
    ``interrupted`` and wakes nothing of the context. Only polled jobs: other background jobs guard their own
    vault, and a request already sent finishes and is recorded in its own vault as before."""

    if not vault_root:
        return
    vault = str(Path(vault_root).resolve())
    for jobs in list((getattr(ctx, "polled_registries", None) or {}).values()):
        jobs.interrupt(vault)


__all__ = ["CANCELLED", "DONE", "EXPIRED", "FAILED", "MAX_KEPT_JOBS", "MAX_RECEIPTS", "MAX_REMEMBERED_IDS",
           "MAX_RUNNING", "QUEUED", "RUNNING", "PolledJob", "PolledJobs", "Receipt", "as_job_error", "interrupt_vault",
           "registry", "vault_key"]
