"""CLI adapter admission and cache-only behavior, without credentials or APIs."""
from dataclasses import replace
import hashlib
import json
from types import SimpleNamespace

import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.cli import field_llm
from learnloop.config.schema import AIProviderConfig
from learnloop.field.types import AttemptRow, ItemFeatures
from learnloop.vault.loader import load_vault
from tests.helpers import create_basic_vault


def forbidden(*args, **kwargs):
    raise AssertionError("Unexpected credentials, client, or repository access")


@pytest.fixture
def case(tmp_path, monkeypatch):
    paths = create_basic_vault(tmp_path / "vault")
    monkeypatch.setattr("learnloop.config.loader.load_dotenv", forbidden)
    monkeypatch.setattr("learnloop.config.loader.global_settings_path", forbidden)
    monkeypatch.setattr(field_llm, "ready_client_for_task", forbidden)
    loaded = load_vault(paths.root, load_environment=False)
    loaded.config.field.enabled = True
    loaded.config.field.llm_probability_enabled = True
    loaded.config.ai.routing.field_llm_probability = "offline"
    loaded.config.ai.providers["offline"] = AIProviderConfig(
        type="openai_chat", model="fake", base_url="https://example.invalid/v1",
    )
    rows = [
        AttemptRow("attempt-private", ItemFeatures(
            "item-private", "lo-private", "2025-01-01T00:00:00Z",
        ), 1., 1.),
    ]
    kwargs = dict(cache_dir=tmp_path / "cache", caps=SpendCaps(),
                  price_per_million=1., output_tokens=128)
    return loaded, rows, kwargs, paths


@pytest.mark.parametrize("setting", [
    "output_tokens", "model", "base_url", "reasoning_effort", "max_tokens",
    "thinking", "response_format",
])
def test_prepare_then_cache_load_has_zero_calls_and_no_repository(case, monkeypatch, setting):
    loaded, rows, kwargs, paths = case
    calls = []

    def resolve(*args, **kwargs):
        assert kwargs == {"allow_env": False}
        assert args[2] == "field_llm_probability"
        return SimpleNamespace(client=object(), runtime=SimpleNamespace(ready=True))

    def execute(client, **kwargs):
        calls.append(kwargs)
        return field_llm.ProbabilityResult(p_success=.7)

    monkeypatch.setattr(field_llm, "ready_client_for_task", resolve)
    monkeypatch.setattr(field_llm, "execute_structured_operation", execute)
    arm, report = field_llm.prepare_or_load_llm(loaded, rows, prepare=True, **kwargs)
    assert arm.predict(rows[0].features) == pytest.approx(.7)
    assert report["charged"]["calls"] == 1
    assert len(calls) == 1
    assert "current_outcome" not in calls[0]["prompt"]
    assert "item-private" not in json.dumps(report)
    assert "attempt-private" not in json.dumps(report)
    before = hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()
    monkeypatch.setattr(field_llm, "ready_client_for_task", forbidden)
    monkeypatch.setattr(field_llm, "Repository", forbidden)
    cached, report = field_llm.prepare_or_load_llm(loaded, rows, **kwargs)
    assert cached.predict(rows[0].features) == pytest.approx(.7)
    assert report["charged"]["calls"] == 0
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == before
    if setting == "output_tokens":
        kwargs[setting] = 129
    else:
        setattr(loaded.config.ai.providers["offline"], setting, 64 if setting == "max_tokens" else "changed")
    with pytest.raises(ValueError, match="incomplete"):
        field_llm.prepare_or_load_llm(loaded, rows, **kwargs)


def test_dry_run_is_read_only_and_lazy(case, monkeypatch):
    loaded, rows, kwargs, paths = case
    before = hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()
    original = field_llm.Repository
    monkeypatch.setattr(field_llm, "Repository", SimpleNamespace(attach=original.attach))
    arm, report = field_llm.prepare_or_load_llm(loaded, rows, prepare=True, dry_run=True, **kwargs)
    assert arm is None
    assert report["status"] == "dry_run"
    assert report["estimate"]["calls"] == 1
    assert report["charged"]["calls"] == 0
    assert not kwargs["cache_dir"].exists()
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == before


