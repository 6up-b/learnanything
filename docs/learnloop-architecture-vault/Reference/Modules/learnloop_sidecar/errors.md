---
title: "learnloop_sidecar.errors"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/errors.py"
source_paths:
  - "src/learnloop_sidecar/errors.py"
source_commit: "4a28c9635f24945d78366fa26212db7488d82545"
source_commit_timestamp: "2026-05-28T11:36:12-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.errors module"
  - "src/learnloop_sidecar/errors.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.errors`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps errors behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]]. Its public surface centers on `SidecarError`, `json_rpc_error`, `sidecar_error`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/errors.py](../../../../../src/learnloop_sidecar/errors.py) |
| Source lines | 56 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `4a28c9635f24945d78366fa26212db7488d82545` |
| Commit timestamp | `2026-05-28T11:36:12-04:00` |

## Public API

- `class SidecarError(Exception)` ([source](../../../../../src/learnloop_sidecar/errors.py), line 11)
  - `__str__(self) -> str` (line 17; internal)
- `json_rpc_error(code: int, message: str, *, stable_code: str | None=None, retryable: bool=False, details: dict[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../src/learnloop_sidecar/errors.py), line 21)
- `sidecar_error(exc: SidecarError) -> dict[str, Any]` ([source](../../../../../src/learnloop_sidecar/errors.py), line 38)

### Module constants

- `APPLICATION_ERROR_CODE` ([src/learnloop_sidecar/errors.py](../../../../../src/learnloop_sidecar/errors.py), line 7)

## Internal implementation anchors

- `_stable_code_for_json_rpc(code: int) -> str` ([source](../../../../../src/learnloop_sidecar/errors.py), line 48)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/app|learnloop_sidecar.handlers.app]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/capture|learnloop_sidecar.handlers.capture]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/chatgpt_plan|learnloop_sidecar.handlers.chatgpt_plan]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/claims|learnloop_sidecar.handlers.claims]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/cli|learnloop_sidecar.handlers.cli]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/compare_scope|learnloop_sidecar.handlers.compare_scope]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnosis_card|learnloop_sidecar.handlers.diagnosis_card]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnostic|learnloop_sidecar.handlers.diagnostic]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_identity|learnloop_sidecar.handlers.facet_identity]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path|learnloop_sidecar.handlers.golden_path]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path_assessment|learnloop_sidecar.handlers.golden_path_assessment]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/graph_edit|learnloop_sidecar.handlers.graph_edit]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/intent|learnloop_sidecar.handlers.intent]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/kept_comparisons|learnloop_sidecar.handlers.kept_comparisons]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_model|learnloop_sidecar.handlers.knowledge_model]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ladder|learnloop_sidecar.handlers.ladder]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/learner_gaps|learnloop_sidecar.handlers.learner_gaps]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/library|learnloop_sidecar.handlers.library]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/notes|learnloop_sidecar.handlers.notes]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/placement|learnloop_sidecar.handlers.placement]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/practice_index|learnloop_sidecar.handlers.practice_index]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/proposals|learnloop_sidecar.handlers.proposals]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/provenance|learnloop_sidecar.handlers.provenance]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_followups|learnloop_sidecar.handlers.reader_followups]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/reading_paths|learnloop_sidecar.handlers.reading_paths]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/recap|learnloop_sidecar.handlers.recap]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/registry|learnloop_sidecar.handlers.registry]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/side_by_side|learnloop_sidecar.handlers.side_by_side]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/source_service|learnloop_sidecar.handlers.source_service]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/sqlite_admin|learnloop_sidecar.handlers.sqlite_admin]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/vault|learnloop_sidecar.handlers.vault]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `SidecarError`, `json_rpc_error`, `sidecar_error`; statically calls `SidecarError`, `json_rpc_error`, `sidecar_error`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/source_identity|learnloop_sidecar.source_identity]] — imports `SidecarError`; statically calls `SidecarError`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]], [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]], [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]], [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]] and 68 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_build_study_map_routing.py](../../../../../tests/test_build_study_map_routing.py) — direct import
  - `test_out_of_range_or_unknown_ceilings_are_refused`
- [tests/test_capture_desktop.py](../../../../../tests/test_capture_desktop.py) — direct import
  - `test_card_route_after_success_only`
  - `test_desktop_photo_preview_rpc_reads_only_the_capture_original`
  - `test_quick_add_route_after_durable_enqueue_only`
  - `test_tutor_route_after_answer_only_and_reference_anchor`
- [tests/test_capture_route_recovery.py](../../../../../tests/test_capture_route_recovery.py) — direct import
  - `test_changed_route_inputs_cannot_create_a_second_destination`
  - `test_incomplete_tutor_event_is_not_duplicated`
  - `test_preflight_failure_allows_corrected_input`
  - `test_purge_during_tutor_answer_does_not_restore_capture`
  - `test_purge_erases_the_persisted_request`
  - `test_resume_finishes_an_unfinished_route_without_any_inputs`
- [tests/test_compare_keep_switch_off.py](../../../../../tests/test_compare_keep_switch_off.py) — direct import
  - `test_keep_off_every_rw4d_rpc_refuses_and_writes_nothing`
- [tests/test_compare_sources_keep.py](../../../../../tests/test_compare_sources_keep.py) — direct import
  - `test_a_comparison_holding_exam_material_is_refused`
  - `test_a_comparison_job_read_after_withholding_returns_nothing_of_it`
  - `test_a_comparison_jobs_first_delivery_is_withheld_whole`
  - `test_a_dropped_pin_naming_no_passage_withholds_the_comparison`
  - `test_a_kept_comparison_held_out_later_is_neither_marked_nor_reopened`
  - `test_a_kept_comparison_held_out_later_is_not_returned_by_any_reader_rpc`
  - `test_a_new_take_on_an_existing_keep_after_withholding_is_refused`
  - `test_a_take_on_a_passage_not_in_the_comparison_is_refused_and_writes_nothing`
  - `test_a_take_on_an_older_kept_comparison_stays_on_it`
  - `test_a_tutor_keep_takes_a_take_with_the_library_answer_off`
  - `test_an_unreadable_comparison_is_withheld_whole`
  - `test_comparing_writes_no_proposal_and_keep_writes_only_proposals`
  - `test_material_held_out_after_the_comparison_is_not_kept`
  - `test_remove_supersedes_and_never_deletes`
  - `test_replaying_a_take_does_not_duplicate_it_even_at_the_limit`
  - `test_reuse_keeps_every_asks_provenance`
  - `test_the_comparison_switch_and_the_services_switch_turn_keep_off`
  - `test_the_held_out_predicate_fails_closed`
  - `test_the_tutors_comparison_is_kept_only_after_its_press_with_what_it_showed`
  - `test_withholding_the_anchor_before_the_first_keep_refuses_it_with_no_writes`
- [tests/test_curriculum_c0b_landing.py](../../../../../tests/test_curriculum_c0b_landing.py) — direct import
  - `test_ii_curriculum_off_leaves_ca3_and_ca5a_as_with_no_deliverable`
- [tests/test_daily_loop_lo_lifecycle_serving.py](../../../../../tests/test_daily_loop_lo_lifecycle_serving.py) — direct import
  - `test_sidecar_serve_doors_refuse_items_of_a_dormant_lo`
- [tests/test_daily_loop_reference_adoption.py](../../../../../tests/test_daily_loop_reference_adoption.py) — direct import
  - `test_adoption_kill_switch_restores_baseline_and_keeps_adopted_cards`
- [tests/test_daily_plan_rpc.py](../../../../../tests/test_daily_plan_rpc.py) — direct import
  - `test_rpcs_validate_their_inputs`
- [tests/test_deliverable_codex_review.py](../../../../../tests/test_deliverable_codex_review.py) — direct import
  - `test_f16_an_ambiguous_subject_is_offered_and_the_chosen_one_creates_the_topic`
- [tests/test_deliverable_rpcs.py](../../../../../tests/test_deliverable_rpcs.py) — direct import
  - `test_set_scope_refuses_an_exam_passage_and_writes_nothing`
  - `test_switched_off_every_rpc_refuses_and_nothing_is_called_or_written`
  - `test_the_reader_selection_action_scopes_from_the_selected_passage_only`
- [tests/test_dialogue_causal_join.py](../../../../../tests/test_dialogue_causal_join.py) — direct import
  - `test_submit_eliciting_response_sidecar_method`
- [tests/test_exam_protection_review.py](../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_a_session_serve_of_an_item_marked_held_out_is_refused`
  - `test_the_exam_screen_stops_serving_an_item_exposed_mid_exam_and_refuses_its_answer`
