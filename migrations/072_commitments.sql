-- P1 step 1 (spec_p1_shared_substrate §3.1, §3.2): durable learner commitments,
-- immutable commitment versions + targets, and the commitment-level depth objects
-- (policy / envelope / milestone) that P0's goal_contracts envelope validation
-- plugs into. Net-new; commitments are SQLite-owned so they DO carry FKs among
-- themselves. Vault-owned ids (goal_id, target_ref) stay bare TEXT.
--
-- Migration numbering: highest applied on disk = 071 (probe robust cutover);
-- P1 starts at 072. Never edit applied migrations 065-071.
--
-- Depth objects are declared before commitment_versions because commitment_versions
-- FK-references them (connect() runs PRAGMA foreign_keys = ON; DDL forward refs are
-- harmless but referenced rows must exist before any INSERT).

CREATE TABLE depth_policy_versions (
  id TEXT PRIMARY KEY,
  policy TEXT NOT NULL CHECK (policy IN
    ('hold_at_target', 'suggest_next', 'auto_within_envelope')),
  body_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(content_hash)
);

CREATE TABLE depth_envelope_versions (
  id TEXT PRIMARY KEY,
  envelope_version TEXT NOT NULL,
  -- capabilities, task-feature bounds, scaffold fade, tool/time tightening,
  -- cumulative burden (§3.1.1).
  bounds_json TEXT NOT NULL,
  -- ordered DAG of reviewed milestone edges (§3.1.1).
  reviewed_edges_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(content_hash)
);

CREATE TABLE depth_milestone_versions (
  id TEXT PRIMARY KEY,
  envelope_version_id TEXT NOT NULL
    REFERENCES depth_envelope_versions(id) ON DELETE CASCADE,
  milestone_slug TEXT NOT NULL,
  task_contract_json TEXT NOT NULL,
  entry_evidence_json TEXT,
  exit_evidence_json TEXT,
  fresh_proof_json TEXT,
  expected_burden_json TEXT,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_depth_milestone_envelope ON depth_milestone_versions(envelope_version_id);

CREATE TABLE commitments (
  id TEXT PRIMARY KEY,
  learner_id TEXT NOT NULL DEFAULT 'local',
  created_action TEXT NOT NULL CHECK (created_action IN
    ('help_me_remember', 'test_me_later', 'select_exemplar', 'create_quest')),
  -- idempotency key (§3.1): learner + normalized target set + action + client key.
  -- NULL when the caller supplied no client key (then a matching commitment is a
  -- merge candidate, never a silent merge).
  idempotency_key TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_commitments_learner_action ON commitments(learner_id, created_action);

CREATE TABLE commitment_versions (
  id TEXT PRIMARY KEY,
  commitment_id TEXT NOT NULL REFERENCES commitments(id) ON DELETE CASCADE,
  version INTEGER NOT NULL CHECK (version >= 1),
  predecessor_version_id TEXT REFERENCES commitment_versions(id),
  intent_text TEXT NOT NULL,
  interpretation_text TEXT,
  goal_id TEXT,                                   -- vault-owned, bare TEXT
  depth_preset TEXT NOT NULL CHECK (depth_preset IN
    ('keep_in_touch', 'remember_key_ideas', 'work_fluently', 'master_tasks_like_these')),
  depth_policy_version_id TEXT REFERENCES depth_policy_versions(id),
  depth_envelope_version_id TEXT REFERENCES depth_envelope_versions(id),
  attention_bounds_json TEXT,
  due_hint TEXT,
  hiatus_hint TEXT,
  reason TEXT,
  provenance_json TEXT,
  target_set_hash TEXT NOT NULL,
  version_hash TEXT NOT NULL,
  change_reason TEXT,
  author TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(commitment_id, version),
  UNIQUE(commitment_id, version_hash)
);
CREATE INDEX idx_commitment_versions_commitment ON commitment_versions(commitment_id, version);

CREATE TABLE commitment_events (
  id TEXT PRIMARY KEY,
  commitment_id TEXT NOT NULL REFERENCES commitments(id) ON DELETE CASCADE,
  commitment_version_id TEXT REFERENCES commitment_versions(id),
  kind TEXT NOT NULL CHECK (kind IN (
    'created', 'version_appended', 'disposition_changed', 'depth_policy_changed',
    'depth_envelope_changed', 'depth_milestone_reached', 'depth_transition_committed',
    'target_added', 'target_removed', 'family_attached', 'family_detached',
    'paused', 'resumed', 'retired')),
  detail_json TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_commitment_events_commitment ON commitment_events(commitment_id, created_at);

CREATE TABLE commitment_target_versions (
  id TEXT PRIMARY KEY,
  commitment_version_id TEXT NOT NULL
    REFERENCES commitment_versions(id) ON DELETE CASCADE,
  target_kind TEXT NOT NULL CHECK (target_kind IN (
    'p0_target_exemplar', 'canonical_facet', 'learning_object',
    'source_locator', 'legacy_practice_item')),
  target_ref TEXT NOT NULL,                       -- kind-specific id, bare TEXT
  salience REAL,
  role TEXT NOT NULL CHECK (role IN ('required', 'optional')),
  provenance_json TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_ctv_version ON commitment_target_versions(commitment_version_id);
