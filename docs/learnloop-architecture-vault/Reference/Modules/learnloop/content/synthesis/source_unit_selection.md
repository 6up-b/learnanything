---
title: "learnloop.content.synthesis.source_unit_selection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/source_unit_selection.py"
source_paths:
  - "src/learnloop/content/synthesis/source_unit_selection.py"
source_commit: "542adc8869b3c2d17c359f79a489c4b4b8519192"
source_commit_timestamp: "2026-10-15T06:29:40-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.synthesis"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.synthesis.source_unit_selection module"
  - "src/learnloop/content/synthesis/source_unit_selection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.source_unit_selection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.source_unit_selection` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Unit selection persistence with re-anchoring (spec_source_ingestion_v2 §5.3).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/source_unit_selection.py](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py) |
| Source lines | 566 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `542adc8869b3c2d17c359f79a489c4b4b8519192` |
| Commit timestamp | `2026-10-15T06:29:40-04:00` |

## Public API

- `class SelectionValidationError(ValueError)` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 38) — A selection or boundary override references units/spans that don't exist.
- `class ReanchoredSelection` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 43)
- `normalize_overrides(boundary_overrides: list[dict] | None) -> list[dict]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 57) — Normalize free-form override dicts to canonical snake_case keys.
- `compute_effective_units(ir: DocumentIR, boundary_overrides: list[dict] | None) -> list[dict]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 218) — The *effective* unit shape after boundary overrides (see :func:`_effective_units_with_spans`).
- `effective_unit_spans(ir: DocumentIR, boundary_overrides: list[dict] | None) -> dict[str, tuple[str, ...]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 224) — ``{effective unit id: the span ids it holds}``, from the same walk as :func:`compute_effective_units`.
- `effective_scope_groups(ir: DocumentIR, boundary_overrides: list[dict] | None, selected_unit_ids: list[str], *, role_by_unit: Mapping[str, str] | None=None, default_role: str='reference') -> list[dict]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 238) — Project a selected scope through the canonical effective-unit shape.
- `validate_unit_selection(ir: DocumentIR, selected_unit_ids: list[str], boundary_overrides: list[dict] | None=None) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 310) — App-level validation of a selection against its extraction's IR.
- `default_exam_use_modes(unit_ids: list[str], *, held_out_fraction: float=DEFAULT_HELD_OUT_FRACTION) -> dict[str, str]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 345) — Deterministic default: the first ``held_out_fraction`` of units (by sorted id) are held-out evaluation, the rest blueprint_only (§4.2).
- `save_unit_selection(repo: Repository, extraction_id: str, selected_unit_ids: list[str], *, boundary_overrides: list[dict] | None=None, exam_use_modes: dict[str, str] | None=None, exam_paper_metadata: dict | None=None, role_override: str | None=None, clock: Clock | None=None) -> dict` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 355) — Validate and persist a selection for one extraction run.
- `reanchor_units(from_ir: DocumentIR, to_ir: DocumentIR) -> dict[str, str | None]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 430) — Map each old unit id onto a new unit id (or ``None`` when unresolved).
- `reanchor_selection(from_ir: DocumentIR, to_ir: DocumentIR, selected_unit_ids: list[str], boundary_overrides: list[dict] | None=None) -> ReanchoredSelection` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 482) — Re-anchor a stored selection + overrides onto a fresh extraction (§5.3).
- `reanchor_selection_to(repo: Repository, from_extraction_id: str, to_extraction_id: str, *, clock: Clock | None=None) -> dict` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 511) — Re-anchor the stored selection of ``from`` onto ``to`` and persist it.

### Module constants

- `MERGE_WITH_NEXT` ([src/learnloop/content/synthesis/source_unit_selection.py](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 33)
- `SPLIT_AT_HEADING` ([src/learnloop/content/synthesis/source_unit_selection.py](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 34)
- `_OVERRIDE_OPS` ([src/learnloop/content/synthesis/source_unit_selection.py](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 35)
- `EXAM_USE_MODES` ([src/learnloop/content/synthesis/source_unit_selection.py](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 339)
- `DEFAULT_EXAM_USE_MODE` ([src/learnloop/content/synthesis/source_unit_selection.py](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 341)
- `DEFAULT_HELD_OUT_FRACTION` ([src/learnloop/content/synthesis/source_unit_selection.py](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 342)

## Internal implementation anchors

- `_override_unit_id(override: dict) -> str | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 49)
- `_override_at_span(override: dict) -> str | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 53)
- `_override_op_by_unit(boundary_overrides: list[dict] | None) -> dict[str, str]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 74) — Map unit_id → op for the recognized boundary-override operations.
- `_approx_tokens(blocks: list) -> int` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 86)
- `_effective_units_with_spans(ir: DocumentIR, boundary_overrides: list[dict] | None) -> list[tuple[dict, list[str]]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 90) — Deterministically compute the *effective* unit shape after boundary overrides.
- `_span_majority_unit(unit, span_result, to_unit_of_span) -> str | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 464)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `SelectionValidationError`, `save_unit_selection`; statically calls `save_unit_selection`
- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `effective_unit_spans`; statically calls `effective_unit_spans`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `effective_scope_groups`; statically calls `effective_scope_groups`
- [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]] — imports `reanchor_units`; statically calls `reanchor_units`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `effective_unit_spans`; statically calls `effective_unit_spans`
- [[Reference/Modules/learnloop/content/synthesis/source_coverage|learnloop.content.synthesis.source_coverage]] — imports `effective_scope_groups`; statically calls `effective_scope_groups`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `compute_effective_units`, `effective_scope_groups`; statically calls `compute_effective_units`, `effective_scope_groups`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `compute_effective_units`; statically calls `compute_effective_units`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `SelectionValidationError`, `compute_effective_units`, `save_unit_selection`; statically calls `compute_effective_units`, `save_unit_selection`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `HELD_OUT_EVALUATION`, `MARKS_MADE_ON_KEY`, `PROTECTION_MARK_KEY`, `marks_made_on`; calls `marks_made_on`
- [[Reference/Modules/learnloop/content/sources/role_authority|learnloop.content.sources.role_authority]] — imports `KNOWN_ROLES`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `DocumentIR`
- [[Reference/Modules/learnloop/ingest/reanchor|learnloop.ingest.reanchor]] — imports `reanchor_spans`; calls `reanchor_spans`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]], [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/exam_scope_fixtures.py](../../../../../../../tests/exam_scope_fixtures.py) — direct import
- [tests/section_coverage_fixtures.py](../../../../../../../tests/section_coverage_fixtures.py) — direct import
- [tests/test_ad1_codex_review_fixes.py](../../../../../../../tests/test_ad1_codex_review_fixes.py) — direct import
- [tests/test_ad3_relatedness.py](../../../../../../../tests/test_ad3_relatedness.py) — direct import
  - `test_relatedness_proposal_reads_no_learner_or_held_out_data`
