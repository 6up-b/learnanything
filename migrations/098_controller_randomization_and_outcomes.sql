-- P4 step 4 (spec_p4_controller_and_scale §3.2, §9.3, §15 step 4; design B step 4).
-- The single randomization layer (U-024) + delayed outcome bookkeeping:
--   * policy_experiment_assignments -- the ONE place policy experimentation lives.
--     Micro-randomized decisions among reversible near-equivalent feasible candidates
--     + epsilon tie-breaking, with assignment + TRUE PROPENSITY persisted BEFORE
--     selection so off-policy joins stay valid across the whole controller seam.
--     There is no separate crossover machinery.
--   * controller_outcome_windows -- proximal outcomes are defined at the NEXT SPACED
--     COLD REVIEW of the affected cards (never end-of-session: desirable difficulties
--     invert immediate rankings). Burden is co-primary; immediate accuracy is
--     secondary telemetry. An intervention with unmodeled carryover is labelled
--     hypothesis-grade regardless of how much data accumulates.
--
-- No FK to vault-owned ids (commitment/card/surface ids are plain TEXT, per the
-- 069/096 convention). Controller-internal aggregates DO use FKs.

-- One randomization assignment (§9.3). The propensity is the TRUE probability under
-- which this unit was assigned its variant, written before the selection commits so a
-- later IPS/DR off-policy join is valid. `design` records which of the two admissible
-- randomization designs produced it; `grade` carries the hypothesis-grade label an
-- intervention earns when it fits neither reversible-MRT nor commitment-parallel.
CREATE TABLE policy_experiment_assignments (
  id TEXT PRIMARY KEY,
  experiment_id TEXT NOT NULL,
  decision_id TEXT REFERENCES controller_decisions(id),
  -- The experimental unit. At n=1 a durable intervention randomizes the COMMITMENT,
  -- not time; a reversible near-equivalent decision randomizes the decision itself.
  unit_kind TEXT NOT NULL CHECK (unit_kind IN ('decision', 'commitment')),
  unit_id TEXT,
  variant TEXT NOT NULL,
  -- The true assignment probability of `variant` (logged before selection, §9.3).
  propensity REAL NOT NULL CHECK (propensity >= 0.0 AND propensity <= 1.0),
  -- Deterministic draw provenance: seed + drawn value replay the assignment exactly.
  seed TEXT NOT NULL,
  draw REAL,
  -- The declared near-equivalence margin the decision fell within (epsilon tie-break),
  -- NULL for a non-tie MRT/commitment assignment.
  epsilon_margin REAL,
  near_equivalent INTEGER NOT NULL DEFAULT 0 CHECK (near_equivalent IN (0, 1)),
  design TEXT NOT NULL
    CHECK (design IN ('mrt_reversible', 'epsilon_tiebreak', 'commitment_parallel')),
  -- 'experimental' = a valid randomization design; 'hypothesis_grade' = an intervention
  -- with unmodeled carryover that stays hypothesis-grade regardless of accumulated data.
  grade TEXT NOT NULL DEFAULT 'experimental'
    CHECK (grade IN ('experimental', 'hypothesis_grade')),
  candidate_refs_json TEXT NOT NULL DEFAULT '[]',
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);
CREATE INDEX idx_policy_experiment_assignments_experiment
  ON policy_experiment_assignments(experiment_id, created_at);
CREATE INDEX idx_policy_experiment_assignments_unit
  ON policy_experiment_assignments(unit_kind, unit_id);
CREATE INDEX idx_policy_experiment_assignments_decision
  ON policy_experiment_assignments(decision_id);

-- A delayed outcome window (§3.2, §9.3). Opened when a decision commits an
-- administration whose effect must be read at the NEXT SPACED COLD REVIEW of the
-- affected card -- never at end-of-session. `anchor_kind` names the event the window
-- is anchored to; `due_at` is the expected next cold review; `status` moves pending ->
-- resolved (a qualifying cold observation landed) or censored (never resolved).
CREATE TABLE controller_outcome_windows (
  id TEXT PRIMARY KEY,
  decision_id TEXT REFERENCES controller_decisions(id),
  assignment_id TEXT REFERENCES policy_experiment_assignments(id),
  candidate_ref TEXT,
  commitment_id TEXT,
  card_ref TEXT,
  -- The horizon is the next spaced cold review (invariant across the layer, §9.3).
  horizon_kind TEXT NOT NULL DEFAULT 'next_spaced_cold_review'
    CHECK (horizon_kind IN ('next_spaced_cold_review')),
  anchor_kind TEXT NOT NULL,
  anchor_ref TEXT,
  opened_at TEXT NOT NULL,
  due_at TEXT,
  resolved_at TEXT,
  -- Burden is co-primary; immediate accuracy is secondary telemetry only (§9.3).
  outcome_json TEXT,
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'resolved', 'censored')),
  -- An unmodeled-carryover intervention's window is hypothesis-grade (label enforced).
  hypothesis_grade INTEGER NOT NULL DEFAULT 0 CHECK (hypothesis_grade IN (0, 1)),
  created_at TEXT NOT NULL
);
CREATE INDEX idx_controller_outcome_windows_decision
  ON controller_outcome_windows(decision_id);
CREATE INDEX idx_controller_outcome_windows_status
  ON controller_outcome_windows(status, due_at);
CREATE INDEX idx_controller_outcome_windows_card
  ON controller_outcome_windows(card_ref, status);
