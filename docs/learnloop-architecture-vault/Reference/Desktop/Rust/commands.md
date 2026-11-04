---
title: "Desktop module · src-tauri/src/commands.rs"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src-tauri.src.commands"
language: "Rust"
area: "Rust"
source_path: "apps/learnloop-tauri/src-tauri/src/commands.rs"
source_paths:
  - "apps/learnloop-tauri/src-tauri/src/commands.rs"
source_commit: "e262b85b96108b93ffda0fb5bf84527952b7c3e2"
source_commit_timestamp: "2026-11-03T22:37:18-05:00"
source_worktree_state: "staged-or-mixed"
activation_kind: "native-entry-reachable"
activation_evidence: "A Rust mod/use edge reaches this crate module from src-tauri/src/main.rs."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/rust"
  - "refactor/active"
---

# `src-tauri/src/commands.rs`

Area: [[Reference/Desktop/Rust/_area|Rust]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the native command boundary, adapting Tauri invocations to typed JSON-RPC calls on the Python sidecar.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src-tauri/src/commands.rs](../../../../../apps/learnloop-tauri/src-tauri/src/commands.rs) |
| Source lines | 1566 |
| Language | `Rust` |
| Area | [[Reference/Desktop/Rust/_area|Rust]] |
| Refactor status | `ACTIVE` |
| Activation kind | `native-entry-reachable` |
| Worktree state | `staged-or-mixed` |
| Source commit | `e262b85b96108b93ffda0fb5bf84527952b7c3e2` |
| Commit timestamp | `2026-11-03T22:37:18-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A Rust mod/use edge reaches this crate module from src-tauri/src/main.rs.
>
> Build/entry chain: [[Reference/Desktop/Rust/main|src-tauri/src/main.rs]] → [[Reference/Desktop/Rust/commands|src-tauri/src/commands.rs]]

## Public API

- `pub async fn select_vault( path: Option<String>, sidecar: State<'_, SidecarManager>, watcher: State<'_, VaultWatcher>, ) -> Result<Value, CommandError>` — fn, line 78
- `pub async fn load_vault( sidecar: State<'_, SidecarManager>, watcher: State<'_, VaultWatcher>, ) -> Result<Value, CommandError>` — fn, line 90
- `pub async fn reload_vault(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 101
- `pub async fn create_vault(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 105; macro-expanded
- `pub async fn get_learner_profile( sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 108
- `pub async fn set_learner_profile(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 114; macro-expanded
- `pub async fn get_runtime_health(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 117
- `pub async fn get_config(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 122
- `pub async fn start_session(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 126; macro-expanded
- `pub async fn adopt_session(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 127; macro-expanded
- `pub async fn get_start_summary(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 130
- `pub async fn get_session( session_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 135
- `pub async fn update_session_checkpoint(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 142; macro-expanded
- `pub async fn clear_session_checkpoint( session_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 145
- `pub async fn end_session( session_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 158
- `pub async fn get_today_queue(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 165; macro-expanded
- `pub async fn get_queue_revision(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 167; macro-expanded
- `pub async fn explain_practice_item( practice_item_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 170
- `pub async fn open_queue_item( practice_item_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 183
- `pub async fn get_practice_item( practice_item_id: String, session_id: Option<String>, proposal_id: Option<String>, source_exercise_import_id: Option<String>, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 196
- `pub async fn get_probe_contract( practice_item_id: String, session_id: Option<String>, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 219
- `pub async fn stop_probe_diagnosing( practice_item_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 233
- `pub async fn get_next_probe_item( learning_object_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 246
- `pub async fn save_practice_draft(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 258; macro-expanded
- `pub async fn practice_record_hint_reveal(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 261; macro-expanded
- `pub async fn practice_request_hint(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 266; macro-expanded
- `pub async fn practice_hint_job(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 267; macro-expanded
- `pub async fn practice_cancel_hint(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 268; macro-expanded
- `pub async fn practice_answer_discriminating(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 269; macro-expanded
- `pub async fn practice_set_help_style(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 270; macro-expanded
- `pub async fn recover_practice_submission(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 272; macro-expanded
- `pub async fn acknowledge_practice_submission(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 274; macro-expanded
- `pub async fn submit_attempt(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 279; macro-expanded
- `pub async fn submit_dont_know(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 281; macro-expanded
- `pub async fn skip_practice_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 283; macro-expanded
- `pub async fn followup_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 286; macro-expanded
- `pub async fn followup_next(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 287; macro-expanded
- `pub async fn followup_continue_without(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 288; macro-expanded
- `pub async fn followup_show_anyway(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 289; macro-expanded
- `pub async fn record_hypothesis_exposure(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 290; macro-expanded
- `pub async fn record_hypothesis_mark(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 291; macro-expanded
- `pub async fn get_feedback( attempt_id: String, record_open: Option<bool>, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 294
- `pub async fn get_attempt( attempt_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 310
- `pub async fn get_attempt_trace_evidence( attempt_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 318
- `pub async fn get_grading_clarification( attempt_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 331
- `pub async fn answer_grading_clarification(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 343; macro-expanded
- `pub async fn inspect_entity( id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 346
- `pub async fn get_concept_graph(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 354
- `pub async fn get_vault_tree(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 359
- `pub async fn get_recent_ingests(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 364
- `pub async fn classify_ingest_source(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 368; macro-expanded
- `pub async fn start_ingest(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 370; macro-expanded
- `pub async fn get_ingest_job( job_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 373
- `pub async fn get_ingest_jobs(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 381
- `pub async fn cancel_ingest( job_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 386
- `pub async fn start_import_batch(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 393; macro-expanded
- `pub async fn get_ingest_batch( batch_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 396
- `pub async fn list_ingest_batches(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 403; macro-expanded
- `pub async fn cancel_ingest_batch( batch_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 406
- `pub async fn resume_ingest_batch( batch_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 414
- `pub async fn retry_synthesis(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 421; macro-expanded
- `pub async fn get_synthesis_candidate( batch_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 424
- `pub async fn get_source_library(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 437
- `pub async fn preview_source_deletion( source_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 442
- `pub async fn delete_source( source_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 455
- `pub async fn get_source_outline( extraction_ref: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 465
- `pub async fn get_selection_preview(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 477; macro-expanded
- `pub async fn get_effective_outline(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 479; macro-expanded
- `pub async fn save_unit_selection(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 481; macro-expanded
- `pub async fn get_acquisition_preview(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 483; macro-expanded
- `pub async fn get_build_plan(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 485; macro-expanded
- `pub async fn list_source_sets(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 488
- `pub async fn get_source_set( source_set_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 493
- `pub async fn upsert_source_set(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 505; macro-expanded
- `pub async fn get_source_coverage( source_set_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 508
- `pub async fn start_inventory(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 520; macro-expanded
- `pub async fn create_study_map(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 522; macro-expanded
- `pub async fn build_study_map(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 524; macro-expanded
- `pub async fn append_source(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 526; macro-expanded
- `pub async fn refresh_revision(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 528; macro-expanded
- `pub async fn maintenance_feed(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 530; macro-expanded
- `pub async fn get_measurement_health( sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 533
- `pub async fn generate_commissioning_practice(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 542; macro-expanded
- `pub async fn get_review_counts(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 550
- `pub async fn schedule_certification_cold_probes(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 554; macro-expanded
- `pub async fn transition_causal_probe_candidate(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 559; macro-expanded
- `pub async fn apply_integration_backfill(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 564; macro-expanded
- `pub async fn maintenance_notice_action(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 566; macro-expanded
- `pub async fn list_source_conflicts(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 568; macro-expanded
- `pub async fn resolve_source_conflict(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 570; macro-expanded
- `pub async fn exam_readiness(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 572; macro-expanded
- `pub async fn start_extraction_repair(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 574; macro-expanded
- `pub async fn read_vault_file( path: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 577
- `pub async fn write_vault_file( path: String, body: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 585
- `pub async fn create_vault_file(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 598; macro-expanded
- `pub async fn sqlite_tables(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 600; macro-expanded
- `pub async fn sqlite_table(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 602; macro-expanded
- `pub async fn sqlite_exec(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 604; macro-expanded
- `pub async fn sqlite_update_cell(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 606; macro-expanded
- `pub async fn sqlite_insert_row(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 608; macro-expanded
- `pub async fn sqlite_delete_row(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 610; macro-expanded
- `pub async fn get_proposals(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 613
- `pub async fn get_entity_provenance( entity_type: String, entity_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 618
- `pub async fn plan_quick_add(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 631; macro-expanded
- `pub async fn get_inbox_summary(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 633; macro-expanded
- `pub async fn list_capture_inbox(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 634; macro-expanded
- `pub async fn dismiss_capture(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 635; macro-expanded
- `pub async fn purge_capture(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 636; macro-expanded
- `pub async fn resume_capture_route(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 637; macro-expanded
- `pub async fn get_capture_media(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 638; macro-expanded
- `pub async fn confirm_quick_add(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 640; macro-expanded
- `pub async fn get_span_view(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 642; macro-expanded
- `pub async fn get_subject_registry(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 644; macro-expanded
- `pub async fn propose_facet_merge(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 646; macro-expanded
- `pub async fn list_facet_identity_actions(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 648; macro-expanded
- `pub async fn undo_facet_identity_action(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 650; macro-expanded
- `pub async fn decide_facet_reword(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 652; macro-expanded
- `pub async fn accept_proposal_items(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 654; macro-expanded
- `pub async fn reject_proposal_items(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 656; macro-expanded
- `pub async fn reset_proposal_items(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 658; macro-expanded
- `pub async fn edit_proposal_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 660; macro-expanded
- `pub async fn refresh_proposal_item_validation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 662; macro-expanded
- `pub async fn delete_proposal_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 667; macro-expanded
- `pub async fn trigger_regrade(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 669; macro-expanded
- `pub async fn record_answer_display(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 672; macro-expanded
- `pub async fn record_self_grade_disclosure(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 673; macro-expanded
- `pub async fn add_error_event(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 675; macro-expanded
- `pub async fn trigger_followup(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 677; macro-expanded
- `pub async fn rate_followup(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 679; macro-expanded
- `pub async fn report_unresolved_cause(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 681; macro-expanded
- `pub async fn submit_eliciting_response(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 683; macro-expanded
- `pub async fn contest_causal_diagnosis(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 685; macro-expanded
- `pub async fn diagnosis_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 691; macro-expanded
- `pub async fn record_diagnosis_feedback(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 693; macro-expanded
- `pub async fn causal_repair_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 701; macro-expanded
- `pub async fn causal_probe_offer_action(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 703; macro-expanded
- `pub async fn causal_probe_defer(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 705; macro-expanded
- `pub async fn causal_teach_me_now(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 707; macro-expanded
- `pub async fn start_primed_retry(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 709; macro-expanded
- `pub async fn start_guided_redo(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 711; macro-expanded
- `pub async fn run_cli_command( input: Value, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 714
- `pub async fn get_facet_mastery(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 726
- `pub async fn get_knowledge_map(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 731
- `pub async fn get_attempt_trace( attempt_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 738
- `pub async fn get_capability_grid( learning_object_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 751
- `pub async fn get_facet_evidence_timeline( facet_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 764
- `pub async fn get_knowledge_map_history( sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 777
- `pub async fn set_grading_provider( provider: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 784
- `pub async fn get_settings(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 797
- `pub async fn update_ai_settings(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 801; macro-expanded
- `pub async fn set_openrouter_api_key( api_key: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 804
- `pub async fn update_ingest_settings(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 816; macro-expanded
- `pub async fn chatgpt_plan_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 817; macro-expanded
- `pub async fn add_source(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 819; macro-expanded
- `pub async fn get_ai_connection(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 820; macro-expanded
- `pub async fn connect_ai(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 821; macro-expanded
- `pub async fn source_action(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 822; macro-expanded
- `pub async fn chatgpt_plan_signin_start(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 823; macro-expanded
- `pub async fn chatgpt_plan_signin_cancel(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 824; macro-expanded
- `pub async fn chatgpt_plan_signout(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 825; macro-expanded
- `pub async fn chatgpt_plan_acknowledge_welcome(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 826; macro-expanded
- `pub async fn chatgpt_plan_resume(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 827; macro-expanded
- `pub async fn ai_use_fallback(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 829; macro-expanded
- `pub async fn detect_provider_capabilities(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 830; macro-expanded
- `pub async fn update_provider_modalities(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 831; macro-expanded
- `pub async fn set_transcription_api_key( api_key: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 834
- `pub async fn set_text_recognition_api_key( api_key: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 847
- `pub async fn get_animation_runtime( sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 860
- `pub async fn update_animation_settings(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 866; macro-expanded
- `pub async fn request_concept_animation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 867; macro-expanded
- `pub async fn get_concept_animation_status( animation_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 870
- `pub async fn list_concept_animations( concept_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 883
- `pub async fn ask_tutor_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 895; macro-expanded
- `pub async fn get_learner_text_gap(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 896; macro-expanded
- `pub async fn reverse_learner_text_gap(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 897; macro-expanded
- `pub async fn preview_tutor_opening(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 899; macro-expanded
- `pub async fn rate_tutor_answer(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 901; macro-expanded
- `pub async fn save_tutor_answer_note(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 903; macro-expanded
- `pub async fn get_tutor_transcript(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 905; macro-expanded
- `pub async fn promote_tutor_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 907; macro-expanded
- `pub async fn author_practice_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 909; macro-expanded
- `pub async fn request_rung_variant(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 911; macro-expanded
- `pub async fn get_rung_variant_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 913; macro-expanded
- `pub async fn remint_diagnostic_probe(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 915; macro-expanded
- `pub async fn edit_practice_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 917; macro-expanded
- `pub async fn retire_practice_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 919; macro-expanded
- `pub async fn split_practice_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 921; macro-expanded
- `pub async fn list_question_queue(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 923; macro-expanded
- `pub async fn resolve_question_event(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 925; macro-expanded
- `pub async fn request_teach_back(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 927; macro-expanded
- `pub async fn start_teach_back(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 929; macro-expanded
- `pub async fn submit_teach_back_turn(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 931; macro-expanded
- `pub async fn goals_list(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 934
- `pub async fn get_goal_report( goal_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 939
- `pub async fn get_goal_report_series(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 946; macro-expanded
- `pub async fn goal_feasibility(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 948; macro-expanded
- `pub async fn get_overconfidence_list( goal_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 951
- `pub async fn get_reentry_summary(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 963; macro-expanded
- `pub async fn get_decay_pressure(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 965; macro-expanded
- `pub async fn start_overconfidence_probe(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 967; macro-expanded
- `pub async fn create_goal(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 969; macro-expanded
- `pub async fn generate_starter_practice(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 971; macro-expanded
- `pub async fn update_goal_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 973; macro-expanded
- `pub async fn update_goal_intent(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 975; macro-expanded
- `pub async fn get_exam_status( goal_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 978
- `pub async fn start_exam(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 985; macro-expanded
- `pub async fn submit_exam_answer(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 987; macro-expanded
- `pub async fn start_calibration_session(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 989; macro-expanded
- `pub async fn placement_self_report(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 991; macro-expanded
- `pub async fn get_placement_state(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 993; macro-expanded
- `pub async fn start_quick_check(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 995; macro-expanded
- `pub async fn get_daily_plan(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 998; macro-expanded
- `pub async fn set_plan_minutes(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1000; macro-expanded
- `pub async fn next_plan_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1002; macro-expanded
- `pub async fn plan_reading_ended(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1004; macro-expanded
- `pub async fn plan_keep_going(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1006; macro-expanded
- `pub async fn plan_more_new(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1008; macro-expanded
- `pub async fn plan_learner_pick(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1010; macro-expanded
- `pub async fn find_practice(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1014; macro-expanded
- `pub async fn record_practice_usage(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1015; macro-expanded
- `pub async fn record_proposal_impressions(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1016; macro-expanded
- `pub async fn import_source_exercise(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1017; macro-expanded
- `pub async fn get_source_exercise_import(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1018; macro-expanded
- `pub async fn run_source_tool(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1019; macro-expanded
- `pub async fn record_source_offer_shown(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1020; macro-expanded
- `pub async fn find_sources(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1021; macro-expanded
- `pub async fn compare_sources(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1022; macro-expanded
- `pub async fn get_today_headline(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1024; macro-expanded
- `pub async fn get_intent(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1027; macro-expanded
- `pub async fn set_intent(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1029; macro-expanded
- `pub async fn set_intent_deadline(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1031; macro-expanded
- `pub async fn get_calibration_session( calibration_session_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1034
- `pub async fn stop_calibration_session( calibration_session_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1047
- `pub async fn finish_exam(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1059; macro-expanded
- `pub async fn begin_probe_dialogue( learning_object_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1062
- `pub async fn next_probe_dialogue_turn( dialogue_state: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1075
- `pub async fn record_probe_dialogue_turn( dialogue_state: String, presentation_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1088
- `pub async fn end_probe_dialogue( dialogue_state: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1102
- `pub async fn present_claims(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1114; macro-expanded
- `pub async fn respond_claim(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1116; macro-expanded
- `pub async fn dismiss_claim( presentation_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1119
- `pub async fn export_claims(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 1132
- `pub async fn purge_claims(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 1137
- `pub async fn get_review_log(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 1142
- `pub async fn start_remediation( misconception_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1147
- `pub async fn prescribe_remediation( episode_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1160
- `pub async fn start_remediation_treatment( episode_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1173
- `pub async fn get_remediation( episode_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1186
- `pub async fn get_forecast_track_record(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1193; macro-expanded
- `pub async fn get_answer_calibration( sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1196
- `pub async fn propose_graph_edits(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1202; macro-expanded
- `pub async fn queue_restructure_request(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1204; macro-expanded
- `pub async fn resolve_edge_direction(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1206; macro-expanded
- `pub async fn get_facet_detail( facet_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1209
- `pub async fn list_facets(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 1217
- `pub async fn preview_knowledge_map(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1221; macro-expanded
- `pub async fn preview_blueprint_readiness(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1223; macro-expanded
- `pub async fn blueprint_register(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1231; macro-expanded
- `pub async fn blueprint_review(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1232; macro-expanded
- `pub async fn blueprint_get_version(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1233; macro-expanded
- `pub async fn blueprint_discover_candidates(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1234; macro-expanded
- `pub async fn blueprint_compose_draft(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1238; macro-expanded
- `pub async fn golden_path_confirm(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1241; macro-expanded
- `pub async fn golden_path_run_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1242; macro-expanded
- `pub async fn golden_path_list_runs(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1243; macro-expanded
- `pub async fn golden_path_advance(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1244; macro-expanded
- `pub async fn golden_path_assess_open(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1247; macro-expanded
- `pub async fn golden_path_assess_submit(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1248; macro-expanded
- `pub async fn golden_path_assess_result(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1249; macro-expanded
- `pub async fn golden_path_restore(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1250; macro-expanded
- `pub async fn golden_path_boundary_diff(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1251; macro-expanded
- `pub async fn golden_path_depth_invitation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1252; macro-expanded
- `pub async fn golden_path_accept_edge(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1253; macro-expanded
- `pub async fn golden_path_decline_edge(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1254; macro-expanded
- `pub async fn diagnostic_pack_assemble(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1257; macro-expanded
- `pub async fn diagnostic_pack_admit(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1258; macro-expanded
- `pub async fn diagnostic_pack_review(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1259; macro-expanded
- `pub async fn diagnostic_pack_list(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1260; macro-expanded
- `pub async fn diagnostic_baseline_enter(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1261; macro-expanded
- `pub async fn diagnostic_boundary_view(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1262; macro-expanded
- `pub async fn diagnostic_triage(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1263; macro-expanded
- `pub async fn diagnostic_triage_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1264; macro-expanded
- `pub async fn diagnostic_triage_decide(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1265; macro-expanded
- `pub async fn diagnostic_triage_override(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1266; macro-expanded
- `pub async fn ladder_policy(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1269; macro-expanded
- `pub async fn ladder_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1270; macro-expanded
- `pub async fn ladder_enter(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1271; macro-expanded
- `pub async fn ladder_advance(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1272; macro-expanded
- `pub async fn practice_pool_assemble(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1273; macro-expanded
- `pub async fn practice_pool_admit_surface(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1274; macro-expanded
- `pub async fn practice_pool_review(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1275; macro-expanded
- `pub async fn practice_pool_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1276; macro-expanded
- `pub async fn practice_pool_next_surface(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1277; macro-expanded
- `pub async fn practice_pool_for_run(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1278; macro-expanded
- `pub async fn practice_pool_seed_for_run(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1279; macro-expanded
- `pub async fn practice_pool_admit_anchor(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1280; macro-expanded
- `pub async fn adjudication_queue(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1285; macro-expanded
- `pub async fn adjudication_record(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1286; macro-expanded
- `pub async fn adjudication_scoreboard(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1287; macro-expanded
- `pub async fn reader_ask(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1290; macro-expanded
- `pub async fn reader_ask_history(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1291; macro-expanded
- `pub async fn reader_set_answer_mode(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1292; macro-expanded
- `pub async fn reader_present_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1293; macro-expanded
- `pub async fn reader_submit_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1294; macro-expanded
- `pub async fn reader_skip_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1295; macro-expanded
- `pub async fn reader_choose_disposition(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1296; macro-expanded
- `pub async fn reader_restore_source(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1297; macro-expanded
- `pub async fn reader_routing_prior(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1298; macro-expanded
- `pub async fn reader_prompt_contract(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1299; macro-expanded
- `pub async fn reader_render_view(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1301; macro-expanded
- `pub async fn reader_guide_plan(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1302; macro-expanded
- `pub async fn reader_saved_place(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1303; macro-expanded
- `pub async fn reader_pdf_view(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1304; macro-expanded
- `pub async fn reader_watch_plan(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1305; macro-expanded
- `pub async fn reader_author_section_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1306; macro-expanded
- `pub async fn reader_authored_question_action(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1310; macro-expanded
- `pub async fn reader_get_progress(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1314; macro-expanded
- `pub async fn reader_mark_section_progress(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1315; macro-expanded
- `pub async fn reader_escalate_authored_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1316; macro-expanded
- `pub async fn reader_import_exercise(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1320; macro-expanded
- `pub async fn reader_exercise_import_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1321; macro-expanded
- `pub async fn reader_search_sources(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1325; macro-expanded
- `pub async fn reader_retrieval_open(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1327; macro-expanded
- `pub async fn reader_span_learning_objects(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1328; macro-expanded
- `pub async fn reader_manual_anchor(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1329; macro-expanded
- `pub async fn reader_set_inquiry_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1332; macro-expanded
- `pub async fn reader_reconnect_answer(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1333; macro-expanded
- `pub async fn reader_inquiry_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1334; macro-expanded
- `pub async fn reader_inquiry_question_action(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1335; macro-expanded
- `pub async fn reader_log_activity(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1336; macro-expanded
- `pub async fn reader_cue_action(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1338; macro-expanded
- `pub async fn reader_cue_preferences(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1339; macro-expanded
- `pub async fn reader_set_cue_preferences(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1340; macro-expanded
- `pub async fn reader_cue_discovery(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1342; macro-expanded
- `pub async fn reader_cue_discovery_job(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1343; macro-expanded
- `pub async fn reader_cue_impressions(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1344; macro-expanded
- `pub async fn reader_cue_tap(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1345; macro-expanded
- `pub async fn workbench_open(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1347; macro-expanded
- `pub async fn workbench_get(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1348; macro-expanded
- `pub async fn workbench_save_step(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1349; macro-expanded
- `pub async fn workbench_set_book(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1350; macro-expanded
- `pub async fn workbench_leave(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1351; macro-expanded
- `pub async fn workbench_abandon(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1352; macro-expanded
- `pub async fn workbench_reopen(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1353; macro-expanded
- `pub async fn workbench_refresh_import(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1354; macro-expanded
- `pub async fn workbench_bind(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1355; macro-expanded
- `pub async fn workbench_retry_import(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1356; macro-expanded
- `pub async fn workbench_admit(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1358; macro-expanded
- `pub async fn workbench_submit(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1359; macro-expanded
- `pub async fn workbench_session_for_attempt(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1360; macro-expanded
- `pub async fn workbench_for_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1361; macro-expanded
- `pub async fn workbench_for_source(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1362; macro-expanded
- `pub async fn workbench_open_problems(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1364; macro-expanded
- `pub async fn workbench_check(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1366; macro-expanded
- `pub async fn workbench_suggest_help(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1367; macro-expanded
- `pub async fn workbench_request_help(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1368; macro-expanded
- `pub async fn workbench_help_job(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1369; macro-expanded
- `pub async fn workbench_cancel_help(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1370; macro-expanded
- `pub async fn workbench_answer_discriminating(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1371; macro-expanded
- `pub async fn workbench_set_help_style(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1372; macro-expanded
- `pub async fn workbench_help_state(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1373; macro-expanded
- `pub async fn workbench_show_example(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1375; macro-expanded
- `pub async fn workbench_another_passage(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1376; macro-expanded
- `pub async fn workbench_compare_offer(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1377; macro-expanded
- `pub async fn workbench_compare_methods(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1378; macro-expanded
- `pub async fn reader_recap(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1380; macro-expanded
- `pub async fn reader_recap_event(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1381; macro-expanded
- `pub async fn reader_wrap_up(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1382; macro-expanded
- `pub async fn reader_wrap_up_offer(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1383; macro-expanded
- `pub async fn reader_followups(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1385; macro-expanded
- `pub async fn reader_followup_undo(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1386; macro-expanded
- `pub async fn reader_followup_undo_all(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1387; macro-expanded
- `pub async fn reader_followup_restore(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1388; macro-expanded
- `pub async fn reader_route_intent(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1390; macro-expanded
- `pub async fn reader_intent_routing(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1391; macro-expanded
- `pub async fn reader_intent_outcome(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1392; macro-expanded
- `pub async fn reader_active_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1393; macro-expanded
- `pub async fn reader_active_question_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1394; macro-expanded
- `pub async fn reader_active_question_action(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1395; macro-expanded
- `pub async fn reader_reconstruct(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1396; macro-expanded
- `pub async fn reader_reconstruct_undo(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1397; macro-expanded
- `pub async fn reader_library_ask(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1399; macro-expanded
- `pub async fn reader_library_ask_notes(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1400; macro-expanded
- `pub async fn reader_library_compare(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1401; macro-expanded
- `pub async fn reader_library_ask_tutor(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1402; macro-expanded
- `pub async fn reader_library_job(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1403; macro-expanded
- `pub async fn reader_library_job_cancel(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1404; macro-expanded
- `pub async fn reader_compare_scope(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1406; macro-expanded
- `pub async fn reader_compare_scope_correction(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1407; macro-expanded
- `pub async fn reader_exercise_candidates(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1409; macro-expanded
- `pub async fn reader_find_exercises(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1410; macro-expanded
- `pub async fn reader_library_compare_keep(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1412; macro-expanded
- `pub async fn reader_library_compare_remove(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1413; macro-expanded
- `pub async fn reader_library_compare_reopen(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1414; macro-expanded
- `pub async fn reader_kept_comparisons(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1415; macro-expanded
- `pub async fn reader_reading_path(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1417; macro-expanded
- `pub async fn reader_reading_path_set_depth(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1418; macro-expanded
- `pub async fn reader_reading_path_override(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1419; macro-expanded
- `pub async fn reader_correspondents(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1422; macro-expanded
- `pub async fn curriculum_coverage_correct(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1423; macro-expanded
- `pub async fn reader_correspondent_peek(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1424; macro-expanded
- `pub async fn reader_correspondent_dismiss(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1425; macro-expanded
- `pub async fn reader_correspondence_preferences(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1427; macro-expanded
- `pub async fn reader_set_correspondence_preferences(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1428; macro-expanded
- `pub async fn curriculum_deliverables(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1431; macro-expanded
- `pub async fn curriculum_create_deliverable(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1432; macro-expanded
- `pub async fn curriculum_set_scope(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1433; macro-expanded
- `pub async fn curriculum_scope(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1434; macro-expanded
- `pub async fn curriculum_scope_decide(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1435; macro-expanded
- `pub async fn curriculum_set_depth(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1436; macro-expanded
- `pub async fn curriculum_path(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1437; macro-expanded
- `pub async fn curriculum_guide_slice(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1438; macro-expanded
- `pub async fn curriculum_path_override(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1439; macro-expanded
- `pub async fn curriculum_ready(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1440; macro-expanded
- `pub async fn curriculum_ready_check(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1441; macro-expanded
- `pub async fn curriculum_also_about(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1442; macro-expanded
- `pub async fn notes_path(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1444; macro-expanded
- `pub async fn notes_marks(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1445; macro-expanded
- `pub async fn notes_passages(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1446; macro-expanded
- `pub async fn notes_search(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1447; macro-expanded
- `pub async fn notes_link(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1448; macro-expanded
- `pub async fn notes_decide(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1449; macro-expanded
- `pub async fn notes_hidden(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1450; macro-expanded
- `pub async fn notes_set_gaps(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1452; macro-expanded
- `pub async fn lesson_turn(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1454; macro-expanded
- `pub async fn lesson_view(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1455; macro-expanded
- `pub async fn lesson_suggestion(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1457; macro-expanded
- `pub async fn lesson_suggestion_respond(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1458; macro-expanded
- `pub async fn reader_side_by_side_section(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1460; macro-expanded
- `pub async fn reader_figure_request(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1463; macro-expanded
- `pub async fn figure_request(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1465; macro-expanded
- `pub async fn figure_rich_cancel(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1467; macro-expanded
- `pub async fn figure_rich_retry(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1469; macro-expanded
- `pub async fn figure_manim_opt_in(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1470; macro-expanded
- `pub async fn figure_take_step(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1473; macro-expanded
- `pub async fn figure_open(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1474; macro-expanded
- `pub async fn reader_figure_revise(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1475; macro-expanded
- `pub async fn reader_figure_recheck(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1476; macro-expanded
- `pub async fn reader_figure_job(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1477; macro-expanded
- `pub async fn reader_figure_job_cancel(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1478; macro-expanded
- `pub async fn reader_figures(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1479; macro-expanded
- `pub async fn reader_figure_predict(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1480; macro-expanded
- `pub async fn reader_figure_explain(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1481; macro-expanded
- `pub async fn reader_dose_offer(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1484; macro-expanded
- `pub async fn reader_dose_offer_event(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1485; macro-expanded
- `pub async fn adaptive_difficulty_readiness(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1486; macro-expanded
- `pub async fn adaptive_difficulty_why_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1487; macro-expanded
- `pub async fn reader_block_health(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1488; macro-expanded
- `pub async fn reader_block_original_region(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1489; macro-expanded
- `pub async fn practice_as_printed(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1492; macro-expanded
- `pub async fn practice_report_transcription(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1493; macro-expanded
- `pub async fn reader_translate_selection(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1494; macro-expanded
- `pub async fn reader_capture(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1495; macro-expanded
- `pub async fn reader_create_annotation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1496; macro-expanded
- `pub async fn reader_edit_annotation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1497; macro-expanded
- `pub async fn reader_delete_intent_annotation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1498; macro-expanded
- `pub async fn reader_restore_annotation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1503; macro-expanded
- `pub async fn reader_reanchor(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1504; macro-expanded
- `pub async fn reader_annotation_history(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1505; macro-expanded
- `pub async fn reader_source_annotations(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1506; macro-expanded
- `pub async fn reader_outbox_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1507; macro-expanded
- `pub async fn reader_drain_outbox(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1508; macro-expanded
- `pub async fn reader_invoke_preset(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1510; macro-expanded
- `pub async fn reader_set_mode(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1511; macro-expanded
- `pub async fn reader_question_control(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1512; macro-expanded
- `pub async fn reader_enqueue_request(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1513; macro-expanded
- `pub async fn reader_request_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1514; macro-expanded
- `pub async fn reader_cancel_request(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1515; macro-expanded
- `pub async fn reader_retry_request(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1516; macro-expanded
- `pub async fn reader_source_requests(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1517; macro-expanded
- `pub async fn reader_drain_requests(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1518; macro-expanded
- `pub async fn reader_source_objects(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1519; macro-expanded
- `pub async fn reader_review_source_object(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1520; macro-expanded
- `pub async fn reader_link_relation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1521; macro-expanded
- `pub async fn reader_proposal_inbox(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1522; macro-expanded
- `pub async fn reader_accept_proposal(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1523; macro-expanded
- `pub async fn reader_reject_proposal(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1524; macro-expanded
- `pub async fn reader_author_qa(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1526; macro-expanded
- `pub async fn reader_coach_lint(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1527; macro-expanded
- `pub async fn reader_maintain(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1528; macro-expanded
- `pub async fn reader_arc(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1529; macro-expanded
- `pub async fn reader_set_depth_policy(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1530; macro-expanded
- `pub async fn reader_pause_arc(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1531; macro-expanded
- `pub async fn reader_shrink_envelope(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1532; macro-expanded
- `pub async fn reader_prime(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1533; macro-expanded
- `pub async fn reader_restore(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1534; macro-expanded

## Internal implementation anchors

- `async fn run_sidecar_task( sidecar: State<'_, SidecarManager>, operation: impl FnOnce(SidecarManager) -> Result<Value, CommandError> + Send + 'static, ) -> Result<Value, CommandError>` — fn, line 7
- `async fn blocking_sidecar_call( sidecar: State<'_, SidecarManager>, method: &'static str, params: Value, ) -> Result<Value, CommandError>` — fn, line 17
- `async fn blocking_select_vault( sidecar: State<'_, SidecarManager>, path: Option<String>, ) -> Result<Value, CommandError>` — fn, line 25
- `async fn blocking_isolated_cli_call( sidecar: State<'_, SidecarManager>, input: Value, ) -> Result<Value, CommandError>` — fn, line 32
- `fn is_populate_goal_command(input: &Value) -> bool` — fn, line 49
- `fn cli_command_succeeded(result: &Value) -> bool` — fn, line 61
- `fn populate_goal_cli_calls_are_classified_as_isolated()` — fn, line 1542
- `fn other_cli_calls_stay_on_the_primary_sidecar()` — fn, line 1552
- `fn successful_cli_results_are_detected_from_the_camel_case_contract()` — fn, line 1561

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/Rust/main|src-tauri/src/main.rs]] — module declaration: module declaration; no named call claim

## Dependencies

### Desktop source modules

- [[Reference/Desktop/Rust/errors|src-tauri/src/errors.rs]] — crate import; imports `errors`
- [[Reference/Desktop/Rust/sidecar|src-tauri/src/sidecar.rs]] — crate import; imports `sidecar`
- [[Reference/Desktop/Rust/vault_watcher|src-tauri/src/vault_watcher.rs]] — crate import; imports `vault_watcher`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `serde_json`, `tauri`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Architecture/Adapter Architecture#Sidecar structure|sidecar structure]] — owns the four-layer RPC contract.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src-tauri/src/commands.rs](../../../../../apps/learnloop-tauri/src-tauri/src/commands.rs) — inline Rust unit-test module; run with `cargo test` from `apps/learnloop-tauri/src-tauri`.
- [tests/test_desktop_rpc_contract.py](../../../../../tests/test_desktop_rpc_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../tests/test_sidecar_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Keep native code an adapter: process/protocol/window/filesystem concerns belong here, while learning rules and durable state interpretation stay in Python domains.
- Command changes must remain synchronized with `src/api/client.ts`, `src/api/dto.ts`, `main.rs` registration, and the Python sidecar registry.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src-tauri/src/commands.rs](../../../../../apps/learnloop-tauri/src-tauri/src/commands.rs) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
