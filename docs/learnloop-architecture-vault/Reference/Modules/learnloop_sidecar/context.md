---
title: "learnloop_sidecar.context"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/context.py"
source_paths:
  - "src/learnloop_sidecar/context.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop_sidecar"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.context module"
  - "src/learnloop_sidecar/context.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.context`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps context behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]]. Its public surface centers on `SidecarContext`, `vault_summary`, `config_dto`, `available_grading_providers`, `runtime_health`, `session_snapshot`, `checkpoint_dto`, `teach_back_envelope` and 1 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/context.py](../../../../../src/learnloop_sidecar/context.py) |
| Source lines | 566 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class SidecarContext` ([source](../../../../../src/learnloop_sidecar/context.py), line 31)
  - `load(self, vault_path: str | Path, *, maintenance: bool=True) -> None` (line 45; public)
  - `reload(self, *, maintenance: bool=True) -> None` (line 82; public)
  - `refresh_vault_files(self, relative_paths: list[str], *, expected_root: str | Path | None=None) -> dict[str, Any]` (line 87; public) — Incrementally refresh watcher-reported Practice Item files.
  - `require_vault(self) -> tuple[LoadedVault, Repository]` (line 266; public)
  - `app_snapshot(self) -> dict[str, Any]` (line 271; public)
- `vault_summary(vault: LoadedVault) -> dict[str, Any]` ([source](../../../../../src/learnloop_sidecar/context.py), line 288)
- `config_dto(vault: LoadedVault) -> dict[str, Any]` ([source](../../../../../src/learnloop_sidecar/context.py), line 308)
- `available_grading_providers(vault: LoadedVault) -> list[str]` ([source](../../../../../src/learnloop_sidecar/context.py), line 373) — Selectable grading backends: configured AI providers, legacy codex, manual.
- `runtime_health(vault: LoadedVault, repository: Repository, grading_override: str | None=None) -> dict[str, Any]` ([source](../../../../../src/learnloop_sidecar/context.py), line 380)
- `session_snapshot(repository: Repository, session_id: str) -> dict[str, Any] | None` ([source](../../../../../src/learnloop_sidecar/context.py), line 476)
- `checkpoint_dto(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../src/learnloop_sidecar/context.py), line 495)
- `teach_back_envelope(current_answer: Any) -> dict[str, Any] | None` ([source](../../../../../src/learnloop_sidecar/context.py), line 524) — Parse a teach-back conversation envelope from checkpoint current_answer.
- `mastery_dto(repository: Repository, learning_object_id: str, vault: LoadedVault | None=None) -> dict[str, Any] | None` ([source](../../../../../src/learnloop_sidecar/context.py), line 548)

## Internal implementation anchors

