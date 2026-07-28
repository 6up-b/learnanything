-- Diagnostic-surface replenishment needs (probe freshness rule).
--
-- A vault-authored `practice_mode: diagnostic_probe` item is a single-use
-- surface: one administration consumes it (attempt recording deactivates the
-- item) because re-serving would conflate memorization of the question with
-- understanding of what it examines. Consumption therefore creates a supply
-- gap: nothing replenished the learning object's diagnostic coverage.
--
-- This mirrors the probe-time `probe_generation_needs` machinery (migration
-- 028) and the synthesis-scoped `synthesis_generation_needs` (migration 045),
-- but is consumption-scoped: there is no probe episode, the trigger is the one
-- administration of a durable diagnostic surface. Needs are DERIVED from
-- attempts + item state by an idempotent reconciliation sweep
-- (`services/diagnostic_surface_supply.py`), deduplicated on the consumed
-- surface, so replay order does not matter and re-running the sweep is a no-op.

CREATE TABLE diagnostic_surface_generation_needs (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT NOT NULL,
  consumed_practice_item_id TEXT NOT NULL,  -- the administered single-use surface
  target_key TEXT NOT NULL,                 -- facet signature the replacement must cover
  missing_capability TEXT NOT NULL,         -- 'diagnostic_probe_surface'
  facet_ids_json TEXT NOT NULL DEFAULT '[]',
  misconception_ids_json TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL CHECK (status IN ('pending', 'resolved', 'declined')),
  created_at TEXT NOT NULL,
  resolved_at TEXT,
  UNIQUE (consumed_practice_item_id)
);

CREATE INDEX idx_diagnostic_surface_needs_lo
  ON diagnostic_surface_generation_needs(learning_object_id, status);
