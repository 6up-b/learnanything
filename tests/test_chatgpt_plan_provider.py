"""The ``chatgpt_plan`` transport against a fake Responses SSE stream.

Covers the documented request shape, structured output, receipts, billing,
readiness, the usage-limit pause with fallback, and error recovery. No test
leaves 127.0.0.1.
"""
from __future__ import annotations

from contextlib import closing
import json
import sqlite3
import threading
import time

import pytest
import tomlkit

from learnloop.ai.chatgpt_plan.responses import UNSUPPORTED_FIELDS
from learnloop.ai.chatgpt_plan.session import (
    ChatGPTPlanNotEligible,
    ChatGPTPlanUsageExhausted,
    ChatGPTSignInRequired,
    PlanSession,
)
from learnloop.ai.disclosures import recipient
from learnloop.ai.errors import AIInterrupted, AIInvalidOutput, AIOutputTruncated, AITurnTimeout
from learnloop.ai.execution import observe_model_calls, single_request
from learnloop.ai.isolation import isolation_mode
from learnloop.ai.providers.chatgpt_plan import (
    ChatGPTPlanProviderClient,
    ChatGPTPlanRequestRejected,
    ChatGPTPlanTransient,
    ChatGPTPlanUnauthorized,
    list_plan_models,
)
from learnloop.ai.routing import ready_client_for_task
from learnloop.ai.runtime import check_ai_runtime
from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import is_subscription_transport
from learnloop.ai.transport import (
    BOUNDED_STRUCTURED_COMPLETION,
    ISOLATED_TURN,
    READ_ONLY_WORKSPACE,
    execute_structured_operation,
)
from learnloop.config import LearnLoopConfig, load_config
from learnloop.config.schema import ChatGPTPlanProviderConfig
from learnloop.practice_index.paid import billing_for, plan_route

from tests.chatgpt_plan_fakes import (
    DOCUMENTED_UNSUPPORTED_FIELDS,
    REFUSED_FIELDS,
    Reply,
    completed_events,
    failed_events,
    fake_chatgpt,
    pause_after,
    run_in_thread,
    sign_in,
)
from tests.helpers import create_basic_vault


class Answer(WireModel):
    ok: bool
    note: str


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    monkeypatch.setattr("learnloop.ai.providers.chatgpt_plan._sleep", lambda _seconds: None)


@pytest.fixture
def server():
    with fake_chatgpt() as fake:
        sign_in(PlanSession(), fake)
        yield fake


def _client(server, **profile) -> ChatGPTPlanProviderClient:
    settings = {"model": "gpt-test-fast", "base_url": server.base_url, "timeout_seconds": 10, **profile}
    return ChatGPTPlanProviderClient("chatgpt", ChatGPTPlanProviderConfig(**settings))


def _ask(client, **kwargs):
    return execute_structured_operation(client, purpose="probe", prompt="Say ok", result_model=Answer, **kwargs)


def test_request_shape_follows_the_plan_route_rules(server):
    server.replies.append(Reply(events=completed_events('{"ok": true, "note": "fine"}')))
    client = _client(server, reasoning_effort="low")
    assert _ask(client) == Answer(ok=True, note="fine")
    request = server.requests[-1]
    body = request["body"]
    assert request["authorization"].startswith("Bearer access-")
    assert body["store"] is False and body["stream"] is True
    assert body["model"] == "gpt-test-fast"
    assert body["instructions"].startswith("Return only valid JSON")
    assert body["input"] == [{"role": "user", "content": "Say ok"}]
    assert body["text"]["format"]["type"] == "json_schema" and body["text"]["format"]["strict"] is True
    assert body["text"]["format"]["schema"]["additionalProperties"] is False
    assert body["reasoning"] == {"effort": "low"}
    assert not set(body) & REFUSED_FIELDS  # no max_output_tokens, temperature, tools, metadata, ...
    # The implementation's list covers everything the docs name.
    assert DOCUMENTED_UNSUPPORTED_FIELDS <= UNSUPPORTED_FIELDS


