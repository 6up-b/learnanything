"""E0 hosted adapters with fakes (spec §4.3): ordering, methods, spaces, validation, resume."""
from __future__ import annotations

import base64
import json

import numpy as np
import pytest

from learnloop.experiments.contextual_embeddings import adapters as A
from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.budget import E0BudgetExceeded, E0Ledger
from learnloop.experiments.contextual_embeddings.retrieval import exact_search
from tests.e0_fakes import FAKE_KEYS, FakeEmbeddingTransport, FakeQwenClient, hash_vector, int8_vector

from tests.e0_fakes import verified_prices  # noqa: F401 - the fixture below

#: Every metered pin priced as verified (E0 admission refuses unverified prices; fix round 4).
pytestmark = pytest.mark.usefixtures("verified_prices")


PPLX = pins.EMBEDDING_PINS["pplx_context_4b"]
PPLX_IND = pins.EMBEDDING_PINS["pplx_4b"]
VOYAGE = pins.EMBEDDING_PINS["voyage_context_4"]
VOYAGE_IND = pins.EMBEDDING_PINS["voyage_4_large"]
DIMS = {PPLX.model: PPLX.dimensions, PPLX_IND.model: PPLX_IND.dimensions, VOYAGE.model: VOYAGE.dimensions,
        VOYAGE_IND.model: VOYAGE_IND.dimensions}


def _ledger(tmp_path, cap=pins.E0_CAP_USD):
    allocation = {key: min(value, cap) for key, value in pins.ALLOCATION_USD.items()} if cap < 25 else None
    if allocation is not None:
        allocation = {key: cap / 4 for key in pins.ALLOCATION_USD}
    return E0Ledger(tmp_path / "ledger", cap_usd=cap, allocation=allocation)


def _adapter(cls, pin, tmp_path, *, encoding, transport, store=None, receipts=None, ledger=None, sleep=None):
    return cls(pin, encoding=encoding, recipe="plain", ledger=ledger or _ledger(tmp_path), arm="test",
               transport=transport, receipts=receipts or A.Receipts(tmp_path / "receipts.jsonl"),
               store=store or A.VectorStore(tmp_path / "vectors"), environ=FAKE_KEYS,
               sleep=sleep or (lambda _seconds: None))


def _documents():
    return [A.Document("w1", (A.Chunk("w1:a", "Definition of a vector space."), A.Chunk("w1:b", "Theorem on identity."),
                              A.Chunk("w1:c", "Proof by the definition.")), key="k1"),
            A.Document("w2", (A.Chunk("w2:a", "Linear maps preserve zero."),), key="k2")]


@pytest.mark.parametrize("cls,pin", [(A.PerplexityContextualAdapter, PPLX), (A.VoyageContextualAdapter, VOYAGE)])
def test_grouped_responses_are_matched_by_index_not_position(tmp_path, cls, pin):
    transport = FakeEmbeddingTransport(dims=DIMS, int8_models=frozenset({PPLX.model}))
    adapter = _adapter(cls, pin, tmp_path, encoding="grouped", transport=transport)
    vectors = adapter.encode_documents(_documents())
    assert [len(document) for document in vectors] == [3, 1]
    expected = A.decode(int8_vector("Theorem on identity.\nDefinition of a vector space. Theorem on identity. "
                                    "Proof by the definition.", pin.dimensions) if pin is PPLX
                        else hash_vector("Theorem on identity.\nDefinition of a vector space. Theorem on identity. "
                                         "Proof by the definition.", pin.dimensions), pin)
    assert np.allclose(vectors[0][1], expected, atol=1e-6)
    body = transport.requests[0]["body"]
    if pin is PPLX:
        # The documented Perplexity body has no input_type (Perplexity canary round).
        assert "input_type" not in body and body["encoding_format"] == "base64_int8"
    else:
        assert body["input_type"] == "document"
    assert all(abs(np.linalg.norm(vector) - 1) < 1e-5 for document in vectors for vector in document)


