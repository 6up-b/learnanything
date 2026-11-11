---
title: "learnloop.content.pipeline.runner"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/pipeline/runner.py"
source_paths:
  - "src/learnloop/content/pipeline/runner.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.pipeline"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.pipeline.runner module"
  - "src/learnloop/content/pipeline/runner.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-pipeline"
---

# `learnloop.content.pipeline.runner`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.pipeline.runner` exists within [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] to own the behavior summarized by its module contract: Durable ingest runner (spec_source_ingestion_v2 §6.2).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py) |
| Source lines | 1261 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `effective_ingest_job_status(job: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 85) — The status to present for a job, correcting contradictory rung rows.
- `class IngestRunnerError(ValueError)` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 145) — A typed, user-actionable job failure persisted for the Activity UI.
  - `__init__(self, message: str, *, code: str='invalid_job', details: Mapping[str, Any] | None=None, retryable: bool=False) -> None` (line 148; internal)
- `class JobCancelled(Exception)` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 162) — Raised from ``report()`` when a cancellation was requested mid-stage.
- `class WaitingForInput(Exception)` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 166) — A handler pauses the job pending user input (unit choice, consent, budget).
  - `__init__(self, payload: Mapping[str, Any], *, message: str='Waiting for input') -> None` (line 172; internal)
- `class FetchedBytes` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 179)
- `class RunnerServices` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 193) — The side-effecting seams the M2 handlers need.
  - `fetch_bytes(self, source: str, category: str, ctx: 'JobContext') -> FetchedBytes` (line 231; public)
  - `extract_ir(self, fetched: FetchedBytes, category: str, ctx: 'JobContext') -> Any` (line 234; public)
  - `extraction_identity(self, fetched: FetchedBytes, category: str, ctx: 'JobContext') -> Mapping[str, Any]` (line 237; public)
  - `legacy_ingest(self, **kwargs: Any) -> Any` (line 244; public)
  - `inventory_identity(self, ctx: 'JobContext') -> tuple[str, str] | None` (line 249; public) — Return cache identity without initializing a provider when possible.
  - `inventory_client(self, ctx: 'JobContext', *, bind_interruptible: bool=True) -> Any` (line 258; public)
  - `synthesis_client(self, ctx: 'JobContext') -> Any` (line 274; public)
  - `quick_check_client(self, ctx: 'JobContext') -> Any` (line 281; public)
  - `rung_variant_client(self, ctx: 'JobContext') -> Any` (line 289; public)
  - `promotion_analysis_client(self, ctx: 'JobContext') -> Any` (line 297; public)
  - `promotion_authoring_client(self, ctx: 'JobContext') -> Any` (line 305; public)
  - `exercise_import_client(self, ctx: 'JobContext') -> Any` (line 313; public)
  - `animation_client(self, ctx: 'JobContext') -> Any` (line 324; public)
  - `video_client(self, ctx: 'JobContext') -> Any` (line 329; public) — The text-to-video client for [animation] renderer = "video_model".
  - `authoring_route(self, ctx: 'JobContext') -> Any` (line 334; public) — The question-writing route an automatic build would use (no model call).
- `class JobContext` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 376) — What a handler is handed: repository, vault root, payload, and the checkpoint/usage/cancellation primitives the runner threads through.
  - `payload(self) -> dict[str, Any]` (line 396; public)
  - `job_id(self) -> str` (line 400; public)
  - `owner(self) -> JobOwner` (line 404; public)
  - `report(self, phase: str, *, message: str | None=None, current_window: int | None=None, total_windows: int | None=None) -> None` (line 407; public) — Advance the checkpoint ladder and refresh the lease heartbeat.
  - `record_usage(self, usage: Mapping[str, Any]) -> None` (line 436; public) — Add one call's usage to the running per-attempt sum (§6.2).
  - `cancelled(self) -> bool` (line 445; public)
  - `bind_interruptible(self, client: Any) -> None` (line 448; public) — Expose a job-scoped provider's interrupt hook to the worker host.
  - `hold(self, scope: AbstractContextManager[Any]) -> Any` (line 454; public) — Enter ``scope`` for the rest of this attempt: the runner exits it when the handler returns or raises (in this thread, so context variables it sets are reset), before the outcome is recorded.
  - `enqueue_batch(self, workflow_type: str, jobs: Sequence['JobSpec'], **kwargs: Any) -> str` (line 463; public) — Queue a follow-up batch through the runner that is running this job.
  - `_cancel_requested(self) -> bool` (line 490; internal)
- `class JobSpec` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 502) — One job in an enqueued batch.
- `class IngestRunner` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 556)
  - `__init__(self, repo: Repository, *, vault_root: Path, worker_id: str, clock: Clock | None=None, handlers: Mapping[str, Handler] | None=None, services: RunnerServices | None=None, lease_ttl_seconds: int=120, heartbeat_interval_seconds: float=15) -> None` (line 557; internal)
  - `active_interruptible_jobs(self) -> list[dict[str, Any]]` (line 591; public) — Return running jobs that currently own an interruptible AI client.
  - `interrupt_job(self, job_id: str, *, alongside: Callable[[], object] | None=None) -> bool` (line 607; public) — Cancel a batch and interrupt the selected job's active provider call.
  - `_bind_job_interruptible(self, job_id: str, attempt_count: int, client: Any) -> None` (line 627; internal)
  - `_clear_job_interruptible(self, job_id: str, attempt_count: int) -> None` (line 634; internal)
  - `enqueue_batch(self, workflow_type: str, jobs: Sequence[JobSpec], *, subject_id: str | None=None, source_set_id: str | None=None, priority: int=0, batch_id: str | None=None, grant: 'plan_fallback.GrantToken | None'=None, origin: str | None=None) -> str` (line 640; public) — ``grant`` / ``origin``: a job's own child build (:meth:`JobContext.enqueue_batch` with ``inherit_grant``); otherwise the batch belongs to the request around this call (``plan_fallback.unit_origin``) and carries its token when that action is granted (``unit_token``).
  - `_enqueue_batch(self, workflow_type: str, jobs: Sequence[JobSpec], *, subject_id: str | None, source_set_id: str | None, priority: int, batch_id: str | None, grant: 'plan_fallback.GrantToken | None'=None, origin: str | None=None) -> str` (line 668; internal)
  - `batch_origin_method(self, batch_id: str) -> str | None` (line 720; public) — The batch's durable action (migration 218), for a batch from before a sidecar restart.
  - `recover_stale_leases(self, *, sweep_abandoned_synthesis: bool=True) -> list[str]` (line 730; public) — Startup recovery (§6.2), run when a host opens the vault.
  - `_expire_stale_leases(self, *, lock_timeout_s: float) -> list[str] | None` (line 759; internal) — Expire running leases older than the TTL, or return None if the vault lock stayed busy for ``lock_timeout_s``.
  - `_expire_stale_leases_locked(self) -> list[str]` (line 771; internal)
  - `_finalize_abandoned_synthesis_runs_locked(self) -> None` (line 797; internal) — Finalize non-terminal synthesis runs older than the lease cutoff.
  - `_lease_expiry_due(self) -> bool` (line 816; internal)
  - `run_next(self, *, eligible_job_types: Sequence[str] | None=None, compatible_running_job_types: Sequence[str]=(), allow_parallel: bool=False, max_parallel: int | None=None) -> bool` (line 822; public) — Claim and run one eligible job.
  - `drain(self, *, max_jobs: int | None=None, eligible_job_types: Sequence[str] | None=None, compatible_running_job_types: Sequence[str]=(), allow_parallel: bool=False, max_parallel: int | None=None) -> int` (line 861; public) — Drain matching jobs until none remain (or ``max_jobs``).
  - `cancel_batch(self, batch_id: str, *, alongside: Callable[[], object] | None=None) -> None` (line 886; public) — Request cancellation.
  - `resume_batch(self, batch_id: str) -> None` (line 914; public) — Resume a partially-complete or cancelled batch: only unfinished jobs (failed/blocked/cancelled) are re-queued; completed jobs are preserved, so a resume creates new attempts only for what did not finish (§6.2).
  - `requeue_failed_unless_cancelled(self, batch_id: str, *, error_code: str) -> bool` (line 950; public) — Requeue the batch's jobs that failed with ``error_code``, only while the batch is not cancelled.
  - `_run_claimed(self, job: dict[str, Any]) -> None` (line 977; internal)
  - `_heartbeat_while_running(self, job_id: str, stop: threading.Event, owner: JobOwner) -> None` (line 1126; internal) — Keep a blocking extractor/LLM stage's lease alive until it returns.
  - `_propagate_blocks(self, batch_id: str) -> None` (line 1153; internal) — Mark every downstream queued job blocked when a dependency failed, blocked, or was cancelled — to a fixpoint (§6.2).
  - `_refresh_batch(self, batch_id: str) -> None` (line 1181; internal)
  - `_lease_cutoff_iso(self) -> str` (line 1197; internal)
- `derive_batch_status(jobs: Sequence[Mapping[str, Any]], batch: Mapping[str, Any] | None) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 1210) — Batch status is derived from its member jobs and can represent partial completion (§6.2).

