"""`learnloop usage`: receipts seeded through the real observer and providers."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import time

import pytest

from learnloop.ai.execution import declared_budgets, observe_model_calls, report_call_usage
from learnloop.ai.providers.openai_chat import OpenAIChatProviderClient
from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import STRUCTURED_COMPLETION, execute_structured_operation
from learnloop.config import AIProviderConfig
from learnloop.db.repositories import Repository
from learnloop.substrate.model_usage import (
    GRAPH_STRUCTURING_PURPOSE,
    SYNTHESIS_PASS_PURPOSE,
    build_usage_report,
    distribution,
    model_usage_report,
)
from tests.helpers import create_basic_vault
from tests.openai_fakes import install_fake_openai


class Answer(WireModel):
    answer: str


ANSWER = '{"answer":"ok"}'
DEFAULT_BUDGETS = {
    "synthesis_shard_input_tokens": 40000,
    "synthesis_shard_output_tokens": 10000,
    "synthesis_total_input_ceiling": 48000,
    "synthesis_output_tokens": 16000,
}


def _usage(prompt, completion, *, cached=None, reasoning=None, cost=None):
    usage = {"prompt_tokens": prompt, "completion_tokens": completion}
    if cached is not None:
        usage["prompt_tokens_details"] = {"cached_tokens": cached}
    if reasoning is not None:
        usage["completion_tokens_details"] = {"reasoning_tokens": reasoning}
    if cost is not None:
        usage["cost"] = cost
    return usage


def _openai_client(monkeypatch, responses, usages=()):
    """A real OpenAI-compatible adapter over a fake SDK that reports ``usages``."""

    install_fake_openai(monkeypatch, *responses, usages=list(usages))
    monkeypatch.setenv("TEST_KEY", "unused")
    monkeypatch.setattr("learnloop.ai.providers.openai_chat._sleep", lambda _: None)
    return OpenAIChatProviderClient("openai", AIProviderConfig(type="openai_chat", base_url="https://unused.invalid", api_key_env="TEST_KEY", model="gpt-test"))


class _ReportingTransport:
    """Reports usage on the operation's own receipt, as the Codex HTTP adapter does."""

    provider_name = "codex_http"
    model = "codex-test"

    def __init__(self, usage):
        self._usage = usage

    def supports(self, capability):
        return capability == STRUCTURED_COMPLETION

    def complete(self, request):
        if self._usage is not None:
            report_call_usage(self._usage)
        return Answer(answer="ok")


def _observed(repository, owner_id, *, owner_kind="ingest_job"):
    return observe_model_calls(lambda action, event: repository.record_model_event(action, event, owner_kind=owner_kind, owner_id=owner_id))


def _run(client, purpose):
    return execute_structured_operation(client, purpose=purpose, prompt="Summarize", result_model=Answer)


def _report(paths, **filters):
    return model_usage_report(paths.sqlite_path, budgets=DEFAULT_BUDGETS, **filters)


def _group(report, purpose):
    return next(group for group in report["by_purpose"] if group["purpose"] == purpose)


@pytest.fixture
def vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    return paths, Repository(paths.sqlite_path)


def test_empty_vault_reports_no_usage_and_keeps_the_schema(vault):
    paths, _ = vault
    report = _report(paths)
    assert report["totals"] == {"receipts": 0, "operations": 0, "requests": 0}
    assert report["by_purpose"] == [] and report["coverage"] == []
    assert report["synthesis_runs"] == {"config_budgets": DEFAULT_BUDGETS, "runs": []}
    assert report["report_version"] == 1


