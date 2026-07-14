-- Typed learner-facing claim presentations and raw response telemetry.
-- Presentation rows are append-only; response/dismissal rows point back to the
-- exact presentation whose rendered value the learner saw.
CREATE TABLE hypothesis_events (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  presentation_id TEXT REFERENCES hypothesis_events(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL CHECK (event_type IN ('presented', 'responded', 'dismissed')),
  claim_class TEXT NOT NULL CHECK (claim_class IN ('estimate', 'diagnosis', 'policy', 'ledger_fact')),
  claim_type TEXT NOT NULL,
  claim_ref TEXT NOT NULL,
  claim_version TEXT NOT NULL,
  producer_version TEXT NOT NULL,
  surface TEXT NOT NULL,
  temperature TEXT NOT NULL CHECK (temperature IN ('hot', 'cold')),
  visible_at TEXT,
  suppression_reason TEXT,
  response_payload_json TEXT,
  session_id TEXT,
  visit_id TEXT,
  CHECK (
    (event_type = 'presented' AND presentation_id IS NULL)
    OR (event_type IN ('responded', 'dismissed') AND presentation_id IS NOT NULL)
  ),
  CHECK (event_type = 'responded' OR response_payload_json IS NULL)
);

CREATE INDEX idx_hypothesis_events_presentation
  ON hypothesis_events(presentation_id, created_at);
CREATE INDEX idx_hypothesis_events_claim
  ON hypothesis_events(claim_ref, claim_version, surface, created_at);
CREATE INDEX idx_hypothesis_events_session
  ON hypothesis_events(session_id, event_type, created_at);
CREATE INDEX idx_hypothesis_events_visit
  ON hypothesis_events(visit_id, event_type, created_at);
