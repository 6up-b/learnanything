-- Exam protection by extraction identity (docs/reviews/exam-protection-identity.md):
-- the held-out assessment signals a model run marked on one reading, kept
-- where they were made. Built as migration 225, a placeholder: renumber it
-- when it lands on main after the migrations queued ahead of it.
--
-- source_unit_inventories is a cache: a cache hit for another reading of the
-- same revision rebinds the cached row to that reading (its UNIQUE key is per
-- revision) and rewrites its span ids, so the row no longer says which
-- reading its signals were made on and the origin's signals are gone (final
-- verify F2). Exam protection never reads that mutable binding. Each fresh
-- inventory (a model run on its extraction, never a reuse) appends here the
-- span ids its held-out signals name, with the reading and revision it read
-- and the role it was made under; exam_material reads this ledger, across
-- every revision of the book, whatever the source sets now say (F14).
--
-- extraction_id NULL: the reading is not known. Only the backfill writes it,
-- for a cached row that a cache hit had already rebound (its usage names the
-- inventory it was rebound from): the book stays protected and the row marks
-- no reading. made_as_role NULL: not recorded (every backfilled row).
-- RAW_LEDGER: written by Repository.insert_unit_inventory, never updated
-- (trigger), deleted only with its book (source deletion).
CREATE TABLE source_held_out_signal_marks (
  id TEXT PRIMARY KEY,
  revision_id TEXT NOT NULL REFERENCES source_revisions(id),
  extraction_id TEXT REFERENCES source_extraction_runs(id),
  unit_id TEXT NOT NULL,
  inventory_id TEXT NOT NULL,
  made_as_role TEXT,
  -- JSON array of the held-out signals' span ids on that reading, sorted.
  span_ids_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_source_held_out_signal_marks_revision
  ON source_held_out_signal_marks(revision_id);
CREATE INDEX idx_source_held_out_signal_marks_extraction
  ON source_held_out_signal_marks(extraction_id);

CREATE TRIGGER source_held_out_signal_marks_no_update
BEFORE UPDATE ON source_held_out_signal_marks
BEGIN
  SELECT RAISE(ABORT, 'source_held_out_signal_marks is append-only');
END;

-- Backfill: every cached inventory whose signals hold anything out. A row
-- whose usage names no inventory it was rebound from was written by the model
-- run on its own extraction (a rebind rewrites usage), so its reading is
-- exact; a rebound row (or one whose usage cannot be read) marks no reading.
INSERT OR IGNORE INTO source_held_out_signal_marks(
  id, revision_id, extraction_id, unit_id, inventory_id, made_as_role, span_ids_json, created_at
)
SELECT
  'hos_legacy_' || inventory.id,
  inventory.source_revision_id,
  CASE
    WHEN inventory.usage_json IS NULL THEN inventory.extraction_id
    WHEN NOT json_valid(inventory.usage_json) THEN NULL
    WHEN json_extract(inventory.usage_json, '$.rebound_from_inventory_id') IS NOT NULL THEN NULL
    ELSE inventory.extraction_id
  END,
  inventory.unit_id,
  inventory.id,
  NULL,
  (
    SELECT json_group_array(span_id) FROM (
      SELECT DISTINCT CAST(span.value AS TEXT) AS span_id
      FROM json_each(inventory.inventory_json, '$.assessment_signals') AS signal,
           json_each(signal.value, '$.span_ids') AS span
      WHERE json_extract(signal.value, '$.held_out') = 1
        AND span.value IS NOT NULL AND CAST(span.value AS TEXT) != ''
      ORDER BY span_id
    )
  ),
  inventory.created_at
FROM source_unit_inventories AS inventory
WHERE json_valid(inventory.inventory_json)
  AND EXISTS (
    SELECT 1
    FROM json_each(inventory.inventory_json, '$.assessment_signals') AS signal,
         json_each(signal.value, '$.span_ids') AS span
    WHERE json_extract(signal.value, '$.held_out') = 1
      AND span.value IS NOT NULL AND CAST(span.value AS TEXT) != ''
  );
