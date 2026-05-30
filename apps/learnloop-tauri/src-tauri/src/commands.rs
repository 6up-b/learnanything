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
pub async fn run_cli_command(
    input: Value,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    blocking_sidecar_call(sidecar, "run_cli_command", input).await
}
