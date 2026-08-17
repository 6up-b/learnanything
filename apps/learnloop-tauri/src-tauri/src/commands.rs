use crate::errors::CommandError;
use crate::sidecar::SidecarManager;
use crate::vault_watcher::VaultWatcher;
use serde_json::{json, Value};
use tauri::State;

async fn run_sidecar_task(
    sidecar: State<'_, SidecarManager>,
    operation: impl FnOnce(SidecarManager) -> Result<Value, CommandError> + Send + 'static,
) -> Result<Value, CommandError> {
    let sidecar = sidecar.inner().clone();
    tauri::async_runtime::spawn_blocking(move || operation(sidecar))
        .await
        .map_err(|err| CommandError::task_failed(err.to_string()))?
}

async fn blocking_sidecar_call(
    sidecar: State<'_, SidecarManager>,
    method: &'static str,
    params: Value,
) -> Result<Value, CommandError> {
    run_sidecar_task(sidecar, move |sidecar| sidecar.call(method, params)).await
}

async fn blocking_select_vault(
    sidecar: State<'_, SidecarManager>,
    path: Option<String>,
) -> Result<Value, CommandError> {
    run_sidecar_task(sidecar, move |sidecar| sidecar.select_vault(path)).await
}

async fn blocking_isolated_cli_call(
    sidecar: State<'_, SidecarManager>,
    input: Value,
) -> Result<Value, CommandError> {
    run_sidecar_task(sidecar, move |sidecar| {
        let result = sidecar.call_isolated("run_cli_command", input)?;
        if cli_command_succeeded(&result) {
            // The isolated sidecar reloads only its own in-memory vault after a
            // successful CLI mutation. Refresh the primary sidecar so the rest
            // of the app sees the newly populated practice items.
            sidecar.call("reload_vault", json!({}))?;
        }
        Ok(result)
    })
    .await
}

fn is_populate_goal_command(input: &Value) -> bool {
    input
        .get("argv")
        .and_then(Value::as_array)
        .and_then(|argv| {
            argv.iter()
                .filter_map(Value::as_str)
                .find(|arg| !arg.is_empty() && *arg != "learnloop")
        })
        == Some("populate-goal")
}

fn cli_command_succeeded(result: &Value) -> bool {
    result.get("exitCode").and_then(Value::as_i64) == Some(0)
}

macro_rules! sidecar_passthrough {
    ($fn_name:ident, $method:literal) => {
        #[tauri::command]
        pub async fn $fn_name(
            input: Value,
            sidecar: State<'_, SidecarManager>,
        ) -> Result<Value, CommandError> {
            blocking_sidecar_call(sidecar, $method, input).await
        }
    };
}

#[tauri::command]
pub async fn select_vault(
    path: Option<String>,
    sidecar: State<'_, SidecarManager>,
    watcher: State<'_, VaultWatcher>,
) -> Result<Value, CommandError> {
    let manager = sidecar.inner().clone();
    let result = blocking_select_vault(sidecar, path).await?;
    watcher.watch(manager.resolved_vault_path());
    Ok(result)
}

#[tauri::command]
pub async fn load_vault(
    sidecar: State<'_, SidecarManager>,
    watcher: State<'_, VaultWatcher>,
) -> Result<Value, CommandError> {
    let manager = sidecar.inner().clone();
    let result = blocking_sidecar_call(sidecar, "load_vault", json!({})).await?;
    watcher.watch(manager.resolved_vault_path());
    Ok(result)
}

#[tauri::command]
pub async fn reload_vault(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "reload_vault", json!({})).await
}

sidecar_passthrough!(create_vault, "create_vault");

#[tauri::command]
pub async fn get_learner_profile(
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_learner_profile", json!({})).await
}

sidecar_passthrough!(set_learner_profile, "set_learner_profile");

#[tauri::command]
pub async fn get_runtime_health(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_runtime_health", json!({})).await
}

#[tauri::command]
pub async fn get_config(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_config", json!({})).await
}

sidecar_passthrough!(start_session, "start_session");

#[tauri::command]
pub async fn get_session(
    session_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_session", json!({"sessionId": session_id})).await
}

sidecar_passthrough!(update_session_checkpoint, "update_session_checkpoint");

#[tauri::command]
pub async fn clear_session_checkpoint(
    session_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "clear_session_checkpoint",
        json!({"sessionId": session_id}),
    )
    .await
}

