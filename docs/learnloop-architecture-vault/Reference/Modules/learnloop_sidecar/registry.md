---
title: "learnloop_sidecar.registry"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/registry.py"
source_paths:
  - "src/learnloop_sidecar/registry.py"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
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
  - "learnloop_sidecar.registry module"
  - "src/learnloop_sidecar/registry.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.registry`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps registry behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]]. Its public surface centers on `MethodSpec`, `method`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/registry.py](../../../../../src/learnloop_sidecar/registry.py) |
| Source lines | 36 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class MethodSpec` ([source](../../../../../src/learnloop_sidecar/registry.py), line 14)
- `method(name: str, params_model: type[ParamsModel]=EmptyParams) -> Callable[[Handler], Handler]` ([source](../../../../../src/learnloop_sidecar/registry.py), line 23)

### Module constants

- `METHOD_REGISTRY` ([src/learnloop_sidecar/registry.py](../../../../../src/learnloop_sidecar/registry.py), line 20)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/app|learnloop_sidecar.handlers.app]] — imports `METHOD_REGISTRY`, `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/capture|learnloop_sidecar.handlers.capture]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/chatgpt_plan|learnloop_sidecar.handlers.chatgpt_plan]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/claims|learnloop_sidecar.handlers.claims]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/cli|learnloop_sidecar.handlers.cli]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/compare_scope|learnloop_sidecar.handlers.compare_scope]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnosis_card|learnloop_sidecar.handlers.diagnosis_card]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnostic|learnloop_sidecar.handlers.diagnostic]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/epigraphs|learnloop_sidecar.handlers.epigraphs]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_identity|learnloop_sidecar.handlers.facet_identity]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/facets|learnloop_sidecar.handlers.facets]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/followup|learnloop_sidecar.handlers.followup]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path|learnloop_sidecar.handlers.golden_path]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path_assessment|learnloop_sidecar.handlers.golden_path_assessment]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/graph|learnloop_sidecar.handlers.graph]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/graph_edit|learnloop_sidecar.handlers.graph_edit]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/inspector|learnloop_sidecar.handlers.inspector]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/intent|learnloop_sidecar.handlers.intent]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/kept_comparisons|learnloop_sidecar.handlers.kept_comparisons]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_model|learnloop_sidecar.handlers.knowledge_model]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/ladder|learnloop_sidecar.handlers.ladder]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/learner_gaps|learnloop_sidecar.handlers.learner_gaps]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/library|learnloop_sidecar.handlers.library]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/notes|learnloop_sidecar.handlers.notes]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/placement|learnloop_sidecar.handlers.placement]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/practice_index|learnloop_sidecar.handlers.practice_index]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/proposals|learnloop_sidecar.handlers.proposals]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/provenance|learnloop_sidecar.handlers.provenance]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_followups|learnloop_sidecar.handlers.reader_followups]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/reading_paths|learnloop_sidecar.handlers.reading_paths]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/recap|learnloop_sidecar.handlers.recap]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/registry|learnloop_sidecar.handlers.registry]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/review|learnloop_sidecar.handlers.review]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/router_objective|learnloop_sidecar.handlers.router_objective]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/side_by_side|learnloop_sidecar.handlers.side_by_side]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/source_service|learnloop_sidecar.handlers.source_service]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/sqlite_admin|learnloop_sidecar.handlers.sqlite_admin]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/vault|learnloop_sidecar.handlers.vault]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `METHOD_REGISTRY`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `EmptyParams`, `ParamsModel`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]], [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]], [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]], [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]], [[Reference/Modules/learnloop_sidecar/handlers/app|learnloop_sidecar.handlers.app]] and 70 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/reading_path_fixtures.py](../../../../../tests/reading_path_fixtures.py) — direct import
- [tests/recap_fixtures.py](../../../../../tests/recap_fixtures.py) — direct import
- [tests/rw2b_fix10_base_sequence.py](../../../../../tests/rw2b_fix10_base_sequence.py) — direct import
- [tests/rw2b_fix11_base_sequence.py](../../../../../tests/rw2b_fix11_base_sequence.py) — direct import
- [tests/rw2c_state_parity.py](../../../../../tests/rw2c_state_parity.py) — direct import
- [tests/test_ad1_attempt_columns.py](../../../../../tests/test_ad1_attempt_columns.py) — direct import
- [tests/test_ad23_contract.py](../../../../../tests/test_ad23_contract.py) — direct import
  - `test_the_sidecar_uptake_callback_answers_a_no_op_with_ad_off`
