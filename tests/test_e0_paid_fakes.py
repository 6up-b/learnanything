"""The E0 paid run's steps end to end with fakes only (no network, no keys).

Every embedding goes to ``FakeEmbeddingTransport`` / ``FakeQwenClient``,
every LLM role to ``fake_respond``; the run still admits each request
through the E0 ledger, so budget stops, resume and the incomplete report are
exercised exactly as a paid run would hit them."""
from __future__ import annotations

import socket

import pytest

from learnloop.experiments.contextual_embeddings import corpus as C
from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.adapters import CANARY_CHUNKS, CANARY_QUERY
from learnloop.experiments.contextual_embeddings.budget import E0Ledger
from learnloop.experiments.contextual_embeddings.callers import Checkpoints, FakeRoleCaller, LiveRoleCaller
from learnloop.experiments.contextual_embeddings.paid import effective_query, run_paid
from learnloop.experiments.contextual_embeddings.report import assert_aggregate, render
from learnloop.experiments.contextual_embeddings.retrieval import GeneratedContexts
from learnloop.experiments.contextual_embeddings.system_arms import enable_embeddings_on_copy, make_service_copy, \
    open_service, rank_system
from tests.e0_fakes import FAKE_KEYS, FakeEmbeddingTransport, FakeQwenClient, FakeRoleClient, build_e0_vault, \
    fake_respond

from tests.e0_fakes import verified_prices  # noqa: F401 - the fixture below

#: Every metered pin priced as verified (E0 admission refuses unverified prices; fix round 4).
pytestmark = pytest.mark.usefixtures("verified_prices")


STRATA = {"reader_deictic": 2, "distant_same_source": 1, "direct_lookup": 1, "no_support": 1, "intent_explain": 1}
DIMS = {pin.model: pin.dimensions for pin in pins.EMBEDDING_PINS.values()}


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("network attempted in a fake paid run")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


def _run(tmp_path, ledger, *, run_dir=None, transport=None, caller=None, **kwargs):
    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    transport = transport or FakeEmbeddingTransport(
        dims=DIMS, int8_models=frozenset({"pplx-embed-context-v1-4b", "pplx-embed-v1-4b"}))
    qwen = FakeQwenClient()
    caller = caller or FakeRoleCaller(fake_respond, ledger)
    result = run_paid(snapshot, ledger=ledger, caller=caller, run_dir=run_dir, transport=transport,
                      qwen_client_factory=lambda: qwen, strata=STRATA, environ=FAKE_KEYS, **kwargs)
    return result, transport, qwen, caller, paths


def test_a_fake_paid_run_completes_every_arm_and_computes_the_stop_rules(tmp_path):
    ledger = E0Ledger(tmp_path / "ledger")
    result, transport, qwen, caller, _paths = _run(tmp_path, ledger, run_dir=tmp_path / "fixtures-local" / "run")
    assert result["status"] == "complete", (result["failures"], result["incomplete_reason"])
    assert set(result["retrieval"]) == {"R1", "R2", "R3", "R3_bm25", "R4_grouped", "R4_singleton", "R4_independent",
                                        "R5_grouped", "R5_singleton", "R5_independent"}
    assert all(contract["status"] == "cached_first" for contract in result["contracts"].values())
    assert set(result["decisions"]) == {"S1", "S2", "S3", "S4", "production_adoption"}
    assert result["decisions"]["production_adoption"] == "not_authorized_by_e0"
    assert result["finalists"]["one_model"] in ("R1", "R2", "R3")
    assert result["ledger"]["committed_usd"] <= pins.E0_CAP_USD
    assert {role for role, _prompt in caller.calls} >= {"writer", "context", "label_a", "label_b", "tutor"}
    assert result["planned"]["missing"] == {}
    assert_aggregate(result)
    report = render(result)
    assert "S1:" in report and "not production authorization" in report
    for role, prompt in caller.calls:
        assert "Solution: apply linearity" not in prompt and "Exam question" not in prompt, role


def test_a_budget_stop_reports_incomplete_with_no_substitution(tmp_path):
    allocation = {"embeddings": 0.00002, "drafting_context": 1.0, "labels_audits": 1.0, "answers_verification": 1.0}
    ledger = E0Ledger(tmp_path / "ledger", cap_usd=3.00002, allocation=allocation)
    result, _transport, _qwen, _caller, _paths = _run(tmp_path, ledger)
    assert result["status"] == "incomplete"
    blocked = {row["item"] for row in result["failures"] if row["kind"] == "budget"}
    assert blocked
    # A blocked arm has no results, and no other arm or recipe stands in for it.
    assert not blocked & set(result["retrieval"])
    assert result["ledger"]["committed_usd"] <= 3.00002
    assert "Incomplete" in render(result)


