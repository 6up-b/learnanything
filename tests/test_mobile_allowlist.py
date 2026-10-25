import pytest

from learnloop_mobile.allowlist import ALLOWLIST, validate_envelope


def test_m1_allowlist_is_empty_and_frozen():
    assert not ALLOWLIST
    with pytest.raises(TypeError):
        ALLOWLIST["run_cli_command"] = object()


@pytest.mark.parametrize("value", [
    [], None, {"method": 1}, {"method": ""}, {"method": "x", "params": []},
    {"method": "x", "request_id": None}, {"method": "x", "request_id": ""},
    {"method": "x", "jsonrpc": "2.0"}, {"method": "x", "path": "/vault"},
])
def test_envelope_rejects_batches_unknown_fields_and_bad_types(value):
    with pytest.raises(ValueError):
        validate_envelope(value)


def test_all_registered_methods_are_denied():
    from learnloop_sidecar import handlers  # noqa: F401 — populates the registry
    from learnloop_sidecar.registry import METHOD_REGISTRY
    assert METHOD_REGISTRY
    for method in METHOD_REGISTRY:
        assert validate_envelope({"method": method, "params": {}})["method"] not in ALLOWLIST


# Desktop-only capture RPCs (mobile M1) and the sidecar RPCs main gained before
# the mobile merge: daily loop (Today start summary), Slice 1 M2 diagnosis card,
# Phase 5b practice index, and Slice A Phase 6 placement (learner field F2,
# merged after mobile). Pinned by name so a registry rename cannot make the
# blanket test above vacuous for them.
DESKTOP_ONLY_CAPTURE_RPCS = ("resume_capture_route", "get_capture_media")
MAIN_SIDECAR_RPCS = (
    "get_start_summary",
    "diagnosis_status",
    "record_diagnosis_feedback",
    "find_practice",
    "record_practice_usage",
    "get_practice_coverage",
    "placement_self_report",
    "get_placement_state",
    "start_quick_check",
)
# Router R0's Settings additions: get_settings carries the read-only
# "Decision models" disclosures (judges) and update_ai_settings refuses
# decision-model profiles. Desktop only.
ROUTER_R0_SETTINGS_RPCS = ("get_settings", "update_ai_settings")
# Slice 2 T1 adds no RPC; it extends three desktop ones: diagnosis_status (the
# card's escalation block), record_diagnosis_feedback (the escalation: tap)
# and get_feedback (an escalated repair leads the repairs shown). The first
# two are pinned above; get_feedback is pinned here.
SLICE2_T1_RPCS = ("get_feedback",)
# Slice 2 T6 (source retrieval) adds reader.span_learning_objects (the labelled
# nearest-LO suggestion) and extends five desktop ones: reader.search_sources
# (the deep search on Enter), reader.ask (suggested_learning_objects),
# ask_tutor_question (question-dependent, verified source spans) and the
# Quick Add plan (the retrieved scope, through plan_quick_add and
# confirm_quick_add). Desktop only.
SLICE2_T6_RPCS = (
    "reader.span_learning_objects",
    "reader.search_sources",
    "reader.ask",
    "ask_tutor_question",
    "plan_quick_add",
    "confirm_quick_add",
)

# The stuck prompt (mvp-0.13, "I'm stuck" replaces "I don't know") adds no
# RPC; it extends nine desktop ones: submit_attempt (declaredStuck),
# submit_dont_know (an empty stuck answer where the vault offers it),
# save_practice_draft and update_session_checkpoint (the draft's stuck mode),
# start_session and get_session (the checkpoint carries it back), and
# load_vault, reload_vault and get_config (config.practice.stuck_prompt).
STUCK_PROMPT_RPCS = (
    "submit_attempt",
    "submit_dont_know",
    "save_practice_draft",
    "update_session_checkpoint",
    "start_session",
    "get_session",
    "load_vault",
    "reload_vault",
    "get_config",
)