def test_a_chunked_event_stream_is_reassembled(server):
    server.replies.append(Reply(events=completed_events('{"ok": true, "note": "chunked"}'), chunked=True))
    assert _ask(_client(server)).note == "chunked"


def test_output_budget_rides_in_the_prompt_never_as_max_output_tokens(server):
    client = _client(server)
    server.replies.append(Reply(events=completed_events('{"ok": true, "note": "x"}')))
    from learnloop.ai.execution import generation_limit

    with generation_limit(200):
        _ask(client)
    body = server.requests[-1]["body"]
    assert "max_output_tokens" not in body
    assert "within 200 output tokens" in body["input"][0]["content"]


def test_a_json_repair_is_sent_with_the_budget_of_the_request_it_repairs(server):
    """Final verification F9: the repair states the same budget once and its
    receipt records it, like the request it repairs; no wire cap on either."""

    from learnloop.ai.execution import generation_limit

    client = _client(server, response_format="json_object")
    server.replies.extend([
        Reply(events=completed_events('{"ok": true}')),  # missing a field
        Reply(events=completed_events('{"ok": true, "note": "repaired"}')),
    ])
    events: list[dict] = []
    with generation_limit(200), observe_model_calls(
            lambda action, event: events.append(event) if action == "start" else None):
        assert _ask(client).note == "repaired"
    first, repair = (request["body"] for request in server.requests[-2:])
    assert repair["input"][0]["content"].startswith("Repair the following model output")
    for body in (first, repair):
        content = body["input"][0]["content"]
        assert content.endswith("\n\nKeep the complete JSON response within 200 output tokens.")
        assert content.count("Keep the complete JSON response within") == 1
        assert "max_output_tokens" not in body
    root, *children = events
    assert root["purpose"] == "probe" and root["output_budget_tokens"] == 200
    assert [(child["purpose"], child["output_budget_tokens"]) for child in children] == [
        ("responses_request", 200), ("responses_request", 200)]


def test_receipts_name_the_provider_model_and_answering_model(server):
    events: list[tuple[str, dict]] = []
    server.replies.append(Reply(events=completed_events('{"ok": true, "note": "r"}', model="gpt-test-2026-10-01")))
    client = _client(server)
    with observe_model_calls(lambda action, event: events.append((action, event))):
        _ask(client)
    starts = [event for action, event in events if action == "start"]
    finishes = {event["id"]: event for action, event in events if action == "finish"}
    root, child = starts
    assert root["purpose"] == "probe" and child["purpose"] == "responses_request"
    assert child["parent_call_id"] == root["id"]
    assert child["provider"] == "chatgpt" and child["model"] == "gpt-test-fast"
    assert child["endpoint"] == server.base_url
    finished = finishes[child["id"]]
    assert finished["status"] == "completed" and finished["resolved_model"] == "gpt-test-2026-10-01"
    assert finished["provider_response_id"] == "resp_test_1"
    assert (finished["input_tokens"], finished["output_tokens"]) == (120, 30)
    assert (finished["cached_input_tokens"], finished["reasoning_tokens"]) == (20, 8)
    assert json.loads(finished["usage_json"])["chatgpt_plan"]["request_id"] == "req_ok"
    assert "access-" not in json.dumps(events)
    assert client.consume_usage().total_tokens == 150


def test_capabilities_isolated_tool_free_and_bounded(server):
    client = _client(server)
    assert client.supports(ISOLATED_TURN) and client.supports(BOUNDED_STRUCTURED_COMPLETION)
    # A read-only workspace is served by LearnLoop (test_chatgpt_plan_workspace.py);
    # every other request declares no tools.
    assert client.supports(READ_ONLY_WORKSPACE)
    assert isolation_mode(client) == ("tool_free", None)
    server.replies.append(Reply(events=completed_events('{"ok": true, "note": "iso"}')))
    assert _ask(client, isolated=True).note == "iso"


