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
* Resume: a document whose vector key is already stored is not re-sent; the
  first successful canary output is cached and later canaries are compared
  within a tolerance (``CanaryDrift`` opens a new epoch).

Every provider contract here is UNVERIFIED offline (``pins``). The canary
(``learnloop experiments e0 contracts``) validates it before any paid run.
"""
from __future__ import annotations

import base64
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Protocol
import urllib.error
import urllib.request

import numpy as np

from learnloop.experiments.contextual_embeddings import credentials, pins
from learnloop.experiments.contextual_embeddings.budget import E0BudgetExceeded, E0Ledger, Request
from learnloop.experiments.contextual_embeddings.pins import EmbeddingPin, conservative_tokens

Vector = list[float]
#: A fixed, public canary (no private text): re-encoded on resume to detect drift.
CANARY_CHUNKS = ("Definition. A vector space is a set with addition and scalar multiplication.",
                 "Example. The real numbers form a vector space over themselves.")
CANARY_TOLERANCE = 0.995


class AdapterError(RuntimeError):
    """An adapter failure; ``kind`` is transient, auth, contract, limit or validation."""

    def __init__(self, message: str, *, kind: str) -> None:
        super().__init__(message)
        self.kind = kind


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


class Transport(Protocol):
    def post(self, url: str, *, headers: Mapping[str, str], body: Mapping[str, Any],
             timeout: float) -> HttpResponse: ...


class UrllibTransport:
    """The real HTTPS transport. Errors carry the status only, never the body
    (provider error bodies can echo request text)."""

    def post(self, url: str, *, headers: Mapping[str, str], body: Mapping[str, Any],
             timeout: float) -> HttpResponse:
        data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(url, data=data, method="POST", headers=dict(headers))
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 (fixed https pins)
                payload = json.loads(response.read().decode("utf-8"))
                request_id = response.headers.get("x-request-id") or response.headers.get("request-id")
                return HttpResponse(int(response.status), payload, request_id)
        except urllib.error.HTTPError as exc:
            return HttpResponse(int(exc.code), None, exc.headers.get("x-request-id") if exc.headers else None)
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


def query_encoder_id(pin: EmbeddingPin, *, epoch: int = 0) -> str:
    """The spec's ``query_encoder_id`` (§4.3)."""

    return "qe_" + _hash({"model": pin.model, "alias_epoch": epoch, "query_mode": pin.query_method,
                          "precision": pin.output_format, "projection": None, "dimensions": pin.dimensions,
                          "output_transform": pin.decode_transform})[:24]


def decode(values: Any, pin: EmbeddingPin) -> np.ndarray:
    """A raw output row as the FP32 scoring copy (validated, L2-normalized)."""

    if pin.output_format == "int8":
        if isinstance(values, str):
            try:
                raw = np.frombuffer(base64.b64decode(values, validate=True), dtype=np.int8).astype(np.float32)
            except (ValueError, TypeError):
                raise AdapterError("int8 output is not valid base64", kind="validation") from None
        else:
            if not isinstance(values, list) or not all(isinstance(value, int) and not isinstance(value, bool)
                                                       for value in values):
                raise AdapterError("int8 output is not a list of integers", kind="validation")
            if any(value < -128 or value > 127 for value in values):
                raise AdapterError("int8 output is out of range", kind="validation")
            raw = np.asarray(values, dtype=np.float32)
    else:
        if not isinstance(values, list) or not all(isinstance(value, (int, float)) and not isinstance(value, bool)
                                                   for value in values):
            raise AdapterError("float output is not a list of numbers", kind="validation")
        raw = np.asarray(values, dtype=np.float64)
    if raw.shape != (pin.dimensions,):
        raise AdapterError(f"output has {raw.shape[0] if raw.ndim else 0} dimensions, pinned {pin.dimensions}",
                           kind="contract")
    if not np.all(np.isfinite(raw)):
        raise AdapterError("output contains non-finite values", kind="validation")
    norm = float(np.linalg.norm(raw))
    if not norm or not math.isfinite(norm):
        raise AdapterError("output is a zero vector", kind="validation")
    return (raw / norm).astype(np.float32)


