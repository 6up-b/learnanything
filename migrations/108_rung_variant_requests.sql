-- Learner-initiated re-runging (easier/harder variants). One row per request:
-- the durable lock (caps), the audit trail (target rung snapshot, evidence ids),
-- and the linkage to the minted variant. The evidence writes (self_report
-- attempt + learner claim) happen synchronously at request time and are NEVER
-- rolled back on generation failure — the request itself was real evidence.
CREATE TABLE rung_variant_requests (
  id TEXT PRIMARY KEY,
  source_practice_item_id TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  direction TEXT NOT NULL CHECK (direction IN ('easier', 'harder')),
  source_waypoint_slug TEXT NOT NULL,
  target_waypoint_slug TEXT NOT NULL,
  -- RungTarget.as_dict() snapshot at request time (audit + job rebuild).
  target_rung_json TEXT NOT NULL,
  status TEXT NOT NULL CHECK (
    status IN ('pending', 'generating', 'applied', 'review_required', 'failed')
  ),
  attempt_id TEXT,
  learner_claim_id TEXT,
  batch_id TEXT,
  patch_id TEXT,
  created_practice_item_id TEXT,
  failure_reason TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX idx_rvr_source ON rung_variant_requests(source_practice_item_id, status);
CREATE INDEX idx_rvr_created_item ON rung_variant_requests(created_practice_item_id);
