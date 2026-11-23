"""The notebook runtime a sidecar context owns: every open session, on one event loop thread of its own.

The sidecar answers one request at a time on its own thread; the runtime's servers, proxies and supervisors live on
a daemon thread running an asyncio loop, and the request thread calls into it with a bounded wait. Nothing here
waits for a server to become ready on the request thread: ``open`` answers at once with the session ``starting``
and its frame URL, and ``status`` reads the state.

Sessions belong to one vault and one epoch. Every call names the vault open now, so another vault's session is not
found; a vault switch or the context closing ends the epoch and stops every session started before it, so nothing
crosses vaults. One session per owner (``pad:<id>`` or ``lesson:<id>``): opening the same owner on the same
notebook revision returns its session (restarting it, with its UI values, after an idle stop); a new revision
replaces it.
"""
from __future__ import annotations

import asyncio
import logging
import signal
import secrets
import threading
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from learnloop.notebook_runtime import adapter, hostfiles, settings
from learnloop.notebook_runtime.proxy import FrameProxy
from learnloop.notebook_runtime.sandbox import (
    Layout,
    Limits,
    SOCKET_PATH_MAX_BYTES,
    RuntimeUnavailable,
    missing_requirements,
    runtime_base_dir,
    scope_available,
    write_shared_files,
)
from learnloop.notebook_runtime.supervisor import (
    LIVE_STATES,
    READY,
    STARTING,
    STOPPED,
    SandboxBackend,
    Session,
    Supervisor,
    notebook_revision,
)

LOG = logging.getLogger(__name__)
T = TypeVar("T")

#: The bound on a call from the request thread into the runtime's loop (stops are graceful-then-forced, each
#: bounded by the supervisor's own timeout).
CALL_SECONDS = 30.0
#: The bound on stopping everything when the context closes or switches vaults.
CLOSE_SECONDS = 15.0


class SessionNotFound(LookupError):
    """No such session in the vault open now."""


class SessionsFull(RuntimeError):
    """As many sessions run as allowed and every one has a frame attached."""


class NotConnected(RuntimeError):
    """No frame has connected to the session yet, so marimo has no session to address."""


class CellUnknown(KeyError):
    """A cell name the session's notebook does not have."""


class KernelRefused(RuntimeError):
    """marimo answered a sidecar request with an error."""


class ReleaseRefused(PermissionError):
    """A lesson notebook's held cells are released only by the learner's commit, and never in a review."""


@dataclass
class _Entry:
    session: Session
    supervisor: Supervisor
    proxy: FrameProxy
    idle_minutes: int


