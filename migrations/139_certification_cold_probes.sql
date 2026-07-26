-- Delayed cold probe per certified LO + the `false_certification_rate` ground
-- truth (spec_measurement_efficiency_v1.md §5.7, plan item 4.2).
--
-- §5.7: "The delayed cold probe is the ground truth ... one held-out-surface
-- item per certified LO at +2-3 weeks. If it passes, the certificate held. In a
-- single-learner vault this is the only external validity check available."
-- `false_certification_rate` is the first metric on the extended §3 B5
-- scoreboard because "optimizing time-to-certification without measuring false
-- certification is lowering the bar with extra steps".
--
-- TWO changes, and the split between them is the design:
--
-- 1. `followup_tasks` is GENERALIZED, not duplicated. The delay/serve/consume/
--    expire lifecycle, the `not_before` invisibility window, the `context_json`
--    carry-the-inputs precedent (migration 124 §6.2) and the scheduler's
--    `pending_followup_practice_items` reader all already exist and are all
--    exactly what a certification probe needs. What did not exist is a second
--    `kind`: the CHECK constraints admitted only `cold_retry` / (`misconception`
--    | `diagnosis`), i.e. the repair-scoped lane. SQLite cannot ALTER a CHECK,
--    so the table is rebuilt (same pattern as 070/071/110/111).
--
--    `learning_object_id` is added while we are here. A certification probe is
--    scoped to an LO, and the two queries that decide correctness -- "does this
--    certificate already have a probe?" and "is there a live probe for an LO
--    whose certificate has since been withdrawn?" -- must be indexable rather
--    than a JSON scan over `context_json`. Nullable, so `cold_retry` rows are
--    untouched.
--
-- 2. `certification_cold_probe_outcomes` is a NEW table because it is a
--    different KIND of record. `followup_tasks` is a QUEUE (mutable `status`,
--    the distinction migration 124 draws for `causal_machine_checks`); the probe
--    verdict is a GROUND-TRUTH LABEL, so it is append-only with `no_update` /
--    `no_delete` triggers, content-addressed, and version-stamped the way
--    `diagnosis_adjudications` (126) and `causal_cold_verifications` (121) are.
--    A label that a later rebuild can silently rewrite is not ground truth, and
--    `false_certification_rate` is the number that licenses every speed claim in
--    Part III (§5.7) plus the revert criterion for C2 (§5.5 / plan 8.6).
--
-- WHY THE VERDICT IS NOT A BOOLEAN: `held` / `failed` / `indeterminate`. §5.7's
-- denominator is "certified AND probed"; an unprobed certificate must never
-- count as a pass, and an *administered but uninterpretable* probe (the learner
-- took it primed, the chosen surface turned out not to be held out, the
-- certificate had already been withdrawn) is neither a pass nor a failure. Both
-- non-arms have to be representable or the rate is 1.0-by-construction in one
-- direction and 0.0-by-construction in the other. Standing constraint 2 / §11:
-- no new closed vocabulary without an explicit abstention arm.

PRAGMA foreign_keys=OFF;

CREATE TABLE followup_tasks_new (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('cold_retry', 'certification_cold_probe')),
  case_kind TEXT NOT NULL CHECK (
    case_kind IN ('misconception', 'diagnosis', 'certification')
  ),
  -- For `certification` this is the certificate id (a content hash over LO +
  -- blueprint/recipe + certified cells), which is what makes "one probe per
  -- certificate, ever" a UNIQUE-indexable fact instead of a caller convention.
  case_ref TEXT NOT NULL,
  source_attempt_id TEXT REFERENCES practice_attempts(id),
  remediation_episode_id TEXT REFERENCES remediation_episodes(id) ON DELETE CASCADE,
  not_before TEXT NOT NULL,
  expires_at TEXT,
  status TEXT NOT NULL CHECK (status IN ('pending', 'served', 'consumed', 'expired')),
  selected_item_id TEXT,
  consumed_attempt_id TEXT REFERENCES practice_attempts(id),
  context_json TEXT,
  learning_object_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

