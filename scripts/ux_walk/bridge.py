"""The walk bridge: the Tauri shell's job, done over HTTP on 127.0.0.1 for the browser-mode frontend.

One process per walk. It starts ONE ``python -m learnloop_sidecar`` for one
vault and, for every command the frontend invokes, does what
``apps/learnloop-tauri/src-tauri/src/commands.rs`` does (the table is parsed
from that file at start: walk_commands.py). It also serves the browser-mode
bundle (vite.browser.config.mjs), the vault-files-changed event the Rust
watcher pushes, the llpdf/llmedia protocols, the native file chooser as a
request the walk driver answers, and, in fake-model mode, the fake chat
endpoint the vault's ``walk_fake`` profile points at.

Everything the persona never sees (each call, its time, every failure, the
fake model's requests) goes to ``<walk>/analyst/bridge.jsonl``.

    python scripts/ux_walk/bridge.py --walk-root <walk> --vault <path> --port <n> [--create-if-missing]
        [--models fake|live --allow-live-route --config-dir <dir>]
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
import os
import queue
import re
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fake_model  # noqa: E402
import walk_commands  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TAURI_DIR = ROOT / "apps" / "learnloop-tauri"
DEFAULT_BUNDLE = TAURI_DIR / "dist-browser"
CLIENT_VERSION = "0.1.0-browser-walk"
RESPONSE_TIMEOUT = float(os.environ.get("LEARNLOOP_SIDECAR_TIMEOUT_SECS") or 16 * 60)
STARTUP_TIMEOUT = 60.0
INVALIDATING = {"internal", "sidecar_timeout", "sidecar_unavailable", "sidecar_protocol_error"}
WATCHED_SUFFIXES = {".yaml", ".yml", ".md", ".toml", ".json"}
IGNORED_PARTS = {".git", "target", "__pycache__", ".pytest_cache"}
IGNORED_PREFIXES = (("canonical-sources", "raw"), ("media", "animations"))
MAX_MEDIA_RANGE = 4 * 1024 * 1024
CONTENT_ADDRESSED = re.compile(r"^sha256-[0-9a-fA-F]+$")
VAULT_FILES_CHANGED = "learnloop://vault-files-changed"


# -- errors, in the shapes errors.rs gives the frontend --------------------------------------------


def command_error(code: str, message: str, retryable: bool, details: Any = None) -> dict:
    return {"code": code, "message": message, "retryable": retryable, "details": details}


def unavailable(details: Any) -> dict:
    return command_error(
        "sidecar_unavailable",
        "LearnLoop's local service is unavailable. Retry the action; if it keeps failing, restart the app.",
        True, details)


def outcome_unknown(details: dict) -> dict:
    return command_error(
        "sidecar_unavailable",
        "LearnLoop lost contact with its local service and could not confirm whether this action completed. "
        "Check the current state before trying it again.",
        False, {"outcome": "unknown", **details})


def protocol_error(details: dict) -> dict:
    return command_error(
        "sidecar_protocol_error",
        "LearnLoop received an invalid response and could not confirm whether this action completed. "
        "Check the current state before trying it again.",
        False, {"outcome": "unknown", **details})


def timeout_error(details: dict) -> dict:
    return command_error(
        "sidecar_timeout",
        "The local learning service took too long to respond, so LearnLoop could not confirm whether this action "
        "completed. Check the current state before trying it again.",
        False, details)


def from_rpc(error: Any) -> dict:
    if not isinstance(error, dict) or not isinstance(error.get("code"), int) or not isinstance(
            error.get("message"), str):
        return protocol_error({"phase": "decode_error_response"})
    data = error.get("data") if isinstance(error.get("data"), dict) else {}
    return command_error(
        data.get("code") if isinstance(data.get("code"), str) else "internal",
        error["message"],
        data.get("retryable") is True,
        data.get("details"),
    )


class CommandFailed(Exception):
    def __init__(self, error: dict | str):
        super().__init__(error if isinstance(error, str) else error.get("message"))
        self.error = error


# -- the analyst's log -------------------------------------------------------------------------------


class Log:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.lock = threading.Lock()

    def write(self, kind: str, **fields: Any) -> None:
        record = {"t": round(time.time(), 3), "kind": kind, **fields}
        line = json.dumps(record, default=str)
        with self.lock, self.path.open("a", encoding="utf-8") as stream:
            stream.write(line + "\n")


# -- the sidecar -------------------------------------------------------------------------------------


class SidecarClient:
    """One ``python -m learnloop_sidecar`` over ndjson JSON-RPC on stdio (sidecar.rs's SidecarClient)."""

    def __init__(self, env: dict[str, str], cwd: Path, stderr_path: Path):
        self.stderr = stderr_path.open("ab")
        self.process = subprocess.Popen(
            [sys.executable, "-m", "learnloop_sidecar"],
            cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr,
        )
        self.lines: queue.Queue[bytes | None] = queue.Queue()
        self.next_id = 1
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def call(self, method: str, params: Any, timeout: float = RESPONSE_TIMEOUT) -> Any:
        request_id = self.next_id
        self.next_id += 1
        request = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        try:
            assert self.process.stdin is not None
            self.process.stdin.write((json.dumps(request) + "\n").encode("utf-8"))
            self.process.stdin.flush()
        except OSError as exc:
            raise CommandFailed(outcome_unknown({"phase": "write_request", "method": method,
                                                 "diagnostic": str(exc)})) from None
        try:
            line = self.lines.get(timeout=timeout)
        except queue.Empty:
            raise CommandFailed(timeout_error({"method": method, "timeoutSeconds": int(timeout),
                                               "outcome": "unknown"})) from None
        if line is None:
            raise CommandFailed(outcome_unknown({"phase": "await_response", "method": method,
                                                 "exitStatus": str(self.process.poll())}))
        try:
            response = json.loads(line)
        except ValueError as exc:
            raise CommandFailed(protocol_error({"phase": "decode_response", "method": method,
                                                "diagnostic": str(exc)})) from None
        if not isinstance(response, dict) or response.get("jsonrpc") != "2.0" or response.get("id") != request_id:
            raise CommandFailed(protocol_error({"phase": "validate_response_envelope", "method": method}))
        if "result" in response and "error" not in response:
            return response["result"]
        if "error" in response and "result" not in response:
            raise CommandFailed(from_rpc(response["error"]))
        raise CommandFailed(protocol_error({"phase": "validate_response_payload", "method": method}))

    def stop(self, graceful: bool) -> None:
        if graceful and self.process.poll() is None:
            try:
                self.call("shutdown", {}, timeout=2.0)
            except CommandFailed:
                pass
        if self.process.poll() is None:
            self.process.kill()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        self.stderr.close()

    @property
    def pid(self) -> int:
        return self.process.pid


class SidecarManager:
    """sidecar.rs's SidecarManager, without the isolated second process (one sidecar per walk)."""

    def __init__(self, env: dict[str, str], cwd: Path, log: Log, stderr_path: Path, allowed_root: Path):
        self.env = env
        self.cwd = cwd
        self.log = log
        self.stderr_path = stderr_path
        self.allowed_root = allowed_root.resolve()
        self.lock = threading.Lock()
        self.client: SidecarClient | None = None
        self.vault: Path | None = None
        self.grading_override: str | None = None
        self.generation = 0

    def _spawn(self) -> SidecarClient:
        client = SidecarClient(self.env, self.cwd, self.stderr_path)
        try:
            client.call("rpc.ping", {}, timeout=STARTUP_TIMEOUT)
        except CommandFailed as exc:
            client.stop(False)
            raise CommandFailed(unavailable({"phase": "startup", "attempts": [
                {"launcher": "walk bridge", "phase": "readiness_probe", "diagnostic": exc.error}]})) from None
        self.log.write("sidecar_started", pid=client.pid)
        return client

    def initialize(self, vault: Path | None, create_if_missing: bool = False) -> Any:
        """Must hold ``self.lock``."""

        target = (vault or self.vault)
        if target is None:
            raise CommandFailed(unavailable({"phase": "startup", "diagnostic": "no vault selected"}))
        same_vault = target == self.vault
        if self.client is not None and same_vault:
            return {"ok": True}
        if self.client is not None:
            self.client.stop(True)
            self.client = None
        candidate = self._spawn()
        try:
            initialized = candidate.call("initialize", {
                "vaultPath": str(target), "clientVersion": CLIENT_VERSION, "createIfMissing": create_if_missing,
            })
        except CommandFailed:
            candidate.stop(False)
            raise
        reset = None
        provider = self.grading_override
        if self.grading_override and same_vault:
            try:
                candidate.call("set_grading_provider", {"provider": self.grading_override})
            except CommandFailed as exc:
                if isinstance(exc.error, dict) and exc.error.get("code") in INVALIDATING:
                    candidate.stop(False)
                    raise
                reset = exc.error
                self.grading_override = None
        elif not same_vault:
            self.grading_override = None
        self.client = candidate
        if target != self.vault:
            self.generation += 1
        self.vault = target
        if reset is not None:
            raise CommandFailed(command_error(
                "grading_provider_reset",
                f'LearnLoop restarted its local service but could not restore the grading provider "{provider}" '
                f"({reset.get('message')}). Grading now uses the vault's configured provider. Retry the action.",
                True, {"provider": provider, "cause": reset}))
        return initialized

    def call(self, method: str, params: Any) -> Any:
        with self.lock:
            if self.client is None:
                self.initialize(None)
            assert self.client is not None
            try:
                result = self.client.call(method, params)
            except CommandFailed as exc:
                if isinstance(exc.error, dict) and exc.error.get("code") in INVALIDATING:
                    self.client.stop(False)
                    self.client = None
                raise
            if method == "set_grading_provider" and isinstance(params, dict):
                self.grading_override = params.get("provider")
            return result

    def select_vault(self, path: str | None) -> Any:
        """SidecarManager::select_vault, refusing folders outside the walk (owner vaults stay unreachable)."""

        target = Path(path).expanduser().resolve() if path else None
        if target is not None and not target.is_relative_to(self.allowed_root):
            raise CommandFailed(command_error(
                "browser_mode_unavailable",
                "Opening that folder is not available in browser mode: a walk only opens folders inside this "
                "person's files.", False, {"path": str(target)}))
        with self.lock:
            try:
                initialized = self.initialize(target)
            except CommandFailed as exc:
                if not (isinstance(exc.error, dict) and exc.error.get("code") == "grading_provider_reset"):
                    raise
                initialized = {}
            if isinstance(initialized, dict) and "vault" in initialized:
                return initialized["vault"]
            assert self.client is not None
            snapshot = self.client.call("load_vault", {})
            return snapshot.get("vault") if isinstance(snapshot, dict) else None

    def stop(self) -> None:
        with self.lock:
            if self.client is not None:
                self.client.stop(True)
                self.client = None


# -- the vault watcher (vault_watcher.rs, by polling) ---------------------------------------------


def _watchable(relative: Path) -> bool:
    parts = relative.parts
    if any(part in IGNORED_PARTS for part in parts):
        return False
    if any(parts[: len(prefix)] == prefix for prefix in IGNORED_PREFIXES):
        return False
    return relative.suffix in WATCHED_SUFFIXES


def scan(root: Path) -> dict[str, tuple[int, int]]:
    """``{relative path: (mtime_ns, size)}`` of every file the Rust watcher would report."""

    found: dict[str, tuple[int, int]] = {}
    for directory, dirs, files in os.walk(root):
        base = Path(directory)
        relative_dir = base.relative_to(root)
        dirs[:] = [name for name in dirs if name not in IGNORED_PARTS
                   and not any((relative_dir / name).parts[: len(prefix)] == prefix for prefix in IGNORED_PREFIXES)]
        for name in files:
            relative = relative_dir / name
            if not _watchable(relative):
                continue
            try:
                stat = (base / name).stat()
            except OSError:
                continue
            found[relative.as_posix()] = (stat.st_mtime_ns, stat.st_size)
    return found


def changed(before: dict[str, tuple[int, int]], after: dict[str, tuple[int, int]]) -> set[str]:
    return {path for path in before.keys() | after.keys() if before.get(path) != after.get(path)}


class Events:
    def __init__(self) -> None:
        self.subscribers: list[queue.Queue[str]] = []
        self.lock = threading.Lock()

    def subscribe(self) -> queue.Queue[str]:
        subscriber: queue.Queue[str] = queue.Queue()
        with self.lock:
            self.subscribers.append(subscriber)
        return subscriber

    def unsubscribe(self, subscriber: queue.Queue[str]) -> None:
        with self.lock:
            if subscriber in self.subscribers:
                self.subscribers.remove(subscriber)

    def emit(self, event: str, payload: Any) -> None:
        data = json.dumps({"event": event, "payload": payload})
        with self.lock:
            for subscriber in self.subscribers:
                subscriber.put(data)


class Watcher(threading.Thread):
    def __init__(self, bridge: "Bridge"):
        super().__init__(daemon=True)
        self.bridge = bridge
        self.root: Path | None = None
        self.snapshot: dict[str, tuple[int, int]] = {}
        self.target: Path | None = None

    def watch(self, root: Path) -> None:
        self.target = root.resolve()

    def run(self) -> None:
        while not self.bridge.stopping.is_set():
            time.sleep(0.4)
            if self.target is not None and self.target != self.root:
                self.root = self.target
                self.snapshot = scan(self.root) if self.root.exists() else {}
                continue
            if self.root is None or not self.root.exists():
                continue
            current = scan(self.root)
            paths = changed(self.snapshot, current)
            if not paths:
                continue
            # Editors and the sidecar write in bursts: wait for a quiet 160 ms, then refresh once.
            while True:
                time.sleep(0.16)
                later = scan(self.root)
                more = changed(current, later)
                current = later
                if not more:
                    break
                paths |= more
            self.snapshot = current
            self.bridge.refresh(self.root, sorted(paths))


# -- the bridge --------------------------------------------------------------------------------------


class Bridge:
    def __init__(self, args: argparse.Namespace):
        self.walk_root = Path(args.walk_root).resolve()
        self.analyst = self.walk_root / "analyst"
        self.run_dir = self.walk_root / "run"
        self.persona_files = (self.walk_root / "persona" / "files").resolve()
        self.log = Log(self.analyst / "bridge.jsonl")
        self.bundle = Path(args.bundle).resolve()
        self.port = args.port
        self.models = args.models
        self.table = walk_commands.load_table()
        self.events = Events()
        self.stopping = threading.Event()
        self.watcher = Watcher(self)
        self.fake = fake_model.FakeModel() if self.models == "fake" else None
        self.state_lock = threading.Lock()
        self.inflight: dict[int, str] = {}
        self.next_call = 1
        self.dialog: dict | None = None
        self.dialog_seq = 0
        self.opened_urls: list[dict] = []
        self.notes: list[dict] = []
        self.window_closed = False
        self.csp = _browser_csp((TAURI_DIR / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))
        env = self._sidecar_env(args)
        self.sidecar = SidecarManager(env, self.run_dir / "sidecar-cwd", self.log, self.analyst / "sidecar.log",
                                      self.walk_root)
        self.vault = Path(args.vault).resolve()
        self.create_if_missing = args.create_if_missing

    # The sidecar's environment is built from nothing: no credential, no machine config, no .env in its cwd.
    def _sidecar_env(self, args: argparse.Namespace) -> dict[str, str]:
        for name in ("home", "codex", "config", "tmp", "cache", "sidecar-cwd"):
            (self.run_dir / name).mkdir(parents=True, exist_ok=True)
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "LANG": "C.UTF-8",
            "HOME": str(self.run_dir / "home"),
            "CODEX_HOME": str(self.run_dir / "codex"),
            "LEARNLOOP_CONFIG_DIR": str(self.run_dir / "config"),
            "XDG_CACHE_HOME": str(self.run_dir / "cache"),
            "TMPDIR": str(self.run_dir / "tmp"),
            "PYTHONPATH": str(ROOT / "src"),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        if self.models == "fake":
            env.update(no_network_proxy(self.port))
            base_url = f"http://127.0.0.1:{self.port}/fake-model/v1"
            (self.run_dir / "config" / "ai_defaults.toml").write_text(fake_model.ai_defaults_toml(base_url),
                                                                      encoding="utf-8")
            env["LEARNLOOP_AI_PROVIDER"] = fake_model.FAKE_PROFILE
            env[fake_model.FAKE_KEY_ENV] = "walk-fake-not-a-key"
        else:
            # Live routes: the owner's signed-in walk config directory, nothing else. With no session bus in
            # this environment the plan's tokens must be in that directory's file store, not the OS keyring.
            env["LEARNLOOP_CONFIG_DIR"] = str(Path(args.config_dir).resolve())
            env["LEARNLOOP_CHATGPT_SECRET_STORE"] = "file"
        return env

    def prepare_vault(self) -> None:
        """Point the vault (the walk's own copy) at the walk's models: ``walk_fake``, or back to the plan."""

        if not (self.vault / "learnloop.toml").is_file():
            return
        from learnloop.ops.settings_store import apply_config_updates

        if self.models == "fake":
            apply_config_updates(self.vault / "learnloop.toml",
                                 fake_model.provider_table(f"http://127.0.0.1:{self.port}/fake-model/v1"))
        else:
            # make_vault built it with the fake profile active; a live walk serves the template's plan profile.
            apply_config_updates(self.vault / "learnloop.toml", {("ai", "active_provider"): "chatgpt"})

    def start(self) -> None:
        self.prepare_vault()
        with self.sidecar.lock:
            self.sidecar.initialize(self.vault, create_if_missing=self.create_if_missing)
        self.prepare_vault()
        self.check_routes()
        self.watcher.watch(self.vault)
        self.watcher.start()

    def check_routes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("route_check.py")), str(self.vault),
             fake_model.FAKE_PROFILE],
            env=self.sidecar.env, cwd=self.run_dir / "sidecar-cwd", capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise SystemExit(f"route check failed: {result.stderr[-2000:]}")
        report = json.loads(result.stdout)
        (self.analyst / "routes.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        self.log.write("routes", live=report["live"],
                       kinds={kind: sum(1 for r in report["routes"].values() if r["kind"] == kind)
                              for kind in ("fake", "unset", "unreachable", "live")})
        if self.models == "fake" and report["live"]:
            self.sidecar.stop()
            raise SystemExit("refusing to start: these routes would reach a live model in fake mode: "
                             + ", ".join(report["live"]))

    # -- invoke --------------------------------------------------------------------------------------

    def invoke(self, name: str, args: dict) -> Any:
        command = self.table.get(name)
        if command is None:
            raise CommandFailed(f"Command {name} not found")
        if command.kind == "special":
            if name == "select_vault":
                result = self.sidecar.select_vault(args.get("path"))
                self.vault = self.sidecar.vault or self.vault
                self.watcher.watch(self.vault)
                return result
            if name == "run_cli_command":
                if args.get("input") is None:
                    raise CommandFailed(walk_commands.MissingArgument(name, "input").args[0])
                result = self.sidecar.call("run_cli_command", args["input"])
                argv = [arg for arg in (args["input"].get("argv") or []) if isinstance(arg, str)]
                first = next((arg for arg in argv if arg and arg != "learnloop"), None)
                if first == "populate-goal" and isinstance(result, dict) and result.get("exitCode") == 0:
                    self.sidecar.call("reload_vault", {})
                return result
            raise CommandFailed(f"Command {name} not found")
        try:
            params = command.params_for(args)
        except walk_commands.MissingArgument as exc:
            raise CommandFailed(exc.args[0]) from None
        result = self.sidecar.call(command.method or name, params)
        if command.watches_vault and self.sidecar.vault is not None:
            self.watcher.watch(self.sidecar.vault)
        return result

    def tracked_invoke(self, name: str, args: dict) -> tuple[bool, Any]:
        with self.state_lock:
            call_id = self.next_call
            self.next_call += 1
            self.inflight[call_id] = name
        started = time.monotonic()
        try:
            result = self.invoke(name, args)
            ok, payload = True, result
        except CommandFailed as exc:
            ok, payload = False, exc.error
        except Exception as exc:  # noqa: BLE001 - the bridge itself failed: the frontend sees a task failure
            ok, payload = False, command_error(
                "internal", "LearnLoop could not complete its background task. Restart the app and try again.",
                False, {"diagnostic": f"walk bridge: {type(exc).__name__}: {exc}"})
        finally:
            with self.state_lock:
                self.inflight.pop(call_id, None)
        elapsed = round((time.monotonic() - started) * 1000)
        if ok:
            self.log.write("invoke", command=name, ms=elapsed, ok=True)
        else:
            self.log.write("invoke", command=name, ms=elapsed, ok=False, error=payload,
                           args_keys=sorted(args))
        return ok, payload

    def refresh(self, root: Path, paths: list[str]) -> None:
        try:
            refresh = self.sidecar.call("refresh_vault_files", {"paths": paths, "vaultRoot": str(root)})
        except CommandFailed as exc:
            if isinstance(exc.error, dict) and exc.error.get("code") == "vault_changed":
                return
            error = exc.error if isinstance(exc.error, dict) else {"code": "internal", "message": exc.error}
            refresh = {"error": {key: error.get(key) for key in ("code", "message", "retryable", "details")}}
        self.log.write("vault_files_changed", paths=paths[:50], count=len(paths),
                       mode=refresh.get("mode") if isinstance(refresh, dict) else None)
        self.events.emit(VAULT_FILES_CHANGED, {"root": str(root), "changedPaths": paths, "refresh": refresh})

    # -- the file chooser ----------------------------------------------------------------------------

    def open_dialog(self, options: dict) -> dict:
        with self.state_lock:
            if self.dialog is not None:
                self.log.write("dialog_refused", reason="another chooser is open", options=options)
                return {"paths": None}
            self.dialog_seq += 1
            dialog = {"id": self.dialog_seq, "options": options, "answered": threading.Event(), "paths": None}
            self.dialog = dialog
        self.log.write("dialog_open", id=dialog["id"], options=options)
        while not dialog["answered"].wait(0.5):
            if self.stopping.is_set():
                break
        with self.state_lock:
            if self.dialog is dialog:
                self.dialog = None
        self.log.write("dialog_answer", id=dialog["id"], paths=dialog["paths"])
        return {"paths": dialog["paths"]}

    def answer_dialog(self, dialog_id: int, paths: list[str] | None) -> dict:
        with self.state_lock:
            dialog = self.dialog
            if dialog is None or dialog["id"] != dialog_id:
                raise CommandFailed(command_error("no_dialog", "No file chooser is open.", False))
            if paths is not None:
                resolved = [Path(path).resolve() for path in paths]
                outside = [str(path) for path in resolved if not path.is_relative_to(self.walk_root)]
                if outside:
                    raise CommandFailed(command_error("outside_walk", "Only this person's files can be chosen.",
                                                      False, {"paths": outside}))
                paths = [str(path) for path in resolved]
            dialog["paths"] = paths
            dialog["answered"].set()
        return {"ok": True}

    def state(self) -> dict:
        with self.state_lock:
            dialog = self.dialog
            return {
                "inflight": sorted(set(self.inflight.values())),
                "dialog": None if dialog is None else {"id": dialog["id"], "options": dialog["options"]},
                "opened_urls": list(self.opened_urls),
                "notes": list(self.notes),
                "window_closed": self.window_closed,
                "vault": str(self.sidecar.vault or self.vault),
                "persona_files": str(self.persona_files),
            }

    def note(self, payload: dict) -> None:
        with self.state_lock:
            self.notes.append({"seq": len(self.notes) + 1, **payload})
            if payload.get("kind") == "window" and payload.get("call") == "destroy":
                self.window_closed = True
        self.log.write("shell_note", **payload)

    def open_url(self, url: str) -> None:
        with self.state_lock:
            self.opened_urls.append({"seq": len(self.opened_urls) + 1, "url": url})
        self.log.write("open_url", url=url)

    def stop(self) -> None:
        self.stopping.set()
        self.sidecar.stop()


