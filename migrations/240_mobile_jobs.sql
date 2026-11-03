-- Mobile M2a: accepted jobs for the phone's long mutations
-- (docs/specs/spec_mobile_tailnet_v1.md §6.3, §8; docs/reviews/mobile-m2a.md).
-- Built as 240 beside the data-capture stage's 239; renumbered at its landing if need be.
--
-- mobile_jobs (WORKFLOW): one row per long request a phone made. It answers the
-- status endpoints from a read-only connection, and it is what a restarted host
-- picks up. (device_id, request_id) is the acceptance's idempotency key; for a
-- submit, request_id is the submission id. params_json is the accepted copy the job
-- worker runs, whether or not the phone is still connected, and params_sha256 is
-- what tells an identical retry (coalesced) from a conflicting one (409).
-- host_boot_id says which run of the host holds the row, and boot_attempts how many
-- runs have tried it (three, then failed: host_restart_exhausted).
-- failed means no attempt committed under the request. recorded is a submit whose
-- attempt did commit and whose completion has not finished: its feedback is delayed,
-- its key is spent, and a later read or host start may still finish it.
--
-- Never evidence: the attempt and its receipt are written by the ordinary handlers,
-- and nothing in scoring, scheduling, projection or replay reads this table.

CREATE TABLE mobile_jobs (
  id TEXT PRIMARY KEY,
  device_id TEXT NOT NULL,
  request_id TEXT NOT NULL,
  method TEXT NOT NULL,
  params_json TEXT NOT NULL,
  params_sha256 TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('accepted', 'running', 'completed', 'failed', 'recorded')),
  result_json TEXT,
  error_json TEXT,
  host_boot_id TEXT NOT NULL,
  boot_attempts INTEGER NOT NULL DEFAULT 0 CHECK (boot_attempts >= 0),
  accepted_at TEXT NOT NULL,
  started_at TEXT,
  finished_at TEXT,
  UNIQUE (device_id, request_id)
);

CREATE INDEX mobile_jobs_request ON mobile_jobs(request_id);
CREATE INDEX mobile_jobs_open ON mobile_jobs(state) WHERE state IN ('accepted', 'running');
