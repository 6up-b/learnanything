---
title: "learnloop.experiments.contextual_embeddings.adapters"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/adapters.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/adapters.py"
source_commit: "1bb7b87bd93fde8192f97c71bc8edfc7b5fb4bb4"
source_commit_timestamp: "2026-10-23T15:40:42-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.experiments.contextual_embeddings"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.experiments.contextual_embeddings.adapters module"
  - "src/learnloop/experiments/contextual_embeddings/adapters.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.adapters`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.adapters` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: Isolated embedding adapters for E0 (spec §4.3): Qwen, Perplexity, Voyage.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/adapters.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py) |
| Source lines | 1151 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1bb7b87bd93fde8192f97c71bc8edfc7b5fb4bb4` |
| Commit timestamp | `2026-10-23T15:40:42-04:00` |

## Public API

- `class AdapterError(RuntimeError)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 78) — An adapter failure; ``kind`` is transient, auth, contract, limit or validation.
  - `__init__(self, message: str, *, kind: str, http_status: int | None=None) -> None` (line 86; internal)
- `class WrongMethod(AdapterError)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 93)
  - `__init__(self, message: str) -> None` (line 94; internal)
- `class MixedSpace(AdapterError)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 98)
  - `__init__(self, message: str) -> None` (line 99; internal)
- `class CanaryDrift(AdapterError)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 103)
  - `__init__(self, message: str) -> None` (line 104; internal)
- `class Chunk` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 109)
- `class Document` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 115)
- `class PreparedQuery` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 123)
- `class HttpResponse` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 129)
- `safe_error_codes(payload: Any) -> tuple[str, ...]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 163) — A provider error body reduced to allowlisted codes, e.g.
- `class Transport(Protocol)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 209)
  - `post(self, url: str, *, headers: Mapping[str, str], body: Mapping[str, Any], timeout: float) -> HttpResponse` (line 210; public)
- `class NoRedirect(urllib.request.HTTPRedirectHandler)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 214) — Never follow a redirect: a 3xx would replay the request's key header (``x-api-key`` or ``Authorization``) to another host (pre-paid verify L1).
  - `redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None` (line 219; public)
- `class UrllibTransport` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 227) — The real HTTPS transport.
  - `post(self, url: str, *, headers: Mapping[str, str], body: Mapping[str, Any], timeout: float) -> HttpResponse` (line 236; public)
