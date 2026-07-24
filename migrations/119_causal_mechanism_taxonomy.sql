-- Causal-attribution P1 (§6.4): mechanism taxonomies are explicit,
-- content-addressed batch artifacts.  They do not rewrite hypothesis history
-- and are never minted from the attempt-materialization hot path.
CREATE TABLE causal_mechanism_taxonomy_versions (
  id TEXT PRIMARY KEY,
  algorithm TEXT NOT NULL,
  min_cluster_size INTEGER NOT NULL CHECK (min_cluster_size >= 2),
  source_head_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('draft', 'active')),
  taxonomy_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX idx_causal_mechanism_taxonomy_status
  ON causal_mechanism_taxonomy_versions(status, created_at, id);

CREATE TABLE causal_mechanism_taxonomy_assignments (
  taxonomy_version_id TEXT NOT NULL
    REFERENCES causal_mechanism_taxonomy_versions(id),
  hypothesis_id TEXT NOT NULL REFERENCES causal_hypotheses(id),
  mechanism_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (taxonomy_version_id, hypothesis_id)
);

CREATE INDEX idx_causal_mechanism_assignment_hypothesis
  ON causal_mechanism_taxonomy_assignments(hypothesis_id, taxonomy_version_id);

CREATE TRIGGER causal_mechanism_taxonomy_versions_no_update
BEFORE UPDATE ON causal_mechanism_taxonomy_versions
BEGIN
  SELECT RAISE(ABORT, 'causal mechanism taxonomy versions are append-only');
END;

CREATE TRIGGER causal_mechanism_taxonomy_versions_no_delete
BEFORE DELETE ON causal_mechanism_taxonomy_versions
BEGIN
  SELECT RAISE(ABORT, 'causal mechanism taxonomy versions are append-only');
END;

CREATE TRIGGER causal_mechanism_taxonomy_assignments_no_update
BEFORE UPDATE ON causal_mechanism_taxonomy_assignments
BEGIN
  SELECT RAISE(ABORT, 'causal mechanism taxonomy assignments are append-only');
END;

CREATE TRIGGER causal_mechanism_taxonomy_assignments_no_delete
BEFORE DELETE ON causal_mechanism_taxonomy_assignments
BEGIN
  SELECT RAISE(ABORT, 'causal mechanism taxonomy assignments are append-only');
END;
