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
