-- Durable misconception history and authored correction copy.
ALTER TABLE misconceptions ADD COLUMN correction_statement TEXT;
ALTER TABLE misconceptions ADD COLUMN correction_source_span_ids_json TEXT;

CREATE TABLE misconception_transition_events (
  id TEXT PRIMARY KEY,
  misconception_id TEXT NOT NULL REFERENCES misconceptions(id) ON DELETE CASCADE,
  from_status TEXT CHECK (from_status IS NULL OR from_status IN ('active', 'resolving', 'resolved')),
  to_status TEXT NOT NULL CHECK (to_status IN ('active', 'resolving', 'resolved')),
  at TEXT NOT NULL,
  source TEXT NOT NULL
);

CREATE INDEX idx_misconception_transition_events_case
  ON misconception_transition_events(misconception_id, at, id);