- `document_space_id(pin: EmbeddingPin, *, encoding: str, recipe: str, extraction_revisions: Sequence[str], epoch: int=0, serving_provider: str | None=None) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 256) — The spec's ``document_space_id`` (§4.3).
- `query_encoder_id(pin: EmbeddingPin, *, epoch: int=0, serving_provider: str | None=None) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 269) — The spec's ``query_encoder_id`` (§4.3); ``serving_provider``: the validated client identity's digest where one exists (Qwen, fix round 4).
- `qwen_identity(client: Any, pin: EmbeddingPin) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 281) — The Qwen client's resolved identity, checked against its pin BEFORE its first request (fix round 4, High 4): the transport (the production OpenRouter embedding client), the model, the endpoint, the dimensions and the billing class.
- `decode(values: Any, pin: EmbeddingPin, *, where: str='embedding') -> np.ndarray` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 334) — A raw output row as the FP32 scoring copy (validated, L2-normalized).
- `class Receipts` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 372) — Append-only JSON lines (one per physical attempt), private to the run.
  - `__init__(self, path: Path | None) -> None` (line 379; internal)
  - `write(self, **row: Any) -> None` (line 383; public)
- `query_vector_key(encoder_id: str, query_text: str) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 393) — The spec's ``query_vector_key``: the encoder and the complete effective query.
- `class StoreCorrupt(AdapterError)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 399)
  - `__init__(self, message: str) -> None` (line 400; internal)
- `class VectorStore` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 404) — Research vectors keyed by vector key, one JSON-lines file per space (outside production ``embedding_vectors``).
  - `__init__(self, directory: Path | None) -> None` (line 420; internal)
  - `_path(self, space: str) -> Path | None` (line 427; internal)
  - `_checksum(key: str, vectors: Any, raw: Any) -> str` (line 431; internal)
  - `_parse(self, space: str, data: bytes) -> tuple[dict[str, dict[str, Any]], int]` (line 434; internal) — The records and the byte offset after the last complete line.
  - `_load(self, space: str) -> dict[str, dict[str, Any]]` (line 456; internal)
  - `get(self, space: str, key: str) -> list[list[float]] | None` (line 468; public)
  - `get_raw(self, space: str, key: str) -> Any` (line 472; public)
  - `put(self, space: str, key: str, vectors: Sequence[Sequence[float]], *, raw: Any=None) -> None` (line 476; public)
  - `count(self, space: str) -> int` (line 506; public)
- `class EmbeddingAdapter` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 510) — Shared batching, admission, retries, validation and receipts.
  - `__init__(self, pin: EmbeddingPin, *, encoding: str, recipe: str, ledger: E0Ledger, arm: str, extraction_revisions: Sequence[str]=(), transport: Transport | None=None, receipts: Receipts | None=None, store: VectorStore | None=None, epoch: int=0, key_env: str | None=None, environ: Mapping[str, str] | None=None, sleep: Callable[[float], None]=time.sleep) -> None` (line 513; internal)
  - `_document_body(self, documents: Sequence[Document]) -> dict[str, Any]` (line 541; internal)
  - `_query_body(self, queries: Sequence[PreparedQuery]) -> dict[str, Any]` (line 544; internal)
  - `_document_rows(self, body: Any, documents: Sequence[Document]) -> list[list[Any]]` (line 547; internal)
  - `_query_rows(self, body: Any, count: int) -> list[Any]` (line 550; internal)
  - `_headers(self) -> dict[str, str]` (line 553; internal)
  - `_estimate(self, texts: Sequence[str]) -> tuple[int, float]` (line 560; internal)
  - `_require_price(self) -> None` (line 564; internal) — No request is admitted on an unverified price (fix round 4, High 2).
  - `_billed(cost: Any) -> float | None` (line 572; internal) — The provider's explicit cost: a number, or Perplexity's documented ``usage.cost`` object (``{"input_cost", "total_cost", "currency": "USD"}``, docs.perplexity.ai/api-reference/embeddings-post), whose ``total_cost`` in USD is the bill.
  - `_send(self, url: str, body: Mapping[str, Any], *, method: str, texts: Sequence[str], items: int, parse: Callable[[Any], Any] | None=None) -> Any` (line 584; internal) — One admitted request (and its transient retries); returns ``parse(response_body)`` (the body when ``parse`` is None).
  - `_failure_reason(response: HttpResponse | None, error: AdapterError | None) -> str` (line 657; internal) — A failed attempt's safe reason: ``HTTP 422: body.encoding_format:enum`` (allowlisted codes only), or the transport's own safe message.
  - `_kind(response: HttpResponse | None) -> str` (line 669; internal)
  - `_check_document(self, document: Document) -> None` (line 681; internal)
  - `_batches(self, documents: Sequence[Document]) -> list[list[Document]]` (line 692; internal)
  - `encode_documents(self, documents: Sequence[Document]) -> list[list[Vector]]` (line 714; public)
  - `query_space(self) -> str` (line 740; public)
  - `encode_queries(self, queries: Sequence[PreparedQuery], *, fresh: bool=False) -> list[Vector]` (line 743; public) — Query vectors, each cached under its ``query_vector_key`` (the encoder and the complete query text): a resumed run re-sends none it already paid for (Codex review F18).
  - `_canary_document(self) -> Document` (line 775; internal)
  - `_canary_vectors(self) -> tuple[list[Vector], Vector]` (line 779; internal) — The canary document's vectors and the canary query's vector, each through its own method (document and query contracts).
  - `_parse_documents(self, body: Any, documents: Sequence[Document], *, check_model: bool=False) -> list[tuple[list[Any], list[Vector]]]` (line 793; internal) — Each document's raw rows and decoded vectors (inside ``_send``, so a parse failure is on the attempt's receipt).
  - `_parse_queries(self, body: Any, count: int, *, check_model: bool=False) -> list[tuple[Any, Vector]]` (line 807; internal)
  - `_row_path(self, document: int, chunk: int) -> str` (line 813; internal) — A row's field path in the response (sorted by index).
  - `_check_returned_model(self, body: Any) -> None` (line 818; internal) — A response that names its model must name the pinned one.
  - `canary(self) -> dict[str, Any]` (line 826; public) — The route's public contract check, before ANY bulk work (fix round 4, Medium 9): the canary document through the document method AND the canary query through the query method; both must decode at the pinned dimensions, the query must score against the documents in the same paire…
- `class PerplexityContextualAdapter(_GroupedAdapter)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 934) — ``pplx-embed-context-v1-4b``: grouped windows and the singleton control.
  - `_document_body(self, documents: Sequence[Document]) -> dict[str, Any]` (line 947; internal)
  - `_query_body(self, queries: Sequence[PreparedQuery]) -> dict[str, Any]` (line 951; internal)
