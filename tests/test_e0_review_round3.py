"""Regressions for the Codex final verify of the E0 harness (F20 reopened, F21), fakes only.

F21: a missing usage report never settles a metered reservation to $0. Every
E0 settle path reconciles only on an explicit cost or a reported input-token
count; otherwise the whole reservation stays as ``unknown_billing`` and
counts against the cap.

F20: a keyword fallback is not a dense ranking. A Qwen arm's delegated
comparison is dense only when the comparison's per-source production
searches actually ranked by meaning over a complete index.

Every test runs offline behind a socket guard: the fake ``openai`` module,
hash-vector embeddings and fake role clients; production retrieval runs on
service copies with ``ai.active_provider = "manual"``."""
from __future__ import annotations

from decimal import Decimal
import json
import socket
from types import SimpleNamespace

import pytest

from learnloop.ai.execution import gate_model_requests
from learnloop.experiments.contextual_embeddings import adapters as A
from learnloop.experiments.contextual_embeddings import bank as B
from learnloop.experiments.contextual_embeddings import corpus as C
from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.budget import E0BudgetExceeded, E0Ledger, LedgerEnvelope
from learnloop.experiments.contextual_embeddings.callers import E0RequestGate, role_cost
from tests.e0_fakes import FAKE_KEYS, FakeEmbeddingTransport, FakeRoleClient, build_e0_vault
from tests.embedding_fakes import BagOfWordsEmbedder
from tests.openai_fakes import install_fake_openai


from tests.e0_fakes import verified_prices  # noqa: F401 - the fixture below

#: Every metered pin priced as verified (E0 admission refuses unverified prices; fix round 4).
pytestmark = pytest.mark.usefixtures("verified_prices")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("network attempted in an offline E0 test")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


def _entries(ledger):
    """The ledger's entries in admission order (the file is keyed by id)."""

    entries = json.loads(ledger.path.read_text(encoding="utf-8"))["entries"].values()
    return sorted(entries, key=lambda entry: entry["reserved_at"])


def _no_usage_response():
    # A paid 200 with valid vectors and no ``usage`` at all.
    return SimpleNamespace(data=[SimpleNamespace(index=0, embedding=[3.0, 4.0])])


# -- F21 ---------------------------------------------------------------------------------------


def test_f21_omitted_embedding_usage_keeps_the_reservation_through_the_real_wrapper(tmp_path, monkeypatch):
    """Two usage-less embedding requests against an allowance that fits one
    reservation: the first is kept whole as unknown billing, the second is
    refused before it is sent."""

    from learnloop.ai.providers.openai_embedding import OpenAIEmbeddingProviderClient, prefixed_text
    from learnloop.config import OpenAIEmbeddingProviderConfig
    from learnloop.experiments.contextual_embeddings.system_arms import SystemRequestGate

    module = install_fake_openai(monkeypatch, embeddings=[_no_usage_response(), _no_usage_response()])
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    client = OpenAIEmbeddingProviderClient("openrouter_embedding", OpenAIEmbeddingProviderConfig(dimensions=2))
    sdk = module.instances[0]
    query = "why is the zero vector unique"
    described = prefixed_text(query, "retrieval-query", client.model_id)
    reserved = pins.token_upper_bound(described) * pins.EMBEDDING_PINS["qwen3_8b"].price_per_million_upper_bound \
        / 1_000_000
    allowance = reserved * 1.5  # one reservation fits, two do not
    ledger = E0Ledger(tmp_path / "ledger", cap_usd=allowance, allocation={"embeddings": allowance})
    config = SimpleNamespace(source_retrieval=SimpleNamespace(llm_price_per_million=None))
    gate = SystemRequestGate(ledger, config, arm="R1_service_rrf")
    with gate_model_requests(gate):
        assert client.embed([query], "retrieval-query") == [[0.6, 0.8]]
        with pytest.raises(E0BudgetExceeded):
            client.embed([query], "retrieval-query")
    assert len(sdk.embedding_requests) == 1  # the second was never sent
    [entry] = _entries(ledger)
    assert entry["status"] == "unknown_billing" and entry["actual_usd"] is None
    assert entry["usage"] == {"input_tokens": None, "output_tokens": 0, "cost": None}
    report = ledger.report()
    assert report["committed_usd"] == pytest.approx(reserved)
    assert report["outstanding_reservations_usd"] == pytest.approx(reserved)
    assert report["refusals"] == 1


