-- Rebuild learner_claims to extend the source CHECK with the rung-variant
-- self-report source (learner-initiated re-runging: "make this easier/harder"
-- writes a scoped self_rating claim). All columns/rows preserved — mirrors the
-- 027 rebuild.
CREATE TABLE learner_claims_new (
  id TEXT PRIMARY KEY,
  claim_type TEXT NOT NULL CHECK (
    claim_type IN ('background_familiarity', 'prior_coursework', 'self_rating')
  ),
  scope_type TEXT NOT NULL CHECK (
    scope_type IN ('concept', 'learning_object', 'subject', 'domain', 'global')
  ),
  scope_id TEXT,
  evidence_family TEXT,
  claimed_level REAL NOT NULL CHECK (claimed_level >= 0.0 AND claimed_level <= 1.0),
  prior_pseudo_count REAL NOT NULL CHECK (prior_pseudo_count >= 0.0),
  source TEXT NOT NULL CHECK (
    source IN (
      'init_wizard', 'manual_cli', 'imported', 'tutor_gap_declaration',
      'rung_variant_request'
    )
  ),
  created_at TEXT NOT NULL
);

INSERT INTO learner_claims_new(
  id, claim_type, scope_type, scope_id, evidence_family, claimed_level,
  prior_pseudo_count, source, created_at
)
SELECT
  id, claim_type, scope_type, scope_id, evidence_family, claimed_level,
  prior_pseudo_count, source, created_at
FROM learner_claims;

DROP TABLE learner_claims;
ALTER TABLE learner_claims_new RENAME TO learner_claims;
