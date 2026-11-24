"""One notebook session and the supervisor that keeps its marimo server running.

A session is process state, never persisted meaning: its server, the frame proxy's record of UI values and the
cell names marimo reported. States::

    starting -> ready -> stopping -> stopped
        |         |
        v         v
     failed   restarting -> ready (or failed after the restart limit)

A server that exits while the session is ``ready`` was not asked to: the supervisor starts it again with backoff
(``restarting``), up to :data:`~learnloop.notebook_runtime.settings.RESTART_LIMIT` times, then the session is
``failed`` with the reason. A stop (the learner closed it, idle, a vault switch, the context closing) is graceful
first (marimo's own shutdown over the socket) and forced after a timeout (the process group, which takes the
sandbox and, by ``--die-with-parent``, everything inside it).

The process work is behind :class:`Backend`, so the state machine is tested with fakes and the real backend
(:class:`SandboxBackend`) is tested against a real sandbox.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import secrets
import signal
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from learnloop.notebook_runtime import adapter, hostfiles, settings
from learnloop.notebook_runtime.sandbox import Layout, Limits, launch_command

LOG = logging.getLogger(__name__)

STARTING = "starting"
READY = "ready"
RESTARTING = "restarting"
STOPPING = "stopping"
STOPPED = "stopped"
FAILED = "failed"
#: States in which a server runs or is about to (they count against the session limit).
LIVE_STATES = frozenset({STARTING, READY, RESTARTING})

#: How much of a server's output is kept, in memory only (it prints its access token; nothing writes it to disk).
OUTPUT_TAIL_BYTES = 16 * 1024


class Process(Protocol):
    pid: int
    returncode: int | None

    async def wait(self) -> int: ...


class Backend(Protocol):
    async def spawn(self, session: Session) -> Process: ...

    async def ready(self, session: Session) -> bool: ...

    async def server_token(self, session: Session) -> str | None: ...

    async def shutdown(self, session: Session) -> None: ...

    def signal_group(self, session: Session, signum: int) -> None: ...

    async def after_stop(self, session: Session) -> None: ...

    async def api(self, session: Session, rel: str, body: dict[str, Any]) -> tuple[int, str]: ...


@dataclass
class Session:
    session_id: str
    owner: str
    vault_key: str
    revision: str
    layout: Layout
    limits: Limits
    view: str = "app"
    epoch: int = 0
    secret: str = field(default_factory=lambda: secrets.token_urlsafe(18))
    token: str = field(default_factory=lambda: secrets.token_urlsafe(24))
    state: str = STOPPED
    stop_reason: str | None = None
    last_error: str | None = None
    restarts: int = 0
    unit: str = ""
    process: Process | None = None
    server_tok: str = ""
    #: Starts of this session's server (monotonic seconds to ready), for status.
    start_seconds: list[float] = field(default_factory=list)
    # What the frame proxy learns in passing.
    marimo_session_id: str | None = None
    cell_ids: dict[str, str] = field(default_factory=dict)
    cell_codes: dict[str, str] = field(default_factory=dict)
    ui_values: dict[str, Any] = field(default_factory=dict)
    #: The JSON size of each kept value, and their sum (bounded by ``settings.UI_VALUES_MAX_BYTES``).
    ui_sizes: dict[str, int] = field(default_factory=dict, repr=False)
    ui_bytes: int = 0
    #: Per cell name, what its last run said: ``{"status", "ms", "error"}`` (read from marimo's cell messages).
    cell_runs: dict[str, dict[str, Any]] = field(default_factory=dict)
    _run_started: dict[str, float] = field(default_factory=dict, repr=False)
    #: A lesson notebook's commit points and held cells (``lessons.lesson_contract``); None for any other notebook.
    contract: dict[str, Any] | None = None
    #: A pad's cells, ``[(name, code)]``, as the snapshot holds them (None for any other notebook).
    snapshot_cells: list[tuple[str, str]] | None = None
    #: A closed lesson's notebook: shown as it is, nothing committed, nothing released.
    review: bool = False
    #: The commit points the learner answered, and the held cells released in this server process.
    commits: set[str] = field(default_factory=set)
    released: set[str] = field(default_factory=set)
    frames: int = 0
    last_activity: float = field(default_factory=time.monotonic)
    output_tail: bytearray = field(default_factory=bytearray, repr=False)
    generation: int = 0

    @property
    def base_url(self) -> str:
        return f"/s/{self.secret}"

    def touch(self) -> None:
        self.last_activity = time.monotonic()

    def view_dict(self) -> dict[str, Any]:
        return {"session_id": self.session_id, "owner": self.owner, "state": self.state,
                "stop_reason": self.stop_reason, "error": self.last_error, "restarts": self.restarts,
                "frames_attached": self.frames, "cells": sorted(self.cell_ids),
                "cell_runs": {name: dict(run) for name, run in sorted(self.cell_runs.items())},
                "start_seconds": [round(value, 3) for value in self.start_seconds[-5:]],
                **({"lesson": self.lesson_view()} if self.contract is not None else {})}

    def lesson_view(self) -> dict[str, Any]:
        assert self.contract is not None
        return {"review": self.review, "released": sorted(self.released),
                "commit_points": [{"name": point["name"], "held": list(point["held"]),
                                   "committed": point["name"] in self.commits} for point in self.contract["points"]]}

    def releasable(self) -> set[str]:
        """The held cells the learner's commits have unlocked (none in a review)."""

        if self.contract is None or self.review:
            return set()
        return {name for point in self.contract["points"] if point["name"] in self.commits for name in point["held"]}


