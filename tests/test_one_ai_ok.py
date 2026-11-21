"""One OK before LearnLoop uses AI at all (learnloop.ai.model_use; ledger UX-10).

The learner says OK once and it covers every use. Before it, no request leaves on any route: the factory binds
every client to the library's OK and ``model_call`` refuses before anything is sent, so the dispatch trap of each
physical adapter (OpenRouter chat with its retry, embeddings, the Decider, the ChatGPT plan, video) counts zero,
whether the call runs in the request's thread, a background thread or a resumed job, and whichever provider a
fallback picks. The jobs and the RPCs that use a model wait for the OK instead of failing; saying OK resumes what
waited once, and it is never asked for again. An OK given before this record existed is honoured; an upload's
own OK, a sign-in, a connection or a fallback choice is not one.

Every test here runs on a machine with no OK (``no_ai_ok``) and its own config directory.
"""
from __future__ import annotations

import threading
import types
from pathlib import Path

import pytest

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.ai import model_use, plan_fallback
from learnloop.ai.chatgpt_plan.session import PlanSession
from learnloop.ai.client import make_ai_provider_client_from_profile, make_video_generation_client
from learnloop.ai.decisions import NoulQuestion
from learnloop.ai.routing import ready_client_for_task
from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import execute_structured_operation
from learnloop.config import AIProviderConfig, global_ai_defaults_path, load_config
from learnloop.config.schema import ChatGPTPlanProviderConfig, DeciderProviderConfig
from learnloop.content.pipeline.runner import IngestRunner, JobContext, JobSpec
from learnloop.db.repositories import Repository
from learnloop.ops.settings_store import apply_config_updates
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import METHOD_REGISTRY
from learnloop_sidecar.request_origin import RequestOrigin

from tests.chatgpt_plan_fakes import Reply, completed_events, fake_chatgpt, sign_in
from tests.decider_fakes import fake_decisions
from tests.helpers import create_basic_vault
from tests.openai_fakes import install_fake_openai
from tests.ux_phase1_support import CLOCK, Calls, fake_services, fresh_library, route, write_book

pytestmark = pytest.mark.no_ai_ok

ANSWER = '{"ok": true, "note": "done"}'


class Answer(WireModel):
    ok: bool
    note: str


@pytest.fixture(autouse=True)
def fresh_machine(tmp_path, monkeypatch):
    """This computer has never been asked: its AI defaults are empty."""

    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "machine"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    plan_fallback.revoke_all()
    yield
    plan_fallback.revoke_all()


def say_ok(root: Path) -> None:
    """The learner's one OK, written as the sheet writes it."""

    apply_config_updates(root / "learnloop.toml", model_use.record_updates("2026-11-21T09:00:00+00:00"))


def call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


# -- what counts as the OK ---------------------------------------------------------------------------------------


def test_the_one_record_and_an_earlier_ok_count_and_nothing_else_does():
    said = {"granted_at": "2026-11-21T09:00:00Z", "data_flow": "all_model_use", "disclosure_version": 1}
    found = model_use.acceptance_in({"model_use": said})
    assert (found.key, found.disclosure_version, found.where) == ("model_use", 1, "library")
    # The connection sheet's earlier OK, whichever provider it named, is honoured as it stands.
    for key in ("codex", "chatgpt", "openrouter", "openrouter_cheap"):
        earlier = model_use.acceptance_in({key: {"granted_at": "2026-10-13T09:00:00Z",
                                                 "data_flow": "passages_and_answers"}})
        assert earlier is not None and earlier.key == key and earlier.disclosure_version is None
    assert model_use.acceptance_in({"codex": {"granted_at": "2026-10-13T09:00:00Z"}}).key == "codex"
    # The upload-only OKs are not an OK to use AI, nor is a record without its date or with another flow.
    assert model_use.acceptance_in({"whole_files": {"granted_at": "x", "data_flow": "whole_files"}}) is None
    assert model_use.acceptance_in({"whole_files_zai": {"granted_at": "x", "data_flow": "whole_files"}}) is None
    assert model_use.acceptance_in({"whole_files": {"granted_at": "x"}}) is None
    assert model_use.acceptance_in({"model_use": {"data_flow": "all_model_use"}}) is None
    assert model_use.acceptance_in({"model_use": {"granted_at": "x", "data_flow": "passages_and_answers"}}) is None
    assert model_use.acceptance_in({}) is None and model_use.acceptance_in(None) is None


