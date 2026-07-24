-- P0b authoring honesty (§5.7): an attempted PracticeItem is superseded by a
-- newly-authored item and immutable contract snapshot. Historical observations
-- may be reinterpreted only by an explicitly named projection version.
CREATE TABLE measurement_contract_corrections (
  id TEXT PRIMARY KEY,
  correction_set_id TEXT NOT NULL,
  source_practice_item_id TEXT NOT NULL,
  source_contract_version_id TEXT NOT NULL
    REFERENCES assessment_contract_versions(id),
  corrected_practice_item_id TEXT NOT NULL,
  corrected_contract_version_id TEXT NOT NULL
    REFERENCES assessment_contract_versions(id),
  consuming_projection_version TEXT NOT NULL,
  historical_evidence_policy TEXT NOT NULL
    CHECK (historical_evidence_policy IN ('preserve_original', 'reinterpret_measurement')),
  reason TEXT NOT NULL,
  correction_json TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(source_contract_version_id, consuming_projection_version)
);

CREATE INDEX idx_measurement_contract_corrections_source_item
  ON measurement_contract_corrections(source_practice_item_id, created_at, id);
CREATE INDEX idx_measurement_contract_corrections_projection
  ON measurement_contract_corrections(
    source_contract_version_id, consuming_projection_version
  );

-- Corrections are audit events, never mutable state.
CREATE TRIGGER measurement_contract_corrections_no_update
BEFORE UPDATE ON measurement_contract_corrections
BEGIN
  SELECT RAISE(ABORT, 'measurement contract corrections are append-only');
END;

CREATE TRIGGER measurement_contract_corrections_no_delete
BEFORE DELETE ON measurement_contract_corrections
BEGIN
  SELECT RAISE(ABORT, 'measurement contract corrections are append-only');
END;

-- Migration 115 used `misconceptions.status = resolved` as the only
-- backwards-compatible way to remove an invalid first-error promotion from
-- legacy active-state queries. Record its actual lifecycle meaning separately:
-- the learner did not learn it; the diagnosis was demoted. This event stream is
-- the semantic authority and leaves the original row/audit trace intact.
CREATE TABLE misconception_disposition_events (
  id TEXT PRIMARY KEY,
  misconception_id TEXT NOT NULL REFERENCES misconceptions(id),
  disposition TEXT NOT NULL CHECK (disposition IN ('demoted', 'superseded')),
  reason TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX idx_misconception_disposition_events_case
  ON misconception_disposition_events(misconception_id, created_at, id);

INSERT INTO misconception_disposition_events(
  id, misconception_id, disposition, reason, created_at
)
SELECT
  'demotion_' || id,
  id,
  'demoted',
  'first_error_trace_had_no_durable_promotion_authority',
  COALESCE(resolved_at, updated_at, created_at, '1970-01-01T00:00:00Z')
FROM misconceptions
WHERE promotion_reason = 'demoted_first_error_trace'
  AND NOT EXISTS (
    SELECT 1
    FROM misconception_disposition_events d
    WHERE d.misconception_id = misconceptions.id
      AND d.disposition = 'demoted'
  );

CREATE TRIGGER misconception_disposition_events_no_update
BEFORE UPDATE ON misconception_disposition_events
BEGIN
  SELECT RAISE(ABORT, 'misconception dispositions are append-only');
END;

CREATE TRIGGER misconception_disposition_events_no_delete
BEFORE DELETE ON misconception_disposition_events
BEGIN
  SELECT RAISE(ABORT, 'misconception dispositions are append-only');
END;
