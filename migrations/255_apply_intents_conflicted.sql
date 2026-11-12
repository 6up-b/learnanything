-- Refactor arc K, step K3.5: apply recovery never overwrites newer YAML
-- (docs/reviews/k2-ingestion-strategy-2026-11-11.md §3.1 K3.5; docs/reviews/refactor-k3.5.md).
--
-- apply_intents (WORKFLOW) is rebuilt so status also admits:
--   * 'conflicted': recovery found a target file that is neither the intent's
--     pre-image (pre_hash, or absent when pre_hash is null) nor its post-image
--     (post_hash). The file was changed after the intent was written, so
--     recovery writes nothing, keeps the newer file and leaves the intent for
--     the owner. conflict_json lists each such file ({rel_path, pre_hash,
--     post_hash, found_hash}); conflicted_at stamps when recovery saw it.
--   * 'set_aside': the owner kept the files as they are (the maintenance feed's
--     "Keep the files as they are"); the intent's database effects are never
--     performed and its proposal items stay pending. set_aside_at stamps it.
-- A pending or conflicted intent refuses the next accept until it is settled.
--
-- SQLite cannot widen a CHECK in place, so the table is rebuilt
-- temp-then-rename with every row and id preserved. No foreign key names
-- apply_intents and it has no triggers; DROP TABLE removes its one index,
-- recreated on the renamed table with the same name and definition. The
-- existing columns, defaults and CHECK values are otherwise unchanged, and the
-- three new columns are nullable (every existing row keeps NULL). Nothing
-- replays the table and no learner scoring reads it (no successor).
CREATE TABLE apply_intents__255 (
  id TEXT PRIMARY KEY,
  proposed_patch_id TEXT NOT NULL,
  item_ids_json TEXT NOT NULL,       -- accepted closure item ids, in apply order
  targets_json TEXT NOT NULL,        -- [{rel_path, pre_hash, post_content, post_hash}]
  db_plan_json TEXT NOT NULL,        -- per-item change batch / content event / links
  status TEXT NOT NULL DEFAULT 'pending' CHECK (
    status IN ('pending', 'applied', 'rolled_back', 'conflicted', 'set_aside')
  ),
  created_at TEXT NOT NULL,
  applied_at TEXT,
  rolled_back_at TEXT,
  conflict_json TEXT,                -- [{rel_path, pre_hash, post_hash, found_hash}] when conflicted
  conflicted_at TEXT,
  set_aside_at TEXT
);

INSERT INTO apply_intents__255(
  id, proposed_patch_id, item_ids_json, targets_json, db_plan_json, status,
  created_at, applied_at, rolled_back_at
)
SELECT
  id, proposed_patch_id, item_ids_json, targets_json, db_plan_json, status,
  created_at, applied_at, rolled_back_at
FROM apply_intents;

DROP TABLE apply_intents;

ALTER TABLE apply_intents__255 RENAME TO apply_intents;

CREATE INDEX idx_apply_intents_status ON apply_intents(status);
