-- P1 step 4 (spec_p1_shared_substrate §3.7, §3.8): durable card-lineage identity,
-- the richer lineage edge vocabulary, and authoritative card-level scheduling state.
--
-- The P0 (migration 065) activity_card_versions row carries only a 2-value
-- lineage_kind CHECK ('minor_successor','fork') and a bare predecessor id. P1 adds
-- the DURABLE card_lineage identity (§3.7) plus the append-only richer edge vocab
-- (minor_successor/semantic_fork/split_from/merged_from) in a NEW edge table --
-- the 065 immutable rows are never altered (owner decision A.1).
--
-- activity_card_state is keyed by learner x card lineage x scheduler algorithm
-- version (§3.8): a surface never owns FSRS state; minor successors resolve to the
-- same lineage state; forks start a new row with no inherited certification/stability.
-- The legacy practice_item_state (migration 001) becomes a compatibility PROJECTION
-- materialized one-way from this authoritative state during dual-write (§3.8, §7.2).
--
-- Migration numbering: highest applied on disk = 074 (activity contract extensions);
-- P1 step 4 starts at 075. Never edit applied migrations 065-074.

CREATE TABLE card_lineages (
  id TEXT PRIMARY KEY,
  family_id TEXT REFERENCES activity_families(id),
  -- The card whose executable contract this lineage tracks (§3.7). Bare-ish: FKs the
  -- 065 card identity, not a card version (versions live along the lineage edges).
  card_id TEXT REFERENCES activity_cards(id),
  created_at TEXT NOT NULL
);
CREATE INDEX idx_card_lineages_family ON card_lineages(family_id);
CREATE INDEX idx_card_lineages_card ON card_lineages(card_id);

CREATE TABLE card_lineage_edges (
  id TEXT PRIMARY KEY,
  lineage_id TEXT NOT NULL REFERENCES card_lineages(id) ON DELETE CASCADE,
  -- NULL from_ for the lineage's genesis version.
  from_card_version_id TEXT REFERENCES activity_card_versions(id),
  to_card_version_id TEXT NOT NULL REFERENCES activity_card_versions(id),
  edge_kind TEXT NOT NULL CHECK (edge_kind IN (
    'minor_successor', 'semantic_fork', 'split_from', 'merged_from')),
  classifier_version TEXT NOT NULL,
  rationale_json TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_cle_lineage ON card_lineage_edges(lineage_id, created_at);
CREATE INDEX idx_cle_to_version ON card_lineage_edges(to_card_version_id);

CREATE TABLE activity_card_state (
  id TEXT PRIMARY KEY,
  learner_id TEXT NOT NULL DEFAULT 'local',
  card_lineage_id TEXT NOT NULL REFERENCES card_lineages(id) ON DELETE CASCADE,
  scheduler_algorithm_version TEXT NOT NULL,
  -- FSRS is permitted only for stable literal-recall-like contracts (§3.8); other
  -- P1 cards carry a card-level projection labelled provisional_stage_v1 -- NEVER
  -- mislabelled as an FSRS retention estimate.
  model_label TEXT NOT NULL CHECK (model_label IN ('fsrs', 'provisional_stage_v1')),
  difficulty REAL,
  stability REAL,
  retrievability REAL,
  due_at TEXT,
  last_eligible_review_at TEXT,
  lapse_episode_id TEXT,
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
  -- Projection head (§3.8): the rebuildable summary, so a corrupted legacy cache
  -- never alters an authoritative rebuild (§9.5).
  projection_head_json TEXT,
  updated_at TEXT NOT NULL,
  UNIQUE(learner_id, card_lineage_id, scheduler_algorithm_version)
);
CREATE INDEX idx_acs_lineage ON activity_card_state(card_lineage_id);
