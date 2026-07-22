-- P3 slice 1, step 2 (spec_p3_reader_integration §3.4, design B step 2).
-- Per-block extraction health as an ADDITIVE, immutable, versioned artifact keyed
-- by extraction/span + analyzer_version. This does NOT mutate DocumentBlock and
-- makes no retroactive claim that old IR carried block quality: rows begin
-- `unknown` until analyzed (§13.1.2), and unknown is never treated as healthy
-- (§16). Health does not infer equation/figure safety from a page-wide flag alone
-- -- it folds page-health inputs with block geometry/text-density heuristics.
--
-- recommended_view drives the reader's four §3.4 behaviors:
--   derived      -> render marker markdown, "view original" available (ok)
--   crop_adjacent-> derived + original PDF region crop toggle (suspect+geometry)
--   crop_default -> default to region crop, label text unreliable (failed+geometry)
--   warn_link    -> visible warning + source link (no geometry)

CREATE TABLE source_block_health (
  id TEXT PRIMARY KEY,
  extraction_id TEXT NOT NULL REFERENCES source_extraction_runs(id),
  span_id TEXT NOT NULL,
  analyzer_version TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'unknown'
    CHECK (status IN ('ok', 'suspect', 'failed', 'unknown')),
  reason_flags_json TEXT NOT NULL DEFAULT '[]',
  signal_provenance_json TEXT NOT NULL DEFAULT '{}',
  confidence REAL,
  page_health_flags_json TEXT NOT NULL DEFAULT '[]',
  recommended_view TEXT NOT NULL DEFAULT 'derived'
    CHECK (recommended_view IN ('derived', 'crop_adjacent', 'crop_default', 'warn_link')),
  created_at TEXT NOT NULL,
  UNIQUE(extraction_id, span_id, analyzer_version)
);
CREATE INDEX idx_source_block_health_extraction ON source_block_health(extraction_id);
