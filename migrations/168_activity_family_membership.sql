-- Authored family identity remains activity_families; regrouping never edits cards.
CREATE TABLE family_proposals (
  id TEXT PRIMARY KEY,
  family_id TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('applying','applied','undoing','undone','rejected')),
  plan_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE activity_family_membership_events (
  -- Deletion is forbidden, so ordinary rowid allocation is monotone without
  -- introducing sqlite_sequence into every formerly unchanged no-family vault.
  seq INTEGER PRIMARY KEY,
  id TEXT NOT NULL UNIQUE,
  family_id TEXT NOT NULL REFERENCES activity_families(id),
  card_id TEXT NOT NULL REFERENCES activity_cards(id),
  practice_item_id TEXT NOT NULL,
  variant_relation TEXT NOT NULL CHECK(variant_relation IN ('same_target','isomorph','near','far')),
  action TEXT NOT NULL CHECK(action IN ('add','remove')),
  proposal_id TEXT NOT NULL,
  judgment_id TEXT NOT NULL REFERENCES judgment_ledger(id),
  created_at TEXT NOT NULL,
  UNIQUE(proposal_id,card_id,action)
);
CREATE INDEX idx_family_membership_card ON activity_family_membership_events(card_id,seq);
-- REPLACE deletes do not fire DELETE triggers with recursive_triggers=OFF.
CREATE TRIGGER family_membership_no_replace BEFORE INSERT ON activity_family_membership_events
WHEN EXISTS (
  SELECT 1 FROM activity_family_membership_events
  WHERE seq=NEW.seq OR id=NEW.id
     OR (proposal_id=NEW.proposal_id AND card_id=NEW.card_id AND action=NEW.action)
)
BEGIN SELECT RAISE(ABORT,'family membership events are append-only'); END;
CREATE TRIGGER family_membership_no_update BEFORE UPDATE ON activity_family_membership_events
BEGIN SELECT RAISE(ABORT,'family membership events are append-only'); END;
CREATE TRIGGER family_membership_no_delete BEFORE DELETE ON activity_family_membership_events
BEGIN SELECT RAISE(ABORT,'family membership events are append-only'); END;
CREATE TABLE family_memory_state (
  family_id TEXT PRIMARY KEY REFERENCES activity_families(id),
  difficulty REAL NOT NULL,
  stability REAL NOT NULL,
  retrievability REAL NOT NULL,
  last_review_at TEXT NOT NULL,
  review_count INTEGER NOT NULL CHECK(review_count > 0),
  weights_hash TEXT NOT NULL,
  projection_version TEXT NOT NULL
);
