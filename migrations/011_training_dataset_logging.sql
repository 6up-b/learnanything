-- Training-dataset logging (spec_training_dataset_architecture.md §3.2, §3.3).
-- Makes the scheduler decision log trainable by (1) freezing the decision-time
-- feature inputs that are otherwise recomputed live, and (2) recording the
-- selection propensity needed for off-policy estimation.
-- No live algorithm behavior changes; these are append-only logging additions.

-- (§3.2) Frozen decision-time feature snapshots. decision_id is a soft reference
-- whose target table depends on decision_type: 'selection' -> scheduler_slate_candidates.id,
-- 'probe' -> elicitation_events.id, 'grading' -> practice_attempts.id. No FK: the
-- application validates the reference, matching the soft-reference convention.
CREATE TABLE IF NOT EXISTS decision_features (
  id TEXT PRIMARY KEY,
  decision_id TEXT NOT NULL,
  decision_type TEXT NOT NULL CHECK (decision_type IN ('selection', 'probe', 'grading')),
  ability_vector_json TEXT NOT NULL,
  item_demand_vector_json TEXT,
  context_json TEXT,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (decision_id, decision_type)
);

CREATE INDEX IF NOT EXISTS idx_decision_features_type_time
  ON decision_features(decision_type, created_at);

-- (§3.3) Propensity / exploration logging on the candidate slate. selection_propensity
-- is P(this candidate chosen | slate) under the (possibly stochastic) selection policy;
-- it enables IPS / doubly-robust off-policy estimation. exploration_flag marks rows
-- chosen by seeded exploration rather than the greedy argmax. selection_temperature
-- records the softmax temperature (NULL when selection was deterministic).
ALTER TABLE scheduler_slate_candidates ADD COLUMN selection_propensity REAL;
ALTER TABLE scheduler_slate_candidates ADD COLUMN exploration_flag INTEGER NOT NULL DEFAULT 0 CHECK (exploration_flag IN (0, 1));
ALTER TABLE scheduler_slate_candidates ADD COLUMN selection_temperature REAL;
