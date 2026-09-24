---
title: "learnloop.content.pipeline.runner"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/pipeline/runner.py"
source_paths:
  - "src/learnloop/content/pipeline/runner.py"
source_commit: "workspace/uncommitted @ HEAD df970cd96725b112447395846bb53a0164a5853c"
source_commit_timestamp: "2026-09-23T20:46:40-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-09-23"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.pipeline.runner` exists within [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] to own the behavior summarized by its module contract: Durable ingest runner (spec_source_ingestion_v2 §6.2).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py) |
| Source lines | 1065 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD df970cd96725b112447395846bb53a0164a5853c` |
| Commit timestamp | `2026-09-23T20:46:40-04:00` |

## Public API

- `effective_ingest_job_status(job: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 84) — The status to present for a job, correcting contradictory rung rows.
- `class IngestRunnerError(ValueError)` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 136) — A typed, user-actionable job failure persisted for the Activity UI.
  - `__init__(self, message: str, *, code: str='invalid_job', details: Mapping[str, Any] | None=None, retryable: bool=False) -> None` (line 139; internal)
- `class JobCancelled(Exception)` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 153) — Raised from ``report()`` when a cancellation was requested mid-stage.
- `class WaitingForInput(Exception)` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 157) — A handler pauses the job pending user input (unit choice, consent, budget).
  - `__init__(self, payload: Mapping[str, Any], *, message: str='Waiting for input') -> None` (line 163; internal)
- `class FetchedBytes` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 170)
- `class RunnerServices` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 184) — The side-effecting seams the M2 handlers need.
  - `fetch_bytes(self, source: str, category: str, ctx: 'JobContext') -> FetchedBytes` (line 207; public)
  - `extract_ir(self, fetched: FetchedBytes, category: str, ctx: 'JobContext') -> Any` (line 210; public)
  - `extraction_identity(self, fetched: FetchedBytes, category: str, ctx: 'JobContext') -> Mapping[str, Any]` (line 213; public)
  - `legacy_ingest(self, **kwargs: Any) -> Any` (line 220; public)
  - `inventory_identity(self, ctx: 'JobContext') -> tuple[str, str] | None` (line 225; public) — Return cache identity without initializing a provider when possible.
  - `inventory_client(self, ctx: 'JobContext', *, bind_interruptible: bool=True) -> Any` (line 234; public)
  - `synthesis_client(self, ctx: 'JobContext') -> Any` (line 250; public)
  - `quick_check_client(self, ctx: 'JobContext') -> Any` (line 257; public)
  - `rung_variant_client(self, ctx: 'JobContext') -> Any` (line 265; public)
  - `promotion_analysis_client(self, ctx: 'JobContext') -> Any` (line 273; public)
  - `promotion_authoring_client(self, ctx: 'JobContext') -> Any` (line 281; public)
  - `exercise_import_client(self, ctx: 'JobContext') -> Any` (line 289; public)
  - `animation_client(self, ctx: 'JobContext') -> Any` (line 300; public)
  - `video_client(self, ctx: 'JobContext') -> Any` (line 305; public) — The text-to-video client for [animation] renderer = "video_model".
- `class JobContext` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 325) — What a handler is handed: repository, vault root, payload, and the checkpoint/usage/cancellation primitives the runner threads through.
  - `payload(self) -> dict[str, Any]` (line 340; public)
  - `job_id(self) -> str` (line 344; public)
  - `owner(self) -> JobOwner` (line 348; public)
  - `report(self, phase: str, *, message: str | None=None, current_window: int | None=None, total_windows: int | None=None) -> None` (line 351; public) — Advance the checkpoint ladder and refresh the lease heartbeat.
  - `record_usage(self, usage: Mapping[str, Any]) -> None` (line 380; public) — Add one call's usage to the running per-attempt sum (§6.2).
  - `cancelled(self) -> bool` (line 389; public)
  - `bind_interruptible(self, client: Any) -> None` (line 392; public) — Expose a job-scoped provider's interrupt hook to the worker host.
  - `_cancel_requested(self) -> bool` (line 398; internal)
- `class JobSpec` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 410) — One job in an enqueued batch.
- `class IngestRunner` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 464)
  - `__init__(self, repo: Repository, *, vault_root: Path, worker_id: str, clock: Clock | None=None, handlers: Mapping[str, Handler] | None=None, services: RunnerServices | None=None, lease_ttl_seconds: int=120, heartbeat_interval_seconds: float=15) -> None` (line 465; internal)
  - `active_interruptible_jobs(self) -> list[dict[str, Any]]` (line 499; public) — Return running jobs that currently own an interruptible AI client.
  - `interrupt_job(self, job_id: str) -> bool` (line 515; public) — Cancel a batch and interrupt the selected job's active provider call.
  - `_bind_job_interruptible(self, job_id: str, attempt_count: int, client: Any) -> None` (line 531; internal)
  - `_clear_job_interruptible(self, job_id: str, attempt_count: int) -> None` (line 538; internal)
  - `enqueue_batch(self, workflow_type: str, jobs: Sequence[JobSpec], *, subject_id: str | None=None, source_set_id: str | None=None, priority: int=0) -> str` (line 544; public)
  - `recover_stale_leases(self) -> list[str]` (line 589; public) — Startup recovery (§6.2), run when a host opens the vault.
  - `_expire_stale_leases(self, *, lock_timeout_s: float) -> list[str] | None` (line 610; internal) — Expire running leases older than the TTL, or return None if the vault lock stayed busy for ``lock_timeout_s``.
  - `_expire_stale_leases_locked(self) -> list[str]` (line 622; internal)
  - `_finalize_abandoned_synthesis_runs_locked(self) -> None` (line 648; internal) — Finalize non-terminal synthesis runs older than the lease cutoff.
  - `_lease_expiry_due(self) -> bool` (line 667; internal)
  - `run_next(self, *, eligible_job_types: Sequence[str] | None=None, compatible_running_job_types: Sequence[str]=(), allow_parallel: bool=False, max_parallel: int | None=None) -> bool` (line 673; public) — Claim and run one eligible job.
  - `drain(self, *, max_jobs: int | None=None, eligible_job_types: Sequence[str] | None=None, compatible_running_job_types: Sequence[str]=(), allow_parallel: bool=False, max_parallel: int | None=None) -> int` (line 712; public) — Drain matching jobs until none remain (or ``max_jobs``).
  - `cancel_batch(self, batch_id: str) -> None` (line 737; public) — Request cancellation.
  - `resume_batch(self, batch_id: str) -> None` (line 755; public) — Resume a partially-complete or cancelled batch: only unfinished jobs (failed/blocked/cancelled) are re-queued; completed jobs are preserved, so a resume creates new attempts only for what did not finish (§6.2).
  - `_run_claimed(self, job: dict[str, Any]) -> None` (line 790; internal)
  - `_heartbeat_while_running(self, job_id: str, stop: threading.Event, owner: JobOwner) -> None` (line 930; internal) — Keep a blocking extractor/LLM stage's lease alive until it returns.
  - `_propagate_blocks(self, batch_id: str) -> None` (line 957; internal) — Mark every downstream queued job blocked when a dependency failed, blocked, or was cancelled — to a fixpoint (§6.2).
  - `_refresh_batch(self, batch_id: str) -> None` (line 985; internal)
  - `_lease_cutoff_iso(self) -> str` (line 1001; internal)
- `derive_batch_status(jobs: Sequence[Mapping[str, Any]], batch: Mapping[str, Any] | None) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 1014) — Batch status is derived from its member jobs and can represent partial completion (§6.2).

