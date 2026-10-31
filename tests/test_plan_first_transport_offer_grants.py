"""Plan-first transport T1, landing redesign D (owner Q1-Q3, 2026-10-23): the offer is the grant.

"Use OpenRouter instead" answers one offer, and the offer names the action
that asked: the RPC method whose request raised it (for an offer relayed from
a job, the job's starting method, never the poll's). The answer grants that
action for the session (Q1: including the times LearnLoop runs it by itself),
and gives a token to the units of work the offer lists. OpenRouter then serves
only in a request of a granted method, or in a unit created by one (or named
by the answered offer), and only while the vault's epoch is the one the grant
was given in: "Stop using OpenRouter" bumps it, so no captured token revives.
No sender table, no task table, no resume classification.

Every scenario is driven through the sidecar's real dispatch
(``server._handle``) with stub handlers registered under real method names,
so it runs on the round-2 tree too (``_answer`` uses the offer id when the
hint has one, else the round-2 task list): Codex's five round-3 scenarios
(S1-S5) fail there and pass here. Nothing is sent; no test leaves 127.0.0.1.
"""
from __future__ import annotations

import os
import sys
import threading
import time
import traceback
from typing import Any, Callable

import pytest

from learnloop.ai import plan_fallback
from learnloop.ai.routing import ready_client_for_task

from tests.openai_fakes import install_fake_openai
from tests.test_plan_first_transport_paid_roles import _priced_vault


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


class _OsWithoutFsync:
    """``os`` for the vault lock without the holder file's fsync (crash diagnostics these tests never
    read): P1 takes the lock twice per job, ~1800 fsyncs, the slowest I/O of the drain under load."""

    def __getattr__(self, name: str) -> Any:
        return getattr(os, name)

    @staticmethod
    def fsync(_fd: int) -> None:
        return None


@pytest.fixture
def harness(tmp_path, monkeypatch, fake_openai):
    from learnloop import vault_lock

    monkeypatch.setattr(vault_lock, "os", _OsWithoutFsync())
    return Harness(tmp_path, monkeypatch)


# -- Codex's five round-3 scenarios (fail on b5d8e0f01) -----------------------------------------


def test_s1_a_build_yes_never_reaches_the_automatic_quick_check(harness):
    """Round 3 M1: reader.author_section_question is sent by the 60% effect; a yes to a build is not a yes to it."""

    harness.stub("build_study_map", resolve="canonical_ingest", enqueue=True)
    harness.stub("reader.author_section_question", enqueue=True)
    harness.answer(harness.call("build_study_map"))
    built = harness.out(harness.call("build_study_map"))["batch"]
    quick = harness.out(harness.call("reader.author_section_question"))["batch"]
    harness.drain()
    assert harness.seen[built] is True
    assert harness.seen[quick] is False


def test_s2_a_retry_by_retry_synthesis_keeps_the_batch_grant(harness):
    """Round 3 M2: a resume reached from retry_synthesis (no press in the round-2 table) nulled the token."""

    harness.stub("build_study_map", resolve="canonical_ingest", enqueue=True)
    harness.answer(harness.call("build_study_map"))
    batch = harness.out(harness.call("build_study_map"))["batch"]
    harness.stub("retry_synthesis", work=lambda _ctx: harness.runner.resume_batch(batch))
    harness.call("retry_synthesis")
    harness.drain()
    assert harness.seen[batch] is True


def test_s3_resume_ingest_batch_keeps_a_rung_variant_batch_on_its_own_grant(harness):
    """Round 3 M3: resume_ingest_batch narrowed every resumed batch to the build's tasks."""

    harness.stub("request_rung_variant", resolve="rung_variant", enqueue=True)
    harness.answer(harness.call("request_rung_variant"))
    batch = harness.out(harness.call("request_rung_variant"))["batch"]
    harness.stub("resume_ingest_batch", work=lambda _ctx: harness.runner.resume_batch(batch))
    harness.call("resume_ingest_batch")
    harness.drain()
    assert harness.seen[batch] is True


def test_s4_the_workbench_opens_import_carries_its_grant_after_its_own_yes(harness):
    """Round 3 M4: workbench.open is sent automatically and by "Work through this"; its import lost the grant."""

    harness.stub("workbench.open", resolve="canonical_ingest", enqueue=True)
    harness.answer(harness.call("workbench.open"))
    batch = harness.out(harness.call("workbench.open"))["batch"]
    harness.drain()
    assert harness.seen[batch] is True


