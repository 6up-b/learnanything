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
from dataclasses import dataclass, replace
import logging
from pathlib import Path
import sqlite3
import threading
import time
from typing import Any, Callable, Mapping

from learnloop import capture, provenance
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
#: How many times a committed attempt's completion may fail before the status says its feedback
#: is delayed and lets the phone open it. A `keep` bound: past it the reads go on trying, so it
#: only decides how long a phone waits on the grading screen.
_REDRIVES_BEFORE_DELAYED = 3


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

    id: str | None
    request_id: str
    state: str
    result: Any = None
    error: dict[str, Any] | None = None

    @property
    def terminal(self) -> bool:
        return self.state in (capture.COMPLETED, capture.FAILED, capture.RECORDED)

    @classmethod
    def of(cls, job: Mapping[str, Any]) -> "JobView":
        return cls(id=job["id"], request_id=job["request_id"], state=job["state"], result=job["result"],
                   error=job["error"])


#: Long methods whose ``request_id`` is the submission id (§6.3) and whose acceptance
#: checks the session's owner (§6.5). A clarification names an attempt, not a session.
SUBMIT_METHODS = frozenset(capture.SUBMIT_METHODS)


#: Request fields added after jobs were first hashed, left out of a request's canonical form while unset (see ``validate``).
OPTIONAL_SINCE_RE0: tuple[str, ...] = ("active_seconds",)


