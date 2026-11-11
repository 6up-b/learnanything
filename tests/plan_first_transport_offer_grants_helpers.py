"""What other test files use from ``tests/test_plan_first_transport_offer_grants.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import sys
import threading
import traceback
from typing import Any, Callable

import pytest

from learnloop.ai import plan_fallback
from learnloop.ai.routing import ready_client_for_task

from tests.openai_fakes import install_fake_openai
from tests.plan_first_transport_paid_roles_helpers import _priced_vault


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))  # the plan is signed out
    for name in ("LEARNLOOP_AI_PROVIDER", "LEARNLOOP_AI_FALLBACK", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    plan_fallback.revoke_all()
    yield
    plan_fallback.revoke_all()


@pytest.fixture
def fake_openai(monkeypatch):
    fake = install_fake_openai(monkeypatch)
    yield fake
    assert all(instance.requests == [] for instance in fake.instances)  # built at most, never called


class Harness:
    """A vault, a sidecar context, an ingest runner with a probe job, and stub RPCs."""

    def __init__(self, tmp_path, monkeypatch) -> None:
        import learnloop_sidecar.handlers  # noqa: F401
        from learnloop.config import load_config
        from learnloop.content.pipeline.runner import IngestRunner
        from learnloop.db.repositories import Repository
        from learnloop.vault.paths import VaultPaths
        from learnloop_sidecar.context import SidecarContext

        self.monkeypatch = monkeypatch
        self.root = _priced_vault(tmp_path)
        self.ctx = SidecarContext()
        self.ctx.load(self.root, maintenance=False)
        paths = VaultPaths(self.root, load_config(self.root / "learnloop.toml"))
        self.seen: dict[str, bool] = {}
        self.runner = IngestRunner(Repository.attach(paths.sqlite_path), vault_root=self.root,
                                   worker_id="t1-landing-d", handlers={"t1_probe": self._probe})

    def _probe(self, job_ctx) -> dict[str, Any]:
        task = str((job_ctx.job.get("payload") or {}).get("task") or "canonical_ingest")
        self.seen[job_ctx.job["batch_id"]] = plan_fallback.is_granted(task, job_ctx.vault_root)
        return {}

    def stub(self, method: str, *, resolve: str | None = None, enqueue: bool = False,
             work: Callable[[Any], Any] | None = None) -> None:
        from learnloop.content.pipeline.runner import JobSpec
        from learnloop_sidecar.dto import EmptyParams
        from learnloop_sidecar.errors import SidecarError
        from learnloop_sidecar.registry import METHOD_REGISTRY, MethodSpec

        def handler(ctx, _params) -> dict[str, Any]:
            out: dict[str, Any] = {}
            if enqueue:
                out["batch"] = self.runner.enqueue_batch(
                    "t1_landing_d", [JobSpec(job_type="t1_probe", payload={"task": resolve or "canonical_ingest"})])
            if work is not None:
                out["work"] = work(ctx)
            if resolve is not None:
                loaded, _repository = ctx.require_vault()
                resolved = ready_client_for_task(loaded.root, loaded.config, resolve)  # type: ignore[arg-type]
                out["provider"] = resolved.provider_name
                if not resolved.ready:
                    raise SidecarError("ai_unavailable", resolved.runtime.message or "unavailable",
                                       details={"out": out})
            return out

        self.monkeypatch.setitem(METHOD_REGISTRY, method, MethodSpec(method, EmptyParams, handler))

    def call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        from learnloop_sidecar.server import _handle

        return _handle(self.ctx, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}})

    @staticmethod
    def hint(response: dict[str, Any]) -> dict[str, Any] | None:
        details = ((response.get("error") or {}).get("data") or {}).get("details") or {}
        if "fallback_available" in details:
            return details
        result = response.get("result") or {}
        return result if "fallbackAvailable" in result else None

    @staticmethod
    def out(response: dict[str, Any]) -> dict[str, Any]:
        details = ((response.get("error") or {}).get("data") or {}).get("details") or {}
        return details.get("out") or response.get("result") or {}

    def answer(self, response: dict[str, Any]) -> dict[str, Any]:
        """The learner's "Use OpenRouter instead" on this response's banner."""

        hint = self.hint(response)
        assert hint is not None, response
        offer_id = hint.get("fallback_offer_id") or hint.get("fallbackOfferId")
        if offer_id:
            params: dict[str, Any] = {"provider": "openrouter", "offerId": offer_id}
        else:  # the round-2 API
            params = {"provider": "openrouter", "tasks": list(hint.get("fallback_tasks") or hint.get("fallbackTasks"))}
        answered = self.call("ai_use_fallback", params)
        assert "result" in answered, answered
        return answered

    def stop(self) -> None:
        assert "result" in self.call("ai_use_fallback", {"provider": "openrouter", "stop": True})

    def drain(self) -> None:
        """Run every queued job on a worker thread, as the sidecar's ingest worker does: off any request.

        Load-robust (Oct 27 flake: at load ~17 P1's ~900 jobs overran a 60 s join, the test read
        ``seen`` before the drain had run and the thread guard caught the drain still running). No
        timing decides the outcome: the worker drains until no job of this runner is queued or
        running (a claim the vault lock deferred is retried).

        A drain that never ends fails, bounded (review F1): past the hang guard the worker is told to
        stop after its current chunk, and every batch with a job still pending is cancelled through
        the runner's own cancellation, which a running handler reads at its checkpoints (the path the
        sidecar's Cancel takes). The worker then gets a bounded grace to return. A job blocked where
        no cancellation reaches it (a thread cannot be killed) fails the drain naming the worker's
        stack instead of joining it forever; the thread guard then reports the survivor too."""

        stop = threading.Event()

        def pending() -> list[dict[str, Any]]:
            return [job for job in self.runner.repo.ingest_jobs_by_types(tuple(self.runner.handlers))
                    if job["status"] in ("queued", "running")]

        def work() -> None:
            while not stop.is_set() and (self.runner.drain(max_jobs=_DRAIN_CHUNK) or pending()):
                pass

        thread = threading.Thread(target=work, name="t1-landing-d-drain", daemon=True)
        thread.start()
        thread.join(_DRAIN_HANG_GUARD_S)
        if not thread.is_alive():
            assert pending() == []
            return
        stop.set()
        for batch_id in sorted({job["batch_id"] for job in pending()}):
            self.runner.cancel_batch(batch_id)
        thread.join(_DRAIN_STOP_GRACE_S)
        if thread.is_alive():
            frame = sys._current_frames().get(thread.ident or -1)
            where = "".join(traceback.format_stack(frame)) if frame is not None else "(no frame)"
            raise AssertionError(
                f"the drain did not finish within {_DRAIN_HANG_GUARD_S} s, and its worker is still running "
                f"{_DRAIN_STOP_GRACE_S} s after its jobs were cancelled; it is blocked at:\n{where}")
        raise AssertionError(
            f"the drain did not finish within {_DRAIN_HANG_GUARD_S} s; its pending jobs were cancelled")


#: keep: a hang guard, not a pass/fail timing; a drain this long means it is stuck, not slow.
_DRAIN_HANG_GUARD_S = 900
#: keep: how long a stuck drain's worker gets to return once its jobs are cancelled (a cleanup
#: bound: a handler honours a cancel at its next checkpoint, so a worker still running after this
#: is blocked where no cancel reaches it).
_DRAIN_STOP_GRACE_S = 60
#: keep: how many jobs the drain runs between stop checks (any positive size checks the same).
_DRAIN_CHUNK = 25
