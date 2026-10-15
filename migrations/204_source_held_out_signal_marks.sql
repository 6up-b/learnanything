-- Exam protection by extraction identity (docs/reviews/exam-protection-identity.md):
-- the held-out assessment signals a model run marked on one reading, kept
-- where they were made. Built on fix/reread-safety as migration 225, a
-- placeholder, and renumbered 204 at its landing on main after main's 203
-- (the chat frontend's C1a).
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
-- inventory it was rebound from): the book stays protected, no reading is
-- marked by any signal beside it, and the row marks no reading.
-- made_as_role NULL: not recorded (a backfilled row on a book with no outline
-- exam pick: the cache never recorded the role an inventory was made under).
-- RAW_LEDGER: written by Repository.insert_unit_inventory, never updated
-- (trigger), deleted only with its book (source deletion). A row whose role
-- was not recorded is recorded again as exam material, never rewritten, when
-- its book is exam material in the vault when the app migrates or opens it,
-- or before it stops being exam material (the vault writer, an outline pick
-- changed: db.stores.held_out_signals); exam protection reads either.
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
-- Its role, where the database knows it (Codex review of extraction
-- identity, F3): a book with an outline exam pick is exam material by its
-- role, so its signals protect whatever its membership becomes. The inventory
-- profile is no role: it is chosen apart from the role ('--role
-- primary_textbook --profile assessment'), so it qualifies nothing (re-review
-- F7). Only the vault knows the source sets' roles: the app records the
-- signals they qualify after migrating (learnloop.migration_coordinator).
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
  CASE
    WHEN EXISTS (
      SELECT 1 FROM source_unit_selections AS pick
      LEFT JOIN source_extraction_runs AS pick_run ON pick_run.id = pick.extraction_id
      LEFT JOIN source_revisions AS pick_revision ON pick_revision.id = pick_run.revision_id
      JOIN source_revisions AS own ON own.id = inventory.source_revision_id
      WHERE pick.role_override = 'exam'
        AND COALESCE(pick.source_id, pick_revision.source_id) = own.source_id
    ) THEN 'exam'
    ELSE NULL
  END,
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
