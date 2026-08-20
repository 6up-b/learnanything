---
title: "learnloop_sidecar.handlers.ingest"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/ingest.py"
source_paths:
  - "src/learnloop_sidecar/handlers/ingest.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop_sidecar.handlers.ingest module"
  - "src/learnloop_sidecar/handlers/ingest.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.ingest`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps ingest behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]]. Its public surface centers on `validate_budget`, `validated_budget_overrides`, `ClassifyIngestSourceInput`, `StartIngestInput`, `IngestJobInput`, `SourcePageRangeInput`, `StartImportBatchInput`, `IngestBatchInput` and 69 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/ingest.py](../../../../../../src/learnloop_sidecar/handlers/ingest.py) |
| Source lines | 1446 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `validate_budget(field: str, value: int | None) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 53) — Raise a typed error when a ceiling falls outside its accepted range.
- `validated_budget_overrides(overrides: dict[str, int] | None) -> dict[str, int]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 73) — Accept only the plan-charted ceilings, each within its bounds.
- `class ClassifyIngestSourceInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 93)
- `class StartIngestInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 97)
- `class IngestJobInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 106)
- `class SourcePageRangeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 110)
- `class StartImportBatchInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 118)
- `class IngestBatchInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 140)
- `class ListIngestBatchesInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 144)
- `class RetrySynthesisInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 148)
- `classify_ingest_source(_ctx: SidecarContext, params: ClassifyIngestSourceInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 164)
- `start_ingest(ctx: SidecarContext, params: StartIngestInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 173)
- `get_ingest_job(ctx: SidecarContext, params: IngestJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 199)
- `get_ingest_jobs(ctx: SidecarContext, _params) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 208)
- `cancel_ingest(ctx: SidecarContext, params: IngestJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 215)
- `start_import_batch(ctx: SidecarContext, params: StartImportBatchInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 228)
- `get_ingest_batch(ctx: SidecarContext, params: IngestBatchInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 321)
- `list_ingest_batches(ctx: SidecarContext, params: ListIngestBatchesInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 330)
- `cancel_ingest_batch(ctx: SidecarContext, params: IngestBatchInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 361)
- `resume_ingest_batch(ctx: SidecarContext, params: IngestBatchInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 369)
- `retry_synthesis(ctx: SidecarContext, params: RetrySynthesisInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 377) — Requeue only a failed synthesis job with revised execution ceilings.
- `get_synthesis_candidate(ctx: SidecarContext, params: IngestBatchInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 415) — Summarize the preserved synthesis candidate behind a failed batch (§8).
- `get_source_library(ctx: SidecarContext, _params) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 465) — The Source library card grid (§5.7): one card per artifact fed by the M1 artifact/revision/extraction tables — title, readiness/health line, suggested role, and an update-available placeholder.
- `class SourceDeletionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 510)
- `preview_source_deletion(ctx: SidecarContext, params: SourceDeletionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 515) — What deleting this source would remove, cost, and currently block (§4.1).
- `delete_source(ctx: SidecarContext, params: SourceDeletionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 533) — Delete an imported source and everything derived from it (§4.1).
- `class SourceOutlineInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 559)
- `class SaveUnitSelectionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 563)
- `class AcquisitionPreviewInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 570)
- `class BuildPlanSelection(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 574)
- `class BuildPlanInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 579)
- `class StartExtractionRepairInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 587)
- `get_source_outline(ctx: SidecarContext, params: SourceOutlineInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 597) — Deterministic outline of a source's extraction (zero agent runs, §3/§5.7).
- `class SelectionPreviewInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 619)
- `get_selection_preview(ctx: SidecarContext, params: SelectionPreviewInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 625) — Byte-exact display markdown for a unit selection — the same ``render_ir_markdown`` output synthesis feeds the model (§2.3), so the learner can inspect what the LLM will see before starting a batch.
- `class EffectiveOutlineInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 656)
- `get_effective_outline(ctx: SidecarContext, params: EffectiveOutlineInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 662) — Deterministic effective-unit shape after boundary overrides (§5.3).
- `save_unit_selection_rpc(ctx: SidecarContext, params: SaveUnitSelectionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 682) — Persist per-extraction unit selection + boundary overrides (§5.3).
- `get_acquisition_preview(ctx: SidecarContext, params: AcquisitionPreviewInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 708) — Deterministic acquisition preview — no downloads/extraction/LLM (§8.6.1).
- `get_build_plan(ctx: SidecarContext, params: BuildPlanInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 717) — Deterministic build plan with per-stage token estimates (§8.6.2).
- `start_extraction_repair(ctx: SidecarContext, params: StartExtractionRepairInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 739) — Enqueue a consent-gated extraction-repair batch (§2.5).
- `class ListSourceSetsInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 763)
- `class SourceSetRefInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 767)
- `class SourceSetScopeParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 771)
- `class SourceSetMemberParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 776)
- `class UpsertSourceSetInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 784)
- `class StartInventoryInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 791)
- `list_source_sets(ctx: SidecarContext, _params: ListSourceSetsInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 808) — List source collections (§4.3).
- `get_source_set(ctx: SidecarContext, params: SourceSetRefInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 823) — Show a collection's members, roles, and scopes (§4.3).
- `upsert_source_set_rpc(ctx: SidecarContext, params: UpsertSourceSetInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 832) — Create or update a collection; membership owns role/scope/priority (§4.3).
- `get_source_coverage(ctx: SidecarContext, params: SourceSetRefInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 851) — Deterministic coverage + readiness preview for a collection (§9.3).
- `class CreateStudyMapInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 875)
- `create_study_map(ctx: SidecarContext, params: CreateStudyMapInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 885) — Bootstrap synthesis: brief -> gated dependency-closed study map (§8, M6).
- `class BuildStudyMapInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 923)
- `build_study_map_rpc(ctx: SidecarContext, params: BuildStudyMapInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 935) — Enqueue a mode-aware study-map build batch for a collection (§1/§8/§10), surfaced as a durable Activity batch.
- `class AppendSourceInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1040)
- `append_source_rpc(ctx: SidecarContext, params: AppendSourceInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1050) — Update study map: bounded affected-neighborhood append reconciliation (§10).
- `class RefreshRevisionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1080)
- `refresh_revision_rpc(ctx: SidecarContext, params: RefreshRevisionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1090) — Adopt a new source revision (§10.4).
- `class ExamReadinessInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1118)
- `exam_readiness_rpc(ctx: SidecarContext, params: ExamReadinessInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1123) — Lightweight deterministic exam-readiness-by-task-family report (§15).
- `class SourceOutcomesInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1133)
- `source_outcomes_rpc(ctx: SidecarContext, params: SourceOutcomesInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1138) — Provenance-outcome associations (§11) — report-only, additive suggestions.
- `class MaintenanceFeedInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1148)
- `maintenance_feed_rpc(ctx: SidecarContext, params: MaintenanceFeedInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1153) — Generate + return the maintenance feed (§11), deterministic from state.
- `class MaintenanceNoticeActionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1168)
- `maintenance_notice_action_rpc(ctx: SidecarContext, params: MaintenanceNoticeActionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1175) — Dismiss or snooze a notice WITHOUT changing source or curriculum state (§11).
- `class ListConflictsInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1188)
- `list_source_conflicts_rpc(ctx: SidecarContext, params: ListConflictsInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1193) — List source conflicts by status (§10.2) for the conflict review surface.
- `class ResolveConflictInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1219)
- `resolve_source_conflict_rpc(ctx: SidecarContext, params: ResolveConflictInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1227) — Resolve an open conflict (§10.2) — never applies either competing side.
- `class PlanQuickAddInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1241)
- `class ConfirmQuickAddInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1247)
- `plan_quick_add_rpc(ctx: SidecarContext, params: PlanQuickAddInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1260) — Quick add step 1 (§1): the single-confirmation plan for an imported source.
- `confirm_quick_add_rpc(ctx: SidecarContext, params: ConfirmQuickAddInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1292) — Quick add step 2 (§1): the post-confirmation step.
- `start_inventory(ctx: SidecarContext, params: StartInventoryInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1344) — Enqueue a role-aware unit-inventory batch (§7).
- `get_recent_ingests(ctx: SidecarContext, _params) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1400) — Canonical-source notes staged by `learnloop ingest` / `ingest-exam`.

### Module constants

- `_RECENT_LIMIT` ([src/learnloop_sidecar/handlers/ingest.py](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 26)
- `BUDGET_BOUNDS` ([src/learnloop_sidecar/handlers/ingest.py](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 33)
- `PLAN_BUDGET_FIELDS` ([src/learnloop_sidecar/handlers/ingest.py](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 44)
- `_BUDGET_FIELD_BY_ALIAS` ([src/learnloop_sidecar/handlers/ingest.py](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 66)

## Internal implementation anchors

- `_contiguous_page_selection(start: int, end: int) -> list[int]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 286)
- `_parse_page_selection(raw: str) -> list[int]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 294)
- `_reload_applied_batches(ctx: SidecarContext, batches: list[dict[str, Any]]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 336) — Refresh the in-memory vault once after a content-applying job completes.
- `_source_set_or_error(vault, set_id: str)` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 800)
- `_validated_brief(raw: dict[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 864) — Strict brief validation at the RPC boundary (typed error, camel→snake).
- `_validate_inventory_output_budget(value: int | None) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1367)
- `_artifact_title(artifact: dict[str, Any], revision: dict[str, Any] | None) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1371)
- `_reload_completed_jobs(ctx: SidecarContext, jobs: list[dict[str, Any]]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1380)
- `_note_path_from_ref(ref: Any) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/ingest.py), line 1389)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `BUDGET_BOUNDS`, `PLAN_BUDGET_FIELDS`, `validated_budget_overrides`; statically calls `validated_budget_overrides`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/pipeline/acquisition_preview|learnloop.content.pipeline.acquisition_preview]] — imports `build_acquisition_preview`; calls `build_acquisition_preview`
- [[Reference/Modules/learnloop/content/pipeline/build_plan|learnloop.content.pipeline.build_plan]] — imports `build_build_plan`; calls `build_build_plan`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `APPLYING_JOB_TYPES`, `ActiveIngestJobError`
- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `QuickAddError`, `enqueue_quick_add`, `plan_quick_add`; calls `enqueue_quick_add`, `plan_quick_add`
- [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]] — imports `refresh_revision`; calls `refresh_revision`
- [[Reference/Modules/learnloop/content/proposals/conflict_resolution|learnloop.content.proposals.conflict_resolution]] — imports `ConflictResolutionError`, `conflict_with_audit`, `resolve_conflict`; calls `conflict_with_audit`, `resolve_conflict`
- [[Reference/Modules/learnloop/content/sources/source_deletion|learnloop.content.sources.source_deletion]] — imports `SourceDeletionError`, `delete_source`, `plan_source_deletion`; calls `delete_source`, `plan_source_deletion`
- [[Reference/Modules/learnloop/content/sources/source_outcome_analytics|learnloop.content.sources.source_outcome_analytics]] — imports `analyze_source_outcomes`; calls `analyze_source_outcomes`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `OutlineNotFound`, `build_source_outline`, `resolve_extraction_id`; calls `build_source_outline`, `resolve_extraction_id`
- [[Reference/Modules/learnloop/content/synthesis/brief|learnloop.content.synthesis.brief]] — imports `BriefValidationError`, `validate_brief`; calls `validate_brief`
- [[Reference/Modules/learnloop/content/synthesis/coverage_rollup|learnloop.content.synthesis.coverage_rollup]] — imports `coverage_rollup`; calls `coverage_rollup`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `append_source`, `subject_has_applied_study_map`; calls `append_source`, `subject_has_applied_study_map`
- [[Reference/Modules/learnloop/content/synthesis/source_coverage|learnloop.content.synthesis.source_coverage]] — imports `build_source_coverage`; calls `build_source_coverage`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `StudyMapError`, `create_study_map`; calls `create_study_map`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] — imports `SelectionValidationError`, `compute_effective_units`, `save_unit_selection`; calls `compute_effective_units`, `save_unit_selection`
- [[Reference/Modules/learnloop/goals/exam_readiness|learnloop.goals.exam_readiness]] — imports `exam_readiness_report`; calls `exam_readiness_report`
- [[Reference/Modules/learnloop/goals/forecast_ledger|learnloop.goals.forecast_ledger]] — imports `resolve_due_forecasts`; calls `resolve_due_forecasts`
- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `render_ir_markdown`; calls `render_ir_markdown`
- [[Reference/Modules/learnloop/ingest/models|learnloop.ingest.models]] — imports `UnsupportedSourceError`
- [[Reference/Modules/learnloop/ingest/resolution|learnloop.ingest.resolution]] — imports `resolve_source`; calls `resolve_source`
- [[Reference/Modules/learnloop/ops/maintenance_feed|learnloop.ops.maintenance_feed]] — imports `dismiss_notice`, `generate_maintenance_feed`, `snooze_notice`; calls `dismiss_notice`, `generate_maintenance_feed`, `snooze_notice`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_source_set`; calls `upsert_source_set`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `camel_name`, `versioned`; calls `camel_name`, `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `ready_canonical_ingest_provider`; calls `ready_canonical_ingest_provider`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_build_study_map_routing.py](../../../../../../tests/test_build_study_map_routing.py) — direct import
  - `test_existing_map_routes_to_append_over_new_members_only`
  - `test_no_map_routes_to_bootstrap_over_all_members`
  - `test_omitted_ceilings_fall_back_to_the_vault_defaults`
  - `test_out_of_range_or_unknown_ceilings_are_refused`
  - `test_per_run_ceilings_split_between_inventory_args_and_synthesis_budgets`
  - `test_unlimited_budget_is_forwarded_to_every_build_stage`
- [tests/test_ingest_jobs.py](../../../../../../tests/test_ingest_jobs.py) — direct import
  - `test_batch_completion_triggers_one_vault_reload`
- [tests/test_ingest_latency_journey.py](../../../../../../tests/test_ingest_latency_journey.py) — direct import
  - `test_synthetic_markdown_import_reaches_ready_library_and_outline`
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_youtube_import_without_metadata_falls_back_to_url`
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_disjoint_pdf_page_expression_normalizes_to_exact_zero_based_pages`
  - `test_invalid_pdf_page_expressions_are_rejected`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/ingest.py](../../../../../../src/learnloop_sidecar/handlers/ingest.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
