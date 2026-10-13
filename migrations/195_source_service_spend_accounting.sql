-- Canonical sources (spec_source_practice_and_probes_v1.md §7.5; the
-- sources-spend-accounting stage, Codex verification of ee3115d5: F2 reopened
-- and F14): the daily cap counts every request exactly once, across crashes
-- and this upgrade. One accounting function serves admission, recovery and
-- every report (learnloop.db.stores.source_service.service_spend_accounting):
--
-- * a reservation whose owner is alive counts the larger of its own charge
--   (the estimate, reconciled upward) and what the receipts naming it show;
-- * once reconciled (`settled`) it counts what its receipts show (its
--   reconciled cost bounds a receipt whose finish was lost);
-- * once its owner is terminal (its lease ran out: `lease_expires_at`,
--   renewed while the owning process lives) recovery reconciles it with its
--   receipts, or releases it (`released`) when it has none: it was never sent;
-- * a receipt naming no reservation (spend before the ledger, or another path)
--   counts once by its own cost.
--
-- Rows written before receipts named their reservation (migration 194's
-- first code) cannot be matched with their receipts by name. They are marked
-- `legacy`: such a row keeps counting its own charge and suppresses no
-- receipt, since nothing durable ties one to it (an amount or a
-- second-resolution stamp is no identity: the Codex verify of the stage
-- review's F1, at the merge onto main). Both count, conservatively, and the
-- report says how much may be counted twice. A row is legacy when no root
-- receipt names it.
--
-- SQLite cannot widen a CHECK in place, so the WORKFLOW table is rebuilt with
-- every row and its index; nothing references it. Two indexes let the
-- per-admission receipt scan read only today's receipts and find leaves.
CREATE TABLE source_service_spend_new (
  id TEXT PRIMARY KEY,
  envelope TEXT NOT NULL,
  day TEXT NOT NULL,
  reserved_usd REAL NOT NULL CHECK (reserved_usd >= 0),
  charged_usd REAL NOT NULL CHECK (charged_usd >= 0),
  state TEXT NOT NULL CHECK (state IN ('in_flight', 'settled', 'released')),
  legacy INTEGER NOT NULL DEFAULT 0 CHECK (legacy IN (0, 1)),
  process TEXT NOT NULL,
  lease_expires_at TEXT,
  resolved_by TEXT CHECK (resolved_by IS NULL OR resolved_by IN ('owner', 'recovery')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

INSERT INTO source_service_spend_new (
  id, envelope, day, reserved_usd, charged_usd, state, legacy, process, lease_expires_at, resolved_by,
  created_at, updated_at
)
SELECT
  s.id, s.envelope, s.day, s.reserved_usd, s.charged_usd, s.state,
  CASE WHEN EXISTS (
    SELECT 1
    FROM model_call_receipts r,
         json_each(CASE WHEN json_valid(r.budget_json) THEN r.budget_json ELSE '{}' END,
                   '$.envelope_reservations') j
    WHERE r.parent_call_id IS NULL
      AND instr(r.budget_json, 'envelope_reservations') > 0
      AND j.value = s.id
  ) THEN 0 ELSE 1 END,
  s.process,
  NULL,
  CASE WHEN s.state = 'settled' THEN 'owner' END,
  s.created_at, s.updated_at
FROM source_service_spend s;

DROP TABLE source_service_spend;
ALTER TABLE source_service_spend_new RENAME TO source_service_spend;
CREATE INDEX idx_source_service_spend_day ON source_service_spend(envelope, day);
CREATE INDEX idx_model_calls_started ON model_call_receipts(started_at);
CREATE INDEX idx_model_calls_parent ON model_call_receipts(parent_call_id);
