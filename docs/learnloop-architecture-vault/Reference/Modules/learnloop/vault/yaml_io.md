---
title: "learnloop.vault.yaml_io"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault/yaml_io.py"
source_paths:
  - "src/learnloop/vault/yaml_io.py"
source_commit: "7a2e4135bbc440eff990392a9e5c5b69e6637d85"
source_commit_timestamp: "2026-10-13T14:47:04-04:00"
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
  - "learnloop.vault.yaml_io module"
  - "src/learnloop/vault/yaml_io.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-vault"
---

# `learnloop.vault.yaml_io`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps yaml io behavior inside its owning package, [[Reference/Modules/learnloop/vault/_package|learnloop.vault]]. Its public surface centers on `read_yaml`, `read_yaml_data`, `write_yaml`, `yaml_to_string`, `yaml_from_string`, `read_markdown_with_frontmatter`, `read_markdown_frontmatter_data`, `write_markdown_with_frontmatter`.

The authoritative system-level explanation remains in [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault/yaml_io.py](../../../../../../src/learnloop/vault/yaml_io.py) |
| Source lines | 267 |
| Owning package | [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `7a2e4135bbc440eff990392a9e5c5b69e6637d85` |
| Commit timestamp | `2026-10-13T14:47:04-04:00` |

## Public API

- `read_yaml(path: Path) -> dict[str, Any]` ([source](../../../../../../src/learnloop/vault/yaml_io.py), line 27) — Load a YAML mapping for editing.
- `read_yaml_data(path: Path) -> dict[str, Any]` ([source](../../../../../../src/learnloop/vault/yaml_io.py), line 43) — Load a YAML mapping as plain Python data, for callers that never write it back.
- `write_yaml(path: Path, data: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/vault/yaml_io.py), line 96)
- `yaml_to_string(data: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/vault/yaml_io.py), line 103)
- `yaml_from_string(text: str) -> Any` ([source](../../../../../../src/learnloop/vault/yaml_io.py), line 107) — Parse YAML text for editing (the round-trip loader ``read_yaml`` uses).
- `read_markdown_with_frontmatter(path: Path) -> tuple[dict[str, Any], str]` ([source](../../../../../../src/learnloop/vault/yaml_io.py), line 117)
- `read_markdown_frontmatter_data(path: Path) -> tuple[dict[str, Any], str]` ([source](../../../../../../src/learnloop/vault/yaml_io.py), line 130) — ``read_markdown_with_frontmatter`` for read-only callers; see ``read_yaml_data``.
- `write_markdown_with_frontmatter(path: Path, metadata: dict[str, Any], body: str) -> None` ([source](../../../../../../src/learnloop/vault/yaml_io.py), line 149)

### Module constants

- `WIDE_EMITTER_WIDTH` ([src/learnloop/vault/yaml_io.py](../../../../../../src/learnloop/vault/yaml_io.py), line 65)
- `_NEEDS_ROUND_TRIP` ([src/learnloop/vault/yaml_io.py](../../../../../../src/learnloop/vault/yaml_io.py), line 167)
- `_TAG_OR_DIRECTIVE` ([src/learnloop/vault/yaml_io.py](../../../../../../src/learnloop/vault/yaml_io.py), line 172)
- `_CANONICAL_INT` ([src/learnloop/vault/yaml_io.py](../../../../../../src/learnloop/vault/yaml_io.py), line 173)
- `_TAG_PREFIX` ([src/learnloop/vault/yaml_io.py](../../../../../../src/learnloop/vault/yaml_io.py), line 174)
- `_MERGE_OR_VALUE_KEY_TAGS` ([src/learnloop/vault/yaml_io.py](../../../../../../src/learnloop/vault/yaml_io.py), line 175)

## Internal implementation anchors

