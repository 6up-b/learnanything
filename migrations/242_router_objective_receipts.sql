-- Router objective RO0: logging what is being lost (docs/specs/spec_router_objective_v1.md §4;
-- docs/reviews/router-ro0-logging.md).
--
-- Additive: new columns and three new RECEIPT tables, no existing row changes, and nothing
-- serving, scheduling, certification or replay reads. The one offline reader is the
-- probability arms' card (llm-probability-state-v4), which reads hints_used_before.
-- Written behind [router_objective] receipts at every algorithm version; off, nothing is written.
--
-- Row 1: question_events.reveal_state_json, the disclosure state at the ask, computed by
--   the server before the model call; 'ever disclosed' and 'visible now' are separate fields.
-- Row 3: plan_presentations.ask_available, the state at serve. The table stays append-only:
--   a later change is an attention_block_events row of kind ask_availability_changed.
-- Row 4: source_exposure_events.initiator and the ids beside it. A new field and not a new
--   row: coldness readers count rows, and context keeps its meaning.
-- Row 10: decision_objectives.delay_json and decision_measurement_events.delay_json, how a measurement
--   check's delay was chosen; decision_measurement_events.non_service_type, the typed reason it was not served.
ALTER TABLE question_events ADD COLUMN reveal_state_json TEXT;
ALTER TABLE plan_presentations ADD COLUMN ask_available INTEGER
  CHECK (ask_available IS NULL OR ask_available IN (0, 1));
ALTER TABLE source_exposure_events ADD COLUMN initiator TEXT
  CHECK (initiator IS NULL OR initiator IN ('learner', 'plan', 'tutor_citation', 'dose_offer', 'lesson'));
ALTER TABLE source_exposure_events ADD COLUMN initiator_block_id TEXT;
ALTER TABLE source_exposure_events ADD COLUMN initiator_session_id TEXT;
ALTER TABLE source_exposure_events ADD COLUMN initiator_visit_id TEXT;
ALTER TABLE decision_measurement_events ADD COLUMN non_service_type TEXT
  CHECK (non_service_type IS NULL OR non_service_type IN (
    'structurally_refused', 'policy_refused', 'operationally_unavailable', 'learner_declined', 'answered_unread'
  ));
ALTER TABLE decision_measurement_events ADD COLUMN delay_json TEXT;
ALTER TABLE decision_objectives ADD COLUMN delay_json TEXT;

-- Rows 7 and 8 (RECEIPT): one 'availability' row stamped before a session's first block, one
-- 'end' row, and a 'stop_response' row each time an offered stop was overridden (the session
-- goes on, so it is no end). Immutable; missing availability is recorded as missing
-- (minutes_source = 'missing'), and an end nobody reported is marked 'inferred'.
CREATE TABLE session_receipts (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  kind TEXT NOT NULL CHECK (kind IN ('availability', 'end', 'stop_response')),
  minutes_offered REAL,
  minutes_source TEXT,
  local_time TEXT,
  time_zone TEXT,
  utc_offset_minutes INTEGER,
  device TEXT,
  -- Filled by a later m1nty bridge; no integration exists in this repository.
  external_window_json TEXT,
  end_reason TEXT CHECK (end_reason IS NULL OR end_reason IN (
    'offered_stop_accepted', 'offered_stop_overridden', 'unprompted_stop', 'app_closed', 'foreground_lost',
    'external_interruption', 'rule', 'unknown'
  )),
  end_basis TEXT CHECK (end_basis IS NULL OR end_basis IN ('explicit', 'inferred')),
  ended_at TEXT,
  plan_id TEXT,
  block_id TEXT,
  stop_decision_id TEXT,
  detail_json TEXT NOT NULL DEFAULT '{}',
  receipt_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK ((kind = 'availability') = (minutes_source IS NOT NULL)),
  CHECK (kind = 'availability' OR (end_reason IS NOT NULL AND end_basis IS NOT NULL)),
  CHECK (session_id IS NOT NULL OR kind = 'stop_response')
);
CREATE UNIQUE INDEX session_receipts_once ON session_receipts(session_id, kind)
  WHERE kind IN ('availability', 'end');
CREATE INDEX session_receipts_created ON session_receipts(created_at);
CREATE TRIGGER session_receipts_no_update
BEFORE UPDATE ON session_receipts
BEGIN
    SELECT RAISE(ABORT, 'session_receipts is append-only');
END;
CREATE TRIGGER session_receipts_no_delete
BEFORE DELETE ON session_receipts
BEGIN
    SELECT RAISE(ABORT, 'session_receipts is append-only');
END;

-- Rows 9 and 13 (RECEIPT): what the router believed at one decision, ids and numbers only: per
-- candidate item FSRS S, D, R and due; per candidate LO mastery, AD p-bar and P_band, open
-- factors and hypothesis posteriors; goals and contracts in force; versions; session and day
-- active minutes; predicted minutes and their source; pending reports; the stop that was
-- offered and not taken; the VOI verdict in force for a pick. Canonical JSON, zlib-compressed.
CREATE TABLE decision_state_receipts (
  id TEXT PRIMARY KEY,
  decision_id TEXT NOT NULL UNIQUE REFERENCES router_decisions(id),
  decision_kind TEXT NOT NULL,
  receipt_version TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  session_id TEXT,
  ad_state_hash TEXT,
  session_active_minutes REAL,
  day_active_minutes REAL,
  pending_reports INTEGER,
  candidate_items INTEGER NOT NULL CHECK (candidate_items >= 0),
  candidate_los INTEGER NOT NULL CHECK (candidate_los >= 0),
  state_z BLOB NOT NULL,
  raw_bytes INTEGER NOT NULL,
  stored_bytes INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX decision_state_receipts_created ON decision_state_receipts(created_at);
CREATE TRIGGER decision_state_receipts_no_update
BEFORE UPDATE ON decision_state_receipts
BEGIN
    SELECT RAISE(ABORT, 'decision_state_receipts is append-only');
END;
CREATE TRIGGER decision_state_receipts_no_delete
BEFORE DELETE ON decision_state_receipts
BEGIN
    SELECT RAISE(ABORT, 'decision_state_receipts is append-only');
END;

-- Row 11 (RECEIPT): a goal's lifecycle as it was seen at load, for what versioned contracts do
-- not cover: status lives in the vault's YAML. 'abandoned' has no writer yet: the vault's status
-- has no such value, so a removal while active says so in its reason.
CREATE TABLE goal_lifecycle_events (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  event TEXT NOT NULL CHECK (event IN (
    'created', 'date_changed', 'paused', 'resumed', 'expired', 'abandoned', 'completed', 'removed'
  )),
  reason TEXT NOT NULL,
  status TEXT,
  previous_status TEXT,
  due_at TEXT,
  previous_due_at TEXT,
  contract_version_id TEXT,
  occurred_at TEXT,
  receipt_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX goal_lifecycle_events_goal ON goal_lifecycle_events(goal_id, created_at);
CREATE TRIGGER goal_lifecycle_events_no_update
BEFORE UPDATE ON goal_lifecycle_events
BEGIN
    SELECT RAISE(ABORT, 'goal_lifecycle_events is append-only');
END;
CREATE TRIGGER goal_lifecycle_events_no_delete
BEFORE DELETE ON goal_lifecycle_events
BEGIN
    SELECT RAISE(ABORT, 'goal_lifecycle_events is append-only');
END;
