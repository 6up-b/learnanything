"""Every private marimo interface the notebook runtime relies on, and nothing else.

marimo is pinned exactly in the ``notebook`` extra. The runtime drives ``marimo edit`` through its HTTP API, its
WebSocket messages and its frontend's URL parameters, none of which marimo documents as stable; each one the
runtime uses is named here, and :func:`interface_problems` checks the installed marimo still has them, so a pin
bump that moves one fails a test instead of a learner's notebook.

The file is also the launcher that runs inside the sandbox (``python -I -B <this file> SOCKET -- marimo-args``):
marimo's CLI has no Unix-socket option, so :func:`launch` patches ``uvicorn.Config`` to bind the socket and hands
the rest to marimo's own entry point. That is why the module imports only the standard library at the top: the
sandbox mounts this one file, and marimo's edit kernel is a multiprocessing *spawn* child that re-executes it as
``__mp_main__``, where the guard at the bottom keeps the launcher from running a second time.
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Any

#: The distribution and the extra that pin it (``pyproject.toml``); the pin itself is read from LearnLoop's
#: installed metadata, so there is no second copy of the version here.
MARIMO = "marimo"
NOTEBOOK_EXTRA = "notebook"

# -- the HTTP API (paths under the server's base URL) -------------------------------------------------------------
HEALTH = "health"
INDEX = ""
WEBSOCKET = "ws"
INSTANTIATE = "api/kernel/instantiate"
SET_UI_ELEMENT_VALUE = "api/kernel/set_ui_element_value"
SET_MODEL_VALUE = "api/kernel/set_model_value"
FUNCTION_CALL = "api/kernel/function_call"
SET_CELL_CONFIG = "api/kernel/set_cell_config"
RUN = "api/kernel/run"
SHUTDOWN = "api/kernel/shutdown"
RESTART_SESSION = "api/kernel/restart_session"

#: The routing header every kernel endpoint reads (the frame's consumer id, the ``session_id`` of its WebSocket).
SESSION_HEADER = "Marimo-Session-Id"
#: Skew protection: every POST but the WebSocket and the agent endpoint must carry the server's token, which the
#: server writes into its index page and changes at every start.
SERVER_TOKEN_HEADER = "Marimo-Server-Token"
_SERVER_TOKEN = re.compile(r'"serverToken":\s*"([^"]+)"')

#: What the frame (the notebook page, whose JavaScript includes model-written widget code) may call. Everything
#: that edits code, changes a cell's config (a held cell's release), runs scratch code, saves, restarts, shuts down,
#: browses files, opens a terminal or installs packages is the sidecar's, over the socket. marimo's app view also
#: asks for ``api/datasources/discover``, ``api/packages/sandbox`` and ``api/document/transaction``; refused, they
#: change nothing it shows.
FRAME_ALLOWED: frozenset[tuple[str, str]] = frozenset({
    ("GET", INDEX), ("GET", "index.html"), ("GET", HEALTH),
    ("POST", INSTANTIATE), ("POST", SET_UI_ELEMENT_VALUE), ("POST", SET_MODEL_VALUE), ("POST", FUNCTION_CALL),
})
#: Path prefixes the frame may GET: the frontend's hashed assets, anywidget ES modules and virtual files.
FRAME_ALLOWED_GET_PREFIXES: tuple[str, ...] = ("assets/", "@file/", "favicon", "apple-touch-icon",
                                               "android-chrome", "logo.png", "manifest.json")

#: The frontend's URL parameters: ``view-as=present`` is the app view of an edit-mode server, ``show-chrome=false``
#: hides the editor's chrome, ``kiosk=true`` joins a session as a read-only viewer.
APP_VIEW_PARAMS: tuple[tuple[str, str], ...] = (("view-as", "present"), ("show-chrome", "false"))
KIOSK_PARAM = "kiosk"
SESSION_ID_PARAM = "session_id"

#: What marimo's server sends a page that reconnects to a running session: a ``banner`` (with a Restart action) or
#: an ``alert`` titled "Reconnected". The proxy drops both on the way to the frame.
RECONNECTED_TITLE = "Reconnected"
RECONNECTED_OPS = ("banner", "alert")

#: The WebSocket message that names the session's cells (ids, names and code, in order).
KERNEL_READY_OP = "kernel-ready"

#: marimo's user config inside the sandbox: no autosave (the notebook is read-only), no language servers, no
#: Copilot, no watcher reloads.
MARIMO_TOML = """\
[save]
autosave = "off"
format_on_save = false

