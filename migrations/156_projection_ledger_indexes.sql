-- Canonical evidence replay is a whole-ledger ordered scan.  The repository
-- loads it in bulk (rather than one query per attempt); these filter/order
-- indexes let SQLite produce that stable order and find the latest
-- authoritative heads without sorting the full history on every rebuild.

CREATE INDEX idx_grading_evidence_live_replay
  ON grading_evidence(attempt_id, created_at, criterion_id, id)
  WHERE superseded_at IS NULL;

CREATE INDEX idx_error_events_attempt_replay
  ON error_events(attempt_id, created_at, id);

-- Replace the prefix-only indexes: the extended forms serve both point lookups
-- and latest-head replay without charging every write for two indexes sharing
-- the same leading column.
DROP INDEX IF EXISTS idx_activity_observations_attempt;
CREATE INDEX idx_activity_observations_attempt
  ON activity_observations(attempt_id, created_at DESC, id DESC)
  WHERE attempt_id IS NOT NULL;

DROP INDEX IF EXISTS idx_gadj_observation;
CREATE INDEX idx_gadj_observation
  ON grade_adjudications(observation_id, created_at DESC, id DESC)
  WHERE observation_id IS NOT NULL;