def no_network_proxy(port: int) -> dict[str, str]:
    """Proxy settings that send any outside request the sidecar makes to the bridge, which refuses it.

    Python's HTTP clients (urllib, requests, httpx with its default trust_env)
    honour these; the model client's own loopback calls are exempt
    (NO_PROXY, and it ignores proxy settings anyway). A walk never fetches a
    web page, a sign-in or a catalogue: the app shows its own error instead,
    and analyst/bridge.jsonl says which host it tried."""

    proxy = f"http://127.0.0.1:{port}"
    return {"HTTP_PROXY": proxy, "HTTPS_PROXY": proxy, "ALL_PROXY": proxy, "http_proxy": proxy,
            "https_proxy": proxy, "all_proxy": proxy, "NO_PROXY": "127.0.0.1,localhost",
            "no_proxy": "127.0.0.1,localhost"}


def _browser_csp(tauri_conf: str) -> str:
    """The app's CSP with its custom schemes mapped onto the bridge's own origin."""

    csp = json.loads(tauri_conf)["app"]["security"]["csp"]
    same_origin = {"tauri://localhost/sketch-frame.html", "http://tauri.localhost/sketch-frame.html", "ipc:",
                   "http://ipc.localhost", "llpdf:", "http://llpdf.localhost", "llmedia:", "http://llmedia.localhost"}
    directives = []
    for directive in csp.split(";"):
        tokens = directive.split()
        if not tokens:
            continue
        name, values = tokens[0], tokens[1:]
        mapped: list[str] = []
        for value in values:
            value = "'self'" if value in same_origin else value
            if value not in mapped:
                mapped.append(value)
        directives.append(" ".join([name, *mapped]))
    return "; ".join(directives)


