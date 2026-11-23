"""The notebook runtime with fakes: the supervisor's state machine, the runtime's sessions (one per owner, vault
and epoch scoped, bounded, idle-stopped), the frame proxy's checks, the adapter's parsing and the launch command.
The real sandbox is tests/test_notebook_runtime_sandbox.py."""

from __future__ import annotations

import asyncio
import json
import signal
import time
from pathlib import Path

import pytest

from learnloop.config.schema import LearnLoopConfig, NotebooksConfig
from learnloop.notebook_runtime import adapter, proxy, settings
from learnloop.notebook_runtime.sandbox import Layout, Limits, launch_command, scope_prefix
from learnloop.notebook_runtime.supervisor import (
    FAILED,
    READY,
    RESTARTING,
    STOPPED,
    Supervisor,
)
from tests.notebook_runtime_helpers import LIMITS, FakeBackend, session, short_base_dir, until


def run(coroutine):
    return asyncio.run(coroutine)


# -- the supervisor ---------------------------------------------------------------------------------------------

def test_a_start_ends_ready_with_the_servers_token(tmp_path):
    async def go():
        backend = FakeBackend()
        supervisor = Supervisor(session(tmp_path), backend)
        await supervisor.start()
        assert supervisor.session.state == READY
        assert supervisor.session.server_tok == "server-token"
        assert len(supervisor.session.start_seconds) == 1
        await supervisor.stop("closed")
    run(go())


def test_a_server_that_never_answers_fails_and_is_killed(tmp_path):
    async def go():
        backend = FakeBackend(ready=False)
        supervisor = Supervisor(session(tmp_path), backend, ready_timeout=0.2, stop_timeout=0.2)
        await supervisor.start()
        assert supervisor.session.state == FAILED
        assert "did not answer" in supervisor.session.last_error
        assert backend.signals == [signal.SIGTERM]
    run(go())


def test_a_spawn_that_fails_is_said(tmp_path):
    async def go():
        supervisor = Supervisor(session(tmp_path), FakeBackend(spawn_fails=True))
        await supervisor.start()
        assert supervisor.session.state == FAILED
        assert "could not start" in supervisor.session.last_error
    run(go())


def test_a_crashed_server_is_restarted_with_backoff(tmp_path):
    async def go():
        backend = FakeBackend()
        supervisor = Supervisor(session(tmp_path), backend, backoff_seconds=0.01)
        await supervisor.start()
        backend.processes[-1].exit(-9)
        await until(lambda: supervisor.session.restarts == 1 and supervisor.session.state == READY)
        assert len(backend.processes) == 2
        assert supervisor.session.generation == 2
        await supervisor.stop("closed")
    run(go())


def test_past_the_restart_limit_the_session_fails(tmp_path):
    async def go():
        backend = FakeBackend()
        supervisor = Supervisor(session(tmp_path), backend, restart_limit=2, backoff_seconds=0.01)
        await supervisor.start()
        for expected in (1, 2):
            backend.processes[-1].exit(1)
            await until(lambda n=expected: supervisor.session.restarts == n and supervisor.session.state == READY)
        backend.processes[-1].exit(1)
        await until(lambda: supervisor.session.state == FAILED)
        assert "stopped 3 times" in supervisor.session.last_error
        assert len(backend.processes) == 3
    run(go())


def test_a_stop_is_graceful_first(tmp_path):
    async def go():
        backend = FakeBackend()
        supervisor = Supervisor(session(tmp_path), backend)
        await supervisor.start()
        await supervisor.stop("idle")
        assert backend.shutdowns == 1 and backend.signals == []
        assert supervisor.session.state == STOPPED and supervisor.session.stop_reason == "idle"
        assert supervisor.session.process is None
        assert supervisor.session.restarts == 0  # an asked-for exit is no crash
    run(go())


def test_a_server_that_ignores_shutdown_is_terminated(tmp_path):
    async def go():
        backend = FakeBackend(obeys_shutdown=False)
        supervisor = Supervisor(session(tmp_path), backend, stop_timeout=0.1)
        await supervisor.start()
        await supervisor.stop("closed")
        assert backend.signals == [signal.SIGTERM]
        assert supervisor.session.state == STOPPED
    run(go())


def test_a_stopped_session_starts_again(tmp_path):
    async def go():
        backend = FakeBackend()
        supervisor = Supervisor(session(tmp_path), backend)
        await supervisor.start()
        supervisor.session.ui_values["MJUe-0"] = 7
        await supervisor.stop("idle")
        await supervisor.start()
        assert supervisor.session.state == READY and supervisor.session.stop_reason is None
        assert supervisor.session.ui_values == {"MJUe-0": 7}  # replayed into the next page's instantiate
        await supervisor.stop("closed")
    run(go())


def test_a_restart_waits_out_its_backoff_and_a_stop_ends_it(tmp_path):
    async def go():
        backend = FakeBackend()
        supervisor = Supervisor(session(tmp_path), backend, backoff_seconds=5)
        await supervisor.start()
        backend.processes[-1].exit(-9)
        await until(lambda: supervisor.session.state == RESTARTING)
        await supervisor.stop("closed")
        assert supervisor.session.state == STOPPED and len(backend.processes) == 1
    run(go())


