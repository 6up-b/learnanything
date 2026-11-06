---
title: "learnloop.db.migrate"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/migrate.py"
source_paths:
  - "src/learnloop/db/migrate.py"
source_commit: "ced3f8ea5c1f7080fb666e90e6e88f8d633eb7a6"
source_commit_timestamp: "2026-10-25T11:47:46-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.migrate module"
  - "src/learnloop/db/migrate.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db"
---

# `learnloop.db.migrate`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/_package|learnloop.db]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps migrate behavior inside its owning package, [[Reference/Modules/learnloop/db/_package|learnloop.db]]. Its public surface centers on `JournalModeSwitchError`, `UncoordinatedMigrationError`, `upgrade_allowance`, `upgrade_authority`, `Migration`, `default_migrations_dir`, `discover_migrations`, `applied_versions` and 4 more public symbols.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/migrate.py](../../../../../../src/learnloop/db/migrate.py) |
| Source lines | 463 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `ced3f8ea5c1f7080fb666e90e6e88f8d633eb7a6` |
| Commit timestamp | `2026-10-25T11:47:46-04:00` |

## Public API

- `class JournalModeSwitchError(RuntimeError)` ([source](../../../../../../src/learnloop/db/migrate.py), line 30) — The database could not be moved to WAL, so its journal mode is unchanged.
- `class UncoordinatedMigrationError(RuntimeError)` ([source](../../../../../../src/learnloop/db/migrate.py), line 34) — An existing database is behind this code's migrations, and only the vault's migration coordinator may upgrade it.
  - `__init__(self, sqlite_path: Path, current: int, pending: list[Migration]) -> None` (line 46; internal)
- `upgrade_allowance(name: str) -> Iterator[str]` ([source](../../../../../../src/learnloop/db/migrate.py), line 82) — Allow upgrades of existing databases in this context (this thread or task), under one of the named allowances, for the ``with`` block only.
- `upgrade_authority() -> str | None` ([source](../../../../../../src/learnloop/db/migrate.py), line 95) — The allowance this context upgrades under, or ``None``.
- `class Migration` ([source](../../../../../../src/learnloop/db/migrate.py), line 102)
- `default_migrations_dir() -> Path` ([source](../../../../../../src/learnloop/db/migrate.py), line 108)
- `discover_migrations(migrations_dir: Path | None=None) -> list[Migration]` ([source](../../../../../../src/learnloop/db/migrate.py), line 112)
- `applied_versions(sqlite_path: Path) -> set[int]` ([source](../../../../../../src/learnloop/db/migrate.py), line 123)
- `schema_is_current(sqlite_path: Path, migrations_dir: Path | None=None) -> bool` ([source](../../../../../../src/learnloop/db/migrate.py), line 136) — Whether an existing database has exactly this code's migrations applied.
- `apply_migrations(sqlite_path: Path, migrations_dir: Path | None=None, clock: Clock | None=None) -> list[Migration]` ([source](../../../../../../src/learnloop/db/migrate.py), line 152) — Create the database, or upgrade it to this code's migrations.
- `create_or_attach_current(sqlite_path: Path, migrations_dir: Path | None=None, clock: Clock | None=None) -> list[Migration]` ([source](../../../../../../src/learnloop/db/migrate.py), line 174) — Create the database (a missing file, or one with no migration applied yet), or check that an existing one is at this code's migrations (moving it to WAL as :func:`apply_migrations` does).
- `switch_to_wal(connection: sqlite3.Connection, sqlite_path: Path) -> str | None` ([source](../../../../../../src/learnloop/db/migrate.py), line 219) — Move a database to WAL journal mode once, where the linked SQLite allows it.

### Module constants

