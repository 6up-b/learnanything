-- Content-addressed copy of every practice-item revision the scheduler scored.
-- Selection decision features reference the item by content_hash (SHA-256 of
-- item_json exactly), and the vault keeps only the current revision, so this
-- is the only record of the text behind an older decision. Written with
-- INSERT OR IGNORE: one row per distinct revision, never per candidate.
CREATE TABLE practice_item_snapshots (
  content_hash TEXT PRIMARY KEY,
  practice_item_id TEXT NOT NULL,
  item_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX practice_item_snapshots_item ON practice_item_snapshots(practice_item_id);
CREATE TRIGGER practice_item_snapshots_immutable_update BEFORE UPDATE ON practice_item_snapshots
BEGIN SELECT RAISE(ABORT, 'practice item snapshots are immutable'); END;
CREATE TRIGGER practice_item_snapshots_immutable_delete BEFORE DELETE ON practice_item_snapshots
BEGIN SELECT RAISE(ABORT, 'practice item snapshots are immutable'); END;

-- attempt_id deliberately has no foreign key: like the other append-only
-- ledgers, the table must stay outside the practice_attempts FK graph that
-- scratch replays walk when they truncate attempts, because its no-delete
-- trigger would abort that walk. record_false_remediation checks the attempt.
-- SQLite cannot drop a foreign key in place, so the table is rebuilt with
-- every row and id preserved (150/153 precedent); DROP TABLE removes the old
-- index and triggers, which are recreated on the renamed table.
PRAGMA foreign_keys = OFF;

CREATE TABLE false_remediation_adjudications__164 (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL,
  label_value INTEGER NOT NULL CHECK(label_value IN (0,1)),
  evidence_refs_json TEXT NOT NULL,
  author_kind TEXT NOT NULL CHECK(author_kind IN ('human','machine')),
  verifier_version TEXT NOT NULL,
  label_version TEXT NOT NULL,
  collection_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
INSERT INTO false_remediation_adjudications__164(
  id, attempt_id, label_value, evidence_refs_json, author_kind,
  verifier_version, label_version, collection_version, created_at
)
SELECT
  id, attempt_id, label_value, evidence_refs_json, author_kind,
  verifier_version, label_version, collection_version, created_at
FROM false_remediation_adjudications;

DROP TABLE false_remediation_adjudications;
ALTER TABLE false_remediation_adjudications__164 RENAME TO false_remediation_adjudications;

CREATE INDEX idx_false_remediation_attempt ON false_remediation_adjudications(attempt_id,created_at,id);
CREATE TRIGGER false_remediation_no_update BEFORE UPDATE ON false_remediation_adjudications
BEGIN SELECT RAISE(ABORT, 'false-remediation adjudications are append-only'); END;
CREATE TRIGGER false_remediation_no_delete BEFORE DELETE ON false_remediation_adjudications
BEGIN SELECT RAISE(ABORT, 'false-remediation adjudications are append-only'); END;

PRAGMA foreign_keys = ON;
