-- Probe/EIG redesign Checkpoint 2/3 (spec_probe_eig_redesign.md):
-- predictive-EIG selection telemetry and learner-initiated calibration sessions.

-- §7.3/§13.1: utility components stay separately inspectable. The committed
-- presentation records the primary selection objective and every component
-- (hypothesis EIG, predictive EIG, information rate, expected seconds, task
-- evidence share for dialogue turns) as JSON.
ALTER TABLE probe_presentations ADD COLUMN selection_components_json TEXT;

-- §5.9: a calibration session batches multiple episode blocks across a goal's
-- facet scope in one sitting, with its own time budget, progress display, and
-- stop control. It lifts only the per-session qualifying-observation cap.
CREATE TABLE probe_calibration_sessions (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  goal_id TEXT,
  learning_object_ids_json TEXT NOT NULL,
  planned_episode_ids_json TEXT NOT NULL,
  time_budget_minutes INTEGER NOT NULL CHECK (time_budget_minutes >= 1),
  status TEXT NOT NULL CHECK (status IN ('active', 'completed', 'stopped', 'expired')),
  started_at TEXT NOT NULL,
  ended_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
-- One active calibration session per client session.
CREATE UNIQUE INDEX idx_probe_calibration_sessions_active
  ON probe_calibration_sessions(session_id)
  WHERE status = 'active';