#[tauri::command]
pub async fn end_session(
    session_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "end_session", json!({"sessionId": session_id})).await
}

sidecar_passthrough!(get_today_queue, "get_today_queue");

#[tauri::command]
pub async fn get_queue_revision(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_queue_revision", json!({})).await
}

#[tauri::command]
pub async fn explain_practice_item(
    practice_item_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "explain_practice_item",
        json!({"practiceItemId": practice_item_id}),
    )
    .await
}

#[tauri::command]
pub async fn open_queue_item(
    practice_item_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "open_queue_item",
        json!({"practiceItemId": practice_item_id}),
    )
    .await
}

#[tauri::command]
pub async fn get_practice_item(
    practice_item_id: String,
    session_id: Option<String>,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "get_practice_item",
        json!({"practiceItemId": practice_item_id, "sessionId": session_id}),
    )
    .await
}

#[tauri::command]
pub async fn get_probe_contract(
    practice_item_id: String,
    session_id: Option<String>,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "get_probe_contract",
        json!({"practiceItemId": practice_item_id, "sessionId": session_id}),
    )
    .await
}

#[tauri::command]
pub async fn stop_probe_diagnosing(
    practice_item_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "stop_probe_diagnosing",
        json!({"practiceItemId": practice_item_id}),
    )
    .await
}

#[tauri::command]
pub async fn get_next_probe_item(
    learning_object_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "get_next_probe_item",
        json!({"learningObjectId": learning_object_id}),
    )
    .await
}

sidecar_passthrough!(save_practice_draft, "save_practice_draft");

sidecar_passthrough!(recover_practice_submission, "recover_practice_submission");

sidecar_passthrough!(
    acknowledge_practice_submission,
    "acknowledge_practice_submission"
);

sidecar_passthrough!(submit_attempt, "submit_attempt");

sidecar_passthrough!(submit_dont_know, "submit_dont_know");

sidecar_passthrough!(skip_practice_item, "skip_practice_item");

#[tauri::command]
pub async fn get_feedback(
    attempt_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_feedback", json!({"attemptId": attempt_id})).await
}

#[tauri::command]
pub async fn get_attempt(
    attempt_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_attempt", json!({"attemptId": attempt_id})).await
}

#[tauri::command]
pub async fn get_attempt_trace_evidence(
    attempt_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "get_attempt_trace_evidence",
        json!({"attemptId": attempt_id}),
    )
    .await
}

#[tauri::command]
pub async fn get_grading_clarification(
    attempt_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "get_grading_clarification",
        json!({"attemptId": attempt_id}),
    )
    .await
}

sidecar_passthrough!(answer_grading_clarification, "answer_grading_clarification");

#[tauri::command]
pub async fn inspect_entity(
    id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "inspect_entity", json!({"id": id})).await
}

#[tauri::command]
pub async fn get_concept_graph(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_concept_graph", json!({})).await
}

#[tauri::command]
pub async fn get_vault_tree(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_vault_tree", json!({})).await
}

#[tauri::command]
pub async fn get_recent_ingests(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_recent_ingests", json!({})).await
}

sidecar_passthrough!(classify_ingest_source, "classify_ingest_source");

sidecar_passthrough!(start_ingest, "start_ingest");

#[tauri::command]
pub async fn get_ingest_job(
    job_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_ingest_job", json!({"jobId": job_id})).await
}

#[tauri::command]
pub async fn get_ingest_jobs(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_ingest_jobs", json!({})).await
}

#[tauri::command]
pub async fn cancel_ingest(
    job_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "cancel_ingest", json!({"jobId": job_id})).await
}

sidecar_passthrough!(start_import_batch, "start_import_batch");

#[tauri::command]
pub async fn get_ingest_batch(
    batch_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_ingest_batch", json!({"batchId": batch_id})).await
}

sidecar_passthrough!(list_ingest_batches, "list_ingest_batches");

#[tauri::command]
pub async fn cancel_ingest_batch(
    batch_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "cancel_ingest_batch", json!({"batchId": batch_id})).await
}

#[tauri::command]
pub async fn resume_ingest_batch(
    batch_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "resume_ingest_batch", json!({"batchId": batch_id})).await
}

sidecar_passthrough!(retry_synthesis, "retry_synthesis");

