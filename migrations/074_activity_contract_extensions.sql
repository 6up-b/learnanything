-- P1 step 3 (spec_p1_shared_substrate §3.6, §3.7): extend the P0 (migration 065)
-- immutable family/card contracts via side tables keyed by the P0 version id
-- (owner decision A.1 -- never ALTER or rename the immutable P0 version rows; they
-- stay byte-frozen for replay). Adds the immutable progression_policy_versions
-- object (owner decision A.2) that the family construction rule
-- (ActivityFamily = commitment target x ActivityPattern version x progression policy)
-- references as its third factor.

CREATE TABLE progression_policy_versions (
  id TEXT PRIMARY KEY,
  policy_slug TEXT NOT NULL,
  version INTEGER NOT NULL,
  -- angle progression order, prerequisite evidence per pattern role, orthogonal-next
  -- behavior, sibling success-propagation shrinkage, family-stage prior update (§5.4/§5.5).
  body_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(policy_slug, version),
  UNIQUE(content_hash)
);

-- Family-version authoring pins, keyed by the P0 immutable family version id.
-- Additive: the 065 activity_family_versions row is never altered.
CREATE TABLE activity_family_authoring (
  family_version_id TEXT PRIMARY KEY
    REFERENCES activity_family_versions(id) ON DELETE CASCADE,
  commitment_id TEXT REFERENCES commitments(id),
  commitment_target_version_id TEXT REFERENCES commitment_target_versions(id),
  authoring_purpose TEXT NOT NULL CHECK (authoring_purpose IN (
    'diagnostic', 'instructional', 'practice', 'assessment')),
  pattern_version_id TEXT REFERENCES activity_pattern_versions(id),
  progression_policy_version_id TEXT REFERENCES progression_policy_versions(id),
  goal_contract_version_id TEXT,           -- evaluated at authoring, bare TEXT (068-owned)
  depth_policy_version_id TEXT REFERENCES depth_policy_versions(id),
  depth_envelope_version_id TEXT REFERENCES depth_envelope_versions(id),
  served_milestone_edges_json TEXT,
  -- typed cross-purpose links (diagnoses_for/teaches_for/practices_for/assesses_for);
  -- links families, never re-labels a card/surface identity (invariant 2, §3.6).
  cross_purpose_links_json TEXT,
  angle_inventory_json TEXT,
  coverage_targets_json TEXT,
  evidence_cap_policy_id TEXT,
  mint_policy_json TEXT,
  retirement_policy_json TEXT,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'retired')),
  created_at TEXT NOT NULL
);
CREATE INDEX idx_afa_commitment ON activity_family_authoring(commitment_id);

-- Card-version authoring pins, keyed by the P0 immutable card version id.
CREATE TABLE activity_card_authoring (
  card_version_id TEXT PRIMARY KEY
    REFERENCES activity_card_versions(id) ON DELETE CASCADE,
  family_version_id TEXT REFERENCES activity_family_versions(id),
  pattern_version_id TEXT REFERENCES activity_pattern_versions(id),
  task_feature_schema_version_id TEXT REFERENCES task_feature_schema_versions(id),
  task_features_json TEXT,
  capability TEXT CHECK (capability IS NULL OR capability IN (
    'retrieval', 'schema_interpretation', 'procedure_execution',
    'method_selection', 'coordination')),
  outcome_schema_id TEXT,                  -- 066-owned, bare
  outcome_schema_version INTEGER,
  surface_policy TEXT CHECK (surface_policy IS NULL OR surface_policy IN ('fixed', 'rotating')),
  surface_variation_bounds_json TEXT,
  angle_identity_json TEXT,
  generator_version TEXT,
  gate_policy_version TEXT,
  expected_burden_json TEXT,
  calibration_metadata_json TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_aca_family ON activity_card_authoring(family_version_id);