def test_openai_requests_are_attributed_to_their_root_purpose(vault, monkeypatch):
    paths, repository = vault
    # One repair turn: the first response is not valid JSON, so the operation
    # makes two chat_request leaves under one source_set_synthesis root.
    client = _openai_client(monkeypatch, ["not json", ANSWER], [_usage(100, 10), _usage(120, 12, cached=64, reasoning=4, cost=0.002)])
    with _observed(repository, "job-1"):
        _run(client, SYNTHESIS_PASS_PURPOSE)

    report = _report(paths)
    assert report["totals"] == {"receipts": 3, "operations": 1, "requests": 2}
    assert [group["purpose"] for group in report["by_purpose"]] == [SYNTHESIS_PASS_PURPOSE]
    group = _group(report, SYNTHESIS_PASS_PURPOSE)
    assert (group["provider"], group["model"]) == ("openai", "gpt-test")
    assert group["request_purposes"] == {"chat_request": 2}
    assert group["operations"] == 1 and group["requests"] == 2
    assert group["statuses"]["completed"] == 2
    assert group["tokens"]["input_tokens"] == {"known": 2, "total": 220, "mean": 110.0, "median": 110.0, "p95": 120, "max": 120}
    assert group["tokens"]["cached_input_tokens"]["known"] == 1
    assert group["cost"] == {"known": 1, "total": 0.002}


def test_unknown_usage_is_counted_and_never_averaged_as_zero(vault, monkeypatch):
    paths, repository = vault
    transient = RuntimeError("transient")
    transient.status_code = 503
    reporting = _openai_client(monkeypatch, [transient, ANSWER], [_usage(50, 5)])
    silent = _openai_client(monkeypatch, [ANSWER])
    with _observed(repository, "rpc-1", owner_kind="sidecar_rpc"):
        _run(reporting, "tutor_qa")
        _run(silent, "reader_preset_synthesis")

    report = _report(paths)
    tutor = _group(report, "tutor_qa")
    assert tutor["statuses"]["failed"] == 1 and tutor["statuses"]["completed"] == 1
    assert tutor["usage_unknown"] == 1
    assert tutor["tokens"]["input_tokens"]["known"] == 1
    assert tutor["tokens"]["input_tokens"]["mean"] == 50.0
    reader = _group(report, "reader_preset_synthesis")
    assert reader["usage_unknown"] == 1
    assert reader["tokens"]["output_tokens"] == {"known": 0, "total": None, "mean": None, "median": None, "p95": None, "max": None}

    coverage = {(row["purpose"], row["request_purpose"]): row for row in report["coverage"]}
    assert coverage[("tutor_qa", "chat_request")]["completed_usage_coverage"] == "full"
    assert coverage[("reader_preset_synthesis", "chat_request")] == {
        "purpose": "reader_preset_synthesis", "request_purpose": "chat_request", "provider": "openai",
        "requests": 1, "requests_with_usage": 0, "completed_requests": 1,
        "completed_without_usage": 1, "completed_usage_coverage": "none",
    }


def test_a_transport_reporting_on_its_own_receipt_is_its_own_request(vault):
    paths, repository = vault
    with _observed(repository, "job-1"):
        _run(_ReportingTransport({"input_tokens": 700, "output_tokens": 70}), "source_unit_inventory")
    group = _group(_report(paths), "source_unit_inventory")
    assert group["request_purposes"] == {"source_unit_inventory": 1}
    assert group["tokens"]["input_tokens"]["total"] == 700