def test_query_and_document_methods_are_separate(tmp_path):
    transport = FakeEmbeddingTransport(dims=DIMS)
    adapter = _adapter(A.VoyageContextualAdapter, VOYAGE, tmp_path, encoding="grouped", transport=transport)
    adapter.encode_queries([A.PreparedQuery("q1", "what is a vector space?")])
    adapter.encode_documents(_documents()[:1])
    assert [request["body"]["input_type"] for request in transport.requests] == ["query", "document"]
    independent = _adapter(A.VoyageIndependentAdapter, VOYAGE_IND, tmp_path, encoding="independent",
                           transport=transport)
    independent.encode_documents([A.Document("u1", (A.Chunk("u1", "Some passage text."),), key="u1")])
    assert transport.requests[-1]["body"]["truncation"] is False


def test_wrong_methods_are_refused_before_any_request(tmp_path):
    transport = FakeEmbeddingTransport(dims=DIMS)
    with pytest.raises(A.WrongMethod):
        _adapter(A.PerplexityIndependentAdapter, PPLX_IND, tmp_path, encoding="grouped", transport=transport)
    with pytest.raises(A.WrongMethod):
        _adapter(A.PerplexityContextualAdapter, PPLX, tmp_path, encoding="independent", transport=transport)
    singleton = _adapter(A.PerplexityContextualAdapter, PPLX, tmp_path, encoding="singleton", transport=transport)
    with pytest.raises(A.WrongMethod):
        singleton.encode_documents(_documents()[:1])
    assert transport.requests == []


def test_mixed_spaces_and_foreign_query_encoders_are_refused(tmp_path):
    transport = FakeEmbeddingTransport(dims=DIMS)
    grouped = _adapter(A.VoyageContextualAdapter, VOYAGE, tmp_path, encoding="grouped", transport=transport)
    other = _adapter(A.VoyageIndependentAdapter, VOYAGE_IND, tmp_path, encoding="independent", transport=transport)
    assert grouped.document_space_id != other.document_space_id
    vector = [1.0] + [0.0] * (VOYAGE.dimensions - 1)
    with pytest.raises(A.MixedSpace):
        A.build_index([("u1", grouped.document_space_id, grouped.query_encoder_id, vector),
                       ("u2", other.document_space_id, other.query_encoder_id, vector)])
    index = A.build_index([("u1", grouped.document_space_id, grouped.query_encoder_id, vector)])
    # Same width, different encoder: still refused.
    with pytest.raises(A.MixedSpace):
        exact_search(index, vector, query_encoder=other.query_encoder_id)
    assert exact_search(index, vector, query_encoder=grouped.query_encoder_id) == [("u1", 1.0)]


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_nonfinite_vectors_are_refused(tmp_path, bad):
    def corrupt(rows):
        rows[0]["data"][0]["embedding"][0] = bad
        return rows

    transport = FakeEmbeddingTransport(dims=DIMS, corrupt=corrupt)
    adapter = _adapter(A.VoyageContextualAdapter, VOYAGE, tmp_path, encoding="grouped", transport=transport)
    with pytest.raises(A.AdapterError, match="non-finite") as error:
        adapter.encode_documents(_documents()[:1])
    assert error.value.kind == "validation"


def test_zero_wrong_width_and_out_of_range_vectors_are_refused():
    with pytest.raises(A.AdapterError, match="zero vector"):
        A.decode([0.0] * VOYAGE.dimensions, VOYAGE)
    with pytest.raises(A.AdapterError, match="dimensions") as error:
        A.decode([1.0] * (VOYAGE.dimensions - 1), VOYAGE)
    assert error.value.kind == "contract"
    with pytest.raises(A.AdapterError, match="out of range"):
        A.decode([200] + [1] * (PPLX.dimensions - 1), PPLX)
    packed = base64.b64encode(np.asarray([1] * PPLX.dimensions, dtype=np.int8).tobytes()).decode()
    decoded = A.decode(packed, PPLX)
    assert decoded.dtype == np.float32 and abs(float(np.linalg.norm(decoded)) - 1) < 1e-5