- [tests/test_facet_reword_confirm.py](../../../../../tests/test_facet_reword_confirm.py) — direct import
  - `test_the_sidecar_keeps_the_current_wording_on_request`
- [tests/test_facet_reword_paths.py](../../../../../tests/test_facet_reword_paths.py) — direct import
  - `test_a_library_registry_edit_that_does_not_parse_is_refused_and_writes_nothing`
- [tests/test_figure_offers.py](../../../../../tests/test_figure_offers.py) — direct import
  - `test_a_block_the_judgment_did_not_offer_is_refused_before_any_call`
  - `test_offers_off_the_contract_has_none_and_the_press_is_refused`
  - `test_with_the_panels_off_the_author_may_not_emit_them_and_stored_ones_are_cant_draw`
- [tests/test_figure_predictions.py](../../../../../tests/test_figure_predictions.py) — direct import
  - `test_a_prediction_is_answered_once_and_validated`
  - `test_predictions_switch_off`
- [tests/test_figure_region.py](../../../../../tests/test_figure_region.py) — direct import
  - `test_a_region_outside_the_figure_crops_nothing_and_calls_nothing`
  - `test_a_route_without_image_input_is_refused_before_any_call`
  - `test_region_switch_off_refuses_a_region`
- [tests/test_figure_revisions.py](../../../../../tests/test_figure_revisions.py) — direct import
  - `test_revising_an_unknown_figure_is_refused`
  - `test_revisions_switch_off`