INSERT INTO followup_tasks_new (
  id, kind, case_kind, case_ref, source_attempt_id, remediation_episode_id,
  not_before, expires_at, status, selected_item_id, consumed_attempt_id,
  context_json, learning_object_id, created_at, updated_at
)
SELECT
  id, kind, case_kind, case_ref, source_attempt_id, remediation_episode_id,
  not_before, expires_at, status, selected_item_id, consumed_attempt_id,
  context_json, NULL, created_at, updated_at
FROM followup_tasks;

DROP TABLE followup_tasks;
ALTER TABLE followup_tasks_new RENAME TO followup_tasks;

CREATE INDEX idx_followup_tasks_due
  ON followup_tasks(status, not_before, expires_at);
CREATE INDEX idx_followup_tasks_item
  ON followup_tasks(selected_item_id, status);
-- The two certification-probe queries: idempotency by certificate, and the
-- withdrawal sweep by LO.
CREATE INDEX idx_followup_tasks_kind_case
  ON followup_tasks(kind, case_ref);
CREATE INDEX idx_followup_tasks_kind_lo
  ON followup_tasks(kind, learning_object_id, status);
-- One probe per certificate, for the whole life of the vault -- including after
-- it has been consumed or has expired. A re-run of the scheduler must not queue
-- a second probe, and a certificate that was measured once must not be measured
-- again under the same id (a re-earned certificate hashes differently, because
-- its cells or recipe differ, and is therefore a new certificate).
CREATE UNIQUE INDEX uq_followup_tasks_certification_probe
  ON followup_tasks(case_ref)
  WHERE kind = 'certification_cold_probe';

PRAGMA foreign_key_check;
PRAGMA foreign_keys=ON;

CREATE TABLE certification_cold_probe_outcomes (
  -- Content hash over (certificate id, probe task, probe attempt): the same
  -- probe recorded twice is one row, so the live path may run inside
  -- `apply_attempt` and a replay of the same attempt cannot double-count a
  -- ground-truth label.
  id TEXT PRIMARY KEY,

  -- WHICH CERTIFICATE. No FK to a certificates table because none exists yet:
  -- §5.3 receipts are plan item 8.4. Until then the certificate is derived from
  -- the capability ledger and SNAPSHOTTED here (`certificate_receipt_json`), so
  -- this row keeps meaning something after the ledger moves. When 8.4 lands, the
  -- stored receipt id goes in `certificate_id` unchanged -- it is already the
  -- content hash of the same tuple.
  certificate_id TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  blueprint_id TEXT NOT NULL,
  recipe_id TEXT NOT NULL,
  -- The §5.3 receipt as it stood when the probe was scheduled: which cells were
  -- certified, at what credit, from which surface groups, measured-vs-inferred.
  -- "A certificate that cannot distinguish these is not one" (standing
  -- constraint 9).
  certificate_receipt_json TEXT NOT NULL,
  certified_at TEXT,

  -- THE SCHEDULE. `horizon_days` / `window_days` are recorded per row because
  -- they are fitted parameters (scope `certification_cold_probe`): a rate
  -- computed across a horizon change must be sliceable by horizon.
  followup_task_id TEXT NOT NULL,
  scheduled_not_before TEXT NOT NULL,
  scheduled_expires_at TEXT,
  horizon_days REAL NOT NULL,
  window_days REAL NOT NULL,

  -- THE PROBE. `excluded_surface_groups_json` is the held-out claim: the surface
  -- groups the certifying evidence came from. `probe_surface_group` must not be
  -- among them, and the CHECK below refuses to record `held` when it is.
  probe_practice_item_id TEXT NOT NULL,
  probe_attempt_id TEXT NOT NULL,
  probe_surface_group TEXT NOT NULL,
  excluded_surface_groups_json TEXT NOT NULL,
  held_out_basis TEXT NOT NULL CHECK (
    held_out_basis IN ('distinct_surface_group', 'shared_surface_group', 'unknown')
  ),
  -- Affordances the certifying evidence had that this probe does not, in the
  -- `causal_cold_verifications.avoided_affordances_json` vocabulary, so a P4
  -- reader can union the two cold-outcome channels.
  avoided_affordances_json TEXT NOT NULL,

  -- THE VERDICT.
  verdict TEXT NOT NULL CHECK (verdict IN ('held', 'failed', 'indeterminate')),
  -- Required exactly when the verdict is `indeterminate`, forbidden otherwise:
  -- an abstention whose reason is not recorded is indistinguishable from a
  -- missing row, and "not yet measured" is the arm this metric exists to keep
  -- separate from "passed".
  indeterminate_reason TEXT CHECK (
    indeterminate_reason IS NULL
    OR indeterminate_reason IN (
      'assisted_probe',
      'surface_not_held_out',
      'certificate_withdrawn',
      'grade_unavailable'
    )
  ),
  -- Denormalized 0/1 so the metric is one SQL aggregate and cannot drift from
  -- the verdict vocabulary; NULL on `indeterminate` (no label).
  success INTEGER CHECK (success IS NULL OR success IN (0, 1)),
  correctness REAL,
  success_threshold REAL NOT NULL,
  assisted INTEGER NOT NULL CHECK (assisted IN (0, 1)),
  certificate_state_at_probe TEXT NOT NULL CHECK (
    certificate_state_at_probe IN ('active', 'withdrawn')
  ),

  -- VERSION PINS, following `diagnosis_adjudications` (126). A label that
  -- cannot name the policy, the parameter set, and the grader that produced it
  -- is not reusable once any of the three moves -- and all three move inside a
  -- single Stage 6 week.
  store_version TEXT NOT NULL,
  policy_version TEXT NOT NULL,
  certification_algorithm_version TEXT,
  parameters_json TEXT NOT NULL,
  grading_source TEXT,
  grading_prompt_version TEXT,
  grader_model TEXT,
  grader_provider TEXT,
  grader_provider_revision TEXT,
  grading_agent_run_id TEXT,
  created_at TEXT NOT NULL,

  -- The verdict partitions on the abstention reason in both directions.
  CHECK (
    (verdict = 'indeterminate' AND indeterminate_reason IS NOT NULL AND success IS NULL)
    OR
    (verdict IN ('held', 'failed') AND indeterminate_reason IS NULL AND success IS NOT NULL)
  ),
  CHECK (verdict != 'held' OR success = 1),
  CHECK (verdict != 'failed' OR success = 0),
  -- A scored verdict requires a genuinely held-out surface and an unassisted
  -- probe. Both failure modes have their own `indeterminate_reason`, so this
  -- CHECK cannot silently discard a probe -- it forces it into the abstention
  -- arm where the denominator can see it.
  CHECK (verdict = 'indeterminate' OR held_out_basis = 'distinct_surface_group'),
  CHECK (verdict = 'indeterminate' OR assisted = 0),
  CHECK (verdict = 'indeterminate' OR certificate_state_at_probe = 'active')
);

