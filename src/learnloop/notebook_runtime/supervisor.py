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
from pathlib import Path
from typing import Any, Protocol

from learnloop.notebook_runtime import adapter, settings
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
                "start_seconds": [round(value, 3) for value in self.start_seconds[-5:]]}


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
        self._stopping = False
        self.ready_event = asyncio.Event()

    async def start(self) -> None:
        """Start the server and wait until it answers on its socket (``ready``) or say why not (``failed``)."""

        session = self.session
        self._stopping = False
        session.state = STARTING
        session.stop_reason = None
        session.last_error = None
        if await self._launch():
            self._watch = asyncio.create_task(self._supervise())

    async def _launch(self) -> bool:
        session = self.session
        session.generation += 1
        session.unit = f"learnloop-notebook-{secrets.token_hex(6)}"
        began = time.monotonic()
        try:
            session.process = await self.backend.spawn(session)
        except Exception as exc:  # noqa: BLE001 - every failure is said in the session's state
            session.state = FAILED
            session.last_error = f"the notebook server could not start ({type(exc).__name__}: {exc})"
            return False
        if not await self._wait_ready():
            if self._stopping:
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

        return httpx.AsyncClient(transport=httpx.AsyncHTTPTransport(uds=str(session.layout.socket)),
                                 base_url="http://127.0.0.1", timeout=timeout,
                                 headers={"Authorization": f"Bearer {session.token}"})

    async def spawn(self, session: Session) -> Process:
        layout = session.layout
        layout.run_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(layout.run_dir, 0o700)
        if layout.socket.exists():
            layout.socket.unlink()
        layout.token_file.write_text(session.token, encoding="utf-8")
        os.chmod(layout.token_file, 0o600)
        argv, env = launch_command(layout, session.limits, base_url=session.base_url, unit=session.unit,
                                   scoped=self.scoped, python=self.python)
        process = await asyncio.create_subprocess_exec(*argv, env=env, stdin=subprocess.DEVNULL,
                                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                                       start_new_session=True)
        asyncio.get_running_loop().create_task(_drain(process, session))
        return process

    async def ready(self, session: Session) -> bool:
        if not session.layout.socket.exists():
            return False
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

        try:
            session.layout.socket.unlink()
        except FileNotFoundError:
            pass
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


def run_dir_bytes(run_dir: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(run_dir):
        for name in files:
            try:
                total += os.lstat(os.path.join(root, name)).st_size
            except OSError:
                pass
    return total