def test_the_ok_is_read_live_from_the_library_and_from_this_computer(tmp_path):
    root = create_basic_vault(tmp_path / "first").root
    other = create_basic_vault(tmp_path / "second").root
    lookup = model_use.AcceptanceLookup(root)
    assert not lookup() and not model_use.accepted(other)
    say_ok(root)
    # The same lookup, never rebuilt, sees the OK at once: a client built before it was given is covered.
    assert lookup() and model_use.recorded_acceptance(root).where == "library"
    assert not model_use.accepted(other)
    # Mirrored to this computer's AI defaults (as the sheet does), it covers every library opened here.
    machine = global_ai_defaults_path()
    machine.parent.mkdir(parents=True, exist_ok=True)
    machine.write_text("", encoding="utf-8")
    apply_config_updates(machine, model_use.record_updates("2026-11-21T09:00:00+00:00"))
    assert model_use.recorded_acceptance(other).where == "machine"


# -- the dispatch trap of every physical adapter --------------------------------------------------------------


class Trap:
    """One adapter behind the factory, its fake transport, the call a feature makes, and what reached the wire."""

    def __init__(self, client, run, sent):
        self.client, self.run, self.sent = client, run, sent


def _openrouter(root, monkeypatch, responses):
    fake = install_fake_openai(monkeypatch, *responses)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    client = make_ai_provider_client_from_profile(
        "openrouter", AIProviderConfig(type="openrouter", model="test/model", response_format="json_object"), root)
    return Trap(client, lambda: execute_structured_operation(client, purpose="t", prompt="Say ok", result_model=Answer),
                lambda: sum(len(instance.requests) for instance in fake.instances))


def _throttled():
    error = RuntimeError("rate limited")
    error.status_code = 429
    error.response = types.SimpleNamespace(headers={"retry-after-ms": "0"})
    return error


def trap_openrouter(root, monkeypatch, stack):
    return _openrouter(root, monkeypatch, [ANSWER, ANSWER])


def trap_openrouter_retry(root, monkeypatch, stack):
    # The first physical request is throttled and retried at once: both are admitted only after the OK.
    return _openrouter(root, monkeypatch, [_throttled(), ANSWER, ANSWER])


def trap_embeddings(root, monkeypatch, stack):
    vector = types.SimpleNamespace(data=[types.SimpleNamespace(embedding=[0.1, 0.2, 0.3], index=0)], usage=None)
    fake = install_fake_openai(monkeypatch, embeddings=[vector, vector])
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    client = make_ai_provider_client_from_profile(
        "openrouter_embedding", AIProviderConfig(type="openai_embedding", model="qwen/qwen3-embedding-8b",
                                                 base_url="https://openrouter.ai/api/v1",
                                                 api_key_env="OPENROUTER_API_KEY", dimensions=3), root)
    return Trap(client, lambda: client.embed(["a passage"], "similarity"),
                lambda: sum(len(instance.embedding_requests) for instance in fake.instances))


def trap_decider(root, monkeypatch, stack):
    server = stack.enter_context(fake_decisions(dialect="openrouter"))
    monkeypatch.setenv("OPENROUTER_API_KEY", server.key)
    client = make_ai_provider_client_from_profile(
        "test_decider", DeciderProviderConfig(api="openrouter", base_url=server.base_url), root)
    return Trap(client, lambda: client.decide("A review.", {"q": NoulQuestion("Is it a review?")}, purpose="t"),
                lambda: len(server.requests))


