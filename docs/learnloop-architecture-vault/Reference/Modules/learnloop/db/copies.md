---
title: "learnloop.db.copies"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/copies.py"
source_paths:
  - "src/learnloop/db/copies.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.copies module"
  - "src/learnloop/db/copies.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db"
---

# `learnloop.db.copies`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/_package|learnloop.db]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.copies` exists within [[Reference/Modules/learnloop/db/_package|learnloop.db]] to own the behavior summarized by its module contract: Copies of SQLite databases and of directory trees that contain them.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/copies.py](../../../../../../src/learnloop/db/copies.py) |
| Source lines | 177 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class DatabaseCopyTimeout(TimeoutError)` ([source](../../../../../../src/learnloop/db/copies.py), line 38) — The source stayed locked past the backup deadline; nothing was copied.
- `backup_database(source_path: Path, destination_path: Path, *, busy_deadline_s: float | None=None) -> None` ([source](../../../../../../src/learnloop/db/copies.py), line 42) — Write a transactionally consistent copy of a database to a new file.
- `is_database_file_name(name: str, database_names: Collection[str]=()) -> bool` ([source](../../../../../../src/learnloop/db/copies.py), line 92)
- `is_companion_file_name(name: str, database_names: Collection[str]=()) -> bool` ([source](../../../../../../src/learnloop/db/copies.py), line 96)
- `copy_tree_without_databases(source_root: Path, destination_root: Path, *, database_names: Collection[str]=(), ignore: IgnoreFunction | None=None, dirs_exist_ok: bool=False) -> list[Path]` ([source](../../../../../../src/learnloop/db/copies.py), line 103) — Copy a directory tree, leaving out every database and companion file.
- `copy_tree_with_databases(source_root: Path, destination_root: Path, *, database_names: Collection[str]=(), ignore: IgnoreFunction | None=None, dirs_exist_ok: bool=False) -> list[Path]` ([source](../../../../../../src/learnloop/db/copies.py), line 137) — Copy a directory tree, copying each database through the backup API.

### Module constants

- `DATABASE_SUFFIX` ([src/learnloop/db/copies.py](../../../../../../src/learnloop/db/copies.py), line 25)
- `BACKUP_BUSY_DEADLINE_S` ([src/learnloop/db/copies.py](../../../../../../src/learnloop/db/copies.py), line 27)
- `_BUSY_RETRY_SLEEP_S` ([src/learnloop/db/copies.py](../../../../../../src/learnloop/db/copies.py), line 28)
- `_SQLITE_BUSY` ([src/learnloop/db/copies.py](../../../../../../src/learnloop/db/copies.py), line 30)
- `_SQLITE_LOCKED` ([src/learnloop/db/copies.py](../../../../../../src/learnloop/db/copies.py), line 31)
- `_RETRIED_STATUSES` ([src/learnloop/db/copies.py](../../../../../../src/learnloop/db/copies.py), line 32)
- `COMPANION_SUFFIXES` ([src/learnloop/db/copies.py](../../../../../../src/learnloop/db/copies.py), line 33)

### Explicit exports

`__all__` declares:

- `BACKUP_BUSY_DEADLINE_S`
- `COMPANION_SUFFIXES`
- `DatabaseCopyTimeout`
- `backup_database`
- `copy_tree_with_databases`
- `copy_tree_without_databases`
- `is_companion_file_name`
- `is_database_file_name`

## Internal implementation anchors

- `_remove_database_files(database_path: Path) -> None` ([source](../../../../../../src/learnloop/db/copies.py), line 87)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `backup_database`, `copy_tree_with_databases`; statically calls `backup_database`, `copy_tree_with_databases`
- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `copy_tree_without_databases`; statically calls `copy_tree_without_databases`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `backup_database`; statically calls `backup_database`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `backup_database`; statically calls `backup_database`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `backup_database`, `copy_tree_with_databases`; statically calls `backup_database`, `copy_tree_with_databases`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] — imports `copy_tree_with_databases`; statically calls `copy_tree_with_databases`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `copy_tree_with_databases`; statically calls `copy_tree_with_databases`
- [[Reference/Modules/learnloop/goals/goal_series|learnloop.goals.goal_series]] — imports `backup_database`; statically calls `backup_database`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `copy_tree_with_databases`, `copy_tree_without_databases`
- [[Reference/Modules/learnloop/substrate/dataset|learnloop.substrate.dataset]] — imports `backup_database`; statically calls `backup_database`

### Repository tooling consumers

- [scripts/benchmark_sqlite_concurrency.py](../../../../../../scripts/benchmark_sqlite_concurrency.py); calls `copy_tree_with_databases`
- [scripts/s0_landing.py](../../../../../../scripts/s0_landing.py); calls `copy_tree_with_databases`
- [scripts/sanitize_migration_head_fixture.py](../../../../../../scripts/sanitize_migration_head_fixture.py); calls `copy_tree_with_databases`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `pathlib`, `shutil`, `sqlite3`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]], [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]], [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]], [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/conftest.py](../../../../../../tests/conftest.py) — direct import
- [tests/helpers.py](../../../../../../tests/helpers.py) — direct import
- [tests/test_ad1_migration.py](../../../../../../tests/test_ad1_migration.py) — direct import
  - `test_the_head_fixture_is_at_head_with_empty_ad1_tables`
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
- [tests/test_ad23_fix_r5.py](../../../../../../tests/test_ad23_fix_r5.py) — direct import
  - `test_with_the_kill_switch_off_today_projects_the_predecessors_blocks`
- [tests/test_ad23_successor.py](../../../../../../tests/test_ad23_successor.py) — direct import
- [tests/test_approach_map_replay.py](../../../../../../tests/test_approach_map_replay.py) — direct import
  - `test_rebuild_and_replay_call_no_model_and_never_read_approach_maps`
- [tests/test_approach_maps_schema.py](../../../../../../tests/test_approach_maps_schema.py) — direct import
  - `test_the_head_fixture_carries_the_empty_table`
  - `test_the_store_refuses_unknown_columns`
- [tests/test_canonical_projection_fold_skip.py](../../../../../../tests/test_canonical_projection_fold_skip.py) — direct import
  - `test_a_database_restored_at_the_same_path_forces_the_fold`
- [tests/test_collection_dataset.py](../../../../../../tests/test_collection_dataset.py) — direct import
  - `test_export_gives_up_on_a_source_locked_after_its_probe_and_removes_the_export`
- [tests/test_connection_reuse.py](../../../../../../tests/test_connection_reuse.py) — direct import
  - `test_the_durability_lane_runs_production_connections_copies_and_fsync`
- [tests/test_curriculum_c1_fix_round4.py](../../../../../../tests/test_curriculum_c1_fix_round4.py) — direct import
  - `test_m3_a_database_restored_at_the_same_path_is_watched_as_the_new_file`
- [tests/test_daily_loop_start_minutes.py](../../../../../../tests/test_daily_loop_start_minutes.py) — direct import
  - `test_the_streak_count_is_unchanged_on_fixture_copies`
  - `test_today_queue_serves_the_same_queue_without_energy_on_fixture_copies`
- [tests/test_daily_plan_kill_switch.py](../../../../../../tests/test_daily_plan_kill_switch.py) — direct import
- [tests/test_decider_agreement.py](../../../../../../tests/test_decider_agreement.py) — direct import
  - `test_agreement_counts_each_ledger_row_once_across_a_review_runs_vault_copy`
- [tests/test_diagnosis_replay.py](../../../../../../tests/test_diagnosis_replay.py) — direct import
  - `test_joint_fixture_rebuild_is_identical_at_the_previous_version`
  - `test_joint_reads_are_untouched_by_the_overlay`
- [tests/test_embedding_store.py](../../../../../../tests/test_embedding_store.py) — direct import
  - `test_replay_preserves_paid_inputs_without_models`
- [tests/test_exam_protection_review.py](../../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_replay_never_reads_the_switch`
- [tests/test_figure_prefetch_migration.py](../../../../../../tests/test_figure_prefetch_migration.py) — direct import
  - `test_237_on_the_head_fixture_copy_adds_only_its_objects`