### Module constants

- `CHECKPOINT_LADDER` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 55)
- `TERMINAL_STATUSES` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 65)
- `_UNFINISHED_STATUSES` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 66)
- `_LOG` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 68)
- `_HEARTBEAT_RETRY_SECONDS` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 73)
- `_LEASE_EXPIRY_INTERVAL_SECONDS` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 76)
- `_LEASE_LOCK_TIMEOUT_S` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 80)
- `_TICK_EXPIRY_LOCK_TIMEOUT_S` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 81)
- `KNOWN_WORKFLOW_TYPES` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 105)
- `KNOWN_JOB_TYPES` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 108)
- `_QUEUE_AFFECTING_JOB_TYPES` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 125)
- `_LIVE_ATTEMPTS` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 456)
- `_PHASE_MESSAGES` ([src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py), line 1039)

## Internal implementation anchors

- `_job_defaults() -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 311) — Load concrete ingest jobs only when a default seam is actually used.
- `class _LiveAttempts` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 419) — Job attempts whose handler is executing in this process.
- `class _FixedClock` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 1007)
- `_phase_message(phase: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 1050)
- `_as_number(value: Any) -> float | int` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 1054)
- `_error_code(exc: Exception) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/runner.py), line 1060)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `JobSpec`; statically calls `JobSpec`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `IngestRunner`; statically calls `IngestRunner`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `CHECKPOINT_LADDER`, `FetchedBytes`, `Handler`, `IngestRunner`, `IngestRunnerError`, `JobCancelled`, `JobContext`, `JobSpec`, `RunnerServices`, `WaitingForInput`, `derive_batch_status`, `effective_ingest_job_status`; statically calls `FetchedBytes`, `IngestRunner`, `IngestRunnerError`, `JobCancelled`, `JobSpec`, `derive_batch_status`, `effective_ingest_job_status`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `record_model_calls`; calls `record_model_calls`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `interrupt_callback`; calls `interrupt_callback`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `utc_now_iso`; calls `SystemClock`, `utc_now_iso`
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

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_concept_animation_service.py](../../../../../../../tests/test_concept_animation_service.py) — direct import
  - `test_runner_handler_drives_generation_through_the_queue`
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
- [tests/test_model_work_checkpoints.py](../../../../../../../tests/test_model_work_checkpoints.py) — direct import
  - `test_ingest_job_and_direct_inventory_key_windows_identically`
- [tests/test_question_promotion_jobs.py](../../../../../../../tests/test_question_promotion_jobs.py) — direct import
  - `test_queue_revision_advances_after_promotion_job_is_completed`
- [tests/test_quick_add.py](../../../../../../../tests/test_quick_add.py) — direct import
  - `test_quick_add_batches_take_queue_priority`
- [tests/test_sidecar_goals.py](../../../../../../../tests/test_sidecar_goals.py) — direct import
  - `test_create_goal_enqueues_durable_population_batch`
- [tests/test_source_ingestion_v2lite.py](../../../../../../../tests/test_source_ingestion_v2lite.py) — direct import
  - `test_legacy_path_without_ir_unchanged`
  - `test_v2lite_batch_persists_ir_and_synthesizes_over_its_rendering`
  - `test_v2lite_synthesis_respects_persisted_unit_selection`
- [tests/test_source_inventory.py](../../../../../../../tests/test_source_inventory.py) — direct import
  - `test_inventory_job_blocks_when_extraction_dependency_fails`
  - `test_inventory_job_caches_zero_tokens_on_hit`
- [tests/test_sqlite_wal_lifecycle.py](../../../../../../../tests/test_sqlite_wal_lifecycle.py) — direct import
  - `test_finished_ingest_batch_truncates_the_wal`
  - `test_ingest_batch_checkpoints_once_when_it_becomes_terminal`

## Modification guidance

- Change runner policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/pipeline/runner.py](../../../../../../../src/learnloop/content/pipeline/runner.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
