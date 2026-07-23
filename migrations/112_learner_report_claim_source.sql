-- Rebuild learner_claims to extend the source CHECK with 'learner_report':
-- a too_easy/too_hard card retirement is a learner statement about their own
-- level, so it writes the same LO-scoped self_rating a rung-variant request
-- writes (then re-anchors mastery). Mirrors the 027/109 rebuilds.
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
      'rung_variant_request', 'learner_report'
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
