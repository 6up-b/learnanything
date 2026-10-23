"""Isolated embedding adapters for E0 (spec §4.3): Qwen, Perplexity, Voyage.

The contract every adapter keeps:

* ``encode_documents(list[Document]) -> list[list[Vector]]``: one vector per
  chunk, in each document's chunk order, whatever order the provider returns
  (rows are matched by their ``index`` fields, never by position).
  ``encode_queries(list[PreparedQuery]) -> list[Vector]``: the documented query
  method only; a document method is never used for a query nor the reverse
  (``WrongMethod``).
* Validation of every response: count and order, dimensions against the pin,
  finite values, nonzero norm, integer range for int8 output. No silent
  truncation: an input over the pin's per-document or per-request bound is
  refused before sending, and the Voyage independent endpoint is sent
  ``truncation: false``.
* Spaces: ``document_space_id`` and ``query_encoder_id`` follow the spec's
  identity formula. ``assert_compatible`` refuses a query vector from another
  encoder and an index mixing spaces (``MixedSpace``); equal dimensions never
  imply compatibility.
* Admission: each physical request (each retry too) is admitted by the E0
  ledger BEFORE it is sent; two retries for transient failures only, none for
  authentication or contract errors.
* Receipts: one JSON line per attempt (endpoint, model, input hash, counts,
  usage, billed or estimated amount, latency, status, the provider's request
  id); never headers, keys or provider error bodies.
* Resume: a document or query whose vector key is already stored is not re-sent
  (raw provider rows are kept beside the decoded vectors; the store survives a
  torn append); the
  first successful canary output is cached and later canaries are compared
  within a tolerance (``CanaryDrift`` opens a new epoch).

The Perplexity request and response shapes follow the published API
reference (read 2026-10-23; the Perplexity canary round in
docs/reviews/experiments-e0-harness-codex-review.md). Every contract is still
validated by the canary before any bulk work of a paid run. A failed attempt's
receipt carries ``http_status`` and a safe ``contract_reason``.
"""
from __future__ import annotations

import base64
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import threading
import time
from typing import Any, Protocol
import urllib.error
import urllib.request

import numpy as np

from learnloop.experiments.contextual_embeddings import credentials, pins
from learnloop.experiments.contextual_embeddings.budget import (
    E0BudgetExceeded,
    E0Ledger,
    E0PriceUnverified,
    Request,
    explicit_cost,
    known_tokens,
    reconciled_usd,
)
from learnloop.experiments.contextual_embeddings.pins import EmbeddingPin, token_upper_bound

Vector = list[float]
#: A fixed, public canary (no private text): re-encoded on resume to detect drift.
CANARY_CHUNKS = ("Definition. A vector space is a set with addition and scalar multiplication.",
                 "Example. The real numbers form a vector space over themselves.")
CANARY_TOLERANCE = 0.995
#: The public canary query (the query contract is checked before any bulk work).
CANARY_QUERY = "What is a vector space?"


class AdapterError(RuntimeError):
    """An adapter failure; ``kind`` is transient, auth, contract, limit or validation.

    ``reason`` is SAFE to record (Perplexity canary round): the message is
    built here from constants, field paths and counts, never from a response
    body, a key or the request's text. ``http_status`` is the provider's
    status when one came back."""

    def __init__(self, message: str, *, kind: str, http_status: int | None = None) -> None:
        super().__init__(message)
        self.kind = kind
        self.reason = message
        self.http_status = http_status


class WrongMethod(AdapterError):
    def __init__(self, message: str) -> None:
        super().__init__(message, kind="contract")


class MixedSpace(AdapterError):
    def __init__(self, message: str) -> None:
        super().__init__(message, kind="contract")


class CanaryDrift(AdapterError):
    def __init__(self, message: str) -> None:
        super().__init__(message, kind="contract")


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    text: str


@dataclass(frozen=True)
class Document:
    document_id: str
    chunks: tuple[Chunk, ...]
    #: The document's vector key (resume identity), from the caller.
    key: str = ""


@dataclass(frozen=True)
class PreparedQuery:
    query_id: str
    text: str


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: Any
    request_id: str | None = None
    #: A non-2xx response's allowlisted error codes (``safe_error_codes``);
    #: the error body itself is never kept.
    error_codes: tuple[str, ...] = ()


#: Field names an error location may name in a receipt; any other part of a
#: location becomes ``?`` (a location can name a user-chosen key).
SAFE_ERROR_FIELDS = frozenset({
    "body", "query", "header", "path", "input", "inputs", "model", "dimensions", "encoding_format", "input_type",
    "output_dimension", "output_dtype", "truncation", "data", "embedding", "index", "authorization",
})
#: Validation error types a receipt may name (FastAPI/Pydantic's fixed
#: vocabulary, as Perplexity's documented 422 ``HTTPValidationError`` carries
#: them); any other value becomes ``other``.
SAFE_ERROR_TYPES = frozenset({
    "missing", "extra_forbidden", "enum", "literal_error", "string_type", "int_type", "int_parsing", "int_from_float",
    "float_type", "float_parsing", "bool_type", "list_type", "dict_type", "model_type", "model_attributes_type",
    "too_short", "too_long", "string_too_short", "string_too_long", "greater_than", "greater_than_equal",
    "less_than", "less_than_equal", "value_error", "assertion_error", "json_invalid", "json_type", "union_tag_invalid",
    "type_error", "value_error.missing", "value_error.extra", "type_error.enum",
    # The OpenAI-style ``error.type`` / ``error.code`` envelope.
    "invalid_request_error", "authentication_error", "permission_error", "rate_limit_error", "not_found_error",
    "server_error", "api_error", "overloaded_error", "insufficient_quota", "invalid_api_key", "invalid_model",
    "model_not_found", "context_length_exceeded", "bad_request",
})
#: At most this many codes and this many error-body bytes are read.
MAX_ERROR_CODES = 8
MAX_ERROR_BODY_BYTES = 65_536