#[tauri::command]
pub async fn get_synthesis_candidate(
    batch_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "get_synthesis_candidate",
        json!({"batchId": batch_id}),
    )
    .await
}

#[tauri::command]
pub async fn get_source_library(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_source_library", json!({})).await
}

#[tauri::command]
pub async fn preview_source_deletion(
    source_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "preview_source_deletion",
        json!({"sourceId": source_id}),
    )
    .await
}

#[tauri::command]
pub async fn delete_source(
    source_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "delete_source", json!({"sourceId": source_id})).await
}

// ── ING M3: outline, unit selection, budget planning, repair (§3/§5.3/§8.6) ──

#[tauri::command]
pub async fn get_source_outline(
    extraction_ref: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "get_source_outline",
        json!({"extractionRef": extraction_ref}),
    )
    .await
}

sidecar_passthrough!(get_selection_preview, "get_selection_preview");

sidecar_passthrough!(get_effective_outline, "get_effective_outline");

sidecar_passthrough!(save_unit_selection, "save_unit_selection");

sidecar_passthrough!(get_acquisition_preview, "get_acquisition_preview");

sidecar_passthrough!(get_build_plan, "get_build_plan");

#[tauri::command]
pub async fn list_source_sets(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "list_source_sets", json!({})).await
}

#[tauri::command]
pub async fn get_source_set(
    source_set_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "get_source_set",
        json!({"sourceSetId": source_set_id}),
    )
    .await
}

sidecar_passthrough!(upsert_source_set, "upsert_source_set");

#[tauri::command]
pub async fn get_source_coverage(
    source_set_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "get_source_coverage",
        json!({"sourceSetId": source_set_id}),
    )
    .await
}

sidecar_passthrough!(start_inventory, "start_inventory");

sidecar_passthrough!(create_study_map, "create_study_map");

sidecar_passthrough!(build_study_map, "build_study_map");

sidecar_passthrough!(append_source, "append_source");

sidecar_passthrough!(refresh_revision, "refresh_revision");

sidecar_passthrough!(maintenance_feed, "maintenance_feed");

#[tauri::command]
pub async fn get_measurement_health(
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_measurement_health", json!({})).await
}

// Enqueues authoring for the commissioning queue's gaps. Returns as soon as the
// batch is queued -- the generation itself runs on the sidecar's job worker, so
// this call does not hold the single RPC channel for the length of a model run.
sidecar_passthrough!(
    generate_commissioning_practice,
    "generate_commissioning_practice"
);

/// Counts behind the nav-tab badges. Cheap by construction; safe to call on the
/// same events that already refresh the vault.
#[tauri::command]
pub async fn get_review_counts(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_review_counts", json!({})).await
}

sidecar_passthrough!(
    schedule_certification_cold_probes,
    "schedule_certification_cold_probes"
);

sidecar_passthrough!(
    transition_causal_probe_candidate,
    "transition_causal_probe_candidate"
);

sidecar_passthrough!(apply_integration_backfill, "apply_integration_backfill");

sidecar_passthrough!(maintenance_notice_action, "maintenance_notice_action");

sidecar_passthrough!(list_source_conflicts, "list_source_conflicts");

sidecar_passthrough!(resolve_source_conflict, "resolve_source_conflict");

sidecar_passthrough!(exam_readiness, "exam_readiness");

sidecar_passthrough!(start_extraction_repair, "start_extraction_repair");

#[tauri::command]
pub async fn read_vault_file(
    path: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "read_vault_file", json!({ "path": path })).await
}

#[tauri::command]
pub async fn write_vault_file(
    path: String,
    body: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "write_vault_file",
        json!({ "path": path, "body": body }),
    )
    .await
}

sidecar_passthrough!(create_vault_file, "create_vault_file");

sidecar_passthrough!(sqlite_tables, "sqlite_tables");

sidecar_passthrough!(sqlite_table, "sqlite_table");

sidecar_passthrough!(sqlite_exec, "sqlite_exec");

sidecar_passthrough!(sqlite_update_cell, "sqlite_update_cell");

sidecar_passthrough!(sqlite_insert_row, "sqlite_insert_row");

sidecar_passthrough!(sqlite_delete_row, "sqlite_delete_row");

#[tauri::command]
pub async fn get_proposals(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_proposals", json!({})).await
}

