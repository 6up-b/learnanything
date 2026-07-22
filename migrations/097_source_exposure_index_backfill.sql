-- P3 follow-up: migration 092 rebuilt source_exposure_events (temp-then-rename)
-- but omitted the two indexes its predecessors (049/052/058) always restored,
-- so any vault that applied 092 before this fix is missing them. Recreate both
-- idempotently for already-migrated vaults; fresh vaults get them from 092.

CREATE INDEX IF NOT EXISTS idx_source_exposure_events_span
  ON source_exposure_events(extraction_id, span_id);
CREATE INDEX IF NOT EXISTS idx_source_exposure_events_entity
  ON source_exposure_events(entity_type, entity_id);
