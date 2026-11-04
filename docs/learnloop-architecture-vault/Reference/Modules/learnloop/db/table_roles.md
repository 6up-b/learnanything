---
title: "learnloop.db.table_roles"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/table_roles.py"
source_paths:
  - "src/learnloop/db/table_roles.py"
source_commit: "f5f64a43a037dc77d24058d3432f60b6f6b87a9d"
source_commit_timestamp: "2026-11-04T09:01:45-05:00"
source_worktree_state: "clean"
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
  - "learnloop.db.table_roles module"
  - "src/learnloop/db/table_roles.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db"
---

# `learnloop.db.table_roles`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/_package|learnloop.db]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.table_roles` exists within [[Reference/Modules/learnloop/db/_package|learnloop.db]] to own the behavior summarized by its module contract: Persistent-table roles for migration-head ``state.sqlite``.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/table_roles.py](../../../../../../src/learnloop/db/table_roles.py) |
| Source lines | 778 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `f5f64a43a037dc77d24058d3432f60b6f6b87a9d` |
| Commit timestamp | `2026-11-04T09:01:45-05:00` |

## Public API

- `class TableRole(str, Enum)` ([source](../../../../../../src/learnloop/db/table_roles.py), line 28) — The rebuild policy for one persistent user table.
- `class TableRoleMismatch` ([source](../../../../../../src/learnloop/db/table_roles.py), line 680) — The two directions in which a schema and registry can disagree.
  - `is_complete(self) -> bool` (line 687; public)
- `role_for_table(table_name: str) -> TableRole` ([source](../../../../../../src/learnloop/db/table_roles.py), line 691) — Return ``table_name``'s declared role, raising ``KeyError`` if absent.
- `tables_for_role(role: TableRole) -> frozenset[str]` ([source](../../../../../../src/learnloop/db/table_roles.py), line 697) — Return every table assigned to ``role``.
- `fts5_shadow_table_names(connection: sqlite3.Connection) -> frozenset[str]` ([source](../../../../../../src/learnloop/db/table_roles.py), line 707) — FTS5 shadow tables: implementation storage of a registered virtual table.
- `user_table_names(connection: sqlite3.Connection) -> frozenset[str]` ([source](../../../../../../src/learnloop/db/table_roles.py), line 725) — Read the non-SQLite table names from an open database connection.
- `registry_mismatch(table_names: Iterable[str]) -> TableRoleMismatch` ([source](../../../../../../src/learnloop/db/table_roles.py), line 742) — Compare an observed schema to the declarative registry.
- `assert_complete_registry(table_names: Iterable[str]) -> None` ([source](../../../../../../src/learnloop/db/table_roles.py), line 753) — Raise ``ValueError`` unless observed and registered tables match exactly.

### Module constants

- `_TABLE_ROLE_ITEMS` ([src/learnloop/db/table_roles.py](../../../../../../src/learnloop/db/table_roles.py), line 41)
- `TABLE_ROLES` ([src/learnloop/db/table_roles.py](../../../../../../src/learnloop/db/table_roles.py), line 676)
- `FTS5_SHADOW_SUFFIXES` ([src/learnloop/db/table_roles.py](../../../../../../src/learnloop/db/table_roles.py), line 704)

### Explicit exports

`__all__` declares:

- `TABLE_ROLES`
- `TableRole`
- `TableRoleMismatch`
- `FTS5_SHADOW_SUFFIXES`
- `assert_complete_registry`
- `fts5_shadow_table_names`
- `registry_mismatch`
- `role_for_table`
- `tables_for_role`
- `user_table_names`

## Internal implementation anchors

