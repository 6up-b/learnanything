---
title: "learnloop.cli.runtime"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/runtime.py"
source_paths:
  - "src/learnloop/cli/runtime.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.cli"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
aliases:
  - "learnloop.cli.runtime module"
  - "src/learnloop/cli/runtime.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.runtime`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This implementation module supports [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] through internal helpers such as `_root`, `_repository`, `_load_vault_or_exit`, `_contracts_env`, `_split_items`, `_parse_mode_mix`, `_resolve_focus`, `_parse_points`; it does not advertise a standalone public API.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/runtime.py](../../../../../../src/learnloop/cli/runtime.py) |
| Source lines | 852 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

No public top-level function or class definition is declared in this file.

### Module constants

- `_INGEST_SPINNER_FRAMES` ([src/learnloop/cli/runtime.py](../../../../../../src/learnloop/cli/runtime.py), line 112)
- `_INGEST_PROGRESS_EVENT` ([src/learnloop/cli/runtime.py](../../../../../../src/learnloop/cli/runtime.py), line 114)
- `_WRAP_WIDTH` ([src/learnloop/cli/runtime.py](../../../../../../src/learnloop/cli/runtime.py), line 496)
- `_ATTEMPT_COVERED_FIELDS` ([src/learnloop/cli/runtime.py](../../../../../../src/learnloop/cli/runtime.py), line 498)
- `EXAM_SELF_GRADE_REFUSAL` ([src/learnloop/cli/runtime.py](../../../../../../src/learnloop/cli/runtime.py), line 805)

## Internal implementation anchors