[runtime]
auto_instantiate = true
auto_reload = "off"
on_cell_change = "autorun"

[completion]
activate_on_typing = false
copilot = false

[language_servers.pylsp]
enabled = false
"""


def marimo_edit_args(notebook: str, token_file: str) -> list[str]:
    """``marimo edit``'s arguments: headless, token from a file, no update check and no marimo-managed sandbox
    (bubblewrap is the sandbox). The base URL (the session's secret path) is added by the launcher from its
    environment, so it never appears in a command line."""

    return ["edit", notebook, "--headless", "--skip-update-check", "--no-sandbox", "--token-password-file", token_file]


#: The launcher's environment variable carrying the base URL (``sandbox.BASE_URL_ENV``; named here too because the
#: launcher runs alone inside the sandbox).
BASE_URL_ENV = "LEARNLOOP_NOTEBOOK_BASE_URL"


def server_token(index_html: str) -> str | None:
    """The skew-protection token the server wrote into its index page."""

    match = _SERVER_TOKEN.search(index_html)
    return match.group(1) if match else None


def kernel_ready_cells(message: str) -> tuple[dict[str, str], dict[str, str]] | None:
    """From a WebSocket message: ``({cell name: cell id}, {cell id: code})`` when it is ``kernel-ready``."""

    if KERNEL_READY_OP not in message[:200]:
        return None
    try:
        data = json.loads(message)
    except ValueError:
        return None
    body = data.get("data", data) if isinstance(data, dict) else {}
    if not isinstance(body, dict) or body.get("op", data.get("op")) != KERNEL_READY_OP:
        return None
    ids = [str(value) for value in body.get("cell_ids") or ()]
    names = [str(value) for value in body.get("names") or ()]
    codes = [str(value) for value in body.get("codes") or ()]
    # Untrusted input (the sandbox writes it): a short list pairs what it can, never raises.
    return dict(zip(names, ids, strict=False)), dict(zip(ids, codes, strict=False))


def is_reconnected_notice(message: str) -> bool:
    """Whether a WebSocket message is marimo's "Reconnected" banner or toast."""

    if RECONNECTED_TITLE not in message[:400]:
        return False
    try:
        data = json.loads(message)
    except ValueError:
        return False
    body = data.get("data", data) if isinstance(data, dict) else {}
    op = data.get("op") if isinstance(data, dict) else None
    return op in RECONNECTED_OPS and isinstance(body, dict) and body.get("title") == RECONNECTED_TITLE


#: The WebSocket message that reports a cell's state (``status``: queued, running, idle, …) with its time.
CELL_OP = "cell-op"


def cell_progress(message: str) -> tuple[str, str | None, float | None, bool] | None:
    """From a ``cell-op`` message: ``(cell id, status or None, timestamp, whether its output is an error)``."""

    if CELL_OP not in message[:60]:
        return None
    try:
        data = json.loads(message)
    except ValueError:
        return None
    body = data.get("data", data) if isinstance(data, dict) else {}
    if not isinstance(body, dict) or data.get("op") != CELL_OP or not isinstance(body.get("cell_id"), str):
        return None
    output = body.get("output")
    error = isinstance(output, dict) and "error" in str(output.get("mimetype") or "")
    stamp = body.get("timestamp")
    status = body.get("status")
    return (body["cell_id"], status if isinstance(status, str) else None,
            float(stamp) if isinstance(stamp, (int, float)) else None, bool(error))


def ui_values(set_request_body: bytes) -> dict[str, Any]:
    """The UI element values a ``set_ui_element_value`` request sets (object id to value)."""

    try:
        data = json.loads(set_request_body or b"{}")
    except ValueError:
        return {}
    if not isinstance(data, dict):
        return {}
    # Untrusted input (the frame sends it): a short list pairs what it can, never raises.
    return {str(oid): value for oid, value in zip(data.get("objectIds") or (), data.get("values") or (), strict=False)}


def instantiate_with_values(body: bytes, recorded: dict[str, Any]) -> bytes | None:
    """An ``instantiate`` request filled with recorded UI values, or None to send it as it is.

    Only a page that sends no values of its own is filled (a fresh page after a restart or an idle stop): a page
    that kept its values knows them better than the record."""

    if not recorded:
        return None
    try:
        data = json.loads(body or b"{}")
    except ValueError:
        return None
    if not isinstance(data, dict) or data.get("objectIds"):
        return None
    data["objectIds"] = list(recorded)
    data["values"] = list(recorded.values())
    return json.dumps(data).encode("utf-8")


# -- notebooks generated from cells (a pad's marimo cells) --------------------------------------------------------

def cell_name(block_id: str) -> str:
    """A cell's marimo name from the block that holds it: stable, a valid identifier, unique per block id."""

    import hashlib

    safe = re.sub(r"[^0-9A-Za-z_]", "_", block_id).lower()
    if safe != block_id:
        # Two ids that differ only in case, or in characters an identifier cannot hold, must not share a name: the
        # exact id's hash keeps them apart.
        safe = f"{safe}_{hashlib.sha256(block_id.encode()).hexdigest()[:8]}"
    return f"c_{safe}"


def _cell_source(name: str, code: str) -> str:
    import ast

    try:
        ast.parse(code)
    except SyntaxError:
        # marimo's own form for a cell that does not parse, so the notebook still loads and the cell says why.
        literal = (f'"""\n{code.replace(chr(92), chr(92) * 2).replace(chr(34), chr(92) + chr(34))}\n"""'
                   if '"""' in code else f'r"""\n{code}\n"""')
        body = "\n".join("    " + line if line else line for line in f"{literal},\nname={name!r}".splitlines())
        return f"app._unparsable_cell(\n{body}\n)"
    # Tabs become the spaces Python reads them as (to the next multiple of 8), so indenting the body under the
    # function never mixes the two.
    lines = [("    " + line if line.strip() else "") for line in code.expandtabs(8).rstrip().splitlines()]
    return "\n".join([f"@app.cell\ndef {name}():", *lines, "    return"])


def notebook_from_cells(cells: list[tuple[str, str]]) -> str:
    """A marimo notebook file from ``(name, code)`` pairs, in order: the same cells always give the same bytes.

    A cell's signature is left empty: marimo reads each cell's references and definitions from its code (the
    runtime never saves the file, so marimo's canonical signatures are never needed)."""

    parts = ["import marimo", "", 'app = marimo.App(width="medium")']
    for name, code in cells:
        parts += ["", "", _cell_source(name, code)]
    parts += ["", "", 'if __name__ == "__main__":', "    app.run()", ""]
    return "\n".join(parts)


def cell_config_body(cell_ids: list[str], *, disabled: bool) -> dict[str, Any]:
    return {"configs": {cell_id: {"disabled": disabled} for cell_id in cell_ids}}


def run_body(cell_ids: list[str], codes: list[str]) -> dict[str, Any]:
    return {"cellIds": list(cell_ids), "codes": list(codes)}


# -- the pin -------------------------------------------------------------------------------------------------------

def pinned_version() -> str | None:
    """The exact marimo version LearnLoop's ``notebook`` extra pins, from its installed metadata."""

    from importlib import metadata

    try:
        requirements = metadata.requires("learnloop") or ()
    except metadata.PackageNotFoundError:
        return None
    for requirement in requirements:
        match = re.match(r"\s*marimo\s*==\s*([^\s;]+)", requirement)
        if match and NOTEBOOK_EXTRA in requirement.split(";", 1)[-1]:
            return match.group(1)
    return None


def installed_version() -> str | None:
    from importlib import metadata

    try:
        return metadata.version(MARIMO)
    except metadata.PackageNotFoundError:
        return None


def interface_problems() -> list[str]:
    """Every private interface above that the installed marimo no longer has, said in words; empty when all hold.

    Imports marimo (a test calls it; the runtime does not need to)."""

    import importlib
    import inspect

    problems: list[str] = []
    installed, pinned = installed_version(), pinned_version()
    if installed is None:
        return ["marimo is not installed (the notebook extra)"]
    if pinned is not None and installed != pinned:
        problems.append(f"marimo {installed} is installed but the notebook extra pins {pinned}")
    try:
        cli = importlib.import_module("marimo._cli.cli")
        start = importlib.import_module("marimo._server.start")
        router = importlib.import_module("marimo._server.api.router")
        middleware = importlib.import_module("marimo._server.api.middleware")
        deps = importlib.import_module("marimo._server.api.deps")
        models = importlib.import_module("marimo._server.models.models")
        requests = importlib.import_module("marimo._session.requests")
        notification = importlib.import_module("marimo._messaging.notification")
        kernel = importlib.import_module("marimo._session.managers.kernel")
        import uvicorn
    except ImportError as exc:
        return problems + [f"a marimo module the runtime relies on is gone: {exc}"]
    if not callable(getattr(cli, "main", None)):
        problems.append("marimo._cli.cli.main (the launcher's entry point) is gone")
    edit = getattr(cli, "edit", None)
    options = {param.name for param in getattr(edit, "params", ())}
    for option in ("headless", "skip_update_check", "sandbox", "token_password_file", "base_url"):
        if option not in options:
            problems.append(f"`marimo edit` has no --{option.replace('_', '-')} option")
    if "uvicorn.Config(" not in inspect.getsource(start.start):
        problems.append("marimo's start() no longer builds uvicorn.Config, which the socket launcher patches")
    if "fd" not in inspect.signature(uvicorn.Config.__init__).parameters:
        problems.append("uvicorn.Config has no `fd` parameter")
    paths = set(_route_paths(router.build_routes(base_url="")))
    for endpoint in (HEALTH, INSTANTIATE, SET_UI_ELEMENT_VALUE, SET_MODEL_VALUE, FUNCTION_CALL, SET_CELL_CONFIG,
                     RUN, SHUTDOWN, RESTART_SESSION, WEBSOCKET):
        if not any(path.rstrip("/").endswith("/" + endpoint) for path in paths):
            problems.append(f"marimo serves no /{endpoint}")
    if getattr(middleware.SkewProtectionMiddleware, "HEADER_NAME", None) != SERVER_TOKEN_HEADER:
        problems.append(f"the skew-protection header is no longer {SERVER_TOKEN_HEADER}")
    if SESSION_HEADER not in inspect.getsource(deps.AppState.get_current_session_id):
        problems.append(f"the kernel endpoints no longer route by {SESSION_HEADER}")
    for module, model, fields in ((requests, "InstantiateNotebookRequest", ("object_ids", "values", "auto_run")),
                                  (models, "UpdateUIElementRequest", ("object_ids", "values")),
                                  (models, "UpdateCellConfigRequest", ("configs",)),
                                  (models, "ExecuteCellsRequest", ("cell_ids", "codes"))):
        struct = getattr(module, model, None)
        have = set(getattr(struct, "__struct_fields__", ()))
        if struct is None or not set(fields) <= have:
            problems.append(f"{model} no longer has {fields}")
    ready = getattr(notification, "KernelReadyNotification", None)
    if ready is None or KERNEL_READY_OP not in repr(getattr(ready, "__struct_config__", "")) + inspect.getsource(
            ready):
        problems.append(f"the {KERNEL_READY_OP!r} WebSocket message is gone")
    probe = notebook_from_cells([("c_one", "x = 2"), ("c_two", "y = x * 3\ny"), ("c_bad", "def (")])
    try:
        load = importlib.import_module("marimo._ast.load")
        import tempfile

        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "probe.py")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(probe)
            app = load.load_app(path)
            names = [cell.name for _id, cell in app._cell_manager.valid_cells()]
            refs = {cell.name: sorted(cell.refs) for _id, cell in app._cell_manager.valid_cells()}
        if names != ["c_one", "c_two"] or refs.get("c_two") != ["x"]:
            problems.append(f"a notebook generated from cells loads as {names} {refs}, not as its cells")
    except Exception as exc:  # noqa: BLE001 - any failure to load the generated form is the problem itself
        problems.append(f"marimo no longer loads a notebook generated from cells: {type(exc).__name__}: {exc}")
    if 'Listener(family="AF_INET")' not in inspect.getsource(kernel):
        problems.append("the edit kernel no longer connects over an AF_INET listener (the sandbox's hosts file "
                        "may be unneeded, or something else may be)")
    static = os.path.join(os.path.dirname(importlib.import_module("marimo").__file__ or ""), "_static", "assets")
    bundle = ""
    try:
        for name in sorted(os.listdir(static)):
            if name.endswith(".js"):
                with open(os.path.join(static, name), encoding="utf-8", errors="replace") as handle:
                    text = handle.read()
                if "view-as" in text and "show-chrome" in text:
                    bundle = name
                    break
    except OSError:
        pass
    if not bundle:
        problems.append("the frontend no longer reads the view-as and show-chrome URL parameters")
    handler = importlib.import_module("marimo._server.api.endpoints.ws.session_handler")
    source = inspect.getsource(handler)
    if f'title="{RECONNECTED_TITLE}"' not in source or "BannerNotification(" not in source:
        problems.append("marimo's reconnect notice is no longer a banner titled Reconnected")
    return problems


