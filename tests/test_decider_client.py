"""The Decider client against a fake endpoint (router spec §12 tests).

Covers the request shape (typed questions only, no unknown fields), the 400
an unknown field earns, typed parsing that fails closed, receipts, and the
OpenRouter/Perplexity dialects. Every request goes to a local fake server.
"""
from __future__ import annotations

import json
import urllib.request

import pytest

from learnloop.ai.decisions import (
    ChoiceAnswer, ChoiceQuestion, DecisionResponseInvalid, NoulAnswer, NoulQuestion,
    ScoreAnswer, ScoreQuestion, parse_response, request_body,
)
from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.execution import call_labels, observe_model_calls
from learnloop.ai.providers.decider import (
    DECISIONS, DeciderProviderClient, DecisionRequestFailed, probe_decider_endpoint,
    resolved_decider_settings,
)
from learnloop.config.schema import DeciderProviderConfig, openrouter_decider_provider
from tests.decider_fakes import fake_decisions

QUESTIONS = {
    "defect": NoulQuestion("Does the review report a defect?", when_true="Broken.", when_false="Fine."),
    "sentiment": ChoiceQuestion("What is the sentiment?", {"positive": "Satisfied", "mixed": None, "negative": "Unhappy"}),
    "severity": ScoreQuestion("How severe?", ("Cosmetic", "Inconvenient", "Unusable")),
}


def client_for(server, monkeypatch, *, api="openrouter", key_env=None, model=None, **profile):
    env = key_env or ("OPENROUTER_API_KEY" if api == "openrouter" else "PERPLEXITY_API_KEY")
    monkeypatch.setenv(env, server.key)
    config = DeciderProviderConfig(api=api, base_url=server.base_url, model=model, **profile)
    return DeciderProviderClient("test_decider", config)


def test_request_body_holds_exactly_model_state_and_typed_questions():
    body = request_body("perplexity/pplx-decider-v1.1-27b", {"review": "text"}, QUESTIONS)
    assert set(body) == {"model", "state", "questions"}
    assert body["questions"]["defect"] == {
        "type": "noul", "instructions": "Does the review report a defect?",
        "criteria": {"true": "Broken.", "false": "Fine."},
    }
    assert body["questions"]["sentiment"]["criteria"] == {"positive": "Satisfied", "mixed": None, "negative": "Unhappy"}
    assert body["questions"]["severity"]["criteria"] == ["Cosmetic", "Inconvenient", "Unusable"]


@pytest.mark.parametrize("build", [
    lambda: NoulQuestion(""),
    lambda: NoulQuestion("q", when_true="only one side"),
    lambda: ChoiceQuestion("q", {}),
    lambda: ChoiceQuestion("q", {f"o{i}": None for i in range(256)}),
    lambda: ChoiceQuestion("q", {"": "unnamed"}),
    lambda: ScoreQuestion("q", ()),
    lambda: ScoreQuestion("q", tuple(str(i) for i in range(11))),
    lambda: ScoreQuestion("q", "not a sequence of levels"),
])
def test_question_classes_refuse_invalid_shapes(build):
    with pytest.raises(ValueError):
        build()


def test_requests_refuse_untyped_questions_and_bad_counts():
    with pytest.raises(TypeError, match="NoulQuestion"):
        request_body("m", "state", {"raw": {"type": "noul", "instructions": "q", "temperature": 0}})
    with pytest.raises(ValueError, match="1 to 128"):
        request_body("m", "state", {})
    with pytest.raises(ValueError, match="1 to 128"):
        request_body("m", "state", {f"q{i}": NoulQuestion("q") for i in range(129)})
    with pytest.raises(ValueError, match="state"):
        request_body("m", None, {"q": NoulQuestion("q")})
    with pytest.raises(ValueError, match="state"):
        request_body("m", "  ", {"q": NoulQuestion("q")})


def test_openrouter_dialect_posts_the_typed_request_and_parses_typed_answers(monkeypatch):
    with fake_decisions(dialect="openrouter") as server:
        client = client_for(server, monkeypatch)
        assert client.supports(DECISIONS) and not client.supports("structured_completion")
        result = client.decide({"review": "Battery died."}, QUESTIONS, purpose="test")
    request = server.requests[0]
    assert request["path"] == "/api/alpha/decisions"
    assert set(request["body"]) == {"model", "state", "questions"}
    assert request["body"]["model"] == "perplexity/pplx-decider-v1.1-27b"
    assert request["headers"]["Authorization"] == "Bearer test-key"
    assert request["headers"]["X-Title"] == "LearnLoop"
    assert isinstance(result.answers["defect"], NoulAnswer) and result.answers["defect"].p_yes == 0.73
    choice = result.answers["sentiment"]
    assert isinstance(choice, ChoiceAnswer) and choice.choice == "positive"
    assert set(choice.probabilities) == {"positive", "mixed", "negative"}
    score = result.answers["severity"]
    assert isinstance(score, ScoreAnswer) and set(score.probabilities) == {0, 1, 2} and score.score == 1.0
    assert result.model == "perplexity/pplx-decider-v1.1-27b-20261006"
    assert result.provider == "Perplexity" and result.response_id == "gen-dec-1"
    assert result.cost is not None and result.input_tokens > 0


