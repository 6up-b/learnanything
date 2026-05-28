ALTER TABLE practice_attempts ADD COLUMN session_id TEXT;
ALTER TABLE practice_attempts ADD COLUMN scheduler_slate_id TEXT;
ALTER TABLE practice_attempts ADD COLUMN scheduler_candidate_id TEXT;

ALTER TABLE attempt_feedback_metadata ADD COLUMN shown_count INTEGER NOT NULL DEFAULT 0 CHECK (shown_count >= 0);
ALTER TABLE attempt_feedback_metadata ADD COLUMN first_shown_at TEXT;
ALTER TABLE attempt_feedback_metadata ADD COLUMN last_shown_at TEXT;

CREATE TABLE IF NOT EXISTS scheduler_slates (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  generated_at TEXT NOT NULL,
  requested_limit INTEGER,
  returned_count INTEGER NOT NULL DEFAULT 0,
  candidate_count INTEGER NOT NULL DEFAULT 0,
  chosen_practice_item_id TEXT,
  chosen_attempt_id TEXT,
  selection_policy TEXT NOT NULL,
  session_context_json TEXT NOT NULL,
  config_snapshot_json TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scheduler_slates_session
  ON scheduler_slates(session_id, generated_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_scheduler_slates_chosen_attempt
  ON scheduler_slates(chosen_attempt_id);

CREATE TABLE IF NOT EXISTS scheduler_slate_candidates (
  id TEXT PRIMARY KEY,
  slate_id TEXT NOT NULL REFERENCES scheduler_slates(id) ON DELETE CASCADE,
  practice_item_id TEXT NOT NULL,
  learning_object_id TEXT,
  rank INTEGER NOT NULL CHECK (rank >= 1),
  returned_rank INTEGER CHECK (returned_rank IS NULL OR returned_rank >= 1),
  was_returned INTEGER NOT NULL DEFAULT 0 CHECK (was_returned IN (0, 1)),
  chosen_attempt_id TEXT,
  selected_mode TEXT NOT NULL,
  priority REAL NOT NULL,
  selection_reward REAL,
  predicted_correctness REAL,
  legacy_priority REAL,
  expected_information_gain REAL,
  readiness_factor REAL,
  components_json TEXT NOT NULL,
  reward_debug_json TEXT,
  target_scope_json TEXT,
  plain_english_json TEXT,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  chosen_at TEXT,
  UNIQUE (slate_id, practice_item_id)
);
CREATE INDEX IF NOT EXISTS idx_scheduler_slate_candidates_slate_rank
  ON scheduler_slate_candidates(slate_id, rank);
CREATE INDEX IF NOT EXISTS idx_scheduler_slate_candidates_item
  ON scheduler_slate_candidates(practice_item_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scheduler_slate_candidates_chosen
  ON scheduler_slate_candidates(chosen_attempt_id);

CREATE TABLE IF NOT EXISTS learning_outcome_labels (
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
    outcome_rubric_score IS NULL OR (outcome_rubric_score >= 0 AND outcome_rubric_score <= 4)
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
CREATE INDEX IF NOT EXISTS idx_learning_outcome_labels_source
  ON learning_outcome_labels(source_attempt_id, label_type, created_at);
CREATE INDEX IF NOT EXISTS idx_learning_outcome_labels_outcome
  ON learning_outcome_labels(outcome_attempt_id);
