-- Explicit coldness administration receipts for the repair lane's cold
-- retrieval.
--
-- Coldness used to be an INFERENCE: the §6.2 preconditions (chronology,
-- surface-group difference, unprimed + hints_used == 0, the +1-day
-- not_before) enforced it, but nothing RECORDED it — a cold verification's
-- claim to be "cold" rested on `hints_used == 0` plus the absence of
-- counter-evidence nobody had scanned for. This table makes coldness a
-- positive administration receipt: per-dimension `pass|fail|unknown` statuses
-- with evidence, scoped absence claims (which ledgers were scanned, over what
-- interval, and which channels are KNOWN to be unobserved), and derived
-- qualifications (`qualifies_as_cold_retrieval` /
-- `qualifies_as_repair_effect_verification` /
-- `qualifies_as_held_out_validation`) as distinct, separately-falsifiable
-- claims.
--
-- Two stages per follow-up task: one `administration` snapshot when the cold
-- item is first served while its task is active (window state, surface
-- eligibility, selection basis, render-time exposure scan), and one `final`
-- receipt when the terminal disposition lands (measured verification OR a
-- typed §4.3 refusal — refusals get a receipt with partial evidence too).
--
-- `lane` is deliberately unconstrained TEXT: only 'repair_cold_retry' has a
-- producer today, but the certification (§5.7) and teach-back lanes are
-- expected adopters and a CHECK on an append-only table calcifies (the
-- migration-145 lesson). Semantics are prospective-only: verifications
-- recorded before this table keep their meaning, and consumers distinguish
-- eras by receipt presence and `receipt_version`.
--
-- Linking choice: the receipt row carries `cold_verification_id`;
-- `causal_cold_verifications` (121) is NOT altered. That table's rows are
-- immutable-by-convention and are inserted BEFORE the receipt exists, so a
-- back-reference column would need a second-phase UPDATE on settled rows.
-- One direction, receipt -> verification, with a unique partial index.

CREATE TABLE coldness_receipts (
  id TEXT PRIMARY KEY,

  lane TEXT NOT NULL,
  stage TEXT NOT NULL CHECK (stage IN ('administration', 'final')),

  followup_task_id TEXT,
  remediation_episode_id TEXT,
  source_attempt_id TEXT,
  -- NULL on the administration snapshot (no attempt yet) and on refusal
  -- receipts whose disposition never had a concrete attempt.
  cold_attempt_id TEXT,
  -- Set exactly when the final receipt accompanies a measured verification.
  cold_verification_id TEXT,

  -- Per-dimension {status: pass|fail|unknown, evidence: {...}} for:
  -- retrieval_delay, exposure_isolation, surface_novelty, selection_basis,
  -- answer_leakage, window_integrity, verification_blinding, unassisted.
  dimensions_json TEXT NOT NULL,
  -- The derived qualification claims plus the disposition outcome and the
  -- administration-receipt link.
  derived_json TEXT NOT NULL,
  -- Scoped absence claim: enumerated scanned ledgers, interval boundaries,
  -- known_unobserved_channels, telemetry_coverage_version.
  telemetry_coverage_json TEXT NOT NULL,

  receipt_version TEXT NOT NULL,
  created_at TEXT NOT NULL,

  -- An administration snapshot precedes any attempt or verification.
  CHECK (
    stage != 'administration'
    OR (cold_attempt_id IS NULL AND cold_verification_id IS NULL)
  )
);

-- Idempotency: one snapshot and one final receipt per task. INSERT OR IGNORE
-- over these makes re-serving the detail or replaying the disposition a no-op.
CREATE UNIQUE INDEX uq_coldness_receipts_task_stage
  ON coldness_receipts(followup_task_id, stage)
  WHERE followup_task_id IS NOT NULL;

CREATE UNIQUE INDEX uq_coldness_receipts_verification
  ON coldness_receipts(cold_verification_id)
  WHERE cold_verification_id IS NOT NULL;

CREATE INDEX idx_coldness_receipts_episode
  ON coldness_receipts(remediation_episode_id, created_at, id);
CREATE INDEX idx_coldness_receipts_lane
  ON coldness_receipts(lane, stage, created_at, id);

-- Append-only, per the migration-145 precedent: a receipt is evidence about a
-- moment, never a row to correct in place.
CREATE TRIGGER coldness_receipts_no_update
BEFORE UPDATE ON coldness_receipts
BEGIN
  SELECT RAISE(ABORT, 'coldness receipts are append-only');
END;

CREATE TRIGGER coldness_receipts_no_delete
BEFORE DELETE ON coldness_receipts
BEGIN
  SELECT RAISE(ABORT, 'coldness receipts are append-only');
END;
