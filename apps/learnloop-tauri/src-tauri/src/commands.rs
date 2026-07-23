use crate::errors::CommandError;
use crate::sidecar::SidecarManager;
use serde_json::{json, Value};
use tauri::State;

async fn blocking_sidecar_call(
    sidecar: State<'_, SidecarManager>,
    method: &'static str,
    params: Value,
) -> Result<Value, CommandError> {
    let sidecar = sidecar.inner().clone();
    tauri::async_runtime::spawn_blocking(move || sidecar.call(method, params))
        .await
        .map_err(|err| CommandError::internal(format!("Sidecar task failed: {err}")))?
}

async fn blocking_select_vault(
    sidecar: State<'_, SidecarManager>,
    path: Option<String>,
) -> Result<Value, CommandError> {
    let sidecar = sidecar.inner().clone();
    tauri::async_runtime::spawn_blocking(move || sidecar.select_vault(path))
        .await
        .map_err(|err| CommandError::internal(format!("Sidecar task failed: {err}")))?
}

#[tauri::command]
pub async fn select_vault(
    path: Option<String>,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_select_vault(sidecar, path).await
}

#[tauri::command]
pub async fn load_vault(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "load_vault", json!({})).await
}

#[tauri::command]
pub async fn reload_vault(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "reload_vault", json!({})).await
}

#[tauri::command]
pub async fn create_vault(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "create_vault", input).await
}

#[tauri::command]
pub async fn get_learner_profile(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_learner_profile", json!({})).await
}

#[tauri::command]
pub async fn set_learner_profile(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "set_learner_profile", input).await
}

#[tauri::command]
pub async fn get_runtime_health(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_runtime_health", json!({})).await
}

#[tauri::command]
pub async fn get_config(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_config", json!({})).await
}

#[tauri::command]
pub async fn start_session(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "start_session", input).await
}

#[tauri::command]
pub async fn get_session(
    session_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_session", json!({"sessionId": session_id})).await
}

#[tauri::command]
pub async fn update_session_checkpoint(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "update_session_checkpoint", input).await
}

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

#[tauri::command]
pub async fn get_today_queue(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_today_queue", input).await
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
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(
        sidecar,
        "get_practice_item",
        json!({"practiceItemId": practice_item_id}),
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

#[tauri::command]
pub async fn save_practice_draft(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "save_practice_draft", input).await
}

#[tauri::command]
pub async fn submit_attempt(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "submit_attempt", input).await
}

#[tauri::command]
pub async fn submit_dont_know(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "submit_dont_know", input).await
}

#[tauri::command]
pub async fn skip_practice_item(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "skip_practice_item", input).await
}

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

#[tauri::command]
pub async fn classify_ingest_source(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "classify_ingest_source", input).await
}

#[tauri::command]
pub async fn start_ingest(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "start_ingest", input).await
}

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

#[tauri::command]
pub async fn start_import_batch(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "start_import_batch", input).await
}

#[tauri::command]
pub async fn get_ingest_batch(
    batch_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_ingest_batch", json!({"batchId": batch_id})).await
}

#[tauri::command]
pub async fn list_ingest_batches(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "list_ingest_batches", input).await
}

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

#[tauri::command]
pub async fn retry_synthesis(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "retry_synthesis", input).await
}

#[tauri::command]
pub async fn get_synthesis_candidate(
    batch_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_synthesis_candidate", json!({"batchId": batch_id})).await
}

#[tauri::command]
pub async fn get_source_library(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_source_library", json!({})).await
}

// ── ING M3: outline, unit selection, budget planning, repair (§3/§5.3/§8.6) ──

#[tauri::command]
pub async fn get_source_outline(
    extraction_ref: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_source_outline", json!({"extractionRef": extraction_ref})).await
}

#[tauri::command]
pub async fn get_selection_preview(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_selection_preview", input).await
}

#[tauri::command]
pub async fn get_effective_outline(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_effective_outline", input).await
}

#[tauri::command]
pub async fn save_unit_selection(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "save_unit_selection", input).await
}

#[tauri::command]
pub async fn get_acquisition_preview(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_acquisition_preview", input).await
}

#[tauri::command]
pub async fn get_build_plan(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_build_plan", input).await
}

#[tauri::command]
pub async fn list_source_sets(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "list_source_sets", json!({})).await
}