- `_yaml() -> YAML` ([source](../../../../../../src/learnloop/vault/yaml_io.py), line 19)
- `_dumped(data: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/vault/yaml_io.py), line 68) — The YAML text for ``data``, guaranteed to read back.
- `class _RoundTripOnly(Exception)` ([source](../../../../../../src/learnloop/vault/yaml_io.py), line 178) — The document uses a form only the round-trip loader reproduces exactly.
- `_fast_load(text: str, loader: type | None=None) -> Any` ([source](../../../../../../src/learnloop/vault/yaml_io.py), line 182) — Parse ``text`` on the fast path, or return ``_NEEDS_ROUND_TRIP``.
- `_build_fast_loader(base: type) -> type` ([source](../../../../../../src/learnloop/vault/yaml_io.py), line 194) — Subclass a PyYAML safe loader (C or pure Python) with round-trip scalar rules.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `read_yaml`; statically calls `read_yaml`
- [[Reference/Modules/learnloop/cli/calibration|learnloop.cli.calibration]] — imports `read_yaml`; statically calls `read_yaml`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `read_yaml`, `yaml_to_string`; statically calls `read_yaml`, `yaml_to_string`
- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `read_yaml`, `yaml_from_string`, `yaml_to_string`; statically calls `read_yaml`, `yaml_from_string`, `yaml_to_string`
- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `read_yaml`, `yaml_from_string`; statically calls `read_yaml`, `yaml_from_string`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `read_yaml`, `write_markdown_with_frontmatter`, `write_yaml`; statically calls `read_yaml`, `write_markdown_with_frontmatter`, `write_yaml`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `read_yaml`, `write_yaml`; statically calls `read_yaml`, `write_yaml`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_eval|learnloop.content.synthesis.synthesis_eval]] — imports `read_yaml`; statically calls `read_yaml`
- [[Reference/Modules/learnloop/curriculum/concepts|learnloop.curriculum.concepts]] — imports `read_markdown_with_frontmatter`, `read_yaml`, `write_markdown_with_frontmatter`, `write_yaml`; statically calls `read_markdown_with_frontmatter`, `read_yaml`, `write_markdown_with_frontmatter`, `write_yaml`
- [[Reference/Modules/learnloop/curriculum/golden_path_fixture|learnloop.curriculum.golden_path_fixture]] — imports `write_yaml`; statically calls `write_yaml`
- [[Reference/Modules/learnloop/curriculum/integration_backfill|learnloop.curriculum.integration_backfill]] — imports `read_yaml`, `write_yaml`, `yaml_to_string`; statically calls `read_yaml`, `write_yaml`, `yaml_to_string`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `read_yaml`; statically calls `read_yaml`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `read_yaml`, `write_yaml`; statically calls `read_yaml`, `write_yaml`
- [[Reference/Modules/learnloop/intent/deadline|learnloop.intent.deadline]] — imports `read_yaml`, `yaml_to_string`; statically calls `read_yaml`, `yaml_to_string`
- [[Reference/Modules/learnloop/learner/learner_profile|learnloop.learner.learner_profile]] — imports `read_yaml`, `write_yaml`; statically calls `read_yaml`, `write_yaml`
- [[Reference/Modules/learnloop/ops/content_fixes|learnloop.ops.content_fixes]] — imports `read_yaml`, `yaml_to_string`; statically calls `read_yaml`, `yaml_to_string`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `read_yaml_data`; statically calls `read_yaml_data`
- [[Reference/Modules/learnloop/sim/profiles|learnloop.sim.profiles]] — imports `read_yaml`; statically calls `read_yaml`
- [[Reference/Modules/learnloop/sim/sweep|learnloop.sim.sweep]] — imports `read_yaml`; statically calls `read_yaml`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `read_yaml`, `yaml_to_string`; statically calls `read_yaml`, `yaml_to_string`
- [[Reference/Modules/learnloop/substrate/families|learnloop.substrate.families]] — imports `read_yaml`, `yaml_to_string`; statically calls `read_yaml`, `yaml_to_string`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `read_markdown_frontmatter_data`, `read_markdown_with_frontmatter`, `read_yaml_data`, `write_markdown_with_frontmatter`, `write_yaml`; statically calls `read_markdown_frontmatter_data`, `read_markdown_with_frontmatter`, `write_markdown_with_frontmatter`, `write_yaml`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `read_yaml`, `write_yaml`; statically calls `read_yaml`, `write_yaml`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `read_yaml`, `write_yaml`; statically calls `read_yaml`, `write_yaml`
- [[Reference/Modules/learnloop_sidecar/handlers/router_objective|learnloop_sidecar.handlers.router_objective]] — imports `read_yaml`, `write_yaml`; statically calls `read_yaml`, `write_yaml`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `io`, `pathlib`, `re`, `typing`
- Third party: `ruamel`, `yaml`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cli/calibration|learnloop.cli.calibration]], [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]], [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] and 20 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/approach_map_fakes.py](../../../../../../tests/approach_map_fakes.py) — direct import
- [tests/deliverable_fixtures.py](../../../../../../tests/deliverable_fixtures.py) — direct import
- [tests/diagnosis_split_helpers.py](../../../../../../tests/diagnosis_split_helpers.py) — direct import
- [tests/exam_scope_fixtures.py](../../../../../../tests/exam_scope_fixtures.py) — direct import
- [tests/followup_serve_helpers.py](../../../../../../tests/followup_serve_helpers.py) — direct import
- [tests/helpers.py](../../../../../../tests/helpers.py) — direct import
- [tests/library_ask_fixtures.py](../../../../../../tests/library_ask_fixtures.py) — direct import
- [tests/mcp_world.py](../../../../../../tests/mcp_world.py) — direct import
- [tests/practice_index_fakes.py](../../../../../../tests/practice_index_fakes.py) — direct import
- [tests/reading_path_fixtures.py](../../../../../../tests/reading_path_fixtures.py) — direct import
- [tests/section_coverage_fixtures.py](../../../../../../tests/section_coverage_fixtures.py) — direct import
- [tests/source_service_fakes.py](../../../../../../tests/source_service_fakes.py) — direct import
- [tests/teacher_fakes.py](../../../../../../tests/teacher_fakes.py) — direct import
- [tests/test_activity_families.py](../../../../../../tests/test_activity_families.py) — direct import
  - `test_apply_undo_preserves_cards_and_owner_edits`
  - `test_auto_family_rechecks_judged_content_from_disk`
  - `test_complete_link_cannot_chain_pair_judgments`
  - `test_ensemble_source_kind_loads_and_round_trips`
  - `test_family_schema_and_loader_relationships`
  - `test_interrupted_apply_can_abort_after_owner_edit`
  - `test_learner_edit_during_family_publication_is_not_lost`
  - `test_retire_from_a_stale_snapshot_keeps_family_membership`
  - `test_undo_conflicting_membership_is_not_overwritten`
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
- [tests/test_assessment_contracts.py](../../../../../../tests/test_assessment_contracts.py) — direct import
  - `test_contract_hash_changes_when_targets_change`
  - `test_snapshot_authoritative_after_live_rubric_change`
- [tests/test_assessment_enforcement.py](../../../../../../tests/test_assessment_enforcement.py) — direct import
  - `test_detect_contract_drift_and_doctor_surface`
- [tests/test_authoring_context.py](../../../../../../tests/test_authoring_context.py) — direct import
  - `test_authoring_context_includes_blueprint_facets_before_items_exist`
- [tests/test_canonical_exercise_serialization.py](../../../../../../tests/test_canonical_exercise_serialization.py) — direct import
  - `test_long_mapping_keys_are_written_readably`
  - `test_the_practice_item_detail_names_the_book_and_the_key_label`
- [tests/test_capability_residual.py](../../../../../../tests/test_capability_residual.py) — direct import
- [tests/test_causal_attribution_exhibit.py](../../../../../../tests/test_causal_attribution_exhibit.py) — direct import
- [tests/test_causal_factor_deferral.py](../../../../../../tests/test_causal_factor_deferral.py) — direct import
- [tests/test_causal_probe_commissioning.py](../../../../../../tests/test_causal_probe_commissioning.py) — direct import
- [tests/test_causal_shadow_selection.py](../../../../../../tests/test_causal_shadow_selection.py) — direct import
- [tests/test_certification_cold_probe.py](../../../../../../tests/test_certification_cold_probe.py) — direct import
  - `test_a_superseded_certificate_has_its_probe_cancelled_and_a_fresh_one_queued`
  - `test_probe_prefers_the_whole_task_item_that_covers_integration`
  - `test_shared_surface_group_makes_the_certificate_unmeasurable`
- [tests/test_characterization_assessment_exam.py](../../../../../../tests/test_characterization_assessment_exam.py) — direct import
  - `test_single_hash_moves_when_any_covered_component_changes`
- [tests/test_cli_attempt.py](../../../../../../tests/test_cli_attempt.py) — direct import
  - `test_cli_attempt_defaults_to_allowed_open_text_attempt_type`
- [tests/test_common_repair_delivery.py](../../../../../../tests/test_common_repair_delivery.py) — direct import
- [tests/test_concepts.py](../../../../../../tests/test_concepts.py) — direct import
  - `test_merge_concepts_rewrites_vault_references`
- [tests/test_conjunctive_instruments.py](../../../../../../tests/test_conjunctive_instruments.py) — direct import
- [tests/test_contract_commissioning.py](../../../../../../tests/test_contract_commissioning.py) — direct import
  - `test_authoring_at_the_contract_capability_makes_the_cell_reachable`
  - `test_max_los_truncates_by_queue_priority`
  - `test_unrubricked_item_is_not_scored_as_a_miss`
- [tests/test_contract_frontier_coverage.py](../../../../../../tests/test_contract_frontier_coverage.py) — direct import
- [tests/test_contract_reachability.py](../../../../../../tests/test_contract_reachability.py) — direct import
  - `test_recipe_duplicate_cells_collapse_to_one_obligation`
  - `test_retired_items_are_not_instruments`
  - `test_unrubricked_items_are_counted_not_silently_dropped`
- [tests/test_contrast_pairs.py](../../../../../../tests/test_contrast_pairs.py) — direct import
  - `test_the_doctor_catches_a_one_sided_pair_binding`
- [tests/test_coverage_denominator_boundary.py](../../../../../../tests/test_coverage_denominator_boundary.py) — direct import
  - `test_a_comment_or_timestamp_touch_does_not_change_the_version`
- [tests/test_coverage_on_extract.py](../../../../../../tests/test_coverage_on_extract.py) — direct import
  - `test_the_job_rejudges_covered_los_a_new_book_joins_and_a_fresh_state_pays_nothing`
- [tests/test_curriculum_c2b_past_papers.py](../../../../../../tests/test_curriculum_c2b_past_papers.py) — direct import
- [tests/test_curriculum_c3_codex_review.py](../../../../../../tests/test_curriculum_c3_codex_review.py) — direct import
  - `test_a_paused_second_subject_keeps_the_only_active_subject_s_past_papers`
- [tests/test_curriculum_locks.py](../../../../../../tests/test_curriculum_locks.py) — direct import
  - `test_a_facet_merge_is_legal_with_review`
  - `test_attempt_evidence_no_longer_locks_a_facet`
  - `test_deactivating_a_practised_learning_object_is_still_invalid`
  - `test_independent_surface_groups_and_mass_no_longer_lock_a_facet`
- [tests/test_daily_loop_golden_path_lifecycle.py](../../../../../../tests/test_daily_loop_golden_path_lifecycle.py) — direct import
- [tests/test_daily_loop_lo_lifecycle_serving.py](../../../../../../tests/test_daily_loop_lo_lifecycle_serving.py) — direct import
- [tests/test_daily_loop_reader_authored_practice.py](../../../../../../tests/test_daily_loop_reader_authored_practice.py) — direct import
  - `test_question_is_not_filed_under_a_put_away_lo`
- [tests/test_daily_loop_reference_adoption.py](../../../../../../tests/test_daily_loop_reference_adoption.py) — direct import
- [tests/test_daily_plan_owner_decisions.py](../../../../../../tests/test_daily_plan_owner_decisions.py) — direct import
- [tests/test_daily_plan_reentry.py](../../../../../../tests/test_daily_plan_reentry.py) — direct import
- [tests/test_daily_plan_review_regressions.py](../../../../../../tests/test_daily_plan_review_regressions.py) — direct import
- [tests/test_data_capture_a6_delayed_pick.py](../../../../../../tests/test_data_capture_a6_delayed_pick.py) — direct import
- [tests/test_deferred_regrade.py](../../../../../../tests/test_deferred_regrade.py) — direct import
  - `test_deferred_regrade_replays_targeted_error_attribution_facets`
- [tests/test_deliverable_codex_review.py](../../../../../../tests/test_deliverable_codex_review.py) — direct import
  - `test_f5_a_changed_statement_owes_coverage_again`
- [tests/test_diagnosis_input_provenance.py](../../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_f2_the_drafter_folds_a_generated_topic_only_under_the_name_it_was_shown`
  - `test_rereview_f2_the_drafter_checks_its_anchor_and_prerequisite_names`
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
  - `test_a_method_explicit_question_records_the_contract_it_was_presented_with`
