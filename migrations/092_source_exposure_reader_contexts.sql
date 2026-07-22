-- P3 slice 1 (spec_p3_reader_integration §2 exposure row, §13.1.6; design B 092).
-- Extend source_exposure_events.context with the reader + restoration contexts so
-- render-view opens and post-cold restoration record exposure through the same
-- closed CHECK, temp-then-rename per the 049/052/058 precedent. Every historical
-- row/id is preserved verbatim (§15.10: no migration alters legacy ids). Column
-- set reproduced verbatim from migration 058 plus the two new context values.

PRAGMA foreign_keys=OFF;

CREATE TABLE source_exposure_events__092 (
  id TEXT PRIMARY KEY,
  context TEXT NOT NULL
    CHECK (context IN (
      'provenance', 'gate_diagnostic', 'registry_review', 'library', 'other',
      'tutor_citation', 'provenance_panel', 'conflict_review', 'remediation',
      -- P3 reader contexts:
      'reader', 'reader_restoration'
    )),
  extraction_id TEXT NOT NULL,
  span_id TEXT NOT NULL,
  revision_id TEXT,
  source_id TEXT,
  entity_type TEXT,
  entity_id TEXT,
  page INTEGER,
  locator TEXT,
  section_path_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL
);

INSERT INTO source_exposure_events__092 (
  id, context, extraction_id, span_id, revision_id, source_id,
  entity_type, entity_id, page, locator, section_path_json, created_at
)
SELECT
  id, context, extraction_id, span_id, revision_id, source_id,
  entity_type, entity_id, page, locator, section_path_json, created_at
FROM source_exposure_events;

DROP TABLE source_exposure_events;
ALTER TABLE source_exposure_events__092 RENAME TO source_exposure_events;

-- Restore the two indexes the temp-then-rename dropped (per 052/058 precedent).
CREATE INDEX idx_source_exposure_events_span ON source_exposure_events(extraction_id, span_id);
CREATE INDEX idx_source_exposure_events_entity ON source_exposure_events(entity_type, entity_id);

PRAGMA foreign_keys=ON;