#[tauri::command]
pub async fn get_source_set(
    source_set_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_source_set", json!({"sourceSetId": source_set_id})).await
}

#[tauri::command]
pub async fn upsert_source_set(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "upsert_source_set", input).await
}

#[tauri::command]
pub async fn get_source_coverage(
    source_set_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_source_coverage", json!({"sourceSetId": source_set_id})).await
}

#[tauri::command]
pub async fn start_inventory(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "start_inventory", input).await
}

#[tauri::command]
pub async fn create_study_map(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "create_study_map", input).await
}

#[tauri::command]
pub async fn build_study_map(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "build_study_map", input).await
}

#[tauri::command]
pub async fn append_source(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "append_source", input).await
}

#[tauri::command]
pub async fn refresh_revision(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "refresh_revision", input).await
}

#[tauri::command]
pub async fn maintenance_feed(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "maintenance_feed", input).await
}

#[tauri::command]
pub async fn maintenance_notice_action(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "maintenance_notice_action", input).await
}

#[tauri::command]
pub async fn list_source_conflicts(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "list_source_conflicts", input).await
}

#[tauri::command]
pub async fn resolve_source_conflict(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "resolve_source_conflict", input).await
}

#[tauri::command]
pub async fn exam_readiness(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "exam_readiness", input).await
}

#[tauri::command]
pub async fn start_extraction_repair(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "start_extraction_repair", input).await
}

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
    blocking_sidecar_call(sidecar, "write_vault_file", json!({ "path": path, "body": body })).await
}

#[tauri::command]
pub async fn create_vault_file(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "create_vault_file", input).await
}

#[tauri::command]
pub async fn sqlite_tables(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "sqlite_tables", input).await
}

#[tauri::command]
pub async fn sqlite_table(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "sqlite_table", input).await
}

#[tauri::command]
pub async fn sqlite_exec(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "sqlite_exec", input).await
}

#[tauri::command]
pub async fn sqlite_update_cell(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "sqlite_update_cell", input).await
}

#[tauri::command]
pub async fn sqlite_insert_row(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "sqlite_insert_row", input).await
}

#[tauri::command]
pub async fn sqlite_delete_row(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "sqlite_delete_row", input).await
}

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

#[tauri::command]
pub async fn plan_quick_add(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "plan_quick_add", input).await
}

#[tauri::command]
pub async fn confirm_quick_add(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "confirm_quick_add", input).await
}

#[tauri::command]
pub async fn get_span_view(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_span_view", input).await
}

#[tauri::command]
pub async fn get_subject_registry(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_subject_registry", input).await
}

#[tauri::command]
pub async fn propose_facet_merge(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "propose_facet_merge", input).await
}

#[tauri::command]
pub async fn accept_proposal_items(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "accept_proposal_items", input).await
}

#[tauri::command]
pub async fn reject_proposal_items(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "reject_proposal_items", input).await
}

#[tauri::command]
pub async fn reset_proposal_items(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "reset_proposal_items", input).await
}

#[tauri::command]
pub async fn edit_proposal_item(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "edit_proposal_item", input).await
}

#[tauri::command]
pub async fn refresh_proposal_item_validation(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "refresh_proposal_item_validation", input).await
}

#[tauri::command]
pub async fn delete_proposal_item(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "delete_proposal_item", input).await
}

#[tauri::command]
pub async fn trigger_regrade(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "trigger_regrade", input).await
}

#[tauri::command]
pub async fn add_error_event(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "add_error_event", input).await
}

#[tauri::command]
pub async fn trigger_followup(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "trigger_followup", input).await
}

#[tauri::command]
pub async fn rate_followup(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "rate_followup", input).await
}

#[tauri::command]
pub async fn start_primed_retry(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "start_primed_retry", input).await
}

#[tauri::command]
pub async fn run_cli_command(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "run_cli_command", input).await
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
    blocking_sidecar_call(sidecar, "get_attempt_trace", json!({ "attemptId": attempt_id })).await
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
pub async fn get_knowledge_map_history(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_knowledge_map_history", json!({})).await
}

#[tauri::command]
pub async fn set_grading_provider(
    provider: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "set_grading_provider", json!({ "provider": provider })).await
}

#[tauri::command]
pub async fn ask_tutor_question(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "ask_tutor_question", input).await
}

