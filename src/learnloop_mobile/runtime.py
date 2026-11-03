"""The host's practice runtime (spec §3.1): two workers, each owning one secondary context.

No context is ever shared between threads. HTTP threads only enqueue and wait. The RPC
worker runs short allowlisted methods in arrival order; the job worker runs long
mutations as durable jobs, so a 60 to 180 s grade never blocks a short read. The two
contexts relate to each other as two processes do: SQLite serializes writes, the
completion lock serializes post-attempt completion, the vault lock serializes YAML.

Nothing here runs at import or at host start. A host that only ever takes captures
never loads a vault or imports the sidecar (G6a): the first RPC starts the workers.
"""
from __future__ import annotations

from collections import deque
from concurrent.futures import Future
from dataclasses import dataclass
import logging
from pathlib import Path
import sqlite3
import threading
import time
from typing import Any, Callable, Mapping

from learnloop import capture
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid

from learnloop_mobile.adapter import canonical_hash, flat_error
from learnloop_mobile.allowlist import MobileMethod

LOG = logging.getLogger(__name__)

#: §4.6's admission: beyond these the host answers 503 ``host_busy``.
RPC_QUEUE_LIMIT = 16
JOB_QUEUE_LIMIT = 8
#: How long a stopping host waits for a running grade; the unit's TimeoutStopSec is 300.
STOP_JOIN_SECONDS = 280.0
#: How long the status endpoint trusts its last grading-readiness read.
READINESS_TTL_SECONDS = 60.0
#: A job's terminal write meeting a busy database is retried this many times, because
#: the handler's commit stands and the row is all the phone has to read.
_FINISH_RETRIES = 5
_FINISH_BACKOFF_SECONDS = 0.5
#: Past those, how often this run tries a terminal write it still owes. A `keep` bound: a slow
#: try costs nothing a phone sees, since the status reads already answer from the debt.
_FINISH_DEBT_RETRY_SECONDS = 5.0


class HostBusy(Exception):
    """An admission queue is full."""


class ParamsInvalid(Exception):
    def __init__(self, details: Mapping[str, Any]):
        super().__init__("Invalid params.")
        self.details = dict(details)


class _Worker:
    """One thread and the one context it owns. Everything on the context runs here."""

    def __init__(self, name: str, make_context: Callable[[], Any], limit: int):
        self.name = name
        self._make_context = make_context
        self._limit = limit
        self._queue: deque[tuple[Callable[["_Worker"], Any], Future]] = deque()
        self._wake = threading.Condition()
        self._stopping = False
        self._thread: threading.Thread | None = None
        self.context: Any = None

    def pending(self) -> int:
        with self._wake:
            return len(self._queue)

    def has_room(self) -> bool:
        return self.pending() < self._limit

    def submit(self, work: Callable[["_Worker"], Any], *, admit: bool = True) -> Future:
        """Queue ``work(worker)``. ``admit=False`` is a job already accepted durably: a
        restarted host's, or one whose admission ran in its acceptance transaction."""

        future: Future = Future()
        with self._wake:
            if self._stopping or (admit and len(self._queue) >= self._limit):
                raise HostBusy()
            self._queue.append((work, future))
            if self._thread is None:
                self._thread = threading.Thread(target=self._run, name=self.name, daemon=True)
                self._thread.start()
            self._wake.notify()
        return future

    def _run(self) -> None:
        while True:
            with self._wake:
                while not self._queue and not self._stopping:
                    self._wake.wait()
                if self._stopping:
                    # What is queued stays durable (§3.1): a job's row waits for the next
                    # start, and a short request's caller gets host_busy.
                    abandoned, self._queue = list(self._queue), deque()
                    for _work, future in abandoned:
                        future.set_exception(HostBusy())
                    return
                work, future = self._queue.popleft()
            if not future.set_running_or_notify_cancel():
                continue
            try:
                future.set_result(work(self))
            except BaseException as error:  # noqa: BLE001 - the worker outlives one request
                future.set_exception(error)

    def loaded_context(self) -> Any:
        """This worker's context, loaded on its own thread at first use (and retried if that failed)."""

        if self.context is None:
            self.context = self._make_context()
        return self.context

    def stop(self, timeout: float) -> bool:
        """Stop taking work and let the running request finish. False if it outlived ``timeout``."""

        with self._wake:
            self._stopping = True
            self._wake.notify_all()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=timeout)
        finished = thread is None or not thread.is_alive()
        context, self.context = self.context, None
        if context is not None and finished:
            context.close()
        return finished


