-- P4 step 1-2 (spec_p4_controller_and_scale §3, §5, §15 steps 1-2; design B steps 1-2).
-- The staged controller substrate: one immutable, content-hashed ControllerSnapshot
-- per decision (§3.1), a versioned feasible-set constraint engine manifest (§5), the
-- transparent staged decision + its candidate/exclusion trace (§3.3, §4), coherent
-- attention blocks + append-only block events (§4.1), and ZERO-AUTHORITY shadow
-- predictions (§3.2, §7, invariant 3). Every controller decision consumes exactly
-- one snapshot; the snapshot hash + constraint manifest hash + decision-parameter
-- hash are recorded on the decision so the whole choice replays from events (§16.10).
--
-- No FK to vault-owned ids (commitment/learning-object/surface ids are stored as
-- plain TEXT, per the 069 convention). Controller-internal aggregates DO use FKs.

-- The immutable, content-hashed decision-time snapshot (§3.1). Deduped on the hash:
-- identical inputs produce identical bytes and reuse the same row (determinism).
CREATE TABLE controller_snapshots (
  id TEXT PRIMARY KEY,
  snapshot_hash TEXT NOT NULL,
  session_id TEXT,
  -- The canonical snapshot body (state projections, feasible-input material,
  -- registered-parameter + projection versions). Never any cold-answer material.
  body_json TEXT NOT NULL,
  param_manifest_hash TEXT,
  projection_versions_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  UNIQUE(snapshot_hash)
);
CREATE INDEX idx_controller_snapshots_session ON controller_snapshots(session_id, created_at);

-- Versioned, content-hashed constraint-engine manifest (§5). Constraints define the
-- FEASIBLE SET; scores rank only within it (invariant 1). The manifest is the frozen
-- set of active constraint definitions (key + version + parameter bindings), hashed;
-- every decision records the manifest hash it evaluated under.
CREATE TABLE controller_constraint_manifests (
  id TEXT PRIMARY KEY,
  manifest_hash TEXT NOT NULL,
  definitions_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(manifest_hash)
);

-- One staged decision. Points to exactly one snapshot; names the ONE staged rule
-- that fired and the ONE canonical action/subtype; carries the full inspectable
-- trace. `mode` is 'shadow' for all of P4 steps 1-2 (the staged policy logs a
-- recommendation beside the legacy scheduler; live authority is the §14.2 cutover).
-- `receipt_key` gives retry-after-commit idempotency (§3.2, §14.4): a replayed
-- decision returns the standing row, never a different candidate.
CREATE TABLE controller_decisions (
  id TEXT PRIMARY KEY,
  receipt_key TEXT,
  snapshot_id TEXT NOT NULL REFERENCES controller_snapshots(id),
  snapshot_hash TEXT NOT NULL,
  session_id TEXT,
  mode TEXT NOT NULL DEFAULT 'shadow' CHECK (mode IN ('shadow', 'live')),
  commitment_id TEXT,
  staged_rule TEXT NOT NULL,
  action TEXT NOT NULL
    CHECK (action IN (
      'measure_diagnostic', 'instruct', 'practice', 'assess_terminal',
      'maintain', 'expand_model', 'stop'
    )),
  subtype TEXT,
  attention_block_id TEXT REFERENCES attention_blocks(id),
  chosen_candidate_ref TEXT,
  stop_reason TEXT,
  constraint_manifest_hash TEXT,
  decision_params_hash TEXT,
  policy_version TEXT,
  -- The legacy scheduler weighted-sum outputs, recorded for comparison ONLY. Never
  -- authority for the staged choice (design §B4; the demoted `_priority`/
  -- `score_selection_reward`).
  comparator_json TEXT,
  trace_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_controller_decisions_snapshot ON controller_decisions(snapshot_id);
CREATE INDEX idx_controller_decisions_session ON controller_decisions(session_id, created_at);
CREATE INDEX idx_controller_decisions_commitment ON controller_decisions(commitment_id, created_at);
CREATE UNIQUE INDEX idx_controller_decisions_receipt
  ON controller_decisions(receipt_key) WHERE receipt_key IS NOT NULL;

-- Every considered candidate with its feasibility verdict, typed exclusion reasons,
-- within-mode ranking metrics, and selected flag (§3.2). A score can never resurrect
-- an infeasible candidate: `selected` is only ever set on a `feasible=1` row.
CREATE TABLE controller_candidates (
  id TEXT PRIMARY KEY,
  decision_id TEXT NOT NULL REFERENCES controller_decisions(id),
  candidate_ref TEXT NOT NULL,
  learning_object_id TEXT,
  feasible INTEGER NOT NULL DEFAULT 0 CHECK (feasible IN (0, 1)),
  exclusion_reasons_json TEXT NOT NULL DEFAULT '[]',
  within_mode_metrics_json TEXT NOT NULL DEFAULT '{}',
  comparator_score REAL,
  selected INTEGER NOT NULL DEFAULT 0 CHECK (selected IN (0, 1)),
  rank_ordinal INTEGER,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_controller_candidates_decision ON controller_candidates(decision_id);

-- One coherent 5-15 minute attention block (§4.1): commitment neighborhood +
-- canonical action + subtype + budget + exit rules. A short-circuit (continuation /
-- explicit learner choice / served administration) is logged as such.
CREATE TABLE attention_blocks (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  commitment_id TEXT,
  action TEXT NOT NULL,
  subtype TEXT,
  budget_minutes REAL NOT NULL,
  neighborhood_json TEXT NOT NULL DEFAULT '{}',
  exit_rules_json TEXT NOT NULL DEFAULT '[]',
  short_circuit_reason TEXT,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_attention_blocks_session ON attention_blocks(session_id, created_at);

CREATE TABLE attention_block_events (
  id TEXT PRIMARY KEY,
  block_id TEXT NOT NULL REFERENCES attention_blocks(id),
  event_ordinal INTEGER NOT NULL,
  kind TEXT NOT NULL,
  detail_json TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(block_id, event_ordinal)
);
CREATE INDEX idx_attention_block_events_block ON attention_block_events(block_id, event_ordinal);

-- Scorer/kernel output with NO authority (invariant 3, §7). Joins to the exact
-- predecision snapshot hash; a record that cannot join is marked unusable, never
-- allowed to influence a live decision.
CREATE TABLE controller_shadow_predictions (
  id TEXT PRIMARY KEY,
  decision_id TEXT REFERENCES controller_decisions(id),
  snapshot_hash TEXT NOT NULL,
  scorer_kind TEXT NOT NULL,
  model_version TEXT,
  authority TEXT NOT NULL DEFAULT 'none' CHECK (authority IN ('none')),
  prediction_json TEXT NOT NULL,
  usable INTEGER NOT NULL DEFAULT 1 CHECK (usable IN (0, 1)),
  created_at TEXT NOT NULL
);
CREATE INDEX idx_controller_shadow_predictions_decision ON controller_shadow_predictions(decision_id);
CREATE INDEX idx_controller_shadow_predictions_snapshot ON controller_shadow_predictions(snapshot_hash);
