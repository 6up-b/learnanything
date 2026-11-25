-- The writer fence (refactor bug ledger L42-R2; docs/reviews/refactor-writer-fence.md; learnloop.db.writer_fence).
--
-- writer_fence holds the algorithm tag a tag-dependent write may commit under. An activation sets it inside its own
-- transaction, so it flips at the activation's commit and never before; a vault no fence-aware activation has touched
-- has no row, and then nothing is fenced (the config's tag is the vault's, as before this migration).
--
-- Each trigger below fences one write of a tag-dependent fact. A writable connection of fence-aware code registers
-- SQL functions named after the tags it writes under ('learnloop writes under <tag>') and the marker 'learnloop
-- fenced writer'. The triggers only look those names up in pragma_function_list and never call them, so a connection
-- without them still prepares the statement and meets the plain refusal. Once the row exists, a write is allowed only
-- on a connection registered for the row's tag, or on a fence-aware connection bound to no tag (a process that never
-- loaded this vault's config: a scratch copy, a test seeding rows). Everything else is refused: a stale writer of
-- this code (bound to another tag) and any connection without the marker, which is how code older than the fence
-- (and every other SQLite client) meets the database after the first activation it does not know.
CREATE TABLE writer_fence (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    algorithm_version TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TRIGGER writer_fence_no_delete BEFORE DELETE ON writer_fence
BEGIN SELECT RAISE(ABORT, 'writer_fence keeps its row'); END;
CREATE TRIGGER writer_fence_practice_attempts_insert BEFORE INSERT ON practice_attempts
WHEN EXISTS (SELECT 1 FROM writer_fence WHERE id = 1)
 AND NOT EXISTS (SELECT 1 FROM pragma_function_list
                 WHERE name = lower('learnloop writes under ' || (SELECT algorithm_version FROM writer_fence WHERE id = 1)))
 AND (EXISTS (SELECT 1 FROM pragma_function_list WHERE name GLOB 'learnloop writes under *')
      OR NOT EXISTS (SELECT 1 FROM pragma_function_list WHERE name = 'learnloop fenced writer'))
BEGIN SELECT RAISE(ABORT, 'LearnLoop writer fence: this vault was upgraded while this LearnLoop process had it open, so nothing was saved. Restart LearnLoop from the upgraded version, or reload the vault, and try again.'); END;
CREATE TRIGGER writer_fence_grading_evidence_insert BEFORE INSERT ON grading_evidence
WHEN EXISTS (SELECT 1 FROM writer_fence WHERE id = 1)
 AND NOT EXISTS (SELECT 1 FROM pragma_function_list
                 WHERE name = lower('learnloop writes under ' || (SELECT algorithm_version FROM writer_fence WHERE id = 1)))
 AND (EXISTS (SELECT 1 FROM pragma_function_list WHERE name GLOB 'learnloop writes under *')
      OR NOT EXISTS (SELECT 1 FROM pragma_function_list WHERE name = 'learnloop fenced writer'))
BEGIN SELECT RAISE(ABORT, 'LearnLoop writer fence: this vault was upgraded while this LearnLoop process had it open, so nothing was saved. Restart LearnLoop from the upgraded version, or reload the vault, and try again.'); END;
CREATE TRIGGER writer_fence_attempt_surprise_insert BEFORE INSERT ON attempt_surprise
WHEN EXISTS (SELECT 1 FROM writer_fence WHERE id = 1)
 AND NOT EXISTS (SELECT 1 FROM pragma_function_list
                 WHERE name = lower('learnloop writes under ' || (SELECT algorithm_version FROM writer_fence WHERE id = 1)))
 AND (EXISTS (SELECT 1 FROM pragma_function_list WHERE name GLOB 'learnloop writes under *')
      OR NOT EXISTS (SELECT 1 FROM pragma_function_list WHERE name = 'learnloop fenced writer'))
BEGIN SELECT RAISE(ABORT, 'LearnLoop writer fence: this vault was upgraded while this LearnLoop process had it open, so nothing was saved. Restart LearnLoop from the upgraded version, or reload the vault, and try again.'); END;
CREATE TRIGGER writer_fence_attempt_surprise_update BEFORE UPDATE ON attempt_surprise
WHEN EXISTS (SELECT 1 FROM writer_fence WHERE id = 1)
 AND NOT EXISTS (SELECT 1 FROM pragma_function_list
                 WHERE name = lower('learnloop writes under ' || (SELECT algorithm_version FROM writer_fence WHERE id = 1)))
 AND (EXISTS (SELECT 1 FROM pragma_function_list WHERE name GLOB 'learnloop writes under *')
      OR NOT EXISTS (SELECT 1 FROM pragma_function_list WHERE name = 'learnloop fenced writer'))
BEGIN SELECT RAISE(ABORT, 'LearnLoop writer fence: this vault was upgraded while this LearnLoop process had it open, so nothing was saved. Restart LearnLoop from the upgraded version, or reload the vault, and try again.'); END;
CREATE TRIGGER writer_fence_attempt_grade_curves_insert BEFORE INSERT ON attempt_grade_curves
WHEN EXISTS (SELECT 1 FROM writer_fence WHERE id = 1)
 AND NOT EXISTS (SELECT 1 FROM pragma_function_list
                 WHERE name = lower('learnloop writes under ' || (SELECT algorithm_version FROM writer_fence WHERE id = 1)))
 AND (EXISTS (SELECT 1 FROM pragma_function_list WHERE name GLOB 'learnloop writes under *')
      OR NOT EXISTS (SELECT 1 FROM pragma_function_list WHERE name = 'learnloop fenced writer'))
BEGIN SELECT RAISE(ABORT, 'LearnLoop writer fence: this vault was upgraded while this LearnLoop process had it open, so nothing was saved. Restart LearnLoop from the upgraded version, or reload the vault, and try again.'); END;
CREATE TRIGGER writer_fence_lesson_checks_insert BEFORE INSERT ON lesson_checks
WHEN EXISTS (SELECT 1 FROM writer_fence WHERE id = 1)
 AND NOT EXISTS (SELECT 1 FROM pragma_function_list
                 WHERE name = lower('learnloop writes under ' || (SELECT algorithm_version FROM writer_fence WHERE id = 1)))
 AND (EXISTS (SELECT 1 FROM pragma_function_list WHERE name GLOB 'learnloop writes under *')
      OR NOT EXISTS (SELECT 1 FROM pragma_function_list WHERE name = 'learnloop fenced writer'))
BEGIN SELECT RAISE(ABORT, 'LearnLoop writer fence: this vault was upgraded while this LearnLoop process had it open, so nothing was saved. Restart LearnLoop from the upgraded version, or reload the vault, and try again.'); END;
CREATE TRIGGER writer_fence_learning_object_mastery_insert BEFORE INSERT ON learning_object_mastery
WHEN EXISTS (SELECT 1 FROM writer_fence WHERE id = 1)
 AND NOT EXISTS (SELECT 1 FROM pragma_function_list
                 WHERE name = lower('learnloop writes under ' || (SELECT algorithm_version FROM writer_fence WHERE id = 1)))
 AND (EXISTS (SELECT 1 FROM pragma_function_list WHERE name GLOB 'learnloop writes under *')
      OR NOT EXISTS (SELECT 1 FROM pragma_function_list WHERE name = 'learnloop fenced writer'))
BEGIN SELECT RAISE(ABORT, 'LearnLoop writer fence: this vault was upgraded while this LearnLoop process had it open, so nothing was saved. Restart LearnLoop from the upgraded version, or reload the vault, and try again.'); END;
CREATE TRIGGER writer_fence_learning_object_mastery_update BEFORE UPDATE ON learning_object_mastery
WHEN EXISTS (SELECT 1 FROM writer_fence WHERE id = 1)
 AND NOT EXISTS (SELECT 1 FROM pragma_function_list
                 WHERE name = lower('learnloop writes under ' || (SELECT algorithm_version FROM writer_fence WHERE id = 1)))
 AND (EXISTS (SELECT 1 FROM pragma_function_list WHERE name GLOB 'learnloop writes under *')
      OR NOT EXISTS (SELECT 1 FROM pragma_function_list WHERE name = 'learnloop fenced writer'))
BEGIN SELECT RAISE(ABORT, 'LearnLoop writer fence: this vault was upgraded while this LearnLoop process had it open, so nothing was saved. Restart LearnLoop from the upgraded version, or reload the vault, and try again.'); END;
CREATE TRIGGER writer_fence_forecast_receipts_insert BEFORE INSERT ON forecast_receipts
WHEN EXISTS (SELECT 1 FROM writer_fence WHERE id = 1)
 AND NOT EXISTS (SELECT 1 FROM pragma_function_list
                 WHERE name = lower('learnloop writes under ' || (SELECT algorithm_version FROM writer_fence WHERE id = 1)))
 AND (EXISTS (SELECT 1 FROM pragma_function_list WHERE name GLOB 'learnloop writes under *')
      OR NOT EXISTS (SELECT 1 FROM pragma_function_list WHERE name = 'learnloop fenced writer'))
BEGIN SELECT RAISE(ABORT, 'LearnLoop writer fence: this vault was upgraded while this LearnLoop process had it open, so nothing was saved. Restart LearnLoop from the upgraded version, or reload the vault, and try again.'); END;
CREATE TRIGGER writer_fence_attempt_application_order_insert BEFORE INSERT ON attempt_application_order
WHEN EXISTS (SELECT 1 FROM writer_fence WHERE id = 1)
 AND NOT EXISTS (SELECT 1 FROM pragma_function_list
                 WHERE name = lower('learnloop writes under ' || (SELECT algorithm_version FROM writer_fence WHERE id = 1)))
 AND (EXISTS (SELECT 1 FROM pragma_function_list WHERE name GLOB 'learnloop writes under *')
      OR NOT EXISTS (SELECT 1 FROM pragma_function_list WHERE name = 'learnloop fenced writer'))
BEGIN SELECT RAISE(ABORT, 'LearnLoop writer fence: this vault was upgraded while this LearnLoop process had it open, so nothing was saved. Restart LearnLoop from the upgraded version, or reload the vault, and try again.'); END;
CREATE TRIGGER writer_fence_derived_state_rebuilds_insert BEFORE INSERT ON derived_state_rebuilds
WHEN EXISTS (SELECT 1 FROM writer_fence WHERE id = 1)
 AND NOT EXISTS (SELECT 1 FROM pragma_function_list
                 WHERE name = lower('learnloop writes under ' || (SELECT algorithm_version FROM writer_fence WHERE id = 1)))
 AND (EXISTS (SELECT 1 FROM pragma_function_list WHERE name GLOB 'learnloop writes under *')
      OR NOT EXISTS (SELECT 1 FROM pragma_function_list WHERE name = 'learnloop fenced writer'))
BEGIN SELECT RAISE(ABORT, 'LearnLoop writer fence: this vault was upgraded while this LearnLoop process had it open, so nothing was saved. Restart LearnLoop from the upgraded version, or reload the vault, and try again.'); END;
