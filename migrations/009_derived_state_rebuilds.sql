CREATE TABLE IF NOT EXISTS derived_state_rebuilds (
  id TEXT PRIMARY KEY,
  scope TEXT NOT NULL,
  learning_object_ids_json TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  rebuilt_learning_objects INTEGER NOT NULL,
  replayed_attempts INTEGER NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_derived_state_rebuilds_latest
  ON derived_state_rebuilds(created_at DESC, id DESC);
