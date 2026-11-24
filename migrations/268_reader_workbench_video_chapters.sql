-- Reader workbench v2, suggested video chapters (docs/specs/spec_reader_workbench_v2.md §7.9, §15.1): a video's
-- chapters as LearnLoop suggested them and as the learner decided.
--
-- One new table:
--   video_chapters   WORKFLOW: one row per chapter of one reading of a video: its time range, its title and its LO
--                    tags as the chapters judge proposed them (judgment_ref names the judge's ledger row for the
--                    chapter's first transcript section), and its state: 'suggested' until the learner decides,
--                    then 'accepted' (it draws its tick on the scrub track and its range on the minimap) or
--                    'dismissed' ("not this"; logged by its decided_at). A decision is made once.
--
-- chapter_id is derived from the reading, the range and the title, so the same chapter suggested again finds its row
-- (and keeps the learner's decision): a new run replaces only the chapters still 'suggested'.
--
-- A suggestion is a proposal and never changes coverage: nothing that scores, schedules, certifies or writes evidence
-- reads this table, so no algorithm tag moves. Nothing is backfilled: no chapter exists before this migration.
CREATE TABLE video_chapters (
  chapter_id TEXT PRIMARY KEY,
  extraction_id TEXT NOT NULL,
  source_id TEXT,
  t0 REAL NOT NULL CHECK (t0 >= 0),
  t1 REAL NOT NULL CHECK (t1 > t0),
  title TEXT NOT NULL CHECK (length(title) >= 1),
  lo_ids_json TEXT NOT NULL DEFAULT '[]',
  state TEXT NOT NULL CHECK (state IN ('suggested', 'accepted', 'dismissed')),
  judgment_ref TEXT,
  suggested_at TEXT NOT NULL,
  decided_at TEXT,
  CHECK ((state = 'suggested') = (decided_at IS NULL))
);
CREATE INDEX idx_video_chapters_reading ON video_chapters(extraction_id, t0);

-- A decision is made once: only a suggested row changes, and only its state and decided_at.
CREATE TRIGGER video_chapters_decide_once
BEFORE UPDATE ON video_chapters
WHEN OLD.state != 'suggested'
  OR NEW.chapter_id IS NOT OLD.chapter_id OR NEW.extraction_id IS NOT OLD.extraction_id
  OR NEW.source_id IS NOT OLD.source_id OR NEW.t0 IS NOT OLD.t0 OR NEW.t1 IS NOT OLD.t1
  OR NEW.title IS NOT OLD.title OR NEW.lo_ids_json IS NOT OLD.lo_ids_json
  OR NEW.judgment_ref IS NOT OLD.judgment_ref OR NEW.suggested_at IS NOT OLD.suggested_at
BEGIN
  SELECT RAISE(ABORT, 'video_chapters: a chapter is decided once');
END;

-- Only a chapter still suggested is ever removed (a new run's replacement); a decision stays.
CREATE TRIGGER video_chapters_keep_decided
BEFORE DELETE ON video_chapters
WHEN OLD.state != 'suggested'
BEGIN
  SELECT RAISE(ABORT, 'video_chapters: a decided chapter is kept');
END;