- `class PerplexityIndependentAdapter(_IndependentAdapter)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 956) — ``pplx-embed-v1-4b``: the independent family baseline.
  - `_document_body(self, documents: Sequence[Document]) -> dict[str, Any]` (line 966; internal)
  - `_query_body(self, queries: Sequence[PreparedQuery]) -> dict[str, Any]` (line 970; internal)
- `class VoyageContextualAdapter(_GroupedAdapter)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 975) — ``voyage-context-4``: grouped windows and the singleton control.
  - `_document_body(self, documents: Sequence[Document]) -> dict[str, Any]` (line 978; internal)
  - `_query_body(self, queries: Sequence[PreparedQuery]) -> dict[str, Any]` (line 982; internal)
- `class VoyageIndependentAdapter(_IndependentAdapter)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 987) — ``voyage-4-large`` through the Voyage API (never truncated).
  - `_document_body(self, documents: Sequence[Document]) -> dict[str, Any]` (line 990; internal)
  - `_query_body(self, queries: Sequence[PreparedQuery]) -> dict[str, Any]` (line 995; internal)
- `class QwenAdapter(EmbeddingAdapter)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 1000) — Qwen through the production OpenRouter client (``data_collection=deny``), one admitted request per batch; the production prefixes for each method.
  - `__init__(self, pin: EmbeddingPin, *, client_factory: Callable[[], Any], **kwargs: Any) -> None` (line 1004; internal)
  - `_client_now(self) -> Any` (line 1021; internal)
  - `_canary_vectors(self) -> tuple[list[Vector], Vector]` (line 1024; internal)
  - `_embed(self, texts: list[str], task: str, method: str) -> list[list[float]]` (line 1030; internal)
  - `encode_documents(self, documents: Sequence[Document]) -> list[list[Vector]]` (line 1070; public)
  - `encode_queries(self, queries: Sequence[PreparedQuery], *, fresh: bool=False) -> list[Vector]` (line 1091; public) — Cached per ``query_vector_key`` like every adapter (Codex review F18); ``fresh`` sends every query anew.
