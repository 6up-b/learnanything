-- Daily-loop DL1 (daily_plan_v1, mvp-0.14): the finite daily plan
-- (built as migration 174 at mvp-0.12; renumbered 180 and relabelled
-- mvp-0.14 when it merged after main's 174-179, none of which touches
-- attention_blocks or facet_outcome_observations)
-- (spec_daily_loop_v1.md §6, §10). Workflow and receipt rows only: nothing
-- here is evidence, mastery, certification or FSRS state, and replay never
-- reads it.

-- One plan per local calendar date and kind: the day's normal (or re-entry)
-- plan and its "keep going" extensions, linked by parent_plan_id. Mutable
-- workflow state (status, budget after a minutes tap); the decisions that
-- built it are attention_block_events receipts.
CREATE TABLE daily_plans (
  id TEXT PRIMARY KEY,
  local_date TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('normal', 'reentry', 'keep_going')),
  parent_plan_id TEXT REFERENCES daily_plans(id),
  minutes_budget REAL NOT NULL CHECK (minutes_budget >= 0),
  -- The learner's ordinary daily budget in force (§6.6): carried forward from
  -- the previous plan unless a chip set it; generated budgets never change it.
  remembered_minutes INTEGER NOT NULL CHECK (remembered_minutes > 0),
  minutes_source TEXT NOT NULL CHECK (minutes_source IN ('chip', 'carried', 'generated')),
  -- Lane minutes, loads, caps and one-line reasons (§6.2), plus re-plans.
  split_json TEXT NOT NULL,
  -- §6.3 admission inputs and result.
  admission_json TEXT NOT NULL,
  estimator_version TEXT NOT NULL,
  source TEXT NOT NULL,
  chooser TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open'
    CHECK (status IN ('open', 'complete', 'stopped', 'abandoned')),
  stop_reason TEXT,
  algorithm_version TEXT NOT NULL,
  config_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  completed_at TEXT
);
CREATE INDEX idx_daily_plans_date ON daily_plans(local_date, created_at, id);

-- A plan's blocks reuse the P4 attention-block store (§3.2, §10). Existing
-- rows (the staged policy's) keep these NULL.
ALTER TABLE attention_blocks ADD COLUMN daily_plan_id TEXT REFERENCES daily_plans(id);
ALTER TABLE attention_blocks ADD COLUMN plan_ordinal INTEGER;
ALTER TABLE attention_blocks ADD COLUMN lane TEXT;
ALTER TABLE attention_blocks ADD COLUMN chosen_by TEXT;
ALTER TABLE attention_blocks ADD COLUMN decision_ref TEXT;
ALTER TABLE attention_blocks ADD COLUMN reading_json TEXT;
CREATE UNIQUE INDEX idx_attention_blocks_plan
  ON attention_blocks(daily_plan_id, plan_ordinal) WHERE daily_plan_id IS NOT NULL;

-- Owner decision 2026-10-12 (applied at DL1's merge): a plan-served attempt
-- carries a `daily_plan` serving kind in the learner field, read from the
-- plan's `item_served` receipts, instead of `unknown`. The field's DERIVED
-- read model checks its serving_origin vocabulary, so the table is rebuilt
-- with every column, key and index as migration 167 created it (unchanged
-- through 179); only the CHECK gains `daily_plan`. Its rows are copied as
-- they are (all already valid) and the next rebuild rewrites them.
CREATE TABLE facet_outcome_observations_new (
  attempt_id TEXT NOT NULL,
  facet_id TEXT NOT NULL,
  practice_item_id TEXT NOT NULL,
  item_snapshot_hash TEXT,
  revision_status TEXT NOT NULL CHECK (revision_status IN ('exact','reconstructed_current','excluded')),
  observed_at TEXT NOT NULL,
  outcome REAL NOT NULL CHECK (outcome BETWEEN 0 AND 1),
  facet_share REAL NOT NULL CHECK (facet_share > 0 AND facet_share <= 1),
  effective_mass REAL NOT NULL CHECK (effective_mass >= 0),
  cold INTEGER NOT NULL CHECK (cold IN (0,1)),
  assisted INTEGER NOT NULL CHECK (assisted IN (0,1)),
  primed INTEGER NOT NULL CHECK (primed IN (0,1)),
  surface_group_id TEXT,
  serving_origin TEXT NOT NULL CHECK (serving_origin IN ('learner_pick','system_probe','forced_followup','requested','daily_plan','unknown')),
  serving_propensity REAL CHECK (serving_propensity IS NULL OR serving_propensity BETWEEN 0 AND 1),
  scheduler_candidate_id TEXT,
  PRIMARY KEY (attempt_id, facet_id)
);
INSERT INTO facet_outcome_observations_new (
  attempt_id, facet_id, practice_item_id, item_snapshot_hash, revision_status, observed_at, outcome,
  facet_share, effective_mass, cold, assisted, primed, surface_group_id, serving_origin,
  serving_propensity, scheduler_candidate_id
)
SELECT
  attempt_id, facet_id, practice_item_id, item_snapshot_hash, revision_status, observed_at, outcome,
  facet_share, effective_mass, cold, assisted, primed, surface_group_id, serving_origin,
  serving_propensity, scheduler_candidate_id
FROM facet_outcome_observations;
DROP TABLE facet_outcome_observations;
ALTER TABLE facet_outcome_observations_new RENAME TO facet_outcome_observations;
CREATE INDEX facet_outcome_observations_time ON facet_outcome_observations(observed_at,attempt_id);