- `_settings_ready(vault: LoadedVault) -> bool` ([source](../../../../../src/learnloop_sidecar/context.py), line 411) — Whether every distinct provider the app routes to is configured/ready.
- `_ai_health(vault: LoadedVault, grading_override: str | None) -> dict[str, Any]` ([source](../../../../../src/learnloop_sidecar/context.py), line 431) — The health.ai dto, honoring the runtime grading override.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `SidecarContext`, `available_grading_providers`; statically calls `available_grading_providers`
- [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/app|learnloop_sidecar.handlers.app]] — imports `SidecarContext`, `config_dto`, `runtime_health`, `vault_summary`; statically calls `config_dto`, `runtime_health`, `vault_summary`
- [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/claims|learnloop_sidecar.handlers.claims]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/cli|learnloop_sidecar.handlers.cli]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnostic|learnloop_sidecar.handlers.diagnostic]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/facets|learnloop_sidecar.handlers.facets]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path|learnloop_sidecar.handlers.golden_path]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path_assessment|learnloop_sidecar.handlers.golden_path_assessment]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/graph|learnloop_sidecar.handlers.graph]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/graph_edit|learnloop_sidecar.handlers.graph_edit]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/inspector|learnloop_sidecar.handlers.inspector]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_model|learnloop_sidecar.handlers.knowledge_model]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/ladder|learnloop_sidecar.handlers.ladder]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/library|learnloop_sidecar.handlers.library]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/proposals|learnloop_sidecar.handlers.proposals]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/provenance|learnloop_sidecar.handlers.provenance]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/registry|learnloop_sidecar.handlers.registry]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/review|learnloop_sidecar.handlers.review]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `mastery_dto`; statically calls `mastery_dto`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `SidecarContext`, `session_snapshot`; statically calls `session_snapshot`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `SidecarContext`, `runtime_health`; statically calls `runtime_health`
- [[Reference/Modules/learnloop_sidecar/handlers/sqlite_admin|learnloop_sidecar.handlers.sqlite_admin]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `SidecarContext`, `teach_back_envelope`; statically calls `teach_back_envelope`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/vault|learnloop_sidecar.handlers.vault]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `SidecarContext`; statically calls `SidecarContext`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`, `runtime_for_provider`; calls `ready_client_for_task`, `runtime_for_provider`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `IngestJobManager`
- [[Reference/Modules/learnloop/db/migrate|learnloop.db.migrate]] — imports `applied_versions`, `discover_migrations`; calls `applied_versions`, `discover_migrations`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `pending_review_instance_ids`; calls `pending_review_instance_ids`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `schedule_certification_cold_probes`; calls `schedule_certification_cold_probes`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `mastery_diagnostic_view`; calls `mastery_diagnostic_view`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `display_mastery`; calls `display_mastery`
- [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]] — imports `run_startup_maintenance`; calls `run_startup_maintenance`
- [[Reference/Modules/learnloop/substrate/canonical_projection_rollout|learnloop.substrate.canonical_projection_rollout]] — imports `refresh_canonical_projection_on_startup`; calls `refresh_canonical_projection_on_startup`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `practice_item_activatable`, `sync_vault_state`; calls `practice_item_activatable`, `sync_vault_state`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `practice_item_hash`; calls `practice_item_hash`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_practice_item_file`, `load_vault`; calls `load_practice_item_file`, `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `to_camel`, `versioned`; calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/exam_grading|learnloop_sidecar.exam_grading]] — imports `ExamGradingManager`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]], [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]], [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]], [[Reference/Modules/learnloop_sidecar/handlers/app|learnloop_sidecar.handlers.app]], [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]] and 36 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_canonical_projection_rollout.py](../../../../../tests/test_canonical_projection_rollout.py) — direct import
  - `test_fresh_startup_stamps_a_silent_projection_baseline_once`
  - `test_projection_upgrade_stays_silent_while_vault_has_no_attempts`
  - `test_startup_records_one_recalibration_for_an_unstamped_practised_vault`
- [tests/test_config_refactor.py](../../../../../tests/test_config_refactor.py) — direct import
  - `test_legacy_codex_is_input_only_and_sidecar_does_not_reexport_it`
- [tests/test_dialogue_causal_join.py](../../../../../tests/test_dialogue_causal_join.py) — direct import
  - `test_submit_eliciting_response_sidecar_method`
- [tests/test_goal_scope_material.py](../../../../../tests/test_goal_scope_material.py) — direct import
- [tests/test_graph_editor_reads.py](../../../../../tests/test_graph_editor_reads.py) — direct import
- [tests/test_ingest_jobs.py](../../../../../tests/test_ingest_jobs.py) — direct import
  - `test_batch_completion_triggers_one_vault_reload`
- [tests/test_ingest_latency_journey.py](../../../../../tests/test_ingest_latency_journey.py) — direct import
  - `test_synthetic_markdown_import_reaches_ready_library_and_outline`
- [tests/test_instrument_servability_journeys.py](../../../../../tests/test_instrument_servability_journeys.py) — direct import
- [tests/test_km2_activation.py](../../../../../tests/test_km2_activation.py) — direct import
  - `test_app_load_repairs_vault_activated_by_old_upgrade`
- [tests/test_sidecar_adjudication.py](../../../../../tests/test_sidecar_adjudication.py) — direct import
- [tests/test_sidecar_exams.py](../../../../../tests/test_sidecar_exams.py) — direct import
  - `test_exam_submit_advances_before_background_grade_finishes`
  - `test_finished_report_carries_per_item_feedback_and_repairs`
- [tests/test_sidecar_goals.py](../../../../../tests/test_sidecar_goals.py) — direct import
- [tests/test_sidecar_item_authoring.py](../../../../../tests/test_sidecar_item_authoring.py) — direct import
  - `test_retire_rpc_updates_cached_vault_without_global_reload`
- [tests/test_sidecar_item_presentation.py](../../../../../tests/test_sidecar_item_presentation.py) — direct import
- [tests/test_sidecar_measurement.py](../../../../../tests/test_sidecar_measurement.py) — direct import
  - `test_generate_commissioning_practice_treats_an_empty_queue_as_success`
- [tests/test_sidecar_trace_and_clarification.py](../../../../../tests/test_sidecar_trace_and_clarification.py) — direct import
- [tests/test_sidecar_transport.py](../../../../../tests/test_sidecar_transport.py) — direct import
  - `test_duplicate_method_registration_fails_loudly`
  - `test_unexpected_handler_failure_marks_the_commit_outcome_unknown`
- [tests/test_vault_watcher_refresh.py](../../../../../tests/test_vault_watcher_refresh.py) — direct import
  - `test_non_item_watch_refresh_returns_the_updated_application_snapshot`
  - `test_practice_item_deletion_deactivates_cached_serving_state`
  - `test_practice_item_watch_refresh_is_incremental`
  - `test_watch_refresh_rejects_an_event_from_the_previously_selected_vault`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/context.py](../../../../../src/learnloop_sidecar/context.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