- `_root(vault: Path | None) -> Path` ([source](../../../../../../src/learnloop/cli/runtime.py), line 116)
- `_repository(vault_root: Path) -> Repository` ([source](../../../../../../src/learnloop/cli/runtime.py), line 119)
- `_load_vault_or_exit(vault_root: Path, *, json_output: bool=False)` ([source](../../../../../../src/learnloop/cli/runtime.py), line 126)
- `_contracts_env(vault: Path | None)` ([source](../../../../../../src/learnloop/cli/runtime.py), line 136)
- `_split_items(items: str | None) -> list[str] | None` ([source](../../../../../../src/learnloop/cli/runtime.py), line 142)
- `_parse_mode_mix(mode_mix: str | None) -> dict[str, int] | None` ([source](../../../../../../src/learnloop/cli/runtime.py), line 147) — Parse ``--mode-mix`` (e.g.
- `_resolve_focus(loaded, *, focus_concepts: str | None, focus_facets: str | None, from_goal: str | None, json_output: bool) -> tuple[list[str] | None, list[str] | None]` ([source](../../../../../../src/learnloop/cli/runtime.py), line 178) — Merge --focus-concepts/--focus-facets with a goal's concept anchors.
- `_parse_points(value: str | None) -> dict[str, float]` ([source](../../../../../../src/learnloop/cli/runtime.py), line 211)
- `_load_mapping_file(file: Path, *, label: str='file') -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/runtime.py), line 228)
- `_parse_observation_response(response_json: str | None, response_file: Path | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/runtime.py), line 234)
- `_observation_template_yaml(file: Path) -> str` ([source](../../../../../../src/learnloop/cli/runtime.py), line 252)
- `_observation_template_payload(template: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/runtime.py), line 257)
- `_observation_result_payload(result) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/runtime.py), line 271)
- `_json_queue(queue: list) -> dict[str, object]` ([source](../../../../../../src/learnloop/cli/runtime.py), line 279)
- `_provider_for_task(config, task: str, explicit: str | None=None) -> str` ([source](../../../../../../src/learnloop/cli/runtime.py), line 296)
- `_fallback_provider_for_task(config, task: str, explicit: str | None=None) -> str | None` ([source](../../../../../../src/learnloop/cli/runtime.py), line 299)
- `_runtime_for_provider(vault_root: Path, config, provider_name: str)` ([source](../../../../../../src/learnloop/cli/runtime.py), line 303)
- `_client_for_provider(vault_root: Path, config, provider_name: str, *, codex_timeout_seconds: int | None=None)` ([source](../../../../../../src/learnloop/cli/runtime.py), line 306)
- `_ready_provider_for_task(vault_root: Path, config, task: str, explicit: str | None=None, *, codex_timeout_seconds: int | None=None)` ([source](../../../../../../src/learnloop/cli/runtime.py), line 320)
- `_runtime_status_for_cli(provider_name: str, status: str) -> str` ([source](../../../../../../src/learnloop/cli/runtime.py), line 338) — Keep pre-provider-refactor Codex CLI error codes stable.
- `_run_canonical_ingest_command(source: str, *, kind: str, subject: str | None, learning_objects: list[str] | None, goal: str | None, allow_auto_captions: bool | None, instructions: str | None, ai_provider: str | None, json_output: bool, progress_json: bool, vault: Path | None, purpose: str='canonical_ingest', spinner_label: str='Ingesting canonical source', pdf_engine: str | None=None, pdf_use_llm: bool | None=None)` ([source](../../../../../../src/learnloop/cli/runtime.py), line 347)
- `_ingest_runner(vault_root: Path)` ([source](../../../../../../src/learnloop/cli/runtime.py), line 420)
- `_batch_json(runner, batch_id: str, *, batch: dict[str, Any] | None=None, jobs: list[dict[str, Any]] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/runtime.py), line 433)
- `_show_source_set(root: Path, set_id: str, json_output: bool) -> None` ([source](../../../../../../src/learnloop/cli/runtime.py), line 471)
- `_find_goal_or_exit(loaded, goal_id: str)` ([source](../../../../../../src/learnloop/cli/runtime.py), line 489)
- `_echo_practice_attempt(attempt_id: str, payload: dict, repository: Repository) -> None` ([source](../../../../../../src/learnloop/cli/runtime.py), line 523)
- `_echo_causal_episode(episode: dict[str, Any] | None) -> None` ([source](../../../../../../src/learnloop/cli/runtime.py), line 654)
- `_goal_or_exit(loaded, goal_id: str, *, json_output: bool)` ([source](../../../../../../src/learnloop/cli/runtime.py), line 794)
- `_exam_answer_refusal(code: str, message: str, *, json_output: bool) -> None` ([source](../../../../../../src/learnloop/cli/runtime.py), line 810)
- `_stage7_manifest(path: Path) -> Any` ([source](../../../../../../src/learnloop/cli/runtime.py), line 817)
- `_parse_sim_sets(sets: list[str] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/runtime.py), line 823)
- `_sim_run_root(source_root: Path, *, fresh_copy: bool, reset_state: bool) -> Path` ([source](../../../../../../src/learnloop/cli/runtime.py), line 834)
- `_write_or_echo_report(payload: dict, *, json_output: bool, output: Path | None) -> None` ([source](../../../../../../src/learnloop/cli/runtime.py), line 844)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `module`
- [[Reference/Modules/learnloop/cli/calibration|learnloop.cli.calibration]] — imports `module`
- [[Reference/Modules/learnloop/cli/card|learnloop.cli.card]] — imports `module`
- [[Reference/Modules/learnloop/cli/claims|learnloop.cli.claims]] — imports `module`
- [[Reference/Modules/learnloop/cli/clarification|learnloop.cli.clarification]] — imports `module`
- [[Reference/Modules/learnloop/cli/config|learnloop.cli.config]] — imports `module`
- [[Reference/Modules/learnloop/cli/contracts|learnloop.cli.contracts]] — imports `module`
- [[Reference/Modules/learnloop/cli/controller|learnloop.cli.controller]] — imports `module`
- [[Reference/Modules/learnloop/cli/depth|learnloop.cli.depth]] — imports `module`
- [[Reference/Modules/learnloop/cli/diagnosis|learnloop.cli.diagnosis]] — imports `module`
- [[Reference/Modules/learnloop/cli/exam|learnloop.cli.exam]] — imports `module`
- [[Reference/Modules/learnloop/cli/fit|learnloop.cli.fit]] — imports `module`
- [[Reference/Modules/learnloop/cli/goldenpath|learnloop.cli.goldenpath]] — imports `module`
- [[Reference/Modules/learnloop/cli/grading|learnloop.cli.grading]] — imports `module`
- [[Reference/Modules/learnloop/cli/ingest_batches|learnloop.cli.ingest_batches]] — imports `module`
- [[Reference/Modules/learnloop/cli/questions|learnloop.cli.questions]] — imports `module`
- [[Reference/Modules/learnloop/cli/registry|learnloop.cli.registry]] — imports `module`
- [[Reference/Modules/learnloop/cli/sim|learnloop.cli.sim]] — imports `module`
- [[Reference/Modules/learnloop/cli/source_set|learnloop.cli.source_set]] — imports `module`
- [[Reference/Modules/learnloop/cli/surfaces|learnloop.cli.surfaces]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `client_for_provider`, `fallback_provider_for`, `provider_for_task`, `ready_client_for_task`, `runtime_for_provider`; calls `client_for_provider`, `fallback_provider_for`, `provider_for_task`, `ready_client_for_task`, `runtime_for_provider`
- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `legacy_codex_status`; calls `legacy_codex_status`
- [[Reference/Modules/learnloop/attempt_types|learnloop.attempt_types]] — imports `default_attempt_type`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AttemptDraft`, `AttemptValidationError`, `SelfGradeInput`, `complete_attempt_with_ai_fallback`, `complete_attempt_with_codex_fallback`
- [[Reference/Modules/learnloop/attempts/observations|learnloop.attempts.observations]] — imports `ObservationTemplateError`, `parse_template_yaml`, `record_observation`, `register_observation_template`; calls `parse_template_yaml`
- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `run_post_attempt_pipeline`
- [[Reference/Modules/learnloop/cli/render|learnloop.cli.render]] — imports `module`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `CODEX_PROVIDER_NAMES`, `ConfigLoadError`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `DiagnosticPracticePlan`, `PracticeExpansionError`, `build_diagnostic_practice_plan`, `build_goal_practice_plan`, `build_practice_expansion_plan`, `generate_diagnostic_practice_proposal`, `generate_goal_practice_proposal`, `generate_post_probe_practice_proposal`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `IngestRunner`; calls `IngestRunner`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `SourceIngestionError`, `ingest_canonical_source`; calls `ingest_canonical_source`
- [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]] — imports `AuthoringProposal`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `PatchApplicationError`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `accept_items`, `authoring_context_stats`, `build_authoring_context`, `edit_proposal_item`, `generate_authoring_proposal`, `list_proposals`, `persist_authoring_proposal`, `reject_items`
- [[Reference/Modules/learnloop/content/sources/source_refs|learnloop.content.sources.source_refs]] — imports `source_ref_display_dto`
- [[Reference/Modules/learnloop/curriculum/concepts|learnloop.curriculum.concepts]] — imports `ConceptMergeError`, `merge_concepts`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_gate|learnloop.diagnosis.diagnostic_gate]] — imports `BACKFILL_SKIPPED_EXISTING`, `BACKFILL_SKIPPED_UNREGISTERED`, `backfill_discrimination_rows`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `rank_error_type_candidates`
- [[Reference/Modules/learnloop/goals/exam_calibration|learnloop.goals.exam_calibration]] — imports `calibration_report`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `reserve_exam_pool`
- [[Reference/Modules/learnloop/goals/exam_seeding|learnloop.goals.exam_seeding]] — imports `ExamSeedingError`, `exam_ingest_instructions`, `parse_exam_outcomes`, `seed_exam_attempts`
- [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]] — imports `ExamSessionError`, `exam_availability`, `exam_report`, `finish_exam`, `record_exam_answer`, `start_exam`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`
- [[Reference/Modules/learnloop/learner/hypothesis_claims|learnloop.learner.hypothesis_claims]] — imports `export_claim_events`, `purge_claim_events`
- [[Reference/Modules/learnloop/learner/recall_calibration|learnloop.learner.recall_calibration]] — imports `assert_recall_calibration_bands`, `format_recall_calibration_table`, `run_recall_calibration_harness`
- [[Reference/Modules/learnloop/ops/debug_time|learnloop.ops.debug_time]] — imports `DebugAdvanceError`, `advance_vault_days`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `run_doctor`
- [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]] — imports `run_startup_maintenance`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `SchedulerSession`, `build_due_queue`, `explain_practice_item`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `coerce_override_value`, `prepare_run_vault`; calls `coerce_override_value`, `prepare_run_vault`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `rebuild_all_derived_state`
- [[Reference/Modules/learnloop/substrate/shadow_rebuild|learnloop.substrate.shadow_rebuild]] — imports `ShadowRebuildError`, `shadow_rebuild`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `sync_vault_state`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `add_note`, `add_subject`, `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`, `find_vault_root`; calls `VaultPaths`, `find_vault_root`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`, `yaml_to_string`; calls `read_yaml`, `yaml_to_string`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `os`, `pathlib`, `sys`, `tempfile`, `textwrap`, `threading`, `time`, `typing`
- Third party: `pydantic`, `typer`

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cli/calibration|learnloop.cli.calibration]], [[Reference/Modules/learnloop/cli/card|learnloop.cli.card]], [[Reference/Modules/learnloop/cli/claims|learnloop.cli.claims]], [[Reference/Modules/learnloop/cli/clarification|learnloop.cli.clarification]] and 15 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_config_matrix_executes_all_six_production_resolution_paths`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/runtime.py](../../../../../../src/learnloop/cli/runtime.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
