-- Durable ingest workflows (spec_source_ingestion_v2 §6.2): repository-backed
-- batches/jobs/dependencies that survive process restarts, replacing the old
-- in-memory job manager. Schemas follow §6.2 verbatim with house NOT NULL /
-- REFERENCES / defaults added.
--
-- `workflow_type` / `job_type` are APPLICATION-validated open strings (core
-- types: import, extract, inventory, legacy_ingest, exam_ingest,
-- bootstrap_synthesis, append_synthesis, extraction_repair). Deliberately NO
-- SQL CHECK on them so a new workflow never needs a migration. Status vocabulary
-- is closed, so a CHECK is appropriate there.

CREATE TABLE ingest_batches (
  id TEXT PRIMARY KEY,
  workflow_type TEXT NOT NULL,
  payload_schema_version INTEGER NOT NULL DEFAULT 1,
  subject_id TEXT,
  source_set_id TEXT,
  status TEXT NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued', 'running', 'waiting_for_input',
                      'completed', 'failed', 'blocked', 'cancelled')),
  created_at TEXT NOT NULL,
  started_at TEXT,
  finished_at TEXT,
  cancel_requested INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_ingest_batches_status ON ingest_batches(status);

CREATE TABLE ingest_jobs (
  id TEXT PRIMARY KEY,
  batch_id TEXT NOT NULL REFERENCES ingest_batches(id),
  ordinal INTEGER NOT NULL,
  job_type TEXT NOT NULL,
  payload_schema_version INTEGER NOT NULL DEFAULT 1,
  payload_json TEXT,
  status TEXT NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued', 'running', 'waiting_for_input',
                      'completed', 'failed', 'blocked', 'cancelled')),
  phase TEXT,
  message TEXT,
  current_window INTEGER,
  total_windows INTEGER,
  result_json TEXT,
  error_json TEXT,
  usage_json TEXT,
  attempt_count INTEGER NOT NULL DEFAULT 0,
  cancel_requested INTEGER NOT NULL DEFAULT 0,
  -- Lease: a running job is owned by worker_id and kept alive by heartbeat_at.
  -- Exactly one worker drains at a time; on startup an expired running lease is
  -- recovered to failed(interrupted). waiting_for_input holds NO lease.
  worker_id TEXT,
  heartbeat_at TEXT,
  created_at TEXT NOT NULL,
  started_at TEXT,
  finished_at TEXT
);

CREATE INDEX idx_ingest_jobs_batch ON ingest_jobs(batch_id, ordinal);
CREATE INDEX idx_ingest_jobs_status ON ingest_jobs(status);

CREATE TABLE ingest_job_dependencies (
  job_id TEXT NOT NULL REFERENCES ingest_jobs(id),
  depends_on_job_id TEXT NOT NULL REFERENCES ingest_jobs(id),
  PRIMARY KEY (job_id, depends_on_job_id)
);

CREATE INDEX idx_ingest_job_dependencies_dep ON ingest_job_dependencies(depends_on_job_id);
