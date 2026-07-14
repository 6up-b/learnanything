-- ING M5 (source-ingestion §8.4, §9.1, §10.2): the provenance, manifest, and
-- crash-safe apply foundation that must exist before an LLM builds curriculum at
-- scale. Schemas follow the spec verbatim with house NOT NULL / DEFAULT / CHECK
-- added; the spec's `status CHECK(a|b)` shorthand is written as `IN (...)`.
--
-- Migration numbers 041-043 are reserved for the parallel ING M4 worktree; M5
-- owns 044+.

-- §9.1 Entity-source links: authoritative aggregate multi-source provenance.
-- YAML provenance.source_refs remains a compatible embedded snapshot. Rows are
-- written by apply_accepted_items for created content and by accepted
-- provenance_link items during append (M7). source_id/revision_id/extraction_id
-- are identifiers, not FKs (a cited revision may be legacy or externally mirrored).
CREATE TABLE entity_source_links (
  id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  source_id TEXT,
  revision_id TEXT,
  locator TEXT NOT NULL,
  locator_scheme TEXT,
  relation TEXT NOT NULL CHECK (
    relation IN ('primary', 'support', 'alternate', 'exercise', 'assessment_alignment')
  ),
  extraction_id TEXT,
  asset_hash TEXT,
  span_hash TEXT,
  patch_id TEXT,
  status TEXT NOT NULL DEFAULT 'current' CHECK (
    status IN ('current', 'stale', 'removed', 'needs_reanchor')
  ),
  stale_at TEXT,
  superseded_by_link_id TEXT REFERENCES entity_source_links(id),
  created_at TEXT NOT NULL,
  UNIQUE (entity_type, entity_id, revision_id, locator, relation)
);

CREATE INDEX idx_entity_source_links_entity
  ON entity_source_links(entity_type, entity_id);
CREATE INDEX idx_entity_source_links_revision
  ON entity_source_links(revision_id);
CREATE INDEX idx_entity_source_links_status
  ON entity_source_links(status);

-- §10.2 Notation mappings: contextual notation equivalences (append-only, review).
CREATE TABLE notation_mappings (
  id TEXT PRIMARY KEY,
  subject_id TEXT,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  canonical_notation TEXT NOT NULL,
  alternate_notation TEXT NOT NULL,
  context TEXT,
  source_id TEXT,
  revision_id TEXT,
  locator TEXT,
  patch_id TEXT,
  status TEXT NOT NULL DEFAULT 'active' CHECK (
    status IN ('active', 'superseded', 'rejected')
  ),
  created_at TEXT NOT NULL
);

CREATE INDEX idx_notation_mappings_entity
  ON notation_mappings(entity_type, entity_id);

-- §10.2 Source conflicts: an unresolved two-sided conflict. Accepting persists
-- an open conflict; it never applies either competing definition.
CREATE TABLE source_conflicts (
  id TEXT PRIMARY KEY,
  subject_id TEXT,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  left_source_id TEXT,
  left_revision_id TEXT,
  left_locator TEXT,
  right_source_id TEXT,
  right_revision_id TEXT,
  right_locator TEXT,
  statement TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open' CHECK (
    status IN ('open', 'resolved', 'dismissed')
  ),
  resolution_json TEXT,
  patch_id TEXT,
  created_at TEXT NOT NULL,
  resolved_at TEXT
);

CREATE INDEX idx_source_conflicts_entity
  ON source_conflicts(entity_type, entity_id);
CREATE INDEX idx_source_conflicts_status
  ON source_conflicts(status);

-- §8.4 Immutable synthesis manifests: the complete input manifest persisted
-- BEFORE model execution. manifest_hash IS the agent_runs.input_context_hash
-- cache seam. Includes the §12.4 completeness fields (curriculum/facet/task
-- hashes, assessment schema version, learner-model contract version).
CREATE TABLE synthesis_manifests (
  id TEXT PRIMARY KEY,
  manifest_hash TEXT NOT NULL UNIQUE,
  source_set_id TEXT,
  membership_json TEXT,
  revision_ids_json TEXT,
  asset_hashes_json TEXT,
  extraction_ids_json TEXT,
  unit_inventory_versions_json TEXT,
  scope_json TEXT,
  brief_json TEXT,
  prompt_version TEXT,
  schema_version INTEGER,
  provider TEXT,
  model TEXT,
  extractor_versions_json TEXT,
  curriculum_snapshot_hash TEXT,
  facet_registry_hash TEXT,
  task_graph_hash TEXT,
  assessment_schema_version TEXT,
  learner_model_contract_version TEXT,
  lock_fingerprint TEXT,
  token_budget_json TEXT,
  estimated_usage_json TEXT,
  created_at TEXT NOT NULL
);

-- §8.4 Synthesis runs: mutable run status/outputs over an immutable manifest.
CREATE TABLE synthesis_runs (
  id TEXT PRIMARY KEY,
  manifest_id TEXT NOT NULL REFERENCES synthesis_manifests(id),
  mode TEXT NOT NULL,
  agent_run_id TEXT,
  proposal_id TEXT,
  span_request_json TEXT,
  resolved_span_hashes_json TEXT,
  coverage_decisions_json TEXT,
  actual_usage_json TEXT,
  status TEXT NOT NULL DEFAULT 'created' CHECK (
    status IN ('created', 'running', 'completed', 'failed')
  ),
  created_at TEXT NOT NULL,
  completed_at TEXT
);

CREATE INDEX idx_synthesis_runs_manifest ON synthesis_runs(manifest_id);

-- §10.2 Write-ahead apply intents: the durable record that closes crashes (the
-- vault mutation lock closes races). An accepted dependency closure plus its
-- target file contents/hashes and DB side-effect plan commit to SQLite FIRST;
-- YAML is then staged/fsynced/atomically renamed; the intent is marked applied.
-- Startup/doctor recovery completes or rolls back any intent left mid-flight,
-- and application is idempotent.
CREATE TABLE apply_intents (
  id TEXT PRIMARY KEY,
  proposed_patch_id TEXT NOT NULL,
  item_ids_json TEXT NOT NULL,       -- accepted closure item ids, in apply order
  targets_json TEXT NOT NULL,        -- [{rel_path, pre_hash, post_content, post_hash}]
  db_plan_json TEXT NOT NULL,        -- per-item change batch / content event / links
  status TEXT NOT NULL DEFAULT 'pending' CHECK (
    status IN ('pending', 'applied', 'rolled_back')
  ),
  created_at TEXT NOT NULL,
  applied_at TEXT,
  rolled_back_at TEXT
);

CREATE INDEX idx_apply_intents_status ON apply_intents(status);