def test_synthesis_runs_compare_measured_tokens_with_the_budgets(vault):
    paths, repository = vault
    with _observed(repository, "job-1"):
        _run(_ReportingTransport({"input_tokens": 20000, "output_tokens": 4000}), SYNTHESIS_PASS_PURPOSE)
        _run(_ReportingTransport({"input_tokens": 10000, "output_tokens": 2000}), SYNTHESIS_PASS_PURPOSE)
        _run(_ReportingTransport({"input_tokens": 6000, "output_tokens": 2000}), GRAPH_STRUCTURING_PURPOSE)
        _run(_ReportingTransport({"input_tokens": 999, "output_tokens": 99}), "source_unit_inventory")
    with _observed(repository, "job-2"):
        _run(_ReportingTransport(None), SYNTHESIS_PASS_PURPOSE)

    runs = _report(paths)["synthesis_runs"]["runs"]
    assert [run["owner_id"] for run in runs] == ["job-1", "job-2"]
    first, second = runs
    assert first["passes"] == {SYNTHESIS_PASS_PURPOSE: 2, GRAPH_STRUCTURING_PURPOSE: 1}
    assert (first["input_tokens"], first["output_tokens"]) == (36000, 8000)
    assert (first["largest_pass_input_tokens"], first["largest_pass_output_tokens"]) == (20000, 4000)
    assert first["budget_ratios"] == {
        "input_to_total_input_ceiling": 0.75,
        "output_to_output_ceiling": 0.5,
        "largest_pass_input_to_shard_input": 0.5,
        "largest_pass_output_to_shard_output": 0.4,
    }
    assert second["requests_without_usage"] == 1
    assert second["input_tokens"] is None
    assert second["budget_ratios"]["input_to_total_input_ceiling"] is None


def test_runs_are_compared_with_the_budgets_recorded_on_their_receipts(vault, monkeypatch):
    paths, repository = vault
    declared = {**DEFAULT_BUDGETS, "synthesis_total_input_ceiling": 72000}
    client = _openai_client(monkeypatch, [ANSWER], [_usage(36000, 8000)])
    with _observed(repository, "job-1"), declared_budgets(declared):
        _run(client, SYNTHESIS_PASS_PURPOSE)
    with _observed(repository, "job-2"), declared_budgets({"unlimited": True, "synthesis_shard_input_tokens": 40000}):
        _run(_ReportingTransport({"input_tokens": 50000, "output_tokens": 20000}), SYNTHESIS_PASS_PURPOSE)
    with _observed(repository, "job-3"):
        _run(_ReportingTransport({"input_tokens": 24000, "output_tokens": 8000}), SYNTHESIS_PASS_PURPOSE)

    with repository.connection() as connection:
        recorded = dict(connection.execute(
            "SELECT purpose, budget_json FROM model_call_receipts WHERE owner_id='job-1'"
        ).fetchall())
    # Only the operation's own receipt carries the budgets, not its requests.
    assert recorded["chat_request"] is None
    assert recorded[SYNTHESIS_PASS_PURPOSE] is not None

    declared_run, unlimited_run, config_run = _report(paths)["synthesis_runs"]["runs"]
    assert declared_run["budget_source"] == "receipt"
    assert declared_run["budget_ratios"]["input_to_total_input_ceiling"] == 0.5
    assert unlimited_run["budgets"]["unlimited"] is True
    assert unlimited_run["budget_ratios"]["input_to_total_input_ceiling"] is None
    assert unlimited_run["budget_ratios"]["largest_pass_input_to_shard_input"] == 1.25
    assert config_run["budget_source"] == "config"
    assert config_run["budget_ratios"]["input_to_total_input_ceiling"] == 0.5


def test_purpose_prefix_and_since_filter_whole_chains(vault, monkeypatch):
    paths, repository = vault
    early = _openai_client(monkeypatch, [ANSWER], [_usage(10, 1)])
    with _observed(repository, "job-1"):
        _run(early, SYNTHESIS_PASS_PURPOSE)
    time.sleep(0.01)
    boundary = datetime.now(timezone.utc)
    time.sleep(0.01)
    late = _openai_client(monkeypatch, [ANSWER, ANSWER], [_usage(20, 2), _usage(30, 3)])
    with _observed(repository, "job-2"):
        _run(late, SYNTHESIS_PASS_PURPOSE)
        _run(late, "tutor_qa")

    by_purpose = _report(paths, purpose_prefix="source_set")["by_purpose"]
    assert [(group["purpose"], group["requests"]) for group in by_purpose] == [(SYNTHESIS_PASS_PURPOSE, 2)]
    # The leaf purpose is not a filter key: requests follow their root.
    assert _report(paths, purpose_prefix="chat_request")["totals"]["requests"] == 0

    recent = _report(paths, since=boundary)
    assert recent["totals"] == {"receipts": 4, "operations": 2, "requests": 2}
    assert [run["owner_id"] for run in recent["synthesis_runs"]["runs"]] == ["job-2"]
    assert _group(recent, SYNTHESIS_PASS_PURPOSE)["tokens"]["input_tokens"]["total"] == 20