def test_s5_a_regrant_never_revives_a_token_a_waiting_worker_captured(harness):
    """Round 3 Low: a hint job waiting when the learner stops (and later says yes again) gets no grant back."""

    from learnloop_sidecar.handlers import hints as hint_rpcs

    resume = threading.Event()
    seen: dict[int, bool] = {}
    started: list[Any] = []
    jobs = hint_rpcs.HintJobs()

    def start(ctx) -> str:
        index = len(started)

        def wait_then_check(_repository, _cancelled) -> dict[str, Any]:
            assert resume.wait(30)
            seen[index] = plan_fallback.is_granted("hint_writer", harness.root)
            return {}

        started.append(jobs.start(ctx, "item_1", wait_then_check))
        return "started"

    harness.stub("practice.request_hint", resolve="hint_writer", work=start)
    harness.answer(harness.call("practice.request_hint"))  # job 0 started before the yes
    harness.call("practice.request_hint")  # job 1: started after the yes, carries it, and waits
    harness.stop()
    harness.answer(harness.call("practice.request_hint"))  # job 2 before the new yes; then yes again
    harness.call("practice.request_hint")  # job 3: after the new yes
    resume.set()
    assert all(job.done.wait(30) for job in started)
    assert seen == {0: False, 1: False, 2: False, 3: True}


# -- the redesign's properties --------------------------------------------------------------------


def _methods() -> list[str]:
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.registry import METHOD_REGISTRY

    return sorted(name for name in METHOD_REGISTRY if name != "ai_use_fallback")


def test_p1_after_a_yes_to_one_method_only_its_requests_and_units_use_openrouter(harness):
    """Over every registered RPC: nothing before any answer; after answering M's offer, only M."""

    from learnloop_sidecar.handlers import hints as hint_rpcs

    methods = _methods()
    assert len(methods) > 300
    jobs = hint_rpcs.HintJobs()
    granted_in_job: dict[tuple[str, int], bool] = {}
    started: list[Any] = []
    rounds = {"n": 0}

    def start_job(method: str):
        def start(ctx):
            key = (method, rounds["n"])

            def job_work(_repository, _cancelled) -> dict[str, Any]:
                granted_in_job[key] = plan_fallback.is_granted("hint_writer", harness.root)
                return {}

            started.append(jobs.start(ctx, "item_1", job_work))
            return "started"

        return start

    for method in methods:
        harness.stub(method, resolve="tutor_qa", enqueue=True, work=start_job(method))
    before = {method: harness.call(method) for method in methods}
    assert all(harness.out(response).get("provider") != "openrouter" for response in before.values())
    chosen = "reader.library_ask_tutor"
    harness.answer(before[chosen])
    rounds["n"] = 1
    after = {method: harness.call(method) for method in methods}
    for method, response in after.items():
        assert (harness.out(response).get("provider") == "openrouter") == (method == chosen), method
    harness.drain()
    assert all(job.done.wait(30) for job in started)
    for method in methods:
        batch_before, batch_after = harness.out(before[method])["batch"], harness.out(after[method])["batch"]
        # Queued before any yes: only the answered offer's own batch (it lists it) gets a token.
        assert harness.seen[batch_before] is (method == chosen), method
        assert harness.seen[batch_after] is (method == chosen), method
        assert granted_in_job[(method, 0)] is False, method
        assert granted_in_job[(method, 1)] is (method == chosen), method


def test_p2_a_relayed_offer_keeps_the_jobs_starting_method(harness):
    from learnloop_sidecar.handlers import hints as hint_rpcs

    jobs = hint_rpcs.HintJobs()
    started: list[Any] = []

    def unavailable(_repository, _cancelled) -> dict[str, Any]:
        loaded = harness.ctx.require_vault()[0]
        resolved = ready_client_for_task(loaded.root, loaded.config, "hint_writer")
        assert not resolved.ready
        return {}

    harness.stub("practice.request_hint", work=lambda ctx: started.append(jobs.start(ctx, "item_1", unavailable)))

    def poll(_ctx) -> str:
        job = started[-1]
        assert job.done.wait(30)
        plan_fallback.relay_job_offer(job)
        return "polled"

    harness.stub("practice.hint_job", work=poll)
    assert harness.hint(harness.call("practice.request_hint")) is None  # the job asks on its own thread
    relayed = harness.call("practice.hint_job")
    hint = harness.hint(relayed)
    assert hint is not None and (hint.get("fallbackOrigin") or hint.get("fallback_origin")) == "practice.request_hint"
    harness.answer(relayed)
    assert plan_fallback.granted_origins(harness.root) == ["practice.request_hint"]