def test_missing_or_duplicate_indices_are_contract_errors(tmp_path):
    transport = FakeEmbeddingTransport(dims=DIMS, corrupt=lambda rows: [rows[0], rows[0]])
    adapter = _adapter(A.VoyageContextualAdapter, VOYAGE, tmp_path, encoding="grouped", transport=transport)
    with pytest.raises(A.AdapterError) as error:
        adapter.encode_documents(_documents())
    assert error.value.kind == "contract"


def test_oversize_input_is_refused_never_truncated(tmp_path):
    transport = FakeEmbeddingTransport(dims=DIMS)
    adapter = _adapter(A.VoyageContextualAdapter, VOYAGE, tmp_path, encoding="grouped", transport=transport)
    huge = A.Document("big", (A.Chunk("big:a", "x " * (VOYAGE.max_tokens_per_document * 3)),), key="big")
    with pytest.raises(A.AdapterError, match="limit") as error:
        adapter.encode_documents([huge])
    assert error.value.kind == "limit" and transport.requests == []


def test_transient_failures_retry_twice_each_attempt_admitted_auth_never(tmp_path):
    ledger = _ledger(tmp_path)
    transport = FakeEmbeddingTransport(dims=DIMS, fail=lambda count, _body: 503 if count <= 2 else None)
    adapter = _adapter(A.VoyageContextualAdapter, VOYAGE, tmp_path, encoding="grouped", transport=transport,
                       ledger=ledger)
    adapter.encode_documents(_documents()[:1])
    assert len(transport.requests) == 3 and ledger.report()["requests"] == 3
    auth = FakeEmbeddingTransport(dims=DIMS, fail=lambda _count, _body: 401)
    adapter = _adapter(A.VoyageContextualAdapter, VOYAGE, tmp_path, encoding="grouped", transport=auth,
                       store=A.VectorStore(None))
    with pytest.raises(A.AdapterError) as error:
        adapter.encode_documents(_documents()[:1])
    assert error.value.kind == "auth" and len(auth.requests) == 1
    always = FakeEmbeddingTransport(dims=DIMS, fail=lambda _count, _body: 500)
    adapter = _adapter(A.VoyageContextualAdapter, VOYAGE, tmp_path, encoding="grouped", transport=always,
                       store=A.VectorStore(None))
    with pytest.raises(A.AdapterError):
        adapter.encode_documents(_documents()[:1])
    assert len(always.requests) == 1 + pins.TRANSIENT_RETRIES


def test_a_refused_admission_sends_nothing(tmp_path):
    ledger = E0Ledger(tmp_path / "tiny", cap_usd=0.0000001,
                      allocation={key: 0.000000025 for key in pins.ALLOCATION_USD})
    transport = FakeEmbeddingTransport(dims=DIMS)
    adapter = _adapter(A.VoyageContextualAdapter, VOYAGE, tmp_path, encoding="grouped", transport=transport,
                       ledger=ledger)
    with pytest.raises(E0BudgetExceeded):
        adapter.encode_documents(_documents())
    assert transport.requests == []


def test_an_absent_key_fails_before_admission_or_request(tmp_path):
    ledger = _ledger(tmp_path)
    transport = FakeEmbeddingTransport(dims=DIMS)
    adapter = A.VoyageContextualAdapter(VOYAGE, encoding="grouped", recipe="plain", ledger=ledger, arm="t",
                                        transport=transport, environ={}, sleep=lambda _s: None)
    with pytest.raises(A.AdapterError) as error:
        adapter.encode_documents(_documents()[:1])
    assert error.value.kind == "auth" and transport.requests == [] and ledger.report()["requests"] == 0