@pytest.mark.parametrize("cap", [
    "max_candidates", "max_calls", "max_total_tokens", "max_estimated_usd",
])
def test_every_applicable_cap_blocks_before_client(case, cap):
    loaded, rows, kwargs, _ = case
    kwargs["caps"] = replace(kwargs["caps"], **{cap: 0})
    arm, report = field_llm.prepare_or_load_llm(loaded, rows, prepare=True, **kwargs)
    assert arm is None
    assert report["status"] == "over_budget"
    assert report["charged"]["calls"] == 0


def test_unknown_price_fails_closed(case):
    loaded, rows, kwargs, _ = case
    kwargs["price_per_million"] = None
    arm, report = field_llm.prepare_or_load_llm(loaded, rows, prepare=True, **kwargs)
    assert arm is None
    assert report["status"] == "over_budget"
    assert report["price_source"] == "unknown"


@pytest.mark.parametrize("price", [0, -1, float("nan"), float("inf"), True])
def test_invalid_price_rejected(case, price):
    loaded, rows, kwargs, _ = case
    kwargs["price_per_million"] = price
    with pytest.raises(ValueError, match="finite and positive"):
        field_llm.prepare_or_load_llm(loaded, rows, prepare=True, **kwargs)


@pytest.mark.parametrize("switch", ["enabled", "llm_probability_enabled"])
def test_both_switches_required_without_repository(case, monkeypatch, switch):
    loaded, rows, kwargs, _ = case
    setattr(loaded.config.field, switch, False)
    monkeypatch.setattr(field_llm, "Repository", forbidden)
    arm, report = field_llm.prepare_or_load_llm(loaded, rows, prepare=True, **kwargs)
    assert arm is None
    assert report["status"] == "disabled"


def test_explicit_supported_route_required(case):
    loaded, rows, kwargs, _ = case
    loaded.config.ai.routing.field_llm_probability = None
    with pytest.raises(ValueError, match="explicit"):
        field_llm.prepare_or_load_llm(loaded, rows, **kwargs)
    loaded.config.ai.routing.field_llm_probability = "offline"
    loaded.config.ai.providers["offline"].type = "openai_embedding"
    with pytest.raises(ValueError, match="openai_chat/openrouter route .* or a Codex route"):
        field_llm.prepare_or_load_llm(loaded, rows, **kwargs)


# Owner decision 2026-10-12 (Slice A §5 rule 6): Codex runs every paid LLM role
# on the subscription, without a physical-request bound, with estimated cost.

def _codex(loaded):
    loaded.config.ai.providers["offline"] = AIProviderConfig(type="codex_sdk", model="fake-codex")
    return loaded


def _receipts(paths):
    import sqlite3

    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(
            "SELECT purpose, budget_json, usage_json FROM model_call_receipts "
            "WHERE owner_kind='field_llm_probability' ORDER BY started_at, id"
        )]


class FakeCodex:
    """Subscription-billed: two physical SDK turns per operation are allowed."""

    provider_name = "codex"
    provider_type = "codex_sdk"
    model = "fake-codex"

    def __init__(self, *, usage=True):
        self.usage, self.turns = usage, 0

    def execute(self, client, **kwargs):
        from learnloop.ai.execution import model_call, report_call_usage

        assert client is self
        for _ in range(2):  # e.g. a JSON repair turn: unbounded on Codex
            with model_call(self, purpose=f"{kwargs['purpose']}:sdk_turn"):
                self.turns += 1
                if self.usage:
                    report_call_usage({"input_tokens": 10, "output_tokens": 20})
        return field_llm.ProbabilityResult(p_success=.7)


def _enable_codex_field_routes(root):
    """Both field switches on and both field routes on the template Codex profile."""
    config = root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    for old, new in (
        ('field_llm_probability = ""', 'field_llm_probability = "codex"'),
        ('field_question_classifier = ""', 'field_question_classifier = "codex"'),
        ("[field]\n", "[field]\nenabled = true\n"),
        ("llm_probability_enabled = false", "llm_probability_enabled = true"),
        ("question_classification_enabled = false", "question_classification_enabled = true"),
    ):
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    config.write_text(text, encoding="utf-8")


