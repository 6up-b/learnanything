-- mvp-0.21 (value-of-information stopping, owner-directed 2026-10-12/13): a
-- probe episode keeps asking while its next observation's value of
-- information pays for its minutes, and stops when it no longer does. The
-- new completion_reason 'value_of_information_stop' records that stop
-- distinctly from 'decision_stable', 'action_equivalent' and the robust
-- abstention, so eval can compare the stopping families; the new nullable
-- completion_detail_json keeps the stop decision with its forecast (predicted
-- outcomes, EIG, EVSI point and robust, P(action change), the heuristic
-- parameters) beside the episode it ended. Below mvp-0.21, or with
-- voi_stopping off, nothing writes either, so earlier versions are unchanged.
-- Built as migration 187 (a placeholder) and renumbered 200 when it merged
-- onto main after migrations 184-199.
--
-- SQLite cannot ALTER a CHECK constraint, so probe_episodes is rebuilt (the
-- pattern of migrations 070/071/110). Data-preserving: every existing row and
-- column is copied as is, the new column is NULL.
PRAGMA foreign_keys=OFF;

CREATE TABLE probe_episodes_new (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (
    status IN ('pending_items', 'in_progress', 'complete', 'abandoned', 'converted_to_tutoring')
  ),
  trigger TEXT NOT NULL CHECK (
    trigger IN ('initial', 'misconception', 'stale_uncertainty', 'manual', 'goal_diagnostic')
  ),
  hypothesis_set_id TEXT,
  active_state_segment_id TEXT,
  target_decision_json TEXT,
  required_facets_json TEXT,
  minimum_independent_observations INTEGER NOT NULL DEFAULT 2 CHECK (minimum_independent_observations >= 1),
  maximum_observations INTEGER NOT NULL DEFAULT 4 CHECK (maximum_observations >= 1),
  entered_at TEXT,
  completed_at TEXT,
  completion_reason TEXT CHECK (
    completion_reason IS NULL OR completion_reason IN (
      'decision_stable',
      'predictive_uncertainty_below_threshold',
      'observation_budget_exhausted',
      'no_suitable_candidate',
      'converted_to_tutoring',
      'learner_abandoned',
      'manual_stop',
      'fast_path_strong_claim',
      'superseded_by_redesign',
      'couldnt_reliably_distinguish',
      'action_equivalent',
      'value_of_information_stop'
    )
  ),
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  origin TEXT,
  target_contract_version_id TEXT,
  target_support_hash TEXT,
  calibration_model_id TEXT,
  calibration_model_hash TEXT,
  probe_mapping_version TEXT,
  completion_posterior_json TEXT,
  completion_detail_json TEXT
);

INSERT INTO probe_episodes_new (
  id, learning_object_id, status, trigger, hypothesis_set_id, active_state_segment_id,
  target_decision_json, required_facets_json, minimum_independent_observations,
  maximum_observations, entered_at, completed_at, completion_reason, algorithm_version,
  created_at, updated_at, origin, target_contract_version_id, target_support_hash,
  calibration_model_id, calibration_model_hash, probe_mapping_version, completion_posterior_json
)
SELECT
  id, learning_object_id, status, trigger, hypothesis_set_id, active_state_segment_id,
  target_decision_json, required_facets_json, minimum_independent_observations,
  maximum_observations, entered_at, completed_at, completion_reason, algorithm_version,
  created_at, updated_at, origin, target_contract_version_id, target_support_hash,
  calibration_model_id, calibration_model_hash, probe_mapping_version, completion_posterior_json
FROM probe_episodes;

DROP TABLE probe_episodes;
ALTER TABLE probe_episodes_new RENAME TO probe_episodes;

CREATE INDEX idx_probe_episodes_lo ON probe_episodes(learning_object_id, created_at);
CREATE UNIQUE INDEX idx_probe_episodes_open
  ON probe_episodes(learning_object_id)
  WHERE status IN ('pending_items', 'in_progress');
CREATE INDEX idx_probe_episodes_target_version
  ON probe_episodes(target_contract_version_id);

PRAGMA foreign_key_check;
PRAGMA foreign_keys=ON;
