-- What a running ingest job is doing, beyond its phase and its done/total count: the facts a learner's wait shows,
-- each recorded at the moment it happens.
--
-- Additive: one new table (WORKFLOW in db.table_roles, as ingest_jobs beside it; DENIED to adaptive difficulty). No
-- row is changed or backfilled. Operational only: nothing that builds, writes, scores, schedules, certifies or
-- counts exposure reads it (the status lines that Today and the Library show read it), and it changes no model
-- request, deadline or retry rule, so there is no algorithm tag.
--
-- One row per job (no foreign key: the queue's history is deleted with its rows, delete_finished_ingest_batches),
-- for its newest attempt (attempt_count) and its try within that attempt (try_number: 2 is the
-- runner's own second try after a failure a retry may cure), from try_started_at. A new attempt or try starts the
-- row afresh.
-- step: the job's own step, where its handler says one (the study map's synthesis: 'plan', 'plan_reused',
-- 'evidence', 'identity', 'structure', 'validate', 'persist', 'apply'); NULL otherwise.
-- drafted_topics: how many topics a complete, parsed and normalized candidate holds, written when its checks
-- start; NULL before one exists (never counted from an unfinished answer).
-- reused: how many of the job's units it kept from an earlier run and does not ask for again (an inventory's
-- units already read), once it knows; NULL otherwise.
-- output_call_id, output_events, last_output_at: the model request whose streamed output last arrived (its
-- model_call_receipts id), how many non-empty output pieces it has streamed so far, and when the last arrived.
-- Written as output arrives (at most about once a second); a transport that streams nothing writes none.
CREATE TABLE ingest_job_progress (
  job_id TEXT PRIMARY KEY,
  attempt_count INTEGER NOT NULL,
  try_number INTEGER NOT NULL DEFAULT 1,
  try_started_at TEXT NOT NULL,
  step TEXT,
  drafted_topics INTEGER,
  reused INTEGER,
  output_call_id TEXT,
  output_events INTEGER NOT NULL DEFAULT 0,
  last_output_at TEXT,
  updated_at TEXT NOT NULL
);
