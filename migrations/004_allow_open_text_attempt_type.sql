PRAGMA foreign_keys = OFF;

DROP INDEX IF EXISTS idx_attempts_lo_time;
DROP INDEX IF EXISTS idx_attempts_item_time;

CREATE TABLE practice_attempts_new (
  id TEXT PRIMARY KEY,
  practice_item_id TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  subject TEXT,
  concept TEXT,
  practice_mode TEXT NOT NULL,
  attempt_type TEXT NOT NULL CHECK (
    attempt_type IN (
      'independent_attempt',
      'hinted_attempt',
      'dont_know',
      'diagnostic_probe',
      'guided_walkthrough',
      'reconstruction_after_walkthrough',
      'skip',
      'self_report',
      'open_text'
    )
  ),
  learner_answer_md TEXT,
  evidence_facets_json TEXT,
  evidence_weights_json TEXT,
  rubric_score INTEGER CHECK (rubric_score IS NULL OR rubric_score BETWEEN 0 AND 4),
  correctness REAL CHECK (correctness IS NULL OR (correctness >= 0.0 AND correctness <= 1.0)),
  confidence INTEGER CHECK (confidence IS NULL OR confidence BETWEEN 1 AND 5),
  latency_seconds INTEGER CHECK (latency_seconds IS NULL OR latency_seconds >= 0),
  hints_used INTEGER NOT NULL DEFAULT 0 CHECK (hints_used >= 0),
  error_type TEXT,
  grader_confidence REAL CHECK (
    grader_confidence IS NULL OR (grader_confidence >= 0.0 AND grader_confidence <= 1.0)
  ),
  manual_review INTEGER NOT NULL DEFAULT 0 CHECK (manual_review IN (0, 1)),
  manual_review_reason TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT
);

INSERT INTO practice_attempts_new(
  id, practice_item_id, learning_object_id, subject, concept, practice_mode,
  attempt_type, learner_answer_md, evidence_facets_json, evidence_weights_json,
  rubric_score, correctness, confidence, latency_seconds, hints_used,
  error_type, grader_confidence, manual_review, manual_review_reason,
  created_at, updated_at
)
SELECT
  id, practice_item_id, learning_object_id, subject, concept, practice_mode,
  attempt_type, learner_answer_md, evidence_facets_json, evidence_weights_json,
  rubric_score, correctness, confidence, latency_seconds, hints_used,
  error_type, grader_confidence, manual_review, manual_review_reason,
  created_at, updated_at
FROM practice_attempts;

DROP TABLE practice_attempts;
ALTER TABLE practice_attempts_new RENAME TO practice_attempts;

CREATE INDEX idx_attempts_lo_time
  ON practice_attempts(learning_object_id, created_at);
CREATE INDEX idx_attempts_item_time
  ON practice_attempts(practice_item_id, created_at);

PRAGMA foreign_keys = ON;
