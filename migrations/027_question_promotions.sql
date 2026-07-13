-- Promote Socratic tutor questions to practice items / learning objects
-- (spec_tutor_promotion.md §5). Adds the question_promotions ledger, a
-- persistent saved-note back-link on question_events, and extends two CHECK
-- constraints (learner_claims.source, decision_features.decision_type) via the
-- SQLite table-rebuild pattern (004/012/018/022 precedent — SQLite cannot
-- alter a CHECK in place).
PRAGMA foreign_keys = OFF;

-- question_promotions: one row per promoted tutor turn. PK on the event id
-- makes the pipeline idempotent (a second promote returns the existing row).
CREATE TABLE question_promotions (
  question_event_id TEXT PRIMARY KEY REFERENCES question_events(id) ON DELETE CASCADE,
  intent TEXT NOT NULL CHECK (intent IN ('practice', 'gap')),
  attributed_facets_json TEXT,        -- PromotionAnalysis output
  question_nature TEXT CHECK (question_nature IN
    ('core_recall','mechanism','transfer','edge_case','what_if')
    OR question_nature IS NULL),
  attempted_in_thread INTEGER,        -- PromotionAnalysis output (nullable bool)
  learner_claim_id TEXT,              -- gap route: the self_rating claim written
  intervention_need_id TEXT,          -- gap route: the filed need
  proposed_patch_id TEXT,             -- practice route (gap route's patch comes via the need)
  saved_note_id TEXT,                 -- grounding note (reused or created)
  existing_practice_item_id TEXT,     -- dedup route: promotion resolved to an existing item
  created_practice_item_id TEXT,      -- filled when applied
  created_learning_object_id TEXT,    -- filled when a new LO was applied
  route TEXT NOT NULL CHECK (route IN
    ('auto_apply', 'review_required', 'diagnostic_pending', 'existing_item')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- Requested-items scheduling floor (§4a) and question-signal join (§3 G2) both
-- select promotions by the practice item they point at.
CREATE INDEX idx_question_promotions_created_item
  ON question_promotions(created_practice_item_id);
CREATE INDEX idx_question_promotions_existing_item
  ON question_promotions(existing_practice_item_id);

-- Persist the tutor-turn -> saved-note link so the "saved" UI state survives a
-- remount and get_tutor_transcript can surface it (§5). save_tutor_answer_note
-- now writes this column.
ALTER TABLE question_events ADD COLUMN saved_note_id TEXT;

-- Rebuild learner_claims to extend the source CHECK with the gap-declaration
-- self-report source (§3 G2). All columns/rows preserved.
CREATE TABLE learner_claims_new (
  id TEXT PRIMARY KEY,
  claim_type TEXT NOT NULL CHECK (
    claim_type IN ('background_familiarity', 'prior_coursework', 'self_rating')
  ),
  scope_type TEXT NOT NULL CHECK (
    scope_type IN ('concept', 'learning_object', 'subject', 'domain', 'global')
  ),
  scope_id TEXT,
  evidence_family TEXT,
  claimed_level REAL NOT NULL CHECK (claimed_level >= 0.0 AND claimed_level <= 1.0),
  prior_pseudo_count REAL NOT NULL CHECK (prior_pseudo_count >= 0.0),
  source TEXT NOT NULL CHECK (
    source IN ('init_wizard', 'manual_cli', 'imported', 'tutor_gap_declaration')
  ),
  created_at TEXT NOT NULL
);

INSERT INTO learner_claims_new(
  id, claim_type, scope_type, scope_id, evidence_family, claimed_level,
  prior_pseudo_count, source, created_at
)
SELECT
  id, claim_type, scope_type, scope_id, evidence_family, claimed_level,
  prior_pseudo_count, source, created_at
FROM learner_claims;

DROP TABLE learner_claims;
ALTER TABLE learner_claims_new RENAME TO learner_claims;

-- Rebuild decision_features to extend the decision_type CHECK with
-- 'question_promotion' (§5; the promotion decision_features insert would
-- otherwise throw). Mirrors the 012 rebuild — preserve all columns and the
-- UNIQUE(decision_id, decision_type) constraint.
CREATE TABLE decision_features_new (
  id TEXT PRIMARY KEY,
  decision_id TEXT NOT NULL,
  decision_type TEXT NOT NULL CHECK (
    decision_type IN ('selection', 'probe', 'grading', 'followup', 'question_promotion')
  ),
  ability_vector_json TEXT NOT NULL,
  item_demand_vector_json TEXT,
  context_json TEXT,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (decision_id, decision_type)
);

INSERT INTO decision_features_new(
  id, decision_id, decision_type, ability_vector_json, item_demand_vector_json,
  context_json, algorithm_version, created_at
)
SELECT
  id, decision_id, decision_type, ability_vector_json, item_demand_vector_json,
  context_json, algorithm_version, created_at
FROM decision_features;

DROP TABLE decision_features;
ALTER TABLE decision_features_new RENAME TO decision_features;

CREATE INDEX IF NOT EXISTS idx_decision_features_type_time
  ON decision_features(decision_type, created_at);

PRAGMA foreign_keys = ON;
