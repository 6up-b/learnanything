-- P0.4 (spec_p0_measurement_correctness §3.4, §4.5, §7.3, §9.4): terminal-contract
-- versions, the head projection, non-pinnable drafts, and the probe-episode target
-- pin. SQLite is authoritative for confirmed versions + consumer pins; goals.yaml
-- keeps the pre-confirmation draft + a controlled-writer mirror of the head id.
-- IMMUTABLE: a confirmed goal_contract_versions row is never UPDATEd -- every
-- material edit APPENDS a successor. Purely additive except two nullable
-- ALTER TABLE ADD COLUMN on probe_episodes (byte-safe under legacy replay, same
-- pattern as 034/059). Vault-owned goal_id/edge ids are bare TEXT (no FK target).

------------------------------------------------------------------------------
-- goal_contract_versions (§3.4): the confirmed terminal-contract version ledger.
-- A consumer pins one row's id. content_hash is the _canonical_hash over the whole
-- contract body; support_hash the _canonical_hash over the support-bearing subset
-- (§2.4) -- support_change/authorized_depth_step change it, other classes do not.
------------------------------------------------------------------------------
CREATE TABLE goal_contract_versions (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  version INTEGER NOT NULL CHECK (version >= 1),
  predecessor_version_id TEXT REFERENCES goal_contract_versions(id),
  contract_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  support_hash TEXT NOT NULL,
  contract_schema_version INTEGER NOT NULL,
  change_class TEXT NOT NULL CHECK (change_class IN (
    'confirm', 'support_change', 'authorized_depth_step',
    'evaluation_change', 'reweight', 'metadata'
  )),
  -- authorized_depth_step receipt columns (§3.4); NULL for every other class:
  envelope_version TEXT,
  predecessor_milestone TEXT,
  activated_edge_id TEXT,
  evidence_receipt_json TEXT,
  burden_delta_json TEXT,
  author TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(goal_id, version),
  UNIQUE(goal_id, content_hash)
);
CREATE INDEX idx_gcv_goal ON goal_contract_versions(goal_id);
CREATE INDEX idx_gcv_support ON goal_contract_versions(goal_id, support_hash);

------------------------------------------------------------------------------
-- goal_contract_heads (§3.4): the current-head projection. One row per goal,
-- rewritten on every appended successor (a derived projection, not raw history,
-- so it is safe to UPDATE -- unlike the immutable version rows).
------------------------------------------------------------------------------
CREATE TABLE goal_contract_heads (
  goal_id TEXT PRIMARY KEY,
  head_version_id TEXT NOT NULL REFERENCES goal_contract_versions(id),
  head_version INTEGER NOT NULL,
  head_content_hash TEXT NOT NULL,
  head_support_hash TEXT NOT NULL,
  head_envelope_version TEXT,
  updated_at TEXT NOT NULL
);

------------------------------------------------------------------------------
-- goal_contract_drafts (§3.4): non-pinnable proposals. A rejected
-- append_authorized_depth_successor or a pre-confirmation body lands here. No
-- version id, no head row -> the type-level guarantee a draft cannot be pinned.
------------------------------------------------------------------------------
CREATE TABLE goal_contract_drafts (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  predecessor_version_id TEXT REFERENCES goal_contract_versions(id),
  proposed_contract_json TEXT NOT NULL,
  proposed_change_class TEXT,
  rejection_reason TEXT NOT NULL CHECK (rejection_reason IN (
    'outside_envelope', 'unreviewed_edge', 'stale_envelope',
    'predecessor_not_head', 'multiple_edges', 'insufficient_evidence',
    'pre_confirmation_draft'
  )),
  evidence_receipt_json TEXT,
  requires TEXT NOT NULL CHECK (requires IN (
    'learner_confirmed_envelope', 'learner_confirmed_successor', 'exemplar_and_blueprint'
  )),
  author TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_gcd_goal ON goal_contract_drafts(goal_id);

------------------------------------------------------------------------------
-- Probe-episode target pin (§3.4 "pin exact contract version at episode open").
-- Nullable; NULL for an ungoal-conditioned diagnostic probe (not a terminal
-- claim, invariant 9) and under legacy replay.
------------------------------------------------------------------------------
ALTER TABLE probe_episodes ADD COLUMN target_contract_version_id TEXT;
ALTER TABLE probe_episodes ADD COLUMN target_support_hash TEXT;
