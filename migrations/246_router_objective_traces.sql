-- Router objective RO4 (docs/specs/spec_router_objective_v1.md §8.8): the
-- objective's trace, one immutable row per decision.
--
-- Additive: one new append-only RECEIPT table; no existing table changes.
--
-- router_objective_traces: every value the decision computed, so a reader can
-- see each sensor, the objective's terms, both policies, the mix and the
-- output (owner's requirement, Nov 3 2026): per candidate the sensors (each
-- value, model and prompt version, receipt id, whether it reached Q-bar) and
-- terms (the crossed-date reward, the undated reward, the kappa integral,
-- E[V(x')], T_C, Q-bar, Q-bar - V, Q-bar - Q-bar(stop), precision); the
-- policies (pi_L and its rationale, a_Q, availability, latency, spend, staged
-- and the Decider as advice); the mixing (the weight's posterior, p, the
-- minimum shares, w, the weights after fallback, mu, the seed, the chosen
-- action and which draw chose it); the evaluation's frozen uses (U_i, B_i,
-- m0, C0, the objective version); the frontier (G against minutes); the
-- versions. The JSON is in trace_json; the columns are what the report and
-- the price's daily seed read. It references RO0's decision-state row (§4
-- row 9) by id. Ids and numbers, plus the LLM policy's unvalidated rationale
-- (at most three sentences, as the decision's own payload). Nothing serving,
-- scheduling, evidence or certification reads it except the price's carry of
-- the day's kappa0 seed and the weight's posterior (both by their spec); a
-- rebuild never writes or clears it.
CREATE TABLE router_objective_traces (
  id TEXT PRIMARY KEY,
  -- router_decisions.id of the decision (plan_block or plan_interrupt).
  decision_id TEXT NOT NULL UNIQUE,
  decision_kind TEXT NOT NULL CHECK (decision_kind IN ('plan_block', 'plan_interrupt')),
  -- RO0's decision_state_receipts.id (§4 row 9), when one was written.
  decision_state_id TEXT,
  -- The trace's and the objective's code versions (router_objective.trace,
  -- router_objective.value).
  trace_version TEXT NOT NULL,
  objective_version TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  -- The plan's local date (the price's daily seed is per local date).
  local_date TEXT NOT NULL,
  session_id TEXT,
  -- Active minutes in the objective's session at the decision, and the
  -- plan's remembered minutes m-bar.
  session_minutes REAL,
  remembered_minutes REAL,
  -- kappa0 in force and how it was set (day_seed, carried_today,
  -- carried_last, tail_average, floored_at_last_positive); until RO5 the
  -- regime is the seed.
  kappa0 REAL,
  kappa_how TEXT,
  kappa_regime TEXT,
  -- The served choice, the component whose draw chose it, its exact
  -- probability, the weight w_i and the numeric policy's choice.
  chosen_ref TEXT NOT NULL,
  drawn_component TEXT,
  propensity REAL CHECK (propensity IS NULL OR (propensity > 0 AND propensity <= 1)),
  w REAL CHECK (w IS NULL OR (w >= 0 AND w <= 1)),
  numeric_ref TEXT,
  -- Each policy's status: answered, timeout, failed, invalid, spend,
  -- not_ready, unreachable (a failure's share went to staged).
  llm_status TEXT,
  numeric_status TEXT,
  -- Whether stop was in the support, and whether the runaway guard's
  -- session minutes were crossed (reported, never a budget).
  stop_in_support INTEGER NOT NULL CHECK (stop_in_support IN (0, 1)),
  guard_crossed INTEGER NOT NULL DEFAULT 0 CHECK (guard_crossed IN (0, 1)),
  -- When the decision's evaluation window B closes (its score can form only
  -- after it, from outcomes in it).
  window_closes_at TEXT,
  trace_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_router_objective_traces_local_date ON router_objective_traces(local_date, created_at);
CREATE INDEX idx_router_objective_traces_created ON router_objective_traces(created_at);

CREATE TRIGGER router_objective_traces_no_update
BEFORE UPDATE ON router_objective_traces
BEGIN
  SELECT RAISE(ABORT, 'router_objective_traces is append-only');
END;

CREATE TRIGGER router_objective_traces_no_delete
BEFORE DELETE ON router_objective_traces
BEGIN
  SELECT RAISE(ABORT, 'router_objective_traces is append-only');
END;

-- Router objective RO4 (§8.5): a goal contract's use weights (``use_weight``:
-- the dated goal's weight per topic at its date, and the undated use density
-- copied from config at creation) are in the content hash and out of the
-- support hash, and an edit to them alone is its own change class,
-- 'use_weight_change' (most-invalidating-wins puts it after 'reweight' and
-- before 'metadata'). No old row or hash is rewritten: a contract without the
-- field keeps its bytes, and its weights are the stated defaults.
--
-- SQLite cannot widen a CHECK in place, so goal_contract_versions is rebuilt
-- temp-then-rename with every row and id preserved, under
-- PRAGMA foreign_keys = OFF (the FK-safe precedent of 208, 212, 231 and 235).
-- Its self-reference (predecessor_version_id) is written against the final
-- name; goal_contract_heads, goal_contract_drafts and golden_path_runs keep
-- referencing goal_contract_versions by name; it has no triggers; its two
-- indexes are recreated as they were; the runner's foreign_key_check runs
-- before the migration commits. The same columns, defaults, CHECKs and UNIQUE
-- keys, the change class's set widened by one value.
PRAGMA foreign_keys = OFF;

CREATE TABLE goal_contract_versions__246 (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  version INTEGER NOT NULL CHECK (version >= 1),
  predecessor_version_id TEXT REFERENCES goal_contract_versions(id),
  contract_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  support_hash TEXT NOT NULL,
  contract_schema_version INTEGER NOT NULL,
  change_class TEXT NOT NULL CHECK (change_class IN (
    'confirm', 'support_change', 'authorized_depth_step',
    'evaluation_change', 'reweight', 'use_weight_change', 'metadata'
  )),
  -- authorized_depth_step receipt columns (§3.4); NULL for every other class:
  envelope_version TEXT,
  predecessor_milestone TEXT,
  activated_edge_id TEXT,
  evidence_receipt_json TEXT,
  burden_delta_json TEXT,
  author TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(goal_id, version),
  UNIQUE(goal_id, content_hash)
);
INSERT INTO goal_contract_versions__246 (
  id, goal_id, version, predecessor_version_id, contract_json, content_hash, support_hash,
  contract_schema_version, change_class, envelope_version, predecessor_milestone, activated_edge_id,
  evidence_receipt_json, burden_delta_json, author, reason, created_at
)
SELECT
  id, goal_id, version, predecessor_version_id, contract_json, content_hash, support_hash,
  contract_schema_version, change_class, envelope_version, predecessor_milestone, activated_edge_id,
  evidence_receipt_json, burden_delta_json, author, reason, created_at
FROM goal_contract_versions;

DROP TABLE goal_contract_versions;
ALTER TABLE goal_contract_versions__246 RENAME TO goal_contract_versions;

CREATE INDEX idx_gcv_goal ON goal_contract_versions(goal_id);
CREATE INDEX idx_gcv_support ON goal_contract_versions(goal_id, support_hash);

PRAGMA foreign_keys = ON;