def safe_error_codes(payload: Any) -> tuple[str, ...]:
    """A provider error body reduced to allowlisted codes, e.g.
    ``body.encoding_format:enum``; messages (``msg``, ``message``, a string
    ``detail``) are never read, so no request text or key can reach a receipt.

    Perplexity documents one error shape for both embedding endpoints: 422
    ``HTTPValidationError`` = ``{"detail": [{"loc": [...], "msg": ..., "type": ...}]}``
    (docs.perplexity.ai/api-reference/embeddings-post and
    .../contextualized-embeddings-post). The OpenAI-style ``{"error": {"type",
    "code"}}`` envelope is reduced the same way."""

    def kind(value: Any) -> str:
        return value if isinstance(value, str) and value in SAFE_ERROR_TYPES else "other"

    def place(part: Any) -> str:
        if isinstance(part, int) and not isinstance(part, bool) and 0 <= part < 1_000_000:
            return str(part)
        return part if isinstance(part, str) and part in SAFE_ERROR_FIELDS else "?"

    codes: list[str] = []
    if isinstance(payload, Mapping):
        detail = payload.get("detail")
        if isinstance(detail, list):
            for item in detail[:MAX_ERROR_CODES]:
                if isinstance(item, Mapping):
                    loc = item.get("loc")
                    where = ".".join(place(part) for part in loc[:8]) if isinstance(loc, list) else "?"
                    codes.append(f"{where}:{kind(item.get('type'))}")
        error = payload.get("error")
        if isinstance(error, Mapping):
            for field in ("type", "code"):
                if error.get(field) is not None:
                    codes.append(f"error.{field}:{kind(error.get(field))}")
    return tuple(codes[:MAX_ERROR_CODES])


def _error_codes(exc: urllib.error.HTTPError) -> tuple[str, ...]:
    """The allowlisted codes of an HTTP error body, read bounded and dropped."""

    try:
        raw = exc.read(MAX_ERROR_BODY_BYTES)
        return safe_error_codes(json.loads(raw.decode("utf-8")))
    except Exception:  # noqa: BLE001 - an unreadable error body has no codes
        return ()


class Transport(Protocol):
    def post(self, url: str, *, headers: Mapping[str, str], body: Mapping[str, Any],
             timeout: float) -> HttpResponse: ...


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never follow a redirect: a 3xx would replay the request's key header
    (``x-api-key`` or ``Authorization``) to another host (pre-paid verify L1).
    Returning None makes urllib raise the 3xx as an ``HTTPError``."""

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


#: The opener every E0 HTTPS request uses: urllib's defaults with redirects refused.
OPENER = urllib.request.build_opener(NoRedirect)


class UrllibTransport:
    """The real HTTPS transport. Errors carry the status and the body's
    allowlisted codes only (``safe_error_codes``), never the body (provider
    error bodies can echo request text). Redirects are never
    followed: a 3xx comes back as its status, a contract failure that is not
    retried (``EmbeddingAdapter._kind``, ``anthropic_api._classify``)."""

    opener = OPENER

    def post(self, url: str, *, headers: Mapping[str, str], body: Mapping[str, Any],
             timeout: float) -> HttpResponse:
        data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(url, data=data, method="POST", headers=dict(headers))
        try:
            with self.opener.open(request, timeout=timeout) as response:  # noqa: S310 (fixed https pins)
                payload = json.loads(response.read().decode("utf-8"))
                request_id = response.headers.get("x-request-id") or response.headers.get("request-id")
                return HttpResponse(int(response.status), payload, request_id)
        except urllib.error.HTTPError as exc:
            return HttpResponse(int(exc.code), None, exc.headers.get("x-request-id") if exc.headers else None,
                                _error_codes(exc))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise AdapterError(f"network failure ({type(exc).__name__})", kind="transient") from None


def _hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()


def document_space_id(pin: EmbeddingPin, *, encoding: str, recipe: str, extraction_revisions: Sequence[str],
                      epoch: int = 0, serving_provider: str | None = None) -> str:
    """The spec's ``document_space_id`` (§4.3)."""

    return "ds_" + _hash({
        "endpoint": pin.document_endpoint, "model": pin.model, "alias_epoch": epoch,
        "serving_provider": serving_provider or "unknown", "precision": pin.output_format,
        "tokenizer": "unknown", "extraction": sorted(extraction_revisions), "recipe": recipe,
        "dimensions": pin.dimensions, "output_format": pin.output_format,
        "decode_and_score": pin.decode_transform, "encoding": encoding,
    })[:24]


def query_encoder_id(pin: EmbeddingPin, *, epoch: int = 0, serving_provider: str | None = None) -> str:
    """The spec's ``query_encoder_id`` (§4.3); ``serving_provider``: the
    validated client identity's digest where one exists (Qwen, fix round 4)."""

    payload = {"model": pin.model, "alias_epoch": epoch, "query_mode": pin.query_method,
               "precision": pin.output_format, "projection": None, "dimensions": pin.dimensions,
               "output_transform": pin.decode_transform}
    if serving_provider is not None:
        payload["serving_provider"] = serving_provider
    return "qe_" + _hash(payload)[:24]


def qwen_identity(client: Any, pin: EmbeddingPin) -> dict[str, Any]:
    """The Qwen client's resolved identity, checked against its pin BEFORE
    its first request (fix round 4, High 4): the transport (the production
    OpenRouter embedding client), the model, the endpoint, the dimensions and
    the billing class. Any difference is a contract failure: nothing is sent,
    and another model's vectors can never be cached or reported as Qwen."""

    from learnloop.ai.spend import is_subscription_transport

    profile = getattr(client, "profile", None)
    base = getattr(profile, "base_url", None) or getattr(client, "default_base_url", None)
    identity = {
        "provider_type": getattr(client, "provider_type", None),
        "model": getattr(client, "model_id", None) or getattr(client, "model", None),
        "endpoint": None if not base else str(base).rstrip("/") + "/embeddings",
        "dimensions": getattr(client, "dims", None),
        "billing": "subscription" if is_subscription_transport(client=client) else "metered",
    }
    problems = []
    if identity["provider_type"] != "openai_embedding":
        problems.append("transport")
    if identity["model"] != pin.model:
        problems.append("model")
    if identity["endpoint"] != pin.document_endpoint:
        problems.append("endpoint")
    if identity["dimensions"] != pin.dimensions:
        problems.append("dimensions")
    if identity["billing"] != "metered":
        problems.append("billing")
    if problems:
        raise AdapterError("the Qwen client does not match its pin (" + ", ".join(problems) + "); nothing was sent",
                           kind="contract")
    return identity


def _type_name(value: Any) -> str:
    """A JSON type name (safe to record: never the value)."""

    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, Mapping):
        return "object"
    return "other"


