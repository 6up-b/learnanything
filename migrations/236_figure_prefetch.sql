-- Reader RW5d P5: figures ahead of need (docs/specs/spec_reader_show_me_figures_v1.md
-- §10b, §13.2b; docs/reviews/reader-rw5d-p5-prefetch.md).
--
-- Numbered 236: 235 is claimed by followups-nov2 (the help-fold successor);
-- the migration runner has no contiguity rule, and the number is confirmed at
-- landing.
--
-- figure_prefetch_decisions (RAW_LEDGER, append-only): one row per candidate
-- the prefetch service decided on: the trigger (plan, section, offer, lesson,
-- gap) and what it names, the request it would build (anchor, goal, who wrote
-- it, and its request key: the identity of that request before any build),
-- the judge's content probability, the decision model's version and the
-- digest of the posterior it sampled from, the draw's expected utility and
-- the propensity (the share of posterior draws that would build), the
-- minutes terms as used, the decision (build, skip, capped, deferred_power,
-- deferred_plan) and the structural horizon. Set once each, by the service,
-- and never changed after: request_id and input_hash (when the build stores
-- its request; input_hash is the figure's reuse key, spec §8.5), and outcome
-- with outcome_at (opened, asked, neither, void) at the horizon. Never
-- evidence: nothing in scoring, scheduling, projection or serving reads it.
--
-- plan_usage_pauses (RAW_LEDGER, append-only): every ChatGPT plan usage-limit
-- pause the prefetch service observed (the plan session keeps only the
-- latest), idempotently by hit_at, with the day's plan requests and the plan
-- tokens known by then: the pause-risk model's data.
--
-- figure_requests.prefetch_decision_id (carried since 224 with no foreign
-- key) gains its index.
CREATE TABLE figure_prefetch_decisions (
  id TEXT PRIMARY KEY,
  trigger_kind TEXT NOT NULL CHECK (trigger_kind IN ('plan', 'section', 'offer', 'lesson', 'gap')),
  trigger_ref TEXT NOT NULL,
  request_key TEXT NOT NULL,
  input_hash TEXT,
  anchor_json TEXT,
  goal_text TEXT,
  goal_author TEXT CHECK (goal_author IS NULL OR goal_author IN ('prefetch', 'teacher')),
  source_key TEXT,
  p_open_content REAL CHECK (p_open_content IS NULL OR (p_open_content >= 0 AND p_open_content <= 1)),
  model_version TEXT NOT NULL,
  posterior_digest TEXT NOT NULL,
  sampled_eu REAL,
  propensity REAL CHECK (propensity IS NULL OR (propensity >= 0 AND propensity <= 1)),
  w_minutes REAL,
  cost_minutes REAL,
  decision TEXT NOT NULL CHECK (decision IN ('build', 'skip', 'capped', 'deferred_power', 'deferred_plan')),
  request_id TEXT,
  horizon_kind TEXT NOT NULL CHECK (horizon_kind IN ('plan_day_ended', 'section_read', 'lesson_closed',
                                                     'thread_closed', 'gap_closed')),
  outcome TEXT CHECK (outcome IS NULL OR outcome IN ('opened', 'asked', 'neither', 'void')),
  outcome_at TEXT,
  created_at TEXT NOT NULL,
  CHECK (goal_text IS NULL OR goal_author IS NOT NULL),
  CHECK ((outcome IS NULL) = (outcome_at IS NULL))
);
CREATE INDEX idx_figure_prefetch_decisions_created ON figure_prefetch_decisions(created_at);
CREATE INDEX idx_figure_prefetch_decisions_key ON figure_prefetch_decisions(request_key, created_at);
CREATE INDEX idx_figure_prefetch_decisions_open ON figure_prefetch_decisions(outcome) WHERE outcome IS NULL;

CREATE TRIGGER figure_prefetch_decisions_no_delete
BEFORE DELETE ON figure_prefetch_decisions
BEGIN
  SELECT RAISE(ABORT, 'figure_prefetch_decisions is append-only');
END;

-- Only NULL -> value, once each, for request_id, input_hash, outcome and
-- outcome_at; every other column is fixed at insert.
CREATE TRIGGER figure_prefetch_decisions_set_once
BEFORE UPDATE ON figure_prefetch_decisions
WHEN (OLD.request_id IS NOT NULL AND NEW.request_id IS NOT OLD.request_id)
  OR (OLD.input_hash IS NOT NULL AND NEW.input_hash IS NOT OLD.input_hash)
  OR (OLD.outcome IS NOT NULL AND NEW.outcome IS NOT OLD.outcome)
  OR (OLD.outcome_at IS NOT NULL AND NEW.outcome_at IS NOT OLD.outcome_at)
  OR NEW.id IS NOT OLD.id
  OR NEW.trigger_kind IS NOT OLD.trigger_kind
  OR NEW.trigger_ref IS NOT OLD.trigger_ref
  OR NEW.request_key IS NOT OLD.request_key
  OR NEW.anchor_json IS NOT OLD.anchor_json
  OR NEW.goal_text IS NOT OLD.goal_text
  OR NEW.goal_author IS NOT OLD.goal_author
  OR NEW.source_key IS NOT OLD.source_key
  OR NEW.p_open_content IS NOT OLD.p_open_content
  OR NEW.model_version IS NOT OLD.model_version
  OR NEW.posterior_digest IS NOT OLD.posterior_digest
  OR NEW.sampled_eu IS NOT OLD.sampled_eu
  OR NEW.propensity IS NOT OLD.propensity
  OR NEW.w_minutes IS NOT OLD.w_minutes
  OR NEW.cost_minutes IS NOT OLD.cost_minutes
  OR NEW.decision IS NOT OLD.decision
  OR NEW.horizon_kind IS NOT OLD.horizon_kind
  OR NEW.created_at IS NOT OLD.created_at
BEGIN
  SELECT RAISE(ABORT, 'figure_prefetch_decisions is append-only (request_id, input_hash and the outcome are set once)');
END;

CREATE TABLE plan_usage_pauses (
  id TEXT PRIMARY KEY,
  hit_at TEXT NOT NULL UNIQUE,
  reset_at TEXT,
  plan_requests_today INTEGER NOT NULL DEFAULT 0 CHECK (plan_requests_today >= 0),
  plan_tokens_today_known INTEGER NOT NULL DEFAULT 0 CHECK (plan_tokens_today_known >= 0),
  observed_at TEXT NOT NULL
);

CREATE TRIGGER plan_usage_pauses_no_delete
BEFORE DELETE ON plan_usage_pauses
BEGIN
  SELECT RAISE(ABORT, 'plan_usage_pauses is append-only');
END;

CREATE TRIGGER plan_usage_pauses_no_update
BEFORE UPDATE ON plan_usage_pauses
BEGIN
  SELECT RAISE(ABORT, 'plan_usage_pauses is append-only');
END;

CREATE INDEX idx_figure_requests_prefetch_decision ON figure_requests(prefetch_decision_id)
  WHERE prefetch_decision_id IS NOT NULL;
