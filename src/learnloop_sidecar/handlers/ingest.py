from __future__ import annotations

from typing import Any, Literal

from learnloop.ingest.models import UnsupportedSourceError
from learnloop.ingest.resolution import resolve_source
from learnloop.services.acquisition_preview import build_acquisition_preview
from learnloop.services.build_plan import build_build_plan
from learnloop.services.source_outline import (
    OutlineNotFound,
    build_source_outline,
    resolve_extraction_id,
)
from learnloop.services.source_unit_selection import (
    SelectionValidationError,
    compute_effective_units,
    save_unit_selection,
)
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.ingest_jobs import _APPLYING_JOB_TYPES, ActiveIngestJobError
from learnloop_sidecar.registry import method

# How many recent ingests the screen shows; the vault keeps everything.
_RECENT_LIMIT = 30


class ClassifyIngestSourceInput(ParamsModel):
    source: str


class StartIngestInput(ParamsModel):
    source: str
    subject_id: str
    mode: Literal["canonical", "exam"] = "canonical"
    # PDF extraction engine: marker-pdf (structured Markdown, math, OCR) or the
    # pypdf native-text fallback. "auto" defers to the vault's [ingest.pdf].
    pdf_engine: Literal["auto", "marker", "pypdf", "native"] = "auto"


class IngestJobInput(ParamsModel):
    job_id: str


class SourcePageRangeInput(ParamsModel):
    source: str
    pages: str | None = None
    # Backward-compatible contiguous range form.
    page_start: int | None = None
    page_end: int | None = None


class StartImportBatchInput(ParamsModel):
    sources: list[str]
    subject_id: str | None = None
    inventory: bool = False
    # Optional, inclusive, user-facing PDF page range. Pages are 1-based at the
    # RPC boundary and normalized to the IR's 0-based page indices below.
    page_start: int | None = None
    page_end: int | None = None
    pages: str | None = None
    # Multi-source imports carry ranges per source. The top-level pair remains
    # the convenient single-source form used by Quick Add.
    page_ranges: list[SourcePageRangeInput] = []
    # A build-plan estimate snapshot (§8.6.2) when the batch is started from a plan.
    estimate: dict[str, Any] | None = None
    # Sources the learner opted OUT of the reader loop at ingest setup (e.g.
    # practice exams). Everything else defaults to reader-enabled.
    reader_disabled_sources: list[str] = []
    # PDF extraction engine for this batch: marker-pdf or the pypdf fallback.
    # "auto" defers to the vault's [ingest.pdf] configuration.
    pdf_engine: Literal["auto", "marker", "pypdf", "native"] = "auto"


class IngestBatchInput(ParamsModel):
    batch_id: str


class ListIngestBatchesInput(ParamsModel):
    limit: int = 30


class RetrySynthesisInput(ParamsModel):
    batch_id: str
    # Required for a model rerun; optional (ignored) when reusing the preserved
    # candidate, which re-runs gates/persistence with zero model calls.
    synthesis_total_input_tokens: int | None = None
    synthesis_shard_output_tokens: int | None = None
    synthesis_output_tokens: int | None = None
    reuse_candidate: bool = False
    # Both require reuse_candidate: auto-derive mechanically-safe repairs over
    # the preserved candidate / apply explicit user- or agent-authored ops.
    repair_candidate: bool = False
    repair_ops: list[dict[str, Any]] | None = None
    unlimited_token_budget: bool = False


@method("classify_ingest_source", ClassifyIngestSourceInput)
def classify_ingest_source(_ctx: SidecarContext, params: ClassifyIngestSourceInput) -> dict[str, Any]:
    try:
        resolved = resolve_source(params.source)
    except UnsupportedSourceError as exc:
        raise SidecarError("unsupported_source", str(exc)) from exc
    return versioned({"kind": resolved.category, "normalized_source": resolved.source})


@method("start_ingest", StartIngestInput)
def start_ingest(ctx: SidecarContext, params: StartIngestInput) -> dict[str, Any]:
    vault, _repository = ctx.require_vault()
    source = params.source.strip()
    if not source:
        raise SidecarError("unsupported_source", "A source is required.")
    if params.subject_id not in vault.subjects:
        raise SidecarError("unknown_subject", f"Subject '{params.subject_id}' does not exist.")
    try:
        resolve_source(source)
    except UnsupportedSourceError as exc:
        raise SidecarError("unsupported_source", str(exc)) from exc
    try:
        job = ctx.ingest_jobs.start(
            vault.root, source, params.subject_id, params.mode, pdf_engine=params.pdf_engine
        )
    except ActiveIngestJobError as exc:
        raise SidecarError(
            "ingest_in_progress",
            str(exc),
            retryable=True,
            details={"jobId": exc.job_id},
        ) from exc
    return versioned(job)


@method("get_ingest_job", IngestJobInput)
def get_ingest_job(ctx: SidecarContext, params: IngestJobInput) -> dict[str, Any]:
    job = ctx.ingest_jobs.get(params.job_id)
    if job is None:
        raise SidecarError("ingest_job_not_found", f"Ingest job '{params.job_id}' was not found.")
    _reload_completed_jobs(ctx, [job])
    return versioned(ctx.ingest_jobs.get(params.job_id) or job)


@method("get_ingest_jobs")
def get_ingest_jobs(ctx: SidecarContext, _params) -> dict[str, Any]:
    jobs = ctx.ingest_jobs.list()
    _reload_completed_jobs(ctx, jobs)
    return versioned({"jobs": ctx.ingest_jobs.list()})


@method("cancel_ingest", IngestJobInput)
def cancel_ingest(ctx: SidecarContext, params: IngestJobInput) -> dict[str, Any]:
    job = ctx.ingest_jobs.cancel(params.job_id)
    if job is None:
        raise SidecarError("ingest_job_not_found", f"Ingest job '{params.job_id}' was not found.")
    return versioned(job)


# ---------------------------------------------------------------------------
# Durable batches (spec §6.2/§6.3): Source library + Batch progress screens
# ---------------------------------------------------------------------------


