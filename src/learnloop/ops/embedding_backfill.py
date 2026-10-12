"""Explicit, bounded embedding work. Never called by sync or rebuild."""
from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import closing, contextmanager
from dataclasses import asdict
import json
import math
from pathlib import Path
from typing import Any

from learnloop.ai.embedding import EmbeddingClient
from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable
from learnloop.ai.execution import content_key, observe_model_calls
from learnloop.ai.routing import ready_client_for_task
from learnloop.ai.spend import SpendBudget, SpendCaps, SpendEstimate, SpendLimitExceeded
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.embedding_vectors import get_vector, put_vector
from learnloop.ids import new_ulid
from learnloop.vault.embedding_recipes import EmbeddingRecord, select_recipes
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths


TASK_PREFIX = "retrieval-document"
# Spec §9.1's published estimate, not a promise of the provider's invoice.
PRICES_PER_MILLION = {"qwen/qwen3-embedding-8b": 0.01}


def estimated_tokens(text: str) -> int:
    """Conservative UTF-8 byte bound, including coarse-prefix/framing allowance."""
    return len(text.encode("utf-8")) + 128


def _identity(record: EmbeddingRecord, model_id: str) -> dict[str, str]:
    return {
        "record_kind": record.record_kind, "record_id": record.record_id,
        "field": record.field, "content_hash": record.content_hash,
        "model_id": model_id, "task_prefix": TASK_PREFIX,
    }


def _pending(
    sqlite_path: Path, records: list[EmbeddingRecord], model_id: str, dims: int,
) -> list[EmbeddingRecord]:
    if not sqlite_path.exists():
        return records
    with closing(connect(sqlite_path, read_only=True)) as connection:
        if not connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='embedding_vectors'"
        ).fetchone():
            return records
        dimensions = {
            row[0] for row in connection.execute(
                "SELECT DISTINCT dims FROM embedding_vectors WHERE model_id=?", (model_id,),
            )
        }
        if dimensions - {dims}:
            raise ValueError(
                "This model already has vectors at different dimensions; "
                "use its existing dimensions. Consumer truncation is query-time."
            )
        return [
            record for record in records
            if get_vector(connection, **_identity(record, model_id)) is None
        ]


def _estimate(records: list[EmbeddingRecord], calls: int, price: float | None) -> SpendEstimate:
    tokens = sum(estimated_tokens(record.text) for record in records)
    return SpendEstimate(
        candidates=len(records), calls=calls, total_tokens=tokens,
        estimated_usd=tokens * price / 1_000_000 if price is not None else (None if records else 0.0),
    )