def _system_gate(tmp_path, price=2.0):
    from learnloop.experiments.contextual_embeddings.system_arms import SystemRequestGate

    ledger = E0Ledger(tmp_path / "ledger")
    config = SimpleNamespace(source_retrieval=SimpleNamespace(llm_price_per_million=price))
    return ledger, SystemRequestGate(ledger, config, arm="R0")


@pytest.mark.parametrize("usage", [{}, {"output_tokens": 0}, {"output_tokens": 40}, {"input_tokens": 0},
                                   {"input_tokens": 0, "output_tokens": 0}, {"input_tokens": True},
                                   {"cost": float("nan")}, {"cost": -1.0}])
def test_f21_a_metered_system_llm_request_without_input_usage_or_cost_keeps_its_reservation(tmp_path, usage):
    ledger, gate = _system_gate(tmp_path)
    metered = SimpleNamespace(provider_type="openrouter", provider_name="e0_openrouter_sonnet",
                              model=pins.ROLE_PINS["adjudicator"].model)
    admission = gate.admit(metered, purpose="verify", prompt="a prompt " * 50, budget=200)
    gate.settle(admission, usage)
    [entry] = _entries(ledger)
    assert entry["actual_usd"] is None and entry["status"] == "unknown_billing"
    assert ledger.report()["committed_usd"] == pytest.approx(float(entry["reserved_usd"]))


def test_f21_reported_input_tokens_or_an_explicit_cost_still_reconcile(tmp_path):
    ledger, gate = _system_gate(tmp_path)
    metered = SimpleNamespace(provider_type="openrouter", provider_name="e0_openrouter_sonnet",
                              model=pins.ROLE_PINS["adjudicator"].model)
    # Input reported, output not: the output side is charged at its reserved bound.
    gate.settle(gate.admit(metered, purpose="verify", prompt="x" * 400, budget=200), {"input_tokens": 50})
    # Both reported: exactly those counts.
    gate.settle(gate.admit(metered, purpose="verify", prompt="x" * 400, budget=200),
                {"input_tokens": 50, "output_tokens": 10})
    # An explicit cost, zero included, is the bill.
    gate.settle(gate.admit(metered, purpose="verify", prompt="x" * 400, budget=200),
                {"cost": 0.0, "output_tokens": 0})
    actual = [float(entry["actual_usd"]) for entry in _entries(ledger)]
    # Priced by the verified metered role pin for the route's model (fix round 4).
    pin = pins.ROLE_PINS["adjudicator"]
    assert actual == pytest.approx([role_cost(pin, 50, 200), role_cost(pin, 50, 10), 0.0])
    # An embedding with its input tokens reported reconciles at the Qwen bound.
    embedding = SimpleNamespace(provider_type="openai_embedding", provider_name="openrouter_embedding",
                                model=pins.EMBEDDING_PINS["qwen3_8b"].model)
    gate.settle(gate.admit(embedding, purpose="embedding", prompt=["a query"], budget=None),
                {"input_tokens": 7, "output_tokens": 0})
    last = _entries(ledger)[-1]
    assert float(last["actual_usd"]) == pytest.approx(7 * pins.EMBEDDING_PINS["qwen3_8b"]
                                                      .price_per_million_upper_bound / 1e6)


def test_f21_the_role_gate_never_settles_a_metered_request_from_output_tokens_alone(tmp_path):
    ledger = E0Ledger(tmp_path / "ledger")
    pin = pins.ROLE_PINS["adjudicator"]
    assert pin.billing == "metered"
    gate = E0RequestGate(ledger, pin, arm="labels")
    gate.settle(gate.admit(None, purpose="adjudicate", prompt="p" * 300, budget=500), {"output_tokens": 0})
    gate.settle(gate.admit(None, purpose="adjudicate", prompt="p" * 300, budget=500), {"output_tokens": 120})
    gate.settle(gate.admit(None, purpose="adjudicate", prompt="p" * 300, budget=500), {"input_tokens": 80})
    entries = _entries(ledger)
    assert [entry["status"] for entry in entries] == ["unknown_billing", "unknown_billing", "settled"]
    assert entries[0]["actual_usd"] is None and entries[1]["actual_usd"] is None
    # Input reported, output not: charged at the output bound the request was sent with.
    assert float(entries[2]["actual_usd"]) == pytest.approx(role_cost(pin, 80, 500))


