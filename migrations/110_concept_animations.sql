-- AI-generated Manim explainer animations (spec_fork_features §2). One row per
-- generation request: the durable status machine, the candidate scene code
-- (kept on failure for debugging, with a capped stderr tail), provenance of
-- the authoring model, and the content-addressed mp4 once rendered. Videos
-- live at media/animations/sha256-<hex>.mp4 under the vault root and are
-- served over the llmedia:// scheme — bytes never cross the RPC channel.
CREATE TABLE concept_animations (
  id TEXT PRIMARY KEY,
  concept_id TEXT NOT NULL,
  learning_object_id TEXT,
  status TEXT NOT NULL CHECK (
    status IN ('queued', 'generating', 'validating', 'rendering', 'completed', 'failed', 'cancelled')
  ),
  scene_code TEXT,
  scene_class TEXT,
  title TEXT,
  narration_md TEXT,
  video_hash TEXT,
  video_file_name TEXT,
  duration_seconds REAL,
  provider TEXT,
  model TEXT,
  prompt_version TEXT,
  quality TEXT,
  repair_attempted INTEGER NOT NULL DEFAULT 0,
  failure_stage TEXT,
  failure_reason TEXT,
  render_stderr TEXT,
  batch_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  completed_at TEXT
);

CREATE INDEX idx_concept_animations_concept
  ON concept_animations(concept_id, status, created_at);
