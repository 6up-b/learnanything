mod commands;
mod errors;
mod sidecar;

use commands::*;
use sidecar::SidecarManager;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .manage(SidecarManager::new())
        .invoke_handler(tauri::generate_handler![
            select_vault,
            load_vault,
            reload_vault,
            get_runtime_health,
            get_config,
            start_session,
            get_session,
            update_session_checkpoint,
            clear_session_checkpoint,
            end_session,
            get_today_queue,
            explain_practice_item,
            open_queue_item,
            get_practice_item,
            save_practice_draft,
            submit_attempt,
            submit_dont_know,
            skip_practice_item,
            get_feedback,
            get_attempt,
            trigger_regrade,
            add_error_event,
            trigger_followup,
            inspect_entity,
            get_concept_graph,
            get_vault_tree,
            read_vault_file,
            write_vault_file,
            create_vault_file,
            sqlite_tables,
            sqlite_table,
            sqlite_exec,
            sqlite_update_cell,
            sqlite_insert_row,
            sqlite_delete_row,
            get_proposals,
            accept_proposal_items,
            reject_proposal_items,
            reset_proposal_items,
            edit_proposal_item,
            refresh_proposal_item_validation,
            delete_proposal_item,
            run_cli_command
        ])
        .run(tauri::generate_context!())
        .expect("error while running LearnLoop");
}
