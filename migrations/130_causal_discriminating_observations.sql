-- Causal-attribution P2 (§6, §7): the discriminating-observation receipt.
--
-- THE MISSING EDGE.  A causal probe could be offered, accepted, served with
-- pinned blind bundles, answered, and classified -- and then nothing happened.
-- `classify_against_blind_bundles` / `causal_orchestrator.classify_probe_response`
-- returned a verdict that no service consumed: no factor closed, no diagnosis
-- support moved, and the loop the whole P2 lane exists to close stayed open at
-- its last link.  This table is that link.
--
-- WHY A SEPARATE RECEIPT rather than a field on the cold verification or an
-- edit to the diagnosis receipt:
--
--   * §6 requires diagnosis support to move ONLY through an independent
--     discriminating observation, never as a side effect of repair success.  A
--     record that exists only as an argument to `record_delayed_cold_verification`
--     cannot satisfy that: it is written by the repair path.
--   * The diagnosis receipt lives in `attempt_debug_payloads`, which replay
--     rebuilds (`services/replay.py`).  Support written there would be silently
--     discarded on the next rebuild.  This ledger is append-only and survives.
--   * A resolution whose grounds are not recorded is not auditable.  Every row
--     names the presentation, the pinned bundle ids, the observed features, the
--     outcome, and WHETHER it was admitted -- so a replay can re-derive the same
--     verdict from the same frozen inputs.
--
-- WHAT MAY BE ADMITTED.  Only `matched_single` resolves a factor, and only when
-- the observation actually covered the declared feature keys of the bundles it
-- classified against.  `matched_multiple` and `all_bundles_matched` mean the
-- instrument did not discriminate; `cohort_mismatch` and `unparsed_features`
-- mean it could not be read; `no_bundle_matched` is genuine open-set evidence
-- for H_OTHER and supports it WITHOUT resolving the factor (an open-world arm
-- names no cause to repair).  `admitted` and `admission_reason` record which of
-- those applied, so the negative cases are data rather than silence.
--
-- SUPPORT AUTHORITY.  `support_authority` is `validator_owned` only when the
-- observed features came from a deterministic sensor (`feature_source =
-- 'deterministic'`); a model-extracted feature vector is still evidence and may
-- still VETO a triage route (§2.1 lets causal support downgrade freely), but it
-- may never PROMOTE.  Storing the sensor alongside the verdict is what keeps
-- that distinction reviewable instead of implicit.

CREATE TABLE causal_discriminating_observations (
  id TEXT PRIMARY KEY,

  factor_id TEXT NOT NULL,
  -- The attempt whose DIAGNOSIS this observation bears on (the factor's own
  -- attempt), not the attempt that answered the probe.  `failure_triage` keys
  -- its causal-support overlay on this.
  attempt_id TEXT,
  -- The attempt that ANSWERED the probe, when one exists.  Null for an
  -- out-of-band classification (a replayed transcript, an adjudicated review).
  probe_attempt_id TEXT,

  presentation_id TEXT NOT NULL,
  hypothesis_set_id TEXT NOT NULL,
  candidate_id TEXT,
  -- The bundle ids PINNED at presentation time.  Recording them makes the row
  -- replayable: the append-only bundle substrate guarantees the same ids
  -- resolve to the same predictions forever.
  blind_bundle_ids_json TEXT NOT NULL,

  outcome TEXT NOT NULL CHECK (outcome IN (
    'matched_single',
    'matched_multiple',
    'no_bundle_matched',
    'all_bundles_matched',
    'cohort_mismatch',
    'unparsed_features'
  )),
  classified_as_json TEXT NOT NULL,
  supports_open_set INTEGER NOT NULL CHECK (supports_open_set IN (0, 1)),

  -- Where the observed feature vector came from.  `unknown` is the fail-closed
  -- default and is deliberately representable: a sensor that cannot say what it
  -- is must not be silently promoted to a deterministic one.
  feature_source TEXT NOT NULL CHECK (feature_source IN (
    'deterministic',
    'model_extracted',
    'learner_declared',
    'unknown'
  )),
  observed_features_json TEXT NOT NULL,
  -- Whether the observation covered every declared key of the bundles it was
  -- matched against.  An exact-key matcher reports "no bundle matched" both
  -- when the declared feature was measured and differed AND when it was never
  -- measured at all; only the first is open-set evidence.
  declared_keys_observed INTEGER NOT NULL CHECK (declared_keys_observed IN (0, 1)),

  admitted INTEGER NOT NULL CHECK (admitted IN (0, 1)),
  admission_reason TEXT NOT NULL,
  support_authority TEXT,
  support_scores_json TEXT NOT NULL,
  resolved_factor INTEGER NOT NULL CHECK (resolved_factor IN (0, 1)),

  detail_json TEXT NOT NULL,
  decision_policy_version TEXT NOT NULL,
  formula_version TEXT NOT NULL,
  created_at TEXT NOT NULL,

  -- An unadmitted observation grants no authority and resolves nothing.
  CHECK (admitted = 1 OR (support_authority IS NULL AND resolved_factor = 0))
);

CREATE INDEX idx_causal_discriminating_observation_factor
  ON causal_discriminating_observations(factor_id, created_at, id);
CREATE INDEX idx_causal_discriminating_observation_attempt
  ON causal_discriminating_observations(attempt_id, created_at, id);
CREATE INDEX idx_causal_discriminating_observation_presentation
  ON causal_discriminating_observations(presentation_id, created_at, id);

CREATE TRIGGER causal_discriminating_observations_no_update
BEFORE UPDATE ON causal_discriminating_observations
BEGIN
  SELECT RAISE(ABORT, 'causal discriminating observations are append-only');
END;

CREATE TRIGGER causal_discriminating_observations_no_delete
BEFORE DELETE ON causal_discriminating_observations
BEGIN
  SELECT RAISE(ABORT, 'causal discriminating observations are append-only');
END;