- `_LOG` ([src/learnloop/db/migrate.py](../../../../../../src/learnloop/db/migrate.py), line 16)
- `_MIGRATION_RE` ([src/learnloop/db/migrate.py](../../../../../../src/learnloop/db/migrate.py), line 18)
- `_FOREIGN_KEYS_OFF_RE` ([src/learnloop/db/migrate.py](../../../../../../src/learnloop/db/migrate.py), line 19)
- `_COMPANION_SUFFIXES` ([src/learnloop/db/migrate.py](../../../../../../src/learnloop/db/migrate.py), line 27)
- `UPGRADE_BY_COORDINATOR` ([src/learnloop/db/migrate.py](../../../../../../src/learnloop/db/migrate.py), line 71)
- `UPGRADE_SCRATCH_COPY` ([src/learnloop/db/migrate.py](../../../../../../src/learnloop/db/migrate.py), line 72)
- `UPGRADE_TEST_HELPER` ([src/learnloop/db/migrate.py](../../../../../../src/learnloop/db/migrate.py), line 73)
- `_UPGRADE_ALLOWANCES` ([src/learnloop/db/migrate.py](../../../../../../src/learnloop/db/migrate.py), line 74)
- `_UPGRADE_AUTHORITY` ([src/learnloop/db/migrate.py](../../../../../../src/learnloop/db/migrate.py), line 75)
- `_CREATING` ([src/learnloop/db/migrate.py](../../../../../../src/learnloop/db/migrate.py), line 78)

## Internal implementation anchors

