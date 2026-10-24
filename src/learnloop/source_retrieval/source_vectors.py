"""Source-block vectors follow extraction (tutor delivery fixes, 2026-10-13).

Dense retrieval ranks an extraction only when every embeddable block of it has
a ``source_block/text`` vector (``source_retrieval.dense``). Until now only the
explicit ``learnloop embeddings backfill --record-kind source_block`` command
bought them, so a new import or a re-extraction (a repair, another engine, a
future GLM-OCR pass) quietly left its source to keyword search.

Now a completed extraction queues the backfill of its source's current
extraction (``source_embedding_backfill`` ingest job) when both embedding
switches are on and ``embedding.backfill_sources_on_extract`` is true. The job
runs through the existing path (``ops.embedding_backfill.backfill_embeddings``:
the switches, the per-run caps, the advisory lock, ``embedding_backfill``
model-call receipts, content-addressed reuse), capped at
``embedding.source_backfill_max_cost_usd`` per run. With either switch off
nothing is queued and nothing is sent; a job queued before a switch went off
records ``disabled`` and sends nothing.

The obligation survives an interruption (Codex review F3): every path that
establishes an extraction, a fresh one or a completed one a retry reuses,
asks :func:`backfill_owed` and queues the job when the source's current
extraction is not fully covered and no live job already owes it. A completed
extraction whose worker died before queueing is therefore queued by the retry,
and a covered one queues nothing (no second purchase).

A job reports what happened (Codex review F4): ``complete`` (or nothing to
do: ``disabled``, ``no_extraction``) completes it; lock contention
(``busy``), a provider failure (``provider_failed``, ``unavailable``) or a
cancellation do not, and neither does a run over its money cap
(``over_budget``) or a vector-width conflict (``blocked``); the paid batches
before a failure stay saved, so a retry buys only the rest.

``source_coverage`` is the status note: per source, how many of its current
extraction's embeddable blocks have a vector, and whether dense retrieval is
effectively on (``learnloop doctor``).
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import closing
import math
from pathlib import Path
from typing import Any

from learnloop.ai.spend import SpendCaps
from learnloop.config.schema import LearnLoopConfig
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.repository import vault_repository
from learnloop.db.stores.source_block_fts import extraction_blocks, section_header_titles
from learnloop.ops.embedding_backfill import BackfillLockBusy, backfill_embeddings, estimated_tokens
from learnloop.source_retrieval.corpus import current_extractions
from learnloop.source_retrieval.dense import extraction_coverage
from learnloop.source_retrieval.recipes import (
    SOURCE_BLOCK_RECIPE,
    SOURCE_RETRIEVAL_RECIPES,
    block_record_id,
    embeddable,
    source_block_text,
)
from learnloop.vault.embedding_recipes import EmbeddingRecord
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths

#: The ingest job (and its batch's workflow) that embeds one source's blocks.
SOURCE_VECTORS_JOB = "source_embedding_backfill"
#: Job statuses that still owe their source's vectors (a queued or running job).
LIVE_JOB_STATUSES = frozenset({"queued", "running"})
BATCH_SIZE = 32
MAX_RETRIES = 2


def auto_backfill_reason(config: LearnLoopConfig) -> str | None:
    """None when a completed extraction queues its source's backfill, else why not."""

    embedding = config.embedding
    if not embedding.enabled:
        return "embedding.enabled is false"
    if not embedding.backfill_enabled:
        return "embedding.backfill_enabled is false"
    if not embedding.backfill_sources_on_extract:
        return "embedding.backfill_sources_on_extract is false"
    return None


def target_extraction(repository: Repository, extraction_id: str) -> tuple[str | None, str | None]:
    """``(source id, its current extraction)`` for a completed extraction.

    The current extraction is what retrieval reads (``corpus.current_extractions``):
    a new top-level extraction is current itself; a page repair composes onto
    its parent, which stays current."""

    run = repository.get_extraction_run(extraction_id) or {}
    revision = repository.get_source_revision(str(run.get("revision_id") or "")) or {}
    source_id = revision.get("source_id")
    if not source_id:
        return None, None
    return str(source_id), resolve_extraction_id(repository, str(source_id))


def backfill_owed(config: LearnLoopConfig, repository: Repository, extraction_id: str) -> tuple[str | None, str | None]:
    """``(current extraction, None)`` when a completed ``extraction_id`` owes
    its source a backfill, else ``(current extraction or None, why not)``.

    Owed when the automatic backfill is on, the source has a current
    extraction with embeddable blocks not all covered for ``embedding.model``,
    and no queued or running ``source_embedding_backfill`` job targets it.
    Read-only: no vector bytes read."""

    reason = auto_backfill_reason(config)
    if reason is not None:
        return None, reason
    _source_id, current = target_extraction(repository, extraction_id)
    if current is None:
        return None, "the source has no current extraction"
    sqlite_path = Path(repository.sqlite_path)
    with closing(connect(sqlite_path, read_only=True)) as connection:
        covered, blocks = extraction_coverage(connection, sqlite_path, config.embedding.model, current)
    if covered >= blocks:
        return current, "every embeddable block already has a vector"
    for job in repository.ingest_jobs_by_types((SOURCE_VECTORS_JOB,)):
        if job.get("status") not in LIVE_JOB_STATUSES:
            continue
        payload = job.get("payload") or {}
        queued_for = payload.get("current_extraction_id") or target_extraction(
            repository, str(payload.get("extraction_id") or ""))[1]
        if queued_for == current:
            return current, "a queued backfill already covers it"
    return current, None


