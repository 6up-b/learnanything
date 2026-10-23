"""The Perplexity canary round (SAFE TO RUN, fakes only).

The first paid run (plan e0_a47534fecc49ded5, stopped after the canaries,
$0.0004 spent) failed all three Perplexity canaries with ``contract`` in about
70 ms. The adapters sent ``input_type`` and ``encoding_format: "int8"``; the
published API reference for both endpoints (read 2026-10-23) has no
``input_type`` and ``encoding_format`` is ``base64_int8`` or ``base64_binary``:
a 422 ``HTTPValidationError``.

* The documented request and response shapes, from
  https://docs.perplexity.ai/api-reference/embeddings-post and
  https://docs.perplexity.ai/api-reference/contextualized-embeddings-post.
* A failed attempt records ``http_status`` and a SAFE ``contract_reason``
  (allowlisted codes, field paths, JSON types, counts; never body text or keys),
  a parse failure after a 2xx included.
* Resume: the plan id (pins fingerprint) is unchanged by this round, the
  ledger is reopened without --new-authorization, and an interrupted
  reservation stays counted in full.

No network: a socket guard refuses any connection."""
from __future__ import annotations

import base64
import io
import json
from pathlib import Path
import socket
import urllib.error

import numpy as np
import pytest

from learnloop.experiments.contextual_embeddings import adapters as A
from learnloop.experiments.contextual_embeddings import corpus as C
from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.budget import E0Ledger, Request, authorized_ledger
from tests.e0_fakes import FAKE_KEYS, PPLX_CONTEXTUAL_URL, PPLX_EMBEDDINGS_URL, FakeEmbeddingTransport, \
    FakeQwenClient, build_e0_vault, perplexity_documented, perplexity_violations, pplx_base64_int8

from tests.e0_fakes import verified_prices  # noqa: F401 - the fixture below

ARTIFACT = Path(__file__).resolve().parents[1] / "docs" / "reviews" / "artifacts" / "experiments-e0" / "dry-run-plan.json"
CONTEXT = pins.EMBEDDING_PINS["pplx_context_4b"]
INDEPENDENT = pins.EMBEDDING_PINS["pplx_4b"]
DIMS = {pin.model: pin.dimensions for pin in pins.EMBEDDING_PINS.values()}
#: Text that must never reach a receipt (a provider error ``msg`` may echo it).
SECRET_TEXT = "PRIVATE-PASSAGE-TEXT-7731"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("network attempted in an offline E0 test")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


def _adapter(pin, tmp_path, *, transport, encoding=None, ledger=None, cls=None):
    cls = cls or A.ADAPTERS[pin.name]
    encoding = encoding or ("grouped" if pin.method == "grouped" else "independent")
    return cls(pin, encoding=encoding, recipe="plain", ledger=ledger or E0Ledger(tmp_path / "ledger"), arm="R4_test",
               transport=transport, receipts=A.Receipts(tmp_path / "receipts.jsonl"),
               store=A.VectorStore(tmp_path / "vectors"), environ=FAKE_KEYS, sleep=lambda _seconds: None)


def _receipts(tmp_path):
    return [json.loads(line) for line in (tmp_path / "receipts.jsonl").read_text().splitlines()]


def _int8(seed, dims):
    values = np.random.default_rng(seed).integers(-127, 128, size=dims)
    values[0] = 100  # never a zero vector
    return [int(value) for value in values]


class Recording:
    """A transport answering with one fixed (documented) response, recording bodies."""

    def __init__(self, response):
        self.response = response
        self.bodies = []

    def post(self, url, *, headers, body, timeout):
        self.bodies.append((url, json.loads(json.dumps(body))))
        return self.response(url, body) if callable(self.response) else self.response


# -- 1. the documented request bodies -----------------------------------------------------