def decode(values: Any, pin: EmbeddingPin, *, where: str = "embedding") -> np.ndarray:
    """A raw output row as the FP32 scoring copy (validated, L2-normalized).

    Int8 pins accept Perplexity's documented ``base64_int8`` string (the
    signed int8 bytes, base64-encoded; length = ``dimensions``) or a list of
    integers. ``where`` is the row's field path, for a safe reason."""

    if pin.output_format == "int8":
        if isinstance(values, str):
            try:
                raw = np.frombuffer(base64.b64decode(values, validate=True), dtype=np.int8).astype(np.float32)
            except (ValueError, TypeError):
                raise AdapterError(f"int8 output is not valid base64 at {where}", kind="validation") from None
        else:
            if not isinstance(values, list) or not all(isinstance(value, int) and not isinstance(value, bool)
                                                       for value in values):
                raise AdapterError(f"int8 output is not a list of integers: unexpected type at {where} "
                                   f"({_type_name(values)})", kind="validation")
            if any(value < -128 or value > 127 for value in values):
                raise AdapterError(f"int8 output is out of range at {where}", kind="validation")
            raw = np.asarray(values, dtype=np.float32)
    else:
        if not isinstance(values, list) or not all(isinstance(value, (int, float)) and not isinstance(value, bool)
                                                   for value in values):
            raise AdapterError(f"float output is not a list of numbers: unexpected type at {where} "
                               f"({_type_name(values)})", kind="validation")
        raw = np.asarray(values, dtype=np.float64)
    if raw.shape != (pin.dimensions,):
        raise AdapterError(f"output has {raw.shape[0] if raw.ndim else 0} dimensions at {where}, "
                           f"pinned {pin.dimensions}", kind="contract")
    if not np.all(np.isfinite(raw)):
        raise AdapterError(f"output contains non-finite values at {where}", kind="validation")
    norm = float(np.linalg.norm(raw))
    if not norm or not math.isfinite(norm):
        raise AdapterError(f"output is a zero vector at {where}", kind="validation")
    return (raw / norm).astype(np.float32)


class Receipts:
    """Append-only JSON lines (one per physical attempt), private to the run."""

    FIELDS = ("at", "arm", "adapter", "endpoint", "model", "method", "input_hash", "items", "estimated_tokens",
              "usage", "billed_usd", "estimated_usd", "status", "attempt", "latency_s", "request_id",
              "error_kind", "resumed", "identity", "http_status", "contract_reason")

    def __init__(self, path: Path | None) -> None:
        self.path = Path(path) if path is not None else None
        self.rows: list[dict[str, Any]] = []

    def write(self, **row: Any) -> None:
        clean = {key: row.get(key) for key in self.FIELDS}
        clean["at"] = clean["at"] or time.time()
        self.rows.append(clean)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(clean, sort_keys=True, default=str) + "\n")


def query_vector_key(encoder_id: str, query_text: str) -> str:
    """The spec's ``query_vector_key``: the encoder and the complete effective query."""

    return "qv_" + _hash([encoder_id, query_text])[:32]


class StoreCorrupt(AdapterError):
    def __init__(self, message: str) -> None:
        super().__init__(message, kind="validation")


class VectorStore:
    """Research vectors keyed by vector key, one JSON-lines file per space
    (outside production ``embedding_vectors``). Idempotent: a key is written
    once; ``get`` returns the first successful output.

    **Durable (Codex review F18).** Each line is one complete record: the
    key, the decoded scoring vectors, the provider's RAW output rows (so the
    decoding can be reproduced from what was paid for) and a checksum. An
    append runs under an exclusive ``fcntl`` lock on the space's lock file
    (other processes and threads wait), re-reads what other writers added
    first (a key already written is never written twice), writes the record
    and its newline in one write, then flushes and fsyncs. A crash mid-append
    leaves at most a torn LAST line (no newline): a load ignores it and the
    next locked append truncates it away. A damaged complete record is
    corruption and is refused, never skipped."""

    def __init__(self, directory: Path | None) -> None:
        self.directory = Path(directory) if directory is not None else None
        self._memory: dict[str, dict[str, dict[str, Any]]] = {}
        #: Bytes of torn tail found per space (reported; truncated on the next append).
        self.recovered: dict[str, int] = {}
        self._thread_lock = threading.Lock()

    def _path(self, space: str) -> Path | None:
        return None if self.directory is None else self.directory / f"{space}.jsonl"

    @staticmethod
    def _checksum(key: str, vectors: Any, raw: Any) -> str:
        return _hash({"key": key, "vectors": vectors, "raw": raw})[:16]

    def _parse(self, space: str, data: bytes) -> tuple[dict[str, dict[str, Any]], int]:
        """The records and the byte offset after the last complete line."""

        rows: dict[str, dict[str, Any]] = {}
        position = 0
        while position < len(data):
            end = data.find(b"\n", position)
            if end < 0:
                break  # a torn tail: the crash interrupted the last append
            line = data[position:end]
            if line.strip():
                try:
                    record = json.loads(line.decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    record = None
                if not (isinstance(record, dict) and isinstance(record.get("key"), str) and record.get("sum")
                        == self._checksum(record["key"], record.get("vectors"), record.get("raw"))):
                    raise StoreCorrupt(f"vector store {space}: a damaged complete record")
                rows.setdefault(record["key"], record)
            position = end + 1
        return rows, position

    def _load(self, space: str) -> dict[str, dict[str, Any]]:
        if space not in self._memory:
            path = self._path(space)
            rows: dict[str, dict[str, Any]] = {}
            if path is not None and path.exists():
                data = path.read_bytes()
                rows, good = self._parse(space, data)
                if good < len(data):
                    self.recovered[space] = len(data) - good
            self._memory[space] = rows
        return self._memory[space]

    def get(self, space: str, key: str) -> list[list[float]] | None:
        record = self._load(space).get(key)
        return None if record is None else record["vectors"]

    def get_raw(self, space: str, key: str) -> Any:
        record = self._load(space).get(key)
        return None if record is None else record.get("raw")

    def put(self, space: str, key: str, vectors: Sequence[Sequence[float]], *, raw: Any = None) -> None:
        values = [[float(value) for value in vector] for vector in vectors]
        record = {"key": key, "vectors": values, "raw": raw, "sum": self._checksum(key, values, raw)}
        path = self._path(space)
        with self._thread_lock:
            if path is None:
                self._load(space).setdefault(key, record)
                return
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path.with_suffix(".lock"), "a+") as lock:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
                try:
                    # Other writers may have appended since this process loaded the file.
                    data = path.read_bytes() if path.exists() else b""
                    rows, good = self._parse(space, data)
                    self._memory[space] = rows
                    if key in rows:
                        return
                    with open(path, "r+b" if path.exists() else "wb") as handle:
                        if good < len(data):
                            handle.truncate(good)  # drop a torn tail before appending
                            self.recovered[space] = len(data) - good
                        handle.seek(good)
                        handle.write((json.dumps(record, sort_keys=True) + "\n").encode("utf-8"))
                        handle.flush()
                        os.fsync(handle.fileno())
                    rows[key] = record
                finally:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def count(self, space: str) -> int:
        return len(self._load(space))


