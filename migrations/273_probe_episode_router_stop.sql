-- The probe router's continuation (refactor G2, docs/reviews/algorithm-probe-router.md, "The continuation decision"):
-- a router-owned probe episode the router decides not to continue completes with its own reason. probe_episodes'
-- completion_reason gains 'router_stop': the router's continuation decision (a router_decisions row, named in the
-- episode's completion_detail_json) chose to stop. It is not the legacy value stop ('value_of_information_stop'), and
-- no other reason describes it.
--
-- The rebuild follows 200 and 272: SQLite cannot widen a CHECK in place, so probe_episodes is rebuilt
-- temp-then-rename with every row and id preserved, under PRAGMA foreign_keys = OFF; probe_presentations' foreign key
-- names probe_episodes and resolves to the rebuilt table; DROP TABLE removes its three indexes, recreated on the renamed
-- table with the same names and definitions; the runner's foreign_key_check runs before the migration commits. The same
-- columns, defaults and CHECKs otherwise. No row changes.
PRAGMA foreign_keys = OFF;

CREATE TABLE probe_episodes__273 (
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
      'value_of_information_stop',
      'router_stop'
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
INSERT INTO probe_episodes__273 (
  id, learning_object_id, status, trigger, hypothesis_set_id, active_state_segment_id, target_decision_json,
  required_facets_json, minimum_independent_observations, maximum_observations, entered_at, completed_at,
  completion_reason, algorithm_version, created_at, updated_at, origin, target_contract_version_id,
  target_support_hash, calibration_model_id, calibration_model_hash, probe_mapping_version,
  completion_posterior_json, completion_detail_json
)
SELECT
  id, learning_object_id, status, trigger, hypothesis_set_id, active_state_segment_id, target_decision_json,
  required_facets_json, minimum_independent_observations, maximum_observations, entered_at, completed_at,
  completion_reason, algorithm_version, created_at, updated_at, origin, target_contract_version_id,
  target_support_hash, calibration_model_id, calibration_model_hash, probe_mapping_version,
  completion_posterior_json, completion_detail_json
FROM probe_episodes;

DROP TABLE probe_episodes;
ALTER TABLE probe_episodes__273 RENAME TO probe_episodes;
CREATE INDEX idx_probe_episodes_lo ON probe_episodes(learning_object_id, created_at);
CREATE UNIQUE INDEX idx_probe_episodes_open
  ON probe_episodes(learning_object_id)
  WHERE status IN ('pending_items', 'in_progress');
CREATE INDEX idx_probe_episodes_target_version
  ON probe_episodes(target_contract_version_id);

PRAGMA foreign_keys = ON;
