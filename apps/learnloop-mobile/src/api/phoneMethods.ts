// Generated from src/learnloop_mobile/allowlist.py by src/learnloop_mobile/client_contract.py.
// Do not edit: tests/test_mobile_phone_contract.py fails on any difference, and rewrites this
// file under LEARNLOOP_UPDATE_PHONE_CONTRACT=1.

/** What `GET /api/v1/meta` answers when this build and the host agree (spec §5.2). */
export const ALLOWLIST_DIGEST = "9d84d2185c8773d30b60d5aed39a48a9277f5b7db4c93d75efdb60cbec4885dd";

/** Every method the host lets the phone call. Anything else is a 403. */
export const PHONE_METHODS = [
  "acknowledge_practice_submission",
  "adopt_session",
  "answer_grading_clarification",
  "clear_session_checkpoint",
  "diagnosis_status",
  "end_session",
  "get_attempt",
  "get_feedback",
  "get_grading_clarification",
  "get_practice_item",
  "get_probe_contract",
  "get_session",
  "get_today_queue",
  "open_queue_item",
  "save_practice_draft",
  "skip_practice_item",
  "start_session",
  "submit_attempt",
  "submit_dont_know",
  "submit_eliciting_response",
  "update_session_checkpoint",
] as const;

export type PhoneMethod = (typeof PHONE_METHODS)[number];

/** Methods that run as durable jobs: a `request_id`, a 15 s wait, then 202 and a poll (§6.3). */
export const LONG_METHODS = [
  "answer_grading_clarification",
  "submit_attempt",
  "submit_dont_know",
] as const;
