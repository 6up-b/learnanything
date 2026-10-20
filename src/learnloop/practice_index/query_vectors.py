"""Query embeddings for the practice index: cached, capped, and opt-in.

Queries are embedded with the ``retrieval-query`` task prefix through the Phase 1
embedding route, which never falls back to a chat provider and is off while
``embedding.enabled`` is false. Each vector is cached in ``embedding_vectors``
(record kind ``practice_query``) so an evaluation rerun or a repeated request
never pays twice, and replay never embeds anything.
"""
from __future__ import annotations

from collections.abc import Callable
from contextlib import closing, nullcontext
from dataclasses import asdict, dataclass, field
import hashlib
import json
import time
from typing import Any

import numpy as np

from learnloop.ai.embedding import EmbeddingClient, embedding_request_timeout
from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable
from learnloop.ai.execution import observe_model_calls
from learnloop.ai.routing import ready_client_for_task
from learnloop.ai.spend import SpendBudget, SpendEstimate, SpendLimitExceeded
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.embedding_vectors import get_vector, put_vector
from learnloop.ops.embedding_backfill import PRICES_PER_MILLION, estimated_tokens
from learnloop.text_canon import collapse_whitespace
from learnloop.vault.models import LoadedVault


QUERY_RECORD_KIND = "practice_query"
QUERY_FIELD = "text"
QUERY_TASK_PREFIX = "retrieval-query"
BATCH_SIZE = 32


def normalize_query(text: str) -> str:
    # The one whitespace normalisation, shared with the bound Reader's guard
    # and delivery plan (``learnloop.text_canon``, RW1c fix round 11), so the
    # search, the rewrite and the guard cannot drift apart.
    return collapse_whitespace(text)


def query_id(text: str) -> str:
    return "pq_" + hashlib.sha256(normalize_query(text).encode("utf-8")).hexdigest()[:32]


