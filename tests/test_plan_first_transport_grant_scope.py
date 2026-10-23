"""Plan-first transport T1, landing review: a grant serves only what the learner asked for.

Owner decision 2026-10-21: "Use OpenRouter instead" serves that one request
(or that feature for the session), and a grant never serves background work.
By construction (``learnloop.ai.plan_fallback``):

* a grant counts only on the thread serving a learner request
  (``plan_fallback.interactive()``: the sidecar's RPC dispatch, the CLI
  command), bound to that thread, so a fresh thread or a context copied to
  another thread has none;
* a job the learner started carries the grant explicitly: a token captured in
  their request (``capture_grant``) and entered on the worker
  (``job_grant``): the sidecar's hint, library, margin-note and reading-path
  jobs and every ingest batch enqueued in a learner request;
* every other background path (startup recovery of import key checks, the
  Reader import's background key check, the edit re-check, build_on_serve,
  hint outcome placement, AD preparation) plans onto the plan profile and
  sends nothing, grant or not.

Nothing here leaves 127.0.0.1; nothing is sent.
"""
from __future__ import annotations

import contextvars
from pathlib import Path
import threading
from types import SimpleNamespace
from typing import Any, Callable

import pytest

from learnloop.ai import plan_fallback
from learnloop.ai.routing import ready_client_for_task
from learnloop.config.schema import CHATGPT_PLAN_PROVIDER_NAMES
from learnloop.practice_index.paid import plan_route, resolve_client
from learnloop.vault.loader import load_vault

from tests.openai_fakes import install_fake_openai
from tests.test_plan_first_transport_paid_roles import _priced_vault, _routed_tasks

KEY_TASK = "source_solution_match"


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


def _paths(root: Path):
    from learnloop.config import load_config
    from learnloop.vault.paths import VaultPaths

    return VaultPaths(root, load_config(root / "learnloop.toml"))


def _grant_all(root: Path, tasks: list[str]) -> None:
    plan_fallback.remember_offer(root, {"fallback_tasks": tasks})
    plan_fallback.grant(root, tasks)


def _in_thread(fn: Callable[[], Any], *, copied: bool = False) -> Any:
    out: list[Any] = []
    errors: list[BaseException] = []
    context = contextvars.copy_context() if copied else None

    def run() -> None:
        try:
            out.append(context.run(fn) if context is not None else fn())
        except BaseException as exc:  # noqa: BLE001 - re-raised in the test thread
            errors.append(exc)

    thread = threading.Thread(target=run)
    thread.start()
    thread.join(30)
    if errors:
        raise errors[0]
    return out[0]


def _planned(root: Path, task: str = KEY_TASK) -> tuple[str | None, str, str | None]:
    """The route a paid role plans here, its billing, and the profile resolve_client builds (if any)."""

    vault = load_vault(root)
    route = plan_route(vault, task)  # type: ignore[arg-type]
    client, _message = resolve_client(vault, route)
    return route.provider, route.billing, getattr(client, "provider_name", None) if client is not None else None


# -- (1) the property over every paid task ---------------------------------------------------


def test_a_grant_counts_only_in_the_learners_request_or_a_job_carrying_it(tmp_path, fake_openai):
    root = _priced_vault(tmp_path)
    vault = load_vault(root)
    tasks = _routed_tasks(vault.config)
    _grant_all(root, tasks)

    # Outside any learner request: no task is served by the grant.
    for task in tasks:
        assert plan_route(vault, task).provider in CHATGPT_PLAN_PROVIDER_NAMES, task  # type: ignore[arg-type]
        assert not ready_client_for_task(root, vault.config, task).provider_name == "openrouter", task  # type: ignore[arg-type]
    assert plan_fallback.capture_grant(root) is None

    with plan_fallback.interactive():
        served = {task for task in tasks
                  if ready_client_for_task(root, vault.config, task).provider_name == "openrouter"}  # type: ignore[arg-type]
        assert len(served) >= 40
        for task in tasks:
            planned = plan_route(vault, task).provider  # type: ignore[arg-type]
            assert (planned == "openrouter") == (task in served), task
        token = plan_fallback.capture_grant(root)
        assert token is not None and set(token.tasks) == set(tasks)

        def plans() -> set[str]:
            return {task for task in tasks if plan_route(vault, task).provider == "openrouter"}  # type: ignore[arg-type]

        # A fresh thread, and a context copied to another thread, carry no grant.
        assert _in_thread(plans) == set()
        assert _in_thread(plans, copied=True) == set()

        # A job carrying the token captured in the request: exactly the request's routes.
        def carried() -> set[str]:
            with plan_fallback.job_grant(token):
                return plans()

        assert _in_thread(carried) == served
        # A readiness probe in the request honours no grant.
        with plan_fallback.quiet():
            assert plans() == set()
            assert plan_fallback.capture_grant(root) is None

    # "Stop using OpenRouter" ends a carried token at the job's next route.
    plan_fallback.revoke(root)

    def after_revoke() -> set[str]:
        with plan_fallback.job_grant(token):
            return {task for task in tasks if plan_route(vault, task).provider == "openrouter"}  # type: ignore[arg-type]

    assert _in_thread(after_revoke) == set()


