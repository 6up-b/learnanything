"""Retrieval's derived-index job types: the source embedding backfill, the local index, the fallback backfill and
the coverage pass after an extraction, and the obligations a completed extraction queues for them.

They run on the ingest host (:mod:`learnloop.content.pipeline.jobs`), which holds the lease and the lock they need;
what each type is (its handler and its flags) is its row in :mod:`learnloop.content.pipeline.job_types`.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping

from learnloop.content.pipeline.job_contracts import IngestRunnerError, JobCancelled, JobSpec

if TYPE_CHECKING:
    from learnloop.content.pipeline.runner import JobContext


def queue_source_vectors(ctx: JobContext, extraction_id: str, *, title: str | None = None) -> str | None:
    """Queue the source-block embedding backfill a completed extraction owes.

    Tutor delivery fixes (2026-10-13): every path that establishes an
    extraction run (an import, a page repair, any extractor; a fresh run or a
    completed one a retry reuses) calls this, so a re-extracted source does
    not silently fall back to keyword search. Acts only when
    ``embedding.enabled``, ``embedding.backfill_enabled`` and
    ``embedding.backfill_sources_on_extract`` are on, and only when the
    source's current extraction is not fully covered and no live job owes it
    (``source_vectors.backfill_owed``), so a retry never buys twice. Queued as
    its own batch (``source_embedding_backfill``): the import never waits on
    the embedding and its failure never fails the import.

    Codex review F3: an obligation that cannot be queued is not dropped. The
    job fails retryably (``source_vectors_not_queued``) and its retry, which
    reuses the completed extraction, queues it. Returns the batch id, or None."""

    from learnloop.config.loader import load_config
    from learnloop.source_retrieval.source_vectors import SOURCE_VECTORS_JOB, auto_backfill_reason, backfill_owed

    try:
        config = load_config(Path(ctx.vault_root) / "learnloop.toml", load_environment=False)
    except Exception:  # noqa: BLE001 - no readable config: nothing to queue
        return None
    queue_contextual_indexes(ctx, config, extraction_id, title=title)
    queue_coverage_on_extract(ctx, config, extraction_id)
    if auto_backfill_reason(config) is not None:
        return None
    try:
        current, reason = backfill_owed(config, ctx.repo, extraction_id)
        if reason is not None:
            return None
        payload: dict[str, Any] = {"extraction_id": extraction_id, "current_extraction_id": current}
        if title:
            payload["title"] = title
        return ctx.enqueue_batch(SOURCE_VECTORS_JOB, [JobSpec(SOURCE_VECTORS_JOB, payload)])
    except JobCancelled:
        raise
    except Exception as exc:  # noqa: BLE001 - classified: the obligation must not be lost silently
        raise IngestRunnerError(
            "The source was extracted, but indexing it for meaning search could not be queued. "
            "Retry: the extraction is reused, not repeated.",
            code="source_vectors_not_queued",
            details={"extraction_id": extraction_id, "error_type": type(exc).__name__},
            retryable=True,
        ) from exc


def queue_coverage_on_extract(ctx: JobContext, config: Any, extraction_id: str) -> str | None:
    """Deliverable curriculum C0b (spec §6.3): a completed extraction queues one
    ``curriculum_coverage_on_extract`` job, which judges the already-covered LOs again
    so the new reading's sections join their coverage (quiet: the plan only).

    Only while ``curriculum.enabled`` and ``curriculum.coverage_on_extract`` are on,
    and only when some LO is covered. **Coalesced only with a job still queued** (Codex
    review F7): a queued job reads the library when it starts, so it sees this
    extraction; a running one read it already, so an extraction completed while it runs
    queues one more pass (at most one queued and one running). One job judges every
    covered LO, coalesced per LO. Its failure never fails the import: coverage is
    display and retrieval context, and the next extraction or a pressed check judges
    again. Returns the batch id, or None."""

    from learnloop.source_retrieval.section_coverage import ON_EXTRACT_JOB, covered_learning_objects, on_extract_reason

    if on_extract_reason(config) is not None:
        return None
    try:
        if not covered_learning_objects(ctx.repo):
            return None
        if any(job.get("status") == "queued" for job in ctx.repo.ingest_jobs_by_types((ON_EXTRACT_JOB,))):
            return None
        return ctx.enqueue_batch(ON_EXTRACT_JOB, [JobSpec(ON_EXTRACT_JOB, {"extraction_id": extraction_id})])
    except JobCancelled:
        raise
    except Exception:  # noqa: BLE001 - coverage is context: the import stands, the next one queues again
        logging.getLogger(__name__).warning("the coverage job for %s could not be queued", extraction_id,
                                            exc_info=True)
        return None


def queue_contextual_indexes(ctx: JobContext, config: Any, extraction_id: str, *, title: str | None = None) -> list[str]:
    """Local contextual retrieval P1a/P1b (spec §4.1, §8): a completed
    extraction queues the local index job and the Voyage fallback backfill.

    Each acts only while its switch is on (``embedding.local.enabled`` with
    ``index_on_extract``; the fallback's ``enabled`` with ``maintain_index``
    and ``embedding.enabled``): with both off, the defaults, nothing is queued.
    One live local index job indexes everything owed, so a second is not
    queued; a fallback backfill is queued once per current extraction.

    Codex review F4: an obligation that cannot be queued is not dropped (the
    ``source_vectors`` survival rule): the extraction job fails retryably
    (``contextual_index_not_queued``) and its retry, which reuses the
    completed extraction, queues it. A local job that defers (the batch wait,
    a busy GPU) is woken by the host's sweep at its ``retry_at``."""

    from learnloop.source_retrieval.fallback_space import FALLBACK_JOB, fallback_reason
    from learnloop.source_retrieval.local_index import INDEX_JOB
    from learnloop.source_retrieval.source_vectors import LIVE_JOB_STATUSES, target_extraction

    queued: list[str] = []
    embedding = config.embedding
    want_local = embedding.local.enabled and embedding.local.index_on_extract
    want_fallback = fallback_reason(config) is None and embedding.fallback.maintain_index
    if not (want_local or want_fallback):
        return queued
    try:
        _source_id, current = target_extraction(ctx.repo, extraction_id)
        if current is None:
            return queued
        live = [job for job in ctx.repo.ingest_jobs_by_types((INDEX_JOB, FALLBACK_JOB))
                if job.get("status") in LIVE_JOB_STATUSES]
        payload: dict[str, Any] = {"extraction_id": extraction_id, "current_extraction_id": current}
        if title:
            payload["title"] = title
        if want_local and not any(job.get("job_type") == INDEX_JOB for job in live):
            queued.append(ctx.enqueue_batch(INDEX_JOB, [JobSpec(INDEX_JOB, payload)]))
        if want_fallback and not any(job.get("job_type") == FALLBACK_JOB
                                     and (job.get("payload") or {}).get("current_extraction_id") == current
                                     for job in live):
            queued.append(ctx.enqueue_batch(FALLBACK_JOB, [JobSpec(FALLBACK_JOB, payload)]))
    except JobCancelled:
        raise
    except Exception as exc:  # noqa: BLE001 - classified: the obligation must not be lost silently
        raise IngestRunnerError(
            "The source was extracted, but indexing it in the local or fallback meaning space could not be "
            "queued. Retry: the extraction is reused, not repeated.",
            code="contextual_index_not_queued",
            details={"extraction_id": extraction_id, "error_type": type(exc).__name__},
            retryable=True,
        ) from exc
    return queued


