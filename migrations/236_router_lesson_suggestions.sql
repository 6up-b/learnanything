-- Teacher TE1b: the router suggests lessons, the learner opts in
-- (spec_teacher_v1 §15.1, §18.1; docs/reviews/teacher-te1b-router-suggestions.md).
--
-- Numbered 236 on its branch: main's head is TE1's 234, and followups-nov2's
-- 235 lands first (the migration runner has no contiguity rule); renumbered
-- at landing if another migration takes 236.
--
-- 1. router_decisions (RAW_LEDGER) is rebuilt so decision_kind also admits
--    'lesson_suggestion': the day's instruct(lesson) draw (shown or not, with
--    its exact propensity). SQLite cannot widen a CHECK in place, so the
--    append-only ledger is rebuilt temp-then-rename with every row and id
--    preserved, under PRAGMA foreign_keys = OFF (202's precedent, the same
--    table): DROP TABLE removes the old indexes and triggers, which are
--    recreated on the renamed table with the same names and definitions; the
--    foreign keys that name the table (its own parent_decision_id,
--    plan_presentations, router_decision_payloads, retrieval_interventions)
--    resolve to the rebuilt one, and the runner's foreign_key_check runs
--    before the migration commits. The same columns, CHECKs, indexes and
--    append-only triggers otherwise.
--
-- 2. router_suggestion_responses (RAW_LEDGER, append-only): the learner's one
--    response to a shown suggestion: accepted (Start), chose_alternative (one
--    of the card's up to two alternatives; candidate_ref names it), declined
--    ("Not now") or ignored (no response by the end of the day the card was
--    shown, recorded at the next suggestion step), its time, and the lesson
--    that opened when one did. One response per decision (UNIQUE): the
--    acceptance model and the decline recovery replay this ledger (no derived
--    table; every reader replays it).
PRAGMA foreign_keys = OFF;

CREATE TABLE router_decisions__236 (
  id TEXT PRIMARY KEY,
  receipt_key TEXT NOT NULL UNIQUE,
  decision_kind TEXT NOT NULL CHECK (
    decision_kind IN ('today_offer', 'staged_p2', 'learner_pick', 'plan_block', 'plan_interrupt',
                      'lesson_suggestion')
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
INSERT INTO router_decisions__236 (
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
ALTER TABLE router_decisions__236 RENAME TO router_decisions;

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

CREATE TABLE router_suggestion_responses (
  id TEXT PRIMARY KEY,
  decision_id TEXT NOT NULL UNIQUE REFERENCES router_decisions(id),
  response TEXT NOT NULL CHECK (response IN ('accepted', 'chose_alternative', 'declined', 'ignored')),
  -- The candidate the response is about: the card's suggestion (accepted,
  -- declined, ignored) or the alternative the learner picked.
  candidate_ref TEXT NOT NULL,
  learning_object_ids_json TEXT NOT NULL,
  -- The lesson that opened (accepted or chose_alternative), when one did.
  lesson_id TEXT,
  session_id TEXT,
  responded_at TEXT NOT NULL,
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  CHECK (lesson_id IS NULL OR response IN ('accepted', 'chose_alternative'))
);
CREATE INDEX idx_router_suggestion_responses_at ON router_suggestion_responses(responded_at);

CREATE TRIGGER router_suggestion_responses_no_update
BEFORE UPDATE ON router_suggestion_responses
BEGIN
    SELECT RAISE(ABORT, 'router_suggestion_responses is append-only');
END;

CREATE TRIGGER router_suggestion_responses_no_delete
BEFORE DELETE ON router_suggestion_responses
BEGIN
    SELECT RAISE(ABORT, 'router_suggestion_responses is append-only');
END;

PRAGMA foreign_keys = ON;
