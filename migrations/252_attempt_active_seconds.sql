-- Recognition and effort RE0 (docs/specs/spec_recognition_and_effort_v1.md §4.1).
--
-- Additive: one nullable column on practice_attempts. No row is deleted or backfilled, no evidence column changes,
-- and nothing scoring, scheduling, FSRS, mastery or the projection reads is touched (no successor; the playbook's
-- ruling is in docs/reviews/re0-capture.md).
--
-- practice_attempts.active_seconds: the seconds the learner was active on the attempt, on the same clock as the
-- router objective's active minutes (a gap between touches shorter than the Reader's idle threshold counts, a longer
-- one does not), summed across resumes of the same draft. It is never blended with latency_seconds (elapsed time
-- since the problem opened): RO's two clocks stay two. NULL means the surface did not send it, which every attempt
-- before this migration and every surface without a clock says; reports count it as missing and never impute it.
-- practice_attempts is RAW_LEDGER: replay updates graded columns in place and never this one. Only reports read it.
ALTER TABLE practice_attempts ADD COLUMN active_seconds INTEGER
  CHECK (active_seconds IS NULL OR active_seconds >= 0);
