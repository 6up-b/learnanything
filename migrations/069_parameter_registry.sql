-- P0.5 calibration discipline (spec_p0_measurement_correctness §6):
-- per-vault effective state of the code-authored parameter registry, the frozen
-- per-algorithm-version manifests replay reads, the sim-sweep sensitivity
-- certificates required for `active` lifecycle, and the bind-event logs mandated
-- for `dormant` constraint parameters. Definitions live in code
-- (services/parameter_registry.py); this file stores only the time-varying,
-- per-vault projection + immutable evidence/manifest rows. Additive. No FK to
-- vault-owned ids (repo convention); references are stored as plain ids.

-- (b) Per-vault effective-state projection. Rewritten by registry_service.refresh;
-- a projection, never raw history -> safe to UPSERT (like goal_contract_heads).
CREATE TABLE IF NOT EXISTS parameter_registry (
  path TEXT PRIMARY KEY,               -- stable key, matches the code REGISTRY
  kind TEXT NOT NULL CHECK (kind IN ('decision','structural')),
  param_class TEXT NOT NULL,
  effective_value_json TEXT NOT NULL,  -- resolved value (scalar/tuple/map)
  effective_value_hash TEXT NOT NULL,  -- _canonical_hash of the value
  source TEXT NOT NULL CHECK (source IN
    ('default','vault_override','fitted','model_artifact')),
  status TEXT NOT NULL CHECK (status IN
    ('heuristic','simulation_validated','live_calibrated')),
  lifecycle TEXT NOT NULL CHECK (lifecycle IN ('active','dormant','deleted')),
  rationale TEXT NOT NULL,
  scope TEXT NOT NULL,
  owner TEXT NOT NULL,
  -- evidence refs (§6, U-022 v2 -- two-artifact split):
  --  * sensitivity_certificate_id: the COVERAGE certificate (descriptive) required
  --    for EVERY active decision parameter; documents where in the swept range
  --    decisions flip. Finding flip points does NOT invalidate it.
  --  * promotion_evidence_id: the sim-derived PROMOTION EVIDENCE (normative) that
  --    gates status heuristic -> simulation_validated (carries the decision_stable
  --    refusal). Both ids reference parameter_sensitivity_certificates rows.
  --  * evidence_manifest_id: activated real-outcome manifest gating -> live_calibrated.
  --  * redundancy_proof_id: redundancy proof gating -> deleted.
  -- Stored as ids, not blobs.
  sensitivity_certificate_id TEXT,
  promotion_evidence_id TEXT,
  evidence_manifest_id TEXT,
  redundancy_proof_id TEXT,
  last_review_at TEXT,
  updated_at TEXT NOT NULL
);

-- (c) Immutable frozen manifest per algorithm version (replay reproducibility).
CREATE TABLE IF NOT EXISTS parameter_registry_manifests (
  id TEXT PRIMARY KEY,
  algorithm_version TEXT NOT NULL,     -- 'mvp-0.6','mvp-0.7','mvp-0.8'
  manifest_hash TEXT NOT NULL,         -- _canonical_hash over entries_json
  entries_json TEXT NOT NULL,          -- {path:{value_hash,status,lifecycle,source}}
  frozen_at TEXT NOT NULL,
  UNIQUE(algorithm_version)            -- one frozen manifest per version
);

-- Sim-sweep artifacts (§3): each row shows where in the plausible range a decision
-- flips. Stores BOTH roles (distinguished by which registry column references them):
-- COVERAGE certificates (required for every active decision param; flip points are
-- informational) and PROMOTION EVIDENCE (decision_stable=1 gates promotion). Immutable.
CREATE TABLE IF NOT EXISTS parameter_sensitivity_certificates (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  covered_value_hash TEXT NOT NULL,    -- the effective value this cert certifies
  plausible_range_json TEXT NOT NULL,  -- {low, high} swept
  flip_points_json TEXT NOT NULL,      -- values at which a decision flipped
  decision_stable INTEGER NOT NULL CHECK (decision_stable IN (0,1)),
  scenario_json TEXT NOT NULL,         -- {profile, seed, days, vault_fixture}
  sim_report_hash TEXT NOT NULL,       -- SweepReport content hash (repro)
  produced_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_psc_path ON parameter_sensitivity_certificates(path);

-- Bind-event log for dormant constraint parameters (§4/§6). "An unmonitored
-- guardrail is dead code." Append-only.
CREATE TABLE IF NOT EXISTS parameter_bind_events (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  bound_context_json TEXT NOT NULL,    -- where/when the guardrail actually fired
  observation_ref TEXT,                -- administration/observation/decision id
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pbe_path ON parameter_bind_events(path);
