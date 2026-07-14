-- Source layer v2 (spec_source_ingestion_v2 §2.3/§2.4): immutable source
-- identity (work -> artifact -> revision -> extraction run) plus the Document IR
-- and cross-run span re-anchoring. Schemas follow the spec verbatim with house
-- NOT NULL / REFERENCES added. Legacy subject-scoped notes remain readable in
-- place and are indexed into these rows without moving files (§13).

CREATE TABLE source_artifacts (
  id TEXT PRIMARY KEY,
  acquisition_kind TEXT NOT NULL,
  canonical_uri TEXT,
  work_id TEXT,
  current_revision_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX idx_source_artifacts_uri ON source_artifacts(canonical_uri);

CREATE TABLE source_revisions (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES source_artifacts(id),
  asset_hash TEXT NOT NULL,
  note_id TEXT,
  original_uri TEXT,
  retrieved_at TEXT,
  supersedes_revision_id TEXT REFERENCES source_revisions(id),
  created_at TEXT NOT NULL,
  UNIQUE(source_id, asset_hash)
);

CREATE INDEX idx_source_revisions_source ON source_revisions(source_id);
CREATE INDEX idx_source_revisions_asset ON source_revisions(asset_hash);

CREATE TABLE source_extraction_runs (
  id TEXT PRIMARY KEY,
  revision_id TEXT NOT NULL REFERENCES source_revisions(id),
  parent_extraction_id TEXT REFERENCES source_extraction_runs(id),
  extractor TEXT NOT NULL,
  extractor_version TEXT NOT NULL,
  model_versions_json TEXT,
  config_json TEXT,
  page_selection_json TEXT,
  ir_schema_version TEXT NOT NULL,
  extraction_request_hash TEXT NOT NULL,
  extraction_result_hash TEXT,   -- NULL until the run completes
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  completed_at TEXT,
  UNIQUE(revision_id, extraction_request_hash)
);

CREATE INDEX idx_source_extraction_runs_revision ON source_extraction_runs(revision_id);

CREATE TABLE source_document_units (
  extraction_id TEXT NOT NULL REFERENCES source_extraction_runs(id),
  unit_id TEXT NOT NULL,
  parent_unit_id TEXT,
  label TEXT NOT NULL,
  ordinal INTEGER NOT NULL,
  locator_json TEXT,
  semantic_hash TEXT NOT NULL,
  page_start INTEGER,
  page_end INTEGER,
  span_ids_json TEXT,
  PRIMARY KEY(extraction_id, unit_id)
);

CREATE INDEX idx_source_document_units_semantic ON source_document_units(semantic_hash);

CREATE TABLE source_document_blocks (
  extraction_id TEXT NOT NULL REFERENCES source_extraction_runs(id),
  span_id TEXT NOT NULL,
  extractor_block_id TEXT,
  block_type TEXT NOT NULL,
  role_hint TEXT,
  page INTEGER,
  bbox_json TEXT,
  polygon_json TEXT,
  section_path_json TEXT,
  text TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  asset_ids_json TEXT,
  ordinal INTEGER NOT NULL,
  PRIMARY KEY(extraction_id, span_id)
);

CREATE INDEX idx_source_document_blocks_hash ON source_document_blocks(extraction_id, content_hash);

CREATE TABLE source_document_assets (
  id TEXT NOT NULL,
  extraction_id TEXT NOT NULL REFERENCES source_extraction_runs(id),
  media_type TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  path TEXT,
  caption TEXT,
  page INTEGER,
  geometry_json TEXT,
  neighboring_span_ids_json TEXT,
  PRIMARY KEY(extraction_id, id)
);

CREATE TABLE source_span_reanchors (
  from_extraction_id TEXT NOT NULL REFERENCES source_extraction_runs(id),
  from_span_id TEXT NOT NULL,
  to_extraction_id TEXT NOT NULL REFERENCES source_extraction_runs(id),
  to_span_id TEXT NOT NULL,
  match_kind TEXT NOT NULL CHECK (match_kind IN ('exact_hash', 'geometry_section', 'manual')),
  confidence REAL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(from_extraction_id, from_span_id, to_extraction_id)
);

-- Locator-scheme backfill (§2.4): shape-detected schemes stamped onto existing
-- provenance refs without rewriting user files. Scheme is declared per ref and
-- never silently converted.
CREATE TABLE source_locator_schemes (
  locator TEXT PRIMARY KEY,
  scheme TEXT NOT NULL,
  detected_at TEXT NOT NULL
);
