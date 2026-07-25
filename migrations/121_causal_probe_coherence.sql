-- Causal-attribution P2 (§7): immutable blind predictions, shared manipulation
-- audits, a review ladder for generated probes, explicit contamination
-- eligibility, and delayed cold-verification receipts.  These records attach to
-- the P1 causal-hypothesis home by id; they never copy mutable hypothesis prose.

CREATE TABLE causal_blind_prediction_bundles (
  id TEXT PRIMARY KEY,
  hypothesis_id TEXT NOT NULL REFERENCES causal_hypotheses(id),
  hypothesis_version INTEGER NOT NULL CHECK (hypothesis_version >= 1),
  practice_item_id TEXT NOT NULL,
  input_hash TEXT NOT NULL,
  predictions_json TEXT NOT NULL,
  generated_without_observation INTEGER NOT NULL DEFAULT 1
    CHECK (generated_without_observation = 1),
  model_revision TEXT NOT NULL CHECK (length(trim(model_revision)) > 0),
  outcome_schema_version TEXT NOT NULL
    CHECK (length(trim(outcome_schema_version)) > 0),
  generation_agent_run_id TEXT,
  created_at TEXT NOT NULL
  -- No UNIQUE over the blind input.  `id` is the content hash of (hypothesis,
  -- version, item, input_hash, predictions, cohort), so the primary key already
  -- dedupes an identical regeneration exactly.  A UNIQUE over the input alone
  -- instead forbids recording a SECOND, differing sample from the same blind
  -- input -- and INSERT OR IGNORE would drop it silently.  Recording every
  -- sample is the case this append-only substrate exists to support: a probe is
  -- classified against the bundle ids PINNED when it was minted, never against
  -- whichever bundle happens to be newest.
);

CREATE INDEX idx_causal_blind_prediction_item
  ON causal_blind_prediction_bundles(practice_item_id, hypothesis_id, created_at);

CREATE TRIGGER causal_blind_prediction_bundles_no_update
BEFORE UPDATE ON causal_blind_prediction_bundles
BEGIN
  SELECT RAISE(ABORT, 'blind prediction bundles are append-only');
END;

CREATE TRIGGER causal_blind_prediction_bundles_no_delete
BEFORE DELETE ON causal_blind_prediction_bundles
BEGIN
  SELECT RAISE(ABORT, 'blind prediction bundles are append-only');
END;

