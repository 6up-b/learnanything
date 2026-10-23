"""Frozen round of the Codex tool lockdown (orchestrator verify 20261021-140119-uuB5X5, High 3).

A legacy ``notify`` command inherited from the user's Codex configuration runs
after every turn with the turn's input messages and final answer, outside the
turn's sandbox and with the app server's whole environment (codex-cli 0.163.0
``hooks/src/legacy_notify.rs``), whatever ``features.hooks`` says. Every launch
now clears it with ``notify=[]``.

The regression runs a real turn on the installed CLI against a local stand-in
for the Responses API (a thread in this process on 127.0.0.1): no model, no
network beyond the loopback, no credentials.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from learnloop.ai.providers.codex import isolated_turn_overrides

CODEX = shutil.which("codex")
needs_codex = pytest.mark.skipif(CODEX is None, reason="the Codex CLI is not installed")
CANARY = "LLCANARY-frozen-notify-learner-text"


class _FakeResponses(BaseHTTPRequestHandler):
    """Every POST streams one final assistant message, then completes."""

    requests: list[str] = []

    def log_message(self, *_args):
        return None

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(length)
        type(self).requests.append(self.path)
        events = [
            {"type": "response.created", "response": {"id": "resp_fake"}},
            {"type": "response.output_item.done",
             "item": {"type": "message", "role": "assistant", "id": "msg_1", "phase": "final_answer",
                      "content": [{"type": "output_text", "text": '{"links": []}'}]}},
            {"type": "response.completed",
             "response": {"id": "resp_fake", "usage": {"input_tokens": 10, "input_tokens_details": {"cached_tokens": 0},
                                                       "output_tokens": 5,
                                                       "output_tokens_details": {"reasoning_tokens": 0},
                                                       "total_tokens": 15}}},
        ]
        body = "".join(f"event: {event['type']}\ndata: {json.dumps(event)}\n\n" for event in events).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture()
def fake_responses():
    _FakeResponses.requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeResponses)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    finally:
        server.shutdown()
        server.server_close()


def _turn(tmp_path: Path, base_url: str, overrides: list[str]) -> Path:
    """One turn of the installed CLI under ``overrides`` whose user config has a notifier; returns its marker."""

    home, codex_home, turn = tmp_path / "home", tmp_path / "codex-home", tmp_path / "turn"
    for path in (home, codex_home, turn):
        path.mkdir(exist_ok=True)
    marker = tmp_path / "NOTIFIED"
    notifier = tmp_path / "notify.sh"
    notifier.write_text(f'#!/bin/sh\nprintf "%s" "$@" > {marker}\n', encoding="utf-8")
    notifier.chmod(0o755)
    (codex_home / "config.toml").write_text(f"notify = [{json.dumps(str(notifier))}]\n", encoding="utf-8")
    provider = ['model_provider="fake"', 'model_providers.fake.name="fake"',
                f"model_providers.fake.base_url={json.dumps(base_url)}", 'model_providers.fake.wire_api="responses"',
                'model_providers.fake.env_key="LL_FAKE_PROVIDER_KEY"', 'model="gpt-5.6-sol"']
    args = [CODEX]
    for override in [*overrides, *provider]:
        args += ["-c", override]
    environ = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home), "CODEX_HOME": str(codex_home),
               "LL_FAKE_PROVIDER_KEY": "synthetic"}
    done = subprocess.run([*args, "exec", "--skip-git-repo-check", f"Answer {CANARY}"], cwd=turn, env=environ,
                          stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr[-2000:]
    return marker


def test_every_launch_clears_the_legacy_notifier(tmp_path):
    overrides = isolated_turn_overrides(tmp_path, shell=False)
    assert "notify=[]" in overrides


@needs_codex
def test_an_inherited_notifier_cannot_run_after_a_locked_down_turn(tmp_path, fake_responses):
    """High 3 on the installed binary: the turn completes, and the user's
    notifier never runs, so the learner's text never reaches it."""

    turn = tmp_path / "turn"
    turn.mkdir()
    marker = _turn(tmp_path, fake_responses, isolated_turn_overrides(turn, shell=False))
    assert _FakeResponses.requests, "the turn never reached the stand-in"
    time.sleep(1.0)  # the notifier is spawned after the turn, without being awaited
    assert not marker.exists(), "an inherited notifier ran with the turn's text"
    # The control: the same turn without `notify=[]` runs it with the learner's text.
    control = [override for override in isolated_turn_overrides(turn, shell=False) if override != "notify=[]"]
    marker = _turn(tmp_path, fake_responses, control)
    for _ in range(50):
        if marker.exists():
            break
        time.sleep(0.1)
    assert marker.exists() and CANARY in marker.read_text(encoding="utf-8")
