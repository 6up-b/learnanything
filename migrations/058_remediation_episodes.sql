-- Structured misconception repair episodes and delayed cold follow-up tasks.
CREATE TABLE remediation_episodes (
  id TEXT PRIMARY KEY,
  case_kind TEXT NOT NULL CHECK (case_kind IN ('misconception', 'diagnosis')),
  case_ref TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('diagnosis', 'prescribed', 'treatment', 'cold_scheduled', 'completed', 'abandoned')),
  passages_shown_json TEXT NOT NULL DEFAULT '[]',
  primed_item_id TEXT,
  cold_item_id TEXT,
  primed_attempt_id TEXT REFERENCES practice_attempts(id),
  cold_attempt_id TEXT REFERENCES practice_attempts(id),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  completed_at TEXT
);

CREATE INDEX idx_remediation_episodes_case
  ON remediation_episodes(case_kind, case_ref, created_at);

CREATE TABLE followup_tasks (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('cold_retry')),
  case_kind TEXT NOT NULL CHECK (case_kind IN ('misconception', 'diagnosis')),
  case_ref TEXT NOT NULL,
  source_attempt_id TEXT REFERENCES practice_attempts(id),
  remediation_episode_id TEXT REFERENCES remediation_episodes(id) ON DELETE CASCADE,
  not_before TEXT NOT NULL,
  expires_at TEXT,
  status TEXT NOT NULL CHECK (status IN ('pending', 'served', 'consumed', 'expired')),
  selected_item_id TEXT,
  consumed_attempt_id TEXT REFERENCES practice_attempts(id),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX idx_followup_tasks_due
  ON followup_tasks(status, not_before, expires_at);
CREATE INDEX idx_followup_tasks_item
  ON followup_tasks(selected_item_id, status);

-- `source_exposure_events.context` is a closed CHECK, so extend it with the
-- current table shape rather than mutating the constraint in place.
PRAGMA foreign_keys = OFF;

DROP INDEX IF EXISTS idx_source_exposure_events_span;
DROP INDEX IF EXISTS idx_source_exposure_events_entity;

CREATE TABLE source_exposure_events_new (
  id TEXT PRIMARY KEY,
  context TEXT NOT NULL
    CHECK (context IN (
      'provenance', 'gate_diagnostic', 'registry_review', 'library', 'other',
      'tutor_citation', 'provenance_panel', 'conflict_review', 'remediation'
    )),
  extraction_id TEXT NOT NULL,
  span_id TEXT NOT NULL,
  revision_id TEXT,
  source_id TEXT,
  entity_type TEXT,
  entity_id TEXT,
  page INTEGER,
  locator TEXT,
  section_path_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL
);

INSERT INTO source_exposure_events_new(
  id, context, extraction_id, span_id, revision_id, source_id,
  entity_type, entity_id, page, locator, section_path_json, created_at
)
SELECT
  id, context, extraction_id, span_id, revision_id, source_id,
  entity_type, entity_id, page, locator, section_path_json, created_at
FROM source_exposure_events;

DROP TABLE source_exposure_events;
ALTER TABLE source_exposure_events_new RENAME TO source_exposure_events;

CREATE INDEX idx_source_exposure_events_span ON source_exposure_events(extraction_id, span_id);
CREATE INDEX idx_source_exposure_events_entity ON source_exposure_events(entity_type, entity_id);

PRAGMA foreign_keys = ON;