def test_the_cli_commands_grant_is_its_own_threads_only(tmp_path, monkeypatch, fake_openai):
    root = _priced_vault(tmp_path)
    monkeypatch.setenv("LEARNLOOP_AI_FALLBACK", "openrouter")
    with plan_fallback.command_grant():
        assert _planned(root)[0] == "openrouter"
        assert _in_thread(lambda: _planned(root)[0]) in CHATGPT_PLAN_PROVIDER_NAMES
        assert _in_thread(lambda: _planned(root)[0], copied=True) in CHATGPT_PLAN_PROVIDER_NAMES
        token = plan_fallback.capture_grant(root)

        def carried() -> str | None:
            with plan_fallback.job_grant(token):
                return _planned(root)[0]

        assert _in_thread(carried) == "openrouter"
    with plan_fallback.command_grant(host=True):
        assert _planned(root)[0] in CHATGPT_PLAN_PROVIDER_NAMES


def test_a_manual_fallback_is_never_replaced_by_a_grant(tmp_path, fake_openai):
    import tomlkit

    root = _priced_vault(tmp_path)
    path = root / "learnloop.toml"
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    document["ai"]["fallback_provider"] = "manual"
    path.write_text(tomlkit.dumps(document), encoding="utf-8")
    _grant_all(root, [KEY_TASK, "tutor_qa"])
    with plan_fallback.interactive():
        vault = load_vault(root)
        # Routing answers manual before any grant; the paid path does the same.
        assert ready_client_for_task(root, vault.config, KEY_TASK).provider_name != "openrouter"
        provider, _billing, client = _planned(root)
        assert provider in CHATGPT_PLAN_PROVIDER_NAMES and client is None


# -- (2) the three background key checks, with the learner's grant of source_solution_match -------


def _key_check_vault(tmp_path) -> Path:
    import tomlkit

    root = _priced_vault(tmp_path)
    path = root / "learnloop.toml"
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    document["source_service"]["enabled"] = True
    document["source_service"]["exercise_verification"] = True
    path.write_text(tomlkit.dumps(document), encoding="utf-8")
    return root