class Receipts:
    """Append-only JSON lines (one per physical attempt), private to the run."""

    FIELDS = ("at", "arm", "adapter", "endpoint", "model", "method", "input_hash", "items", "estimated_tokens",
              "usage", "billed_usd", "estimated_usd", "status", "attempt", "latency_s", "request_id",
              "error_kind", "resumed")

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


class VectorStore:
    """Research vectors keyed by vector key, one JSON-lines file per space
    (outside production ``embedding_vectors``). Idempotent: a key is written
    once; ``get`` returns the first successful output."""

    def __init__(self, directory: Path | None) -> None:
        self.directory = Path(directory) if directory is not None else None
        self._memory: dict[str, dict[str, list[list[float]]]] = {}

    def _path(self, space: str) -> Path | None:
        return None if self.directory is None else self.directory / f"{space}.jsonl"

    def _load(self, space: str) -> dict[str, list[list[float]]]:
        if space not in self._memory:
            rows: dict[str, list[list[float]]] = {}
            path = self._path(space)
            if path is not None and path.exists():
                for line in path.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        entry = json.loads(line)
                        rows.setdefault(entry["key"], entry["vectors"])
            self._memory[space] = rows
        return self._memory[space]

    def get(self, space: str, key: str) -> list[list[float]] | None:
        return self._load(space).get(key)

    def put(self, space: str, key: str, vectors: Sequence[Sequence[float]]) -> None:
        rows = self._load(space)
        if key in rows:
            return
        values = [[float(value) for value in vector] for vector in vectors]
        rows[key] = values
        path = self._path(space)
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps({"key": key, "vectors": values}) + "\n")

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
        tokens = sum(conservative_tokens(text) + pins.CHUNK_MARKER_TOKENS for text in texts)
        return tokens, tokens * self.pin.price_per_million_upper_bound / 1_000_000

    def _send(self, url: str, body: Mapping[str, Any], *, method: str, texts: Sequence[str], items: int) -> Any:
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
                    reported_tokens = usage.get("total_tokens") or usage.get("prompt_tokens")
                    cost = usage.get("cost")
                    billed = float(cost) if isinstance(cost, (int, float)) and not isinstance(cost, bool) else None
                    actual = billed if billed is not None else (
                        int(reported_tokens) * self.pin.price_per_million_upper_bound / 1_000_000
                        if isinstance(reported_tokens, int) else None)
                    charge.settle(actual_usd=actual, usage={"input_tokens": reported_tokens, "cost": cost},
                                  request_id=response.request_id, latency_s=latency)
                    self.receipts.write(arm=self.arm, adapter=self.pin.name, endpoint=url, model=self.pin.model,
                                        method=method, input_hash=input_hash, items=items, estimated_tokens=tokens,
                                        usage={"tokens": reported_tokens}, billed_usd=billed, estimated_usd=actual,
                                        status="ok", attempt=attempt, latency_s=round(latency, 4),
                                        request_id=response.request_id)
                    return response.body
                kind = error.kind if error is not None else self._kind(response)
                charge.settle(actual_usd=None, status="failed", latency_s=latency,
                              request_id=response.request_id if response is not None else None)
                self.receipts.write(arm=self.arm, adapter=self.pin.name, endpoint=url, model=self.pin.model,
                                    method=method, input_hash=input_hash, items=items, estimated_tokens=tokens,
                                    status="failed", attempt=attempt, latency_s=round(latency, 4),
                                    request_id=response.request_id if response is not None else None,
                                    error_kind=kind)
            if kind != "transient" or attempt >= pins.TRANSIENT_RETRIES:
                raise AdapterError(f"{self.pin.name} {method} request failed ({kind})", kind=kind)
            attempt += 1
            self.sleep(min(30.0, 2.0 ** attempt))

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
        tokens = sum(conservative_tokens(chunk.text) + pins.CHUNK_MARKER_TOKENS for chunk in document.chunks)
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
            size = sum(conservative_tokens(chunk.text) + pins.CHUNK_MARKER_TOKENS for chunk in document.chunks)
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
            body = self._send(self.pin.document_endpoint, self._document_body(batch), method="document",
                              texts=[chunk.text for document in batch for chunk in document.chunks],
                              items=sum(len(document.chunks) for document in batch))
            rows = self._document_rows(body, batch)
            for document, document_rows in zip(batch, rows, strict=True):
                vectors = [decode(row, self.pin).tolist() for row in document_rows]
                results[document.document_id] = vectors
                if document.key:
                    self.store.put(self.document_space_id, document.key, vectors)
        return [results[document.document_id] for document in documents]

    def encode_queries(self, queries: Sequence[PreparedQuery]) -> list[Vector]:
        for query in queries:
            if not query.text.strip():
                raise AdapterError("a query is empty", kind="limit")
            if conservative_tokens(query.text) > self.pin.max_tokens_per_document:
                raise AdapterError("a query passes the input limit", kind="limit")
        found: list[Vector] = []
        size = max(1, min(self.pin.max_documents_per_request, 128))
        for start in range(0, len(queries), size):
            chunk = list(queries[start:start + size])
            body = self._send(self.pin.query_endpoint, self._query_body(chunk), method="query",
                              texts=[query.text for query in chunk], items=len(chunk))
            rows = self._query_rows(body, len(chunk))
            found.extend(decode(row, self.pin).tolist() for row in rows)
        return found

    def canary(self) -> dict[str, Any]:
        """Encode the public canary and compare with the first cached output."""

        document = Document("canary", tuple(Chunk(f"c{index}", text) for index, text in enumerate(
            CANARY_CHUNKS if self.encoding == "grouped" else CANARY_CHUNKS[:1])))
        if self.encoding != "grouped":
            document = Document("canary", document.chunks[:1])
        fresh = self._document_rows(self._send(self.pin.document_endpoint, self._document_body([document]),
                                               method="canary", texts=[chunk.text for chunk in document.chunks],
                                               items=len(document.chunks)), [document])[0]
        vectors = [decode(row, self.pin).tolist() for row in fresh]
        space = f"{self.document_space_id}_canary"
        first = self.store.get(space, "canary")
        if first is None:
            self.store.put(space, "canary", vectors)
            return {"status": "cached_first", "dimensions": len(vectors[0])}
        similarity = min(float(np.dot(np.asarray(a), np.asarray(b))) for a, b in zip(first, vectors, strict=True))
        if similarity < CANARY_TOLERANCE:
            raise CanaryDrift(f"canary drift: cosine {similarity:.4f} < {CANARY_TOLERANCE}; open a new epoch")
        return {"status": "stable", "min_cosine": round(similarity, 6)}


