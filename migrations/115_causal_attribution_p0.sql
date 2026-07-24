-- Causal-attribution P0: distinguish a depth-trajectory shift from a
-- direction-preserving easier/harder sibling request. Existing rows retain
-- their historical direction; new requests always stamp variant_kind.
ALTER TABLE rung_variant_requests ADD COLUMN variant_kind TEXT
  CHECK (variant_kind IS NULL OR variant_kind IN ('easier', 'harder', 'rung_shift'));

-- A confidence-only first-error trace never had causal promotion authority.
-- Keep the rows for audit/replay, but remove them from the active durable
-- projection and mark the originating candidate as demoted. `resolved` here is
-- only the legacy table's inactive storage state (its CHECK predates demotion);
-- migration 116 records the authoritative semantic disposition as `demoted`,
-- explicitly distinguishing this cleanup from learner resolution.
UPDATE misconceptions
   SET status = 'resolved',
       promotion_reason = 'demoted_first_error_trace',
       resolved_at = COALESCE(resolved_at, updated_at, created_at)
 WHERE promotion_reason = 'first_error_trace'
   AND status IN ('active', 'resolving');

UPDATE misconception_candidates
   SET status = 'demoted',
       promotion_reason = 'demoted_first_error_trace'
 WHERE promotion_reason = 'first_error_trace';

-- Immutable learner self-report channel for the one-tap unresolved-cause
-- question. Kept separate from interaction_events because that legacy table
-- has a closed kind CHECK.
CREATE TABLE causal_attribution_reports (
  id TEXT PRIMARY KEY,
  factor_id TEXT NOT NULL REFERENCES unresolved_cause_factors(id),
  attempt_id TEXT NOT NULL,
  response TEXT NOT NULL,
  candidate_index INTEGER,
  payload_json TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_causal_attribution_reports_factor
  ON causal_attribution_reports(factor_id, created_at);