- `_migrate(sqlite_path: Path, migrations: list[Migration], clock: Clock | None, *, upgrade: bool) -> list[Migration]` ([source](../../../../../../src/learnloop/db/migrate.py), line 191)
- `_switch_failure_cause(error: sqlite3.OperationalError, sqlite_path: Path) -> str` ([source](../../../../../../src/learnloop/db/migrate.py), line 262) — Name the real cause of a failed switch from SQLite's error code.
- `_apply_incremental_migration(connection: sqlite3.Connection, migration: Migration, clock: Clock | None) -> bool` ([source](../../../../../../src/learnloop/db/migrate.py), line 286) — Apply one existing-database migration as one durable transaction.
- `_refuse_unauthorized(connection: sqlite3.Connection, migration: Migration) -> None` ([source](../../../../../../src/learnloop/db/migrate.py), line 355) — Raise :class:`UncoordinatedMigrationError` for an upgrade of an existing database outside every :func:`upgrade_allowance` (F8).
- `_migration_is_applied(connection: sqlite3.Connection, version: int) -> bool` ([source](../../../../../../src/learnloop/db/migrate.py), line 370)
- `_iter_sql_statements(sql: str) -> Iterator[str]` ([source](../../../../../../src/learnloop/db/migrate.py), line 385) — Yield executable statements without splitting trigger bodies.
- `_apply_fresh(sqlite_path: Path, migrations: list[Migration], clock: Clock | None) -> list[Migration]` ([source](../../../../../../src/learnloop/db/migrate.py), line 404) — Create a brand-new database with every migration, fast and atomically.
- `_existing_companion_files(sqlite_path: Path) -> list[Path]` ([source](../../../../../../src/learnloop/db/migrate.py), line 452)
- `_remove_companion_files(sqlite_path: Path, *, include_database: bool) -> None` ([source](../../../../../../src/learnloop/db/migrate.py), line 457) — Delete companions of a database that does not exist (or is being replaced).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/receipts|learnloop.cli.receipts]] — imports `applied_versions`; statically calls `applied_versions`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `create_or_attach_current`; statically calls `create_or_attach_current`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `UPGRADE_SCRATCH_COPY`, `apply_migrations`, `upgrade_allowance`; statically calls `apply_migrations`, `upgrade_allowance`
- [[Reference/Modules/learnloop/migration_coordinator|learnloop.migration_coordinator]] — imports `Migration`, `UPGRADE_BY_COORDINATOR`, `apply_migrations`, `upgrade_allowance`; statically calls `apply_migrations`, `upgrade_allowance`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `applied_versions`, `discover_migrations`; statically calls `applied_versions`, `discover_migrations`
- [[Reference/Modules/learnloop/projects/experiment_store|learnloop.projects.experiment_store]] — imports `JournalModeSwitchError`, `switch_to_wal`; statically calls `switch_to_wal`
- [[Reference/Modules/learnloop/remote/runtime|learnloop.remote.runtime]] — imports `schema_is_current`; statically calls `schema_is_current`
- [[Reference/Modules/learnloop/remote/views|learnloop.remote.views]] — imports `applied_versions`, `discover_migrations`; statically calls `applied_versions`, `discover_migrations`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `UncoordinatedMigrationError`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `applied_versions`, `discover_migrations`, `schema_is_current`; statically calls `applied_versions`, `discover_migrations`, `schema_is_current`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`, `wal_unavailable_reason`; calls `connect`, `wal_unavailable_reason`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `contextvars`, `dataclasses`, `logging`, `os`, `pathlib`, `re`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/receipts|learnloop.cli.receipts]], [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]], [[Reference/Modules/learnloop/migration_coordinator|learnloop.migration_coordinator]], [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/conftest.py](../../../../../../tests/conftest.py) — direct import
- [tests/test_activity_contract_extensions.py](../../../../../../tests/test_activity_contract_extensions.py) — direct import
- [tests/test_activity_patterns.py](../../../../../../tests/test_activity_patterns.py) — direct import
- [tests/test_ad1_migration.py](../../../../../../tests/test_ad1_migration.py) — direct import
- [tests/test_ad23_migration.py](../../../../../../tests/test_ad23_migration.py) — direct import
  - `test_a_vault_at_218_without_214_gets_it`
  - `test_head_fixture_at_head_with_214_in_rollback_mode`
- [tests/test_administration_adapters.py](../../../../../../tests/test_administration_adapters.py) — direct import
- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — direct import
  - `test_agent_run_token_columns_exist_and_default_to_zero`
- [tests/test_approach_maps_schema.py](../../../../../../tests/test_approach_maps_schema.py) — direct import
  - `test_the_head_fixture_is_at_head_in_rollback_mode`
- [tests/test_card_lineage.py](../../../../../../tests/test_card_lineage.py) — direct import
- [tests/test_commitments.py](../../../../../../tests/test_commitments.py) — direct import
- [tests/test_coordinated_migrations.py](../../../../../../tests/test_coordinated_migrations.py) — direct import
  - `test_a_bare_repository_refuses_to_upgrade_and_leaves_the_database_as_it_was`
  - `test_a_bare_repository_still_creates_a_database_and_attaches_a_current_one`
  - `test_f8_a_repository_reached_indirectly_never_upgrades`
  - `test_f8_an_indirect_upgrade_outside_the_coordinator_raises_and_leaves_the_file_byte_identical`
  - `test_f8_an_unknown_allowance_is_refused`
  - `test_f8_creating_or_attaching_needs_no_allowance`
  - `test_f8_the_coordinator_upgrades_under_its_allowance_and_qualifies`
  - `test_f8_the_offline_reviews_scratch_copy_is_upgraded_under_its_own_allowance`
  - `test_f8_the_test_suites_allowance_is_its_fixture`
  - `test_vault_repository_attaches_a_current_vault_without_the_coordinator`
  - `test_vault_repository_upgrades_a_vault_that_is_behind_through_the_coordinator`
- [tests/test_daily_plan_owner_decisions.py](../../../../../../tests/test_daily_plan_owner_decisions.py) — direct import
  - `test_migration_180_widens_the_field_serving_origins_and_keeps_its_rows`
- [tests/test_data_capture_migration.py](../../../../../../tests/test_data_capture_migration.py) — direct import
  - `test_240_adds_exactly_its_objects_and_changes_nothing_else`
  - `test_240_is_the_head_and_its_tables_are_receipts`
  - `test_240_on_the_durability_lane`
  - `test_the_head_fixture_is_at_240_in_rollback_mode_with_empty_tables`
- [tests/test_deliverable_curriculum_migration.py](../../../../../../tests/test_deliverable_curriculum_migration.py) — direct import
  - `test_228_is_c0bs_migration_classified_with_no_derived_table`
  - `test_the_head_fixture_holds_exactly_228s_objects_in_rollback_mode`
- [tests/test_depth_transition.py](../../../../../../tests/test_depth_transition.py) — direct import
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
  - `test_q14_on_a_vault_the_coordinator_upgrades_the_receipt_commits_with_the_grade`
- [tests/test_embedding_store.py](../../../../../../tests/test_embedding_store.py) — direct import
- [tests/test_event_sufficiency.py](../../../../../../tests/test_event_sufficiency.py) — direct import
- [tests/test_exam_protection_identity.py](../../../../../../tests/test_exam_protection_identity.py) — direct import
  - `test_f3_final_a_cli_upgrade_records_what_membership_qualifies_before_a_hand_edit`
  - `test_identity_rereview_f3_a_hand_edit_never_releases_a_signal_its_membership_qualified`
  - `test_identity_rereview_f7_an_assessment_profile_is_not_an_exam_role`
  - `test_migration_225_backfills_each_signal_on_the_reading_it_was_made_on`
- [tests/test_exam_seeding.py](../../../../../../tests/test_exam_seeding.py) — direct import
  - `test_migration_018_allows_exam_evidence_on_existing_db`
- [tests/test_facet_rewords_migration.py](../../../../../../tests/test_facet_rewords_migration.py) — direct import
  - `test_migration_196_upgrades_a_195_vault_keeping_actions_and_the_forecast_log`
- [tests/test_familiarity.py](../../../../../../tests/test_familiarity.py) — direct import
- [tests/test_figure_prefetch_migration.py](../../../../../../tests/test_figure_prefetch_migration.py) — direct import
  - `test_237_is_p5s_migration_and_every_table_is_classified`
- [tests/test_figure_requests_migration.py](../../../../../../tests/test_figure_requests_migration.py) — direct import
  - `test_224_is_the_figure_requests_migration_and_the_table_is_a_raw_ledger`
- [tests/test_figures_migration.py](../../../../../../tests/test_figures_migration.py) — direct import
  - `test_216_is_the_figures_migration`
- [tests/test_followup_migration.py](../../../../../../tests/test_followup_migration.py) — direct import
  - `test_241_is_applied_and_its_tables_have_their_roles`
  - `test_the_head_fixture_holds_241_in_rollback_mode_with_empty_tables`
- [tests/test_forecast_receipts_landing.py](../../../../../../tests/test_forecast_receipts_landing.py) — direct import
  - `test_the_renumbered_migration_and_its_table_role`
- [tests/test_goal_contracts.py](../../../../../../tests/test_goal_contracts.py) — direct import
- [tests/test_help_assist_figures_migration.py](../../../../../../tests/test_help_assist_figures_migration.py) — direct import
  - `test_232_is_the_figures_migration_and_help_assists_stays_a_raw_ledger`
  - `test_232_on_the_durability_lane`
  - `test_232_rebuilds_figure_predictions_with_every_row_and_the_attempt_link`
  - `test_232_widens_three_checks_adds_figure_id_and_keeps_every_row`
  - `test_the_head_fixture_holds_232_in_rollback_mode`
- [tests/test_help_assist_work_md_migration.py](../../../../../../tests/test_help_assist_work_md_migration.py) — direct import
  - `test_230_adds_only_the_nullable_column_and_keeps_every_row`
  - `test_230_is_the_work_md_migration_and_help_assists_stays_a_raw_ledger`
  - `test_230_on_the_durability_lane`
  - `test_the_head_fixture_holds_230_in_rollback_mode`
- [tests/test_help_assists_schema.py](../../../../../../tests/test_help_assists_schema.py) — direct import
  - `test_the_head_fixture_is_at_head_in_rollback_mode`
- [tests/test_hint_feedback_widening.py](../../../../../../tests/test_hint_feedback_widening.py) — direct import
  - `test_212_adds_hint_feedback_and_nothing_else`
  - `test_212_classifies_nothing_new`
- [tests/test_hypothesis_marks_migration.py](../../../../../../tests/test_hypothesis_marks_migration.py) — direct import
  - `test_242_adds_exactly_its_objects_and_changes_nothing_else`
  - `test_242_is_applied_and_its_tables_have_their_roles`
  - `test_242_on_the_durability_lane`
  - `test_the_head_fixture_holds_242_in_rollback_mode_with_empty_tables`
- [tests/test_journey6.py](../../../../../../tests/test_journey6.py) — direct import
- [tests/test_judge_routes.py](../../../../../../tests/test_judge_routes.py) — direct import
  - `test_judgment_ledger_accepts_the_decider_with_provenance`
  - `test_migration_175_preserves_every_judgment_and_its_references`
  - `test_receipts_store_labels_and_unlabelled_calls_work_below_175`
- [tests/test_judgment_ledger.py](../../../../../../tests/test_judgment_ledger.py) — direct import
- [tests/test_laddered_stems.py](../../../../../../tests/test_laddered_stems.py) — direct import
- [tests/test_learner_claim_application_migration.py](../../../../../../tests/test_learner_claim_application_migration.py) — direct import
  - `test_221_adds_the_claim_point_column_and_nothing_else`
  - `test_221_on_the_durability_lane`
  - `test_the_head_fixture_holds_221_in_rollback_mode`
- [tests/test_learner_claim_superseded_migration.py](../../../../../../tests/test_learner_claim_superseded_migration.py) — direct import
  - `test_225_adds_the_superseded_by_column_and_nothing_else`
  - `test_225_on_the_durability_lane`
  - `test_the_head_fixture_holds_225_in_rollback_mode`
- [tests/test_learner_gap_unlinked_migration.py](../../../../../../tests/test_learner_gap_unlinked_migration.py) — direct import
  - `test_235_adds_unlinked_and_nothing_else`
  - `test_235_classifies_nothing_new`
  - `test_the_head_fixture_holds_235_in_rollback_mode`
- [tests/test_learner_note_source_kind_migration.py](../../../../../../tests/test_learner_note_source_kind_migration.py) — direct import
  - `test_231_adds_learner_note_and_nothing_else`
  - `test_231_classifies_nothing_new`
  - `test_the_head_fixture_holds_231_in_rollback_mode_with_no_note_gap`
- [tests/test_learner_notes_migration.py](../../../../../../tests/test_learner_notes_migration.py) — direct import
  - `test_229_is_c2s_migration_classified_with_no_derived_table`
  - `test_229_on_the_durability_lane`
  - `test_the_head_fixture_holds_exactly_229s_objects_in_rollback_mode`
- [tests/test_learner_notes_vault_origin_migration.py](../../../../../../tests/test_learner_notes_vault_origin_migration.py) — direct import
  - `test_233_classifies_nothing_new`
  - `test_the_head_fixture_holds_233_in_rollback_mode`
- [tests/test_learner_text_source_widening.py](../../../../../../tests/test_learner_text_source_widening.py) — direct import
  - `test_the_migration_names_both_kinds_in_one_rebuild`
- [tests/test_library_asks_migration.py](../../../../../../tests/test_library_asks_migration.py) — direct import
  - `test_the_head_fixture_is_at_head_in_rollback_mode`
- [tests/test_migrate_fresh.py](../../../../../../tests/test_migrate_fresh.py) — direct import
  - `test_existing_database_upgrades_incrementally`
  - `test_fk_toggle_migration_is_atomic_and_restores_enforcement`
  - `test_fresh_database_applies_all_migrations_atomically`
  - `test_incremental_migration_and_ledger_receipt_roll_back_together`
  - `test_incremental_statement_parser_preserves_trigger_bodies`
  - `test_real_fk_rebuild_153_rolls_back_on_interruption`
  - `test_real_migration_set_builds_fresh`
  - `test_stale_tmp_from_a_crashed_creation_is_replaced`
- [tests/test_migration_coordinator.py](../../../../../../tests/test_migration_coordinator.py) — direct import
  - `test_coordinator_locks_the_vault_for_a_relocated_database`
  - `test_process_death_mid_migration_leaves_body_and_receipt_fully_absent`
  - `test_two_normal_repository_opens_serialize_migration`
  - `test_two_processes_racing_to_migrate_share_one_consistent_ledger`
- [tests/test_migrations.py](../../../../../../tests/test_migrations.py) — direct import
  - `test_agent_runs_have_generic_provider_metadata`
  - `test_attempt_feedback_metadata_allows_ai_source`
  - `test_controller_decision_action_and_shadow_authority_checks`
  - `test_controller_snapshot_migration_applies_on_pre_096_db`
  - `test_controller_snapshot_schema_is_available`
  - `test_discover_finds_initial_migration`
  - `test_durable_ingest_jobs_migration_applies_on_pre_033_db`
  - `test_durable_ingest_jobs_schema_is_available`
  - `test_entity_source_links_relation_and_status_checks`
  - `test_every_fixture_upgrades_with_clean_foreign_keys`
  - `test_existing_db_migrates_cleanly`
  - `test_facet_diagnostic_schema_is_available`
  - `test_first_error_cleanup_is_semantically_demoted_not_learned`
  - `test_fresh_db_applies_all_migrations`
  - `test_head_163_database_upgrades_to_snapshots_and_fk_free_adjudications`
  - `test_migrations_are_idempotent`
  - `test_misconception_migration_applies_on_pre_025_db`
  - `test_misconception_registry_schema_is_available`
  - `test_open_text_migration_preserves_existing_attempts_and_foreign_keys`
  - `test_opening_the_vault_applies_pending_migrations_a_bare_repository_refuses`
  - `test_practice_attempts_allow_open_text_after_fresh_migration`
  - `test_practice_attempts_schema_matches_supported_attempt_types`
  - `test_provenance_manifests_apply_intents_schema_is_available`
  - `test_provenance_migration_applies_on_pre_044_db`
  - `test_question_promotion_request_migration_backfills_legacy_ledger`
  - `test_real_migration_chain_applies_incrementally_after_initial_schema`
  - `test_repair_opportunity_bridge_applies_after_opportunity_substrate`
  - `test_repository_carries_a_fixture_at_the_current_migration_head`
  - `test_scheduler_training_log_schema_is_available`
  - `test_source_exposure_index_backfill_is_idempotent_on_092_only_vault`
  - `test_source_exposure_indexes_present_on_fresh_vault`
  - `test_source_layer_migration_applies_on_pre_032_db`
  - `test_source_layer_schema_is_available`
  - `test_source_unit_selections_migration_applies_on_pre_040_db`
  - `test_source_unit_selections_schema_is_available`
  - `test_variable_rubric_scale_migration_allows_scores_above_four`
- [tests/test_mobile_jobs_migration.py](../../../../../../tests/test_mobile_jobs_migration.py) — direct import
  - `test_239_is_named_and_the_table_is_classified`
  - `test_a_database_at_238_gets_it_and_nothing_else_changes`
  - `test_the_head_fixture_is_at_head_in_rollback_mode_with_an_empty_table`
- [tests/test_model_call_receipt_owners.py](../../../../../../tests/test_model_call_receipt_owners.py) — direct import
  - `test_a_database_below_the_receipt_schema_lets_the_model_call_run_unrecorded`
- [tests/test_persistence_open.py](../../../../../../tests/test_persistence_open.py) — direct import
  - `test_repository_attach_can_open_a_writable_scratch_copy`
  - `test_repository_attach_skips_migrations_and_can_be_physically_read_only`
- [tests/test_practice_index_adapters.py](../../../../../../tests/test_practice_index_adapters.py) — direct import
- [tests/test_probe_migration.py](../../../../../../tests/test_probe_migration.py) — direct import
  - `test_migration_closes_in_progress_phases_as_superseded`
- [tests/test_progression.py](../../../../../../tests/test_progression.py) — direct import
- [tests/test_question_promotions.py](../../../../../../tests/test_question_promotions.py) — direct import
  - `test_027_rebuild_preserves_existing_rows`
  - `test_learner_claims_accepts_tutor_gap_declaration_source`
  - `test_question_promotions_schema_available_on_fresh_db`
- [tests/test_reader_ca2_fix_orchestrator.py](../../../../../../tests/test_reader_ca2_fix_orchestrator.py) — direct import
  - `test_223_adds_only_the_earlier_opening_column`
- [tests/test_reader_rw3b_migration.py](../../../../../../tests/test_reader_rw3b_migration.py) — direct import
  - `test_the_head_fixture_is_at_head_in_rollback_mode_with_empty_rw3b_tables`
- [tests/test_reader_rw7a_migration.py](../../../../../../tests/test_reader_rw7a_migration.py) — direct import
  - `test_the_head_fixture_is_at_217_in_rollback_mode_with_empty_rw7a_tables`
- [tests/test_reader_session_digests_migration.py](../../../../../../tests/test_reader_session_digests_migration.py) — direct import
  - `test_227_is_the_reader_session_digests_migration_and_the_table_is_workflow`
  - `test_head_226_upgrades_by_adding_only_227s_objects`
- [tests/test_retrieval_spaces_migration.py](../../../../../../tests/test_retrieval_spaces_migration.py) — direct import
  - `test_220_adds_three_tables_and_alters_nothing`
  - `test_220_on_the_durability_lane`
  - `test_the_head_fixture_holds_220_in_rollback_mode`
- [tests/test_reveal_ledger.py](../../../../../../tests/test_reveal_ledger.py) — direct import
  - `test_migration_154_adds_the_ledger_and_the_question_event_columns`
- [tests/test_ro1_availability.py](../../../../../../tests/test_ro1_availability.py) — direct import
  - `test_244_adds_exactly_its_columns_and_changes_nothing_else`
  - `test_244_is_the_head_and_the_head_fixture_holds_its_empty_columns`
  - `test_244_on_the_durability_lane`
  - `test_the_backfill_reads_an_imported_exam_rows_ulid_time_and_leaves_bad_ids_null`
- [tests/test_ro2_history_migration.py](../../../../../../tests/test_ro2_history_migration.py) — direct import
  - `test_245_adds_exactly_its_objects_and_the_table_is_append_only`
  - `test_245_is_the_head_and_its_table_a_receipt_ad_classifies`
  - `test_245_on_the_durability_lane`
  - `test_the_head_fixture_holds_245_in_rollback_mode_with_an_empty_table`
- [tests/test_ro4_traces_migration.py](../../../../../../tests/test_ro4_traces_migration.py) — direct import
  - `test_246_adds_exactly_its_objects_and_the_table_is_append_only`
  - `test_246_is_the_head_and_its_table_a_receipt`
  - `test_246_widens_the_contract_change_class_keeping_every_row`
  - `test_the_head_fixture_holds_246_in_rollback_mode_with_an_empty_table`
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_migration_186_keeps_its_trigger_which_nothing_writes_now`
- [tests/test_router_objective_migration.py](../../../../../../tests/test_router_objective_migration.py) — direct import
  - `test_243_exists_and_its_tables_are_receipts`
  - `test_the_head_fixture_holds_243_in_rollback_mode_with_empty_tables_and_null_columns`
