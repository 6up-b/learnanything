---
title: "learnloop.substrate.rebuild_orchestrator"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/rebuild_orchestrator.py"
source_paths:
  - "src/learnloop/substrate/rebuild_orchestrator.py"
source_commit: "2574993e6dd12dd85300cc807bf0e7321e29e1a4"
source_commit_timestamp: "2026-11-03T19:31:22-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.rebuild_orchestrator module"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.rebuild_orchestrator`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.rebuild_orchestrator` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: R2 umbrella for rebuilding every declared derived-state family.

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/rebuild_orchestrator.py](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py) |
| Source lines | 813 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2574993e6dd12dd85300cc807bf0e7321e29e1a4` |
| Commit timestamp | `2026-11-03T19:31:22-05:00` |

## Public API

- `class DerivedStateReplayer` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 34) — One ordered replay unit and the derived tables it exclusively owns.
- `class ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 43) — Observable accounting from one replay unit.
  - `as_dict(self) -> dict[str, Any]` (line 52; public)
- `class OrchestratedRebuildResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 63) — Whole-vault rebuild result plus the R3 completeness evidence.
  - `as_dict(self) -> dict[str, Any]` (line 76; public)
- `class ReplayerRegistryError(ValueError)` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 92) — The declarative replayer registry is incomplete or ambiguous.
- `class ReplayCompletenessError(RuntimeError)` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 96) — At least one raw attempt was not observed by any registered replayer.
  - `__init__(self, attempt_ids: Sequence[str])` (line 99; internal)
- `derived_table_owners(replayers: Sequence[DerivedStateReplayer]=DERIVED_STATE_REPLAYERS) -> dict[str, tuple[str, ...]]` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 226) — Return all declared owners, retaining duplicates for validation.
- `validate_replayer_registry(replayers: Sequence[DerivedStateReplayer]=DERIVED_STATE_REPLAYERS) -> None` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 238) — Require exact, unique DERIVED ownership and valid dependency order.
- `rebuild_all_derived_state(vault: LoadedVault, repository: Repository, *, learning_object_ids: list[str] | None=None, clock: Clock | None=None, require_complete_attempt_coverage: bool=True) -> OrchestratedRebuildResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 685) — Run all registered replayers and append exactly one rebuild receipt.
- `rebuild_live_derived_state(vault: LoadedVault, repository: Repository, *, learning_object_ids: list[str] | None=None, clock: Clock | None=None) -> OrchestratedRebuildResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 770) — Rebuild a vault's live database, then truncate the WAL it grew.

### Module constants

- `COLD_MASTERY_BASELINE_AT` ([src/learnloop/substrate/rebuild_orchestrator.py](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 111)
- `DERIVED_STATE_REPLAYERS` ([src/learnloop/substrate/rebuild_orchestrator.py](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 117)
- `REPLAYER_REGISTRY` ([src/learnloop/substrate/rebuild_orchestrator.py](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 223)
- `_RUNNERS` ([src/learnloop/substrate/rebuild_orchestrator.py](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 634)
- `MAX_RECURRENCE_RECONCILIATION_PASSES` ([src/learnloop/substrate/rebuild_orchestrator.py](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 659)

### Explicit exports

`__all__` declares:

- `DERIVED_STATE_REPLAYERS`
- `REPLAYER_REGISTRY`
- `DerivedStateReplayer`
- `OrchestratedRebuildResult`
- `ReplayCompletenessError`
- `ReplayerRegistryError`
- `ReplayerResult`
- `derived_table_owners`
- `rebuild_all_derived_state`
- `rebuild_derived_state_umbrella`
- `rebuild_live_derived_state`
- `validate_replayer_registry`

## Internal implementation anchors

- `class _ReplayContext` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 282)
- `_rows_in(repository: Repository, table_names: Sequence[str]) -> int` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 290)
- `_clear_tables(repository: Repository, table_names: Sequence[str]) -> dict[str, int]` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 298) — Delete a replayer's whole declared projection family atomically.
- `_run_activity_substrate(spec: DerivedStateReplayer, context: _ReplayContext) -> ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 306) — Backfill the authoritative activity ledger before learner replay.
- `_run_recurrence_groups(spec: DerivedStateReplayer, context: _ReplayContext) -> ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 333) — Clear and recompute the recurrence-group projection (no model call).
- `_run_learning_state(spec: DerivedStateReplayer, context: _ReplayContext) -> ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 355)
- `_run_canonical_projection(spec: DerivedStateReplayer, context: _ReplayContext) -> ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 416)
- `_run_identifiability(spec: DerivedStateReplayer, context: _ReplayContext) -> ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 437)
- `_run_field_outcomes(spec, context)` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 477)
- `_run_family_memory(spec: DerivedStateReplayer, context: _ReplayContext) -> ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 487)
- `_run_item_fingerprints(spec: DerivedStateReplayer, context: _ReplayContext) -> ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 514)
- `_run_source_block_fts(spec: DerivedStateReplayer, context: _ReplayContext) -> ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 525)
- `_run_router_outcomes(spec: DerivedStateReplayer, context: _ReplayContext) -> ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 537)
- `_run_retrieval_intervention_outcomes(spec: DerivedStateReplayer, context: _ReplayContext) -> ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 585)
- `_run_adaptive_difficulty(spec: DerivedStateReplayer, context: _ReplayContext) -> ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 595)
- `_run_item_forecast_scores(spec: DerivedStateReplayer, context: _ReplayContext) -> ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 605)
- `_run_retrieval_fusion_posteriors(spec: DerivedStateReplayer, context: _ReplayContext) -> ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 615)
- `_run_lesson_weight(spec: DerivedStateReplayer, context: _ReplayContext) -> ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 626)
- `_run_replayers(context: _ReplayContext) -> list[ReplayerResult]` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 662)
- `_reconcile_recurrence_groups(context: _ReplayContext) -> bool` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 666) — Refresh the recurrence projection on the inputs learner replay left.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]] — imports `COLD_MASTERY_BASELINE_AT`, `rebuild_all_derived_state`; statically calls `rebuild_all_derived_state`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `rebuild_all_derived_state`, `rebuild_live_derived_state`
- [[Reference/Modules/learnloop/regrade_contract_upgrade|learnloop.regrade_contract_upgrade]] — imports `rebuild_all_derived_state`; statically calls `rebuild_all_derived_state`
- [[Reference/Modules/learnloop/replay_ledger_upgrade|learnloop.replay_ledger_upgrade]] — imports `rebuild_all_derived_state`; statically calls `rebuild_all_derived_state`
- [[Reference/Modules/learnloop/substrate/shadow_rebuild|learnloop.substrate.shadow_rebuild]] — imports `OrchestratedRebuildResult`, `rebuild_all_derived_state`; statically calls `rebuild_all_derived_state`

### Repository tooling consumers

- [scripts/benchmark_sqlite_concurrency.py](../../../../../../scripts/benchmark_sqlite_concurrency.py); calls `rebuild_all_derived_state`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `rebuild`; calls `rebuild`
- [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]] — imports `rebuild`; calls `rebuild`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/data_capture/reading_exposures|learnloop.data_capture.reading_exposures]] — imports `module`; calls `for_version`
- [[Reference/Modules/learnloop/db/checkpoint|learnloop.db.checkpoint]] — imports `checkpoint_wal`; calls `checkpoint_wal`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/scopes|learnloop.db.scopes]] — imports `atomic_repository_call`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `rebuild_source_block_fts`; calls `rebuild_source_block_fts`
- [[Reference/Modules/learnloop/db/table_roles|learnloop.db.table_roles]] — imports `TableRole`, `tables_for_role`; calls `tables_for_role`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `fsrs_predicted_retrievability`, `load_effective_replay_rows`, `rebuild_outcome_view`; calls `fsrs_predicted_retrievability`, `load_effective_replay_rows`, `rebuild_outcome_view`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `coverage_denominator_version`; calls `coverage_denominator_version`
- [[Reference/Modules/learnloop/learner/identifiability|learnloop.learner.identifiability]] — imports `graph_identifiability_report`; calls `graph_identifiability_report`
- [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]] — imports `rebuild_lesson_weight_state`; calls `rebuild_lesson_weight_state`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `initial_mastery_state_for_learning_object`; calls `initial_mastery_state_for_learning_object`
- [[Reference/Modules/learnloop/local_embeddings/fusion|learnloop.local_embeddings.fusion]] — imports `refit_posteriors`; calls `refit_posteriors`
- [[Reference/Modules/learnloop/router/outcomes|learnloop.router.outcomes]] — imports `outcome_version_for`, `rebuild_router_outcomes`, `servable_items_by_learning_object`; calls `outcome_version_for`, `rebuild_router_outcomes`, `servable_items_by_learning_object`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `CANONICAL_PROJECTION_VERSION`, `held_for_review_attempts`, `pfc_assessments`, `project_canonical_facet_state`; calls `held_for_review_attempts`, `pfc_assessments`, `project_canonical_facet_state`
- [[Reference/Modules/learnloop/substrate/compat/activity_backfill|learnloop.substrate.compat.activity_backfill]] — imports `backfill_activity_substrate`; calls `backfill_activity_substrate`
- [[Reference/Modules/learnloop/substrate/family_memory|learnloop.substrate.family_memory]] — imports `PROJECTION_LEGACY_FALLBACK`, `rebuild_family_memory`; calls `rebuild_family_memory`
- [[Reference/Modules/learnloop/substrate/intervention_outcomes|learnloop.substrate.intervention_outcomes]] — imports `rebuild_intervention_outcomes`; calls `rebuild_intervention_outcomes`
- [[Reference/Modules/learnloop/substrate/item_fingerprints|learnloop.substrate.item_fingerprints]] — imports `rebuild_item_fingerprints`; calls `rebuild_item_fingerprints`
- [[Reference/Modules/learnloop/substrate/recurrence_groups|learnloop.substrate.recurrence_groups]] — imports `active_group_map`, `refresh_recurrence_groups`; calls `active_group_map`, `refresh_recurrence_groups`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `rebuild_derived_state`; calls `rebuild_derived_state`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]], [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/regrade_contract_upgrade|learnloop.regrade_contract_upgrade]], [[Reference/Modules/learnloop/replay_ledger_upgrade|learnloop.replay_ledger_upgrade]], [[Reference/Modules/learnloop/substrate/shadow_rebuild|learnloop.substrate.shadow_rebuild]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_fix_r5.py](../../../../../../tests/test_ad23_fix_r5.py) — direct import
  - `test_an_item_that_landed_before_expiry_gets_its_receipt_at_a_later_serve`
- [tests/test_ad23_fix_r6.py](../../../../../../tests/test_ad23_fix_r6.py) — direct import
  - `test_one_owner_at_equal_timestamps_and_the_first_attribution_is_final`
- [tests/test_ad23_successor.py](../../../../../../tests/test_ad23_successor.py) — direct import
  - `test_below_the_tag_a_rebuild_writes_no_ad_state`
- [tests/test_ad2_model.py](../../../../../../tests/test_ad2_model.py) — direct import
  - `test_zero_model_calls`
- [tests/test_ad_guard_offer_receipts.py](../../../../../../tests/test_ad_guard_offer_receipts.py) — direct import
  - `test_rebuild_derived_state_over_a_learner_pick_runs_with_zero_denials`
- [tests/test_ad_guard_reachable_reads.py](../../../../../../tests/test_ad_guard_reachable_reads.py) — direct import
- [tests/test_adaptive_difficulty_ad1.py](../../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
  - `test_replay_reads_receipts_zero_model_calls`
- [tests/test_approach_map_replay.py](../../../../../../tests/test_approach_map_replay.py) — direct import
  - `test_rebuild_and_replay_call_no_model_and_never_read_approach_maps`
- [tests/test_assumed_known.py](../../../../../../tests/test_assumed_known.py) — direct import
  - `test_placement_receipts_survive_rebuild_with_zero_model_calls`
- [tests/test_daily_plan_composition.py](../../../../../../tests/test_daily_plan_composition.py) — direct import
  - `test_an_empty_stuck_answer_on_a_plan_item_is_done_and_labelled_daily_plan`
- [tests/test_daily_plan_replay.py](../../../../../../tests/test_daily_plan_replay.py) — direct import
  - `test_rebuild_ignores_the_plan_and_calls_no_model`
- [tests/test_data_capture_landing_review.py](../../../../../../tests/test_data_capture_landing_review.py) — direct import
  - `test_f1_a_rebuild_with_no_decisions_needs_no_read`
  - `test_f1_a_rebuild_with_no_sweep_cannot_bring_back_the_cold_label`
- [tests/test_data_capture_successor.py](../../../../../../tests/test_data_capture_successor.py) — direct import
  - `test_the_outcomes_cache_is_rebuilt_under_the_vaults_version`
- [tests/test_diagnosis_input_provenance.py](../../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_f5_replay_never_reads_the_switch_or_the_records`
- [tests/test_diagnosis_replay.py](../../../../../../tests/test_diagnosis_replay.py) — direct import
  - `test_joint_fixture_rebuild_is_identical_at_the_previous_version`
  - `test_replay_makes_zero_model_and_embedding_calls`
  - `test_split_vault_rebuild_is_a_fixed_point_and_keeps_diagnosis_sourced_causes`