def source_block_records(repository: Repository, extraction_id: str) -> list[EmbeddingRecord]:
    """The ``source_block/text`` records of one extraction (the recipe's texts and hashes)."""

    recipe = SOURCE_RETRIEVAL_RECIPES[SOURCE_BLOCK_RECIPE]
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        titles = section_header_titles(connection, extraction_id)
        return [recipe.record(block_record_id(block.extraction_id, block.span_id), source_block_text(block, titles))
                for block in extraction_blocks(connection, extraction_id) if embeddable(block)]


def backfill_caps(config: LearnLoopConfig, records: list[EmbeddingRecord], batch_size: int = BATCH_SIZE) -> SpendCaps:
    """Caps sized to this extraction (every record, its batches, a retry of the
    largest), the money bounded by ``embedding.source_backfill_max_cost_usd``."""

    tokens = [estimated_tokens(record.text) for record in records]
    largest = max((sum(tokens[start:start + batch_size]) for start in range(0, len(tokens), batch_size)), default=0)
    return SpendCaps(
        max_candidates=len(records), max_pairs=0, max_retries=MAX_RETRIES,
        max_calls=math.ceil(len(records) / batch_size) + MAX_RETRIES,
        max_total_tokens=sum(tokens) + MAX_RETRIES * largest,
        max_estimated_usd=config.embedding.source_backfill_max_cost_usd,
    )


