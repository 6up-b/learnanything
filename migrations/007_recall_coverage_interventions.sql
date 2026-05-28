CREATE TABLE IF NOT EXISTS evidence_facet_recall_state (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT NOT NULL,
  facet_id TEXT NOT NULL,
  practice_item_id TEXT,
  recall_alpha REAL NOT NULL DEFAULT 1.0,
  recall_beta REAL NOT NULL DEFAULT 1.0,
  recall_mean REAL NOT NULL,
  recall_variance REAL NOT NULL,
  independent_evidence_mass REAL NOT NULL DEFAULT 0.0,
  raw_coverage_mass REAL NOT NULL DEFAULT 0.0,
  last_attempt_at TEXT,
  last_error_at TEXT,
  consecutive_failures INTEGER NOT NULL DEFAULT 0,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_evidence_facet_recall_aggregate
  ON evidence_facet_recall_state(learning_object_id, facet_id)
  WHERE practice_item_id IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_evidence_facet_recall_item
  ON evidence_facet_recall_state(learning_object_id, facet_id, practice_item_id)
  WHERE practice_item_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS practice_item_quality_state (
  practice_item_id TEXT PRIMARY KEY,
  bad_item_suspicion REAL NOT NULL DEFAULT 0.0,
  evidence_count INTEGER NOT NULL DEFAULT 0,
  suspicion_reasons_json TEXT,
  last_flagged_at TEXT,
  algorithm_version TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intervention_needs (
  id TEXT PRIMARY KEY,
  attempt_id TEXT,
  learning_object_id TEXT NOT NULL,
  practice_item_id TEXT,
  desired_intent TEXT NOT NULL,
  trigger_reason TEXT NOT NULL,
  target_facets_json TEXT NOT NULL,
  error_types_json TEXT,
  priority REAL NOT NULL DEFAULT 0.5,
  status TEXT NOT NULL CHECK (status IN ('pending', 'fulfilled', 'dismissed', 'stale')),
  blocked_reason TEXT NOT NULL,
  candidate_requirements_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_intervention_needs_pending
  ON intervention_needs(status, learning_object_id, priority, created_at);

CREATE TABLE IF NOT EXISTS attempt_debug_payloads (
  attempt_id TEXT PRIMARY KEY REFERENCES practice_attempts(id) ON DELETE CASCADE,
  payload_json TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
