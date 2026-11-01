-- Deliverable curriculum C2: notes in the learner's voice, linked
-- (spec_deliverable_curriculum_v1 §10, §12 C2;
-- docs/reviews/curriculum-c2-notes-linked.md).
--
-- Numbered 229: main's head is 228 (the migration runner has no contiguity
-- rule; renumbered at landing if another stage lands first).
--
-- LearnLoop never indexes the learner's notes: the owner's `tend` does
-- (curriculum/notes_tend.py is the one adapter). These two tables keep only
-- what a link needs, and only once a note is linked.
--
-- learner_notes (RAW_LEDGER): a snapshot of one note section (tend's heading
-- section) taken ONLY when it is linked (proposed or accepted): its tend
-- reference (path, heading path, line), tend's content hash, the file's title,
-- the heading, the note's date as tend reports it (captured_on: "your note
-- from 3 Oct"), its origin ('tend', or 'pocket_notes' for a 3DS page Pocket
-- Notes transcribed) and its text, bounded per note (truncated says so). When
-- tend reports a new content hash a new snapshot row is written (the newest
-- per note_key stands); a note is never written back to.
--
-- learner_note_links (RAW_LEDGER): one row per link decision. A model
-- proposal (authorship 'ai', status 'proposed', the how and its one line,
-- the LO it was judged for, the state key of that judgment) or the learner's
-- own act (authorship 'learner': 'accepted' when they link a note by hand
-- from the Reader or keep one, 'rejected' when one tap hides it). A link is
-- to a passage (extraction, section and the span its margin mark sits
-- beside) or to an LO (anchored at the LO's primary passage when judged).
-- target_key names what the note discusses (passage:<extraction>/<section>/<span>
-- or lo:<id>). The learner's newest row per (note_key, LO or target) stands
-- across re-judgments, so a hidden link stays hidden.
--
-- A note is never a source (no source_artifacts row), never a generation
-- input, never evidence and never a claim: no scoring, scheduling,
-- projection, grading, serving, generation or replay path reads these
-- tables. Kill switches notes.enabled and notes.tend.lexical_only.
-- Append-only by trigger.
CREATE TABLE learner_notes (
  id TEXT PRIMARY KEY,
  note_key TEXT NOT NULL,
  path TEXT NOT NULL,
  heading_path TEXT NOT NULL DEFAULT '',
  line INTEGER NOT NULL CHECK (line >= 1),
  content_hash TEXT NOT NULL,
  title TEXT NOT NULL,
  heading TEXT NOT NULL DEFAULT '',
  captured_on TEXT,
  origin TEXT NOT NULL CHECK (origin IN ('tend', 'pocket_notes')),
  text_md TEXT NOT NULL,
  truncated INTEGER NOT NULL DEFAULT 0 CHECK (truncated IN (0, 1)),
  created_at TEXT NOT NULL,
  UNIQUE (note_key, content_hash)
);
CREATE INDEX idx_learner_notes_key ON learner_notes(note_key, created_at);

CREATE TRIGGER learner_notes_no_update
BEFORE UPDATE ON learner_notes
BEGIN
  SELECT RAISE(ABORT, 'learner_notes is append-only');
END;

CREATE TRIGGER learner_notes_no_delete
BEFORE DELETE ON learner_notes
BEGIN
  SELECT RAISE(ABORT, 'learner_notes is append-only');
END;

CREATE TABLE learner_note_links (
  id TEXT PRIMARY KEY,
  note_id TEXT NOT NULL REFERENCES learner_notes(id),
  note_key TEXT NOT NULL,
  target_kind TEXT NOT NULL CHECK (target_kind IN ('passage', 'learning_object')),
  target_key TEXT NOT NULL,
  learning_object_id TEXT,
  extraction_id TEXT,
  section_id TEXT,
  span_id TEXT,
  goal_id TEXT,
  authorship TEXT NOT NULL CHECK (authorship IN ('ai', 'learner')),
  status TEXT NOT NULL CHECK (status IN ('proposed', 'accepted', 'rejected')),
  how TEXT CHECK (how IS NULL OR how IN ('restates', 'questions', 'disagrees', 'applies', 'worked_it')),
  how_line TEXT,
  state_key TEXT,
  ledger_id TEXT REFERENCES judgment_ledger(id),
  model TEXT,
  prompt_version TEXT,
  created_at TEXT NOT NULL,
  CHECK (target_kind <> 'passage' OR (extraction_id IS NOT NULL AND (section_id IS NOT NULL OR span_id IS NOT NULL))),
  CHECK (target_kind <> 'learning_object' OR learning_object_id IS NOT NULL),
  CHECK (authorship <> 'ai' OR (status = 'proposed' AND learning_object_id IS NOT NULL AND state_key IS NOT NULL
                                AND model IS NOT NULL AND prompt_version IS NOT NULL AND ledger_id IS NOT NULL)),
  CHECK (authorship <> 'learner' OR status IN ('accepted', 'rejected'))
);
CREATE INDEX idx_learner_note_links_note ON learner_note_links(note_key, created_at);
CREATE INDEX idx_learner_note_links_lo ON learner_note_links(learning_object_id, created_at);
CREATE INDEX idx_learner_note_links_reading ON learner_note_links(extraction_id, section_id);

CREATE TRIGGER learner_note_links_no_update
BEFORE UPDATE ON learner_note_links
BEGIN
  SELECT RAISE(ABORT, 'learner_note_links is append-only');
END;

CREATE TRIGGER learner_note_links_no_delete
BEFORE DELETE ON learner_note_links
BEGIN
  SELECT RAISE(ABORT, 'learner_note_links is append-only');
END;
