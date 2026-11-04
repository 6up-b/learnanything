-- Follow-up generate and serve (FG1; docs/specs/spec_followup_generate_serve_v1.md).
--
-- Additive: new tables only, no existing row or table changes, and nothing replay
-- reads for scoring, FSRS, mastery or the projection.
--
-- 1. followup_workflows (WORKFLOW): one durable owner of one intervention, keyed to
--    the source attempt and the effective grade revision, with a stable id before
--    routing. Every Next and serve door reads it; predecessor insertion is withheld
--    only while it owns the attempt.
--
-- 2. followup_workflow_events (RECEIPT): every state move of a workflow, append-only,
--    so failure, skip, abandonment and fallback stay distinct outcomes.
--
-- 3. followup_generation_jobs (WORKFLOW): the durable lease-fenced queue of generation
--    work, apart from the strictly ordered diagnosis worker. One row per deduplicated
--    key (a workflow, an entered episode, a recorded need): that is the structural
--    bound on physical generation on a subscription route (spec §8).
--
-- 4. generated_probe_items (RAW_LEDGER): the one durable single-use identity (§4.2).
--    Not a naming convention, and not the generic codex_proposal origin.
--
-- 5. generated_probe_burns (RAW_LEDGER): the burn ledger. kind 'served' is the atomic
--    first-serve claim, keyed to item revision, surface and presentation; kind
--    'retired' retires a probe that was never served. One row per item and kind. Replay
--    and state sync read it; it persists after a rollback.
--
-- 6. router_decision_bindings (RECEIPT): router_decisions rows are append-only and FG1
--    decides before any item exists, so a separate appended row links a decision to the
--    workflow, the generated item and its presentations. Receipt parsing, outcome joins
--    and data capture's measurement follow it.
CREATE TABLE followup_workflows (
  id TEXT PRIMARY KEY,
  source_attempt_id TEXT NOT NULL REFERENCES practice_attempts(id),
  revision_key TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  session_id TEXT,
  surface TEXT NOT NULL,
  origin TEXT NOT NULL CHECK (origin IN ('practice', 'exam', 'block')),
  state TEXT NOT NULL
    CHECK (state IN ('pending', 'ready', 'waiting', 'refused', 'failed', 'skipped', 'settled')),
  settled_reason TEXT,
  lane TEXT CHECK (lane IN ('probe', 'practice') OR lane IS NULL),
  factor_id TEXT,
  decision_id TEXT,
  chosen_ref TEXT,
  practice_item_id TEXT,
  probe_candidate_id TEXT,
  hypothesis_set_id TEXT,
  probe_episode_id TEXT,
  presentation_id TEXT,
  feedback_held INTEGER NOT NULL DEFAULT 0 CHECK (feedback_held IN (0, 1)),
  feedback_released_at TEXT,
  release_reason TEXT,
  shown_anyway_at TEXT,
  exposed_at TEXT,
  next_requested_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (source_attempt_id, revision_key)
);
CREATE INDEX followup_workflows_state ON followup_workflows(state, updated_at);
CREATE INDEX followup_workflows_session ON followup_workflows(session_id, state);
CREATE INDEX followup_workflows_item ON followup_workflows(practice_item_id);

CREATE TABLE followup_workflow_events (
  id TEXT PRIMARY KEY,
  workflow_id TEXT NOT NULL REFERENCES followup_workflows(id),
  from_state TEXT,
  to_state TEXT NOT NULL,
  reason TEXT NOT NULL,
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);
CREATE INDEX followup_workflow_events_workflow ON followup_workflow_events(workflow_id, created_at);
CREATE TRIGGER followup_workflow_events_no_update
BEFORE UPDATE ON followup_workflow_events
BEGIN
    SELECT RAISE(ABORT, 'followup_workflow_events is append-only');
END;
CREATE TRIGGER followup_workflow_events_no_delete
BEFORE DELETE ON followup_workflow_events
BEGIN
    SELECT RAISE(ABORT, 'followup_workflow_events is append-only');
END;

CREATE TABLE followup_generation_jobs (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('workflow', 'entry_episode', 'need')),
  dedupe_key TEXT NOT NULL UNIQUE,
  workflow_id TEXT REFERENCES followup_workflows(id),
  probe_episode_id TEXT,
  need_id TEXT,
  state TEXT NOT NULL DEFAULT 'queued'
    CHECK (state IN ('queued', 'leased', 'done', 'failed', 'skipped')),
  attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  lease_owner TEXT,
  lease_expires_at TEXT,
  lease_epoch INTEGER NOT NULL DEFAULT 0,
  not_before TEXT,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX followup_generation_jobs_order ON followup_generation_jobs(state, created_at, id);

CREATE TABLE generated_probe_items (
  practice_item_id TEXT PRIMARY KEY,
  item_revision TEXT NOT NULL,
  source TEXT NOT NULL CHECK (source IN ('workflow', 'entry', 'mint', 'batch', 'manual')),
  workflow_id TEXT REFERENCES followup_workflows(id),
  probe_episode_id TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX generated_probe_items_workflow ON generated_probe_items(workflow_id);
CREATE TRIGGER generated_probe_items_no_delete
BEFORE DELETE ON generated_probe_items
BEGIN
    SELECT RAISE(ABORT, 'generated_probe_items is append-only');
END;
CREATE TRIGGER generated_probe_items_no_update
BEFORE UPDATE ON generated_probe_items
BEGIN
    SELECT RAISE(ABORT, 'generated_probe_items is append-only');
END;

CREATE TABLE generated_probe_burns (
  id TEXT PRIMARY KEY,
  practice_item_id TEXT NOT NULL REFERENCES generated_probe_items(practice_item_id),
  kind TEXT NOT NULL CHECK (kind IN ('served', 'retired')),
  item_revision TEXT NOT NULL,
  surface TEXT,
  presentation_id TEXT,
  workflow_id TEXT,
  reason TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (practice_item_id, kind)
);
CREATE TRIGGER generated_probe_burns_no_update
BEFORE UPDATE ON generated_probe_burns
BEGIN
    SELECT RAISE(ABORT, 'generated_probe_burns is append-only');
END;
CREATE TRIGGER generated_probe_burns_no_delete
BEFORE DELETE ON generated_probe_burns
BEGIN
    SELECT RAISE(ABORT, 'generated_probe_burns is append-only');
END;

CREATE TABLE router_decision_bindings (
  id TEXT PRIMARY KEY,
  decision_id TEXT NOT NULL REFERENCES router_decisions(id),
  workflow_id TEXT NOT NULL REFERENCES followup_workflows(id),
  binding_kind TEXT NOT NULL
    CHECK (binding_kind IN ('item', 'presentation', 'plan_presentation', 'outcome')),
  practice_item_id TEXT,
  probe_presentation_id TEXT,
  plan_presentation_id TEXT,
  outcome TEXT,
  created_at TEXT NOT NULL,
  UNIQUE (decision_id, binding_kind)
);
CREATE INDEX router_decision_bindings_item ON router_decision_bindings(practice_item_id);
CREATE TRIGGER router_decision_bindings_no_update
BEFORE UPDATE ON router_decision_bindings
BEGIN
    SELECT RAISE(ABORT, 'router_decision_bindings is append-only');
END;
CREATE TRIGGER router_decision_bindings_no_delete
BEFORE DELETE ON router_decision_bindings
BEGIN
    SELECT RAISE(ABORT, 'router_decision_bindings is append-only');
END;