class NotebookRuntime:
    def __init__(self, *, backend: Any = None, base_dir: Path | None = None,
                 requirements: Callable[[], list[str]] = missing_requirements,
                 sweep_seconds: float = settings.SWEEP_SECONDS,
                 supervisor_options: dict[str, Any] | None = None) -> None:
        self._backend = backend
        self._base_dir = base_dir
        self._requirements = requirements
        self._sweep_seconds = sweep_seconds
        self._supervisor_options = dict(supervisor_options or {})
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._entries: dict[str, _Entry] = {}
        self._epoch = 0
        self._shared: tuple[Path, Path] | None = None
        self._sweep: Any = None

    # -- the loop ----------------------------------------------------------------------------------------------

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        with self._lock:
            if self._loop is not None and self._thread is not None and self._thread.is_alive():
                return self._loop
            loop = asyncio.new_event_loop()
            ready = threading.Event()

            def run() -> None:
                asyncio.set_event_loop(loop)
                loop.call_soon(ready.set)
                loop.run_forever()

            thread = threading.Thread(target=run, name="notebook-runtime", daemon=True)
            thread.start()
            ready.wait(5)
            self._loop, self._thread = loop, thread
            self._sweep = asyncio.run_coroutine_threadsafe(self._sweep_forever(), loop)
            return loop

    def _call(self, make: Callable[[], Awaitable[T]], timeout: float = CALL_SECONDS) -> T:
        loop = self._ensure_loop()

        async def run() -> T:
            return await make()

        return asyncio.run_coroutine_threadsafe(run(), loop).result(timeout)

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # -- the request thread's calls -----------------------------------------------------------------------------

    def open(self, *, vault_key: str, owner: str, source: bytes, view: str, limits: Limits, idle_minutes: int,
             max_sessions: int, revision: str | None = None, contract: dict[str, Any] | None = None,
             review: bool = False) -> dict[str, Any]:
        """``revision`` names the notebook's identity when its bytes are not it: a pad's cells are one notebook
        while the same cells stand in the same order, whatever their code (an edit reaches the running kernel
        through ``run_cells``), so moving or reopening the pad keeps its kernel. ``contract`` is a lesson
        notebook's commit points and held cells, and ``review`` says the lesson is closed (nothing is released)."""

        problems = self._requirements()
        if problems:
            raise RuntimeUnavailable("; ".join(problems))
        return self._call(lambda: self._open(vault_key, owner, source, view, limits, idle_minutes, max_sessions,
                                             revision, contract, review))

    def status(self, *, vault_key: str, session_id: str) -> dict[str, Any]:
        return self._call(lambda: self._status(vault_key, session_id))

    def close_session(self, *, vault_key: str, session_id: str) -> dict[str, Any]:
        return self._call(lambda: self._close_session(vault_key, session_id))

    def mark_review(self, *, vault_key: str, session_id: str) -> dict[str, Any]:
        """The session's lesson closed: a review from now on (nothing committed or released); its view."""

        return self._call(lambda: self._mark_review(vault_key, session_id))

    def release(self, *, vault_key: str, session_id: str, names: list[str]) -> dict[str, Any]:
        return self._call(lambda: self._release(vault_key, session_id, names))

    def run_cells(self, *, vault_key: str, session_id: str, cells: list[tuple[str, str]]) -> dict[str, Any]:
        return self._call(lambda: self._run_cells(vault_key, session_id, cells))

    def switch_vault(self, vault_key: str | None) -> None:
        """A vault switch (or a refusal of the vault open now, with None): every session of another vault stops."""

        if not self.running:
            self._epoch += 1
            return
        others = [entry for entry in list(self._entries.values()) if entry.session.vault_key != vault_key]
        try:
            self._call(lambda: self._stop_where(lambda entry: entry.session.vault_key != vault_key, "vault_switch"),
                       timeout=CLOSE_SECONDS)
        finally:
            self._kill_left(others)

    def close(self) -> None:
        """Stop every session and the loop thread (the context closing). Bounded; idempotent."""

        if not self.running:
            return
        loop, thread = self._loop, self._thread
        every = list(self._entries.values())
        try:
            self._call(lambda: self._stop_where(lambda entry: True, "closed", forget=True), timeout=CLOSE_SECONDS)
        except Exception:  # noqa: BLE001 - the loop stops below either way
            LOG.warning("notebook sessions did not all stop within %.0f s", CLOSE_SECONDS, exc_info=True)
        # One deadline for the graceful part; then every server still alive is killed, before any task is cancelled.
        self._kill_left(every)
        assert loop is not None and thread is not None
        try:
            self._call(_cancel_other_tasks, timeout=5)
        except Exception:  # noqa: BLE001 - the loop stops below either way
            pass
        loop.call_soon_threadsafe(loop.stop)
        thread.join(5)
        if not thread.is_alive():
            loop.close()
        with self._lock:
            self._loop, self._thread, self._sweep = None, None, None

    def _kill_left(self, entries: list[_Entry]) -> None:
        """SIGKILL the process group of every given session's server still running (from the calling thread: it
        cannot be cancelled with the loop's tasks)."""

        for entry in entries:
            process = entry.session.process
            if process is None or process.returncode is not None:
                continue
            try:
                entry.supervisor.backend.signal_group(entry.session, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass

    # -- on the loop --------------------------------------------------------------------------------------------

    def _backend_now(self) -> Any:
        if self._backend is None:
            self._backend = SandboxBackend(scoped=scope_available())
        return self._backend

    def _base(self) -> Path:
        if self._base_dir is None:
            self._base_dir = runtime_base_dir()
        if self._shared is None:
            self._shared = write_shared_files(self._base_dir)
        return self._base_dir

    def _entry(self, vault_key: str, session_id: str) -> _Entry:
        entry = self._entries.get(session_id)
        if entry is None or entry.session.vault_key != vault_key:
            raise SessionNotFound(session_id)
        return entry

    def _view(self, entry: _Entry) -> dict[str, Any]:
        session = entry.session
        view = session.view_dict()
        params = adapter.APP_VIEW_PARAMS if session.view == "app" else (("show-chrome", "false"),)
        query = "&".join(f"{name}={value}" for name, value in params)
        view["frame_url"] = f"http://{settings.FRAME_HOST}:{entry.proxy.port}{session.base_url}/?{query}"
        view["memory_bytes"] = _memory_bytes(session)
        return view

    async def _open(self, vault_key: str, owner: str, source: bytes, view: str, limits: Limits, idle_minutes: int,
                    max_sessions: int, revision: str | None = None, contract: dict[str, Any] | None = None,
                    review: bool = False) -> dict[str, Any]:
        revision = revision or notebook_revision(source)
        for entry in list(self._entries.values()):
            if entry.session.vault_key != vault_key or entry.session.owner != owner:
                continue
            if entry.session.revision == revision and entry.session.view == view:
                entry.idle_minutes = idle_minutes
                # A lesson closed while its notebook ran is a review from now on (a lesson never reopens).
                entry.session.review = entry.session.review or review
                if entry.session.state not in LIVE_STATES:
                    await self._make_room(max_sessions, keep=entry)
                    entry.session.limits = limits
                    # The same notebook may have new code since it stopped (a pad's cells edited meanwhile).
                    hostfiles.write_private(entry.session.layout.notebook.parent, entry.session.layout.notebook.name,
                                            source)
                    asyncio.get_running_loop().create_task(entry.supervisor.start())
                    entry.session.state = STARTING
                entry.session.touch()
                return self._view(entry)
            await self._forget(entry, "replaced")
        await self._make_room(max_sessions)
        base = self._base()
        assert self._shared is not None
        session_id = f"nbs_{secrets.token_hex(8)}"
        notebook = hostfiles.write_private(base / "nb", f"{session_id}.py", source)
        layout = Layout(run_dir=base / "run" / session_id[4:], notebook=notebook, config_dir=self._shared[0],
                        hosts_file=self._shared[1])
        if len(str(layout.socket).encode()) > SOCKET_PATH_MAX_BYTES:
            hostfiles.remove_private(notebook.parent, notebook.name)
            raise RuntimeUnavailable(f"the runtime directory {base} is too deep for a Unix socket's path")
        session = Session(session_id=session_id, owner=owner, vault_key=vault_key, revision=revision,
                          layout=layout, limits=limits, view=view, epoch=self._epoch, contract=contract, review=review)
        supervisor = Supervisor(session, self._backend_now(), **self._supervisor_options)
        proxy = FrameProxy(session)
        await proxy.start()
        entry = _Entry(session, supervisor, proxy, idle_minutes)
        self._entries[session_id] = entry
        session.state = STARTING
        asyncio.get_running_loop().create_task(supervisor.start())
        return self._view(entry)

    async def _make_room(self, max_sessions: int, keep: _Entry | None = None) -> None:
        live = [entry for entry in self._entries.values()
                if entry.session.state in LIVE_STATES and entry is not keep]
        if len(live) < max_sessions:
            return
        idle = sorted((entry for entry in live if entry.session.frames == 0),
                      key=lambda entry: entry.session.last_activity)
        if len(live) - len(idle) >= max_sessions:
            raise SessionsFull(f"{len(live)} notebook sessions are open, each with a window showing it")
        for entry in idle[:len(live) - max_sessions + 1]:
            await entry.supervisor.stop("make_room")

    async def _status(self, vault_key: str, session_id: str) -> dict[str, Any]:
        return self._view(self._entry(vault_key, session_id))

    async def _close_session(self, vault_key: str, session_id: str) -> dict[str, Any]:
        entry = self._entry(vault_key, session_id)
        view = self._view(entry)
        await self._forget(entry, "closed")
        view.update(state=STOPPED, stop_reason="closed", frames_attached=0)
        return view

    async def _forget(self, entry: _Entry, reason: str) -> None:
        await entry.supervisor.stop(reason)
        await entry.proxy.stop()
        self._entries.pop(entry.session.session_id, None)
        layout = entry.session.layout
        try:
            hostfiles.remove_private(layout.notebook.parent, layout.notebook.name)
            hostfiles.remove_private(layout.run_dir, layout.token_file.name)
            hostfiles.remove_private(layout.run_dir, layout.socket.name)
            hostfiles.remove_private_dir(layout.run_dir)
        except hostfiles.UnsafePath:
            LOG.warning("a notebook session's host files were not as made; left in place")

    async def _stop_where(self, select: Callable[[_Entry], bool], reason: str, *, forget: bool = False) -> None:
        self._epoch += 1
        chosen = [entry for entry in list(self._entries.values()) if select(entry)]
        # A session of another vault is forgotten, never kept: its frame URL must not answer in this vault.
        await asyncio.gather(*(self._forget(entry, reason) if forget or reason == "vault_switch"
                               else entry.supervisor.stop(reason) for entry in chosen),
                             return_exceptions=True)

    def _connected(self, entry: _Entry) -> None:
        if entry.session.state != READY:
            raise NotConnected(f"the notebook session is {entry.session.state}")
        if not entry.session.marimo_session_id or entry.session.frames == 0:
            # marimo routes these requests to the window's own connection; with none attached it refuses them.
            raise NotConnected("no window shows the notebook")

    def _cell_ids(self, entry: _Entry, names: list[str]) -> list[str]:
        unknown = [name for name in names if name not in entry.session.cell_ids]
        if unknown:
            raise CellUnknown(", ".join(unknown))
        return [entry.session.cell_ids[name] for name in names]

    async def _mark_review(self, vault_key: str, session_id: str) -> dict[str, Any]:
        entry = self._entry(vault_key, session_id)
        entry.session.review = True
        return self._view(entry)

    async def _release(self, vault_key: str, session_id: str, names: list[str]) -> dict[str, Any]:
        entry = self._entry(vault_key, session_id)
        session = entry.session
        if session.contract is not None:
            if session.review:
                raise ReleaseRefused("a review shows the notebook as it is and releases nothing")
            locked = [name for name in names if name not in session.releasable()]
            if locked:
                raise ReleaseRefused(f"not released by a commit yet: {', '.join(locked)}")
        self._connected(entry)
        ids = self._cell_ids(entry, names)
        status, text = await self._backend_now().api(entry.session, adapter.SET_CELL_CONFIG,
                                                     adapter.cell_config_body(ids, disabled=False))
        if status != 200:
            raise KernelRefused(f"marimo refused the release ({status})")
        # marimo runs an enabled cell only when it went stale while held; a held cell whose inputs never changed
        # would stay blank. Running the released cells shows them either way.
        codes = [entry.session.cell_codes.get(cell_id) for cell_id in ids]
        if all(code is not None for code in codes):
            status, text = await self._backend_now().api(entry.session, adapter.RUN, adapter.run_body(ids, codes))
            if status != 200:
                raise KernelRefused(f"marimo refused to run the released cells ({status})")
        entry.session.released.update(names)
        entry.session.touch()
        return {"session_id": session_id, "released": list(names)}

    async def _run_cells(self, vault_key: str, session_id: str, cells: list[tuple[str, str]]) -> dict[str, Any]:
        entry = self._entry(vault_key, session_id)
        self._connected(entry)
        ids = self._cell_ids(entry, [name for name, _code in cells])
        status, text = await self._backend_now().api(entry.session, adapter.RUN,
                                                     adapter.run_body(ids, [code for _name, code in cells]))
        if status != 200:
            raise KernelRefused(f"marimo refused the run ({status})")
        for cell_id, (_name, code) in zip(ids, cells, strict=True):
            entry.session.cell_codes[cell_id] = code
        entry.session.touch()
        return {"session_id": session_id, "ran": [name for name, _code in cells]}

    async def sweep(self, now: float | None = None) -> list[str]:
        """Stop sessions idle past their limit; their ids. (The sandbox writes no host directory, so there is no
        size to watch: its tmpfs mounts are capped and charged to its scope.)"""

        now = time.monotonic() if now is None else now
        stopped = []
        for entry in list(self._entries.values()):
            session = entry.session
            if session.state != READY:
                continue
            if session.frames == 0 and now - session.last_activity >= entry.idle_minutes * 60:
                await entry.supervisor.stop("idle")
                stopped.append(session.session_id)
        return stopped

    async def _sweep_forever(self) -> None:
        while True:
            await asyncio.sleep(self._sweep_seconds)
            try:
                await self.sweep()
            except Exception:  # noqa: BLE001 - the sweep never ends the loop
                LOG.warning("notebook sweep failed", exc_info=True)

    # -- for tests and status ----------------------------------------------------------------------------------

    def sessions(self) -> list[Session]:
        return [entry.session for entry in self._entries.values()]

    def run_on_loop(self, make: Callable[[], Awaitable[T]], timeout: float = CALL_SECONDS) -> T:
        return self._call(make, timeout)


async def _cancel_other_tasks() -> None:
    """Every task left on the runtime's loop (the sweep, a draining pipe) ends before the loop stops."""

    current = asyncio.current_task()
    tasks = [task for task in asyncio.all_tasks() if task is not current]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


def _memory_bytes(session: Session) -> int | None:
    """The session's scope memory (``memory.current``), when it runs in a scope of its own."""

    process = session.process
    if process is None or process.returncode is not None:
        return None
    try:
        line = Path(f"/proc/{process.pid}/cgroup").read_text(encoding="utf-8").strip().splitlines()[-1]
        group = line.split("::", 1)[1]
        if not group.endswith(f"{session.unit}.scope"):
            return None
        return int((Path("/sys/fs/cgroup") / group.lstrip("/") / "memory.current").read_text())
    except (OSError, IndexError, ValueError):
        return None
