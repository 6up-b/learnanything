-- P1 step 2 (spec_p1_shared_substrate §3.3, §3.4, §3.5): the closed capability
-- vocabulary alias registry, the immutable TaskFeature schema, and the curated
-- ActivityPattern registry with U-035 `learning_process` routing metadata.
--
-- `learning_process` is closed-vocabulary controller-side routing metadata: it is
-- surfaced in the "why this activity?" DTO but is categorically excluded from any
-- evidence/projection input path (§3.5, U-035). It lives ONLY on the pattern
-- version row; no projection selects it (enforced by test).

CREATE TABLE capability_aliases (
  id TEXT PRIMARY KEY,
  registry_version INTEGER NOT NULL,
  legacy_value TEXT NOT NULL,
  -- NULL canonical => legacy_unmapped: fails NEW authoring, visible in replay only.
  canonical TEXT CHECK (canonical IS NULL OR canonical IN (
    'retrieval', 'schema_interpretation', 'procedure_execution',
    'method_selection', 'coordination')),
  created_at TEXT NOT NULL,
  UNIQUE(registry_version, legacy_value)
);

CREATE TABLE task_feature_schema_versions (
  id TEXT PRIMARY KEY,
  schema_slug TEXT NOT NULL,
  version INTEGER NOT NULL,
  -- complexity / transfer / representation / response / scaffolding / time / tools / span (§3.4).
  dimensions_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(schema_slug, version)
);

CREATE TABLE activity_patterns (
  id TEXT PRIMARY KEY,
  pattern_slug TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL
);

CREATE TABLE activity_pattern_versions (
  id TEXT PRIMARY KEY,
  pattern_id TEXT NOT NULL REFERENCES activity_patterns(id) ON DELETE CASCADE,
  version INTEGER NOT NULL,
  allowed_purposes_json TEXT NOT NULL,   -- subset of diagnostic/instructional/practice/assessment
  operation TEXT NOT NULL CHECK (operation IN (
    'retrieve', 'discriminate', 'generate', 'compare', 'explain',
    'set_up', 'apply', 'reflect', 'create')),
  -- U-035 induced learning process: closed vocabulary, ROUTING-ONLY.
  learning_process TEXT NOT NULL CHECK (learning_process IN (
    'prior_knowledge_activation', 'comprehension_monitoring', 'self_explanation',
    'schema_induction', 'procedure_compilation', 'memory_fluency', 'method_selection',
    'coordination', 'transfer', 'reflection')),
  allowed_target_kinds_json TEXT NOT NULL,
  allowed_capabilities_json TEXT NOT NULL,
  completion_semantics_json TEXT NOT NULL,
  response_contract_json TEXT NOT NULL,
  progression_role TEXT,
  prerequisite_evidence_json TEXT,
  feedback_strategy_json TEXT,
  assistance_strategy_json TEXT,
  evidence_semantics_by_context_json TEXT NOT NULL,
  task_feature_bounds_json TEXT NOT NULL,
  variation_axes_json TEXT NOT NULL,
  rubric_shape_json TEXT NOT NULL,
  mint_gates_json TEXT NOT NULL,
  burden_model_json TEXT,
  calibration_status TEXT NOT NULL CHECK (calibration_status IN (
    'heuristic', 'simulation_validated', 'live_calibrated')),
  generator_version TEXT,
  content_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('draft', 'reviewed', 'active', 'retired')),
  created_at TEXT NOT NULL,
  UNIQUE(pattern_id, version),
  UNIQUE(pattern_id, content_hash)
);
CREATE INDEX idx_apv_pattern_status ON activity_pattern_versions(pattern_id, status);