def _route(monkeypatch, client):
    def resolve(*args, **kwargs):
        assert args[2] == "field_llm_probability" and kwargs == {"allow_env": False}
        return SimpleNamespace(client=client, runtime=SimpleNamespace(ready=True))

    monkeypatch.setattr(field_llm, "ready_client_for_task", resolve)
    monkeypatch.setattr(field_llm, "execute_structured_operation", client.execute)


def test_codex_dry_run_estimates_without_price_or_client(case):
    loaded, rows, kwargs, paths = case
    _codex(loaded)
    kwargs.update(price_per_million=None, caps=SpendCaps(max_total_tokens=1, max_estimated_usd=0))
    before = hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()
    arm, report = field_llm.prepare_or_load_llm(loaded, rows, prepare=True, dry_run=True, **kwargs)
    assert arm is None and report["status"] == "dry_run"
    assert report["billing"] == "subscription" and report["cost_basis"] == "estimated_only"
    assert report["physical_request_bound"] is False
    assert report["caps_in_force"]["not_enforced"] == ["max_total_tokens", "max_estimated_usd"]
    assert report["estimate"]["calls"] == 1 and report["estimate"]["total_tokens"] > 1
    assert report["estimate"]["estimated_usd"] is None  # unknown, never refused, never zero
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == before