@dataclass(frozen=True)
class JobView:
    """A job's state as the status endpoints and ``/rpc`` answer it."""

    id: str
    request_id: str
    state: str
    result: Any = None
    error: dict[str, Any] | None = None

    @property
    def terminal(self) -> bool:
        return self.state in (capture.COMPLETED, capture.FAILED)

    @classmethod
    def of(cls, job: Mapping[str, Any]) -> "JobView":
        return cls(id=job["id"], request_id=job["request_id"], state=job["state"], result=job["result"],
                   error=job["error"])


#: Long methods whose ``request_id`` is the submission id (§6.3) and whose acceptance
#: checks the session's owner (§6.5). A clarification names an attempt, not a session.
SUBMIT_METHODS = frozenset({"submit_attempt", "submit_dont_know"})


class HostRuntime:
    """The two workers and the jobs they run, for one pinned vault."""

    def __init__(self, vault: Path, repo: Repository, read_repo: Repository):
        self._vault = vault
        self._repo = repo
        self._read_repo = read_repo
        self.boot_id = new_ulid()
        self._post_attempt: Any = None
        self._setup_lock = threading.Lock()
        self._started = False
        self.rpc_worker = _Worker("mobile-rpc", self._load_context, RPC_QUEUE_LIMIT)
        self.job_worker = _Worker("mobile-job", self._load_job_context, JOB_QUEUE_LIMIT)
        # job id -> what its waiters wait on. Only for jobs this run holds.
        self._waiters: dict[str, Future] = {}
        self._waiters_lock = threading.Lock()
        self._readiness: tuple[float, bool] | None = None
        self._readiness_refreshing = False
        # Terminal writes this run still owes (job id -> what the row should say). The handler's
        # commit stands, so the status reads answer from here until the row catches up.
        self._owed: dict[str, tuple[JobView, Any]] = {}
        self._owed_lock = threading.Lock()
        self._owed_thread: threading.Thread | None = None
        self._owed_stop = threading.Event()

    # -- contexts (each on its worker's own thread) ----------------------------

    def _shared_post_attempt(self) -> Any:
        """One post-attempt worker for the host, so a queue build's bounded wait on the RPC
        context sees the diagnosis the job context's answer queued. Its queue is durable
        and lease-fenced, so a desktop draining beside it runs nothing twice."""

        from learnloop_sidecar.post_attempt_worker import PostAttemptWorker

        with self._setup_lock:
            if self._post_attempt is None:
                self._post_attempt = PostAttemptWorker()
            return self._post_attempt

    def _load_context(self) -> Any:
        from learnloop_sidecar.context import SidecarContext

        context = SidecarContext(post_attempt_worker=self._shared_post_attempt())
        context.load_secondary(self._vault)
        return context

    def _load_job_context(self) -> Any:
        context = self._load_context()
        # §3.1 leaves "queued work durable for the primary", which would leave a phone's
        # diagnosis pending for as long as the desktop app stays closed (D2: the phone
        # works with it closed). This one queue drains here, from this context; everything
        # else a primary owes stays the primary's.
        context.post_attempt_worker.bind(context._worker_target)
        return context

    def ensure_started(self) -> None:
        """The first RPC starts both workers, so the job context is bound before a queue
        build on the RPC context can wait on a diagnosis."""

        with self._setup_lock:
            if self._started:
                return
            self._started = True

        def load(worker: _Worker) -> None:
            try:
                worker.loaded_context()
            except Exception:  # the request that needs it reports the typed error
                LOG.warning("%s: context not loaded yet", worker.name, exc_info=True)

        self.job_worker.submit(load, admit=False)
        self.rpc_worker.submit(load, admit=False)

    @staticmethod
    def _dispatch(worker: _Worker, method: str, params: Mapping[str, Any], origin: Any) -> dict[str, Any]:
        from learnloop_sidecar.errors import SidecarError, sidecar_error
        from learnloop_sidecar.server import _handle

        request_id = new_ulid()
        try:
            context = worker.loaded_context()
            # §3.1: reloads when another process changed the vault's files, at most 2 s stale.
            context.refresh_if_content_changed()
        except SidecarError as error:
            return {"jsonrpc": "2.0", "id": request_id, "error": sidecar_error(error)}
        with context.acting_as(origin):
            response = _handle(context, {"jsonrpc": "2.0", "id": request_id, "method": method, "params": dict(params)})
        assert response is not None  # every request carries an id
        return response

    def _origin(self, device_id: str, *, accepted_session_id: str | None = None) -> Any:
        from learnloop_sidecar.request_origin import RequestOrigin

        return RequestOrigin(device_id=device_id, accepted_session_id=accepted_session_id)

    # -- requests ----------------------------------------------------------------

    def validate(self, method: MobileMethod, params: Mapping[str, Any]) -> dict[str, Any]:
        """The method's own model over the phone's params; canonical for a job's hash."""

        from pydantic import ValidationError

        from learnloop_sidecar.server import METHOD_REGISTRY, _safe_validation_errors  # imports every handler

        self.ensure_started()
        try:
            validated = METHOD_REGISTRY[method.name].params_model.model_validate(dict(params))
        except ValidationError as error:
            raise ParamsInvalid({"errors": _safe_validation_errors(error)}) from None
        return validated.model_dump(mode="json")

    def call_short(self, method: MobileMethod, params: Mapping[str, Any], device_id: str) -> Future:
        origin = self._origin(device_id)
        return self.rpc_worker.submit(lambda worker: self._dispatch(worker, method.name, params, origin))

    # -- jobs (§6.3) ------------------------------------------------------------

    def accept(
        self, method: MobileMethod, params: Mapping[str, Any], validated: Mapping[str, Any], *,
        request_id: str, device_id: str,
    ) -> JobView:
        """Commit the job, or find it; then it runs whether or not the caller is still here."""

        session_id = validated.get("session_id") if method.name in SUBMIT_METHODS else None

        def check_new() -> None:
            if not self.job_worker.has_room():
                raise HostBusy()
            # A submission that already committed answers from its receipt, whoever owns
            # the session now, as the handler does (PR-4).
            if session_id and self._repo.practice_attempt_by_submission_id(request_id) is None:
                self._repo.require_session_owner(str(session_id), device_id)

        job, enqueue = capture.accept_job(
            self._repo, device_id=device_id, request_id=request_id, method=method.name, params=dict(params),
            params_sha256=canonical_hash(validated), boot_id=self.boot_id, check_new=check_new,
        )
        if enqueue:
            self._enqueue(job)
        return JobView.of(job)

    def _enqueue(self, job: Mapping[str, Any]) -> None:
        with self._waiters_lock:
            self._waiters[job["id"]] = Future()
        try:
            self.job_worker.submit(lambda worker: self._run_job(worker, job), admit=False)
        except HostBusy:
            # Stopping: the row is durable and the next start runs it.
            LOG.info("job %s left for the next host start", job["id"])

    def _run_job(self, worker: _Worker, job: Mapping[str, Any]) -> None:
        job_id = job["id"]
        response: dict[str, Any] | None = None
        try:
            capture.start_job(self._repo, job_id)
            session_id = job["params"].get("session_id") or job["params"].get("sessionId")
            origin = self._origin(
                job["device_id"],
                accepted_session_id=str(session_id) if job["method"] in SUBMIT_METHODS and session_id else None,
            )
            response = self._dispatch(worker, job["method"], job["params"], origin)
        except Exception:
            LOG.exception("job %s failed", job_id)
            response = {"error": {"message": "This request stopped unexpectedly.", "data": {"code": "internal"}}}
        error = flat_error(response)
        view = JobView(id=job_id, request_id=job["request_id"],
                       state=capture.FAILED if error is not None else capture.COMPLETED,
                       result=None if error is not None else response.get("result"), error=error)
        self._finish(view, result=response.get("result"))
        with self._waiters_lock:
            waiter = self._waiters.pop(job_id, None)
        if waiter is not None:
            waiter.set_result(view)

    def _finish(self, view: JobView, *, result: Any) -> None:
        for attempt in range(_FINISH_RETRIES + 1):
            try:
                capture.finish_job(self._repo, view.id, result=result, error=view.error)
                return
            except sqlite3.OperationalError:
                if attempt == _FINISH_RETRIES:
                    # Busy past the retries, or a full disk: the row stays behind while this run
                    # answers for it and keeps trying. Dying here, a restart finds the row open
                    # and the handler's receipt beside it.
                    LOG.exception("job %s finished but its row was not written; retrying in the background", view.id)
                    self._owe(view, result)
                    return
                time.sleep(_FINISH_BACKOFF_SECONDS * (2 ** attempt))

    def _owe(self, view: JobView, result: Any) -> None:
        with self._owed_lock:
            self._owed[view.id] = (view, result)
            if self._owed_thread is None:
                self._owed_thread = threading.Thread(target=self._pay_owed, name="mobile-job-finish", daemon=True)
                self._owed_thread.start()

    def _pay_owed_once(self) -> None:
        with self._owed_lock:
            owed = list(self._owed.values())
        for view, result in owed:
            try:
                capture.finish_job(self._repo, view.id, result=result, error=view.error)
            except sqlite3.OperationalError:
                LOG.warning("job %s: its terminal write is still owed", view.id)
                continue
            with self._owed_lock:
                self._owed.pop(view.id, None)

    def _pay_owed(self) -> None:
        while not self._owed_stop.wait(_FINISH_DEBT_RETRY_SECONDS):
            self._pay_owed_once()
            with self._owed_lock:
                if not self._owed:
                    self._owed_thread = None
                    return

    def owed_finishes(self) -> int:
        with self._owed_lock:
            return len(self._owed)

    def _view_of(self, job: Mapping[str, Any]) -> JobView:
        """The row, unless this run has finished the job and owes the row its end."""

        view = JobView.of(job)
        if view.terminal:
            return view
        with self._owed_lock:
            owed = self._owed.get(view.id)
        return owed[0] if owed is not None else view

    def waiter(self, job_id: str) -> Future | None:
        with self._waiters_lock:
            return self._waiters.get(job_id)

    def recover(self) -> int:
        """A starting host's debt: the jobs another run left open (§6.3). No jobs, no sidecar."""

        requeued = capture.recover_jobs(self._repo, self.boot_id)
        for job in requeued:
            self._enqueue(job)
        return len(requeued)

    # -- status reads: never a handler, never a lock (§3.1) ---------------------

    def job_status(self, job_id: str) -> JobView | None:
        job = capture.get_job(self._read_repo, job_id)
        return self._view_of(job) if job is not None else None

    def submission_status(self, submission_id: str) -> dict[str, Any]:
        """§6.1: covers a desktop's submissions through their receipts. An attempt without a
        receipt is a completion under way; no attempt and no job is ``unknown``, which is
        the client's cue to treat the checkpoint as a draft (§6.5)."""

        job = capture.job_for_request(self._read_repo, submission_id)
        if job is not None:
            return _status_body(self._view_of(job))
        receipt = self._read_repo.attempt_submission_receipt(submission_id)
        if receipt is not None:
            return {"state": capture.COMPLETED, "result": receipt["result"]}
        if self._read_repo.practice_attempt_by_submission_id(submission_id) is not None:
            return {"state": capture.RUNNING}
        return {"state": "unknown"}

    def grading_ready(self) -> bool | None:
        """Last known grading readiness; None until the first RPC has loaded the vault.

        Stale while it refreshes: the status endpoint is a poll, and a route's readiness
        can start a provider's runtime, so it never waits for it. ``doctor`` checks the
        same thing against the unit's environment.
        """

        context = self.rpc_worker.context
        if context is None or context.vault is None:
            return None
        now = time.monotonic()
        if self._readiness is None or now - self._readiness[0] >= READINESS_TTL_SECONDS:
            if not self._readiness_refreshing:
                self._readiness_refreshing = True
                threading.Thread(target=self._refresh_readiness, args=(context.vault,),
                                 name="mobile-readiness", daemon=True).start()
        return self._readiness[1] if self._readiness is not None else None

    def _refresh_readiness(self, vault: Any) -> None:
        try:
            from learnloop_sidecar.handlers.ai_providers import ready_grading_provider

            _name, runtime, client = ready_grading_provider(vault)
            self._readiness = (time.monotonic(), bool(runtime.ready and client is not None))
        except Exception:
            LOG.warning("grading readiness not read", exc_info=True)
            self._readiness = (time.monotonic(), False)
        finally:
            self._readiness_refreshing = False

    def stop(self) -> None:
        """§3.1: stop accepting work, let a running job finish, leave queued jobs durable."""

        self.rpc_worker.stop(STOP_JOIN_SECONDS)
        if not self.job_worker.stop(STOP_JOIN_SECONDS):
            LOG.warning("a job outlived the stop; a restarted host picks it up")
        # One last try at what this run owes; what is left, the next start recovers from the row.
        self._owed_stop.set()
        self._pay_owed_once()


def _status_body(view: JobView) -> dict[str, Any]:
    body: dict[str, Any] = {"job_id": view.id, "state": view.state}
    if view.state == capture.COMPLETED:
        body["result"] = view.result
    elif view.state == capture.FAILED:
        body["error"] = view.error
    return body