def test_the_contextual_bodies_are_the_documented_shape(tmp_path, verified_prices):
    adapter = _adapter(CONTEXT, tmp_path, transport=FakeEmbeddingTransport(dims=DIMS))
    documents = [A.Document("w1", (A.Chunk("a", "First chunk."), A.Chunk("b", "Second chunk."))),
                 A.Document("w2", (A.Chunk("c", "Only chunk."),))]
    body = adapter._document_body(documents)
    # ContextualizedEmbeddingsRequest: input (array of documents, each an array of
    # chunk strings), model, optional dimensions and encoding_format; nothing else.
    assert set(body) == {"input", "model", "dimensions", "encoding_format"}
    assert body["input"] == [["First chunk.", "Second chunk."], ["Only chunk."]]
    assert body["model"] == "pplx-embed-context-v1-4b" and body["encoding_format"] == "base64_int8"
    assert 128 <= body["dimensions"] <= 2560
    # The documented query method: the same endpoint and model, each query a one-chunk document.
    query = adapter._query_body([A.PreparedQuery("q", "What is a vector space?")])
    assert set(query) == set(body) and query["input"] == [["What is a vector space?"]]
    assert CONTEXT.query_endpoint == CONTEXT.document_endpoint == PPLX_CONTEXTUAL_URL
    assert perplexity_violations(PPLX_CONTEXTUAL_URL, body) == []
    assert perplexity_violations(PPLX_CONTEXTUAL_URL, query) == []


def test_the_independent_bodies_are_the_documented_shape(tmp_path, verified_prices):
    adapter = _adapter(INDEPENDENT, tmp_path, transport=FakeEmbeddingTransport(dims=DIMS))
    body = adapter._document_body([A.Document("u1", (A.Chunk("u1", "A passage."),)),
                                   A.Document("u2", (A.Chunk("u2", "Another."),))])
    # EmbeddingsRequest: input (a string or an array of strings), model, optional
    # dimensions and encoding_format; no input_type and no query prefix.
    assert set(body) == {"input", "model", "dimensions", "encoding_format"}
    assert body["input"] == ["A passage.", "Another."] and body["model"] == "pplx-embed-v1-4b"
    assert body["encoding_format"] == "base64_int8"
    query = adapter._query_body([A.PreparedQuery("q", "What is a vector space?")])
    assert query == {**body, "input": ["What is a vector space?"]}
    assert INDEPENDENT.query_endpoint == INDEPENDENT.document_endpoint == PPLX_EMBEDDINGS_URL
    assert perplexity_violations(PPLX_EMBEDDINGS_URL, body) == []


def test_the_first_paid_runs_bodies_break_the_documented_schema():
    """The bodies the first paid run sent (fail-before): 422 on both endpoints."""

    contextual = {"model": "pplx-embed-context-v1-4b", "input": [["a", "b"]], "input_type": "document",
                  "dimensions": 2560, "encoding_format": "int8"}
    independent = {"model": "pplx-embed-v1-4b", "input": ["a"], "input_type": "query", "dimensions": 2560,
                   "encoding_format": "int8"}
    for url, body in ((PPLX_CONTEXTUAL_URL, contextual), (PPLX_EMBEDDINGS_URL, independent)):
        response = perplexity_documented(url, body, request_id="r", vector=lambda *_args: [1] * 2560)
        assert response.status == 422 and response.body is None
        assert set(response.error_codes) == {"body.input_type:extra_forbidden", "body.encoding_format:enum"}


# -- 2. the documented responses parse ----------------------------------------------------


