---
title: "learnloop.db.migrate"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/migrate.py"
source_paths:
  - "src/learnloop/db/migrate.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
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

This module keeps migrate behavior inside its owning package, [[Reference/Modules/learnloop/db/_package|learnloop.db]]. Its public surface centers on `Migration`, `default_migrations_dir`, `discover_migrations`, `applied_versions`, `apply_migrations`.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/migrate.py](../../../../../../src/learnloop/db/migrate.py) |
| Source lines | 208 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class Migration` ([source](../../../../../../src/learnloop/db/migrate.py), line 21)
- `default_migrations_dir() -> Path` ([source](../../../../../../src/learnloop/db/migrate.py), line 27)
- `discover_migrations(migrations_dir: Path | None=None) -> list[Migration]` ([source](../../../../../../src/learnloop/db/migrate.py), line 31)
- `applied_versions(sqlite_path: Path) -> set[int]` ([source](../../../../../../src/learnloop/db/migrate.py), line 42)
- `apply_migrations(sqlite_path: Path, migrations_dir: Path | None=None, clock: Clock | None=None) -> list[Migration]` ([source](../../../../../../src/learnloop/db/migrate.py), line 55)

### Module constants

- `_MIGRATION_RE` ([src/learnloop/db/migrate.py](../../../../../../src/learnloop/db/migrate.py), line 13)
- `_FOREIGN_KEYS_OFF_RE` ([src/learnloop/db/migrate.py](../../../../../../src/learnloop/db/migrate.py), line 14)

## Internal implementation anchors

- `_apply_incremental_migration(connection: sqlite3.Connection, migration: Migration, clock: Clock | None) -> bool` ([source](../../../../../../src/learnloop/db/migrate.py), line 75) — Apply one existing-database migration as one durable transaction.
- `_migration_is_applied(connection: sqlite3.Connection, version: int) -> bool` ([source](../../../../../../src/learnloop/db/migrate.py), line 140)
- `_iter_sql_statements(sql: str) -> Iterator[str]` ([source](../../../../../../src/learnloop/db/migrate.py), line 155) — Yield executable statements without splitting trigger bodies.
- `_apply_fresh(sqlite_path: Path, migrations: list[Migration], clock: Clock | None) -> list[Migration]` ([source](../../../../../../src/learnloop/db/migrate.py), line 174) — Create a brand-new database with every migration, fast and atomically.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `apply_migrations`; statically calls `apply_migrations`
- [[Reference/Modules/learnloop/migration_coordinator|learnloop.migration_coordinator]] — imports `Migration`, `apply_migrations`; statically calls `apply_migrations`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `applied_versions`, `discover_migrations`; statically calls `applied_versions`, `discover_migrations`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `applied_versions`, `discover_migrations`; statically calls `applied_versions`, `discover_migrations`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `os`, `pathlib`, `re`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/migration_coordinator|learnloop.migration_coordinator]], [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_activity_contract_extensions.py](../../../../../../tests/test_activity_contract_extensions.py) — direct import
- [tests/test_activity_patterns.py](../../../../../../tests/test_activity_patterns.py) — direct import
- [tests/test_administration_adapters.py](../../../../../../tests/test_administration_adapters.py) — direct import
- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — direct import
  - `test_agent_run_token_columns_exist_and_default_to_zero`
- [tests/test_card_lineage.py](../../../../../../tests/test_card_lineage.py) — direct import
- [tests/test_commitments.py](../../../../../../tests/test_commitments.py) — direct import
- [tests/test_depth_transition.py](../../../../../../tests/test_depth_transition.py) — direct import
- [tests/test_event_sufficiency.py](../../../../../../tests/test_event_sufficiency.py) — direct import
- [tests/test_exam_seeding.py](../../../../../../tests/test_exam_seeding.py) — direct import
  - `test_migration_018_allows_exam_evidence_on_existing_db`
- [tests/test_familiarity.py](../../../../../../tests/test_familiarity.py) — direct import
- [tests/test_goal_contracts.py](../../../../../../tests/test_goal_contracts.py) — direct import
- [tests/test_journey6.py](../../../../../../tests/test_journey6.py) — direct import
- [tests/test_laddered_stems.py](../../../../../../tests/test_laddered_stems.py) — direct import
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
  - `test_migrations_are_idempotent`
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
  - `test_repository_carries_a_fixture_at_the_current_migration_head`
  - `test_scheduler_training_log_schema_is_available`
  - `test_source_exposure_index_backfill_is_idempotent_on_092_only_vault`
  - `test_source_exposure_indexes_present_on_fresh_vault`
  - `test_source_layer_migration_applies_on_pre_032_db`
  - `test_source_layer_schema_is_available`
  - `test_source_unit_selections_migration_applies_on_pre_040_db`
  - `test_source_unit_selections_schema_is_available`
  - `test_variable_rubric_scale_migration_allows_scores_above_four`
- [tests/test_persistence_open.py](../../../../../../tests/test_persistence_open.py) — direct import
  - `test_repository_attach_can_open_a_writable_scratch_copy`
  - `test_repository_attach_skips_migrations_and_can_be_physically_read_only`
- [tests/test_probe_migration.py](../../../../../../tests/test_probe_migration.py) — direct import
  - `test_migration_closes_in_progress_phases_as_superseded`
- [tests/test_progression.py](../../../../../../tests/test_progression.py) — direct import
- [tests/test_question_promotions.py](../../../../../../tests/test_question_promotions.py) — direct import
  - `test_027_rebuild_preserves_existing_rows`
  - `test_learner_claims_accepts_tutor_gap_declaration_source`
  - `test_question_promotions_schema_available_on_fresh_db`
- [tests/test_reveal_ledger.py](../../../../../../tests/test_reveal_ledger.py) — direct import
  - `test_migration_154_adds_the_ledger_and_the_question_event_columns`
- [tests/test_substrate_cutover.py](../../../../../../tests/test_substrate_cutover.py) — direct import
- [tests/test_surface_mint.py](../../../../../../tests/test_surface_mint.py) — direct import
- [tests/test_table_roles.py](../../../../../../tests/test_table_roles.py) — direct import
  - `test_migration_head_user_tables_match_role_registry_exactly`
  - `test_synthetic_unclassified_table_fails_registry_check`
- [tests/test_task_blueprints.py](../../../../../../tests/test_task_blueprints.py) — direct import
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_migration_020_allows_teach_back_on_existing_db`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/migrate.py](../../../../../../src/learnloop/db/migrate.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
