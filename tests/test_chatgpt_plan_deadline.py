"""Live output extends only ingest-owned calls; all waits remain bounded."""
from types import SimpleNamespace

import pytest

from learnloop.ai.errors import AIInterrupted, AITurnTimeout
from learnloop.ai.execution import observe_model_calls, single_request
from learnloop.ai.providers.chatgpt_plan import ChatGPTPlanProviderClient
from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import execute_structured_operation
from learnloop.config.schema import ChatGPTPlanProviderConfig
from learnloop.content.pipeline.runner import JobSpec, retried_on_its_own
from tests.ingest_runner_helpers import _runner
from tests.plan_deadline_fakes import Session, completed, delta, install_stream


class Answer(WireModel):
    ok: bool


def client():
    return ChatGPTPlanProviderClient("plan", ChatGPTPlanProviderConfig(
        model="fake", base_url="http://127.0.0.1", timeout_seconds=180), session=Session())


def ask(transport, *, background=True):
    # Duck request lets the behavioral regression run against the old contract.
    return transport.complete(SimpleNamespace(
        purpose="synthesis", prompt="unchanged", result_model=Answer, timeout_seconds=480,
        output_budget_tokens=None, workspace=None, reasoning_effort=None, background=background))


def test_live_background_stream_completes_past_old_total(monkeypatch):
    clock, requests, connections = install_stream(monkeypatch, [
        *[(t, delta()) for t in range(100, 701, 100)], (710, completed())])
    with single_request():
        assert ask(client()).ok
    assert clock.now == 710
    assert len(requests) == 1 and connections[0].closed
    assert "background" not in requests[0] and "tools" not in requests[0]
    assert not any(t.active for t in clock.timers)


def test_same_live_foreground_stream_keeps_total_deadline(monkeypatch):
    clock, requests, connections = install_stream(monkeypatch, [
        *[(t, delta()) for t in range(100, 701, 100)], (710, completed())])
    with single_request(), pytest.raises(AITurnTimeout):
        ask(client(), background=False)
    assert len(requests) == 1
    assert any(t.at == 480 for t in clock.timers)
    assert connections[0].shutdown_at == 480


@pytest.mark.parametrize("events,cut_at", [
    ([(100, delta()), (300, completed())], 280),
    ([(100, {"type": "response.created"}), (200, completed())], 180),
    ([(100, delta("")), (200, completed())], 180),
])
def test_silent_background_stream_is_cut(monkeypatch, events, cut_at):
    clock, requests, _ = install_stream(monkeypatch, events)
    receipts = []
    with single_request(), observe_model_calls(lambda action, row: receipts.append((action, row))):
        with pytest.raises(AITurnTimeout) as failure:
            ask(client())
    assert failure.value.reason == "idle"
    assert any(t.at == cut_at for t in clock.timers)
    finish = [row for action, row in receipts if action == "finish"][-1]
    assert finish["status"] == "failed" and finish["error_type"] == "AITurnTimeout"
    assert finish["finish_reason"] == "idle"
    assert finish.get("output_tokens") is None and finish.get("output_text") is None
    assert len(requests) == 1


def test_reasoning_output_counts_as_progress(monkeypatch):
    install_stream(monkeypatch, [(t, delta(kind="response.reasoning_text.delta")) for t in range(100, 701, 100)]
                   + [(710, completed())])
    assert ask(client()).ok


def test_endless_background_stream_hits_ceiling_without_job_retry(tmp_path, monkeypatch):
    clock, requests, _ = install_stream(monkeypatch, [(t, delta()) for t in range(100, 1501, 100)])

    def handler(ctx):
        with single_request():
            return execute_structured_operation(client(), purpose="probe", prompt="unchanged", result_model=Answer,
                                                timeout_seconds=480)

    runner = _runner(tmp_path, handlers={"bootstrap_synthesis": handler})
    batch = runner.enqueue_batch("import", [JobSpec("bootstrap_synthesis", payload={"auto_build": {}})])
    runner.drain()
    job = runner.repo.ingest_jobs_for_batch(batch)[0]
    assert len(requests) == 1
    assert job["status"] == "failed" and job["error"]["code"] == "timeout_ceiling"
    assert not retried_on_its_own(job)
    assert any(t.at == 1200 for t in clock.timers)


def test_idle_cut_retries_once_and_records_failed_state(tmp_path, monkeypatch):
    _, requests, _ = install_stream(monkeypatch, [(100, delta()), (300, completed())])

    def handler(ctx):
        with single_request():
            return execute_structured_operation(client(), purpose="probe", prompt="unchanged", result_model=Answer,
                                                timeout_seconds=480)

    runner = _runner(tmp_path, handlers={"inventory": handler})
    batch = runner.enqueue_batch("import", [JobSpec("inventory", payload={"auto_build": {}})])
    runner.drain()
    job = runner.repo.ingest_jobs_for_batch(batch)[0]
    assert len(requests) == 2
    assert job["status"] == "failed" and job["error"]["code"] == "timeout"
    assert retried_on_its_own(job)


