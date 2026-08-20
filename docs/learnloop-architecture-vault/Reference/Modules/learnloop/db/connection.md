---
title: "learnloop.db.connection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/connection.py"
source_paths:
  - "src/learnloop/db/connection.py"
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

This module keeps connection behavior inside its owning package, [[Reference/Modules/learnloop/db/_package|learnloop.db]]. Its public surface centers on `connect`.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/connection.py](../../../../../../src/learnloop/db/connection.py) |
| Source lines | 26 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `connect(sqlite_path: Path, *, read_only: bool=False) -> sqlite3.Connection` ([source](../../../../../../src/learnloop/db/connection.py), line 7) — Open a configured SQLite connection.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/migrate|learnloop.db.migrate]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `connect`; statically calls `connect`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `pathlib`, `sqlite3`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/migrate|learnloop.db.migrate]], [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/conftest.py](../../../../../../tests/conftest.py) — direct import
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
  - `test_golden_projection_survives_one_umbrella_rebuild_exactly_and_stale_rows_clear`
  - `test_umbrella_accounts_for_every_raw_attempt_and_records_one_receipt`
- [tests/test_reveal_ledger.py](../../../../../../tests/test_reveal_ledger.py) — direct import
  - `test_migration_154_adds_the_ledger_and_the_question_event_columns`
- [tests/test_shadow_rebuild.py](../../../../../../tests/test_shadow_rebuild.py) — direct import
- [tests/test_table_roles.py](../../../../../../tests/test_table_roles.py) — direct import
  - `test_migration_head_user_tables_match_role_registry_exactly`
  - `test_synthetic_unclassified_table_fails_registry_check`
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_migration_020_allows_teach_back_on_existing_db`
  - `test_regrade_teach_back_attempt_without_evidence_falls_back_to_core`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/connection.py](../../../../../../src/learnloop/db/connection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
