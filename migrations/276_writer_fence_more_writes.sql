-- The writer fence's review fix round (WF-R2, WF-R6, WF-R8, WF-R9; docs/reviews/refactor-writer-fence.md,
-- "Review fix round"; learnloop.db.writer_fence.GUARDED): four more stale writes that lose or corrupt a fact join the
-- fence of migration 275, with the same rule.
--
-- plan_presentations: a plan's served item; the serve-time forecast is recorded only by the serve that inserts it, so
--   a stale serve that commits its presentation loses that forecast for good.
-- probe_presentations: a probe pinned for the learner; a stale writer would pin one the current rule refuses, with no
--   router decision behind it.
-- grade_adjudications: an adjudication moves an interpretation's head even when it adds no evidence; a stale command
--   would skip the replay the current rule runs.
-- reader_section_progress: only where a row first records a completion (the first completed_at and its cause are
--   kept for good); a stale reader's progress without a completion is not fenced.
CREATE TRIGGER writer_fence_plan_presentations_insert BEFORE INSERT ON plan_presentations
WHEN EXISTS (SELECT 1 FROM writer_fence WHERE id = 1)
 AND NOT EXISTS (SELECT 1 FROM pragma_function_list
                 WHERE name = lower('learnloop writes under ' || (SELECT algorithm_version FROM writer_fence WHERE id = 1)))
 AND (EXISTS (SELECT 1 FROM pragma_function_list WHERE name GLOB 'learnloop writes under *')
      OR NOT EXISTS (SELECT 1 FROM pragma_function_list WHERE name = 'learnloop fenced writer'))
BEGIN SELECT RAISE(ABORT, 'LearnLoop writer fence: this vault was upgraded while this LearnLoop process had it open, so nothing was saved. Restart LearnLoop from the upgraded version, or reload the vault, and try again.'); END;
CREATE TRIGGER writer_fence_probe_presentations_insert BEFORE INSERT ON probe_presentations
WHEN EXISTS (SELECT 1 FROM writer_fence WHERE id = 1)
 AND NOT EXISTS (SELECT 1 FROM pragma_function_list
                 WHERE name = lower('learnloop writes under ' || (SELECT algorithm_version FROM writer_fence WHERE id = 1)))
 AND (EXISTS (SELECT 1 FROM pragma_function_list WHERE name GLOB 'learnloop writes under *')
      OR NOT EXISTS (SELECT 1 FROM pragma_function_list WHERE name = 'learnloop fenced writer'))
BEGIN SELECT RAISE(ABORT, 'LearnLoop writer fence: this vault was upgraded while this LearnLoop process had it open, so nothing was saved. Restart LearnLoop from the upgraded version, or reload the vault, and try again.'); END;
CREATE TRIGGER writer_fence_grade_adjudications_insert BEFORE INSERT ON grade_adjudications
WHEN EXISTS (SELECT 1 FROM writer_fence WHERE id = 1)
 AND NOT EXISTS (SELECT 1 FROM pragma_function_list
                 WHERE name = lower('learnloop writes under ' || (SELECT algorithm_version FROM writer_fence WHERE id = 1)))
 AND (EXISTS (SELECT 1 FROM pragma_function_list WHERE name GLOB 'learnloop writes under *')
      OR NOT EXISTS (SELECT 1 FROM pragma_function_list WHERE name = 'learnloop fenced writer'))
BEGIN SELECT RAISE(ABORT, 'LearnLoop writer fence: this vault was upgraded while this LearnLoop process had it open, so nothing was saved. Restart LearnLoop from the upgraded version, or reload the vault, and try again.'); END;
CREATE TRIGGER writer_fence_reader_section_progress_insert BEFORE INSERT ON reader_section_progress
WHEN EXISTS (SELECT 1 FROM writer_fence WHERE id = 1)
 AND (NEW.completed_at IS NOT NULL)
 AND NOT EXISTS (SELECT 1 FROM pragma_function_list
                 WHERE name = lower('learnloop writes under ' || (SELECT algorithm_version FROM writer_fence WHERE id = 1)))
 AND (EXISTS (SELECT 1 FROM pragma_function_list WHERE name GLOB 'learnloop writes under *')
      OR NOT EXISTS (SELECT 1 FROM pragma_function_list WHERE name = 'learnloop fenced writer'))
BEGIN SELECT RAISE(ABORT, 'LearnLoop writer fence: this vault was upgraded while this LearnLoop process had it open, so nothing was saved. Restart LearnLoop from the upgraded version, or reload the vault, and try again.'); END;
CREATE TRIGGER writer_fence_reader_section_progress_update BEFORE UPDATE ON reader_section_progress
WHEN EXISTS (SELECT 1 FROM writer_fence WHERE id = 1)
 AND (OLD.completed_at IS NULL AND NEW.completed_at IS NOT NULL)
 AND NOT EXISTS (SELECT 1 FROM pragma_function_list
                 WHERE name = lower('learnloop writes under ' || (SELECT algorithm_version FROM writer_fence WHERE id = 1)))
 AND (EXISTS (SELECT 1 FROM pragma_function_list WHERE name GLOB 'learnloop writes under *')
      OR NOT EXISTS (SELECT 1 FROM pragma_function_list WHERE name = 'learnloop fenced writer'))
BEGIN SELECT RAISE(ABORT, 'LearnLoop writer fence: this vault was upgraded while this LearnLoop process had it open, so nothing was saved. Restart LearnLoop from the upgraded version, or reload the vault, and try again.'); END;
