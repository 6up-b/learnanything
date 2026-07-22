-- P1 step 8 (spec_p1_shared_substrate §4.3, §5.4, §5.5, §5.7): angle inventories,
-- family evidence-cap policies, and durable lapse/retry episodes. These back the
-- within-family angle progression (§5.4 orthogonal-next), the family evidence cap
-- (§4.3 + owner decision A.4 tight-kinship clustering), and post-lapse linked
-- retries (§5.5). The one-edge depth-transition service (§5.7) reuses P0.4's
-- goal_contracts.append_authorized_depth_successor + P1 commitments/card lineage and
-- adds no schema of its own.
--
-- Migration numbering: highest applied on disk = 078 (surface mint jobs); P1 step 8
-- starts at 079. Never edit applied migrations.

CREATE TABLE angle_inventories (
  id TEXT PRIMARY KEY,
  family_version_id TEXT REFERENCES activity_family_versions(id),
  -- §5.4 coordinates: cue direction / response form / representation / operation /
  -- context / task span / transfer distance / scaffolding. A cosmetic paraphrase is
  -- the same angle; a new cognitive angle is a sibling card/branch.
  coordinates_json TEXT NOT NULL,
  coverage_targets_json TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_angle_inv_family ON angle_inventories(family_version_id);

CREATE TABLE family_evidence_cap_policies (
  id TEXT PRIMARY KEY,
  policy_slug TEXT NOT NULL,
  version INTEGER NOT NULL,
  -- caps: max effective independent mass per target x capability x angle neighborhood
  -- and the tight_kinship_threshold that defines a cluster (§4.3, A.4). Every numeric
  -- knob here is a registered heuristic decision parameter.
  caps_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(policy_slug, version)
);

CREATE TABLE lapse_episodes (
  id TEXT PRIMARY KEY,
  card_lineage_id TEXT NOT NULL REFERENCES card_lineages(id),
  learner_id TEXT NOT NULL DEFAULT 'local',
  opened_administration_id TEXT,
  -- §5.5: a failed eligible practice administration opens a durable lapse. Same-session
  -- retries are LINKED observations that never overwrite the original failure; before
  -- give_up they update a derived retrievability but stack no independent evidence.
  status TEXT NOT NULL CHECK (status IN ('open', 'given_up', 'recovered')),
  retry_observations_json TEXT,
  derived_retrievability REAL,
  followup_due_at TEXT,
  opened_at TEXT NOT NULL,
  closed_at TEXT
);
CREATE INDEX idx_lapse_lineage ON lapse_episodes(card_lineage_id, status);
