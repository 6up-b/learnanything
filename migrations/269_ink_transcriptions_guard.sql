-- Reader workbench v2, pen and ink, fix round: a reading's receipt can no longer be replaced through its owner and
-- strokes.
--
-- ink_transcriptions (RECEIPT, migration 267) is append-only by trigger, but its replacing-INSERT guard checked the
-- primary key alone. An INSERT OR REPLACE with a fresh transcription_id and an existing (owner_kind, owner_id,
-- content_hash) met the UNIQUE key instead, and SQLite's REPLACE deleted the standing row without firing the delete
-- guard (recursive triggers are off). The guard now refuses an insert that meets either key. Nothing else changes:
-- the table, its rows and its other triggers stay as 267 made them.
DROP TRIGGER ink_transcriptions_no_replace;

CREATE TRIGGER ink_transcriptions_no_replace
BEFORE INSERT ON ink_transcriptions
WHEN EXISTS (SELECT 1 FROM ink_transcriptions WHERE transcription_id = NEW.transcription_id
             OR (owner_kind = NEW.owner_kind AND owner_id = NEW.owner_id AND content_hash = NEW.content_hash))
BEGIN
    SELECT RAISE(ABORT, 'ink_transcriptions is append-only');
END;
