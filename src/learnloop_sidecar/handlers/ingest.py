from __future__ import annotations

from typing import Any, Literal

from learnloop.ingest.models import UnsupportedSourceError
from learnloop.ingest.resolution import resolve_source
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.ingest_jobs import ActiveIngestJobError
from learnloop_sidecar.registry import method

# How many recent ingests the screen shows; the vault keeps everything.
_RECENT_LIMIT = 30


class ClassifyIngestSourceInput(ParamsModel):
    source: str


class StartIngestInput(ParamsModel):
    source: str
    subject_id: str
    mode: Literal["canonical", "exam"] = "canonical"


class IngestJobInput(ParamsModel):
    job_id: str


class StartImportBatchInput(ParamsModel):
    sources: list[str]
    subject_id: str | None = None
    inventory: bool = False


class IngestBatchInput(ParamsModel):
    batch_id: str


class ListIngestBatchesInput(ParamsModel):
    limit: int = 30


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
        job = ctx.ingest_jobs.start(vault.root, source, params.subject_id, params.mode)
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
    for source in sources:
        try:
            resolve_source(source)
        except UnsupportedSourceError as exc:
            raise SidecarError("unsupported_source", str(exc)) from exc
    batch_id = ctx.ingest_jobs.enqueue_import(
        sources, subject_id=params.subject_id, inventory=params.inventory
    )
    return versioned(ctx.ingest_jobs.get_batch(batch_id))


@method("get_ingest_batch", IngestBatchInput)
def get_ingest_batch(ctx: SidecarContext, params: IngestBatchInput) -> dict[str, Any]:
    batch = ctx.ingest_jobs.get_batch(params.batch_id)
    if batch is None:
        raise SidecarError("ingest_batch_not_found", f"Batch '{params.batch_id}' was not found.")
    return versioned(batch)


@method("list_ingest_batches", ListIngestBatchesInput)
def list_ingest_batches(ctx: SidecarContext, params: ListIngestBatchesInput) -> dict[str, Any]:
    return versioned({"batches": ctx.ingest_jobs.list_batches(limit=params.limit)})


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
                "update_available": len(revisions) > 1 and current is not None and current["id"] != revisions[-1]["id"],
            }
        )
    return versioned({"sources": cards})


def _artifact_title(artifact: dict[str, Any], revision: dict[str, Any] | None) -> str:
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
