---
title: "learnloop.vault.repository"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault/repository.py"
source_paths:
  - "src/learnloop/vault/repository.py"
source_commit: "4422791ddadf4e39abf1975876e86c3fdf45b18f"
source_commit_timestamp: "2026-10-25T14:26:31-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.vault"
layer: "infrastructure"
concepts:
  - "State and Persistence"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.vault.repository module"
  - "src/learnloop/vault/repository.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-vault"
---

# `learnloop.vault.repository`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.vault.repository` exists within [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] to own the behavior summarized by its module contract: Application-level repository opening for a configured vault.

The authoritative system-level explanation remains in [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault/repository.py](../../../../../../src/learnloop/vault/repository.py) |
| Source lines | 103 |
| Owning package | [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `4422791ddadf4e39abf1975876e86c3fdf45b18f` |
| Commit timestamp | `2026-10-25T14:26:31-04:00` |

## Public API

- `open_vault_repository(vault_root: Path, sqlite_path: Path, *, migrations_dir: Path | None=None, clock: Clock | None=None, timeout_s: float=DEFAULT_TIMEOUT_S) -> Repository` ([source](../../../../../../src/learnloop/vault/repository.py), line 37) — Migrate and attach a repository under the vault mutation lock.
- `complete_interrupted_activation(vault_root: Path, sqlite_path: Path) -> None` ([source](../../../../../../src/learnloop/vault/repository.py), line 63) — Complete an activation a dead process left journalled, or raise (LP-min (a), re-review F2).
- `vault_repository(paths: VaultPaths) -> Repository` ([source](../../../../../../src/learnloop/vault/repository.py), line 81) — The vault's repository for code below an entry point.

### Explicit exports

`__all__` declares:

- `complete_interrupted_activation`
- `open_vault_repository`
- `vault_repository`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ad_successor_upgrade|learnloop.ad_successor_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/attempt_content_state_upgrade|learnloop.attempt_content_state_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/bootstrap|learnloop.bootstrap]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/cli/curriculum|learnloop.cli.curriculum]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/cli/data|learnloop.cli.data]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/cli/facets|learnloop.cli.facets]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/cli/families|learnloop.cli.families]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/cli/gaps|learnloop.cli.gaps]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/cli/recurrence|learnloop.cli.recurrence]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/cli/teacher|learnloop.cli.teacher]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/cold_retry_reschedule_upgrade|learnloop.cold_retry_reschedule_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/content/facet_identity/dedupe|learnloop.content.facet_identity.dedupe]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/curriculum/concepts|learnloop.curriculum.concepts]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/curriculum/golden_path_fixture|learnloop.curriculum.golden_path_fixture]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/curriculum/graph_edit_proposals|learnloop.curriculum.graph_edit_proposals]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/daily_plan_upgrade|learnloop.daily_plan_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/data_capture_upgrade|learnloop.data_capture_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/decider_upgrade|learnloop.decider_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/deliverable_plan_upgrade|learnloop.deliverable_plan_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/diagnosis/grading_hardcases|learnloop.diagnosis.grading_hardcases]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/diagnosis/recurrence/upgrade|learnloop.diagnosis.recurrence.upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/eligibility_decision_upgrade|learnloop.eligibility_decision_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/records|learnloop.experiments.contextual_embeddings.records]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/help_fold_attach_upgrade|learnloop.help_fold_attach_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/intent_upgrade|learnloop.intent_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/learner/recall_calibration|learnloop.learner.recall_calibration]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/learner_text_gap_upgrade|learnloop.learner_text_gap_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/lesson_suggestions_upgrade|learnloop.lesson_suggestions_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/method_explicit_upgrade|learnloop.method_explicit_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/one_ask_upgrade|learnloop.one_ask_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/ops/contamination/report|learnloop.ops.contamination.report]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/ops/pf_reports|learnloop.ops.pf_reports]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/probe_tie_upgrade|learnloop.probe_tie_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/proof_check_upgrade|learnloop.proof_check_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/reader_followups_upgrade|learnloop.reader_followups_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/reading_path_plan_upgrade|learnloop.reading_path_plan_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/regrade_contract_upgrade|learnloop.regrade_contract_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/replay_ledger_upgrade|learnloop.replay_ledger_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/route_rules_upgrade|learnloop.route_rules_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/router_mixture_upgrade|learnloop.router_mixture_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/router_staged_upgrade|learnloop.router_staged_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/sim/diagnostic_validation|learnloop.sim.diagnostic_validation]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/sources_upgrade|learnloop.sources_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/stuck_prompt_upgrade|learnloop.stuck_prompt_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/superseded_claims_upgrade|learnloop.superseded_claims_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/teacher_upgrade|learnloop.teacher_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `vault_repository`; statically calls `vault_repository`
- [[Reference/Modules/learnloop/voi_stopping_upgrade|learnloop.voi_stopping_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/workbench_field_signals_upgrade|learnloop.workbench_field_signals_upgrade]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `open_vault_repository`; statically calls `open_vault_repository`

### Repository tooling consumers

- [scripts/benchmark_sqlite_concurrency.py](../../../../../../scripts/benchmark_sqlite_concurrency.py); calls `open_vault_repository`
- [scripts/gen_goldenpath_fixtures.py](../../../../../../scripts/gen_goldenpath_fixtures.py); calls `open_vault_repository`
- [scripts/voi_cap_report.py](../../../../../../scripts/voi_cap_report.py); calls `open_vault_repository`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/activation_journal|learnloop.activation_journal]] — imports `module`; calls `complete`, `completing`, `pending`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/migrate|learnloop.db.migrate]] — imports `UncoordinatedMigrationError`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`; calls `Repository`
- [[Reference/Modules/learnloop/migration_coordinator|learnloop.migration_coordinator]] — imports `migrate_vault`; calls `migrate_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `DEFAULT_TIMEOUT_S`