def test_json_object_mode_carries_the_schema_and_repairs_once(server):
    client = _client(server, response_format="json_object")
    server.replies.extend([
        Reply(events=completed_events('{"ok": true}')),  # missing a field
        Reply(events=completed_events('{"ok": true, "note": "repaired"}')),
    ])
    assert _ask(client).note == "repaired"
    first, second = (request["body"] for request in server.requests[-2:])
    assert first["text"]["format"] == {"type": "json_object"}
    assert "Schema:" in first["instructions"] and '"note"' in first["instructions"]
    assert "Repair the following model output" in second["input"][0]["content"]


def test_single_request_never_repairs_or_retries(server):
    client = _client(server, response_format="json_object")
    server.replies.append(Reply(events=completed_events('{"ok": true}')))
    before = len(server.requests)
    with single_request(), pytest.raises(AIInvalidOutput):
        _ask(client)
    assert len(server.requests) - before == 1
    server.replies.append(Reply(status=503, body={"error": {"code": "subscription_sharing_usage_unavailable",
                                                            "message": "later"}}))
    with single_request(), pytest.raises(ChatGPTPlanTransient):
        _ask(client)
    assert len(server.requests) - before == 2


def test_transient_failures_retry_with_backoff(server):
    client = _client(server)
    server.replies.extend([
        Reply(status=503, body={"error": {"code": "subscription_sharing_usage_unavailable", "message": "later"}}),
        Reply(status=503, body={"detail": "direct routing unavailable"}),
        Reply(events=completed_events('{"ok": true, "note": "third"}')),
    ])
    assert _ask(client).note == "third"


def test_usage_limit_mid_stream_pauses_the_plan_and_routes_fall_back(server, tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-used")  # the fallback is only built, never called
    client = _client(server)
    server.replies.append(Reply(events=failed_events("subscription_sharing_usage_limit_exceeded", after_deltas="{")))
    with pytest.raises(ChatGPTPlanUsageExhausted) as caught:
        _ask(client)
    assert "chatgpt.com/settings/usage" in str(caught.value)
    assert client.consume_usage().total_tokens == 52  # the failed response's usage is still metered
    sent = len(server.requests)
    with pytest.raises(ChatGPTPlanUsageExhausted):
        _ask(client)  # refused locally: nothing sent while paused
    assert len(server.requests) == sent

    vault = _vault(tmp_path, server, routes={"tutor_qa": "chatgpt"}, fallback="openrouter")
    report = check_ai_runtime(vault, load_config(vault / "learnloop.toml"), provider_name="chatgpt")
    assert report.status == "provider_unavailable" and "usage exhausted" in report.message
    config = load_config(vault / "learnloop.toml")
    resolved = ready_client_for_task(vault, config, "tutor_qa")
    assert resolved.fallback_from == "chatgpt" and resolved.provider_name == "openrouter"
    pinned = ready_client_for_task(vault, config, "tutor_qa", explicit="chatgpt")
    assert not pinned.ready and pinned.provider_name == "chatgpt"

    PlanSession().resume()
    assert check_ai_runtime(vault, config, provider_name="chatgpt").ready
    server.replies.append(Reply(events=completed_events('{"ok": true, "note": "back"}')))
    assert _ask(client).note == "back"


def test_usage_limit_before_the_stream_and_not_eligible(server):
    client = _client(server)
    server.replies.append(Reply(status=429, body={"error": {"code": "subscription_sharing_usage_limit_exceeded",
                                                            "message": "limit"}}))
    with pytest.raises(ChatGPTPlanUsageExhausted):
        _ask(client)
    PlanSession().resume()
    server.replies.append(Reply(status=403, body={"error": {"code": "subscription_sharing_user_not_eligible",
                                                            "message": "policy"}}))
    with pytest.raises(ChatGPTPlanNotEligible):
        _ask(client)
    assert PlanSession().status().readiness()[0] == "not_eligible"


def test_a_401_refreshes_once_and_retries(server):
    client = _client(server)
    server.revoke_all_access()  # the saved access token is no longer accepted
    server.replies.append(Reply(events=completed_events('{"ok": true, "note": "refreshed"}')))
    assert _ask(client).note == "refreshed"
    assert server.token_requests[-1]["grant_type"] == "refresh_token"


def test_a_401_under_single_request_fails_and_the_next_call_refreshes(server):
    client = _client(server)
    server.revoke_all_access()
    with single_request(), pytest.raises(ChatGPTPlanUnauthorized):
        _ask(client)
    server.replies.append(Reply(events=completed_events('{"ok": true, "note": "next"}')))
    with single_request():
        assert _ask(client).note == "next"


def test_rejected_structured_output_names_the_setting(server):
    client = _client(server)
    server.replies.append(Reply(status=400, body={"error": {
        "code": "subscription_sharing_unsupported_capability", "message": "text.format unsupported",
        "param": "text.format"}}))
    with pytest.raises(ChatGPTPlanRequestRejected) as caught:
        _ask(client)
    assert 'response_format = "json_object"' in str(caught.value)
    assert len([r for r in server.requests]) == 1  # never retried


def test_incomplete_truncated_and_broken_streams(server):
    client = _client(server)
    incomplete = completed_events("{")[:-1] + [{"type": "response.incomplete", "response": {
        "id": "r", "status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"},
        "usage": {"input_tokens": 5, "output_tokens": 9}}}]
    server.replies.append(Reply(events=incomplete))
    with pytest.raises(AIOutputTruncated):
        _ask(client)
    server.replies.append(Reply(events=completed_events('{"ok": true, "note": "x"}'), truncate=True))
    with single_request(), pytest.raises(ChatGPTPlanTransient) as caught:
        _ask(client)
    assert "before response.completed" in str(caught.value)


