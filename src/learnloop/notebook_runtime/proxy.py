"""The frame proxy: the only way a notebook frame reaches its sandboxed marimo server.

One proxy per session, on its own ``127.0.0.1`` port, so every notebook is its own origin (two frames cannot read
each other's DOM or call each other's server). It:

* refuses any ``Host`` but ``127.0.0.1:<port>`` (DNS rebinding) and any path outside ``/s/<secret>/`` (other local
  pages, other frames), which is also marimo's base URL;
* lets the frame call only :data:`~learnloop.notebook_runtime.adapter.FRAME_ALLOWED`; everything else (cell
  config, run, scratch, save, restart, terminal, files, packages, service workers) is refused here, and the sidecar
  does it over the socket;
* adds marimo's token upstream and strips every ``Set-Cookie``, so the page never holds the token and nothing
  depends on third-party cookies in a cross-site frame;
* rewrites the skew-protection token to the running server's (after a supervised restart the open page's token is
  stale, and the page is always the pinned marimo served through here, so the check guards nothing);
* sets a strict CSP on every response: no other origin, no Tauri IPC (``ipc:`` and ``http://ipc.localhost`` are not
  in ``connect-src``), ``'wasm-unsafe-eval'`` for marimo's WebAssembly, no ``'unsafe-eval'``;
* injects the bridge script and relays WebSockets, recording UI values (replayed into a fresh page's
  ``instantiate``) and the cell names marimo reports.
"""
from __future__ import annotations

import asyncio
import json
import logging
import socket
from typing import Any, Callable

from learnloop.notebook_runtime import adapter, settings, theme
from learnloop.notebook_runtime.supervisor import READY, Session, note_cell_progress, note_commits

LOG = logging.getLogger(__name__)

#: Request headers never forwarded upstream: the frame's cookies and credentials, hop-by-hop headers, and what the
#: proxy sets itself.
_DROPPED_REQUEST_HEADERS = frozenset({"host", "cookie", "authorization", "content-length", "connection",
                                      "accept-encoding", "origin", "referer", "upgrade", "keep-alive",
                                      "transfer-encoding", adapter.SERVER_TOKEN_HEADER.lower()})
#: Response headers never passed to the frame: cookies, framing and policy headers the proxy owns, hop-by-hop ones.
_DROPPED_RESPONSE_HEADERS = frozenset({"set-cookie", "content-length", "transfer-encoding", "content-encoding",
                                       "connection", "content-security-policy", "x-frame-options", "keep-alive"})

#: The bridge (the workbench's four messages): posts only when framed, and only ``companion``, ``menu``, ``click``
#: and ``escape``. It addresses each of the app's own origins in turn: a ``postMessage`` whose target origin is not
#: the parent's is dropped by the browser, so exactly the workbench receives it, without reading the parent's origin
#: from ``location.ancestorOrigins`` (which not every engine has). Notebook JavaScript shares the frame's origin and
#: can post the same messages, so the workbench treats their payloads as untrusted notebook text.
BRIDGE_JS = """(function () {
  if (window.parent === window) return;
  var origins = %(origins)s;
  function post(msg) {
    for (var i = 0; i < origins.length; i++) {
      try { window.parent.postMessage(msg, origins[i]); } catch (e) { /* not this origin */ }
    }
  }
  function selection() {
    var sel = window.getSelection(); var text = sel ? String(sel) : ""; var rect = null;
    if (sel && sel.rangeCount && text) {
      var r = sel.getRangeAt(0).getBoundingClientRect();
      rect = { x: r.x, y: r.y, width: r.width, height: r.height };
    }
    return { text: text.slice(0, %(text_max)d), rect: rect };
  }
  function typing(el) {
    return !!el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.isContentEditable);
  }
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { post({ ll: "escape" }); return; }
    if (e.key !== "c" && e.key !== "C") return;
    if (typing(e.target) ? !e.altKey : (e.ctrlKey || e.metaKey || e.altKey)) return;
    var s = selection();
    post({ ll: "companion", text: s.text, rect: s.rect, shift: e.shiftKey });
    e.preventDefault();
  }, true);
  document.addEventListener("contextmenu", function (e) {
    if (e.shiftKey) return;
    var s = selection();
    post({ ll: "menu", text: s.text, rect: s.rect, x: e.clientX, y: e.clientY });
    e.preventDefault();
  }, true);
  document.addEventListener("mousedown", function () { post({ ll: "click" }); }, true);
})();
"""
#: The longest selection the bridge sends (the workbench quotes it as context, never more).
BRIDGE_TEXT_MAX = 4000
BRIDGE_PATH = "__ll/bridge.js"
THEME_PATH = "__ll/theme.css"
FONTS_PREFIX = "__ll/fonts/"