# Daily-loop DL1 (mvp-0.14): the finite plan. Mobile M2a will show the plan
# through allowlisted plan RPCs; until then they are desktop-only, pinned by
# name. DL1 also extends get_today_queue (no re-entry cap while the plan
# serves) and reader.mark_section_progress (the reading block's progress),
# pinned here too.
DAILY_PLAN_RPCS = (
    "get_daily_plan",
    "set_plan_minutes",
    "next_plan_item",
    "plan_reading_ended",
    "plan_keep_going",
    "plan_more_new",
    "plan_learner_pick",
    "get_today_headline",
)
DAILY_PLAN_EXTENDED_RPCS = ("get_today_queue", "reader.mark_section_progress")


def test_the_pinned_daily_plan_rpcs_are_all_of_them():
    from learnloop_sidecar.handlers.daily_plan import DAILY_PLAN_RPCS as registered

    assert set(DAILY_PLAN_RPCS) == set(registered)


# Daily-loop DL2 (intent; a live change behind intent.enabled): the single
# control and deadlines are desktop-only. DL2 also extends the practice serve
# (a due "Check once" carries its cold banner and help header), the feedback
# read (the answered check and its way back) and the Today queue (intent's
# exclusion, recall targets and the dated check branch), pinned here too.
INTENT_RPCS = ("get_intent", "set_intent", "set_intent_deadline")
INTENT_EXTENDED_RPCS = ("get_practice_item", "get_feedback")


def test_the_pinned_intent_rpcs_are_all_of_them():
    from learnloop_sidecar.handlers.intent import INTENT_RPCS as registered

    assert set(INTENT_RPCS) == set(registered)


# The ChatGPT-plan provider's desktop sign-in ("Continue with ChatGPT"), its
# status and plan-usage actions. Machine credentials: desktop only, never phone.
CHATGPT_PLAN_RPCS = (
    "chatgpt_plan_status",
    "chatgpt_plan_signin_start",
    "chatgpt_plan_signin_cancel",
    "chatgpt_plan_signout",
    "chatgpt_plan_acknowledge_welcome",
    "chatgpt_plan_resume",
    # Plan-first transport T1: "Use OpenRouter instead" while the plan is
    # unavailable (the learner's choice for this desktop session).
    "ai_use_fallback",
)

# Router R1 (mvp-0.15) adds no RPC. It extends these: a published Today offer
# (and a skip's requeue) writes a router decision, and a first bind of a
# submission to an offered candidate other than the head writes a learner
# pick. Every daily-plan block decision and chooser stop (DAILY_PLAN_RPCS,
# pinned above) is also a plan_block router decision. Desktop only.
ROUTER_R1_LOGGING_RPCS = (
    "get_today_queue",
    "skip_practice_item",
    "save_practice_draft",
    "submit_attempt",
    "submit_dont_know",
    "start_teach_back",
)

# Learner-text gaps (mvp-0.16) add get_learner_text_gap and
# reverse_learner_text_gap (the overlay's gap reading and its one-tap
# reversals) and extend the two ask RPCs (pinned for T6 above), which now
# queue a reading and return learnerGap. Desktop only.
LEARNER_TEXT_GAP_RPCS = ("get_learner_text_gap", "reverse_learner_text_gap", "ask_tutor_question", "reader.ask")

# Facet identity adds the ingest activity's merge list and its one-tap undo
# (a facets.yaml rewrite and owner verdicts), and the owner's one-tap decision
# on a reword held for confirm (owner, 2026-10-13). Desktop only.
FACET_IDENTITY_RPCS = ("list_facet_identity_actions", "undo_facet_identity_action", "decide_facet_reword")

# Reader workbench RW1a (inquiry) adds five RPCs -- inquiry status with reopen,
# the reconnect answer, the passage-scoped quick check's read and actions, and
# the Reader's funnel activity -- and extends three: reader.ask (a parent
# exchange), reader.ask_history (parents, saved selections, status) and
# reader.prompt_contract (inquiryEnabled). Desktop only (spec D20).
READER_RW1A_RPCS = (
    "reader.set_inquiry_status",
    "reader.reconnect_answer",
    "reader.inquiry_question",
    "reader.inquiry_question_action",
    "reader.log_activity",
    "reader.ask",
    "reader.ask_history",
    "reader.prompt_contract",
)


