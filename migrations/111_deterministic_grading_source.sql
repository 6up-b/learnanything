-- Deterministic grading lane: recognition/multiple-choice answers with an
-- authored option-letter key are graded by exact option comparison (certainty
-- 1.0, no LLM call, no calibration-channel discount). attempt_feedback_metadata
-- gains the 'deterministic' grading_source. SQLite cannot ALTER a CHECK
-- constraint, so the table is rebuilt (same pattern as 070/071/110).
PRAGMA foreign_keys=OFF;

CREATE TABLE attempt_feedback_metadata_new (
  attempt_id TEXT PRIMARY KEY REFERENCES practice_attempts(id) ON DELETE CASCADE,
  grading_source TEXT NOT NULL CHECK (grading_source IN ('ai', 'codex', 'self', 'deterministic')),
  fallback_reason TEXT,
  agent_run_id TEXT REFERENCES agent_runs(id),
  fatal_errors_json TEXT NOT NULL DEFAULT '[]',
  feedback_md TEXT,
  repair_suggestions_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  shown_count INTEGER NOT NULL DEFAULT 0 CHECK (shown_count >= 0),
  first_shown_at TEXT,
  last_shown_at TEXT
);

INSERT INTO attempt_feedback_metadata_new (
  attempt_id, grading_source, fallback_reason, agent_run_id, fatal_errors_json,
  feedback_md, repair_suggestions_json, created_at, updated_at,
  shown_count, first_shown_at, last_shown_at
)
SELECT
  attempt_id, grading_source, fallback_reason, agent_run_id, fatal_errors_json,
  feedback_md, repair_suggestions_json, created_at, updated_at,
  shown_count, first_shown_at, last_shown_at
FROM attempt_feedback_metadata;

DROP TABLE attempt_feedback_metadata;
ALTER TABLE attempt_feedback_metadata_new RENAME TO attempt_feedback_metadata;

PRAGMA foreign_key_check;
PRAGMA foreign_keys=ON;