def test_p3_units_get_the_answered_offers_token_and_every_resume_keeps_it(harness):
    from learnloop.content.pipeline.runner import JobSpec

    # The offer lists the batch its request queued: answering tokens it.
    harness.stub("build_study_map", resolve="canonical_ingest", enqueue=True)
    first = harness.call("build_study_map")
    listed = harness.out(first)["batch"]
    assert plan_fallback.batch_grant(listed) is None
    harness.answer(first)
    assert plan_fallback.batch_grant(listed) is not None
    # Every resume path keeps it: a pressed Retry, an automatic resume, a sweep, a resume in another action.
    for method in ("resume_ingest_batch", "retry_synthesis", "source_action", "reader.mark_section_progress"):
        harness.stub(method, work=lambda _ctx: harness.runner.resume_batch(listed))
        harness.call(method)
        assert plan_fallback.batch_grant(listed) is not None, method
    harness.runner.resume_batch(listed)  # a sweep, off any request
    harness.drain()
    assert harness.seen[listed] is True
    # A batch made under quiet() records no origin: no token, no offer, ever.
    with plan_fallback.request(harness.root, "build_study_map"), plan_fallback.quiet():
        quiet = harness.runner.enqueue_batch("t1_landing_d", [JobSpec(job_type="t1_probe", payload={})])
    assert plan_fallback.batch_grant(quiet) is None and plan_fallback.batch_origin(quiet) is None


def test_p3_a_batch_asks_on_its_own_and_its_answer_tokens_it(harness):
    """A batch created before any yes runs, meets the unavailable plan, and keeps a batch offer that the
    batch read relays; answering it grants its origin and tokens the batch."""

    from learnloop.content.pipeline.runner import JobSpec

    asked: list[str] = []

    def unavailable(job_ctx) -> dict[str, Any]:
        loaded_root = job_ctx.vault_root
        from learnloop.config import load_config

        resolved = ready_client_for_task(loaded_root, load_config(loaded_root / "learnloop.toml"), "canonical_ingest")
        asked.append(resolved.provider_name)
        return {}

    harness.runner.handlers["t1_unavailable"] = unavailable
    harness.stub("workbench.open", work=lambda _ctx: harness.runner.enqueue_batch(
        "t1_landing_d", [JobSpec(job_type="t1_unavailable", payload={})]))
    batch = harness.out(harness.call("workbench.open"))["work"]
    harness.drain()
    harness.stub("get_ingest_batch", work=lambda _ctx: plan_fallback.relay_batch_offer(batch))
    read = harness.call("get_ingest_batch")
    hint = harness.hint(read)
    assert hint is not None and (hint.get("fallbackOrigin") or hint.get("fallback_origin")) == "workbench.open"
    harness.answer(read)
    assert plan_fallback.batch_grant(batch) is not None
    assert plan_fallback.granted_origins(harness.root) == ["workbench.open"]
    # Relayed once: a second read brings no banner back.
    assert harness.hint(harness.call("get_ingest_batch")) is None


def test_p4_stop_kills_every_captured_token_even_after_a_new_yes(harness):
    harness.stub("build_study_map", resolve="canonical_ingest", enqueue=True)
    harness.answer(harness.call("build_study_map"))
    queued = harness.out(harness.call("build_study_map"))["batch"]
    token = plan_fallback.batch_grant(queued)
    assert token is not None
    harness.stop()
    harness.answer(harness.call("build_study_map"))  # yes again: a new epoch
    harness.drain()
    assert harness.seen[queued] is False
    with plan_fallback.job_grant(token):
        assert not plan_fallback.is_granted("canonical_ingest", harness.root)
    # A stale offer id (from before the stop) answers nothing.
    harness.stop()
    old = harness.call("build_study_map")
    harness.stop()
    stale = harness.call("ai_use_fallback", {"provider": "openrouter",
                                             "offerId": harness.hint(old)["fallback_offer_id"]})
    assert stale["error"]["data"]["code"] == "not_offered"