#[tauri::command]
pub async fn get_entity_provenance(
    entity_type: String,
    entity_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "get_entity_provenance",
        json!({"entityType": entity_type, "entityId": entity_id}),
    )
    .await
}

sidecar_passthrough!(plan_quick_add, "plan_quick_add");

sidecar_passthrough!(confirm_quick_add, "confirm_quick_add");

sidecar_passthrough!(get_span_view, "get_span_view");

sidecar_passthrough!(get_subject_registry, "get_subject_registry");

sidecar_passthrough!(propose_facet_merge, "propose_facet_merge");

sidecar_passthrough!(accept_proposal_items, "accept_proposal_items");

sidecar_passthrough!(reject_proposal_items, "reject_proposal_items");

sidecar_passthrough!(reset_proposal_items, "reset_proposal_items");

sidecar_passthrough!(edit_proposal_item, "edit_proposal_item");

sidecar_passthrough!(
    refresh_proposal_item_validation,
    "refresh_proposal_item_validation"
);

sidecar_passthrough!(delete_proposal_item, "delete_proposal_item");

sidecar_passthrough!(trigger_regrade, "trigger_regrade");

sidecar_passthrough!(add_error_event, "add_error_event");

sidecar_passthrough!(trigger_followup, "trigger_followup");

sidecar_passthrough!(rate_followup, "rate_followup");

sidecar_passthrough!(report_unresolved_cause, "report_unresolved_cause");

sidecar_passthrough!(submit_eliciting_response, "submit_eliciting_response");

sidecar_passthrough!(contest_causal_diagnosis, "contest_causal_diagnosis");

// ── P2 causal repair orchestration (spec_causal_attribution_v1 §6) ──
// One orchestration service, four learner-facing RPCs: read the typed repair
// status, take the quick check, defer the offer ("Not now"), or ask to be
// taught under ambiguity. `causal_repair_status` is a pure read — it records
// the decision receipt but never mints a remediation episode.

sidecar_passthrough!(causal_repair_status, "causal_repair_status");

sidecar_passthrough!(causal_probe_offer_action, "causal_probe_offer_action");

sidecar_passthrough!(causal_probe_defer, "causal_probe_defer");

sidecar_passthrough!(causal_teach_me_now, "causal_teach_me_now");

sidecar_passthrough!(start_primed_retry, "start_primed_retry");

sidecar_passthrough!(start_guided_redo, "start_guided_redo");

#[tauri::command]
pub async fn run_cli_command(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    if is_populate_goal_command(&input) {
        blocking_isolated_cli_call(sidecar, input).await
    } else {
        blocking_sidecar_call(sidecar, "run_cli_command", input).await
    }
}

#[tauri::command]
pub async fn get_facet_mastery(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_facet_mastery", json!({})).await
}

#[tauri::command]
pub async fn get_knowledge_map(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_knowledge_map", json!({})).await
}

// ── KM3b: provenance UI (§9.6) — attempt trace, capability grid, evidence timeline ──

#[tauri::command]
pub async fn get_attempt_trace(
    attempt_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "get_attempt_trace",
        json!({ "attemptId": attempt_id }),
    )
    .await
}

#[tauri::command]
pub async fn get_capability_grid(
    learning_object_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "get_capability_grid",
        json!({ "learningObjectId": learning_object_id }),
    )
    .await
}

#[tauri::command]
pub async fn get_facet_evidence_timeline(
    facet_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "get_facet_evidence_timeline",
        json!({ "facetId": facet_id }),
    )
    .await
}

#[tauri::command]
pub async fn get_knowledge_map_history(
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_knowledge_map_history", json!({})).await
}

#[tauri::command]
pub async fn set_grading_provider(
    provider: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "set_grading_provider",
        json!({ "provider": provider }),
    )
    .await
}

#[tauri::command]
pub async fn get_settings(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_settings", json!({})).await
}

sidecar_passthrough!(update_ai_settings, "update_ai_settings");

#[tauri::command]
pub async fn set_openrouter_api_key(
    api_key: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "set_openrouter_api_key",
        json!({ "apiKey": api_key }),
    )
    .await
}

sidecar_passthrough!(update_ingest_settings, "update_ingest_settings");

