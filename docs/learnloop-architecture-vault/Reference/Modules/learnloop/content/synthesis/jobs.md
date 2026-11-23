---
title: "learnloop.content.synthesis.jobs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/jobs.py"
source_paths:
  - "src/learnloop/content/synthesis/jobs.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.synthesis"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.synthesis.jobs module"
  - "src/learnloop/content/synthesis/jobs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.jobs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.jobs` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: The unit-inventory and synthesis job types: ``inventory``, ``bootstrap_synthesis`` and ``append_synthesis``, with the inventory and synthesis clients the runner's services fall back on.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/jobs.py](../../../../../../../src/learnloop/content/synthesis/jobs.py) |
| Source lines | 848 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `inventory_client_identity(client: Any) -> tuple[str, str]` ([source](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 36)
- `default_inventory_identity(ctx: JobContext) -> tuple[str, str] | None` ([source](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 43) — Resolve the primary inventory cache key without a runtime probe.
- `default_inventory_client(ctx: JobContext, *, codex_timeout_seconds: int | None=None) -> Any` ([source](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 57) — Resolve the unit-inventory/quick-check client through ai routing (§7).
- `default_synthesis_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 90) — Resolve the canonical-ingest route for judgment-heavy synthesis.
- `handle_inventory(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 255) — inventory: role-aware per-unit inventories for the selected units (§7).
- `handle_bootstrap_synthesis(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 618) — bootstrap_synthesis: N-way study-map synthesis over a source set (ING M6).
- `handle_append_synthesis(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 774) — append_synthesis: bounded reconciliation against an existing study map.

### Module constants

- `_MAX_INVENTORY_WORKERS` ([src/learnloop/content/synthesis/jobs.py](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 28)
- `INGEST_CODEX_TIMEOUT_SECONDS` ([src/learnloop/content/synthesis/jobs.py](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 29)
- `_INVENTORY_CANCEL_POLL_SECONDS` ([src/learnloop/content/synthesis/jobs.py](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 33)
- `_SYNTH_STAGE_PHASE` ([src/learnloop/content/synthesis/jobs.py](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 733)

## Internal implementation anchors

- `_routed_task_client(ctx: JobContext, task: str, *, codex_timeout_seconds: int | None=None) -> Any` ([source](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 106)
- `class _InventoryInterruptGroup` ([source](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 135) — One job-scoped interrupt hook covering its active inventory clients.
- `class _RunnerMailbox` ([source](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 178) — Carry inventory workers' requests to the runner thread and back.
- `_ingest_budgets(ctx: JobContext)` ([source](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 499) — Load vault budgets, retaining service defaults for isolated workers/tests.
- `_inventory_inputs(ctx: JobContext, payload: Mapping[str, Any]) -> tuple[str, list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 511) — Resolve public import→inventory shorthand from the completed dependency.
- `_effective_inventory_inputs(repo: Repository, extraction_id: str, units: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 534) — Fold explicit same-role ``merge_with_next`` groups into one model input.
- `_build_trace_id(ctx: JobContext) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 608) — The trace a synthesis job's decision records (and model receipts) join: the automatic build's planner job when there is one, so its scope, the inventory rows the run read and what it applied answer as one trace in ``learnloop why``; the job itself otherwise.
- `_bootstrap_synthesis(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 633)
- `_synthesis_progress(ctx: JobContext)` ([source](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 741) — A ProgressFn bridging create_study_map to the durable job heartbeat.
- `_record_step(ctx: JobContext, **facts: Any) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 764) — What the job is doing, for a waiting screen (``ingest_job_progress``); never a reason for the job to fail.
- `_append_synthesis(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/jobs.py), line 783)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/jobs|learnloop.content.authoring.jobs]] — imports `_routed_task_client`; statically calls `_routed_task_client`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `observe_model_calls`; calls `observe_model_calls`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `INTERRUPT`, `interrupt_callback`; calls `interrupt_callback`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `IngestBudgetsConfig`; calls `IngestBudgetsConfig`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `AutoApplyGate`, `admit_auto_build_job`, `after_auto_build`; calls `AutoApplyGate`, `admit_auto_build_job`, `after_auto_build`
- [[Reference/Modules/learnloop/content/pipeline/import_jobs|learnloop.content.pipeline.import_jobs]] — imports `_optional_int`; calls `_optional_int`
- [[Reference/Modules/learnloop/content/pipeline/job_contracts|learnloop.content.pipeline.job_contracts]] — imports `IngestRunnerError`, `JobCancelled`; calls `IngestRunnerError`, `JobCancelled`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `JobContext`
- [[Reference/Modules/learnloop/content/sources/role_authority|learnloop.content.sources.role_authority]] — imports `default_inventory_profile`; calls `default_inventory_profile`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `APPEND_INPUT_OVER_CEILING`, `append_source`, `subject_has_applied_study_map`; calls `append_source`, `subject_has_applied_study_map`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `StudyMapError`, `create_study_map`, `revalidate_synthesis_candidate`; calls `create_study_map`, `revalidate_synthesis_candidate`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `InventoryResult`, `PreparedInventory`, `current_inventory_identity`, `execute_prepared_inventory`, `normalize_profile`, `persist_prepared_inventory`, `prepare_unit_inventory`, `window_checkpoint`; calls `current_inventory_identity`, `execute_prepared_inventory`, `normalize_profile`, `persist_prepared_inventory`, `prepare_unit_inventory`, `window_checkpoint`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] — imports `effective_scope_groups`; calls `effective_scope_groups`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `module`; calls `trace_scope`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `concurrent`, `contextvars`, `logging`, `queue`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/jobs|learnloop.content.authoring.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_fix_review.py](../../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_a_commission_queued_before_models_go_off_waits_and_resumes`
- [tests/test_ad23_owner_decisions.py](../../../../../../../tests/test_ad23_owner_decisions.py) — direct import
  - `test_a_cancelled_commission_stays_cancelled_when_models_come_back_on`
  - `test_a_commission_waiting_on_models_stays_open_and_a_cancelled_one_expires`
- [tests/test_ingest_runner.py](../../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_default_inventory_client_defaults_to_codex_and_errors_when_unavailable`
  - `test_default_inventory_client_routes_via_canonical_ingest`
  - `test_default_synthesis_client_resolves_openrouter_in_inherited_new_vault`
- [tests/test_ingestion_checkpoints.py](../../../../../../../tests/test_ingestion_checkpoints.py) — direct import
  - `test_parallel_inventory_drains_checkpoints_and_stops_new_units_after_failure`
- [tests/test_inventory_runner_mailbox.py](../../../../../../../tests/test_inventory_runner_mailbox.py) — direct import
  - `test_keyboard_interrupt_during_parallel_inventory_releases_waiting_workers`
  - `test_parallel_inventory_notices_cancellation_without_polling_the_database_constantly`
- [tests/test_job_types.py](../../../../../../../tests/test_job_types.py) — direct import
  - `test_the_job_contracts_are_one_set_of_objects_through_every_path`
- [tests/test_provider_resolution_parity.py](../../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_config_matrix_executes_all_six_production_resolution_paths`

## Modification guidance

- Change jobs policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/jobs.py](../../../../../../../src/learnloop/content/synthesis/jobs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
