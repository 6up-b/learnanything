"""The one sheet: connect an AI, and say OK once before LearnLoop uses AI at all (ux_learnloop_v1 §6.6, Q4; UX-10).

The OK covers every use of AI and every provider (``learnloop.ai.model_use``): it is recorded once in the
library's config (with the date and the version of the words it was given under), travels to libraries created
later on the same machine, and releases any book whose questions were waiting for it. An OK given on this sheet
before it covered every use is honoured. Connecting is not the OK, nor is a ChatGPT sign-in, an upload's own OK or
a "Use OpenRouter instead" choice. "Continue with ChatGPT" routes every use case to the plan.

Every test here starts on a machine with no OK (``no_ai_ok``).
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

from tests.ux_phase1_support import CLOCK, fake_services, fresh_library, grant_consent, route, set_config, write_book

pytestmark = pytest.mark.no_ai_ok


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
    # The AI this library is set up with, named as the learner knows it
    # (usability round 2: a Codex user's OK said only "ChatGPT").
    assert before["providerLabel"] == "Codex (your ChatGPT account)"
    # The one sheet's words: every use, and what goes where behind "What's sent".
    assert before["title"] == "Before LearnLoop uses AI"
    assert before["whatLeaves"] == (
        "LearnLoop uses AI for questions, replies, feedback and other learning help. It can send your books, "
        "files you choose, your questions and your answers to the services you connect."
    )
    sent = before["whatsSent"]
    assert sent[0].startswith("To Codex (your ChatGPT account): passages of your books")
    # Tier 1 (mvp-0.22, the Decider landing): the one OK also names what the
    # Decider's small judgments send to Perplexity, as Settings discloses it
    # (tests/test_decider_landing.py).
    assert before["deciderNote"] in sent and "Perplexity, through OpenRouter" in before["deciderNote"]
    assert sent[-1] == "You say OK once, and it covers every use. Your library stays on this computer."

    after = call(ctx, "connect_ai", {"provider": "current"})

    assert after["consented"] is True and after["needs"] is None
    consent = _consent(root)
    assert set(consent) == {"model_use"}
    assert consent["model_use"]["granted_at"]
    assert consent["model_use"]["data_flow"] == "all_model_use"
    assert consent["model_use"]["disclosure_version"] == 1
    assert load_vault(root).config.ai.consent["model_use"].granted_at == consent["model_use"]["granted_at"]
    assert after["consentedAt"] == consent["model_use"]["granted_at"]
    # Mirrored to this computer, so a library opened or made here later is covered too.
    raw_defaults = tomllib.loads(global_ai_defaults_path().read_text(encoding="utf-8"))
    assert raw_defaults["ai"]["consent"]["model_use"]["data_flow"] == "all_model_use"


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
    assert payload["needs"] == "connect" and payload["consented"] is False
    # The OK comes first and needs nothing connected (owner, 2026-11-20); connecting is still asked for.
    out = call(ctx, "connect_ai", {"provider": "current"})
    assert out["consented"] is True and out["needs"] == "connect"
    assert set(_consent(root)) == {"model_use"}


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
    # Plan-first transport T1: each use case at the effort tier of its default
    # route; the tiers copy [ai.providers.chatgpt], so they serve the chosen slug.
    from learnloop.config.schema import DEFAULT_SERVING_TASK_ROUTES

    for task in ("grading", "diagnosis", "canonical_ingest", "canonical_ingest_retry", "authoring",
                 "tutor_qa", "teach_back", "rung_variant"):
        assert getattr(routing, task) == DEFAULT_SERVING_TASK_ROUTES.get(task, "chatgpt"), task
        served = config.ai.providers[getattr(routing, task)]
        assert (served.type, served.model) == ("chatgpt_plan", "gpt-test-fast"), task
    # Signing in and connecting is not the OK: the sheet asks for it next.
    assert _consent(root) == {}
    assert out["consented"] is False and out["needs"] == "consent"
    call(ctx, "connect_ai", {"provider": "current"})
    # A library made later on this machine inherits both the routes and the OK.
    raw_defaults = tomllib.loads(global_ai_defaults_path().read_text(encoding="utf-8"))
    assert raw_defaults["ai"]["consent"]["model_use"]["granted_at"]
    later = create_vault(tmp_path / "Later").root
    later_config = load_vault(later).config
    assert later_config.ai.routing.canonical_ingest == "chatgpt_medium"
    assert "model_use" in later_config.ai.consent


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
    assert _consent(root) == {}  # a connection is not the OK


def test_openrouter_needs_its_key(tmp_path, monkeypatch):
    root = fresh_library(tmp_path)
    ctx = _ctx(root)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "connect_ai", {"provider": "openrouter"})
    assert caught.value.code == "openrouter_key_missing"


def test_quick_add_reads_the_recorded_ok_instead_of_asking_per_build(tmp_path):
    """The deliberate Quick add path (kept reachable) no longer asks for a
    checkbox the learner already answered once: the synthesis consent entry
    carries the recorded OK (spec §10 item 1.7)."""

    from learnloop.content.pipeline.quick_add import plan_quick_add
    from learnloop.content.pipeline.jobs import DurableIngestJobs
    from learnloop.content.pipeline.add_source import AddSourceOptions, add_source
    from tests.ux_phase1_support import repository

    root = fresh_library(tmp_path)
    set_config(root, {("ingest", "auto_build"): False})
    repo = repository(root)
    jobs = DurableIngestJobs()
    jobs.bind(repo, root, background=False, clock=CLOCK, services=fake_services())
    book = write_book(tmp_path)
    add_source(load_vault(root), jobs, str(book), AddSourceOptions(), clock=CLOCK)

    def synthesis_consent():
        vault = load_vault(root)
        plan = plan_quick_add(repo, vault.config, vault, str(book), subject_id=None)
        return next(entry for entry in plan.external_ai_consent if entry["stage"] == "synthesis")

    before = synthesis_consent()
    assert before["granted"] is False
    # Plan-first transport T1: a new library's builds route to the plan's tiers (one "chatgpt" OK).
    grant_consent(root, "chatgpt")
    after = synthesis_consent()
    assert after["granted"] is True
    assert after["granted_at"] == "2026-10-13T09:00:00Z"


def test_an_earlier_ok_is_honoured_whichever_provider_serves_now(tmp_path, monkeypatch):
    """An OK this sheet recorded before it covered every use (for one provider) is the learner's OK:
    they are not asked again, and a route that moves to another provider does not ask either."""

    root = fresh_library(tmp_path)
    ctx = _ctx(root)
    grant_consent(root, "codex")
    monkeypatch.setattr(first_run, "authoring_route_for", lambda vault: route())
    assert call(ctx, "get_ai_connection", {})["needs"] is None
    monkeypatch.setattr(first_run, "authoring_route_for",
                        lambda vault: route(provider="openrouter", subscription=False, consent_key="openrouter"))
    payload = call(ctx, "get_ai_connection", {})
    assert payload["needs"] is None and payload["consentedAt"] == "2026-10-13T09:00:00Z"


def test_a_sign_in_an_upload_ok_or_a_fallback_choice_is_not_the_ok(tmp_path, monkeypatch):
    root = fresh_library(tmp_path)
    ctx = _ctx(root)
    # The separate OKs for sending whole files.
    set_config(root, {("ai", "consent", "whole_files", "granted_at"): "2026-10-13T09:00:00Z",
                      ("ai", "consent", "whole_files", "data_flow"): "whole_files",
                      ("ai", "consent", "whole_files_zai", "granted_at"): "2026-10-13T09:00:00Z",
                      ("ai", "consent", "whole_files_zai", "data_flow"): "whole_files"})
    ctx.reload(maintenance=False)
    # "Use OpenRouter instead" for one action (T1 redesign D) picks the provider; it was the build's consent before.
    granted = route(provider="openrouter", subscription=False, consent_key="openrouter")
    monkeypatch.setattr(first_run, "authoring_route_for",
                        lambda vault: type(granted)(**{**granted.__dict__, "granted": True}))
    assert call(ctx, "get_ai_connection", {})["needs"] == "consent"
    # A ChatGPT sign-in, and connecting it.
    monkeypatch.setattr(first_run, "chatgpt_plan_ready", lambda: True)
    monkeypatch.setattr(first_run, "chatgpt_plan_models", lambda: ["gpt-test-fast"])
    monkeypatch.setattr(first_run, "authoring_route_for", lambda vault: route(provider="chatgpt", consent_key="chatgpt"))
    out = call(ctx, "connect_ai", {"provider": "chatgpt"})
    assert out["consented"] is False and out["needs"] == "consent" and out["released"] == []


def test_closing_the_sheet_leaves_the_book_readable_and_its_questions_waiting(tmp_path, monkeypatch):
    from learnloop.content.pipeline.add_source import _completed_extraction, source_status_line
    from tests.ux_phase1_support import Calls

    root = fresh_library(tmp_path)
    calls = Calls()
    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=fake_services(calls=calls))
    monkeypatch.setattr(first_run, "authoring_route_for", lambda vault: route())
    added = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})
    source_id = added["items"][0]["sourceId"]
    assert added["waitingForOk"] is True
    # "Not now" sends nothing: reading is local and there; the questions wait, nothing is lost or failed.
    for _ in range(2):
        assert call(ctx, "get_ai_connection", {})["needs"] == "consent"
    assert _completed_extraction(ctx.repository, source_id) is not None
    assert latest_auto_outcome(ctx.repository, source_id)["reason"] == "needs_consent"
    line = source_status_line(ctx.repository, load_vault(root), source_id)
    assert line["text"] == "Questions wait for your OK" and line["action"]["kind"] == "connect_ai"
    assert calls.inventory_calls == 0 and calls.synthesis_calls == 0
    # The OK, given later, resumes the waiting build once; a second OK resumes nothing.
    assert call(ctx, "connect_ai", {"provider": "current"})["released"] == [source_id]
    assert calls.inventory_calls > 0
    assert call(ctx, "connect_ai", {"provider": "current"})["released"] == []