def test_p5_scrolling_after_a_build_yes_queues_nothing_that_carries_a_grant(tmp_path):
    from tests.test_ux_phase1_round2_review import _added_book

    root, ctx, _source_id, extraction_id = _added_book(tmp_path)
    ctx.ingest_jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    plan_fallback.grant_origin(root, "build_study_map")
    before = {str(batch["id"]) for batch in ctx.repository.list_ingest_batches()}
    from learnloop_sidecar.server import _handle

    for section_id, seen in (("u3", 1), ("u3", 4), ("u4", 1), ("u4", 4)):
        response = _handle(ctx, {"jsonrpc": "2.0", "id": 1, "method": "reader.mark_section_progress",
                                 "params": {"extractionId": extraction_id, "sectionId": section_id,
                                            "spansSeen": seen, "spanCount": 4}})
        assert "result" in response, response.get("error")
        assert "fallbackAvailable" not in response["result"]
    queued = {str(batch["id"]) for batch in ctx.repository.list_ingest_batches()} - before
    assert queued
    assert all(plan_fallback.batch_grant(batch) is None for batch in queued)
    assert all(plan_fallback.batch_origin(batch) is None for batch in queued)


def test_p6_the_quick_check_uses_openrouter_only_after_its_own_yes(harness):
    """Q1: once the quick check's own offer is answered, its automatic sends use OpenRouter too."""

    harness.stub("reader.author_section_question", resolve="canonical_ingest", enqueue=True)
    harness.stub("add_source", resolve="canonical_ingest")
    harness.stub("reader.import_exercise", resolve="canonical_ingest")
    harness.answer(harness.call("add_source"))
    harness.answer(harness.call("reader.import_exercise"))
    assert harness.out(harness.call("reader.author_section_question"))["provider"] != "openrouter"
    harness.answer(harness.call("reader.author_section_question"))
    sent = harness.call("reader.author_section_question")
    assert harness.out(sent)["provider"] == "openrouter"
    harness.drain()
    assert harness.seen[harness.out(sent)["batch"]] is True


