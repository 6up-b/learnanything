-- Reader workbench v2, RD7's fix round (the adversarial review of 2026-11-24): what an inline administration froze at
-- its opening and what it promised at its close, and guards against a replacing insert on every RD7 table.
--
-- check_administrations (WORKFLOW, migration 270) gains five columns, each written while the row is open (a closed
-- row stays final: check_administrations_closed_final):
--   candidates_json   every item that can settle the check as begin resolved them (the serving view's candidates),
--                     each with its answer key as it was then: an opening is charged to exactly these, measured
--                     against these keys, never a set rebuilt later from the served item.
--   presentation_json the learner-facing cold presentation served at begin (question, blocks, banner; never the key,
--                     hints, rubric or history): a restart shows it again without serving the item again.
--   pending_before    whether the check was still pending when the submission was reserved, so a retry's outcome is
--                     the first one's.
--   outcome_json      the outcome the close promised (cold or not, and why), returned to every retry.
--   exposure_ids_json the client's ids of the openings already recorded, so a retried opening charges nothing again.
--
-- The guards. SQLite's REPLACE deletes the row it conflicts with without firing a delete trigger (recursive triggers
-- are off), and a conflict can come through any unique key or an explicit rowid:
--   check_administrations_no_replace refuses an insert meeting a standing row's token, request id, submission id or
--     rowid, or a second open row (the one-open partial index would otherwise let REPLACE delete the open one).
--   check_veil_sets_no_replace and video_chapters_no_replace_decided (270) gain the explicit-rowid case.
ALTER TABLE check_administrations ADD COLUMN candidates_json TEXT NOT NULL DEFAULT '[]';
ALTER TABLE check_administrations ADD COLUMN presentation_json TEXT;
ALTER TABLE check_administrations ADD COLUMN pending_before INTEGER CHECK (pending_before IS NULL OR pending_before IN (0, 1));
ALTER TABLE check_administrations ADD COLUMN outcome_json TEXT;
ALTER TABLE check_administrations ADD COLUMN exposure_ids_json TEXT NOT NULL DEFAULT '[]';

CREATE TRIGGER check_administrations_no_replace
BEFORE INSERT ON check_administrations
WHEN EXISTS (SELECT 1 FROM check_administrations
             WHERE administration_token = NEW.administration_token
                OR request_id = NEW.request_id
                OR (NEW.submission_id IS NOT NULL AND submission_id = NEW.submission_id)
                OR rowid = NEW.rowid
                OR (NEW.state = 'open' AND state = 'open'))
BEGIN
  SELECT RAISE(ABORT, 'check_administrations: an administration is never replaced');
END;

DROP TRIGGER check_veil_sets_no_replace;

CREATE TRIGGER check_veil_sets_no_replace
BEFORE INSERT ON check_veil_sets
WHEN EXISTS (SELECT 1 FROM check_veil_sets WHERE veil_set_id = NEW.veil_set_id
             OR (administration_token = NEW.administration_token AND seq = NEW.seq)
             OR rowid = NEW.rowid)
BEGIN
  SELECT RAISE(ABORT, 'check_veil_sets is append-only');
END;

DROP TRIGGER video_chapters_no_replace_decided;

-- A decided chapter is never replaced: an insert meeting its id or its rowid is skipped (a suggested row is replaced
-- as before).
CREATE TRIGGER video_chapters_no_replace_decided
BEFORE INSERT ON video_chapters
WHEN EXISTS (SELECT 1 FROM video_chapters WHERE (chapter_id = NEW.chapter_id OR rowid = NEW.rowid)
             AND state != 'suggested')
BEGIN
  SELECT RAISE(IGNORE);
END;
