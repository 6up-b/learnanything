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
| Source lines | 1503 |
| Language | `Rust` |
| Area | [[Reference/Desktop/Rust/_area|Rust]] |
| Refactor status | `ACTIVE` |
| Activation kind | `native-entry-reachable` |

## Activation and status evidence

> [!success] ACTIVE
> A Rust mod/use edge reaches this crate module from src-tauri/src/main.rs.
>
> Build/entry chain: [[Reference/Desktop/Rust/main|src-tauri/src/main.rs]] → [[Reference/Desktop/Rust/commands|src-tauri/src/commands.rs]]

## Public API

- `pub async fn select_vault( path: Option<String>, sidecar: State<'_, SidecarManager>, watcher: State<'_, VaultWatcher>, ) -> Result<Value, CommandError>` — fn, line 78
- `pub async fn load_vault( sidecar: State<'_, SidecarManager>, watcher: State<'_, VaultWatcher>, ) -> Result<Value, CommandError>` — fn, line 90
- `pub async fn create_vault(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 100; macro-expanded
- `pub async fn get_learner_profile( sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 103
- `pub async fn set_learner_profile(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 109; macro-expanded
- `pub async fn get_runtime_health(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 112
- `pub async fn start_session(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 116; macro-expanded
- `pub async fn adopt_session(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 117; macro-expanded
- `pub async fn get_start_summary(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 120
- `pub async fn get_session( session_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 125
- `pub async fn clear_session_checkpoint( session_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 133
- `pub async fn end_session( session_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 146
- `pub async fn get_today_queue(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 153; macro-expanded
- `pub async fn get_queue_revision(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 155; macro-expanded
- `pub async fn explain_practice_item( practice_item_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 158
- `pub async fn open_queue_item( practice_item_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 171
- `pub async fn get_practice_item( practice_item_id: String, session_id: Option<String>, proposal_id: Option<String>, source_exercise_import_id: Option<String>, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 184
- `pub async fn get_probe_contract( practice_item_id: String, session_id: Option<String>, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 207
- `pub async fn stop_probe_diagnosing( practice_item_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 221
- `pub async fn get_next_probe_item( learning_object_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 234
- `pub async fn save_practice_draft(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 246; macro-expanded
- `pub async fn practice_record_hint_reveal(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 249; macro-expanded
- `pub async fn record_ask_availability(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 250; macro-expanded
- `pub async fn record_offer_shown(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 252; macro-expanded
- `pub async fn router_objective_explain(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 254; macro-expanded
- `pub async fn practice_request_hint(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 259; macro-expanded
- `pub async fn practice_hint_job(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 260; macro-expanded
- `pub async fn practice_cancel_hint(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 261; macro-expanded
- `pub async fn practice_answer_discriminating(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 262; macro-expanded
- `pub async fn practice_set_help_style(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 263; macro-expanded
- `pub async fn recover_practice_submission(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 265; macro-expanded
- `pub async fn acknowledge_practice_submission(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 267; macro-expanded
- `pub async fn submit_attempt(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 272; macro-expanded
- `pub async fn submit_dont_know(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 274; macro-expanded
- `pub async fn skip_practice_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 276; macro-expanded
- `pub async fn followup_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 279; macro-expanded
- `pub async fn followup_next(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 280; macro-expanded
- `pub async fn followup_continue_without(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 281; macro-expanded
- `pub async fn followup_show_anyway(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 282; macro-expanded
- `pub async fn record_hypothesis_exposure(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 283; macro-expanded
- `pub async fn record_hypothesis_mark(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 284; macro-expanded
- `pub async fn get_feedback( attempt_id: String, record_open: Option<bool>, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 287
- `pub async fn get_attempt( attempt_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 303
- `pub async fn get_attempt_trace_evidence( attempt_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 311
- `pub async fn get_grading_clarification( attempt_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 324
- `pub async fn answer_grading_clarification(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 336; macro-expanded
- `pub async fn inspect_entity( id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 339
- `pub async fn get_concept_graph(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 347
- `pub async fn get_vault_tree(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 352
- `pub async fn classify_ingest_source(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 356; macro-expanded
- `pub async fn start_ingest(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 358; macro-expanded
- `pub async fn get_ingest_job( job_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 361
- `pub async fn get_ingest_jobs(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 369
- `pub async fn cancel_ingest( job_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 374
- `pub async fn start_import_batch(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 381; macro-expanded
- `pub async fn get_ingest_batch( batch_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 384
- `pub async fn list_ingest_batches(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 391; macro-expanded
- `pub async fn cancel_ingest_batch( batch_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 394
- `pub async fn resume_ingest_batch( batch_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 402
- `pub async fn retry_synthesis(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 409; macro-expanded
- `pub async fn get_synthesis_candidate( batch_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 412
- `pub async fn get_source_library(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 425
- `pub async fn preview_source_deletion( source_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 430
- `pub async fn delete_source( source_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 443
- `pub async fn get_source_outline( extraction_ref: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 453
- `pub async fn get_selection_preview(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 465; macro-expanded
- `pub async fn get_effective_outline(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 467; macro-expanded
- `pub async fn save_unit_selection(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 469; macro-expanded
- `pub async fn get_acquisition_preview(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 471; macro-expanded
- `pub async fn get_build_plan(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 473; macro-expanded
- `pub async fn list_source_sets(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 476
- `pub async fn get_source_set( source_set_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 481
- `pub async fn upsert_source_set(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 493; macro-expanded
- `pub async fn get_source_coverage( source_set_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 496
- `pub async fn create_study_map(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 508; macro-expanded
- `pub async fn build_study_map(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 510; macro-expanded
- `pub async fn append_source(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 512; macro-expanded
- `pub async fn maintenance_feed(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 514; macro-expanded
- `pub async fn get_measurement_health( sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 517
- `pub async fn generate_commissioning_practice(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 526; macro-expanded
- `pub async fn get_review_counts(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 534
- `pub async fn schedule_certification_cold_probes(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 538; macro-expanded
- `pub async fn transition_causal_probe_candidate(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 543; macro-expanded
- `pub async fn apply_integration_backfill(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 548; macro-expanded
- `pub async fn maintenance_notice_action(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 550; macro-expanded
- `pub async fn list_source_conflicts(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 552; macro-expanded
- `pub async fn resolve_source_conflict(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 554; macro-expanded
- `pub async fn exam_readiness(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 556; macro-expanded
- `pub async fn start_extraction_repair(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 558; macro-expanded
- `pub async fn read_vault_file( path: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 561
- `pub async fn write_vault_file( path: String, body: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 569
- `pub async fn create_vault_file(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 582; macro-expanded
- `pub async fn sqlite_tables(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 584; macro-expanded
- `pub async fn sqlite_table(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 586; macro-expanded
- `pub async fn sqlite_exec(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 588; macro-expanded
- `pub async fn sqlite_update_cell(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 590; macro-expanded
- `pub async fn sqlite_insert_row(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 592; macro-expanded
- `pub async fn sqlite_delete_row(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 594; macro-expanded
- `pub async fn get_proposals(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 597
- `pub async fn get_entity_provenance( entity_type: String, entity_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 602
- `pub async fn plan_quick_add(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 615; macro-expanded
- `pub async fn get_inbox_summary(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 617; macro-expanded
- `pub async fn list_capture_inbox(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 618; macro-expanded
- `pub async fn dismiss_capture(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 619; macro-expanded
- `pub async fn purge_capture(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 620; macro-expanded
- `pub async fn resume_capture_route(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 621; macro-expanded
- `pub async fn get_capture_media(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 622; macro-expanded
- `pub async fn confirm_quick_add(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 624; macro-expanded
- `pub async fn get_span_view(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 626; macro-expanded
- `pub async fn get_subject_registry(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 628; macro-expanded
- `pub async fn propose_facet_merge(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 630; macro-expanded
- `pub async fn list_facet_identity_actions(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 632; macro-expanded
- `pub async fn undo_facet_identity_action(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 634; macro-expanded
- `pub async fn decide_facet_reword(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 636; macro-expanded
- `pub async fn accept_proposal_items(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 638; macro-expanded
- `pub async fn reject_proposal_items(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 640; macro-expanded
- `pub async fn reset_proposal_items(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 642; macro-expanded
- `pub async fn edit_proposal_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 644; macro-expanded
- `pub async fn refresh_proposal_item_validation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 646; macro-expanded
- `pub async fn delete_proposal_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 651; macro-expanded
- `pub async fn trigger_regrade(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 653; macro-expanded
- `pub async fn record_answer_display(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 656; macro-expanded
- `pub async fn record_self_grade_disclosure(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 657; macro-expanded
- `pub async fn add_error_event(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 659; macro-expanded
- `pub async fn trigger_followup(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 661; macro-expanded
- `pub async fn rate_followup(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 663; macro-expanded
- `pub async fn report_unresolved_cause(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 665; macro-expanded
- `pub async fn submit_eliciting_response(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 667; macro-expanded
- `pub async fn contest_causal_diagnosis(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 669; macro-expanded
- `pub async fn diagnosis_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 675; macro-expanded
- `pub async fn record_diagnosis_feedback(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 677; macro-expanded
- `pub async fn causal_repair_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 685; macro-expanded
- `pub async fn causal_probe_offer_action(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 687; macro-expanded
- `pub async fn causal_probe_defer(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 689; macro-expanded
- `pub async fn causal_teach_me_now(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 691; macro-expanded
- `pub async fn start_primed_retry(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 693; macro-expanded
- `pub async fn start_guided_redo(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 695; macro-expanded
- `pub async fn run_cli_command( input: Value, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 698
- `pub async fn get_facet_mastery(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 710
- `pub async fn get_knowledge_map(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 715
- `pub async fn get_attempt_trace( attempt_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 722
- `pub async fn get_capability_grid( learning_object_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 735
- `pub async fn get_facet_evidence_timeline( facet_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 748
- `pub async fn get_knowledge_map_history( sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 761
- `pub async fn set_grading_provider( provider: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 768
- `pub async fn get_settings(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 781
- `pub async fn update_ai_settings(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 785; macro-expanded
- `pub async fn set_openrouter_api_key( api_key: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 788
- `pub async fn update_ingest_settings(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 800; macro-expanded
- `pub async fn chatgpt_plan_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 801; macro-expanded
- `pub async fn add_source(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 803; macro-expanded
- `pub async fn get_ai_connection(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 804; macro-expanded
- `pub async fn connect_ai(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 805; macro-expanded
- `pub async fn source_action(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 806; macro-expanded
- `pub async fn chatgpt_plan_signin_start(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 807; macro-expanded
- `pub async fn chatgpt_plan_signin_cancel(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 808; macro-expanded
- `pub async fn chatgpt_plan_signout(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 809; macro-expanded
- `pub async fn chatgpt_plan_acknowledge_welcome(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 810; macro-expanded
- `pub async fn chatgpt_plan_resume(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 811; macro-expanded
- `pub async fn ai_use_fallback(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 813; macro-expanded
- `pub async fn detect_provider_capabilities(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 814; macro-expanded
- `pub async fn update_provider_modalities(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 815; macro-expanded
- `pub async fn set_transcription_api_key( api_key: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 818
- `pub async fn set_text_recognition_api_key( api_key: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 831
- `pub async fn get_animation_runtime( sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 844
- `pub async fn update_animation_settings(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 850; macro-expanded
- `pub async fn request_concept_animation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 851; macro-expanded
- `pub async fn get_concept_animation_status( animation_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 854
- `pub async fn list_concept_animations( concept_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 867
- `pub async fn ask_tutor_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 879; macro-expanded
- `pub async fn get_learner_text_gap(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 880; macro-expanded
- `pub async fn reverse_learner_text_gap(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 881; macro-expanded
- `pub async fn preview_tutor_opening(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 883; macro-expanded
- `pub async fn rate_tutor_answer(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 885; macro-expanded
- `pub async fn save_tutor_answer_note(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 887; macro-expanded
- `pub async fn get_tutor_transcript(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 889; macro-expanded
- `pub async fn promote_tutor_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 891; macro-expanded
- `pub async fn author_practice_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 893; macro-expanded
- `pub async fn request_rung_variant(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 895; macro-expanded
- `pub async fn get_rung_variant_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 897; macro-expanded
- `pub async fn remint_diagnostic_probe(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 899; macro-expanded
- `pub async fn edit_practice_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 901; macro-expanded
- `pub async fn retire_practice_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 903; macro-expanded
- `pub async fn split_practice_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 905; macro-expanded
- `pub async fn list_question_queue(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 907; macro-expanded
- `pub async fn resolve_question_event(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 909; macro-expanded
- `pub async fn request_teach_back(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 911; macro-expanded
- `pub async fn start_teach_back(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 913; macro-expanded
- `pub async fn submit_teach_back_turn(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 915; macro-expanded
- `pub async fn goals_list(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 918
- `pub async fn get_goal_report( goal_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 923
- `pub async fn get_goal_report_series(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 930; macro-expanded
- `pub async fn goal_feasibility(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 932; macro-expanded
- `pub async fn get_overconfidence_list( goal_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 935
- `pub async fn get_reentry_summary(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 947; macro-expanded
- `pub async fn get_decay_pressure(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 949; macro-expanded
- `pub async fn start_overconfidence_probe(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 951; macro-expanded
- `pub async fn create_goal(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 953; macro-expanded
- `pub async fn generate_starter_practice(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 955; macro-expanded
- `pub async fn update_goal_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 957; macro-expanded
- `pub async fn update_goal_intent(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 959; macro-expanded
- `pub async fn get_exam_status( goal_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 962
- `pub async fn start_exam(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 969; macro-expanded
- `pub async fn submit_exam_answer(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 971; macro-expanded
- `pub async fn start_calibration_session(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 973; macro-expanded
- `pub async fn placement_self_report(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 975; macro-expanded
- `pub async fn start_quick_check(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 977; macro-expanded
- `pub async fn get_daily_plan(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 980; macro-expanded
- `pub async fn set_plan_minutes(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 982; macro-expanded
- `pub async fn next_plan_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 984; macro-expanded
- `pub async fn plan_reading_ended(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 986; macro-expanded
- `pub async fn plan_keep_going(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 988; macro-expanded
- `pub async fn plan_more_new(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 990; macro-expanded
- `pub async fn plan_learner_pick(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 992; macro-expanded
- `pub async fn plan_something_else_options(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 995; macro-expanded
- `pub async fn plan_something_else(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 996; macro-expanded
- `pub async fn find_practice(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1000; macro-expanded
- `pub async fn record_proposal_impressions(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1001; macro-expanded
- `pub async fn import_source_exercise(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1002; macro-expanded
- `pub async fn get_source_exercise_import(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1003; macro-expanded
- `pub async fn run_source_tool(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1004; macro-expanded
- `pub async fn record_source_offer_shown(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1005; macro-expanded
- `pub async fn find_sources(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1006; macro-expanded
- `pub async fn get_today_headline(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1008; macro-expanded
- `pub async fn get_intent(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1011; macro-expanded
- `pub async fn set_intent(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1013; macro-expanded
- `pub async fn set_intent_deadline(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1015; macro-expanded
- `pub async fn get_calibration_session( calibration_session_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1018
- `pub async fn stop_calibration_session( calibration_session_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1031
- `pub async fn finish_exam(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1043; macro-expanded
- `pub async fn begin_probe_dialogue( learning_object_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1046
- `pub async fn next_probe_dialogue_turn( dialogue_state: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1059
- `pub async fn record_probe_dialogue_turn( dialogue_state: String, presentation_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1072
- `pub async fn end_probe_dialogue( dialogue_state: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1086
- `pub async fn present_claims(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1098; macro-expanded
- `pub async fn respond_claim(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1100; macro-expanded
- `pub async fn dismiss_claim( presentation_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1103
- `pub async fn get_review_log(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 1116
- `pub async fn start_remediation( misconception_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1121
- `pub async fn prescribe_remediation( episode_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1134
- `pub async fn start_remediation_treatment( episode_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1147
- `pub async fn get_forecast_track_record(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1159; macro-expanded
- `pub async fn get_answer_calibration( sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1162
- `pub async fn propose_graph_edits(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1168; macro-expanded
- `pub async fn queue_restructure_request(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1170; macro-expanded
- `pub async fn resolve_edge_direction(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1172; macro-expanded
- `pub async fn get_facet_detail( facet_id: String, sidecar: State<'_, SidecarManager>, ) -> Result<Value, CommandError>` — fn, line 1175
- `pub async fn list_facets(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError>` — fn, line 1183
- `pub async fn preview_knowledge_map(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1187; macro-expanded
- `pub async fn preview_blueprint_readiness(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1189; macro-expanded
- `pub async fn blueprint_review(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1197; macro-expanded
- `pub async fn blueprint_get_version(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1198; macro-expanded
- `pub async fn blueprint_discover_candidates(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1199; macro-expanded
- `pub async fn blueprint_compose_draft(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1203; macro-expanded
- `pub async fn golden_path_confirm(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1206; macro-expanded
- `pub async fn golden_path_run_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1207; macro-expanded
- `pub async fn golden_path_list_runs(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1208; macro-expanded
- `pub async fn golden_path_advance(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1209; macro-expanded
- `pub async fn golden_path_assess_open(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1212; macro-expanded
- `pub async fn golden_path_assess_submit(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1213; macro-expanded
- `pub async fn golden_path_assess_result(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1214; macro-expanded
- `pub async fn golden_path_restore(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1215; macro-expanded
- `pub async fn golden_path_depth_invitation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1216; macro-expanded
- `pub async fn golden_path_accept_edge(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1217; macro-expanded
- `pub async fn golden_path_decline_edge(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1218; macro-expanded
- `pub async fn diagnostic_triage(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1221; macro-expanded
- `pub async fn diagnostic_triage_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1222; macro-expanded
- `pub async fn diagnostic_triage_decide(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1223; macro-expanded
- `pub async fn ladder_policy(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1226; macro-expanded
- `pub async fn ladder_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1227; macro-expanded
- `pub async fn ladder_enter(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1228; macro-expanded
- `pub async fn ladder_advance(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1229; macro-expanded
- `pub async fn practice_pool_review(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1230; macro-expanded
- `pub async fn practice_pool_next_surface(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1231; macro-expanded
- `pub async fn practice_pool_for_run(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1232; macro-expanded
- `pub async fn practice_pool_seed_for_run(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1233; macro-expanded
- `pub async fn practice_pool_admit_anchor(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1234; macro-expanded
- `pub async fn adjudication_queue(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1239; macro-expanded
- `pub async fn adjudication_record(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1240; macro-expanded
- `pub async fn adjudication_scoreboard(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1241; macro-expanded
- `pub async fn reader_ask(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1244; macro-expanded
- `pub async fn reader_ask_history(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1245; macro-expanded
- `pub async fn reader_set_answer_mode(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1246; macro-expanded
- `pub async fn reader_present_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1247; macro-expanded
- `pub async fn reader_submit_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1248; macro-expanded
- `pub async fn reader_skip_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1249; macro-expanded
- `pub async fn reader_choose_disposition(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1250; macro-expanded
- `pub async fn reader_restore_source(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1251; macro-expanded
- `pub async fn reader_prompt_contract(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1252; macro-expanded
- `pub async fn reader_render_view(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1254; macro-expanded
- `pub async fn reader_guide_plan(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1255; macro-expanded
- `pub async fn reader_saved_place(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1256; macro-expanded
- `pub async fn reader_pdf_view(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1257; macro-expanded
- `pub async fn reader_watch_plan(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1258; macro-expanded
- `pub async fn reader_author_section_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1259; macro-expanded
- `pub async fn reader_authored_question_action(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1263; macro-expanded
- `pub async fn reader_get_progress(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1267; macro-expanded
- `pub async fn reader_mark_section_progress(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1268; macro-expanded
- `pub async fn reader_escalate_authored_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1269; macro-expanded
- `pub async fn reader_import_exercise(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1273; macro-expanded
- `pub async fn reader_exercise_import_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1274; macro-expanded
- `pub async fn reader_search_sources(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1278; macro-expanded
- `pub async fn reader_retrieval_open(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1280; macro-expanded
- `pub async fn reader_manual_anchor(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1281; macro-expanded
- `pub async fn reader_set_inquiry_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1284; macro-expanded
- `pub async fn reader_reconnect_answer(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1285; macro-expanded
- `pub async fn reader_inquiry_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1286; macro-expanded
- `pub async fn reader_inquiry_question_action(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1287; macro-expanded
- `pub async fn reader_log_activity(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1288; macro-expanded
- `pub async fn reader_cue_action(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1290; macro-expanded
- `pub async fn reader_cue_preferences(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1291; macro-expanded
- `pub async fn reader_set_cue_preferences(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1292; macro-expanded
- `pub async fn reader_cue_discovery(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1294; macro-expanded
- `pub async fn reader_cue_discovery_job(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1295; macro-expanded
- `pub async fn reader_cue_impressions(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1296; macro-expanded
- `pub async fn reader_cue_tap(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1297; macro-expanded
- `pub async fn workbench_open(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1299; macro-expanded
- `pub async fn workbench_save_step(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1300; macro-expanded
- `pub async fn workbench_set_book(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1301; macro-expanded
- `pub async fn workbench_leave(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1302; macro-expanded
- `pub async fn workbench_abandon(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1303; macro-expanded
- `pub async fn workbench_reopen(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1304; macro-expanded
- `pub async fn workbench_refresh_import(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1305; macro-expanded
- `pub async fn workbench_bind(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1306; macro-expanded
- `pub async fn workbench_retry_import(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1307; macro-expanded
- `pub async fn workbench_admit(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1309; macro-expanded
- `pub async fn workbench_submit(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1310; macro-expanded
- `pub async fn workbench_session_for_attempt(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1311; macro-expanded
- `pub async fn workbench_for_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1312; macro-expanded
- `pub async fn workbench_for_source(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1313; macro-expanded
- `pub async fn workbench_open_problems(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1315; macro-expanded
- `pub async fn workbench_check(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1317; macro-expanded
- `pub async fn workbench_suggest_help(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1318; macro-expanded
- `pub async fn workbench_request_help(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1319; macro-expanded
- `pub async fn workbench_help_job(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1320; macro-expanded
- `pub async fn workbench_cancel_help(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1321; macro-expanded
- `pub async fn workbench_answer_discriminating(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1322; macro-expanded
- `pub async fn workbench_set_help_style(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1323; macro-expanded
- `pub async fn workbench_help_state(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1324; macro-expanded
- `pub async fn workbench_show_example(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1326; macro-expanded
- `pub async fn workbench_another_passage(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1327; macro-expanded
- `pub async fn workbench_compare_offer(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1328; macro-expanded
- `pub async fn workbench_compare_methods(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1329; macro-expanded
- `pub async fn reader_recap(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1331; macro-expanded
- `pub async fn reader_recap_event(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1332; macro-expanded
- `pub async fn reader_wrap_up(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1333; macro-expanded
- `pub async fn reader_wrap_up_offer(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1334; macro-expanded
- `pub async fn reader_followup_undo(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1336; macro-expanded
- `pub async fn reader_followup_undo_all(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1337; macro-expanded
- `pub async fn reader_followup_restore(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1338; macro-expanded
- `pub async fn reader_route_intent(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1340; macro-expanded
- `pub async fn reader_intent_routing(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1341; macro-expanded
- `pub async fn reader_intent_outcome(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1342; macro-expanded
- `pub async fn reader_active_question(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1343; macro-expanded
- `pub async fn reader_active_question_status(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1344; macro-expanded
- `pub async fn reader_active_question_action(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1345; macro-expanded
- `pub async fn reader_reconstruct(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1346; macro-expanded
- `pub async fn reader_reconstruct_undo(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1347; macro-expanded
- `pub async fn reader_library_ask(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1349; macro-expanded
- `pub async fn reader_library_ask_notes(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1350; macro-expanded
- `pub async fn reader_library_compare(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1351; macro-expanded
- `pub async fn reader_library_ask_tutor(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1352; macro-expanded
- `pub async fn reader_library_job(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1353; macro-expanded
- `pub async fn reader_library_job_cancel(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1354; macro-expanded
- `pub async fn reader_compare_scope(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1356; macro-expanded
- `pub async fn reader_compare_scope_correction(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1357; macro-expanded
- `pub async fn reader_exercise_candidates(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1359; macro-expanded
- `pub async fn reader_find_exercises(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1360; macro-expanded
- `pub async fn reader_library_compare_keep(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1362; macro-expanded
- `pub async fn reader_library_compare_remove(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1363; macro-expanded
- `pub async fn reader_library_compare_reopen(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1364; macro-expanded
- `pub async fn reader_kept_comparisons(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1365; macro-expanded
- `pub async fn reader_reading_path(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1367; macro-expanded
- `pub async fn reader_reading_path_set_depth(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1368; macro-expanded
- `pub async fn reader_reading_path_override(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1369; macro-expanded
- `pub async fn reader_correspondents(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1372; macro-expanded
- `pub async fn reader_correspondent_peek(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1373; macro-expanded
- `pub async fn reader_correspondent_dismiss(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1374; macro-expanded
- `pub async fn reader_correspondence_preferences(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1376; macro-expanded
- `pub async fn reader_set_correspondence_preferences(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1377; macro-expanded
- `pub async fn curriculum_deliverables(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1380; macro-expanded
- `pub async fn curriculum_create_deliverable(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1381; macro-expanded
- `pub async fn curriculum_set_scope(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1382; macro-expanded
- `pub async fn curriculum_scope(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1383; macro-expanded
- `pub async fn curriculum_scope_decide(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1384; macro-expanded
- `pub async fn curriculum_set_depth(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1385; macro-expanded
- `pub async fn curriculum_guide_slice(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1386; macro-expanded
- `pub async fn curriculum_path_override(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1387; macro-expanded
- `pub async fn curriculum_ready_check(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1388; macro-expanded
- `pub async fn curriculum_also_about(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1389; macro-expanded
- `pub async fn notes_path(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1391; macro-expanded
- `pub async fn notes_marks(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1392; macro-expanded
- `pub async fn notes_passages(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1393; macro-expanded
- `pub async fn notes_search(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1394; macro-expanded
- `pub async fn notes_link(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1395; macro-expanded
- `pub async fn notes_decide(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1396; macro-expanded
- `pub async fn notes_hidden(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1397; macro-expanded
- `pub async fn notes_set_gaps(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1399; macro-expanded
- `pub async fn lesson_turn(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1401; macro-expanded
- `pub async fn lesson_view(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1402; macro-expanded
- `pub async fn lesson_activity(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1404; macro-expanded
- `pub async fn lesson_goal(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1406; macro-expanded
- `pub async fn lesson_open_lessons(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1407; macro-expanded
- `pub async fn lesson_suggestion(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1409; macro-expanded
- `pub async fn lesson_suggestion_respond(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1410; macro-expanded
- `pub async fn reader_side_by_side_section(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1412; macro-expanded
- `pub async fn reader_figure_request(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1415; macro-expanded
- `pub async fn figure_request(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1417; macro-expanded
- `pub async fn figure_rich_cancel(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1419; macro-expanded
- `pub async fn figure_rich_retry(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1421; macro-expanded
- `pub async fn figure_manim_opt_in(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1422; macro-expanded
- `pub async fn figure_take_step(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1425; macro-expanded
- `pub async fn figure_open(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1426; macro-expanded
- `pub async fn reader_figure_revise(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1427; macro-expanded
- `pub async fn reader_figure_recheck(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1428; macro-expanded
- `pub async fn reader_figure_job(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1429; macro-expanded
- `pub async fn reader_figure_job_cancel(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1430; macro-expanded
- `pub async fn reader_figures(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1431; macro-expanded
- `pub async fn reader_figure_predict(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1432; macro-expanded
- `pub async fn reader_figure_explain(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1433; macro-expanded
- `pub async fn reader_dose_offer(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1436; macro-expanded
- `pub async fn reader_dose_offer_event(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1437; macro-expanded
- `pub async fn adaptive_difficulty_readiness(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1438; macro-expanded
- `pub async fn adaptive_difficulty_why_item(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1439; macro-expanded
- `pub async fn reader_block_original_region(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1440; macro-expanded
- `pub async fn practice_as_printed(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1443; macro-expanded
- `pub async fn practice_report_transcription(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1444; macro-expanded
- `pub async fn reader_capture(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1445; macro-expanded
- `pub async fn reader_edit_annotation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1446; macro-expanded
- `pub async fn reader_delete_intent_annotation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1447; macro-expanded
- `pub async fn reader_restore_annotation(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1452; macro-expanded
- `pub async fn reader_reanchor(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1453; macro-expanded
- `pub async fn reader_source_annotations(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1454; macro-expanded
- `pub async fn reader_drain_outbox(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1455; macro-expanded
- `pub async fn reader_invoke_preset(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1457; macro-expanded
- `pub async fn reader_set_mode(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1458; macro-expanded
- `pub async fn reader_question_control(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1459; macro-expanded
- `pub async fn reader_retry_request(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1460; macro-expanded
- `pub async fn reader_source_requests(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1461; macro-expanded
- `pub async fn reader_source_objects(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1462; macro-expanded
- `pub async fn reader_proposal_inbox(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1463; macro-expanded
- `pub async fn reader_accept_proposal(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1464; macro-expanded
- `pub async fn reader_reject_proposal(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1465; macro-expanded
- `pub async fn reader_author_qa(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1467; macro-expanded
- `pub async fn reader_coach_lint(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1468; macro-expanded
- `pub async fn reader_arc(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1469; macro-expanded
- `pub async fn reader_set_depth_policy(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1470; macro-expanded
- `pub async fn reader_pause_arc(input, sidecar) [expanded by sidecar_passthrough!]` — fn, line 1471; macro-expanded

## Internal implementation anchors

- `async fn run_sidecar_task( sidecar: State<'_, SidecarManager>, operation: impl FnOnce(SidecarManager) -> Result<Value, CommandError> + Send + 'static, ) -> Result<Value, CommandError>` — fn, line 7
- `async fn blocking_sidecar_call( sidecar: State<'_, SidecarManager>, method: &'static str, params: Value, ) -> Result<Value, CommandError>` — fn, line 17
- `async fn blocking_select_vault( sidecar: State<'_, SidecarManager>, path: Option<String>, ) -> Result<Value, CommandError>` — fn, line 25
- `async fn blocking_isolated_cli_call( sidecar: State<'_, SidecarManager>, input: Value, ) -> Result<Value, CommandError>` — fn, line 32
- `fn is_populate_goal_command(input: &Value) -> bool` — fn, line 49
- `fn cli_command_succeeded(result: &Value) -> bool` — fn, line 61
- `fn populate_goal_cli_calls_are_classified_as_isolated()` — fn, line 1479
- `fn other_cli_calls_stay_on_the_primary_sidecar()` — fn, line 1489
- `fn successful_cli_results_are_detected_from_the_camel_case_contract()` — fn, line 1498

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