@method("start_import_batch", StartImportBatchInput)
def start_import_batch(ctx: SidecarContext, params: StartImportBatchInput) -> dict[str, Any]:
    vault, _repository = ctx.require_vault()
    sources = [source.strip() for source in params.sources if source.strip()]
    if not sources:
        raise SidecarError("unsupported_source", "At least one source is required.")
    if params.subject_id is not None and params.subject_id not in vault.subjects:
        raise SidecarError("unknown_subject", f"Subject '{params.subject_id}' does not exist.")
    if params.pages and (params.page_start is not None or params.page_end is not None):
        raise SidecarError("invalid_page_range", "Use either a page expression or first/last page, not both.")
    if (params.page_start is None) != (params.page_end is None):
        raise SidecarError("invalid_page_range", "Enter both the first and last PDF page.")
    page_selection = _parse_page_selection(params.pages) if params.pages else None
    if params.page_start is not None and params.page_end is not None:
        page_selection = _contiguous_page_selection(params.page_start, params.page_end)
    if page_selection is not None and len(sources) > 1:
        raise SidecarError(
            "invalid_page_range",
            "Multi-source imports require a separate page range for each PDF.",
        )
    page_selections: dict[str, list[int]] = {}
    for item in params.page_ranges:
        range_source = item.source.strip()
        if range_source not in sources:
            raise SidecarError("invalid_page_range", f"Page range source '{range_source}' is not in this import batch.")
        if range_source in page_selections:
            raise SidecarError("invalid_page_range", f"Source '{range_source}' has more than one page range.")
        if item.pages and (item.page_start is not None or item.page_end is not None):
            raise SidecarError("invalid_page_range", "Use either a page expression or first/last page, not both.")
        if item.pages:
            page_selections[range_source] = _parse_page_selection(item.pages)
        elif item.page_start is not None and item.page_end is not None:
            page_selections[range_source] = _contiguous_page_selection(item.page_start, item.page_end)
        else:
            raise SidecarError("invalid_page_range", f"Source '{range_source}' has an incomplete page selection.")
    for source in sources:
        try:
            resolve_source(source)
        except UnsupportedSourceError as exc:
            raise SidecarError("unsupported_source", str(exc)) from exc
    reader_disabled = {s.strip() for s in params.reader_disabled_sources if s.strip()}
    for source in reader_disabled:
        if source not in sources:
            raise SidecarError(
                "unsupported_source", f"Reader opt-out source '{source}' is not in this import batch."
            )
    batch_id = ctx.ingest_jobs.enqueue_import(
        sources,
        subject_id=params.subject_id,
        inventory=params.inventory,
        estimate=params.estimate,
        page_selection=page_selection,
        page_selections=page_selections,
        reader_disabled_sources=reader_disabled,
        pdf_engine=params.pdf_engine,
    )
    return versioned(ctx.ingest_jobs.get_batch(batch_id))


def _contiguous_page_selection(start: int, end: int) -> list[int]:
    if start < 1 or end < 1:
        raise SidecarError("invalid_page_range", "PDF pages must be positive numbers.")
    if start > end:
        raise SidecarError("invalid_page_range", "The first PDF page must not exceed the last page.")
    return list(range(start - 1, end))


def _parse_page_selection(raw: str) -> list[int]:
    pages: set[int] = set()
    text = raw.strip()
    if not text:
        raise SidecarError("invalid_page_range", "Enter at least one PDF page or range.")
    for raw_segment in text.split(","):
        segment = raw_segment.strip()
        if not segment:
            raise SidecarError("invalid_page_range", "Remove the empty page segment.")
        if "-" in segment:
            parts = [part.strip() for part in segment.split("-")]
            if len(parts) != 2 or not all(part.isdigit() for part in parts):
                raise SidecarError("invalid_page_range", f"'{segment}' must be a page or range such as 36 or 3-27.")
            start, end = (int(part) for part in parts)
        elif segment.isdigit():
            start = end = int(segment)
        else:
            raise SidecarError("invalid_page_range", f"'{segment}' must be a page or range such as 36 or 3-27.")
        if start < 1 or end < 1:
            raise SidecarError("invalid_page_range", "PDF pages must be positive numbers.")
        if start > end:
            raise SidecarError("invalid_page_range", f"Range {start}-{end} runs backwards.")
        pages.update(range(start - 1, end))
    return sorted(pages)


@method("get_ingest_batch", IngestBatchInput)
def get_ingest_batch(ctx: SidecarContext, params: IngestBatchInput) -> dict[str, Any]:
    batch = ctx.ingest_jobs.get_batch(params.batch_id)
    if batch is None:
        raise SidecarError("ingest_batch_not_found", f"Batch '{params.batch_id}' was not found.")
    _reload_applied_batches(ctx, [batch])
    return versioned(batch)


@method("list_ingest_batches", ListIngestBatchesInput)
def list_ingest_batches(ctx: SidecarContext, params: ListIngestBatchesInput) -> dict[str, Any]:
    batches = ctx.ingest_jobs.list_batches(limit=params.limit)
    _reload_applied_batches(ctx, batches)
    return versioned({"batches": batches})


def _reload_applied_batches(ctx: SidecarContext, batches: list[dict[str, Any]]) -> None:
    """Refresh the in-memory vault once after a content-applying job completes.

    Durable synthesis/ingest batches finish in the background drain thread, so
    the batch-polling RPCs are the first place the sidecar can observe that new
    study-map content landed. Without this, screens reading the loaded vault
    (Today, knowledge map) keep serving the pre-apply snapshot until an app
    restart even though the proposal shows as accepted."""

    pending = [
        job["id"]
        for batch in batches
        for job in batch.get("jobs") or []
        if job.get("job_type") in _APPLYING_JOB_TYPES
        and job.get("status") == "completed"
        and ctx.ingest_jobs.needs_reload(job["id"])
    ]
    if not pending:
        return
    ctx.reload(maintenance=False)
    for job_id in pending:
        ctx.ingest_jobs.mark_reloaded(job_id)


@method("cancel_ingest_batch", IngestBatchInput)
def cancel_ingest_batch(ctx: SidecarContext, params: IngestBatchInput) -> dict[str, Any]:
    batch = ctx.ingest_jobs.cancel_batch(params.batch_id)
    if batch is None:
        raise SidecarError("ingest_batch_not_found", f"Batch '{params.batch_id}' was not found.")
    return versioned(batch)


@method("resume_ingest_batch", IngestBatchInput)
def resume_ingest_batch(ctx: SidecarContext, params: IngestBatchInput) -> dict[str, Any]:
    batch = ctx.ingest_jobs.resume_batch(params.batch_id)
    if batch is None:
        raise SidecarError("ingest_batch_not_found", f"Batch '{params.batch_id}' was not found.")
    return versioned(batch)