- `_build_registry(items: tuple[tuple[str, TableRole], ...]) -> dict[str, TableRole]` ([source](../../../../../../src/learnloop/db/table_roles.py), line 662)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `TableRole`, `tables_for_role`; statically calls `tables_for_role`
- [[Reference/Modules/learnloop/db/stores/collection|learnloop.db.stores.collection]] — imports `TABLE_ROLES`, `TableRole`
- [[Reference/Modules/learnloop/goals/goal_series_store|learnloop.goals.goal_series_store]] — imports `role_for_table`, `user_table_names`; statically calls `role_for_table`, `user_table_names`
- [[Reference/Modules/learnloop/ops/debug_time_store|learnloop.ops.debug_time_store]] — imports `role_for_table`, `user_table_names`; statically calls `role_for_table`, `user_table_names`
- [[Reference/Modules/learnloop/substrate/dataset|learnloop.substrate.dataset]] — imports `TABLE_ROLES`, `TableRole`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `TableRole`, `tables_for_role`; statically calls `tables_for_role`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `enum`, `re`, `sqlite3`, `types`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/db/stores/collection|learnloop.db.stores.collection]], [[Reference/Modules/learnloop/goals/goal_series_store|learnloop.goals.goal_series_store]], [[Reference/Modules/learnloop/ops/debug_time_store|learnloop.ops.debug_time_store]], [[Reference/Modules/learnloop/substrate/dataset|learnloop.substrate.dataset]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad1_migration.py](../../../../../../tests/test_ad1_migration.py) — direct import
  - `test_the_ad1_tables_are_classified`
- [tests/test_ad23_migration.py](../../../../../../tests/test_ad23_migration.py) — direct import
  - `test_the_tables_are_classified`
- [tests/test_approach_map_replay.py](../../../../../../tests/test_approach_map_replay.py) — direct import
  - `test_approach_maps_has_no_replayer_and_is_never_cleared`
  - `test_rebuild_and_replay_call_no_model_and_never_read_approach_maps`
- [tests/test_approach_maps_schema.py](../../../../../../tests/test_approach_maps_schema.py) — direct import
  - `test_approach_maps_is_workflow`
- [tests/test_daily_plan_replay.py](../../../../../../tests/test_daily_plan_replay.py) — direct import
  - `test_rebuild_ignores_the_plan_and_calls_no_model`
- [tests/test_data_capture_migration.py](../../../../../../tests/test_data_capture_migration.py) — direct import
  - `test_240_is_the_head_and_its_tables_are_receipts`
- [tests/test_deliverable_curriculum_migration.py](../../../../../../tests/test_deliverable_curriculum_migration.py) — direct import
  - `test_228_is_c0bs_migration_classified_with_no_derived_table`