# -- the runtime ------------------------------------------------------------------------------------------------

@pytest.fixture
def runtime():
    pytest.importorskip("uvicorn")
    from learnloop.notebook_runtime.runtime import NotebookRuntime

    backend = FakeBackend()
    with short_base_dir() as base:
        made = NotebookRuntime(backend=backend, base_dir=base, requirements=lambda: [], sweep_seconds=3600)
        made.fake_backend = backend
        yield made
        made.close()


def test_a_runtime_directory_too_deep_for_a_socket_is_refused(tmp_path):
    pytest.importorskip("uvicorn")
    from learnloop.notebook_runtime.runtime import NotebookRuntime
    from learnloop.notebook_runtime.sandbox import RuntimeUnavailable

    made = NotebookRuntime(backend=FakeBackend(), base_dir=tmp_path / ("deep" * 30), requirements=lambda: [])
    try:
        with pytest.raises(RuntimeUnavailable, match="too deep"):
            _open(made)
    finally:
        made.close()


def _open(runtime, *, vault="/v1", owner="pad:p1", source=b"cells", view="app", max_sessions=3, idle=10):
    return runtime.open(vault_key=vault, owner=owner, source=source, view=view, limits=LIMITS, idle_minutes=idle,
                        max_sessions=max_sessions)


def _ready(runtime, vault, session_id):
    from tests.notebook_runtime_helpers import wait_state

    return wait_state(runtime, vault, session_id, READY, timeout=5)


def test_open_answers_at_once_with_a_frame_url_on_its_own_port(runtime):
    view = _open(runtime)
    assert view["state"] in ("starting", READY)
    assert view["frame_url"].startswith("http://127.0.0.1:")
    assert "/s/" in view["frame_url"] and "view-as=present" in view["frame_url"]
    other = _open(runtime, owner="lesson:l1")
    assert other["frame_url"].split("/s/")[0] != view["frame_url"].split("/s/")[0]  # its own origin
    assert _ready(runtime, "/v1", view["session_id"])["frames_attached"] == 0


def test_the_same_owner_and_revision_is_one_session_and_a_new_revision_replaces_it(runtime):
    first = _open(runtime)
    assert _open(runtime)["session_id"] == first["session_id"]
    replaced = _open(runtime, source=b"other cells")
    assert replaced["session_id"] != first["session_id"]
    with pytest.raises(Exception, match=first["session_id"]):
        runtime.status(vault_key="/v1", session_id=first["session_id"])


def test_a_session_is_not_found_from_another_vault(runtime):
    from learnloop.notebook_runtime.runtime import SessionNotFound

    view = _open(runtime)
    with pytest.raises(SessionNotFound):
        runtime.status(vault_key="/v2", session_id=view["session_id"])
    with pytest.raises(SessionNotFound):
        runtime.close_session(vault_key="/v2", session_id=view["session_id"])


def test_a_vault_switch_stops_and_forgets_the_other_vaults_sessions(runtime):
    from learnloop.notebook_runtime.runtime import SessionNotFound

    kept = _open(runtime, vault="/v2", owner="pad:p2")
    gone = _open(runtime)
    _ready(runtime, "/v1", gone["session_id"])
    runtime.switch_vault("/v2")
    with pytest.raises(SessionNotFound):
        runtime.status(vault_key="/v1", session_id=gone["session_id"])
    assert runtime.status(vault_key="/v2", session_id=kept["session_id"])["state"] in ("starting", READY)
    assert [s.vault_key for s in runtime.sessions()] == ["/v2"]


def test_the_session_limit_stops_the_least_recently_used_idle_session(runtime):
    a = _open(runtime, owner="pad:a", max_sessions=2)
    _ready(runtime, "/v1", a["session_id"])
    b = _open(runtime, owner="pad:b", max_sessions=2)
    _ready(runtime, "/v1", b["session_id"])
    c = _open(runtime, owner="pad:c", max_sessions=2)
    states = {name: runtime.status(vault_key="/v1", session_id=view["session_id"])
              for name, view in (("a", a), ("b", b), ("c", c))}
    assert states["a"]["state"] == STOPPED and states["a"]["stop_reason"] == "make_room"
    assert states["b"]["state"] == READY


def test_with_every_session_shown_a_new_one_is_refused(runtime):
    from learnloop.notebook_runtime.runtime import SessionsFull

    a = _open(runtime, owner="pad:a", max_sessions=1)
    _ready(runtime, "/v1", a["session_id"])
    runtime.sessions()[0].frames = 1
    with pytest.raises(SessionsFull):
        _open(runtime, owner="pad:b", max_sessions=1)