def _content_hash(text: str, record_kind: str = QUERY_RECORD_KIND) -> str:
    payload = json.dumps([record_kind, QUERY_FIELD, 1, normalize_query(text)],
                         ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _identity(record_id: str, text: str, model_id: str,
              record_kind: str = QUERY_RECORD_KIND) -> dict[str, str]:
    return {"record_kind": record_kind, "record_id": record_id, "field": QUERY_FIELD,
            "content_hash": _content_hash(text, record_kind), "model_id": model_id,
            "task_prefix": QUERY_TASK_PREFIX}


@dataclass
class QueryVectors:
    vectors: dict[str, np.ndarray] = field(default_factory=dict)
    status: str = "unused"
    reason: str | None = None
    cached: int = 0
    embedded: int = 0
    charged: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        values = asdict(self)
        values.pop("vectors")
        return values


def embedding_ready(vault: LoadedVault, embedder: EmbeddingClient | None) -> str | None:
    """Why query embeddings cannot be used, or None."""
    if embedder is None and not vault.config.embedding.enabled:
        return "embeddings are disabled (embedding.enabled = false)"
    return None


def cached_query_vectors(repository: Repository, model_id: str,
                         queries: dict[str, str], *,
                         record_kind: str = QUERY_RECORD_KIND) -> dict[str, np.ndarray]:
    """Stored query vectors; ``record_kind`` keeps another consumer's queries apart
    (Slice 2 T6 uses ``source_query``)."""
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        found = {}
        for record_id, text in queries.items():
            vector = get_vector(connection, **_identity(record_id, text, model_id, record_kind))
            if vector is not None:
                found[record_id] = vector
        return found


def query_embedding_price(model_id: str, price_per_million: float | None) -> tuple[float | None, str]:
    """The owner's explicit price, else the published estimate; unknown is None."""
    if price_per_million is not None:
        return price_per_million, "owner_override"
    price = PRICES_PER_MILLION.get(model_id)
    return price, "spec_estimate" if price is not None else "unknown"


def plan_query_embedding(vault: LoadedVault, repository: Repository,
                         queries: dict[str, str], *,
                         price_per_million: float | None = None) -> dict[str, Any]:
    """Dry-run view: how many query texts would be embedded, and at what cost."""
    model_id = vault.config.embedding.model
    pending = {k: v for k, v in queries.items()
               if k not in cached_query_vectors(repository, model_id, queries)}
    tokens = sum(estimated_tokens(text) for text in pending.values())
    price, source = query_embedding_price(model_id, price_per_million)
    return {
        "model_id": model_id, "queries": len(queries), "pending": len(pending),
        "calls": -(-len(pending) // BATCH_SIZE), "estimated_tokens": tokens,
        "estimated_usd": (tokens * price / 1_000_000 if price is not None
                          else (0.0 if not pending else None)),
        "price_per_million": price, "price_source": source,
        "embedding_enabled": vault.config.embedding.enabled,
    }


def embed_queries(
    vault: LoadedVault,
    repository: Repository,
    queries: dict[str, str],
    *,
    budget: SpendBudget,
    embedder: EmbeddingClient | None = None,
    price_per_million: float | None = None,
    owner_kind: str = "practice_query_embedding",
    owner_id: str = "",
    cancelled: Callable[[], bool] | None = None,
    record_kind: str = QUERY_RECORD_KIND,
    deadline: float | None = None,
) -> QueryVectors:
    """Vectors for ``{record_id: text}``, embedding only what is not cached.

    ``record_kind`` names the consumer whose queries these are (default the
    practice index's ``practice_query``). ``deadline`` (``time.monotonic()``)
    time-boxes the requests: none starts after it, and each one carries the
    time left as its request timeout (status ``timed_out`` either way)."""
    result = QueryVectors()
    reason = embedding_ready(vault, embedder)
    if reason is not None:
        result.status, result.reason = "unavailable", reason
        return result
    model_id = vault.config.embedding.model
    result.vectors = cached_query_vectors(repository, model_id, queries, record_kind=record_kind)
    result.cached = len(result.vectors)
    pending = [(k, v) for k, v in sorted(queries.items()) if k not in result.vectors]
    if not pending:
        result.status = "cached"
        return result
    price, _source = query_embedding_price(model_id, price_per_million)
    if price is None:
        result.status, result.reason = "skipped", (
            f"unknown embedding price for {model_id}; set an explicit price "
            "(practice_index.query_embedding_price_per_million, or --embedding-price-per-million)")
        return result
    client = embedder
    if client is None:
        resolved = ready_client_for_task(vault.root, vault.config, "embedding")
        if resolved.client is None or not resolved.runtime.ready:
            result.status, result.reason = "unavailable", resolved.runtime.message
            return result
        client = resolved.client
    if client.model_id != model_id or client.dims != vault.config.embedding.dimensions:
        result.status, result.reason = "unavailable", "embedding client does not match embedding.model/dimensions"
        return result

    def observe(action: str, event: dict[str, Any]) -> None:
        if action == "start" and event.get("parent_call_id") is None:
            declared = json.loads(event.get("budget_json") or "{}")
            declared["practice_index"] = {"task": "embedding", "billing": "metered",
                                          "task_prefix": QUERY_TASK_PREFIX, "model_id": model_id,
                                          "price_per_million": price, "record_kind": record_kind}
            event = {**event, "budget_json": json.dumps(declared, sort_keys=True)}
        repository.record_model_event(action, event, owner_kind=owner_kind, owner_id=owner_id)

    try:
        with observe_model_calls(observe):
            for start in range(0, len(pending), BATCH_SIZE):
                if cancelled is not None and cancelled():
                    raise AIInterrupted("Query embedding cancelled")
                batch = pending[start:start + BATCH_SIZE]
                tokens = sum(estimated_tokens(text) for _, text in batch)
                if any(estimated_tokens(text) > client.max_input_tokens for _, text in batch):
                    raise ValueError("A query exceeds the embedding input limit")
                estimate = SpendEstimate(candidates=len(batch), calls=1, total_tokens=tokens,
                                         estimated_usd=tokens * price / 1_000_000)
                remaining = None if deadline is None else deadline - time.monotonic()
                if remaining is not None and remaining <= 0:
                    raise TimeoutError("the time box ran out before the query embedding")
                bounded = nullcontext() if remaining is None else embedding_request_timeout(remaining)
                with budget.request(estimate), bounded:
                    vectors = client.embed([text for _, text in batch], QUERY_TASK_PREFIX)
                if len(vectors) != len(batch) or any(len(v) != client.dims for v in vectors):
                    raise ValueError("Embedding provider returned the wrong vector count or width")
                with repository.connection() as connection:
                    for (record_id, text), vector in zip(batch, vectors, strict=True):
                        put_vector(connection, **_identity(record_id, text, model_id, record_kind),
                                   vector=vector)
                        # The stored float16 view, so a first use ranks exactly like
                        # every later cached use.
                        result.vectors[record_id] = np.asarray(vector, dtype="<f2").astype(np.float64)
                result.embedded += len(batch)
        result.status = "embedded"
    except (AIInterrupted, KeyboardInterrupt):
        result.status = "cancelled"
    except SpendLimitExceeded as exc:
        result.status, result.reason = "over_budget", str(exc)
    except TimeoutError as exc:
        result.status, result.reason = "timed_out", str(exc)
    except AIProviderUnavailable as exc:
        if getattr(exc, "provider_error", None) == "APITimeoutError":
            result.status, result.reason = "timed_out", "the embedding request ran out of time"
        else:
            result.status, result.reason = "provider_failed", type(exc).__name__
    except ValueError as exc:
        result.status, result.reason = "invalid", str(exc)
    result.charged = asdict(budget.used)
    return result


__all__ = [
    "QUERY_FIELD",
    "QUERY_RECORD_KIND",
    "QUERY_TASK_PREFIX",
    "QueryVectors",
    "cached_query_vectors",
    "embed_queries",
    "embedding_ready",
    "normalize_query",
    "plan_query_embedding",
    "query_embedding_price",
    "query_id",
]