- [tests/test_diagnostic_probe_single_use.py](../../../../../../tests/test_diagnostic_probe_single_use.py) — direct import
- [tests/test_discrimination_profiles.py](../../../../../../tests/test_discrimination_profiles.py) — direct import
- [tests/test_doctor.py](../../../../../../tests/test_doctor.py) — direct import
  - `test_doctor_does_not_merge_opposite_registered_facet_contracts`
  - `test_doctor_does_not_merge_unrelated_equal_length_facet_ids`
  - `test_doctor_fix_state_merges_registered_facet_alias_state`
  - `test_doctor_report_is_the_same_with_and_without_the_parse_cache`
  - `test_doctor_reports_reference_issues_and_json_cli`
  - `test_doctor_resolves_legacy_error_event_through_causal_taxonomy`
  - `test_doctor_surfaces_likely_facet_merge_candidates`
  - `test_doctor_validates_criterion_facet_maps`
  - `test_doctor_warns_on_duplicate_learning_objects`
  - `test_doctor_warns_on_unknown_yaml_key_that_looks_like_typo`
- [tests/test_error_hunt_items.py](../../../../../../tests/test_error_hunt_items.py) — direct import
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
- [tests/test_exam_protection_identity.py](../../../../../../tests/test_exam_protection_identity.py) — direct import
  - `test_a_scope_edited_outside_the_writer_names_no_reading`
