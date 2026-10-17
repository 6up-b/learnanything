-- Reader workbench RW1b (spec_reader_workbench_v1 §3.4 item 13, §4.2, §4.3):
-- the learner-text source kinds the Reader adds, and what its
-- selection-scoped formative questions need.
--
-- 1. learner_text_gaps.source_kind and learner_text_gap_jobs.source_kind gain
--    both of the reader workbench's kinds in ONE widening, so neither table is
--    rebuilt again: 'reader_formative' (RW1b: a next-step, why-step or
--    assumption answer the learner marked partly or no; later RW5a's missed
--    predictions) and 'workbench_text' (RW2b's stuck steps, "doesn't connect"
--    text and discriminating answers; RW2b builds its adapter). SQLite cannot
--    widen a CHECK in place, so each table is rebuilt temp-then-rename with
--    every row and id preserved (202's router_decisions precedent). DROP
--    TABLE removes the old indexes and triggers, which are recreated on the
--    renamed tables; the three tables whose foreign keys name
--    learner_text_gaps (learner_text_gap_reversals, learner_gap_check_advances,
--    learner_gap_commitments) resolve to the rebuilt one, and the runner's
--    foreign_key_check runs before the migration commits. Nothing else changes:
--    the same columns, defaults, CHECKs, UNIQUE keys, indexes and append-only
--    triggers.
-- 2. reader_authored_questions.answer_basis: whose words a selection-scoped
--    question's expected answer is -- 'source' (the book's own lines, found in
--    the passage in code) or 'model' (LearnLoop's model's, labelled so, W2).
--    NULL on section and inquiry rows, which stay byte-identical.
-- 3. The selection reuse key (spec §4.3: extraction, anchor spans, style,
--    prompt version) is enforced by the database, as RW1a's inquiry key is:
--    two workers can never land two questions for one selection, and a late
--    completion can never replace the one the learner saw.
PRAGMA foreign_keys = OFF;

CREATE TABLE learner_text_gaps__208 (
  id TEXT PRIMARY KEY,
  source_kind TEXT NOT NULL CHECK (source_kind IN (
    'tutor_question', 'stuck_answer', 'diagnosis', 'workbench_text', 'reader_formative'
  )),
  -- question_events.id | practice_attempts.id | attempt_diagnoses.id |
  -- reader_authored_questions.id (reader_formative) | RW2b's row (workbench_text)
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
INSERT INTO learner_text_gaps__208 (
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
ALTER TABLE learner_text_gaps__208 RENAME TO learner_text_gaps;

CREATE INDEX learner_text_gaps_created ON learner_text_gaps(created_at, id);
CREATE INDEX learner_text_gaps_target ON learner_text_gaps(target_kind, target_id);
CREATE INDEX learner_text_gaps_created_lo ON learner_text_gaps(created_learning_object_id);
CREATE TRIGGER learner_text_gaps_no_update BEFORE UPDATE ON learner_text_gaps
BEGIN SELECT RAISE(ABORT, 'learner_text_gaps is append-only'); END;
CREATE TRIGGER learner_text_gaps_no_delete BEFORE DELETE ON learner_text_gaps
BEGIN SELECT RAISE(ABORT, 'learner_text_gaps is append-only'); END;

CREATE TABLE learner_text_gap_jobs__208 (
  id TEXT PRIMARY KEY,
  source_kind TEXT NOT NULL CHECK (source_kind IN (
    'tutor_question', 'stuck_answer', 'diagnosis', 'workbench_text', 'reader_formative'
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
INSERT INTO learner_text_gap_jobs__208 (
  id, source_kind, source_id, state, attempt_count, lease_owner, lease_expires_at, lease_epoch,
  not_before, last_error, payload_json, created_at, updated_at
)
SELECT
  id, source_kind, source_id, state, attempt_count, lease_owner, lease_expires_at, lease_epoch,
  not_before, last_error, payload_json, created_at, updated_at
FROM learner_text_gap_jobs;

DROP TABLE learner_text_gap_jobs;
ALTER TABLE learner_text_gap_jobs__208 RENAME TO learner_text_gap_jobs;

CREATE INDEX learner_text_gap_jobs_order ON learner_text_gap_jobs(state, created_at, id);

ALTER TABLE reader_authored_questions ADD COLUMN answer_basis TEXT
  CHECK (answer_basis IS NULL OR answer_basis IN ('source', 'model'));

CREATE UNIQUE INDEX idx_reader_authored_questions_selection
  ON reader_authored_questions(extraction_id, anchor_span_ids_json, question_style, prompt_version)
  WHERE scope_kind = 'selection';

PRAGMA foreign_keys = ON;