#[tauri::command]
pub async fn preview_tutor_opening(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "preview_tutor_opening", input).await
}

#[tauri::command]
pub async fn rate_tutor_answer(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "rate_tutor_answer", input).await
}

#[tauri::command]
pub async fn save_tutor_answer_note(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "save_tutor_answer_note", input).await
}

#[tauri::command]
pub async fn get_tutor_transcript(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_tutor_transcript", input).await
}

#[tauri::command]
pub async fn promote_tutor_question(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "promote_tutor_question", input).await
}

#[tauri::command]
pub async fn author_practice_item(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "author_practice_item", input).await
}

#[tauri::command]
pub async fn request_rung_variant(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "request_rung_variant", input).await
}

#[tauri::command]
pub async fn get_rung_variant_status(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_rung_variant_status", input).await
}

#[tauri::command]
pub async fn edit_practice_item(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "edit_practice_item", input).await
}

#[tauri::command]
pub async fn retire_practice_item(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "retire_practice_item", input).await
}

#[tauri::command]
pub async fn split_practice_item(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "split_practice_item", input).await
}

#[tauri::command]
pub async fn list_question_queue(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "list_question_queue", input).await
}

#[tauri::command]
pub async fn resolve_question_event(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "resolve_question_event", input).await
}

#[tauri::command]
pub async fn request_teach_back(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "request_teach_back", input).await
}

#[tauri::command]
pub async fn start_teach_back(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "start_teach_back", input).await
}

#[tauri::command]
pub async fn submit_teach_back_turn(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "submit_teach_back_turn", input).await
}

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

#[tauri::command]
pub async fn get_goal_report_series(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_goal_report_series", input).await
}

#[tauri::command]
pub async fn goal_feasibility(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "goal_feasibility", input).await
}

#[tauri::command]
pub async fn get_overconfidence_list(
    goal_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_overconfidence_list", json!({"goalId": goal_id})).await
}

#[tauri::command]
pub async fn get_reentry_summary(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_reentry_summary", input).await
}

#[tauri::command]
pub async fn get_decay_pressure(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_decay_pressure", input).await
}

#[tauri::command]
pub async fn start_overconfidence_probe(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "start_overconfidence_probe", input).await
}

#[tauri::command]
pub async fn create_goal(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "create_goal", input).await
}

#[tauri::command]
pub async fn update_goal_status(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "update_goal_status", input).await
}

#[tauri::command]
pub async fn get_exam_status(
    goal_id: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_exam_status", json!({"goalId": goal_id})).await
}

#[tauri::command]
pub async fn start_exam(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "start_exam", input).await
}

#[tauri::command]
pub async fn submit_exam_answer(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "submit_exam_answer", input).await
}

#[tauri::command]
pub async fn start_calibration_session(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "start_calibration_session", input).await
}

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

#[tauri::command]
pub async fn finish_exam(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "finish_exam", input).await
}

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

#[tauri::command]
pub async fn present_claims(input: Value, sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "present_claims", input).await
}

#[tauri::command]
pub async fn respond_claim(input: Value, sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "respond_claim", input).await
}

#[tauri::command]
pub async fn dismiss_claim(presentation_id: String, sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "dismiss_claim", json!({"presentationId": presentation_id})).await
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
pub async fn start_remediation(misconception_id: String, sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "start_remediation", json!({"misconceptionId": misconception_id})).await
}

#[tauri::command]
pub async fn prescribe_remediation(episode_id: String, sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "prescribe_remediation", json!({"episodeId": episode_id})).await
}

#[tauri::command]
pub async fn start_remediation_treatment(episode_id: String, sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "start_remediation_treatment", json!({"episodeId": episode_id})).await
}

#[tauri::command]
pub async fn get_remediation(episode_id: String, sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_remediation", json!({"episodeId": episode_id})).await
}

#[tauri::command]
pub async fn get_forecast_track_record(input: Value, sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_forecast_track_record", input).await
}

#[tauri::command]
pub async fn get_answer_calibration(sidecar: State<'_, SidecarManager>) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "get_answer_calibration", json!({})).await
}

#[tauri::command]
pub async fn propose_graph_edits(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "propose_graph_edits", input).await
}

#[tauri::command]
pub async fn queue_restructure_request(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "queue_restructure_request", input).await
}

