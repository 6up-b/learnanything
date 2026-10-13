"""The sidecar's post-attempt worker (Slice 1 §11).

Three daemon slots - ``diagnose`` (concurrency 1, strict attempt order),
``embed`` (concurrency 1, unordered) and ``gaps`` (learner-text gaps,
concurrency 1, oldest first: ``learner_text_gap_jobs``) - drain their queues
on their own SQLite connection, in short transactions. The queue is durable and lease-fenced,
so a process exit loses at most the in-flight model call; the next start (or the
next notify) reclaims expired leases. Built on the ``ExamGradingManager``
pattern: threads run in a copy of the starting context, so ``model_call``
receipts still record.

The worker starts lazily on the first :meth:`notify` (a submit that queued a
job), so a joint vault never starts a thread. ``autostart=False`` keeps jobs
queued until :meth:`run_pending` is called, which tests use for determinism.
"""

from __future__ import annotations

import contextvars
import logging
import sqlite3
import threading
import time
from typing import Any, Callable

from learnloop.ids import new_ulid

LOG = logging.getLogger(__name__)

#: Poll interval when idle, so backoff and lease expiries are picked up even
#: without a notify.
IDLE_POLL_SECONDS = 30.0
#: SQLITE_BUSY: the sidecar treats lock errors as non-retryable, so the worker
#: retries them itself with a bounded backoff (§11).
BUSY_RETRIES = 5
BUSY_BACKOFF_SECONDS = 0.5
KINDS = ("diagnose", "embed", "gaps")

VaultSupplier = Callable[[], tuple[Any, Any] | None]


def _is_busy(exc: BaseException) -> bool:
    return isinstance(exc, sqlite3.OperationalError) and (
        "locked" in str(exc).lower() or "busy" in str(exc).lower()
    )