def test_an_idle_session_is_stopped_and_reopening_restarts_it(runtime):
    view = _open(runtime, idle=1)
    _ready(runtime, "/v1", view["session_id"])
    runtime.sessions()[0].ui_values["MJUe-0"] = 5
    stopped = runtime.run_on_loop(lambda: runtime.sweep(now=runtime.sessions()[0].last_activity + 61))
    assert stopped == [view["session_id"]]
    assert runtime.status(vault_key="/v1", session_id=view["session_id"])["stop_reason"] == "idle"
    again = _open(runtime, idle=1)
    assert again["session_id"] == view["session_id"] and again["frame_url"] == view["frame_url"]
    _ready(runtime, "/v1", view["session_id"])
    assert runtime.sessions()[0].ui_values == {"MJUe-0": 5}


def test_a_session_with_a_frame_attached_is_not_idle(runtime):
    view = _open(runtime, idle=1)
    _ready(runtime, "/v1", view["session_id"])
    runtime.sessions()[0].frames = 1
    assert runtime.run_on_loop(lambda: runtime.sweep(now=runtime.sessions()[0].last_activity + 3600)) == []


def test_release_and_run_need_a_frame_and_known_cells(runtime):
    from learnloop.notebook_runtime.runtime import CellUnknown, NotConnected

    view = _open(runtime)
    _ready(runtime, "/v1", view["session_id"])
    with pytest.raises(NotConnected):
        runtime.release(vault_key="/v1", session_id=view["session_id"], names=["reveal"])
    session = runtime.sessions()[0]
    session.marimo_session_id, session.frames = "s_page", 1
    session.cell_ids = {"reveal": "bkHC", "square": "vblA"}
    with pytest.raises(CellUnknown):
        runtime.release(vault_key="/v1", session_id=view["session_id"], names=["nope"])
    assert runtime.release(vault_key="/v1", session_id=view["session_id"], names=["reveal"])["released"] == [
        "reveal"]
    runtime.run_cells(vault_key="/v1", session_id=view["session_id"], cells=[("square", "y = 2")])
    backend = runtime.fake_backend
    assert backend.api_calls == [(adapter.SET_CELL_CONFIG, {"configs": {"bkHC": {"disabled": False}}}),
                                 (adapter.RUN, {"cellIds": ["vblA"], "codes": ["y = 2"]})]


def test_a_refused_runtime_is_said_before_anything_starts(tmp_path):
    from learnloop.notebook_runtime.runtime import NotebookRuntime
    from learnloop.notebook_runtime.sandbox import RuntimeUnavailable

    made = NotebookRuntime(backend=FakeBackend(), base_dir=tmp_path, requirements=lambda: ["no bwrap"])
    with pytest.raises(RuntimeUnavailable, match="no bwrap"):
        _open(made)
    assert not made.running


def test_close_stops_every_session_and_the_loop(runtime):
    view = _open(runtime)
    _ready(runtime, "/v1", view["session_id"])
    backend = runtime.fake_backend
    runtime.close()
    assert not runtime.running and runtime.sessions() == []
    assert backend.shutdowns == 1


# -- the frame proxy's checks -----------------------------------------------------------------------------------

def test_the_gate_refuses_another_host_and_another_path():
    base = "/s/secret"
    assert proxy.gate("127.0.0.1:5000", "/s/secret/api/x", port=5000, base_url=base) == (None, "api/x")
    assert proxy.gate("127.0.0.1:5000", "/s/secret", port=5000, base_url=base) == (None, "")
    assert proxy.gate("localhost:5000", "/s/secret/", port=5000, base_url=base)[0] == "host"
    assert proxy.gate("evil.example:5000", "/s/secret/", port=5000, base_url=base)[0] == "host"
    assert proxy.gate(None, "/s/secret/", port=5000, base_url=base)[0] == "host"
    assert proxy.gate("127.0.0.1:5000", "/s/other/", port=5000, base_url=base)[0] == "path"
    assert proxy.gate("127.0.0.1:5000", "/s/secretx/", port=5000, base_url=base)[0] == "path"
    assert proxy.gate("127.0.0.1:5000", "/", port=5000, base_url=base)[0] == "path"


@pytest.mark.parametrize("method, rel", [
    ("GET", ""), ("GET", "assets/index-abc.js"), ("GET", "@file/12-x.js"), ("GET", proxy.BRIDGE_PATH),
    ("GET", "health"), ("POST", adapter.INSTANTIATE), ("POST", adapter.SET_UI_ELEMENT_VALUE),
    ("POST", adapter.SET_MODEL_VALUE), ("POST", adapter.FUNCTION_CALL),
])
def test_the_frame_may_load_the_app_and_drive_its_widgets(method, rel):
    assert proxy.frame_may(method, rel)


@pytest.mark.parametrize("method, rel", [
    ("POST", adapter.SET_CELL_CONFIG), ("POST", adapter.RUN), ("POST", "api/kernel/execute"),
    ("POST", "api/kernel/scratchpad/run"), ("POST", "api/document/transaction"), ("POST", "api/kernel/save"),
    ("POST", adapter.SHUTDOWN), ("POST", adapter.RESTART_SESSION), ("POST", "api/kernel/install_missing_packages"),
    ("POST", "api/files/list_files"), ("GET", "api/sessions"), ("GET", "terminal/ws"), ("POST", "assets/x.js"),
    ("POST", "api/datasources/discover"), ("POST", "api/packages/sandbox"), ("GET", "public-files-sw.js"),
])
def test_the_frame_may_not_edit_release_run_scratch_save_or_restart(method, rel):
    assert not proxy.frame_may(method, rel)


