-- P3 slice 2, step 6 (spec_p3_reader_integration §6, design B step 6 + §D).
-- Demand-paged synthesis: a durable, lease-fenced background-request queue keyed on
-- the canonical hash of {revision, block span/deterministic window, action/preset,
-- inventory schema+profile, synthesis/output schema, prompt+provider+model, config
-- hash} (§6.2). The key includes the REVISION (not a mutable "current source") and
-- the exact model contract, so the same request reuses a standing/completed result
-- and a material version change mints a SUCCESSOR request.
--
-- No LLM runs on the reading hot path: reader.capture / invoke_preset only ENQUEUE
-- a `queued` row; a separate worker drains it. Results land as REVIEWABLE proposals
-- (source objects / canonical mapping proposals, migration 094) and are NEVER
-- auto-admitted into pools or evidence (§6.4). Cancelling a job never cancels the
-- local capture (§6.2 last line).
--
-- Lease fencing mirrors the migration-080 surface-mint precedent: `lease_epoch` is
-- bumped on every claim; a guarded write (WHERE ... AND lease_epoch = ?) from a
-- slow-but-alive worker whose lease expired and whose job was re-claimed applies to
-- zero rows and is silently rejected -- no double-apply (P1 fencing precedent).

CREATE TABLE reader_background_requests (
  id TEXT PRIMARY KEY,
  request_key TEXT NOT NULL,
  source_id TEXT NOT NULL,
  revision_id TEXT NOT NULL,
  extraction_id TEXT NOT NULL,
  span_id TEXT NOT NULL DEFAULT '',
  window_json TEXT NOT NULL DEFAULT '{}',
  preset TEXT NOT NULL,
  action TEXT NOT NULL DEFAULT '',
  inventory_profile TEXT NOT NULL DEFAULT 'semantic',
  inventory_schema_version TEXT NOT NULL DEFAULT '',
  synthesis_schema_version TEXT NOT NULL DEFAULT '',
  prompt_version TEXT NOT NULL DEFAULT '',
  provider TEXT NOT NULL DEFAULT '',
  model TEXT NOT NULL DEFAULT '',
  config_hash TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued', 'running', 'complete', 'partial', 'failed', 'cancelled', 'obsolete')),
  priority_band INTEGER NOT NULL DEFAULT 0,
  est_input_tokens INTEGER NOT NULL DEFAULT 0,
  est_output_tokens INTEGER NOT NULL DEFAULT 0,
  actual_input_tokens INTEGER NOT NULL DEFAULT 0,
  actual_output_tokens INTEGER NOT NULL DEFAULT 0,
  token_cap INTEGER NOT NULL DEFAULT 0,
  cache_hit INTEGER NOT NULL DEFAULT 0,
  reason TEXT,
  result_json TEXT NOT NULL DEFAULT '{}',
  annotation_id TEXT,
  commitment_id TEXT,
  client_idempotency_key TEXT,
  -- Fenced lease (migration 080 precedent):
  lease_owner TEXT,
  lease_expires_at TEXT,
  lease_epoch INTEGER NOT NULL DEFAULT 0,
  attempt_count INTEGER NOT NULL DEFAULT 0,
  cancel_requested INTEGER NOT NULL DEFAULT 0,
  error_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  completed_at TEXT,
  UNIQUE(request_key)
);
CREATE INDEX idx_reader_bg_requests_status ON reader_background_requests(status, priority_band DESC, created_at);
CREATE INDEX idx_reader_bg_requests_source ON reader_background_requests(source_id);
CREATE INDEX idx_reader_bg_requests_revision ON reader_background_requests(revision_id);