- [tests/test_embedding_store.py](../../../../../../tests/test_embedding_store.py) — direct import
  - `test_replay_preserves_paid_inputs_without_models`
- [tests/test_evsi_router_composition.py](../../../../../../tests/test_evsi_router_composition.py) — direct import
- [tests/test_exam_protection_review.py](../../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_replay_never_reads_the_switch`
- [tests/test_family_memory_projection.py](../../../../../../tests/test_family_memory_projection.py) — direct import
  - `test_rebuild_and_evaluation_fold_the_same_leak_aware_rows`
  - `test_registry_has_exactly_one_owner_on_the_outcome_view`
- [tests/test_figure_requests_migration.py](../../../../../../tests/test_figure_requests_migration.py) — direct import
  - `test_no_replayer_reads_the_request_ledger`
- [tests/test_figures_migration.py](../../../../../../tests/test_figures_migration.py) — direct import
  - `test_no_replayer_reads_the_figure_tables`
- [tests/test_forecast_receipts.py](../../../../../../tests/test_forecast_receipts.py) — direct import
  - `test_replay_neither_reads_nor_writes_forecast_receipts`
- [tests/test_held_grade_composition.py](../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_router_never_scores_a_held_attempt_and_its_fold_applies_no_review`
- [tests/test_held_grade_evidence.py](../../../../../../tests/test_held_grade_evidence.py) — direct import
  - `test_f2_a_regrade_that_validates_nothing_keeps_the_hold`
  - `test_f4_a_validating_regrade_leaves_no_stale_unassessed_row`
  - `test_f5_an_adjudication_releases_the_follow_up_suppression`
  - `test_f9_f10_held_grades_build_no_failure_streak_and_move_no_item_quality`
  - `test_review_f1_a_regrade_into_a_hold_supersedes_the_assessed_grade_it_replaces`
  - `test_review_f1_the_ledger_reads_the_evidence_as_the_attempt_step_does`
- [tests/test_hint_telemetry.py](../../../../../../tests/test_hint_telemetry.py) — direct import
  - `test_rebuild_with_help_assists_populated_calls_no_model_and_never_reads_it`
- [tests/test_intervention_outcomes_replayer.py](../../../../../../tests/test_intervention_outcomes_replayer.py) — direct import
  - `test_the_replayer_is_registered_deterministic_and_calls_nothing`
- [tests/test_item_fingerprints.py](../../../../../../tests/test_item_fingerprints.py) — direct import
  - `test_a_published_item_later_used_as_the_parent_rebuilds`
  - `test_a_vault_without_families_has_no_fingerprint_rows`
  - `test_rebuild_recomputes_fingerprints_without_any_model_or_generator`
  - `test_skeletons_from_one_model_at_two_prompt_versions_rebuild_without_a_key_collision`
- [tests/test_learner_report_superseded.py](../../../../../../tests/test_learner_report_superseded.py) — direct import
  - `test_a_new_starting_level_keeps_the_old_one_for_an_lo_first_practised_under_it`
  - `test_random_attempts_and_learner_reports_rebuild_to_live`
  - `test_the_activation_derives_what_the_predecessor_derived`
  - `test_two_rung_requests_on_a_cold_lo_then_an_attempt_rebuild_to_live`
- [tests/test_lp_claim_fixes.py](../../../../../../tests/test_lp_claim_fixes.py) — direct import
  - `test_off_is_the_predecessor_on_a_tracked_fixture_copy`
  - `test_owner_copies_off_is_the_predecessor_and_on_reports_the_mastery_deltas`
- [tests/test_lp_claim_fixes_review.py](../../../../../../tests/test_lp_claim_fixes_review.py) — direct import
- [tests/test_method_explicit_upgrade.py](../../../../../../tests/test_method_explicit_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
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
  - `test_an_mvp017_vault_replays_its_grades_exactly`
  - `test_the_bounded_replay_corrects_the_copy_in_one_rebuild_and_then_changes_nothing`
  - `test_upgrading_the_mvp017_copy_to_the_successor_rewrites_no_grade`
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
- [tests/test_pfc_unassessed_readers.py](../../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_a_record_written_before_the_rule_keeps_its_interpretation_until_regraded`
  - `test_an_ordinary_item_gives_the_unverified_criterion_s_facet_nothing`
- [tests/test_pfc_unverified_unassessed.py](../../../../../../tests/test_pfc_unverified_unassessed.py) — direct import
  - `test_joint_fixture_replays_through_the_unchanged_path`
  - `test_joint_grades_replay_untouched_beside_blind_unverified_ones`
  - `test_split_vault_replay_and_rebuild_keep_unverified_criteria_unassessed`
- [tests/test_plan_determinism.py](../../../../../../tests/test_plan_determinism.py) — direct import
  - `test_replay_never_reads_the_switch`
- [tests/test_plan_follows_path.py](../../../../../../tests/test_plan_follows_path.py) — direct import
  - `test_g47_a_rebuild_shows_zero_projection_deltas_and_never_reads_a_path`
- [tests/test_practice_index_dossiers.py](../../../../../../tests/test_practice_index_dossiers.py) — direct import
  - `test_rebuild_preserves_dossiers_and_calls_no_model`
- [tests/test_reader_workbench_rw2a.py](../../../../../../tests/test_reader_workbench_rw2a.py) — direct import
  - `test_an_abandoned_session_writes_no_attempt_and_a_rebuild_leaves_the_workbench_alone`
  - `test_round4_f2_held_assistance_on_an_independent_only_item_is_assisted_on_every_submit_path_and_after_replay`
- [tests/test_reading_step_switch.py](../../../../../../tests/test_reading_step_switch.py) — direct import
  - `test_replay_never_reads_the_switch`
- [tests/test_rebuild_equivalence.py](../../../../../../tests/test_rebuild_equivalence.py) — direct import
  - `test_a_full_sync_after_a_rebuild_keeps_retired_items_retired`
  - `test_a_retired_item_stays_inactive_through_a_primary_load_and_a_rebuild`
  - `test_a_two_attempt_history_without_claims_rebuilds_to_live_mastery`
  - `test_content_sync_nests_inside_a_rebuild_transaction_and_rolls_back_with_it`
  - `test_random_attempt_histories_rebuild_to_live_state_exactly`
  - `test_random_histories_with_claims_after_attempts_and_too_easy_retirements_rebuild_to_live`
  - `test_replay_reads_no_attempt_recorded_after_the_one_it_recomputes`
- [tests/test_rebuild_equivalence_review.py](../../../../../../tests/test_rebuild_equivalence_review.py) — direct import
  - `test_a_partial_rebuild_under_the_tag_does_not_complete_the_activation`
  - `test_two_same_second_attempts_committed_in_reverse_id_order_rebuild_to_live`
- [tests/test_rebuild_orchestrator.py](../../../../../../tests/test_rebuild_orchestrator.py) — direct import
  - `test_golden_projection_survives_one_umbrella_rebuild_exactly_and_stale_rows_clear`
  - `test_live_rebuild_completeness_failure_publishes_nothing`
  - `test_live_rebuild_failure_preserves_all_published_state`
  - `test_replayer_registry_owns_each_derived_table_exactly_once`
  - `test_same_version_full_rebuild_is_semantically_idempotent_on_golden_fixture`
  - `test_umbrella_accounts_for_every_raw_attempt_and_records_one_receipt`
- [tests/test_recurrence_commands.py](../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_a_vault_with_no_merges_rebuilds_with_an_empty_projection`
  - `test_rebuild_makes_no_model_call_and_is_a_fixed_point`
  - `test_the_head_fixture_predecessor_to_successor_path`
- [tests/test_recurrence_live.py](../../../../../../tests/test_recurrence_live.py) — direct import
  - `test_a_verdict_after_a_promotion_moves_only_the_group_projection_and_rebuild_matches_live`
- [tests/test_regrade_contract_replay.py](../../../../../../tests/test_regrade_contract_replay.py) — direct import
  - `test_case1_a_model_grade_regraded_above_its_original_maximum_is_saved`
  - `test_case2_a_model_grade_regraded_within_its_original_maximum_replays_its_own_maximum`
  - `test_case3_a_lowered_rubric_that_still_fits_never_rescores_the_regrade`
  - `test_case3_lowering_the_rubric_after_a_regrade_never_fails_the_rebuild`
- [tests/test_regrade_contract_successor.py](../../../../../../tests/test_regrade_contract_successor.py) — direct import
- [tests/test_regrade_contract_upgrade.py](../../../../../../tests/test_regrade_contract_upgrade.py) — direct import
  - `test_after_the_upgrade_a_rebuild_settles_and_stays`
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_required_method_authority.py](../../../../../../tests/test_required_method_authority.py) — direct import
  - `test_a_live_answer_its_regrade_and_replay_are_graded_under_the_frozen_field`
- [tests/test_required_method_grading.py](../../../../../../tests/test_required_method_grading.py) — direct import
  - `test_a_regrade_grades_the_statement_and_rubric_its_method_was_frozen_with`
  - `test_grades_recorded_at_the_predecessor_replay_unchanged_after_the_upgrade`
  - `test_replay_reproduces_method_grades_without_a_model`
- [tests/test_retrieval_spaces_migration.py](../../../../../../tests/test_retrieval_spaces_migration.py) — direct import
  - `test_table_roles_and_the_one_replayer`
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_f1_live_an_incomplete_grade_with_nothing_located_is_held`
  - `test_f4_the_graders_route_verdict_reaches_the_judgment_ledger_and_regrades_supersede_it`
  - `test_f5_a_regrade_with_the_rule_switched_off_supersedes_the_held_verdict`
  - `test_live_an_adjudication_releases_a_hold_on_replay`
  - `test_live_nothing_located_and_nothing_validated_is_held`
  - `test_replay_reproduces_ruled_grades_without_a_model`
- [tests/test_router_coldness_covariates.py](../../../../../../tests/test_router_coldness_covariates.py) — direct import
  - `test_the_replayer_records_the_fsrs_predicted_retrievability`
- [tests/test_router_outcomes.py](../../../../../../tests/test_router_outcomes.py) — direct import
  - `test_router_tables_survive_rebuild_under_production_pragmas`
  - `test_the_replayer_rebuilds_router_outcomes_deterministically_with_no_model_call`
- [tests/test_router_r1_composition.py](../../../../../../tests/test_router_r1_composition.py) — direct import
  - `test_plan_block_decisions_get_router_decision_ids_end_to_end`
- [tests/test_router_r2a_serving.py](../../../../../../tests/test_router_r2a_serving.py) — direct import
  - `test_presentations_and_cards_survive_production_pragmas`
  - `test_router_outcomes_v2_replay_twice_with_no_model_call`
- [tests/test_source_block_fts.py](../../../../../../tests/test_source_block_fts.py) — direct import
  - `test_the_index_is_derived_with_one_owner_and_its_shadow_tables_are_not_tables`
  - `test_the_umbrella_rebuild_restores_the_index_without_any_model_or_embedding_call`
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — direct import
  - `test_signals_join_their_delivery_and_the_posterior_replays_byte_identically`
- [tests/test_sqlite_wal_lifecycle.py](../../../../../../tests/test_sqlite_wal_lifecycle.py) — direct import
  - `test_live_rebuild_truncates_the_wal_it_grew`
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — direct import
  - `test_an_empty_stuck_answer_is_a_bare_zero_with_no_error_tag`
- [tests/test_stuck_prompt_replay.py](../../../../../../tests/test_stuck_prompt_replay.py) — direct import
  - `test_a_joint_stuck_reading_survives_rebuild_with_no_model_call`
  - `test_a_stuck_vault_rebuilds_to_a_fixed_point_with_no_model_call`
  - `test_historical_dont_know_rows_replay_unchanged_under_the_successor`
  - `test_the_kill_switch_never_changes_how_stuck_answers_replay`
- [tests/test_teacher_te1_successor.py](../../../../../../tests/test_teacher_te1_successor.py) — direct import
  - `test_a_shadow_rebuild_after_a_lesson_has_zero_projection_deltas`
  - `test_the_whole_rebuild_owns_the_lesson_weight_tables_and_reproduces_them`
- [tests/test_voi_stopping.py](../../../../../../tests/test_voi_stopping.py) — direct import
- [tests/test_workbench_assistance.py](../../../../../../tests/test_workbench_assistance.py) — direct import
  - `test_an_abandoned_problem_writes_no_attempt_and_a_rebuild_leaves_the_evidence`

## Modification guidance

- Change rebuild orchestrator policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/rebuild_orchestrator.py](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