def test_upstream_carries_the_token_and_never_the_frames_cookies():
    headers = proxy.upstream_headers({"cookie": "a=b", "authorization": "Basic x", "host": "h", "origin": "o",
                                      "marimo-server-token": "stale", "marimo-session-id": "s_1",
                                      "content-type": "application/json"}, token="tok", server_token="fresh")
    assert headers == {"marimo-session-id": "s_1", "content-type": "application/json",
                       "authorization": "Bearer tok", "marimo-server-token": "fresh"}


def test_downstream_drops_cookies_and_framing_headers_and_sets_the_csp():
    out = dict(proxy.downstream_headers({"Set-Cookie": "session=1", "X-Frame-Options": "DENY",
                                         "Content-Security-Policy": "default-src *", "Content-Type": "text/html"},
                                        port=4321))
    assert b"set-cookie" not in {name.lower() for name in out}
    assert b"x-frame-options" not in {name.lower() for name in out}
    assert out[b"Content-Type"] == b"text/html"
    assert out[b"content-security-policy"] == proxy.frame_csp(4321).encode()


def test_the_frame_csp_contains_the_page():
    directives = dict(part.split(" ", 1) for part in proxy.frame_csp(4321).split("; "))
    assert directives["default-src"] == "'none'"
    assert "'wasm-unsafe-eval'" in directives["script-src"] and "'unsafe-eval'" not in directives["script-src"]
    assert directives["connect-src"] == "'self' ws://127.0.0.1:4321"  # no ipc:, no http://ipc.localhost
    assert directives["frame-ancestors"].split() == list(settings.WORKBENCH_ORIGINS)
    assert directives["object-src"] == "'none'" and directives["form-action"] == "'none'"


def test_the_bridge_and_the_paper_theme_are_injected_and_the_bridge_names_only_the_workbench_origins():
    html = proxy.inject_bridge(b"<html><head><title>x</title></head></html>", "/s/abc")
    assert html.startswith(b'<html><head><link rel="stylesheet" href="/s/abc/__ll/theme.css">'
                           b'<script src="/s/abc/__ll/bridge.js"></script>')
    script = proxy.bridge_script().decode()
    for origin in settings.WORKBENCH_ORIGINS:
        assert origin in script
    assert '"companion"' in script and '"menu"' in script and '"click"' in script and '"escape"' in script
    # It addresses each workbench origin in turn rather than reading the parent's from location.ancestorOrigins,
    # which not every engine has; the browser drops a post whose target origin is not the parent's.
    assert "ancestorOrigins" not in script and "postMessage(msg, origins[i])" in script


def test_the_paper_theme_sets_variables_and_serves_its_faces_from_the_frames_origin(tmp_path, monkeypatch):
    from learnloop.notebook_runtime import theme

    css = theme.theme_css("/s/abc")
    for variable, value in (("--background", theme.PAGE), ("--foreground", theme.INK), ("--card", theme.SURFACE),
                            ("--border", theme.RULE), ("--primary", theme.PURPLE), ("--tw-prose-headings", theme.INK)):
        assert f"{variable}: {value} !important" in css
    assert 'url("/s/abc/__ll/fonts/literata.woff2")' in css and "--marimo-heading-font" in css
    assert ".ll-commit" in css and f"border-left: 3px solid {theme.PURPLE}" in css
    # Variables plus exactly one rule: prose at the mockup's measured size and line.
    rules = [line for line in css.splitlines() if "{" in line and not line.lstrip().startswith(("@font-face", ":root", ".prose, .markdown {", "html, body", ".ll-"))]
    assert rules == [".markdown .paragraph, .markdown p, .markdown li, .prose .paragraph, .prose p, .prose li "
                     "{ font-size: 14.4px !important; line-height: 24px !important; }"]
    package = tmp_path / "literata" / "files"
    package.mkdir(parents=True)
    (package / "literata-latin-wght-normal.woff2").write_bytes(b"wOF2")
    monkeypatch.setenv(theme.FONT_PACKAGES_ENV, str(tmp_path))
    assert theme.font_file("literata.woff2").read_bytes() == b"wOF2"
    assert theme.font_file("../../etc/passwd") is None and theme.font_file("jetbrains-mono.woff2") is None


def test_the_frame_may_load_the_theme_and_its_fonts_and_nothing_else_of_the_proxys():
    assert proxy.frame_may("GET", proxy.THEME_PATH) and proxy.frame_may("GET", proxy.FONTS_PREFIX + "literata.woff2")
    assert not proxy.frame_may("POST", proxy.THEME_PATH) and not proxy.frame_may("GET", "__ll/other")