def note_cell_progress(session: Session, cell_id: str, status: str | None, stamp: float | None, error: bool) -> None:
    """A cell's run as marimo reports it: running starts its clock, idle stops it (``ms``), an error output marks it."""

    names = {value: key for key, value in session.cell_ids.items()}
    name = names.get(cell_id)
    if name is None:
        return
    run = session.cell_runs.setdefault(name, {"status": None, "ms": None, "error": False})
    if status is not None:
        run["status"] = status
        if status == "running" and stamp is not None:
            session._run_started[name] = stamp
            run["error"] = False
        elif status == "idle" and stamp is not None and name in session._run_started:
            run["ms"] = round(max(0.0, stamp - session._run_started.pop(name)) * 1000, 1)
    if error:
        run["error"] = True


def record_ui_values(session: Session, values: dict[str, Any]) -> None:
    """Keep the controls' values the server accepted, for replay after a restart: only controls of the notebook's
    own cells (marimo names one ``<cell id>-<n>``), and never more than ``UI_VALUES_MAX_BYTES`` in all (a value that
    would pass it is not kept; the page keeps its own)."""

    import json

    known = set(session.cell_ids.values())
    for object_id, value in values.items():
        cell, _, index = object_id.rpartition("-")
        if cell not in known or not index.isdigit():
            continue
        try:
            size = len(json.dumps(value))
        except (TypeError, ValueError):
            continue
        total = session.ui_bytes - session.ui_sizes.get(object_id, 0) + size
        if total > settings.UI_VALUES_MAX_BYTES:
            continue
        session.ui_values[object_id] = value
        session.ui_sizes[object_id] = size
        session.ui_bytes = total


def note_commits(session: Session, values: dict[str, Any]) -> None:
    """Controls set by the frame (object id to value): a non-empty value on a commit point's own control commits it.
    marimo names a control ``<cell id>-<n>``. A review commits nothing."""

    from learnloop.notebook_runtime.lessons import committed_value

    if session.contract is None or session.review:
        return
    points = {point["name"] for point in session.contract["points"]}
    names = {value: key for key, value in session.cell_ids.items()}
    for object_id, value in values.items():
        name = names.get(object_id.rsplit("-", 1)[0])
        if name in points and committed_value(value):
            session.commits.add(name)


def notebook_revision(source: bytes) -> str:
    return hashlib.sha256(source).hexdigest()


