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


# The ChatGPT-plan provider's desktop sign-in ("Continue with ChatGPT"), its
# status and plan-usage actions. Machine credentials: desktop only, never phone.
CHATGPT_PLAN_RPCS = (
    "chatgpt_plan_status",
    "chatgpt_plan_signin_start",
    "chatgpt_plan_signin_cancel",
    "chatgpt_plan_signout",
    "chatgpt_plan_acknowledge_welcome",
    "chatgpt_plan_resume",
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


@pytest.mark.parametrize(
    "method",
    DESKTOP_ONLY_CAPTURE_RPCS + MAIN_SIDECAR_RPCS + ROUTER_R0_SETTINGS_RPCS + SLICE2_T1_RPCS + SLICE2_T6_RPCS
    + STUCK_PROMPT_RPCS + DAILY_PLAN_RPCS + DAILY_PLAN_EXTENDED_RPCS + ROUTER_R1_LOGGING_RPCS
    + LEARNER_TEXT_GAP_RPCS + FACET_IDENTITY_RPCS + CHATGPT_PLAN_RPCS + READER_RW1A_RPCS
    + SOURCE_SERVICE_RPCS + SOURCE_SERVICE_EXTENDED_RPCS + UX_PHASE1_RPCS + UX_PHASE1_EXTENDED_RPCS,
)
def test_desktop_and_main_rpcs_are_registered_but_never_phone_allowed(method):
    from learnloop_sidecar import handlers  # noqa: F401 — populates the registry
    from learnloop_sidecar.registry import METHOD_REGISTRY
    assert method in METHOD_REGISTRY
    assert method not in ALLOWLIST