# Reader workbench RW3a (margin cues from the Guide) adds three RPCs -- a tap
# on a cue (open, check me, not relevant and its undo), the learner's cue
# preferences and their change -- and extends reader.guide_plan (its cues).
# Desktop only (spec D20).
READER_RW3A_RPCS = (
    "reader.cue_action",
    "reader.cue_preferences",
    "reader.set_cue_preferences",
    "reader.guide_plan",
)


# Reader workbench RW3b (discovered cues) adds four RPCs -- the background
# discovery and its job read, the impressions and a tap on any cue while
# discovery is on -- and extends reader.guide_plan (discovered cues merged).
# Desktop only (spec D20).
READER_RW3B_RPCS = (
    "reader.cue_discovery",
    "reader.cue_discovery_job",
    "reader.cue_impressions",
    "reader.cue_tap",
)


def test_reader_rw3b_rpcs_are_the_modules_own():
    from learnloop_sidecar.handlers.reader_cue_discovery import CUE_DISCOVERY_RPCS

    assert set(READER_RW3B_RPCS) == set(CUE_DISCOVERY_RPCS)


# Reader workbench RW2a (the resumable scratchpad) adds fourteen RPCs -- a
# session's open, read, step save, book choice, leave, abandon, reopen, import
# binding (refresh, bind a part, retry), submit, and the reads for an attempt,
# an item and a source (RW6a's recap). Desktop only (spec D20).
READER_RW2A_RPCS = (
    "workbench.open",
    "workbench.get",
    "workbench.save_step",
    "workbench.set_book",
    "workbench.leave",
    "workbench.abandon",
    "workbench.reopen",
    "workbench.refresh_import",
    "workbench.bind",
    "workbench.retry_import",
    "workbench.submit",
    "workbench.session_for_attempt",
    "workbench.for_item",
    "workbench.for_source",
)


# UX Phase 3 (Today) adds workbench.open_problems: every source's open
# problems for Today's "Pick up a thread". A pure read. Desktop only.
UX_PHASE3_RPCS = ("workbench.open_problems",)


# Reader workbench RW6a ("Last time here") adds four RPCs -- the returning
# card, its events (recap_shown, recap_dismissed, wrap_up_opened), Wrap up and
# the wrap-up offer at the destination. All pure reads but the events.
# Desktop only (spec D20).
READER_RW6A_RPCS = (
    "reader.recap",
    "reader.recap_event",
    "reader.wrap_up",
    "reader.wrap_up_offer",
)


# Reader workbench RW1b (the intent box and active reading) adds eight RPCs --
# the intent box's routing start, read and outcome (used, discarded, changed),
# and active reading's question request, status read and actions, and
# "reconstruct this later" with its undo -- and extends reader.prompt_contract
# (the grouped palette, the speculation settings and active reading's fold).
# Desktop only (spec D20).
READER_RW1B_RPCS = (
    "reader.route_intent",
    "reader.intent_routing",
    "reader.intent_outcome",
    "reader.active_question",
    "reader.active_question_status",
    "reader.active_question_action",
    "reader.reconstruct",
    "reader.reconstruct_undo",
    "reader.prompt_contract",
)


def test_the_pinned_rw1b_rpcs_are_all_of_them():
    from learnloop_sidecar.handlers.reader_intent import RW1B_RPCS

    assert set(READER_RW1B_RPCS) - {"reader.prompt_contract"} == set(RW1B_RPCS)


# Reader workbench RW4a (spec_reader_workbench_v1 §7.3): ask your library, its
# organizer notes, compare pinned passages and the tutor about them; it
# extends reader.prompt_contract (libraryAsk) and the find_practice RPC's
# reader caller ("practice this question"). Desktop only (spec D20).
READER_RW4A_RPCS = (
    "reader.library_ask",
    "reader.library_ask_notes",
    "reader.library_compare",
    "reader.library_ask_tutor",
    # The jobs those four answer with (never on the request path; Codex review F6).
    "reader.library_job",
    "reader.library_job_cancel",
    "reader.prompt_contract",
    "find_practice",
)


def test_the_pinned_rw4a_rpcs_are_all_of_them():
    from learnloop_sidecar.handlers.library_ask import LIBRARY_ASK_RPCS

    assert set(READER_RW4A_RPCS) - {"reader.prompt_contract", "find_practice"} == set(LIBRARY_ASK_RPCS)