def _ordered(rows: Any, count: int, what: str) -> list[Any]:
    """Rows matched to inputs by their ``index``, never by position."""

    if not isinstance(rows, list) or len(rows) != count:
        raise AdapterError(f"{what}: expected {count} rows", kind="contract")
    by_index: dict[int, Any] = {}
    for row in rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("index"), int) or isinstance(row.get("index"), bool):
            raise AdapterError(f"{what}: a row has no integer index", kind="contract")
        if row["index"] in by_index:
            raise AdapterError(f"{what}: duplicate index", kind="contract")
        by_index[row["index"]] = row
    if sorted(by_index) != list(range(count)):
        raise AdapterError(f"{what}: indices do not match the inputs", kind="contract")
    return [by_index[index] for index in range(count)]


class _GroupedAdapter(EmbeddingAdapter):
    """Contextualized endpoints: nested documents, nested ordered responses."""

    def _document_rows(self, body: Any, documents: Sequence[Document]) -> list[list[Any]]:
        if not isinstance(body, Mapping):
            raise AdapterError("response is not a JSON object", kind="contract")
        outer = _ordered(body.get("data"), len(documents), "documents")
        rows: list[list[Any]] = []
        for document, entry in zip(documents, outer, strict=True):
            inner = _ordered(entry.get("data"), len(document.chunks), "chunks")
            rows.append([row.get("embedding") for row in inner])
        return rows

    def _query_rows(self, body: Any, count: int) -> list[Any]:
        rows = self._document_rows(body, [Document(f"q{index}", (Chunk("q", "q"),)) for index in range(count)])
        return [row[0] for row in rows]