-- One outcome per probe attempt: the label is attempt-scoped.
CREATE UNIQUE INDEX uq_certification_cold_probe_outcome_attempt
  ON certification_cold_probe_outcomes(probe_attempt_id);
-- ...and one per certificate, matching the one-probe-per-certificate schedule.
CREATE UNIQUE INDEX uq_certification_cold_probe_outcome_certificate
  ON certification_cold_probe_outcomes(certificate_id);
CREATE INDEX idx_certification_cold_probe_outcome_lo
  ON certification_cold_probe_outcomes(learning_object_id, created_at, id);
-- The `false_certification_rate` aggregate slice.
CREATE INDEX idx_certification_cold_probe_outcome_verdict
  ON certification_cold_probe_outcomes(verdict, created_at, id);
-- The B5 per-horizon / per-grader slice (§3 B5 reports per prompt version and
-- per model; a rate mixing two horizons is two metrics in a trench coat).
CREATE INDEX idx_certification_cold_probe_outcome_slices
  ON certification_cold_probe_outcomes(horizon_days, grader_model, created_at);

CREATE TRIGGER certification_cold_probe_outcomes_no_update
BEFORE UPDATE ON certification_cold_probe_outcomes
BEGIN
  SELECT RAISE(ABORT, 'certification cold probe outcomes are append-only');
END;

CREATE TRIGGER certification_cold_probe_outcomes_no_delete
BEFORE DELETE ON certification_cold_probe_outcomes
BEGIN
  SELECT RAISE(ABORT, 'certification cold probe outcomes are append-only');
END;
