-- Remediation passage DELIVERY telemetry (coldness receipts v2).
--
-- `remediation_episodes.passages_shown_json` records what a prescription
-- PREPARED, never what a surface showed, so the coldness receipt (migration
-- 149) had to classify every in-interval prescription as `indeterminate` and
-- leave `exposure_isolation` unknown. The repair overlay renders the prescribed
-- passage text inline the moment the prescribe response lands, so the honest
-- observable is DELIVERY: the sidecar handing the passage text to the surface
-- that renders it.
--
-- That is deliberately NOT the existing `remediation` context, which means the
-- learner clicked Open-in-source on a passage — a stronger claim than delivery.
-- A separate discriminator keeps the two apart in the ledger, so a receipt can
-- say "the passage text reached the screen" without pretending anyone chose to
-- open it. On-screen dwell stays unobserved and stays declared.
--
-- Expanding a closed CHECK requires the SQLite table-rebuild dance (mirrors
-- migrations 052 and 092); every historical row and id is preserved verbatim.

PRAGMA foreign_keys=OFF;

CREATE TABLE source_exposure_events__150 (
  id TEXT PRIMARY KEY,
  context TEXT NOT NULL
    CHECK (context IN (
      'provenance', 'gate_diagnostic', 'registry_review', 'library', 'other',
      'tutor_citation', 'provenance_panel', 'conflict_review', 'remediation',
      'reader', 'reader_restoration',
      -- Coldness receipts v2: prescribed passage text delivered for render.
      'remediation_delivery'
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

INSERT INTO source_exposure_events__150 (
  id, context, extraction_id, span_id, revision_id, source_id,
  entity_type, entity_id, page, locator, section_path_json, created_at
)
SELECT
  id, context, extraction_id, span_id, revision_id, source_id,
  entity_type, entity_id, page, locator, section_path_json, created_at
FROM source_exposure_events;

DROP TABLE source_exposure_events;
ALTER TABLE source_exposure_events__150 RENAME TO source_exposure_events;

-- Restore the indexes the temp-then-rename dropped (052/092 precedent).
CREATE INDEX idx_source_exposure_events_span ON source_exposure_events(extraction_id, span_id);
CREATE INDEX idx_source_exposure_events_entity ON source_exposure_events(entity_type, entity_id);

PRAGMA foreign_keys=ON;