- [tests/test_figure_rich_rpc.py](../../../../../tests/test_figure_rich_rpc.py) — direct import
  - `test_allowing_where_manim_cannot_run_is_refused`
  - `test_an_interrupted_rich_only_build_reads_as_failed_and_rich_retry_requeues_it`
  - `test_cancelling_an_unknown_or_other_job_is_refused`
  - `test_switched_off_the_rpcs_refuse_and_the_listing_has_no_rich_key`
- [tests/test_figures_codex_review.py](../../../../../tests/test_figures_codex_review.py) — direct import
  - `test_f1_a_context_neighbour_held_out_after_authoring_withholds_the_figure`
- [tests/test_figures_help.py](../../../../../tests/test_figures_help.py) — direct import
  - `test_a_check_that_takes_no_help_refuses_the_take_step`
  - `test_a_cold_request_without_the_take_step_is_refused_before_any_call`
  - `test_attempt_host_references_are_refused_from_any_other_origin`
  - `test_switched_off_no_figure_in_attempts`
  - `test_the_take_step_converts_first_then_the_request_carrying_its_token_is_built`
- [tests/test_figures_help_codex_review.py](../../../../../tests/test_figures_help_codex_review.py) — direct import
  - `test_f1_a_key_already_in_another_session_is_refused_so_no_row_escapes_the_fold`
  - `test_f1_a_take_step_token_from_another_session_is_not_this_attempts`
  - `test_f1_an_unknown_or_ended_session_is_refused_before_any_job`
  - `test_f4_a_revision_names_an_attempt_host_or_none`
  - `test_f5_switched_off_between_the_build_and_the_delivery_nothing_is_shown_or_counted`
  - `test_rr_f1_a_committed_key_of_another_item_or_session_is_not_free_feedback`
  - `test_rr_f1_a_fresh_key_under_another_open_session_is_refused`
  - `test_s0_a_legacy_queued_attempt_rich_job_stops_before_any_model_request`
  - `test_s0_an_attempt_host_rich_request_is_refused_at_the_rpc`
