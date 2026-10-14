-- Chat frontend C1a (spec_mcp_frontend_c1 §5): the MCP adapter records every
-- tool call a chat host makes in the interaction_events envelope, so the local
-- learner model sees chat activity in the same ledger as the Reader's.
--
-- Widen two CHECKs (temp-then-rename, FK-safe, exactly as migrations 086, 091
-- and 103 did): `kind` gains 'chat_tool_call' and `origin` gains 'chat_host'
-- (a host model acting in the learner's chat: neither the learner's own typed
-- action, LearnLoop's system, nor owner tooling). Every column, index and
-- prior kind is preserved; this is a SUPERSET widening only. Rows of the new
-- kind are telemetry with authority_class = 'salience_only' in their payload:
-- never learner evidence.
--
-- PLACEHOLDER NUMBER 210: renumber at merge (the stage brief reserves it).

PRAGMA foreign_keys=OFF;

CREATE TABLE interaction_events__210 (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN
    ('attempt_duration', 'retirement_reason', 'affect_tap',
     -- U-033 reader-dialogue kinds (migration 086, §7.6):
     'reader_question_presented', 'reader_question_skipped',
     'reader_answer_submitted', 'learner_question_asked',
     'reader_answer_mode_set', 'reader_disposition_chosen',
     'reader_source_restored',
     -- P3 launch reader/reading event kinds (§8.1):
     'reader_view_opened', 'reader_view_closed', 'reader_mode_changed',
     'reader_span_visible', 'reader_scroll', 'reader_dwell',
     'reader_selection', 'reader_highlight', 'reader_annotation_edited',
     'reader_action_invoked', 'reader_capture_acknowledged',
     'reader_job_queued', 'reader_job_completed',
     'reader_proposal_accepted', 'reader_proposal_edited', 'reader_proposal_rejected',
     'reader_authoring_coach_response',
     'reader_depth_policy_confirmed', 'reader_depth_envelope_confirmed',
     'reader_depth_envelope_changed', 'reader_milestone_reached',
     'reader_automatic_edge_committed', 'reader_automatic_edge_blocked',
     'reader_automatic_depth_paused', 'reader_question_control',
     -- Learner-owned item authoring lifecycle (migration 103):
     'learner_item_authored', 'learner_item_edited',
     'learner_item_retired', 'learner_item_split',
     -- Chat frontend C1a (migration 210): one row per MCP tool call a chat
     -- host made (ChatGPT, Claude, or a local stdio client).
     'chat_tool_call')),
  subject_type TEXT,
  subject_id TEXT,
  administration_id TEXT,
  surface_id TEXT,
  attempt_id TEXT,
  affect_tap_kind TEXT CHECK (affect_tap_kind IS NULL OR affect_tap_kind IN (
    'cue_gave_it_away', 'ambiguous', 'misgraded', 'felt_rote',
    'not_worth_my_attention', 'meaningful_connection', 'wanted_more_depth'
  )),
  attempt_duration_ms INTEGER
    CHECK (attempt_duration_ms IS NULL OR attempt_duration_ms >= 0),
  payload_json TEXT,
  origin TEXT NOT NULL
    CHECK (origin IN ('learner', 'system', 'owner_tooling', 'chat_host')),
  created_at TEXT NOT NULL,
  occurred_at TEXT,
  received_at TEXT,
  actor TEXT,
  client_id TEXT,
  session_id TEXT,
  visit_id TEXT,
  payload_schema_version TEXT,
  source_id TEXT,
  revision_id TEXT,
  render_view_id TEXT,
  locator_json TEXT,
  annotation_id TEXT,
  commitment_id TEXT,
  activity_id TEXT,
  payload_hash TEXT,
  client_idempotency_key TEXT,
  privacy_locality TEXT,
  consent_context TEXT,
  producer_version TEXT,
  app_version TEXT,
  policy_version TEXT,
  supersedes_event_id TEXT
);

INSERT INTO interaction_events__210 SELECT * FROM interaction_events;

DROP TABLE interaction_events;
ALTER TABLE interaction_events__210 RENAME TO interaction_events;

CREATE INDEX idx_interaction_events_kind
  ON interaction_events(kind, created_at);
CREATE INDEX idx_interaction_events_subject
  ON interaction_events(subject_type, subject_id);
CREATE INDEX idx_interaction_events_admin
  ON interaction_events(administration_id);
CREATE INDEX idx_interaction_events_source
  ON interaction_events(source_id);
CREATE INDEX idx_interaction_events_session
  ON interaction_events(session_id);
CREATE UNIQUE INDEX idx_interaction_events_client_key
  ON interaction_events(client_idempotency_key)
  WHERE client_idempotency_key IS NOT NULL;

PRAGMA foreign_keys=ON;
