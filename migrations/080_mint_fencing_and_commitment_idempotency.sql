-- P1 audit Wave B (B1, B2, B6). Two new-substrate-only concerns; both tables are
-- new-substrate-only, so a rebuild carries no durable-vault concern (standing owner
-- decision). Never edit applied migrations 065-079.
--
-- B6 commitment idempotency DB backstop (§3.1): a partial UNIQUE index enforces at
-- the storage layer that one (learner, action, client idempotency key) yields exactly
-- one commitment even under concurrent create_commitment races. NULL keys stay
-- distinct (an absent client key is a merge candidate, never a hard-unique row).
CREATE UNIQUE INDEX idx_commitments_idempotency
  ON commitments(learner_id, created_action, idempotency_key)
  WHERE idempotency_key IS NOT NULL;

-- B1 + B2 rebuild of surface_mint_requests:
--   * B2 anchor_surface_id becomes NOT NULL DEFAULT '' ('' sentinel), mirroring the
--     requested_angle_json fix, so the UNIQUE idempotency index treats "no anchor" as
--     ONE value (SQLite treats NULLs as distinct, which defeats the UNIQUE). The FK to
--     activity_surfaces is dropped: the '' sentinel has no matching surface row.
--   * B1 lease_epoch (fencing token): monotonically bumped on every claim. A late
--     write from a slow-but-alive worker whose lease expired (and the job was
--     re-claimed) carries a stale epoch and is rejected, so no double-admit.
CREATE TABLE surface_mint_requests_new (
  id TEXT PRIMARY KEY,
  card_version_id TEXT NOT NULL REFERENCES activity_card_versions(id),
  anchor_surface_id TEXT NOT NULL DEFAULT '',
  requested_angle_json TEXT NOT NULL DEFAULT '',
  generator_version TEXT NOT NULL,
  gate_policy_version TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
    'pending', 'running', 'candidate_ready', 'admitted', 'rejected', 'obsolete', 'failed')),
  lease_owner TEXT,
  lease_expires_at TEXT,
  lease_epoch INTEGER NOT NULL DEFAULT 0,
  candidate_surface_id TEXT REFERENCES activity_surfaces(id),
  gate_results_json TEXT,
  token_cost_json TEXT,
  failure_reason TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(card_version_id, anchor_surface_id, requested_angle_json,
         generator_version, gate_policy_version)
);

INSERT INTO surface_mint_requests_new(
  id, card_version_id, anchor_surface_id, requested_angle_json, generator_version,
  gate_policy_version, status, lease_owner, lease_expires_at, lease_epoch,
  candidate_surface_id, gate_results_json, token_cost_json, failure_reason,
  created_at, updated_at
)
SELECT
  id, card_version_id, COALESCE(anchor_surface_id, ''), requested_angle_json,
  generator_version, gate_policy_version, status, lease_owner, lease_expires_at, 0,
  candidate_surface_id, gate_results_json, token_cost_json, failure_reason,
  created_at, updated_at
FROM surface_mint_requests;

DROP TABLE surface_mint_requests;
ALTER TABLE surface_mint_requests_new RENAME TO surface_mint_requests;
CREATE INDEX idx_smr_status ON surface_mint_requests(status);
CREATE INDEX idx_smr_card_version ON surface_mint_requests(card_version_id);