def test_perplexity_dialect_uses_its_path_key_and_model(monkeypatch):
    with fake_decisions(dialect="perplexity") as server:
        client = client_for(server, monkeypatch, api="perplexity")
        result = client.decide("A review.", {"q": NoulQuestion("Is it a review?")}, purpose="test")
    request = server.requests[0]
    assert request["path"] == "/v1/decisions"
    assert request["body"]["model"] == "pplx-decider-v1.1-27b"
    assert "X-Title" not in request["headers"]
    assert result.model == "pplx-decider-v1.1-27b" and result.cost is None


def test_fake_endpoint_answers_400_to_an_unknown_field_and_the_client_never_sends_one(monkeypatch):
    with fake_decisions() as server:
        raw = json.dumps({"model": "m", "state": "s", "questions": {"q": {"type": "noul", "instructions": "q"}},
                          "temperature": 0}).encode()
        request = urllib.request.Request(
            server.base_url + "/alpha/decisions", data=raw, method="POST",
            headers={"Authorization": "Bearer test-key", "Content-Type": "application/json"},
        )
        with pytest.raises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request, timeout=5)
        assert caught.value.code == 400
        client = client_for(server, monkeypatch)
        client.decide("s", {"q": NoulQuestion("q")}, purpose="test")
    assert set(server.requests[-1]["body"]) == {"model", "state", "questions"}


def test_error_statuses_surface_without_parsing(monkeypatch):
    def reject(body):
        if body["state"] == "rate":
            return 429, {"error": {"message": "slow down", "type": "rate_limit"}}, {"Retry-After": "2"}
        if body["state"] == "bad":
            return 400, {"error": {"message": "Unknown field: x", "type": "invalid_request"}}, {}
        return None

    with fake_decisions(respond=reject) as server:
        client = client_for(server, monkeypatch)
        with pytest.raises(DecisionRequestFailed) as limited:
            client.decide("rate", {"q": NoulQuestion("q")}, purpose="test")
        assert limited.value.status == 429 and limited.value.retry_after == 2.0
        with pytest.raises(DecisionRequestFailed, match="HTTP 400: invalid_request: Unknown field") as bad:
            client.decide("bad", {"q": NoulQuestion("q")}, purpose="test")
        assert bad.value.status == 400
    # A wrong key is a 401 from the fake.
    with fake_decisions(key="other") as server:
        monkeypatch.setenv("OPENROUTER_API_KEY", "wrong")
        client = DeciderProviderClient("d", DeciderProviderConfig(base_url=server.base_url))
        with pytest.raises(DecisionRequestFailed) as unauthorized:
            client.decide("s", {"q": NoulQuestion("q")}, purpose="test")
        assert unauthorized.value.status == 401


