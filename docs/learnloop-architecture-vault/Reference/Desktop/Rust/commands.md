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
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "clean"
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
| Source lines | 1260 |
| Language | `Rust` |
| Area | [[Reference/Desktop/Rust/_area|Rust]] |
| Refactor status | `ACTIVE` |
| Activation kind | `native-entry-reachable` |
| Worktree state | `clean` |
| Source commit | `62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

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
- `pub async fn get_session( session_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 129
- `pub async fn update_session_checkpoint(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 136; macro-expanded
- `pub async fn clear_session_checkpoint( session_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 139
- `pub async fn end_session( session_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 152
- `pub async fn get_today_queue(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 159; macro-expanded
- `pub async fn get_queue_revision(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 162
- `pub async fn explain_practice_item( practice_item_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 167
- `pub async fn open_queue_item( practice_item_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 180
- `pub async fn get_practice_item( practice_item_id: String, session_id: Option<String>, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 193
- `pub async fn get_probe_contract( practice_item_id: String, session_id: Option<String>, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 207
- `pub async fn stop_probe_diagnosing( practice_item_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 221
- `pub async fn get_next_probe_item( learning_object_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 234
- `pub async fn save_practice_draft(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 246; macro-expanded
- `pub async fn recover_practice_submission(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 248; macro-expanded
- `pub async fn acknowledge_practice_submission(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 250; macro-expanded
- `pub async fn submit_attempt(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 255; macro-expanded
- `pub async fn submit_dont_know(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 257; macro-expanded
- `pub async fn skip_practice_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 259; macro-expanded
- `pub async fn get_feedback( attempt_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 262
- `pub async fn get_attempt( attempt_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 270
- `pub async fn get_attempt_trace_evidence( attempt_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 278
- `pub async fn get_grading_clarification( attempt_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 291
- `pub async fn answer_grading_clarification(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 303; macro-expanded
- `pub async fn inspect_entity( id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 306
- `pub async fn get_concept_graph(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 314
- `pub async fn get_vault_tree(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 319
- `pub async fn get_recent_ingests(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 324
- `pub async fn classify_ingest_source(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 328; macro-expanded
- `pub async fn start_ingest(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 330; macro-expanded
- `pub async fn get_ingest_job( job_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 333
- `pub async fn get_ingest_jobs(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 341
- `pub async fn cancel_ingest( job_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 346
- `pub async fn start_import_batch(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 353; macro-expanded
- `pub async fn get_ingest_batch( batch_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 356
- `pub async fn list_ingest_batches(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 363; macro-expanded
- `pub async fn cancel_ingest_batch( batch_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 366
- `pub async fn resume_ingest_batch( batch_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 374
- `pub async fn retry_synthesis(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 381; macro-expanded
- `pub async fn get_synthesis_candidate( batch_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 384
- `pub async fn get_source_library(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 397
- `pub async fn preview_source_deletion( source_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 402
- `pub async fn delete_source( source_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 415
- `pub async fn get_source_outline( extraction_ref: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 425
- `pub async fn get_selection_preview(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 437; macro-expanded
- `pub async fn get_effective_outline(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 439; macro-expanded
- `pub async fn save_unit_selection(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 441; macro-expanded
- `pub async fn get_acquisition_preview(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 443; macro-expanded
- `pub async fn get_build_plan(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 445; macro-expanded
- `pub async fn list_source_sets(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 448
- `pub async fn get_source_set( source_set_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 453
- `pub async fn upsert_source_set(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 465; macro-expanded
- `pub async fn get_source_coverage( source_set_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 468
- `pub async fn start_inventory(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 480; macro-expanded
- `pub async fn create_study_map(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 482; macro-expanded
- `pub async fn build_study_map(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 484; macro-expanded
- `pub async fn append_source(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 486; macro-expanded
- `pub async fn refresh_revision(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 488; macro-expanded
- `pub async fn maintenance_feed(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 490; macro-expanded
- `pub async fn get_measurement_health( sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 493
- `pub async fn generate_commissioning_practice(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 502; macro-expanded
- `pub async fn get_review_counts(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 510
- `pub async fn schedule_certification_cold_probes(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 514; macro-expanded
- `pub async fn transition_causal_probe_candidate(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 519; macro-expanded
- `pub async fn apply_integration_backfill(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 524; macro-expanded
- `pub async fn maintenance_notice_action(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 526; macro-expanded
- `pub async fn list_source_conflicts(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 528; macro-expanded
- `pub async fn resolve_source_conflict(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 530; macro-expanded
- `pub async fn exam_readiness(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 532; macro-expanded
- `pub async fn start_extraction_repair(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 534; macro-expanded
- `pub async fn read_vault_file( path: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 537
- `pub async fn write_vault_file( path: String, body: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 545
- `pub async fn create_vault_file(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 558; macro-expanded
- `pub async fn sqlite_tables(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 560; macro-expanded
- `pub async fn sqlite_table(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 562; macro-expanded
- `pub async fn sqlite_exec(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 564; macro-expanded
- `pub async fn sqlite_update_cell(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 566; macro-expanded
- `pub async fn sqlite_insert_row(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 568; macro-expanded
- `pub async fn sqlite_delete_row(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 570; macro-expanded
- `pub async fn get_proposals(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 573
- `pub async fn get_entity_provenance( entity_type: String, entity_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 578
- `pub async fn plan_quick_add(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 591; macro-expanded
- `pub async fn confirm_quick_add(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 593; macro-expanded
- `pub async fn get_span_view(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 595; macro-expanded
- `pub async fn get_subject_registry(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 597; macro-expanded
- `pub async fn propose_facet_merge(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 599; macro-expanded
- `pub async fn accept_proposal_items(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 601; macro-expanded
- `pub async fn reject_proposal_items(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 603; macro-expanded
- `pub async fn reset_proposal_items(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 605; macro-expanded
- `pub async fn edit_proposal_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 607; macro-expanded
- `pub async fn refresh_proposal_item_validation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 609; macro-expanded
- `pub async fn delete_proposal_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 614; macro-expanded
- `pub async fn trigger_regrade(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 616; macro-expanded
- `pub async fn add_error_event(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 618; macro-expanded
- `pub async fn trigger_followup(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 620; macro-expanded
- `pub async fn rate_followup(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 622; macro-expanded
- `pub async fn report_unresolved_cause(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 624; macro-expanded
- `pub async fn submit_eliciting_response(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 626; macro-expanded
- `pub async fn contest_causal_diagnosis(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 628; macro-expanded
- `pub async fn causal_repair_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 636; macro-expanded
- `pub async fn causal_probe_offer_action(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 638; macro-expanded
- `pub async fn causal_probe_defer(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 640; macro-expanded
- `pub async fn causal_teach_me_now(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 642; macro-expanded
- `pub async fn start_primed_retry(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 644; macro-expanded
- `pub async fn start_guided_redo(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 646; macro-expanded
- `pub async fn run_cli_command( input: Value, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 649
- `pub async fn get_facet_mastery(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 661
- `pub async fn get_knowledge_map(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 666
- `pub async fn get_attempt_trace( attempt_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 673
- `pub async fn get_capability_grid( learning_object_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 686
- `pub async fn get_facet_evidence_timeline( facet_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 699
- `pub async fn get_knowledge_map_history( sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 712
- `pub async fn set_grading_provider( provider: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 719
- `pub async fn get_settings(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 732
- `pub async fn update_ai_settings(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 736; macro-expanded
- `pub async fn set_openrouter_api_key( api_key: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 739
- `pub async fn update_ingest_settings(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 751; macro-expanded
- `pub async fn set_transcription_api_key( api_key: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 754
- `pub async fn get_animation_runtime( sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 767
- `pub async fn request_concept_animation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 773; macro-expanded
- `pub async fn get_concept_animation_status( animation_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 776
- `pub async fn list_concept_animations( concept_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 789
- `pub async fn ask_tutor_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 801; macro-expanded
- `pub async fn preview_tutor_opening(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 803; macro-expanded
- `pub async fn rate_tutor_answer(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 805; macro-expanded
- `pub async fn save_tutor_answer_note(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 807; macro-expanded
- `pub async fn get_tutor_transcript(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 809; macro-expanded
- `pub async fn promote_tutor_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 811; macro-expanded
- `pub async fn author_practice_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 813; macro-expanded
- `pub async fn request_rung_variant(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 815; macro-expanded
- `pub async fn get_rung_variant_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 817; macro-expanded
- `pub async fn remint_diagnostic_probe(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 819; macro-expanded
- `pub async fn edit_practice_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 821; macro-expanded
- `pub async fn retire_practice_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 823; macro-expanded
- `pub async fn split_practice_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 825; macro-expanded
- `pub async fn list_question_queue(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 827; macro-expanded
- `pub async fn resolve_question_event(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 829; macro-expanded
- `pub async fn request_teach_back(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 831; macro-expanded
- `pub async fn start_teach_back(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 833; macro-expanded
- `pub async fn submit_teach_back_turn(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 835; macro-expanded
- `pub async fn goals_list(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 838
- `pub async fn get_goal_report( goal_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 843
- `pub async fn get_goal_report_series(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 850; macro-expanded
- `pub async fn goal_feasibility(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 852; macro-expanded
- `pub async fn get_overconfidence_list( goal_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 855
- `pub async fn get_reentry_summary(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 867; macro-expanded
- `pub async fn get_decay_pressure(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 869; macro-expanded
- `pub async fn start_overconfidence_probe(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 871; macro-expanded
- `pub async fn create_goal(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 873; macro-expanded
- `pub async fn generate_starter_practice(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 875; macro-expanded
- `pub async fn update_goal_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 877; macro-expanded
- `pub async fn update_goal_intent(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 879; macro-expanded
- `pub async fn get_exam_status( goal_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 882
- `pub async fn start_exam(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 889; macro-expanded
- `pub async fn submit_exam_answer(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 891; macro-expanded
- `pub async fn start_calibration_session(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 893; macro-expanded
- `pub async fn get_calibration_session( calibration_session_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 896
- `pub async fn stop_calibration_session( calibration_session_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 909
- `pub async fn finish_exam(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 921; macro-expanded
- `pub async fn begin_probe_dialogue( learning_object_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 924
- `pub async fn next_probe_dialogue_turn( dialogue_state: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 937
- `pub async fn record_probe_dialogue_turn( dialogue_state: String, presentation_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 950
- `pub async fn end_probe_dialogue( dialogue_state: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 964
- `pub async fn present_claims(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 976; macro-expanded
- `pub async fn respond_claim(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 978; macro-expanded
- `pub async fn dismiss_claim( presentation_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 981
- `pub async fn export_claims(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 994
- `pub async fn purge_claims(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 999
- `pub async fn get_review_log(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 1004
- `pub async fn start_remediation( misconception_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1009
- `pub async fn prescribe_remediation( episode_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1022
- `pub async fn start_remediation_treatment( episode_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1035
- `pub async fn get_remediation( episode_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1048
- `pub async fn get_forecast_track_record(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1055; macro-expanded
- `pub async fn get_answer_calibration( sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1058
- `pub async fn propose_graph_edits(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1064; macro-expanded
- `pub async fn queue_restructure_request(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1066; macro-expanded
- `pub async fn resolve_edge_direction(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1068; macro-expanded
- `pub async fn get_facet_detail( facet_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1071
- `pub async fn list_facets(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 1079
- `pub async fn preview_knowledge_map(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1083; macro-expanded
- `pub async fn preview_blueprint_readiness(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1085; macro-expanded
- `pub async fn blueprint_register(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1093; macro-expanded
- `pub async fn blueprint_review(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1094; macro-expanded
- `pub async fn blueprint_get_version(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1095; macro-expanded
- `pub async fn blueprint_discover_candidates(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1096; macro-expanded
- `pub async fn blueprint_compose_draft(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1100; macro-expanded
- `pub async fn golden_path_confirm(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1103; macro-expanded
- `pub async fn golden_path_run_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1104; macro-expanded
- `pub async fn golden_path_list_runs(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1105; macro-expanded
- `pub async fn golden_path_advance(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1106; macro-expanded
- `pub async fn golden_path_assess_open(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1109; macro-expanded
- `pub async fn golden_path_assess_submit(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1110; macro-expanded
- `pub async fn golden_path_assess_result(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1111; macro-expanded
- `pub async fn golden_path_restore(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1112; macro-expanded
- `pub async fn golden_path_boundary_diff(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1113; macro-expanded
- `pub async fn golden_path_depth_invitation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1114; macro-expanded
- `pub async fn golden_path_accept_edge(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1115; macro-expanded
- `pub async fn golden_path_decline_edge(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1116; macro-expanded
- `pub async fn diagnostic_pack_assemble(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1119; macro-expanded
- `pub async fn diagnostic_pack_admit(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1120; macro-expanded
- `pub async fn diagnostic_pack_review(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1121; macro-expanded
- `pub async fn diagnostic_pack_list(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1122; macro-expanded
- `pub async fn diagnostic_baseline_enter(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1123; macro-expanded
- `pub async fn diagnostic_boundary_view(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1124; macro-expanded
- `pub async fn diagnostic_triage(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1125; macro-expanded
- `pub async fn diagnostic_triage_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1126; macro-expanded
- `pub async fn diagnostic_triage_decide(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1127; macro-expanded
- `pub async fn diagnostic_triage_override(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1128; macro-expanded
- `pub async fn ladder_policy(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1131; macro-expanded
- `pub async fn ladder_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1132; macro-expanded
- `pub async fn ladder_enter(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1133; macro-expanded
- `pub async fn ladder_advance(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1134; macro-expanded
- `pub async fn practice_pool_assemble(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1135; macro-expanded
- `pub async fn practice_pool_admit_surface(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1136; macro-expanded
- `pub async fn practice_pool_review(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1137; macro-expanded
- `pub async fn practice_pool_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1138; macro-expanded
- `pub async fn practice_pool_next_surface(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1139; macro-expanded
- `pub async fn practice_pool_for_run(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1140; macro-expanded
- `pub async fn practice_pool_seed_for_run(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1141; macro-expanded
- `pub async fn practice_pool_admit_anchor(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1142; macro-expanded
- `pub async fn adjudication_queue(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1147; macro-expanded
- `pub async fn adjudication_record(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1148; macro-expanded
- `pub async fn adjudication_scoreboard(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1149; macro-expanded
- `pub async fn reader_ask(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1152; macro-expanded
- `pub async fn reader_ask_history(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1153; macro-expanded
- `pub async fn reader_set_answer_mode(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1154; macro-expanded
- `pub async fn reader_present_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1155; macro-expanded
- `pub async fn reader_submit_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1156; macro-expanded
- `pub async fn reader_skip_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1157; macro-expanded
- `pub async fn reader_choose_disposition(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1158; macro-expanded
- `pub async fn reader_restore_source(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1159; macro-expanded
- `pub async fn reader_routing_prior(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1160; macro-expanded
- `pub async fn reader_prompt_contract(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1161; macro-expanded
- `pub async fn reader_render_view(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1163; macro-expanded
- `pub async fn reader_guide_plan(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1164; macro-expanded
- `pub async fn reader_pdf_view(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1165; macro-expanded
- `pub async fn reader_watch_plan(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1166; macro-expanded
- `pub async fn reader_author_section_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1167; macro-expanded
- `pub async fn reader_authored_question_action(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1171; macro-expanded
- `pub async fn reader_get_progress(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1175; macro-expanded
- `pub async fn reader_mark_section_progress(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1176; macro-expanded
- `pub async fn reader_escalate_authored_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1177; macro-expanded
- `pub async fn reader_import_exercise(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1181; macro-expanded
- `pub async fn reader_exercise_import_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1182; macro-expanded
- `pub async fn reader_search_sources(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1186; macro-expanded
- `pub async fn reader_manual_anchor(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1187; macro-expanded
- `pub async fn reader_block_health(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1188; macro-expanded
- `pub async fn reader_block_original_region(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1189; macro-expanded
- `pub async fn reader_translate_selection(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1190; macro-expanded
- `pub async fn reader_capture(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1191; macro-expanded
- `pub async fn reader_create_annotation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1192; macro-expanded
- `pub async fn reader_edit_annotation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1193; macro-expanded
- `pub async fn reader_delete_intent_annotation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1194; macro-expanded
- `pub async fn reader_reanchor(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1198; macro-expanded
- `pub async fn reader_annotation_history(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1199; macro-expanded
- `pub async fn reader_source_annotations(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1200; macro-expanded
- `pub async fn reader_outbox_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1201; macro-expanded
- `pub async fn reader_drain_outbox(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1202; macro-expanded
- `pub async fn reader_invoke_preset(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1204; macro-expanded
- `pub async fn reader_set_mode(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1205; macro-expanded
- `pub async fn reader_question_control(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1206; macro-expanded
- `pub async fn reader_enqueue_request(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1207; macro-expanded
- `pub async fn reader_request_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1208; macro-expanded
- `pub async fn reader_cancel_request(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1209; macro-expanded
- `pub async fn reader_retry_request(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1210; macro-expanded
- `pub async fn reader_source_requests(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1211; macro-expanded
- `pub async fn reader_drain_requests(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1212; macro-expanded
- `pub async fn reader_source_objects(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1213; macro-expanded
- `pub async fn reader_review_source_object(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1214; macro-expanded
- `pub async fn reader_link_relation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1215; macro-expanded
- `pub async fn reader_proposal_inbox(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1216; macro-expanded
- `pub async fn reader_accept_proposal(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1217; macro-expanded
- `pub async fn reader_reject_proposal(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1218; macro-expanded
- `pub async fn reader_author_qa(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1220; macro-expanded
- `pub async fn reader_coach_lint(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1221; macro-expanded
- `pub async fn reader_maintain(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1222; macro-expanded
- `pub async fn reader_arc(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1223; macro-expanded
- `pub async fn reader_set_depth_policy(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1224; macro-expanded
- `pub async fn reader_pause_arc(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1225; macro-expanded
- `pub async fn reader_shrink_envelope(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1226; macro-expanded
- `pub async fn reader_prime(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1227; macro-expanded
- `pub async fn reader_restore(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1228; macro-expanded

## Internal implementation anchors

- `async fn run_sidecar_task( sidecar: State<'_, SidecarManager>, operation: impl FnOnce(SidecarManager) -> Result<Value, CommandError> + Send + 'static, ) -> Result<Value, CommandError>` — fn, line 7
- `async fn blocking_sidecar_call( sidecar: State<'_, SidecarManager>, method: &'static str, params: Value, ) -> Result<Value, CommandError>` — fn, line 17
- `async fn blocking_select_vault( sidecar: State<'_, SidecarManager>, path: Option<String>, ) -> Result<Value, CommandError>` — fn, line 25
- `async fn blocking_isolated_cli_call( sidecar: State<'_, SidecarManager>, input: Value, ) -> Result<Value, CommandError>` — fn, line 32
- `fn is_populate_goal_command(input: &Value) -> bool` — fn, line 49
- `fn cli_command_succeeded(result: &Value) -> bool` — fn, line 61
- `fn populate_goal_cli_calls_are_classified_as_isolated()` — fn, line 1236
- `fn other_cli_calls_stay_on_the_primary_sidecar()` — fn, line 1246
- `fn successful_cli_results_are_detected_from_the_camel_case_contract()` — fn, line 1255

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
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src-tauri/src/commands.rs](../../../../../apps/learnloop-tauri/src-tauri/src/commands.rs) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
