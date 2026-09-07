from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop.ai.errors import AIOutputTruncated, AITurnTimeout
from learnloop.ai.execution import generation_limit, observe_model_calls
from learnloop.ai.providers.openai_chat import OpenAIChatProviderClient
from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import execute_structured_operation
from learnloop.config import AIProviderConfig
from learnloop.db.repositories import Repository
from learnloop.content.synthesis import source_unit_inventory as inventory
from tests.openai_fakes import install_fake_openai
from tests.test_source_inventory import FakeInventoryClient, _block, _ir, _persist, _register_revision, _CLOCK


class Answer(WireModel):
    answer: str


def test_evidence_followup_keeps_the_full_inventory_in_its_cached_prefix():
    from dataclasses import replace
    from learnloop.content.synthesis.ai_contracts import SourceSetSynthesisContext, source_set_synthesis_prompt
    context = SourceSetSynthesisContext(source_set_id="set", subject_id="subject", mode="bootstrap", brief={}, unit_inventories=[{"text": "stable inventory " * 1000}], exam_profile={}, registry_index={}, resolved_spans=[], shard_ordinal=0, shard_count=1)
    first = source_set_synthesis_prompt(context)
    second = source_set_synthesis_prompt(replace(context, resolved_spans=[{"text": "additional evidence"}]))
    prefix = first[:first.index('"resolved_spans":')]
    assert second.startswith(prefix)
    assert "stable inventory " * 1000 in prefix


def test_inventory_retry_reuses_validated_window_after_interruption(tmp_path, monkeypatch):
    repo = Repository(tmp_path / "state.sqlite")
    _register_revision(repo)
    document = _ir([("u1", "Chapter", [_block("s1", "An eigenvector scales under a matrix.")], "hash1", 1)])
    _persist(repo, document, revision_id="rev1", extraction_id="ext1")
    window = inventory.build_inventory_windows(document, "u1", input_budget_tokens=20000)[0]
    monkeypatch.setattr(inventory, "build_inventory_windows", lambda *_args, **_kwargs: [{**window, "window_ordinal": 1}, {**window, "window_ordinal": 2}])
    original = inventory.request_source_unit_inventory
    interrupted = False
    def request(client, context):
        nonlocal interrupted
        if context.unit_view["window_ordinal"] == 2 and not interrupted:
            interrupted = True
            raise AITurnTimeout("interrupted window")
        return original(client, context)
    monkeypatch.setattr(inventory, "request_source_unit_inventory", request)
    client = FakeInventoryClient()
    with pytest.raises(AITurnTimeout):
        inventory.run_unit_inventory(repo, "ext1", "u1", role="reference", client=client, clock=_CLOCK)
    assert not repo.unit_inventories_for_revision("rev1")
    with repo.connection() as connection:
        assert connection.execute("SELECT count(*) FROM model_work_checkpoints").fetchone()[0] == 1
    result = inventory.run_unit_inventory(repo, "ext1", "u1", role="reference", client=client, clock=_CLOCK)
    assert result.usage["reused_windows"] == 1
    assert result.usage["calls"] == 1
    assert len(client.calls) == 2


def test_parallel_inventory_drains_checkpoints_and_stops_new_units_after_failure(tmp_path, monkeypatch):
    from threading import Event
    from learnloop.content.pipeline import jobs
    from learnloop.content.pipeline.runner import IngestRunner, JobSpec, RunnerServices
    repo = Repository(tmp_path / "state.sqlite")
    _register_revision(repo)
    document = _ir([(f"u{n}", f"Chapter {n}", [_block(f"s{n}", f"Eigenvector section {n}.")], f"hash{n}", n) for n in range(1, 4)])
    _persist(repo, document, revision_id="rev1", extraction_id="ext1")
    monkeypatch.setattr(jobs, "_MAX_INVENTORY_WORKERS", 2)
    first_started, interrupted = Event(), Event()
    calls = []
    class Client(FakeInventoryClient):
        def supports(self, capability):
            return capability == "interrupt" or super().supports(capability)
        def interrupt(self):
            interrupted.set()
        def run_source_unit_inventory(self, context):
            calls.append(context.unit_id)
            if context.unit_id == "u1":
                first_started.set()
                assert interrupted.wait(5), "failed lane did not interrupt its peers"
            if context.unit_id == "u2":
                assert first_started.wait(5)
                raise AITurnTimeout("unit two failed")
            return super().run_source_unit_inventory(context)
    runner = IngestRunner(repo, vault_root=tmp_path, worker_id="worker", clock=_CLOCK, services=RunnerServices(inventory_client_factory=lambda ctx: Client()))
    batch = runner.enqueue_batch("import_inventory", [JobSpec("inventory", {"extraction_id": "ext1", "units": [{"unit_id": f"u{n}", "role": "reference"} for n in range(1, 4)]})])
    runner.drain()
    assert repo.ingest_jobs_for_batch(batch)[0]["status"] == "failed"
    assert sorted(calls) == ["u1", "u2"]
    with repo.connection() as connection:
        saved = connection.execute("SELECT result_json FROM model_work_checkpoints").fetchall()
    assert len(saved) == 1 and '"u1"' in saved[0][0]