class PostAttemptWorker:
    def __init__(self, *, autostart: bool = True) -> None:
        self.autostart = autostart
        self._lock = threading.RLock()
        self._wake = {kind: threading.Event() for kind in KINDS}
        self._threads: dict[str, threading.Thread] = {}
        self._stop = threading.Event()
        self._changed = threading.Condition(self._lock)
        self._supplier: VaultSupplier | None = None
        self.owner = f"sidecar:{new_ulid()}"
        #: Test seams; None means the configured routes.
        self.client_factory: Callable[[Any], Any] | None = None
        self.embedding_factory: Callable[[Any], Any] | None = None
        #: vault -> learner-text gap PipelineClients (test seam; None: the routes).
        self.gap_clients: Callable[[Any], Any] | None = None
        self.last_errors: list[str] = []
        #: session id -> seconds the last next-item wait took, until the
        #: serve that follows it records it (E7).
        self._waits: dict[str, float] = {}

    def note_wait(self, session_id: str, seconds: float) -> None:
        with self._lock:
            self._waits[session_id] = float(seconds)

    def take_wait(self, session_id: str) -> float:
        with self._lock:
            return self._waits.pop(session_id, 0.0)

    def bind(self, supplier: VaultSupplier) -> None:
        """``supplier`` returns the CURRENT (vault, sqlite path) or None."""

        with self._lock:
            self._supplier = supplier

    # -- lifecycle -------------------------------------------------------------

    def notify(self) -> None:
        """A job may be runnable: wake both slots (start them on first use)."""

        if not self.autostart:
            return
        with self._lock:
            self._stop.clear()
            for kind in KINDS:
                thread = self._threads.get(kind)
                if thread is None or not thread.is_alive():
                    context = contextvars.copy_context()
                    thread = threading.Thread(
                        target=context.run,
                        args=(self._loop, kind),
                        name=f"learnloop-post-attempt-{kind}",
                        daemon=True,
                    )
                    self._threads[kind] = thread
                    thread.start()
                self._wake[kind].set()

    @property
    def running(self) -> bool:
        with self._lock:
            return any(thread.is_alive() for thread in self._threads.values())

    def shutdown(self, timeout: float = 2.0) -> None:
        self._stop.set()
        for event in self._wake.values():
            event.set()
        with self._lock:
            threads = list(self._threads.values())
        for thread in threads:
            thread.join(timeout=timeout)

    # -- work --------------------------------------------------------------------

    def _repository(self, sqlite_path: Any) -> Any:
        from learnloop.db.repositories import Repository

        # Its own connection: attach, never re-run migrations from a thread.
        return Repository.attach(sqlite_path)

    def run_pending(self, kind: str = "diagnose", *, max_jobs: int = 100, clock: Any = None) -> list[Any]:
        """Synchronously run runnable jobs of ``kind`` (tests and drains)."""

        from learnloop.diagnosis.split.jobs import process_next_job

        supplied = self._supplier() if self._supplier is not None else None
        if supplied is None:
            return []
        vault, sqlite_path = supplied
        repository = self._repository(sqlite_path)
        if kind == "gaps":
            return self._run_gaps(vault, repository, max_jobs=max_jobs, clock=clock)
        outcomes: list[Any] = []
        while len(outcomes) < max_jobs:
            result = self._with_busy_retry(
                lambda: process_next_job(
                    vault,
                    repository,
                    kind=kind,
                    owner=self.owner,
                    client_factory=(
                        (lambda: self.client_factory(vault)) if self.client_factory is not None else None
                    ),
                    embedding_factory=(
                        (lambda: self.embedding_factory(vault)) if self.embedding_factory is not None else None
                    ),
                    # Shutdown stops before the next paid request; a job
                    # leased by then is released unspent.
                    cancelled=self._stop.is_set,
                    clock=clock,
                )
            )
            if result is None:
                break
            outcomes.append(result)
            with self._changed:
                self._changed.notify_all()
            if kind == "diagnose":
                # An applied diagnosis may have queued a learner-text gap job.
                self._wake["gaps"].set()
            if result.state in ("released", "lease_lost"):
                break
        return outcomes

    def _run_gaps(self, vault: Any, repository: Any, *, max_jobs: int, clock: Any) -> list[Any]:
        from learnloop.diagnosis.text_gaps.jobs import process_next_gap_job

        outcomes: list[Any] = []
        clients = self.gap_clients(vault) if self.gap_clients is not None else None
        while len(outcomes) < max_jobs and not self._stop.is_set():
            result = self._with_busy_retry(
                lambda: process_next_gap_job(vault.root, repository, owner=self.owner, clients=clients, clock=clock)
            )
            if result is None:
                break
            outcomes.append(result)
            with self._changed:
                self._changed.notify_all()
            if result.state in ("released", "lease_lost"):
                break
        return outcomes

    def _with_busy_retry(self, work: Callable[[], Any]) -> Any:
        for attempt in range(BUSY_RETRIES + 1):
            try:
                return work()
            except sqlite3.OperationalError as exc:
                if not _is_busy(exc) or attempt == BUSY_RETRIES:
                    raise
                time.sleep(BUSY_BACKOFF_SECONDS * (2**attempt))
        return None

    def _loop(self, kind: str) -> None:
        wake = self._wake[kind]
        while not self._stop.is_set():
            try:
                self.run_pending(kind)
            except Exception as exc:  # noqa: BLE001 - a worker never dies on one job
                LOG.exception("post-attempt %s worker iteration failed", kind)
                with self._lock:
                    self.last_errors = [*self.last_errors[-9:], f"{kind}:{type(exc).__name__}"]
            wake.wait(timeout=IDLE_POLL_SECONDS)
            wake.clear()

    # -- bounded waiting (§11) ------------------------------------------------------

    def wait_for(self, pending: Callable[[], list[str]], timeout: float) -> tuple[list[str], float]:
        """Wait until ``pending()`` is empty or ``timeout`` passes.

        Returns (still pending, seconds waited). Wakes on each job the worker
        settles and re-checks the durable queue (the source of truth).
        """

        started = time.monotonic()
        remaining = pending()
        if not remaining or timeout <= 0 or not self.running:
            return remaining, 0.0
        deadline = started + timeout
        with self._changed:
            while remaining:
                left = deadline - time.monotonic()
                if left <= 0:
                    break
                self._changed.wait(timeout=min(left, 0.5))
                remaining = pending()
        return remaining, round(time.monotonic() - started, 3)


__all__ = ["PostAttemptWorker"]
