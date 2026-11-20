"""A stalled JSON answer is abandoned without losing its delivery measurements."""
import json
from types import SimpleNamespace

import pytest

from learnloop.ai.chatgpt_plan import responses
from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable
from learnloop.ai.execution import observe_model_calls, single_request
from learnloop.ai.providers import chatgpt_plan
from learnloop.ai.schemas import WireModel
from learnloop.ai.strict_schema import strict_output_schema
from learnloop.ai.transport import execute_structured_operation
from learnloop.config.schema import ChatGPTPlanProviderConfig
from learnloop.db.connection import connect
from learnloop.content.pipeline.runner import JobSpec, retried_on_its_own
from learnloop.content.synthesis.ai_contracts import (
    SourceSetSynthesis, SourceSetSynthesisContext, source_set_synthesis_prompt,
)
from tests.ingest_runner_helpers import _runner
from tests.plan_deadline_fakes import Session, completed, delta, install_stream


class Answer(WireModel):
    ok: bool


def client():
    return chatgpt_plan.ChatGPTPlanProviderClient("plan", ChatGPTPlanProviderConfig(
        model="fake", base_url="http://127.0.0.1", timeout_seconds=180), session=Session())


def ask(transport):
    return transport.complete(SimpleNamespace(
        purpose="synthesis", prompt="unchanged", result_model=Answer, timeout_seconds=480,
        output_budget_tokens=None, workspace=None, reasoning_effort=None, background=True))


def stream(monkeypatch, events, **kwargs):
    clock, requests, connections = install_stream(monkeypatch, events, **kwargs)
    monkeypatch.setattr(chatgpt_plan, "_sleep", lambda delay: clock.advance(clock.now + delay))
    monkeypatch.setattr(chatgpt_plan, "_random", lambda: 1)
    return clock, requests, connections


def runaway():
    # Cross delta boundaries and end a delta with non-whitespace: a suffix-only
    # check misses a run that crosses the limit earlier in that same delta.
    return [(9, delta('{"ok":')), (10, delta(" " * 1000)),
            (11, delta("\n" + " " * 999)), (12, delta(" true}")), (13, completed())]


@pytest.mark.parametrize("one_facet_per_skill", [False, True])
def test_built_synthesis_prompt_agrees_with_required_nullable_integration(one_facet_per_skill):
    prompt = source_set_synthesis_prompt(SourceSetSynthesisContext(
        source_set_id="set", subject_id="subject", mode="bootstrap", one_facet_per_skill=one_facet_per_skill))
    assert "`integration` key is always present" in prompt
    assert "set `integration` to null" in prompt
    assert "OMIT it" not in prompt and "leave `integration` absent" not in prompt
    recipe = strict_output_schema(SourceSetSynthesis)["$defs"]["SynthRecipe"]
    assert recipe["required"] == ["id", "composition", "all_of", "any_of", "integration"]
    assert {"type": "null"} in recipe["properties"]["integration"]["anyOf"]


def test_runaway_is_cut_then_transient_retry_returns_good_answer(monkeypatch):
    clock, requests, connections = stream(monkeypatch, lambda n: runaway() if n == 1 else [(9, completed())])
    receipts = []
    with observe_model_calls(lambda action, row: receipts.append((action, row))):
        assert ask(client()).ok
    assert len(requests) == 2
    assert requests[0] == requests[1]
    assert connections[0].shutdown_at == 12
    assert clock.now == 22
    finishes = [r for action, r in receipts if action == "finish"]
    assert finishes[0]["error_type"] == "ChatGPTPlanTransient"
    assert finishes[0]["finish_reason"] == "runaway_whitespace"
    assert finishes[1]["status"] == "completed"
    assert not any(t.active for t in clock.timers)


