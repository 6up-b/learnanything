-- Canonical sources S3 (spec_source_practice_and_probes_v1.md §9.6): stored
-- syntopic comparisons. A paid output (one comparison call over verified
-- counterparts), never re-run on rebuild, reused when the same caller reopens
-- the same comparison. It holds no consensus: per-source contributions,
-- quote-verified pair relations and what was dropped or left uncompared.
CREATE TABLE source_comparisons (
  id TEXT PRIMARY KEY,
  query_hash TEXT NOT NULL,
  query_md TEXT NOT NULL,
  requested_perspectives_json TEXT NOT NULL DEFAULT '[]',
  counterpart_keys_json TEXT NOT NULL DEFAULT '[]',
  comparison_json TEXT NOT NULL,
  dropped_lines_json TEXT NOT NULL DEFAULT '[]',
  dropped_pins_json TEXT NOT NULL DEFAULT '[]',
  unverified_sources_json TEXT NOT NULL DEFAULT '[]',
  policy TEXT NOT NULL CHECK (policy IN ('reading', 'assisted_practice', 'post_attempt')),
  caller_context_json TEXT NOT NULL,
  model TEXT,
  prompt_version TEXT NOT NULL,
  ledger_ids_json TEXT NOT NULL DEFAULT '[]',
  caller TEXT NOT NULL,
  caller_ref TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_source_comparisons_query ON source_comparisons(query_hash, created_at);
