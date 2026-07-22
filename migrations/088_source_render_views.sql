-- P3 slice 1, step 1 (spec_p3_reader_integration §3.1-3.3, design B step 1).
-- Immutable marker render views + the display<->source-block crosswalk.
--
-- A render view is a REPLACEABLE display layer (marker markdown / KaTeX) over the
-- immutable source bytes and the versioned extraction IR. Re-rendering marker
-- markdown NEVER rewrites annotations, source objects, commitments, or evidence
-- (invariant 1.1.4): a new render bumps only render/crosswalk versions. Views are
-- created LAZILY, one per actively opened extraction (§13.1.1), and are idempotent
-- on `request_hash` -- repeating a render for the same contract reuses the view.
--
-- Display offsets on the crosswalk are highlight-only and disposable (§3.2): a
-- selection is translated THROUGH the crosswalk into source-block anchor segments
-- (code-point offsets against source-block text) before anything is persisted.

CREATE TABLE source_render_views (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES source_artifacts(id),
  revision_id TEXT NOT NULL REFERENCES source_revisions(id),
  extraction_id TEXT NOT NULL REFERENCES source_extraction_runs(id),
  renderer TEXT NOT NULL DEFAULT 'marker_markdown',
  renderer_version TEXT NOT NULL,
  model_version TEXT,
  config_version TEXT,
  schema_version TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  asset_manifest_hash TEXT,
  status TEXT NOT NULL DEFAULT 'ready'
    CHECK (status IN ('pending', 'ready', 'failed', 'superseded')),
  health_summary_json TEXT NOT NULL DEFAULT '{}',
  predecessor_view_id TEXT REFERENCES source_render_views(id),
  predecessor_reason TEXT,
  output_ref TEXT,
  request_hash TEXT NOT NULL,
  result_hash TEXT,
  created_at TEXT NOT NULL,
  completed_at TEXT,
  UNIQUE(request_hash)
);
CREATE INDEX idx_source_render_views_extraction ON source_render_views(extraction_id);
CREATE INDEX idx_source_render_views_revision ON source_render_views(revision_id);

CREATE TABLE source_render_block_crosswalk (
  id TEXT PRIMARY KEY,
  render_view_id TEXT NOT NULL REFERENCES source_render_views(id),
  display_node_id TEXT NOT NULL,
  display_ordinal INTEGER NOT NULL,
  extraction_id TEXT NOT NULL,
  span_id TEXT,
  block_content_hash TEXT,
  block_ordinal INTEGER,
  display_start INTEGER,
  display_end INTEGER,
  katex_node_ids_json TEXT NOT NULL DEFAULT '[]',
  asset_ids_json TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'mapped'
    CHECK (status IN ('mapped', 'unmapped', 'ambiguous')),
  reason TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_render_crosswalk_view ON source_render_block_crosswalk(render_view_id, display_ordinal);
CREATE INDEX idx_render_crosswalk_span ON source_render_block_crosswalk(render_view_id, span_id);
