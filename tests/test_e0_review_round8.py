"""Paid run 2 (plan e0_a47534fecc49ded5, INCOMPLETE): its three failures, fakes only.

* Labels ``invalid_output``: label A (Haiku) answered valid JSON with an
  extra, misspelled top-level key (``validation ?:extra_forbidden``);
  label B (Sonnet) answered two different valid objects with prose
  between them (``json Extra data``). The parse now takes the ONE valid
  object, and an unusable answer gets ONE admitted repair; a question that
  still fails is skipped and counted, the step goes on.
* R3 ``truncated``: a 40-ref window's context request stopped at
  ``max_tokens`` 16,384, thinking included (adaptive thinking is the
  documented default of these models, and the body grammar sends no
  ``thinking`` key). A truncated window request is split into halves of its
  refs; the same truncated request is never re-sent at the same bound.
* The probability Qwen backfill: a paid 200 whose vectors failed the
  production client's contract check (``ValueError``); the batch was not
  saved. The reason is now reported (allowlisted fixed messages), and one
  more pass re-sends the missing batch.
* Every failure is diagnosable from the run directory: a failed role call's
  ``.failed.json`` holds its classification, safe reason and details.

The Messages API shapes are the documented ones: ``content`` holds
``thinking`` blocks (empty text by default) and ``text`` blocks;
``stop_reason`` is ``end_turn``, ``max_tokens``, ``refusal``...; ``usage``
counts thinking in ``output_tokens``. No network: a socket guard refuses
any connection."""
from __future__ import annotations

import json
import socket

import pytest

from learnloop.experiments.contextual_embeddings import bank as B
from learnloop.experiments.contextual_embeddings import corpus as C
from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings import retrieval as Rt
from learnloop.experiments.contextual_embeddings.adapters import HttpResponse
from learnloop.experiments.contextual_embeddings.anthropic_api import AnthropicMessagesClient, parse_answer
from learnloop.experiments.contextual_embeddings.budget import E0Ledger, E0ProviderFailure
from learnloop.experiments.contextual_embeddings.callers import Checkpoints, E0RequestGate, LiveRoleCaller
from tests.e0_fakes import FakeQwenClient, build_e0_vault, fake_respond
from tests.e0_fakes import verified_prices  # noqa: F401 - the fixture below

KEY = "sk-ant-test-key-not-real-0000000000"
#: Model text that must never reach a failure record, a reason or a report.
SECRET = "PRIVATE-MODEL-TEXT-4417"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("network attempted in an offline E0 test")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


def message(text, *, stop="end_turn", output_tokens=900, model=None):
    """A documented Messages API response: an (empty, omitted-display)
    thinking block, then the text block; thinking counted in output_tokens."""

    def build(body):
        return HttpResponse(200, {"id": "msg_1", "type": "message", "role": "assistant",
                                  "model": model or body["model"], "stop_reason": stop, "stop_sequence": None,
                                  "content": [{"type": "thinking", "thinking": "", "signature": "sig"},
                                              {"type": "text", "text": text}],
                                  "usage": {"input_tokens": 1200, "output_tokens": output_tokens}}, "req_ok")
    return build


