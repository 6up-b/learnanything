-- Reader workbench v2, scratchpads (docs/specs/spec_reader_workbench_v2.md §10.6, §10.9, §10.11, §10.12, §15.1,
-- §15.2): what a submitted block, a carried question and a proposal leave behind, and pad text as learner text.
--
-- 1. Five new tables:
--      pad_block_submissions     RAW_LEDGER, append-only by trigger: one row per explicit "submit this block as...",
--                                naming the frozen block version and the attempt or teach-back it was handed to.
--      carried_questions         WORKFLOW: a question the learner carries, with its latest label.
--      carried_question_events   RAW_LEDGER, append-only by trigger: carried, surfaced, each label, ignored.
--      pad_proposals             RECEIPT, append-only by trigger: a connection LearnLoop suggested for one committed
--                                block version (at most one per version), with what found it.
--      proposal_labels           RAW_LEDGER, append-only by trigger: opened, not this, dismiss, ignored.
-- 2. learner_text_gaps.source_kind and learner_text_gap_jobs.source_kind gain 'pad_text': a committed block version
--    of the learner's own words, read by the gap pipeline as any learner text; its source_id is the
--    pad_block_versions.version_id whose words were read (the table's own comment, kept as 248 wrote it so the
--    rebuilt definition differs from 248's in the CHECK alone, does not list it).
-- 3. learner_text_gap_reversals.reversal gains 'superseded' (a pad block was edited: the gap read from its earlier
--    words stands aside for the new reading) and 'retracted' (the block was removed). The gap rows stay.
--
-- Each rebuild follows 235 and 248 exactly: SQLite cannot widen a CHECK in place, so the table is rebuilt
-- temp-then-rename with every row and id preserved, under PRAGMA foreign_keys = OFF; DROP TABLE removes the old
-- indexes and triggers, which are recreated on the renamed table with the same names and definitions; the tables
-- whose foreign keys name learner_text_gaps resolve to the rebuilt one; the runner's foreign_key_check runs before
-- the migration commits. The same columns, defaults, CHECKs, UNIQUE keys, indexes and append-only triggers
-- otherwise. No row changes.
PRAGMA foreign_keys = OFF;

-- 1. The five tables ------------------------------------------------------------------------------------------------

-- An explicit submission of one block version as an attempt or a teach-back. submission_id is client-minted, so a
-- retried submission finds its row instead of handing the text over twice; request_hash tells a retry from the same
-- id reused for something else. attempt_id is the attempt the entry point recorded; teach_back_id the conversation a
-- teach-back opened (the attempt that finishes it carries the same id as its agent run).
CREATE TABLE pad_block_submissions (
  submission_id TEXT PRIMARY KEY,
  block_id TEXT NOT NULL,
  version_id TEXT NOT NULL REFERENCES pad_block_versions(version_id),
  pad_id TEXT NOT NULL REFERENCES pads(pad_id),
  submitted_as TEXT NOT NULL CHECK (submitted_as IN ('attempt', 'teach_back')),
  practice_item_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  attempt_id TEXT,
  teach_back_id TEXT,
  request_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK ((submitted_as = 'attempt' AND attempt_id IS NOT NULL)
         OR (submitted_as = 'teach_back' AND teach_back_id IS NOT NULL))
);
CREATE INDEX idx_pad_block_submissions_block ON pad_block_submissions(block_id, created_at);

CREATE TRIGGER pad_block_submissions_no_update
BEFORE UPDATE ON pad_block_submissions
BEGIN
    SELECT RAISE(ABORT, 'pad_block_submissions is append-only');
END;

CREATE TRIGGER pad_block_submissions_no_delete
BEFORE DELETE ON pad_block_submissions
BEGIN
    SELECT RAISE(ABORT, 'pad_block_submissions is append-only');
END;

CREATE TRIGGER pad_block_submissions_no_replace
BEFORE INSERT ON pad_block_submissions
WHEN EXISTS (SELECT 1 FROM pad_block_submissions WHERE submission_id = NEW.submission_id)
BEGIN
    SELECT RAISE(ABORT, 'pad_block_submissions is append-only');
END;

-- A question the learner carries. carried_id is client-minted. origin_kind/origin_ref say where it was carried from
-- (a pad block, a selection or margin note on a passage, the desk drain, or typed); anchor_json is the passage it
-- was carried beside (extraction_id, span_id, anchor-v1), when there is one. state is the latest label: 'carried'
-- and 'not_now' are still carried, 'fruitful' and 'let_go' are not. version counts the labels, so a label names the
-- state it expects.
CREATE TABLE carried_questions (
  carried_id TEXT PRIMARY KEY,
  text TEXT NOT NULL CHECK (length(trim(text)) > 0),
  origin_kind TEXT NOT NULL CHECK (origin_kind IN ('block', 'selection', 'note', 'drain', 'typed')),
  origin_ref TEXT,
  anchor_json TEXT,
  desk_id TEXT,
  since TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'carried' CHECK (state IN ('carried', 'fruitful', 'not_now', 'let_go')),
  version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_carried_questions_state ON carried_questions(state, since);

CREATE TABLE carried_question_events (
  event_id TEXT PRIMARY KEY,
  carried_id TEXT NOT NULL REFERENCES carried_questions(carried_id),
  event TEXT NOT NULL CHECK (event IN ('carried', 'surfaced', 'fruitful', 'not_now', 'let_go', 'ignored')),
  ref TEXT,
  at TEXT NOT NULL
);
CREATE INDEX idx_carried_question_events_carried ON carried_question_events(carried_id, at);

CREATE TRIGGER carried_question_events_no_update
BEFORE UPDATE ON carried_question_events
BEGIN
    SELECT RAISE(ABORT, 'carried_question_events is append-only');
END;

CREATE TRIGGER carried_question_events_no_delete
BEFORE DELETE ON carried_question_events
BEGIN
    SELECT RAISE(ABORT, 'carried_question_events is append-only');
END;

CREATE TRIGGER carried_question_events_no_replace
BEFORE INSERT ON carried_question_events
WHEN EXISTS (SELECT 1 FROM carried_question_events WHERE event_id = NEW.event_id)
BEGIN
    SELECT RAISE(ABORT, 'carried_question_events is append-only');
END;

-- A connection LearnLoop suggested for one committed block version: target_spec_json is the content reference it
-- opens (with its target passage), reason_md the one line the marker's card shows, quote the target's words,
-- judgment_ref the judgment it rests on, found_by the machinery that found it (spec §10.6: passage links, search,
-- correspondents). One per block version: the marker density is at most one per block.
CREATE TABLE pad_proposals (
  proposal_id TEXT PRIMARY KEY,
  block_version_id TEXT NOT NULL UNIQUE REFERENCES pad_block_versions(version_id),
  block_id TEXT NOT NULL,
  pad_id TEXT NOT NULL REFERENCES pads(pad_id),
  found_by TEXT NOT NULL CHECK (found_by IN ('passage_link', 'search', 'correspondent')),
  target_spec_json TEXT NOT NULL,
  reason_md TEXT NOT NULL,
  quote TEXT NOT NULL DEFAULT '',
  judgment_ref TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_pad_proposals_pad ON pad_proposals(pad_id, block_id);

CREATE TRIGGER pad_proposals_no_update
BEFORE UPDATE ON pad_proposals
BEGIN
    SELECT RAISE(ABORT, 'pad_proposals is append-only');
END;

CREATE TRIGGER pad_proposals_no_delete
BEFORE DELETE ON pad_proposals
BEGIN
    SELECT RAISE(ABORT, 'pad_proposals is append-only');
END;

CREATE TRIGGER pad_proposals_no_replace
BEFORE INSERT ON pad_proposals
WHEN EXISTS (SELECT 1 FROM pad_proposals WHERE proposal_id = NEW.proposal_id
             OR block_version_id = NEW.block_version_id)
BEGIN
    SELECT RAISE(ABORT, 'pad_proposals is append-only');
END;

-- What the learner did with a proposal: a pad proposal's marker, or (from the menus' stage) a promoted row.
-- label_id is client-minted, so a retried label is written once.
CREATE TABLE proposal_labels (
  label_id TEXT PRIMARY KEY,
  proposal_kind TEXT NOT NULL CHECK (proposal_kind IN ('pad_proposal', 'promoted_row')),
  proposal_id TEXT NOT NULL,
  label TEXT NOT NULL CHECK (label IN ('opened', 'not_this', 'dismiss', 'ignored')),
  at TEXT NOT NULL
);
CREATE INDEX idx_proposal_labels_proposal ON proposal_labels(proposal_kind, proposal_id, at);

CREATE TRIGGER proposal_labels_no_update
BEFORE UPDATE ON proposal_labels
BEGIN
    SELECT RAISE(ABORT, 'proposal_labels is append-only');
END;

CREATE TRIGGER proposal_labels_no_delete
BEFORE DELETE ON proposal_labels
BEGIN
    SELECT RAISE(ABORT, 'proposal_labels is append-only');
END;

CREATE TRIGGER proposal_labels_no_replace
BEFORE INSERT ON proposal_labels
WHEN EXISTS (SELECT 1 FROM proposal_labels WHERE label_id = NEW.label_id)
BEGIN
    SELECT RAISE(ABORT, 'proposal_labels is append-only');
END;

-- 2. learner_text_gaps and learner_text_gap_jobs --------------------------------------------------------------------
CREATE TABLE learner_text_gaps__266 (
  id TEXT PRIMARY KEY,
  source_kind TEXT NOT NULL CHECK (source_kind IN (
    'tutor_question', 'stuck_answer', 'diagnosis', 'workbench_text', 'reader_formative', 'hint_feedback', 'learner_note',
    'lesson', 'external_chat', 'pad_text'
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
INSERT INTO learner_text_gaps__266 (
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
ALTER TABLE learner_text_gaps__266 RENAME TO learner_text_gaps;

CREATE INDEX learner_text_gaps_created ON learner_text_gaps(created_at, id);
CREATE INDEX learner_text_gaps_target ON learner_text_gaps(target_kind, target_id);
CREATE INDEX learner_text_gaps_created_lo ON learner_text_gaps(created_learning_object_id);
CREATE TRIGGER learner_text_gaps_no_update BEFORE UPDATE ON learner_text_gaps
BEGIN SELECT RAISE(ABORT, 'learner_text_gaps is append-only'); END;
CREATE TRIGGER learner_text_gaps_no_delete BEFORE DELETE ON learner_text_gaps
BEGIN SELECT RAISE(ABORT, 'learner_text_gaps is append-only'); END;

CREATE TABLE learner_text_gap_jobs__266 (
  id TEXT PRIMARY KEY,
  source_kind TEXT NOT NULL CHECK (source_kind IN (
    'tutor_question', 'stuck_answer', 'diagnosis', 'workbench_text', 'reader_formative', 'hint_feedback', 'learner_note',
    'lesson', 'external_chat', 'pad_text'
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
INSERT INTO learner_text_gap_jobs__266 (
  id, source_kind, source_id, state, attempt_count, lease_owner, lease_expires_at, lease_epoch,
  not_before, last_error, payload_json, created_at, updated_at
)
SELECT
  id, source_kind, source_id, state, attempt_count, lease_owner, lease_expires_at, lease_epoch,
  not_before, last_error, payload_json, created_at, updated_at
FROM learner_text_gap_jobs;

DROP TABLE learner_text_gap_jobs;
ALTER TABLE learner_text_gap_jobs__266 RENAME TO learner_text_gap_jobs;

CREATE INDEX learner_text_gap_jobs_order ON learner_text_gap_jobs(state, created_at, id);

-- 3. learner_text_gap_reversals ------------------------------------------------------------------------------------
CREATE TABLE learner_text_gap_reversals__266 (
  id TEXT PRIMARY KEY,
  gap_id TEXT NOT NULL REFERENCES learner_text_gaps(id),
  reversal TEXT NOT NULL CHECK (reversal IN (
    'undo_edge', 'undo_creation', 'not_this_belief', 'unlinked', 'superseded', 'retracted'
  )),
  actor TEXT NOT NULL CHECK (actor IN ('learner', 'owner')),
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  UNIQUE (gap_id, reversal)
);
INSERT INTO learner_text_gap_reversals__266 (id, gap_id, reversal, actor, detail_json, created_at)
SELECT id, gap_id, reversal, actor, detail_json, created_at
FROM learner_text_gap_reversals;

DROP TABLE learner_text_gap_reversals;
ALTER TABLE learner_text_gap_reversals__266 RENAME TO learner_text_gap_reversals;

CREATE TRIGGER learner_text_gap_reversals_no_update BEFORE UPDATE ON learner_text_gap_reversals
BEGIN SELECT RAISE(ABORT, 'learner_text_gap_reversals is append-only'); END;
CREATE TRIGGER learner_text_gap_reversals_no_delete BEFORE DELETE ON learner_text_gap_reversals
BEGIN SELECT RAISE(ABORT, 'learner_text_gap_reversals is append-only'); END;

PRAGMA foreign_keys = ON;
