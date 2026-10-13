-- Canonical sources S0 (spec_source_practice_and_probes_v1.md §6.5): find_practice
-- gets real callers. Receipts and append-only facts only: nothing here is
-- evidence, mastery, FSRS or scheduler state, and replay never reads it.

-- Who asked for a proposal and for what. `origin` keeps its closed CHECK
-- (rpc | cli | tool | api); the new callers are recorded here instead of in a
-- table rebuild. All nullable: rows written before S0 keep NULL.
ALTER TABLE practice_index_proposals ADD COLUMN caller TEXT;
ALTER TABLE practice_index_proposals ADD COLUMN caller_ref TEXT;
ALTER TABLE practice_index_proposals ADD COLUMN intent TEXT;

-- What reached the screen: one row per proposal candidate a surface rendered.
-- Retrieved, displayed and served stay three separate records (the proposal
-- row, this impression, the pick or attempt). Deliberately NOT
-- activity_exposure_events: `rendered` there is a once-ever burn boundary for
-- held-out use, and a glimpse in a strip must not burn a surface. Read only by
-- the exposure rule (an earlier impression of a prompt excludes it from the
-- independent intents within the cold retrieval delay) and by S5's records.
CREATE TABLE instructional_impressions (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  surface TEXT NOT NULL CHECK (surface IN ('tutor_strip', 'plan', 'dl3_box', 'reader', 'other')),
  caller_kind TEXT,
  caller_ref TEXT,
  proposal_id TEXT NOT NULL,
  candidate_kind TEXT NOT NULL CHECK (candidate_kind IN ('item', 'source_exercise')),
  practice_item_id TEXT,
  extraction_id TEXT,
  span_ids_json TEXT NOT NULL DEFAULT '[]',
  shown_fields_json TEXT NOT NULL,
  session_id TEXT,
  CHECK (
    (candidate_kind = 'item' AND practice_item_id IS NOT NULL)
    OR (candidate_kind = 'source_exercise' AND extraction_id IS NOT NULL)
  )
);
CREATE INDEX idx_instructional_impressions_item
  ON instructional_impressions(practice_item_id, created_at);
CREATE INDEX idx_instructional_impressions_extraction
  ON instructional_impressions(extraction_id, created_at);
CREATE INDEX idx_instructional_impressions_proposal
  ON instructional_impressions(proposal_id);
CREATE TRIGGER instructional_impressions_no_update BEFORE UPDATE ON instructional_impressions
BEGIN SELECT RAISE(ABORT, 'instructional impressions are append-only'); END;
CREATE TRIGGER instructional_impressions_no_delete BEFORE DELETE ON instructional_impressions
BEGIN SELECT RAISE(ABORT, 'instructional impressions are append-only'); END;