def test_marimos_reconnected_notice_is_recognised_and_nothing_else():
    banner = json.dumps({"op": "banner", "data": {"op": "banner", "title": "Reconnected",
                                                  "description": "You have reconnected to an existing session.",
                                                  "action": "restart"}})
    alert = json.dumps({"op": "alert", "data": {"title": "Reconnected", "description": "x"}})
    assert adapter.is_reconnected_notice(banner) and adapter.is_reconnected_notice(alert)
    other = json.dumps({"op": "banner", "data": {"title": "Kernel restarted", "description": "x"}})
    cell = json.dumps({"op": "cell-op", "data": {"output": "Reconnected"}})
    assert not adapter.is_reconnected_notice(other) and not adapter.is_reconnected_notice(cell)
    assert not adapter.is_reconnected_notice("Reconnected but not json")


def test_a_runtime_directory_too_deep_for_a_socket_is_passed_over(tmp_path, monkeypatch):
    from learnloop.notebook_runtime import sandbox

    deep = tmp_path / ("d" * 90)
    deep.mkdir()
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(deep))
    chosen = sandbox.runtime_base_dir()
    assert not str(chosen).startswith(str(deep))
    short = Path("/run/user") / str(__import__("os").getuid())
    if short.is_dir():
        monkeypatch.setenv("XDG_RUNTIME_DIR", str(short))
        assert sandbox.runtime_base_dir().parent == short


def _asgi(app, scope):
    sent = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    asyncio.run(app(scope, receive, send))
    return sent


def _scope(path, *, host="127.0.0.1:7000", method="GET", extra=()):
    return {"type": "http", "method": method, "path": path, "query_string": b"",
            "headers": [(b"host", host.encode()), *extra]}


@pytest.mark.parametrize("path, host, method, extra, status", [
    ("/s/abc/", "localhost:7000", "GET", (), 421),
    ("/s/zzz/", "127.0.0.1:7000", "GET", (), 403),
    ("/s/abc/api/kernel/set_cell_config", "127.0.0.1:7000", "POST", (), 403),
    ("/s/abc/public-files-sw.js", "127.0.0.1:7000", "GET", ((b"service-worker", b"script"),), 403),
    ("/s/abc/", "127.0.0.1:7000", "GET", (), 503),  # allowed, but the server is not ready
])
def test_the_proxy_refuses_before_reaching_the_server(tmp_path, path, host, method, extra, status):
    app = proxy.FrameProxy(session(tmp_path, secret="abc"))
    app.port = 7000
    sent = _asgi(app, _scope(path, host=host, method=method, extra=extra))
    assert sent[0]["status"] == status
    assert (b"content-security-policy", proxy.frame_csp(7000).encode()) in sent[0]["headers"]


def test_the_proxy_serves_its_bridge_and_records_ui_values_as_they_pass(tmp_path):
    app = proxy.FrameProxy(session(tmp_path, secret="abc"))
    app.port = 7000
    sent = _asgi(app, _scope("/s/abc/" + proxy.BRIDGE_PATH))
    assert sent[0]["status"] == 200 and sent[1]["body"] == proxy.bridge_script()


# -- the adapter's parsing --------------------------------------------------------------------------------------

def test_the_adapter_reads_marimos_messages():
    assert adapter.server_token('x "serverToken": "abc123", y') == "abc123"
    ready = '{"op": "kernel-ready", "data": {"op":"kernel-ready","cell_ids":["a","b"],"names":["x","y"],' \
            '"codes":["1","2"]}}'
    assert adapter.kernel_ready_cells(ready) == ({"x": "a", "y": "b"}, {"a": "1", "b": "2"})
    assert adapter.kernel_ready_cells('{"op": "cell-op"}') is None
    assert adapter.ui_values(b'{"objectIds": ["a-0", "b-0"], "values": [3, "x"]}') == {"a-0": 3, "b-0": "x"}
    assert adapter.ui_values(b"not json") == {}


def test_recorded_values_fill_only_a_page_that_sends_none():
    filled = adapter.instantiate_with_values(b'{"objectIds": [], "values": [], "autoRun": true}', {"a-0": 9})
    assert filled is not None
    import json

    assert json.loads(filled) == {"objectIds": ["a-0"], "values": [9], "autoRun": True}
    assert adapter.instantiate_with_values(b'{"objectIds": ["a-0"], "values": [4]}', {"a-0": 9}) is None
    assert adapter.instantiate_with_values(b'{"objectIds": []}', {}) is None


# -- the launch command ----------------------------------------------------------------------------------------

