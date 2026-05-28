PRAGMA foreign_keys = OFF;

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
  origin TEXT NOT NULL CHECK (origin IN ('learner', 'system', 'codex', 'import')),
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

PRAGMA foreign_keys = ON;
