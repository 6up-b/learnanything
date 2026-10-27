"""The asynchronous jobs a sidecar context starts from a request (test-thread-leak
review F1).

A Reader cue discovery, a library ask, a reading-path judgment, an intent
routing, a hint or a coverage check runs on a thread of its own, started by
the request that asked for it and read back by later polls. Before this
registry those threads belonged to nobody: ``SidecarContext.close`` (the
``shutdown`` RPC, EOF, a host dropping a context) could not reach them, so a
job kept sending model requests for a context that was gone.

Each such thread is started through :meth:`BackgroundJobs.spawn`, which

* records the *epoch* the job started in. :meth:`BackgroundJobs.close` ends
  that epoch first, so every job started before the close is cancelled at
  once: a job's own cancellation predicate (``closed_since(epoch)``) turns
  true, and every physical model request it would still make is refused by a
  request gate (:func:`learnloop.ai.execution.gate_model_requests`) with
  :class:`~learnloop.ai.spend.SpendCancelled`, the refusal every paid path
  already stops on. A request already sent finishes; its receipt is kept.
* joins the threads it started for a bounded time (never hangs: a thread
  inside a model call is a daemon thread and ends with its call).

A job started after a close belongs to the new epoch and runs normally (a
later ``load`` or request starts work again, as the post-attempt worker's
``notify`` does after its ``shutdown``).
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable

from learnloop.ai.execution import active_request_gate, gate_model_requests
from learnloop.ai.spend import SpendCancelled

#: How long ``close`` waits for the jobs it cancelled, in all (a guardrail,
#: not a parameter: the post-attempt worker's own bounded join).
CLOSE_JOIN_SECONDS = 2.0


class _ClosingGate:
    """Refuses a job's physical model requests once its epoch has ended; an
    outer gate (installed by the job itself) is admitted first and settled on a
    refusal, so nothing it reserved is kept for a request never sent."""

    def __init__(self, jobs: "BackgroundJobs", epoch: int, outer: Any) -> None:
        self._jobs = jobs
        self._epoch = epoch
        self._outer = outer

    def admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> Any:
        admission = None if self._outer is None else self._outer.admit(client, purpose=purpose, prompt=prompt,
                                                                       budget=budget)
        if self._jobs.closed_since(self._epoch):
            if self._outer is not None:
                self._outer.settle(admission, {})
            raise SpendCancelled(f"{purpose} not sent: the sidecar context closed")
        return admission

    def settle(self, admission: Any, usage: dict[str, Any]) -> None:
        if self._outer is not None:
            self._outer.settle(admission, usage)


class BackgroundJobs:
    """The request-started job threads of one sidecar context."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._epoch = 0
        self._threads: list[threading.Thread] = []

    def epoch(self) -> int:
        """The epoch a job starting now belongs to (capture it before building
        the job's cancellation predicate, and pass it to :meth:`spawn`)."""

        with self._lock:
            return self._epoch

    def closed_since(self, epoch: int) -> bool:
        """Whether the context was closed after a job of ``epoch`` started."""

        with self._lock:
            return self._epoch != epoch

    def spawn(self, target: Callable[[], Any], *, name: str, epoch: int | None = None) -> threading.Thread:
        """Start ``target`` on a daemon thread owned by this context: a close
        cancels it (its requests refused from then on) and joins it, bounded."""

        start_epoch = self.epoch() if epoch is None else epoch

        def run() -> None:
            with gate_model_requests(_ClosingGate(self, start_epoch, active_request_gate())):
                target()

        thread = threading.Thread(target=run, name=name, daemon=True)
        with self._lock:
            self._threads = [kept for kept in self._threads if kept.is_alive()]
            self._threads.append(thread)
        thread.start()
        return thread

    def cancel(self) -> list[threading.Thread]:
        """End the current epoch: every job started so far is cancelled.
        Returns the threads still running."""

        with self._lock:
            self._epoch += 1
            self._threads = [kept for kept in self._threads if kept.is_alive()]
            return list(self._threads)

    def close(self, timeout: float = CLOSE_JOIN_SECONDS) -> None:
        """Cancel every job started so far, then join them for at most
        ``timeout`` seconds in all. Idempotent."""

        threads = self.cancel()
        deadline = time.monotonic() + timeout
        for thread in threads:
            if thread is not threading.current_thread():
                thread.join(timeout=max(0.0, deadline - time.monotonic()))

    @property
    def running(self) -> list[threading.Thread]:
        with self._lock:
            return [kept for kept in self._threads if kept.is_alive()]


def background_jobs(ctx: Any) -> BackgroundJobs:
    """``ctx``'s job registry (a stand-in context without one gets its own)."""

    jobs = getattr(ctx, "background_jobs", None)
    if jobs is None:
        jobs = BackgroundJobs()
        try:
            ctx.background_jobs = jobs
        except AttributeError:  # a frozen stand-in: the jobs still run, owned by nobody
            pass
    return jobs


__all__ = ["CLOSE_JOIN_SECONDS", "BackgroundJobs", "background_jobs"]
