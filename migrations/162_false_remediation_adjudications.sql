-- F is an explicit evidence-backed adjudication, never inferred from a later
-- successful answer. Corrections append a new adjudication and dataset version.
CREATE TABLE false_remediation_adjudications (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id),
  label_value INTEGER NOT NULL CHECK(label_value IN (0,1)),
  evidence_refs_json TEXT NOT NULL,
  author_kind TEXT NOT NULL CHECK(author_kind IN ('human','machine')),
  verifier_version TEXT NOT NULL,
  label_version TEXT NOT NULL,
  collection_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_false_remediation_attempt ON false_remediation_adjudications(attempt_id,created_at,id);
CREATE TRIGGER false_remediation_no_update BEFORE UPDATE ON false_remediation_adjudications
BEGIN SELECT RAISE(ABORT, 'false-remediation adjudications are append-only'); END;
CREATE TRIGGER false_remediation_no_delete BEFORE DELETE ON false_remediation_adjudications
BEGIN SELECT RAISE(ABORT, 'false-remediation adjudications are append-only'); END;