- `class SpaceVectors` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 1123) — An index's vectors, all from one document space.
- `assert_compatible(index: SpaceVectors, query_encoder: str) -> None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 1132) — Refuse a query vector from another encoder (equal widths prove nothing).
- `build_index(entries: Sequence[tuple[str, str, str, Sequence[float]]]) -> SpaceVectors` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 1139) — ``entries``: (id, document_space_id, paired query encoder, vector).

### Module constants

- `CANARY_CHUNKS` ([src/learnloop/experiments/contextual_embeddings/adapters.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 71)
- `CANARY_TOLERANCE` ([src/learnloop/experiments/contextual_embeddings/adapters.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 73)
- `CANARY_QUERY` ([src/learnloop/experiments/contextual_embeddings/adapters.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 75)
- `SAFE_ERROR_FIELDS` ([src/learnloop/experiments/contextual_embeddings/adapters.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 140)
- `SAFE_ERROR_TYPES` ([src/learnloop/experiments/contextual_embeddings/adapters.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 147)
- `MAX_ERROR_CODES` ([src/learnloop/experiments/contextual_embeddings/adapters.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 159)
- `MAX_ERROR_BODY_BYTES` ([src/learnloop/experiments/contextual_embeddings/adapters.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 160)
- `OPENER` ([src/learnloop/experiments/contextual_embeddings/adapters.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 224)
- `PERPLEXITY_ENCODING` ([src/learnloop/experiments/contextual_embeddings/adapters.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 931)
- `ADAPTERS` ([src/learnloop/experiments/contextual_embeddings/adapters.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 1114)

## Internal implementation anchors

- `_error_codes(exc: urllib.error.HTTPError) -> tuple[str, ...]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 199) — The allowlisted codes of an HTTP error body, read bounded and dropped.
- `_hash(payload: Any) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 252)
- `_type_name(value: Any) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 316) — A JSON type name (safe to record: never the value).
- `_ordered(rows: Any, count: int, where: str) -> list[Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 855) — Rows matched to inputs by their ``index``, never by position.
- `_embedding(row: Mapping[str, Any], where: str) -> Any` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 885)
- `_json_object(body: Any) -> Mapping[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 891)
- `class _GroupedAdapter(EmbeddingAdapter)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 898) — Contextualized endpoints: nested documents, nested ordered responses.
- `class _IndependentAdapter(EmbeddingAdapter)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py), line 918)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/anthropic_api|learnloop.experiments.contextual_embeddings.anthropic_api]] — imports `UrllibTransport`; statically calls `UrllibTransport`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/local|learnloop.experiments.contextual_embeddings.e1.local]] — imports `AdapterError`, `Document`, `VectorStore`, `build_index`, `decode`, `document_space_id`, `query_encoder_id`, `query_vector_key`; statically calls `build_index`, `decode`, `document_space_id`, `query_encoder_id`, `query_vector_key`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] — imports `AdapterError`, `Receipts`, `VectorStore`; statically calls `Receipts`, `VectorStore`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `AdapterError`, `Receipts`, `UrllibTransport`, `VectorStore`; statically calls `Receipts`, `UrllibTransport`, `VectorStore`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]] — imports `Receipts`, `UrllibTransport`, `VectorStore`; statically calls `Receipts`, `UrllibTransport`, `VectorStore`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]] — imports `ADAPTERS`, `AdapterError`, `EmbeddingAdapter`, `PreparedQuery`, `QwenAdapter`, `Receipts`, `SpaceVectors`, `Transport`, `VectorStore`, `build_index`; statically calls `AdapterError`, `PreparedQuery`, `QwenAdapter`, `Receipts`, `VectorStore`, `build_index`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/plan|learnloop.experiments.contextual_embeddings.plan]] — imports `Chunk`, `Document`; statically calls `Chunk`, `Document`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/retrieval|learnloop.experiments.contextual_embeddings.retrieval]] — imports `Chunk`, `Document`, `SpaceVectors`, `assert_compatible`, `query_vector_key`; statically calls `Chunk`, `Document`, `assert_compatible`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `is_subscription_transport`; calls `is_subscription_transport`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/budget|learnloop.experiments.contextual_embeddings.budget]] — imports `E0BudgetExceeded`, `E0Ledger`, `E0PriceUnverified`, `Request`, `explicit_cost`, `known_tokens`, `reconciled_usd`; calls `E0PriceUnverified`, `Request`, `explicit_cost`, `known_tokens`, `reconciled_usd`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/credentials|learnloop.experiments.contextual_embeddings.credentials]] — imports `module`; calls `read_key`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `EmbeddingPin`, `module`, `token_upper_bound`; calls `price_problem`, `token_upper_bound`

### Platform and third-party dependencies

- Standard library: `__future__`, `base64`, `collections`, `dataclasses`, `fcntl`, `hashlib`, `json`, `math`, `os`, `pathlib`, `threading`, `time`, `typing`, `urllib`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/anthropic_api|learnloop.experiments.contextual_embeddings.anthropic_api]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/local|learnloop.experiments.contextual_embeddings.e1.local]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/e0_fakes.py](../../../../../../../tests/e0_fakes.py) — direct import
- [tests/test_e0_adapters.py](../../../../../../../tests/test_e0_adapters.py) — direct import
  - `test_a_refused_admission_sends_nothing`
  - `test_an_absent_key_fails_before_admission_or_request`
  - `test_canary_caches_first_output_and_flags_drift`
  - `test_exact_search_ties_break_by_id`
  - `test_grouped_responses_are_matched_by_index_not_position`
  - `test_missing_or_duplicate_indices_are_contract_errors`
  - `test_mixed_spaces_and_foreign_query_encoders_are_refused`
  - `test_nonfinite_vectors_are_refused`
  - `test_oversize_input_is_refused_never_truncated`
  - `test_query_and_document_methods_are_separate`
  - `test_qwen_adapter_uses_production_prefixes_and_admits_each_batch`
  - `test_receipts_and_ledger_never_hold_keys`
  - `test_resume_is_idempotent_by_vector_key`
  - `test_transient_failures_retry_twice_each_attempt_admitted_auth_never`
  - `test_wrong_methods_are_refused_before_any_request`
  - `test_zero_wrong_width_and_out_of_range_vectors_are_refused`