- [tests/test_ad23_fix_review.py](../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_the_offer_names_the_sections_other_question_and_its_answer_is_the_extra`
  - `test_the_sidecar_queues_a_serve_commission_after_the_serve`
- [tests/test_ad23_intent_compose.py](../../../../../tests/test_ad23_intent_compose.py) — direct import
  - `test_the_real_scheduler_lane_with_commitments`
- [tests/test_ad23_successor.py](../../../../../tests/test_ad23_successor.py) — direct import
- [tests/test_ad2_serving.py](../../../../../tests/test_ad2_serving.py) — direct import
  - `test_why_this_item_names_the_draw_that_chose_it`
- [tests/test_ad3_dose_arm.py](../../../../../tests/test_ad3_dose_arm.py) — direct import
  - `test_switch_off_is_todays_reader_exactly`
- [tests/test_approach_map_replay.py](../../../../../tests/test_approach_map_replay.py) — direct import
- [tests/test_approach_maps.py](../../../../../tests/test_approach_maps.py) — direct import
- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../tests/test_causal_repair_sidecar_rpcs.py) — direct import
  - `test_causal_repair_methods_are_registered_and_accept_the_client_payloads`
- [tests/test_chatgpt_plan_sidecar.py](../../../../../tests/test_chatgpt_plan_sidecar.py) — direct import
  - `test_rpcs_are_registered`
- [tests/test_compare_sources_keep.py](../../../../../tests/test_compare_sources_keep.py) — direct import
  - `test_every_registered_handler_reading_source_objects_is_pinned`
- [tests/test_daily_loop_lo_lifecycle_serving.py](../../../../../tests/test_daily_loop_lo_lifecycle_serving.py) — direct import
- [tests/test_daily_loop_reader_retire.py](../../../../../tests/test_daily_loop_reader_retire.py) — direct import
  - `test_sidecar_retire_takes_the_card_out_of_today`
- [tests/test_daily_loop_reentry_break.py](../../../../../tests/test_daily_loop_reentry_break.py) — direct import
- [tests/test_daily_loop_reentry_cap.py](../../../../../tests/test_daily_loop_reentry_cap.py) — direct import
- [tests/test_daily_loop_reference_adoption.py](../../../../../tests/test_daily_loop_reference_adoption.py) — direct import
  - `test_adoption_kill_switch_restores_baseline_and_keeps_adopted_cards`
  - `test_sidecar_reload_adopts_and_today_serves_it`
- [tests/test_daily_loop_start_minutes.py](../../../../../tests/test_daily_loop_start_minutes.py) — direct import
- [tests/test_daily_plan_composition.py](../../../../../tests/test_daily_plan_composition.py) — direct import
- [tests/test_daily_plan_kill_switch.py](../../../../../tests/test_daily_plan_kill_switch.py) — direct import
- [tests/test_daily_plan_reading.py](../../../../../tests/test_daily_plan_reading.py) — direct import
- [tests/test_daily_plan_reentry.py](../../../../../tests/test_daily_plan_reentry.py) — direct import
- [tests/test_daily_plan_review_regressions.py](../../../../../tests/test_daily_plan_review_regressions.py) — direct import
- [tests/test_daily_plan_rpc.py](../../../../../tests/test_daily_plan_rpc.py) — direct import
- [tests/test_data_capture_a1_prefilter.py](../../../../../tests/test_data_capture_a1_prefilter.py) — direct import
  - `test_todays_offer_links_its_builds_receipt_with_every_gate`
- [tests/test_data_capture_codex_review.py](../../../../../tests/test_data_capture_codex_review.py) — direct import
  - `test_f8_an_offers_receipt_commits_in_its_decisions_transaction`
- [tests/test_decider_landing.py](../../../../../tests/test_decider_landing.py) — direct import
- [tests/test_deliverable_rpcs.py](../../../../../tests/test_deliverable_rpcs.py) — direct import
  - `test_the_rpcs_are_registered_and_desktop_only`
- [tests/test_desktop_rpc_contract.py](../../../../../tests/test_desktop_rpc_contract.py) — direct import
  - `test_every_decorated_handler_is_loaded_once`
  - `test_the_revision_read_carries_its_hold_through_every_layer`
- [tests/test_device_eligibility.py](../../../../../tests/test_device_eligibility.py) — direct import
- [tests/test_dialogue_causal_join.py](../../../../../tests/test_dialogue_causal_join.py) — direct import
- [tests/test_evsi_router_composition.py](../../../../../tests/test_evsi_router_composition.py) — direct import
- [tests/test_exam_protection_review.py](../../../../../tests/test_exam_protection_review.py) — direct import
- [tests/test_facet_reword_paths.py](../../../../../tests/test_facet_reword_paths.py) — direct import
- [tests/test_facet_rewords.py](../../../../../tests/test_facet_rewords.py) — direct import
  - `test_the_facet_inspector_shows_the_version_history_and_undoes_a_reword`
- [tests/test_figures_help.py](../../../../../tests/test_figures_help.py) — direct import
- [tests/test_followup_codex_review.py](../../../../../tests/test_followup_codex_review.py) — direct import
- [tests/test_followup_journey.py](../../../../../tests/test_followup_journey.py) — direct import
- [tests/test_followup_next_matrix.py](../../../../../tests/test_followup_next_matrix.py) — direct import
- [tests/test_followup_rival_factor.py](../../../../../tests/test_followup_rival_factor.py) — direct import
- [tests/test_goal_scope_material.py](../../../../../tests/test_goal_scope_material.py) — direct import
- [tests/test_graph_editor_reads.py](../../../../../tests/test_graph_editor_reads.py) — direct import
- [tests/test_help_assist_work_md_migration.py](../../../../../tests/test_help_assist_work_md_migration.py) — direct import
- [tests/test_hint_authored_reveal_ruling.py](../../../../../tests/test_hint_authored_reveal_ruling.py) — direct import
- [tests/test_hint_blind.py](../../../../../tests/test_hint_blind.py) — direct import
- [tests/test_hint_discriminating.py](../../../../../tests/test_hint_discriminating.py) — direct import
- [tests/test_hint_evidence.py](../../../../../tests/test_hint_evidence.py) — direct import
- [tests/test_hint_feedback_texts.py](../../../../../tests/test_hint_feedback_texts.py) — direct import
- [tests/test_hint_h2a_review.py](../../../../../tests/test_hint_h2a_review.py) — direct import
- [tests/test_hint_h2a_review_round2.py](../../../../../tests/test_hint_h2a_review_round2.py) — direct import
- [tests/test_hint_h2b_review.py](../../../../../tests/test_hint_h2b_review.py) — direct import
- [tests/test_hint_kill_switch.py](../../../../../tests/test_hint_kill_switch.py) — direct import
  - `test_h2b_the_app_snapshot_through_the_sidecar_carries_no_hints_key_when_off`
  - `test_the_served_item_and_its_cold_check_fields_are_unchanged_by_the_switch`
- [tests/test_hint_outcome.py](../../../../../tests/test_hint_outcome.py) — direct import
- [tests/test_hint_report.py](../../../../../tests/test_hint_report.py) — direct import
- [tests/test_hint_service.py](../../../../../tests/test_hint_service.py) — direct import
  - `test_a_job_of_another_vault_is_never_delivered_after_a_switch`
  - `test_a_malformed_request_answers_its_job_with_a_validation_error`
  - `test_the_request_is_a_job_and_the_read_that_returns_it_shows_it`
  - `test_with_no_draft_in_the_request_the_session_checkpoints_draft_is_read`
- [tests/test_hint_telemetry.py](../../../../../tests/test_hint_telemetry.py) — direct import
- [tests/test_host_queue_revision.py](../../../../../tests/test_host_queue_revision.py) — direct import
- [tests/test_instrument_servability_journeys.py](../../../../../tests/test_instrument_servability_journeys.py) — direct import
- [tests/test_integration_daily_loop_field.py](../../../../../tests/test_integration_daily_loop_field.py) — direct import
- [tests/test_intent_fix_round4.py](../../../../../tests/test_intent_fix_round4.py) — direct import
- [tests/test_intent_orchestrator_rulings.py](../../../../../tests/test_intent_orchestrator_rulings.py) — direct import
- [tests/test_intent_rpc.py](../../../../../tests/test_intent_rpc.py) — direct import
- [tests/test_keep_local_retired.py](../../../../../tests/test_keep_local_retired.py) — direct import
- [tests/test_learner_pick_proposal.py](../../../../../tests/test_learner_pick_proposal.py) — direct import
- [tests/test_library_exercises.py](../../../../../tests/test_library_exercises.py) — direct import
  - `test_r2_contract_no_workbench_or_reader_exercise_rpc_returns_a_held_out_statement`
- [tests/test_lp_claim_fixes_review.py](../../../../../tests/test_lp_claim_fixes_review.py) — direct import
- [tests/test_mobile_allowlist.py](../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_desktop_and_main_rpcs_are_registered_but_never_phone_allowed`
  - `test_every_other_registered_method_is_denied`
  - `test_r2a_params_are_the_plan_presentation_on_the_three_answer_rpcs`
  - `test_rw2b_fix5_authored_hints_is_an_optional_param_of_the_two_submits`
- [tests/test_mobile_handoff.py](../../../../../tests/test_mobile_handoff.py) — direct import
- [tests/test_mobile_host_auth.py](../../../../../tests/test_mobile_host_auth.py) — direct import
  - `test_desktop_only_and_main_rpcs_are_http_denied_for_every_phone_scope`
  - `test_every_method_outside_the_m2_row_is_http_denied`
- [tests/test_mobile_jobs.py](../../../../../tests/test_mobile_jobs.py) — direct import
  - `test_the_submission_endpoint_covers_a_desktops_submissions`
- [tests/test_mobile_phone_contract.py](../../../../../tests/test_mobile_phone_contract.py) — direct import
  - `test_a_renamed_field_fails_the_model_not_the_phone`
  - `test_every_recorded_request_passes_the_hosts_own_checks`
- [tests/test_mobile_rpc.py](../../../../../tests/test_mobile_rpc.py) — direct import
  - `test_a_locked_database_is_503_retryable`
  - `test_an_unknown_id_is_404_and_a_handler_crash_is_500_with_no_detail`
  - `test_every_other_registered_method_answers_403`
  - `test_no_allowlisted_model_declares_a_path_the_rule_misses`
  - `test_the_allowlist_is_the_m2_row_and_every_name_is_a_registered_method`
  - `test_the_desktops_offer_under_a_plan_is_still_full_list`
- [tests/test_mobile_two_process.py](../../../../../tests/test_mobile_two_process.py) — direct import
  - `test_the_desktop_and_the_host_coexist_with_no_lost_writes`
  - `test_the_phone_and_the_desktop_take_turns_on_one_plan`
- [tests/test_mobile_v2_followup.py](../../../../../tests/test_mobile_v2_followup.py) — direct import
- [tests/test_mobile_v2_plan.py](../../../../../tests/test_mobile_v2_plan.py) — direct import
- [tests/test_notes_linked.py](../../../../../tests/test_notes_linked.py) — direct import
  - `test_the_rpcs_are_registered_and_desktop_only`
- [tests/test_owner_capture_1025.py](../../../../../tests/test_owner_capture_1025.py) — direct import
- [tests/test_plan_determinism.py](../../../../../tests/test_plan_determinism.py) — direct import
- [tests/test_plan_first_transport.py](../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_f8_an_error_that_is_not_a_sidecar_error_keeps_the_offer`
  - `test_the_sidecar_attaches_the_typed_hint_and_ai_use_fallback_records_the_choice`
- [tests/test_plan_first_transport_offer_grants.py](../../../../../tests/test_plan_first_transport_offer_grants.py) — direct import
- [tests/test_pr4_superseded_claims_landing.py](../../../../../tests/test_pr4_superseded_claims_landing.py) — direct import
- [tests/test_practice_index_adapters.py](../../../../../tests/test_practice_index_adapters.py) — direct import
  - `test_sidecar_rpcs`
- [tests/test_reader_ca1_as_printed.py](../../../../../tests/test_reader_ca1_as_printed.py) — direct import
  - `test_the_crop_rpc_takes_a_problems_blocks`
- [tests/test_reader_ca1_codex_review.py](../../../../../tests/test_reader_ca1_codex_review.py) — direct import
  - `test_render_and_region_belong_to_the_multi_block_form`
- [tests/test_reader_ca2_codex_review.py](../../../../../tests/test_reader_ca2_codex_review.py) — direct import
- [tests/test_reader_ca2_one_ask.py](../../../../../tests/test_reader_ca2_one_ask.py) — direct import
- [tests/test_reader_ca5_also_in_books.py](../../../../../tests/test_reader_ca5_also_in_books.py) — direct import
  - `test_the_ca5_rpcs_are_registered_and_desktop_only`
- [tests/test_reader_followups_successor.py](../../../../../tests/test_reader_followups_successor.py) — direct import
- [tests/test_reader_rw3a_landing.py](../../../../../tests/test_reader_rw3a_landing.py) — direct import
- [tests/test_reader_workbench_rw2a.py](../../../../../tests/test_reader_workbench_rw2a.py) — direct import
- [tests/test_reader_wrap_up.py](../../../../../tests/test_reader_wrap_up.py) — direct import
  - `test_wrap_up_is_a_pure_read_and_its_actions_are_the_chips_rpcs`
- [tests/test_regrade_contract_replay.py](../../../../../tests/test_regrade_contract_replay.py) — direct import
  - `test_case1_a_contest_of_a_model_grade_above_its_original_maximum_looks_again`
- [tests/test_regrade_contract_successor.py](../../../../../tests/test_regrade_contract_successor.py) — direct import
- [tests/test_request_origin.py](../../../../../tests/test_request_origin.py) — direct import
  - `test_no_parameter_can_set_the_surface_or_the_device`
- [tests/test_required_method_round3_review.py](../../../../../tests/test_required_method_round3_review.py) — direct import
  - `test_f3_adjudication_shows_the_question_the_answer_was_given`
- [tests/test_reread_safety.py](../../../../../tests/test_reread_safety.py) — direct import
- [tests/test_ro0_codex_review.py](../../../../../tests/test_ro0_codex_review.py) — direct import
- [tests/test_ro0_gate.py](../../../../../tests/test_ro0_gate.py) — direct import
- [tests/test_ro0_rows7_8_sessions.py](../../../../../tests/test_ro0_rows7_8_sessions.py) — direct import
- [tests/test_ro4_goals.py](../../../../../tests/test_ro4_goals.py) — direct import
- [tests/test_router_offer_log.py](../../../../../tests/test_router_offer_log.py) — direct import
- [tests/test_router_outcomes.py](../../../../../tests/test_router_outcomes.py) — direct import
  - `test_the_replayer_rebuilds_router_outcomes_deterministically_with_no_model_call`
- [tests/test_router_p2_bridge.py](../../../../../tests/test_router_p2_bridge.py) — direct import
- [tests/test_router_probe_ties.py](../../../../../tests/test_router_probe_ties.py) — direct import
- [tests/test_router_r1_composition.py](../../../../../tests/test_router_r1_composition.py) — direct import
- [tests/test_router_r2a_serving.py](../../../../../tests/test_router_r2a_serving.py) — direct import
- [tests/test_router_r2b_serving.py](../../../../../tests/test_router_r2b_serving.py) — direct import
- [tests/test_section_coverage_rpcs.py](../../../../../tests/test_section_coverage_rpcs.py) — direct import
  - `test_the_rpcs_are_registered_and_desktop_only`
- [tests/test_serve_eligibility_review.py](../../../../../tests/test_serve_eligibility_review.py) — direct import
  - `test_a_cold_check_on_a_direct_open_is_withdrawn_when_its_item_can_no_longer_take_it_cold`
- [tests/test_session_ownership.py](../../../../../tests/test_session_ownership.py) — direct import
- [tests/test_sidecar_adjudication.py](../../../../../tests/test_sidecar_adjudication.py) — direct import
- [tests/test_sidecar_contract.py](../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_database_lock_contention_is_a_retryable_error`
  - `test_model_call_receipts_are_owned_by_the_normalized_submission_key`
- [tests/test_sidecar_exams.py](../../../../../tests/test_sidecar_exams.py) — direct import
- [tests/test_sidecar_goals.py](../../../../../tests/test_sidecar_goals.py) — direct import
- [tests/test_sidecar_item_presentation.py](../../../../../tests/test_sidecar_item_presentation.py) — direct import
- [tests/test_sidecar_measurement.py](../../../../../tests/test_sidecar_measurement.py) — direct import
- [tests/test_sidecar_trace_and_clarification.py](../../../../../tests/test_sidecar_trace_and_clarification.py) — direct import
- [tests/test_sidecar_transport.py](../../../../../tests/test_sidecar_transport.py) — direct import
  - `test_duplicate_method_registration_fails_loudly`
  - `test_unexpected_handler_failure_marks_the_commit_outcome_unknown`
- [tests/test_stuck_prompt.py](../../../../../tests/test_stuck_prompt.py) — direct import
- [tests/test_teacher_te2_sidecar.py](../../../../../tests/test_teacher_te2_sidecar.py) — direct import
  - `test_the_rpcs_are_registered_desktop_only`
- [tests/test_teacher_te2log_activity.py](../../../../../tests/test_teacher_te2log_activity.py) — direct import
  - `test_lesson_activity_is_a_desktop_only_rpc_that_records_intervals`
- [tests/test_ux_phase1_add_source.py](../../../../../tests/test_ux_phase1_add_source.py) — direct import
- [tests/test_ux_phase1_connect_ai.py](../../../../../tests/test_ux_phase1_connect_ai.py) — direct import
- [tests/test_ux_phase1_review_fixes.py](../../../../../tests/test_ux_phase1_review_fixes.py) — direct import
- [tests/test_ux_phase4_feedback.py](../../../../../tests/test_ux_phase4_feedback.py) — direct import
- [tests/test_ux_phase4_landing.py](../../../../../tests/test_ux_phase4_landing.py) — direct import
  - `test_a_cold_check_on_a_direct_open_is_served_as_on_main_unless_a_routine_display_covers_it`
- [tests/test_voi_merge_composition.py](../../../../../tests/test_voi_merge_composition.py) — direct import
- [tests/test_voi_stopping.py](../../../../../tests/test_voi_stopping.py) — direct import
  - `test_below_the_successor_the_offer_logs_no_value_decisions`
  - `test_the_continue_decision_rides_on_the_committed_presentation_and_the_offer`
- [tests/workbench_help_fakes.py](../../../../../tests/workbench_help_fakes.py) — direct import

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/registry.py](../../../../../src/learnloop_sidecar/registry.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
