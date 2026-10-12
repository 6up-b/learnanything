-- Router R1 (spec_action_router_v1 §9, §11): decision logging on today's
-- paths. One append-only row per Today offer, staged P2 decision and learner
-- pick, with the full candidate set, the chosen candidate and its true
-- propensity (or an explicit 'deterministic'). The outcome table is a derived
-- cache with one replayer; nothing here is evidence, mastery or certification.

CREATE TABLE router_decisions (
  id TEXT PRIMARY KEY,
  -- Idempotency: today_offer:<slate>, staged_p2:<controller decision>,
  -- learner_pick:<scheduler candidate>.
  receipt_key TEXT NOT NULL UNIQUE,
  decision_kind TEXT NOT NULL CHECK (decision_kind IN ('today_offer', 'staged_p2', 'learner_pick')),
  -- Where the decision was served: desktop_queue | skip_requeue | p2_bridge |
  -- the bind's entry surface for a learner pick.
  surface TEXT NOT NULL,
  -- Who composed the choice: legacy_queue | staged (R2 adds mixture).
  mode TEXT NOT NULL,
  -- The policy that chose: composed_offer_v2 | staged_policy_v1 | learner.
  policy TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  log_version TEXT NOT NULL,
  session_id TEXT,
  -- A learner pick names the offer it overrode.
  parent_decision_id TEXT REFERENCES router_decisions(id),
  scheduler_slate_id TEXT,
  controller_decision_id TEXT,
  -- Content hash of the decision's inputs (candidates, planner values,
  -- exclusions and the randomization design).
  snapshot_hash TEXT NOT NULL,
  -- epsilon_tiebreak when the chosen candidate was drawn; NULL when the
  -- choice was deterministic.
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
  propensity_kind TEXT NOT NULL CHECK (propensity_kind IN ('exact', 'deterministic', 'none')),
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
  -- has no propensity (its choice was not sampled).
  CHECK (
    (propensity_kind = 'exact' AND propensity > 0 AND propensity < 1)
    OR (propensity_kind = 'deterministic' AND propensity = 1)
    OR (propensity_kind = 'none' AND propensity IS NULL)
  ),
  CHECK ((learner_pick = 1) = (propensity_kind = 'none'))
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
-- practice_attempts, grading evidence and reveal_events.
CREATE TABLE router_outcomes (
  decision_id TEXT PRIMARY KEY,
  outcome_version TEXT NOT NULL,
  target_practice_item_id TEXT,
  target_learning_object_id TEXT,
  action_status TEXT NOT NULL CHECK (
    action_status IN ('taken', 'open', 'superseded', 'overridden', 'not_applicable')
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
  s_status TEXT NOT NULL CHECK (s_status IN ('final', 'provisional', 'pending', 'not_applicable')),
  s_value REAL CHECK (s_value IS NULL OR (s_value >= 0 AND s_value <= 1)),
  s_alpha REAL NOT NULL,
  observed_through TEXT,
  detail_json TEXT NOT NULL
);
CREATE INDEX router_outcomes_target ON router_outcomes(target_learning_object_id);