- [tests/test_ad_protected_readings.py](../../../../../../../tests/test_ad_protected_readings.py) — direct import
  - `test_marking_and_release_flip_the_epoch_and_the_reading_with_it`
- [tests/test_adaptive_difficulty_ad1.py](../../../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
  - `test_held_out_sentinel_never_reaches_ad_inputs`
- [tests/test_compare_sources_keep.py](../../../../../../../tests/test_compare_sources_keep.py) — direct import
- [tests/test_curriculum_c2b_past_papers.py](../../../../../../../tests/test_curriculum_c2b_past_papers.py) — direct import
  - `test_a_group_held_out_meanwhile_refuses_the_request`
- [tests/test_curriculum_c3_codex_review.py](../../../../../../../tests/test_curriculum_c3_codex_review.py) — direct import
  - `test_a_change_that_leaves_the_sent_ids_practice_available_publishes`
- [tests/test_curriculum_c3_exam_scoping.py](../../../../../../../tests/test_curriculum_c3_exam_scoping.py) — direct import
  - `test_past_papers_contribute_their_lo_ids_only_and_held_out_units_nothing`
  - `test_the_role_is_set_through_the_existing_role_surfaces`
- [tests/test_e0_corpus.py](../../../../../../../tests/test_e0_corpus.py) — direct import
  - `test_a_later_held_out_mark_invalidates_dependent_artifacts`
- [tests/test_effective_units.py](../../../../../../../tests/test_effective_units.py) — direct import
  - `test_merge_chain_fuses_three_units`
  - `test_passthrough_no_overrides`
  - `test_split_no_op_without_level2_headings`
  - `test_split_with_intro_blocks`
- [tests/test_exam_protection.py](../../../../../../../tests/test_exam_protection.py) — direct import
  - `test_a_held_out_textbook_unit_never_feeds_synthesis_as_teaching`
  - `test_a_held_out_unit_of_any_role_joins_the_leakage_inventory`
  - `test_a_reader_import_of_held_out_material_is_refused_before_any_model_call`
  - `test_a_reader_question_about_held_out_material_is_refused_before_anything_is_sent`
  - `test_an_import_rechecks_a_stale_proposal_before_any_paid_call`
  - `test_an_item_made_from_held_out_material_is_exam_material`
  - `test_an_unresolvable_held_out_mark_fingerprints_its_whole_extraction`
  - `test_held_out_and_exam_role_picks_count_outside_any_source_set`
- [tests/test_exam_protection_identity.py](../../../../../../../tests/test_exam_protection_identity.py) — direct import
  - `test_f15_the_plans_reading_step_never_offers_held_out_material_in_either_order`
- [tests/test_exam_protection_landing.py](../../../../../../../tests/test_exam_protection_landing.py) — direct import
  - `test_a_book_picked_as_an_exam_in_its_outline_builds_nothing`
  - `test_the_reading_step_never_offers_a_held_out_section_of_a_book_in_no_source_set`
- [tests/test_exam_protection_review.py](../../../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_a_pick_of_an_item_marked_held_out_since_its_proposal_is_refused`
  - `test_a_second_extraction_marked_by_the_owner_is_held_by_its_own_marks_only`
  - `test_an_unresolvable_mark_withholds_every_extraction_of_its_source`
  - `test_held_out_marks_in_two_extractions_each_hold_their_own_extraction_exactly`
  - `test_pf_never_forwards_a_held_out_parent_quote`
  - `test_the_same_unit_marked_in_two_extractions_withholds_only_that_unit`
  - `test_the_switch_never_reaches_what_a_model_is_shown`
- [tests/test_facet_authority_review.py](../../../../../../../tests/test_facet_authority_review.py) — direct import
  - `test_an_undo_never_mints_a_candidate_whose_recorded_citations_no_longer_resolve`
- [tests/test_facet_locks_landing.py](../../../../../../../tests/test_facet_locks_landing.py) — direct import
- [tests/test_facet_reword_confirm.py](../../../../../../../tests/test_facet_reword_confirm.py) — direct import
  - `test_a_held_out_evaluation_unit_is_exam_material_whatever_its_members_role`
- [tests/test_facet_reword_confirm_review.py](../../../../../../../tests/test_facet_reword_confirm_review.py) — direct import
  - `test_a_pending_confirm_hides_a_sources_text_once_its_unit_is_held_out`
- [tests/test_ingest_m3.py](../../../../../../../tests/test_ingest_m3.py) — direct import
  - `test_boundary_override_camelcase_keys_are_normalized`
  - `test_reanchor_flags_unresolved_units_for_review`
  - `test_selection_survives_reextraction_via_reanchor`
  - `test_unit_selection_persists_and_validates`
- [tests/test_inventory_merge_parallel.py](../../../../../../../tests/test_inventory_merge_parallel.py) — direct import
  - `test_exam_role_merge_group_does_not_fold`
  - `test_merged_inventory_marker_covers_member_units`
  - `test_merged_units_inventory_as_one_call_and_cache_composite`
  - `test_mixed_role_merge_group_does_not_fold`
  - `test_synthesis_gather_folds_merged_group_once_with_member_fallback`
- [tests/test_label_roles_cli.py](../../../../../../../tests/test_label_roles_cli.py) — direct import
  - `test_held_out_and_exam_material_never_reach_the_labeller`
- [tests/test_library_exercises.py](../../../../../../../tests/test_library_exercises.py) — direct import
  - `test_r4_a_problem_opened_before_its_region_was_held_out_is_not_shown_again`
  - `test_r4_verify_f7_an_exercise_held_out_after_its_card_was_shown_is_never_read_or_opened`
  - `test_the_held_out_sentinel_is_never_offered_by_the_view_the_arm_or_the_fallback`
- [tests/test_plan_follows_path.py](../../../../../../../tests/test_plan_follows_path.py) — direct import
  - `test_the_path_never_opens_a_held_out_section_even_where_dl1s_exact_selection_would`
- [tests/test_reader_cues.py](../../../../../../../tests/test_reader_cues.py) — direct import
  - `test_a_cue_on_held_out_material_cannot_be_tapped`
  - `test_a_held_out_section_never_carries_a_cue_though_the_rail_still_lists_it`
- [tests/test_reader_rw3b_protection.py](../../../../../../../tests/test_reader_rw3b_protection.py) — direct import
- [tests/test_reader_rw5d_p4a_figures_follow.py](../../../../../../../tests/test_reader_rw5d_p4a_figures_follow.py) — direct import
  - `test_protection_is_read_again_on_both_sides`
- [tests/test_reader_tutor_retrieval.py](../../../../../../../tests/test_reader_tutor_retrieval.py) — direct import
  - `test_a_held_out_sentinel_never_reaches_the_tutor_the_verifier_or_the_excerpt`
- [tests/test_reading_hardening_landing.py](../../../../../../../tests/test_reading_hardening_landing.py) — direct import
- [tests/test_reading_paths.py](../../../../../../../tests/test_reading_paths.py) — direct import
  - `test_a_held_out_section_is_never_sent_and_a_stored_one_withheld_later_is_not_shown`
  - `test_fix_a_cached_reason_quoting_a_section_held_out_since_is_never_shown`
- [tests/test_reread_safety.py](../../../../../../../tests/test_reread_safety.py) — direct import
  - `test_redesign_a_study_map_save_keeps_the_owners_marks`
- [tests/test_ro2_history_protection.py](../../../../../../../tests/test_ro2_history_protection.py) — direct import
  - `test_a_gap_whose_source_is_marked_held_out_after_it_was_named_is_withheld`
  - `test_content_held_out_after_the_serve_is_never_sent`
- [tests/test_router_r2a_landing.py](../../../../../../../tests/test_router_r2a_landing.py) — direct import
- [tests/test_rw4d_rw3b_composition.py](../../../../../../../tests/test_rw4d_rw3b_composition.py) — direct import
  - `test_a_cue_and_a_kept_mark_on_one_passage_are_independent_and_both_withheld`
  - `test_discovery_on_a_source_whose_kept_comparison_is_withheld_shows_only_its_own_passage`
  - `test_every_passage_rw4ds_predicate_withholds_is_one_the_cues_never_surface`
- [tests/test_source_ingestion_v2lite.py](../../../../../../../tests/test_source_ingestion_v2lite.py) — direct import
  - `test_v2lite_synthesis_respects_persisted_unit_selection`
- [tests/test_source_roles.py](../../../../../../../tests/test_source_roles.py) — direct import
  - `test_a_proposal_held_out_later_is_never_returned`
  - `test_exam_and_held_out_passages_are_never_proposed`
- [tests/test_source_set_synthesis.py](../../../../../../../tests/test_source_set_synthesis.py) — direct import
- [tests/test_source_sets.py](../../../../../../../tests/test_source_sets.py) — direct import
  - `test_exam_use_modes_persist_at_selection`
- [tests/test_tutor_delivery_fixes.py](../../../../../../../tests/test_tutor_delivery_fixes.py) — direct import
  - `test_a_held_out_neighbour_is_skipped_and_the_other_side_still_arrives`
  - `test_references_never_cross_sources_or_reach_held_out_material`
  - `test_the_expanded_delivery_kill_switch_restores_the_predecessors_reader_window`
- [tests/test_ux_phase1_landing.py](../../../../../../../tests/test_ux_phase1_landing.py) — direct import
- [tests/test_whole_comparison_provenance_surfaces.py](../../../../../../../tests/test_whole_comparison_provenance_surfaces.py) — direct import
- [tests/test_whole_comparison_reuse_provenance.py](../../../../../../../tests/test_whole_comparison_reuse_provenance.py) — direct import
  - `test_f1_a_cached_tutor_comparison_checks_the_current_questions_passage`
  - `test_f1_rereview_a_direct_tutor_reuse_persists_its_question_for_later_readers`

## Modification guidance

- Change source unit selection policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/source_unit_selection.py](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
