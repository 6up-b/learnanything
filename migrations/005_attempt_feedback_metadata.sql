CREATE TABLE attempt_feedback_metadata (
  attempt_id TEXT PRIMARY KEY REFERENCES practice_attempts(id) ON DELETE CASCADE,
  grading_source TEXT NOT NULL CHECK (grading_source IN ('codex', 'self')),
  fallback_reason TEXT,
  agent_run_id TEXT REFERENCES agent_runs(id),
  fatal_errors_json TEXT NOT NULL DEFAULT '[]',
  feedback_md TEXT,
  repair_suggestions_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
