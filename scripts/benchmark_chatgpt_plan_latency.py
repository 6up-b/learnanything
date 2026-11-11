"""LearnLoop-side latency of the ChatGPT-plan transport, with fakes only.

Run with `uv run python scripts/benchmark_chatgpt_plan_latency.py --calls 50`.

Nothing leaves the machine and no real credential is read: the sign-in and
the Responses stream are the local fakes from `tests/chatgpt_plan_fakes.py`,
under a temporary LEARNLOOP_CONFIG_DIR. The fake answers instantly, so the
number is the transport's own overhead, not model time: the real
`ChatGPTPlanProviderClient` (token read, one HTTP request to 127.0.0.1, SSE
parse, validation, receipts off). Only a real call (`learnloop ai latency`)
measures the model. (The Codex comparison this script also ran left with the
Codex transport, refactor C4.)
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


def _summary(samples: list[float]) -> dict[str, float]:
    ordered = sorted(samples)
    return {
        "calls": len(ordered),
        "median_ms": round(statistics.median(ordered) * 1000, 2),
        "p95_ms": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))] * 1000, 2),
        "min_ms": round(ordered[0] * 1000, 2),
        "max_ms": round(ordered[-1] * 1000, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--calls", type=int, default=50)
    args = parser.parse_args()

    scratch = Path(tempfile.mkdtemp(prefix="learnloop-latency-"))
    os.environ["LEARNLOOP_CONFIG_DIR"] = str(scratch / "config")
    os.environ["LEARNLOOP_CHATGPT_SECRET_STORE"] = "file"

    from learnloop.ai.chatgpt_plan.session import PlanSession
    from learnloop.ai.providers.chatgpt_plan import ChatGPTPlanProviderClient
    from learnloop.ai.schemas import WireModel
    from learnloop.ai.transport import execute_structured_operation
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

    shutil.rmtree(scratch, ignore_errors=True)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