def test_the_launch_uses_the_shared_hardened_profile_and_the_servers_mounts(tmp_path):
    layout = Layout(run_dir=tmp_path / "run", notebook=tmp_path / "nb.py", config_dir=tmp_path / "cfg",
                    hosts_file=tmp_path / "hosts")
    argv, env = launch_command(layout, Limits(memory_mib=2048, scratch_mib=256), base_url="/s/x", unit="u",
                               scoped=True, socket_fd=9, bwrap="/usr/bin/bwrap")
    cut = argv.index("--", argv.index("/usr/bin/bwrap"))
    flags, inner = argv[argv.index("/usr/bin/bwrap"):cut], argv[cut + 1:]
    for flag in ("--unshare-all", "--die-with-parent", "--unshare-user", "--disable-userns", "--cap-drop"):
        assert flag in flags
    assert flags[-2:] == ["--remount-ro", "/"]
    assert ["--ro-bind", str(layout.notebook), "/nb/notebook.py"] == flags[flags.index(str(layout.notebook)) - 1:][:3]
    assert ["--ro-bind", str(layout.hosts_file), "/etc/hosts"] == flags[flags.index(str(layout.hosts_file)) - 1:][:3]
    assert flags[flags.index("--tmpfs", flags.index("--size")) - 2:][:4] == ["--size", str(256 * 1024 * 1024),
                                                                          "--tmpfs", "/scratch"]
    # No writable host path: the server listens on the socket trusted code made (descriptor 9 here) and reads its
    # token through a read-only mount.
    assert "--bind" not in flags and str(layout.run_dir) not in flags
    assert ["--ro-bind", str(layout.token_file), "/ll/token"] == flags[flags.index(str(layout.token_file)) - 1:][:3]
    assert "--dev-bind" not in flags  # CPU only: no device node beyond the profile's minimal /dev
    assert inner[2:4] == ["-B", "/ll/launcher.py"] and inner[4] == "9"
    # The secret path is in the environment, never the arguments (any local user reads a command line).
    assert inner[inner.index("--token-password-file") + 1] == "/ll/token" and "--base-url" not in inner
    assert env["LEARNLOOP_NOTEBOOK_BASE_URL"] == "/s/x"
    assert env["HOME"] == "/scratch" and env["XDG_CONFIG_HOME"] == "/ll/config"
    assert flags[flags.index("--unsetenv") + 1] == "DBUS_SESSION_BUS_ADDRESS"
    assert argv[:argv.index("/usr/bin/bwrap")][-1] == "--"


def test_the_scope_keeps_the_session_when_a_child_runs_out_of_memory():
    prefix = scope_prefix("learnloop-notebook-x", Limits(memory_mib=2048, scratch_mib=256), scoped=True)
    assert "OOMPolicy=continue" in prefix and f"MemoryMax={2048 * 1024 * 1024}" in prefix
    assert "MemorySwapMax=0" in prefix and f"TasksMax={settings.TASKS_MAX}" in prefix
    assert "--unit=learnloop-notebook-x" in prefix


def test_the_settings_defaults_and_their_dump():
    config = LearnLoopConfig()
    assert config.notebooks == NotebooksConfig(memory_max_mib=2048, idle_minutes=10, max_sessions=6, scratch_mib=256)
    assert "notebooks" not in config.model_dump(mode="json")  # whole-config hashes keep their bytes
    changed = LearnLoopConfig.model_validate({"notebooks": {"idle_minutes": 5}})
    assert changed.model_dump(mode="json")["notebooks"]["idle_minutes"] == 5
    assert settings.LEARNER_CELLS_SANDBOXED is True and settings.CPU_ONLY is True
    assert settings.FRAME_HOST == "127.0.0.1"


def test_the_app_frames_notebooks_from_any_loopback_port():
    import json

    conf = json.loads((Path(__file__).resolve().parents[1] / "apps" / "learnloop-tauri" / "src-tauri"
                       / "tauri.conf.json").read_text(encoding="utf-8"))
    frame_src = next(part for part in conf["app"]["security"]["csp"].split("; ") if part.startswith("frame-src"))
    assert f"http://{settings.FRAME_HOST}:*" in frame_src.split()


# -- a pad's cells: the session follows the cells' shape, not their code ------------------------------------------

def test_a_named_revision_keeps_the_session_while_its_code_changes(runtime):
    first = runtime.open(vault_key="/v1", owner="pad:p", source=b"x = 1", view="app", limits=LIMITS, idle_minutes=10,
                         max_sessions=3, revision="shape-1")
    _ready(runtime, "/v1", first["session_id"])
    again = runtime.open(vault_key="/v1", owner="pad:p", source=b"x = 2", view="app", limits=LIMITS, idle_minutes=10,
                         max_sessions=3, revision="shape-1")
    assert again["session_id"] == first["session_id"]
    reshaped = runtime.open(vault_key="/v1", owner="pad:p", source=b"x = 2\ny = 3", view="app", limits=LIMITS,
                            idle_minutes=10, max_sessions=3, revision="shape-2")
    assert reshaped["session_id"] != first["session_id"]


def test_a_stopped_session_restarts_on_the_code_it_is_reopened_with(runtime):
    view = runtime.open(vault_key="/v1", owner="pad:p", source=b"x = 1", view="app", limits=LIMITS, idle_minutes=1,
                        max_sessions=3, revision="shape-1")
    _ready(runtime, "/v1", view["session_id"])
    runtime.run_on_loop(lambda: runtime.sweep(now=runtime.sessions()[0].last_activity + 61))
    runtime.open(vault_key="/v1", owner="pad:p", source=b"x = 7", view="app", limits=LIMITS, idle_minutes=1,
                 max_sessions=3, revision="shape-1")
    assert runtime.sessions()[0].layout.notebook.read_bytes() == b"x = 7"