@method("retry_synthesis", RetrySynthesisInput)
def retry_synthesis(ctx: SidecarContext, params: RetrySynthesisInput) -> dict[str, Any]:
    """Requeue only a failed synthesis job with revised execution ceilings.

    Completed inventory dependencies remain completed and are reused verbatim.
    With ``reuse_candidate`` the preserved merged candidate is revalidated and
    persisted with zero model calls (budgets are not required or applied).
    """

    budgets: dict[str, int] = {}
    if not params.reuse_candidate and not params.unlimited_token_budget:
        if params.synthesis_total_input_tokens is None:
            raise SidecarError(
                "invalid_synthesis_budget",
                "A synthesis total-input ceiling is required for a model rerun.",
            )
        if not 10_000 <= params.synthesis_total_input_tokens <= 2_000_000:
            raise SidecarError(
                "invalid_synthesis_budget",
                "Synthesis total-input ceiling must be between 10,000 and 2,000,000 tokens.",
            )
        for label, value in (
            ("Synthesis shard-output ceiling", params.synthesis_shard_output_tokens),
            ("Synthesis merged-output ceiling", params.synthesis_output_tokens),
        ):
            if value is not None and not 1_000 <= value <= 200_000:
                raise SidecarError(
                    "invalid_synthesis_budget",
                    f"{label} must be between 1,000 and 200,000 tokens.",
                )
        budgets = {"synthesis_total_input_ceiling": params.synthesis_total_input_tokens}
        if params.synthesis_shard_output_tokens is not None:
            budgets["synthesis_shard_output_tokens"] = params.synthesis_shard_output_tokens
        if params.synthesis_output_tokens is not None:
            budgets["synthesis_output_tokens"] = params.synthesis_output_tokens
    try:
        batch = ctx.ingest_jobs.retry_synthesis(
            params.batch_id,
            synthesis_budgets=budgets or None,
            reuse_candidate=params.reuse_candidate,
            repair_candidate=params.repair_candidate,
            repair_ops=params.repair_ops,
            unlimited_token_budget=params.unlimited_token_budget,
        )
    except ValueError as exc:
        raise SidecarError("synthesis_retry_unavailable", str(exc)) from exc
    return versioned(batch)


@method("get_synthesis_candidate", IngestBatchInput)
def get_synthesis_candidate(ctx: SidecarContext, params: IngestBatchInput) -> dict[str, Any]:
    """Summarize the preserved synthesis candidate behind a failed batch (§8).

    Deterministic and read-only: item counts, summary line, and run lineage from
    ``synthesis_runs.candidate_output_json``, so the learner can decide between
    revalidating the paid-for candidate and paying for a fresh model run."""

    _vault, repository = ctx.require_vault()
    batch = ctx.ingest_jobs.get_batch(params.batch_id)
    if batch is None:
        raise SidecarError("ingest_batch_not_found", f"Batch '{params.batch_id}' was not found.")
    synthesis_run_id = ""
    for job in batch.get("jobs") or []:
        details = ((job.get("error") or {}).get("details")) or {}
        if details.get("candidate_preserved") and details.get("synthesis_run_id"):
            synthesis_run_id = str(details["synthesis_run_id"])
            break
    if not synthesis_run_id:
        raise SidecarError(
            "no_saved_candidate", "This batch has no failed synthesis attempt with a preserved candidate."
        )
    run = repository.synthesis_run(synthesis_run_id)
    candidate = (run or {}).get("candidate_output") or None
    if run is None or candidate is None:
        raise SidecarError("no_saved_candidate", "The preserved candidate is no longer available.")
    counts = {
        key: len(candidate.get(key) or [])
        for key in (
            "concepts",
            "facets",
            "learning_objects",
            "blueprints",
            "practice_items",
            "concept_relations",
        )
    }
    return versioned(
        {
            "synthesis_run_id": synthesis_run_id,
            "run_status": run.get("status"),
            "created_at": run.get("created_at"),
            "completed_at": run.get("completed_at"),
            "summary": str(candidate.get("summary") or ""),
            "item_counts": counts,
            "notes": list(candidate.get("notes") or []),
        }
    )


@method("get_source_library")
def get_source_library(ctx: SidecarContext, _params) -> dict[str, Any]:
    """The Source library card grid (§5.7): one card per artifact fed by the M1
    artifact/revision/extraction tables — title, readiness/health line, suggested
    role, and an update-available placeholder."""

    _vault, repository = ctx.require_vault()
    cards: list[dict[str, Any]] = []
    for artifact in repository.all_source_artifacts():
        revisions = repository.source_revisions_for(artifact["id"])
        current_revision_id = artifact.get("current_revision_id")
        current = next((rev for rev in revisions if rev["id"] == current_revision_id), None)
        if current is None and revisions:
            current = revisions[-1]
        runs = repository.extraction_runs_for_revision(current["id"]) if current else []
        completed = [run for run in runs if run.get("status") == "completed"]
        latest = completed[-1] if completed else (runs[-1] if runs else None)
        counts = repository.document_ir_counts(latest["id"]) if latest else {"unit_count": 0, "block_count": 0}
        if latest is not None and latest.get("status") == "completed" and counts["block_count"] > 0:
            readiness = "ready"
        elif latest is not None:
            readiness = "processing"
        else:
            readiness = "needs_extraction"
        cards.append(
            {
                "source_id": artifact["id"],
                "title": _artifact_title(artifact, current),
                "acquisition_kind": artifact.get("acquisition_kind"),
                "canonical_uri": artifact.get("canonical_uri"),
                "work_id": artifact.get("work_id"),
                "current_revision_id": current["id"] if current else None,
                "revision_count": len(revisions),
                "readiness": readiness,
                "unit_count": counts["unit_count"],
                "block_count": counts["block_count"],
                "extraction_status": latest["status"] if latest else None,
                # Placeholders wired to real signals in later milestones (§5.7).
                "suggested_role": None,
                "reader_enabled": bool(artifact.get("reader_enabled", 1)),
                "update_available": len(revisions) > 1 and current is not None and current["id"] != revisions[-1]["id"],
            }
        )
    return versioned({"sources": cards})


# ---------------------------------------------------------------------------
# Outline, selection, budget planning, and repair (ING M3, §3/§5.3/§5.7/§8.6)
# ---------------------------------------------------------------------------


class SourceOutlineInput(ParamsModel):
    extraction_ref: str


class SaveUnitSelectionInput(ParamsModel):
    extraction_id: str
    selected_unit_ids: list[str]
    boundary_overrides: list[dict[str, Any]] = []
    role_override: str | None = None


class AcquisitionPreviewInput(ParamsModel):
    inputs: list[str]


class BuildPlanSelection(ParamsModel):
    extraction_id: str
    selected_unit_ids: list[str] = []


class BuildPlanInput(ParamsModel):
    selections: list[BuildPlanSelection]
    subject_id: str | None = None


class StartExtractionRepairInput(ParamsModel):
    revision_id: str
    pages: list[Any]
    consent: dict[str, Any]
    repair_options: dict[str, Any] = {}
    parent_extraction_id: str | None = None
    subject_id: str | None = None