#[tauri::command]
pub async fn resolve_edge_direction(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "resolve_edge_direction", input).await
}

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

#[tauri::command]
pub async fn preview_knowledge_map(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "preview_knowledge_map", input).await
}

#[tauri::command]
pub async fn preview_blueprint_readiness(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "preview_blueprint_readiness", input).await
}

// ── P2 narrow golden path (spec_p2 §9; spec_tauri_ui §3 P2 rows) ──────────────
// The dotted sidecar method names (golden_path.* / blueprint.* / diagnostic.* /
// ladder.* / practice_pool.* / reader.*) cannot be Tauri command identifiers, so
// each command forwards its `input` Value straight through to the dotted method.

macro_rules! p2_passthrough {
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

// blueprint.* (exemplar selection + blueprint review)
p2_passthrough!(blueprint_register, "blueprint.register");
p2_passthrough!(blueprint_review, "blueprint.review");
p2_passthrough!(blueprint_get_version, "blueprint.get_version");
p2_passthrough!(blueprint_discover_candidates, "blueprint.discover_candidates");
p2_passthrough!(blueprint_compose_draft, "blueprint.compose_draft");

// golden_path.* spine (atomic confirmation + run state machine)
p2_passthrough!(golden_path_confirm, "golden_path.confirm");
p2_passthrough!(golden_path_run_status, "golden_path.run_status");
p2_passthrough!(golden_path_list_runs, "golden_path.list_runs");
p2_passthrough!(golden_path_advance, "golden_path.advance");

// golden_path.* assessment + restoration + milestone / depth invitation
p2_passthrough!(golden_path_assess_open, "golden_path.assess_open");
p2_passthrough!(golden_path_assess_submit, "golden_path.assess_submit");
p2_passthrough!(golden_path_assess_result, "golden_path.assess_result");
p2_passthrough!(golden_path_restore, "golden_path.restore");
p2_passthrough!(golden_path_boundary_diff, "golden_path.boundary_diff");
p2_passthrough!(golden_path_depth_invitation, "golden_path.depth_invitation");
p2_passthrough!(golden_path_accept_edge, "golden_path.accept_edge");
p2_passthrough!(golden_path_decline_edge, "golden_path.decline_edge");

// diagnostic.* (pre-authored pack + bounded baseline + two-tier triage)
p2_passthrough!(diagnostic_pack_assemble, "diagnostic.pack_assemble");
p2_passthrough!(diagnostic_pack_admit, "diagnostic.pack_admit");
p2_passthrough!(diagnostic_pack_review, "diagnostic.pack_review");
p2_passthrough!(diagnostic_pack_list, "diagnostic.pack_list");
p2_passthrough!(diagnostic_baseline_enter, "diagnostic.baseline_enter");
p2_passthrough!(diagnostic_boundary_view, "diagnostic.boundary_view");
p2_passthrough!(diagnostic_triage, "diagnostic.triage");
p2_passthrough!(diagnostic_triage_status, "diagnostic.triage_status");
p2_passthrough!(diagnostic_triage_decide, "diagnostic.triage_decide");
p2_passthrough!(diagnostic_triage_override, "diagnostic.triage_override");

// ladder.* (pattern ladder) + practice_pool.* (rotating practice)
p2_passthrough!(ladder_policy, "ladder.policy");
p2_passthrough!(ladder_status, "ladder.status");
p2_passthrough!(ladder_enter, "ladder.enter");
p2_passthrough!(ladder_advance, "ladder.advance");
p2_passthrough!(practice_pool_assemble, "practice_pool.assemble");
p2_passthrough!(practice_pool_admit_surface, "practice_pool.admit_surface");
p2_passthrough!(practice_pool_review, "practice_pool.review");
p2_passthrough!(practice_pool_status, "practice_pool.status");
p2_passthrough!(practice_pool_next_surface, "practice_pool.next_surface");
p2_passthrough!(practice_pool_for_run, "practice_pool.for_run");
p2_passthrough!(practice_pool_seed_for_run, "practice_pool.seed_for_run");
p2_passthrough!(practice_pool_admit_anchor, "practice_pool.admit_anchor");

// reader.* (minimal bidirectional reader dialogue, U-033)
p2_passthrough!(reader_ask, "reader.ask");
p2_passthrough!(reader_set_answer_mode, "reader.set_answer_mode");
p2_passthrough!(reader_present_question, "reader.present_question");
p2_passthrough!(reader_submit_question, "reader.submit_question");
p2_passthrough!(reader_skip_question, "reader.skip_question");
p2_passthrough!(reader_choose_disposition, "reader.choose_disposition");
p2_passthrough!(reader_restore_source, "reader.restore_source");
p2_passthrough!(reader_routing_prior, "reader.routing_prior");
p2_passthrough!(reader_prompt_contract, "reader.prompt_contract");
// reader.* (P3 slice 1: render views, block health, annotations, capture/outbox)
p2_passthrough!(reader_render_view, "reader.render_view");
p2_passthrough!(reader_guide_plan, "reader.guide_plan");
p2_passthrough!(reader_pdf_view, "reader.pdf_view");
p2_passthrough!(reader_watch_plan, "reader.watch_plan");
p2_passthrough!(reader_author_section_question, "reader.author_section_question");
p2_passthrough!(reader_authored_question_action, "reader.authored_question_action");
p2_passthrough!(reader_get_progress, "reader.get_progress");
p2_passthrough!(reader_mark_section_progress, "reader.mark_section_progress");
p2_passthrough!(reader_escalate_authored_question, "reader.escalate_authored_question");
p2_passthrough!(reader_import_exercise, "reader.import_exercise");
p2_passthrough!(reader_exercise_import_status, "reader.exercise_import_status");
p2_passthrough!(reader_search_sources, "reader.search_sources");
p2_passthrough!(reader_manual_anchor, "reader.manual_anchor");
p2_passthrough!(reader_block_health, "reader.block_health");
p2_passthrough!(reader_block_original_region, "reader.block_original_region");
p2_passthrough!(reader_translate_selection, "reader.translate_selection");
p2_passthrough!(reader_capture, "reader.capture");
p2_passthrough!(reader_create_annotation, "reader.create_annotation");
p2_passthrough!(reader_edit_annotation, "reader.edit_annotation");
p2_passthrough!(reader_delete_intent_annotation, "reader.delete_intent_annotation");
p2_passthrough!(reader_reanchor, "reader.reanchor");
p2_passthrough!(reader_annotation_history, "reader.annotation_history");
p2_passthrough!(reader_source_annotations, "reader.source_annotations");
p2_passthrough!(reader_outbox_status, "reader.outbox_status");
p2_passthrough!(reader_drain_outbox, "reader.drain_outbox");
// P3 slice 2: palette + demand-paged synthesis + source objects.
p2_passthrough!(reader_invoke_preset, "reader.invoke_preset");
p2_passthrough!(reader_set_mode, "reader.set_mode");
p2_passthrough!(reader_question_control, "reader.question_control");
p2_passthrough!(reader_enqueue_request, "reader.enqueue_request");
p2_passthrough!(reader_request_status, "reader.request_status");
p2_passthrough!(reader_cancel_request, "reader.cancel_request");
p2_passthrough!(reader_retry_request, "reader.retry_request");
p2_passthrough!(reader_source_requests, "reader.source_requests");
p2_passthrough!(reader_drain_requests, "reader.drain_requests");
p2_passthrough!(reader_source_objects, "reader.source_objects");
p2_passthrough!(reader_review_source_object, "reader.review_source_object");
p2_passthrough!(reader_link_relation, "reader.link_relation");
p2_passthrough!(reader_proposal_inbox, "reader.proposal_inbox");
p2_passthrough!(reader_accept_proposal, "reader.accept_proposal");
p2_passthrough!(reader_reject_proposal, "reader.reject_proposal");
// P3 slice 3: authoring + coach + maintenance, arcs + depth + primes, restoration.
p2_passthrough!(reader_author_qa, "reader.author_qa");
p2_passthrough!(reader_coach_lint, "reader.coach_lint");
p2_passthrough!(reader_maintain, "reader.maintain");
p2_passthrough!(reader_arc, "reader.arc");
p2_passthrough!(reader_set_depth_policy, "reader.set_depth_policy");
p2_passthrough!(reader_pause_arc, "reader.pause_arc");
p2_passthrough!(reader_shrink_envelope, "reader.shrink_envelope");
p2_passthrough!(reader_prime, "reader.prime");
p2_passthrough!(reader_restore, "reader.restore");