class EmbeddingAdapter:
    """Shared batching, admission, retries, validation and receipts."""

    def __init__(self, pin: EmbeddingPin, *, encoding: str, recipe: str, ledger: E0Ledger, arm: str,
                 extraction_revisions: Sequence[str] = (), transport: Transport | None = None,
                 receipts: Receipts | None = None, store: VectorStore | None = None, epoch: int = 0,
                 key_env: str | None = None, environ: Mapping[str, str] | None = None,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        if encoding not in ("grouped", "singleton", "independent"):
            raise ValueError("encoding must be grouped, singleton or independent")
        if pin.method == "independent" and encoding != "independent":
            raise WrongMethod(f"{pin.model} is an independent model; it has no {encoding} document method")
        if pin.method == "grouped" and encoding == "independent":
            raise WrongMethod(f"{pin.model} is contextual; use grouped or singleton documents")
        self.pin = pin
        self.encoding = encoding
        self.recipe = recipe
        self.ledger = ledger
        self.arm = arm
        self.transport = transport or UrllibTransport()
        self.receipts = receipts or Receipts(None)
        self.store = store or VectorStore(None)
        self.epoch = epoch
        self.key_env = key_env or pin.key_env
        self.environ = environ
        self.sleep = sleep
        self.document_space_id = document_space_id(pin, encoding=encoding, recipe=recipe,
                                                   extraction_revisions=extraction_revisions, epoch=epoch)
        self.query_encoder_id = query_encoder_id(pin, epoch=epoch)

    # -- provider specifics (overridden) ------------------------------------------
    def _document_body(self, documents: Sequence[Document]) -> dict[str, Any]:
        raise NotImplementedError

    def _query_body(self, queries: Sequence[PreparedQuery]) -> dict[str, Any]:
        raise NotImplementedError

    def _document_rows(self, body: Any, documents: Sequence[Document]) -> list[list[Any]]:
        raise NotImplementedError

    def _query_rows(self, body: Any, count: int) -> list[Any]:
        raise NotImplementedError

    def _headers(self) -> dict[str, str]:
        key = credentials.read_key(self.key_env, environ=self.environ) if self.key_env else None
        if not key:
            raise AdapterError(f"{self.key_env} is absent", kind="auth")
        return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    # -- the shared request path --------------------------------------------------
    def _estimate(self, texts: Sequence[str]) -> tuple[int, float]:
        tokens = sum(token_upper_bound(text) + pins.CHUNK_MARKER_TOKENS for text in texts)
        return tokens, tokens * self.pin.price_per_million_upper_bound / 1_000_000

    def _require_price(self) -> None:
        """No request is admitted on an unverified price (fix round 4, High 2)."""

        problem = pins.price_problem(self.pin)
        if problem is not None:
            raise E0PriceUnverified(problem)

    @staticmethod
    def _billed(cost: Any) -> float | None:
        """The provider's explicit cost: a number, or Perplexity's documented
        ``usage.cost`` object (``{"input_cost", "total_cost", "currency": "USD"}``,
        docs.perplexity.ai/api-reference/embeddings-post), whose ``total_cost``
        in USD is the bill. Anything else is no explicit cost."""

        if isinstance(cost, Mapping):
            if cost.get("currency", "USD") != "USD":
                return None
            return explicit_cost(cost.get("total_cost"))
        return explicit_cost(cost)

    def _send(self, url: str, body: Mapping[str, Any], *, method: str, texts: Sequence[str], items: int,
              parse: Callable[[Any], Any] | None = None) -> Any:
        """One admitted request (and its transient retries); returns
        ``parse(response_body)`` (the body when ``parse`` is None).

        The parse runs INSIDE the receipt path (Perplexity canary round): a
        2xx whose body does not parse is settled as billed, and its receipt
        is ``status: "failed"`` with ``error_kind``, ``http_status`` and a
        safe ``contract_reason`` (``AdapterError.reason``: field paths, types
        and counts, never body text). A non-2xx records its status and the
        error body's allowlisted codes (``safe_error_codes``)."""

        self._require_price()
        tokens, usd = self._estimate(texts)
        input_hash = _hash({"url": url, "body": body})
        attempt = 0
        while True:
            request = Request(category="embeddings", provider=self.pin.provider, route=self.pin.model,
                              purpose=f"embed:{method}", arm=self.arm, billing="metered",
                              estimated_usd=usd, estimated_tokens=tokens, attempt=attempt)
            headers = self._headers()
            started = time.monotonic()
            with self.ledger.admit(request) as charge:
                try:
                    response = self.transport.post(url, headers=headers, body=body, timeout=pins.REQUEST_TIMEOUT_S)
                    error = None
                except AdapterError as exc:
                    response, error = None, exc
                latency = time.monotonic() - started
                if response is not None and 200 <= response.status < 300 and isinstance(response.body, Mapping):
                    usage = dict(response.body.get("usage") or {})
                    # The larger reported positive count (an embedding has no
                    # output); none, or only zeros, is unknown billing (F21).
                    counts = [count for key in ("total_tokens", "prompt_tokens")
                              if (count := known_tokens(usage.get(key)))]
                    reported_tokens = max(counts) if counts else None
                    billed = self._billed(usage.get("cost"))
                    price = self.pin.price_per_million_upper_bound
                    actual = reconciled_usd({"input_tokens": reported_tokens, "cost": billed},
                                            lambda tokens_in, _out: tokens_in * price / 1_000_000)
                    charge.settle(actual_usd=actual, usage={"input_tokens": reported_tokens, "cost": billed},
                                  request_id=response.request_id, latency_s=latency)
                    receipt = dict(arm=self.arm, adapter=self.pin.name, endpoint=url, model=self.pin.model,
                                   method=method, input_hash=input_hash, items=items, estimated_tokens=tokens,
                                   usage={"tokens": reported_tokens}, billed_usd=billed, estimated_usd=actual,
                                   attempt=attempt, latency_s=round(latency, 4), request_id=response.request_id,
                                   http_status=response.status)
                    try:
                        parsed = response.body if parse is None else parse(response.body)
                    except AdapterError as exc:
                        self.receipts.write(**receipt, status="failed", error_kind=exc.kind,
                                            contract_reason=exc.reason)
                        exc.http_status = response.status
                        raise
                    self.receipts.write(**receipt, status="ok")
                    return parsed
                kind = error.kind if error is not None else self._kind(response)
                status = response.status if response is not None else None
                reason = self._failure_reason(response, error)
                charge.settle(actual_usd=None, status="failed", latency_s=latency,
                              request_id=response.request_id if response is not None else None)
                self.receipts.write(arm=self.arm, adapter=self.pin.name, endpoint=url, model=self.pin.model,
                                    method=method, input_hash=input_hash, items=items, estimated_tokens=tokens,
                                    status="failed", attempt=attempt, latency_s=round(latency, 4),
                                    request_id=response.request_id if response is not None else None,
                                    error_kind=kind, http_status=status, contract_reason=reason)
            if kind != "transient" or attempt >= pins.TRANSIENT_RETRIES:
                raise AdapterError(f"{self.pin.name} {method} request failed ({kind}): {reason}", kind=kind,
                                   http_status=status)
            attempt += 1
            self.sleep(min(30.0, 2.0 ** attempt))

    @staticmethod
    def _failure_reason(response: HttpResponse | None, error: AdapterError | None) -> str:
        """A failed attempt's safe reason: ``HTTP 422: body.encoding_format:enum``
        (allowlisted codes only), or the transport's own safe message."""

        if response is None:
            return error.reason if error is not None else "no response"
        if 200 <= response.status < 300:
            return f"HTTP {response.status}: the body is not a JSON object ({_type_name(response.body)})"
        codes = ", ".join(response.error_codes)
        return f"HTTP {response.status}" + (f": {codes}" if codes else "")

    @staticmethod
    def _kind(response: HttpResponse | None) -> str:
        if response is None:
            return "transient"
        if response.status in (401, 403):
            return "auth"
        if response.status in (408, 409, 425, 429) or response.status >= 500:
            return "transient"
        if 200 <= response.status < 300:
            return "contract"  # a 2xx without the documented JSON object
        return "contract"

    # -- limits -------------------------------------------------------------------
    def _check_document(self, document: Document) -> None:
        if not document.chunks:
            raise AdapterError("a document has no chunks", kind="limit")
        if any(not chunk.text.strip() for chunk in document.chunks):
            raise AdapterError("a chunk is empty", kind="limit")
        tokens = sum(token_upper_bound(chunk.text) + pins.CHUNK_MARKER_TOKENS for chunk in document.chunks)
        if tokens > self.pin.max_tokens_per_document:
            # Never silently truncated: the caller splits deterministically instead.
            raise AdapterError(f"a document of ~{tokens} tokens passes the {self.pin.max_tokens_per_document} limit",
                               kind="limit")

    def _batches(self, documents: Sequence[Document]) -> list[list[Document]]:
        batches: list[list[Document]] = []
        current: list[Document] = []
        tokens = chunks = 0
        for document in documents:
            self._check_document(document)
            size = sum(token_upper_bound(chunk.text) + pins.CHUNK_MARKER_TOKENS for chunk in document.chunks)
            if current and (tokens + size > self.pin.max_tokens_per_request
                            or chunks + len(document.chunks) > self.pin.max_chunks_per_request
                            or len(current) + 1 > self.pin.max_documents_per_request):
                batches.append(current)
                current, tokens, chunks = [], 0, 0
            if len(document.chunks) > self.pin.max_chunks_per_request:
                raise AdapterError("a document has more chunks than one request allows", kind="limit")
            current.append(document)
            tokens += size
            chunks += len(document.chunks)
        if current:
            batches.append(current)
        return batches

    # -- the contract -------------------------------------------------------------
    def encode_documents(self, documents: Sequence[Document]) -> list[list[Vector]]:
        if self.encoding == "singleton" and any(len(document.chunks) != 1 for document in documents):
            raise WrongMethod("a singleton control sends exactly one chunk per document")
        if self.encoding == "independent" and any(len(document.chunks) != 1 for document in documents):
            raise WrongMethod("an independent model embeds one text per vector")
        results: dict[str, list[Vector]] = {}
        missing: list[Document] = []
        for document in documents:
            saved = self.store.get(self.document_space_id, document.key) if document.key else None
            if saved is not None and len(saved) == len(document.chunks):
                results[document.document_id] = saved
            else:
                missing.append(document)
        for batch in self._batches(missing):
            decoded = self._send(self.pin.document_endpoint, self._document_body(batch), method="document",
                                 texts=[chunk.text for document in batch for chunk in document.chunks],
                                 items=sum(len(document.chunks) for document in batch),
                                 parse=lambda body, batch=batch: self._parse_documents(body, batch))
            for document, (document_rows, vectors) in zip(batch, decoded, strict=True):
                results[document.document_id] = vectors
                if document.key:
                    # The raw rows too: decoding is reproducible from what was paid for.
                    self.store.put(self.document_space_id, document.key, vectors, raw=list(document_rows))
        return [results[document.document_id] for document in documents]

    @property
    def query_space(self) -> str:
        return f"{self.query_encoder_id}_queries"

    def encode_queries(self, queries: Sequence[PreparedQuery], *, fresh: bool = False) -> list[Vector]:
        """Query vectors, each cached under its ``query_vector_key`` (the
        encoder and the complete query text): a resumed run re-sends none it
        already paid for (Codex review F18). ``fresh`` sends every query anew
        (the online latency measurement), never reading the cache."""

        for query in queries:
            if not query.text.strip():
                raise AdapterError("a query is empty", kind="limit")
            if token_upper_bound(query.text) > self.pin.max_tokens_per_document:
                raise AdapterError("a query passes the input limit", kind="limit")
        found: dict[str, Vector] = {}
        missing: list[PreparedQuery] = []
        for query in queries:
            key = query_vector_key(self.query_encoder_id, query.text)
            saved = None if fresh else self.store.get(self.query_space, key)
            if saved is not None:
                found[query.text] = saved[0]
            elif query.text not in {item.text for item in missing}:
                missing.append(query)
        size = max(1, min(self.pin.max_documents_per_request, 128))
        for start in range(0, len(missing), size):
            chunk = list(missing[start:start + size])
            decoded = self._send(self.pin.query_endpoint, self._query_body(chunk), method="query",
                                 texts=[query.text for query in chunk], items=len(chunk),
                                 parse=lambda body, count=len(chunk): self._parse_queries(body, count))
            for query, (row, vector) in zip(chunk, decoded, strict=True):
                found[query.text] = vector
                self.store.put(self.query_space, query_vector_key(self.query_encoder_id, query.text), [vector],
                               raw=[row])
        return [found[query.text] for query in queries]

    def _canary_document(self) -> Document:
        chunks = CANARY_CHUNKS if self.encoding == "grouped" else CANARY_CHUNKS[:1]
        return Document("canary", tuple(Chunk(f"c{index}", text) for index, text in enumerate(chunks)))

    def _canary_vectors(self) -> tuple[list[Vector], Vector]:
        """The canary document's vectors and the canary query's vector, each
        through its own method (document and query contracts)."""

        document = self._canary_document()
        [(_rows, vectors)] = self._send(self.pin.document_endpoint, self._document_body([document]), method="canary",
                                        texts=[chunk.text for chunk in document.chunks], items=len(document.chunks),
                                        parse=lambda body: self._parse_documents(body, [document], check_model=True))
        query = PreparedQuery("canary_query", CANARY_QUERY)
        [(_row, query_vector)] = self._send(self.pin.query_endpoint, self._query_body([query]), method="canary_query",
                                            texts=[query.text], items=1,
                                            parse=lambda body: self._parse_queries(body, 1, check_model=True))
        return vectors, query_vector

    def _parse_documents(self, body: Any, documents: Sequence[Document], *,
                         check_model: bool = False) -> list[tuple[list[Any], list[Vector]]]:
        """Each document's raw rows and decoded vectors (inside ``_send``, so
        a parse failure is on the attempt's receipt)."""

        if check_model:
            self._check_returned_model(body)
        decoded = []
        for position, rows in enumerate(self._document_rows(body, documents)):
            vectors = [decode(row, self.pin, where=self._row_path(position, chunk)).tolist()
                       for chunk, row in enumerate(rows)]
            decoded.append((list(rows), vectors))
        return decoded

    def _parse_queries(self, body: Any, count: int, *, check_model: bool = False) -> list[tuple[Any, Vector]]:
        if check_model:
            self._check_returned_model(body)
        return [(row, decode(row, self.pin, where=self._row_path(position, 0)).tolist())
                for position, row in enumerate(self._query_rows(body, count))]

    def _row_path(self, document: int, chunk: int) -> str:
        """A row's field path in the response (sorted by index)."""

        return f"data[{document}].embedding"

    def _check_returned_model(self, body: Any) -> None:
        """A response that names its model must name the pinned one."""

        model = body.get("model") if isinstance(body, Mapping) else None
        if model is not None and str(model) != self.pin.model:
            raise AdapterError("the provider answered with another model than the pinned one (at model)",
                               kind="contract")

    def canary(self) -> dict[str, Any]:
        """The route's public contract check, before ANY bulk work (fix round
        4, Medium 9): the canary document through the document method AND the
        canary query through the query method; both must decode at the pinned
        dimensions, the query must score against the documents in the same
        paired space (finite similarities), the responses must name the
        pinned model when they name one, and both are compared with the first
        cached outputs (drift beyond cosine 0.995 opens a new epoch)."""

        vectors, query_vector = self._canary_vectors()
        assert_compatible(SpaceVectors(self.document_space_id, self.query_encoder_id, ("c",),
                                       np.asarray([vectors[0]], dtype=np.float32)), self.query_encoder_id)
        scores = [float(np.dot(np.asarray(query_vector), np.asarray(vector))) for vector in vectors]
        if not all(math.isfinite(score) for score in scores):
            raise AdapterError("the canary query does not score against the canary documents", kind="contract")
        space = f"{self.document_space_id}_canary"
        first = self.store.get(space, "canary")
        first_query = self.store.get(space, "canary_query")
        if first is None or first_query is None:
            self.store.put(space, "canary", vectors)
            self.store.put(space, "canary_query", [query_vector])
            return {"status": "cached_first", "dimensions": len(vectors[0]), "query_checked": True}
        similarity = min(float(np.dot(np.asarray(a), np.asarray(b)))
                         for a, b in zip([*first, *first_query], [*vectors, query_vector], strict=True))
        if similarity < CANARY_TOLERANCE:
            raise CanaryDrift(f"canary drift: cosine {similarity:.4f} < {CANARY_TOLERANCE}; open a new epoch")
        return {"status": "stable", "min_cosine": round(similarity, 6), "query_checked": True}


def _ordered(rows: Any, count: int, where: str) -> list[Any]:
    """Rows matched to inputs by their ``index``, never by position.
    ``where`` is the list's field path (``data``, ``data[1].data``); every
    error names a path, a JSON type or a count only (a safe reason)."""

    if rows is None:
        raise AdapterError(f"missing field {where}", kind="contract")
    if not isinstance(rows, list):
        raise AdapterError(f"unexpected type at {where} ({_type_name(rows)}, expected array)", kind="contract")
    if len(rows) != count:
        raise AdapterError(f"{where}: expected {count} rows, got {len(rows)}", kind="contract")
    by_index: dict[int, Any] = {}
    for position, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise AdapterError(f"unexpected type at {where}[{position}] ({_type_name(row)}, expected object)",
                               kind="contract")
        index = row.get("index")
        if index is None:
            raise AdapterError(f"missing field {where}[{position}].index", kind="contract")
        if not isinstance(index, int) or isinstance(index, bool):
            raise AdapterError(f"unexpected type at {where}[{position}].index ({_type_name(index)}, expected "
                               "integer)", kind="contract")
        if index in by_index:
            raise AdapterError(f"{where}: duplicate index", kind="contract")
        by_index[index] = row
    if sorted(by_index) != list(range(count)):
        raise AdapterError(f"{where}: indices do not match the inputs", kind="contract")
    return [by_index[index] for index in range(count)]


def _embedding(row: Mapping[str, Any], where: str) -> Any:
    if "embedding" not in row or row.get("embedding") is None:
        raise AdapterError(f"missing field {where}.embedding", kind="contract")
    return row["embedding"]


def _json_object(body: Any) -> Mapping[str, Any]:
    if not isinstance(body, Mapping):
        raise AdapterError(f"unexpected type at the response body ({_type_name(body)}, expected object)",
                           kind="contract")
    return body


class _GroupedAdapter(EmbeddingAdapter):
    """Contextualized endpoints: nested documents, nested ordered responses."""

    def _document_rows(self, body: Any, documents: Sequence[Document]) -> list[list[Any]]:
        outer = _ordered(_json_object(body).get("data"), len(documents), "data")
        rows: list[list[Any]] = []
        for position, (document, entry) in enumerate(zip(documents, outer, strict=True)):
            where = f"data[{position}].data"
            inner = _ordered(entry.get("data"), len(document.chunks), where)
            rows.append([_embedding(row, f"{where}[{chunk}]") for chunk, row in enumerate(inner)])
        return rows

    def _query_rows(self, body: Any, count: int) -> list[Any]:
        rows = self._document_rows(body, [Document(f"q{index}", (Chunk("q", "q"),)) for index in range(count)])
        return [row[0] for row in rows]

    def _row_path(self, document: int, chunk: int) -> str:
        return f"data[{document}].data[{chunk}].embedding"


class _IndependentAdapter(EmbeddingAdapter):
    def _document_rows(self, body: Any, documents: Sequence[Document]) -> list[list[Any]]:
        rows = _ordered(_json_object(body).get("data"), len(documents), "data")
        return [[_embedding(row, f"data[{position}]")] for position, row in enumerate(rows)]

    def _query_rows(self, body: Any, count: int) -> list[Any]:
        rows = _ordered(_json_object(body).get("data"), count, "data")
        return [_embedding(row, f"data[{position}]") for position, row in enumerate(rows)]


#: Perplexity's documented encoding (both endpoints): ``base64_int8`` (the
#: default; ``base64_binary`` is the other value). The first paid run sent
#: ``"int8"``, outside that enum, and every canary got a 422.
PERPLEXITY_ENCODING = "base64_int8"


class PerplexityContextualAdapter(_GroupedAdapter):
    """``pplx-embed-context-v1-4b``: grouped windows and the singleton control.

    The documented request (docs.perplexity.ai/api-reference/contextualized-embeddings-post,
    read 2026-10-23): ``input`` = an array of documents, each an array of its
    chunk strings; ``model``; optional ``dimensions`` (128-2560 for 4b,
    default 2560) and ``encoding_format``. There is NO ``input_type``: the
    documented query method is the same endpoint and model with each query
    wrapped as a one-chunk document, ``[[query]]``
    (docs.perplexity.ai/docs/embeddings/contextualized-embeddings). The
    response nests ``data[]`` per document (``index``) holding ``data[]`` per
    chunk (``index``, ``embedding`` = a base64 string)."""

    def _document_body(self, documents: Sequence[Document]) -> dict[str, Any]:
        return {"model": self.pin.model, "input": [[chunk.text for chunk in document.chunks] for document in documents],
                "dimensions": self.pin.dimensions, "encoding_format": PERPLEXITY_ENCODING}

    def _query_body(self, queries: Sequence[PreparedQuery]) -> dict[str, Any]:
        return {"model": self.pin.model, "input": [[query.text] for query in queries],
                "dimensions": self.pin.dimensions, "encoding_format": PERPLEXITY_ENCODING}


class PerplexityIndependentAdapter(_IndependentAdapter):
    """``pplx-embed-v1-4b``: the independent family baseline.

    The documented request (docs.perplexity.ai/api-reference/embeddings-post,
    read 2026-10-23): ``input`` = a string or an array of 1-512 strings;
    ``model``; optional ``dimensions`` and ``encoding_format``. No
    ``input_type`` and no query prefix: queries and documents go through the
    same call (docs.perplexity.ai/docs/embeddings/standard-embeddings). The
    response is ``data[]`` (``index``, ``embedding`` = a base64 string)."""

    def _document_body(self, documents: Sequence[Document]) -> dict[str, Any]:
        return {"model": self.pin.model, "input": [document.chunks[0].text for document in documents],
                "dimensions": self.pin.dimensions, "encoding_format": PERPLEXITY_ENCODING}

    def _query_body(self, queries: Sequence[PreparedQuery]) -> dict[str, Any]:
        return {"model": self.pin.model, "input": [query.text for query in queries],
                "dimensions": self.pin.dimensions, "encoding_format": PERPLEXITY_ENCODING}


class VoyageContextualAdapter(_GroupedAdapter):
    """``voyage-context-4``: grouped windows and the singleton control."""

    def _document_body(self, documents: Sequence[Document]) -> dict[str, Any]:
        return {"model": self.pin.model, "inputs": [[chunk.text for chunk in document.chunks] for document in documents],
                "input_type": "document", "output_dimension": self.pin.dimensions, "output_dtype": "float"}

    def _query_body(self, queries: Sequence[PreparedQuery]) -> dict[str, Any]:
        return {"model": self.pin.model, "inputs": [[query.text] for query in queries], "input_type": "query",
                "output_dimension": self.pin.dimensions, "output_dtype": "float"}


class VoyageIndependentAdapter(_IndependentAdapter):
    """``voyage-4-large`` through the Voyage API (never truncated)."""

    def _document_body(self, documents: Sequence[Document]) -> dict[str, Any]:
        return {"model": self.pin.model, "input": [document.chunks[0].text for document in documents],
                "input_type": "document", "truncation": False, "output_dimension": self.pin.dimensions,
                "output_dtype": "float"}

    def _query_body(self, queries: Sequence[PreparedQuery]) -> dict[str, Any]:
        return {"model": self.pin.model, "input": [query.text for query in queries], "input_type": "query",
                "truncation": False, "output_dimension": self.pin.dimensions, "output_dtype": "float"}


class QwenAdapter(EmbeddingAdapter):
    """Qwen through the production OpenRouter client (``data_collection=deny``),
    one admitted request per batch; the production prefixes for each method."""

    def __init__(self, pin: EmbeddingPin, *, client_factory: Callable[[], Any], **kwargs: Any) -> None:
        super().__init__(pin, encoding="independent", **kwargs)
        self._client_factory = client_factory
        try:
            self._client: Any = client_factory()
        except Exception as exc:  # an absent key, an unknown profile: nothing was sent
            raise AdapterError(f"the Qwen client could not be built ({type(exc).__name__})", kind="auth") from None
        # Validated before the first request; part of every cache key and receipt (High 4).
        self.identity = qwen_identity(self._client, pin)
        serving = _hash(self.identity)[:16]
        self.document_space_id = document_space_id(pin, encoding="independent", recipe=self.recipe,
                                                   extraction_revisions=kwargs.get("extraction_revisions") or (),
                                                   epoch=self.epoch, serving_provider=serving)
        self.query_encoder_id = query_encoder_id(pin, epoch=self.epoch, serving_provider=serving)
        #: The raw rows of the last batch (kept beside the decoded vectors).
        self._last_raw: list[list[float]] = []

    def _client_now(self) -> Any:
        return self._client

    def _canary_vectors(self) -> tuple[list[Vector], Vector]:
        document = self._canary_document()
        vectors = self._embed([chunk.text for chunk in document.chunks], "retrieval-document", "canary")
        query_vector = self._embed([CANARY_QUERY], "retrieval-query", "canary_query")[0]
        return vectors, query_vector

    def _embed(self, texts: list[str], task: str, method: str) -> list[list[float]]:
        self._require_price()
        tokens, usd = self._estimate(texts)
        request = Request(category="embeddings", provider=self.pin.provider, route=self.pin.model,
                          purpose=f"embed:{method}", arm=self.arm, billing="metered", estimated_usd=usd,
                          estimated_tokens=tokens)
        attempt = 0
        while True:
            started = time.monotonic()
            with self.ledger.admit(Request(**{**request.__dict__, "attempt": attempt})) as charge:
                try:
                    vectors = self._client_now().embed(texts, task)
                    failure = None
                except Exception as exc:  # the production client normalizes provider errors
                    vectors, failure = None, exc
                latency = time.monotonic() - started
                if vectors is not None:
                    # The production client reports usage to receipts; the ledger
                    # reconciles at the conservative estimate (the price bound).
                    charge.settle(actual_usd=usd, usage={"input_tokens": tokens}, latency_s=latency)
                    self.receipts.write(arm=self.arm, adapter=self.pin.name, endpoint=self.pin.document_endpoint,
                                        model=self.pin.model, method=method, input_hash=_hash(texts), identity=self.identity,
                                        items=len(texts), estimated_tokens=tokens, estimated_usd=usd, status="ok",
                                        attempt=attempt, latency_s=round(latency, 4))
                    break
                charge.settle(actual_usd=None, status="failed", latency_s=latency)
                self.receipts.write(arm=self.arm, adapter=self.pin.name, endpoint=self.pin.document_endpoint,
                                    model=self.pin.model, method=method, input_hash=_hash(texts), identity=self.identity,
                                    items=len(texts),
                                    estimated_tokens=tokens, status="failed", attempt=attempt,
                                    latency_s=round(latency, 4), error_kind=type(failure).__name__)
            if attempt >= pins.TRANSIENT_RETRIES or isinstance(failure, (ValueError, E0BudgetExceeded)):
                raise AdapterError(f"qwen {method} request failed ({type(failure).__name__})", kind="transient")
            attempt += 1
            self.sleep(min(30.0, 2.0 ** attempt))
        if len(vectors) != len(texts):
            raise AdapterError("qwen returned a different number of vectors", kind="contract")
        self._last_raw = [[float(value) for value in vector] for vector in vectors]
        return [decode(raw, self.pin).tolist() for raw in self._last_raw]

    def encode_documents(self, documents: Sequence[Document]) -> list[list[Vector]]:
        if any(len(document.chunks) != 1 for document in documents):
            raise WrongMethod("an independent model embeds one text per vector")
        results: dict[str, list[Vector]] = {}
        missing = []
        for document in documents:
            saved = self.store.get(self.document_space_id, document.key) if document.key else None
            if saved is not None:
                results[document.document_id] = saved
            else:
                self._check_document(document)
                missing.append(document)
        for start in range(0, len(missing), self.pin.max_documents_per_request):
            batch = missing[start:start + self.pin.max_documents_per_request]
            vectors = self._embed([document.chunks[0].text for document in batch], "retrieval-document", "document")
            for document, vector, raw in zip(batch, vectors, self._last_raw, strict=True):
                results[document.document_id] = [vector]
                if document.key:
                    self.store.put(self.document_space_id, document.key, [vector], raw=[raw])
        return [results[document.document_id] for document in documents]

    def encode_queries(self, queries: Sequence[PreparedQuery], *, fresh: bool = False) -> list[Vector]:
        """Cached per ``query_vector_key`` like every adapter (Codex review F18);
        ``fresh`` sends every query anew."""

        found: dict[str, Vector] = {}
        missing: list[PreparedQuery] = []
        for query in queries:
            key = query_vector_key(self.query_encoder_id, query.text)
            saved = None if fresh else self.store.get(self.query_space, key)
            if saved is not None:
                found[query.text] = saved[0]
            elif query.text not in {item.text for item in missing}:
                missing.append(query)
        for start in range(0, len(missing), self.pin.max_documents_per_request):
            chunk = missing[start:start + self.pin.max_documents_per_request]
            vectors = self._embed([query.text for query in chunk], "retrieval-query", "query")
            for query, vector, raw in zip(chunk, vectors, self._last_raw, strict=True):
                found[query.text] = vector
                self.store.put(self.query_space, query_vector_key(self.query_encoder_id, query.text), [vector],
                               raw=[raw])
        return [found[query.text] for query in queries]


ADAPTERS: dict[str, type[EmbeddingAdapter]] = {
    "pplx_context_4b": PerplexityContextualAdapter,
    "pplx_4b": PerplexityIndependentAdapter,
    "voyage_context_4": VoyageContextualAdapter,
    "voyage_4_large": VoyageIndependentAdapter,
}


@dataclass(frozen=True)
class SpaceVectors:
    """An index's vectors, all from one document space."""

    document_space_id: str
    paired_query_encoder_id: str
    ids: tuple[str, ...]
    matrix: np.ndarray


def assert_compatible(index: SpaceVectors, query_encoder: str) -> None:
    """Refuse a query vector from another encoder (equal widths prove nothing)."""

    if query_encoder != index.paired_query_encoder_id:
        raise MixedSpace(f"query encoder {query_encoder} does not match the index's {index.paired_query_encoder_id}")


def build_index(entries: Sequence[tuple[str, str, str, Sequence[float]]]) -> SpaceVectors:
    """``entries``: (id, document_space_id, paired query encoder, vector).
    Refuses mixing spaces in one index."""

    spaces = {(space, encoder) for _id, space, encoder, _vector in entries}
    if len(spaces) != 1:
        raise MixedSpace(f"an index mixes {len(spaces)} spaces")
    (space, encoder), = spaces
    ids = tuple(entry[0] for entry in entries)
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate ids in one index")
    matrix = np.asarray([entry[3] for entry in entries], dtype=np.float32)
    return SpaceVectors(space, encoder, ids, matrix)