- [tests/test_rw2d_receipts_migration.py](../../../../../../tests/test_rw2d_receipts_migration.py) — direct import
  - `test_219_adds_the_receipt_table_and_the_subject_column_and_nothing_else`
  - `test_219_on_the_durability_lane`
  - `test_the_head_fixture_holds_219_in_rollback_mode`
- [tests/test_rw5c_migration.py](../../../../../../tests/test_rw5c_migration.py) — direct import
  - `test_238_is_applied_and_the_table_is_classified`
  - `test_238_upgrades_a_copy_of_237_under_the_durable_pragmas`
  - `test_the_head_fixture_is_past_238_in_rollback_mode_with_an_empty_table`
- [tests/test_section_coverage_migration.py](../../../../../../tests/test_section_coverage_migration.py) — direct import
  - `test_222_adds_one_table_and_alters_nothing`
  - `test_222_on_the_durability_lane`
  - `test_the_head_fixture_is_at_222_in_rollback_mode`
- [tests/test_session_ownership_migration.py](../../../../../../tests/test_session_ownership_migration.py) — direct import
  - `test_226_is_the_session_ownership_migration_and_the_handoffs_are_receipts`
- [tests/test_source_block_fts.py](../../../../../../tests/test_source_block_fts.py) — direct import
  - `test_migration_177_indexes_a_176_vaults_existing_blocks`
