CREATE TABLE IF NOT EXISTS ability_transition_events (
  attempt_id TEXT PRIMARY KEY REFERENCES practice_attempts(id) ON DELETE CASCADE,
  learning_object_id TEXT NOT NULL,
  practice_item_id TEXT NOT NULL,
  transition_type TEXT NOT NULL,
  expected_skill_gain REAL NOT NULL DEFAULT 0.0,
  target_facets_json TEXT NOT NULL,
  reason TEXT NOT NULL,
  applied_to_belief_counts INTEGER NOT NULL DEFAULT 0 CHECK (applied_to_belief_counts IN (0, 1)),
  applied_to_mastery INTEGER NOT NULL DEFAULT 0 CHECK (applied_to_mastery IN (0, 1)),
  applied_to_facet_recall INTEGER NOT NULL DEFAULT 0 CHECK (applied_to_facet_recall IN (0, 1)),
  process_noise REAL,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ability_transition_events_lo
  ON ability_transition_events(learning_object_id, created_at);