def inline_script_hashes(html: str) -> list[str]:
    """Tauri hashes each inline script into the CSP; the bridge does the same for the page it serves."""

    hashes = []
    for match in re.finditer(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S):
        digest = base64.b64encode(hashlib.sha256(match.group(1).encode("utf-8")).digest()).decode("ascii")
        hashes.append(f"'sha256-{digest}'")
    return hashes


def csp_with_hashes(csp: str, hashes: list[str]) -> str:
    if not hashes:
        return csp
    parts = []
    for directive in csp.split("; "):
        if directive.startswith("script-src "):
            directive = directive + " " + " ".join(hashes)
        parts.append(directive)
    return "; ".join(parts)


def slice_range(length: int, header: str | None) -> tuple[int, int] | None | bool:
    """main.rs's slice_range: None serves the whole body, False is 416, a pair is the inclusive range."""

    if not header or not header.strip().startswith("bytes="):
        return None
    spec = header.strip()[len("bytes="):]
    if "," in spec or "-" not in spec:
        return None
    start_raw, end_raw = spec.split("-", 1)
    try:
        if not start_raw:
            suffix = int(end_raw)
            if suffix == 0 or length == 0:
                return False
            return max(0, length - suffix), length - 1
        start = int(start_raw)
        end = int(end_raw) if end_raw else max(0, length - 1)
    except ValueError:
        return None
    if start >= length or end < start:
        return False
    return start, min(end, max(0, length - 1))


