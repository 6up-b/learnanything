-- P3 slice 1, step 3 (spec_p3_reader_integration §4, design B step 3).
-- Greenfield annotation model. Stable identity + append-only versions/anchors/
-- events; deletion is a tombstone disposition event, never a hard delete (§4.1),
-- so historical versions remain for audit, restoration, and any commitment/
-- activity provenance already minted from them (invariant 1.1.11).
--
-- Anchors are SUB-BLOCK: each ordered segment pins block span id + block content
-- hash + Unicode code-point offsets against SOURCE-BLOCK text (never markdown byte
-- offsets, invariant 1.1.3) plus the exact quote and bounded prefix/suffix so an
-- orphaned anchor still shows its quote/context without false attachment (§4.2).
-- A multi-block selection stores multiple segments and is never flattened.
-- The annotation-head projection is rebuildable (max version_ordinal), so no head
-- table is stored -- it is derived, satisfying §15.10 replay.

CREATE TABLE source_annotations (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_source_annotations_source ON source_annotations(source_id);

CREATE TABLE source_annotation_versions (
  id TEXT PRIMARY KEY,
  annotation_id TEXT NOT NULL REFERENCES source_annotations(id),
  version_ordinal INTEGER NOT NULL,
  annotation_type TEXT NOT NULL
    CHECK (annotation_type IN ('highlight', 'question', 'confusion', 'interpretation', 'disposition')),
  learner_text TEXT NOT NULL DEFAULT '',
  what_i_think_is_going_on TEXT,
  privacy_locality TEXT NOT NULL DEFAULT 'local_private',
  authorship TEXT NOT NULL DEFAULT 'learner'
    CHECK (authorship IN ('learner', 'ai', 'expert', 'author')),
  client_idempotency_key TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(annotation_id, version_ordinal)
);
CREATE INDEX idx_source_annotation_versions_ann ON source_annotation_versions(annotation_id, version_ordinal);

CREATE TABLE source_annotation_anchor_versions (
  id TEXT PRIMARY KEY,
  annotation_id TEXT NOT NULL REFERENCES source_annotations(id),
  version_ordinal INTEGER NOT NULL,
  source_id TEXT NOT NULL,
  revision_id TEXT NOT NULL,
  extraction_id TEXT NOT NULL,
  render_view_id TEXT,
  status TEXT NOT NULL
    CHECK (status IN ('exact', 'reanchored', 'needs_reanchor', 'orphaned', 'manually_anchored')),
  algo_version TEXT NOT NULL,
  confidence REAL,
  raw_selection_json TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(annotation_id, version_ordinal)
);
CREATE INDEX idx_source_annotation_anchor_ann ON source_annotation_anchor_versions(annotation_id, version_ordinal);

CREATE TABLE source_annotation_anchor_segments (
  id TEXT PRIMARY KEY,
  anchor_version_id TEXT NOT NULL REFERENCES source_annotation_anchor_versions(id),
  segment_ordinal INTEGER NOT NULL,
  span_id TEXT NOT NULL,
  block_content_hash TEXT NOT NULL,
  codepoint_start INTEGER NOT NULL,
  codepoint_end INTEGER NOT NULL,
  exact_quote TEXT NOT NULL,
  prefix TEXT NOT NULL DEFAULT '',
  suffix TEXT NOT NULL DEFAULT '',
  geometry_json TEXT,
  section_path_json TEXT NOT NULL DEFAULT '[]',
  neighbor_hashes_json TEXT NOT NULL DEFAULT '[]',
  selection_text_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(anchor_version_id, segment_ordinal)
);

CREATE TABLE source_annotation_events (
  id TEXT PRIMARY KEY,
  annotation_id TEXT NOT NULL REFERENCES source_annotations(id),
  event_type TEXT NOT NULL
    CHECK (event_type IN ('create', 'edit', 'reanchor', 'map', 'disposition', 'delete_intent', 'manual_anchor')),
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);
CREATE INDEX idx_annotation_events_annotation ON source_annotation_events(annotation_id, created_at);
