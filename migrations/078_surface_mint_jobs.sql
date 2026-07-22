-- P1 step 7 (spec_p1_shared_substrate §5.2, §5.3, §5.6): durable pre-mint jobs +
-- the fixed/rotating surface mint/gate. Modeled on migration 033 (ingest_jobs):
-- exactly one worker drains at a time via a lease, and an expired running lease is
-- recovered. Jobs NEVER block attempt submission (§5.6, §9.7); opening an admitted
-- administration calls no generator/LLM. Card/family retirement makes pending work
-- 'obsolete'. A failed candidate is retained for audit but is never servable.
--
-- Rendering and candidate minting are SEPARATE transactions (§5.3): a cache race may
-- waste a candidate but may not double-administer or manufacture novelty.
--
-- Migration numbering: highest applied on disk = 077 (familiarity namespace); P1
-- step 7 starts at 078. Never edit applied migrations 065-077.

CREATE TABLE surface_mint_requests (
  id TEXT PRIMARY KEY,
  card_version_id TEXT NOT NULL REFERENCES activity_card_versions(id),
  anchor_surface_id TEXT REFERENCES activity_surfaces(id),
  -- §5.6 idempotency key components. requested_angle_json defaults '' (not NULL) so
  -- the UNIQUE index treats "no requested angle" as one value (SQLite treats NULLs as
  -- distinct, which would defeat idempotency).
  requested_angle_json TEXT NOT NULL DEFAULT '',
  generator_version TEXT NOT NULL,
  gate_policy_version TEXT NOT NULL,
  -- Closed lifecycle (§5.6). A CHECK is appropriate: the vocabulary is fixed.
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
    'pending', 'running', 'candidate_ready', 'admitted', 'rejected', 'obsolete', 'failed')),
  -- Lease (033 pattern): a running job is owned by lease_owner until lease_expires_at.
  -- An expired lease is treated as dead and does not block a new claim.
  lease_owner TEXT,
  lease_expires_at TEXT,
  candidate_surface_id TEXT REFERENCES activity_surfaces(id),
  gate_results_json TEXT,
  token_cost_json TEXT,
  failure_reason TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(card_version_id, anchor_surface_id, requested_angle_json,
         generator_version, gate_policy_version)
);
CREATE INDEX idx_smr_status ON surface_mint_requests(status);
CREATE INDEX idx_smr_card_version ON surface_mint_requests(card_version_id);
