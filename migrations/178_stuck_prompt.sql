-- "Write what you can" replaces "I don't know" (algorithm mvp-0.13; built as
-- migration 172 / mvp-0.11 and renumbered when it merged after main's 172-177).
--
-- The learner's "I'm stuck" control opens the answer box with "Write what you
-- can, or what's confusing you". What they send is an ORDINARY attempt of the
-- surface's attempt type at the standard evidence mass (graded and diagnosed
-- when it has text; a deterministic zero when empty), never `dont_know`. This
-- flag records that the answer came from that control, so replay rebuilds it
-- exactly (an empty stuck answer is a deliberate non-answer, not a blank) and
-- the share of stuck answers that contain text can be read back. The grader's
-- reading of a stuck answer lives on its blind record (`stuck_reading`).
-- Historical rows default to 0; `declared_dont_know` keeps its meaning.
ALTER TABLE practice_attempts ADD COLUMN declared_stuck INTEGER NOT NULL DEFAULT 0
  CHECK (declared_stuck IN (0, 1));
