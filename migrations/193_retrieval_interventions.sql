-- Canonical sources S5 (spec_source_practice_and_probes_v1.md §11): retrieval
-- in the evidence loop, reports only. Nothing reads these tables to serve.

-- One row when a retrieved asset is SHOWN or SERVED (never when it is merely
-- retrieved): a passage offer opened or a tutor answer citing retrieved spans,
-- a remediation passage delivered, a comparison shown, a proposal picked, an
-- imported source exercise served, a need fulfilled from the sources and
-- served. Append-only facts (RAW_LEDGER): references, not copies.
CREATE TABLE retrieval_interventions (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('source_passage', 'source_exercise', 'practice_pick', 'comparison',
                                     'remediation_passage')),
  caller_kind TEXT,
  caller_ref TEXT,
  intent TEXT,
  policy TEXT,
  tool_call_id TEXT,
  proposal_id TEXT,
  question_event_id TEXT,
  remediation_episode_id TEXT,
  -- R1's learner_pick row for the pick, when the router_decisions table exists.
  router_decision_id TEXT,
  assets_json TEXT NOT NULL DEFAULT '{}',
  targets_json TEXT NOT NULL DEFAULT '{}',
  state_ref_json TEXT NOT NULL DEFAULT '{}',
  -- A valued check: predicted EIG/EVSI, the likelihood regime and basis, the
  -- predicted outcome distribution P(E) and the predicted minutes.
  valuation_json TEXT,
  exposure_event_ids_json TEXT NOT NULL DEFAULT '[]',
  impression_ids_json TEXT NOT NULL DEFAULT '[]',
  reading_exposure_label TEXT,
  -- The independence verdict at valuation time and again at serving time.
  eligibility_json TEXT,
  seconds_since_related_exposure REAL,
  session_id TEXT,
  attempt_id TEXT,
  algorithm_version TEXT,
  -- Reserved; randomization is deferred (spec §19). NULL in v1.
  design TEXT,
  seed TEXT,
  propensity REAL
);
CREATE INDEX idx_retrieval_interventions_created ON retrieval_interventions(created_at);
CREATE INDEX idx_retrieval_interventions_proposal ON retrieval_interventions(proposal_id);
CREATE TRIGGER retrieval_interventions_no_update BEFORE UPDATE ON retrieval_interventions
BEGIN SELECT RAISE(ABORT, 'retrieval interventions are append-only'); END;
CREATE TRIGGER retrieval_interventions_no_delete BEFORE DELETE ON retrieval_interventions
BEGIN SELECT RAISE(ABORT, 'retrieval interventions are append-only'); END;

-- The outcome join (DERIVED; exactly one replayer, zero model calls, persisted
-- rows only). Pending outcomes stay right-censored, never failures.
CREATE TABLE retrieval_intervention_outcomes (
  intervention_id TEXT PRIMARY KEY,
  as_of TEXT,
  next_attempt_id TEXT,
  next_correctness REAL,
  next_assisted INTEGER,
  next_window TEXT,
  cold_attempt_id TEXT,
  cold_outcome_state TEXT NOT NULL,
  cold_correctness REAL,
  observed_bucket TEXT,
  predicted_outcomes_json TEXT,
  predicted_minutes REAL,
  actual_minutes REAL,
  hypothesis_movement_json TEXT NOT NULL DEFAULT '{}',
  learner_signals_json TEXT NOT NULL DEFAULT '[]',
  action_before TEXT,
  action_after TEXT,
  action_flipped INTEGER,
  outcome_version TEXT NOT NULL
);
