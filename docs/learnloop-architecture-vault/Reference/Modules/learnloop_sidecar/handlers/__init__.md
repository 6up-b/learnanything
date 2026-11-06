---
title: "learnloop_sidecar.handlers"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/__init__.py"
source_paths:
  - "src/learnloop_sidecar/handlers/__init__.py"
source_commit: "838d8ee1fcee48de3b5b41f59e451f042ec9a690"
source_commit_timestamp: "2026-11-05T04:03:05-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop_sidecar.handlers module"
  - "src/learnloop_sidecar/handlers/__init__.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module establishes the Python package boundary for [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]].

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/__init__.py](../../../../../../src/learnloop_sidecar/handlers/__init__.py) |
| Source lines | 78 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `838d8ee1fcee48de3b5b41f59e451f042ec9a690` |
| Commit timestamp | `2026-11-05T04:03:05-05:00` |

## Public API

No public top-level function or class definition is declared in this file.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/app|learnloop_sidecar.handlers.app]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/capture|learnloop_sidecar.handlers.capture]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/chatgpt_plan|learnloop_sidecar.handlers.chatgpt_plan]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/claims|learnloop_sidecar.handlers.claims]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/cli|learnloop_sidecar.handlers.cli]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/compare_scope|learnloop_sidecar.handlers.compare_scope]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnosis_card|learnloop_sidecar.handlers.diagnosis_card]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnostic|learnloop_sidecar.handlers.diagnostic]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/epigraphs|learnloop_sidecar.handlers.epigraphs]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_identity|learnloop_sidecar.handlers.facet_identity]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/facets|learnloop_sidecar.handlers.facets]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/followup|learnloop_sidecar.handlers.followup]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path|learnloop_sidecar.handlers.golden_path]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path_assessment|learnloop_sidecar.handlers.golden_path_assessment]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/graph|learnloop_sidecar.handlers.graph]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/graph_edit|learnloop_sidecar.handlers.graph_edit]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/inspector|learnloop_sidecar.handlers.inspector]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/intent|learnloop_sidecar.handlers.intent]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/kept_comparisons|learnloop_sidecar.handlers.kept_comparisons]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_model|learnloop_sidecar.handlers.knowledge_model]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/ladder|learnloop_sidecar.handlers.ladder]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/learner_gaps|learnloop_sidecar.handlers.learner_gaps]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/library|learnloop_sidecar.handlers.library]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/notes|learnloop_sidecar.handlers.notes]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/placement|learnloop_sidecar.handlers.placement]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/practice_index|learnloop_sidecar.handlers.practice_index]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/proposals|learnloop_sidecar.handlers.proposals]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/provenance|learnloop_sidecar.handlers.provenance]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_followups|learnloop_sidecar.handlers.reader_followups]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/reading_paths|learnloop_sidecar.handlers.reading_paths]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/recap|learnloop_sidecar.handlers.recap]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/registry|learnloop_sidecar.handlers.registry]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/review|learnloop_sidecar.handlers.review]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/router_objective|learnloop_sidecar.handlers.router_objective]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/side_by_side|learnloop_sidecar.handlers.side_by_side]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/source_service|learnloop_sidecar.handlers.source_service]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/sqlite_admin|learnloop_sidecar.handlers.sqlite_admin]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/vault|learnloop_sidecar.handlers.vault]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/reading_path_fixtures.py](../../../../../../tests/reading_path_fixtures.py) — direct import
- [tests/recap_fixtures.py](../../../../../../tests/recap_fixtures.py) — direct import
- [tests/rw2b_fix10_base_sequence.py](../../../../../../tests/rw2b_fix10_base_sequence.py) — direct import
- [tests/rw2b_fix11_base_sequence.py](../../../../../../tests/rw2b_fix11_base_sequence.py) — direct import
- [tests/rw2c_base_sequence.py](../../../../../../tests/rw2c_base_sequence.py) — direct import
- [tests/rw2c_state_parity.py](../../../../../../tests/rw2c_state_parity.py) — direct import
- [tests/test_ad1_attempt_columns.py](../../../../../../tests/test_ad1_attempt_columns.py) — direct import
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
- [tests/test_ad23_intent_compose.py](../../../../../../tests/test_ad23_intent_compose.py) — direct import
- [tests/test_ad23_successor.py](../../../../../../tests/test_ad23_successor.py) — direct import
- [tests/test_ad2_serving.py](../../../../../../tests/test_ad2_serving.py) — direct import
- [tests/test_ad3_dose_arm.py](../../../../../../tests/test_ad3_dose_arm.py) — direct import
- [tests/test_approach_map_replay.py](../../../../../../tests/test_approach_map_replay.py) — direct import
- [tests/test_approach_maps.py](../../../../../../tests/test_approach_maps.py) — direct import
- [tests/test_chatgpt_plan_sidecar.py](../../../../../../tests/test_chatgpt_plan_sidecar.py) — direct import
- [tests/test_daily_loop_lo_lifecycle_serving.py](../../../../../../tests/test_daily_loop_lo_lifecycle_serving.py) — direct import
- [tests/test_daily_loop_reader_retire.py](../../../../../../tests/test_daily_loop_reader_retire.py) — direct import
- [tests/test_daily_loop_reentry_break.py](../../../../../../tests/test_daily_loop_reentry_break.py) — direct import
- [tests/test_daily_loop_reentry_cap.py](../../../../../../tests/test_daily_loop_reentry_cap.py) — direct import
- [tests/test_daily_loop_reference_adoption.py](../../../../../../tests/test_daily_loop_reference_adoption.py) — direct import
- [tests/test_daily_loop_start_minutes.py](../../../../../../tests/test_daily_loop_start_minutes.py) — direct import
- [tests/test_daily_plan_composition.py](../../../../../../tests/test_daily_plan_composition.py) — direct import
- [tests/test_daily_plan_kill_switch.py](../../../../../../tests/test_daily_plan_kill_switch.py) — direct import
- [tests/test_daily_plan_reading.py](../../../../../../tests/test_daily_plan_reading.py) — direct import
- [tests/test_daily_plan_reentry.py](../../../../../../tests/test_daily_plan_reentry.py) — direct import
- [tests/test_daily_plan_review_regressions.py](../../../../../../tests/test_daily_plan_review_regressions.py) — direct import
- [tests/test_daily_plan_rpc.py](../../../../../../tests/test_daily_plan_rpc.py) — direct import
- [tests/test_data_capture_a1_prefilter.py](../../../../../../tests/test_data_capture_a1_prefilter.py) — direct import
- [tests/test_data_capture_codex_review.py](../../../../../../tests/test_data_capture_codex_review.py) — direct import
- [tests/test_decider_landing.py](../../../../../../tests/test_decider_landing.py) — direct import
- [tests/test_desktop_rpc_contract.py](../../../../../../tests/test_desktop_rpc_contract.py) — direct import
- [tests/test_device_eligibility.py](../../../../../../tests/test_device_eligibility.py) — direct import
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — direct import
- [tests/test_evsi_router_composition.py](../../../../../../tests/test_evsi_router_composition.py) — direct import
- [tests/test_exam_protection_identity.py](../../../../../../tests/test_exam_protection_identity.py) — direct import
- [tests/test_exam_protection_review.py](../../../../../../tests/test_exam_protection_review.py) — direct import
- [tests/test_facet_reword_paths.py](../../../../../../tests/test_facet_reword_paths.py) — direct import
- [tests/test_facet_rewords.py](../../../../../../tests/test_facet_rewords.py) — direct import
- [tests/test_figures_help.py](../../../../../../tests/test_figures_help.py) — direct import
- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
- [tests/test_followup_journey.py](../../../../../../tests/test_followup_journey.py) — direct import
- [tests/test_followup_next_matrix.py](../../../../../../tests/test_followup_next_matrix.py) — direct import
- [tests/test_followup_rival_factor.py](../../../../../../tests/test_followup_rival_factor.py) — direct import
- [tests/test_followups_batch6_verify_fixes.py](../../../../../../tests/test_followups_batch6_verify_fixes.py) — direct import
  - `test_v2_an_offer_from_the_learners_own_question_carries_learner_activity`