- [tests/test_source_service_spend_accounting.py](../../../../../../tests/test_source_service_spend_accounting.py) — direct import
  - `test_an_upgrade_counts_every_request_and_reports_the_unprovable_overlap`
- [tests/test_sqlite_wal.py](../../../../../../tests/test_sqlite_wal.py) — direct import
  - `test_affected_sqlite_leaves_databases_in_rollback_mode_and_doctor_says_why`
  - `test_fixed_sqlite_switches_to_wal_and_doctor_is_quiet`
  - `test_fresh_creation_discards_an_orphaned_wal_from_a_deleted_database`
  - `test_fresh_database_is_created_in_wal_mode_without_companion_files`
  - `test_idle_connection_elsewhere_does_not_block_the_switch`
  - `test_switch_fails_clearly_and_leaves_the_mode_unchanged_while_a_reader_is_open`
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — direct import
  - `test_migration_179_widens_the_reveal_kinds_and_keeps_the_ledger`
- [tests/test_substrate_cutover.py](../../../../../../tests/test_substrate_cutover.py) — direct import
- [tests/test_surface_mint.py](../../../../../../tests/test_surface_mint.py) — direct import
- [tests/test_t1_batch_origin_migration.py](../../../../../../tests/test_t1_batch_origin_migration.py) — direct import
  - `test_218_adds_the_batch_origin_column_and_nothing_else`
  - `test_the_head_fixture_is_at_head_in_rollback_mode`