class HostRuntime:
    """The two workers and the jobs they run, for one pinned vault."""

    def __init__(self, vault: Path, repo: Repository, read_repo: Repository, *, phone_probes: bool = False,
                 phone_reader: bool = False):
        self._vault = vault
        self._repo = repo
        self._read_repo = read_repo
        #: Mobile v2 V3: the host's ``phone_probes``, carried on every origin it makes (never a parameter).
        self.phone_probes = phone_probes
        #: Mobile v2 V4: the host's ``phone_reader``, carried on every origin it makes (never a parameter).
        self.phone_reader = phone_reader
        self.boot_id = new_ulid()
        self._post_attempt: Any = None
        self._setup_lock = threading.Lock()
        self._started = False
        self.rpc_worker = _Worker("mobile-rpc", self._load_context, RPC_QUEUE_LIMIT)
        self.job_worker = _Worker("mobile-job", self._load_job_context, JOB_QUEUE_LIMIT)
        # job id -> what its waiters wait on. Only for jobs this run holds.
        self._waiters: dict[str, Future] = {}
        self._waiters_lock = threading.Lock()
        # job id -> whether the app that sent it said it answers probes (mobile v2 V3, F3). Only for jobs this run
        # accepted; under _waiters_lock.
        self._probes_said: dict[str, bool] = {}
        # Mobile v2 V4: job id -> whether the app that sent it said it has the Reader. Under _waiters_lock.
        self._reader_said: dict[str, bool] = {}
        self._readiness: tuple[float, bool] | None = None
        self._readiness_refreshing = False
        # Terminal writes this run still owes (job id -> what the row should say). The handler's
        # commit stands, so the status reads answer from here until the row catches up.
        self._owed: dict[str, tuple[JobView, Mapping[str, Any]]] = {}
        self._owed_lock = threading.Lock()
        self._owed_thread: threading.Thread | None = None
        self._owed_stop = threading.Event()
        # Committed attempts this run is re-driving, and how their completions have gone: the
        # count of failed tries, or None once the handler has said it can't finish. All under
        # _waiters_lock, so a status poll starts one recovery at most.
        self._redriving: set[str] = set()
        self._redrive_failures: dict[str, int | None] = {}

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
        # One phone request is one learner-visible action (ADR-017): its trace covers the reload as well as the
        # handler, and the sidecar's ``_handle`` continues it rather than starting its own.
        with provenance.trace_scope() as trace_id:
            try:
                context = worker.loaded_context()
                # §3.1: reloads when another process changed the vault's files, at most 2 s stale.
                context.refresh_if_content_changed()
            except SidecarError as error:
                return {"jsonrpc": "2.0", "id": request_id, "error": sidecar_error(error)}
            with context.acting_as(origin):
                response = _handle(context, {"jsonrpc": "2.0", "id": request_id, "method": method,
                                             "params": dict(params)}, trace_id=trace_id)
        assert response is not None  # every request carries an id
        return response

    def _origin(self, device_id: str, *, accepted_session_id: str | None = None, probes: bool = True,
                reader: bool = False, job_id: str | None = None) -> Any:
        """``probes``: the app said it answers probes (Codex review of V3, F3; the host's ``/rpc`` reads it). A job
        keeps the switch alone: its only V3 meaning is a submit naming a presentation, which the host admitted only
        from an app that said so. ``reader`` (mobile v2 V4): the app said it has the Reader, so the plan may hand it
        a reading step; a cached V3 app, which has none, is never handed one it can't end. ``job_id`` (V4, Codex
        review F5): the job this runs as, whose receipt an outbox intent's handler commits with its rows."""

        from learnloop_sidecar.request_origin import RequestOrigin

        return RequestOrigin(device_id=device_id, accepted_session_id=accepted_session_id,
                             phone_probes=self.phone_probes and probes, phone_reader=self.phone_reader and reader,
                             job_id=job_id)

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
        # A field a request left unset must not change its hash, or an identical retry of a request accepted before the
        # field existed (RE0's ``active_seconds``, on every request model that gained it) reads as another request
        # (``submission_conflict``). So an unset ``active_seconds`` is left out, and the hash is what it was.
        unset = {name for name in OPTIONAL_SINCE_RE0 if name in type(validated).model_fields
                 and getattr(validated, name) is None}
        return validated.model_dump(mode="json", exclude=unset)

    def call_short(
        self, method: MobileMethod, params: Mapping[str, Any], device_id: str, *, timing: dict[str, float] | None = None,
        probes: bool = False, reader: bool = False,
    ) -> Future:
        """``timing``, if given, gets the worker's ``started`` and ``finished`` monotonic times, for
        ``Server-Timing`` (mobile v2 §4.5): the queue wait and the handler, measured, not guessed.
        ``probes``: the app said it answers probes (mobile v2 V3, F3); without it the request is V2's.
        ``reader``: the app said it has the Reader (V4); without it the request is V3's."""

        origin = self._origin(device_id, probes=probes, reader=reader)

        def run(worker: _Worker) -> dict[str, Any]:
            if timing is not None:
                timing["started"] = time.monotonic()
            try:
                return self._dispatch(worker, method.name, params, origin)
            finally:
                if timing is not None:
                    timing["finished"] = time.monotonic()

        return self.rpc_worker.submit(run)

    # -- jobs (§6.3) ------------------------------------------------------------

    def accept(
        self, method: MobileMethod, params: Mapping[str, Any], validated: Mapping[str, Any], *,
        request_id: str, device_id: str, probes: bool = False, reader: bool = False,
    ) -> JobView:
        """Commit the job, or find it; then it runs whether or not the caller is still here.

        ``probes``: the app said it answers probes (mobile v2 V3; Codex review of V3, F3). The job runs with it
        (:meth:`_job_probes_for`), so a cached V2 app's plan Next is V2's whenever it runs."""

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
            with self._waiters_lock:
                self._probes_said[job["id"]] = probes
                self._reader_said[job["id"]] = reader
            self._enqueue(job)
            return JobView.of(job)
        return self._current_view(job)

    def _job_probes_for(self, job: Mapping[str, Any]) -> bool:
        """What the app said when this run accepted the job. A job another run accepted (a restart's) is a submit
        or not: a submit's only V3 meaning is naming a presentation, which the host admitted only from an app that
        said it answers probes, so it keeps the switch; anything else runs as V2's (it never burns a probe)."""

        with self._waiters_lock:
            said = self._probes_said.pop(job["id"], None)
        return said if said is not None else job["method"] in SUBMIT_METHODS

    def _job_reader_for(self, job: Mapping[str, Any]) -> bool:
        """Mobile v2 V4: what the app said when this run accepted the job. A job another run accepted (a restart's)
        runs as V3's: no reading step is handed to an app not known to have the Reader."""

        with self._waiters_lock:
            return bool(self._reader_said.pop(job["id"], False))

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
                probes=self._job_probes_for(job),
                reader=self._job_reader_for(job),
                job_id=job_id,
            )
            response = self._dispatch(worker, job["method"], job["params"], origin)
        except Exception:
            LOG.exception("job %s failed", job_id)
            response = {"error": {"message": "This request stopped unexpectedly.", "data": {"code": "internal"}}}
        error = flat_error(response)
        view = JobView(id=job_id, request_id=job["request_id"],
                       state=capture.FAILED if error is not None else capture.COMPLETED,
                       result=None if error is not None else response.get("result"), error=error)
        view = self._finish(view, job)
        with self._waiters_lock:
            waiter = self._waiters.pop(job_id, None)
        if waiter is not None:
            waiter.set_result(view)

    def _ending(self, view: JobView, job: Mapping[str, Any]) -> JobView:
        """How a job really ended (R2): a submit fails only if no attempt committed under it.

        The handler's error may be its completion's: then the job isn't over, and the status
        reads re-drive the completion. ``submission_committed`` says it can't finish: recorded.
        """

        if view.state != capture.FAILED or job["method"] not in SUBMIT_METHODS:
            return view
        receipt, attempt = self._committed(self._repo, job, job["request_id"])
        if receipt is not None:
            return replace(view, state=capture.COMPLETED, result=receipt["result"], error=None)
        if attempt is None:
            return view
        if (view.error or {}).get("code") == capture.SUBMISSION_COMMITTED:
            return replace(view, state=capture.RECORDED, error=capture.recorded_error(attempt))
        return replace(view, state=capture.RUNNING, error=None)

    def _finish(self, view: JobView, job: Mapping[str, Any]) -> JobView:
        """Write the job's end, and return it as its waiters should hear it."""

        ending: JobView | None = None
        for attempt in range(_FINISH_RETRIES + 1):
            try:
                ending = self._ending(view, job)
                if ending.terminal:
                    capture.finish_job(self._repo, ending.id, result=ending.result, error=ending.error, state=ending.state)
                return ending
            except sqlite3.OperationalError:
                if attempt == _FINISH_RETRIES:
                    # Busy past the retries, or a full disk: the row stays behind while this run
                    # answers for it and keeps trying. Dying here, a restart finds the row open
                    # and the handler's receipt beside it.
                    LOG.exception("job %s finished but its row was not written; retrying in the background", view.id)
                    self._owe(view, job)
                    # A failure not yet checked against the attempts isn't known to be one.
                    return ending if ending is not None else replace(view, state=capture.RUNNING, error=None)
                time.sleep(_FINISH_BACKOFF_SECONDS * (2 ** attempt))
        raise AssertionError("the loop returns on its last pass")

    def _owe(self, view: JobView, job: Mapping[str, Any]) -> None:
        with self._owed_lock:
            self._owed[view.id] = (view, job)
            if self._owed_thread is None:
                self._owed_thread = threading.Thread(target=self._pay_owed, name="mobile-job-finish", daemon=True)
                self._owed_thread.start()

    def _pay_owed_once(self) -> None:
        with self._owed_lock:
            owed = list(self._owed.values())
        for view, job in owed:
            try:
                ending = self._ending(view, job)
                if ending.terminal:
                    capture.finish_job(self._repo, ending.id, result=ending.result, error=ending.error, state=ending.state)
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
        return self._current_view(job) if job is not None else None

    def submission_status(self, submission_id: str, device_id: str | None = None) -> dict[str, Any]:
        """§6.1: what committed decides (R2), before anything a job's row says. A receipt is
        ``completed``; an attempt without one is a completion under way, or ``recorded`` once
        it has stopped trying to be, and either way its key is spent. So ``failed`` means no
        attempt committed. No attempt and no job is ``unknown``, which is the client's cue to
        treat the checkpoint as a draft (§6.5). Covers a desktop's submissions too."""

        job = capture.job_for_request(self._read_repo, submission_id)
        if job is not None:
            return _status_body(self._current_view(job))
        view = self._what_committed(None, submission_id, device_id)
        return _status_body(view) if view is not None else {"state": "unknown"}

    def _current_view(self, job: Mapping[str, Any]) -> JobView:
        if job["method"] in SUBMIT_METHODS and job["state"] != capture.COMPLETED:
            view = self._what_committed(job, job["request_id"], job["device_id"])
            if view is not None:
                return view
        return self._view_of(job)

    @staticmethod
    def _committed(repo: Repository, job: Mapping[str, Any] | None, submission_id: str) -> tuple[Any, Any]:
        """``(receipt, attempt)`` of this submission; for a job, under the key its handler answers
        with (B4's successor), and only for its item, since a key reused for another is refused."""

        key, item = submission_id, None
        if job is not None:
            from learnloop_sidecar.handlers.practice import answering_key

            params = job["params"]
            session_id = params.get("sessionId") or params.get("session_id")
            item = params.get("practiceItemId") or params.get("practice_item_id")
            if session_id and item:
                key = answering_key(repo, submission_id, str(session_id), str(item))[0] or submission_id
        receipt = repo.attempt_submission_receipt(key)
        if receipt is not None and item in (None, receipt["practice_item_id"]):
            return receipt, None
        attempt = repo.practice_attempt_by_submission_id(key)
        return None, attempt if attempt is not None and item in (None, attempt["practice_item_id"]) else None

    def _what_committed(self, job: Mapping[str, Any] | None, submission_id: str, device_id: str | None) -> JobView | None:
        """The view from the attempts' side; None if nothing committed under this submission."""

        job_id = job["id"] if job is not None else None
        receipt, attempt = self._committed(self._read_repo, job, submission_id)
        if receipt is not None:
            return JobView(id=job_id, request_id=submission_id, state=capture.COMPLETED, result=receipt["result"])
        if attempt is None:
            return None
        self._redrive(job, submission_id, attempt, device_id)
        with self._waiters_lock:
            failures = self._redrive_failures.get(submission_id, 0)
        delayed = failures is None or failures >= _REDRIVES_BEFORE_DELAYED
        if delayed or (job is not None and job["state"] == capture.RECORDED):
            return JobView(id=job_id, request_id=submission_id, state=capture.RECORDED,
                           error=capture.recorded_error(attempt))
        return JobView(id=job_id, request_id=submission_id, state=capture.RUNNING)

    # -- re-driving a committed attempt's completion (R2) -----------------------

    def _redrive(self, job: Mapping[str, Any] | None, submission_id: str, attempt: Mapping[str, Any],
                 device_id: str | None) -> None:
        """Queue one recovery under the same key, from a status poll: the read itself stays a
        read. Never beside the job that is completing it or another recovery, so at most one
        per poll and nothing at all with nobody polling."""

        session_id = attempt.get("session_id")
        with self._waiters_lock:
            if not session_id:
                # Recovery names a session, and this attempt has none to name.
                self._redrive_failures[submission_id] = None
                return
            if submission_id in self._redriving or (job is not None and job["id"] in self._waiters):
                return
            self._redriving.add(submission_id)
        params = {"sessionId": str(session_id), "practiceItemId": str(attempt["practice_item_id"]),
                  "submissionId": submission_id}
        origin = self._origin(device_id) if device_id else None
        try:
            self.ensure_started()
            self.job_worker.submit(lambda worker: self._run_redrive(worker, job, submission_id, params, origin))
        except HostBusy:
            # Full or stopping: the next poll, or the next start.
            with self._waiters_lock:
                self._redriving.discard(submission_id)

    def _run_redrive(self, worker: _Worker, job: Mapping[str, Any] | None, submission_id: str,
                     params: Mapping[str, Any], origin: Any) -> None:
        try:
            response = self._dispatch(worker, "recover_practice_submission", params, origin)
        except Exception:
            LOG.exception("recovery of submission %s stopped", submission_id)
            response = {"error": {"message": "This request stopped unexpectedly.", "data": {"code": "internal"}}}
        error = flat_error(response)
        recovered = error is None and response["result"].get("status") == "recovered"
        with self._waiters_lock:
            if recovered:
                self._redrive_failures.pop(submission_id, None)
            elif (error or {}).get("code") == capture.SUBMISSION_COMMITTED:
                self._redrive_failures[submission_id] = None
            elif self._redrive_failures.get(submission_id, 0) is not None:
                self._redrive_failures[submission_id] = self._redrive_failures.get(submission_id, 0) + 1
            failures = self._redrive_failures.get(submission_id, 0)
            self._redriving.discard(submission_id)
        if job is None:
            return
        if recovered:
            view = JobView(id=job["id"], request_id=submission_id, state=capture.COMPLETED,
                           result=response["result"].get("result"))
        elif failures is None or failures >= _REDRIVES_BEFORE_DELAYED:
            view = JobView(id=job["id"], request_id=submission_id, state=capture.FAILED, error={"code": capture.SUBMISSION_COMMITTED})
        else:
            return
        self._finish(view, job)

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
    body: dict[str, Any] = {"state": view.state} if view.id is None else {"job_id": view.id, "state": view.state}
    if view.state == capture.COMPLETED:
        body["result"] = view.result
    elif view.state == capture.FAILED:
        body["error"] = view.error
    elif view.state == capture.RECORDED:
        body["error"] = view.error
        body["attempt_id"] = (view.error or {}).get("details", {}).get("attempt_id")
    return body