def test_every_try_runs_away_then_job_stays_failed(tmp_path, monkeypatch):
    _, requests, connections = stream(monkeypatch, runaway())

    def handler(ctx):
        return execute_structured_operation(client(), purpose="probe", prompt="unchanged", result_model=Answer,
                                            timeout_seconds=480)

    runner = _runner(tmp_path, handlers={"bootstrap_synthesis": handler})
    batch = runner.enqueue_batch("import", [JobSpec("bootstrap_synthesis", payload={"auto_build": {}})])
    runner.drain()
    job = runner.repo.ingest_jobs_for_batch(batch)[0]
    assert len(requests) == 6
    assert job["status"] == "failed" and job["error"]["code"] == "ChatGPTPlanTransient"
    assert retried_on_its_own(job)
    runner.drain()
    assert len(requests) == 6
    assert all(c.shutdown_at is not None for c in connections)
    with connect(runner.repo.sqlite_path) as connection:
        receipts = connection.execute(
            "SELECT finish_reason, usage_json, output_text FROM model_call_receipts WHERE purpose='responses_request'"
        ).fetchall()
    assert len(receipts) == 6
    for receipt in receipts:
        assert receipt["finish_reason"] == "runaway_whitespace"
        assert receipt["output_text"] is None
        progress = json.loads(receipt["usage_json"])["chatgpt_plan"]
        assert progress["output_characters"] == 2012
        assert progress["seconds_to_first_output"] == 9


@pytest.mark.parametrize("terminal", ["runaway", "failed", "incomplete", "ended", "idle"])
def test_failed_receipt_records_delivery_without_partial_text(monkeypatch, terminal):
    prefix = [(2, {"type": "response.created"}), (9, delta('{"ok":'))]
    tails = {
        "runaway": [(10, delta(" " * 2001)), (11, completed())],
        "failed": [(10, {"type": "response.failed", "response": {"status": "failed"}})],
        "incomplete": [(10, {"type": "response.incomplete", "response": {"status": "incomplete"}})],
        "ended": [(10, None)],
        "idle": [(200, completed())],
    }
    stream(monkeypatch, prefix + tails[terminal])
    receipts = []
    with single_request(), observe_model_calls(lambda action, row: receipts.append((action, row))):
        with pytest.raises(AIProviderUnavailable):
            ask(client())
    finish = [r for action, r in receipts if action == "finish"][-1]
    progress = json.loads(finish["usage_json"])["chatgpt_plan"]
    assert progress["output_characters"] == 6 + (2001 if terminal == "runaway" else 0)
    assert progress["seconds_to_first_output"] == 9
    assert progress["request_id"] == "fake-request"
    assert finish.get("output_text") is None and finish.get("output_tokens") is None


def test_single_request_preserves_transient_code_and_does_not_retry(monkeypatch):
    _, requests, _ = stream(monkeypatch, runaway())
    with single_request(), pytest.raises(chatgpt_plan.ChatGPTPlanTransient) as failure:
        ask(client())
    assert failure.value.provider_error["code"] == "runaway_whitespace"
    assert len(requests) == 1


def test_long_indented_structured_answer_is_not_cut(monkeypatch):
    class LongAnswer(WireModel):
        rows: list[str]

    text = json.dumps({"rows": ["x" * 100 for _ in range(1000)]}, indent=6)
    assert len(text) > 100_000
    events = [(i / 300, delta(text[i:i + 101])) for i in range(0, len(text), 101)]
    final = completed()
    final["response"]["output"][0]["content"][0]["text"] = text
    events.append((len(text) / 300 + 1, final))
    _, requests, connections = stream(monkeypatch, events)
    body = responses.request_body(model="fake", instructions="", prompt="",
                                  text_format=client()._text_format(LongAnswer))
    result = responses.ResponsesStream("http://127.0.0.1").send(body, access_token="fake-token", timeout=1200)
    assert result.text == text
    assert len(requests) == 1 and connections[0].shutdown_at is None


@pytest.mark.parametrize("text_format", [None, {"type": "text"}, {"type": "json_object"}])
def test_non_schema_whitespace_is_not_watched(monkeypatch, text_format):
    _, requests, connections = stream(monkeypatch, [(9, delta(" " * 100_000)), (10, completed())])
    body = responses.request_body(model="fake", instructions="", prompt="", text_format=text_format)
    result = responses.ResponsesStream("http://127.0.0.1").send(body, access_token="fake-token", timeout=180)
    assert result.response["status"] == "completed"
    assert len(requests) == 1 and connections[0].shutdown_at is None


def test_interrupt_during_runaway_wins_without_retry(monkeypatch):
    transport = client()
    clock, requests, connections = stream(monkeypatch, runaway(),
        interrupt_at=lambda t: transport.interrupt() if t >= 11 else None)
    with pytest.raises(AIInterrupted):
        ask(transport)
    assert clock.now == 11 and len(requests) == 1 and connections[0].shutdown_at == 11
    assert not any(t.active for t in clock.timers)
