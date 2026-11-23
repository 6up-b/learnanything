"""Shared pieces of the notebook runtime's tests: a synthetic notebook, a fake process backend, and a frame client
that speaks marimo's frontend protocol through the frame proxy (no browser)."""

from __future__ import annotations

import asyncio
import contextlib
import json
import re
import shutil
import tempfile
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from learnloop.notebook_runtime.sandbox import Layout, Limits
from learnloop.notebook_runtime.supervisor import Session

#: A reactive notebook: a slider drives a computed cell; a held cell ships disabled.
SYNTHETIC_NOTEBOOK = '''import marimo

app = marimo.App()


@app.cell
def imports():
    import marimo as mo
    return (mo,)


@app.cell
def controls(mo):
    x = mo.ui.slider(1, 20, value=3)
    x
    return (x,)


@app.cell
def square(mo, x):
    mo.md(f"square={x.value * x.value}")
    return


@app.cell(disabled=True)
def reveal(mo, x):
    mo.md(f"revealed={x.value}")
    return


if __name__ == "__main__":
    app.run()
'''

#: A lesson notebook: a commit point (its own text field), a held reveal under it, and a held cell above every
#: commit point (released by none).
LESSON_NOTEBOOK = '''import marimo

app = marimo.App()


@app.cell
def imports():
    import marimo as mo
    return (mo,)


@app.cell(disabled=True)
def preface(mo):
    mo.md("preface=shown")
    return


@app.cell
def commit_square(mo):
    answer = mo.ui.text(placeholder="will the square grow faster than x?")
    mo.Html("<div class='ll-commit'>Will the square grow faster than x?</div>")
    answer
    return (answer,)


@app.cell
def echo(answer, mo):
    mo.md(f"committed={answer.value or 'nothing'}")
    return


@app.cell(disabled=True)
def reveal_square(mo):
    mo.md("revealed=yes, quadratically")
    return


if __name__ == "__main__":
    app.run()
'''

LIMITS = Limits(memory_mib=1024, scratch_mib=64)


@contextlib.contextmanager
def short_base_dir() -> Iterator[Path]:
    """A runtime directory in the system temp directory, removed after: a Unix socket's path must stay under about
    100 bytes, and a test's tmp_path is deeper than that."""

    base = Path(tempfile.mkdtemp(prefix="nbrt-"))
    try:
        yield base
    finally:
        shutil.rmtree(base, ignore_errors=True)


def session(tmp_path: Path, **values: Any) -> Session:
    layout = Layout(run_dir=tmp_path / "run", notebook=tmp_path / "nb.py", config_dir=tmp_path / "cfg",
                    hosts_file=tmp_path / "hosts")
    defaults = dict(session_id="nbs_test", owner="pad:p1", vault_key="/v", revision="r", layout=layout,
                    limits=LIMITS)
    defaults.update(values)
    return Session(**defaults)


class FakeProcess:
    _next_pid = 1000

    def __init__(self) -> None:
        FakeProcess._next_pid += 1
        self.pid = FakeProcess._next_pid
        self.returncode: int | None = None
        self._exited = asyncio.Event()

    def exit(self, code: int) -> None:
        if self.returncode is None:
            self.returncode = code
            self._exited.set()

    async def wait(self) -> int:
        await self._exited.wait()
        assert self.returncode is not None
        return self.returncode


class FakeBackend:
    """Processes that answer ready at once (or never), shut down when asked (or not), and record what happened."""

    def __init__(self, *, ready: bool = True, obeys_shutdown: bool = True, spawn_fails: bool = False,
                 api_status: int = 200) -> None:
        self.ready_answer = ready
        self.obeys_shutdown = obeys_shutdown
        self.spawn_fails = spawn_fails
        self.api_status = api_status
        self.processes: list[FakeProcess] = []
        self.signals: list[int] = []
        self.shutdowns = 0
        self.after_stops = 0
        self.api_calls: list[tuple[str, dict[str, Any]]] = []

    async def spawn(self, session: Session) -> FakeProcess:
        if self.spawn_fails:
            raise OSError("no bwrap here")
        process = FakeProcess()
        self.processes.append(process)
        return process

    async def ready(self, session: Session) -> bool:
        return self.ready_answer

    async def server_token(self, session: Session) -> str | None:
        return "server-token"

    async def shutdown(self, session: Session) -> None:
        self.shutdowns += 1
        if self.obeys_shutdown and session.process is not None:
            session.process.exit(0)

    def signal_group(self, session: Session, signum: int) -> None:
        self.signals.append(signum)
        if session.process is not None:
            session.process.exit(-signum)

    async def after_stop(self, session: Session) -> None:
        self.after_stops += 1

    async def api(self, session: Session, rel: str, body: dict[str, Any]) -> tuple[int, str]:
        self.api_calls.append((rel, body))
        return self.api_status, "{}"