def test_codex_eval_cli_dry_run_constructs_no_client(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from learnloop.cli import app

    paths = create_basic_vault(tmp_path / "vault")
    _enable_codex_field_routes(paths.root)
    monkeypatch.setattr(field_llm, "ready_client_for_task", forbidden)
    result = CliRunner().invoke(app, [
        "eval", "--vault", str(paths.root), "--section", "field", "--llm-cache",
        str(tmp_path / "cache"), "--prepare-llm", "--dry-run", "--max-tokens", "0",
        "--max-cost-usd", "0", "--json",
    ])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["status"] == "dry_run" and report["cost_basis"] == "estimated_only"
    assert report["billing"] == "subscription" and report["physical_request_bound"] is False


def test_fake_codex_run_records_estimated_only_receipts(case, monkeypatch):
    loaded, rows, kwargs, paths = case
    _codex(loaded)
    client = FakeCodex()
    _route(monkeypatch, client)
    # Token and dollar caps are not enforced and the price is unknown.
    kwargs.update(price_per_million=None, caps=SpendCaps(max_total_tokens=1, max_estimated_usd=0))
    arm, report = field_llm.prepare_or_load_llm(loaded, rows, prepare=True, **kwargs)
    assert report["status"] == "complete", report
    assert arm.predict(rows[0].features) == pytest.approx(.7)
    assert client.turns == 2  # no physical-request bound on the subscription
    assert report["charged"]["calls"] == 1 and report["charged"]["estimated_usd"] is None
    receipts = _receipts(paths)
    roots = [json.loads(r["budget_json"]) for r in receipts if r["budget_json"]]
    assert roots and len(receipts) == 3  # one root receipt, two physical turns
    for budget in roots:  # caps in force are declared on the root receipt
        assert budget["billing"] == "subscription" and budget["cost_basis"] == "estimated_only"
        assert budget["physical_request_bound"] is False
    for receipt in receipts:
        usage = json.loads(receipt["usage_json"])
        assert usage["cost_basis"] == "estimated_only" and usage["estimated_usd"] is None
    turns = [json.loads(r["usage_json"]) for r in receipts if r["purpose"].endswith(":sdk_turn")]
    assert [u["estimated_total_tokens"] for u in turns] == [30, 30]
    assert {u["estimated_token_source"] for u in turns} == {"reported_usage"}


def test_codex_estimate_falls_back_to_input_plus_output_tokens(case, monkeypatch):
    loaded, rows, kwargs, paths = case
    _codex(loaded)
    _route(monkeypatch, FakeCodex(usage=False))
    arm, report = field_llm.prepare_or_load_llm(loaded, rows, prepare=True, **kwargs)
    assert report["status"] == "complete" and arm is not None
    usage = [json.loads(r["usage_json"]) for r in _receipts(paths)]
    assert usage and {u["estimated_token_source"] for u in usage} == {"input_plus_output_estimate"}
    planned = report["estimate"]["total_tokens"]
    assert all(u["estimated_total_tokens"] == planned and u["estimated_usd"] > 0 for u in usage)


def test_codex_run_still_stops_at_the_call_cap(case, monkeypatch):
    loaded, rows, kwargs, _ = case
    _codex(loaded)
    client = FakeCodex()
    _route(monkeypatch, client)
    kwargs.update(price_per_million=None, caps=SpendCaps(max_calls=0))
    arm, report = field_llm.prepare_or_load_llm(loaded, rows, prepare=True, **kwargs)
    assert arm is None and report["status"] == "over_budget"
    assert client.turns == 0 and report["charged"]["calls"] == 0


def test_metered_route_keeps_physical_bound_unknown_price_refusal_and_token_cap(case, monkeypatch):
    loaded, rows, kwargs, paths = case
    sent = []

    def execute(client, **kwargs):
        from learnloop.ai.execution import model_call, report_call_usage

        for index in range(2):
            with model_call(client, purpose="chat_request"):
                sent.append(index)
                report_call_usage({"input_tokens": 10, "output_tokens": 20})
        return field_llm.ProbabilityResult(p_success=.7)

    client = SimpleNamespace(provider_name="offline", provider_type="openai_chat", model="fake")
    monkeypatch.setattr(field_llm, "ready_client_for_task", lambda *a, **k: SimpleNamespace(
        client=client, runtime=SimpleNamespace(ready=True)))
    monkeypatch.setattr(field_llm, "execute_structured_operation", execute)
    arm, report = field_llm.prepare_or_load_llm(loaded, rows, prepare=True, **kwargs)
    assert arm is None and report["status"] == "over_budget" and sent == [0]
    assert report["billing"] == "metered" and report["physical_request_bound"] is True
    budgets = [json.loads(r["budget_json"]) for r in _receipts(paths) if r["budget_json"]]
    assert budgets and all("cost_basis" not in b for b in budgets)
    for change in ({"price_per_million": None}, {"caps": SpendCaps(max_total_tokens=1)}):
        sent.clear()
        arm, report = field_llm.prepare_or_load_llm(loaded, rows, prepare=True, **(kwargs | change))
        assert arm is None and report["status"] == "over_budget" and sent == []


def test_codex_route_resolving_to_metered_client_is_refused(case, monkeypatch):
    loaded, rows, kwargs, _ = case
    _codex(loaded)
    metered = FakeCodex()
    metered.provider_type = "openai_chat"
    _route(monkeypatch, metered)
    with pytest.raises(field_llm.AIProviderUnavailable, match="billing"):
        field_llm.prepare_or_load_llm(loaded, rows, prepare=True, **kwargs)
    assert metered.turns == 0


def test_cache_must_be_outside_vault_even_on_read(case):
    loaded, rows, kwargs, paths = case
    kwargs["cache_dir"] = paths.root / "cache"
    with pytest.raises(ValueError, match="outside the vault"):
        field_llm.prepare_or_load_llm(loaded, rows, **kwargs)


def test_missing_cache_never_prepares_implicitly(case, monkeypatch):
    loaded, rows, kwargs, _ = case
    monkeypatch.setattr(field_llm, "Repository", forbidden)
    with pytest.raises(ValueError, match="incomplete"):
        field_llm.prepare_or_load_llm(loaded, rows, **kwargs)
    assert not kwargs["cache_dir"].exists()


def test_cancelled_before_first_call(case):
    loaded, rows, kwargs, _ = case
    arm, report = field_llm.prepare_or_load_llm(
        loaded, rows, prepare=True, cancelled=lambda: True, **kwargs,
    )
    assert arm is None
    assert report["status"] == "cancelled"
    assert report["charged"]["calls"] == 0