CREATE TABLE probe_manipulation_audits (
  id TEXT PRIMARY KEY,
  source_kind TEXT NOT NULL CHECK (
    source_kind IN ('causal_probe', 'rung_variant')
  ),
  source_item_id TEXT NOT NULL,
  candidate_item_id TEXT NOT NULL,
  contract_json TEXT NOT NULL,
  structural_diff_json TEXT NOT NULL,
  adversarial_review_json TEXT,
  status TEXT NOT NULL CHECK (
    status IN ('passed', 'rejected', 'pending_adversarial_review')
  ),
  generation_agent_run_id TEXT,
  reviewer_agent_run_id TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX idx_probe_manipulation_audit_candidate
  ON probe_manipulation_audits(candidate_item_id, created_at, id);

CREATE TRIGGER probe_manipulation_audits_no_update
BEFORE UPDATE ON probe_manipulation_audits
BEGIN
  SELECT RAISE(ABORT, 'probe manipulation audits are append-only');
END;

CREATE TRIGGER probe_manipulation_audits_no_delete
BEFORE DELETE ON probe_manipulation_audits
BEGIN
  SELECT RAISE(ABORT, 'probe manipulation audits are append-only');
END;

CREATE TABLE causal_probe_candidates (
  id TEXT PRIMARY KEY,
  factor_id TEXT NOT NULL REFERENCES unresolved_cause_factors(id),
  practice_item_id TEXT NOT NULL,
  hypothesis_set_id TEXT NOT NULL REFERENCES hypothesis_sets(id),
  manipulation_audit_id TEXT NOT NULL REFERENCES probe_manipulation_audits(id),
  measurement_contract_json TEXT NOT NULL,
  blind_bundle_ids_json TEXT NOT NULL,
  discrimination_json TEXT,
  status TEXT NOT NULL CHECK (
    status IN ('candidate', 'registered', 'reviewed', 'active', 'rejected')
  ),
  reviewer TEXT,
  review_reason TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX idx_causal_probe_candidate_factor
  ON causal_probe_candidates(factor_id, status, created_at, id);
CREATE INDEX idx_causal_probe_candidate_item
  ON causal_probe_candidates(practice_item_id, status, created_at, id);

CREATE TABLE causal_probe_candidate_events (
  id TEXT PRIMARY KEY,
  candidate_id TEXT NOT NULL REFERENCES causal_probe_candidates(id),
  seq INTEGER NOT NULL CHECK (seq >= 1),
  from_status TEXT,
  to_status TEXT NOT NULL CHECK (
    to_status IN ('candidate', 'registered', 'reviewed', 'active', 'rejected')
  ),
  actor TEXT,
  reason TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(candidate_id, seq)
);

CREATE INDEX idx_causal_probe_candidate_events
  ON causal_probe_candidate_events(candidate_id, seq);

CREATE TRIGGER causal_probe_candidate_events_no_update
BEFORE UPDATE ON causal_probe_candidate_events
BEGIN
  SELECT RAISE(ABORT, 'causal probe candidate events are append-only');
END;

CREATE TRIGGER causal_probe_candidate_events_no_delete
BEFORE DELETE ON causal_probe_candidate_events
BEGIN
  SELECT RAISE(ABORT, 'causal probe candidate events are append-only');
END;

CREATE TABLE causal_activity_classifications (
  attempt_id TEXT PRIMARY KEY,
  contamination_class TEXT NOT NULL CHECK (
    contamination_class IN (
      'pure_diagnostic',
      'instructional_diagnostic',
      'repair_activity',
      'verification'
    )
  ),
  near_clone INTEGER NOT NULL DEFAULT 0 CHECK (near_clone IN (0, 1)),
  closes_pre_intervention_segment INTEGER NOT NULL DEFAULT 0
    CHECK (closes_pre_intervention_segment IN (0, 1)),
  eligible_for_fsrs INTEGER NOT NULL DEFAULT 0 CHECK (eligible_for_fsrs IN (0, 1)),
  eligible_for_certification INTEGER NOT NULL DEFAULT 0
    CHECK (eligible_for_certification IN (0, 1)),
  detail_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TRIGGER causal_activity_classifications_no_update
BEFORE UPDATE ON causal_activity_classifications
BEGIN
  SELECT RAISE(ABORT, 'causal activity classifications are append-only');
END;

CREATE TRIGGER causal_activity_classifications_no_delete
BEFORE DELETE ON causal_activity_classifications
BEGIN
  SELECT RAISE(ABORT, 'causal activity classifications are append-only');
END;

CREATE TABLE causal_cold_verifications (
  id TEXT PRIMARY KEY,
  source_attempt_id TEXT NOT NULL,
  cold_attempt_id TEXT NOT NULL UNIQUE,
  repair_class_id TEXT NOT NULL,
  hypothesis_ids_json TEXT NOT NULL,
  source_surface_family TEXT NOT NULL,
  cold_surface_family TEXT NOT NULL,
  avoided_affordances_json TEXT NOT NULL,
  success INTEGER NOT NULL CHECK (success IN (0, 1)),
  capability_update_json TEXT NOT NULL,
  diagnosis_support_update_json TEXT NOT NULL,
  repair_effect_support_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK (source_attempt_id != cold_attempt_id),
  CHECK (source_surface_family != cold_surface_family)
);

CREATE INDEX idx_causal_cold_verification_source
  ON causal_cold_verifications(source_attempt_id, created_at, id);

CREATE TRIGGER causal_cold_verifications_no_update
BEFORE UPDATE ON causal_cold_verifications
BEGIN
  SELECT RAISE(ABORT, 'causal cold verifications are append-only');
END;

CREATE TRIGGER causal_cold_verifications_no_delete
BEFORE DELETE ON causal_cold_verifications
BEGIN
  SELECT RAISE(ABORT, 'causal cold verifications are append-only');
END;