def trap_plan(root, monkeypatch, stack):
    server = stack.enter_context(fake_chatgpt())
    sign_in(PlanSession(), server)
    server.default_reply = lambda _body: Reply(events=completed_events(ANSWER))
    client = make_ai_provider_client_from_profile(
        "chatgpt", ChatGPTPlanProviderConfig(model="gpt-test-fast", base_url=server.base_url, timeout_seconds=10),
        root)
    return Trap(client, lambda: execute_structured_operation(client, purpose="t", prompt="Say ok", result_model=Answer),
                lambda: len(server.requests))


ADAPTERS = {
    "openrouter": trap_openrouter,
    "openrouter_retry": trap_openrouter_retry,
    "embeddings": trap_embeddings,
    "decider": trap_decider,
    "chatgpt_plan": trap_plan,
}


@pytest.mark.parametrize("adapter", sorted(ADAPTERS))
@pytest.mark.parametrize("thread", ["request", "background"])
def test_no_adapter_sends_anything_before_the_ok_and_each_proceeds_once_it_is_given(tmp_path, monkeypatch, adapter,
                                                                                      thread):
    from contextlib import ExitStack

    root = create_basic_vault(tmp_path / "library").root
    with ExitStack() as stack:
        trap = ADAPTERS[adapter](root, monkeypatch, stack)

        def run():
            if thread == "request":
                return trap.run()
            # A thread of its own carries no context of the request: the client's bound lookup still holds.
            out: dict = {}

            def target():
                try:
                    out["value"] = trap.run()
                except BaseException as exc:  # noqa: BLE001 - surfaced below
                    out["error"] = exc

            worker = threading.Thread(target=target)
            worker.start()
            worker.join(timeout=30)
            if "error" in out:
                raise out["error"]
            return out.get("value")

        assert model_use.client_waiting(trap.client)
        with pytest.raises(model_use.ModelUseNotAccepted):
            run()
        assert trap.sent() == 0
        say_ok(root)
        run()
        first = trap.sent()
        assert first == (2 if adapter == "openrouter_retry" else 1)
        # Never asked again: the next call goes straight out.
        run()
        assert trap.sent() == first + 1


def test_the_video_adapter_asks_for_the_ok_too(tmp_path, monkeypatch):
    root = create_basic_vault(tmp_path / "library").root
    sent: list[str] = []

    def http(method, url, headers, body, timeout):
        sent.append(f"{method} {url}")
        return 200, {}, b'{"data": []}'

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    config = load_config(root / "learnloop.toml").model_copy(deep=True)
    config.ai.providers["openrouter_video"] = AIProviderConfig(type="openrouter", model="video/model")
    client = make_video_generation_client(config, root, provider_name="openrouter_video", http=http)
    from learnloop.ai.providers.openrouter_video import VideoGenerationRequest

    with pytest.raises(model_use.ModelUseNotAccepted):
        client.submit(VideoGenerationRequest(prompt="A short clip of a circle.", duration_seconds=4))
    assert sent == []


def test_a_fallback_provider_is_held_to_the_same_ok(tmp_path, monkeypatch):
    """The learner's "Use OpenRouter instead" picks a provider for one action; it is not the OK."""

    fake = install_fake_openai(monkeypatch, ANSWER, ANSWER)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    root = create_basic_vault(tmp_path / "library").root
    config = load_config(root / "learnloop.toml")
    with plan_fallback.request(None, "test.learner_request"):
        plan_fallback.grant_origin(root, "test.learner_request", ["tutor_qa"])
        chosen = ready_client_for_task(root, config, "tutor_qa")
    assert chosen.ready and chosen.provider_name == "openrouter"
    with pytest.raises(model_use.ModelUseNotAccepted):
        execute_structured_operation(chosen.client, purpose="t", prompt="Say ok", result_model=Answer)
    assert sum(len(instance.requests) for instance in fake.instances) == 0
    say_ok(root)
    execute_structured_operation(chosen.client, purpose="t", prompt="Say ok", result_model=Answer)
    assert sum(len(instance.requests) for instance in fake.instances) == 1


