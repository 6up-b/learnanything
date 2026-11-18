"""The phone walk's front door: the real phone host (learnloop_mobile) behind a loopback proxy.

The host only answers requests that arrive through Tailscale Serve: the
``Host`` and ``Origin`` of its tailnet name and the owner's
``Tailscale-User-Login``. A walk has no tailnet, so this proxy adds exactly
those three to every request from the walk's browser and changes nothing
else. It starts the host on a walk-only ``mobile.toml``, pairs one device for
the app (the QR code a phone would scan becomes the URL the driver opens), and
serves the walk driver's state and, in fake-model mode, the fake chat endpoint.

    python scripts/ux_walk/phone_proxy.py --walk-root <walk> --vault <path> --port <n>
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fake_model  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HOSTNAME = "walk-phone.ts.net"
OWNER = "walker@example.invalid"
HOP_BY_HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers",
              "transfer-encoding", "upgrade", "host", "origin", "referer", "content-length"}


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def walk_env(run_dir: Path, port: int) -> dict[str, str]:
    for name in ("home", "codex", "config", "tmp", "cache"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    base_url = f"http://127.0.0.1:{port}/fake-model/v1"
    (run_dir / "config" / "ai_defaults.toml").write_text(fake_model.ai_defaults_toml(base_url), encoding="utf-8")
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8", "HOME": str(run_dir / "home"),
        "CODEX_HOME": str(run_dir / "codex"), "LEARNLOOP_CONFIG_DIR": str(run_dir / "config"),
        "XDG_CACHE_HOME": str(run_dir / "cache"), "TMPDIR": str(run_dir / "tmp"), "PYTHONPATH": str(ROOT / "src"),
        "PYTHONDONTWRITEBYTECODE": "1", "LEARNLOOP_AI_PROVIDER": fake_model.FAKE_PROFILE,
        **{name: f"http://127.0.0.1:{port}" for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy",
                                                         "https_proxy", "all_proxy")},
        "NO_PROXY": "127.0.0.1,localhost", "no_proxy": "127.0.0.1,localhost",
        fake_model.FAKE_KEY_ENV: "walk-fake-not-a-key",
    }


class Proxy:
    def __init__(self, args: argparse.Namespace):
        self.walk_root = Path(args.walk_root).resolve()
        self.run_dir = self.walk_root / "run"
        self.analyst = self.walk_root / "analyst"
        self.analyst.mkdir(parents=True, exist_ok=True)
        self.vault = Path(args.vault).resolve()
        self.port = args.port
        self.host_port = free_port()
        self.env = walk_env(self.run_dir, self.port)
        self.fake = fake_model.FakeModel()
        self.lock = threading.Lock()
        self.inflight = 0
        self.process: subprocess.Popen | None = None
        self.stopping = threading.Event()
        self.log_path = self.analyst / "bridge.jsonl"

    def log(self, kind: str, **fields: Any) -> None:
        with self.lock, self.log_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"t": round(time.time(), 3), "kind": kind, **fields}, default=str) + "\n")

    def config(self) -> Path:
        path = self.run_dir / "mobile.toml"
        path.write_text(
            "enabled = true\n"
            f'vault = "{self.vault}"\n'
            f'hostname = "{HOSTNAME}"\n'
            f'owner_login = "{OWNER}"\n'
            f"port = {self.host_port}\n"
            f'page_cache_dir = "{self.run_dir / "cache" / "mobile-pages"}"\n', encoding="utf-8")
        return path

    def start(self) -> str:
        from learnloop.ops.settings_store import apply_config_updates

        apply_config_updates(self.vault / "learnloop.toml",
                             fake_model.provider_table(f"http://127.0.0.1:{self.port}/fake-model/v1"))
        config = self.config()
        output = (self.analyst / "phone_host.log").open("ab")
        self.process = subprocess.Popen([sys.executable, "-m", "learnloop_mobile", "serve", "--config", str(config)],
                                        cwd=self.run_dir, env=self.env, stdout=output, stderr=output)
        deadline = time.monotonic() + 90
        while True:
            try:
                status, _, _ = self.forward("GET", "/healthz", {}, b"")
                if status == 200:
                    break
            except OSError:
                pass
            if self.process.poll() is not None or time.monotonic() > deadline:
                raise SystemExit("the phone host did not start (see analyst/phone_host.log)")
            time.sleep(0.3)
        paired = subprocess.run(
            [sys.executable, "-m", "learnloop_mobile", "pair", "--config", str(config), "--scope", "app",
             "--label", "Walk phone"], cwd=self.run_dir, env=self.env, capture_output=True, text=True, timeout=60)
        match = re.search(r"/pair#s=([^\s]+)", paired.stdout)
        if paired.returncode != 0 or match is None:
            raise SystemExit(f"pairing failed: {paired.stderr[-500:]}")
        self.log("phone_paired")
        return f"/pair#s={match.group(1)}"

    def forward(self, method: str, path: str, headers: dict[str, str], body: bytes) -> tuple[int, list, bytes]:
        connection = http.client.HTTPConnection("127.0.0.1", self.host_port, timeout=300)
        outgoing = {name: value for name, value in headers.items() if name.lower() not in HOP_BY_HOP}
        outgoing["Host"] = HOSTNAME
        outgoing["Tailscale-User-Login"] = OWNER
        if any(name.lower() == "origin" for name in headers):
            outgoing["Origin"] = f"https://{HOSTNAME}"
        if body:
            outgoing["Content-Length"] = str(len(body))
        connection.request(method, path, body=body or None, headers=outgoing)
        response = connection.getresponse()
        data = response.read()
        result = (response.status, response.getheaders(), data)
        connection.close()
        return result

    def stop(self) -> None:
        self.stopping.set()
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.process.kill()


class Handler(BaseHTTPRequestHandler):
    proxy: Proxy
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _reply(self, status: int, headers: list, body: bytes) -> None:
        self.send_response(status)
        for name, value in headers:
            if name.lower() not in HOP_BY_HOP:
                self.send_header(name, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_CONNECT(self) -> None:  # noqa: N802 - the stdlib's naming
        self.proxy.log("outside_request_refused", method="CONNECT", target=self.path[:300])
        self._reply(403, [("Content-Type", "text/plain")], b"no network on a UX walk")
        self.close_connection = True

    def _handle(self) -> None:
        proxy = self.proxy
        if self.path.startswith(("http://", "https://")):
            proxy.log("outside_request_refused", method=self.command, target=self.path[:300])
            return self._reply(403, [("Content-Type", "text/plain")], b"no network on a UX walk")
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        if self.path == "/__bridge/state":
            with proxy.lock:
                busy = proxy.inflight
            payload = {"inflight": ["phone host"] * busy, "dialog": None, "opened_urls": [], "notes": [],
                       "window_closed": False}
            return self._reply(200, [("Content-Type", "application/json")], json.dumps(payload).encode())
        if self.path == "/fake-model/v1/chat/completions" and self.command == "POST":
            try:
                completion, record = proxy.fake.answer(json.loads(body or b"{}"))
            except fake_model.Declined as exc:
                proxy.log("fake_model", schema=str(exc), declined=True)
                error = {"error": {"message": f"walk fake model declines {exc}", "type": "invalid_request_error"}}
                return self._reply(400, [("Content-Type", "application/json")], json.dumps(error).encode())
            proxy.log("fake_model", **record)
            return self._reply(200, [("Content-Type", "application/json")], json.dumps(completion).encode())
        with proxy.lock:
            proxy.inflight += 1
        started = time.monotonic()
        try:
            status, headers, data = proxy.forward(self.command, self.path, dict(self.headers.items()), body)
        except OSError as exc:
            status, headers, data = 502, [("Content-Type", "text/plain")], f"phone host unreachable: {exc}".encode()
        finally:
            with proxy.lock:
                proxy.inflight -= 1
        if self.path.startswith(("/rpc", "/api/", "/pair")):
            proxy.log("invoke", command=f"{self.command} {self.path.split('?')[0]}", ok=status < 400, status=status,
                      ms=round((time.monotonic() - started) * 1000))
        self._reply(status, headers, data)

    do_GET = do_POST = do_HEAD = do_PUT = do_DELETE = _handle  # noqa: N815


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--walk-root", required=True)
    parser.add_argument("--vault", required=True)
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args(argv)
    if not Path(args.vault).resolve().is_relative_to(Path(args.walk_root).resolve()):
        parser.error("the vault must be inside the walk directory")
    proxy = Proxy(args)
    Handler.proxy = proxy
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    signal.signal(signal.SIGTERM, lambda *_: proxy.stopping.set())
    signal.signal(signal.SIGINT, lambda *_: proxy.stopping.set())
    try:
        pair_path = proxy.start()
    except SystemExit as exc:
        proxy.stop()
        server.shutdown()
        print(str(exc), file=sys.stderr)
        return 3
    (proxy.run_dir / "bridge.ready").write_text(json.dumps({"port": args.port, "pid": os.getpid(),
                                                            "start_path": pair_path}), encoding="utf-8")
    while not proxy.stopping.wait(0.5):
        if proxy.process is not None and proxy.process.poll() is not None:
            proxy.log("phone_host_exited", code=proxy.process.returncode)
            break
    proxy.stop()
    server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