- [tests/test_e0_paid_fakes.py](../../../../../../../tests/test_e0_paid_fakes.py) — direct import
  - `test_resume_pays_only_for_what_is_missing`
- [tests/test_e0_relabel_round.py](../../../../../../../tests/test_e0_relabel_round.py) — direct import
  - `test_the_earlier_ledgers_admissions_stay_visible_so_a_known_truncation_is_not_resent`
- [tests/test_e0_review_round1.py](../../../../../../../tests/test_e0_review_round1.py) — direct import
  - `test_f15_provider_limits_use_a_guaranteed_upper_bound`
  - `test_f18_a_torn_vector_append_is_recovered_and_raw_output_is_kept`
  - `test_f18_concurrent_writers_never_duplicate_a_key`
  - `test_f18_query_vectors_are_cached_and_not_repaid`
  - `test_f2_a_metered_request_is_sent_and_reserved_at_the_output_budget_policy`
- [tests/test_e0_review_round3.py](../../../../../../../tests/test_e0_review_round3.py) — direct import
  - `test_f21_a_hosted_embedding_without_positive_usage_keeps_its_reservation`
- [tests/test_e0_review_round4.py](../../../../../../../tests/test_e0_review_round4.py) — direct import
  - `test_h2_an_overcharged_hosted_response_stops_the_paid_run_at_once`
  - `test_h2_an_unverified_price_refuses_every_metered_request_before_sending`
  - `test_h4_a_qwen_client_that_is_not_its_pin_is_refused_before_its_first_request`
  - `test_h4_the_qwen_identity_is_in_cache_keys_and_receipts_and_the_service_gate`
  - `test_m9_a_broken_query_method_fails_the_canary_before_any_bulk_work`
  - `test_m9_the_qwen_route_is_canaried_before_its_service_backfill`
- [tests/test_e0_review_round4_followup.py](../../../../../../../tests/test_e0_review_round4_followup.py) — direct import
  - `test_the_label_passes_never_reach_a_codex_turn`
  - `test_voyage_is_admitted_at_the_full_price_never_the_free_tier`
- [tests/test_e0_review_round5.py](../../../../../../../tests/test_e0_review_round5.py) — direct import
- [tests/test_e0_review_round6.py](../../../../../../../tests/test_e0_review_round6.py) — direct import
  - `test_l1_a_redirect_is_a_contract_failure_that_is_never_retried`
  - `test_l1_the_transport_never_follows_a_redirect`
- [tests/test_e0_review_round7.py](../../../../../../../tests/test_e0_review_round7.py) — direct import
  - `test_a_2xx_that_does_not_parse_records_a_safe_reason`
  - `test_a_422_records_its_status_and_allowlisted_codes_only`
  - `test_a_canary_failure_reaches_the_contracts_result_with_its_reason`
  - `test_a_documented_contextual_response_decodes_by_index`
  - `test_a_documented_independent_response_decodes_by_index`
  - `test_error_bodies_never_reach_a_receipt`
  - `test_the_contextual_bodies_are_the_documented_shape`
  - `test_the_https_transport_reduces_an_error_body_to_codes`
  - `test_the_independent_bodies_are_the_documented_shape`
  - `test_the_three_perplexity_canaries_pass_against_the_documented_contract`
- [tests/test_e0_review_round8.py](../../../../../../../tests/test_e0_review_round8.py) — direct import
- [tests/test_e1_harness.py](../../../../../../../tests/test_e1_harness.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains adapters within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/adapters.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/adapters.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