def backfill_source_vectors(
    loaded: LoadedVault,
    extraction_id: str,
    *,
    client_factory: Callable[[], Any] | None = None,
    cancelled: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Embed the current extraction of ``extraction_id``'s source (missing vectors only).

    Aggregate report only (counts, caps, charges, model): never block text."""

    repository = vault_repository(VaultPaths(loaded.root, loaded.config))
    source_id, current = target_extraction(repository, extraction_id)
    report: dict[str, Any] = {"extraction_id": extraction_id, "source_id": source_id,
                              "embedded_extraction_id": current}
    reason = auto_backfill_reason(loaded.config)
    if reason is not None:
        return {**report, "status": "disabled", "reason": reason}
    if current is None:
        return {**report, "status": "no_extraction", "reason": "the source has no current extraction"}
    records = source_block_records(repository, current)
    if not records:
        return {**report, "status": "complete", "records": 0, "embedded": 0}
    # An owner's estimate for a model without a published price (the same
    # model embeds the queries); unpriced, the backfill refuses and says so.
    price = loaded.config.source_retrieval.query_embedding_price_per_million
    try:
        result = backfill_embeddings(
            loaded, caps=backfill_caps(loaded.config, records, BATCH_SIZE), recipes=(SOURCE_BLOCK_RECIPE,),
            registry=SOURCE_RETRIEVAL_RECIPES, records=records, batch_size=BATCH_SIZE,
            price_per_million=price, cancelled=cancelled,
            client_factory=client_factory,
        )
    except BackfillLockBusy as exc:
        # Another backfill holds the vault's lock: nothing was sent; retry later.
        return {**report, "status": "busy", "reason": str(exc), "records": len(records)}
    except ValueError as exc:
        # The stored vectors have another width or model, or a record is past
        # the model's input: nothing was sent; the owner must resolve it.
        return {**report, "status": "blocked", "reason": str(exc), "records": len(records)}
    return {**report, **{key: result.get(key) for key in (
        "status", "reason", "model_id", "dimensions", "records", "cached", "reused_by_content", "pending",
        "embedded", "remaining", "estimate", "charged", "caps", "price_per_million", "price_source", "run_id",
        "error_type",
    ) if key in result}}


def source_coverage(vault: LoadedVault, repository: Repository) -> dict[str, Any]:
    """Per source: dense coverage of its current extraction, and whether dense
    retrieval is effectively on (the switches and at least one complete source)."""

    config = vault.config
    model_id = config.embedding.model
    sqlite_path = Path(repository.sqlite_path)
    sources: list[dict[str, Any]] = []
    with closing(connect(sqlite_path, read_only=True)) as connection:
        for extraction_id, extraction in sorted(current_extractions(repository).items(),
                                                key=lambda item: (item[1].title, item[0])):
            covered, blocks = extraction_coverage(connection, sqlite_path, model_id, extraction_id)
            status = ("empty" if not blocks else "complete" if covered == blocks
                      else "partial" if covered else "none")
            sources.append({"source_id": extraction.source_id, "title": extraction.title,
                            "extraction_id": extraction_id, "reader_enabled": extraction.reader_enabled,
                            "blocks": blocks, "covered": covered, "status": status})
    switches = {
        "embedding.enabled": config.embedding.enabled,
        "source_retrieval.enabled": config.source_retrieval.enabled,
        "source_retrieval.dense": config.source_retrieval.dense,
    }
    off = [name for name, value in switches.items() if not value]
    complete = sum(1 for source in sources if source["status"] == "complete")
    embeddable_sources = sum(1 for source in sources if source["status"] != "empty")
    if off:
        effective, reason = False, ", ".join(off) + " off: retrieval ranks by keyword only"
    elif not complete:
        effective, reason = False, ("no source has a complete set of block vectors: run "
                                    "`learnloop embeddings backfill --record-kind source_block`")
    elif complete < embeddable_sources:
        effective, reason = True, (f"dense ranking covers {complete} of {embeddable_sources} sources; "
                                   "the others rank by keyword only")
    else:
        effective, reason = True, "every source has a complete set of block vectors"
    report = {
        "model_id": model_id, "effective": effective, "reason": reason, "switches": switches,
        "auto_backfill": auto_backfill_reason(config) or "on",
        "sources": sources,
        "totals": {"sources": len(sources), "complete": complete,
                   "blocks": sum(source["blocks"] for source in sources),
                   "covered": sum(source["covered"] for source in sources)},
    }
    from learnloop.source_retrieval.spaces import resolver_active

    if resolver_active(config):
        # Local contextual retrieval P1: the new spaces, only while one is on.
        report["source_spaces"] = source_spaces_note(vault, repository)
    return report


def source_spaces_note(vault: LoadedVault, repository: Repository) -> dict[str, Any]:
    """Doctor's per-space note: the local spaces' cache and canaries, the
    fallback's switch and coverage, and the feedback receipts' counts."""

    from learnloop.source_retrieval.fallback_space import coverage as fallback_coverage
    from learnloop.source_retrieval.fallback_space import fallback_reason
    from learnloop.source_retrieval.feedback import feedback_summary
    from learnloop.source_retrieval.local_index import coverage_report
    from learnloop.source_retrieval.windows import windows_by_extraction

    note: dict[str, Any] = {"local": coverage_report(vault, repository), "default": vault.config.embedding.source_space.default,
                            "learned_fusion": vault.config.embedding.source_space.learned_fusion,
                            "exploration": vault.config.embedding.source_space.exploration}
    reason = fallback_reason(vault.config)
    if reason is None:
        extractions = sorted(current_extractions(repository))
        windows = windows_by_extraction(vault, repository, extractions, ("grouped",))
        covered = fallback_coverage(vault, repository, extractions,
                                    lambda extraction_id: windows[(extraction_id, "grouped")])
        note["fallback"] = {"enabled": True, "covered_sources": len(covered), "sources": len(extractions)}
    else:
        note["fallback"] = {"enabled": False, "reason": reason}
    note["feedback"] = feedback_summary(repository)
    return note


def coverage_line(coverage: Mapping[str, Any]) -> str:
    """One status line for ``learnloop doctor``'s text output."""

    totals = coverage.get("totals") or {}
    state = "on" if coverage.get("effective") else "off"
    line = (f"Dense source retrieval: {state} ({coverage.get('reason')}); "
            f"{totals.get('complete', 0)} of {totals.get('sources', 0)} sources complete, "
            f"{totals.get('covered', 0)} of {totals.get('blocks', 0)} blocks embedded "
            f"({coverage.get('model_id')}); automatic backfill after extraction: {coverage.get('auto_backfill')}.")
    spaces = coverage.get("source_spaces")
    if not spaces:
        return line
    local = spaces.get("local") or {}
    if local.get("enabled"):
        parts = [f"{name} {row['covered_sources']}/{row['sources']} sources ({row['status']}, canaries "
                 f"{row['canaries']})" for name, row in sorted((local.get("spaces") or {}).items())]
        local_text = "; ".join(parts)
    else:
        local_text = f"off ({local.get('reason')})"
    fallback = spaces.get("fallback") or {}
    fallback_text = (f"{fallback.get('covered_sources')}/{fallback.get('sources')} sources" if fallback.get("enabled")
                     else f"off ({fallback.get('reason')})")
    weights = "learned" if spaces.get("learned_fusion") else f"seed (full weight on {spaces.get('default')})"
    return (line + f"\nSource spaces: local {local_text}; Voyage fallback {fallback_text}; serving weights {weights}; "
            f"exploration {'on' if spaces.get('exploration') else 'off'}.")


__all__ = [
    "LIVE_JOB_STATUSES",
    "SOURCE_VECTORS_JOB",
    "auto_backfill_reason",
    "backfill_caps",
    "backfill_owed",
    "backfill_source_vectors",
    "coverage_line",
    "source_block_records",
    "source_coverage",
    "target_extraction",
]