def bridge_script() -> bytes:
    return (BRIDGE_JS % {"origins": json.dumps(list(settings.WORKBENCH_ORIGINS)), "text_max": BRIDGE_TEXT_MAX}).encode("utf-8")


def frame_csp(port: int) -> str:
    """The notebook frame's CSP. marimo's page needs inline scripts (its mount configuration) and WebAssembly; it
    does not need ``eval``. The policy contains the page (no other origin, no IPC, no beacons), it does not stop
    model JavaScript, which runs by design."""

    return "; ".join([
        "default-src 'none'",
        "script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' blob:",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: blob:",
        "font-src 'self' data:",
        f"connect-src 'self' ws://{settings.FRAME_HOST}:{port}",
        "worker-src 'self' blob:",
        "frame-src 'self' blob: data:",
        "media-src 'self' blob: data:",
        "manifest-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'none'",
        "frame-ancestors " + " ".join(settings.WORKBENCH_ORIGINS),
    ])


def gate(host: str | None, path: str, *, port: int, base_url: str) -> tuple[str | None, str]:
    """``(refusal, rel)``: why the request is refused (``"host"``, ``"path"``) or None, and its path under the
    session's base URL."""

    if host != f"{settings.FRAME_HOST}:{port}":
        return "host", ""
    if path != base_url and not path.startswith(base_url + "/"):
        return "path", ""
    return None, path[len(base_url) + 1:]


def frame_may(method: str, rel: str) -> bool:
    """Whether the frame may make this request (the bridge script is the proxy's own)."""

    if (method, rel) in adapter.FRAME_ALLOWED or (method == "GET" and rel in (BRIDGE_PATH, THEME_PATH)):
        return True
    if method == "GET" and rel.startswith(FONTS_PREFIX):
        return True
    return method == "GET" and rel.startswith(adapter.FRAME_ALLOWED_GET_PREFIXES)


def upstream_headers(headers: dict[str, str], *, token: str, server_token: str) -> dict[str, str]:
    forwarded = {name: value for name, value in headers.items() if name not in _DROPPED_REQUEST_HEADERS}
    forwarded["authorization"] = f"Bearer {token}"
    if server_token:
        forwarded[adapter.SERVER_TOKEN_HEADER.lower()] = server_token
    return forwarded


def downstream_headers(headers: Any, *, port: int) -> list[tuple[bytes, bytes]]:
    out = [(name.encode("latin-1"), value.encode("latin-1")) for name, value in headers.items()
           if name.lower() not in _DROPPED_RESPONSE_HEADERS]
    return out + security_headers(port)


def security_headers(port: int) -> list[tuple[bytes, bytes]]:
    return [(b"content-security-policy", frame_csp(port).encode()), (b"x-content-type-options", b"nosniff"),
            (b"referrer-policy", b"no-referrer"), (b"cross-origin-resource-policy", b"same-origin"),
            (b"cache-control", b"no-store")]


def inject_bridge(html: bytes, base_url: str) -> bytes:
    """The bridge script and the paper theme, first in the page's head (marimo adds its own styles later, at
    runtime; the theme's variables carry ``!important`` so its order does not matter)."""

    tag = (f'<link rel="stylesheet" href="{base_url}/{THEME_PATH}">'
           f'<script src="{base_url}/{BRIDGE_PATH}"></script>').encode()
    return html.replace(b"<head>", b"<head>" + tag, 1) if b"<head>" in html else tag + html


def _headers(scope: dict[str, Any]) -> dict[str, str]:
    return {name.decode("latin-1").lower(): value.decode("latin-1") for name, value in scope.get("headers", ())}