@pytest.mark.parametrize("finish_reason", ["length", "stop"])
def test_truncation_or_exhausted_repair_budget_records_usage_without_repaying(tmp_path, monkeypatch, finish_reason):
    module = install_fake_openai(monkeypatch)
    monkeypatch.setenv("TEST_KEY", "unused")
    client = OpenAIChatProviderClient("test", AIProviderConfig(type="openai_chat", base_url="https://unused.invalid", api_key_env="TEST_KEY", model="fake", max_tokens=100))
    assert module.instances[0].kwargs["max_retries"] == 0
    requests = []
    def create(**kwargs):
        requests.append(kwargs)
        return SimpleNamespace(id="response-1", choices=[SimpleNamespace(finish_reason=finish_reason, message=SimpleNamespace(content="{"))], usage={"prompt_tokens": 40, "completion_tokens": 10, "prompt_tokens_details": {"cached_tokens": 32}, "completion_tokens_details": {"reasoning_tokens": 2}, "cost": 0.001})
    client._client.chat.completions.create = create
    repo = Repository(tmp_path / "state.sqlite")
    with observe_model_calls(lambda action, event: repo.record_model_event(action, event, owner_kind="test", owner_id="work")), generation_limit(10), pytest.raises(AIOutputTruncated):
        execute_structured_operation(client, purpose="inventory_test", prompt="Extract", result_model=Answer)
    assert len(requests) == 1 and requests[0]["max_tokens"] == 10
    with repo.connection() as connection:
        rows = [dict(row) for row in connection.execute("SELECT * FROM model_call_receipts ORDER BY parent_call_id IS NULL")]
    physical = next(row for row in rows if row["purpose"] == "chat_request")
    assert (physical["input_tokens"], physical["output_tokens"], physical["cached_input_tokens"], physical["reasoning_tokens"]) == (40, 10, 32, 2)
    assert physical["provider_response_id"] == "response-1"
    assert physical["output_text"] == "{"
    logical = next(row for row in rows if row["purpose"] == "inventory_test")
    assert logical["input_text"] == "Extract"
    assert '"answer"' in logical["schema_json"]
    assert next(row for row in rows if row["purpose"] == "inventory_test")["status"] == "truncated"


def test_retry_policy_records_each_failed_request_with_unknown_usage(tmp_path, monkeypatch):
    module = install_fake_openai(monkeypatch)
    monkeypatch.setenv("TEST_KEY", "unused")
    monkeypatch.setattr("learnloop.ai.providers.openai_chat._sleep", lambda _: None)
    client = OpenAIChatProviderClient("test", AIProviderConfig(type="openai_chat", base_url="https://unused.invalid", api_key_env="TEST_KEY", model="fake"))
    calls = 0
    def create(**kwargs):
        nonlocal calls
        calls += 1
        if calls < 3:
            error = RuntimeError("transient")
            error.status_code = 503
            raise error
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content='{"answer":"done"}'))])
    client._client.chat.completions.create = create
    repo = Repository(tmp_path / "state.sqlite")
    with observe_model_calls(lambda action, event: repo.record_model_event(action, event, owner_kind="test", owner_id="work")):
        result = execute_structured_operation(client, purpose="test", prompt="Extract", result_model=Answer)
    assert result.answer == "done" and calls == 3
    with repo.connection() as connection:
        rows = connection.execute("SELECT status,input_tokens,output_tokens FROM model_call_receipts WHERE purpose='chat_request' ORDER BY started_at").fetchall()
    assert [row[0] for row in rows] == ["failed", "failed", "completed"]
    assert all(row[1] is None and row[2] is None for row in rows)


def test_codex_does_not_repair_when_reported_output_consumed_the_budget(tmp_path, monkeypatch):
    from learnloop.ai.providers.codex import SdkCodexClient
    from learnloop.config import CodexConfig
    client = SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex")), tmp_path)
    turns = []
    def run(prompt, schema, *, purpose):
        turns.append(purpose)
        client.record_token_usage(20, 10)
        return "{"
    monkeypatch.setattr(client, "_run_structured", run)
    with generation_limit(10), pytest.raises(AIOutputTruncated):
        execute_structured_operation(client, purpose="test", prompt="Extract", result_model=Answer)
    assert turns == ["test"]


def test_concurrent_original_writers_use_independent_temporary_files(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from pathlib import Path
    from learnloop.ingest.originals import store_original_bytes
    barrier = Barrier(2)
    original = Path.replace
    def replace(path, target):
        barrier.wait(timeout=5)
        return original(path, target)
    monkeypatch.setattr(Path, "replace", replace)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(store_original_bytes, tmp_path, "sha256:shared", b"same source") for _ in range(2)]
        paths = [future.result(timeout=10) for future in futures]
    assert paths[0] == paths[1] and paths[0].read_bytes() == b"same source"
    assert not list(paths[0].parent.glob("*.tmp"))