# Reader workbench RW4b (spec_reader_workbench_v1 §7.4): the view of a
# proposal's textbook exercises (their exposure) and the fallback search, and
# (fix round 4, R1) the one server operation that admits a picked exercise's
# learner pick; it extends reader.prompt_contract (libraryExercises),
# workbench.open (sourceExercise: the sources service's import in the
# workbench) and workbench.submit (an owed pick is admitted first, R2).
# Desktop only.
READER_RW4B_RPCS = (
    "reader.exercise_candidates",
    "reader.find_exercises",
    "workbench.admit",
    "reader.prompt_contract",
    "workbench.open",
    "workbench.submit",
)
READER_RW4B_EXTENDED_RPCS = ("reader.prompt_contract", "workbench.open", "workbench.submit")


def test_the_pinned_rw4b_rpcs_are_all_of_them():
    from learnloop_sidecar.handlers.library_exercises import LIBRARY_EXERCISE_RPCS
    from learnloop_sidecar.handlers.workbench import EXERCISE_ADMISSION_RPCS

    assert set(READER_RW4B_RPCS) - set(READER_RW4B_EXTENDED_RPCS) == {
        *LIBRARY_EXERCISE_RPCS, *EXERCISE_ADMISSION_RPCS}


# Reader workbench RW4d (spec_reader_workbench_v1 §7.8): keep a comparison as
# source-object proposals (from a library ask or the tutor's comparison),
# remove it, reopen it from its ⇄ mark, and the marks of a reading; it
# extends reader.prompt_contract (compareKeep), reader.library_compare
# (requested perspectives, whether it is kept) and reader.library_ask ("you
# compared these on …"). Desktop only.
READER_RW4D_RPCS = (
    "reader.library_compare_keep",
    "reader.library_compare_remove",
    "reader.library_compare_reopen",
    "reader.kept_comparisons",
    "reader.prompt_contract",
    "reader.library_compare",
    "reader.library_ask",
)
READER_RW4D_EXTENDED_RPCS = ("reader.prompt_contract", "reader.library_compare", "reader.library_ask")


def test_the_pinned_rw4d_rpcs_are_all_of_them():
    from learnloop_sidecar.handlers.kept_comparisons import KEPT_COMPARISON_RPCS

    assert set(READER_RW4D_RPCS) - set(READER_RW4D_EXTENDED_RPCS) == set(KEPT_COMPARISON_RPCS)


# Reader workbench RW7a (spec_reader_workbench_v1 §10.1): the Guide's reading
# path (the view, which starts its judge in the background), the depth
# choice per source and the learner's overrides; it extends
# reader.prompt_contract (readingPaths, and Orient's "what matters here?" in
# the intent palette). Desktop only.
READER_RW7A_RPCS = (
    "reader.reading_path",
    "reader.reading_path_set_depth",
    "reader.reading_path_override",
    "reader.prompt_contract",
)
READER_RW7A_EXTENDED_RPCS = ("reader.prompt_contract",)


def test_the_pinned_rw7a_rpcs_are_all_of_them():
    from learnloop_sidecar.handlers.reading_paths import READING_PATH_RPCS

    assert set(READER_RW7A_RPCS) - set(READER_RW7A_EXTENDED_RPCS) == set(READING_PATH_RPCS)


# Deliverable curriculum C0a (spec_deliverable_curriculum_v1 §6.4-6.5): the
# correspondents read API, the pressed coverage check, its job and the
# learner's corrections. Desktop only.
CURRICULUM_C0A_RPCS = (
    "reader.correspondents",
    "curriculum.cover",
    "curriculum.cover_job",
    "curriculum.coverage_correct",
)


def test_the_pinned_c0a_rpcs_are_all_of_them():
    from learnloop_sidecar.handlers.correspondents import CORRESPONDENT_RPCS

    assert set(CURRICULUM_C0A_RPCS) == set(CORRESPONDENT_RPCS)
