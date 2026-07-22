-- P4 §14.2 step 3 -- commitment-scoped controller ownership (design §A.2, §C step 3).
-- The dual-controller coexistence seam: during the cutover window the staged policy
-- owns P2 golden-path commitments and the legacy scheduler owns everything else. A
-- commitment (and its P2 golden-path run) is owned by EXACTLY ONE controller at a time
-- (design §A.2). Ownership is a rebuildable projection head keyed by commitment_id;
-- every transition is append-only with a durable receipt (design §A.5 / §C: transitions
-- append-only with receipts, rollback applies to the next uncommitted decision only).
--
-- No FK to vault-owned ids (commitment ids are plain TEXT, per the 069/096 convention).

-- Append-only ownership transition log -- the authority. Each row is one durable
-- receipt: who owned before, who owns after, why, under which ownership-policy version,
-- and the (optional) shared rollback receipt id that batched the transition.
CREATE TABLE controller_ownership_events (
  id TEXT PRIMARY KEY,
  commitment_id TEXT NOT NULL,
  event_ordinal INTEGER NOT NULL,
  from_owner TEXT CHECK (from_owner IN ('staged', 'legacy')),
  to_owner TEXT NOT NULL CHECK (to_owner IN ('staged', 'legacy')),
  reason TEXT NOT NULL,
  receipt_id TEXT NOT NULL,
  policy_version INTEGER NOT NULL,
  detail_json TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(commitment_id, event_ordinal)
);
CREATE INDEX idx_controller_ownership_events_commitment
  ON controller_ownership_events(commitment_id, event_ordinal);
CREATE INDEX idx_controller_ownership_events_receipt
  ON controller_ownership_events(receipt_id);

-- The rebuildable current-owner head projection (design §A.2: commitment_id -> owner).
-- Deterministically re-derivable by folding controller_ownership_events; kept as a
-- head for the scheduler's per-build ownership-exclusion read.
CREATE TABLE controller_ownership (
  commitment_id TEXT PRIMARY KEY,
  owner TEXT NOT NULL CHECK (owner IN ('staged', 'legacy')),
  ownership_version INTEGER NOT NULL,
  policy_version INTEGER NOT NULL,
  receipt_id TEXT NOT NULL,
  assigned_at TEXT NOT NULL
);
CREATE INDEX idx_controller_ownership_owner ON controller_ownership(owner);
