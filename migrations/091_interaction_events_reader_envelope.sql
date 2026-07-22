-- P3 slice 1, step 4 (spec_p3_reader_integration §8.1, design B step 4 + §A.3.1).
-- Extend the P0-owned interaction_events envelope IN PLACE (temp-then-rename,
-- FK-safe, exactly as migration 086 did) rather than duplicating it:
--   (a) widen the `kind` CHECK with the launch reader/reading event kinds --
--       a SUPERSET of the 086 vocabulary; all 10 prior kinds are preserved so
--       live P0/P1/P2 writers keep working;
--   (b) add the §8.1 columns (all nullable, back-compatible): occurred/received
--       split, actor, client/session/visit ids, payload schema version,
--       source/revision/render/locator/annotation/commitment/activity refs,
--       payload hash, client_idempotency_key (UNIQUE -> one row per client retry),
--       privacy/consent, producer/app/policy versions, supersedes id;
--   (c) add the §15.10 indexed query paths on (source_id) and (session_id),
--       keeping the existing (kind, created_at) / subject / admin indexes.
-- The reading-signal firewall (§C) rides `payload_json.authority_class` =
-- 'salience_only'; no numeric conversion path to evidence exists.
--
-- Also creates reader_capture_outbox: the durable single-transaction spine for
-- local-first capture (§5.3). One capture writes ONE outbox row in ONE txn; a
-- background drain converts pending rows into their target work idempotently.
-- A crash between capture-commit and drain leaves the row `pending` and the
-- annotation/commitment already safe (§15.2, §13.3 last row).

PRAGMA foreign_keys=OFF;

CREATE TABLE interaction_events__091 (
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
     'reader_automatic_depth_paused', 'reader_question_control')),
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
    CHECK (origin IN ('learner', 'system', 'owner_tooling')),
  created_at TEXT NOT NULL,
  -- §8.1 envelope extension (all nullable; P0/P1/P2 callers leave them NULL):
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

INSERT INTO interaction_events__091 (
  id, kind, subject_type, subject_id, administration_id, surface_id,
  attempt_id, affect_tap_kind, attempt_duration_ms, payload_json, origin, created_at
)
SELECT
  id, kind, subject_type, subject_id, administration_id, surface_id,
  attempt_id, affect_tap_kind, attempt_duration_ms, payload_json, origin, created_at
FROM interaction_events;

DROP TABLE interaction_events;
ALTER TABLE interaction_events__091 RENAME TO interaction_events;

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

-- The durable local-first capture outbox (§5.3, §15.2).
CREATE TABLE reader_capture_outbox (
  id TEXT PRIMARY KEY,
  client_idempotency_key TEXT NOT NULL UNIQUE,
  capture_kind TEXT NOT NULL
    CHECK (capture_kind IN ('annotation', 'flashcard_intent', 'question_intent')),
  state TEXT NOT NULL DEFAULT 'pending'
    CHECK (state IN ('pending', 'draining', 'done', 'failed')),
  payload_json TEXT NOT NULL DEFAULT '{}',
  annotation_id TEXT,
  commitment_id TEXT,
  source_id TEXT,
  revision_id TEXT,
  render_view_id TEXT,
  interaction_event_id TEXT,
  target_ref TEXT,
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  drained_at TEXT
);
CREATE INDEX idx_reader_capture_outbox_state ON reader_capture_outbox(state, created_at);
