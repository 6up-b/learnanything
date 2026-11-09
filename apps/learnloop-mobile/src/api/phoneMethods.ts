// Generated from src/learnloop_mobile/allowlist.py by src/learnloop_mobile/client_contract.py.
// Do not edit: tests/test_mobile_phone_contract.py fails on any difference, and rewrites this
// file under LEARNLOOP_UPDATE_PHONE_CONTRACT=1.

/** What `GET /api/v1/meta` answers when this build and the host agree (spec §5.2). */
export const ALLOWLIST_DIGEST = "19fdf16608023469e925cf7453f76117961ec1e811470311ade2e87dd03dade3";

/** Every method the host lets the phone call. Anything else is a 403. */
export const PHONE_METHODS = [
  "acknowledge_practice_submission",
  "adopt_session",
  "answer_grading_clarification",
  "clear_session_checkpoint",
  "diagnosis_status",
  "end_session",
  "followup_continue_without",
  "followup_next",
  "followup_show_anyway",
  "followup_status",
  "get_attempt",
  "get_daily_plan",
  "get_feedback",
  "get_grading_clarification",
  "get_practice_item",
  "get_probe_contract",
  "get_session",
  "get_start_summary",
  "get_today_headline",
  "get_today_queue",
  "next_plan_item",
  "open_queue_item",
  "plan_keep_going",
  "plan_learner_pick",
  "plan_more_new",
  "plan_prefetch",
  "plan_reading_ended",
  "practice.record_hint_reveal",
  "rate_followup",
  "record_answer_display",
  "record_diagnosis_feedback",
  "record_hypothesis_exposure",
  "record_hypothesis_mark",
  "router_objective_explain",
  "save_practice_draft",
  "set_plan_minutes",
  "skip_practice_item",
  "start_session",
  "submit_attempt",
  "submit_dont_know",
  "submit_eliciting_response",
  "trigger_regrade",
  "update_session_checkpoint",
] as const;

export type PhoneMethod = (typeof PHONE_METHODS)[number];

/** Methods that run as durable jobs: a `request_id`, a 15 s wait, then 202 and a poll (§6.3). */
export const LONG_METHODS = [
  "answer_grading_clarification",
  "next_plan_item",
  "submit_attempt",
  "submit_dont_know",
  "trigger_regrade",
] as const;