#: ``run_local_index`` statuses that end the job without a failure: the work
#: is done, off, or waiting for the GPU or the batch (coverage keeps the debt).
_LOCAL_INDEX_DONE = frozenset({"complete", "partial", "disabled", "waiting_for_gpu", "waiting_for_batch",
                               "epoch_drift", "epoch_changed"})


def handle_local_source_index(ctx: JobContext) -> dict[str, Any]:
    """local_source_index: index every owed window in one 9B worker batch.

    Waiting for the GPU or the batch is not a failure: the job completes with
    its reason and coverage stays partial (the resolver uses another space)."""

    from learnloop.source_retrieval.local_index import run_local_index
    from learnloop.vault.loader import load_vault

    ctx.report("acquired", message="Indexing sources on the local model")
    report = run_local_index(load_vault(ctx.vault_root), ctx.repo)
    status = str(report.get("status") or "")
    if status not in _LOCAL_INDEX_DONE:
        raise IngestRunnerError(f"The local index worker ended with status {status!r}: {report.get('reason')}.",
                                code="local_index_failed", details={key: report.get(key) for key in (
                                    "status", "owed_extractions", "owed_windows")}, retryable=True)
    messages = {"complete": "Local meaning index updated", "partial": "Local meaning index partly updated",
                "disabled": f"Not indexed locally: {report.get('reason')}",
                "waiting_for_gpu": f"Waiting for the GPU: {report.get('reason')}",
                "waiting_for_batch": f"Waiting for the batch: {report.get('reason')}",
                "epoch_drift": f"Local index paused: {report.get('reason')}",
                "epoch_changed": f"Local index paused: {report.get('reason')}"}
    ctx.report("applied", message=messages[status])
    return {key: value for key, value in report.items() if key != "worker"}


