-- Slice 2 T6 re-review F20: recreate source_block_fts's delete paths with the
-- block's identity match.
--
-- Migration 175 was edited in place (review F14) so that its delete and update
-- triggers delete an index row only when the row's rowid AND
-- (extraction_id, span_id) name the deleted block: a rowid renumbered by a
-- table rebuild can then never delete another block's row. Migrations carry no
-- checksum, so a vault that had already applied the earlier 175 (its delete
-- paths matched the rowid alone) would keep those triggers silently. This
-- migration drops and recreates both triggers with the identity match; for a
-- vault that applied the edited 175 it recreates them unchanged. The insert
-- trigger never changed. Any drift the earlier triggers allowed is reported by
-- `learnloop doctor` (sql:source_block_fts_drift) and repaired by
-- `learnloop rebuild-derived-state` (the source_block_fts replayer).
DROP TRIGGER IF EXISTS source_block_fts_after_delete;
DROP TRIGGER IF EXISTS source_block_fts_after_update;

CREATE TRIGGER source_block_fts_after_delete
AFTER DELETE ON source_document_blocks
BEGIN
  DELETE FROM source_block_fts
   WHERE rowid = OLD.rowid AND extraction_id = OLD.extraction_id AND span_id = OLD.span_id;
END;

CREATE TRIGGER source_block_fts_after_update
AFTER UPDATE OF extraction_id, span_id, block_type, text ON source_document_blocks
BEGIN
  DELETE FROM source_block_fts
   WHERE rowid = OLD.rowid AND extraction_id = OLD.extraction_id AND span_id = OLD.span_id;
  INSERT OR REPLACE INTO source_block_fts(rowid, text, extraction_id, span_id)
  SELECT NEW.rowid, NEW.text, NEW.extraction_id, NEW.span_id
  WHERE NEW.block_type NOT IN ('PageHeader', 'PageFooter', 'TableOfContents');
END;
