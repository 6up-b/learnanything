-- Canonical sources S4 (spec_source_practice_and_probes_v1.md §10.4): the typed
-- tool interface's receipts. Append-only: a validated request writes a
-- `request` row; running it writes a `run` row naming the request as its
-- parent. Nothing is updated in place, and nothing here is evidence, mastery,
-- FSRS or scheduler state.
CREATE TABLE source_tool_calls (
  id TEXT PRIMARY KEY,
  parent_id TEXT REFERENCES source_tool_calls(id),
  row_kind TEXT NOT NULL CHECK (row_kind IN ('request', 'run')),
  created_at TEXT NOT NULL,
  caller_kind TEXT NOT NULL CHECK (caller_kind IN ('tutor', 'router', 'agent')),
  caller_ref TEXT,
  -- The stored caller context the policy was derived from (re-read at run time,
  -- so the policy cannot change between the answer and the run).
  context_json TEXT NOT NULL,
  policy TEXT NOT NULL,
  tool TEXT NOT NULL CHECK (tool IN ('find_practice', 'find_sources', 'compare_sources', 'find_facets',
                                     'practice_availability')),
  arguments_json TEXT NOT NULL,
  dropped_json TEXT NOT NULL DEFAULT '[]',
  ledger_id TEXT,
  status TEXT NOT NULL CHECK (status IN ('requested', 'refused', 'ran', 'failed')),
  result_ref TEXT,
  result_keys_json TEXT NOT NULL DEFAULT '[]',
  source_versions_json TEXT NOT NULL DEFAULT '{}',
  model TEXT,
  prompt_version TEXT,
  latency_ms INTEGER,
  cost_json TEXT,
  CHECK ((row_kind = 'request' AND parent_id IS NULL AND status IN ('requested', 'refused'))
         OR (row_kind = 'run' AND parent_id IS NOT NULL AND status IN ('ran', 'failed')))
);
CREATE INDEX idx_source_tool_calls_parent ON source_tool_calls(parent_id);
CREATE INDEX idx_source_tool_calls_caller ON source_tool_calls(caller_kind, caller_ref, created_at);
CREATE TRIGGER source_tool_calls_no_update BEFORE UPDATE ON source_tool_calls
BEGIN SELECT RAISE(ABORT, 'source tool calls are append-only'); END;
CREATE TRIGGER source_tool_calls_no_delete BEFORE DELETE ON source_tool_calls
BEGIN SELECT RAISE(ABORT, 'source tool calls are append-only'); END;