def test_a_documented_contextual_response_decodes_by_index(tmp_path, verified_prices):
    rows = {(d, c): _int8(10 * d + c, CONTEXT.dimensions) for d in range(2) for c in range(2)}
    # The documented ContextualizedEmbeddingsResponse, rows deliberately out of order.
    documented = {
        "object": "list", "model": "pplx-embed-context-v1-4b",
        "data": [
            {"object": "list", "index": 1, "data": [
                {"object": "embedding", "index": 0, "embedding": pplx_base64_int8(rows[1, 0])}]},
            {"object": "list", "index": 0, "data": [
                {"object": "embedding", "index": 1, "embedding": pplx_base64_int8(rows[0, 1])},
                {"object": "embedding", "index": 0, "embedding": pplx_base64_int8(rows[0, 0])}]},
        ],
        "usage": {"prompt_tokens": 12, "total_tokens": 12,
                  "cost": {"input_cost": 0.0000006, "total_cost": 0.0000006, "currency": "USD"}},
    }
    ledger = E0Ledger(tmp_path / "ledger")
    transport = Recording(A.HttpResponse(200, documented, "pplx-req-1"))
    adapter = _adapter(CONTEXT, tmp_path, transport=transport, ledger=ledger)
    vectors = adapter.encode_documents([
        A.Document("w1", (A.Chunk("a", "First."), A.Chunk("b", "Second.")), key="k1"),
        A.Document("w2", (A.Chunk("c", "Third."),), key="k2")])
    expected = [[A.decode(pplx_base64_int8(rows[0, 0]), CONTEXT), A.decode(pplx_base64_int8(rows[0, 1]), CONTEXT)],
                [A.decode(pplx_base64_int8(rows[1, 0]), CONTEXT)]]
    for got, want in zip(vectors, expected, strict=True):
        assert np.allclose(np.asarray(got), np.asarray(want), atol=1e-6)
    # The documented usage.cost.total_cost (USD) is the bill.
    [entry] = json.loads((tmp_path / "ledger" / "e0_spend_ledger.json").read_text())["entries"].values()
    assert float(entry["actual_usd"]) == pytest.approx(0.0000006) and entry["status"] == "settled"
    [receipt] = _receipts(tmp_path)
    assert receipt["status"] == "ok" and receipt["http_status"] == 200 and receipt["billed_usd"] == pytest.approx(6e-7)
    assert receipt["request_id"] == "pplx-req-1" and receipt["contract_reason"] is None


def test_a_documented_independent_response_decodes_by_index(tmp_path, verified_prices):
    rows = [_int8(index, INDEPENDENT.dimensions) for index in range(2)]
    documented = {"object": "list", "model": "pplx-embed-v1-4b",
                  "data": [{"object": "embedding", "index": 1, "embedding": pplx_base64_int8(rows[1])},
                           {"object": "embedding", "index": 0, "embedding": pplx_base64_int8(rows[0])}],
                  "usage": {"prompt_tokens": 4, "total_tokens": 4,
                            "cost": {"input_cost": 1.2e-7, "total_cost": 1.2e-7, "currency": "USD"}}}
    adapter = _adapter(INDEPENDENT, tmp_path, transport=Recording(A.HttpResponse(200, documented, "r")))
    vectors = adapter.encode_queries([A.PreparedQuery("q0", "zero?"), A.PreparedQuery("q1", "one?")])
    assert np.allclose(vectors[0], A.decode(pplx_base64_int8(rows[0]), INDEPENDENT), atol=1e-6)
    assert np.allclose(vectors[1], A.decode(pplx_base64_int8(rows[1]), INDEPENDENT), atol=1e-6)


@pytest.mark.parametrize("arm", ["R4_grouped", "R4_singleton", "R4_independent"])
def test_the_three_perplexity_canaries_pass_against_the_documented_contract(tmp_path, verified_prices, arm):
    """The three canaries that failed live, against the documented contract
    (a schema violation would be the documented 422)."""

    from learnloop.experiments.contextual_embeddings.paid import make_adapter

    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    transport = FakeEmbeddingTransport(dims=DIMS)
    adapter = make_adapter(arm, snapshot, ledger=E0Ledger(tmp_path / "ledger"), transport=transport,
                           receipts=A.Receipts(tmp_path / "receipts.jsonl"), store=A.VectorStore(tmp_path / "v"),
                           qwen_client_factory=lambda: FakeQwenClient(), environ=FAKE_KEYS)
    assert adapter.canary()["status"] == "cached_first"
    receipts = _receipts(tmp_path)
    assert [row["method"] for row in receipts] == ["canary", "canary_query"]
    assert all(row["status"] == "ok" and row["http_status"] == 200 for row in receipts)
    assert all("input_type" not in request["body"] for request in transport.requests)


# -- 3. safe contract reasons on the receipt ----------------------------------------------


