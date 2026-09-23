ALTER TABLE practice_attempts ADD COLUMN collection_version TEXT NOT NULL DEFAULT 'legacy-unversioned';
ALTER TABLE practice_attempts ADD COLUMN entry_surface TEXT NOT NULL DEFAULT 'unknown';
ALTER TABLE practice_attempts ADD COLUMN evidence_origin TEXT NOT NULL DEFAULT 'unknown';
ALTER TABLE scheduler_slates ADD COLUMN collection_version TEXT NOT NULL DEFAULT 'legacy-unversioned';
ALTER TABLE scheduler_slate_candidates ADD COLUMN propensity_kind TEXT NOT NULL DEFAULT 'legacy-unverified';
CREATE TABLE scheduler_offer_receipts (
  slate_id TEXT PRIMARY KEY REFERENCES scheduler_slates(id),
  returned_candidate_ids_json TEXT NOT NULL,
  entry_surface TEXT NOT NULL,
  collection_version TEXT NOT NULL DEFAULT 'learnloop-events-v1',
  created_at TEXT NOT NULL
);
CREATE TABLE submission_intents (
  submission_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id),
  practice_item_id TEXT NOT NULL,
  scheduler_candidate_id TEXT REFERENCES scheduler_slate_candidates(id),
  entry_surface TEXT NOT NULL,
  viewing_status TEXT NOT NULL DEFAULT 'unknown',
  collection_version TEXT NOT NULL DEFAULT 'learnloop-events-v1',
  created_at TEXT NOT NULL
);
CREATE TRIGGER scheduler_offer_receipts_immutable_update BEFORE UPDATE ON scheduler_offer_receipts
BEGIN SELECT RAISE(ABORT, 'scheduler offer receipts are immutable'); END;
CREATE TRIGGER scheduler_offer_receipts_immutable_delete BEFORE DELETE ON scheduler_offer_receipts
BEGIN SELECT RAISE(ABORT, 'scheduler offer receipts are immutable'); END;
CREATE TRIGGER submission_intents_immutable_update BEFORE UPDATE ON submission_intents
BEGIN SELECT RAISE(ABORT, 'submission intents are immutable'); END;
CREATE TRIGGER submission_intents_immutable_delete BEFORE DELETE ON submission_intents
BEGIN SELECT RAISE(ABORT, 'submission intents are immutable'); END;
CREATE TRIGGER decision_features_immutable_update BEFORE UPDATE ON decision_features
BEGIN SELECT RAISE(ABORT, 'decision features are immutable'); END;
CREATE TRIGGER decision_features_immutable_delete BEFORE DELETE ON decision_features
BEGIN SELECT RAISE(ABORT, 'decision features are immutable'); END;
