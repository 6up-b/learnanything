mod commands;
mod errors;
mod sidecar;

use commands::*;
use sidecar::SidecarManager;
use std::borrow::Cow;
use tauri::Manager;

const DEBUG_ZOOM_ENV: &str = "LEARNLOOP_TAURI_DEBUG_ZOOM";

// llpdf://localhost/<store-file-name> serves original source bytes from the
// vault's content-addressed store (canonical-sources/raw/). Streaming through a
// protocol keeps multi-MB PDFs off the mutex-serialized stdin JSON-RPC channel.
// Only bare content-addressed names (sha256-<hex>) are served — the store
// directory is the whole reachable surface, so no path traversal is possible.
fn llpdf_response(status: u16, body: Vec<u8>) -> tauri::http::Response<Cow<'static, [u8]>> {
    tauri::http::Response::builder()
        .status(status)
        .header("Content-Type", "application/pdf")
        .header("Access-Control-Allow-Origin", "*")
        .body(Cow::Owned(body))
        .expect("static llpdf response")
}

fn serve_llpdf(
    manager: &SidecarManager,
    uri_path: &str,
) -> tauri::http::Response<Cow<'static, [u8]>> {
    let name = uri_path.trim_start_matches('/');
    let content_addressed = name
        .strip_prefix("sha256-")
        .is_some_and(|hex| !hex.is_empty() && hex.chars().all(|c| c.is_ascii_hexdigit()));
    if !content_addressed {
        return llpdf_response(400, b"invalid store name".to_vec());
    }
    let path = manager
        .resolved_vault_path()
        .join("canonical-sources")
        .join("raw")
        .join(name);
    match std::fs::read(&path) {
        Ok(bytes) => llpdf_response(200, bytes),
        Err(_) => llpdf_response(404, b"not in originals store".to_vec()),
    }
}

// llmedia://localhost/<sha256-<hex>.mp4> serves rendered explainer animations
// from the vault's media/animations/ store. Same strict content-addressed-name
// rule as llpdf (no path traversal surface), plus Range/206 support because
// HTML5 <video> seeking issues byte-range requests.
fn llmedia_response(
    status: u16,
    body: Vec<u8>,
    extra: Option<(String, String)>,
) -> tauri::http::Response<Cow<'static, [u8]>> {
    let mut builder = tauri::http::Response::builder()
        .status(status)
        .header("Content-Type", "video/mp4")
        .header("Accept-Ranges", "bytes")
        .header("Access-Control-Allow-Origin", "*");
    if let Some((name, value)) = extra {
        builder = builder.header(name, value);
    }
    builder.body(Cow::Owned(body)).expect("static llmedia response")
}

/// Parse a `bytes=start-end` Range header against a body of `len` bytes.
/// Returns None for absent/unsupported forms (serve 200 full-body) and
/// Some(Err(())) for unsatisfiable ranges (416).
fn slice_range(len: u64, range_header: Option<&str>) -> Option<Result<(u64, u64), ()>> {
    let header = range_header?.trim();
    let spec = header.strip_prefix("bytes=")?;
    if spec.contains(',') {
        return None; // multipart ranges unsupported: fall back to 200
    }
    let (start_raw, end_raw) = spec.split_once('-')?;
    if start_raw.is_empty() {
        // suffix form: last N bytes
        let suffix: u64 = end_raw.parse().ok()?;
        if suffix == 0 || len == 0 {
            return Some(Err(()));
        }
        let start = len.saturating_sub(suffix);
        return Some(Ok((start, len - 1)));
    }
    let start: u64 = start_raw.parse().ok()?;
    let end: u64 = if end_raw.is_empty() {
        len.saturating_sub(1)
    } else {
        end_raw.parse().ok()?
    };
    if start >= len || end < start {
        return Some(Err(()));
    }
    Some(Ok((start, end.min(len.saturating_sub(1)))))
}

fn serve_llmedia(
    manager: &SidecarManager,
    uri_path: &str,
    range_header: Option<&str>,
) -> tauri::http::Response<Cow<'static, [u8]>> {
    let name = uri_path.trim_start_matches('/');
    let content_addressed = name
        .strip_prefix("sha256-")
        .and_then(|rest| rest.strip_suffix(".mp4"))
        .is_some_and(|hex| !hex.is_empty() && hex.chars().all(|c| c.is_ascii_hexdigit()));
    if !content_addressed {
        return llmedia_response(400, b"invalid animation name".to_vec(), None);
    }
    let path = manager
        .resolved_vault_path()
        .join("media")
        .join("animations")
        .join(name);
    let bytes = match std::fs::read(&path) {
        Ok(bytes) => bytes,
        Err(_) => return llmedia_response(404, b"not in animation store".to_vec(), None),
    };
    let total = bytes.len() as u64;
    match slice_range(total, range_header) {
        None => llmedia_response(200, bytes, None),
        Some(Err(())) => llmedia_response(416, Vec::new(), Some(("Content-Range".into(), format!("bytes */{total}")))),
        Some(Ok((start, end))) => {
            let body = bytes[start as usize..=(end as usize)].to_vec();
            llmedia_response(
                206,
                body,
                Some(("Content-Range".into(), format!("bytes {start}-{end}/{total}"))),
            )
        }
    }
}