- [tests/test_exam_protection_review.py](../../../../../../tests/test_exam_protection_review.py) — direct import
- [tests/test_exercise_authoring.py](../../../../../../tests/test_exercise_authoring.py) — direct import
- [tests/test_facet_authority.py](../../../../../../tests/test_facet_authority.py) — direct import
  - `test_a_library_save_listing_a_facet_twice_is_refused_and_writes_nothing`
  - `test_an_ingest_consolidation_keeps_exam_only_meaning_out_and_its_undo_cannot_mint_it`
  - `test_the_registry_writer_refuses_exam_only_meaning_whatever_the_caller_declares`
- [tests/test_facet_authority_rereview.py](../../../../../../tests/test_facet_authority_rereview.py) — direct import
  - `test_a_save_that_fails_in_process_settles_its_intent`
  - `test_a_save_that_lands_records_a_settled_intent`
  - `test_doctor_reports_and_settles_an_interrupted_save_with_no_reword`
  - `test_recovery_keeps_the_verdict_of_a_save_killed_after_its_write`
  - `test_recovery_withdraws_the_verdict_of_a_save_killed_before_its_write`
- [tests/test_facet_authority_review.py](../../../../../../tests/test_facet_authority_review.py) — direct import
  - `test_a_library_save_that_never_lands_withdraws_its_authority_verdicts`
  - `test_every_library_change_to_a_facets_meaning_records_the_owners_authority_verdict`
  - `test_recovery_settles_an_undo_intent_the_authority_rule_refuses`
  - `test_recovery_withdraws_the_verdicts_of_a_library_save_killed_before_its_write`
  - `test_the_registry_writer_refuses_an_owner_edit_with_no_audit_record`
- [tests/test_facet_identity.py](../../../../../../tests/test_facet_identity.py) — direct import
  - `test_dedupe_regression_set_merges_the_agreed_pairs_and_keeps_the_distinct_ones`
  - `test_in_run_consolidation_of_the_regression_set`
- [tests/test_facet_identity_actions.py](../../../../../../tests/test_facet_identity_actions.py) — direct import
  - `test_a_facet_that_used_to_be_locked_merges_and_undoes_exactly`
  - `test_a_merge_intent_whose_file_changed_meanwhile_is_withdrawn`
  - `test_a_merge_rekeys_evidence_and_undo_restores_facets_and_evidence_exactly`
  - `test_an_interrupted_undo_is_finished_by_a_retry`
  - `test_dedupe_applies_a_set_whose_facets_carry_evidence`
  - `test_dedupe_reports_a_held_back_retiree_as_refused`
- [tests/test_facet_identity_composition.py](../../../../../../tests/test_facet_identity_composition.py) — direct import
  - `test_the_ledger_records_merged_pairs_and_shortlisted_different_pairs_only`
- [tests/test_facet_identity_ingest.py](../../../../../../tests/test_facet_identity_ingest.py) — direct import
  - `test_a_duplicate_candidate_is_merged_before_the_gates_and_undo_re_mints_it`
