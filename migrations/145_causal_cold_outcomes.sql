-- Typed cold-outcome dispositions for the causal repair lane
-- (decision_value_and_commissioning_spec_v1.md §4.3; Wave-2 item B1).
--
-- `causal_cold_verifications` (121) records only a MEASURED verification: its
-- CHECKs (`cold_attempt_id NOT NULL UNIQUE`, `source_surface_family !=
-- cold_surface_family`) make the non-service terminals unrepresentable, so an
-- expired task, a declined retry, a same-surface pair, an assisted attempt and
-- "never scheduled at all" were all indistinguishable from "no row". The
-- certification lane solved this in 139 (`held/failed/indeterminate` with a
-- required abstention reason); this table is the repair lane's counterpart:
-- one append-only row per TERMINAL DISPOSITION of a cold-verification
-- opportunity, measured or not. §4.3's exact rule is enforced by CHECK: only a
-- task that had a genuine independent serving opportunity may become ordinary
-- right-censoring; a missing/never-servable surface is structural
-- unmeasurability, not evidence about the repair.
--
-- These labels are capture-now data (aug. standing constraint 6): none of them
-- can be backfilled once the moment has passed, and P4's repair-effectiveness
-- training set is exactly this table unioned with 139's outcomes.
--
-- `learner_declined` is in the vocabulary per §4.3 but has NO producer yet —
-- followup tasks currently have no decline affordance. Representable-first is
-- deliberate (the CHECK calcifies on an append-only table; see A4's
-- `should_not_have_abstained` precedent).

CREATE TABLE causal_cold_outcomes (
  -- Content hash over (task, episode, source attempt, cold attempt, outcome):
  -- replaying the same terminal event is one row, so recording may run inside
  -- `apply_attempt` and per-attempt sweeps without double-counting.
  id TEXT PRIMARY KEY,

  outcome TEXT NOT NULL CHECK (outcome IN (
    'cold_success',
    'cold_failure',
    'right_censored_expired',
    'learner_declined',
    'unmeasurable_no_held_out_surface',
    'unmeasurable_unservable_surface',
    'same_surface',
    'contaminated_or_assisted',
    'chronology_invalid',
    'missing_chain'
  )),

  -- NULL exactly for schedule-time refusals: "no independent surface existed,
  -- so no task was ever created" is itself a disposition.
  followup_task_id TEXT,
  remediation_episode_id TEXT,
  case_kind TEXT,
  case_ref TEXT,
  source_attempt_id TEXT,
  cold_attempt_id TEXT,
  repair_class_id TEXT,
  hypothesis_ids_json TEXT NOT NULL DEFAULT '[]',

  -- Set exactly when the disposition is a measured verification; the paired
  -- row in `causal_cold_verifications` stays the authority on the three
  -- support channels.
  cold_verification_id TEXT,

  -- §4.3: was there a genuine independent serving opportunity? Gates
  -- right-censoring below.
  servable_opportunity INTEGER NOT NULL CHECK (servable_opportunity IN (0, 1)),

  -- Duration availability is orthogonal to the outcome (spec §4.3 lists
  -- `missing_duration` as a state; here it is a flag so `cold_failure with
  -- missing duration` is representable without a second row). NULL when there
  -- is no cold attempt to time.
  duration_state TEXT CHECK (
    duration_state IS NULL OR duration_state IN ('captured', 'missing')
  ),

  detail_json TEXT NOT NULL,
  store_version TEXT NOT NULL,
  scheduled_not_before TEXT,
  scheduled_expires_at TEXT,
  created_at TEXT NOT NULL,

  -- Measured outcomes carry their verification; nothing else may.
  CHECK (
    (outcome IN ('cold_success', 'cold_failure'))
    = (cold_verification_id IS NOT NULL)
  ),
  -- Only a genuinely-servable opportunity right-censors (spec §4.3).
  CHECK (outcome != 'right_censored_expired' OR servable_opportunity = 1),
  -- Consume-time dispositions are about a concrete attempt.
  CHECK (
    outcome NOT IN (
      'cold_success', 'cold_failure', 'same_surface',
      'contaminated_or_assisted', 'chronology_invalid'
    )
    OR cold_attempt_id IS NOT NULL
  )
);

-- One terminal disposition per scheduled task (schedule-time refusals have no
-- task and dedupe on the content id).
CREATE UNIQUE INDEX uq_causal_cold_outcomes_task
  ON causal_cold_outcomes(followup_task_id)
  WHERE followup_task_id IS NOT NULL;
CREATE INDEX idx_causal_cold_outcomes_outcome
  ON causal_cold_outcomes(outcome, created_at, id);
CREATE INDEX idx_causal_cold_outcomes_episode
  ON causal_cold_outcomes(remediation_episode_id, created_at, id);

CREATE TRIGGER causal_cold_outcomes_no_update
BEFORE UPDATE ON causal_cold_outcomes
BEGIN
  SELECT RAISE(ABORT, 'causal cold outcomes are append-only');
END;

CREATE TRIGGER causal_cold_outcomes_no_delete
BEFORE DELETE ON causal_cold_outcomes
BEGIN
  SELECT RAISE(ABORT, 'causal cold outcomes are append-only');
END;