def handle_source_fallback_backfill(ctx: JobContext) -> dict[str, Any]:
    """source_fallback_backfill: the Voyage fallback space's windows for one
    source (capped, receipted; an aggregate report, never block text)."""

    from learnloop.source_retrieval.dense import clear_cache
    from learnloop.source_retrieval.fallback_space import backfill_fallback_vectors
    from learnloop.vault.loader import load_vault

    extraction_id = str(ctx.payload.get("current_extraction_id") or ctx.payload.get("extraction_id") or "").strip()
    if not extraction_id:
        raise IngestRunnerError("source_fallback_backfill requires an 'extraction_id'.")
    ctx.report("acquired", message="Indexing the source in the fallback space")
    report = backfill_fallback_vectors(load_vault(ctx.vault_root), ctx.repo, extraction_id, cancelled=ctx.cancelled)
    status = str(report.get("status") or "")
    if report.get("embedded_windows"):
        clear_cache()
    if status == "cancelled":
        raise JobCancelled()
    if status in {"complete", "disabled"}:
        ctx.report("applied", message="Fallback index updated" if status == "complete"
                   else f"Not indexed in the fallback space: {report.get('reason')}; nothing was sent")
        return report
    details = {key: report.get(key) for key in ("status", "extraction_id", "space_id", "missing_windows",
                                               "embedded_windows", "remaining_windows", "charged", "error_type")}
    if status == "over_budget":
        raise IngestRunnerError(
            "Indexing this source in the fallback space would exceed embedding.fallback.max_cost_usd_per_run; "
            "raise the cap and retry, or run `learnloop embeddings fallback backfill`.",
            code="over_budget", details=details, retryable=False)
    raise IngestRunnerError(f"The fallback backfill ended with status {status!r}; retry to index the rest "
                            "(saved windows are not bought again).",
                            code="fallback_backfill_incomplete", details=details, retryable=True)


#: ``backfill_source_vectors`` statuses that end the job without a failure.
_SOURCE_VECTORS_DONE = frozenset({"complete", "disabled", "no_extraction"})


def handle_curriculum_coverage_on_extract(ctx: JobContext) -> dict[str, Any]:
    """curriculum_coverage_on_extract: judge the covered LOs again after an extraction (C0b, §6.3).

    Quiet (plan only); a fresh state pays nothing; the result is counts and statuses,
    never text. A plan that cannot run leaves the job ``waiting`` (completed): the next
    extraction or a pressed check judges again, and nothing asks the learner."""

    from learnloop.source_retrieval import section_coverage as SC
    from learnloop.vault.loader import load_vault

    extraction_id = str(ctx.payload.get("extraction_id") or "").strip()
    if not extraction_id:
        raise IngestRunnerError("curriculum_coverage_on_extract requires an 'extraction_id'.")
    ctx.report("acquired", message="Checking where your books treat the topics already covered")
    return SC.rejudge_on_extract(load_vault(ctx.vault_root), ctx.repo, extraction_id, cancelled=ctx.cancelled)