async def until(predicate: Any, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() > deadline:
            raise AssertionError("condition never held")
        await asyncio.sleep(0.01)


def wait_state(runtime: Any, vault_key: str, session_id: str, state: str, timeout: float = 60.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while True:
        view = runtime.status(vault_key=vault_key, session_id=session_id)
        if view["state"] == state:
            return view
        if time.monotonic() > deadline:
            raise AssertionError(f"the session stayed {view['state']} ({view.get('error')})")
        time.sleep(0.05)


async def frame_round_trip(frame_url: str, *, marimo_session: str, wanted: list[str],
                           set_value: tuple[str, Any] | None = None, then_wanted: tuple[str, ...] = (),
                           during: Any = None, after_during: tuple[str, ...] = (),
                           pattern: str | None = None, linger: float = 0.0) -> dict[str, Any]:
    """Load the page, open the WebSocket, instantiate, wait for ``wanted`` in the cells' output; then optionally set
    a UI element's value (object id from a cell name) or call ``during()`` in a thread, and wait for
    ``then_wanted`` (with both, ``during()`` runs after the value is set, and ``after_during`` is waited for).
    ``pattern``: a regular expression whose matches in any message are kept in ``out["matches"]``. ``linger``: keep
    the WebSocket open (and read) this many seconds more, so reports that follow an output (a cell's idle) reach
    the proxy. What a browser frame would do, through the proxy."""

    import httpx
    import websockets
    from urllib.parse import urlparse

    url = urlparse(frame_url)
    base = url.path.rstrip("/")
    seen: set[str] = set()
    out: dict[str, Any] = {}
    async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{url.port}", timeout=30) as client:
        page = await client.get(base + "/")
        out["page_status"] = page.status_code
        out["page_csp"] = page.headers.get("content-security-policy", "")
        out["page_set_cookie"] = "set-cookie" in page.headers
        out["bridge_injected"] = "__ll/bridge.js" in page.text
        async with websockets.connect(f"ws://127.0.0.1:{url.port}{base}/ws?session_id={marimo_session}",
                                      max_size=None) as ws:
            reply = await client.post(base + "/api/kernel/instantiate",
                                      json={"objectIds": [], "values": [], "autoRun": True},
                                      headers={"Marimo-Session-Id": marimo_session})
            out["instantiate_status"] = reply.status_code

            async def wait_for(needles: tuple[str, ...] | list[str]) -> None:
                deadline = time.monotonic() + 30
                while not set(needles) <= seen:
                    message = await asyncio.wait_for(ws.recv(), max(0.1, deadline - time.monotonic()))
                    if '"kernel-ready"' in message[:100]:
                        data = json.loads(message)["data"]
                        out["cells"] = dict(zip(data["names"], data["cell_ids"], strict=True))
                    seen.update(needle for needle in needles if needle in message)
                    if pattern is not None:
                        out.setdefault("matches", []).extend(re.findall(pattern, message))

            await wait_for(wanted)
            if set_value is not None:
                cell, value = set_value
                started = time.monotonic()
                reply = await client.post(base + "/api/kernel/set_ui_element_value",
                                          json={"objectIds": [f"{out['cells'][cell]}-0"], "values": [value]},
                                          headers={"Marimo-Session-Id": marimo_session})
                out["set_status"] = reply.status_code
                await wait_for(then_wanted)
                out["round_trip_seconds"] = time.monotonic() - started
            if during is not None:
                out["during"] = await asyncio.get_running_loop().run_in_executor(None, during)
                await wait_for(after_during if set_value is not None else then_wanted)
            end = time.monotonic() + linger
            while time.monotonic() < end:
                try:
                    await asyncio.wait_for(ws.recv(), max(0.05, end - time.monotonic()))
                except asyncio.TimeoutError:
                    break
    out["seen"] = sorted(seen)
    return out


class RecordingRuntime:
    """A notebook runtime that records what it is asked to open and answers as a starting session would."""

    def __init__(self, refuse_release: Exception | None = None) -> None:
        self.opens: list[dict[str, Any]] = []
        self.refuse_release = refuse_release

    def release(self, **kwargs: Any) -> dict[str, Any]:
        if self.refuse_release is not None:
            raise self.refuse_release
        return {"session_id": kwargs["session_id"], "released": list(kwargs["names"])}

    def open(self, **kwargs: Any) -> dict[str, Any]:
        self.opens.append(kwargs)
        return {"session_id": "nbs_rec", "state": "starting", "frame_url": "http://127.0.0.1:1/s/x/",
                "cell_runs": {"c_one": {"status": "idle", "ms": 1.0, "error": False}}}

    def switch_vault(self, vault_key: Any) -> None:
        pass

    def close(self) -> None:
        pass
