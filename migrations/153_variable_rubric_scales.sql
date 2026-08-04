-- Rubric criteria define an item's point scale.  Remove the historical global
-- four-point ceiling from attempt facts and their derived outcome labels.
-- SQLite cannot alter CHECK constraints in place, so preserve the current
-- table shapes while rebuilding both constrained tables.

PRAGMA foreign_keys = OFF;

DROP INDEX IF EXISTS idx_attempts_lo_time;
DROP INDEX IF EXISTS idx_attempts_item_time;
DROP INDEX IF EXISTS idx_attempts_probe_presentation;
DROP INDEX IF EXISTS idx_practice_attempts_submission_id;
DROP INDEX IF EXISTS idx_practice_attempts_created;
DROP INDEX IF EXISTS idx_practice_attempts_item_created;

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
      'open_text',
      'exam_evidence',
      'teach_back',
      'exam_attempt'
    )
  ),
  learner_answer_md TEXT,
  evidence_facets_json TEXT,
  evidence_weights_json TEXT,
  rubric_score INTEGER CHECK (rubric_score IS NULL OR rubric_score >= 0),
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
  updated_at TEXT,
  session_id TEXT,
  scheduler_slate_id TEXT,
  scheduler_candidate_id TEXT,
  primed INTEGER NOT NULL DEFAULT 0,
  probe_presentation_id TEXT,
  answer_confidence INTEGER,
  submission_id TEXT,
  declared_dont_know INTEGER NOT NULL DEFAULT 0
);

INSERT INTO practice_attempts_new(
  id, practice_item_id, learning_object_id, subject, concept, practice_mode,
  attempt_type, learner_answer_md, evidence_facets_json, evidence_weights_json,
  rubric_score, correctness, confidence, latency_seconds, hints_used,
  error_type, grader_confidence, manual_review, manual_review_reason,
  created_at, updated_at, session_id, scheduler_slate_id, scheduler_candidate_id,
  primed, probe_presentation_id, answer_confidence, submission_id,
  declared_dont_know
)
SELECT
  id, practice_item_id, learning_object_id, subject, concept, practice_mode,
  attempt_type, learner_answer_md, evidence_facets_json, evidence_weights_json,
  rubric_score, correctness, confidence, latency_seconds, hints_used,
  error_type, grader_confidence, manual_review, manual_review_reason,
  created_at, updated_at, session_id, scheduler_slate_id, scheduler_candidate_id,
  primed, probe_presentation_id, answer_confidence, submission_id,
  declared_dont_know
FROM practice_attempts;

DROP TABLE practice_attempts;
ALTER TABLE practice_attempts_new RENAME TO practice_attempts;

CREATE INDEX idx_attempts_lo_time
  ON practice_attempts(learning_object_id, created_at);
CREATE INDEX idx_attempts_item_time
  ON practice_attempts(practice_item_id, created_at);
CREATE UNIQUE INDEX idx_attempts_probe_presentation
  ON practice_attempts(probe_presentation_id)
  WHERE probe_presentation_id IS NOT NULL;
CREATE UNIQUE INDEX idx_practice_attempts_submission_id
  ON practice_attempts(submission_id)
  WHERE submission_id IS NOT NULL;
CREATE INDEX idx_practice_attempts_created
  ON practice_attempts(created_at, id);
CREATE INDEX idx_practice_attempts_item_created
  ON practice_attempts(practice_item_id, created_at, id);

DROP INDEX IF EXISTS idx_learning_outcome_labels_source;
DROP INDEX IF EXISTS idx_learning_outcome_labels_outcome;

CREATE TABLE learning_outcome_labels_new (
  id TEXT PRIMARY KEY,
  source_attempt_id TEXT NOT NULL REFERENCES practice_attempts(id) ON DELETE CASCADE,
  outcome_attempt_id TEXT NOT NULL REFERENCES practice_attempts(id) ON DELETE CASCADE,
  label_type TEXT NOT NULL CHECK (
    label_type IN ('same_item_retention', 'same_learning_object_transfer')
  ),
  practice_item_id TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  label_value REAL CHECK (label_value IS NULL OR (label_value >= 0.0 AND label_value <= 1.0)),
  outcome_correctness REAL CHECK (
    outcome_correctness IS NULL OR (outcome_correctness >= 0.0 AND outcome_correctness <= 1.0)
  ),
  outcome_rubric_score INTEGER CHECK (
    outcome_rubric_score IS NULL OR outcome_rubric_score >= 0
  ),
  outcome_attempt_type TEXT,
  outcome_hints_used INTEGER,
  outcome_latency_seconds INTEGER,
  elapsed_seconds INTEGER CHECK (elapsed_seconds IS NULL OR elapsed_seconds >= 0),
  intervening_attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (intervening_attempt_count >= 0),
  metadata_json TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (source_attempt_id, outcome_attempt_id, label_type)
);

INSERT INTO learning_outcome_labels_new(
  id, source_attempt_id, outcome_attempt_id, label_type, practice_item_id,
  learning_object_id, label_value, outcome_correctness, outcome_rubric_score,
  outcome_attempt_type, outcome_hints_used, outcome_latency_seconds,
  elapsed_seconds, intervening_attempt_count, metadata_json, algorithm_version,
  created_at
)
SELECT
  id, source_attempt_id, outcome_attempt_id, label_type, practice_item_id,
  learning_object_id, label_value, outcome_correctness, outcome_rubric_score,
  outcome_attempt_type, outcome_hints_used, outcome_latency_seconds,
  elapsed_seconds, intervening_attempt_count, metadata_json, algorithm_version,
  created_at
FROM learning_outcome_labels;

DROP TABLE learning_outcome_labels;
ALTER TABLE learning_outcome_labels_new RENAME TO learning_outcome_labels;

CREATE INDEX idx_learning_outcome_labels_source
  ON learning_outcome_labels(source_attempt_id, label_type, created_at);
CREATE INDEX idx_learning_outcome_labels_outcome
  ON learning_outcome_labels(outcome_attempt_id);

PRAGMA foreign_keys = ON;
