-- Router R1 (spec_action_router_v1 §9, §11; mvp-0.15): decision logging on
-- today's paths (built as migration 176 at mvp-0.12; renumbered 181 and
-- relabelled mvp-0.15 when it merged after main's 176-180, none of which
-- touches these tables). One append-only row per Today offer, staged P2
-- decision, learner pick and daily-plan block decision (plan_block, through
-- DL1's register_plan_decision_logger hook; owner decision 2026-10-12), with
-- the full candidate set, the chosen candidate and its true propensity (or an
-- explicit 'deterministic'). A list the learner picks from with no
-- system-served head is logged with propensity_kind 'not_served'.
-- The outcome table is a derived cache with one replayer; nothing here is
-- evidence, mastery or certification.

CREATE TABLE router_decisions (
  id TEXT PRIMARY KEY,
  -- Idempotency: today_offer:<slate>, staged_p2:<controller decision>,
  -- learner_pick:<scheduler candidate>, plan_block:<attention block>.
  receipt_key TEXT NOT NULL UNIQUE,
  decision_kind TEXT NOT NULL CHECK (
    decision_kind IN ('today_offer', 'staged_p2', 'learner_pick', 'plan_block')
  ),
  -- Where the decision was served: desktop_queue | full_list | skip_requeue |
  -- p2_bridge | daily_plan | the bind's entry surface for a learner pick.
  surface TEXT NOT NULL,
  -- Who composed the choice: legacy_queue | staged | daily_plan (R2 adds
  -- mixture).
  mode TEXT NOT NULL,
  -- The policy that chose: composed_offer_v2 | staged_policy_v1 | learner |
  -- the plan chooser (lane_quota_v1).
  policy TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  log_version TEXT NOT NULL,
  session_id TEXT,
  -- A learner pick names the offer it overrode.
  parent_decision_id TEXT REFERENCES router_decisions(id),
  scheduler_slate_id TEXT,
  controller_decision_id TEXT,
  -- Content hash of the decision's inputs (candidates, planner values,
  -- exclusions, the randomization design, the session context and the
  -- configuration that shaped the choice; never the build time).
  snapshot_hash TEXT NOT NULL,
  -- The assignment mechanism when the chosen candidate was drawn
  -- (scheduler_seeded_exploration | epsilon_tiebreak; registered in
  -- db.stores.router.ROUTER_DESIGNS); NULL when the choice was deterministic.
  design TEXT,
  seed TEXT,
  candidates_json TEXT NOT NULL,
  exclusions_json TEXT NOT NULL,
  candidate_count INTEGER NOT NULL CHECK (candidate_count >= 0),
  chosen_ref TEXT,
  chosen_practice_item_id TEXT,
  chosen_learning_object_id TEXT,
  chosen_scheduler_candidate_id TEXT,
  propensity REAL,
  propensity_kind TEXT NOT NULL CHECK (propensity_kind IN ('exact', 'deterministic', 'none', 'not_served')),
  learner_pick INTEGER NOT NULL DEFAULT 0 CHECK (learner_pick IN (0, 1)),
  -- R2 fills these (the Decider and the LLM); NULL while no model chooses.
  fallback TEXT,
  mixture_weights_json TEXT,
  model_distributions_json TEXT,
  sensor_answers_json TEXT,
  question_set_version TEXT,
  model_ids_json TEXT,
  card_hash TEXT,
  similar_decision_ids_json TEXT,
  latency_ms INTEGER,
  cost_usd REAL,
  detail_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  -- A drawn choice has 0 < p < 1; a deterministic one p = 1; a learner pick
  -- has no propensity (its choice was not sampled); a list that served no
  -- head (the learner chooses from it) has neither a choice nor a propensity.
  CHECK (
    (propensity_kind = 'exact' AND propensity > 0 AND propensity < 1)
    OR (propensity_kind = 'deterministic' AND propensity = 1)
    OR (propensity_kind IN ('none', 'not_served') AND propensity IS NULL)
  ),
  CHECK ((learner_pick = 1) = (propensity_kind = 'none')),
  CHECK ((chosen_ref IS NULL) = (propensity_kind = 'not_served'))
);
CREATE INDEX router_decisions_session ON router_decisions(session_id, created_at, id);
CREATE INDEX router_decisions_slate ON router_decisions(scheduler_slate_id);
CREATE INDEX router_decisions_candidate ON router_decisions(chosen_scheduler_candidate_id);
CREATE INDEX router_decisions_parent ON router_decisions(parent_decision_id);