#[tauri::command]
pub async fn set_transcription_api_key(
    api_key: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "set_transcription_api_key",
        json!({ "apiKey": api_key }),
    )
    .await
}

#[tauri::command]
pub async fn get_animation_runtime(
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_animation_runtime", json!({})).await
}

sidecar_passthrough!(request_concept_animation, "request_concept_animation");

#[tauri::command]
pub async fn get_concept_animation_status(
    animation_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "get_concept_animation_status",
        json!({ "animationId": animation_id }),
    )
    .await
}

#[tauri::command]
pub async fn list_concept_animations(
    concept_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "list_concept_animations",
        json!({ "conceptId": concept_id }),
    )
    .await
}

sidecar_passthrough!(ask_tutor_question, "ask_tutor_question");

sidecar_passthrough!(preview_tutor_opening, "preview_tutor_opening");

sidecar_passthrough!(rate_tutor_answer, "rate_tutor_answer");

sidecar_passthrough!(save_tutor_answer_note, "save_tutor_answer_note");

sidecar_passthrough!(get_tutor_transcript, "get_tutor_transcript");

sidecar_passthrough!(promote_tutor_question, "promote_tutor_question");

sidecar_passthrough!(author_practice_item, "author_practice_item");

sidecar_passthrough!(request_rung_variant, "request_rung_variant");

sidecar_passthrough!(get_rung_variant_status, "get_rung_variant_status");

sidecar_passthrough!(remint_diagnostic_probe, "remint_diagnostic_probe");

sidecar_passthrough!(edit_practice_item, "edit_practice_item");

sidecar_passthrough!(retire_practice_item, "retire_practice_item");

sidecar_passthrough!(split_practice_item, "split_practice_item");

sidecar_passthrough!(list_question_queue, "list_question_queue");

sidecar_passthrough!(resolve_question_event, "resolve_question_event");

sidecar_passthrough!(request_teach_back, "request_teach_back");

sidecar_passthrough!(start_teach_back, "start_teach_back");

sidecar_passthrough!(submit_teach_back_turn, "submit_teach_back_turn");

#[tauri::command]
pub async fn goals_list(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "goals_list", json!({})).await
}

#[tauri::command]
pub async fn get_goal_report(
    goal_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_goal_report", json!({"goalId": goal_id})).await
}

sidecar_passthrough!(get_goal_report_series, "get_goal_report_series");

sidecar_passthrough!(goal_feasibility, "goal_feasibility");

#[tauri::command]
pub async fn get_overconfidence_list(
    goal_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "get_overconfidence_list",
        json!({"goalId": goal_id}),
    )
    .await
}

sidecar_passthrough!(get_reentry_summary, "get_reentry_summary");

sidecar_passthrough!(get_decay_pressure, "get_decay_pressure");

sidecar_passthrough!(start_overconfidence_probe, "start_overconfidence_probe");

sidecar_passthrough!(create_goal, "create_goal");

sidecar_passthrough!(generate_starter_practice, "generate_starter_practice");

sidecar_passthrough!(update_goal_status, "update_goal_status");

sidecar_passthrough!(update_goal_intent, "update_goal_intent");

#[tauri::command]
pub async fn get_exam_status(
    goal_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_exam_status", json!({"goalId": goal_id})).await
}

sidecar_passthrough!(start_exam, "start_exam");

sidecar_passthrough!(submit_exam_answer, "submit_exam_answer");

sidecar_passthrough!(start_calibration_session, "start_calibration_session");

#[tauri::command]
pub async fn get_calibration_session(
    calibration_session_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "get_calibration_session",
        json!({"calibrationSessionId": calibration_session_id}),
    )
    .await
}

#[tauri::command]
pub async fn stop_calibration_session(
    calibration_session_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "stop_calibration_session",
        json!({"calibrationSessionId": calibration_session_id}),
    )
    .await
}

sidecar_passthrough!(finish_exam, "finish_exam");

#[tauri::command]
pub async fn begin_probe_dialogue(
    learning_object_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "begin_probe_dialogue",
        json!({"learningObjectId": learning_object_id}),
    )
    .await
}

#[tauri::command]
pub async fn next_probe_dialogue_turn(
    dialogue_state: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "next_probe_dialogue_turn",
        json!({"dialogueState": dialogue_state}),
    )
    .await
}