class _IndependentAdapter(EmbeddingAdapter):
    def _document_rows(self, body: Any, documents: Sequence[Document]) -> list[list[Any]]:
        if not isinstance(body, Mapping):
            raise AdapterError("response is not a JSON object", kind="contract")
        rows = _ordered(body.get("data"), len(documents), "texts")
        return [[row.get("embedding")] for row in rows]

    def _query_rows(self, body: Any, count: int) -> list[Any]:
        if not isinstance(body, Mapping):
            raise AdapterError("response is not a JSON object", kind="contract")
        return [row.get("embedding") for row in _ordered(body.get("data"), count, "queries")]


class PerplexityContextualAdapter(_GroupedAdapter):
    """``pplx-embed-context-v1-4b``: grouped windows and the singleton control."""

    def _document_body(self, documents: Sequence[Document]) -> dict[str, Any]:
        return {"model": self.pin.model, "input": [[chunk.text for chunk in document.chunks] for document in documents],
                "input_type": "document", "dimensions": self.pin.dimensions, "encoding_format": "int8"}

    def _query_body(self, queries: Sequence[PreparedQuery]) -> dict[str, Any]:
        return {"model": self.pin.model, "input": [[query.text] for query in queries], "input_type": "query",
                "dimensions": self.pin.dimensions, "encoding_format": "int8"}


class PerplexityIndependentAdapter(_IndependentAdapter):
    """``pplx-embed-v1-4b``: the independent family baseline."""

    def _document_body(self, documents: Sequence[Document]) -> dict[str, Any]:
        return {"model": self.pin.model, "input": [document.chunks[0].text for document in documents],
                "input_type": "document", "dimensions": self.pin.dimensions, "encoding_format": "int8"}

    def _query_body(self, queries: Sequence[PreparedQuery]) -> dict[str, Any]:
        return {"model": self.pin.model, "input": [query.text for query in queries], "input_type": "query",
                "dimensions": self.pin.dimensions, "encoding_format": "int8"}


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
        self._client: Any | None = None

    def _client_now(self) -> Any:
        if self._client is None:
            self._client = self._client_factory()
        return self._client

    def _embed(self, texts: list[str], task: str, method: str) -> list[list[float]]:
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
                                        model=self.pin.model, method=method, input_hash=_hash(texts),
                                        items=len(texts), estimated_tokens=tokens, estimated_usd=usd, status="ok",
                                        attempt=attempt, latency_s=round(latency, 4))
                    break
                charge.settle(actual_usd=None, status="failed", latency_s=latency)
                self.receipts.write(arm=self.arm, adapter=self.pin.name, endpoint=self.pin.document_endpoint,
                                    model=self.pin.model, method=method, input_hash=_hash(texts), items=len(texts),
                                    estimated_tokens=tokens, status="failed", attempt=attempt,
                                    latency_s=round(latency, 4), error_kind=type(failure).__name__)
            if attempt >= pins.TRANSIENT_RETRIES or isinstance(failure, (ValueError, E0BudgetExceeded)):
                raise AdapterError(f"qwen {method} request failed ({type(failure).__name__})", kind="transient")
            attempt += 1
            self.sleep(min(30.0, 2.0 ** attempt))
        if len(vectors) != len(texts):
            raise AdapterError("qwen returned a different number of vectors", kind="contract")
        return [decode([float(value) for value in vector], self.pin).tolist() for vector in vectors]

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
            for document, vector in zip(batch, vectors, strict=True):
                results[document.document_id] = [vector]
                if document.key:
                    self.store.put(self.document_space_id, document.key, [vector])
        return [results[document.document_id] for document in documents]

    def encode_queries(self, queries: Sequence[PreparedQuery]) -> list[Vector]:
        found: list[Vector] = []
        for start in range(0, len(queries), self.pin.max_documents_per_request):
            chunk = queries[start:start + self.pin.max_documents_per_request]
            found.extend(self._embed([query.text for query in chunk], "retrieval-query", "query"))
        return found


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