- [tests/test_figures_prefetch.py](../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_origin_prefetch_is_refused_from_every_rpc_and_outside_the_service`
- [tests/test_figures_rpc.py](../../../../../tests/test_figures_rpc.py) — direct import
  - `test_a_figure_whose_passage_becomes_held_out_is_not_shown`
  - `test_a_metered_route_needs_a_price_and_is_refused_before_sending`
  - `test_held_out_material_is_refused_before_any_call`
  - `test_no_route_set_up_refuses_with_the_reason`
  - `test_switched_off_every_rpc_refuses_and_no_route_is_called`
  - `test_the_client_records_figure_opened_and_animated`
  - `test_the_daily_cap_is_metered_inside_the_spend_machinery`
  - `test_validation_refusals`
- [tests/test_figures_rw5b_fix_round2.py](../../../../../tests/test_figures_rw5b_fix_round2.py) — direct import
  - `test_a_library_note_pointing_at_another_tasks_yes_row_is_refused`
- [tests/test_figures_rw5b_review.py](../../../../../tests/test_figures_rw5b_review.py) — direct import
  - `test_a_figure_using_a_switched_off_panel_is_not_revised`
  - `test_a_library_note_edited_to_offer_without_its_ledger_yes_is_refused`
  - `test_a_reader_ask_answer_offers_and_its_press_builds_from_its_question_event`
  - `test_a_tutor_view_naming_a_block_without_its_ledger_verdict_is_refused`
- [tests/test_figures_show_me.py](../../../../../tests/test_figures_show_me.py) — direct import
  - `test_a_goal_alone_is_refused_while_show_me_is_off`
  - `test_a_retrieved_passage_held_out_later_withholds_the_figure`
  - `test_exam_passages_never_reach_the_author_and_an_exam_home_is_refused`
  - `test_neither_goal_nor_anchor_is_refused_and_show_me_needs_words`
  - `test_show_me_off_lists_no_show_me_figure_and_the_view_is_rw5bs`
  - `test_the_client_never_names_the_goals_author_its_policy_or_a_later_host`
  - `test_the_tutors_goal_is_a_button_and_its_press_builds_from_the_cited_passages`
- [tests/test_figures_show_me_codex_review.py](../../../../../tests/test_figures_show_me_codex_review.py) — direct import
  - `test_f2_a_restricted_question_event_refuses_a_show_me_request`
  - `test_f2_rereview_a_valid_goal_offer_with_a_different_host_is_refused`
  - `test_f2_two_different_answers_named_at_once_are_refused`
  - `test_f4_a_home_held_out_after_construction_withholds_the_figure`
  - `test_f6_a_goal_in_the_view_with_no_ledger_row_is_refused`
  - `test_f6_the_tutors_goal_has_one_ledger_row_and_the_press_reads_it`
  - `test_f7_a_reuse_whose_request_cannot_be_recorded_fails_retryably_and_the_retry_reuses`
- [tests/test_followups_batch5_lesson.py](../../../../../tests/test_followups_batch5_lesson.py) — direct import
  - `test_c_a_step_of_a_saved_lesson_whose_route_is_down_says_it_is_saved`
  - `test_c_an_opening_whose_route_is_down_says_nothing_was_saved`
- [tests/test_goal_scope_material.py](../../../../../tests/test_goal_scope_material.py) — direct import
  - `test_a_facet_only_scope_that_resolves_to_nothing_is_refused`
  - `test_create_goal_refuses_a_concept_with_no_learning_objects`
  - `test_one_unmeasurable_concept_rejects_the_whole_selection`
- [tests/test_graph_editor_reads.py](../../../../../tests/test_graph_editor_reads.py) — direct import
  - `test_get_facet_detail_unknown_facet_raises`
  - `test_preview_blueprint_readiness_malformed_payload_raises`
  - `test_preview_blueprint_readiness_unknown_lo_raises`
  - `test_preview_knowledge_map_unknown_concept_raises`
- [tests/test_hint_kill_switch.py](../../../../../tests/test_hint_kill_switch.py) — direct import
  - `test_h2b_set_help_style_writes_the_one_stored_preference_and_reloads`
- [tests/test_hint_service.py](../../../../../tests/test_hint_service.py) — direct import
  - `test_a_job_of_another_vault_is_never_delivered_after_a_switch`
  - `test_a_malformed_request_answers_its_job_with_a_validation_error`
- [tests/test_hint_telemetry.py](../../../../../tests/test_hint_telemetry.py) — direct import
  - `test_a_grading_fallback_keeps_the_first_submit_time`
  - `test_seconds_into_the_attempt_after_a_grading_fallback_is_the_first_submits`
  - `test_seconds_into_the_attempt_is_unknown_without_the_submits_latency`
  - `test_the_rpc_validates_the_item_and_the_index`
- [tests/test_instrument_servability_journeys.py](../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_a_stem_part_with_no_stimulus_is_still_refused`
  - `test_an_error_hunt_with_a_blank_worked_solution_is_still_refused`
  - `test_an_unknown_item_id_still_reports_not_found`
- [tests/test_intent_rpc.py](../../../../../tests/test_intent_rpc.py) — direct import
  - `test_unknown_scopes_and_choices_are_refused`
  - `test_with_intent_off_the_control_answers_off_and_refuses_writes`
- [tests/test_learner_pick_proposal.py](../../../../../tests/test_learner_pick_proposal.py) — direct import
  - `test_a_pick_of_an_item_reserved_for_an_exam_since_its_proposal_is_refused_before_serving`
  - `test_a_proposal_that_did_not_propose_the_item_is_refused`
  - `test_an_import_that_has_not_written_the_item_is_refused_before_serving`
  - `test_the_open_list_refuses_an_item_reserved_for_an_exam_after_its_pick`
- [tests/test_library_ask_review.py](../../../../../tests/test_library_ask_review.py) — direct import
  - `test_a_compare_without_its_session_stays_the_items_practice`
  - `test_a_held_out_selection_is_refused_before_any_retrieval`
  - `test_every_model_backed_rpc_answers_with_a_job`
  - `test_the_tutor_refuses_a_bound_ask_while_its_cold_administration_is_open`
- [tests/test_library_exercises.py](../../../../../tests/test_library_exercises.py) — direct import
  - `test_a_key_the_proposal_did_not_propose_is_refused`
  - `test_a_problem_imports_one_way_and_an_unproposed_exercise_never_opens`
  - `test_r1_admit_is_a_workbench_rpc_that_refuses_while_switched_off`
  - `test_r2_a_submit_whose_admission_fails_submits_nothing_and_stays_retryable`
  - `test_r2_contract_no_workbench_or_reader_exercise_rpc_returns_a_held_out_statement`
  - `test_r2_verify_f7_get_refresh_and_an_admitted_admit_never_return_a_withheld_statement`
  - `test_r3_a_resume_opens_the_problem_it_names_on_its_own_item_and_book`
  - `test_r4_a_problem_opened_before_its_region_was_held_out_is_not_shown_again`
  - `test_r4_verify_f7_an_exercise_held_out_after_its_card_was_shown_is_never_read_or_opened`
  - `test_switched_off_the_contract_rpcs_and_practice_answer_are_as_before`
  - `test_the_fallback_is_learner_initiated_and_switched_off_by_default`
  - `test_the_learner_pick_is_owed_durably_across_a_restart_and_acknowledged_only_after_delivery`
  - `test_with_the_sources_service_absent_the_view_is_absent`
- [tests/test_notes_linked.py](../../../../../tests/test_notes_linked.py) — direct import
  - `test_a_learner_links_a_note_by_hand_from_the_reader`
  - `test_meaning_search_is_refused_while_embeddings_are_off`
  - `test_switched_off_every_rpc_refuses_nothing_is_read_and_the_reader_is_todays`
- [tests/test_owner_capture_1025.py](../../../../../tests/test_owner_capture_1025.py) — direct import
  - `test_fix2_a_key_from_another_session_is_refused_not_succeeded`
- [tests/test_placement_sidecar.py](../../../../../tests/test_placement_sidecar.py) — direct import
  - `test_self_report_rpc_refuses_honestly_when_placement_is_off`
- [tests/test_plan_first_transport.py](../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_a_background_jobs_offer_reaches_the_read_that_finds_it_done`
  - `test_the_sidecar_attaches_the_typed_hint_and_ai_use_fallback_records_the_choice`
- [tests/test_plan_first_transport_offer_grants.py](../../../../../tests/test_plan_first_transport_offer_grants.py) — direct import
- [tests/test_pr4_superseded_claims_landing.py](../../../../../tests/test_pr4_superseded_claims_landing.py) — direct import
  - `test_landing_i_a_too_easy_retirement_during_a_session`
- [tests/test_practice_index_adapters.py](../../../../../tests/test_practice_index_adapters.py) — direct import
  - `test_sidecar_rpcs`
- [tests/test_reader_active_reading.py](../../../../../tests/test_reader_active_reading.py) — direct import
  - `test_the_rpcs_refuse_while_active_reading_is_off`
- [tests/test_reader_ca1_as_printed.py](../../../../../tests/test_reader_ca1_as_printed.py) — direct import
  - `test_only_a_verbatim_import_can_be_reported`
  - `test_the_switch_off_shows_nothing_and_refuses_the_report`
- [tests/test_reader_ca2_astra_handoff.py](../../../../../tests/test_reader_ca2_astra_handoff.py) — direct import
  - `test_the_budget_spent_in_the_answer_box_stays_spent_in_the_reader`
- [tests/test_reader_ca2_astra_handoff_recovery.py](../../../../../tests/test_reader_ca2_astra_handoff_recovery.py) — direct import
  - `test_a_failed_handoff_write_fails_the_open_and_exposes_no_problem`
  - `test_after_a_restart_the_reader_still_reads_the_answer_box_s_questions`
- [tests/test_reader_ca2_codex_rereview.py](../../../../../tests/test_reader_ca2_codex_rereview.py) — direct import
  - `test_f12_a_withheld_answer_is_never_stored_saved_promoted_or_queued`
- [tests/test_reader_ca2_codex_review.py](../../../../../tests/test_reader_ca2_codex_review.py) — direct import
  - `test_a_workbench_of_another_item_is_refused`
  - `test_worked_help_taken_first_on_a_cold_follow_up_is_practice_with_help`
- [tests/test_reader_ca2_one_ask.py](../../../../../tests/test_reader_ca2_one_ask.py) — direct import
  - `test_a_steps_question_names_its_items_workbench_and_its_step`
  - `test_panel_off_the_sidecar_asks_as_before`
- [tests/test_reader_ca3_codex_rereview.py](../../../../../tests/test_reader_ca3_codex_rereview.py) — direct import
  - `test_f10_a_comparison_that_is_not_the_asks_own_is_refused`
  - `test_f10_while_ca3_is_off_the_tutor_request_is_todays`
- [tests/test_reader_ca3_codex_round3.py](../../../../../tests/test_reader_ca3_codex_round3.py) — direct import
  - `test_f10_a_passages_id_is_its_asks_own_and_unknown_ones_are_refused`
  - `test_f10_while_ca3_is_off_there_is_no_passages_id`
  - `test_f12_a_refinement_that_finishes_unsuperseded_binds_as_before`
- [tests/test_reader_ca3_compare_anywhere.py](../../../../../tests/test_reader_ca3_compare_anywhere.py) — direct import
  - `test_a_library_answer_door_takes_its_answers_question_never_a_new_one`
  - `test_a_named_book_outside_the_scope_is_refused_by_the_rpc`
  - `test_an_exam_anchor_is_refused_before_anything_is_read`
  - `test_pins_still_work_with_the_switch_on`
  - `test_switched_off_the_rpc_is_todays_exactly`
- [tests/test_reader_ca3_landing_ca5a.py](../../../../../tests/test_reader_ca3_landing_ca5a.py) — direct import
  - `test_ii_a_held_out_counterpart_is_never_compared_on_either_path`
  - `test_ii_a_held_out_or_exam_anchor_is_refused_like_the_peek_and_writes_nothing`
- [tests/test_reader_ca4_table_by_point.py](../../../../../tests/test_reader_ca4_table_by_point.py) — direct import
  - `test_a_row_hidden_before_keep_is_left_out`
  - `test_a_take_on_a_row_and_on_the_whole_comparison`
  - `test_a_take_waiting_on_a_hidden_row_goes_with_showing_it`
  - `test_switched_off_rows_and_row_takes_are_refused`
- [tests/test_reader_ca5_also_in_books.py](../../../../../tests/test_reader_ca5_also_in_books.py) — direct import
  - `test_an_operation_id_reused_for_another_lo_set_is_refused_and_writes_nothing`
  - `test_no_change_writes_nothing_and_a_book_must_be_named`
  - `test_not_about_this_names_only_los_of_the_open_section`
  - `test_switched_off_the_preferences_say_so_and_refuse_changes`
  - `test_the_cache_reads_protection_every_time_and_rebuilds_on_a_change`
- [tests/test_reader_ca5_landing.py](../../../../../tests/test_reader_ca5_landing.py) — direct import
  - `test_ii_curriculum_off_and_correspondence_off_each_restore_todays_reader`
- [tests/test_reader_ca5a_find_section.py](../../../../../tests/test_reader_ca5a_find_section.py) — direct import
  - `test_f1_protection_marked_after_the_search_refuses_the_peek`
  - `test_f1_the_peek_is_off_with_the_presentations_switch`
  - `test_f3_an_operation_id_is_never_reused_for_another_correction`
  - `test_f6_dismissing_is_off_with_the_presentations_switch_and_refuses_protected_sections`
- [tests/test_reader_ca6_side_by_side.py](../../../../../tests/test_reader_ca6_side_by_side.py) — direct import
  - `test_an_unknown_section_is_a_validation_error`
  - `test_protected_sections_are_never_shown`
  - `test_switched_off_the_section_read_refuses_and_records_nothing`
- [tests/test_reader_compare_table.py](../../../../../tests/test_reader_compare_table.py) — direct import
  - `test_compare_needs_two_pins_and_its_switch`
  - `test_the_services_compare_switch_also_removes_it`
- [tests/test_reader_cue_holdout.py](../../../../../tests/test_reader_cue_holdout.py) — direct import
  - `test_one_impression_per_visit_and_cue_and_the_client_cannot_invent_one`
  - `test_the_impressions_rpcs_refuse_while_discovery_is_off`
- [tests/test_reader_find_sources_callers.py](../../../../../tests/test_reader_find_sources_callers.py) — direct import
  - `test_with_the_sources_spec_absent_the_library_ask_is_absent`
- [tests/test_reader_followups.py](../../../../../tests/test_reader_followups.py) — direct import
  - `test_the_plan_rpc_refuses_with_the_switch_off`
- [tests/test_reader_intent.py](../../../../../tests/test_reader_intent.py) — direct import
  - `test_the_routing_rpcs_refuse_while_switched_off`
  - `test_the_sidecar_never_sends_a_held_out_passage`
- [tests/test_reader_qualified_span_keys.py](../../../../../tests/test_reader_qualified_span_keys.py) — direct import
  - `test_ca6b_open1_keys_naming_the_requests_own_reading_pass_the_guard`
- [tests/test_reader_recap.py](../../../../../tests/test_reader_recap.py) — direct import
  - `test_switched_off_opening_writes_nothing_and_the_recap_rpcs_refuse`
  - `test_unknown_recap_events_are_refused_before_any_write`
- [tests/test_reader_recap_review.py](../../../../../tests/test_reader_recap_review.py) — direct import
  - `test_f10_inquiry_off_refuses_every_recap_rpc_and_names_no_switch`
- [tests/test_reader_reconstruct.py](../../../../../tests/test_reader_reconstruct.py) — direct import
  - `test_the_rpcs_commit_and_undo_and_say_when_no_objective_is_linked`
- [tests/test_reader_rw1b_review.py](../../../../../tests/test_reader_rw1b_review.py) — direct import
  - `test_f4_only_a_capture_routing_reverts`
  - `test_f6_an_undone_reconstruction_is_never_reported_as_scheduled_again`
- [tests/test_reader_rw2b_fix4.py](../../../../../tests/test_reader_rw2b_fix4.py) — direct import
  - `test_item7_every_help_rpc_refuses_when_help_is_switched_off`
- [tests/test_reader_rw2b_review.py](../../../../../tests/test_reader_rw2b_review.py) — direct import
  - `test_f13_a_pending_hint_is_cancelled_by_the_switch_and_stays_cancelled`
  - `test_f13_switching_help_off_while_a_check_is_pending_delivers_and_counts_nothing`
- [tests/test_reader_rw3b_fix_round4.py](../../../../../tests/test_reader_rw3b_fix_round4.py) — direct import
  - `test_a_source_open_id_names_one_source`
  - `test_an_expired_or_dropped_plan_is_refused_and_nothing_is_stored`
  - `test_an_unknown_plan_id_is_refused_and_nothing_is_stored`
- [tests/test_reader_rw3b_fix_round5.py](../../../../../tests/test_reader_rw3b_fix_round5.py) — direct import
  - `test_a_tap_requires_a_plan_id`
- [tests/test_reader_rw3b_protection.py](../../../../../tests/test_reader_rw3b_protection.py) — direct import
  - `test_a_link_made_before_its_passage_was_held_out_is_never_shown_or_tapped`
- [tests/test_reader_rw3b_review_fixes.py](../../../../../tests/test_reader_rw3b_review_fixes.py) — direct import
  - `test_a_cached_try_first_tap_is_refused_once_try_first_is_switched_off_and_reloaded`
- [tests/test_reader_rw4b_fix6.py](../../../../../tests/test_reader_rw4b_fix6.py) — direct import
  - `test_f7_a_finished_help_job_on_a_problem_held_out_since_is_never_delivered`
- [tests/test_reader_source_identity_guard.py](../../../../../tests/test_reader_source_identity_guard.py) — direct import
- [tests/test_reader_try_first.py](../../../../../tests/test_reader_try_first.py) — direct import
  - `test_try_first_on_a_cue_that_does_not_offer_it_is_refused`
- [tests/test_reader_tutor_offers.py](../../../../../tests/test_reader_tutor_offers.py) — direct import
  - `test_offers_off_sends_no_buttons_and_both_off_leave_the_contract`
- [tests/test_reader_tutor_retrieval.py](../../../../../tests/test_reader_tutor_retrieval.py) — direct import
  - `test_another_way_needs_the_answer_it_is_under`
- [tests/test_reader_workbench_rw2a.py](../../../../../tests/test_reader_workbench_rw2a.py) — direct import
  - `test_a_cold_check_with_the_book_open_is_refused_and_the_session_and_steps_stay`
  - `test_a_multi_part_import_asks_which_part_and_binds_only_one_of_its_own`
  - `test_a_selected_problem_opens_at_once_and_steps_save_before_the_import_binds`
  - `test_a_submitted_session_cannot_be_reopened_or_edited`
  - `test_an_import_that_cannot_start_opens_the_session_failed_with_the_steps_writable`
  - `test_leave_keeps_it_open_abandon_closes_it_reopen_opens_it_and_none_writes_an_attempt`
  - `test_switched_off_every_workbench_rpc_refuses_and_writes_nothing`
  - `test_the_practice_screen_never_shows_the_book_and_records_its_own_surface`
  - `test_with_the_eligibility_switch_off_the_old_cold_guard_still_refuses_the_book`
- [tests/test_reader_wrap_up.py](../../../../../tests/test_reader_wrap_up.py) — direct import
  - `test_wrap_up_switched_off_refuses_and_writes_nothing`
- [tests/test_reading_hardening_landing.py](../../../../../tests/test_reading_hardening_landing.py) — direct import
  - `test_asking_for_a_held_out_sections_check_is_refused_before_anything_is_queued`
- [tests/test_reading_paths.py](../../../../../tests/test_reading_paths.py) — direct import
  - `test_an_unknown_depth_or_choice_is_refused`
  - `test_switched_off_the_guide_contract_and_palette_are_a76c8358a_and_every_rpc_refuses`
- [tests/test_reread_safety.py](../../../../../tests/test_reread_safety.py) — direct import
  - `test_e1_bytes_that_match_nowhere_refuse_plainly_and_register_nothing`
  - `test_rereview_f10_a_place_is_translated_onto_the_reading_the_reader_has_open`
- [tests/test_rw4_kill_switches.py](../../../../../tests/test_rw4_kill_switches.py) — direct import
  - `test_every_rw4a_rpc_refuses_and_writes_nothing`
  - `test_reader_compare_off_removes_compare_only`
- [tests/test_rw4d_rw3b_composition.py](../../../../../tests/test_rw4d_rw3b_composition.py) — direct import
  - `test_a_cue_and_a_kept_mark_on_one_passage_are_independent_and_both_withheld`
  - `test_discovery_on_a_source_whose_kept_comparison_is_withheld_shows_only_its_own_passage`
- [tests/test_secondary_attach.py](../../../../../tests/test_secondary_attach.py) — direct import
  - `test_a_directory_alias_does_not_hide_a_truncated_source_sets_file_from_the_sidecar`
  - `test_a_source_sets_file_that_stays_truncated_is_refused_not_published`
  - `test_secondary_never_creates_a_missing_database`
  - `test_secondary_refusals_for_unbuilt_modes`
  - `test_secondary_refuses_a_schema_it_would_have_to_migrate`
- [tests/test_section_coverage_review.py](../../../../../tests/test_section_coverage_review.py) — direct import
  - `test_landing_f1_the_pressed_check_and_the_read_api_refuse`
- [tests/test_section_coverage_rpcs.py](../../../../../tests/test_section_coverage_rpcs.py) — direct import
  - `test_a_check_with_models_off_starts_nothing`
  - `test_a_correction_through_the_rpc`
  - `test_coverage_jobs_belong_to_the_vault_that_started_them`
  - `test_switched_off_every_rpc_refuses_and_nothing_is_written`
- [tests/test_session_ownership.py](../../../../../tests/test_session_ownership.py) — direct import
  - `test_a_skip_never_clears_the_draft_of_a_device_that_adopted_while_the_queue_was_built`
  - `test_a_skip_refuses_a_session_that_moved_and_came_back_while_the_queue_was_built`
  - `test_every_session_scoped_write_from_the_old_owner_is_session_moved`
  - `test_the_desktop_start_reports_a_phone_session_instead_of_ending_it`
  - `test_the_owner_writes_as_before_and_ended_sessions_keep_their_old_errors`
- [tests/test_sidecar_adjudication.py](../../../../../tests/test_sidecar_adjudication.py) — direct import
  - `test_queue_is_stratified_contests_first_then_abstentions`
  - `test_record_refuses_a_verdict_the_partition_forbids`
  - `test_scoreboard_keeps_enum_keys_and_refuses_a_flattering_rate`
- [tests/test_sidecar_contract.py](../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_invalid_pdf_page_expressions_are_rejected`
- [tests/test_sidecar_goals.py](../../../../../tests/test_sidecar_goals.py) — direct import
  - `test_create_goal_rejects_empty_scope`
- [tests/test_sidecar_item_presentation.py](../../../../../tests/test_sidecar_item_presentation.py) — direct import
  - `test_a_stem_part_with_no_stimulus_is_a_typed_refusal`
  - `test_an_error_hunt_with_no_worked_solution_is_a_typed_refusal`
- [tests/test_sidecar_measurement.py](../../../../../tests/test_sidecar_measurement.py) — direct import
  - `test_causal_probe_review_transition_returns_a_typed_sidecar_error`
  - `test_generate_commissioning_practice_rejects_unknown_learning_objects`
  - `test_integration_backfill_requires_explicit_confirmation`
- [tests/test_sidecar_trace_and_clarification.py](../../../../../tests/test_sidecar_trace_and_clarification.py) — direct import
  - `test_an_empty_answer_is_refused_rather_than_burning_the_one_question`
  - `test_answering_a_question_that_was_never_asked_is_a_typed_refusal`
  - `test_answering_the_same_question_twice_is_a_typed_refusal`
  - `test_trace_evidence_read_rejects_an_unknown_attempt`
- [tests/test_sketch_service.py](../../../../../tests/test_sketch_service.py) — direct import
  - `test_a_prediction_an_upgrade_dropped_is_refused`
  - `test_an_engine_upgrade_reverifies_with_no_model_call`
  - `test_off_a_stored_sketch_lists_as_cant_draw_this_yet`
- [tests/test_teacher_te1_successor.py](../../../../../tests/test_teacher_te1_successor.py) — direct import
  - `test_lesson_turn_refuses_with_the_switch_off`
- [tests/test_teacher_te1b_suggestions.py](../../../../../tests/test_teacher_te1b_suggestions.py) — direct import
  - `test_start_opens_a_lesson_whose_origin_is_the_decision`
- [tests/test_ux_phase1_add_source.py](../../../../../tests/test_ux_phase1_add_source.py) — direct import
  - `test_add_source_rejects_a_bad_page_range_plainly`
- [tests/test_ux_phase1_connect_ai.py](../../../../../tests/test_ux_phase1_connect_ai.py) — direct import
  - `test_continue_with_chatgpt_needs_a_sign_in_first`
  - `test_openrouter_needs_its_key`
  - `test_without_a_ready_route_the_sheet_asks_to_connect`
- [tests/test_ux_phase1_review_fixes.py](../../../../../tests/test_ux_phase1_review_fixes.py) — direct import
  - `test_f9_text_recognition_without_an_extractor_that_can_do_it_says_so`
- [tests/test_ux_phase3_today.py](../../../../../tests/test_ux_phase3_today.py) — direct import
  - `test_switched_off_open_problems_refuses_like_every_workbench_rpc`
- [tests/test_ux_phase4_feedback.py](../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_a_plain_regrade_records_no_contest`
  - `test_f10_a_contest_key_resent_with_an_edited_reason_is_refused_never_dropped`
  - `test_f1_an_unknown_attempt_records_no_display`
  - `test_f1g_a_disclosure_display_needs_its_pending_draft`
  - `test_f1g_a_display_that_failed_to_persist_is_never_acknowledged`
  - `test_f7_a_contest_that_fails_before_any_write_reports_not_recorded`
- [tests/test_whole_comparison_provenance_surfaces.py](../../../../../tests/test_whole_comparison_provenance_surfaces.py) — direct import
  - `test_rw4d_followup_a_tutor_run_whose_question_passage_is_held_out_is_refused_whole`
  - `test_rw4d_followup_find_sources_compare_intent_applies_the_rule`
  - `test_rw4d_followup_the_direct_rpc_refuses_a_comparison_pinning_held_out_material`
  - `test_rw4d_followup_the_direct_rpc_refuses_a_comparison_whose_dropped_pin_is_exam_material`
  - `test_rw4d_followup_the_rule_fails_closed_on_the_direct_rpc`
- [tests/test_whole_comparison_reuse_provenance.py](../../../../../tests/test_whole_comparison_reuse_provenance.py) — direct import
  - `test_f1_a_cached_tutor_comparison_checks_the_current_questions_passage`
  - `test_f1_a_reused_comparison_with_a_new_exam_pin_is_withheld_whole`
  - `test_f1_a_reuses_pin_naming_no_passage_is_not_persisted`
  - `test_f1_find_sources_compare_reads_a_reuses_persisted_exam_pin`
  - `test_f1_rereview_a_direct_tutor_reuse_persists_its_question_for_later_readers`
  - `test_f1_the_reuses_dropped_pin_is_persisted_for_later_reads`
  - `test_nov1_open_item_3_a_fresh_comparisons_pin_naming_no_passage_is_not_persisted`
- [tests/test_workbench_check.py](../../../../../tests/test_workbench_check.py) — direct import
  - `test_check_and_help_wait_for_setup_and_refuse_while_switched_off`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/errors.py](../../../../../src/learnloop_sidecar/errors.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