def test_a_422_records_its_status_and_allowlisted_codes_only(tmp_path, verified_prices):
    class OldBody(A.PerplexityContextualAdapter):
        """The first paid run's body (the fail-before reproduction)."""

        def _document_body(self, documents):
            return {**super()._document_body(documents), "input_type": "document", "encoding_format": "int8"}

    adapter = _adapter(CONTEXT, tmp_path, transport=FakeEmbeddingTransport(dims=DIMS), cls=OldBody)
    with pytest.raises(A.AdapterError) as raised:
        adapter.canary()
    assert raised.value.kind == "contract" and raised.value.http_status == 422
    [receipt] = _receipts(tmp_path)
    assert receipt["status"] == "failed" and receipt["error_kind"] == "contract" and receipt["http_status"] == 422
    assert receipt["contract_reason"] in ("HTTP 422: body.input_type:extra_forbidden, body.encoding_format:enum",
                                          "HTTP 422: body.encoding_format:enum, body.input_type:extra_forbidden")
    assert receipt["request_id"]


def test_error_bodies_never_reach_a_receipt():
    payload = {"detail": [
        {"loc": ["body", "input", 0, SECRET_TEXT], "msg": f"bad value {SECRET_TEXT}", "type": "enum"},
        {"loc": ["body", "model"], "msg": "x", "type": f"custom {SECRET_TEXT}"},
        {"loc": "not a list", "msg": SECRET_TEXT, "type": "missing"}],
        "error": {"message": SECRET_TEXT, "type": "invalid_request_error", "code": SECRET_TEXT}}
    codes = A.safe_error_codes(payload)
    assert codes == ("body.input.0.?:enum", "body.model:other", "?:missing", "error.type:invalid_request_error",
                     "error.code:other")
    assert SECRET_TEXT not in json.dumps(codes)
    assert A.safe_error_codes({"detail": SECRET_TEXT}) == () and A.safe_error_codes(SECRET_TEXT) == ()
    assert len(A.safe_error_codes({"detail": [{"loc": ["body"], "type": "missing"}] * 50})) == A.MAX_ERROR_CODES


def test_the_https_transport_reduces_an_error_body_to_codes(monkeypatch):
    body = json.dumps({"detail": [{"loc": ["body", "encoding_format"], "msg": SECRET_TEXT, "type": "enum"}]}).encode()

    class Opener:
        def open(self, request, timeout):
            raise urllib.error.HTTPError(request.full_url, 422, "Unprocessable", {"x-request-id": "rid-1"},
                                         io.BytesIO(body))

    transport = A.UrllibTransport()
    monkeypatch.setattr(transport, "opener", Opener())
    response = transport.post(PPLX_CONTEXTUAL_URL, headers={"Authorization": "Bearer x"}, body={}, timeout=1)
    assert response == A.HttpResponse(422, None, "rid-1", ("body.encoding_format:enum",))
    assert SECRET_TEXT not in repr(response)


@pytest.mark.parametrize("mutate,reason", [
    (lambda body: body.pop("data"), "missing field data"),
    (lambda body: body.update(data={"index": 0}), "unexpected type at data (object, expected array)"),
    (lambda body: body["data"][0]["data"][0].pop("embedding"), "missing field data[0].data[0].embedding"),
    (lambda body: body["data"][0]["data"][1].update(embedding=[1.5] * 4),
     "int8 output is not a list of integers: unexpected type at data[0].data[1].embedding (array)"),
    (lambda body: body["data"][0]["data"][1].update(embedding=pplx_base64_int8([1] * 1024)),
     "output has 1024 dimensions at data[0].data[1].embedding, pinned 2560"),
    (lambda body: body["data"][0].pop("index"), "missing field data[0].index"),
    (lambda body: body.update(model="pplx-embed-context-v1-0.6b"),
     "the provider answered with another model than the pinned one (at model)"),
])
def test_a_2xx_that_does_not_parse_records_a_safe_reason(tmp_path, verified_prices, mutate, reason):
    def respond(url, body):
        response = perplexity_documented(url, body, request_id="rid", vector=lambda _m, text, _c: _int8(len(text), 2560))
        payload = json.loads(json.dumps(response.body))
        payload["data"].sort(key=lambda row: row["index"])
        for row in payload["data"]:
            row["data"].sort(key=lambda item: item["index"])
        mutate(payload)
        return A.HttpResponse(200, payload, "rid")

    ledger = E0Ledger(tmp_path / "ledger")
    adapter = _adapter(CONTEXT, tmp_path, transport=Recording(respond), ledger=ledger)
    with pytest.raises(A.AdapterError) as raised:
        adapter.canary()
    assert raised.value.http_status == 200 and raised.value.reason == reason
    [receipt] = _receipts(tmp_path)
    assert receipt["status"] == "failed" and receipt["http_status"] == 200 and receipt["contract_reason"] == reason
    assert receipt["error_kind"] in ("contract", "validation")
    # The 2xx was billed: its entry is settled on the reported cost, not left failed.
    [entry] = json.loads((tmp_path / "ledger" / "e0_spend_ledger.json").read_text())["entries"].values()
    assert entry["status"] == "settled" and entry["actual_usd"] is not None