- [tests/test_facet_mint_gate.py](../../../../../../tests/test_facet_mint_gate.py) — direct import
  - `test_ingest_aliases_a_collapsing_candidate_into_a_registered_facet`
- [tests/test_facet_registry_v2.py](../../../../../../tests/test_facet_registry_v2.py) — direct import
  - `test_upsert_facet_promotes_v1_registry_to_v2`
- [tests/test_facet_reword_confirm.py](../../../../../../tests/test_facet_reword_confirm.py) — direct import
  - `test_the_library_stays_the_owners_override_for_exam_wording`
  - `test_the_registry_writer_refuses_exam_only_meaning_and_an_unconfirmed_reword`
- [tests/test_facet_reword_paths.py](../../../../../../tests/test_facet_reword_paths.py) — direct import
  - `test_a_library_edit_that_rewords_an_evidenced_facet_records_a_version_with_undo`
  - `test_an_append_facet_restructure_applies_as_a_facet_version_with_undo`
- [tests/test_facet_rewords.py](../../../../../../tests/test_facet_rewords.py) — direct import
- [tests/test_followup_next_matrix.py](../../../../../../tests/test_followup_next_matrix.py) — direct import
- [tests/test_followup_reserved_only.py](../../../../../../tests/test_followup_reserved_only.py) — direct import
  - `test_reserved_questions_and_what_quotes_them_stay_out_of_the_authors_context`
  - `test_wording_an_ordinary_item_already_shows_is_no_match`
- [tests/test_forecast_receipts.py](../../../../../../tests/test_forecast_receipts.py) — direct import
- [tests/test_goal_certification_any_of.py](../../../../../../tests/test_goal_certification_any_of.py) — direct import
- [tests/test_goal_frontier.py](../../../../../../tests/test_goal_frontier.py) — direct import
  - `test_no_active_goals_means_no_goal_frontier`
- [tests/test_goal_projection.py](../../../../../../tests/test_goal_projection.py) — direct import
  - `test_explicit_facet_scope_adds_facet_without_listing_concept`
  - `test_legacy_v1_goal_converts_and_scope_resolves`
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — direct import
- [tests/test_grading_context.py](../../../../../../tests/test_grading_context.py) — direct import
  - `test_grading_context_uses_default_rubric_when_inline_rubric_is_omitted`
  - `test_legacy_evidence_coverage_wrapper_is_score_independent`
- [tests/test_grading_support.py](../../../../../../tests/test_grading_support.py) — direct import
  - `test_an_unverified_multi_target_criterion_opens_no_unresolved_cause_factor`
- [tests/test_graph_correction.py](../../../../../../tests/test_graph_correction.py) — direct import
- [tests/test_graph_edit_proposals.py](../../../../../../tests/test_graph_edit_proposals.py) — direct import
  - `test_queue_restructure_request_needs_no_lock`
- [tests/test_hint_authored_reveal_ruling.py](../../../../../../tests/test_hint_authored_reveal_ruling.py) — direct import
- [tests/test_hint_evidence.py](../../../../../../tests/test_hint_evidence.py) — direct import
- [tests/test_hint_telemetry.py](../../../../../../tests/test_hint_telemetry.py) — direct import
  - `test_unaided_progress_is_reached_only_when_the_uncapped_records_show_no_other_help`
- [tests/test_identifiability_doctor.py](../../../../../../tests/test_identifiability_doctor.py) — direct import
- [tests/test_import_split_parity.py](../../../../../../tests/test_import_split_parity.py) — direct import
- [tests/test_inference_precheck.py](../../../../../../tests/test_inference_precheck.py) — direct import
  - `test_b3_requires_a_directly_reachable_downstream_anchor`
  - `test_declared_prerequisite_without_a_graph_edge_is_reported_missing`