def test_the_deadline_shuts_a_stalled_stream(server):
    client = _client(server, timeout_seconds=1)
    server.replies.append(Reply(events=completed_events('{"ok": true, "note": "late"}'), stall=5))
    with pytest.raises(AITurnTimeout):
        _ask(client)


# -- Codex review (2026-10-12): credential acquisition honours interrupts and deadlines --


@pytest.fixture
def expiring():
    """Signed in with an access token already inside the refresh margin."""

    with fake_chatgpt(access_lifetime=60) as fake:
        sign_in(PlanSession(), fake)
        fake.access_lifetime = 3600
        yield fake


def _hold_refresh_lock():
    held, release = threading.Event(), threading.Event()

    def hold() -> None:
        with PlanSession().store.lock("refresh.lock"):
            held.set()
            release.wait(10)

    thread = threading.Thread(target=hold, daemon=True)
    thread.start()
    assert held.wait(5)
    return thread, release


def test_an_interrupt_while_waiting_for_the_refresh_lock_sends_nothing(expiring):
    client = _client(expiring)
    holder, release = _hold_refresh_lock()
    expiring.replies.append(Reply(events=completed_events('{"ok": true, "note": "late"}')))
    thread, out = run_in_thread(lambda: _ask(client))
    time.sleep(0.3)  # the call is waiting for another process's refresh
    client.interrupt()
    thread.join(2)
    stopped_promptly = not thread.is_alive()
    release.set()
    holder.join(5)
    thread.join(10)
    assert stopped_promptly
    assert isinstance(out.get("error"), AIInterrupted), out
    assert expiring.requests == []


def test_a_deadline_that_passes_while_waiting_for_the_refresh_lock_sends_nothing(expiring):
    client = _client(expiring, timeout_seconds=1)
    holder, release = _hold_refresh_lock()
    expiring.replies.append(Reply(events=completed_events('{"ok": true, "note": "late"}')))
    thread, out = run_in_thread(lambda: _ask(client))
    thread.join(2.5)
    stopped_promptly = not thread.is_alive()
    release.set()
    holder.join(5)
    thread.join(10)
    assert stopped_promptly
    assert isinstance(out.get("error"), AITurnTimeout), out
    assert expiring.requests == []


