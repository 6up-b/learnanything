-- Slice 2 T6 (spec_embedding_consumers_v1 §9, §12): keyword search over source
-- blocks. DERIVED: an FTS5 BM25 index rebuildable from source_document_blocks
-- (RAW_LEDGER) by its one registered replayer (source_block_fts). Retrieval is
-- context only; nothing here is evidence.
--
-- Each row's rowid is its block's rowid, so the triggers below keep the index
-- in step with every writer of source_document_blocks (extraction persistence
-- replaces a run's blocks in one transaction). Page furniture is not indexed,
-- matching the library search's exclusions. extraction_id and span_id are
-- UNINDEXED identity columns: queries filter on them and never match them.
--
-- HAZARD: source_document_blocks has a composite primary key, so its rowid is
-- implicit. A migration that rebuilds that table (create, copy, drop, rename)
-- drops these triggers and may renumber rowids; it must recreate the triggers
-- and rebuild this index (the source_block_fts replayer, run by
-- `learnloop rebuild-derived-state`). The delete paths match the block's
-- identity as well as its rowid, so a renumbered rowid never deletes another
-- block's row, and `learnloop doctor` reports any drift (stale or missing rows).
--
-- Numbering: built as 175 on the T6 branch and renumbered to 177 at its merge
-- (main's 175 is router R0, 176 Slice 2 T1). The branch's 176 (re-review F20)
-- only recreated these delete and update triggers, unchanged, for vaults that
-- had applied 175 before its in-place edit; no vault has applied a 177 other
-- than this one, so that repair is folded in here rather than kept as a 178.
CREATE VIRTUAL TABLE source_block_fts USING fts5(
  text,
  extraction_id UNINDEXED,
  span_id UNINDEXED,
  tokenize = 'porter unicode61 remove_diacritics 2'
);

CREATE TRIGGER source_block_fts_after_insert
AFTER INSERT ON source_document_blocks
WHEN NEW.block_type NOT IN ('PageHeader', 'PageFooter', 'TableOfContents')
BEGIN
  INSERT OR REPLACE INTO source_block_fts(rowid, text, extraction_id, span_id)
  VALUES (NEW.rowid, NEW.text, NEW.extraction_id, NEW.span_id);
END;

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

INSERT INTO source_block_fts(rowid, text, extraction_id, span_id)
SELECT rowid, text, extraction_id, span_id
  FROM source_document_blocks
 WHERE block_type NOT IN ('PageHeader', 'PageFooter', 'TableOfContents');