- [tests/test_init.py](../../../../../../tests/test_init.py) — direct import
  - `test_bootstrap_seeds_subject_and_starting_level`
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_the_certification_cold_probe_selects_an_instrument_as_its_held_out_item`
- [tests/test_integration_backfill.py](../../../../../../tests/test_integration_backfill.py) — direct import
  - `test_apply_writes_a_drop_as_an_explicit_null`
  - `test_coordination_becomes_keepable_once_an_instrument_observes_it`
- [tests/test_integration_daily_loop_field.py](../../../../../../tests/test_integration_daily_loop_field.py) — direct import
  - `test_adopted_reader_card_is_untested_on_the_map_with_no_outcome_row`
- [tests/test_intent_codex_rereview.py](../../../../../../tests/test_intent_codex_rereview.py) — direct import
- [tests/test_intent_codex_review.py](../../../../../../tests/test_intent_codex_review.py) — direct import
- [tests/test_intent_fix_round4.py](../../../../../../tests/test_intent_fix_round4.py) — direct import
- [tests/test_intent_fix_round6.py](../../../../../../tests/test_intent_fix_round6.py) — direct import
  - `test_f19_dl1_pair_plans_are_otherwise_unchanged`
- [tests/test_intent_orchestrator_rulings.py](../../../../../../tests/test_intent_orchestrator_rulings.py) — direct import
- [tests/test_intent_plan.py](../../../../../../tests/test_intent_plan.py) — direct import
- [tests/test_km1_doctor.py](../../../../../../tests/test_km1_doctor.py) — direct import
  - `test_blueprint_invalid_capability_rejected`
  - `test_criterion_dependency_cycle_rejected`
  - `test_valid_blueprint_and_criterion_targets_pass`
- [tests/test_km2_activation.py](../../../../../../tests/test_km2_activation.py) — direct import
  - `test_validate_readiness_flags_incomplete_contract`
- [tests/test_km2_write_path.py](../../../../../../tests/test_km2_write_path.py) — direct import
  - `test_rebuild_uses_presented_contract_after_live_target_change`
- [tests/test_km3_projections.py](../../../../../../tests/test_km3_projections.py) — direct import
- [tests/test_km5_sim_gates.py](../../../../../../tests/test_km5_sim_gates.py) — direct import
  - `test_shadow_intent_logs_practice_integration_at_the_right_moment`
- [tests/test_laddered_stems.py](../../../../../../tests/test_laddered_stems.py) — direct import
- [tests/test_large_practice_flow.py](../../../../../../tests/test_large_practice_flow.py) — direct import
  - `test_many_open_text_practice_items_schedule_and_record_attempt`
- [tests/test_learner_data_relax_2.py](../../../../../../tests/test_learner_data_relax_2.py) — direct import
- [tests/test_mcp_c1a_review.py](../../../../../../tests/test_mcp_c1a_review.py) — direct import
  - `test_a_check_reserved_while_passages_are_retrieved_withholds_them`
  - `test_an_unpinned_answer_shows_no_text_even_when_no_key_change_is_recorded`
- [tests/test_mcp_runtime.py](../../../../../../tests/test_mcp_runtime.py) — direct import
  - `test_the_loaded_vault_follows_its_files`
- [tests/test_method_phrasing_report.py](../../../../../../tests/test_method_phrasing_report.py) — direct import
- [tests/test_minimal_repair_selection_a1.py](../../../../../../tests/test_minimal_repair_selection_a1.py) — direct import
- [tests/test_model_grade_lane.py](../../../../../../tests/test_model_grade_lane.py) — direct import
- [tests/test_persona_gate.py](../../../../../../tests/test_persona_gate.py) — direct import
- [tests/test_pf_generation.py](../../../../../../tests/test_pf_generation.py) — direct import
  - `test_a_published_variant_of_a_textbook_exercise_keeps_its_own_verification`
- [tests/test_pfc_unassessed_readers.py](../../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_a_criterion_without_targets_shares_its_facets_with_the_assessed_one`
- [tests/test_pfc_unverified_unassessed.py](../../../../../../tests/test_pfc_unverified_unassessed.py) — direct import
- [tests/test_placement_diagnosis_decides.py](../../../../../../tests/test_placement_diagnosis_decides.py) — direct import
- [tests/test_placement_opening_probes.py](../../../../../../tests/test_placement_opening_probes.py) — direct import
- [tests/test_plan_determinism.py](../../../../../../tests/test_plan_determinism.py) — direct import
- [tests/test_plan_determinism_landing.py](../../../../../../tests/test_plan_determinism_landing.py) — direct import
- [tests/test_practice_index_admission.py](../../../../../../tests/test_practice_index_admission.py) — direct import
  - `test_parked_learning_objects_are_excluded`
  - `test_shared_rules_exclude_exactly_what_the_scheduler_drops`
- [tests/test_practice_index_dossiers.py](../../../../../../tests/test_practice_index_dossiers.py) — direct import
  - `test_grounding_excludes_answers_diagnostic_surfaces_and_exam_reserves`
  - `test_regenerated_only_when_the_facet_or_its_sources_change`
  - `test_reverting_sources_selects_the_matching_earlier_dossier`
- [tests/test_practice_index_find.py](../../../../../../tests/test_practice_index_find.py) — direct import
  - `test_changed_index_content_voids_an_earlier_evaluation_approval`
- [tests/test_probability_prep.py](../../../../../../tests/test_probability_prep.py) — direct import
  - `test_only_target_overlap_is_evidence_and_other_same_lo_work_is_context`
- [tests/test_probe_targeting.py](../../../../../../tests/test_probe_targeting.py) — direct import
- [tests/test_projection_evidence_polarity.py](../../../../../../tests/test_projection_evidence_polarity.py) — direct import
  - `test_p0_timeline_matches_banked_ledger_including_a6_supporting_credit`
- [tests/test_proposal_persistence.py](../../../../../../tests/test_proposal_persistence.py) — direct import
  - `test_registry_backed_vault_rejects_unknown_evidence_facet`
- [tests/test_reader_ca1_as_printed.py](../../../../../../tests/test_reader_ca1_as_printed.py) — direct import
  - `test_the_report_resolves_when_the_wording_changes_and_holds_until_then`
- [tests/test_reader_ca1_astra_fixes.py](../../../../../../tests/test_reader_ca1_astra_fixes.py) — direct import
  - `test_a_canonical_exercise_never_crops_a_solution_block_it_names`
  - `test_an_empty_exercise_label_is_no_label`
  - `test_the_canonical_exercise_dto_names_the_book_by_its_learner_title`
- [tests/test_reader_ca1_astra_redesign.py](../../../../../../tests/test_reader_ca1_astra_redesign.py) — direct import
  - `test_a_canonical_exercise_never_shows_a_figure_its_import_refused`
  - `test_f3_up_to_moved_spaces_too`