class Supervisor:
    """Starts, watches and stops one session's server."""

    def __init__(self, session: Session, backend: Backend, *,
                 restart_limit: int = settings.RESTART_LIMIT,
                 backoff_seconds: float = settings.RESTART_BACKOFF_SECONDS,
                 ready_timeout: float = settings.READY_TIMEOUT_SECONDS,
                 stop_timeout: float = settings.STOP_TIMEOUT_SECONDS) -> None:
        self.session = session
        self.backend = backend
        self.restart_limit = restart_limit
        self.backoff_seconds = backoff_seconds
        self.ready_timeout = ready_timeout
        self.stop_timeout = stop_timeout
        self._watch: asyncio.Task | None = None
        #: The start in flight (a spawn or a readiness wait); a stop waits for it, so no server outlives a stop.
        self._start_task: asyncio.Task | None = None
        self._stopping = False
        self.ready_event = asyncio.Event()

    async def start(self) -> None:
        """Start the server and wait until it answers on its socket (``ready``) or say why not (``failed``)."""

        session = self.session
        self._stopping = False
        self._start_task = asyncio.current_task()
        session.state = STARTING
        session.stop_reason = None
        session.last_error = None
        try:
            if await self._launch():
                self._watch = asyncio.create_task(self._supervise())
        finally:
            self._start_task = None

    async def _launch(self) -> bool:
        session = self.session
        session.generation += 1
        # A new server process loads the notebook as shipped: every held cell is held again.
        session.released.clear()
        session.unit = f"learnloop-notebook-{secrets.token_hex(6)}"
        began = time.monotonic()
        try:
            session.process = await self.backend.spawn(session)
        except Exception as exc:  # noqa: BLE001 - every failure is said in the session's state
            session.state = FAILED
            session.last_error = f"the notebook server could not start ({type(exc).__name__}: {exc})"
            return False
        if self._stopping:
            # A stop landed while the server was being spawned: it never serves.
            await self._kill()
            return False
        if not await self._wait_ready():
            if self._stopping:
                await self._kill()
                return False
            session.state = FAILED
            session.last_error = "the notebook server did not answer on its socket"
            await self._kill()
            return False
        session.server_tok = await self.backend.server_token(session) or ""
        session.start_seconds.append(time.monotonic() - began)
        session.state = READY
        session.touch()
        self.ready_event.set()
        return True

    async def _wait_ready(self) -> bool:
        session = self.session
        deadline = time.monotonic() + self.ready_timeout
        while time.monotonic() < deadline and not self._stopping:
            process = session.process
            if process is None or process.returncode is not None:
                return False
            try:
                if await self.backend.ready(session):
                    return True
            except Exception:  # noqa: BLE001 - not up yet
                pass
            await asyncio.sleep(0.05)
        return False

    async def _supervise(self) -> None:
        session = self.session
        while True:
            process = session.process
            if process is None:
                return
            returncode = await process.wait()
            if self._stopping:
                return
            LOG.info("notebook server of %s exited (%s); restarting", session.session_id, returncode)
            self.ready_event.clear()
            await self.backend.after_stop(session)
            if session.restarts >= self.restart_limit:
                session.state = FAILED
                session.last_error = (f"the notebook server stopped {session.restarts + 1} times; "
                                      "it was not started again")
                return
            session.restarts += 1
            session.state = RESTARTING
            await asyncio.sleep(self.backoff_seconds * session.restarts)
            if self._stopping:
                return
            if not await self._launch():
                return

    async def stop(self, reason: str, *, graceful: bool = True) -> None:
        """Stop the server (graceful first, forced after the timeout); the session ends ``stopped``."""

        session = self.session
        if session.state in (STOPPED,) and session.process is None:
            session.stop_reason = session.stop_reason or reason
            return
        self._stopping = True
        session.state = STOPPING
        starting = self._start_task
        if starting is not None and starting is not asyncio.current_task() and not starting.done():
            # Let the start see the stop (it kills a server it spawned meanwhile), then stop what is left.
            await asyncio.wait({starting}, timeout=self.stop_timeout * 3)
        process = session.process
        if process is not None and process.returncode is None:
            if graceful:
                try:
                    await asyncio.wait_for(self.backend.shutdown(session), self.stop_timeout)
                except Exception:  # noqa: BLE001 - forced below
                    pass
                try:
                    await asyncio.wait_for(process.wait(), self.stop_timeout)
                except asyncio.TimeoutError:
                    pass
            await self._kill()
        if self._watch is not None and self._watch is not asyncio.current_task():
            self._watch.cancel()
            try:
                await self._watch
            except (asyncio.CancelledError, Exception):  # noqa: BLE001 - the watch ends here
                pass
        await self.backend.after_stop(session)
        session.process = None
        session.state = STOPPED
        session.stop_reason = reason
        session.frames = 0
        self.ready_event.clear()

    async def _kill(self) -> None:
        process = self.session.process
        if process is None or process.returncode is not None:
            return
        for signum in (signal.SIGTERM, signal.SIGKILL):
            try:
                self.backend.signal_group(self.session, signum)
            except ProcessLookupError:
                return
            try:
                await asyncio.wait_for(process.wait(), self.stop_timeout)
                return
            except asyncio.TimeoutError:
                continue