def test_resume_is_idempotent_by_vector_key(tmp_path):
    store = A.VectorStore(tmp_path / "vectors")
    transport = FakeEmbeddingTransport(dims=DIMS)
    first = _adapter(A.VoyageContextualAdapter, VOYAGE, tmp_path, encoding="grouped", transport=transport, store=store)
    vectors = first.encode_documents(_documents())
    sent = len(transport.requests)
    resumed = _adapter(A.VoyageContextualAdapter, VOYAGE, tmp_path, encoding="grouped", transport=transport,
                       store=A.VectorStore(tmp_path / "vectors"))
    assert resumed.encode_documents(_documents()) == vectors
    assert len(transport.requests) == sent
    partial = [*_documents(), A.Document("w3", (A.Chunk("w3:a", "A new window."),), key="k3")]
    resumed.encode_documents(partial)
    assert len(transport.requests) == sent + 1
    assert len(transport.requests[-1]["body"]["inputs"]) == 1


def test_canary_caches_first_output_and_flags_drift(tmp_path):
    store = A.VectorStore(tmp_path / "vectors")
    transport = FakeEmbeddingTransport(dims=DIMS)
    adapter = _adapter(A.VoyageContextualAdapter, VOYAGE, tmp_path, encoding="grouped", transport=transport, store=store)
    assert adapter.canary()["status"] == "cached_first"
    assert adapter.canary()["status"] == "stable"
    drifted = FakeEmbeddingTransport(dims=DIMS, corrupt=lambda rows: [
        {**row, "data": [{**item, "embedding": hash_vector("drift" + str(item["index"]), VOYAGE.dimensions)}
                         for item in row["data"]]} for row in rows])
    adapter = _adapter(A.VoyageContextualAdapter, VOYAGE, tmp_path, encoding="grouped", transport=drifted, store=store)
    with pytest.raises(A.CanaryDrift):
        adapter.canary()


def test_receipts_and_ledger_never_hold_keys(tmp_path):
    transport = FakeEmbeddingTransport(dims=DIMS)
    adapter = _adapter(A.PerplexityIndependentAdapter, PPLX_IND, tmp_path, encoding="independent",
                       transport=FakeEmbeddingTransport(dims=DIMS, int8_models=frozenset({PPLX_IND.model})))
    adapter.encode_documents([A.Document("u1", (A.Chunk("u1", "Some passage."),), key="u1")])
    assert transport is not None
    written = (tmp_path / "receipts.jsonl").read_text() + (tmp_path / "ledger" / "e0_spend_ledger.json").read_text()
    for value in FAKE_KEYS.values():
        assert value not in written
    assert "Authorization" not in written and "Some passage." not in written
    row = json.loads((tmp_path / "receipts.jsonl").read_text().splitlines()[0])
    assert row["status"] == "ok" and row["model"] == PPLX_IND.model


def test_qwen_adapter_uses_production_prefixes_and_admits_each_batch(tmp_path):
    client = FakeQwenClient()
    ledger = _ledger(tmp_path)
    adapter = A.QwenAdapter(pins.EMBEDDING_PINS["qwen3_8b"], client_factory=lambda: client, recipe="production_recipe",
                            ledger=ledger, arm="R1", store=A.VectorStore(None), sleep=lambda _s: None)
    adapter.encode_documents([A.Document(f"u{i}", (A.Chunk(f"u{i}", f"text {i} words"),)) for i in range(70)])
    adapter.encode_queries([A.PreparedQuery("q", "what is it")])
    assert [task for _count, task in client.calls] == ["retrieval-document", "retrieval-document", "retrieval-query"]
    assert ledger.report()["requests"] == 3


def test_exact_search_ties_break_by_id(tmp_path):
    vector = [1.0, 0.0, 0.0]
    index = A.SpaceVectors("ds", "qe", ("u_b", "u_a", "u_c"), np.asarray([vector, vector, [0.0, 1.0, 0.0]],
                                                                          dtype=np.float32))
    assert [unit for unit, _ in exact_search(index, vector, query_encoder="qe", top_k=3)] == ["u_a", "u_b", "u_c"]