CREATE TRIGGER router_decisions_no_update
BEFORE UPDATE ON router_decisions
BEGIN
    SELECT RAISE(ABORT, 'router_decisions is append-only');
END;

CREATE TRIGGER router_decisions_no_delete
BEFORE DELETE ON router_decisions
BEGIN
    SELECT RAISE(ABORT, 'router_decisions is append-only');
END;

-- R_next and R_cold per decision under the Pipeline plan's S definition
-- (S = alpha R_cold + (1 - alpha) R_next, alpha = 0.75). A pending outcome is
-- right-censored at observed_through (the newest attempt in the ledger), never
-- a failure. Rebuilt whole by its one replayer from router_decisions,
-- practice_attempts, grading evidence, reveal_events, tutor questions and
-- source exposures. R_cold's one-day rule is provisional (spec §15.2, owner
-- decision D12): each outcome also records its attempt's coldness covariates
-- (time since the last exposure to the item, its facets and its learning
-- object; attempts in between; the FSRS-predicted retrievability at the
-- attempt; the reveal amount since the last attempt on the learning object),
-- and coldness_candidates_json lists the same covariates for every later
-- attempt on the learning object the rule considered, so coldness can be
-- learned (R3) instead of hard-coded.
CREATE TABLE router_outcomes (
  decision_id TEXT PRIMARY KEY,
  outcome_version TEXT NOT NULL,
  target_practice_item_id TEXT,
  target_learning_object_id TEXT,
  -- not_taken: the session ended without the chosen candidate attempted.
  action_status TEXT NOT NULL CHECK (
    action_status IN ('taken', 'open', 'superseded', 'overridden', 'not_taken', 'not_applicable')
  ),
  action_attempt_id TEXT,
  r_next_status TEXT NOT NULL CHECK (r_next_status IN ('observed', 'pending', 'not_applicable')),
  r_next_value REAL CHECK (r_next_value IS NULL OR (r_next_value >= 0 AND r_next_value <= 1)),
  r_next_attempt_id TEXT,
  r_next_elapsed_seconds INTEGER,
  r_next_skipped INTEGER NOT NULL DEFAULT 0,
  r_cold_status TEXT NOT NULL CHECK (r_cold_status IN ('observed', 'pending', 'not_applicable')),
  r_cold_value REAL CHECK (r_cold_value IS NULL OR (r_cold_value >= 0 AND r_cold_value <= 1)),
  r_cold_attempt_id TEXT,
  r_cold_gap_seconds INTEGER,
  r_cold_skipped INTEGER NOT NULL DEFAULT 0,
  -- Coldness covariates of the R_next and R_cold attempts (NULL while the
  -- outcome is not observed, or when the input does not exist: no earlier
  -- exposure, no FSRS memory before the attempt).
  r_next_since_item_seconds INTEGER,
  r_next_since_facet_seconds INTEGER,
  r_next_since_lo_seconds INTEGER,
  r_next_intervening_attempts INTEGER CHECK (r_next_intervening_attempts IS NULL OR r_next_intervening_attempts >= 0),
  r_next_predicted_retrievability REAL CHECK (
    r_next_predicted_retrievability IS NULL OR (r_next_predicted_retrievability >= 0 AND r_next_predicted_retrievability <= 1)
  ),
  r_next_reveal_amount REAL CHECK (r_next_reveal_amount IS NULL OR r_next_reveal_amount >= 0),
  r_cold_since_item_seconds INTEGER,
  r_cold_since_facet_seconds INTEGER,
  r_cold_since_lo_seconds INTEGER,
  r_cold_intervening_attempts INTEGER CHECK (r_cold_intervening_attempts IS NULL OR r_cold_intervening_attempts >= 0),
  r_cold_predicted_retrievability REAL CHECK (
    r_cold_predicted_retrievability IS NULL OR (r_cold_predicted_retrievability >= 0 AND r_cold_predicted_retrievability <= 1)
  ),
  r_cold_reveal_amount REAL CHECK (r_cold_reveal_amount IS NULL OR r_cold_reveal_amount >= 0),
  coldness_candidates_json TEXT NOT NULL DEFAULT '[]',
  s_status TEXT NOT NULL CHECK (s_status IN ('final', 'provisional', 'pending', 'not_applicable')),
  s_value REAL CHECK (s_value IS NULL OR (s_value >= 0 AND s_value <= 1)),
  s_alpha REAL NOT NULL,
  observed_through TEXT,
  detail_json TEXT NOT NULL
);
CREATE INDEX router_outcomes_target ON router_outcomes(target_learning_object_id);