class SandboxBackend:
    """The real backend: a sandboxed ``marimo edit`` on a Unix socket, reached with httpx over the socket."""

    def __init__(self, *, scoped: bool, python: str | None = None) -> None:
        self.scoped = scoped
        #: The interpreter the server runs on (default: this process's); a harness whose own interpreter is a
        #: throwaway environment names the project's.
        self.python = python

    def _client(self, session: Session, timeout: float = 5.0) -> Any:
        import httpx

        # Only ever the socket trusted code made (a link or anything else in its place is refused).
        hostfiles.check_socket(session.layout.socket)
        return httpx.AsyncClient(transport=httpx.AsyncHTTPTransport(uds=str(session.layout.socket)),
                                 base_url="http://127.0.0.1", timeout=timeout,
                                 headers={"Authorization": f"Bearer {session.token}"})

    async def spawn(self, session: Session) -> Process:
        """Start the server: the token written afresh and the socket created and listening, both by this trusted
        side in the session's private run directory (the sandbox never sees it); the server inherits the socket as
        a descriptor and reads the token through a read-only mount."""

        layout = session.layout
        hostfiles.private_dir(layout.run_dir)
        hostfiles.write_private(layout.run_dir, layout.token_file.name, session.token.encode("utf-8"))
        listener = hostfiles.listening_socket(layout.run_dir, layout.socket.name)
        try:
            argv, env = launch_command(layout, session.limits, base_url=session.base_url, unit=session.unit,
                                       scoped=self.scoped, socket_fd=listener.fileno(), python=self.python)
            process = await asyncio.create_subprocess_exec(*argv, env=env, stdin=subprocess.DEVNULL,
                                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                                           start_new_session=True, pass_fds=(listener.fileno(),))
        finally:
            # The server holds its own copy; this side only ever connects by the path.
            listener.close()
        asyncio.get_running_loop().create_task(_drain(process, session))
        return process

    async def ready(self, session: Session) -> bool:
        async with self._client(session, timeout=2.0) as client:
            response = await client.get(f"{session.base_url}/{adapter.HEALTH}")
            return response.status_code == 200

    async def server_token(self, session: Session) -> str | None:
        async with self._client(session) as client:
            response = await client.get(f"{session.base_url}/{adapter.INDEX}")
            return adapter.server_token(response.text)

    async def shutdown(self, session: Session) -> None:
        async with self._client(session) as client:
            await client.post(f"{session.base_url}/{adapter.SHUTDOWN}", json={},
                              headers={adapter.SERVER_TOKEN_HEADER: session.server_tok})

    async def api(self, session: Session, rel: str, body: dict[str, Any]) -> tuple[int, str]:
        headers = {adapter.SERVER_TOKEN_HEADER: session.server_tok}
        if session.marimo_session_id:
            headers[adapter.SESSION_HEADER] = session.marimo_session_id
        async with self._client(session, timeout=30.0) as client:
            response = await client.post(f"{session.base_url}/{rel}", json=body, headers=headers)
            return response.status_code, response.text

    def signal_group(self, session: Session, signum: int) -> None:
        if session.process is not None:
            os.killpg(session.process.pid, signum)

    async def after_stop(self, session: Session) -> None:
        """A stale socket goes; a scope systemd keeps listed as failed (a server killed by a signal) is reset by
        its own name, so nothing of a stopped session stays registered."""

        hostfiles.remove_private(session.layout.run_dir, session.layout.socket.name)
        if self.scoped and session.unit:
            process = await asyncio.create_subprocess_exec(
                "systemctl", "--user", "reset-failed", f"{session.unit}.scope", stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            await process.wait()


async def _drain(process: Any, session: Session) -> None:
    """Keep the tail of the server's output in memory; the pipe never blocks the server."""

    stream = process.stdout
    if stream is None:
        return
    while True:
        chunk = await stream.read(65536)
        if not chunk:
            return
        tail = session.output_tail
        tail += chunk
        if len(tail) > OUTPUT_TAIL_BYTES:
            del tail[:len(tail) - OUTPUT_TAIL_BYTES]