def test_a_cells_run_is_timed_from_marimos_messages():
    from learnloop.notebook_runtime.supervisor import note_cell_progress

    run = json.dumps({"op": "cell-op", "data": {"op": "cell-op", "cell_id": "Hbol", "status": "running", "timestamp": 10.0}})
    done = json.dumps({"op": "cell-op", "data": {"op": "cell-op", "cell_id": "Hbol", "status": "idle", "timestamp": 10.25}})
    failed = json.dumps({"op": "cell-op", "data": {"op": "cell-op", "cell_id": "Hbol", "output": {"mimetype": "application/vnd.marimo+error", "data": []}}})
    assert adapter.cell_progress(run) == ("Hbol", "running", 10.0, False)
    assert adapter.cell_progress(failed) == ("Hbol", None, None, True)
    assert adapter.cell_progress('{"op": "kernel-ready"}') is None
    held = session(Path("/tmp"))
    held.cell_ids = {"c_a": "Hbol"}
    for message in (run, done):
        note_cell_progress(held, *adapter.cell_progress(message))
    assert held.cell_runs == {"c_a": {"status": "idle", "ms": 250.0, "error": False}}
    note_cell_progress(held, *adapter.cell_progress(failed))
    assert held.cell_runs["c_a"]["error"] is True
    note_cell_progress(held, "unknown", "idle", 1.0, False)
    assert set(held.cell_runs) == {"c_a"}


# -- the runtime's HTTP stays on the machine ------------------------------------------------------------------------