def test_missing_key_and_oversized_state_refuse_before_any_request(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(AIProviderUnavailable, match="OPENROUTER_API_KEY"):
        DeciderProviderClient("d", openrouter_decider_provider())
    with fake_decisions() as server:
        client = client_for(server, monkeypatch, max_input_tokens=10)
        with pytest.raises(ValueError, match="input limit"):
            client.decide("x" * 100, {"q": NoulQuestion("q")}, purpose="test")
    assert server.requests == []


def _payload(**changes):
    payload = {
        "model": "m",
        "answers": {"q": {"type": "noul", "noul": 0.4}},
        "usage": {"input_tokens": 10, "output_tokens": 1},
    }
    payload.update(changes)
    return payload


@pytest.mark.parametrize("payload, reason", [
    (_payload(rationale="because"), "unknown fields"),
    (_payload(answers={"q": {"type": "noul", "noul": 0.4, "why": "x"}}), "unknown fields"),
    (_payload(answers={}), "do not match"),
    (_payload(answers={"q": {"type": "noul", "noul": 0.4}, "extra": {"type": "noul", "noul": 1}}), "do not match"),
    (_payload(answers={"q": {"type": "choice", "choice": "a"}}), "has type"),
    (_payload(answers={"q": {"type": "noul", "noul": 1.2}}), "outside"),
    (_payload(answers={"q": {"type": "noul", "noul": float("nan")}}), "finite"),
    (_payload(answers={"q": {"type": "noul", "noul": True}}), "finite"),
    (_payload(usage={"input_tokens": 1}), "output_tokens"),
    (_payload(usage={"input_tokens": 1, "output_tokens": 1, "credits": 3}), "unknown fields"),
    (_payload(model=""), "no model"),
    ([], "not a JSON object"),
])
def test_parsing_fails_closed_on_any_contract_change(payload, reason):
    with pytest.raises(DecisionResponseInvalid, match=reason):
        parse_response(payload, {"q": NoulQuestion("q")})


@pytest.mark.parametrize("answer, reason", [
    ({"type": "choice", "choice": "a", "probabilities": {"a": 0.5}}, "cover exactly"),
    ({"type": "choice", "choice": "a", "probabilities": {"a": 0.5, "b": 0.1}}, "sum to one"),
    ({"type": "choice", "choice": "c", "probabilities": {"a": 0.5, "b": 0.5}}, "not asked"),
    ({"type": "choice", "choice": "a", "probabilities": {"a": 0.5, "b": 0.5}, "confidence": 2}, "outside"),
])
def test_choice_answers_must_cover_the_asked_options(answer, reason):
    with pytest.raises(DecisionResponseInvalid, match=reason):
        parse_response(_payload(answers={"q": answer}), {"q": ChoiceQuestion("q", {"a": None, "b": None})})


@pytest.mark.parametrize("answer, reason", [
    ({"type": "score", "score": 3, "probabilities": {"0": 0.5, "1": 0.5}}, "outside the rubric"),
    ({"type": "score", "score": 1, "probabilities": {"0": 0.5, "2": 0.5}}, "cover exactly"),
    ({"type": "score", "score": 1, "probabilities": {"0": 0.5, "1": 0.5}, "legend": {"0": "a"}}, "legend"),
])
def test_score_answers_must_match_the_rubric(answer, reason):
    with pytest.raises(DecisionResponseInvalid, match=reason):
        parse_response(_payload(answers={"q": answer}), {"q": ScoreQuestion("q", ("low", "high"))})


def test_receipt_carries_body_usage_cost_model_and_labels(monkeypatch):
    events = []
    with fake_decisions() as server:
        client = client_for(server, monkeypatch)
        with observe_model_calls(lambda action, event: events.append((action, dict(event)))), call_labels(
            judge="decider", question_set_version="qs_v1", state_hash="abc",
        ):
            client.decide({"item": "x"}, {"q": NoulQuestion("q")}, purpose="llm_probability")
    (start_action, start), (finish_action, finish) = events
    assert (start_action, finish_action) == ("start", "finish")
    assert start["purpose"] == "llm_probability" and start["provider"] == "test_decider"
    assert start["judge"] == "decider" and start["question_set_version"] == "qs_v1" and start["state_hash"] == "abc"
    assert json.loads(start["input_text"]) == server.requests[0]["body"]
    assert "test-key" not in json.dumps(start)
    assert finish["status"] == "completed"
    assert finish["input_tokens"] > 0 and finish["output_tokens"] == 3 and finish["cost"] > 0
    assert finish["resolved_model"].endswith("-20261006") and finish["provider_response_id"] == "gen-dec-1"


def test_a_malformed_paid_answer_keeps_its_usage_on_the_receipt(monkeypatch):
    events = []

    def malformed(body):
        return 200, {"model": "m", "answers": {}, "usage": {"input_tokens": 9, "output_tokens": 1, "cost": 1e-7}}, {}

    with fake_decisions(respond=malformed) as server:
        client = client_for(server, monkeypatch)
        with observe_model_calls(lambda action, event: events.append((action, dict(event)))):
            with pytest.raises(DecisionResponseInvalid):
                client.decide("s", {"q": NoulQuestion("q")}, purpose="test")
    finish = events[-1][1]
    assert finish["status"] == "failed" and finish["input_tokens"] == 9 and finish["cost"] == 1e-7


def test_settings_resolve_from_the_dialect():
    openrouter = resolved_decider_settings(openrouter_decider_provider())
    assert openrouter.url == "https://openrouter.ai/api/alpha/decisions"
    assert openrouter.api_key_env == "OPENROUTER_API_KEY"
    assert openrouter.model == "perplexity/pplx-decider-v1.1-27b"
    assert openrouter.price_per_million_input == 0.02
    direct = resolved_decider_settings(DeciderProviderConfig(api="perplexity"))
    assert direct.url == "https://api.perplexity.ai/v1/decisions"
    assert (direct.api_key_env, direct.model) == ("PERPLEXITY_API_KEY", "pplx-decider-v1.1-27b")


def test_probe_reads_the_free_listing_without_a_key():
    seen = []

    def http(method, url, headers, body, timeout):
        seen.append((method, url, dict(headers), body))
        return 200, {}, json.dumps({"data": {
            "id": "perplexity/pplx-decider-v1.1-27b",
            "architecture": {"output_modalities": ["decisions"]},
            "endpoints": [{"provider_name": "Perplexity", "status": 0, "pricing": {"prompt": "0.00000002"}}],
        }}).encode()

    result = probe_decider_endpoint(openrouter_decider_provider(), http=http)
    assert result["reachable"] is True and result["endpoints"][0]["provider"] == "Perplexity"
    method, url, headers, body = seen[0]
    assert method == "GET" and body is None and "Authorization" not in headers
    assert url == "https://openrouter.ai/api/v1/models/perplexity/pplx-decider-v1.1-27b/endpoints"
    chat_only = probe_decider_endpoint(
        openrouter_decider_provider(),
        http=lambda *a: (200, {}, json.dumps({"data": {"architecture": {"output_modalities": ["text"]}, "endpoints": []}}).encode()),
    )
    assert chat_only["reachable"] is False
    assert probe_decider_endpoint(DeciderProviderConfig(api="perplexity"))["checked"] is False
