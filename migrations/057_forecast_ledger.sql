-- Frozen, gradeable learner-facing forecasts. Rendering references these rows;
-- it never mints a forecast implicitly.
CREATE TABLE forecasts (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('decay', 'pace', 'plan')),
  issued_at TEXT NOT NULL,
  as_of_input_snapshot_hash TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  resolution_rule_version TEXT NOT NULL,
  horizon TEXT NOT NULL,
  target_metric TEXT NOT NULL,
  predicted_value REAL NOT NULL,
  model_coverage_json TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'open'
    CHECK (status IN ('open', 'resolved', 'censored', 'unobservable')),
  resolved_value REAL,
  resolved_at TEXT,
  projection_drift REAL,
  UNIQUE(goal_id, kind, as_of_input_snapshot_hash)
);

CREATE INDEX idx_forecasts_due ON forecasts(status, horizon);
CREATE INDEX idx_forecasts_goal ON forecasts(goal_id, issued_at, id);