- [tests/test_reader_ca1_astra_rereview.py](../../../../../../tests/test_reader_ca1_astra_rereview.py) — direct import
- [tests/test_reader_ca1_codex_review.py](../../../../../../tests/test_reader_ca1_codex_review.py) — direct import
  - `test_a_page_known_without_a_box_offers_the_original_page_and_no_substitute_crop`
  - `test_a_reworded_card_resolves_but_a_report_on_the_new_wording_meanwhile_is_kept`
  - `test_a_split_written_before_ownership_was_kept_withholds_the_free_crop`
  - `test_an_ai_proposal_over_the_same_blocks_is_not_the_book_s_problem`
- [tests/test_reader_ca1_unicode_containment.py](../../../../../../tests/test_reader_ca1_unicode_containment.py) — direct import
  - `test_a_statement_reaching_past_what_prints_gives_no_free_crop`
  - `test_a_verbatim_import_of_unicode_math_gets_its_free_crop`
- [tests/test_reader_ca5_also_in_books.py](../../../../../../tests/test_reader_ca5_also_in_books.py) — direct import
- [tests/test_reader_ca5_landing.py](../../../../../../tests/test_reader_ca5_landing.py) — direct import
- [tests/test_reader_progression.py](../../../../../../tests/test_reader_progression.py) — direct import
  - `test_practice_plan_uses_blueprint_facets_before_first_item`
- [tests/test_reader_recap_review.py](../../../../../../tests/test_reader_recap_review.py) — direct import
- [tests/test_reader_recap_review_r2.py](../../../../../../tests/test_reader_recap_review_r2.py) — direct import
- [tests/test_reader_recap_review_r3.py](../../../../../../tests/test_reader_recap_review_r3.py) — direct import
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
- [tests/test_reader_workbench_rw2a.py](../../../../../../tests/test_reader_workbench_rw2a.py) — direct import
  - `test_final_f2_carried_hints_still_count_after_the_items_authored_hints_were_removed`
- [tests/test_reading_paths.py](../../../../../../tests/test_reading_paths.py) — direct import
- [tests/test_rebuild_equivalence_review.py](../../../../../../tests/test_rebuild_equivalence_review.py) — direct import
- [tests/test_recall_coverage_interventions.py](../../../../../../tests/test_recall_coverage_interventions.py) — direct import
  - `test_error_attribution_target_facets_are_canonicalized_before_facet_outcomes`
  - `test_error_attribution_targets_unmapped_facet_before_whole_item_fallback`
  - `test_facet_aliases_are_canonicalized_before_recall_updates`
  - `test_intervention_need_targets_failed_facet_not_whole_item`
  - `test_intervention_needs_canonicalize_target_facets_for_dedup`
  - `test_rubric_criterion_names_infer_targeted_facet_outcomes`
  - `test_second_same_facet_failure_counts_across_different_items`
  - `test_zero_score_independent_attempt_uses_rubric_coverage_and_confidence_as_reliability`
- [tests/test_replay.py](../../../../../../tests/test_replay.py) — direct import
  - `test_replay_preserves_targeted_error_attribution_facets`
- [tests/test_required_method_items.py](../../../../../../tests/test_required_method_items.py) — direct import
- [tests/test_reread_safety_landing.py](../../../../../../tests/test_reread_safety_landing.py) — direct import
- [tests/test_ro0_codex_review.py](../../../../../../tests/test_ro0_codex_review.py) — direct import
- [tests/test_ro0_report.py](../../../../../../tests/test_ro0_report.py) — direct import
  - `test_each_row_reports_what_was_written_and_measured_bytes`
- [tests/test_ro0_row11_goal_lifecycle.py](../../../../../../tests/test_ro0_row11_goal_lifecycle.py) — direct import
- [tests/test_ro2_ad_document_ir.py](../../../../../../tests/test_ro2_ad_document_ir.py) — direct import
- [tests/test_ro4_goals.py](../../../../../../tests/test_ro4_goals.py) — direct import
- [tests/test_router_probe_ties.py](../../../../../../tests/test_router_probe_ties.py) — direct import
- [tests/test_router_r1_composition.py](../../../../../../tests/test_router_r1_composition.py) — direct import
- [tests/test_router_r2a_landing.py](../../../../../../tests/test_router_r2a_landing.py) — direct import
- [tests/test_scheduler.py](../../../../../../tests/test_scheduler.py) — direct import
  - `test_scheduler_orders_eligible_items_by_selection_reward_before_id`
  - `test_scheduler_persists_bounded_reward_debug_and_rejected_candidates`
  - `test_scheduler_preserves_draw_diagnostics_without_claiming_final_propensity`
  - `test_scheduler_scores_due_goal_item`
  - `test_scheduler_selects_item_on_weak_canonical_facet_boundary`
- [tests/test_scheduler_golden.py](../../../../../../tests/test_scheduler_golden.py) — direct import
  - `test_scheduler_forgetting_risk_zero_before_due_date`
  - `test_scheduler_goal_frontier_follows_explicit_scope_only`
  - `test_scheduler_recent_error_decays_by_exp_days_over_seven`
- [tests/test_scheduler_probe_eig.py](../../../../../../tests/test_scheduler_probe_eig.py) — direct import
  - `test_short_session_keeps_probe_eig_when_probe_is_only_reason`
- [tests/test_scheduler_requested_floor.py](../../../../../../tests/test_scheduler_requested_floor.py) — direct import
- [tests/test_scoreboard.py](../../../../../../tests/test_scoreboard.py) — direct import
- [tests/test_secondary_attach.py](../../../../../../tests/test_secondary_attach.py) — direct import
  - `test_fingerprint_covers_every_file_the_loader_reads`
  - `test_retargeting_a_directory_link_between_two_fingerprinted_directories_reloads`
  - `test_retargeting_a_file_link_to_a_same_sized_file_changes_the_fingerprint`