- [tests/test_table_roles.py](../../../../../../tests/test_table_roles.py) — direct import
  - `test_migration_head_user_tables_match_role_registry_exactly`
  - `test_synthetic_unclassified_table_fails_registry_check`
- [tests/test_task_blueprints.py](../../../../../../tests/test_task_blueprints.py) — direct import
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_migration_020_allows_teach_back_on_existing_db`
- [tests/test_teacher_te1_migration.py](../../../../../../tests/test_teacher_te1_migration.py) — direct import
  - `test_234_is_te1s_migration_and_every_table_is_classified`
- [tests/test_teacher_te1b_migration.py](../../../../../../tests/test_teacher_te1b_migration.py) — direct import
  - `test_236_is_te1bs_migration_and_its_table_is_classified`
  - `test_236_keeps_every_router_decision_row`
- [tests/test_teacher_te2log_migration.py](../../../../../../tests/test_teacher_te2log_migration.py) — direct import
  - `test_247_adds_exactly_its_objects`
  - `test_247_is_the_head_and_its_tables_receipts_denied_to_ad`
  - `test_247_on_the_durability_lane`
  - `test_the_head_fixture_holds_247_in_rollback_mode_with_empty_tables`
- [tests/test_today_surfaces.py](../../../../../../tests/test_today_surfaces.py) — direct import
  - `test_overconfidence_probe_origin_survives_target_selection`
  - `test_overconfidence_probe_records_origin`
  - `test_probe_episode_without_origin_is_null`
- [tests/test_voi_v2.py](../../../../../../tests/test_voi_v2.py) — direct import
  - `test_migration_201_backfills_a_legacy_follow_up_receipt_once`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/migrate.py](../../../../../../src/learnloop/db/migrate.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