def test_the_dispatch_alone_opens_a_request_and_one_site_inherits():
    """AST: ``plan_fallback.request(`` is entered by the sidecar's dispatch (and the CLI's
    command grant inside plan_fallback); ``inherit_grant=True`` is passed at one audited site."""

    import ast
    from pathlib import Path

    src = Path(__file__).resolve().parents[1] / "src"
    requests, inherits = set(), set()
    for path in src.rglob("*.py"):
        relative = str(path.relative_to(src))
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for function in ast.walk(tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for node in ast.walk(function):
                if not isinstance(node, ast.Call):
                    continue
                name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
                if name == "request" and isinstance(node.func, ast.Attribute) and \
                        getattr(node.func.value, "id", "") == "plan_fallback":
                    requests.add(relative)
                for keyword in node.keywords:
                    if keyword.arg == "inherit_grant" and not (isinstance(keyword.value, ast.Constant)
                                                               and keyword.value.value is False):
                        inherits.add((relative, function.name))
    assert requests == {"learnloop_sidecar/server.py"}, requests
    assert inherits == {("learnloop/content/pipeline/add_source.py", "run_auto_study_map")}, inherits
    assert not (src / "learnloop_sidecar" / "pressed.py").exists()


def test_p7_rw5b_figures_ask_as_the_rpc_that_asked(harness):
    """RW5b on the merged tree: the offer button's build (``reader.figure_request`` with
    origin/offerRef) runs its figure author in a library job; its offer, relayed by the
    poll, is minted for ``reader.figure_request``. Answering it serves that action's
    later builds, never the library ask (whose organizer judges explorable blocks) or
    the tutor."""

    from learnloop.practice_index.paid import plan_route, resolve_client
    from learnloop.vault.loader import load_vault
    from learnloop_sidecar.handlers import library_ask as library_rpcs

    jobs = library_rpcs.LibraryJobs()
    started: list[Any] = []

    def figure_author_route(_worker_repo) -> dict[str, Any]:
        vault = load_vault(harness.root)
        route = plan_route(vault, "figure_author")
        client, _message = resolve_client(vault, route)
        return {"provider": route.provider, "client": getattr(client, "provider_name", None)}

    harness.stub("reader.figure_request",
                 work=lambda ctx: started.append(jobs.start(ctx, "figure_build", None, figure_author_route)) or "ok")

    def poll(_ctx) -> dict[str, Any]:
        job = started[-1]
        assert job.done.wait(30)
        plan_fallback.relay_job_offer(job)
        return job.result

    harness.stub("reader.library_job", work=poll)
    harness.stub("reader.library_ask", resolve="library_organizer")
    harness.stub("ask_tutor_question", resolve="tutor_qa")
    harness.call("reader.figure_request", {})
    relayed = harness.call("reader.library_job", {})
    hint = harness.hint(relayed)
    assert hint is not None and hint.get("fallbackOrigin") == "reader.figure_request"
    assert harness.out(relayed)["work"]["client"] is None  # unavailable, asked, nothing built
    harness.answer(relayed)
    harness.call("reader.figure_request", {})
    built = harness.call("reader.library_job", {})
    assert harness.out(built)["work"] == {"provider": "openrouter", "client": "openrouter"}
    for other in ("reader.library_ask", "ask_tutor_question"):
        assert harness.out(harness.call(other))["provider"] != "openrouter", other


# -- the drain's hang guard (Oct 27 review F1) ------------------------------------------------------


def _drain_worker() -> threading.Thread | None:
    return next((thread for thread in threading.enumerate() if thread.name == "t1-landing-d-drain"), None)


def _enqueue_blocking(harness, handler: Callable[[Any], dict[str, Any]]) -> str:
    from learnloop.content.pipeline.runner import JobSpec

    harness.runner.handlers["t1_block"] = handler
    return harness.runner.enqueue_batch("t1_block", [JobSpec(job_type="t1_block", payload={})])


def test_the_hang_guard_cancels_a_blocked_job_and_leaves_no_worker(harness, monkeypatch):
    """A job that blocks until it is cancelled: past the hang guard the drain cancels it through the
    runner's own cancellation (the flag a running handler reads at its checkpoints), the worker
    returns, and the drain fails, bounded, with no worker left alive."""

    from learnloop.content.pipeline.runner import JobCancelled

    monkeypatch.setattr(sys.modules[__name__], "_DRAIN_HANG_GUARD_S", 0.2)
    monkeypatch.setattr(sys.modules[__name__], "_DRAIN_STOP_GRACE_S", 60.0, raising=False)
    saw: dict[str, bool] = {}

    def until_cancelled(job_ctx) -> dict[str, Any]:
        # Bounded so a regressed harness cannot hang the suite: 60 s of 10 ms checkpoints.
        for _ in range(6000):
            if job_ctx.cancelled():
                saw["cancelled"] = True
                raise JobCancelled()
            time.sleep(0.01)
        return {}

    batch = _enqueue_blocking(harness, until_cancelled)
    with pytest.raises(AssertionError, match="did not finish"):
        harness.drain()
    assert saw == {"cancelled": True}
    assert _drain_worker() is None
    assert {job["status"] for job in harness.runner.repo.ingest_jobs_for_batch(batch)} == {"cancelled"}


def test_the_hang_guard_fails_bounded_when_a_job_ignores_cancellation(harness, monkeypatch):
    """A job blocked where no cancellation reaches it: the drain still returns (it fails naming the
    stuck worker and where it is blocked) while the worker is blocked, instead of joining it forever."""

    monkeypatch.setattr(sys.modules[__name__], "_DRAIN_HANG_GUARD_S", 0.2)
    monkeypatch.setattr(sys.modules[__name__], "_DRAIN_STOP_GRACE_S", 0.2, raising=False)
    release = threading.Event()

    def ignores_cancellation(_job_ctx) -> dict[str, Any]:
        release.wait(60)  # bounded so a regressed harness cannot hang the suite
        return {}

    _enqueue_blocking(harness, ignores_cancellation)
    try:
        with pytest.raises(AssertionError, match="still running") as failed:
            harness.drain()
        worker = _drain_worker()
        assert worker is not None and worker.is_alive()  # the drain returned while the job was blocked
        assert "ignores_cancellation" in str(failed.value)  # names where the worker is stuck
    finally:
        release.set()
        worker = _drain_worker()
        if worker is not None:
            worker.join(30)
    assert _drain_worker() is None
