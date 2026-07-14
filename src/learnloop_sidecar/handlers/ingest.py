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
    save_unit_selection,
)
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
    # A build-plan estimate snapshot (§8.6.2) when the batch is started from a plan.
    estimate: dict[str, Any] | None = None


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
        sources, subject_id=params.subject_id, inventory=params.inventory, estimate=params.estimate
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


# ---------------------------------------------------------------------------
# Outline, selection, budget planning, and repair (ING M3, §3/§5.3/§5.7/§8.6)
# ---------------------------------------------------------------------------


class SourceOutlineInput(ParamsModel):
    extraction_ref: str


class SaveUnitSelectionInput(ParamsModel):
    extraction_id: str
    selected_unit_ids: list[str]
    boundary_overrides: list[dict[str, Any]] = []


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
    }
    return versioned(payload)


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
        )
    except SelectionValidationError as exc:
        raise SidecarError("invalid_unit_selection", str(exc)) from exc
    return versioned(
        {
            "extraction_id": params.extraction_id,
            "selected_unit_ids": selection.get("selected_unit_ids", []),
            "boundary_overrides": selection.get("boundary_overrides", []),
            "needs_review": selection.get("needs_review", []),
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


class CreateStudyMapInput(ParamsModel):
    source_set_id: str
    mode: str = "auto"
    brief: dict[str, Any] = {}
    apply: bool = False
    create_goal: bool = False


@method("create_study_map", CreateStudyMapInput)
def create_study_map(ctx: SidecarContext, params: CreateStudyMapInput) -> dict[str, Any]:
    """Bootstrap synthesis: brief -> gated dependency-closed study map (§8, M6).

    The proposal is left for review unless ``apply`` is set (which requires the
    vault at mvp-0.7; a legacy vault refuses acceptance with a typed reason)."""

    from learnloop.services.source_set_synthesis import StudyMapError
    from learnloop.services.source_set_synthesis import create_study_map as run_create_study_map
    from learnloop_sidecar.handlers.ai_providers import _codex_client

    vault, repository = ctx.require_vault()
    _source_set_or_error(vault, params.source_set_id)
    client = _codex_client(vault)
    if client is None:
        raise SidecarError("codex_unavailable", "Codex runtime is unavailable for synthesis.", retryable=True)
    try:
        result = run_create_study_map(
            vault.root,
            params.source_set_id,
            client=client,
            brief=dict(params.brief or {}),
            mode=params.mode,
            apply=params.apply,
            create_goal=params.create_goal,
            repository=repository,
        )
    except StudyMapError as exc:
        raise SidecarError(exc.code, str(exc), details={"diagnostics": exc.diagnostics, "lockReasons": exc.lock_reasons})
    if params.apply:
        ctx.reload(maintenance=False)
    return versioned({"studyMap": result.as_dict()})


class AppendSourceInput(ParamsModel):
    source_set_id: str
    new_revision_ids: list[str] | None = None
    change_kind: str = "source_added"
    brief: dict[str, Any] = {}
    auto_apply: bool = True


@method("append_source", AppendSourceInput)
def append_source_rpc(ctx: SidecarContext, params: AppendSourceInput) -> dict[str, Any]:
    """Update study map: bounded affected-neighborhood append reconciliation (§10)."""

    from learnloop.services.source_append import append_source as run_append
    from learnloop.services.source_set_synthesis import StudyMapError
    from learnloop_sidecar.handlers.ai_providers import _codex_client

    vault, repository = ctx.require_vault()
    _source_set_or_error(vault, params.source_set_id)
    client = _codex_client(vault)
    if client is None:
        raise SidecarError("codex_unavailable", "Codex runtime is unavailable for append.", retryable=True)
    try:
        result = run_append(
            vault.root, params.source_set_id, client=client, brief=dict(params.brief or {}),
            new_revision_ids=params.new_revision_ids, change_kind=params.change_kind,
            auto_apply=params.auto_apply, repository=repository,
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
    from learnloop_sidecar.handlers.ai_providers import _codex_client

    vault, repository = ctx.require_vault()
    _source_set_or_error(vault, params.source_set_id)
    client = _codex_client(vault) if params.confirm else None
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
            brief_overrides=dict(params.brief or {}),
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
    if params.subject_id not in vault.subjects:
        raise SidecarError("unknown_subject", f"Subject '{params.subject_id}' does not exist.")
    try:
        plan = plan_quick_add(
            repository,
            vault.config,
            vault,
            params.source.strip(),
            subject_id=params.subject_id,
            brief_overrides=dict(params.brief or {}),
        )
        result = enqueue_quick_add(vault, ctx.ingest_jobs, plan, role_override=params.role_override)
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
    )
    return versioned(ctx.ingest_jobs.get_batch(batch_id))


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
