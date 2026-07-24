-- Causal-attribution P1 (§6.1): the single durable home for causal
-- hypothesis statements.  Rows are immutable episode/version records; a
-- changed interpretation appends a successor version instead of rewriting the
-- observation that produced the earlier one.
CREATE TABLE causal_hypotheses (
  id TEXT PRIMARY KEY,
  episode_key TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
  supersedes_id TEXT REFERENCES causal_hypotheses(id),
  -- Goal-series rewind can remove post-checkpoint attempt projections. The
  -- causal audit row remains immutable, so this is an id reference rather
  -- than a cascading/restricting FK.
  attempt_id TEXT NOT NULL,
  -- Error events are replay-replaced in the legacy derived-state path. Keep
  -- their immutable identifier without an FK that would block that rebuild.
  error_event_id TEXT,
  learning_object_id TEXT NOT NULL,
  cause_scope TEXT NOT NULL CHECK (
    cause_scope IN (
      'learner_state',
      'transient_execution',
      'interaction_context',
      'item_contract',
      'grader_interpretation',
      'unknown'
    )
  ),
  statement TEXT NOT NULL CHECK (length(trim(statement)) > 0),
  statement_normalized TEXT NOT NULL,
  mechanism TEXT,
  operation TEXT,
  target_ref_json TEXT,
  applicability_json TEXT,
  postdictive_claims_json TEXT,
  evidence_json TEXT,
  repair_class_id TEXT,
  status TEXT NOT NULL CHECK (
    status IN ('candidate', 'validated', 'retired', 'demoted', 'open_set')
  ),
  generation_agent_run_id TEXT,
  model TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(episode_key, version)
);

CREATE INDEX idx_causal_hypotheses_attempt
  ON causal_hypotheses(attempt_id, created_at, id);
CREATE INDEX idx_causal_hypotheses_lo_status
  ON causal_hypotheses(learning_object_id, status, created_at, id);
CREATE INDEX idx_causal_hypotheses_statement
  ON causal_hypotheses(learning_object_id, statement_normalized, version);
CREATE INDEX idx_causal_hypotheses_operation
  ON causal_hypotheses(operation)
  WHERE operation IS NOT NULL;

CREATE TRIGGER causal_hypotheses_no_update
BEFORE UPDATE ON causal_hypotheses
BEGIN
  SELECT RAISE(ABORT, 'causal hypotheses are append-only');
END;

CREATE TRIGGER causal_hypotheses_no_delete
BEFORE DELETE ON causal_hypotheses
BEGIN
  SELECT RAISE(ABORT, 'causal hypotheses are append-only');
END;