### Platform and third-party dependencies

- Standard library: `__future__`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/ad_successor_upgrade|learnloop.ad_successor_upgrade]], [[Reference/Modules/learnloop/attempt_content_state_upgrade|learnloop.attempt_content_state_upgrade]], [[Reference/Modules/learnloop/bootstrap|learnloop.bootstrap]], [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]], [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]] and 74 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_activity_backfill.py](../../../../../../tests/test_activity_backfill.py) — direct import
  - `test_backfill_is_idempotent_on_fixture_copy`
  - `test_backfill_logs_attempt_duration_interaction_events`
  - `test_backfill_marks_unverifiable_for_missing_item`
  - `test_backfill_populates_substrate_from_fixture`
  - `test_backfill_render_once_per_shared_surface`
  - `test_diagnostic_probe_attempts_reuse_shared_surface_hash`
- [tests/test_ai_compare.py](../../../../../../tests/test_ai_compare.py) — direct import
  - `test_a_json_repair_carries_the_budget_of_the_request_it_repairs`
  - `test_each_request_carries_the_output_budget_its_estimate_reports`
- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
- [tests/test_collection_dataset.py](../../../../../../tests/test_collection_dataset.py) — direct import
  - `test_adjudicate_cli_records_through_the_locked_vault_opener`
- [tests/test_coordinated_migrations.py](../../../../../../tests/test_coordinated_migrations.py) — direct import
  - `test_vault_repository_attaches_a_current_vault_without_the_coordinator`
  - `test_vault_repository_upgrades_a_vault_that_is_behind_through_the_coordinator`
- [tests/test_daily_loop_start_minutes.py](../../../../../../tests/test_daily_loop_start_minutes.py) — direct import
  - `test_the_streak_count_is_unchanged_on_fixture_copies`
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
  - `test_q14_on_a_vault_the_coordinator_upgrades_the_receipt_commits_with_the_grade`
- [tests/test_exam_protection_identity.py](../../../../../../tests/test_exam_protection_identity.py) — direct import
  - `test_f3_final_a_cli_upgrade_records_what_membership_qualifies_before_a_hand_edit`
- [tests/test_goal_decay_projection.py](../../../../../../tests/test_goal_decay_projection.py) — direct import
  - `test_linear_algebra_fixture_golden_projection`
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — direct import
  - `test_fixture_vault_goal_over_unauthored_concepts_resolves`
- [tests/test_learner_read_model_pinning.py](../../../../../../tests/test_learner_read_model_pinning.py) — direct import
- [tests/test_learner_report_superseded.py](../../../../../../tests/test_learner_report_superseded.py) — direct import
- [tests/test_lp_claim_fixes.py](../../../../../../tests/test_lp_claim_fixes.py) — direct import
  - `test_owner_copies_off_is_the_predecessor_and_on_reports_the_mastery_deltas`
- [tests/test_lp_claim_fixes_rereview.py](../../../../../../tests/test_lp_claim_fixes_rereview.py) — direct import
- [tests/test_migration_coordinator.py](../../../../../../tests/test_migration_coordinator.py) — direct import
- [tests/test_migrations.py](../../../../../../tests/test_migrations.py) — direct import
  - `test_opening_the_vault_applies_pending_migrations_a_bare_repository_refuses`
- [tests/test_mvp017_route_check_replay.py](../../../../../../tests/test_mvp017_route_check_replay.py) — direct import
- [tests/test_output_budget.py](../../../../../../tests/test_output_budget.py) — direct import
- [tests/test_placement_fixture_copies.py](../../../../../../tests/test_placement_fixture_copies.py) — direct import
- [tests/test_practice_index_adapters.py](../../../../../../tests/test_practice_index_adapters.py) — direct import
- [tests/test_practice_index_admission.py](../../../../../../tests/test_practice_index_admission.py) — direct import
- [tests/test_practice_index_dossiers.py](../../../../../../tests/test_practice_index_dossiers.py) — direct import
  - `test_switch_off_and_unknown_metered_price_fail_closed`
- [tests/test_practice_index_evaluation.py](../../../../../../tests/test_practice_index_evaluation.py) — direct import
  - `test_blocked_states_make_no_calls`
- [tests/test_practice_index_find.py](../../../../../../tests/test_practice_index_find.py) — direct import
  - `test_a_forced_dossier_path_falls_back_while_dossiers_are_missing`
  - `test_an_alternative_embedding_model_takes_an_explicit_price`
- [tests/test_practice_index_paid.py](../../../../../../tests/test_practice_index_paid.py) — direct import
- [tests/test_rbeq_pr2_landing.py](../../../../../../tests/test_rbeq_pr2_landing.py) — direct import
- [tests/test_receipt_derivation.py](../../../../../../tests/test_receipt_derivation.py) — direct import
  - `test_ready_derivation_none_on_legacy_vault`
- [tests/test_receipt_exactness.py](../../../../../../tests/test_receipt_exactness.py) — direct import
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_f5_a_regrade_supersedes_an_mvp017_route_check_verdict`
- [tests/test_sqlite_wal_lifecycle.py](../../../../../../tests/test_sqlite_wal_lifecycle.py) — direct import
  - `test_live_rebuild_truncates_the_wal_it_grew`
  - `test_wal_stays_bounded_across_twenty_queue_builds_on_a_fixture_copy`
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains repository within learnloop.vault; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/vault/repository.py](../../../../../../src/learnloop/vault/repository.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