def _route_paths(routes: Any, prefix: str = "") -> Any:
    for route in routes:
        inner = getattr(route, "routes", None)
        if inner is not None and not hasattr(route, "endpoint"):
            yield from _route_paths(inner, prefix + getattr(route, "path", ""))
        else:
            yield prefix + getattr(route, "path", "")


# -- the launcher (runs inside the sandbox) -------------------------------------------------------------------------

def launch(argv: list[str]) -> None:
    """``argv``: ``[this file, FD, "--", *marimo-args]``. Serves marimo on the listening Unix socket ``FD``, which
    trusted code outside the sandbox created and passed down; the server never creates or names a socket path."""

    import uvicorn

    if len(argv) < 3 or argv[2] != "--" or not argv[1].isdigit():
        raise SystemExit("usage: launcher FD -- marimo-args")
    socket_fd = int(argv[1])
    original = uvicorn.Config.__init__

    def on_the_socket(self: Any, app: Any, *args: Any, **kwargs: Any) -> None:
        kwargs["fd"] = socket_fd
        original(self, app, *args, **kwargs)

    uvicorn.Config.__init__ = on_the_socket  # type: ignore[method-assign]
    from marimo._cli.cli import main as marimo_main

    # The secret path stays out of every command line: marimo reads it from this process's own argv in memory,
    # and the variable is taken out so no child (the kernel) inherits it.
    base_url = os.environ.pop(BASE_URL_ENV, "")
    sys.argv = ["marimo", *argv[3:], *(["--base-url", base_url] if base_url else [])]
    marimo_main()


if __name__ == "__main__":
    launch(sys.argv)
