---
title: "learnloop.db.connection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/connection.py"
source_paths:
  - "src/learnloop/db/connection.py"
source_commit: "e851e5c3b2e5a710a4a851a7b245c7e2f851e5cd"
source_commit_timestamp: "2026-09-23T20:44:21-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop.db"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.connection module"
  - "src/learnloop/db/connection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db"
---

# `learnloop.db.connection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/_package|learnloop.db]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps connection behavior inside its owning package, [[Reference/Modules/learnloop/db/_package|learnloop.db]]. Its public surface centers on `UnsupportedSQLiteVersion`, `require_supported_sqlite`, `linked_sqlite_version`, `wal_reset_bug_fixed`, `wal_unavailable_reason`, `connect`.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/connection.py](../../../../../../src/learnloop/db/connection.py) |
| Source lines | 146 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e851e5c3b2e5a710a4a851a7b245c7e2f851e5cd` |
| Commit timestamp | `2026-09-23T20:44:21-04:00` |

## Public API

- `class UnsupportedSQLiteVersion(RuntimeError)` ([source](../../../../../../src/learnloop/db/connection.py), line 33) — The SQLite library linked into Python is too old for WAL vaults.
- `require_supported_sqlite() -> None` ([source](../../../../../../src/learnloop/db/connection.py), line 38) — Fail once, clearly, when the runtime SQLite cannot open WAL vaults.
- `linked_sqlite_version() -> tuple[int, int, int]` ([source](../../../../../../src/learnloop/db/connection.py), line 49)
- `wal_reset_bug_fixed(version: tuple[int, int, int] | None=None) -> bool` ([source](../../../../../../src/learnloop/db/connection.py), line 53) — Whether ``version`` (default: the linked SQLite) has the WAL-reset fix.
- `wal_unavailable_reason(version: tuple[int, int, int] | None=None) -> str | None` ([source](../../../../../../src/learnloop/db/connection.py), line 66) — Why WAL must not be enabled with ``version``, or ``None`` when it may be.
- `connect(sqlite_path: Path, *, read_only: bool=False) -> sqlite3.Connection` ([source](../../../../../../src/learnloop/db/connection.py), line 82) — Open a configured SQLite connection.

### Module constants

- `MINIMUM_SQLITE_VERSION` ([src/learnloop/db/connection.py](../../../../../../src/learnloop/db/connection.py), line 11)
- `BUSY_TIMEOUT_MS` ([src/learnloop/db/connection.py](../../../../../../src/learnloop/db/connection.py), line 12)
- `WAL_RESET_FIX_RELEASES` ([src/learnloop/db/connection.py](../../../../../../src/learnloop/db/connection.py), line 20)
- `WAL_RESET_FIXED_VERSIONS_TEXT` ([src/learnloop/db/connection.py](../../../../../../src/learnloop/db/connection.py), line 25)
- `WAL_RESET_ADVISORY_URL` ([src/learnloop/db/connection.py](../../../../../../src/learnloop/db/connection.py), line 26)
- `_READ_ONLY_OPEN_FAILURES` ([src/learnloop/db/connection.py](../../../../../../src/learnloop/db/connection.py), line 30)

## Internal implementation anchors

- `_configure(connection: sqlite3.Connection) -> None` ([source](../../../../../../src/learnloop/db/connection.py), line 111)
- `_open_read_only(sqlite_path: Path) -> sqlite3.Connection` ([source](../../../../../../src/learnloop/db/connection.py), line 117) — Open with ``mode=ro`` and surface a WAL open failure here.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/checkpoint|learnloop.db.checkpoint]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/db/copies|learnloop.db.copies]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/db/migrate|learnloop.db.migrate]] — imports `connect`, `wal_unavailable_reason`; statically calls `connect`, `wal_unavailable_reason`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/db/scopes|learnloop.db.scopes]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/db/stores/model_calls|learnloop.db.stores.model_calls]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `WAL_RESET_ADVISORY_URL`, `WAL_RESET_FIXED_VERSIONS_TEXT`, `linked_sqlite_version`, `wal_unavailable_reason`; statically calls `linked_sqlite_version`, `wal_unavailable_reason`
- [[Reference/Modules/learnloop/substrate/data_quality|learnloop.substrate.data_quality]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/substrate/dataset|learnloop.substrate.dataset]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/substrate/model_usage|learnloop.substrate.model_usage]] — imports `connect`; statically calls `connect`

### Repository tooling consumers

- [scripts/benchmark_sqlite_concurrency.py](../../../../../../scripts/benchmark_sqlite_concurrency.py); calls `connect`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/scopes|learnloop.db.scopes]] — imports `guarded_connection`; calls `guarded_connection`

### Platform and third-party dependencies

- Standard library: `__future__`, `functools`, `pathlib`, `sqlite3`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/checkpoint|learnloop.db.checkpoint]], [[Reference/Modules/learnloop/db/copies|learnloop.db.copies]], [[Reference/Modules/learnloop/db/migrate|learnloop.db.migrate]], [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/db/scopes|learnloop.db.scopes]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/conftest.py](../../../../../../tests/conftest.py) — direct import
- [tests/helpers.py](../../../../../../tests/helpers.py) — direct import
- [tests/test_activity_backfill.py](../../../../../../tests/test_activity_backfill.py) — direct import
  - `test_backfill_logs_attempt_duration_interaction_events`
  - `test_backfill_marks_unverifiable_for_missing_item`
  - `test_backfill_populates_substrate_from_fixture`
  - `test_backfill_render_once_per_shared_surface`
  - `test_diagnostic_probe_attempts_reuse_shared_surface_hash`
- [tests/test_activity_substrate.py](../../../../../../tests/test_activity_substrate.py) — direct import
  - `test_ensure_activity_family_and_card_are_race_safe`
  - `test_feedback_before_response_yields_no_terminal_credit`
  - `test_migration_created_substrate_tables_and_partial_indices`
  - `test_retire_with_reason_records_and_preserves_evidence`
- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — direct import
  - `test_agent_run_token_columns_exist_and_default_to_zero`
- [tests/test_assessment_contracts.py](../../../../../../tests/test_assessment_contracts.py) — direct import
  - `test_observation_id_attaches_once`
- [tests/test_assessment_enforcement.py](../../../../../../tests/test_assessment_enforcement.py) — direct import
  - `test_failed_with_feedback_appends_practice_successor_proposal`
  - `test_render_marks_unrepresentative_when_head_support_moved`
- [tests/test_collection_dataset.py](../../../../../../tests/test_collection_dataset.py) — direct import
  - `test_export_gives_up_on_a_source_locked_after_its_probe_and_removes_the_export`
  - `test_production_lane_and_live_backup_preserve_committed_state`
  - `test_scored_item_text_is_snapshotted_once_per_revision_and_exported`
  - `test_selection_decision_features_reference_the_item_and_stay_compact`
- [tests/test_exam_seeding.py](../../../../../../tests/test_exam_seeding.py) — direct import
  - `test_migration_018_allows_exam_evidence_on_existing_db`
- [tests/test_goal_contracts.py](../../../../../../tests/test_goal_contracts.py) — direct import
- [tests/test_grade_resolution_pipeline.py](../../../../../../tests/test_grade_resolution_pipeline.py) — direct import
  - `test_backfill_converts_probe_presentations_idempotently`
  - `test_insert_calibration_model_is_content_addressed_no_duplicate`
  - `test_migration_066_created_tables_and_indices`
  - `test_probe_dual_write_helper_records_diagnostic_grade`
- [tests/test_grading_cli.py](../../../../../../tests/test_grading_cli.py) — direct import
  - `test_retire_surface_from_cli_preserves_evidence_and_logs_reason`
- [tests/test_migrate_fresh.py](../../../../../../tests/test_migrate_fresh.py) — direct import
  - `test_fk_toggle_migration_is_atomic_and_restores_enforcement`
  - `test_incremental_migration_and_ledger_receipt_roll_back_together`
  - `test_incremental_statement_parser_preserves_trigger_bodies`
  - `test_real_fk_rebuild_153_rolls_back_on_interruption`
- [tests/test_migration_coordinator.py](../../../../../../tests/test_migration_coordinator.py) — direct import
  - `test_process_death_mid_migration_leaves_body_and_receipt_fully_absent`
- [tests/test_migrations.py](../../../../../../tests/test_migrations.py) — direct import
  - `test_agent_runs_have_generic_provider_metadata`
  - `test_attempt_feedback_metadata_allows_ai_source`
  - `test_controller_decision_action_and_shadow_authority_checks`
  - `test_controller_snapshot_migration_applies_on_pre_096_db`
  - `test_controller_snapshot_schema_is_available`
  - `test_durable_ingest_jobs_migration_applies_on_pre_033_db`
  - `test_durable_ingest_jobs_schema_is_available`
  - `test_entity_source_links_relation_and_status_checks`
  - `test_every_fixture_upgrades_with_clean_foreign_keys`
  - `test_facet_diagnostic_schema_is_available`
  - `test_first_error_cleanup_is_semantically_demoted_not_learned`
  - `test_fresh_db_applies_all_migrations`
  - `test_head_163_database_upgrades_to_snapshots_and_fk_free_adjudications`
  - `test_misconception_migration_applies_on_pre_025_db`
  - `test_misconception_registry_schema_is_available`
  - `test_open_text_migration_preserves_existing_attempts_and_foreign_keys`
  - `test_practice_attempts_allow_open_text_after_fresh_migration`
  - `test_practice_attempts_schema_matches_supported_attempt_types`
  - `test_provenance_manifests_apply_intents_schema_is_available`
  - `test_provenance_migration_applies_on_pre_044_db`
  - `test_question_promotion_request_migration_backfills_legacy_ledger`
  - `test_real_migration_chain_applies_incrementally_after_initial_schema`
  - `test_repair_opportunity_bridge_applies_after_opportunity_substrate`
  - `test_repository_applies_pending_migrations_on_open`
  - `test_scheduler_training_log_schema_is_available`
  - `test_source_exposure_index_backfill_is_idempotent_on_092_only_vault`
  - `test_source_exposure_indexes_present_on_fresh_vault`
  - `test_source_layer_migration_applies_on_pre_032_db`
  - `test_source_layer_schema_is_available`
  - `test_source_unit_selections_migration_applies_on_pre_040_db`
  - `test_source_unit_selections_schema_is_available`
  - `test_variable_rubric_scale_migration_allows_scores_above_four`
- [tests/test_model_call_receipt_owners.py](../../../../../../tests/test_model_call_receipt_owners.py) — direct import
  - `test_a_database_below_the_receipt_schema_lets_the_model_call_run_unrecorded`
- [tests/test_mvp09_upgrade.py](../../../../../../tests/test_mvp09_upgrade.py) — direct import
  - `test_upgrade_to_mvp09_flips_rebuilds_and_preserves_raw_history`
- [tests/test_p0_cutover_mvp08.py](../../../../../../tests/test_p0_cutover_mvp08.py) — direct import
  - `test_upgrade_does_not_rewrite_raw_history`
- [tests/test_p0_projection_cutover.py](../../../../../../tests/test_p0_projection_cutover.py) — direct import
  - `test_adjudication_reverses_projection_and_preserves_history`
  - `test_ruling_a_superseded_rows_inert_nonsuperseded_rows_authoritative`
- [tests/test_persistence_open.py](../../../../../../tests/test_persistence_open.py) — direct import
  - `test_connection_centralizes_busy_timeout`
  - `test_read_only_connect_does_not_create_a_missing_database_or_parent`
  - `test_repository_attach_can_open_a_writable_scratch_copy`
- [tests/test_proposal_dependencies.py](../../../../../../tests/test_proposal_dependencies.py) — direct import
- [tests/test_question_promotions.py](../../../../../../tests/test_question_promotions.py) — direct import
  - `test_027_rebuild_preserves_existing_rows`
  - `test_attempt_before_promotion_does_not_consume_practice_again_request`
  - `test_learner_claims_accepts_tutor_gap_declaration_source`
  - `test_question_promotions_schema_available_on_fresh_db`
  - `test_requested_practice_item_ids_orders_oldest_first_and_excludes_attempted`
- [tests/test_rebuild_orchestrator.py](../../../../../../tests/test_rebuild_orchestrator.py) — direct import
  - `test_content_recalibration_replay_cannot_lose_its_ingest_lease_midway`
  - `test_golden_projection_survives_one_umbrella_rebuild_exactly_and_stale_rows_clear`
  - `test_umbrella_accounts_for_every_raw_attempt_and_records_one_receipt`
- [tests/test_repository_scopes.py](../../../../../../tests/test_repository_scopes.py) — direct import
  - `test_atomic_scope_rolls_back_nested_commits_and_serializes_writers`
- [tests/test_reveal_ledger.py](../../../../../../tests/test_reveal_ledger.py) — direct import
  - `test_migration_154_adds_the_ledger_and_the_question_event_columns`
- [tests/test_shadow_rebuild.py](../../../../../../tests/test_shadow_rebuild.py) — direct import
- [tests/test_sqlite_test_mode.py](../../../../../../tests/test_sqlite_test_mode.py) — direct import
- [tests/test_sqlite_wal.py](../../../../../../tests/test_sqlite_wal.py) — direct import
  - `test_a_long_read_transaction_delays_checkpoints_only_until_it_ends`
  - `test_connect_sets_production_pragmas_and_never_changes_the_journal_mode`
  - `test_fresh_creation_discards_an_orphaned_wal_from_a_deleted_database`
  - `test_read_only_open_in_a_read_only_directory_reads_commits_still_in_the_wal`
  - `test_read_only_open_without_a_shm_in_a_read_only_directory_fails_with_what_to_do`
  - `test_read_only_reports_work_in_a_read_only_vault_whose_wal_files_exist`
  - `test_runtime_sqlite_below_the_minimum_fails_with_a_clear_message`
  - `test_switch_fails_clearly_and_leaves_the_mode_unchanged_while_a_reader_is_open`
  - `test_wal_reset_fix_matches_the_advisory`
- [tests/test_sqlite_wal_lifecycle.py](../../../../../../tests/test_sqlite_wal_lifecycle.py) — direct import
  - `test_backup_gives_up_on_a_source_locked_after_its_probe_and_removes_the_copy`
  - `test_doctor_reports_wal_size_and_warns_when_it_is_large`
  - `test_finished_ingest_batch_truncates_the_wal`
  - `test_live_rebuild_truncates_the_wal_it_grew`
  - `test_sim_run_vault_keeps_commits_still_in_the_source_wal`
  - `test_wal_stays_bounded_across_twenty_queue_builds_on_a_fixture_copy`
- [tests/test_table_roles.py](../../../../../../tests/test_table_roles.py) — direct import
  - `test_migration_head_user_tables_match_role_registry_exactly`
  - `test_synthetic_unclassified_table_fails_registry_check`
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_migration_020_allows_teach_back_on_existing_db`
  - `test_regrade_teach_back_attempt_without_evidence_falls_back_to_core`
- [tests/test_vault_epigraphs.py](../../../../../../tests/test_vault_epigraphs.py) — direct import
  - `test_vault_epigraphs_rows_are_immutable`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/connection.py](../../../../../../src/learnloop/db/connection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