def test_distribution_uses_nearest_rank_p95():
    stats = distribution(list(range(1, 21)) + [None])
    assert stats == {"known": 20, "total": 210, "mean": 10.5, "median": 10.5, "p95": 19, "max": 20}


def test_report_ordering_is_deterministic():
    receipts = [
        {"id": f"call_{n}", "parent_call_id": None, "owner_kind": "job", "owner_id": "j", "purpose": purpose,
         "provider": provider, "model": "m", "status": "completed", "started_at": "2026-09-01T00:00:00+00:00",
         "finished_at": None, "input_tokens": 1, "output_tokens": 1, "cached_input_tokens": None,
         "cache_write_tokens": None, "reasoning_tokens": None, "cost": None}
        for n, (purpose, provider) in enumerate([("b", "z"), ("a", None), ("b", "a"), ("a", "y")])
    ]
    forward = build_usage_report(receipts, budgets=DEFAULT_BUDGETS, generated_at="t")
    backward = build_usage_report(list(reversed(receipts)), budgets=DEFAULT_BUDGETS, generated_at="t")
    assert forward == backward
    assert [(group["purpose"], group["provider"]) for group in forward["by_purpose"]] == [("a", None), ("a", "y"), ("b", "a"), ("b", "z")]


def test_synthesis_purposes_match_the_synthesis_operations(monkeypatch):
    from learnloop.content.synthesis import source_set_synthesis as synthesis

    seen = []
    monkeypatch.setattr(synthesis, "execute_structured_operation", lambda client, *, purpose, **kwargs: seen.append(purpose))
    monkeypatch.setattr(synthesis, "source_set_synthesis_prompt", lambda context: "")
    monkeypatch.setattr(synthesis, "concept_graph_structuring_prompt", lambda context: "")
    synthesis.request_source_set_synthesis(None, None)
    synthesis.request_concept_graph_structuring(None, None)
    assert seen == [SYNTHESIS_PASS_PURPOSE, GRAPH_STRUCTURING_PURPOSE]


def _cli(*args):
    from typer.testing import CliRunner

    from learnloop.cli import app

    return CliRunner().invoke(app, [str(arg) for arg in args])


def test_cli_reads_budgets_from_the_effective_config_and_opens_read_only(vault):
    paths, repository = vault
    with _observed(repository, "job-1"):
        _run(_ReportingTransport({"input_tokens": 36000, "output_tokens": 8000}), SYNTHESIS_PASS_PURPOSE)
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text(encoding="utf-8") + "\n[ingest.budgets]\nsynthesis_total_input_ceiling = 72000\n", encoding="utf-8")
    before = paths.sqlite_path.read_bytes()

    result = _cli("usage", "--vault", paths.root, "--json", "--purpose", "source")
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["synthesis_runs"]["config_budgets"]["synthesis_total_input_ceiling"] == 72000
    assert report["synthesis_runs"]["runs"][0]["budget_ratios"]["input_to_total_input_ceiling"] == 0.5
    assert report["filters"]["purpose_prefix"] == "source"

    text = _cli("usage", "--vault", paths.root)
    assert text.exit_code == 0, text.output
    assert "source_set_synthesis  codex_http / codex-test" in text.output
    assert "36,000 = 0.50 of total ceiling 72,000" in text.output
    assert max(len(line) for line in text.output.splitlines()) <= 88
    assert paths.sqlite_path.read_bytes() == before


def test_cli_rejects_an_unparseable_since(vault):
    paths, _ = vault
    result = _cli("usage", "--vault", paths.root, "--since", "yesterday")
    assert result.exit_code == 2
