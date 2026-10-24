"""The Voyage contextualized-chunk client (spec_local_contextual_retrieval_v1 §8; P1b).

``voyage-context-4`` through ``POST <base_url>/contextualizedembeddings``,
moved from E0's ``VoyageContextualAdapter`` (which stays E0's record): nested
inputs, one inner list per document (a grouped window) and one single-chunk
inner list per query; ``input_type`` ``document`` or ``query``; 1024-d float,
L2-normalized here.

One request per call, no hidden retries or batch splitting: callers own
admission, caps and retries. Each request is one ``model_call`` (a receipt for
the context's observer, admission through its request gate) with the
reported token usage. Provider errors travel as their class or HTTP status
only: a response body or exception message can echo request text or the key,
so neither is ever put in an error. Redirects are refused (the key is never
sent to another host).
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import json
import math
import os
from typing import Any
import urllib.error
import urllib.request

from learnloop.ai.embedding import Vector, current_embedding_timeout
from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.execution import model_call, report_call_usage
from learnloop.ai.transport import EMBEDDING
from learnloop.config import AIProviderConfig

DEFAULT_MODEL = "voyage-context-4"
DEFAULT_BASE_URL = "https://api.voyageai.com/v1"
#: Documented limits (docs.voyageai.com contextualized chunk embeddings).
MAX_INPUTS_PER_REQUEST = 1_000
MAX_CHUNKS_PER_REQUEST = 16_000
MAX_TOKENS_PER_REQUEST = 120_000
MAX_TOKENS_PER_DOCUMENT = 32_000
REQUEST_TIMEOUT_S = 120.0


@dataclass(frozen=True)
class HttpResult:
    status: int
    body: Any
    request_id: str | None = None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args: Any, **_kwargs: Any) -> None:  # noqa: D401 - urllib hook
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def urllib_post(url: str, *, headers: Mapping[str, str], body: Mapping[str, Any], timeout: float) -> HttpResult:
    """The real HTTPS POST (redirects refused; the error body is never read into a message)."""

    request = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                     headers=dict(headers))
    try:
        with _OPENER.open(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return HttpResult(int(response.status), payload, response.headers.get("x-request-id"))
    except urllib.error.HTTPError as exc:
        return HttpResult(int(exc.code), None, exc.headers.get("x-request-id") if exc.headers else None)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        error = AIProviderUnavailable(f"Voyage request failed ({type(exc).__name__})")
        error.provider_error = type(exc).__name__
        raise error from None


Transport = Callable[..., HttpResult]


def _unit(row: Any, dims: int, where: str) -> Vector:
    if not isinstance(row, Mapping) or not isinstance(row.get("embedding"), list):
        raise ValueError(f"Voyage response is malformed at {where}")
    vector = [float(value) for value in row["embedding"]]
    if len(vector) != dims or not all(math.isfinite(value) for value in vector):
        raise ValueError(f"Voyage response has the wrong width or a non-finite value at {where}")
    norm = math.hypot(*vector)
    if not norm or not math.isfinite(norm):
        raise ValueError(f"Voyage response has an invalid vector norm at {where}")
    return [value / norm for value in vector]


def _ordered(rows: Any, count: int, where: str) -> list[Any]:
    if not isinstance(rows, list) or len(rows) != count:
        raise ValueError(f"Voyage response has the wrong number of rows at {where}")
    indexed = sorted(rows, key=lambda row: row.get("index", -1) if isinstance(row, Mapping) else -1)
    if [row.get("index") if isinstance(row, Mapping) else None for row in indexed] != list(range(count)):
        raise ValueError(f"Voyage response indices do not match the request at {where}")
    return indexed


class VoyageContextualClient:
    provider_type = "voyage_contextual_embedding"
    default_base_url = DEFAULT_BASE_URL

    def __init__(self, provider_name: str, profile: AIProviderConfig, *, transport: Transport | None = None) -> None:
        self.provider_name = provider_name
        self.profile = profile
        self.model_id = profile.model or DEFAULT_MODEL
        self.model = self.model_id
        self.dims = int(getattr(profile, "dimensions", 1024))
        self.modalities = frozenset({"text"})
        self.max_input_tokens = MAX_TOKENS_PER_DOCUMENT
        self.base_url = (profile.base_url or DEFAULT_BASE_URL).rstrip("/")
        self.key_env = getattr(profile, "api_key_env", None) or "VOYAGE_API_KEY"
        key = os.environ.get(self.key_env)
        if not key:
            raise AIProviderUnavailable(f"Environment variable {self.key_env} is required.")
        self._key = key
        self._post = transport or urllib_post

    def supports(self, capability: str) -> bool:
        return capability == EMBEDDING

    def _request(self, inputs: list[list[str]], input_type: str, method: str) -> Any:
        if not inputs:
            return {"data": []}
        if len(inputs) > MAX_INPUTS_PER_REQUEST or sum(len(row) for row in inputs) > MAX_CHUNKS_PER_REQUEST:
            raise ValueError("A Voyage request passes the documented input or chunk limit")
        if any(not chunk.strip() for row in inputs for chunk in row):
            raise ValueError("A Voyage input chunk is empty")
        body = {"model": self.model_id, "inputs": inputs, "input_type": input_type,
                "output_dimension": self.dims, "output_dtype": "float"}
        headers = {"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"}
        timeout = current_embedding_timeout()
        with model_call(self, purpose="embedding", prompt=[method, inputs]):
            result = self._post(f"{self.base_url}/contextualizedembeddings", headers=headers, body=body,
                                timeout=max(float(timeout), 0.001) if timeout is not None else REQUEST_TIMEOUT_S)
            if not 200 <= result.status < 300 or not isinstance(result.body, Mapping):
                error = AIProviderUnavailable(f"Voyage request failed (HTTP {result.status})")
                error.provider_error = "APITimeoutError" if result.status == 408 else f"HTTP {result.status}"
                raise error
            usage = result.body.get("usage") if isinstance(result.body.get("usage"), Mapping) else {}
            tokens = usage.get("total_tokens")
            report_call_usage({"input_tokens": int(tokens) if isinstance(tokens, int) else None,
                               "output_tokens": 0, "provider_request_id": result.request_id,
                               "resolved_model": self.model_id})
            return result.body

    def embed_documents(self, documents: Sequence[Sequence[str]]) -> list[list[Vector]]:
        """One vector per chunk of each document (window), in input order."""

        rows = [list(chunks) for chunks in documents]
        body = self._request(rows, "document", "document")
        outer = _ordered(body.get("data"), len(rows), "data")
        vectors: list[list[Vector]] = []
        for position, (entry, chunks) in enumerate(zip(outer, rows, strict=True)):
            inner = _ordered(entry.get("data"), len(chunks), f"data[{position}].data")
            vectors.append([_unit(row, self.dims, f"data[{position}].data[{index}]")
                            for index, row in enumerate(inner)])
        return vectors

    def embed_queries(self, queries: Sequence[str]) -> list[Vector]:
        rows = [[text] for text in queries]
        body = self._request(rows, "query", "query")
        outer = _ordered(body.get("data"), len(rows), "data")
        return [_unit(_ordered(entry.get("data"), 1, f"data[{position}].data")[0], self.dims, f"data[{position}]")
                for position, entry in enumerate(outer)]


__all__ = [
    "DEFAULT_BASE_URL",
    "DEFAULT_MODEL",
    "HttpResult",
    "MAX_CHUNKS_PER_REQUEST",
    "MAX_INPUTS_PER_REQUEST",
    "MAX_TOKENS_PER_DOCUMENT",
    "MAX_TOKENS_PER_REQUEST",
    "VoyageContextualClient",
    "urllib_post",
]
