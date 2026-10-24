"""Plan-first transport T1, landing review round 2: only a press carries a grant into queued work.

Ruling on the verify of 84a3f8947 / 4a8868f09 (Medium): every RPC is not a
learner press, and scrolling is not pressing. A grant ("Use OpenRouter
instead") reaches work that outlives the request only when the learner
pressed the feature:

* the sidecar's dispatch enters ``plan_fallback.pressed(vault, feature)`` for
  the RPCs in ``learnloop_sidecar.pressed.PRESSED_RPCS`` only; an ingest batch
  carries the token of the pressed scope it was enqueued in, narrowed to that
  feature's own tasks (``plan_fallback.FEATURE_TASKS``);
* a child batch inherits it only when the enqueue says so (the pressed
  build's own planned build); keep-ahead after a build and reading progress
  never do, and inside a running job no pressed scope or request counts;
* a resume refreshes the token from a press, or drops it; ``revoke(vault)``
  drops that vault's batch tokens.

Nothing is sent; no test leaves 127.0.0.1.
"""
from __future__ import annotations

import ast
from pathlib import Path
import threading
from typing import Any

import pytest

from learnloop.ai import plan_fallback

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
BUILD_TASKS = ("canonical_ingest", "canonical_ingest_retry", "authoring")
GRANTED = ("canonical_ingest", "canonical_ingest_retry", "authoring", "tutor_qa", "hint_writer", "grading")


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    for name in ("LEARNLOOP_AI_PROVIDER", "LEARNLOOP_AI_FALLBACK", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    plan_fallback.revoke_all()
    yield
    plan_fallback.revoke_all()


def _grant(root: Any, tasks=GRANTED) -> None:
    plan_fallback.remember_offer(root, {"fallback_tasks": list(tasks)})
    plan_fallback.grant(root, list(tasks))


def _handle(ctx, method_name: str, params: dict[str, Any]) -> dict[str, Any]:
    from learnloop_sidecar.server import _handle as handle

    return handle(ctx, {"jsonrpc": "2.0", "id": 1, "method": method_name, "params": params})


def _batch_ids(ctx) -> set[str]:
    return {str(batch["id"]) for batch in ctx.repository.list_ingest_batches()}


# -- the Medium: reading progress (scrolling) queues nothing that carries a grant ---------------


def test_scrolling_a_book_queues_no_batch_that_carries_a_grant(tmp_path):
    from tests.test_ux_phase1_round2_review import _added_book

    root, ctx, _source_id, extraction_id = _added_book(tmp_path)
    ctx.ingest_jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    _grant(root)
    before = _batch_ids(ctx)
    for section_id, seen in (("u3", 1), ("u3", 4), ("u4", 1), ("u4", 4)):
        response = _handle(ctx, "reader.mark_section_progress",
                           {"extractionId": extraction_id, "sectionId": section_id, "spansSeen": seen,
                            "spanCount": 4})
        assert "result" in response, response.get("error")
    queued = _batch_ids(ctx) - before
    assert queued, "reading progress queued no keep-ahead build (the scenario did not run)"
    assert {batch: plan_fallback.batch_grant(batch) for batch in queued} == {batch: None for batch in queued}


def test_a_pressed_build_carries_a_token_narrowed_to_its_own_tasks(tmp_path):
    from tests.test_ux_phase1_round2_review import _added_book

    root, ctx, source_id, _extraction_id = _added_book(tmp_path)
    ctx.ingest_jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    _grant(root)
    response = _handle(ctx, "source_action", {"sourceId": source_id, "action": "build_whole_book"})
    assert "result" in response, response.get("error")
    batch_id = response["result"]["batch_id"] if "batch_id" in response["result"] else response["result"]["batchId"]
    token = plan_fallback.batch_grant(batch_id)
    assert token is not None
    assert set(token.tasks) == set(BUILD_TASKS) & set(GRANTED)


# -- children, follow-ups, resumes, revoke --------------------------------------------------------


def _runner(root, handlers):
    from learnloop.config import load_config
    from learnloop.content.pipeline.runner import IngestRunner
    from learnloop.db.repositories import Repository
    from learnloop.vault.paths import VaultPaths

    paths = VaultPaths(root, load_config(root / "learnloop.toml"))
    return IngestRunner(Repository.attach(paths.sqlite_path), vault_root=root, worker_id="t1-landing-r2",
                        handlers=handlers)


@pytest.fixture
def vault(tmp_path):
    from tests.helpers import create_basic_vault

    return create_basic_vault(tmp_path / "vault").root


def _drain_in_a_fresh_thread(runner) -> None:
    thread = threading.Thread(target=runner.drain)
    thread.start()
    thread.join(60)


def test_the_runner_enters_the_grant_only_for_a_pressed_enqueue(vault):
    """Low 2: _run_claimed enters job_grant for a pressed batch, and nothing for an automatic one."""

    from learnloop.content.pipeline.runner import JobSpec

    _grant(vault)
    seen: dict[str, bool] = {}

    def probe(ctx) -> dict[str, Any]:
        seen[ctx.job["batch_id"]] = plan_fallback.is_granted("canonical_ingest", ctx.vault_root)
        return {}

    runner = _runner(vault, {"t1_probe": probe})
    with plan_fallback.interactive(), plan_fallback.pressed(vault, "build"):
        pressed = runner.enqueue_batch("t1_landing", [JobSpec(job_type="t1_probe", payload={})])
    with plan_fallback.interactive():  # an RPC that is not a press (reading progress, Today, a poll)
        automatic = runner.enqueue_batch("t1_landing", [JobSpec(job_type="t1_probe", payload={})])
    background = runner.enqueue_batch("t1_landing", [JobSpec(job_type="t1_probe", payload={})])
    _drain_in_a_fresh_thread(runner)
    assert seen == {pressed: True, automatic: False, background: False}


def test_children_inherit_only_when_told_and_a_drained_job_sees_no_press(vault):
    from learnloop.content.pipeline.runner import JobSpec

    _grant(vault)
    children: dict[str, str] = {}

    def parent(ctx) -> dict[str, Any]:
        children["own_build"] = ctx.enqueue_batch("t1_child", [JobSpec(job_type="t1_noop", payload={})],
                                                  inherit_grant=True)
        children["follow_up"] = ctx.enqueue_batch("t1_child", [JobSpec(job_type="t1_noop", payload={})])
        return {}

    runner = _runner(vault, {"t1_parent": parent, "t1_noop": lambda ctx: {}})
    with plan_fallback.interactive(), plan_fallback.pressed(vault, "build"):
        runner.enqueue_batch("t1_landing", [JobSpec(job_type="t1_parent", payload={})])
        # Drained in the pressed request's own thread (a foreground drain): the
        # follow-up still inherits nothing from the press around it.
        runner.drain(max_jobs=1)
    assert plan_fallback.batch_grant(children["own_build"]) is not None
    assert plan_fallback.batch_grant(children["follow_up"]) is None


def test_a_resume_refreshes_the_token_from_a_press_or_drops_it_and_revoke_clears_it(vault):
    """Low 1."""

    from learnloop.content.pipeline.runner import JobSpec

    _grant(vault)
    runner = _runner(vault, {"t1_fail": lambda ctx: (_ for _ in ()).throw(RuntimeError("t1"))})
    with plan_fallback.interactive(), plan_fallback.pressed(vault, "build"):
        batch = runner.enqueue_batch("t1_landing", [JobSpec(job_type="t1_fail", payload={})])
    _drain_in_a_fresh_thread(runner)
    assert plan_fallback.batch_grant(batch) is not None
    runner.resume_batch(batch)  # an automatic resume (startup, a sweep): no press
    assert plan_fallback.batch_grant(batch) is None
    _grant(vault, ("canonical_ingest",))
    with plan_fallback.interactive(), plan_fallback.pressed(vault, "build"):
        runner.resume_batch(batch)  # a pressed Retry: a fresh token, narrowed
    assert set(plan_fallback.batch_grant(batch).tasks) == {"canonical_ingest", *set(BUILD_TASKS) & set(GRANTED)}
    plan_fallback.revoke(vault)
    assert plan_fallback.batch_grant(batch) is None
    _grant(vault)  # a later re-grant does not revive the old batch's token
    assert plan_fallback.batch_grant(batch) is None


# -- the dispatch's own marker, and the property over every RPC ----------------------------------


def test_the_dispatch_marks_every_rpc_interactive_and_only_pressed_rpcs_pressed(vault, monkeypatch):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.dto import EmptyParams
    from learnloop_sidecar.pressed import PRESSED_RPCS, pressed_feature
    from learnloop_sidecar.registry import METHOD_REGISTRY, MethodSpec

    every_feature_task = sorted(set().union(*plan_fallback.FEATURE_TASKS.values()))
    _grant(vault, every_feature_task)
    ctx = SidecarContext()
    ctx.load(vault, maintenance=False)
    marks: list[tuple[bool, Any]] = []

    def probe(_ctx, _params) -> dict[str, Any]:
        token = plan_fallback.pressed_token(vault)
        marks.append((plan_fallback.is_interactive(), None if token is None else set(token.tasks)))
        return {}

    probe(ctx, EmptyParams())  # called directly: neither
    monkeypatch.setitem(METHOD_REGISTRY, "test.t1_probe", MethodSpec("test.t1_probe", EmptyParams, probe))
    _handle(ctx, "test.t1_probe", {})
    monkeypatch.setitem(PRESSED_RPCS, "test.t1_probe", "build")
    _handle(ctx, "test.t1_probe", {})
    assert marks == [(False, None), (True, None), (True, set(BUILD_TASKS))]

    # Every registered RPC: dispatched with a stub that enqueues a batch, only a
    # press carries a token, narrowed to that RPC's feature.
    from learnloop.content.pipeline.runner import JobSpec

    runner = _runner(vault, {})
    carried: dict[str, Any] = {}
    for name, spec in list(METHOD_REGISTRY.items()):
        if name.startswith("test."):
            continue

        def enqueue(_ctx, _params, name=name):
            batch = runner.enqueue_batch("t1_property", [JobSpec(job_type="t1_noop", payload={})])
            carried[name] = plan_fallback.batch_grant(batch)
            return {}

        monkeypatch.setitem(METHOD_REGISTRY, name, MethodSpec(name, EmptyParams, enqueue))
        _handle(ctx, name, {})
    assert set(carried) >= set(PRESSED_RPCS) - {"test.t1_probe"}
    for name, token in carried.items():
        feature = pressed_feature(name, {})
        if feature is None:
            assert token is None, name
        else:
            assert token is not None and set(token.tasks) == set(plan_fallback.FEATURE_TASKS[feature]), name


def _frontend_methods() -> set[str]:
    import re

    client = (ROOT / "apps" / "learnloop-tauri" / "src" / "api" / "client.ts").read_text(encoding="utf-8")
    return set(re.findall(r'call<[^>]*>\("([a-z_]+)"', client)) | set(re.findall(r'call\("([a-z_]+)"', client))


def test_no_rpc_the_desktop_sends_without_a_press_is_a_press(vault):
    """Every RPC the desktop calls (from api/client.ts) that the frontend sends by itself
    (an effect, a poll, a scroll, a status read) is not in PRESSED_RPCS: the pressed
    RPCs are each named with the press that sends them."""

    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.pressed import PRESSED_RPCS
    from learnloop_sidecar.registry import METHOD_REGISTRY

    registry = {name.replace(".", "_"): name for name in METHOD_REGISTRY}
    frontend = {registry[name] for name in _frontend_methods() if name in registry}
    assert len(frontend) > 100
    # Automatic by construction: polls of a job, reads of state, progress and status.
    automatic = {name for name in frontend
                 if name.endswith(("_job", "_status", "_progress", ".mark_section_progress"))
                 or name.split(".")[-1].startswith(("get_", "list_", "poll_"))}
    assert "reader.mark_section_progress" in automatic and "get_today_queue" in automatic
    assert not (automatic & set(PRESSED_RPCS)), sorted(automatic & set(PRESSED_RPCS))
    # And the frontend's own automatic senders found in this landing.
    for name in ("reader.cue_discovery", "workbench.open", "workbench.suggest_help", "reader.exercise_candidates",
                 "next_plan_item", "load_vault", "get_ai_connection"):
        assert name not in PRESSED_RPCS, name


def test_only_the_dispatch_enters_a_press_and_only_audited_sites_pass_or_inherit_a_grant():
    """By construction: ``plan_fallback.pressed(`` is entered by the sidecar's
    dispatch alone; ``grant=`` and ``inherit_grant=True`` reach an enqueue only
    from the audited sites below."""

    audited_inherit = {("learnloop/content/pipeline/add_source.py", "run_auto_study_map")}
    pressed_calls, inherit_calls = set(), set()
    for path in SRC.rglob("*.py"):
        relative = str(path.relative_to(SRC))
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for function in ast.walk(tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for node in ast.walk(function):
                if not isinstance(node, ast.Call):
                    continue
                name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
                if name == "pressed" and relative != "learnloop/ai/plan_fallback.py":
                    pressed_calls.add((relative, function.name))
                for keyword in node.keywords:
                    if keyword.arg == "inherit_grant" and not (isinstance(keyword.value, ast.Constant)
                                                               and keyword.value.value is False):
                        inherit_calls.add((relative, function.name))
    assert {path for path, _fn in pressed_calls} == {"learnloop_sidecar/server.py"}, pressed_calls
    assert inherit_calls <= audited_inherit | {("learnloop/content/pipeline/runner.py", "enqueue_batch")}, inherit_calls
