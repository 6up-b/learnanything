-- KM1 (knowledge-model §5.2): immutable assessment-contract snapshots and the
-- observation lineage stamped onto grading evidence. Purely additive: every new
-- grading_evidence column is nullable and unread under legacy algorithm_version,
-- so mvp-0.6 replay reproduces byte-identical derived state.

CREATE TABLE assessment_contract_versions (
  id TEXT PRIMARY KEY,
  practice_item_id TEXT NOT NULL,
  contract_hash TEXT NOT NULL,
  contract_json TEXT NOT NULL,
  schema_version INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(practice_item_id, contract_hash)
);
CREATE INDEX idx_assessment_contract_versions_item
  ON assessment_contract_versions(practice_item_id);

-- Observation lineage on grading evidence. observation_id = (attempt_id,
-- criterion_id, grading_revision); a partial unique index enforces uniqueness
-- while leaving legacy rows (NULL observation_id) untouched.
ALTER TABLE grading_evidence ADD COLUMN assessment_contract_version_id TEXT;
ALTER TABLE grading_evidence ADD COLUMN grading_revision INTEGER;
ALTER TABLE grading_evidence ADD COLUMN observation_id TEXT;
ALTER TABLE grading_evidence ADD COLUMN recipe_id TEXT;
ALTER TABLE grading_evidence ADD COLUMN attribution_json TEXT;
ALTER TABLE grading_evidence ADD COLUMN correlation_group TEXT;

CREATE UNIQUE INDEX idx_grading_evidence_observation_id
  ON grading_evidence(observation_id)
  WHERE observation_id IS NOT NULL;

CREATE TABLE unresolved_cause_factors (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL,
  observation_id TEXT,
  candidate_causes_json TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('open', 'resolved', 'retired')),
  resolution_observation_ids_json TEXT,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_unresolved_cause_factors_attempt
  ON unresolved_cause_factors(attempt_id);
CREATE INDEX idx_unresolved_cause_factors_status
  ON unresolved_cause_factors(status);