@contextmanager
def _backfill_lock(root: Path) -> Iterator[None]:
    """Serialize backfills, not learner activity; death releases the OS lock."""
    try:
        import fcntl
    except ImportError as exc:  # pragma: no cover - app targets POSIX
        raise ValueError("Embedding backfill requires POSIX advisory locks") from exc
    path = root / ".learnloop" / "embedding-backfill.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another embedding backfill is running for this vault") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def backfill_embeddings(
    loaded: LoadedVault,
    *,
    caps: SpendCaps,
    dry_run: bool = False,
    recipes: tuple[str, ...] | None = None,
    batch_size: int = 32,
    price_per_million: float | None = None,
    cancelled: Callable[[], bool] | None = None,
    client_factory: Callable[[], EmbeddingClient] | None = None,
) -> dict[str, Any]:
    """Plan without data changes, or checkpoint successful batches before continuing.

    Caps apply to this invocation. A rerun plans only missing content hashes.
    Unknown prices require a finite owner-supplied estimate; an unlimited cost
    cap is deliberately not an escape hatch. A read-only WAL reader can create
    SQLite coordination sidecars; it must not use immutable mode and miss WAL
    commits when checking already-paid work.
    """
    if type(batch_size) is not int or not 1 <= batch_size <= 256:
        raise ValueError("batch_size must be between 1 and 256")
    if price_per_million is not None and (
        type(price_per_million) not in (int, float)
        or not math.isfinite(price_per_million) or price_per_million <= 0
    ):
        raise ValueError("price_per_million must be finite and positive")
    config = loaded.config.embedding
    sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
    model_id = config.model
    price = price_per_million if price_per_million is not None else PRICES_PER_MILLION.get(model_id)
    selected = select_recipes(recipes)
    records = [record for recipe in selected for record in recipe.records(loaded)]
    pending = _pending(sqlite_path, records, model_id, config.dimensions)
    budget = SpendBudget(caps, cancelled=cancelled)
    estimate = _estimate(pending, math.ceil(len(pending) / batch_size), price)
    report: dict[str, Any] = {
        "status": "dry_run" if dry_run else "pending", "dry_run": dry_run,
        "model_id": model_id, "dimensions": config.dimensions,
        "task_prefix": TASK_PREFIX, "recipes": [recipe.name for recipe in selected],
        "records": len(records), "cached": len(records) - len(pending),
        "pending": len(pending), "embedded": 0, "caps": caps.as_dict(),
        "estimate": asdict(estimate), "charged": asdict(budget.used),
        "price_per_million": price,
        "price_source": (
            "owner_override" if price_per_million is not None
            else "spec_estimate" if price is not None else "unknown"
        ),
        "embedding_enabled": config.enabled,
        "backfill_enabled": config.backfill_enabled,
        "manifest": {
            "algorithm_version": loaded.config.algorithms.algorithm_version,
            "config_hash": content_key(loaded.config.model_dump(mode="json")),
            "recipe_versions": {recipe.name: recipe.version for recipe in selected},
        },
    }
    try:
        budget.check(estimate)
    except AIInterrupted:
        report["status"] = "cancelled"
        return report
    except SpendLimitExceeded as exc:
        report.update(status="over_budget", reason=str(exc))
        return report
    if dry_run:
        return report
    if not config.enabled or not config.backfill_enabled:
        report.update(status="disabled", reason="Enable embedding.enabled and embedding.backfill_enabled explicitly.")
        return report
    if not pending:
        report["status"] = "complete"
        return report

    with _backfill_lock(loaded.root):
        # Another process may have completed between planning and lock acquisition.
        pending = _pending(sqlite_path, records, model_id, config.dimensions)
        report.update(pending=len(pending), cached=len(records) - len(pending))
        if not pending:
            report["status"] = "complete"
            return report
        if cancelled and cancelled():
            report["status"] = "cancelled"
            return report
        if client_factory is None:
            resolved = ready_client_for_task(loaded.root, loaded.config, "embedding")
            if resolved.client is None or not resolved.runtime.ready:
                report.update(status="unavailable", reason=resolved.runtime.message)
                return report
            client = resolved.client
        else:
            client = client_factory()
        if client.model_id != model_id or client.dims != config.dimensions:
            raise ValueError("Embedding client model/dimensions do not match the planned index")
        if "text" not in client.modalities:
            raise ValueError("The embedding client does not support canonical text")
        if any(estimated_tokens(record.text) > client.max_input_tokens for record in pending):
            raise ValueError("An embedding recipe exceeds the model input limit; no text was truncated or sent")
        repository = Repository(sqlite_path)
        run_id = new_ulid()
        report["run_id"] = run_id
        usage: dict[str, Any] = {}

        def observe(action: str, event: dict[str, Any]) -> None:
            if action == "start":
                # Keep the paid request interpretable after the command's
                # aggregate report is discarded. Caps remain top-level.
                declared = json.loads(event.get("budget_json") or "{}")
                declared["embedding"] = {
                    **report["manifest"],
                    "prompt_version": "embedding-v1",
                    "model_id": model_id, "dimensions": config.dimensions,
                    "task_prefix": TASK_PREFIX,
                    "price_per_million": price,
                    "price_source": report["price_source"],
                }
                event = {**event, "budget_json": json.dumps(declared, sort_keys=True)}
            repository.record_model_event(action, event, owner_kind="embedding_backfill", owner_id=run_id)
            if action == "finish":
                usage.update(event)

        try:
            with observe_model_calls(observe):
                for offset in range(0, len(pending), batch_size):
                    batch = pending[offset:offset + batch_size]
                    attempt = 0
                    while True:
                        request = _estimate(batch, 1, price)
                        if attempt:
                            request = SpendEstimate(
                                calls=1, retries=1, total_tokens=request.total_tokens,
                                estimated_usd=request.estimated_usd,
                            )
                        usage.clear()
                        try:
                            with budget.request(request) as charge:
                                try:
                                    vectors = client.embed([record.text for record in batch], TASK_PREFIX)
                                finally:
                                    actual_tokens = usage.get("input_tokens")
                                    actual_cost = usage.get("cost")
                                    if actual_tokens is not None and price is not None:
                                        actual_cost = max(actual_cost or 0, actual_tokens * price / 1_000_000)
                                    charge.reconcile(total_tokens=actual_tokens, estimated_usd=actual_cost)
                        except AIInterrupted:
                            raise
                        except AIProviderUnavailable:
                            if budget.used.retries >= caps.max_retries:
                                raise
                            attempt += 1
                            continue
                        if len(vectors) != len(batch):
                            raise ValueError("Embedding provider returned the wrong number of vectors")
                        # Persist the whole paid batch even if cancellation arrived
                        # during the request. Never hold a DB transaction over I/O.
                        with repository.connection() as connection:
                            for record, vector in zip(batch, vectors, strict=True):
                                if len(vector) != client.dims:
                                    raise ValueError("Embedding provider returned the wrong vector dimensions")
                                put_vector(connection, **_identity(record, model_id), vector=vector)
                        report["embedded"] += len(batch)
                        break
            report["status"] = "complete"
        except (AIInterrupted, KeyboardInterrupt):
            report["status"] = "cancelled"
        except SpendLimitExceeded as exc:
            report.update(status="over_budget", reason=str(exc))
        except AIProviderUnavailable as exc:
            # Aggregate report must not echo provider errors that can contain
            # request/learner text or credentials.
            report.update(status="provider_failed", error_type=type(exc).__name__)
        finally:
            report["charged"] = asdict(budget.used)
            report["remaining"] = len(pending) - report["embedded"]
    return report
