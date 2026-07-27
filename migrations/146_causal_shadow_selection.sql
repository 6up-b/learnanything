-- Shadow selection receipts for the causal diagnostic lane
-- (decision_value_and_commissioning_spec_v1.md §6.6/§10.1; EVSI-2).
--
-- One append-only row per LIVE probe decision receipt, recording what the
-- formal selector WOULD have said alongside the P2 incumbent: the five §6.6
-- baselines (incumbent / formal EVSI / equal-cost modal-route / EVPI skip
-- bound / no-measure), each with typed availability, plus the would_change_*
-- flags the promotion gates (§9.2) are denominated in.
--
-- Shadow has ZERO live authority (§3 invariant 2): nothing reads this table on
-- a serving path; the orchestrator writes it in its own try/except so a shadow
-- failure can never break the attempt path. The scalar columns exist for the
-- readiness report's aggregations; `body_json` carries the full computation
-- (prior + conditional scope, loss table + duration provenance, rank result,
-- per-arm details) so a promotion review can replay any row without re-deriving.

CREATE TABLE causal_shadow_selection_receipts (
  id TEXT PRIMARY KEY,

  -- Exactly one shadow per live decision receipt: the live receipt is the
  -- decision's identity, and re-running the same decision writes a new live
  -- receipt (they are deliberately never deduplicated) with its own shadow.
  decision_receipt_id TEXT NOT NULL UNIQUE,

  factor_id TEXT NOT NULL,
  learning_object_id TEXT,
  attempt_id TEXT,
  candidate_id TEXT,

  -- The live P2 verdict this shadow rode along with.
  incumbent_decision TEXT NOT NULL,
  incumbent_reason TEXT NOT NULL,

  -- 'measure' | 'stop' | 'abstain' from the formal selector, or 'unavailable'
  -- when its inputs did not exist (the honest early state).
  shadow_verdict TEXT NOT NULL CHECK (shadow_verdict IN (
    'measure', 'stop', 'abstain', 'unavailable'
  )),

  -- §6.2 arms. 'arm_a_calibrated' is reserved (no calibrated channel exists
  -- yet); 'arm_b_noiseless_partition' is the declared-emission upper bound;
  -- 'arm_c_structural' may license skips only; 'none' = no instrument.
  likelihood_regime TEXT NOT NULL CHECK (likelihood_regime IN (
    'arm_a_calibrated', 'arm_b_noiseless_partition', 'arm_c_structural', 'none'
  )),
  loss_table_regime TEXT NOT NULL,
  prior_basis TEXT,

  -- NULL = not evaluable (an arm was unavailable), never a silent 0.
  would_change_candidate INTEGER CHECK (
    would_change_candidate IS NULL OR would_change_candidate IN (0, 1)
  ),
  would_change_measure_vs_repair INTEGER CHECK (
    would_change_measure_vs_repair IS NULL
    OR would_change_measure_vs_repair IN (0, 1)
  ),
  would_change_repair INTEGER CHECK (
    would_change_repair IS NULL OR would_change_repair IN (0, 1)
  ),

  baselines_json TEXT NOT NULL,
  body_json TEXT NOT NULL,
  shadow_policy_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX idx_causal_shadow_selection_factor
  ON causal_shadow_selection_receipts(factor_id, created_at, id);
CREATE INDEX idx_causal_shadow_selection_regime
  ON causal_shadow_selection_receipts(likelihood_regime, created_at, id);

CREATE TRIGGER causal_shadow_selection_receipts_no_update
BEFORE UPDATE ON causal_shadow_selection_receipts
BEGIN
  SELECT RAISE(ABORT, 'shadow selection receipts are append-only');
END;

CREATE TRIGGER causal_shadow_selection_receipts_no_delete
BEFORE DELETE ON causal_shadow_selection_receipts
BEGIN
  SELECT RAISE(ABORT, 'shadow selection receipts are append-only');
END;