class _UsageTransport(FakeEmbeddingTransport):
    """The fake hosted transport with its usage replaced (or removed)."""

    def __init__(self, usage, **kwargs):
        super().__init__(**kwargs)
        self.usage = usage

    def post(self, url, *, headers, body, timeout):
        response = super().post(url, headers=headers, body=body, timeout=timeout)
        payload = {key: value for key, value in response.body.items() if key != "usage"}
        if self.usage is not None:
            payload["usage"] = self.usage
        return A.HttpResponse(response.status, payload, response.request_id)


@pytest.mark.parametrize("usage", [None, {}, {"total_tokens": 0, "prompt_tokens": 0}, {"prompt_tokens": 0},
                                   {"total_tokens": False}])
def test_f21_a_hosted_embedding_without_positive_usage_keeps_its_reservation(tmp_path, usage):
    pin = pins.EMBEDDING_PINS["voyage_4_large"]
    ledger = E0Ledger(tmp_path / "ledger")
    transport = _UsageTransport(usage, dims={pin.model: pin.dimensions})
    adapter = A.VoyageIndependentAdapter(pin, encoding="independent", recipe="plain", ledger=ledger, arm="R5",
                                         transport=transport, receipts=A.Receipts(tmp_path / "receipts.jsonl"),
                                         store=A.VectorStore(tmp_path / "vectors"), environ=FAKE_KEYS,
                                         sleep=lambda _seconds: None)
    adapter.encode_documents([A.Document("w1", (A.Chunk("w1:a", "Definition of a vector space."),), key="k1")])
    [entry] = _entries(ledger)
    assert entry["actual_usd"] is None and entry["status"] == "unknown_billing"
    assert float(entry["reserved_usd"]) > 0
    assert ledger.report()["committed_usd"] == pytest.approx(float(entry["reserved_usd"]))


def test_f21_the_ledger_envelope_keeps_a_zero_dollar_reconciliation_reserved(tmp_path):
    ledger = E0Ledger(tmp_path / "ledger")
    envelope = LedgerEnvelope(ledger, category="embeddings", provider="openrouter", route="qwen")
    zero = envelope.reserve(Decimal("0.001"))
    envelope.settle(zero, Decimal(0))  # the backfill prices input_tokens=0 at $0
    known = envelope.reserve(Decimal("0.001"))
    envelope.settle(known, Decimal("0.0004"))
    entries = {entry["status"]: entry for entry in _entries(ledger)}
    assert entries["unknown_billing"]["actual_usd"] is None
    assert float(entries["settled"]["actual_usd"]) == pytest.approx(0.0004)
    assert ledger.report()["committed_usd"] == pytest.approx(0.0014)


# -- F20 ---------------------------------------------------------------------------------------


def _snapshot(tmp_path):
    paths, _repository = build_e0_vault(tmp_path, "e0vault", manual_ai=True)
    return C.build_snapshot(C.open_copy(paths.root)), paths


def _qwen_service(tmp_path, paths, *, dense):
    import tomlkit

    from learnloop.experiments.contextual_embeddings.system_arms import (
        enable_embeddings_on_copy,
        make_service_copy,
        open_service,
        redact_service_copy,
    )

    root = make_service_copy(paths.root, tmp_path / "fixtures-local" / "service" / f"qwen-{dense}")
    enable_embeddings_on_copy(root)
    toml = root / "learnloop.toml"
    document = tomlkit.parse(toml.read_text(encoding="utf-8"))
    document.setdefault("source_retrieval", tomlkit.table())["dense"] = dense
    toml.write_text(tomlkit.dumps(document), encoding="utf-8")
    return open_service(root), redact_service_copy


def _verify_all(_role, prompt, _model):
    context = json.loads(prompt[prompt.index("{"):])["context"]
    refs = [candidate["ref"] for candidate in context["candidates"]]
    return {"judgments": [{"ref": ref, "verdict": "answers", "rationale": "On topic."} for ref in refs],
            "picks": refs[:1]}


def _compare_nothing(_role, _prompt, _model):
    # A comparison with no lines (the ranking is the compared sources).
    return {"contributions": [], "relations": [], "missing_perspectives": []}