### Module constants

- `CHECKPOINT_LADDER` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 56)
- `TERMINAL_STATUSES` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 66)
- `_UNFINISHED_STATUSES` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 67)
- `_LOG` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 69)
- `_HEARTBEAT_RETRY_SECONDS` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 74)
- `_LEASE_EXPIRY_INTERVAL_SECONDS` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 77)
- `_LEASE_LOCK_TIMEOUT_S` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 81)
- `_TICK_EXPIRY_LOCK_TIMEOUT_S` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 82)
- `KNOWN_WORKFLOW_TYPES` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 106)
- `KNOWN_JOB_TYPES` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 109)
- `_QUEUE_AFFECTING_JOB_TYPES` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 134)
- `_LIVE_ATTEMPTS` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 548)
- `_PHASE_MESSAGES` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 1235)

## Internal implementation anchors

- `_job_defaults() -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 344) — Load concrete ingest jobs only when a default seam is actually used.
- `_batch_unit(runner: 'IngestRunner', batch_id: str) -> Iterator[None]` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 358) — Run one job of ``batch_id`` as its unit: its token, its action; it may ask only when it has an action (the offer is kept with the batch and relayed by a read that shows the batch).
- `class _LiveAttempts` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 511) — Job attempts whose handler is executing in this process.
- `class _FixedClock` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 1203)
- `_phase_message(phase: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 1246)
- `_as_number(value: Any) -> float | int` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 1250)
- `_error_code(exc: Exception) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 1256)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `JobSpec`; statically calls `JobSpec`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `IngestRunner`; statically calls `IngestRunner`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `IngestRunnerError`, `JobCancelled`, `JobSpec`, `WaitingForInput`; statically calls `IngestRunnerError`, `JobCancelled`, `JobSpec`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `CHECKPOINT_LADDER`, `FetchedBytes`, `Handler`, `IngestRunner`, `IngestRunnerError`, `JobCancelled`, `JobContext`, `JobSpec`, `RunnerServices`, `derive_batch_status`, `effective_ingest_job_status`; statically calls `FetchedBytes`, `IngestRunner`, `IngestRunnerError`, `JobCancelled`, `JobSpec`, `derive_batch_status`, `effective_ingest_job_status`
- [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]] — imports `FetchedBytes`, `IngestRunnerError`; statically calls `FetchedBytes`, `IngestRunnerError`
- [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]] — imports `IngestRunnerError`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `record_model_calls`; calls `record_model_calls`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `batch_grant`, `batch_origin`, `batch_stamp`, `keep_batch_offer`, `note_unit`, `remember_batch_grant`, `unit`, `unit_origin`, `unit_token`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `interrupt_callback`; calls `interrupt_callback`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `utc_now_iso`; calls `SystemClock`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `default_authoring_route`; calls `default_authoring_route`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `module`; calls `append`, `get`, `values`
- [[Reference/Modules/learnloop/db/checkpoint|learnloop.db.checkpoint]] — imports `checkpoint_wal`; calls `checkpoint_wal`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/scopes|learnloop.db.scopes]] — imports `JobOwnershipLost`, `guard_ingest_writes`; calls `JobOwnershipLost`, `guard_ingest_writes`
- [[Reference/Modules/learnloop/db/stores/ingest_queue|learnloop.db.stores.ingest_queue]] — imports `JobOwner`; calls `JobOwner`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `DEFAULT_TIMEOUT_S`, `VaultLockTimeout`, `vault_mutation_lock`; calls `vault_mutation_lock`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `datetime`, `logging`, `pathlib`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_contract_helpers.py](../../../../../../../tests/ad23_contract_helpers.py) — direct import
- [tests/figure_rich_job_helpers.py](../../../../../../../tests/figure_rich_job_helpers.py) — direct import
- [tests/figure_rich_rpc_helpers.py](../../../../../../../tests/figure_rich_rpc_helpers.py) — direct import
- [tests/glm_ocr_helpers.py](../../../../../../../tests/glm_ocr_helpers.py) — direct import
- [tests/ingest_runner_helpers.py](../../../../../../../tests/ingest_runner_helpers.py) — direct import
- [tests/learner_data_relax_2_helpers.py](../../../../../../../tests/learner_data_relax_2_helpers.py) — direct import
- [tests/plan_first_transport_offer_grants_helpers.py](../../../../../../../tests/plan_first_transport_offer_grants_helpers.py) — direct import
- [tests/reread_safety_helpers.py](../../../../../../../tests/reread_safety_helpers.py) — direct import
- [tests/source_vector_backfill_helpers.py](../../../../../../../tests/source_vector_backfill_helpers.py) — direct import
- [tests/test_ad23_fix_r5.py](../../../../../../../tests/test_ad23_fix_r5.py) — direct import
  - `test_a_generation_jobs_commission_expires_seven_days_after_the_job_finished`
- [tests/test_ad23_fix_review.py](../../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_a_serve_commission_queues_its_generation_once_at_its_point`
- [tests/test_ad23_owner_decisions.py](../../../../../../../tests/test_ad23_owner_decisions.py) — direct import
- [tests/test_concept_animation_service.py](../../../../../../../tests/test_concept_animation_service.py) — direct import
  - `test_runner_handler_drives_generation_through_the_queue`
