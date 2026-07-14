-- KM1 (source-ingestion §10.2, knowledge-model §12): proposal dependency graph
-- and the expanded item-type vocabulary. Expanding the closed item_type /
-- target_entity_type CHECK constraints requires the SQLite table-rebuild dance
-- (CREATE new -> copy -> drop -> rename), mirroring migration 002.

PRAGMA foreign_keys = OFF;

DROP INDEX IF EXISTS idx_proposed_patch_items_decision;

CREATE TABLE proposed_patch_items_new (
  id TEXT PRIMARY KEY,
  proposed_patch_id TEXT NOT NULL REFERENCES proposed_patches(id) ON DELETE CASCADE,
  client_item_id TEXT NOT NULL,
  item_type TEXT NOT NULL CHECK (
    item_type IN (
      'learning_object', 'practice_item', 'concept', 'concept_edge', 'rubric', 'error_type',
      'facet', 'task_blueprint', 'provenance_link', 'notation_mapping', 'source_conflict'
    )
  ),
  operation TEXT NOT NULL CHECK (operation IN ('create', 'update', 'deactivate')),
  target_entity_type TEXT CHECK (
    target_entity_type IS NULL OR
    target_entity_type IN (
      'learning_object', 'practice_item', 'concept', 'concept_edge', 'rubric', 'error_type',
      'facet', 'task_blueprint', 'provenance_link', 'notation_mapping', 'source_conflict'
    )
  ),
  target_entity_id TEXT,
  payload_json TEXT NOT NULL,
  edited_payload_json TEXT,
  decision TEXT NOT NULL CHECK (decision IN ('pending', 'accepted', 'rejected')),
  validation_status TEXT NOT NULL CHECK (validation_status IN ('valid', 'warning', 'invalid')),
  validation_errors_json TEXT,
  applied_change_batch_id TEXT,
  decided_at TEXT,
  decided_by TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  audit_json TEXT,
  source_ref_ids_json TEXT,
  dependency_status TEXT NOT NULL DEFAULT 'pending'
    CHECK (dependency_status IN ('pending', 'ready', 'blocked')),
  dependency_block_reason_json TEXT,
  UNIQUE (proposed_patch_id, client_item_id)
);

INSERT INTO proposed_patch_items_new(
  id, proposed_patch_id, client_item_id, item_type, operation,
  target_entity_type, target_entity_id, payload_json, edited_payload_json,
  decision, validation_status, validation_errors_json, applied_change_batch_id,
  decided_at, decided_by, created_at, updated_at, audit_json, source_ref_ids_json,
  dependency_status, dependency_block_reason_json
)
SELECT
  id, proposed_patch_id, client_item_id, item_type, operation,
  target_entity_type, target_entity_id, payload_json, edited_payload_json,
  decision, validation_status, validation_errors_json, applied_change_batch_id,
  decided_at, decided_by, created_at, updated_at, audit_json, source_ref_ids_json,
  'pending', NULL
FROM proposed_patch_items;

DROP TABLE proposed_patch_items;
ALTER TABLE proposed_patch_items_new RENAME TO proposed_patch_items;

CREATE INDEX idx_proposed_patch_items_decision
  ON proposed_patch_items(proposed_patch_id, decision);

CREATE TABLE proposed_patch_item_dependencies (
  proposed_patch_item_id TEXT NOT NULL
    REFERENCES proposed_patch_items(id) ON DELETE CASCADE,
  depends_on_patch_item_id TEXT NOT NULL
    REFERENCES proposed_patch_items(id) ON DELETE CASCADE,
  PRIMARY KEY (proposed_patch_item_id, depends_on_patch_item_id)
);
CREATE INDEX idx_proposed_patch_item_dependencies_dep
  ON proposed_patch_item_dependencies(depends_on_patch_item_id);

PRAGMA foreign_keys = ON;
