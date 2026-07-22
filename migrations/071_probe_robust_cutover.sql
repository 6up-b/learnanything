-- Probe-episode robust cutover (spec_p0_measurement_correctness §4.2, change-log
-- entry b'). Pins the calibration channel + coarse-mapping version on the episode
-- at open so selection (robust EIG ensemble) and update (observed_update) consume
-- the identical pinned channel (invariant 3), and adds the mvp-0.8 abstention
-- completion outcome. Data-preserving.
--
--   calibration_model_id / calibration_model_hash: the ResolvedModel pinned at
--     episode open. Both the robust selection ensemble and the decision-time
--     observed_update seed from calibration_model_hash, so a change of the active
--     head model can never silently reinterpret a historical episode decision.
--   probe_mapping_version: the versioned deterministic probe-outcome -> coarse-class
--     mapping (§3.1) in force for this episode; snapshotted so replay reproduces it.
--   completion_reason 'couldnt_reliably_distinguish': the explicit robust abstention
--     outcome (§4.2 / U-021) surfaced in the episode result under mvp-0.8.
--
-- SQLite cannot ALTER a CHECK constraint, so probe_episodes is rebuilt (the same
-- pattern migration 070 used for activity_observations / measurement_events). The
-- three pinned-channel columns are added in the rebuilt schema. Byte-safe for legacy
-- mvp-0.6/0.7 replay: the legacy point path never reads these columns and legacy
-- episodes never write the new completion reason.
--
-- foreign_keys is toggled OFF for the table-rebuild procedure (same as migration
-- 070): dropping + recreating a table that child tables (probe_presentations,
-- probe_observations, ...) reference would otherwise trip enforcement mid-rebuild.
-- foreign_key_check re-validates before re-enabling.
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
      'couldnt_reliably_distinguish'
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
  probe_mapping_version TEXT
);

INSERT INTO probe_episodes_new (
  id, learning_object_id, status, trigger, hypothesis_set_id, active_state_segment_id,
  target_decision_json, required_facets_json, minimum_independent_observations,
  maximum_observations, entered_at, completed_at, completion_reason, algorithm_version,
  created_at, updated_at, origin, target_contract_version_id, target_support_hash
)
SELECT
  id, learning_object_id, status, trigger, hypothesis_set_id, active_state_segment_id,
  target_decision_json, required_facets_json, minimum_independent_observations,
  maximum_observations, entered_at, completed_at, completion_reason, algorithm_version,
  created_at, updated_at, origin, target_contract_version_id, target_support_hash
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
