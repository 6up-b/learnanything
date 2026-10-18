-- Adaptive hints H2b (spec_adaptive_hints_v1 §9 "Learner-text gaps", §10 H2,
-- G-H17): the practice screen's learner text written back to a hint.
--
-- learner_text_gaps.source_kind and learner_text_gap_jobs.source_kind gain
-- 'hint_feedback': a "doesn't connect" reply's text (help_assists.feedback_text
-- on a request = 'feedback' row, role hint_feedback) and an answer to a
-- discriminating question (an assist_kind = 'discriminate_answer' row, role
-- discriminate_answer), outside the workbench. Its source_id is the
-- help_assists row. Nothing else changes.
--
-- G-H17 asked for ONE widening carrying hint_feedback with workbench_text and
-- reader_formative; migration 208 (Reader RW1b) widened both tables with the
-- Reader's two kinds only, so this is the second widening (the deviation is
-- recorded in the spec's §15 since H0). It follows 208 exactly: SQLite cannot
-- widen a CHECK in place, so each table is rebuilt temp-then-rename with every
-- row and id preserved, under PRAGMA foreign_keys = OFF. DROP TABLE removes the
-- old indexes and triggers, which are recreated on the renamed tables (the
-- same names and definitions); the three tables whose foreign keys name
-- learner_text_gaps (learner_text_gap_reversals, learner_gap_check_advances,
-- learner_gap_commitments) resolve to the rebuilt one, and the runner's
-- foreign_key_check runs before the migration commits. The same columns,
-- defaults, CHECKs, UNIQUE keys, indexes and append-only triggers.
PRAGMA foreign_keys = OFF;

CREATE TABLE learner_text_gaps__212 (
  id TEXT PRIMARY KEY,
  source_kind TEXT NOT NULL CHECK (source_kind IN (
    'tutor_question', 'stuck_answer', 'diagnosis', 'workbench_text', 'reader_formative', 'hint_feedback'
  )),
  -- question_events.id | practice_attempts.id | attempt_diagnoses.id |
  -- reader_authored_questions.id (reader_formative) | RW2b's row (workbench_text) |
  -- help_assists.id (hint_feedback)
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
INSERT INTO learner_text_gaps__212 (
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
ALTER TABLE learner_text_gaps__212 RENAME TO learner_text_gaps;

CREATE INDEX learner_text_gaps_created ON learner_text_gaps(created_at, id);
CREATE INDEX learner_text_gaps_target ON learner_text_gaps(target_kind, target_id);
CREATE INDEX learner_text_gaps_created_lo ON learner_text_gaps(created_learning_object_id);
CREATE TRIGGER learner_text_gaps_no_update BEFORE UPDATE ON learner_text_gaps
BEGIN SELECT RAISE(ABORT, 'learner_text_gaps is append-only'); END;
CREATE TRIGGER learner_text_gaps_no_delete BEFORE DELETE ON learner_text_gaps
BEGIN SELECT RAISE(ABORT, 'learner_text_gaps is append-only'); END;

CREATE TABLE learner_text_gap_jobs__212 (
  id TEXT PRIMARY KEY,
  source_kind TEXT NOT NULL CHECK (source_kind IN (
    'tutor_question', 'stuck_answer', 'diagnosis', 'workbench_text', 'reader_formative', 'hint_feedback'
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
INSERT INTO learner_text_gap_jobs__212 (
  id, source_kind, source_id, state, attempt_count, lease_owner, lease_expires_at, lease_epoch,
  not_before, last_error, payload_json, created_at, updated_at
)
SELECT
  id, source_kind, source_id, state, attempt_count, lease_owner, lease_expires_at, lease_epoch,
  not_before, last_error, payload_json, created_at, updated_at
FROM learner_text_gap_jobs;

DROP TABLE learner_text_gap_jobs;
ALTER TABLE learner_text_gap_jobs__212 RENAME TO learner_text_gap_jobs;

CREATE INDEX learner_text_gap_jobs_order ON learner_text_gap_jobs(state, created_at, id);

PRAGMA foreign_keys = ON;