#[tauri::command]
pub async fn record_probe_dialogue_turn(
    dialogue_state: String,
    presentation_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "record_probe_dialogue_turn",
        json!({"dialogueState": dialogue_state, "presentationId": presentation_id}),
    )
    .await
}

#[tauri::command]
pub async fn end_probe_dialogue(
    dialogue_state: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "end_probe_dialogue",
        json!({"dialogueState": dialogue_state}),
    )
    .await
}

sidecar_passthrough!(present_claims, "present_claims");

sidecar_passthrough!(respond_claim, "respond_claim");

#[tauri::command]
pub async fn dismiss_claim(
    presentation_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "dismiss_claim",
        json!({"presentationId": presentation_id}),
    )
    .await
}

#[tauri::command]
pub async fn export_claims(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "export_claims", json!({})).await
}

#[tauri::command]
pub async fn purge_claims(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "purge_claims", json!({})).await
}

#[tauri::command]
pub async fn get_review_log(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_review_log", json!({})).await
}

#[tauri::command]
pub async fn start_remediation(
    misconception_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "start_remediation",
        json!({"misconceptionId": misconception_id}),
    )
    .await
}

#[tauri::command]
pub async fn prescribe_remediation(
    episode_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "prescribe_remediation",
        json!({"episodeId": episode_id}),
    )
    .await
}

#[tauri::command]
pub async fn start_remediation_treatment(
    episode_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "start_remediation_treatment",
        json!({"episodeId": episode_id}),
    )
    .await
}

#[tauri::command]
pub async fn get_remediation(
    episode_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_remediation", json!({"episodeId": episode_id})).await
}

sidecar_passthrough!(get_forecast_track_record, "get_forecast_track_record");

#[tauri::command]
pub async fn get_answer_calibration(
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_answer_calibration", json!({})).await
}

sidecar_passthrough!(propose_graph_edits, "propose_graph_edits");

sidecar_passthrough!(queue_restructure_request, "queue_restructure_request");

sidecar_passthrough!(resolve_edge_direction, "resolve_edge_direction");

#[tauri::command]
pub async fn get_facet_detail(
    facet_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_facet_detail", json!({"facetId": facet_id})).await
}

#[tauri::command]
pub async fn list_facets(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "list_facets", json!({})).await
}

sidecar_passthrough!(preview_knowledge_map, "preview_knowledge_map");

sidecar_passthrough!(preview_blueprint_readiness, "preview_blueprint_readiness");

// ── P2 narrow golden path (spec_p2 §9; spec_tauri_ui §3 P2 rows) ──────────────
// The dotted sidecar method names (golden_path.* / blueprint.* / diagnostic.* /
// ladder.* / practice_pool.* / reader.*) cannot be Tauri command identifiers, so
// each command forwards its `input` Value straight through to the dotted method.

// blueprint.* (exemplar selection + blueprint review)
sidecar_passthrough!(blueprint_register, "blueprint.register");
sidecar_passthrough!(blueprint_review, "blueprint.review");
sidecar_passthrough!(blueprint_get_version, "blueprint.get_version");
sidecar_passthrough!(
    blueprint_discover_candidates,
    "blueprint.discover_candidates"
);
sidecar_passthrough!(blueprint_compose_draft, "blueprint.compose_draft");

// golden_path.* spine (atomic confirmation + run state machine)
sidecar_passthrough!(golden_path_confirm, "golden_path.confirm");
sidecar_passthrough!(golden_path_run_status, "golden_path.run_status");
sidecar_passthrough!(golden_path_list_runs, "golden_path.list_runs");
sidecar_passthrough!(golden_path_advance, "golden_path.advance");

// golden_path.* assessment + restoration + milestone / depth invitation
sidecar_passthrough!(golden_path_assess_open, "golden_path.assess_open");
sidecar_passthrough!(golden_path_assess_submit, "golden_path.assess_submit");
sidecar_passthrough!(golden_path_assess_result, "golden_path.assess_result");
sidecar_passthrough!(golden_path_restore, "golden_path.restore");
sidecar_passthrough!(golden_path_boundary_diff, "golden_path.boundary_diff");
sidecar_passthrough!(golden_path_depth_invitation, "golden_path.depth_invitation");
sidecar_passthrough!(golden_path_accept_edge, "golden_path.accept_edge");
sidecar_passthrough!(golden_path_decline_edge, "golden_path.decline_edge");

