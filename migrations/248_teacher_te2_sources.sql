-- Teacher TE2: lesson probes, lesson gaps and the probe's refusal reason
-- (spec_teacher_v1 rev 5 §11.3, §11.7, §11.9, §18.2, §24 row TE2;
-- docs/reviews/teacher-te2.md).
--
-- Numbered 248 on its branch: main's head is TE2-log's 247 (the migration
-- runner has no contiguity rule); renumbered at landing if another branch
-- (TE3a's AD opportunity CHECK) claims 248 first.
--
-- 1. followup_generation_jobs.kind (WORKFLOW) gains 'lesson': one generation
--    job per (lesson, node) a teacher's serve_probe asks for (dedupe_key
--    'lesson:<lesson id>:<node>' names the lesson; FG1's authoring operation on
--    the frontier route, at most FG1's two physical runs).
-- 2. generated_probe_items.source (RAW_LEDGER) gains 'lesson': the probe is
--    FG1's single-use identity, reserved for its lesson until served (no
--    workflow owns it), burned at first serve, retired unused at the lesson's
--    close or on "Teach it anyway". generated_probe_burns' foreign key names
--    this table and resolves to the rebuilt one.
-- 3. learner_text_gaps.source_kind and learner_text_gap_jobs.source_kind gain
--    'lesson' (a teacher's propose_gap on the learner's words in a lesson) and
--    C1b's 'external_chat', so C1b needs no rebuild of its own (spec §11.7,
--    §18.2). The three tables whose foreign keys name learner_text_gaps
--    resolve to the rebuilt one.
-- 4. lesson_episodes (RECEIPT, closed once) gains refusal_reason: why a probe
--    was not prepared (an enum; ids and enums only, as every episode field),
--    set with its close. Its close-once trigger is recreated so the probe's
--    generated item id, unknown at the opening, may also be set once with the
--    close (from NULL only); every other opening field stays as it was.
--
-- Each rebuild follows 231 and 236 exactly: SQLite cannot widen a CHECK in
-- place, so the table is rebuilt temp-then-rename with every row and id
-- preserved, under PRAGMA foreign_keys = OFF; DROP TABLE removes the old
-- indexes and triggers, which are recreated on the renamed table with the same
-- names and definitions; the runner's foreign_key_check runs before the
-- migration commits. The same columns, defaults, CHECKs, UNIQUE keys, indexes
-- and append-only triggers otherwise. No row changes.
PRAGMA foreign_keys = OFF;

-- 1. followup_generation_jobs -------------------------------------------------
CREATE TABLE followup_generation_jobs__248 (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('workflow', 'entry_episode', 'need', 'lesson')),
  dedupe_key TEXT NOT NULL UNIQUE,
  workflow_id TEXT REFERENCES followup_workflows(id),
  probe_episode_id TEXT,
  need_id TEXT,
  state TEXT NOT NULL DEFAULT 'queued'
    CHECK (state IN ('queued', 'leased', 'done', 'failed', 'skipped')),
  attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  lease_owner TEXT,
  lease_expires_at TEXT,
  lease_epoch INTEGER NOT NULL DEFAULT 0,
  not_before TEXT,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
INSERT INTO followup_generation_jobs__248 (
  id, kind, dedupe_key, workflow_id, probe_episode_id, need_id, state, attempt_count, lease_owner,
  lease_expires_at, lease_epoch, not_before, last_error, created_at, updated_at
)
SELECT
  id, kind, dedupe_key, workflow_id, probe_episode_id, need_id, state, attempt_count, lease_owner,
  lease_expires_at, lease_epoch, not_before, last_error, created_at, updated_at
FROM followup_generation_jobs;

DROP TABLE followup_generation_jobs;
ALTER TABLE followup_generation_jobs__248 RENAME TO followup_generation_jobs;

CREATE INDEX followup_generation_jobs_order ON followup_generation_jobs(state, created_at, id);

-- 2. generated_probe_items ----------------------------------------------------
CREATE TABLE generated_probe_items__248 (
  practice_item_id TEXT PRIMARY KEY,
  item_revision TEXT NOT NULL,
  source TEXT NOT NULL CHECK (source IN ('workflow', 'entry', 'mint', 'batch', 'manual', 'lesson')),
  workflow_id TEXT REFERENCES followup_workflows(id),
  probe_episode_id TEXT,
  created_at TEXT NOT NULL
);
INSERT INTO generated_probe_items__248 (
  practice_item_id, item_revision, source, workflow_id, probe_episode_id, created_at
)
SELECT practice_item_id, item_revision, source, workflow_id, probe_episode_id, created_at
FROM generated_probe_items;

DROP TABLE generated_probe_items;
ALTER TABLE generated_probe_items__248 RENAME TO generated_probe_items;

