"""LearnLoop-side latency of the ChatGPT-plan transport vs Codex, with fakes only.

Run with `uv run python scripts/benchmark_chatgpt_plan_latency.py --calls 50`.

Nothing leaves the machine and no real credential is read: the sign-in and
the Responses stream are the local fakes from `tests/chatgpt_plan_fakes.py`,
under a temporary LEARNLOOP_CONFIG_DIR. Both paths answer instantly, so the
numbers are each transport's own overhead, not model time:

* `chatgpt_plan`: the real `ChatGPTPlanProviderClient` (token read, one HTTP
  request to 127.0.0.1, SSE parse, validation, receipts off).
* `codex_sdk (fake app-server)`: the real `SdkCodexClient` with a stand-in SDK
  whose `Codex(...)` starts a child process per call and does the JSON-RPC
  handshake, thread start and turn over its pipes, as the real SDK does with
  `codex app-server`. The child is a tiny Python program, so this is a lower
  bound on what spawning the real app-server costs.
* `codex --version`: the installed Codex binary's bare exec time, when one is
  on PATH (it reads no credentials). The real app-server also loads its
  config, auth and MCP servers before the first turn; only a real call
  (`learnloop ai latency`) measures that.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from types import ModuleType, SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

APP_SERVER_STUB = r"""
import json, sys
for line in sys.stdin:
    message = json.loads(line)
    if message["method"] == "shutdown":
        break
    result = {"final_response": json.dumps({"ok": True, "note": "fake"})} if message["method"] == "turn" else {}
    sys.stdout.write(json.dumps({"id": message["id"], "result": result}) + "\n")
    sys.stdout.flush()
"""


def _summary(samples: list[float]) -> dict[str, float]:
    ordered = sorted(samples)
    return {
        "calls": len(ordered),
        "median_ms": round(statistics.median(ordered) * 1000, 2),
        "p95_ms": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))] * 1000, 2),
        "min_ms": round(ordered[0] * 1000, 2),
        "max_ms": round(ordered[-1] * 1000, 2),
    }


def _install_fake_codex_sdk() -> None:
    class FakeCodex:
        def __init__(self, config):
            from tests.codex_cli_fakes import FakeSdkClient

            self._process: subprocess.Popen | None = None
            self._id = 0
            self._client = FakeSdkClient()  # the seams the locked-down turn replaces

        def _call(self, method: str) -> dict:
            assert self._process is not None and self._process.stdin and self._process.stdout
            self._id += 1
            self._process.stdin.write(json.dumps({"id": self._id, "method": method}) + "\n")
            self._process.stdin.flush()
            return json.loads(self._process.stdout.readline())["result"]

        def __enter__(self):
            self._process = subprocess.Popen([sys.executable, "-c", APP_SERVER_STUB], stdin=subprocess.PIPE,
                                             stdout=subprocess.PIPE, text=True)
            self._call("initialize")
            return self

        def __exit__(self, *_args):
            assert self._process is not None and self._process.stdin
            self._process.stdin.write(json.dumps({"id": 0, "method": "shutdown"}) + "\n")
            self._process.stdin.flush()
            self._process.wait(timeout=10)

        def close(self):
            return None

        def thread_start(self, **_kwargs):
            self._call("thread/start")
            codex = self

            class Thread:
                def turn(self, _prompt, **_kwargs):
                    class Turn:
                        def run(self):
                            result = codex._call("turn")
                            return SimpleNamespace(final_response=result["final_response"], usage=None)

                        def interrupt(self):
                            return None

                    return Turn()

            return Thread()

    class SdkAppConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class ReasoningSummary:
        @classmethod
        def model_validate(cls, value):
            return value

    from enum import Enum

    class ReasoningEffort(Enum):
        low = "low"
        medium = "medium"

    sdk = ModuleType("openai_codex")
    sdk.Codex = FakeCodex  # type: ignore[attr-defined]
    from tests.codex_cli_fakes import FakeApprovalMode

    sdk.ApprovalMode = FakeApprovalMode  # type: ignore[attr-defined]
    sdk.CodexConfig = SdkAppConfig  # type: ignore[attr-defined]
    types = ModuleType("openai_codex.types")
    types.Personality = SimpleNamespace(pragmatic="pragmatic")  # type: ignore[attr-defined]
    types.ReasoningEffort = ReasoningEffort  # type: ignore[attr-defined]
    types.ReasoningSummary = ReasoningSummary  # type: ignore[attr-defined]
    sys.modules["openai_codex"] = sdk
    sys.modules["openai_codex.types"] = types


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--calls", type=int, default=50)
    args = parser.parse_args()

    scratch = Path(tempfile.mkdtemp(prefix="learnloop-latency-"))
    os.environ["LEARNLOOP_CONFIG_DIR"] = str(scratch / "config")
    os.environ["LEARNLOOP_CHATGPT_SECRET_STORE"] = "file"

    from learnloop.ai.chatgpt_plan.session import PlanSession
    from learnloop.ai.providers.chatgpt_plan import ChatGPTPlanProviderClient
    from learnloop.ai.providers.codex import SdkCodexClient
    from learnloop.ai.schemas import WireModel
    from learnloop.ai.transport import execute_structured_operation
    from learnloop.config.compat import CodexConfig
    from learnloop.config.schema import ChatGPTPlanProviderConfig
    from tests.chatgpt_plan_fakes import Reply, completed_events, fake_chatgpt, sign_in

    class Answer(WireModel):
        ok: bool
        note: str

    def timed(client) -> float:
        started = time.perf_counter()
        answer = execute_structured_operation(client, purpose="latency", prompt="Say ok", result_model=Answer)
        assert answer.ok
        return time.perf_counter() - started

    results: dict[str, object] = {"python": sys.version.split()[0], "platform": sys.platform}
    with fake_chatgpt() as server:
        sign_in(PlanSession(), server)
        client = ChatGPTPlanProviderClient("chatgpt", ChatGPTPlanProviderConfig(
            model="gpt-test-fast", base_url=server.base_url, timeout_seconds=30))
        server.replies.append(Reply(events=completed_events('{"ok": true, "note": "fake"}')))
        timed(client)  # warm-up
        samples = []
        for _ in range(args.calls):
            server.replies.append(Reply(events=completed_events('{"ok": true, "note": "fake"}')))
            samples.append(timed(client))
        results["chatgpt_plan"] = _summary(samples)

    _install_fake_codex_sdk()
    codex = SdkCodexClient(CodexConfig(checkout_path=str(scratch / "codex")), scratch)
    # The launch check runs real `codex` probes once per process and config
    # (then cached); the fake app server is what this measures, so it is
    # answered in process.
    from tests.codex_cli_fakes import stub_isolation_probe

    class _Patch:  # stub_isolation_probe's monkeypatch, outside pytest
        @staticmethod
        def setattr(target, name, value):
            setattr(target, name, value)

    stub_isolation_probe(_Patch(), codex)
    timed(codex)
    results["codex_sdk_fake_app_server"] = _summary([timed(codex) for _ in range(max(10, args.calls // 2))])

    binary = shutil.which("codex")
    if binary:
        samples = []
        for _ in range(10):
            started = time.perf_counter()
            subprocess.run([binary, "--version"], capture_output=True, check=False, timeout=30)
            samples.append(time.perf_counter() - started)
        results["codex_binary_version_exec"] = _summary(samples)
    shutil.rmtree(scratch, ignore_errors=True)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
