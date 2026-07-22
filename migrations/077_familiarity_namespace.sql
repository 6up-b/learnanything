-- P1 step 6 (spec_p1_shared_substrate §4.1, §4.2, §3.9): one namespaced
-- familiarity ledger. P0's activity_exposure_events (migration 065) stays THE
-- authoritative exact-exposure ledger; P1 adds, ALONGSIDE it, normalized
-- fingerprint-group memberships + a separate soft-kinship feature vector +
-- surface authoring. familiarity_projection_v1 reads exposure UNION memberships.
--
-- Standing rule 5 / §4.1: namespaces are NEVER interchangeable -- a value `svd-1`
-- in source_example cannot collide with `svd-1` in solution_recipe. A surface may
-- belong to MANY groups; selecting the first non-empty field is forbidden (this
-- replaces the legacy canonical_projection first-field bug). Salience signals are
-- never learner evidence: warmth discounts/withholds evidence, it never mints it.

CREATE TABLE surface_fingerprint_memberships (
  id TEXT PRIMARY KEY,
  surface_id TEXT NOT NULL REFERENCES activity_surfaces(id) ON DELETE CASCADE,
  namespace TEXT NOT NULL CHECK (namespace IN (
    'surface_hash', 'shared_stimulus', 'source_example', 'solution_recipe',
    'parameter_template', 'verbatim_target', 'external_artifact')),
  value_hash TEXT NOT NULL,
  provenance TEXT,
  -- status: 'known' | 'unknown' (§4.1: missing/unverifiable fingerprint -> unknown,
  -- never silently 'novel'). Left free-text so a degraded tutor-exposure can mark it.
  status TEXT,
  confidence REAL,
  created_at TEXT NOT NULL,
  -- One membership per (surface, namespace, value): a surface joins a group once.
  UNIQUE(surface_id, namespace, value_hash)
);
CREATE INDEX idx_sfm_ns_value ON surface_fingerprint_memberships(namespace, value_hash);
CREATE INDEX idx_sfm_surface ON surface_fingerprint_memberships(surface_id);

CREATE TABLE soft_kinship_features (
  id TEXT PRIMARY KEY,
  surface_id TEXT NOT NULL REFERENCES activity_surfaces(id) ON DELETE CASCADE,
  feature_schema_version TEXT NOT NULL,
  -- §4.2 feature vector: NEVER a pre-collapsed group id. Target/facet overlap,
  -- source/shared-stimulus proximity, recipe overlap, representation/answer match,
  -- parameter/template relationship, semantic similarity, angle distance, recency,
  -- exposure count, feedback reveal.
  features_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(surface_id, feature_schema_version)
);

CREATE TABLE activity_surface_authoring (
  surface_id TEXT PRIMARY KEY REFERENCES activity_surfaces(id) ON DELETE CASCADE,
  surface_policy TEXT CHECK (surface_policy IS NULL OR surface_policy IN ('fixed', 'rotating')),
  generator_provenance_json TEXT,
  anchor_surface_id TEXT REFERENCES activity_surfaces(id),
  candidate_batch_id TEXT,
  seed TEXT,
  angle_coords_json TEXT,
  task_features_json TEXT,
  gate_decision_json TEXT,
  reviewer TEXT,
  status TEXT,
  -- A learner-authored surface is PINNED: it stays exactly as written until
  -- edited/retired (§3.9); sibling cards may provide transfer checks.
  pinned_by_learner INTEGER NOT NULL DEFAULT 0 CHECK (pinned_by_learner IN (0, 1)),
  authorship_provenance_json TEXT,
  rotation_eligible INTEGER NOT NULL DEFAULT 0 CHECK (rotation_eligible IN (0, 1)),
  cache_state TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_asa_anchor ON activity_surface_authoring(anchor_surface_id);
