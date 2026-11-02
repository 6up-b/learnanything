-- Curriculum C2b: the learner's notes are the vault's own (spec_deliverable_curriculum_v1
-- §10 as built; docs/reviews/curriculum-c2b-vault-notes.md).
--
-- Numbered 233: main's head is 231 and RW5d P3 claims 232 (the migration
-- runner has no contiguity rule; renumbered at landing if needed).
--
-- "Your notes" are now the learner's Reader notes and highlights with text
-- (source_annotations) and their capture-inbox items (capture_inbox), searched
-- inside the vault; the tend adapter is gone. A snapshot of a linked vault
-- note carries origin 'vault' and a vault reference: vault_ref_kind
-- ('annotation' | 'capture') and vault_ref_id (the annotation's or the
-- capture's id). It has no file path or line, so path and line become
-- nullable: a 'vault' row needs its reference, a 'tend' or 'pocket_notes'
-- row (C2's, kept readable as history) its path and line, exactly as before.
-- Nothing else changes: the same columns otherwise, UNIQUE (note_key,
-- content_hash), index and append-only triggers, every row and id kept.
--
-- It follows 208, 212 and 231: SQLite cannot widen a CHECK in place, so the
-- table is rebuilt temp-then-rename under PRAGMA foreign_keys = OFF.
-- learner_note_links.note_id names learner_notes(id) and resolves to the
-- rebuilt table; the runner's foreign_key_check runs before the migration
-- commits. DROP TABLE removes the old index and triggers, which are recreated
-- on the renamed table with the same names and definitions.
PRAGMA foreign_keys = OFF;

CREATE TABLE learner_notes__233 (
  id TEXT PRIMARY KEY,
  note_key TEXT NOT NULL,
  path TEXT,
  heading_path TEXT NOT NULL DEFAULT '',
  line INTEGER CHECK (line IS NULL OR line >= 1),
  content_hash TEXT NOT NULL,
  title TEXT NOT NULL,
  heading TEXT NOT NULL DEFAULT '',
  captured_on TEXT,
  origin TEXT NOT NULL CHECK (origin IN ('tend', 'pocket_notes', 'vault')),
  text_md TEXT NOT NULL,
  truncated INTEGER NOT NULL DEFAULT 0 CHECK (truncated IN (0, 1)),
  created_at TEXT NOT NULL,
  vault_ref_kind TEXT CHECK (vault_ref_kind IS NULL OR vault_ref_kind IN ('annotation', 'capture')),
  vault_ref_id TEXT,
  CHECK (origin <> 'vault' OR (vault_ref_kind IS NOT NULL AND vault_ref_id IS NOT NULL)),
  CHECK (origin = 'vault' OR (path IS NOT NULL AND line IS NOT NULL)),
  UNIQUE (note_key, content_hash)
);
INSERT INTO learner_notes__233 (
  id, note_key, path, heading_path, line, content_hash, title, heading, captured_on, origin, text_md,
  truncated, created_at
)
SELECT
  id, note_key, path, heading_path, line, content_hash, title, heading, captured_on, origin, text_md,
  truncated, created_at
FROM learner_notes;

DROP TABLE learner_notes;
ALTER TABLE learner_notes__233 RENAME TO learner_notes;

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

PRAGMA foreign_keys = ON;