def handle_source_embedding_backfill(ctx: JobContext) -> dict[str, Any]:
    """source_embedding_backfill: embed a source's current extraction's blocks.

    Through ``ops.embedding_backfill`` (switches, caps, lock, receipts); the
    result is the aggregate report (counts, caps, charges), never block text.

    Codex review F4: only a complete run (or one with nothing to do) completes
    the job. Lock contention and provider failures fail it retryably, a run
    over its money cap or a vector-width conflict fails it for the owner to
    resolve, and a cancellation cancels it; the batches paid before a failure
    stay saved, so a retry buys only the rest."""

    from learnloop.source_retrieval.dense import clear_cache
    from learnloop.source_retrieval.source_vectors import backfill_source_vectors
    from learnloop.vault.loader import load_vault

    extraction_id = str(ctx.payload.get("extraction_id") or "").strip()
    if not extraction_id:
        raise IngestRunnerError("source_embedding_backfill requires an 'extraction_id'.")
    ctx.report("acquired", message="Indexing the source for meaning search")
    factory = ctx.services.embedding_client_factory
    report = backfill_source_vectors(
        load_vault(ctx.vault_root), extraction_id,
        client_factory=(lambda: factory(ctx)) if factory is not None else None,
        cancelled=ctx.cancelled,
    )
    if report.get("embedded"):
        clear_cache()
    status = str(report.get("status") or "")
    title = ctx.payload.get("title")
    result = {**report, **({"title": title} if title else {})}
    if status == "cancelled":
        raise JobCancelled()
    if status not in _SOURCE_VECTORS_DONE:
        raise _source_vectors_failure(status, report)
    if status == "complete":
        message = "Meaning search index updated" if report.get("embedded") else "Meaning search index already up to date"
    elif status == "disabled":
        message = f"Not indexed: {report.get('reason')}; nothing was sent"
    else:
        message = "Nothing to index: the source has no current extraction"
    ctx.report("applied", message=message)
    return result


def _source_vectors_failure(status: str, report: Mapping[str, Any]) -> IngestRunnerError:
    """The workflow failure for an unsuccessful source backfill (Codex review F4).

    ``details`` carries the aggregate report only (counts, caps, charges,
    model, the provider's error class), never block text."""

    details = {key: report.get(key) for key in (
        "status", "extraction_id", "embedded_extraction_id", "model_id", "records", "cached", "embedded",
        "remaining", "charged", "caps", "error_type", "run_id",
    ) if key in report}
    if status == "busy":
        return IngestRunnerError(
            "Another embedding backfill is running for this vault; retry when it finishes (nothing was sent).",
            code="embedding_backfill_busy", details=details, retryable=True)
    if status == "provider_failed":
        return IngestRunnerError(
            f"The embedding provider failed after {report.get('embedded') or 0} of "
            f"{(report.get('embedded') or 0) + (report.get('remaining') or 0)} pending blocks were indexed; "
            "retry to index the rest (the saved blocks are not bought again).",
            code="embedding_provider_failed", details=details, retryable=True)
    if status == "unavailable":
        return IngestRunnerError(
            f"The embedding provider is not ready: {report.get('reason') or 'unavailable'}.",
            code="embedding_unavailable", details=details, retryable=True)
    if status == "over_budget":
        return IngestRunnerError(
            f"Indexing this source would exceed embedding.source_backfill_max_cost_usd ({report.get('reason')}); "
            "raise the cap and retry, or run `learnloop embeddings backfill --record-kind source_block`.",
            code="over_budget", details=details, retryable=False)
    if status == "blocked":
        return IngestRunnerError(
            f"The source could not be indexed: {report.get('reason')}.",
            code="embedding_index_conflict", details=details, retryable=False)
    return IngestRunnerError(f"The source backfill ended with status {status!r}.",
                             code="embedding_backfill_incomplete", details=details, retryable=True)
