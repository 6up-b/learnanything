-- Why a section was finished, and under which algorithm tag (mvp-0.63, a section's end finishes it;
-- docs/reviews/algorithm-mvp-0.63.md).
--
-- reader_section_progress (WORKFLOW) gains two nullable columns, written once, in the same statement that first
-- stamps completed_at, and never changed after:
--   * completion_cause: 'reached_end' (the section's last readable passage was shown during the learner's own
--     reading: reader_section_ends) or 'learner_said' (the learner's "I've read this section");
--   * completion_algorithm_version: the vault's algorithm tag when the completion was written.
-- Both stay NULL on every row finished before the tag, and on every row finished below it: those completions were
-- written by any of the Reader's completions, a quick check's close included, and nothing here can tell which.
-- Nothing is backfilled: no end recorded before the tag is turned into a completion, and no existing completion is
-- given a cause. A completion is a reading and workflow event (the reading exposure, a plan block's end, the
-- section's questions); nothing that scores or certifies reads these columns.
ALTER TABLE reader_section_progress ADD COLUMN completion_cause TEXT
  CHECK (completion_cause IS NULL OR completion_cause IN ('reached_end', 'learner_said'));
ALTER TABLE reader_section_progress ADD COLUMN completion_algorithm_version TEXT;
