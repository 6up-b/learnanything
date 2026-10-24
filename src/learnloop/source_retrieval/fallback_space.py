"""The hosted Voyage fallback space (spec_local_contextual_retrieval_v1 §8; P1b).

A separate index in a separate space: ``voyage-context-4`` grouped windows by
the shared window rule (``source_retrieval.windows``), queried with itself
(``input_type="query"``). Its vectors are paid inputs, so they live in
``embedding_vectors`` (WORKFLOW) with ``model_id`` = the space id and
``content_hash`` = the window key: reuse by content therefore only ever
matches the same window, and no Qwen reader ever sees them (other model id).

Money (T1's rules for an explicit opt-in embedding route):

* nothing is sent while ``embedding.enabled`` or ``embedding.fallback.enabled``
  is false, and the profile must be a ``voyage_contextual_embedding`` profile
  (every AI task refuses that type, so no route reaches it);
* every request is admitted against caps before it is sent and leaves a
  ``model_call_receipts`` row (owner kind ``embedding_backfill`` or
  ``source_query_embedding``); a run is capped at
  ``embedding.fallback.max_cost_usd_per_run`` (keep) and admitted at the full
  ``price_per_million`` (the free tier is never assumed);
* a query that pays is said so in the result's ``space_selection``.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import closing, nullcontext
from dataclasses import asdict
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from learnloop.ai.embedding import embedding_request_timeout
from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable
from learnloop.ai.execution import observe_model_calls
from learnloop.ai.spend import SpendBudget, SpendCaps, SpendEstimate, SpendLimitExceeded
from learnloop.config.schema import VOYAGE_CONTEXTUAL_PROFILE_TYPE, LearnLoopConfig
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.embedding_vectors import get_vector, put_vector
from learnloop.local_embeddings.identity import hosted_space_pins, space_id as make_space_id
from learnloop.source_retrieval.queries import QUERY_EMBEDDING_CAPS
from learnloop.source_retrieval.recipes import (
    DOC_TASK_PREFIX,
    SOURCE_BLOCK_FIELD,
    SOURCE_BLOCK_KIND,
    block_record_id,
)
from learnloop.source_retrieval.windows import (
    WINDOW_RULE,
    Window,
    expected_keys,
    extraction_windows,
    mean_vector,
    window_key,
)
from learnloop.text_canon import collapse_whitespace
from learnloop.vault.models import LoadedVault

NAME = "voyage"
QUERY_RECORD_KIND = "source_query"
QUERY_TASK_PREFIX = "retrieval-query"
#: The backfill job (its own ingest batch, like ``source_embedding_backfill``).
FALLBACK_JOB = "source_fallback_backfill"
#: keep (provider limit): a request's documents (windows), chunks and token bound.
MAX_WINDOWS_PER_REQUEST = 1_000
MAX_CHUNKS_PER_REQUEST = 16_000
MAX_TOKENS_PER_REQUEST = 120_000
MAX_RETRIES = 2


def token_upper_bound(text: str) -> int:
    """UTF-8 bytes plus a special-token allowance: no tokenizer emits more (E0's bound)."""

    return len(text.encode("utf-8")) + 8


def fallback_reason(config: LearnLoopConfig) -> str | None:
    """None when the fallback space may be used, else why not (nothing sent)."""

    embedding = config.embedding
    if not embedding.fallback.enabled:
        return "embedding.fallback.enabled is false"
    if not embedding.enabled:
        return "embedding.enabled is false"
    if not config.source_retrieval.dense:
        return "source_retrieval.dense is false"
    profile = config.ai.providers.get(embedding.fallback.provider)
    if profile is None:
        return f"embedding.fallback.provider names no profile ({embedding.fallback.provider!r})"
    if profile.type.strip().lower() != VOYAGE_CONTEXTUAL_PROFILE_TYPE:
        return f"embedding.fallback.provider must be a {VOYAGE_CONTEXTUAL_PROFILE_TYPE} profile"
    return None


def fallback_space(config: LearnLoopConfig) -> tuple[str, dict[str, Any]]:
    """``(space_id, pins)`` of the configured fallback profile (grouped windows)."""

    profile = config.ai.providers.get(config.embedding.fallback.provider)
    model = getattr(profile, "model", None) or "voyage-context-4"
    dims = int(getattr(profile, "dimensions", 1024) or 1024)
    space_pins = hosted_space_pins(provider="voyage", model=model, dims=dims, variant="grouped",
                                   window_rule=WINDOW_RULE)
    return make_space_id(space_pins), space_pins


def fallback_client(vault: LoadedVault) -> tuple[Any | None, str | None]:
    """The fallback space's client, or ``(None, why not)``; nothing is sent here."""

    reason = fallback_reason(vault.config)
    if reason is not None:
        return None, reason
    from learnloop.ai.client import make_ai_provider_client_from_profile
    from learnloop.ai.runtime import check_ai_runtime

    name = vault.config.embedding.fallback.provider
    runtime = check_ai_runtime(vault.root, vault.config, provider_name=name)
    if runtime.status != "ready":
        return None, runtime.message
    profile = vault.config.ai.providers[name]
    if profile.timeout_seconds is None:
        profile = profile.model_copy(update={"timeout_seconds": vault.config.ai.timeout_seconds})
    try:
        return make_ai_provider_client_from_profile(name, profile, vault.root), None
    except AIProviderUnavailable as exc:
        return None, str(exc)


# -- coverage and the index ---------------------------------------------------------------
def window_vectors(connection, space_id: str, extraction_id: str,
                   keys: Mapping[str, Sequence[tuple[str, int]]]) -> dict[str, np.ndarray]:
    """``{span_id: vector}`` for the blocks whose every key is stored (a split
    block's parts are averaged, weighted by their tokens: ``split_mean``); a
    block missing any part is left out."""

    out: dict[str, np.ndarray] = {}
    for span_id, span_keys in keys.items():
        parts = []
        for key, _weight in span_keys:
            vector = get_vector(connection, record_kind=SOURCE_BLOCK_KIND,
                                record_id=block_record_id(extraction_id, span_id), field=SOURCE_BLOCK_FIELD,
                                content_hash=key, model_id=space_id, task_prefix=DOC_TASK_PREFIX)
            if vector is None:
                break
            parts.append(vector)
        else:
            if parts:
                out[span_id] = (parts[0] if len(parts) == 1 else
                                np.asarray(mean_vector(parts, [weight for _key, weight in span_keys])))
    return out


# -- the backfill -------------------------------------------------------------------------
def _batches(windows: Sequence[Window]) -> list[list[Window]]:
    batches: list[list[Window]] = []
    current: list[Window] = []
    tokens = chunks = 0
    for window in windows:
        size = sum(token_upper_bound(text) for text in window.chunks)
        if current and (tokens + size > MAX_TOKENS_PER_REQUEST or chunks + len(window.chunks) > MAX_CHUNKS_PER_REQUEST
                        or len(current) + 1 > MAX_WINDOWS_PER_REQUEST):
            batches.append(current)
            current, tokens, chunks = [], 0, 0
        current.append(window)
        tokens += size
        chunks += len(window.chunks)
    if current:
        batches.append(current)
    return batches


def backfill_caps(config: LearnLoopConfig, batches: Sequence[Sequence[Window]]) -> SpendCaps:
    sizes = [sum(token_upper_bound(text) for window in batch for text in window.chunks) for batch in batches]
    return SpendCaps(max_candidates=sum(len(window.chunks) for batch in batches for window in batch), max_pairs=0,
                     max_retries=MAX_RETRIES, max_calls=len(batches) + MAX_RETRIES,
                     max_total_tokens=sum(sizes) + MAX_RETRIES * max(sizes, default=0),
                     max_estimated_usd=config.embedding.fallback.max_cost_usd_per_run)


def backfill_fallback_vectors(vault: LoadedVault, repository: Repository, extraction_id: str, *,
                              client: Any | None = None, cancelled: Callable[[], bool] | None = None,
                              dry_run: bool = False) -> dict[str, Any]:
    """Embed the windows of ``extraction_id`` the fallback space lacks (aggregate report only)."""

    report: dict[str, Any] = {"extraction_id": extraction_id, "space": NAME}
    reason = fallback_reason(vault.config)
    if reason is not None:
        return {**report, "status": "disabled", "reason": reason}
    if not vault.config.embedding.fallback.maintain_index:
        return {**report, "status": "disabled", "reason": "embedding.fallback.maintain_index is false"}
    space, _pins = fallback_space(vault.config)
    report["space_id"] = space
    windows = extraction_windows(vault, repository, extraction_id, "grouped")
    keys = expected_keys(space, windows)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        have = window_vectors(connection, space, extraction_id, keys)
    missing = [window for window in windows if any(span not in have for span in window.span_ids)]
    batches = _batches(missing)
    price = float(vault.config.embedding.fallback.price_per_million)
    tokens = sum(token_upper_bound(text) for window in missing for text in window.chunks)
    report.update(windows=len(windows), missing_windows=len(missing), requests=len(batches),
                  estimate={"tokens_upper_bound": tokens, "usd_upper_bound": round(tokens * price / 1_000_000, 6)},
                  price_per_million=price, price_source="Voyage published price, admitted in full (free tier never assumed)")
    if dry_run:
        return {**report, "status": "dry_run"}
    if not missing:
        return {**report, "status": "complete", "embedded": 0}
    if client is None:
        client, why = fallback_client(vault)
        if client is None:
            return {**report, "status": "unavailable", "reason": why}
    budget = SpendBudget(backfill_caps(vault.config, batches), cancelled=cancelled)

    def observe(action: str, event: dict[str, Any]) -> None:
        if action == "start" and event.get("parent_call_id") is None:
            declared = json.loads(event.get("budget_json") or "{}")
            declared["fallback_space"] = {"task": "embedding", "billing": "metered", "space_id": space,
                                          "price_per_million": price, "record_kind": SOURCE_BLOCK_KIND}
            event = {**event, "budget_json": json.dumps(declared, sort_keys=True)}
        repository.record_model_event(action, event, owner_kind="embedding_backfill", owner_id=extraction_id)

    embedded = 0
    status = "complete"
    try:
        with observe_model_calls(observe):
            for batch in batches:
                if cancelled is not None and cancelled():
                    raise AIInterrupted("Fallback backfill cancelled")
                size = sum(token_upper_bound(text) for window in batch for text in window.chunks)
                estimate = SpendEstimate(candidates=sum(len(window.chunks) for window in batch), calls=1,
                                         total_tokens=size, estimated_usd=size * price / 1_000_000)
                with budget.request(estimate):
                    rows = client.embed_documents([window.chunks for window in batch])
                if len(rows) != len(batch) or any(len(row) != len(window.chunks)
                                                  for row, window in zip(rows, batch, strict=True)):
                    raise ValueError("the fallback provider returned the wrong number of vectors")
                with repository.connection() as connection:
                    for window, vectors in zip(batch, rows, strict=True):
                        for member, vector in zip(window.members, vectors, strict=True):
                            put_vector(connection, record_kind=SOURCE_BLOCK_KIND,
                                       record_id=block_record_id(extraction_id, member.span_id),
                                       field=SOURCE_BLOCK_FIELD, content_hash=window_key(space, window, member.span_id),
                                       model_id=space, task_prefix=DOC_TASK_PREFIX, vector=vector)
                embedded += len(batch)
    except (AIInterrupted, KeyboardInterrupt):
        status = "cancelled"
    except SpendLimitExceeded as exc:
        status, report["reason"] = "over_budget", str(exc)
    except AIProviderUnavailable as exc:
        status, report["error_type"] = "provider_failed", getattr(exc, "provider_error", type(exc).__name__)
    except ValueError as exc:
        status, report["reason"] = "invalid", str(exc)
    return {**report, "status": status, "embedded_windows": embedded, "remaining_windows": len(missing) - embedded,
            "charged": asdict(budget.used)}


# -- queries -------------------------------------------------------------------------------
def _query_hash(text: str) -> str:
    payload = json.dumps([QUERY_RECORD_KIND, "text", 1, collapse_whitespace(text)], ensure_ascii=False,
                         separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def query_vectors(vault: LoadedVault, repository: Repository, texts: Mapping[str, str], *, client: Any | None,
                  owner_id: str = "", deadline: float | None = None) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Query vectors in the fallback space (cached by text; one capped, paid request for the rest)."""

    space, _pins = fallback_space(vault.config)
    wanted = {key: collapse_whitespace(text)[:2000] for key, text in texts.items() if text.strip()}
    found: dict[str, np.ndarray] = {}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        for key, text in wanted.items():
            vector = get_vector(connection, record_kind=QUERY_RECORD_KIND, record_id=_query_hash(text),
                                field="text", content_hash=_query_hash(text), model_id=space,
                                task_prefix=QUERY_TASK_PREFIX)
            if vector is not None:
                found[key] = vector
    pending = [(key, text) for key, text in sorted(wanted.items()) if key not in found]
    if not pending:
        return found, {"status": "cached", "paid": False, "cached": len(found)}
    if client is None:
        client, why = fallback_client(vault)
        if client is None:
            return found, {"status": "unavailable", "reason": why, "paid": False}
    price = float(vault.config.embedding.fallback.price_per_million)
    size = sum(token_upper_bound(text) for _key, text in pending)
    # The Qwen query path's caps (one request, at most a cent): the same query
    # time box and money bound for whichever space answers.
    budget = SpendBudget(QUERY_EMBEDDING_CAPS)

    def observe(action: str, event: dict[str, Any]) -> None:
        repository.record_model_event(action, event, owner_kind="source_query_embedding", owner_id=owner_id)

    remaining = None if deadline is None else deadline - time.monotonic()
    if remaining is not None and remaining <= 0:
        return found, {"status": "timed_out", "reason": "the retrieval time box ran out", "paid": False}
    try:
        with observe_model_calls(observe), (nullcontext() if remaining is None
                                             else embedding_request_timeout(remaining)):
            with budget.request(SpendEstimate(candidates=len(pending), calls=1, total_tokens=size,
                                              estimated_usd=size * price / 1_000_000)):
                vectors = client.embed_queries([text for _key, text in pending])
        if len(vectors) != len(pending):
            raise ValueError("the fallback provider returned the wrong number of query vectors")
        with repository.connection() as connection:
            for (key, text), vector in zip(pending, vectors, strict=True):
                put_vector(connection, record_kind=QUERY_RECORD_KIND, record_id=_query_hash(text), field="text",
                           content_hash=_query_hash(text), model_id=space, task_prefix=QUERY_TASK_PREFIX,
                           vector=vector)
                found[key] = np.asarray(vector, dtype="<f2").astype(np.float64)
    except SpendLimitExceeded as exc:
        return found, {"status": "over_budget", "reason": str(exc), "paid": False}
    except AIProviderUnavailable as exc:
        timed_out = getattr(exc, "provider_error", None) == "APITimeoutError"
        return found, {"status": "timed_out" if timed_out else "provider_failed", "paid": True,
                       "charged": asdict(budget.used)}
    except ValueError as exc:
        return found, {"status": "invalid", "reason": str(exc), "paid": True}
    return found, {"status": "embedded", "paid": True, "embedded": len(pending), "cached": len(found) - len(pending),
                   "charged": asdict(budget.used)}


def coverage(vault: LoadedVault, repository: Repository, extraction_ids: Sequence[str],
             windows_for: Callable[[str], Sequence[Window]]) -> dict[str, dict[str, np.ndarray]]:
    """``{extraction_id: {span_id: vector}}`` for the extractions every block of
    which the fallback space covers under the current windows (others left out)."""

    space, _pins = fallback_space(vault.config)
    covered: dict[str, dict[str, np.ndarray]] = {}
    sqlite_path = Path(repository.sqlite_path)
    with closing(connect(sqlite_path, read_only=True)) as connection:
        for extraction_id in extraction_ids:
            windows = windows_for(extraction_id)
            keys = expected_keys(space, windows)
            if not keys:
                continue
            vectors = window_vectors(connection, space, extraction_id, keys)
            if len(vectors) == len(keys):
                covered[extraction_id] = vectors
    return covered


__all__ = [
    "FALLBACK_JOB",
    "NAME",
    "backfill_caps",
    "backfill_fallback_vectors",
    "coverage",
    "fallback_client",
    "fallback_reason",
    "fallback_space",
    "query_vectors",
    "window_vectors",
]