def test_an_interrupt_during_the_token_refresh_keeps_the_new_tokens_and_sends_nothing(expiring):
    reached, release = threading.Event(), threading.Event()
    session = PlanSession(http=pause_after(b"grant_type=refresh_token", reached, release))
    client = ChatGPTPlanProviderClient("chatgpt", ChatGPTPlanProviderConfig(
        model="gpt-test-fast", base_url=expiring.base_url, timeout_seconds=10), session=session)
    expiring.replies.append(Reply(events=completed_events('{"ok": true, "note": "late"}')))
    thread, out = run_in_thread(lambda: _ask(client))
    assert reached.wait(5)  # the refresh answered; the rotated token is not saved yet
    client.interrupt()
    release.set()
    thread.join(10)
    assert isinstance(out.get("error"), AIInterrupted), out
    assert expiring.requests == []
    # The rotation was committed, so the session survives the interrupt.
    store = PlanSession().store
    assert store.load_tokens(store.load_account()).refresh_token in expiring.refresh_tokens
    expiring.replies.clear()  # the interrupted call never used its reply
    expiring.replies.append(Reply(events=completed_events('{"ok": true, "note": "next"}')))
    assert _ask(_client(expiring)).note == "next"


def test_an_expired_deadline_is_never_extended_into_a_send(server, monkeypatch):
    client = _client(server, timeout_seconds=5)
    clock = {"now": 1000.0}
    monkeypatch.setattr("learnloop.ai.providers.chatgpt_plan._monotonic", lambda: clock["now"])
    real_access_token = client.session.access_token

    def slow_token(**kwargs):
        clock["now"] += 10  # the credential step outlives the whole deadline
        return real_access_token(**kwargs)

    monkeypatch.setattr(client.session, "access_token", slow_token)
    server.replies.append(Reply(events=completed_events('{"ok": true, "note": "late"}')))
    before = len(server.requests)
    with pytest.raises(AITurnTimeout):
        _ask(client)
    assert len(server.requests) == before


# -- Codex review (2026-10-12): an overlapping success never erases a newer pause --


def test_a_success_that_overlaps_a_usage_limit_keeps_the_pause(server):
    slow, fast = _client(server), _client(server)
    server.replies.append(Reply(events=completed_events('{"ok": true, "note": "slow"}'), delay=0.6))
    server.replies.append(Reply(status=429, body={"error": {"code": "subscription_sharing_usage_limit_exceeded",
                                                            "message": "limit"}}))
    thread, out = run_in_thread(lambda: _ask(slow))
    for _ in range(100):
        if len(server.replies) == 1:  # the slow request holds its (successful) reply
            break
        time.sleep(0.02)
    with pytest.raises(ChatGPTPlanUsageExhausted):
        _ask(fast)
    thread.join(10)
    assert out["value"].note == "slow"
    assert PlanSession().status().readiness()[0] == "usage_exhausted"
    sent = len(server.requests)
    with pytest.raises(ChatGPTPlanUsageExhausted):
        _ask(fast)  # still refused locally
    assert len(server.requests) == sent


def test_a_success_clears_the_expired_pause_it_saw(server):
    PlanSession().store.update_state(usage_limit={
        "code": "subscription_sharing_usage_limit_exceeded", "at": "2020-01-01T00:00:00+00:00",
        "request_id": None})
    server.replies.append(Reply(events=completed_events('{"ok": true, "note": "fine"}')))
    assert _ask(_client(server)).note == "fine"
    assert "usage_limit" not in PlanSession().store.load_state()


def test_signed_out_is_refused_before_any_request(server):
    PlanSession().sign_out()
    client = _client(server)
    before = len(server.requests)
    with pytest.raises(ChatGPTSignInRequired):
        _ask(client)
    assert len(server.requests) == before


def test_model_list_keeps_listed_models_in_server_order(server):
    models = list_plan_models(server.base_url)
    assert models == [{"slug": "gpt-test-fast", "display_name": "GPT Test Fast"},
                      {"slug": "gpt-test-pro", "display_name": "GPT Test Pro"}]


# -- configuration, readiness, billing ------------------------------------------


