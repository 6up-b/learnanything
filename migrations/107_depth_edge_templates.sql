-- Depth-edge authoring (the P1 curated-edge half, spec v2 §depth / spec_p1 §3.1.1).
-- Owner-curated reusable edge TEMPLATES; LLM-authored concrete edge INSTANCES
-- admitted by deterministic gates and pinned into an immutable envelope version.
-- The instances table is a proposal lifecycle ONLY — authorized edges live
-- exclusively in depth_envelope_versions.reviewed_edges_json; nothing reads
-- authorization from here.

CREATE TABLE depth_edge_templates (
  id TEXT PRIMARY KEY,
  template_slug TEXT NOT NULL UNIQUE,
  domain_scope_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE depth_edge_template_versions (
  id TEXT PRIMARY KEY,
  template_id TEXT NOT NULL REFERENCES depth_edge_templates(id),
  version INTEGER NOT NULL,
  -- Structural pattern: allowed capability transitions, per-dimension max step
  -- deltas, exit-gate kind (closed set), fresh-proof kind, burden params,
  -- eligible activity pattern slugs.
  body_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'reviewed', 'retired')),
  reviewed_by TEXT,
  reviewed_at TEXT,
  created_at TEXT NOT NULL,
  UNIQUE (template_id, version),
  UNIQUE (template_id, content_hash)
);

CREATE TABLE depth_edge_instances (
  id TEXT PRIMARY KEY,
  template_version_id TEXT NOT NULL REFERENCES depth_edge_template_versions(id),
  commitment_id TEXT NOT NULL,
  edge_id TEXT NOT NULL,
  predecessor_milestone TEXT NOT NULL,
  successor_milestone_slug TEXT NOT NULL,
  successor_task_contract_json TEXT NOT NULL,
  entry_evidence_json TEXT,
  exit_evidence_json TEXT,
  fresh_proof_json TEXT,
  expected_burden_json TEXT,
  activity_path_json TEXT,
  status TEXT NOT NULL DEFAULT 'proposed' CHECK (
    status IN ('proposed', 'admitted', 'rejected', 'confirmed', 'pinned')
  ),
  admission_report_json TEXT,
  pinned_envelope_version_id TEXT REFERENCES depth_envelope_versions(id),
  receipt_key TEXT UNIQUE,
  author TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX idx_depth_edge_instances_commitment
  ON depth_edge_instances(commitment_id, status);