// diagnostic.* (pre-authored pack + bounded baseline + two-tier triage)
sidecar_passthrough!(diagnostic_pack_assemble, "diagnostic.pack_assemble");
sidecar_passthrough!(diagnostic_pack_admit, "diagnostic.pack_admit");
sidecar_passthrough!(diagnostic_pack_review, "diagnostic.pack_review");
sidecar_passthrough!(diagnostic_pack_list, "diagnostic.pack_list");
sidecar_passthrough!(diagnostic_baseline_enter, "diagnostic.baseline_enter");
sidecar_passthrough!(diagnostic_boundary_view, "diagnostic.boundary_view");
sidecar_passthrough!(diagnostic_triage, "diagnostic.triage");
sidecar_passthrough!(diagnostic_triage_status, "diagnostic.triage_status");
sidecar_passthrough!(diagnostic_triage_decide, "diagnostic.triage_decide");
sidecar_passthrough!(diagnostic_triage_override, "diagnostic.triage_override");

// ladder.* (pattern ladder) + practice_pool.* (rotating practice)
sidecar_passthrough!(ladder_policy, "ladder.policy");
sidecar_passthrough!(ladder_status, "ladder.status");
sidecar_passthrough!(ladder_enter, "ladder.enter");
sidecar_passthrough!(ladder_advance, "ladder.advance");
sidecar_passthrough!(practice_pool_assemble, "practice_pool.assemble");
sidecar_passthrough!(practice_pool_admit_surface, "practice_pool.admit_surface");
sidecar_passthrough!(practice_pool_review, "practice_pool.review");
sidecar_passthrough!(practice_pool_status, "practice_pool.status");
sidecar_passthrough!(practice_pool_next_surface, "practice_pool.next_surface");
sidecar_passthrough!(practice_pool_for_run, "practice_pool.for_run");
sidecar_passthrough!(practice_pool_seed_for_run, "practice_pool.seed_for_run");
sidecar_passthrough!(practice_pool_admit_anchor, "practice_pool.admit_anchor");

// adjudication.* (diagnosis adjudication store, spec_diagnostic_augmentation §2 A4):
// the queue that decides which attempt is worth a verdict, the append-only write
// path, and the B5 scoreboard the overlay tallies at the top.
sidecar_passthrough!(adjudication_queue, "adjudication.queue");
sidecar_passthrough!(adjudication_record, "adjudication.record");
sidecar_passthrough!(adjudication_scoreboard, "adjudication.scoreboard");