def _vault(tmp_path, server, *, routes: dict[str, str] | None = None, fallback: str = "",
           profile: dict | None = None):
    root = tmp_path / "vault"
    if not root.exists():
        create_basic_vault(root)
    path = root / "learnloop.toml"
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    table = tomlkit.table()
    for key, value in {"type": "chatgpt_plan", "model": "gpt-test-fast", "base_url": server.base_url,
                       "timeout_seconds": 10, **(profile or {})}.items():
        table[key] = value
    document["ai"]["providers"]["chatgpt"] = table
    for task, name in (routes or {}).items():
        document["ai"]["routing"][task] = name
    document["ai"]["fallback_provider"] = fallback
    path.write_text(tomlkit.dumps(document), encoding="utf-8")
    return root


def test_base_url_may_only_be_openai_or_loopback():
    with pytest.raises(ValueError):
        LearnLoopConfig.model_validate({"ai": {"providers": {"c": {
            "type": "chatgpt_plan", "model": "m", "base_url": "https://example.com/v1"}}}})
    for allowed in ("https://api.openai.com/v1", "http://127.0.0.1:9/v1"):
        LearnLoopConfig.model_validate({"ai": {"providers": {"c": {
            "type": "chatgpt_plan", "model": "m", "base_url": allowed}}}})


def test_readiness_reads_local_state_only(tmp_path, monkeypatch):
    with fake_chatgpt() as fake:
        vault = _vault(tmp_path, fake)
        config = load_config(vault / "learnloop.toml")
        report = check_ai_runtime(vault, config, provider_name="chatgpt")
        assert report.status == "provider_auth_required" and "learnloop ai signin chatgpt" in report.message
        sign_in(PlanSession(), fake)
        requests = (len(fake.requests), len(fake.token_requests))
        assert check_ai_runtime(vault, config, provider_name="chatgpt").ready
        assert (len(fake.requests), len(fake.token_requests)) == requests  # no network for readiness
        vault = _vault(tmp_path, fake, profile={"enabled": False})
        report = check_ai_runtime(vault, load_config(vault / "learnloop.toml"), provider_name="chatgpt")
        assert report.status == "provider_unavailable" and "enabled = false" in report.message
        vault = _vault(tmp_path, fake, profile={"model": ""})
        report = check_ai_runtime(vault, load_config(vault / "learnloop.toml"), provider_name="chatgpt")
        assert report.status == "provider_missing_config"


def test_billing_class_is_subscription(tmp_path, server):
    profile = ChatGPTPlanProviderConfig(model="m")
    assert is_subscription_transport(profile=profile)
    assert is_subscription_transport(client=_client(server))
    assert billing_for("chatgpt_plan") == "subscription"
    vault = _vault(tmp_path, server, routes={"source_query_rewrite": "chatgpt", "source_rerank": "chatgpt"})
    from learnloop.vault.loader import load_vault

    loaded = load_vault(vault)
    for task in ("source_query_rewrite", "source_rerank"):
        route = plan_route(loaded, task)
        assert (route.provider, route.profile_type, route.billing) == ("chatgpt", "chatgpt_plan", "subscription")
    assert "ChatGPT plan" in recipient(loaded.config, "chatgpt")


def test_t6_rewrite_runs_on_the_plan_with_receipts(tmp_path, server):
    from learnloop.db.repositories import Repository
    from learnloop.source_retrieval.queries import rewrite_query
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths

    vault = _vault(tmp_path, server, routes={"source_query_rewrite": "chatgpt"})
    loaded = load_vault(vault)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    server.replies.append(Reply(events=completed_events(
        '{"passage": "Conditional probability rescales by the event.", "keywords": ["conditional", "bayes"]}')))
    rewrite = rewrite_query(loaded, repository, "why does conditioning rescale probabilities?", owner_id="t")
    assert rewrite.status == "rewritten", rewrite
    assert rewrite.usage["billing"] == "subscription"
    assert rewrite.usage["cost_basis"] == "estimated_only"
    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        rows = connection.execute(
            "SELECT purpose, provider, model, resolved_model, status FROM model_call_receipts ORDER BY started_at"
        ).fetchall()
    assert ("responses_request", "chatgpt", "gpt-test-fast", "gpt-test-2026-10-01", "completed") in rows
    assert any(row[0] == "source_query_rewrite" and row[4] == "completed" for row in rows)