def test_resume_pays_only_for_what_is_missing(tmp_path):
    ledger = E0Ledger(tmp_path / "ledger")
    run_dir = tmp_path / "fixtures-local" / "run"
    _result, transport, qwen, _caller, _paths = _run(tmp_path, ledger, run_dir=run_dir)
    documents = [request for request in transport.requests
                 if CANARY_CHUNKS[0] not in str(request["body"]) and request["body"].get("input_type") == "document"]
    assert documents
    # Same corpus, same run directory: no document and no stored query is re-sent;
    # only the canaries and the online latency's fresh queries go out again.
    snapshot = C.build_snapshot(C.open_copy(tmp_path / "fixtures-local" / "contextual-embeddings" / "vaults" / "e0vault"))
    again = FakeEmbeddingTransport(dims=DIMS, int8_models=frozenset({"pplx-embed-context-v1-4b", "pplx-embed-v1-4b"}))
    qwen_again = FakeQwenClient()
    run_paid(snapshot, ledger=ledger, caller=FakeRoleCaller(fake_respond, ledger), run_dir=run_dir, transport=again,
             qwen_client_factory=lambda: qwen_again, strata=STRATA, environ=FAKE_KEYS)
    resent = [request for request in again.requests
              if CANARY_CHUNKS[0] not in str(request["body"]) and request["body"].get("input_type") == "document"]
    assert resent == []
    # Only the route canaries' public query goes out again (fix round 4: the
    # canary checks the query contract too, every run).
    assert [request for request in again.requests if request["body"].get("input_type") == "query"
            and CANARY_QUERY not in str(request["body"])] == []
    # Qwen: only its canary document and canary query; documents, queries and
    # the online measurements are all reused.
    assert qwen_again.calls == [(1, "retrieval-document"), (1, "retrieval-query")]


def test_the_live_caller_admits_each_physical_request_and_resumes_from_checkpoints(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    handle = C.open_copy(paths.root)
    ledger = E0Ledger(tmp_path / "ledger")
    client = FakeRoleClient("e0_openrouter_sonnet",
                            respond=lambda *_args: {"contexts": [{"ref": "p1", "context": "a context"}]})
    roles = {"context": pins.ROLE_PINS["adjudicator"]}  # a metered route, to see money admitted
    caller = LiveRoleCaller(handle.root, handle.vault.config, ledger, checkpoints=Checkpoints(tmp_path / "ckpt"),
                            role_pins=roles, client_factory=lambda _profile: client)
    first = caller.call("context", prompt="prompt text", result_model=GeneratedContexts)
    report = ledger.report()
    assert report["requests"] == 1 and report["committed_usd"] > 0
    measured = caller.last.latency_s
    resumed = LiveRoleCaller(handle.root, handle.vault.config, ledger, checkpoints=Checkpoints(tmp_path / "ckpt"),
                             role_pins=roles, client_factory=lambda _profile: client)
    assert resumed.call("context", prompt="prompt text", result_model=GeneratedContexts) == first
    assert len(client.requests) == 1 and resumed.cached == 1 and ledger.report()["requests"] == 1
    # The resumed call reports the ORIGINAL measurement, marked cached (Codex review F9).
    assert resumed.last.cached and resumed.last.latency_s == measured
    assert "e0_openrouter_sonnet" in caller.config.ai.providers
    assert "e0_openrouter_sonnet" not in handle.vault.config.ai.providers  # in memory only


def test_r0_runs_find_sources_on_a_service_copy_and_the_frozen_copy_is_untouched(tmp_path):
    from learnloop.experiments.contextual_embeddings.bank import smoke_bank
    from learnloop.experiments.contextual_embeddings.runner import tree_digest

    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    before = tree_digest(paths.root)
    service_root = make_service_copy(paths.root, tmp_path / "fixtures-local" / "service" / "r0")
    handle = open_service(service_root)
    questions, _ = smoke_bank(snapshot)
    ledger = E0Ledger(tmp_path / "ledger")
    ranked, report = rank_system(handle, snapshot, questions, arm="R0", ledger=ledger,
                                 query_text={question.query_id: effective_query(question, snapshot)
                                             for question in questions})
    assert set(ranked) == {question.query_id for question in questions}
    assert any(ranked.values())
    assert report["interface"] == "find_sources" and report["ranked"] == len(questions)
    assert set(report["pages"]) <= {"1", "2"} and "not_requested" in report["verification"]
    assert all(snapshot.policy.permitted(*key) for units in ranked.values() for unit_id in units
               for key in snapshot.unit(unit_id).keys)
    assert {"withheld", "unmapped", "page_duplicates", "pool_modes", "dense_used"} <= set(report)
    assert tree_digest(paths.root) == before
    with pytest.raises(ValueError, match="fixtures-local"):
        enable_embeddings_on_copy(tmp_path / "not-local")
    enable_embeddings_on_copy(service_root)
    from learnloop.vault.loader import load_vault

    enabled = load_vault(service_root, load_environment=False).config
    assert enabled.embedding.enabled and enabled.embedding.backfill_enabled
    assert enabled.ai.routing.embedding == "openrouter_embedding"
    with pytest.raises(ValueError):
        enable_embeddings_on_copy(service_root)


def test_a_pinned_reader_budget_is_checked_against_measured_answer_latency(tmp_path):
    ledger = E0Ledger(tmp_path / "ledger")
    # A steady simulated tutor latency, so millisecond delivery noise cannot read as a regression.
    caller = FakeRoleCaller(fake_respond, ledger, latency=lambda _role, _prompt: 1.0)
    result, _transport, _qwen, _caller, _paths = _run(tmp_path, ledger, latency_budget_s=60.0, caller=caller)
    assert result["reader_latency_budget_s"] == 60.0
    assert all(entry["p95"] is not None for entry in result["answer_latency_s"].values())
    assert result["decisions"]["S2"]["arms"]["D2"]["latency_fits"] is True