# Reader workbench RW5a (spec_reader_workbench_v1 §8): explorable figures
# (build and "not right?" as jobs, the source's figures, predictions and
# "what changed?"); it extends reader.prompt_contract (figures). Desktop only.
READER_RW5A_RPCS = (
    "reader.figure_request",
    "reader.figure_revise",
    "reader.figure_job",
    "reader.figure_job_cancel",
    "reader.figures",
    "reader.figure_predict",
    "reader.figure_explain",
    "reader.prompt_contract",
)


def test_the_pinned_rw5a_rpcs_are_all_of_them():
    from learnloop_sidecar.handlers.figures import FIGURE_RPCS

    assert set(READER_RW5A_RPCS) - {"reader.prompt_contract"} == set(FIGURE_RPCS)


# Adaptive hints H0 (spec_adaptive_hints_v1 §9, G-H13): the practice screen's
# authored-hint reveal telemetry, and the two submits that attach the
# session's reveal rows to the attempt. Desktop only.
HINTS_H0_RPCS = ("practice.record_hint_reveal",)
HINTS_H0_EXTENDED_RPCS = ("submit_attempt", "submit_dont_know")


def test_the_pinned_hints_h0_rpcs_are_all_of_them():
    from learnloop_sidecar.handlers.practice import HINT_TELEMETRY_RPCS

    assert set(HINTS_H0_RPCS) == set(HINT_TELEMETRY_RPCS)


# Adaptive hints H2a (spec_adaptive_hints_v1 §4.1, §5, G-H13): the hint
# service's job RPCs (request, read-and-deliver, cancel) and the
# discriminating question's answer; the two submits fold the shown server
# rows. Desktop only.
HINTS_H2A_RPCS = (
    "practice.request_hint",
    "practice.hint_job",
    "practice.cancel_hint",
    "practice.answer_discriminating",
)
HINTS_H2A_EXTENDED_RPCS = ("submit_attempt", "submit_dont_know")


def test_the_pinned_hints_h2a_rpcs_are_all_of_them():
    from learnloop_sidecar.handlers.hints import HINT_SERVICE_RPCS

    assert set(HINTS_H2A_RPCS) == set(HINT_SERVICE_RPCS)


# Adaptive hints H2b (spec_adaptive_hints_v1 §4.8, D5, G-H13): the hint
# panel's help-style editor (the "⋯" menu and Settings). Desktop only.
HINTS_H2B_RPCS = ("practice.set_help_style",)


def test_the_pinned_hints_h2b_rpcs_are_all_of_them():
    from learnloop_sidecar.handlers.hints import HINT_PANEL_RPCS

    assert set(HINTS_H2B_RPCS) == set(HINT_PANEL_RPCS)


# Reader workbench RW2b + adaptive hints H3 (spec_reader_workbench_v1 §5.2-5.6,
# D20): "Check my work", the help ladder (suggest, take, reply, read, cancel),
# the discriminating answer, the header's help style and the restored help;
# and the RW2a RPCs they extend (the submit's fold, Leave's learner text, the
# bind's background map). Desktop only.
READER_RW2B_RPCS = (
    "workbench.check",
    "workbench.suggest_help",
    "workbench.request_help",
    "workbench.help_job",
    "workbench.cancel_help",
    "workbench.answer_discriminating",
    "workbench.set_help_style",
    "workbench.help_state",
)
READER_RW2B_EXTENDED_RPCS = ("workbench.submit", "workbench.leave", "workbench.bind", "workbench.refresh_import")
# RW2b fix round 5 (items 4-5): the two answer-box submits take the authored
# reveals on their own (``authoredHints``, optional). Desktop only.
READER_RW2B_FIX5_EXTENDED_RPCS = ("submit_attempt", "submit_dont_know")


def test_rw2b_fix5_authored_hints_is_an_optional_param_of_the_two_submits():
    from learnloop_sidecar import handlers  # noqa: F401 - populates the registry
    from learnloop_sidecar.registry import METHOD_REGISTRY

    for name in READER_RW2B_FIX5_EXTENDED_RPCS:
        # Fix round 12 adds book_counted beside authored_hints, optional too.
        for key in ("authored_hints", "book_counted"):
            field = METHOD_REGISTRY[name].params_model.model_fields[key]
            assert field.default is None and not field.is_required(), (name, key)