def test_the_runtimes_http_only_ever_targets_its_sessions_unix_socket(tmp_path, monkeypatch):
    """The supervisor and the frame proxy import an HTTP client (audited in tests/test_plan_first_transport.py): every
    client they build speaks over the session's own Unix socket with the base URL http://127.0.0.1, so no request
    can leave the machine or reach a model; the WebSocket relay connects to the socket too, and nothing in the
    package names another host or opens a TCP connection of its own."""

    import ast
    import re

    import httpx

    from learnloop.notebook_runtime import supervisor as supervisor_module

    built: list[dict[str, object]] = []
    transports: list[dict[str, object]] = []

    class Transport:
        def __init__(self, **kwargs: object) -> None:
            transports.append(kwargs)

    class Client:
        def __init__(self, **kwargs: object) -> None:
            built.append(kwargs)

    monkeypatch.setattr(httpx, "AsyncHTTPTransport", Transport)
    monkeypatch.setattr(httpx, "AsyncClient", Client)
    from learnloop.notebook_runtime import hostfiles

    with short_base_dir() as base:  # a socket's path must be short
        held = session(base)
        hostfiles.private_dir(held.layout.run_dir)
        hostfiles.listening_socket(held.layout.run_dir, held.layout.socket.name).close()
        supervisor_module.SandboxBackend(scoped=False)._client(held)
        proxy.FrameProxy(held)._upstream()
    assert len(built) == 2 and len(transports) == 2
    assert all(kwargs["base_url"] == "http://127.0.0.1" for kwargs in built)
    assert all(set(kwargs) == {"uds"} and kwargs["uds"] == str(held.layout.socket) for kwargs in transports)

    package = Path(supervisor_module.__file__).parent
    for path in sorted(package.glob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                owner = getattr(node.func.value, "id", None)
                if owner == "httpx" and node.func.attr in {"AsyncClient", "Client"}:
                    transport = next((k.value for k in node.keywords if k.arg == "transport"), None)
                    assert isinstance(transport, ast.Call) and any(k.arg == "uds" for k in transport.keywords), path.name
                if owner == "httpx":
                    assert node.func.attr in {"AsyncClient", "AsyncHTTPTransport", "Limits"}, (path.name, node.func.attr)
                if owner == "websockets":
                    assert node.func.attr == "unix_connect", (path.name, node.func.attr)
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                # A URL's host is the loopback (a fragment ending in "://" is followed by FRAME_HOST, pinned below).
                for host in re.findall(r"[a-z]+://([^/:\s'\"`{]+)", node.value):
                    assert host == "127.0.0.1" or host == "localhost" or host.endswith(".localhost"), (path.name, host)
    assert settings.FRAME_HOST == "127.0.0.1"


# -- the frame cannot grow the sidecar's memory ---------------------------------------------------------------------

def _asgi_body(app, scope, body):
    sent = []

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        sent.append(message)

    asyncio.run(app(scope, receive, send))
    return sent


def test_an_oversized_request_is_refused_and_nothing_is_recorded_before_the_server_accepts_it(tmp_path):
    import json as _json

    held = session(tmp_path, secret="abc")
    held.cell_ids = {"controls": "Hbol"}
    app = proxy.FrameProxy(held)
    app.port = 7000
    path = "/s/abc/" + adapter.SET_UI_ELEMENT_VALUE
    big = _json.dumps({"objectIds": ["Hbol-0"], "values": ["x" * settings.REQUEST_MAX_BYTES]}).encode()
    sent = _asgi_body(app, _scope(path, method="POST"), big)
    assert sent[0]["status"] == 413 and held.ui_values == {}
    small = _json.dumps({"objectIds": ["Hbol-0", "fake-1"], "values": [3, 4]}).encode()
    sent = _asgi_body(app, _scope(path, method="POST"), small)
    assert sent[0]["status"] == 503 and held.ui_values == {}  # the server did not take it: nothing kept


def test_recorded_values_are_only_known_controls_within_a_bound(tmp_path):
    from learnloop.notebook_runtime.supervisor import record_ui_values

    held = session(tmp_path)
    held.cell_ids = {"controls": "Hbol", "other": "MJUe"}
    record_ui_values(held, {"Hbol-0": 3, "nope-0": 1, "Hbol": 2, "MJUe-1": "y"})
    assert held.ui_values == {"Hbol-0": 3, "MJUe-1": "y"}
    record_ui_values(held, {"MJUe-2": "x" * settings.UI_VALUES_MAX_BYTES})
    assert "MJUe-2" not in held.ui_values
    record_ui_values(held, {"Hbol-0": 5})
    assert held.ui_values["Hbol-0"] == 5


# -- a stop that lands while a server is being spawned ---------------------------------------------------------------

def test_a_stop_during_a_spawn_kills_the_server_when_the_spawn_returns(tmp_path):
    class SlowSpawn(FakeBackend):
        def __init__(self) -> None:
            super().__init__()
            self.gate = asyncio.Event()

        async def spawn(self, held):
            await self.gate.wait()
            return await super().spawn(held)

    async def scenario():
        backend = SlowSpawn()
        supervisor = Supervisor(session(tmp_path), backend)
        starting = asyncio.create_task(supervisor.start())
        await asyncio.sleep(0.05)
        stopping = asyncio.create_task(supervisor.stop("closed"))
        await asyncio.sleep(0.05)
        backend.gate.set()
        await asyncio.wait_for(asyncio.gather(starting, stopping), 5)
        return backend, supervisor

    backend, supervisor = asyncio.run(scenario())
    assert backend.processes and all(process.returncode is not None for process in backend.processes)
    assert supervisor.session.state == STOPPED and supervisor.session.process is None


# -- closing never leaves a server running ---------------------------------------------------------------------

def test_closing_kills_a_server_that_stalls_its_shutdown_and_ignores_sigterm(monkeypatch):
    pytest.importorskip("uvicorn")
    import signal as signals

    from learnloop.notebook_runtime import runtime as runtime_module
    from learnloop.notebook_runtime.runtime import NotebookRuntime

    class Stubborn(FakeBackend):
        async def shutdown(self, held):
            self.shutdowns += 1
            await asyncio.sleep(3600)

        def signal_group(self, held, signum):
            self.signals.append(signum)
            if signum == signals.SIGKILL and held.process is not None:
                held.process.exit(-signum)

    monkeypatch.setattr(runtime_module, "CLOSE_SECONDS", 0.5)
    backend = Stubborn()
    with short_base_dir() as base:
        made = NotebookRuntime(backend=backend, base_dir=base, requirements=lambda: [], sweep_seconds=3600,
                               supervisor_options={"stop_timeout": 30})
        view = made.open(vault_key="/v1", owner="pad:p1", source=b"x = 1", view="app", limits=LIMITS,
                         idle_minutes=10, max_sessions=3)
        _ready(made, "/v1", view["session_id"])
        process = backend.processes[0]
        started = time.monotonic()
        made.close()
    assert process.returncode is not None and signals.SIGKILL in backend.signals
    assert time.monotonic() - started < 15


# -- no notebook without aggregate memory and task caps -----------------------------------------------------------

def test_without_a_user_manager_notebooks_are_refused_not_run_under_a_per_process_limit(monkeypatch):
    from learnloop.notebook_runtime import sandbox as sandbox_module

    monkeypatch.setitem(sandbox_module._SCOPE_PROBE, "ok", False)
    assert any("user manager" in problem for problem in sandbox_module.missing_requirements())
    with pytest.raises(sandbox_module.RuntimeUnavailable):
        scope_prefix("u", Limits(memory_mib=512, scratch_mib=64), scoped=False)


def test_a_session_marked_as_a_review_releases_nothing(runtime):
    from learnloop.notebook_runtime.runtime import ReleaseRefused

    contract = {"points": [{"name": "commit_a", "held": ["reveal_a"]}], "held": ["reveal_a"]}
    view = runtime.open(vault_key="/v1", owner="lesson:l1", source=b"x = 1", view="app", limits=LIMITS,
                        idle_minutes=10, max_sessions=3, contract=contract)
    _ready(runtime, "/v1", view["session_id"])
    runtime.sessions()[0].commits.add("commit_a")
    assert runtime.mark_review(vault_key="/v1", session_id=view["session_id"])["lesson"]["review"] is True
    with pytest.raises(ReleaseRefused):
        runtime.release(vault_key="/v1", session_id=view["session_id"], names=["reveal_a"])
