"""UX Phase 1: connect an AI once, consent once (docs/specs/ux_learnloop_v1.md §6.6, Q4).

Consent is recorded once per provider in the library's config (with the date),
travels to libraries created later on the same machine, and releases any book
whose questions were waiting for it. "Continue with ChatGPT" routes every use
case to the plan, where signing in used to route nothing.
"""

from __future__ import annotations

import tomllib

import pytest

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.bootstrap import create_vault
from learnloop.content.pipeline.add_source import latest_auto_outcome
from learnloop.config import global_ai_defaults_path
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers import first_run
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.ux_phase1_support import CLOCK, fake_services, fresh_library, route, write_book


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)


def call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _ctx(root, authoring=None):
    ctx = SidecarContext()
    ctx.load(root)
    services = fake_services(authoring)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=services)
    return ctx


def _consent(root):
    raw = tomllib.loads((root / "learnloop.toml").read_text(encoding="utf-8"))
    return raw.get("ai", {}).get("consent", {})


def test_one_ok_records_consent_for_the_connected_provider(tmp_path, monkeypatch):
    root = fresh_library(tmp_path)
    ctx = _ctx(root)
    monkeypatch.setattr(first_run, "authoring_route_for", lambda vault: route())
    before = call(ctx, "get_ai_connection", {})
    assert before["canAuthor"] is True
    assert before["consented"] is False
    assert before["needs"] == "consent"
    assert before["providerLabel"] == "ChatGPT"
    assert before["whatLeaves"] == (
        "LearnLoop sends passages of the books you add, and your answers, to ChatGPT "
        "to write questions and give feedback."
    )

    after = call(ctx, "connect_ai", {"provider": "current"})

    assert after["consented"] is True and after["needs"] is None
    consent = _consent(root)
    assert set(consent) == {"codex"}
    assert consent["codex"]["granted_at"]
    assert consent["codex"]["data_flow"] == "passages_and_answers"
    assert load_vault(root).config.ai.consent["codex"].granted_at == consent["codex"]["granted_at"]


def test_connecting_releases_books_that_were_waiting(tmp_path, monkeypatch):
    root = fresh_library(tmp_path)
    ctx = _ctx(root)
    monkeypatch.setattr(first_run, "authoring_route_for", lambda vault: route())
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]["sourceId"]
    assert latest_auto_outcome(ctx.repository, source_id)["reason"] == "needs_consent"

    out = call(ctx, "connect_ai", {"provider": "current"})

    assert out["released"] == [source_id]
    assert latest_auto_outcome(ctx.repository, source_id)["outcome"] == "building"


def test_without_a_ready_route_the_sheet_asks_to_connect(tmp_path, monkeypatch):
    root = fresh_library(tmp_path)
    ctx = _ctx(root)
    monkeypatch.setattr(first_run, "authoring_route_for", lambda vault: route(ready=False, message="no codex"))
    payload = call(ctx, "get_ai_connection", {})
    assert payload["canAuthor"] is False
    assert payload["needs"] == "connect"
    with pytest.raises(SidecarError) as caught:
        call(ctx, "connect_ai", {"provider": "current"})
    assert caught.value.code == "ai_not_connected"


def test_continue_with_chatgpt_routes_every_use_case_to_the_plan(tmp_path, monkeypatch):
    root = fresh_library(tmp_path)
    ctx = _ctx(root)
    monkeypatch.setattr(first_run, "chatgpt_plan_ready", lambda: True)
    monkeypatch.setattr(first_run, "chatgpt_plan_models", lambda: ["gpt-test-fast", "gpt-test-deep"])
    monkeypatch.setattr(first_run, "authoring_route_for", lambda vault: route(provider="chatgpt", consent_key="chatgpt"))

    out = call(ctx, "connect_ai", {"provider": "chatgpt"})

    config = load_vault(root).config
    assert config.ai.active_provider == "chatgpt"
    profile = config.ai.providers["chatgpt"]
    assert (profile.type, profile.model) == ("chatgpt_plan", "gpt-test-fast")
    routing = config.ai.routing
    for task in ("grading", "diagnosis", "canonical_ingest", "canonical_ingest_retry", "authoring",
                 "tutor_qa", "teach_back", "rung_variant"):
        assert getattr(routing, task) == "chatgpt", task
    assert set(_consent(root)) == {"chatgpt"}
    assert out["consented"] is True
    # A library made later on this machine inherits both the routes and the OK.
    raw_defaults = tomllib.loads(global_ai_defaults_path().read_text(encoding="utf-8"))
    assert raw_defaults["ai"]["consent"]["chatgpt"]["granted_at"]
    later = create_vault(tmp_path / "Later").root
    later_config = load_vault(later).config
    assert later_config.ai.routing.canonical_ingest == "chatgpt"
    assert "chatgpt" in later_config.ai.consent


def test_continue_with_chatgpt_needs_a_sign_in_first(tmp_path, monkeypatch):
    root = fresh_library(tmp_path)
    ctx = _ctx(root)
    monkeypatch.setattr(first_run, "chatgpt_plan_ready", lambda: False)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "connect_ai", {"provider": "chatgpt"})
    assert caught.value.code == "chatgpt_not_signed_in"
    assert _consent(root) == {}


def test_an_openrouter_key_connects_every_use_case(tmp_path, monkeypatch):
    root = fresh_library(tmp_path)
    ctx = _ctx(root)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-not-real")
    monkeypatch.setattr(first_run, "authoring_route_for",
                        lambda vault: route(provider="openrouter", subscription=False, consent_key="openrouter"))
    call(ctx, "connect_ai", {"provider": "openrouter"})
    config = load_vault(root).config
    assert config.ai.active_provider == "openrouter"
    assert config.ai.routing.canonical_ingest == "openrouter"
    assert set(_consent(root)) == {"openrouter"}


def test_openrouter_needs_its_key(tmp_path, monkeypatch):
    root = fresh_library(tmp_path)
    ctx = _ctx(root)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "connect_ai", {"provider": "openrouter"})
    assert caught.value.code == "openrouter_key_missing"