class FrameProxy:
    """The ASGI app in front of one session's server."""

    def __init__(self, session: Session, *, on_activity: Callable[[], None] | None = None) -> None:
        self.session = session
        self.port = 0
        self.on_activity = on_activity or (lambda: None)
        self._server: Any = None
        self._task: asyncio.Task | None = None
        self._client: Any = None
        self._client_generation = -1
        self._websockets: set[Any] = set()

    # -- lifecycle (on the runtime's loop) --------------------------------------------------------------------

    async def start(self) -> int:
        import uvicorn

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((settings.FRAME_HOST, 0))
        self.port = sock.getsockname()[1]
        config = uvicorn.Config(self, log_level="warning", lifespan="off", ws="websockets-sansio",
                                ws_ping_interval=None, access_log=False)
        self._server = uvicorn.Server(config)
        self._task = asyncio.create_task(self._server.serve(sockets=[sock]))
        while not self._server.started:
            if self._task.done():
                self._task.result()
            await asyncio.sleep(0.005)
        return self.port

    async def stop(self) -> None:
        for upstream in list(self._websockets):
            try:
                await upstream.close()
            except Exception:  # noqa: BLE001 - closing anyway
                pass
        if self._server is not None:
            self._server.should_exit = True
        if self._task is not None:
            try:
                await asyncio.wait_for(self._task, 5)
            except (asyncio.TimeoutError, Exception):  # noqa: BLE001 - the listener is gone either way
                self._task.cancel()
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _upstream(self) -> Any:
        import httpx

        session = self.session
        if self._client is None or self._client_generation != session.generation:
            old = self._client
            if old is not None:
                asyncio.get_running_loop().create_task(old.aclose())
            self._client = httpx.AsyncClient(transport=httpx.AsyncHTTPTransport(uds=str(session.layout.socket)),
                                             base_url="http://127.0.0.1", timeout=60.0,
                                             limits=httpx.Limits(max_connections=16))
            self._client_generation = session.generation
        return self._client

    # -- ASGI --------------------------------------------------------------------------------------------------

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] == "http":
            await self._http(scope, receive, send)
        elif scope["type"] == "websocket":
            await self._websocket(scope, receive, send)

    async def _plain(self, send: Any, status: int, text: str) -> None:
        body = text.encode()
        await send({"type": "http.response.start", "status": status,
                    "headers": [(b"content-type", b"text/plain; charset=utf-8"),
                                (b"content-length", str(len(body)).encode()), *security_headers(self.port)]})
        await send({"type": "http.response.body", "body": body})

    def _own_file(self, rel: str) -> tuple[bytes | None, bytes] | None:
        """The proxy's own files: the bridge, the paper theme and its fonts (None: not the proxy's)."""

        if rel == BRIDGE_PATH:
            return bridge_script(), b"text/javascript; charset=utf-8"
        if rel == THEME_PATH:
            return theme.theme_css(self.session.base_url).encode("utf-8"), b"text/css; charset=utf-8"
        if rel.startswith(FONTS_PREFIX):
            path = theme.font_file(rel[len(FONTS_PREFIX):])
            return (path.read_bytes() if path is not None else None), b"font/woff2"
        return None

    async def _http(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        session = self.session
        headers = _headers(scope)
        method = scope["method"]
        refusal, rel = gate(headers.get("host"), scope["path"], port=self.port, base_url=session.base_url)
        if refusal is None and headers.get("service-worker") == "script":
            refusal = "service-worker"
        if refusal is not None:
            await self._plain(send, 421 if refusal == "host" else 403, "refused")
            return
        if not frame_may(method, rel):
            await self._plain(send, 403, "refused by the notebook frame policy")
            return
        own = self._own_file(rel)
        if own is not None:
            body, content_type = own
            if body is None:
                await self._plain(send, 404, "not installed")
                return
            await send({"type": "http.response.start", "status": 200, "headers": [
                (b"content-type", content_type), (b"content-length", str(len(body)).encode()),
                *security_headers(self.port)]})
            await send({"type": "http.response.body", "body": body})
            return
        body = b""
        while True:
            message = await receive()
            body += message.get("body", b"")
            if not message.get("more_body"):
                break
        if headers.get(adapter.SESSION_HEADER.lower()):
            session.marimo_session_id = headers[adapter.SESSION_HEADER.lower()]
        if rel == adapter.SET_UI_ELEMENT_VALUE:
            values = adapter.ui_values(body)
            session.ui_values.update(values)
            note_commits(session, values)
        elif rel == adapter.INSTANTIATE:
            filled = adapter.instantiate_with_values(body, session.ui_values)
            if filled is not None:
                body = filled
        if session.state != READY:
            await self._plain(send, 503, "the notebook server is starting")
            return
        session.touch()
        self.on_activity()
        query = scope.get("query_string", b"").decode("latin-1")
        url = scope["path"] + (f"?{query}" if query else "")
        try:
            client = self._upstream()
            request = client.build_request(method, url, content=body,
                                           headers=upstream_headers(headers, token=session.token,
                                                                    server_token=session.server_tok))
            response = await client.send(request, stream=True)
        except Exception:  # noqa: BLE001 - the server is down or restarting
            await self._plain(send, 502, "the notebook server is not running")
            return
        try:
            out = downstream_headers(response.headers, port=self.port)
            if "text/html" in response.headers.get("content-type", ""):
                html = inject_bridge(await response.aread(), session.base_url)
                await send({"type": "http.response.start", "status": response.status_code,
                            "headers": out + [(b"content-length", str(len(html)).encode())]})
                await send({"type": "http.response.body", "body": html})
                return
            await send({"type": "http.response.start", "status": response.status_code, "headers": out})
            async for chunk in response.aiter_raw():
                await send({"type": "http.response.body", "body": chunk, "more_body": True})
            await send({"type": "http.response.body", "body": b""})
        finally:
            await response.aclose()

    async def _websocket(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        import websockets

        session = self.session
        await receive()  # websocket.connect
        headers = _headers(scope)
        refusal, rel = gate(headers.get("host"), scope["path"], port=self.port, base_url=session.base_url)
        if refusal is not None or rel != adapter.WEBSOCKET or session.state != READY:
            await send({"type": "websocket.close", "code": 4403 if refusal or rel != adapter.WEBSOCKET else 1013})
            return
        query = scope.get("query_string", b"").decode("latin-1")
        for part in query.split("&"):
            name, _, value = part.partition("=")
            if name == adapter.SESSION_ID_PARAM and value:
                session.marimo_session_id = value
        uri = f"ws://127.0.0.1{scope['path']}" + (f"?{query}" if query else "")
        try:
            upstream = await websockets.unix_connect(str(session.layout.socket), uri,
                                                     additional_headers={"Authorization": f"Bearer {session.token}"},
                                                     max_size=None, ping_interval=None)
        except Exception:  # noqa: BLE001 - the page reconnects with its own backoff
            await send({"type": "websocket.close", "code": 1011})
            return
        await send({"type": "websocket.accept"})
        self._websockets.add(upstream)
        session.frames += 1
        session.touch()
        self.on_activity()

        async def down() -> None:
            try:
                async for message in upstream:
                    if isinstance(message, bytes):
                        await send({"type": "websocket.send", "bytes": message})
                        continue
                    cells = adapter.kernel_ready_cells(message)
                    if cells is not None:
                        session.cell_ids, session.cell_codes = cells
                    progress = adapter.cell_progress(message)
                    if progress is not None:
                        note_cell_progress(session, *progress)
                    if adapter.is_reconnected_notice(message):
                        # A frame reconnects whenever its window moves or reloads; marimo's banner says so and
                        # offers a Restart the frame may not call (restarts are the sidecar's).
                        continue
                    await send({"type": "websocket.send", "text": message})
            except Exception:  # noqa: BLE001 - the server went away; the page reconnects
                pass
            try:
                await send({"type": "websocket.close", "code": 1012})
            except Exception:  # noqa: BLE001 - the page already left
                pass

        async def up() -> None:
            while True:
                message = await receive()
                if message["type"] == "websocket.disconnect":
                    break
                if message.get("text") is not None:
                    await upstream.send(message["text"])
                elif message.get("bytes") is not None:
                    await upstream.send(message["bytes"])
                session.touch()

        tasks = [asyncio.create_task(down()), asyncio.create_task(up())]
        try:
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for task in tasks:
                task.cancel()
            self._websockets.discard(upstream)
            try:
                await upstream.close()
            except Exception:  # noqa: BLE001 - closing anyway
                pass
            session.frames = max(0, session.frames - 1)
            session.touch()
