ALTER TABLE agent_runs ADD COLUMN provider_type TEXT;
ALTER TABLE agent_runs ADD COLUMN provider_revision TEXT;

UPDATE agent_runs
SET provider_type = CASE
    WHEN provider = 'codex' THEN 'codex_sdk'
    ELSE provider_type
  END,
  provider_revision = COALESCE(provider_revision, codex_revision);

PRAGMA foreign_keys = OFF;

CREATE TABLE attempt_feedback_metadata_new (
  attempt_id TEXT PRIMARY KEY REFERENCES practice_attempts(id) ON DELETE CASCADE,
  grading_source TEXT NOT NULL CHECK (grading_source IN ('ai', 'codex', 'self')),
  fallback_reason TEXT,
  agent_run_id TEXT REFERENCES agent_runs(id),
  fatal_errors_json TEXT NOT NULL DEFAULT '[]',
  feedback_md TEXT,
  repair_suggestions_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

INSERT INTO attempt_feedback_metadata_new(
  attempt_id, grading_source, fallback_reason, agent_run_id,
  fatal_errors_json, feedback_md, repair_suggestions_json,
  created_at, updated_at
)
SELECT
  attempt_id, grading_source, fallback_reason, agent_run_id,
  fatal_errors_json, feedback_md, repair_suggestions_json,
  created_at, updated_at
FROM attempt_feedback_metadata;

DROP TABLE attempt_feedback_metadata;
ALTER TABLE attempt_feedback_metadata_new RENAME TO attempt_feedback_metadata;

DROP INDEX IF EXISTS idx_content_events_recent;

CREATE TABLE content_events_new (
  id TEXT PRIMARY KEY,
  change_batch_id TEXT,
  event_type TEXT NOT NULL CHECK (
    event_type IN (
      'created',
      'updated',
      'deactivated',
      'regrade_disagreement',
      'algorithm_version_bumped',
      'source_span_changed',
      'source_span_removed'
    )
  ),
  subject TEXT,
  entity_type TEXT NOT NULL CHECK (
    entity_type IN ('learning_object', 'practice_item', 'concept', 'concept_edge', 'rubric', 'error_type')
  ),
  entity_id TEXT NOT NULL,
  origin TEXT NOT NULL CHECK (origin IN ('learner', 'system', 'codex', 'ai', 'import')),
  review_status TEXT CHECK (
    review_status IS NULL OR review_status IN ('auto_accepted', 'accepted', 'rejected')
  ),
  summary TEXT,
  created_at TEXT NOT NULL
);

INSERT INTO content_events_new(
  id, change_batch_id, event_type, subject, entity_type,
  entity_id, origin, review_status, summary, created_at
)
SELECT
  id, change_batch_id, event_type, subject, entity_type,
  entity_id, origin, review_status, summary, created_at
FROM content_events;

DROP TABLE content_events;
ALTER TABLE content_events_new RENAME TO content_events;

CREATE INDEX idx_content_events_recent
  ON content_events(created_at, event_type);

CREATE TABLE change_batches_new (
  id TEXT PRIMARY KEY,
  proposed_patch_item_id TEXT,
  reason TEXT NOT NULL CHECK (reason IN ('proposal_accept', 'manual_edit', 'import')),
  origin TEXT NOT NULL CHECK (origin IN ('learner', 'system', 'codex', 'ai')),
  summary TEXT,
  created_at TEXT NOT NULL
);

INSERT INTO change_batches_new(
  id, proposed_patch_item_id, reason, origin, summary, created_at
)
SELECT id, proposed_patch_item_id, reason, origin, summary, created_at
FROM change_batches;

DROP TABLE change_batches;
ALTER TABLE change_batches_new RENAME TO change_batches;

CREATE UNIQUE INDEX idx_change_batches_proposal_item
  ON change_batches(proposed_patch_item_id)
  WHERE proposed_patch_item_id IS NOT NULL;

PRAGMA foreign_keys = ON;