- [tests/test_forecast_receipts.py](../../../../../../tests/test_forecast_receipts.py) — direct import
  - `test_replay_neither_reads_nor_writes_forecast_receipts`
- [tests/test_held_grade_evidence.py](../../../../../../tests/test_held_grade_evidence.py) — direct import
- [tests/test_help_assists_schema.py](../../../../../../tests/test_help_assists_schema.py) — direct import
  - `test_every_check_value_either_spec_writes_is_admitted_and_nothing_else`
  - `test_the_ledger_keeps_rows_and_an_attached_attempt`
  - `test_the_store_attach_matches_the_submission_key_only`
  - `test_the_store_refuses_unknown_columns`
  - `test_the_workbench_lifecycle_binds_each_deferred_column_once`
- [tests/test_hint_telemetry.py](../../../../../../tests/test_hint_telemetry.py) — direct import
  - `test_rebuild_with_help_assists_populated_calls_no_model_and_never_reads_it`
  - `test_the_report_summarises_any_number_of_rows`
- [tests/test_import_split_parity.py](../../../../../../tests/test_import_split_parity.py) — direct import
  - `test_author_then_write_writes_what_import_exercises_writes`
- [tests/test_intent_recall_targets.py](../../../../../../tests/test_intent_recall_targets.py) — direct import
  - `test_the_anchor_reproduces_every_stored_due_at_on_fixture_copies`
