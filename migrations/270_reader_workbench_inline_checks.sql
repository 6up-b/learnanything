-- Reader workbench v2, RD7: inline cold checks and veils (spec §12.6), and the video chapters' replacement guard.
--
-- check_administrations (WORKFLOW): one row per inline administration of a due "Check once" in the Reader
-- (surface reader_inline). It holds the administration lock shared with Today: at most one administration is open at
-- a time (the partial unique index), and a closed one never changes (the trigger). Its exposure state is a record of
-- what the learner opened or was helped with; what that does to the answer is the reveal ledger's (reveal_events),
-- written at once by check.expose. Nothing that scores, schedules or certifies reads this table: an answer reaches
-- evidence only as an ordinary attempt through the attempt service.
--
-- check_veil_sets (RECEIPT, append-only): what each protection computation veiled and what had been opened by then,
-- one row at the opening, one per protect_more, one at the close, for audit (§12.6.6).
--
-- video_chapters_no_replace_decided: migration 268 keeps a decided chapter against UPDATE and DELETE, but an
-- INSERT OR REPLACE reusing a decided chapter's id deleted it without firing video_chapters_keep_decided (recursive
-- triggers are off). An insert reusing a decided chapter's id is now skipped; a suggested row is replaced as before.
CREATE TABLE check_administrations (
  administration_token TEXT PRIMARY KEY,
  request_id TEXT NOT NULL UNIQUE,
  commitment_id TEXT NOT NULL,
  surface TEXT NOT NULL CHECK (surface IN ('reader_inline')),
  session_id TEXT NOT NULL,
  practice_item_id TEXT NOT NULL,
  contract_hash TEXT,
  cold INTEGER NOT NULL CHECK (cold IN (0, 1)),
  state TEXT NOT NULL CHECK (state IN ('open', 'submitted', 'abandoned', 'superseded')),
  protection_method TEXT NOT NULL,
  exposure_json TEXT NOT NULL DEFAULT '[]',
  submission_id TEXT UNIQUE,
  attempt_id TEXT,
  opened_at TEXT NOT NULL,
  closed_at TEXT,
  CHECK ((state = 'open') = (closed_at IS NULL)),
  CHECK (state != 'submitted' OR (submission_id IS NOT NULL AND attempt_id IS NOT NULL))
);
CREATE UNIQUE INDEX idx_check_administrations_one_open ON check_administrations((1)) WHERE state = 'open';
CREATE INDEX idx_check_administrations_commitment ON check_administrations(commitment_id, opened_at);

-- A closed administration is final: nothing about it changes, and it is never removed.
CREATE TRIGGER check_administrations_closed_final
BEFORE UPDATE ON check_administrations
WHEN OLD.state != 'open'
BEGIN
  SELECT RAISE(ABORT, 'check_administrations: a closed administration is final');
END;

CREATE TRIGGER check_administrations_kept
BEFORE DELETE ON check_administrations
BEGIN
  SELECT RAISE(ABORT, 'check_administrations: an administration is kept');
END;

CREATE TABLE check_veil_sets (
  veil_set_id TEXT PRIMARY KEY,
  administration_token TEXT NOT NULL REFERENCES check_administrations(administration_token),
  commitment_id TEXT NOT NULL,
  seq INTEGER NOT NULL CHECK (seq >= 1),
  kind TEXT NOT NULL CHECK (kind IN ('begin', 'more', 'close')),
  method TEXT NOT NULL,
  veiled_json TEXT NOT NULL DEFAULT '[]',
  opened_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  UNIQUE (administration_token, seq)
);

CREATE TRIGGER check_veil_sets_no_update
BEFORE UPDATE ON check_veil_sets
BEGIN
  SELECT RAISE(ABORT, 'check_veil_sets is append-only');
END;

CREATE TRIGGER check_veil_sets_no_delete
BEFORE DELETE ON check_veil_sets
BEGIN
  SELECT RAISE(ABORT, 'check_veil_sets is append-only');
END;

CREATE TRIGGER check_veil_sets_no_replace
BEFORE INSERT ON check_veil_sets
WHEN EXISTS (SELECT 1 FROM check_veil_sets WHERE veil_set_id = NEW.veil_set_id
             OR (administration_token = NEW.administration_token AND seq = NEW.seq))
BEGIN
  SELECT RAISE(ABORT, 'check_veil_sets is append-only');
END;

-- A decided chapter is never replaced: an insert reusing its id is skipped (recursive triggers are off, so a
-- REPLACE's implicit delete would not fire video_chapters_keep_decided).
CREATE TRIGGER video_chapters_no_replace_decided
BEFORE INSERT ON video_chapters
WHEN EXISTS (SELECT 1 FROM video_chapters WHERE chapter_id = NEW.chapter_id AND state != 'suggested')
BEGIN
  SELECT RAISE(IGNORE);
END;
