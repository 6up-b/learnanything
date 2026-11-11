"""What other test files use from ``tests/test_mobile_allowlist.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""


#: §4.5's M2 row. test_mobile_rpc.py holds what each entry may do; here, only that the
#: "never phone-allowed" pins below cannot drift from it.
M2_ALLOWED = frozenset({
    "start_session", "adopt_session", "get_session", "end_session", "update_session_checkpoint",
    "clear_session_checkpoint", "get_today_queue", "open_queue_item", "get_practice_item", "get_probe_contract",
    "save_practice_draft", "submit_attempt", "submit_dont_know", "skip_practice_item",
    "acknowledge_practice_submission", "get_feedback", "get_attempt", "get_grading_clarification",
    "answer_grading_clarification", "diagnosis_status", "submit_eliciting_response",
})
#: Mobile v2 §8's V2 row (§2.1 J1-J6, J16 partial): the plan, the router's decisions, feedback
#: parity without probes and the item's own hints. ``followup_next`` and the adaptive hint jobs are
#: not here (V3, and docs/reviews/phone-v2-v2-today-plan.md).
V2_ALLOWED = frozenset({
    "get_daily_plan", "get_today_headline", "get_start_summary", "next_plan_item", "set_plan_minutes",
    "plan_keep_going", "plan_more_new", "plan_reading_ended", "plan_learner_pick", "router_objective_explain",
    "record_answer_display", "record_diagnosis_feedback", "trigger_regrade", "rate_followup", "followup_status",
    "followup_continue_without", "followup_show_anyway", "record_hypothesis_exposure", "record_hypothesis_mark",
    "practice.record_hint_reveal",
})
#: Mobile v2 §8's V3 row (owner decision D3): a generated follow-up probe opened by Next on the phone.
V3_ALLOWED = frozenset({"followup_next"})
#: Spec_instruct_handoff_v1 §3a: the phone's start-only prefetch, gated with the plan's other methods.
IH0_ALLOWED = frozenset({"plan_prefetch"})
#: Spec_instruct_handoff_v1 §6 (IH3): "Something else would help": the options (a read) and the choice (a plan write).
IH3_ALLOWED = frozenset({"plan_something_else_options", "plan_something_else"})
#: Mobile v2 §8's V4 row (owner decision D4): the phone Reader (J7, J8 in the Reader, CA7's *as printed*), and the
#: Read tab's book list.
V4_ALLOWED = frozenset({
    "reader.prompt_contract", "reader.render_view", "reader.guide_plan", "reader.get_progress", "reader.saved_place",
    "reader.mark_section_progress", "reader.log_activity", "reader.dose_offer", "reader.dose_offer_event",
    "reader.ask", "reader.ask_history", "reader.capture", "practice.as_printed", "get_source_library",
    # Codex review F9: a taken extra question is answered as the desktop's quick-check card answers it.
    "reader.authored_question_action",
})
PHONE_ALLOWED = M2_ALLOWED | V2_ALLOWED | V3_ALLOWED | V4_ALLOWED | IH0_ALLOWED | IH3_ALLOWED
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
    "placement_self_report",
    "get_placement_state",
    "start_quick_check",
)
# Daily-loop DL1 (mvp-0.14): the finite plan, pinned by name. Mobile M2a kept it desktop-only
# (docs/reviews/mobile-m2a.md, 2026-11-03); mobile v2 V2 (owner decision D1) allows it, filtered
# at the step (V2_ALLOWED above), so the pins below now say "phone-allowed exactly as V2 lists". DL1 also extends get_today_queue (no re-entry cap while the plan
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
    "plan_prefetch",
    "plan_something_else_options",
    "plan_something_else",
)
DAILY_PLAN_EXTENDED_RPCS = ("get_today_queue", "reader.mark_section_progress")
# Learner-text gaps (mvp-0.16) add get_learner_text_gap and
# reverse_learner_text_gap (the overlay's gap reading and its one-tap
# reversals) and extend the two ask RPCs (pinned for T6 above), which now
# queue a reading and return learnerGap. Desktop only.
LEARNER_TEXT_GAP_RPCS = ("get_learner_text_gap", "reverse_learner_text_gap", "ask_tutor_question", "reader.ask")
# Facet identity adds the ingest activity's merge list and its one-tap undo
# (a facets.yaml rewrite and owner verdicts), and the owner's one-tap decision
# on a reword held for confirm (owner, 2026-10-13). Desktop only.
FACET_IDENTITY_RPCS = ("list_facet_identity_actions", "undo_facet_identity_action", "decide_facet_reword")