class Scripted:
    """Answers each POST with the next scripted response (body -> HttpResponse)."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.posts = []

    def post(self, url, *, headers, body, timeout):
        self.posts.append(json.loads(json.dumps(body)))
        return self.responses.pop(0)(body)


GOOD = {"labels": [{"ref": "c1", "relevance": "required"}], "sufficient_sets": [["c1"]], "answerable": True}


def _structured(tmp_path, server, *, role="label_a", result_model=B.LabelPass, ledger=None):
    from learnloop.ai.execution import gate_model_requests

    ledger = ledger or E0Ledger(tmp_path / "ledger")
    pin = pins.ROLE_PINS[role]
    client = AnthropicMessagesClient(pin, environ={"ANTHROPIC_API_KEY": KEY}, transport=server,
                                     sleep=lambda _seconds: None)
    with gate_model_requests(E0RequestGate(ledger, pin, arm=role)):
        return client.structured(purpose=f"e0_{role}", prompt="prompt", result_model=result_model,
                                 max_tokens=pin.max_output_tokens), ledger


def _entries(ledger):
    return list(json.loads(ledger.path.read_text(encoding="utf-8"))["entries"].values())


# -- 1. the label answers ------------------------------------------------------------------


def test_label_as_extra_misspelled_key_is_named_safely_and_repaired_once(tmp_path):
    bad = json.dumps({**GOOD, "aswerable": True})
    server = Scripted(message(bad), message(json.dumps(GOOD)))
    result, ledger = _structured(tmp_path, server)
    assert result == B.LabelPass.model_validate(GOOD)
    assert len(server.posts) == 2 and len(_entries(ledger)) == 2  # the repair is admitted too
    repair = server.posts[1]["messages"][0]["content"]
    assert "validation ?:extra_forbidden" in repair and bad in repair
    assert server.posts[1]["max_tokens"] == server.posts[0]["max_tokens"] == pins.ROLE_PINS["label_a"].max_output_tokens
    assert server.posts[1]["system"] == server.posts[0]["system"]


def test_label_bs_two_different_objects_with_prose_between_get_one_repair(tmp_path):
    first = {"sufficient_sets": [["c1"]], "answerable": True}
    second = {"sufficient_sets": [["c1", "c2"]], "answerable": True}
    text = json.dumps(first) + "\n\nWait, on reflection c2 is also needed:\n\n" + json.dumps(second)
    with pytest.raises(E0ProviderFailure) as raised:
        parse_answer(text, B.SufficiencyPass)
    assert raised.value.reason == "2 different JSON objects validate"
    server = Scripted(message(text), message(json.dumps(second)))
    result, _ledger = _structured(tmp_path, server, role="label_b", result_model=B.SufficiencyPass)
    assert result.sufficient_sets == [["c1", "c2"]]


def test_one_valid_object_inside_prose_or_a_fence_parses_without_a_repair(tmp_path):
    for text in ("Here is my answer:\n" + json.dumps(GOOD) + "\nDone.", "```json\n" + json.dumps(GOOD) + "\n```",
                 json.dumps(GOOD) + "\n" + json.dumps(GOOD)):
        assert parse_answer(text, B.LabelPass) == B.LabelPass.model_validate(GOOD)
    server = Scripted(message("Sure. " + json.dumps(GOOD)))
    _structured(tmp_path, server)
    assert len(server.posts) == 1


def test_a_failed_repair_raises_with_both_safe_reasons_and_no_model_text(tmp_path):
    server = Scripted(message(f"{SECRET} {{\"labels\": 3}}"), message(f"{SECRET} still not json"))
    with pytest.raises(E0ProviderFailure) as raised:
        _structured(tmp_path, server)
    failure = raised.value
    assert failure.classification == "invalid_output" and failure.details["repaired"] is True
    assert failure.reason.startswith("validation labels:list_type") and "after one repair: no JSON object" in failure.reason
    assert SECRET not in str(failure) and SECRET not in json.dumps(failure.details)
    assert len(server.posts) == 2


@pytest.mark.parametrize("stop,kind", [("max_tokens", "truncated"), ("refusal", "refusal")])
def test_a_max_tokens_or_refusal_stop_is_never_repaired_and_carries_its_details(tmp_path, stop, kind):
    server = Scripted(message('{"labels": [', stop=stop, output_tokens=8192))
    with pytest.raises(E0ProviderFailure) as raised:
        _structured(tmp_path, server)
    assert raised.value.classification == kind and len(server.posts) == 1
    assert raised.value.details["stop_reason"] == stop and raised.value.details["output_tokens"] == 8192
    assert raised.value.details["blocks"] == ["text", "thinking"]
    if kind == "truncated":
        assert "thinking included" in raised.value.reason


# -- 2. failures recorded; the truncated request not re-sent -------------------------------


def _caller(tmp_path, server, ledger=None):
    paths, _repository = build_e0_vault(tmp_path)
    handle = C.open_copy(paths.root)
    checkpoints = Checkpoints(tmp_path / "fixtures-local" / "run" / "llm")
    ledger = ledger or E0Ledger(tmp_path / "ledger")
    return LiveRoleCaller(handle.root, handle.vault.config, ledger, checkpoints=checkpoints,
                          environ={"ANTHROPIC_API_KEY": KEY}, anthropic_transport=server), checkpoints, ledger


def test_a_failed_role_call_leaves_a_safe_failure_record(tmp_path):
    server = Scripted(message(f"{SECRET}", output_tokens=95), message(f"{SECRET}", output_tokens=95))
    caller, checkpoints, _ledger = _caller(tmp_path, server)
    with pytest.raises(E0ProviderFailure):
        caller.call("label_b", prompt="p", result_model=B.LabelPass)
    [path] = list(checkpoints.directory.glob(".*.failed.json"))
    record = json.loads(path.read_text())
    assert len(record["reservations"]) == 2
    failure = record["failure"]
    assert failure["role"] == "label_b" and failure["classification"] == "invalid_output"
    assert failure["reason"] == "no JSON object; after one repair: no JSON object"
    assert failure["details"]["stop_reason"] == "end_turn" and failure["details"]["output_tokens"] == 95
    assert SECRET not in path.read_text()


def test_a_request_known_truncated_at_the_same_bound_is_not_sent_again(tmp_path):
    server = Scripted(message('{"contexts": [', stop="max_tokens", output_tokens=16384))
    caller, _checkpoints, ledger = _caller(tmp_path, server)
    for _attempt in range(2):
        with pytest.raises(E0ProviderFailure) as raised:
            caller.call("context", prompt="window", result_model=Rt.GeneratedContexts, arm="R3")
        assert raised.value.classification == "truncated"
    assert len(server.posts) == 1 and len(_entries(ledger)) == 1


def test_the_first_paid_runs_failure_marker_is_read_and_truncation_inferred_from_the_ledger(tmp_path):
    """The first paid run wrote a bare reservation list; its truncated context
    request reported output_tokens == max_tokens in the ledger."""

    server = Scripted(message('{"contexts": [', stop="max_tokens", output_tokens=16384))
    caller, checkpoints, _ledger = _caller(tmp_path, server)
    with pytest.raises(E0ProviderFailure):
        caller.call("context", prompt="window", result_model=Rt.GeneratedContexts, arm="R3")
    [path] = list(checkpoints.directory.glob(".*.failed.json"))
    path.write_text(json.dumps(json.loads(path.read_text())["reservations"]))  # the old format
    fresh = Checkpoints(checkpoints.directory)
    caller.checkpoints = fresh
    with pytest.raises(E0ProviderFailure, match="known truncated"):
        caller.call("context", prompt="window", result_model=Rt.GeneratedContexts, arm="R3")
    assert len(server.posts) == 1


# -- 3. R3: a truncated window is split ---------------------------------------------------


class ContextCaller:
    """Truncates any context request asking for more than ``limit`` refs."""

    def __init__(self, limit):
        self.limit = limit
        self.prompts = []

    def call(self, role, *, prompt, result_model, arm=None):
        self.prompts.append(prompt)
        context = json.loads(prompt[prompt.index("{"):])["context"]
        refs = context.get("only_refs") or [item["ref"] for item in context["excerpt"]]
        if len(refs) > self.limit:
            raise E0ProviderFailure("truncated", reason="stop_reason max_tokens", details={"max_tokens": 16384})
        return result_model.model_validate({"contexts": [
            {"ref": ref, "context": " ".join(["context"] * 60)} for ref in refs]})


def test_a_truncated_window_is_split_until_every_unit_has_its_context(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    largest = max(len(window.unit_ids) for window in snapshot.windows)
    assert largest >= 2
    caller = ContextCaller(limit=max(1, largest // 2))
    headers, stats = Rt.generate_contexts(snapshot, caller)
    assert stats["missing"] == 0 and stats["split_requests"] >= 1 and stats["failed_requests"] == 0
    assert set(headers) == {unit_id for window in snapshot.windows for unit_id in window.unit_ids}
    # The window's own request is the original prompt, byte for byte (its checkpoint is reused).
    window = max(snapshot.windows, key=lambda item: len(item.unit_ids))
    original, _refs = Rt.context_prompt(snapshot, window)
    assert original in caller.prompts and "only_refs" not in original
    assert Rt.CONTEXT_SUBSET_INSTRUCTIONS not in original


def test_a_single_ref_that_still_truncates_is_counted_missing_not_a_stop(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    headers, stats = Rt.generate_contexts(snapshot, ContextCaller(limit=0))
    assert headers == {} and stats["failed_requests"] >= 1 and stats["failures"] == {"truncated": stats[
        "failed_requests"]}
    assert stats["missing"] == sum(len(window.unit_ids) for window in snapshot.windows)


# -- 4. labels go on past one question --------------------------------------------------------


def test_one_questions_unusable_labels_skip_that_question_only(tmp_path):
    from learnloop.experiments.contextual_embeddings.paid import PaidState, label_all

    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    questions = [B.freeze_context(B.BankQuestion(f"q{index}", "development", None, "writer", "explain",
                                                 "intent_explain", text), snapshot)
                 for index, text in enumerate(("Why is the additive identity unique?", "What is a span?"))]

    class Caller:
        def __init__(self):
            self.calls = 0

        def call(self, role, *, prompt, result_model, arm=None):
            self.calls += 1
            if "Why is the additive identity unique?" in prompt and role == "label_b":
                raise E0ProviderFailure("invalid_output", reason="validation ?:extra_forbidden")
            return result_model.model_validate(fake_respond(role, prompt, result_model))

    state = PaidState()
    labelled = label_all(snapshot, questions, {"R1": {}}, Caller(), state)
    assert set(labelled) == {"q1"} and state.stopped is None
    assert state.incomplete.get("labels_failed") == 1 and state.incomplete.get("labels_missing") == 1
    assert any(item["kind"] == "labels_invalid_output" and "extra_forbidden" in item["reason"]
               for item in state.failures)


def test_a_non_item_failure_still_stops_the_labels(tmp_path):
    from learnloop.experiments.contextual_embeddings.paid import PaidState, label_all

    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    question = B.freeze_context(B.BankQuestion("q0", "development", None, "writer", "explain", "intent_explain",
                                               "Why is the additive identity unique?"), snapshot)

    class Caller:
        def call(self, role, *, prompt, result_model, arm=None):
            raise E0ProviderFailure("auth", status_code=401)

    state = PaidState()
    assert label_all(snapshot, [question], {"R1": {}}, Caller(), state) == {}
    assert state.stopped is not None


# -- 5. the Qwen backfill: a safe reason and one more pass ---------------------------------


class FlakyQwen(FakeQwenClient):
    """Answers its ``fail_on``-th batch with one vector too few (a paid 200
    the production contract check refuses), every other batch correctly."""

    modalities = frozenset({"text"})
    max_input_tokens = 32_768

    def __init__(self, fail_on):
        super().__init__()
        self.fail_on = fail_on

    def embed(self, inputs, task_prefix):
        vectors = super().embed(inputs, task_prefix)
        if len(self.calls) == self.fail_on:
            return vectors[:-1]
        return vectors


def test_a_refused_backfill_batch_is_reported_safely_and_sent_once_more(tmp_path, verified_prices):
    from learnloop.experiments.contextual_embeddings.system_arms import (
        backfill_service_copy,
        dense_coverage_complete,
        enable_embeddings_on_copy,
        guarded_factory,
        make_service_copy,
        open_service,
        redact_service_copy,
    )

    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    root = make_service_copy(paths.root, tmp_path / "fixtures-local" / "svc" / "qwen")
    enable_embeddings_on_copy(root)
    handle = open_service(root)
    redact_service_copy(handle, snapshot.policy)
    qwen = FlakyQwen(fail_on=1)
    reports = backfill_service_copy(handle, E0Ledger(tmp_path / "ledger"),
                                    client_factory=guarded_factory(lambda: qwen, snapshot))
    failed = [report for report in reports if report.get("status") == "provider_failed"]
    assert failed and failed[0]["pass"] == 1 and failed[0]["error_type"] == "ValueError"
    assert failed[0]["invalid_reasons"] == {"Embedding provider returned the wrong vector count or width": 1}
    retried = [report for report in reports if report.get("pass") == 2]
    assert retried and retried[0]["status"] == "complete"
    assert dense_coverage_complete(handle)["complete"] is True


def test_the_contract_error_reasons_are_the_production_clients_fixed_messages():
    import inspect

    from learnloop.ai.providers import openai_embedding
    from learnloop.experiments.contextual_embeddings.system_arms import EMBEDDING_CONTRACT_ERRORS, ProtectedTextGuard
    from learnloop.ops import embedding_backfill

    source = inspect.getsource(openai_embedding) + inspect.getsource(embedding_backfill)
    assert all(f'"{message}"' in source for message in EMBEDDING_CONTRACT_ERRORS)

    class Inner:
        def embed(self, inputs, task_prefix):
            raise ValueError("Embedding response indices do not match the input batch")

    class Leaky:
        def embed(self, inputs, task_prefix):
            raise ValueError(f"bad {SECRET}")

    guard = ProtectedTextGuard(Inner(), [])
    with pytest.raises(ValueError):
        guard.embed(["text"], "retrieval-document")
    assert guard.invalid == {"Embedding response indices do not match the input batch": 1}
    leaky = ProtectedTextGuard(Leaky(), [])
    with pytest.raises(ValueError):
        leaky.embed(["text"], "retrieval-document")
    assert leaky.invalid == {"other ValueError": 1}


def test_this_round_keeps_the_plan_id():
    from pathlib import Path

    artifact = json.loads((Path(__file__).resolve().parents[1] / "docs" / "reviews" / "artifacts" / "experiments-e0"
                           / "dry-run-plan.json").read_text())
    # The relabel round (2026-10-23) made a new plan on purpose (label pins, rubric).
    assert artifact["run_id"] == "e0_e6a077cd391c5421" and pins.pins_fingerprint() == artifact["pins_fingerprint"]