# Reader workbench RW2c (spec_reader_workbench_v1 §5.10): "Show me a similar
# example", "another passage", and compare methods' offer and opening (its
# lines are read through workbench.help_job); help_job and help_state are
# RW2b's, extended. Desktop only.
READER_RW2C_RPCS = (
    "workbench.show_example",
    "workbench.another_passage",
    "workbench.compare_offer",
    "workbench.compare_methods",
)
READER_RW2C_EXTENDED_RPCS = ("workbench.help_job", "workbench.help_state", "workbench.request_help")


def test_the_pinned_rw2c_rpcs_are_all_of_them():
    from learnloop_sidecar.handlers.workbench_rw2c import WORKBENCH_RW2C_RPCS

    assert set(READER_RW2C_RPCS) == set(WORKBENCH_RW2C_RPCS)


def test_the_pinned_rw2b_rpcs_are_all_of_them():
    from learnloop_sidecar.handlers.workbench_help import WORKBENCH_HELP_RPCS

    assert set(READER_RW2B_RPCS) == set(WORKBENCH_HELP_RPCS)


# Adaptive difficulty AD2+AD3 (spec_adaptive_difficulty_v1 §5.12, §9.5): the
# Reader's randomized dose offer and its uptake rows, and an LO's readiness
# lines from the subject view. Desktop only.
AD23_RPCS = ("reader.dose_offer", "reader.dose_offer_event", "adaptive_difficulty.readiness",
             "adaptive_difficulty.why_item")


def test_the_pinned_ad23_rpcs_are_all_of_them():
    from learnloop_sidecar.handlers.adaptive_difficulty import AD23_RPCS as registered

    assert set(AD23_RPCS) == set(registered)


# Canonical sources (spec_source_practice_and_probes_v1, G16): the service's
# own RPCs and the ones it extends (find_practice's caller and intents,
# record_practice_usage's learner text, plan_learner_pick's proposal link,
# ask_tutor_question's practice request and tool requests, reader.ask's
# practice request, edit_practice_item's re-check, reader.import_exercise's
# import row). Desktop only.
SOURCE_SERVICE_RPCS = (
    "record_proposal_impressions",
    "import_source_exercise",
    "get_source_exercise_import",
    "find_sources",
    "compare_sources",
    "run_source_tool",
    "record_source_offer_shown",
)
SOURCE_SERVICE_EXTENDED_RPCS = (
    "prescribe_remediation",
    "find_practice",
    "record_practice_usage",
    "plan_learner_pick",
    "ask_tutor_question",
    "reader.ask",
    "reader.import_exercise",
    "edit_practice_item",
    # Extended by the branch too (proposal delivery; the source-first step).
    "get_practice_item",
    "start_primed_retry",
)


def test_the_pinned_source_service_rpcs_are_all_of_them():
    from learnloop_sidecar.handlers.source_service import SOURCE_SERVICE_RPCS as registered

    assert set(SOURCE_SERVICE_RPCS) == set(registered)


