-- Slice A Phase 6 (learner field F2, mvp-0.11): starting new material without
-- ceremony. Receipts only: nothing here is evidence, mastery or certification.

-- One row per "assumed known (not tested)" decision. Append-only. The first
-- review's outcome is joined from practice_attempts by report 3 and by the
-- serving read, never written back here.
CREATE TABLE assumption_decisions (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT NOT NULL,
  source TEXT NOT NULL CHECK (source IN ('self_report','fast_track','predictor','quick_check')),
  -- What fired it: i_know_this | too_easy | fast_track_rule | quick_check_result | predictor_rule.
  trigger_kind TEXT NOT NULL,
  -- The item, LO list, attempt ids or calibration session that triggered it.
  trigger_ref TEXT,
  -- P(theta_L > theta_known) under the active predictor; NULL for self-reports.
  p REAL CHECK (p IS NULL OR (p >= 0 AND p <= 1)),
  -- 80% interval of theta_L (logit), as JSON [low, high]; NULL when untested.
  interval_json TEXT,
  q_used REAL CHECK (q_used IS NULL OR (q_used > 0 AND q_used < 1)),
  theta_known REAL,
  predictor TEXT NOT NULL,
  predictor_version TEXT NOT NULL,
  first_review_due TEXT NOT NULL,
  quick_check_session_id TEXT,
  algorithm_version TEXT NOT NULL,
  -- The placement config in force and every input the rule read (G8).
  config_json TEXT NOT NULL,
  inputs_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX assumption_decisions_lo ON assumption_decisions(learning_object_id, created_at, id);

-- "I don't know this": an immediate return to learning. assumption_id is the
-- open assumption it closed, or NULL when the LO was not assumed (the report
-- still keeps the LO out of fast-track).
CREATE TABLE assumption_returns (
  id TEXT PRIMARY KEY,
  assumption_id TEXT REFERENCES assumption_decisions(id),
  learning_object_id TEXT NOT NULL,
  reason TEXT NOT NULL CHECK (reason IN ('dont_know_this')),
  trigger_ref TEXT,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX assumption_returns_lo ON assumption_returns(learning_object_id, created_at, id);

-- Queue state of the optional "Check what I already know". The calibration
-- session row keeps the budget and stop/expiry; this keeps the scope, k and
-- the moment its results fed the split.
CREATE TABLE placement_quick_checks (
  calibration_session_id TEXT PRIMARY KEY REFERENCES probe_calibration_sessions(id),
  session_id TEXT NOT NULL,
  learning_object_ids_json TEXT NOT NULL,
  k INTEGER NOT NULL CHECK (k >= 1),
  budget_minutes INTEGER NOT NULL CHECK (budget_minutes >= 1),
  predictor TEXT NOT NULL,
  predictor_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  finished_at TEXT,
  outcome_json TEXT
);