- [tests/test_coverage_on_extract.py](../../../../../../../tests/test_coverage_on_extract.py) — direct import
  - `test_the_handler_is_registered_and_known`
- [tests/test_curriculum_c3_codex_review.py](../../../../../../../tests/test_curriculum_c3_codex_review.py) — direct import
  - `test_the_reader_s_own_import_refuses_a_syllabus_before_any_model_call`
- [tests/test_exam_protection.py](../../../../../../../tests/test_exam_protection.py) — direct import
  - `test_a_reader_check_over_held_out_material_is_refused_before_any_model_call`
  - `test_a_reader_import_of_held_out_material_is_refused_before_any_model_call`
- [tests/test_exam_protection_review.py](../../../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_a_reader_import_of_a_held_out_signal_is_refused`
- [tests/test_figure_rich_failed_correction_durable.py](../../../../../../../tests/test_figure_rich_failed_correction_durable.py) — direct import
  - `test_codex_f4_a_newer_cancelled_correction_still_speaks_for_the_figure_after_500_newer_rich_jobs`
- [tests/test_figure_rich_job.py](../../../../../../../tests/test_figure_rich_job.py) — direct import
  - `test_a_restart_never_wedges_a_row`
- [tests/test_figure_rich_review_fixes.py](../../../../../../../tests/test_figure_rich_review_fixes.py) — direct import
- [tests/test_figure_rich_rpc.py](../../../../../../../tests/test_figure_rich_rpc.py) — direct import
  - `test_an_interrupted_rich_only_build_reads_as_failed_and_rich_retry_requeues_it`
- [tests/test_figures_help_codex_review.py](../../../../../../../tests/test_figures_help_codex_review.py) — direct import
- [tests/test_followups_nov2_figure_provenance.py](../../../../../../../tests/test_followups_nov2_figure_provenance.py) — direct import
  - `test_a_queued_rich_revision_stops_when_an_inherited_input_becomes_protected_while_it_runs`
- [tests/test_glm_ocr.py](../../../../../../../tests/test_glm_ocr.py) — direct import
  - `test_an_image_import_needs_glm_and_reads_with_it`
  - `test_every_glm_ocr_reading_queues_the_source_block_backfill`
  - `test_identity_hashes_the_choice_not_endpoints_prices_or_timeouts`
  - `test_r2_f2_an_import_without_the_ok_reads_locally_and_offers_text_recognition`
  - `test_r2_f2_the_card_reads_it_again_with_text_recognition_after_the_ok`
  - `test_r3_f2_a_scan_or_image_imported_without_the_ok_asks_for_it_on_its_card`
- [tests/test_import_split_parity.py](../../../../../../../tests/test_import_split_parity.py) — direct import
  - `test_the_reader_job_records_an_import_row_and_leaves_the_item_unchanged`
- [tests/test_ingest_jobs.py](../../../../../../../tests/test_ingest_jobs.py) — direct import
  - `test_batch_completion_triggers_one_vault_reload`
  - `test_bind_premarks_previously_completed_apply_jobs`
  - `test_list_batches_bulk_loads_failed_rung_requests`
  - `test_list_batches_bulk_loads_jobs_and_dependencies`
  - `test_plain_retry_clears_candidate_recovery_flags`
  - `test_resume_false_completed_rung_variant_reopens_request`
  - `test_retry_synthesis_can_remove_local_token_ceilings`
  - `test_retry_synthesis_reuses_completed_inventory`
- [tests/test_ingest_latency_journey.py](../../../../../../../tests/test_ingest_latency_journey.py) — direct import
  - `test_background_host_wakes_without_waiting_for_poll_timeout`
- [tests/test_ingest_m3.py](../../../../../../../tests/test_ingest_m3.py) — direct import
  - `test_import_snapshots_build_plan_estimate_into_payload`
  - `test_plain_import_performs_no_external_egress`
  - `test_repair_requires_explicit_consent`
  - `test_targeted_repair_records_consent_and_preserves_unaffected_hashes`
- [tests/test_ingest_ownership.py](../../../../../../../tests/test_ingest_ownership.py) — direct import
  - `test_a_busy_vault_lock_defers_lease_work_instead_of_failing`
  - `test_a_cte_read_is_not_fenced_but_a_cte_write_is`
  - `test_a_replaced_attempt_interrupts_only_its_own_transport`
  - `test_a_replaced_attempt_still_saves_its_paid_checkpoint`
  - `test_a_replaced_ingest_cannot_create_a_subject`
  - `test_a_replaced_ingest_cannot_publish_its_source_note_or_goal_linkage`
  - `test_fast_restart_reconciles_later_expiry_without_replacing_live_work`
  - `test_heartbeat_keeps_renewing_after_a_transient_database_error`
  - `test_late_usage_is_retained_after_takeover_without_restoring_publication_authority`
  - `test_recovery_in_the_same_process_never_fails_a_live_attempt`
  - `test_recovery_rechecks_a_heartbeat_renewed_after_candidate_read`
  - `test_stale_worker_cannot_finish_or_publish_after_replacement`
- [tests/test_ingest_runner.py](../../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_actionable_failure_details_are_persisted_for_activity_ui`
  - `test_append_synthesis_forwards_budget_overrides`
  - `test_append_synthesis_job_is_implemented`
  - `test_append_synthesis_preserves_gate_failure_code_and_diagnostics`
  - `test_audio_extract_routes_transcription_to_time_range_ir`
  - `test_audio_extraction_identity_tracks_model_and_endpoint`
  - `test_audio_import_end_to_end_and_cache_reuse`
  - `test_audio_oversize_rejected_before_any_upload`
  - `test_audio_transcription_mode_uses_endpoint_without_native_route`
  - `test_audio_transcription_unavailable_is_typed_retryable`
  - `test_batch_status_derivation`
  - `test_bootstrap_synthesis_job_validates_payload`
  - `test_cancel_resume_runs_only_unfinished_jobs`
  - `test_checkpoint_ladder_and_window_counts_are_recorded`
  - `test_codex_timeout_releases_lease_and_continues_draining`
  - `test_default_inventory_client_defaults_to_codex_and_errors_when_unavailable`
  - `test_default_synthesis_client_gives_codex_sdk_an_eight_minute_timeout`
  - `test_delete_finished_ingest_batches_removes_queue_history_only`
  - `test_dependency_failure_blocks_downstream`
  - `test_explicit_transcription_route_uses_named_profile_without_legacy_switch`
  - `test_goal_population_handler_generates_and_applies_practice`
  - `test_import_cache_hit_skips_extractor_and_restores_health`
  - `test_import_handler_registers_revision_and_extraction`
  - `test_import_retry_replaces_ir_left_by_interrupted_run`
  - `test_import_retry_reuses_revision_and_extraction`
  - `test_keyed_enqueue_is_atomic_and_recovers_after_restart`
  - `test_lease_expiry_marks_interrupted`
  - `test_legacy_ingest_handler_wraps_pipeline_with_stub_client`
  - `test_long_running_handler_emits_periodic_heartbeats`
  - `test_native_audio_failure_is_typed_and_never_switches_routes`
  - `test_native_audio_route_transcribes_via_chat_provider`
  - `test_native_audio_unready_fails_closed_by_default`
  - `test_native_audio_unready_falls_back_when_opted_in`
  - `test_native_audio_unready_route_is_irrelevant_for_non_chat_containers`
  - `test_native_audio_unsupported_container_falls_back_to_endpoint`
  - `test_native_pdf_engine_extracts_markdown_via_chat_provider`
  - `test_native_pdf_engine_rejects_a_repair_page_range`
  - `test_native_pdf_engine_rejects_page_selection`
  - `test_native_pdf_engine_without_capable_route_is_typed`
  - `test_native_pdf_fallback_when_unavailable_uses_local_with_health_flag`
  - `test_native_pdf_rejects_oversized_file`
  - `test_native_route_takes_precedence_over_openrouter_transcription_setting`
  - `test_openrouter_transcription_missing_key_is_typed`
  - `test_openrouter_transcription_setting_routes_audio_via_chat`
  - `test_openrouter_transcription_unsupported_container_errors`
  - `test_partial_success_preserved_on_batch_failure`
  - `test_public_import_inventory_dependency_resolves_extraction_and_units`
  - `test_queue_survives_restart`
  - `test_quick_check_lane_runs_beside_single_vault_writer_with_bound`
  - `test_retry_usage_accumulates_across_attempts`
  - `test_routed_transcription_keeps_the_chat_upload_size_cap`
  - `test_rung_variant_failed_result_fails_the_durable_job`
  - `test_same_vault_rebind_preserves_kill_codex_interrupt_handle`
  - `test_sidecar_and_cli_never_drain_concurrently`
  - `test_transcription_route_never_falls_back_to_an_unconsented_provider`
  - `test_waiting_for_input_holds_no_lease`
  - `test_web_import_routes_html_normalizer_not_raw_text`
  - `test_youtube_import_routes_caption_cues_to_time_range_ir`
  - `test_youtube_import_stores_display_title_and_labels_transcript_unit`
  - `test_youtube_import_without_metadata_falls_back_to_url`
- [tests/test_ingest_transcripts.py](../../../../../../../tests/test_ingest_transcripts.py) — direct import
  - `test_default_extract_routes_caption_text_to_transcript_ir`
- [tests/test_ingestion_checkpoints.py](../../../../../../../tests/test_ingestion_checkpoints.py) — direct import
  - `test_parallel_inventory_drains_checkpoints_and_stops_new_units_after_failure`
- [tests/test_inventory_merge_parallel.py](../../../../../../../tests/test_inventory_merge_parallel.py) — direct import
  - `test_cache_missed_units_inventory_concurrently`
  - `test_exam_role_merge_group_does_not_fold`
  - `test_full_inventory_cache_hit_never_constructs_provider`
  - `test_merged_inventory_marker_covers_member_units`
  - `test_merged_units_inventory_as_one_call_and_cache_composite`
  - `test_mixed_role_merge_group_does_not_fold`
- [tests/test_inventory_runner_mailbox.py](../../../../../../../tests/test_inventory_runner_mailbox.py) — direct import
  - `test_keyboard_interrupt_during_parallel_inventory_releases_waiting_workers`
  - `test_parallel_inventory_notices_cancellation_without_polling_the_database_constantly`
- [tests/test_keep_local_retired.py](../../../../../../../tests/test_keep_local_retired.py) — direct import
  - `test_an_import_the_retired_choice_refused_offers_to_get_it_ready`
- [tests/test_library_exercises.py](../../../../../../../tests/test_library_exercises.py) — direct import
- [tests/test_local_index.py](../../../../../../../tests/test_local_index.py) — direct import
  - `test_a_deferred_index_job_is_woken_at_its_retry_time`
  - `test_a_queued_index_job_whose_worker_never_started_is_started_by_the_sweep`
  - `test_an_index_obligation_that_cannot_be_queued_fails_the_extraction_retryably`
- [tests/test_mobile_host_coexistence.py](../../../../../../../tests/test_mobile_host_coexistence.py) — direct import
  - `test_capture_host_coexists_without_primary_startup_work`
- [tests/test_mobile_two_process.py](../../../../../../../tests/test_mobile_two_process.py) — direct import
  - `test_the_desktop_and_the_host_coexist_with_no_lost_writes`
- [tests/test_model_work_checkpoints.py](../../../../../../../tests/test_model_work_checkpoints.py) — direct import
  - `test_ingest_job_and_direct_inventory_key_windows_identically`
- [tests/test_plan_first_transport.py](../../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_rr_f2_a_feature_that_needs_its_own_price_is_not_served_by_another_features_grant`
- [tests/test_plan_first_transport_grant_scope.py](../../../../../../../tests/test_plan_first_transport_grant_scope.py) — direct import
  - `test_an_ingest_batch_carries_the_grant_only_when_the_learner_enqueued_it`
  - `test_the_reader_imports_background_key_check_never_uses_the_grant`
- [tests/test_plan_first_transport_offer_grants.py](../../../../../../../tests/test_plan_first_transport_offer_grants.py) — direct import
  - `test_p3_a_batch_asks_on_its_own_and_its_answer_tokens_it`
  - `test_p3_units_get_the_answered_offers_token_and_every_resume_keeps_it`
  - `test_the_hang_guard_cancels_a_blocked_job_and_leaves_no_worker`
- [tests/test_plan_first_transport_offer_grants_r5.py](../../../../../../../tests/test_plan_first_transport_offer_grants_r5.py) — direct import
  - `test_m1_every_relay_path_keeps_its_units_vault_and_epoch`
  - `test_m2_a_batch_resumed_after_a_restart_asks_again_as_its_origin`
  - `test_m3_any_response_that_reports_a_batch_shows_its_offer_once`
- [tests/test_query_student.py](../../../../../../../tests/test_query_student.py) — direct import
  - `test_a_due_replay_is_scheduled_for_a_fully_indexed_library`
- [tests/test_question_promotion_jobs.py](../../../../../../../tests/test_question_promotion_jobs.py) — direct import
  - `test_queue_revision_advances_after_promotion_job_is_completed`
- [tests/test_quick_add.py](../../../../../../../tests/test_quick_add.py) — direct import
  - `test_quick_add_batches_take_queue_priority`
- [tests/test_reader_active_reading.py](../../../../../../../tests/test_reader_active_reading.py) — direct import
  - `test_the_job_refuses_held_out_material_before_any_call`
- [tests/test_reader_passage_check.py](../../../../../../../tests/test_reader_passage_check.py) — direct import
  - `test_a_check_held_past_the_wait_fails_retryably_and_never_completes_without_a_question`
  - `test_a_spend_refusal_says_whether_the_price_is_missing_or_the_check_is_over_its_cap`
  - `test_the_job_fails_closed_with_a_named_reason_when_isolation_is_unavailable`
  - `test_the_job_reports_a_refusal_as_its_error_code_and_sends_nothing`
- [tests/test_reading_hardening_2_fixes.py](../../../../../../../tests/test_reading_hardening_2_fixes.py) — direct import
  - `test_f1_a_foreground_host_starts_no_worker_of_its_own`
  - `test_f1_the_start_and_the_sweep_leave_work_that_cannot_run_alone`
- [tests/test_reading_hardening_landing.py](../../../../../../../tests/test_reading_hardening_landing.py) — direct import
  - `test_the_section_check_job_still_refuses_held_out_material`
- [tests/test_reading_hardening_verify_fixes.py](../../../../../../../tests/test_reading_hardening_verify_fixes.py) — direct import
  - `test_f1_a_cancel_committing_while_a_finished_build_plans_its_follow_on_leaves_nothing_queued`
- [tests/test_reading_request_sweep.py](../../../../../../../tests/test_reading_request_sweep.py) — direct import
  - `test_d_work_the_cli_finishes_leaves_the_request_due_for_the_sweep`
- [tests/test_reread_safety.py](../../../../../../../tests/test_reread_safety.py) — direct import
  - `test_a_retried_import_reads_the_revision_it_registered_not_the_current_one`
  - `test_e1_a_failed_import_of_new_bytes_leaves_the_previous_revision_current`
  - `test_e1_bytes_that_match_nowhere_refuse_plainly_and_register_nothing`
  - `test_f6_an_import_that_reuses_an_older_reading_never_moves_annotations_backward`
- [tests/test_secondary_attach.py](../../../../../../../tests/test_secondary_attach.py) — direct import
- [tests/test_sidecar_goals.py](../../../../../../../tests/test_sidecar_goals.py) — direct import
  - `test_create_goal_enqueues_durable_population_batch`
- [tests/test_source_exercise_rpcs.py](../../../../../../../tests/test_source_exercise_rpcs.py) — direct import
- [tests/test_source_ingestion_v2lite.py](../../../../../../../tests/test_source_ingestion_v2lite.py) — direct import
  - `test_legacy_path_without_ir_unchanged`
  - `test_v2lite_batch_persists_ir_and_synthesizes_over_its_rendering`
  - `test_v2lite_synthesis_respects_persisted_unit_selection`
- [tests/test_source_inventory.py](../../../../../../../tests/test_source_inventory.py) — direct import
  - `test_inventory_job_blocks_when_extraction_dependency_fails`
  - `test_inventory_job_caches_zero_tokens_on_hit`
- [tests/test_source_space_resolver.py](../../../../../../../tests/test_source_space_resolver.py) — direct import
  - `test_ordinary_use_completes_the_loop_opens_ask_citations_and_the_background_refit`
- [tests/test_source_vector_backfill.py](../../../../../../../tests/test_source_vector_backfill.py) — direct import
  - `test_a_backfill_that_cannot_be_queued_fails_the_import_retryably_and_the_retry_queues_it`
  - `test_a_job_queued_before_the_switch_went_off_sends_nothing`
  - `test_an_interruption_right_after_extraction_completes_still_indexes_the_source_on_retry`
- [tests/test_sqlite_wal_lifecycle.py](../../../../../../../tests/test_sqlite_wal_lifecycle.py) — direct import
  - `test_finished_ingest_batch_truncates_the_wal`
  - `test_ingest_batch_checkpoints_once_when_it_becomes_terminal`
- [tests/test_synthesis_sweep_primary_only.py](../../../../../../../tests/test_synthesis_sweep_primary_only.py) — direct import
  - `test_recover_stale_leases_skips_only_the_sweep_when_asked`
- [tests/test_ux_phase1_auto_build.py](../../../../../../../tests/test_ux_phase1_auto_build.py) — direct import
  - `test_a_failed_fetch_says_so_in_one_line`
- [tests/test_ux_phase1_review_fixes.py](../../../../../../../tests/test_ux_phase1_review_fixes.py) — direct import
  - `test_f10_a_books_history_survives_lots_of_other_work`
  - `test_f10_connecting_releases_a_book_however_old_its_wait`
  - `test_f1_sending_a_whole_recording_out_waits_for_its_own_ok`
  - `test_f3_a_planner_that_dies_after_queuing_its_build_is_never_orphaned`
  - `test_f3_rereview_a_link_planner_that_dies_after_queuing_its_build_is_found`
  - `test_f6_failed_chapters_are_built_again_by_build_the_whole_book`
- [tests/test_ux_phase1_usability_round1.py](../../../../../../../tests/test_ux_phase1_usability_round1.py) — direct import
  - `test_a_link_being_fetched_has_a_readable_name`
- [tests/ux_phase1_support.py](../../../../../../../tests/ux_phase1_support.py) — direct import

## Modification guidance

- Change runner policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
