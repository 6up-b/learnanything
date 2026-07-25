-- Causal-attribution P2 (§6.1): the orchestrator's durable records.
--
-- Three tables plus one column, all serving `services/causal_orchestrator.py`:
--
-- 1. `causal_probe_decision_receipts` -- EVERY probe decision, not just the ones
--    that bought a probe. `skip_common_repair`, `skip_action_equivalent` and the
--    `defer_*` verbs are the majority class and the P4 training records; a
--    receipt written only on `probe_now` throws the data away and leaves the
--    negative arms unauditable. Rows are never deduplicated by content: the
--    FREQUENCY of a repeated decision is itself the signal, so the id is a ULID
--    and the content hash rides alongside as `decision_fingerprint`.
--
-- 2. `causal_probe_preference_events` -- "Not now" has to survive the attempt.
--    `decide_probe(learner_preference=...)` was a parameter with no store, so a
--    declined offer re-offered itself on the next attempt. Scoped to a factor,
--    a learning object, or a session; the newest applicable, unexpired event
--    wins (latest learner intent, not most-specific-forever).
--
-- 3. `causal_machine_checks` -- the producer/consumer that makes the
--    `deferred_machine_checks` arm reachable. `probe_targeting`'s
--    `repair_mapping_backfills()` and `probe_priority()["machine_checks"]` emit
--    typed backfill obligations with no consumer; this is the queue they land
--    in and the orchestrator reads. The id is the content hash of the
--    obligation so re-sweeping is idempotent. Unlike the receipt tables this one
--    is a QUEUE, not a ledger, so `status` is mutable.
--
-- 4. `followup_tasks.context_json` -- §6.2 carries the cold-verification inputs
--    (source attempt, factor, hypothesis set, repair class, avoided
--    affordances) THROUGH the follow-up task record instead of trusting a
--    future caller to reconstruct them when the cold retry lands.

CREATE TABLE causal_probe_decision_receipts (
  id TEXT PRIMARY KEY,
  decision_fingerprint TEXT NOT NULL,
  factor_id TEXT NOT NULL,
  learning_object_id TEXT,
  attempt_id TEXT,
  misconception_id TEXT,
  decision TEXT NOT NULL,
  reason TEXT NOT NULL,
  repair_status TEXT NOT NULL CHECK (
    repair_status IN (
      'started',
      'needs_disambiguation',
      'deferred_machine_checks',
      'safe_common_repair_available',
      'blocked_pending_review'
    )
  ),
  decision_policy_version TEXT NOT NULL,
  formula_version TEXT NOT NULL,
  inputs_json TEXT NOT NULL,
  parameters_json TEXT NOT NULL,
  hypothesis_ids_json TEXT NOT NULL,
  repair_class_ids_json TEXT NOT NULL,
  candidate_id TEXT,
  blind_bundle_ids_json TEXT NOT NULL,
  machine_check_ids_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX idx_causal_probe_decision_receipt_factor
  ON causal_probe_decision_receipts(factor_id, created_at, id);
CREATE INDEX idx_causal_probe_decision_receipt_decision
  ON causal_probe_decision_receipts(decision, created_at, id);

CREATE TRIGGER causal_probe_decision_receipts_no_update
BEFORE UPDATE ON causal_probe_decision_receipts
BEGIN
  SELECT RAISE(ABORT, 'causal probe decision receipts are append-only');
END;

CREATE TRIGGER causal_probe_decision_receipts_no_delete
BEFORE DELETE ON causal_probe_decision_receipts
BEGIN
  SELECT RAISE(ABORT, 'causal probe decision receipts are append-only');
END;

CREATE TABLE causal_probe_preference_events (
  id TEXT PRIMARY KEY,
  scope TEXT NOT NULL CHECK (
    scope IN ('factor', 'learning_object', 'session')
  ),
  scope_ref TEXT NOT NULL,
  session_id TEXT,
  preference TEXT NOT NULL CHECK (
    preference IN ('allow', 'decline', 'teach_now', 'no_more_diagnostics')
  ),
  source TEXT NOT NULL,
  expires_at TEXT,
  detail_json TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX idx_causal_probe_preference_scope
  ON causal_probe_preference_events(scope, scope_ref, created_at, id);
CREATE INDEX idx_causal_probe_preference_session
  ON causal_probe_preference_events(session_id, created_at, id);

CREATE TRIGGER causal_probe_preference_events_no_update
BEFORE UPDATE ON causal_probe_preference_events
BEGIN
  SELECT RAISE(ABORT, 'causal probe preference events are append-only');
END;

CREATE TRIGGER causal_probe_preference_events_no_delete
BEFORE DELETE ON causal_probe_preference_events
BEGIN
  SELECT RAISE(ABORT, 'causal probe preference events are append-only');
END;

CREATE TABLE causal_machine_checks (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  learning_object_id TEXT,
  factor_id TEXT,
  attempt_id TEXT,
  status TEXT NOT NULL CHECK (
    status IN ('pending', 'resolved', 'dismissed')
  ),
  source TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  resolution_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  resolved_at TEXT
);

CREATE INDEX idx_causal_machine_checks_open
  ON causal_machine_checks(status, learning_object_id, factor_id, created_at, id);

ALTER TABLE followup_tasks ADD COLUMN context_json TEXT;