# UX Phase 1 (docs/specs/ux_learnloop_v1.md §6, §10): one Add for any source,
# the AI connection sheet with its one-time consent, and the book card's
# actions (undo, build now, retry). It also extends four desktop RPCs:
# initialize (create the default library), get_source_library (the card's
# status line and links still being fetched), reader.pdf_view (a book still
# being prepared) and reader.mark_section_progress (one chapter ahead, pinned
# above). Machine paths, credentials and paid builds: desktop only.
UX_PHASE1_RPCS = ("add_source", "get_ai_connection", "connect_ai", "source_action")
UX_PHASE1_EXTENDED_RPCS = ("initialize", "get_source_library", "reader.pdf_view")
# GLM-OCR primary document reading (docs/reviews/glm-ocr-ingest.md) adds
# set_text_recognition_api_key (saves the z.ai key to the machine's
# settings.env) and extends four desktop RPCs: get_settings (the key's state,
# pinned above), update_ingest_settings and start_ingest/start_import_batch
# (the glm_ocr engine). A machine credential: desktop only.
GLM_OCR_RPCS = ("set_text_recognition_api_key",)
GLM_OCR_EXTENDED_RPCS = ("update_ingest_settings", "start_ingest", "start_import_batch")
# Re-read safety (docs/reviews/reread-safety.md) adds reader.saved_place (a
# saved reading place translated onto the reading the Reader has open, else
# the book's current reading) and extends
# source_action (the re-read's confirmation, its page scope and the one-tap
# restore_reading, pinned above), get_source_library (the E1 line and the z.ai
# OK line's pages and cost, pinned above), reader.render_view (aliased_from)
# and reader.guide_plan (a flagged passage's anchor). The protection redesign
# adds source_action's mark_exam_material (a held-back reading's one action,
# pinned above with source_action) and get_source_library's held-back line.
# Exam protection by extraction identity adds no RPC: it extends
# source_action (confirmedExtractionId and confirmedProposalHash, the
# marking's confirmation bound to what it showed, and the confirmation's
# proposalHash) and the source-set members of upsert_source_set and
# get_source_set (scopeExtractionId, scopeRevisionId, scopeSeal). Desktop only.
REREAD_SAFETY_RPCS = ("reader.saved_place",)
REREAD_SAFETY_EXTENDED_RPCS = ("reader.render_view", "reader.guide_plan")
# Selecting and highlighting on the original PDF (docs/reviews/reader-pdf-
# selection.md) adds reader.restore_annotation (the undo of a removed
# highlight: a disposition event withdrawing the delete) and extends three
# desktop RPCs: reader.source_annotations (extractionId: each annotation's
# placement on the open reading, through span_aliases), reader.pdf_view and
# reader.render_view (protection: what of the reading exam_material holds out,
# so a selection on it offers no model action). Desktop only.
READER_PDF_SELECTION_RPCS = ("reader.restore_annotation",)
READER_PDF_SELECTION_EXTENDED_RPCS = ("reader.source_annotations", "reader.pdf_view", "reader.render_view")
# UX Phase 4, practice and feedback (docs/reviews/ux-phase4.md) adds
# record_answer_display (one routine reveal-ledger row for the full answer the
# plain feedback is about to show or keeps showing; display_not_recorded,
# retryable, when nothing was written, so the answer stays hidden) and
# record_self_grade_disclosure (the trace a plain self-grade freezes before it
# shows the answer; with displayId, one display of that answer), and extends
# desktop RPCs: trigger_regrade (learnerReason and contestId: "I think I was
# right", recorded and sent to the grade-review queue), get_feedback
# (heldForReview, the learner's own answer and answered_source: contract, live
# or unrecorded), submit_attempt (heldForReview on released short-check
# answers), end_session (the session finish's topics, and settling the
# checkpoint's self-grade disclosure), and start_session and
# clear_session_checkpoint (settling it too: the reveal ledger is charged for
# the full answer a plain self-grade showed). Rounds 5 and 6: the serve RPCs
# revalidate a cold check at serve time (open_queue_item, get_practice_item
# with a session, plan_learner_pick), deferring it while a routine display
# covers it, and only a session serve opens a cold administration
# (get_practice_item without a session never does); get_probe_contract
# commits no probe inside that coverage (active false, reason
# probe_item_answer_shown), and causal_probe_offer_action can answer
# probe_item_answer_shown. Nothing is refused (round 5's
# cold_check_unavailable was withdrawn). Round 7: the plan RPCs
# (get_daily_plan, next_plan_item, plan_reading_ended; pinned by name for
# R2a above too) can answer a waiting step, and their plan view carries
# waiting (until, minutes, item, topic) when a routine-display hold lifts
# later today. Desktop only.
UX_PHASE4_RPCS = ("record_answer_display", "record_self_grade_disclosure")
UX_PHASE4_EXTENDED_RPCS = (
    "trigger_regrade",
    "get_feedback",
    "submit_attempt",
    "end_session",
    "start_session",
    "clear_session_checkpoint",
    "open_queue_item",
    "get_practice_item",
    "plan_learner_pick",
    "get_probe_contract",
    "causal_probe_offer_action",
    "get_daily_plan",
    "next_plan_item",
    "plan_reading_ended",
)
#: The book card's actions (source_action): UX Phase 1's, GLM-OCR's
#: allow_upload, and re-read safety's restore_reading (the E1 repair) and
#: mark_exam_material (a held-back reading's one action). Desktop only, with
#: source_action itself.
SOURCE_ACTION_ACTIONS = ("undo_questions", "build_now", "build_whole_book", "retry", "text_recognition",
                         "allow_upload", "restore_reading", "mark_exam_material")