- [tests/test_diagnosis_input_provenance.py](../../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_f5_replay_never_reads_the_switch_or_the_records`
  - `test_the_records_are_append_only_and_classified`
- [tests/test_diagnosis_replay.py](../../../../../../tests/test_diagnosis_replay.py) — direct import
  - `test_joint_fixture_rebuild_is_identical_at_the_previous_version`
  - `test_split_vault_rebuild_is_a_fixed_point_and_keeps_diagnosis_sourced_causes`
- [tests/test_exam_protection_review.py](../../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_replay_never_reads_the_switch`
- [tests/test_facet_identity_actions.py](../../../../../../tests/test_facet_identity_actions.py) — direct import
  - `test_dataset_exports_keep_the_merge_history_an_undo_removes_from_facet_merges`
- [tests/test_figure_prefetch_migration.py](../../../../../../tests/test_figure_prefetch_migration.py) — direct import
  - `test_237_is_p5s_migration_and_every_table_is_classified`
- [tests/test_figure_requests_migration.py](../../../../../../tests/test_figure_requests_migration.py) — direct import
  - `test_224_is_the_figure_requests_migration_and_the_table_is_a_raw_ledger`
- [tests/test_figures_migration.py](../../../../../../tests/test_figures_migration.py) — direct import
  - `test_the_tables_are_classified`
- [tests/test_followup_migration.py](../../../../../../tests/test_followup_migration.py) — direct import
  - `test_241_exists_and_its_tables_have_their_roles`
- [tests/test_forecast_receipts.py](../../../../../../tests/test_forecast_receipts.py) — direct import
  - `test_replay_neither_reads_nor_writes_forecast_receipts`
- [tests/test_forecast_receipts_landing.py](../../../../../../tests/test_forecast_receipts_landing.py) — direct import
  - `test_the_renumbered_migration_and_its_table_role`
- [tests/test_help_assist_figures_migration.py](../../../../../../tests/test_help_assist_figures_migration.py) — direct import
  - `test_232_is_the_figures_migration_and_help_assists_stays_a_raw_ledger`
- [tests/test_help_assist_work_md_migration.py](../../../../../../tests/test_help_assist_work_md_migration.py) — direct import
  - `test_230_is_the_work_md_migration_and_help_assists_stays_a_raw_ledger`
- [tests/test_help_assists_schema.py](../../../../../../tests/test_help_assists_schema.py) — direct import
  - `test_help_assists_is_a_raw_ledger`
- [tests/test_hint_feedback_widening.py](../../../../../../tests/test_hint_feedback_widening.py) — direct import
  - `test_212_classifies_nothing_new`
- [tests/test_hint_telemetry.py](../../../../../../tests/test_hint_telemetry.py) — direct import
  - `test_rebuild_with_help_assists_populated_calls_no_model_and_never_reads_it`
- [tests/test_learner_gap_unlinked_migration.py](../../../../../../tests/test_learner_gap_unlinked_migration.py) — direct import
  - `test_235_classifies_nothing_new`
- [tests/test_learner_note_source_kind_migration.py](../../../../../../tests/test_learner_note_source_kind_migration.py) — direct import
  - `test_231_classifies_nothing_new`
- [tests/test_learner_notes_migration.py](../../../../../../tests/test_learner_notes_migration.py) — direct import
  - `test_229_is_c2s_migration_classified_with_no_derived_table`
- [tests/test_learner_notes_vault_origin_migration.py](../../../../../../tests/test_learner_notes_vault_origin_migration.py) — direct import
  - `test_233_classifies_nothing_new`
- [tests/test_learner_text_source_widening.py](../../../../../../tests/test_learner_text_source_widening.py) — direct import
  - `test_208_keeps_the_table_roles`
- [tests/test_library_asks_migration.py](../../../../../../tests/test_library_asks_migration.py) — direct import
  - `test_library_asks_is_workflow`
- [tests/test_method_explicit_upgrade.py](../../../../../../tests/test_method_explicit_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mobile_jobs_migration.py](../../../../../../tests/test_mobile_jobs_migration.py) — direct import
  - `test_239_is_named_and_the_table_is_classified`
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
  - `test_the_successor_rebuild_equals_mvp020s_projection`
- [tests/test_mvp022_upgrade.py](../../../../../../tests/test_mvp022_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp023_upgrade.py](../../../../../../tests/test_mvp023_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp024_upgrade.py](../../../../../../tests/test_mvp024_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_plan_determinism.py](../../../../../../tests/test_plan_determinism.py) — direct import
  - `test_replay_never_reads_the_switch`
- [tests/test_plan_follows_path.py](../../../../../../tests/test_plan_follows_path.py) — direct import
  - `test_g47_a_rebuild_shows_zero_projection_deltas_and_never_reads_a_path`
- [tests/test_reader_rw3b_migration.py](../../../../../../tests/test_reader_rw3b_migration.py) — direct import
  - `test_the_rw3b_tables_are_classified`
- [tests/test_reader_rw7a_migration.py](../../../../../../tests/test_reader_rw7a_migration.py) — direct import
  - `test_the_rw7a_tables_are_workflow`
- [tests/test_reader_session_digests_migration.py](../../../../../../tests/test_reader_session_digests_migration.py) — direct import
  - `test_227_is_the_reader_session_digests_migration_and_the_table_is_workflow`
- [tests/test_reader_workbench_rw2a.py](../../../../../../tests/test_reader_workbench_rw2a.py) — direct import
  - `test_both_tables_are_classified_and_never_derived`
- [tests/test_reading_step_switch.py](../../../../../../tests/test_reading_step_switch.py) — direct import
  - `test_replay_never_reads_the_switch`
- [tests/test_rebuild_orchestrator.py](../../../../../../tests/test_rebuild_orchestrator.py) — direct import
  - `test_golden_projection_survives_one_umbrella_rebuild_exactly_and_stale_rows_clear`
  - `test_live_rebuild_completeness_failure_publishes_nothing`
  - `test_live_rebuild_failure_preserves_all_published_state`
  - `test_replayer_registry_owns_each_derived_table_exactly_once`
  - `test_same_version_full_rebuild_is_semantically_idempotent_on_golden_fixture`
- [tests/test_recurrence_commands.py](../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_rebuild_makes_no_model_call_and_is_a_fixed_point`
  - `test_the_head_fixture_predecessor_to_successor_path`
- [tests/test_recurrence_live.py](../../../../../../tests/test_recurrence_live.py) — direct import
  - `test_a_verdict_after_a_promotion_moves_only_the_group_projection_and_rebuild_matches_live`
- [tests/test_regrade_contract_upgrade.py](../../../../../../tests/test_regrade_contract_upgrade.py) — direct import
  - `test_after_the_upgrade_a_rebuild_settles_and_stays`
- [tests/test_retrieval_spaces_migration.py](../../../../../../tests/test_retrieval_spaces_migration.py) — direct import
  - `test_table_roles_and_the_one_replayer`
- [tests/test_router_objective_migration.py](../../../../../../tests/test_router_objective_migration.py) — direct import
  - `test_242_exists_and_its_tables_are_receipts`
- [tests/test_rw2d_receipts_migration.py](../../../../../../tests/test_rw2d_receipts_migration.py) — direct import
  - `test_219_adds_the_receipt_table_and_the_subject_column_and_nothing_else`
- [tests/test_rw5c_migration.py](../../../../../../tests/test_rw5c_migration.py) — direct import
  - `test_238_is_applied_and_the_table_is_classified`
- [tests/test_section_coverage_migration.py](../../../../../../tests/test_section_coverage_migration.py) — direct import
  - `test_table_role_and_ad_classification`
- [tests/test_session_ownership_migration.py](../../../../../../tests/test_session_ownership_migration.py) — direct import
  - `test_226_is_the_session_ownership_migration_and_the_handoffs_are_receipts`
- [tests/test_source_block_fts.py](../../../../../../tests/test_source_block_fts.py) — direct import
  - `test_the_index_is_derived_with_one_owner_and_its_shadow_tables_are_not_tables`
- [tests/test_stuck_prompt_replay.py](../../../../../../tests/test_stuck_prompt_replay.py) — direct import
  - `test_a_stuck_vault_rebuilds_to_a_fixed_point_with_no_model_call`
  - `test_historical_dont_know_rows_replay_unchanged_under_the_successor`
  - `test_the_kill_switch_never_changes_how_stuck_answers_replay`
- [tests/test_table_roles.py](../../../../../../tests/test_table_roles.py) — direct import
  - `test_migration_head_user_tables_match_role_registry_exactly`
  - `test_mixed_authoritative_artifacts_are_not_claimed_as_rebuildable`
  - `test_public_role_helpers_partition_registry`
  - `test_synthetic_unclassified_table_fails_registry_check`
- [tests/test_teacher_te1_migration.py](../../../../../../tests/test_teacher_te1_migration.py) — direct import
  - `test_234_is_te1s_migration_and_every_table_is_classified`
- [tests/test_teacher_te1b_migration.py](../../../../../../tests/test_teacher_te1b_migration.py) — direct import
  - `test_236_is_te1bs_migration_and_its_table_is_classified`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/table_roles.py](../../../../../../src/learnloop/db/table_roles.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
