-- Router R2a (docs/specs/plan_router_r2_v1.md §5.2, §9; mvp-0.23): the exact
-- decision -> presentation -> attempt receipt, the stored learner-state card,
-- and the decision ledger's kind CHECK extended once for R2c. Built on
-- router/r2a as 205 (a placeholder number) and renumbered 202 at its landing
-- after main's 200-201 (value-of-information stopping).
--
-- 1. router_decisions is rebuilt so decision_kind also admits 'plan_interrupt'
--    (R2c's mid-block follow-up decision). SQLite cannot widen a CHECK in
--    place, so the append-only ledger is rebuilt with every row and id
--    preserved (175's judgment_ledger precedent). DROP TABLE removes the old
--    indexes and triggers, which are recreated on the renamed table; the one
--    foreign key that names the table (its own parent_decision_id) resolves
--    to the rebuilt one.
-- 2. router_outcomes (DERIVED, one replayer) records how each action was
--    bound (presentation | candidate | session_rule) and the answer-key
--    status of the R_next and R_cold attempts (owner Q13: unverified-key
--    attempts are outcomes, their status a covariate).
-- 3. plan_presentations (RAW_LEDGER, append-only): one row per plan item
--    served, written with its item_served event.
-- 4. practice_attempts.plan_presentation_id: the presentation an attempt
--    answers (attempt metadata, never evidence); at most one attempt each.
-- 5. router_decision_payloads (WORKFLOW): the card each decision stored (R2b
--    adds the model requests and raw responses), pruned after
--    router.payload_retention_days; the hashes stay on the decision row.
PRAGMA foreign_keys = OFF;

CREATE TABLE router_decisions__202 (
  id TEXT PRIMARY KEY,
  receipt_key TEXT NOT NULL UNIQUE,
  decision_kind TEXT NOT NULL CHECK (
    decision_kind IN ('today_offer', 'staged_p2', 'learner_pick', 'plan_block', 'plan_interrupt')
  ),
  surface TEXT NOT NULL,
  mode TEXT NOT NULL,
  policy TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  log_version TEXT NOT NULL,
  session_id TEXT,
  parent_decision_id TEXT REFERENCES router_decisions(id),
  scheduler_slate_id TEXT,
  controller_decision_id TEXT,
  snapshot_hash TEXT NOT NULL,
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
  CHECK (
    (propensity_kind = 'exact' AND propensity > 0 AND propensity < 1)
    OR (propensity_kind = 'deterministic' AND propensity = 1)
    OR (propensity_kind IN ('none', 'not_served') AND propensity IS NULL)
  ),
  CHECK ((learner_pick = 1) = (propensity_kind = 'none')),
  CHECK ((chosen_ref IS NULL) = (propensity_kind = 'not_served'))
);
INSERT INTO router_decisions__202 (
  id, receipt_key, decision_kind, surface, mode, policy, algorithm_version, log_version, session_id,
  parent_decision_id, scheduler_slate_id, controller_decision_id, snapshot_hash, design, seed,
  candidates_json, exclusions_json, candidate_count, chosen_ref, chosen_practice_item_id,
  chosen_learning_object_id, chosen_scheduler_candidate_id, propensity, propensity_kind, learner_pick,
  fallback, mixture_weights_json, model_distributions_json, sensor_answers_json, question_set_version,
  model_ids_json, card_hash, similar_decision_ids_json, latency_ms, cost_usd, detail_json, created_at
)
SELECT
  id, receipt_key, decision_kind, surface, mode, policy, algorithm_version, log_version, session_id,
  parent_decision_id, scheduler_slate_id, controller_decision_id, snapshot_hash, design, seed,
  candidates_json, exclusions_json, candidate_count, chosen_ref, chosen_practice_item_id,
  chosen_learning_object_id, chosen_scheduler_candidate_id, propensity, propensity_kind, learner_pick,
  fallback, mixture_weights_json, model_distributions_json, sensor_answers_json, question_set_version,
  model_ids_json, card_hash, similar_decision_ids_json, latency_ms, cost_usd, detail_json, created_at
FROM router_decisions;

DROP TABLE router_decisions;
ALTER TABLE router_decisions__202 RENAME TO router_decisions;

CREATE INDEX router_decisions_session ON router_decisions(session_id, created_at, id);
CREATE INDEX router_decisions_slate ON router_decisions(scheduler_slate_id);
CREATE INDEX router_decisions_candidate ON router_decisions(chosen_scheduler_candidate_id);
CREATE INDEX router_decisions_parent ON router_decisions(parent_decision_id);
CREATE INDEX router_decisions_controller ON router_decisions(controller_decision_id);

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

ALTER TABLE router_outcomes ADD COLUMN action_binding TEXT CHECK (
  action_binding IS NULL OR action_binding IN ('presentation', 'candidate', 'session_rule')
);
ALTER TABLE router_outcomes ADD COLUMN r_next_reference_status TEXT;
ALTER TABLE router_outcomes ADD COLUMN r_cold_reference_status TEXT;

-- One row per plan item served (DL1's item_served receipt), in the same
-- transaction. The block's router decision (attention_blocks.decision_ref)
-- and, when that decision named one, the staged controller decision are
-- copied so a forecast or an outcome joins without re-reading the block.
CREATE TABLE plan_presentations (
  id TEXT PRIMARY KEY,
  block_id TEXT NOT NULL REFERENCES attention_blocks(id),
  router_decision_id TEXT REFERENCES router_decisions(id),
  controller_decision_id TEXT,
  practice_item_id TEXT NOT NULL,
  position INTEGER CHECK (position IS NULL OR position >= 1),
  -- chooser | requested | followup | learner_pick | open_list
  origin TEXT NOT NULL,
  scheduler_candidate_id TEXT,
  -- A committed probe presentation the item was served under (none yet: the
  -- plan does not open probe presentations; kept for that join).
  probe_presentation_id TEXT,
  session_id TEXT,
  served_at TEXT NOT NULL,
  UNIQUE (block_id, practice_item_id)
);
CREATE INDEX plan_presentations_decision ON plan_presentations(router_decision_id);
CREATE INDEX plan_presentations_controller ON plan_presentations(controller_decision_id);
CREATE INDEX plan_presentations_session_item ON plan_presentations(session_id, practice_item_id);

CREATE TRIGGER plan_presentations_no_update
BEFORE UPDATE ON plan_presentations
BEGIN
    SELECT RAISE(ABORT, 'plan_presentations is append-only');
END;

CREATE TRIGGER plan_presentations_no_delete
BEFORE DELETE ON plan_presentations
BEGIN
    SELECT RAISE(ABORT, 'plan_presentations is append-only');
END;

ALTER TABLE practice_attempts ADD COLUMN plan_presentation_id TEXT REFERENCES plan_presentations(id);
CREATE UNIQUE INDEX practice_attempts_plan_presentation
  ON practice_attempts(plan_presentation_id) WHERE plan_presentation_id IS NOT NULL;

CREATE TABLE router_decision_payloads (
  id TEXT PRIMARY KEY,
  decision_id TEXT NOT NULL REFERENCES router_decisions(id),
  -- card (R2a); R2b adds the model requests and their raw responses.
  kind TEXT NOT NULL CHECK (
    kind IN ('card', 'decider_request', 'decider_response', 'llm_request', 'llm_response')
  ),
  format_version TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  content_json TEXT,
  content_text TEXT,
  created_at TEXT NOT NULL,
  UNIQUE (decision_id, kind)
);
CREATE INDEX router_decision_payloads_created ON router_decision_payloads(created_at);
