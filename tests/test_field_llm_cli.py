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
    loaded.config.ai.providers["offline"].type = "codex_sdk"
    with pytest.raises(ValueError, match="openai_chat or openrouter"):
        field_llm.prepare_or_load_llm(loaded, rows, **kwargs)


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