- [tests/test_learner_notes_migration.py](../../../../../../tests/test_learner_notes_migration.py) — direct import
  - `test_229_on_the_durability_lane`
- [tests/test_lp_claim_fixes.py](../../../../../../tests/test_lp_claim_fixes.py) — direct import
  - `test_owner_copies_off_is_the_predecessor_and_on_reports_the_mastery_deltas`
- [tests/test_method_explicit_upgrade.py](../../../../../../tests/test_method_explicit_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mobile_jobs_migration.py](../../../../../../tests/test_mobile_jobs_migration.py) — direct import
- [tests/test_mvp010_upgrade.py](../../../../../../tests/test_mvp010_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp011_upgrade.py](../../../../../../tests/test_mvp011_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp013_upgrade.py](../../../../../../tests/test_mvp013_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp014_upgrade.py](../../../../../../tests/test_mvp014_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp015_upgrade.py](../../../../../../tests/test_mvp015_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp016_upgrade.py](../../../../../../tests/test_mvp016_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp017_route_check_replay.py](../../../../../../tests/test_mvp017_route_check_replay.py) — direct import
- [tests/test_mvp017_upgrade.py](../../../../../../tests/test_mvp017_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp018_upgrade.py](../../../../../../tests/test_mvp018_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp020_upgrade.py](../../../../../../tests/test_mvp020_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp021_upgrade.py](../../../../../../tests/test_mvp021_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
  - `test_migration_200_lets_probe_episodes_record_a_value_stop`
  - `test_the_successor_rebuild_equals_mvp020s_projection`
- [tests/test_mvp022_upgrade.py](../../../../../../tests/test_mvp022_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp023_upgrade.py](../../../../../../tests/test_mvp023_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp024_upgrade.py](../../../../../../tests/test_mvp024_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_pfc_unverified_unassessed.py](../../../../../../tests/test_pfc_unverified_unassessed.py) — direct import
  - `test_joint_fixture_replays_through_the_unchanged_path`
- [tests/test_placement_fixture_copies.py](../../../../../../tests/test_placement_fixture_copies.py) — direct import
- [tests/test_plan_determinism.py](../../../../../../tests/test_plan_determinism.py) — direct import
  - `test_replay_never_reads_the_switch`
- [tests/test_plan_follows_path.py](../../../../../../tests/test_plan_follows_path.py) — direct import
- [tests/test_provenance.py](../../../../../../tests/test_provenance.py) — direct import
  - `test_a_rebuild_never_calls_the_record_and_keeps_its_rows`
- [tests/test_reader_rw3b_migration.py](../../../../../../tests/test_reader_rw3b_migration.py) — direct import
  - `test_the_head_fixture_is_at_head_in_rollback_mode_with_empty_rw3b_tables`
- [tests/test_reader_rw7a_migration.py](../../../../../../tests/test_reader_rw7a_migration.py) — direct import
  - `test_the_head_fixture_is_at_217_in_rollback_mode_with_empty_rw7a_tables`
- [tests/test_reader_session_digests_migration.py](../../../../../../tests/test_reader_session_digests_migration.py) — direct import
  - `test_head_226_upgrades_by_adding_only_227s_objects`
- [tests/test_reading_step_switch.py](../../../../../../tests/test_reading_step_switch.py) — direct import
  - `test_replay_never_reads_the_switch`
- [tests/test_recurrence_commands.py](../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_the_head_fixture_predecessor_to_successor_path`
- [tests/test_regrade_contract_upgrade.py](../../../../../../tests/test_regrade_contract_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_ro1_projection.py](../../../../../../tests/test_ro1_projection.py) — direct import
- [tests/test_ro1_self_report.py](../../../../../../tests/test_ro1_self_report.py) — direct import
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_f5_a_regrade_supersedes_an_mvp017_route_check_verdict`
  - `test_migration_186_keeps_its_trigger_which_nothing_writes_now`
- [tests/test_router_r2a_serving.py](../../../../../../tests/test_router_r2a_serving.py) — direct import
  - `test_switch_off_at_the_successor_serves_the_predecessors_plan_on_fixture_copies`
- [tests/test_router_r2b_serving.py](../../../../../../tests/test_router_r2b_serving.py) — direct import
  - `test_the_switches_at_the_successor_serve_their_predecessors_on_fixture_copies`
- [tests/test_s0_landing.py](../../../../../../tests/test_s0_landing.py) — direct import
  - `test_check_and_verify_after_read_the_database_the_live_vault_config_names`
  - `test_copy_out_and_move_out_refuse_a_vault_root_that_is_a_symlink`
- [tests/test_secondary_attach.py](../../../../../../tests/test_secondary_attach.py) — direct import
  - `test_load_secondary_writes_nothing_where_load_writes`
- [tests/test_sqlite_wal_lifecycle.py](../../../../../../tests/test_sqlite_wal_lifecycle.py) — direct import
  - `test_backup_copies_commits_that_a_byte_copy_of_the_main_file_loses`
  - `test_backup_gives_up_on_a_source_locked_after_its_probe_and_removes_the_copy`
  - `test_backup_refuses_to_overwrite_an_existing_file`
  - `test_tree_copy_backs_up_databases_and_never_copies_companions`
  - `test_tree_copy_without_databases_leaves_out_configured_names`
  - `test_wal_stays_bounded_across_twenty_queue_builds_on_a_fixture_copy`
- [tests/test_teacher_te1_migration.py](../../../../../../tests/test_teacher_te1_migration.py) — direct import
  - `test_234_keeps_every_source_tool_call_row`
- [tests/test_tracked_fixture_databases.py](../../../../../../tests/test_tracked_fixture_databases.py) — direct import
  - `test_no_fixture_companion_file_is_tracked_by_git`
  - `test_tracked_fixture_databases_have_no_pending_wal_frames`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/copies.py](../../../../../../src/learnloop/db/copies.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