class Handler(BaseHTTPRequestHandler):
    bridge: Bridge
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:
        return

    # -- plumbing --
    def _body(self) -> Any:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        return json.loads(raw) if raw else {}

    def _send(self, status: int, body: bytes, content_type: str, headers: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, payload: Any, status: int = 200) -> None:
        self._send(status, json.dumps(payload, default=str).encode("utf-8"), "application/json")

    def do_HEAD(self) -> None:  # noqa: N802 - the stdlib's naming
        self.do_GET()

    def do_CONNECT(self) -> None:  # noqa: N802
        self._refuse_outside()

    def _refuse_outside(self) -> None:
        """A proxied request for another host: the walk has no network (no_network_proxy)."""

        self.bridge.log.write("outside_request_refused", method=self.command, target=self.path[:300])
        self._send(403, b"no network on a UX walk", "text/plain")
        self.close_connection = True

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith(("http://", "https://")):
            return self._refuse_outside()
        path = urlsplit(self.path).path
        bridge = self.bridge
        if path == "/__bridge/events":
            return self._events()
        if path == "/__bridge/state":
            return self._json(bridge.state())
        if path.startswith("/__bridge/protocol/"):
            return self._protocol(path)
        if path == "/fake-model/v1/models":
            return self._json({"object": "list", "data": [{"id": fake_model.FAKE_MODEL, "object": "model"}]})
        return self._static(path)

    def do_POST(self) -> None:  # noqa: N802
        if self.path.startswith(("http://", "https://")):
            return self._refuse_outside()
        path = urlsplit(self.path).path
        bridge = self.bridge
        try:
            body = self._body()
        except ValueError:
            return self._json({"ok": False, "error": "invalid JSON"}, 400)
        if path == "/__bridge/invoke":
            ok, payload = bridge.tracked_invoke(str(body.get("command")), body.get("args") or {})
            return self._json({"ok": True, "result": payload} if ok else {"ok": False, "error": payload})
        if path == "/__bridge/dialog/open":
            return self._json({"ok": True, "result": bridge.open_dialog(body)})
        if path == "/__bridge/dialog/answer":
            try:
                result = bridge.answer_dialog(int(body.get("id") or 0), body.get("paths"))
            except CommandFailed as exc:
                return self._json({"ok": False, "error": exc.error})
            return self._json({"ok": True, "result": result})
        if path == "/__bridge/note":
            bridge.note(body if isinstance(body, dict) else {"kind": "note"})
            return self._json({"ok": True, "result": None})
        if path == "/__bridge/open-url":
            bridge.open_url(str(body.get("url")))
            return self._json({"ok": True, "result": None})
        if path == "/fake-model/v1/chat/completions" and bridge.fake is not None:
            try:
                completion, record = bridge.fake.answer(body)
            except fake_model.Declined as exc:
                bridge.log.write("fake_model", schema=str(exc), declined=True)
                return self._json({"error": {"message": f"walk fake model declines {exc}", "type": "invalid_request_error",
                                             "code": "walk_fake_declined"}}, 400)
            bridge.log.write("fake_model", **record)
            return self._json(completion)
        return self._json({"ok": False, "error": "not found"}, 404)

    def _events(self) -> None:
        subscriber = self.bridge.events.subscribe()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        try:
            while not self.bridge.stopping.is_set():
                try:
                    data = subscriber.get(timeout=15)
                    self.wfile.write(f"data: {data}\n\n".encode("utf-8"))
                except queue.Empty:
                    self.wfile.write(b": keep-alive\n\n")
                self.wfile.flush()
        except OSError:
            pass
        finally:
            self.bridge.events.unsubscribe(subscriber)
            self.close_connection = True

    def _protocol(self, path: str) -> None:
        parts = path.split("/", 4)
        if len(parts) != 5:
            return self._send(404, b"not found", "text/plain")
        protocol, name = parts[3], unquote(parts[4])
        vault = self.bridge.sidecar.vault or self.bridge.vault
        if protocol == "llpdf":
            if not CONTENT_ADDRESSED.match(name):
                return self._send(400, b"invalid store name", "application/pdf")
            target = vault / "canonical-sources" / "raw" / name
            try:
                body = target.read_bytes()
            except OSError:
                return self._send(404, b"not in originals store", "application/pdf")
            return self._send(200, body, "application/pdf")
        if protocol == "llmedia":
            stem = name[: -len(".mp4")] if name.endswith(".mp4") else ""
            if not CONTENT_ADDRESSED.match(stem):
                return self._send(400, b"invalid animation name", "video/mp4")
            target = vault / "media" / "animations" / name
            try:
                data = target.read_bytes()
            except OSError:
                return self._send(404, b"not in animation store", "video/mp4")
            span = slice_range(len(data), self.headers.get("Range"))
            if span is None:
                return self._send(200, data, "video/mp4", {"Accept-Ranges": "bytes"})
            if span is False:
                return self._send(416, b"", "video/mp4", {"Content-Range": f"bytes */{len(data)}"})
            start, end = span  # type: ignore[misc]
            end = min(end, start + MAX_MEDIA_RANGE - 1)
            return self._send(206, data[start:end + 1], "video/mp4",
                              {"Accept-Ranges": "bytes", "Content-Range": f"bytes {start}-{end}/{len(data)}"})
        return self._send(404, b"protocol not available in browser mode", "text/plain")

    def _static(self, path: str) -> None:
        bundle = self.bridge.bundle
        relative = "index.html" if path in ("", "/") else path.lstrip("/")
        target = (bundle / unquote(relative)).resolve()
        if not target.is_relative_to(bundle) or not target.is_file():
            return self._send(404, b"not found", "text/plain")
        body = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        headers = {}
        if target.suffix == ".html":
            headers["Content-Security-Policy"] = csp_with_hashes(
                self.bridge.csp, inline_script_hashes(body.decode("utf-8")))
            content_type = "text/html; charset=utf-8"
        if target.suffix in (".js", ".mjs"):
            content_type = "text/javascript"
        if target.suffix == ".wasm":
            content_type = "application/wasm"
        return self._send(200, body, content_type, headers)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--walk-root", required=True)
    parser.add_argument("--vault", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--bundle", default=str(DEFAULT_BUNDLE))
    parser.add_argument("--create-if-missing", action="store_true",
                        help="create the library on first launch, as the shell does for ~/LearnLoop")
    parser.add_argument("--models", choices=("fake", "live"), default="fake")
    parser.add_argument("--allow-live-route", action="store_true",
                        help="required with --models live: the walk may spend on the owner's model routes")
    parser.add_argument("--config-dir", help="with --models live: the signed-in LearnLoop config directory to use")
    args = parser.parse_args(argv)
    if args.models == "live" and not (args.allow_live_route and args.config_dir):
        parser.error("--models live needs --allow-live-route and --config-dir (the owner decides at launch)")
    walk_root = Path(args.walk_root).resolve()
    if not Path(args.vault).resolve().is_relative_to(walk_root):
        parser.error("the vault must be inside the walk directory (a walk never opens an owner's vault)")
    bridge = Bridge(args)
    Handler.bridge = bridge
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()

    def stop(_signum: int, _frame: Any) -> None:
        bridge.stopping.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        bridge.start()
    except SystemExit as exc:
        bridge.log.write("bridge_refused", reason=str(exc))
        bridge.stop()
        server.shutdown()
        print(str(exc), file=sys.stderr)
        return 3
    except CommandFailed as exc:
        bridge.log.write("bridge_start_failed", error=exc.error)
        bridge.stop()
        server.shutdown()
        print(f"sidecar did not start: {exc.error}", file=sys.stderr)
        return 4
    (walk_root / "run" / "bridge.ready").write_text(json.dumps({"port": args.port, "pid": os.getpid()}),
                                                     encoding="utf-8")
    bridge.log.write("bridge_ready", port=args.port, commands=walk_commands.counts(bridge.table))
    while not bridge.stopping.wait(0.5):
        pass
    bridge.stop()
    server.shutdown()
    bridge.log.write("bridge_stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
