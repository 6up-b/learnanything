-- Slice A Phase 6 review fixes (learner field F2, mvp-0.11): the quick check's
-- own presentations and a stable start-request identity. Queue state only:
-- nothing here is evidence, mastery or certification.

-- A retried "Check what I already know" start (same request id) recovers the
-- check it already created instead of opening a second one.
ALTER TABLE placement_quick_checks ADD COLUMN request_id TEXT;
CREATE UNIQUE INDEX placement_quick_checks_request
  ON placement_quick_checks(request_id) WHERE request_id IS NOT NULL;

-- One row per item the quick check presented, at most k per check. Only the
-- first attempt on a presented item, in the check's practice session, after
-- the presentation and before the check's stop/expiry boundary, is bound to
-- it; only bound attempts are the check's results.
CREATE TABLE placement_quick_check_items (
  calibration_session_id TEXT NOT NULL
    REFERENCES placement_quick_checks(calibration_session_id),
  ordinal INTEGER NOT NULL CHECK (ordinal >= 1),
  practice_item_id TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  presented_at TEXT NOT NULL,
  attempt_id TEXT,
  answered_at TEXT,
  PRIMARY KEY (calibration_session_id, ordinal),
  UNIQUE (calibration_session_id, practice_item_id),
  CHECK ((attempt_id IS NULL) = (answered_at IS NULL))
);
CREATE UNIQUE INDEX placement_quick_check_items_attempt
  ON placement_quick_check_items(attempt_id) WHERE attempt_id IS NOT NULL;