- [tests/test_section_coverage.py](../../../../../../tests/test_section_coverage.py) — direct import
  - `test_a_changed_statement_makes_old_rows_stale_until_rejudged`
- [tests/test_section_coverage_review.py](../../../../../../tests/test_section_coverage_review.py) — direct import
  - `test_f4_returning_to_a_judged_state_reads_its_rows_again`
- [tests/test_self_attributed_misconceptions.py](../../../../../../tests/test_self_attributed_misconceptions.py) — direct import
- [tests/test_self_grade.py](../../../../../../tests/test_self_grade.py) — direct import
  - `test_dont_know_allowed_when_not_in_attempt_types`
  - `test_self_grade_uses_criterion_total_as_item_scale`
  - `test_self_grade_uses_default_rubric_when_inline_rubric_is_omitted`
- [tests/test_show.py](../../../../../../tests/test_show.py) — direct import
  - `test_show_adds_imported_source_name_without_replacing_ref_id`
- [tests/test_sidecar_item_presentation.py](../../../../../../tests/test_sidecar_item_presentation.py) — direct import
  - `test_rubric_criteria_expose_their_authored_targets_and_dependencies`
- [tests/test_sidecar_trace_and_clarification.py](../../../../../../tests/test_sidecar_trace_and_clarification.py) — direct import
- [tests/test_sim_teach_back.py](../../../../../../tests/test_sim_teach_back.py) — direct import
- [tests/test_simulation.py](../../../../../../tests/test_simulation.py) — direct import
- [tests/test_source_ingestion_v2lite.py](../../../../../../tests/test_source_ingestion_v2lite.py) — direct import
- [tests/test_source_retrieval_rereview.py](../../../../../../tests/test_source_retrieval_rereview.py) — direct import
  - `test_an_items_yaml_source_ref_is_excluded_without_a_link_row`
- [tests/test_source_set_synthesis.py](../../../../../../tests/test_source_set_synthesis.py) — direct import
  - `test_a_vault_whose_facets_used_to_be_locked_still_bootstraps`
- [tests/test_state_sync.py](../../../../../../tests/test_state_sync.py) — direct import
  - `test_state_sync_enters_probe_for_new_active_learning_object_without_goal`
  - `test_state_sync_enters_probe_when_practice_item_arrives_after_learning_object`
- [tests/test_state_sync_scheduling_race.py](../../../../../../tests/test_state_sync_scheduling_race.py) — direct import
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — direct import
- [tests/test_synthesis_criterion_dependencies.py](../../../../../../tests/test_synthesis_criterion_dependencies.py) — direct import
  - `test_doctor_fix_content_cli_reports_self_dependencies_it_leaves`
  - `test_fix_content_keeps_a_self_dependency_because_removing_it_changes_failure_attribution`
  - `test_fix_content_removes_invalid_entries_and_keeps_the_rest_of_the_file`
- [tests/test_synthesis_manifests.py](../../../../../../tests/test_synthesis_manifests.py) — direct import
  - `test_curriculum_change_changes_manifest_hash`
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_ensure_teach_back_item_authors_from_exact_source_and_active_quest`
- [tests/test_teacher_exam_question_guard.py](../../../../../../tests/test_teacher_exam_question_guard.py) — direct import
  - `test_a_short_reserved_question_counts_when_an_ordinary_item_shows_its_number`
- [tests/test_teacher_te1_review_fixes.py](../../../../../../tests/test_teacher_te1_review_fixes.py) — direct import
- [tests/test_teacher_te1b_review_fixes.py](../../../../../../tests/test_teacher_te1b_review_fixes.py) — direct import
- [tests/test_teacher_te1b_suggestions.py](../../../../../../tests/test_teacher_te1b_suggestions.py) — direct import
  - `test_the_outcome_is_r_cold_on_the_drawn_lo_shown_or_not`
- [tests/test_teacher_te2log_episodes.py](../../../../../../tests/test_teacher_te2log_episodes.py) — direct import
- [tests/test_ux_phase1_usability_round1.py](../../../../../../tests/test_ux_phase1_usability_round1.py) — direct import
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
- [tests/test_vault_writer.py](../../../../../../tests/test_vault_writer.py) — direct import
  - `test_writer_preserves_unknown_keys_and_timestamps`
- [tests/test_voi_forecasts.py](../../../../../../tests/test_voi_forecasts.py) — direct import
- [tests/test_voi_stopping.py](../../../../../../tests/test_voi_stopping.py) — direct import
- [tests/test_voi_v2.py](../../../../../../tests/test_voi_v2.py) — direct import
- [tests/test_yaml_fast_read.py](../../../../../../tests/test_yaml_fast_read.py) — direct import
  - `test_fast_frontmatter_read_matches_round_trip_read`
  - `test_fast_read_matches_round_trip_read_for_edge_cases`
  - `test_fast_read_matches_round_trip_read_for_fixture_yaml`
  - `test_fast_read_returns_plain_python_containers`
  - `test_libyaml_and_pure_python_safe_loaders_agree_on_fixture_yaml`

## Modification guidance

- Make changes here when the responsibility remains yaml io within learnloop.vault; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/vault/yaml_io.py](../../../../../../src/learnloop/vault/yaml_io.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