# -- jobs wait, and the OK resumes them once ----------------------------------------------------------------------


def test_jobs_wait_for_the_ok_and_saying_it_resumes_each_once(tmp_path, monkeypatch):
    fake = install_fake_openai(monkeypatch, ANSWER, ANSWER, ANSWER)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    ran: dict[str, int] = {}

    def model_job(ctx: JobContext) -> dict:
        ran[ctx.job["job_type"]] = ran.get(ctx.job["job_type"], 0) + 1
        client = make_ai_provider_client_from_profile(
            "openrouter", AIProviderConfig(type="openrouter", model="test/model", response_format="json_object"),
            ctx.vault_root)
        return execute_structured_operation(client, purpose="t", prompt="Say ok", result_model=Answer).model_dump()

    runner = IngestRunner(Repository(tmp_path / "state.sqlite"), vault_root=tmp_path, worker_id="w1", clock=CLOCK,
                          handlers={"practice_expansion": model_job, "a_job_that_reaches_a_model": model_job})
    runner.enqueue_batch("test", [JobSpec("practice_expansion")])
    runner.enqueue_batch("test", [JobSpec("a_job_that_reaches_a_model")])
    runner.drain()
    runner.drain()  # a waiting job is not tried again
    # A model job waits before it starts; another that reaches a model waits from the refusal itself.
    assert ran == {"a_job_that_reaches_a_model": 1}
    assert sum(len(instance.requests) for instance in fake.instances) == 0
    jobs = runner.repo.active_ingest_jobs()
    assert [job["status"] for job in jobs] == ["waiting_for_input", "waiting_for_input"]
    assert all(job["result"]["waiting_for_input"] == {"code": "waiting_for_ok"} for job in jobs)
    assert all(job.get("error") is None for job in jobs)

    (tmp_path / "learnloop.toml").write_text("", encoding="utf-8")
    say_ok(tmp_path)
    resumed = runner.resume_waiting_for_ok()
    assert sorted(resumed) == sorted(job["id"] for job in jobs)
    assert runner.resume_waiting_for_ok() == []  # once: nothing waits any more
    runner.drain()
    assert ran == {"a_job_that_reaches_a_model": 2, "practice_expansion": 1}
    assert sum(len(instance.requests) for instance in fake.instances) == 2
    assert runner.repo.active_ingest_jobs() == []


# -- the learner's routes ------------------------------------------------------------------------------------------


def _library(tmp_path: Path, calls: Calls | None = None):
    root = fresh_library(tmp_path)
    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK,
                         services=fake_services(route(), calls=calls))
    return root, ctx


def test_adding_a_book_reads_it_at_once_and_its_questions_wait_for_the_one_ok(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import first_run

    monkeypatch.setattr(first_run, "authoring_route_for", lambda vault: route())
    calls = Calls()
    root, ctx = _library(tmp_path, calls)
    added = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})
    source_id = added["items"][0]["sourceId"]
    # Reading is local and starts at once; the desktop asks for the OK now.
    assert added["waitingForOk"] is True and added["opened"]["sourceId"] == source_id
    from learnloop.content.pipeline.add_source import latest_auto_outcome

    assert latest_auto_outcome(ctx.repository, source_id)["reason"] == "needs_consent"
    assert calls.inventory_calls == 0 and calls.synthesis_calls == 0
    first = call(ctx, "connect_ai", {"provider": "current"})
    assert first["released"] == [source_id] and first["consented"] is True
    assert calls.inventory_calls > 0
    sent = (calls.inventory_calls, calls.synthesis_calls)
    again = call(ctx, "connect_ai", {"provider": "current"})
    assert again["released"] == [] and again["resumed"] == []
    assert (calls.inventory_calls, calls.synthesis_calls) == sent
    assert call(ctx, "get_ai_connection", {})["needs"] is None


def _first_span(ctx, source_id: str) -> tuple[str, str]:
    from learnloop.content.pipeline.add_source import _completed_extraction

    extraction_id = _completed_extraction(ctx.repository, source_id)[1]
    ir = ctx.repository.load_document_ir(extraction_id)
    return extraction_id, next(block.span_id for block in ir.blocks if block.text.strip())