- [tests/test_followups_nov2_help_fold.py](../../../../../../tests/test_followups_nov2_help_fold.py) — direct import
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — direct import
- [tests/test_graph_editor_reads.py](../../../../../../tests/test_graph_editor_reads.py) — direct import
- [tests/test_help_assist_work_md_migration.py](../../../../../../tests/test_help_assist_work_md_migration.py) — direct import
- [tests/test_hint_authored_reveal_ruling.py](../../../../../../tests/test_hint_authored_reveal_ruling.py) — direct import
- [tests/test_hint_blind.py](../../../../../../tests/test_hint_blind.py) — direct import
- [tests/test_hint_discriminating.py](../../../../../../tests/test_hint_discriminating.py) — direct import
- [tests/test_hint_evidence.py](../../../../../../tests/test_hint_evidence.py) — direct import
- [tests/test_hint_feedback_texts.py](../../../../../../tests/test_hint_feedback_texts.py) — direct import
- [tests/test_hint_h2a_review.py](../../../../../../tests/test_hint_h2a_review.py) — direct import
- [tests/test_hint_h2a_review_round2.py](../../../../../../tests/test_hint_h2a_review_round2.py) — direct import
- [tests/test_hint_h2a_review_round3.py](../../../../../../tests/test_hint_h2a_review_round3.py) — direct import
- [tests/test_hint_h2b_review.py](../../../../../../tests/test_hint_h2b_review.py) — direct import
- [tests/test_hint_kill_switch.py](../../../../../../tests/test_hint_kill_switch.py) — direct import
- [tests/test_hint_outcome.py](../../../../../../tests/test_hint_outcome.py) — direct import
- [tests/test_hint_report.py](../../../../../../tests/test_hint_report.py) — direct import
- [tests/test_hint_service.py](../../../../../../tests/test_hint_service.py) — direct import
- [tests/test_hint_telemetry.py](../../../../../../tests/test_hint_telemetry.py) — direct import
- [tests/test_host_queue_revision.py](../../../../../../tests/test_host_queue_revision.py) — direct import
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
- [tests/test_integration_daily_loop_field.py](../../../../../../tests/test_integration_daily_loop_field.py) — direct import
- [tests/test_intent_fix_round4.py](../../../../../../tests/test_intent_fix_round4.py) — direct import
- [tests/test_intent_orchestrator_rulings.py](../../../../../../tests/test_intent_orchestrator_rulings.py) — direct import
- [tests/test_intent_rpc.py](../../../../../../tests/test_intent_rpc.py) — direct import
- [tests/test_keep_local_retired.py](../../../../../../tests/test_keep_local_retired.py) — direct import
- [tests/test_learner_pick_proposal.py](../../../../../../tests/test_learner_pick_proposal.py) — direct import
- [tests/test_lp_claim_fixes_review.py](../../../../../../tests/test_lp_claim_fixes_review.py) — direct import
- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
- [tests/test_mobile_handoff.py](../../../../../../tests/test_mobile_handoff.py) — direct import
- [tests/test_mobile_host_auth.py](../../../../../../tests/test_mobile_host_auth.py) — direct import
- [tests/test_mobile_phone_contract.py](../../../../../../tests/test_mobile_phone_contract.py) — direct import
- [tests/test_mobile_rpc.py](../../../../../../tests/test_mobile_rpc.py) — direct import
- [tests/test_mobile_two_process.py](../../../../../../tests/test_mobile_two_process.py) — direct import
- [tests/test_owner_capture_1025.py](../../../../../../tests/test_owner_capture_1025.py) — direct import
- [tests/test_placement_opening_probes.py](../../../../../../tests/test_placement_opening_probes.py) — direct import
- [tests/test_placement_sidecar.py](../../../../../../tests/test_placement_sidecar.py) — direct import
- [tests/test_plan_determinism.py](../../../../../../tests/test_plan_determinism.py) — direct import
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
- [tests/test_plan_first_transport_grant_scope.py](../../../../../../tests/test_plan_first_transport_grant_scope.py) — direct import
- [tests/test_plan_first_transport_offer_grants.py](../../../../../../tests/test_plan_first_transport_offer_grants.py) — direct import
- [tests/test_plan_first_transport_offer_grants_r5.py](../../../../../../tests/test_plan_first_transport_offer_grants_r5.py) — direct import
- [tests/test_plan_first_transport_today_quiet.py](../../../../../../tests/test_plan_first_transport_today_quiet.py) — direct import
- [tests/test_pr4_superseded_claims_landing.py](../../../../../../tests/test_pr4_superseded_claims_landing.py) — direct import
- [tests/test_practice_index_adapters.py](../../../../../../tests/test_practice_index_adapters.py) — direct import
- [tests/test_reader_ca1_as_printed.py](../../../../../../tests/test_reader_ca1_as_printed.py) — direct import
- [tests/test_reader_ca1_astra_codex_review.py](../../../../../../tests/test_reader_ca1_astra_codex_review.py) — direct import
- [tests/test_reader_ca1_astra_fixes.py](../../../../../../tests/test_reader_ca1_astra_fixes.py) — direct import
- [tests/test_reader_ca1_astra_redesign.py](../../../../../../tests/test_reader_ca1_astra_redesign.py) — direct import
- [tests/test_reader_ca1_astra_rereview.py](../../../../../../tests/test_reader_ca1_astra_rereview.py) — direct import
- [tests/test_reader_ca1_codex_review.py](../../../../../../tests/test_reader_ca1_codex_review.py) — direct import
- [tests/test_reader_ca1_unicode_containment.py](../../../../../../tests/test_reader_ca1_unicode_containment.py) — direct import
- [tests/test_reader_ca2_astra_handoff.py](../../../../../../tests/test_reader_ca2_astra_handoff.py) — direct import
- [tests/test_reader_ca2_astra_handoff_recovery.py](../../../../../../tests/test_reader_ca2_astra_handoff_recovery.py) — direct import
- [tests/test_reader_ca2_codex_rereview.py](../../../../../../tests/test_reader_ca2_codex_rereview.py) — direct import
- [tests/test_reader_ca2_codex_review.py](../../../../../../tests/test_reader_ca2_codex_review.py) — direct import
- [tests/test_reader_ca2_fix_orchestrator.py](../../../../../../tests/test_reader_ca2_fix_orchestrator.py) — direct import
- [tests/test_reader_ca2_one_ask.py](../../../../../../tests/test_reader_ca2_one_ask.py) — direct import
- [tests/test_reader_followups_successor.py](../../../../../../tests/test_reader_followups_successor.py) — direct import
- [tests/test_reader_rw3a_landing.py](../../../../../../tests/test_reader_rw3a_landing.py) — direct import
- [tests/test_reader_workbench_rw2a.py](../../../../../../tests/test_reader_workbench_rw2a.py) — direct import
- [tests/test_reader_wrap_up.py](../../../../../../tests/test_reader_wrap_up.py) — direct import
- [tests/test_regrade_contract_replay.py](../../../../../../tests/test_regrade_contract_replay.py) — direct import
- [tests/test_regrade_contract_successor.py](../../../../../../tests/test_regrade_contract_successor.py) — direct import
- [tests/test_request_origin.py](../../../../../../tests/test_request_origin.py) — direct import
- [tests/test_required_method_round3_review.py](../../../../../../tests/test_required_method_round3_review.py) — direct import
- [tests/test_reread_safety.py](../../../../../../tests/test_reread_safety.py) — direct import
- [tests/test_reread_safety_landing.py](../../../../../../tests/test_reread_safety_landing.py) — direct import
- [tests/test_ro0_codex_review.py](../../../../../../tests/test_ro0_codex_review.py) — direct import
- [tests/test_ro0_gate.py](../../../../../../tests/test_ro0_gate.py) — direct import
- [tests/test_ro0_rows7_8_sessions.py](../../../../../../tests/test_ro0_rows7_8_sessions.py) — direct import
- [tests/test_ro4_goals.py](../../../../../../tests/test_ro4_goals.py) — direct import
- [tests/test_router_offer_log.py](../../../../../../tests/test_router_offer_log.py) — direct import
- [tests/test_router_outcomes.py](../../../../../../tests/test_router_outcomes.py) — direct import
- [tests/test_router_p2_bridge.py](../../../../../../tests/test_router_p2_bridge.py) — direct import
- [tests/test_router_probe_ties.py](../../../../../../tests/test_router_probe_ties.py) — direct import
- [tests/test_router_r1_composition.py](../../../../../../tests/test_router_r1_composition.py) — direct import
- [tests/test_router_r2a_serving.py](../../../../../../tests/test_router_r2a_serving.py) — direct import
- [tests/test_router_r2b_serving.py](../../../../../../tests/test_router_r2b_serving.py) — direct import
- [tests/test_serve_eligibility_review.py](../../../../../../tests/test_serve_eligibility_review.py) — direct import
- [tests/test_session_ownership.py](../../../../../../tests/test_session_ownership.py) — direct import
- [tests/test_sidecar_adjudication.py](../../../../../../tests/test_sidecar_adjudication.py) — direct import
- [tests/test_sidecar_exams.py](../../../../../../tests/test_sidecar_exams.py) — direct import
- [tests/test_sidecar_goals.py](../../../../../../tests/test_sidecar_goals.py) — direct import
- [tests/test_sidecar_item_presentation.py](../../../../../../tests/test_sidecar_item_presentation.py) — direct import
- [tests/test_sidecar_measurement.py](../../../../../../tests/test_sidecar_measurement.py) — direct import
- [tests/test_sidecar_trace_and_clarification.py](../../../../../../tests/test_sidecar_trace_and_clarification.py) — direct import
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — direct import
- [tests/test_teacher_te2_sidecar.py](../../../../../../tests/test_teacher_te2_sidecar.py) — direct import
- [tests/test_teacher_te2log_activity.py](../../../../../../tests/test_teacher_te2log_activity.py) — direct import
- [tests/test_ux_phase1_add_source.py](../../../../../../tests/test_ux_phase1_add_source.py) — direct import
- [tests/test_ux_phase1_connect_ai.py](../../../../../../tests/test_ux_phase1_connect_ai.py) — direct import
- [tests/test_ux_phase1_review_fixes.py](../../../../../../tests/test_ux_phase1_review_fixes.py) — direct import
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
- [tests/test_ux_phase4_landing.py](../../../../../../tests/test_ux_phase4_landing.py) — direct import
- [tests/test_voi_merge_composition.py](../../../../../../tests/test_voi_merge_composition.py) — direct import
- [tests/test_voi_stopping.py](../../../../../../tests/test_voi_stopping.py) — direct import
- [tests/workbench_help_fakes.py](../../../../../../tests/workbench_help_fakes.py) — direct import

## Modification guidance

- Change this file when intentionally adding or removing a package-level re-export; keep implementation logic in the owning module.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/__init__.py](../../../../../../src/learnloop_sidecar/handlers/__init__.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