fn debug_zoom_enabled() -> bool {
    std::env::var(DEBUG_ZOOM_ENV).is_ok_and(|value| {
        matches!(
            value.trim().to_ascii_lowercase().as_str(),
            "1" | "true" | "yes" | "on" | "debug"
        )
    })
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .manage(SidecarManager::new())
        .register_uri_scheme_protocol("llpdf", |ctx, request| {
            let manager = ctx.app_handle().state::<SidecarManager>();
            serve_llpdf(&manager, request.uri().path())
        })
        .register_uri_scheme_protocol("llmedia", |ctx, request| {
            let manager = ctx.app_handle().state::<SidecarManager>();
            let range = request
                .headers()
                .get("range")
                .and_then(|value| value.to_str().ok())
                .map(|value| value.to_string());
            serve_llmedia(&manager, request.uri().path(), range.as_deref())
        })
        .setup(|app| {
            let main_window = app
                .config()
                .app
                .windows
                .iter()
                .find(|window| window.label == "main")
                .ok_or("missing main window configuration")?;

            tauri::WebviewWindowBuilder::from_config(app.handle(), main_window)?
                .zoom_hotkeys_enabled(debug_zoom_enabled())
                .build()?;

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            select_vault,
            load_vault,
            reload_vault,
            create_vault,
            get_learner_profile,
            set_learner_profile,
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
            get_probe_contract,
            stop_probe_diagnosing,
            get_next_probe_item,
            save_practice_draft,
            submit_attempt,
            submit_dont_know,
            skip_practice_item,
            get_feedback,
            get_attempt,
            trigger_regrade,
            add_error_event,
            trigger_followup,
            rate_followup,
            start_primed_retry,
            inspect_entity,
            get_concept_graph,
            get_vault_tree,
            get_recent_ingests,
            classify_ingest_source,
            start_ingest,
            get_ingest_job,
            get_ingest_jobs,
            cancel_ingest,
            start_import_batch,
            get_ingest_batch,
            list_ingest_batches,
            cancel_ingest_batch,
            resume_ingest_batch,
            retry_synthesis,
            get_synthesis_candidate,
            get_source_library,
            get_source_outline,
            get_selection_preview,
            get_effective_outline,
            save_unit_selection,
            get_acquisition_preview,
            get_build_plan,
            list_source_sets,
            get_source_set,
            upsert_source_set,
            get_source_coverage,
            start_inventory,
            create_study_map,
            build_study_map,
            append_source,
            refresh_revision,
            maintenance_feed,
            maintenance_notice_action,
            list_source_conflicts,
            resolve_source_conflict,
            exam_readiness,
            start_extraction_repair,
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
            get_entity_provenance,
            plan_quick_add,
            confirm_quick_add,
            get_span_view,
            get_subject_registry,
            propose_facet_merge,
            propose_graph_edits,
            queue_restructure_request,
            resolve_edge_direction,
            get_facet_detail,
            list_facets,
            preview_knowledge_map,
            preview_blueprint_readiness,
            accept_proposal_items,
            reject_proposal_items,
            reset_proposal_items,
            edit_proposal_item,
            refresh_proposal_item_validation,
            delete_proposal_item,
            run_cli_command,
            get_facet_mastery,
            get_knowledge_map,
            get_knowledge_map_history,
            get_attempt_trace,
            get_capability_grid,
            get_facet_evidence_timeline,
            set_grading_provider,
            get_settings,
            update_ai_settings,
            set_openrouter_api_key,
            update_ingest_settings,
            set_transcription_api_key,
            get_animation_runtime,
            request_concept_animation,
            get_concept_animation_status,
            list_concept_animations,
            ask_tutor_question,
            preview_tutor_opening,
            rate_tutor_answer,
            save_tutor_answer_note,
            get_tutor_transcript,
            promote_tutor_question,
            list_question_queue,
            resolve_question_event,
            author_practice_item,
            request_rung_variant,
            get_rung_variant_status,
            edit_practice_item,
            retire_practice_item,
            split_practice_item,
            start_teach_back,
            submit_teach_back_turn,
            goals_list,
            get_goal_report,
            get_goal_report_series,
            goal_feasibility,
            get_overconfidence_list,
            get_reentry_summary,
            get_decay_pressure,
            start_overconfidence_probe,
            create_goal,
            update_goal_status,
            get_exam_status,
            start_exam,
            submit_exam_answer,
            finish_exam,
            start_calibration_session,
            get_calibration_session,
            stop_calibration_session,
            begin_probe_dialogue,
            next_probe_dialogue_turn,
            record_probe_dialogue_turn,
            end_probe_dialogue,
            present_claims,
            respond_claim,
            dismiss_claim,
            export_claims,
            purge_claims,
            get_review_log,
            start_remediation,
            prescribe_remediation,
            start_remediation_treatment,
            get_remediation,
            get_forecast_track_record,
            get_answer_calibration,
            blueprint_register,
            blueprint_review,
            blueprint_get_version,
            blueprint_discover_candidates,
            blueprint_compose_draft,
            golden_path_confirm,
            golden_path_run_status,
            golden_path_list_runs,
            golden_path_advance,
            golden_path_assess_open,
            golden_path_assess_submit,
            golden_path_assess_result,
            golden_path_restore,
            golden_path_boundary_diff,
            golden_path_depth_invitation,
            golden_path_accept_edge,
            golden_path_decline_edge,
            diagnostic_pack_assemble,
            diagnostic_pack_admit,
            diagnostic_pack_review,
            diagnostic_pack_list,
            diagnostic_baseline_enter,
            diagnostic_boundary_view,
            diagnostic_triage,
            diagnostic_triage_status,
            diagnostic_triage_decide,
            diagnostic_triage_override,
            ladder_policy,
            ladder_status,
            ladder_enter,
            ladder_advance,
            practice_pool_assemble,
            practice_pool_admit_surface,
            practice_pool_review,
            practice_pool_status,
            practice_pool_next_surface,
            practice_pool_for_run,
            practice_pool_seed_for_run,
            practice_pool_admit_anchor,
            reader_ask,
            reader_set_answer_mode,
            reader_present_question,
            reader_submit_question,
            reader_skip_question,
            reader_choose_disposition,
            reader_restore_source,
            reader_routing_prior,
            reader_prompt_contract,
            reader_render_view,
            reader_guide_plan,
            reader_pdf_view,
            reader_watch_plan,
            reader_author_section_question,
            reader_get_progress,
            reader_mark_section_progress,
            reader_authored_question_action,
            reader_escalate_authored_question,
            reader_search_sources,
            reader_manual_anchor,
            reader_block_health,
            reader_block_original_region,
            reader_translate_selection,
            reader_capture,
            reader_create_annotation,
            reader_edit_annotation,
            reader_delete_intent_annotation,
            reader_reanchor,
            reader_annotation_history,
            reader_source_annotations,
            reader_outbox_status,
            reader_drain_outbox,
            reader_invoke_preset,
            reader_set_mode,
            reader_question_control,
            reader_enqueue_request,
            reader_request_status,
            reader_cancel_request,
            reader_retry_request,
            reader_source_requests,
            reader_drain_requests,
            reader_source_objects,
            reader_review_source_object,
            reader_link_relation,
            reader_proposal_inbox,
            reader_accept_proposal,
            reader_reject_proposal,
            reader_author_qa,
            reader_coach_lint,
            reader_maintain,
            reader_arc,
            reader_set_depth_policy,
            reader_pause_arc,
            reader_shrink_envelope,
            reader_prime,
            reader_restore
        ])
        .run(tauri::generate_context!())
        .expect("error while running LearnLoop");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn llpdf_rejects_non_content_addressed_names() {
        let manager = SidecarManager::new();
        for name in [
            "/../../etc/passwd",
            "/sha256-XYZ",
            "/sha256-",
            "/notahash",
            "/sha256-abc/../x",
            "/",
        ] {
            assert_eq!(serve_llpdf(&manager, name).status(), 400, "{name}");
        }
    }

    #[test]
    fn llpdf_404s_for_absent_store_file() {
        let manager = SidecarManager::new();
        assert_eq!(serve_llpdf(&manager, "/sha256-deadbeef").status(), 404);
    }

    #[test]
    fn llmedia_rejects_non_content_addressed_names() {
        let manager = SidecarManager::new();
        for name in [
            "/../../etc/passwd",
            "/sha256-XYZ.mp4",
            "/sha256-.mp4",
            "/sha256-deadbeef",
            "/sha256-deadbeef.mkv",
            "/notahash.mp4",
            "/sha256-abc/../x.mp4",
            "/",
        ] {
            assert_eq!(serve_llmedia(&manager, name, None).status(), 400, "{name}");
        }
    }

    #[test]
    fn llmedia_404s_for_absent_animation() {
        let manager = SidecarManager::new();
        assert_eq!(serve_llmedia(&manager, "/sha256-deadbeef.mp4", None).status(), 404);
    }

    #[test]
    fn slice_range_math() {
        // Absent / malformed / multipart headers -> whole-body 200.
        assert_eq!(slice_range(100, None), None);
        assert_eq!(slice_range(100, Some("chunks=0-1")), None);
        assert_eq!(slice_range(100, Some("bytes=0-10,20-30")), None);
        // Normal forms.
        assert_eq!(slice_range(100, Some("bytes=0-49")), Some(Ok((0, 49))));
        assert_eq!(slice_range(100, Some("bytes=50-")), Some(Ok((50, 99))));
        assert_eq!(slice_range(100, Some("bytes=-10")), Some(Ok((90, 99))));
        // End clamps to the last byte.
        assert_eq!(slice_range(100, Some("bytes=90-500")), Some(Ok((90, 99))));
        // Unsatisfiable -> 416.
        assert_eq!(slice_range(100, Some("bytes=100-")), Some(Err(())));
        assert_eq!(slice_range(100, Some("bytes=30-10")), Some(Err(())));
        assert_eq!(slice_range(0, Some("bytes=-5")), Some(Err(())));
    }
}