// reader.* (minimal bidirectional reader dialogue, U-033)
sidecar_passthrough!(reader_ask, "reader.ask");
sidecar_passthrough!(reader_ask_history, "reader.ask_history");
sidecar_passthrough!(reader_set_answer_mode, "reader.set_answer_mode");
sidecar_passthrough!(reader_present_question, "reader.present_question");
sidecar_passthrough!(reader_submit_question, "reader.submit_question");
sidecar_passthrough!(reader_skip_question, "reader.skip_question");
sidecar_passthrough!(reader_choose_disposition, "reader.choose_disposition");
sidecar_passthrough!(reader_restore_source, "reader.restore_source");
sidecar_passthrough!(reader_routing_prior, "reader.routing_prior");
sidecar_passthrough!(reader_prompt_contract, "reader.prompt_contract");
// reader.* (P3 slice 1: render views, block health, annotations, capture/outbox)
sidecar_passthrough!(reader_render_view, "reader.render_view");
sidecar_passthrough!(reader_guide_plan, "reader.guide_plan");
sidecar_passthrough!(reader_pdf_view, "reader.pdf_view");
sidecar_passthrough!(reader_watch_plan, "reader.watch_plan");
sidecar_passthrough!(
    reader_author_section_question,
    "reader.author_section_question"
);
sidecar_passthrough!(
    reader_authored_question_action,
    "reader.authored_question_action"
);
sidecar_passthrough!(reader_get_progress, "reader.get_progress");
sidecar_passthrough!(reader_mark_section_progress, "reader.mark_section_progress");
sidecar_passthrough!(
    reader_escalate_authored_question,
    "reader.escalate_authored_question"
);
sidecar_passthrough!(reader_import_exercise, "reader.import_exercise");
sidecar_passthrough!(
    reader_exercise_import_status,
    "reader.exercise_import_status"
);
sidecar_passthrough!(reader_search_sources, "reader.search_sources");
sidecar_passthrough!(reader_manual_anchor, "reader.manual_anchor");
sidecar_passthrough!(reader_block_health, "reader.block_health");
sidecar_passthrough!(reader_block_original_region, "reader.block_original_region");
sidecar_passthrough!(reader_translate_selection, "reader.translate_selection");
sidecar_passthrough!(reader_capture, "reader.capture");
sidecar_passthrough!(reader_create_annotation, "reader.create_annotation");
sidecar_passthrough!(reader_edit_annotation, "reader.edit_annotation");
sidecar_passthrough!(
    reader_delete_intent_annotation,
    "reader.delete_intent_annotation"
);
sidecar_passthrough!(reader_reanchor, "reader.reanchor");
sidecar_passthrough!(reader_annotation_history, "reader.annotation_history");
sidecar_passthrough!(reader_source_annotations, "reader.source_annotations");
sidecar_passthrough!(reader_outbox_status, "reader.outbox_status");
sidecar_passthrough!(reader_drain_outbox, "reader.drain_outbox");
// P3 slice 2: palette + demand-paged synthesis + source objects.
sidecar_passthrough!(reader_invoke_preset, "reader.invoke_preset");
sidecar_passthrough!(reader_set_mode, "reader.set_mode");
sidecar_passthrough!(reader_question_control, "reader.question_control");
sidecar_passthrough!(reader_enqueue_request, "reader.enqueue_request");
sidecar_passthrough!(reader_request_status, "reader.request_status");
sidecar_passthrough!(reader_cancel_request, "reader.cancel_request");
sidecar_passthrough!(reader_retry_request, "reader.retry_request");
sidecar_passthrough!(reader_source_requests, "reader.source_requests");
sidecar_passthrough!(reader_drain_requests, "reader.drain_requests");
sidecar_passthrough!(reader_source_objects, "reader.source_objects");
sidecar_passthrough!(reader_review_source_object, "reader.review_source_object");
sidecar_passthrough!(reader_link_relation, "reader.link_relation");
sidecar_passthrough!(reader_proposal_inbox, "reader.proposal_inbox");
sidecar_passthrough!(reader_accept_proposal, "reader.accept_proposal");
sidecar_passthrough!(reader_reject_proposal, "reader.reject_proposal");
// P3 slice 3: authoring + coach + maintenance, arcs + depth + primes, restoration.
sidecar_passthrough!(reader_author_qa, "reader.author_qa");
sidecar_passthrough!(reader_coach_lint, "reader.coach_lint");
sidecar_passthrough!(reader_maintain, "reader.maintain");
sidecar_passthrough!(reader_arc, "reader.arc");
sidecar_passthrough!(reader_set_depth_policy, "reader.set_depth_policy");
sidecar_passthrough!(reader_pause_arc, "reader.pause_arc");
sidecar_passthrough!(reader_shrink_envelope, "reader.shrink_envelope");
sidecar_passthrough!(reader_prime, "reader.prime");
sidecar_passthrough!(reader_restore, "reader.restore");

#[cfg(test)]
mod tests {
    use super::{cli_command_succeeded, is_populate_goal_command};
    use serde_json::json;

    #[test]
    fn populate_goal_cli_calls_are_classified_as_isolated() {
        assert!(is_populate_goal_command(
            &json!({"argv": ["populate-goal", "goal_linear_algebra_ml"]})
        ));
        assert!(is_populate_goal_command(
            &json!({"argv": ["learnloop", "populate-goal", "goal_linear_algebra_ml", "--json"]})
        ));
    }

    #[test]
    fn other_cli_calls_stay_on_the_primary_sidecar() {
        assert!(!is_populate_goal_command(
            &json!({"argv": ["generate-practice", "--json"]})
        ));
        assert!(!is_populate_goal_command(&json!({"argv": []})));
        assert!(!is_populate_goal_command(&json!({})));
    }

    #[test]
    fn successful_cli_results_are_detected_from_the_camel_case_contract() {
        assert!(cli_command_succeeded(&json!({"exitCode": 0})));
        assert!(!cli_command_succeeded(&json!({"exitCode": 1})));
        assert!(!cli_command_succeeded(&json!({"exit_code": 0})));
    }
}