def _compare_question(snapshot):
    return B.freeze_context(B.BankQuestion("q1", "development", None, "writer", "compare", "intent_compare",
                                           "Compare the two treatments of a basis of a vector space"), snapshot)


def _run_compare(tmp_path, *, dense):
    from learnloop.experiments.contextual_embeddings.system_arms import backfill_service_copy, rank_system

    snapshot, paths = _snapshot(tmp_path)
    handle, redact = _qwen_service(tmp_path, paths, dense=dense)
    redact(handle, snapshot.policy)
    embedder = BagOfWordsEmbedder(dims=4096)
    backfill_service_copy(handle, E0Ledger(tmp_path / f"backfill-{dense}"), client_factory=lambda: embedder)
    question = _compare_question(snapshot)
    ranked, report = rank_system(handle, snapshot, [question], arm="R1_service_rrf",
                                 ledger=E0Ledger(tmp_path / f"ledger-{dense}"),
                                 query_text={"q1": question.retrieval_query},
                                 clients={"embedder": embedder,
                                          "rerank_client": FakeRoleClient("codex_low", respond=_verify_all),
                                          "compare_client": FakeRoleClient("codex_low", respond=_compare_nothing)})
    return ranked, report


def test_f20_a_keyword_only_comparison_is_missing_for_a_qwen_arm(tmp_path):
    """The verify's scenario through production compare and search:
    ``embedding.enabled = true``, ``source_retrieval.dense = false``, a
    successful query embedding and a verified keyword match. Every source
    search is keyword only, so the Qwen arm has no ranking for the query."""

    ranked, report = _run_compare(tmp_path, dense=False)
    assert ranked == {} and report["ranked"] == 0 and report["dense_used"] == 0, report
    assert report["missing"] == {"dense_not_used": 1}, report
    # Each source's production search ran keyword only (dense switched off).
    assert report["compare_source_searches"] == {"keyword_only:disabled": 3}, report


def test_f20_a_comparison_whose_source_searches_ranked_by_meaning_is_dense(tmp_path):
    ranked, report = _run_compare(tmp_path, dense=True)
    # The book and the talk ranked by meaning; the redacted exam has nothing to embed.
    assert report["compare_source_searches"] == {"dense": 2, "nothing_embeddable": 1}, report
    assert "q1" in ranked and report["dense_used"] == 1 and not report["missing"], report


def test_f20_the_comparison_outcome_needs_every_counted_source_search_dense():
    from learnloop.experiments.contextual_embeddings.system_arms import _comparison_outcome

    result = SimpleNamespace(status="too_few_sources", manifest={"comparison": {"manifest": {
        "verification": {"status": "verified", "sources_with_hits": 1},
        "query_embedding": {"status": "embedded"}}}})
    dense = {"lists": ["keyword", "meaning"], "dense": {"status": "ready"}, "hits": 3}
    keyword = {"lists": ["keyword"], "dense": {"status": "disabled"}, "hits": 1}
    partial = {"lists": ["keyword", "meaning"], "dense": {"status": "partial"}, "hits": 2}
    empty = {"lists": [], "dense": {"status": "empty"}, "hits": 0}
    assert _comparison_outcome(result, [dense])[2] is True
    assert _comparison_outcome(result, [dense, empty])[2] is True  # nothing embeddable, nothing found
    assert _comparison_outcome(result, [keyword])[2] is False      # the verify's case
    assert _comparison_outcome(result, [dense, keyword])[2] is False
    assert _comparison_outcome(result, [partial])[2] is False      # incomplete coverage
    assert _comparison_outcome(result, [])[2] is False             # no search observed
    assert _comparison_outcome(result, None)[2] is False
    # Every outcome above is a completed comparison: never a missing reason of its own.
    assert _comparison_outcome(result, [keyword])[1] is None


def test_f20_the_search_observer_is_scoped_and_removed(tmp_path):
    from learnloop.experiments.contextual_embeddings.system_arms import observe_compare_searches
    from learnloop.source_retrieval import compare as compare_module

    original = compare_module.search_spans
    with observe_compare_searches() as outer:
        with observe_compare_searches() as inner:
            assert compare_module.search_spans is not original
        assert inner == [] and outer == []
        assert compare_module.search_spans is not original
    assert compare_module.search_spans is original