def test_interrupt_during_long_background_stream_is_immediate(monkeypatch):
    transport = client()
    clock, requests, _ = install_stream(monkeypatch, [(t, delta()) for t in range(100, 901, 100)],
                                       interrupt_at=lambda t: transport.interrupt() if t >= 600 else None)
    with single_request(), pytest.raises(AIInterrupted):
        ask(transport)
    assert clock.now == 600 and len(requests) == 1
    assert not any(t.active for t in clock.timers)


@pytest.mark.parametrize("action", ["stop", "quit"])
def test_job_host_stops_long_background_stream(tmp_path, monkeypatch, action):
    caught = []

    def handler(ctx):
        transport = client()
        ctx.bind_interruptible(transport)
        try:
            with single_request():
                execute_structured_operation(transport, purpose="probe", prompt="unchanged", result_model=Answer,
                                             timeout_seconds=480)
        except AIInterrupted:
            caught.append(clock.now)
            raise

    runner = _runner(tmp_path, handlers={"bootstrap_synthesis": handler})
    batch = runner.enqueue_batch("import", [JobSpec("bootstrap_synthesis", payload={"auto_build": {}})])
    job_id = runner.repo.ingest_jobs_for_batch(batch)[0]["id"]

    def interrupt(now):
        if now == 600:
            if action == "stop":
                assert runner.interrupt_job(job_id)
            else:
                runner.halt()

    clock, requests, connections = install_stream(monkeypatch, [(t, delta()) for t in range(100, 901, 100)],
                                                 interrupt_at=interrupt)
    runner.drain()
    assert caught == [600] and len(requests) == 1 and connections[0].closed
    assert not any(t.active for t in clock.timers)


def test_background_flag_is_explicit_scoped_and_inherited_by_inventory_workers(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from contextvars import copy_context
    from learnloop.ai.execution import background_model_work
    from tests.structured_ai import StructuredClientFake

    seen = []

    class Capture(StructuredClientFake):
        def complete(self, request):
            seen.append(request.background)
            return Answer(ok=True)

    transport = Capture()

    def call():
        return execute_structured_operation(transport, purpose="synthesis", prompt="unchanged", result_model=Answer)

    call()
    with background_model_work(), ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(copy_context().run, call).result()
    call()
    assert seen == [False, True, False]


def test_job_override_preserves_original_profile_as_idle_window(tmp_path):
    from learnloop.ai.client import make_ai_provider_client
    from learnloop.config import LearnLoopConfig

    config = LearnLoopConfig()
    config.ai.providers["test_plan"] = ChatGPTPlanProviderConfig(model="fake", timeout_seconds=60)
    transport = make_ai_provider_client(config, tmp_path, provider_name="test_plan", timeout_seconds=480)
    assert transport.profile.timeout_seconds == 480
    assert transport.idle_timeout_seconds == 60
    config.ai.providers["test_plan"] = ChatGPTPlanProviderConfig(model="fake")
    transport = make_ai_provider_client(config, tmp_path, provider_name="test_plan", timeout_seconds=480)
    assert transport.idle_timeout_seconds == config.ai.timeout_seconds == 180


def test_idle_watchdog_can_shutdown_a_socket_detached_by_http_close(monkeypatch):
    _, _, connections = install_stream(monkeypatch, [(100, delta()), (300, completed())], detach_socket=True)
    with pytest.raises(AITurnTimeout):
        ask(client())
    assert connections[0].shutdown_at == 280


def test_background_flag_does_not_change_wire_request(monkeypatch):
    _, requests, _ = install_stream(monkeypatch, [(100, completed())])
    assert ask(client()).ok
    assert ask(client(), background=False).ok
    assert requests[0] == requests[1]


def test_background_token_wait_is_idle_bounded_and_sends_nothing(monkeypatch):
    clock, requests, _ = install_stream(monkeypatch, [(100, completed())])
    transport = client()

    def token(**kwargs):
        assert kwargs["timeout"] == 180
        clock.advance(180)
        assert kwargs["cancelled"]()
        return "fake-token"

    monkeypatch.setattr(transport.session, "access_token", token)
    with pytest.raises(AITurnTimeout) as failure:
        ask(transport)
    assert failure.value.reason == "idle"
    assert requests == []


def test_socket_timeout_at_ceiling_is_not_mistaken_for_retryable_idle(monkeypatch):
    from learnloop.ai.chatgpt_plan import responses

    clock, _, _ = install_stream(monkeypatch, [])
    connection = responses.http.client.HTTPConnection

    def expired_headers(self):
        # The socket timeout can win the race with a scheduled watchdog.
        clock.now = 10
        raise TimeoutError("headers")

    monkeypatch.setattr(connection, "getresponse", expired_headers)
    stream = responses.ResponsesStream("http://127.0.0.1")
    with pytest.raises(responses.StreamCancelled) as failure:
        stream.send({}, access_token="fake-token", timeout=10, idle_timeout=180)
    assert failure.value.reason == "ceiling"