@pytest.mark.parametrize("origin", ["desktop", "phone"])
def test_the_readers_ask_waits_for_the_ok_and_sends_nothing(tmp_path, monkeypatch, origin):
    fake = install_fake_openai(monkeypatch, ANSWER)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    _root, ctx = _library(tmp_path)
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]["sourceId"]
    extraction_id, span_id = _first_span(ctx, source_id)
    params = {"extraction_id": extraction_id, "span_id": span_id, "question": "What does this mean?"}
    phone = RequestOrigin(device_id="dev_phone", phone_reader=True) if origin == "phone" else None
    with ctx.acting_as(phone), pytest.raises(SidecarError) as caught:
        call(ctx, "reader.ask", params)
    assert caught.value.code == "waiting_for_ok"
    assert caught.value.message == model_use.WAITING_MESSAGE
    assert sum(len(instance.requests) for instance in fake.instances) == 0
    # Nothing of the question was stored: it is the learner's to send again after the OK.
    assert call(ctx, "reader.ask_history", {"extraction_id": extraction_id})["exchanges"] == []


def test_the_section_quick_check_waits_for_the_ok_and_queues_nothing(tmp_path):
    _root, ctx = _library(tmp_path)
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]["sourceId"]
    extraction_id, _span = _first_span(ctx, source_id)
    ir = ctx.repository.load_document_ir(extraction_id)
    from learnloop.reader import reader_guidance as RG

    section_id = RG.extraction_sections(ir)[0][0]["id"]
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.author_section_question", {"extraction_id": extraction_id, "section_id": section_id})
    assert caught.value.code == "waiting_for_ok"
    assert ctx.repository.ingest_jobs_by_types(("reader_quick_check",)) == []


def test_the_goal_resolver_waits_for_the_ok_before_the_goal_is_made(tmp_path):
    root, ctx = _library(tmp_path)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "curriculum.create_deliverable", {"sentence": "Pass the probability midterm"})
    assert caught.value.code == "waiting_for_ok"
    assert call(ctx, "curriculum.deliverables", {})["deliverables"] == []


def test_the_reading_path_judge_waits_and_judges_once_the_ok_is_given(tmp_path):
    from learnloop.source_retrieval import reading_paths as RP

    root, ctx = _library(tmp_path)
    vault, _repository = ctx.require_vault()
    problem = RP.admission_problem(vault, ctx.repository)
    assert problem is not None and problem.reason == "waiting_for_ok"
    # A refusal re-asked on every read: it holds only while the OK is missing.
    assert "waiting_for_ok" in RP.ADMISSION_REASONS
    say_ok(root)
    after = RP.admission_problem(vault, ctx.repository)
    assert after is None or after.reason != "waiting_for_ok"


def test_quick_add_waits_for_the_ok_before_it_creates_anything(tmp_path):
    _root, ctx = _library(tmp_path)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "confirm_quick_add", {"source": "probability_book.md", "subject_id": "nothing_yet"})
    assert caught.value.code == "waiting_for_ok"


def test_an_unchecked_model_call_in_any_rpc_answers_waiting_for_ok(tmp_path, monkeypatch):
    """The sidecar's own backstop: a request that reaches a model call no early check stopped."""

    from learnloop_sidecar import server

    root, ctx = _library(tmp_path)

    def handler(_ctx, _params):
        raise model_use.ModelUseNotAccepted()

    spec = METHOD_REGISTRY["get_ai_connection"]
    monkeypatch.setitem(METHOD_REGISTRY, "get_ai_connection", spec.__class__(**{**spec.__dict__, "handler": handler}))
    response = server._handle(ctx, {"jsonrpc": "2.0", "id": 1, "method": "get_ai_connection", "params": {}})
    assert response["error"]["data"]["code"] == "waiting_for_ok"
    assert response["error"]["message"] == model_use.WAITING_MESSAGE