def _recorder() -> tuple[list[tuple[Any, ...]], threading.Event, Callable[..., Any]]:
    seen: list[tuple[Any, ...]] = []
    done = threading.Event()

    def record(root: Any, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        try:
            seen.append(_planned(Path(root)))
        finally:
            done.set()
        return {}

    return seen, done, record


def _assert_on_the_plan(seen: list[tuple[Any, ...]], done: threading.Event) -> None:
    assert done.wait(30)
    [(provider, billing, client)] = seen
    assert provider in CHATGPT_PLAN_PROVIDER_NAMES and billing == "subscription" and client is None


def test_startup_recovery_of_import_key_checks_never_uses_the_grant(tmp_path, monkeypatch, fake_openai):
    import learnloop.content.authoring.source_exercise_import as SEI
    from learnloop_sidecar.context import SidecarContext

    root = _key_check_vault(tmp_path)
    _grant_all(root, [KEY_TASK])
    seen, done, record = _recorder()
    monkeypatch.setattr(SEI, "pending_import_checks", lambda *_a, **_k: True)
    monkeypatch.setattr(SEI, "recover_import_checks", lambda root, _repository: record(root))
    with plan_fallback.interactive():  # load() runs inside an RPC (select_vault)
        assert _planned(root)[0] == "openrouter"  # the grant is real in the request itself
        ctx = SidecarContext()
        ctx.load(root, maintenance=False)
        ctx.recover_import_key_checks()
    _assert_on_the_plan(seen, done)


def test_the_reader_imports_background_key_check_never_uses_the_grant(tmp_path, monkeypatch, fake_openai):
    import learnloop.content.authoring.source_exercise_import as SEI
    from learnloop.clock import SystemClock
    from learnloop.content.pipeline import jobs
    from learnloop.content.pipeline.runner import RunnerServices
    from learnloop.db.repositories import Repository

    root = _key_check_vault(tmp_path)
    _grant_all(root, [KEY_TASK])
    seen, done, record = _recorder()
    monkeypatch.setattr(SEI, "record_reader_import", lambda *_a, **_k: [{"practice_item_id": "pi_x"}])
    monkeypatch.setattr(SEI, "verify_item_key", record)
    with plan_fallback.interactive():
        token = plan_fallback.capture_grant(root)
    ctx = SimpleNamespace(vault_root=root, repo=Repository.attach(_paths(root).sqlite_path),
                          services=RunnerServices(), clock=SystemClock())
    # Inside the Reader-import job, which carries the learner's grant: its background check does not.
    with plan_fallback.job_grant(token):
        assert _planned(root)[0] == "openrouter"
        jobs._record_reader_import_keys(ctx, {"items": []}, extraction_id="ext", raw_selection={"nodes": []},
                                        source_id=None, revision_id=None)
    _assert_on_the_plan(seen, done)


def test_the_edit_recheck_never_uses_the_grant(tmp_path, monkeypatch, fake_openai):
    import learnloop.content.authoring.source_exercise_import as SEI
    import learnloop.db.stores.source_service as source_service_store
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.handlers import item_authoring

    from tests.helpers import seed_due_item

    root = _key_check_vault(tmp_path)
    seed_due_item(_paths(root))
    _grant_all(root, [KEY_TASK])
    seen, done, record = _recorder()
    monkeypatch.setattr(SEI, "verify_item_key", record)
    monkeypatch.setattr(source_service_store, "effective_key_status", lambda *_a, **_k: "model_answer")
    ctx = SidecarContext()
    ctx.load(root, maintenance=False)
    item_id = next(iter(ctx.require_vault()[0].practice_items))
    with plan_fallback.interactive():  # queued by the edit RPC
        assert item_authoring._queue_key_recheck(ctx, item_id) == "queued"
    _assert_on_the_plan(seen, done)


# -- (3) the shared background launcher: build_on_serve, hint outcome placement, AD preparation -------


def test_the_background_build_launcher_never_uses_the_grant(tmp_path, fake_openai):
    from learnloop.hints.map_builder import BackgroundBuilds

    root = _priced_vault(tmp_path)
    vault = load_vault(root)
    tasks = ["approach_map", "hint_outcome", "ad_forecast_llm", "ad_feature_audit", "hint_writer"]
    _grant_all(root, tasks)
    builds = BackgroundBuilds()
    seen: dict[str, str | None] = {}
    done = threading.Event()

    def work(_fence: Any) -> Callable[[], None]:
        def run() -> None:
            try:
                for task in tasks:
                    seen[task] = plan_route(vault, task).provider  # type: ignore[arg-type]
            finally:
                done.set()

        return run

    with plan_fallback.interactive():  # launched from a learner request (a serve, a submit)
        assert plan_route(vault, "approach_map").provider == "openrouter"
        thread = builds.launch(_paths(root).sqlite_path, work, name="t1-landing-grant-scope")
    assert thread is not None and done.wait(30)
    assert all(provider in CHATGPT_PLAN_PROVIDER_NAMES for provider in seen.values()), seen


# -- (4) the jobs the learner started carry their grant -------------------------------------------


def test_a_hint_job_started_in_the_request_carries_its_grant_and_a_background_one_does_not(tmp_path,
                                                                                         fake_openai):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.handlers import hints as hint_rpcs

    root = _priced_vault(tmp_path)
    _grant_all(root, ["hint_writer"])
    ctx = SidecarContext()
    ctx.load(root, maintenance=False)

    def work(_repository: Any, _cancelled: Callable[[], bool]) -> dict[str, Any]:
        return {"provider": _planned(root, "hint_writer")[0]}

    with plan_fallback.interactive():
        pressed = hint_rpcs.HintJobs().start(ctx, "item_1", work)
    background = hint_rpcs.HintJobs().start(ctx, "item_1", work)
    assert pressed.done.wait(30) and background.done.wait(30)
    assert pressed.result == {"provider": "openrouter"}
    assert background.result["provider"] in CHATGPT_PLAN_PROVIDER_NAMES


def test_an_ingest_batch_carries_the_grant_only_when_the_learner_enqueued_it(tmp_path):
    from learnloop.content.pipeline.runner import IngestRunner, JobSpec
    from learnloop.db.repositories import Repository

    root = _priced_vault(tmp_path)
    _grant_all(root, ["canonical_ingest"])
    runner = IngestRunner(Repository.attach(_paths(root).sqlite_path), vault_root=root, worker_id="t1-landing",
                          handlers={})
    with plan_fallback.interactive():
        pressed = runner.enqueue_batch("t1_landing", [JobSpec(job_type="noop", payload={})])
    background = runner.enqueue_batch("t1_landing", [JobSpec(job_type="noop", payload={})])
    token = plan_fallback.batch_grant(pressed)
    assert token is not None and "canonical_ingest" in token.tasks
    assert plan_fallback.batch_grant(background) is None
