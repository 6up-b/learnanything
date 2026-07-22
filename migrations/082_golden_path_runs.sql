-- P2 step 2-3 (spec_p2_narrow_golden_path §4.1, §4.2, §4.3, §12.6): the durable
-- golden-path run + its append-only transition event log. Current state is a
-- PROJECTION of events (§4.1); the `current_state` column on the run is a cache
-- rebuildable from `golden_path_run_events`, never the authority.
--
-- Migration numbering: follows 081_task_blueprints (this P2 pair). Never edit an
-- applied migration.
--
-- The run is its OWN event-sourced state machine (design A.3.1) -- it does NOT
-- extend the ingest/synthesis durable-batch queue. Every transition is
-- append-only and carries a client idempotency key + an expected-head fence so a
-- crash/retry reopens the same committed transition and never chooses a second
-- item or repeats a side effect (invariant 11 / §4.3 / §12.6).

-- Stable run. Pins per §4.1. The atomic confirmation (golden_path_confirm) writes
-- this row LAST, inside the SAME transaction as goal-contract v1 + commitment +
-- assessment reserve: if any part fails, none becomes active (§3.1). `receipt_key`
-- makes the whole confirmation idempotent -- a byte-identical re-confirm returns
-- the existing run rather than minting a second.
CREATE TABLE golden_path_runs (
  id TEXT PRIMARY KEY,
  receipt_key TEXT NOT NULL,
  learner_id TEXT NOT NULL DEFAULT 'local',
  goal_id TEXT NOT NULL,
  commitment_id TEXT NOT NULL REFERENCES commitments(id),
  commitment_version_id TEXT NOT NULL REFERENCES commitment_versions(id),
  source_rev TEXT NOT NULL,
  unit_id TEXT NOT NULL,
  blueprint_version_id TEXT NOT NULL REFERENCES task_blueprint_versions(id),
  goal_contract_version_id TEXT NOT NULL REFERENCES goal_contract_versions(id),
  depth_policy_version_id TEXT REFERENCES depth_policy_versions(id),
  depth_envelope_version_id TEXT REFERENCES depth_envelope_versions(id),
  initial_milestone TEXT NOT NULL,
  -- Reserved fresh held-out assessment (§8.1). Bare TEXT: reservation/surface rows
  -- live in the P0 activity substrate; the pin is the confirmed contract support.
  reserved_reservation_id TEXT,
  reserved_surface_id TEXT,
  reserved_support_hash TEXT,
  -- `certifying` requires entry-gate items 7-8 at confirmation; otherwise the run
  -- is minted `practice_only` and makes no terminal claim (§1.1, A.3.4).
  mode TEXT NOT NULL DEFAULT 'certifying'
    CHECK (mode IN ('certifying', 'practice_only')),
  orchestration_policy_json TEXT,
  decision_param_manifest_json TEXT,
  visible_caps_json TEXT,
  -- Denormalized cache of the projected head state; rebuildable from events.
  current_state TEXT NOT NULL DEFAULT 'draft'
    CHECK (current_state IN (
      'draft', 'ready', 'measuring', 'triaging', 'instructing', 'completing',
      'practicing', 'integrating', 'awaiting_delayed_check', 'ready_to_assess',
      'assessing', 'restoring', 'deepening', 'maintaining', 'complete', 'paused',
      'practice_only', 'needs_review', 'abandoned')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(receipt_key)
);
CREATE INDEX idx_gpr_commitment ON golden_path_runs(commitment_id);
CREATE INDEX idx_gpr_goal ON golden_path_runs(goal_id);
CREATE INDEX idx_gpr_state ON golden_path_runs(current_state);

-- Append-only transition log. Each row records the §4.1 transition fields. The
-- head is the newest row by (created_at, id); `expected_head_event_id` is the
-- optimistic fence a caller must match to append (§4.3). `idempotency_key` is
-- UNIQUE per run so a retried transition collapses to exactly one event
-- (§12.6). `seq` is a monotone per-run ordinal for a stable, gap-checkable chain.
CREATE TABLE golden_path_run_events (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES golden_path_runs(id) ON DELETE CASCADE,
  seq INTEGER NOT NULL,
  from_state TEXT,
  to_state TEXT NOT NULL,
  reason TEXT NOT NULL,
  feasible_alternatives_json TEXT,
  evidence_ids_json TEXT,
  -- P0.4 semantics: every transition logs the goal-contract HEAD version it
  -- evaluated (§4.1, invariant 3 "progression reads/logs the current head").
  goal_contract_head_version_id TEXT,
  depth_policy_version_id TEXT,
  depth_envelope_version_id TEXT,
  predecessor_milestone TEXT,
  successor_milestone TEXT,
  selected_activity_json TEXT,
  policy_calibration_json TEXT,
  burden_json TEXT,
  expected_head_event_id TEXT,
  idempotency_key TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(run_id, seq),
  UNIQUE(run_id, idempotency_key)
);
CREATE INDEX idx_gpre_run ON golden_path_run_events(run_id, seq);