@method("get_source_outline", SourceOutlineInput)
def get_source_outline(ctx: SidecarContext, params: SourceOutlineInput) -> dict[str, Any]:
    """Deterministic outline of a source's extraction (zero agent runs, §3/§5.7)."""

    _vault, repository = ctx.require_vault()
    extraction_id = resolve_extraction_id(repository, params.extraction_ref)
    if extraction_id is None:
        raise SidecarError("extraction_not_found", f"No extraction resolves for '{params.extraction_ref}'.")
    try:
        outline = build_source_outline(repository, extraction_id)
    except OutlineNotFound as exc:
        raise SidecarError("extraction_not_found", str(exc)) from exc
    payload = outline.model_dump(mode="json")
    selection = repository.get_unit_selection(extraction_id)
    payload["selection"] = {
        "selected_unit_ids": selection.get("selected_unit_ids") if selection else [],
        "boundary_overrides": selection.get("boundary_overrides") if selection else [],
        "needs_review": selection.get("needs_review") if selection else [],
        "role_override": selection.get("role_override") if selection else None,
    }
    return versioned(payload)


class SelectionPreviewInput(ParamsModel):
    extraction_ref: str
    selected_unit_ids: list[str] | None = None


@method("get_selection_preview", SelectionPreviewInput)
def get_selection_preview(ctx: SidecarContext, params: SelectionPreviewInput) -> dict[str, Any]:
    """Byte-exact display markdown for a unit selection — the same
    ``render_ir_markdown`` output synthesis feeds the model (§2.3), so the
    learner can inspect what the LLM will see before starting a batch.
    ``selected_unit_ids`` omitted → the persisted selection, or the whole
    document when none exists. Deterministic; zero agent runs."""

    from learnloop.ingest.ir import render_ir_markdown

    _vault, repository = ctx.require_vault()
    extraction_id = resolve_extraction_id(repository, params.extraction_ref)
    if extraction_id is None:
        raise SidecarError("extraction_not_found", f"No extraction resolves for '{params.extraction_ref}'.")
    ir = repository.load_document_ir(extraction_id)
    if ir is None or not ir.blocks:
        raise SidecarError("extraction_not_found", f"No persisted document IR for '{params.extraction_ref}'.")
    unit_ids = params.selected_unit_ids
    if unit_ids is None:
        selection = repository.get_unit_selection(extraction_id)
        unit_ids = (selection or {}).get("selected_unit_ids") or None
    markdown = render_ir_markdown(ir, selected_unit_ids=unit_ids)
    return versioned(
        {
            "extraction_id": extraction_id,
            "selected_unit_ids": unit_ids or [],
            "markdown": markdown,
            "approx_tokens": max(1, len(markdown) // 4) if markdown else 0,
        }
    )


class EffectiveOutlineInput(ParamsModel):
    extraction_ref: str
    boundary_overrides: list[dict[str, Any]] = []


@method("get_effective_outline", EffectiveOutlineInput)
def get_effective_outline(ctx: SidecarContext, params: EffectiveOutlineInput) -> dict[str, Any]:
    """Deterministic effective-unit shape after boundary overrides (§5.3).

    Zero LLM: walks the persisted IR and folds/partitions units per the learner's
    merge/split intents so the outline screen can render the resulting shape live
    as overrides change. ``boundary_overrides`` omitted → the extraction's units
    pass through unchanged."""

    _vault, repository = ctx.require_vault()
    extraction_id = resolve_extraction_id(repository, params.extraction_ref)
    if extraction_id is None:
        raise SidecarError("extraction_not_found", f"No extraction resolves for '{params.extraction_ref}'.")
    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        raise SidecarError("extraction_not_found", f"No persisted document IR for '{params.extraction_ref}'.")
    units = compute_effective_units(ir, params.boundary_overrides)
    return versioned({"extraction_id": extraction_id, "units": units})


@method("save_unit_selection", SaveUnitSelectionInput)
def save_unit_selection_rpc(ctx: SidecarContext, params: SaveUnitSelectionInput) -> dict[str, Any]:
    """Persist per-extraction unit selection + boundary overrides (§5.3)."""

    _vault, repository = ctx.require_vault()
    try:
        selection = save_unit_selection(
            repository,
            params.extraction_id,
            params.selected_unit_ids,
            boundary_overrides=params.boundary_overrides,
            role_override=params.role_override,
        )
    except SelectionValidationError as exc:
        raise SidecarError("invalid_unit_selection", str(exc)) from exc
    return versioned(
        {
            "extraction_id": params.extraction_id,
            "selected_unit_ids": selection.get("selected_unit_ids", []),
            "boundary_overrides": selection.get("boundary_overrides", []),
            "needs_review": selection.get("needs_review", []),
            "role_override": selection.get("role_override"),
        }
    )


@method("get_acquisition_preview", AcquisitionPreviewInput)
def get_acquisition_preview(ctx: SidecarContext, params: AcquisitionPreviewInput) -> dict[str, Any]:
    """Deterministic acquisition preview — no downloads/extraction/LLM (§8.6.1)."""

    vault, repository = ctx.require_vault()
    preview = build_acquisition_preview(repository, vault.config, params.inputs)
    return versioned(preview.as_dict())


@method("get_build_plan", BuildPlanInput)
def get_build_plan(ctx: SidecarContext, params: BuildPlanInput) -> dict[str, Any]:
    """Deterministic build plan with per-stage token estimates (§8.6.2)."""

    vault, repository = ctx.require_vault()
    if params.subject_id is not None and params.subject_id not in vault.subjects:
        raise SidecarError("unknown_subject", f"Subject '{params.subject_id}' does not exist.")
    try:
        plan = build_build_plan(
            repository,
            vault.config,
            vault,
            subject_id=params.subject_id,
            selections=[selection.model_dump() for selection in params.selections],
        )
    except OutlineNotFound as exc:
        raise SidecarError("extraction_not_found", str(exc)) from exc
    return versioned(plan.as_dict())


@method("start_extraction_repair", StartExtractionRepairInput)
def start_extraction_repair(ctx: SidecarContext, params: StartExtractionRepairInput) -> dict[str, Any]:
    """Enqueue a consent-gated extraction-repair batch (§2.5)."""

    vault, repository = ctx.require_vault()
    if repository.get_source_revision(params.revision_id) is None:
        raise SidecarError("revision_not_found", f"Revision '{params.revision_id}' was not found.")
    if not params.consent.get("provider") or not params.consent.get("purpose"):
        raise SidecarError(
            "consent_required",
            "Extraction repair needs an explicit consent record (provider + purpose).",
        )
    if params.subject_id is not None and params.subject_id not in vault.subjects:
        raise SidecarError("unknown_subject", f"Subject '{params.subject_id}' does not exist.")
    batch_id = ctx.ingest_jobs.enqueue_extraction_repair(
        revision_id=params.revision_id,
        pages=params.pages,
        repair_options=params.repair_options,
        consent=params.consent,
        parent_extraction_id=params.parent_extraction_id,
        subject_id=params.subject_id,
    )
    return versioned(ctx.ingest_jobs.get_batch(batch_id))


class ListSourceSetsInput(ParamsModel):
    pass


class SourceSetRefInput(ParamsModel):
    source_set_id: str


class SourceSetScopeParams(ParamsModel):
    unit_id: str
    role_override: str | None = None


class SourceSetMemberParams(ParamsModel):
    source_id: str
    revision_id: str
    default_role: str = "reference"
    scope: list[SourceSetScopeParams] = []
    priority: int = 1


class UpsertSourceSetInput(ParamsModel):
    id: str
    subject_id: str
    title: str = ""
    members: list[SourceSetMemberParams] = []


class StartInventoryInput(ParamsModel):
    extraction_ref: str
    units: list[dict[str, Any]]
    subject_id: str | None = None
    source_set_id: str | None = None
    inventory_output_tokens: int | None = None
    unlimited_token_budget: bool = False


def _source_set_or_error(vault, set_id: str):
    source_set = next((s for s in vault.source_sets if s.id == set_id), None)
    if source_set is None:
        raise SidecarError("source_set_not_found", f"Source set '{set_id}' does not exist.")
    return source_set


@method("list_source_sets", ListSourceSetsInput)
def list_source_sets(ctx: SidecarContext, _params: ListSourceSetsInput) -> dict[str, Any]:
    """List source collections (§4.3)."""

    vault, _repository = ctx.require_vault()
    return versioned(
        {
            "source_sets": [
                {"id": s.id, "subject_id": s.subject_id, "title": s.title, "member_count": len(s.members)}
                for s in vault.source_sets
            ]
        }
    )


@method("get_source_set", SourceSetRefInput)
def get_source_set(ctx: SidecarContext, params: SourceSetRefInput) -> dict[str, Any]:
    """Show a collection's members, roles, and scopes (§4.3)."""

    vault, _repository = ctx.require_vault()
    source_set = _source_set_or_error(vault, params.source_set_id)
    return versioned({"source_set": source_set.model_dump(mode="json")})


@method("upsert_source_set", UpsertSourceSetInput)
def upsert_source_set_rpc(ctx: SidecarContext, params: UpsertSourceSetInput) -> dict[str, Any]:
    """Create or update a collection; membership owns role/scope/priority (§4.3)."""

    from learnloop.vault.writer import upsert_source_set

    vault, _repository = ctx.require_vault()
    if params.subject_id not in vault.subjects:
        raise SidecarError("unknown_subject", f"Subject '{params.subject_id}' does not exist.")
    members = [member.model_dump(by_alias=False) for member in params.members]
    upsert_source_set(
        vault.root,
        {"id": params.id, "subject_id": params.subject_id, "title": params.title or params.id, "members": members},
    )
    ctx.reload(maintenance=False)
    refreshed, _repo = ctx.require_vault()
    return versioned({"source_set": _source_set_or_error(refreshed, params.id).model_dump(mode="json")})


@method("get_source_coverage", SourceSetRefInput)
def get_source_coverage(ctx: SidecarContext, params: SourceSetRefInput) -> dict[str, Any]:
    """Deterministic coverage + readiness preview for a collection (§9.3)."""

    from learnloop.services.source_coverage import build_source_coverage
    from learnloop.services.coverage_rollup import coverage_rollup

    vault, repository = ctx.require_vault()
    source_set = _source_set_or_error(vault, params.source_set_id)
    coverage = build_source_coverage(repository, vault, source_set)
    coverage["rollup"] = coverage_rollup(vault, repository, source_set)
    return versioned({"coverage": coverage})


def _validated_brief(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Strict brief validation at the RPC boundary (typed error, camel→snake)."""

    from learnloop.services.brief import BriefValidationError, validate_brief

    try:
        return validate_brief(raw, strict=True)
    except BriefValidationError as exc:
        raise SidecarError("invalid_brief", f"Invalid brief: {exc}") from exc


class CreateStudyMapInput(ParamsModel):
    source_set_id: str
    mode: str = "auto"
    brief: dict[str, Any] = {}
    apply: bool = False
    create_goal: bool = False
    unlimited_token_budget: bool = False


@method("create_study_map", CreateStudyMapInput)
def create_study_map(ctx: SidecarContext, params: CreateStudyMapInput) -> dict[str, Any]:
    """Bootstrap synthesis: brief -> gated dependency-closed study map (§8, M6).

    The proposal is left for review unless ``apply`` is set (which requires the
    vault at mvp-0.7; a legacy vault refuses acceptance with a typed reason)."""

    from learnloop.services.source_set_synthesis import StudyMapError
    from learnloop.services.source_set_synthesis import create_study_map as run_create_study_map
    from learnloop_sidecar.handlers.ai_providers import ready_canonical_ingest_provider

    vault, repository = ctx.require_vault()
    _source_set_or_error(vault, params.source_set_id)
    _provider, runtime, client = ready_canonical_ingest_provider(vault)
    if client is None:
        raise SidecarError(
            "provider_unavailable",
            runtime.message or "AI provider is unavailable for synthesis.",
            retryable=True,
        )
    try:
        result = run_create_study_map(
            vault.root,
            params.source_set_id,
            client=client,
            brief=_validated_brief(params.brief),
            mode=params.mode,
            apply=params.apply,
            create_goal=params.create_goal,
            repository=repository,
            unlimited_token_budget=params.unlimited_token_budget,
        )
    except StudyMapError as exc:
        raise SidecarError(exc.code, str(exc), details={"diagnostics": exc.diagnostics, "lockReasons": exc.lock_reasons})
    if params.apply:
        ctx.reload(maintenance=False)
    return versioned({"studyMap": result.as_dict()})


class BuildStudyMapInput(ParamsModel):
    source_set_id: str
    brief: dict[str, Any] = {}
    mode: str = "auto"
    inventory_output_tokens: int | None = None
    unlimited_token_budget: bool = False


@method("build_study_map", BuildStudyMapInput)
def build_study_map_rpc(ctx: SidecarContext, params: BuildStudyMapInput) -> dict[str, Any]:
    """Enqueue a mode-aware study-map build batch for a collection (§1/§8/§10),
    surfaced as a durable Activity batch. This is the in-app, multi-member
    counterpart to Quick add's confirm step (which is single-source).

    Routing mirrors the CLI's ``--mode auto``: when the subject has no live study
    map this BOOTSTRAPS (inventory every member's scoped units, then
    ``bootstrap_synthesis`` over the set). When a map already exists this APPENDS —
    it inventories only the NEW (not-yet-synthesized) members and reconciles them
    into the existing map through the bounded affected neighborhood, never resending
    or rebuilding the map. Members added in the app aren't inventoried yet, so the
    batch inventories first and synthesis gates run once."""

    from learnloop.services.source_append import subject_has_applied_study_map
    from learnloop.services.source_outline import resolve_extraction_id

    vault, repository = ctx.require_vault()
    if not params.unlimited_token_budget:
        _validate_inventory_output_budget(params.inventory_output_tokens)
    source_set = _source_set_or_error(vault, params.source_set_id)
    if not source_set.members:
        raise SidecarError("empty_source_set", "This collection has no members to synthesize.")

    resolved_mode = params.mode
    if resolved_mode == "auto":
        resolved_mode = "append" if subject_has_applied_study_map(vault, source_set.subject_id) else "bootstrap"

    members_payload: list[dict[str, Any]] = []
    new_revision_ids: list[str] = []
    for member in source_set.members:
        extraction_id = resolve_extraction_id(repository, member.revision_id)
        if extraction_id is None:
            raise SidecarError(
                "extraction_not_found",
                f"No extraction resolves for revision '{member.revision_id}'.",
            )
        scope_units = [scope.unit_id for scope in member.scope]
        if not scope_units:
            ir = repository.load_document_ir(extraction_id)
            if ir is not None:
                scope_units = [unit.unit_id for unit in ir.units]
        role_overrides = {s.unit_id: s.role_override for s in member.scope if s.role_override}
        units = [
            {"unit_id": unit_id, "role": role_overrides.get(unit_id) or member.default_role}
            for unit_id in scope_units
        ]
        if not units:
            raise SidecarError(
                "no_units",
                f"Member '{member.source_id}' has no units to inventory.",
            )
        entry = {"extraction_id": extraction_id, "units": units}
        # A member is "new / not yet synthesized" when its revision carries no unit
        # inventories yet — the in-app add path leaves them un-inventoried, so this
        # cleanly scopes the append to freshly added material.
        is_new = not repository.unit_inventories_for_revision(member.revision_id)
        if resolved_mode == "bootstrap" or is_new:
            members_payload.append(entry)
        if is_new:
            new_revision_ids.append(member.revision_id)

    if resolved_mode == "append":
        batch_id = ctx.ingest_jobs.enqueue_source_set_append(
            members=members_payload,
            source_set_id=params.source_set_id,
            new_revision_ids=new_revision_ids or None,
            subject_id=source_set.subject_id,
            brief=_validated_brief(params.brief),
            input_budget_tokens=vault.config.ingest.budgets.inventory_input_tokens,
            output_budget_tokens=params.inventory_output_tokens,
            unlimited_token_budget=params.unlimited_token_budget,
        )
    else:
        batch_id = ctx.ingest_jobs.enqueue_source_set_build(
            members=members_payload,
            source_set_id=params.source_set_id,
            subject_id=source_set.subject_id,
            brief=_validated_brief(params.brief),
            mode=params.mode,
            input_budget_tokens=vault.config.ingest.budgets.inventory_input_tokens,
            output_budget_tokens=params.inventory_output_tokens,
            unlimited_token_budget=params.unlimited_token_budget,
        )
    batch_view = ctx.ingest_jobs.get_batch(batch_id) or {}
    batch_view["mode"] = resolved_mode
    return versioned(batch_view)


class AppendSourceInput(ParamsModel):
    source_set_id: str
    new_revision_ids: list[str] | None = None
    change_kind: str = "source_added"
    brief: dict[str, Any] = {}
    auto_apply: bool = True
    unlimited_token_budget: bool = False


@method("append_source", AppendSourceInput)
def append_source_rpc(ctx: SidecarContext, params: AppendSourceInput) -> dict[str, Any]:
    """Update study map: bounded affected-neighborhood append reconciliation (§10)."""

    from learnloop.services.source_append import append_source as run_append
    from learnloop.services.source_set_synthesis import StudyMapError
    from learnloop_sidecar.handlers.ai_providers import ready_canonical_ingest_provider

    vault, repository = ctx.require_vault()
    _source_set_or_error(vault, params.source_set_id)
    _provider_name, runtime, client = ready_canonical_ingest_provider(vault)
    if client is None:
        raise SidecarError(
            "provider_unavailable",
            runtime.message or "AI provider is unavailable for append.",
            retryable=True,
        )
    try:
        result = run_append(
            vault.root, params.source_set_id, client=client, brief=_validated_brief(params.brief),
            new_revision_ids=params.new_revision_ids, change_kind=params.change_kind,
            auto_apply=params.auto_apply, repository=repository,
            unlimited_token_budget=params.unlimited_token_budget,
        )
    except StudyMapError as exc:
        raise SidecarError(exc.code, str(exc), details={"diagnostics": exc.diagnostics})
    if result.auto_applied_item_ids:
        ctx.reload(maintenance=False)
    return versioned({"append": result.as_dict()})


class RefreshRevisionInput(ParamsModel):
    source_set_id: str
    source_id: str
    old_revision_id: str
    new_revision_id: str
    new_extraction_id: str | None = None
    confirm: bool = False


@method("refresh_revision", RefreshRevisionInput)
def refresh_revision_rpc(ctx: SidecarContext, params: RefreshRevisionInput) -> dict[str, Any]:
    """Adopt a new source revision (§10.4). Pinned membership advances only on confirm."""

    from learnloop.services.revision_refresh import refresh_revision
    from learnloop_sidecar.handlers.ai_providers import ready_canonical_ingest_provider

    vault, repository = ctx.require_vault()
    _source_set_or_error(vault, params.source_set_id)
    client = None
    if params.confirm:
        _provider_name, runtime, client = ready_canonical_ingest_provider(vault)
        if client is None:
            raise SidecarError(
                "provider_unavailable",
                runtime.message or "AI provider is unavailable for revision refresh.",
                retryable=True,
            )
    result = refresh_revision(
        vault.root, params.source_set_id, source_id=params.source_id,
        old_revision_id=params.old_revision_id, new_revision_id=params.new_revision_id,
        new_extraction_id=params.new_extraction_id, confirm=params.confirm,
        client=client, repository=repository,
    )
    if params.confirm:
        ctx.reload(maintenance=False)
    return versioned({"refresh": result.as_dict()})


class ExamReadinessInput(ParamsModel):
    subject_id: str | None = None


@method("exam_readiness", ExamReadinessInput)
def exam_readiness_rpc(ctx: SidecarContext, params: ExamReadinessInput) -> dict[str, Any]:
    """Lightweight deterministic exam-readiness-by-task-family report (§15)."""

    from learnloop.services.exam_readiness import exam_readiness_report

    vault, repository = ctx.require_vault()
    report = exam_readiness_report(vault, repository, subject_id=params.subject_id)
    return versioned({"report": report.as_dict()})


class SourceOutcomesInput(ParamsModel):
    subject_id: str | None = None


@method("source_outcomes", SourceOutcomesInput)
def source_outcomes_rpc(ctx: SidecarContext, params: SourceOutcomesInput) -> dict[str, Any]:
    """Provenance-outcome associations (§11) — report-only, additive suggestions."""

    from learnloop.services.source_outcome_analytics import analyze_source_outcomes

    vault, repository = ctx.require_vault()
    report = analyze_source_outcomes(vault, repository, subject_id=params.subject_id)
    return versioned({"report": report.as_dict()})


class MaintenanceFeedInput(ParamsModel):
    subject_id: str | None = None


@method("maintenance_feed", MaintenanceFeedInput)
def maintenance_feed_rpc(ctx: SidecarContext, params: MaintenanceFeedInput) -> dict[str, Any]:
    """Generate + return the maintenance feed (§11), deterministic from state."""

    from learnloop.services.maintenance_feed import generate_maintenance_feed

    vault, repository = ctx.require_vault()
    from learnloop.services.forecast_ledger import resolve_due_forecasts

    resolve_due_forecasts(repository)
    feed = generate_maintenance_feed(vault, repository)
    if params.subject_id is not None:
        feed = [n for n in feed if n.get("subject_id") in (None, params.subject_id)]
    return versioned({"notices": feed})


class MaintenanceNoticeActionInput(ParamsModel):
    notice_id: str
    action: Literal["dismiss", "snooze"]
    snoozed_until: str | None = None


@method("maintenance_notice_action", MaintenanceNoticeActionInput)
def maintenance_notice_action_rpc(ctx: SidecarContext, params: MaintenanceNoticeActionInput) -> dict[str, Any]:
    """Dismiss or snooze a notice WITHOUT changing source or curriculum state (§11)."""

    from learnloop.services.maintenance_feed import dismiss_notice, snooze_notice

    _vault, repository = ctx.require_vault()
    if params.action == "dismiss":
        dismiss_notice(repository, params.notice_id)
    else:
        snooze_notice(repository, params.notice_id, until=params.snoozed_until)
    return versioned({"notice": repository.maintenance_notice(params.notice_id)})


class ListConflictsInput(ParamsModel):
    status: str = "open"


@method("list_source_conflicts", ListConflictsInput)
def list_source_conflicts_rpc(ctx: SidecarContext, params: ListConflictsInput) -> dict[str, Any]:
    """List source conflicts by status (§10.2) for the conflict review surface.

    Each side is enriched with its resolved ``extraction_id`` (from the cited
    revision) so the client can open both bounded spans side by side through the
    M6-UX ``get_span_view``/Open-in-source viewer."""

    from learnloop.services.source_outline import resolve_extraction_id

    _vault, repository = ctx.require_vault()
    conflicts = repository.source_conflicts_by_status(params.status)
    extraction_cache: dict[str, str | None] = {}

    def _extraction_for(revision_id: str | None) -> str | None:
        if not revision_id:
            return None
        if revision_id not in extraction_cache:
            extraction_cache[revision_id] = resolve_extraction_id(repository, revision_id)
        return extraction_cache[revision_id]

    for conflict in conflicts:
        conflict["left_extraction_id"] = _extraction_for(conflict.get("left_revision_id"))
        conflict["right_extraction_id"] = _extraction_for(conflict.get("right_revision_id"))
    return versioned({"conflicts": conflicts})


class ResolveConflictInput(ParamsModel):
    conflict_id: str
    resolution_kind: str
    resolution: dict[str, Any] = {}
    rationale: str | None = None


@method("resolve_source_conflict", ResolveConflictInput)
def resolve_source_conflict_rpc(ctx: SidecarContext, params: ResolveConflictInput) -> dict[str, Any]:
    """Resolve an open conflict (§10.2) — never applies either competing side."""

    from learnloop.services.conflict_resolution import ConflictResolutionError, conflict_with_audit, resolve_conflict

    _vault, repository = ctx.require_vault()
    try:
        resolve_conflict(repository, params.conflict_id, resolution_kind=params.resolution_kind,
                         resolution=dict(params.resolution or {}), actor="user", rationale=params.rationale)
    except ConflictResolutionError as exc:
        raise SidecarError("conflict_resolution_failed", str(exc))
    return versioned({"conflict": conflict_with_audit(repository, params.conflict_id)})


class PlanQuickAddInput(ParamsModel):
    source: str
    subject_id: str | None = None
    brief: dict[str, Any] = {}


class ConfirmQuickAddInput(ParamsModel):
    source: str
    subject_id: str
    brief: dict[str, Any] = {}
    role_override: str | None = None
    inventory_output_tokens: int | None = None
    unlimited_token_budget: bool = False
    # Per-source reader participation chosen in the quick-add compose (None =
    # no opinion; keeps the source's existing/default setting).
    reader_enabled: bool | None = None


@method("plan_quick_add", PlanQuickAddInput)
def plan_quick_add_rpc(ctx: SidecarContext, params: PlanQuickAddInput) -> dict[str, Any]:
    """Quick add step 1 (§1): the single-confirmation plan for an imported source.

    Pure — reads the extracted outline, ToC-selects the relevant scope, suggests a
    role, fills a default brief, and estimates tokens. ``quick_add_requires_import``
    (retryable) means the source must be imported first."""

    from learnloop.services.quick_add import QuickAddError, plan_quick_add

    vault, repository = ctx.require_vault()
    if params.subject_id is not None and params.subject_id not in vault.subjects:
        raise SidecarError("unknown_subject", f"Subject '{params.subject_id}' does not exist.")
    try:
        plan = plan_quick_add(
            repository,
            vault.config,
            vault,
            params.source.strip(),
            subject_id=params.subject_id,
            brief_overrides=_validated_brief(params.brief),
        )
    except QuickAddError as exc:
        raise SidecarError(
            exc.code,
            str(exc),
            details=exc.details,
            retryable=exc.code == "quick_add_requires_import",
        ) from exc
    return versioned({"plan": plan.as_dict()})


@method("confirm_quick_add", ConfirmQuickAddInput)
def confirm_quick_add_rpc(ctx: SidecarContext, params: ConfirmQuickAddInput) -> dict[str, Any]:
    """Quick add step 2 (§1): the post-confirmation step. Re-plans deterministically
    (honouring an edited role/brief), creates the source set, and enqueues the
    priority [inventory(selected) -> bootstrap_synthesis] build batch."""

    from learnloop.services.quick_add import QuickAddError, enqueue_quick_add, plan_quick_add

    vault, repository = ctx.require_vault()
    if not params.unlimited_token_budget:
        _validate_inventory_output_budget(params.inventory_output_tokens)
    if params.subject_id not in vault.subjects:
        raise SidecarError("unknown_subject", f"Subject '{params.subject_id}' does not exist.")
    try:
        plan = plan_quick_add(
            repository,
            vault.config,
            vault,
            params.source.strip(),
            subject_id=params.subject_id,
            brief_overrides=_validated_brief(params.brief),
        )
        result = enqueue_quick_add(
            vault,
            ctx.ingest_jobs,
            plan,
            role_override=params.role_override,
            output_budget_tokens=params.inventory_output_tokens,
            unlimited_token_budget=params.unlimited_token_budget,
        )
        if params.reader_enabled is not None:
            resolved = resolve_source(params.source.strip())
            artifact = repository.source_artifact_by_uri(resolved.category, resolved.source)
            if artifact is not None:
                repository.set_source_reader_enabled(artifact["id"], params.reader_enabled)
    except QuickAddError as exc:
        raise SidecarError(
            exc.code,
            str(exc),
            details=exc.details,
            retryable=exc.code == "quick_add_requires_import",
        ) from exc
    ctx.reload(maintenance=False)
    return versioned(
        {
            "quickAdd": result,
            "batch": ctx.ingest_jobs.get_batch(result["batch_id"]),
            "confirmation": plan.confirmation(),
        }
    )


@method("start_inventory", StartInventoryInput)
def start_inventory(ctx: SidecarContext, params: StartInventoryInput) -> dict[str, Any]:
    """Enqueue a role-aware unit-inventory batch (§7). Cache hits cost zero tokens."""

    vault, repository = ctx.require_vault()
    if not params.unlimited_token_budget:
        _validate_inventory_output_budget(params.inventory_output_tokens)
    extraction_id = resolve_extraction_id(repository, params.extraction_ref)
    if extraction_id is None:
        raise SidecarError("extraction_not_found", f"No extraction resolves for '{params.extraction_ref}'.")
    if not params.units:
        raise SidecarError("no_units", "start_inventory requires at least one unit.")
    batch_id = ctx.ingest_jobs.enqueue_inventory(
        extraction_id=extraction_id,
        units=params.units,
        subject_id=params.subject_id,
        source_set_id=params.source_set_id,
        input_budget_tokens=vault.config.ingest.budgets.inventory_input_tokens,
        output_budget_tokens=params.inventory_output_tokens,
        unlimited_token_budget=params.unlimited_token_budget,
    )
    return versioned(ctx.ingest_jobs.get_batch(batch_id))


def _validate_inventory_output_budget(value: int | None) -> None:
    if value is not None and not 1_000 <= value <= 100_000:
        raise SidecarError(
            "invalid_inventory_budget",
            "Inventory output budget must be between 1,000 and 100,000 tokens per unit.",
        )


def _artifact_title(artifact: dict[str, Any], revision: dict[str, Any] | None) -> str:
    display_title = artifact.get("display_title")
    if isinstance(display_title, str) and display_title.strip():
        return display_title
    if revision is not None and revision.get("original_uri"):
        return str(revision["original_uri"])
    return str(artifact.get("canonical_uri") or artifact["id"])


def _reload_completed_jobs(ctx: SidecarContext, jobs: list[dict[str, Any]]) -> None:
    completed = [job["id"] for job in jobs if ctx.ingest_jobs.needs_reload(job["id"])]
    if not completed:
        return
    ctx.reload(maintenance=False)
    for job_id in completed:
        ctx.ingest_jobs.mark_reloaded(job_id)


def _note_path_from_ref(ref: Any) -> str | None:
    if not isinstance(ref, dict) or ref.get("ref_type") != "canonical_source":
        return None
    path = ref.get("path")
    if not isinstance(path, str) or not path:
        return None
    # Unresolved-locator refs suffix the note path with "#<detail>".
    return path.split("#", 1)[0]


@method("get_recent_ingests")
def get_recent_ingests(ctx: SidecarContext, _params) -> dict[str, Any]:
    """Canonical-source notes staged by `learnloop ingest` / `ingest-exam`.

    One entry per canonical_source note, newest first, joined against the
    proposal batch that the ingest produced (when one exists) so the UI can
    distinguish exam ingests and deep-link into the Proposals screen.
    """

    vault, repository = ctx.require_vault()

    batch_by_note_path: dict[str, dict[str, Any]] = {}
    for batch in repository.proposal_batches():
        if batch.get("purpose") not in {"canonical_ingest", "exam_ingest"}:
            continue
        for ref in batch.get("source_refs") or []:
            path = _note_path_from_ref(ref)
            # proposal_batches() is newest-first; keep the newest batch per note.
            if path and path not in batch_by_note_path:
                batch_by_note_path[path] = batch

    entries: list[dict[str, Any]] = []
    for note in vault.notes.values():
        if note.source_type != "canonical_source":
            continue
        metadata = getattr(note, "model_extra", {}) or {}
        canonical_source = metadata.get("canonical_source")
        if not isinstance(canonical_source, dict):
            canonical_source = {}
        batch = batch_by_note_path.get(note.path or "")
        entries.append(
            {
                "note_id": note.id,
                "path": note.path,
                "subject_id": note.subjects[0] if note.subjects else None,
                "title": canonical_source.get("title") or note.id,
                "kind": canonical_source.get("kind"),
                "canonical_uri": canonical_source.get("canonical_uri"),
                "authors": canonical_source.get("authors") or [],
                "retrieved_at": canonical_source.get("retrieved_at"),
                "created_at": note.created_at,
                "patch_id": batch["id"] if batch else None,
                "purpose": batch["purpose"] if batch else "canonical_ingest",
            }
        )

    entries.sort(key=lambda e: e.get("created_at") or e.get("retrieved_at") or "", reverse=True)
    return versioned({"ingests": entries[:_RECENT_LIMIT]})
