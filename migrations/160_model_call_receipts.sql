-- A started receipt survives a process interruption; NULL usage is unknown,
-- never zero cost. Checkpoints contain reusable validated provider work.
CREATE TABLE model_call_receipts (
  id TEXT PRIMARY KEY,
  parent_call_id TEXT REFERENCES model_call_receipts(id),
  owner_kind TEXT NOT NULL,
  owner_id TEXT NOT NULL,
  purpose TEXT NOT NULL,
  provider TEXT,
  model TEXT,
  prompt_hash TEXT,
  schema_hash TEXT,
  input_text TEXT,
  schema_json TEXT,
  output_text TEXT,
  status TEXT NOT NULL CHECK(status IN ('started','completed','failed','interrupted','truncated')),
  started_at TEXT NOT NULL,
  finished_at TEXT,
  input_tokens INTEGER,
  output_tokens INTEGER,
  cached_input_tokens INTEGER,
  reasoning_tokens INTEGER,
  cost REAL,
  provider_response_id TEXT,
  finish_reason TEXT,
  error_type TEXT,
  output_budget_tokens INTEGER,
  collection_version TEXT NOT NULL DEFAULT 'learnloop-events-v1'
);
CREATE INDEX idx_model_calls_owner ON model_call_receipts(owner_kind, owner_id, started_at);
CREATE TABLE model_work_checkpoints (
  cache_key TEXT PRIMARY KEY,
  purpose TEXT NOT NULL,
  result_json TEXT NOT NULL,
  usage_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