def test_a_canary_failure_reaches_the_contracts_result_with_its_reason(tmp_path, verified_prices):
    from learnloop.experiments.contextual_embeddings.paid import PaidState, run_contracts

    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    state = PaidState()
    run_contracts(snapshot, state, ledger=E0Ledger(tmp_path / "ledger"),
                  transport=FakeEmbeddingTransport(dims=DIMS, fail=lambda _count, body: 422
                                                   if "dimensions" in body else None),
                  receipts=A.Receipts(None), store=A.VectorStore(None), qwen_client_factory=FakeQwenClient,
                  environ=FAKE_KEYS)
    failed = state.contracts["R4_grouped"]
    assert failed == {"status": "failed", "kind": "contract", "http_status": 422, "reason": failed["reason"]}
    assert failed["reason"].endswith("HTTP 422") and state.contracts["R5_grouped"]["status"] == "cached_first"


# -- 4. resume: the same plan id and ledger ----------------------------------------------


def test_this_round_keeps_the_frozen_plans_pins_fingerprint():
    """No pin changed: the plan id of the stopped run (e0_a47534fecc49ded5) is unchanged
    for the same copies, so the rerun reopens its ledger (the fix is in adapter code only)."""

    artifact = json.loads(ARTIFACT.read_text())
    assert artifact["run_id"] == "e0_a47534fecc49ded5"
    assert pins.pins_fingerprint() == artifact["pins_fingerprint"]


def test_a_rerun_reopens_the_ledger_and_keeps_an_interrupted_reservation(tmp_path):
    copy = tmp_path / "fixtures-local" / "contextual-embeddings" / "vaults" / "v"
    copy.mkdir(parents=True)
    plan = "e0_a47534fecc49ded5"
    ledger = authorized_ledger([copy], plan, new_authorization="owner raised cap to $40 on 2026-10-22")
    settled = ledger.reserve(Request(category="embeddings", provider="voyage", route="m", purpose="embed:canary",
                                     arm="R5", billing="metered", estimated_usd=0.001, estimated_tokens=10))
    ledger.settle(settled, actual_usd=0.0004)
    # A stop mid-request: reserved, never settled (the backfill batch of the first run).
    ledger.reserve(Request(category="embeddings", provider="openrouter_embedding", route="qwen",
                           purpose="system:embedding", arm="R1_service_backfill", billing="metered",
                           estimated_usd=0.000073, estimated_tokens=7300))
    # The rerun: the same plan id reopens the same file, with or without --new-authorization.
    again = authorized_ledger([copy], plan)
    report = again.report()
    assert again.path == ledger.path and report["authorization"] == {"plan_id": plan}
    assert report["committed_usd"] == pytest.approx(0.0004 + 0.000073)
    assert report["outstanding_reservations_usd"] == pytest.approx(0.000073)
    assert authorized_ledger([copy], plan, new_authorization="ignored").report()["committed_usd"] == pytest.approx(
        0.000473)
    reason = json.loads(ledger.path.read_text())["authorization"]["reason"]
    assert reason == "owner raised cap to $40 on 2026-10-22"
    # Another plan id is refused without --new-authorization: never a silent fresh $40.
    with pytest.raises(PermissionError, match="new-authorization"):
        authorized_ledger([copy], "e0_0000000000000000")
