"""Plan-first transport T1, redesign D, verify of ad6dad0c4 (Codex 20261024-093024-2xxRr8): four edge fixes.

1. A relayed offer is minted from the unit's own vault and epoch (recorded when
   the job or batch was created / ran), never the session's: a relay whose
   unit belongs to another vault, or to a stale epoch, mints nothing.
2. A batch's origin (the action that created it) is durable
   (``ingest_batches.origin_method``, migration 218): after a sidecar restart
   a resumed batch asks again as its origin.
3. A book card's build ("Build now", "Build the whole book") surfaces its
   queued offer: the library read relays the offers of the batches it shows,
   and every response that reports a batch relays that batch's offer (once).
4. The yes on an offer is the learner's consent for that action: the build's
   provider-consent gate honours an active action grant.

Nothing is sent; no test leaves 127.0.0.1.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

from learnloop.ai import plan_fallback
from learnloop.ai.routing import ready_client_for_task

from tests.test_plan_first_transport_offer_grants import Harness, fake_openai, isolated  # noqa: F401
from tests.test_plan_first_transport_paid_roles import _priced_vault


@pytest.fixture
def harness(tmp_path, monkeypatch, fake_openai):  # noqa: F811
    return Harness(tmp_path, monkeypatch)


def _figure_job_stub(harness, jobs, started):
    from learnloop.practice_index.paid import plan_route, resolve_client
    from learnloop.vault.loader import load_vault

    def figure_author(_worker_repo) -> dict[str, Any]:
        vault = load_vault(harness.root)
        client, _message = resolve_client(vault, plan_route(vault, "figure_author"))
        return {"client": getattr(client, "provider_name", None)}

    harness.stub("reader.figure_request",
                 work=lambda ctx: started.append(jobs.start(ctx, "figure_build", None, figure_author)) or "ok")

    def poll(_ctx) -> dict[str, Any]:
        job = started[-1]
        assert job.done.wait(30)
        plan_fallback.relay_job_offer(job)
        return job.result

    harness.stub("reader.library_job", work=poll)


# -- (1) a relayed offer belongs to its unit's vault and epoch -----------------------------------


def test_m1_a_figure_jobs_delayed_poll_after_a_vault_switch_mints_nothing(harness, tmp_path):
    from learnloop_sidecar.handlers import library_ask as library_rpcs

    jobs = library_rpcs.LibraryJobs()
    started: list[Any] = []
    _figure_job_stub(harness, jobs, started)
    harness.call("reader.figure_request")  # fails in vault A: its offer waits on the job
    assert started[-1].done.wait(30)
    other = _priced_vault(tmp_path / "b")
    harness.ctx.load(other, maintenance=False)  # the learner switches to vault B
    polled = harness.call("reader.library_job")
    assert harness.hint(polled) is None  # vault A's offer never shows in B
    assert plan_fallback.granted_origins(other) == []


def test_m1_a_relay_from_before_a_stop_mints_nothing(harness):
    from learnloop_sidecar.handlers import library_ask as library_rpcs

    jobs = library_rpcs.LibraryJobs()
    started: list[Any] = []
    _figure_job_stub(harness, jobs, started)
    harness.call("reader.figure_request")
    assert started[-1].done.wait(30)
    harness.stop()  # a new epoch: the job's offer is stale
    assert harness.hint(harness.call("reader.library_job")) is None


def test_m1_every_relay_path_keeps_its_units_vault_and_epoch(harness, tmp_path):
    """Hints, library (and figures), batches: each relayed offer is minted for the unit's own
    vault and epoch, or not at all. Margin notes and reading paths run the same ``unit()``
    (pinned below by AST: every unit is opened with its vault)."""

    from learnloop.content.pipeline.runner import JobSpec
    from learnloop_sidecar.handlers import hints as hint_rpcs

    hints = hint_rpcs.HintJobs()
    started: list[Any] = []

    def hint_unavailable(_repository, _cancelled) -> dict[str, Any]:
        loaded = load_root_config(harness.root)
        ready_client_for_task(harness.root, loaded, "hint_writer")
        return {}

    harness.stub("practice.request_hint", work=lambda ctx: started.append(hints.start(ctx, "i", hint_unavailable)))
    harness.stub("practice.hint_job", work=lambda _ctx: _relay_job(started[-1]))

    def batch_unavailable(job_ctx) -> dict[str, Any]:
        ready_client_for_task(job_ctx.vault_root, load_root_config(job_ctx.vault_root), "canonical_ingest")
        return {}

    harness.runner.handlers["t1_unavailable"] = batch_unavailable
    batches: list[str] = []
    harness.stub("build_study_map", work=lambda _ctx: batches.append(harness.runner.enqueue_batch(
        "t1_r5", [JobSpec(job_type="t1_unavailable", payload={})])))
    harness.stub("get_ingest_batch", work=lambda _ctx: plan_fallback.relay_batch_offer(batches[-1]))
    # Same vault and epoch: each relays, as its own origin.
    harness.call("practice.request_hint")
    assert harness.hint(harness.call("practice.hint_job"))["fallbackOrigin"] == "practice.request_hint"
    harness.call("build_study_map")
    harness.drain()
    assert harness.hint(harness.call("get_ingest_batch"))["fallbackOrigin"] == "build_study_map"
    # A stale epoch: nothing.
    harness.call("practice.request_hint")
    harness.call("build_study_map")
    harness.drain()
    harness.stop()
    assert harness.hint(harness.call("practice.hint_job")) is None
    assert harness.hint(harness.call("get_ingest_batch")) is None
    # Another vault: nothing.
    harness.call("practice.request_hint")
    harness.call("build_study_map")
    harness.drain()
    harness.ctx.load(_priced_vault(tmp_path / "b"), maintenance=False)
    assert harness.hint(harness.call("practice.hint_job")) is None
    assert harness.hint(harness.call("get_ingest_batch")) is None


def load_root_config(root):
    from learnloop.config import load_config

    return load_config(Path(root) / "learnloop.toml")


def _relay_job(job) -> str:
    assert job.done.wait(30)
    plan_fallback.relay_job_offer(job)
    return "polled"


def test_m1_every_unit_is_opened_with_its_vault():
    src = Path(__file__).resolve().parents[1] / "src"
    calls = []
    for path in src.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "unit"
                    and getattr(node.func.value, "id", "") == "plan_fallback"):
                calls.append((str(path.relative_to(src)), len(node.args) + len(node.keywords)))
    assert len(calls) >= 5, calls
    assert all(count >= 3 for _path, count in calls), calls


# -- (2) the batch's origin survives a restart ----------------------------------------------------


def test_m2_a_batch_resumed_after_a_restart_asks_again_as_its_origin(harness):
    from learnloop.content.pipeline.runner import JobSpec

    def unavailable(job_ctx) -> dict[str, Any]:
        resolved = ready_client_for_task(job_ctx.vault_root, load_root_config(job_ctx.vault_root),
                                         "canonical_ingest")
        harness.seen[job_ctx.job["batch_id"]] = resolved.provider_name == "openrouter"
        if resolved.provider_name != "openrouter":
            raise RuntimeError("the plan is unavailable")  # the job fails, so a Retry runs it again
        return {}

    harness.runner.handlers["t1_unavailable"] = unavailable
    batches: list[str] = []
    harness.stub("build_study_map", work=lambda _ctx: batches.append(harness.runner.enqueue_batch(
        "t1_r5", [JobSpec(job_type="t1_unavailable", payload={})])))
    harness.call("build_study_map")
    batch = batches[-1]
    # A sidecar restart: every session-only record is gone (grants, tokens, offers, origins in memory).
    plan_fallback.revoke_all()
    plan_fallback._BATCH_ORIGIN.clear()
    plan_fallback._BATCH_STAMP.clear()
    harness.drain()  # the resumed batch runs, meets the unavailable plan, and asks as its origin
    harness.stub("get_ingest_batch", work=lambda _ctx: plan_fallback.relay_batch_offer(batch))
    read = harness.call("get_ingest_batch")
    hint = harness.hint(read)
    assert hint is not None and hint["fallbackOrigin"] == "build_study_map"
    harness.answer(read)  # a fresh yes for that action serves it
    harness.runner.resume_batch(batch)
    harness.drain()
    assert harness.seen[batch] is True


# -- (3) and (4): Build now on a book card, with the plan down ------------------------------------


@pytest.fixture
def book(tmp_path, monkeypatch):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop.content.pipeline.add_source import default_authoring_route
    from learnloop_sidecar.context import SidecarContext

    from tests.test_ux_phase1_add_source import call
    from learnloop.content.sources.source_outline import resolve_extraction_id
    from tests.ux_phase1_support import CLOCK, fake_services, fresh_library, write_book

    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    root = fresh_library(tmp_path)
    ctx = SidecarContext()
    ctx.load(root)
    # The real build route (the plan, signed out); the clients themselves are fakes.
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK,
                         services=fake_services(authoring_route_factory=default_authoring_route))
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]["sourceId"]
    resolve_extraction_id(ctx.repository, source_id)
    return root, ctx, source_id


def _handle(ctx, method: str, params: dict[str, Any]) -> dict[str, Any]:
    from learnloop_sidecar.server import _handle as handle

    return handle(ctx, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})


def _planner_outcome(ctx, batch_id: str) -> dict[str, Any]:
    jobs = ctx.repository.ingest_jobs_for_batch(batch_id)
    return dict((jobs[0].get("result") or {}))


def test_m3_build_now_surfaces_its_offer_on_the_library_read(book, fake_openai):  # noqa: F811
    import threading

    _root, ctx, source_id = book
    ctx.ingest_jobs._ensure_worker = lambda: None  # type: ignore[method-assign]  # the worker runs it later
    pressed = _handle(ctx, "source_action", {"sourceId": source_id, "action": "build_now"})
    assert "result" in pressed, pressed.get("error")
    assert "fallbackAvailable" not in pressed["result"]  # nothing has met the plan yet
    batch = pressed["result"]["batchId"]
    worker = threading.Thread(target=ctx.ingest_jobs._runner.drain)
    worker.start()
    worker.join(60)
    assert _planner_outcome(ctx, batch).get("reason") == "no_ai"
    # The card's refresh: the library read shows the build's offer, once, as the action that asked.
    library = _handle(ctx, "get_source_library", {})["result"]
    assert library.get("fallbackAvailable") == "openrouter" and library.get("fallbackOrigin") == "source_action"
    assert "fallbackAvailable" not in _handle(ctx, "get_source_library", {})["result"]


def test_m4_the_yes_is_the_builds_consent(book, fake_openai):  # noqa: F811
    root, ctx, source_id = book
    assert "openrouter" not in ctx.require_vault()[0].config.ai.consent  # only ever connected to ChatGPT
    plan_fallback.grant_origin(root, "source_action")  # the learner's yes to the book card's offer
    pressed = _handle(ctx, "source_action", {"sourceId": source_id, "action": "build_now"})
    assert "result" in pressed, pressed.get("error")
    outcome = _planner_outcome(ctx, pressed["result"]["batchId"])
    assert outcome.get("reason") != "needs_consent", outcome
    assert outcome.get("outcome") == "building" and outcome.get("provider") == "openrouter", outcome


def test_m3_a_press_drained_in_its_own_request_shows_the_offer_on_its_response(book, fake_openai):  # noqa: F811
    """A foreground drain (the CLI-like inline runner): the press's own response reports its batch, and so
    shows the batch's offer at once (once: the library read then shows nothing)."""

    _root, ctx, source_id = book
    pressed = _handle(ctx, "source_action", {"sourceId": source_id, "action": "build_now"})
    assert pressed["result"].get("fallbackOrigin") == "source_action"
    assert "fallbackAvailable" not in _handle(ctx, "get_source_library", {})["result"]