CREATE INDEX generated_probe_items_workflow ON generated_probe_items(workflow_id);
CREATE TRIGGER generated_probe_items_no_delete
BEFORE DELETE ON generated_probe_items
BEGIN
    SELECT RAISE(ABORT, 'generated_probe_items is append-only');
END;
CREATE TRIGGER generated_probe_items_no_update
BEFORE UPDATE ON generated_probe_items
BEGIN
    SELECT RAISE(ABORT, 'generated_probe_items is append-only');
END;

-- 3. learner_text_gaps and learner_text_gap_jobs ---------------------------------
CREATE TABLE learner_text_gaps__248 (
  id TEXT PRIMARY KEY,
  source_kind TEXT NOT NULL CHECK (source_kind IN (
    'tutor_question', 'stuck_answer', 'diagnosis', 'workbench_text', 'reader_formative', 'hint_feedback', 'learner_note',
    'lesson', 'external_chat'
  )),
  -- question_events.id | practice_attempts.id | attempt_diagnoses.id |
  -- reader_authored_questions.id (reader_formative) | RW2b's row (workbench_text) |
  -- help_assists.id (hint_feedback) | learner_notes.id (learner_note: a linked note's snapshot) |
  -- lesson_turns.id (lesson: the teacher's propose_gap entry, naming the learner's turn) |
  -- C1b's row (external_chat)
  source_id TEXT NOT NULL,
  attempt_id TEXT,
  practice_item_id TEXT,
  -- The LO the text is about (the item's LO, a note's single related LO).
  anchor_learning_object_id TEXT,
  -- The asking item's subject: every target is grounded in it.
  subject_id TEXT,
  learner_text TEXT NOT NULL,
  chooser TEXT NOT NULL CHECK (chooser IN ('context_model', 'decider')),
  -- Who read it in context: the tutor, the diagnoser, or the stuck-text reader.
  context_judge TEXT NOT NULL CHECK (context_judge IN ('tutor', 'diagnoser', 'gap_reader')),
  context_kind TEXT,
  decider_kind TEXT,
  decider_json TEXT NOT NULL DEFAULT '{}',
  kind TEXT NOT NULL CHECK (kind IN ('prerequisite', 'misconception', 'slip', 'wording', 'none', 'unread')),
  named_json TEXT NOT NULL DEFAULT '{}',
  action TEXT NOT NULL CHECK (action IN (
    'matched_prerequisite', 'created_prerequisite', 'unmatched_prerequisite',
    'belief_sighting', 'belief_candidate', 'belief_registry_path', 'unplaced',
    'signal_only', 'unnamed', 'none', 'failed'
  )),
  target_kind TEXT CHECK (target_kind IS NULL OR target_kind IN ('learning_object', 'durable', 'candidate')),
  target_id TEXT,
  target_subject_id TEXT,
  match_basis TEXT,
  edge_id TEXT,
  created_concept_id TEXT,
  created_learning_object_id TEXT,
  seed_practice_item_id TEXT,
  seed_status TEXT,
  detail_json TEXT NOT NULL DEFAULT '{}',
  algorithm_version TEXT NOT NULL,
  pipeline_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (source_kind, source_id)
);
INSERT INTO learner_text_gaps__248 (
  id, source_kind, source_id, attempt_id, practice_item_id, anchor_learning_object_id, subject_id,
  learner_text, chooser, context_judge, context_kind, decider_kind, decider_json, kind, named_json,
  action, target_kind, target_id, target_subject_id, match_basis, edge_id, created_concept_id,
  created_learning_object_id, seed_practice_item_id, seed_status, detail_json, algorithm_version,
  pipeline_version, created_at
)
SELECT
  id, source_kind, source_id, attempt_id, practice_item_id, anchor_learning_object_id, subject_id,
  learner_text, chooser, context_judge, context_kind, decider_kind, decider_json, kind, named_json,
  action, target_kind, target_id, target_subject_id, match_basis, edge_id, created_concept_id,
  created_learning_object_id, seed_practice_item_id, seed_status, detail_json, algorithm_version,
  pipeline_version, created_at
FROM learner_text_gaps;

DROP TABLE learner_text_gaps;
ALTER TABLE learner_text_gaps__248 RENAME TO learner_text_gaps;

CREATE INDEX learner_text_gaps_created ON learner_text_gaps(created_at, id);
CREATE INDEX learner_text_gaps_target ON learner_text_gaps(target_kind, target_id);
CREATE INDEX learner_text_gaps_created_lo ON learner_text_gaps(created_learning_object_id);
CREATE TRIGGER learner_text_gaps_no_update BEFORE UPDATE ON learner_text_gaps
BEGIN SELECT RAISE(ABORT, 'learner_text_gaps is append-only'); END;
CREATE TRIGGER learner_text_gaps_no_delete BEFORE DELETE ON learner_text_gaps
BEGIN SELECT RAISE(ABORT, 'learner_text_gaps is append-only'); END;

CREATE TABLE learner_text_gap_jobs__248 (
  id TEXT PRIMARY KEY,
  source_kind TEXT NOT NULL CHECK (source_kind IN (
    'tutor_question', 'stuck_answer', 'diagnosis', 'workbench_text', 'reader_formative', 'hint_feedback', 'learner_note',
    'lesson', 'external_chat'
  )),
  source_id TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'queued'
    CHECK (state IN ('queued', 'leased', 'done', 'failed', 'skipped')),
  attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  lease_owner TEXT,
  lease_expires_at TEXT,
  lease_epoch INTEGER NOT NULL DEFAULT 0,
  not_before TEXT,
  last_error TEXT,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (source_kind, source_id)
);
INSERT INTO learner_text_gap_jobs__248 (
  id, source_kind, source_id, state, attempt_count, lease_owner, lease_expires_at, lease_epoch,
  not_before, last_error, payload_json, created_at, updated_at
)
SELECT
  id, source_kind, source_id, state, attempt_count, lease_owner, lease_expires_at, lease_epoch,
  not_before, last_error, payload_json, created_at, updated_at
FROM learner_text_gap_jobs;

DROP TABLE learner_text_gap_jobs;
ALTER TABLE learner_text_gap_jobs__248 RENAME TO learner_text_gap_jobs;

CREATE INDEX learner_text_gap_jobs_order ON learner_text_gap_jobs(state, created_at, id);

-- 4. lesson_episodes: the probe's refusal reason, and its item id set with the close --------
ALTER TABLE lesson_episodes ADD COLUMN refusal_reason TEXT CHECK (refusal_reason IS NULL OR refusal_reason IN (
  'reserved_match', 'protection_unavailable', 'not_admitted', 'generation_failed', 'route_unavailable',
  'lesson_closed', 'switch_off'));

DROP TRIGGER lesson_episodes_close_once;
CREATE TRIGGER lesson_episodes_close_once
BEFORE UPDATE ON lesson_episodes
WHEN OLD.closed_at IS NOT NULL OR NEW.closed_at IS NULL
  OR NEW.id IS NOT OLD.id OR NEW.lesson_id IS NOT OLD.lesson_id OR NEW.kind IS NOT OLD.kind
  OR NEW.opened_by IS NOT OLD.opened_by OR NEW.node_id IS NOT OLD.node_id
  OR NEW.learning_object_id IS NOT OLD.learning_object_id OR NEW.opened_at IS NOT OLD.opened_at
  OR NEW.hypothesis_count IS NOT OLD.hypothesis_count OR NEW.hypothesis_hash IS NOT OLD.hypothesis_hash
  OR NEW.hypothesis_payload_id IS NOT OLD.hypothesis_payload_id OR NEW.repair_class IS NOT OLD.repair_class
  OR NEW.teacher_p IS NOT OLD.teacher_p OR NEW.teacher_forecast_receipt_id IS NOT OLD.teacher_forecast_receipt_id
  OR NEW.predicted_success IS NOT OLD.predicted_success OR NEW.predicted_low IS NOT OLD.predicted_low
  OR NEW.predicted_high IS NOT OLD.predicted_high OR NEW.predicted_source IS NOT OLD.predicted_source
  OR NEW.mastery_mean IS NOT OLD.mastery_mean OR NEW.mastery_variance IS NOT OLD.mastery_variance
  OR NEW.open_misconceptions IS NOT OLD.open_misconceptions OR NEW.open_hypotheses IS NOT OLD.open_hypotheses
  OR NEW.open_ids_json IS NOT OLD.open_ids_json OR NEW.origin IS NOT OLD.origin
  OR NEW.origin_decision_id IS NOT OLD.origin_decision_id OR NEW.objective_trace_id IS NOT OLD.objective_trace_id
  OR NEW.generation_job_id IS NOT OLD.generation_job_id
  OR (OLD.generated_item_id IS NOT NULL AND NEW.generated_item_id IS NOT OLD.generated_item_id)
  OR NEW.gap_job_id IS NOT OLD.gap_job_id OR NEW.created_lo_id IS NOT OLD.created_lo_id
  OR NEW.experiment_assignment_ids_json IS NOT OLD.experiment_assignment_ids_json
  OR NEW.episode_version IS NOT OLD.episode_version OR NEW.created_at IS NOT OLD.created_at
BEGIN
  SELECT RAISE(ABORT, 'lesson_episodes: only the closing fields may be set, once');
END;

PRAGMA foreign_keys = ON;
