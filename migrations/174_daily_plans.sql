-- Daily-loop DL1 (daily_plan_v1, mvp-0.12): the finite daily plan
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