def test_the_pinned_source_action_actions_are_all_of_them():
    from typing import get_args

    from learnloop_sidecar.handlers.first_run import SourceActionInput

    assert set(get_args(SourceActionInput.model_fields["action"].annotation)) == set(SOURCE_ACTION_ACTIONS)

# Router R2a (mvp-0.23) adds no RPC. It extends these: a served plan step
# names its presentation (next_plan_item, plan_learner_pick and the plan reads
# that return a step), submit_attempt, submit_dont_know and save_practice_draft
# take planPresentationId (the receipt an answer binds to), and
# golden_path.advance goes through the P2 bridge (a bridge block in its
# response). Desktop only.
ROUTER_R2A_RPCS = (
    "next_plan_item",
    "plan_learner_pick",
    "get_daily_plan",
    "plan_reading_ended",
    "submit_attempt",
    "submit_dont_know",
    "save_practice_draft",
    "golden_path.advance",
)


def test_r2a_params_are_the_plan_presentation_on_the_three_answer_rpcs():
    from learnloop_sidecar import handlers  # noqa: F401 - populates the registry
    from learnloop_sidecar.registry import METHOD_REGISTRY

    for name in ("submit_attempt", "submit_dont_know", "save_practice_draft"):
        model = METHOD_REGISTRY[name].params_model
        assert "plan_presentation_id" in model.model_fields, name
        assert model.model_fields["plan_presentation_id"].default is None, name


@pytest.mark.parametrize(
    "method",
    DESKTOP_ONLY_CAPTURE_RPCS + MAIN_SIDECAR_RPCS + ROUTER_R0_SETTINGS_RPCS + SLICE2_T1_RPCS + SLICE2_T6_RPCS
    + STUCK_PROMPT_RPCS + DAILY_PLAN_RPCS + DAILY_PLAN_EXTENDED_RPCS + ROUTER_R1_LOGGING_RPCS
    + LEARNER_TEXT_GAP_RPCS + FACET_IDENTITY_RPCS + CHATGPT_PLAN_RPCS + READER_RW1A_RPCS + READER_RW3A_RPCS + READER_RW3B_RPCS
    + READER_RW2A_RPCS + READER_RW6A_RPCS + READER_RW1B_RPCS + READER_RW4A_RPCS + READER_RW4B_RPCS + READER_RW4D_RPCS + READER_RW7A_RPCS + SOURCE_SERVICE_RPCS + SOURCE_SERVICE_EXTENDED_RPCS + UX_PHASE1_RPCS + UX_PHASE1_EXTENDED_RPCS
    + ROUTER_R2A_RPCS + GLM_OCR_RPCS + GLM_OCR_EXTENDED_RPCS + REREAD_SAFETY_RPCS + REREAD_SAFETY_EXTENDED_RPCS
    + READER_PDF_SELECTION_RPCS + READER_PDF_SELECTION_EXTENDED_RPCS + UX_PHASE4_RPCS + UX_PHASE4_EXTENDED_RPCS
    + HINTS_H0_RPCS + HINTS_H0_EXTENDED_RPCS + HINTS_H2A_RPCS + HINTS_H2A_EXTENDED_RPCS
    + HINTS_H2B_RPCS + READER_RW2B_RPCS + READER_RW2B_EXTENDED_RPCS + READER_RW2B_FIX5_EXTENDED_RPCS
    + INTENT_RPCS + INTENT_EXTENDED_RPCS + READER_RW5A_RPCS + READER_RW2C_RPCS + READER_RW2C_EXTENDED_RPCS + AD23_RPCS
    + UX_PHASE3_RPCS + CURRICULUM_C0A_RPCS,
)
def test_desktop_and_main_rpcs_are_registered_but_never_phone_allowed(method):
    from learnloop_sidecar import handlers  # noqa: F401 — populates the registry
    from learnloop_sidecar.registry import METHOD_REGISTRY
    assert method in METHOD_REGISTRY
    assert method not in ALLOWLIST
