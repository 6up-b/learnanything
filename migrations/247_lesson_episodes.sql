-- Teacher TE2-log: item 5's logging for lessons (spec_teacher_v1 §11.6, §11.9,
-- §18.1, §20 row TE2-log; docs/reviews/teacher-te2-log.md).
--
-- Additive: two new RECEIPT tables; no existing table changes. Written behind
-- [teacher] episode_log at every algorithm version (no successor, as RO0's
-- receipts): nothing serving, scheduling, certification or replay reads them.
-- Ids, numbers and enums only: a hypothesis's words stay in the turn's payload
-- (lesson_turn_payloads, WORKFLOW), and the row keeps their count, a hash and
-- the payload's turn id.
--
-- lesson_episodes (RECEIPT, append-only, closed once): one row per probe,
-- detour, gap and created goal LO (§11.9). TE2-log writes detours (the
-- teacher's note_detour, and 'unlogged' for a plan that inserts a node with no
-- note); probes, gaps and goal LOs are TE2's actions and use the same row. A row
-- is inserted when its episode opens, with everything known then (the prior
-- belief at the opening, the origin ids); its closing fields (closed_at, why,
-- the minutes from opening to closing and the outcome refs) move from NULL
-- exactly once, as lessons.closed_at does (the trigger below); nothing else is
-- ever updated and nothing is deleted.
--
-- lesson_activity_intervals (RECEIPT, append-only): the lesson screen's own
-- activity intervals (§11.6), sent through lesson.activity: each interval's
-- start and end on the client's clock, whether the screen was in the foreground
-- with input, when the client reported it (occurred_at) and when the sidecar
-- received it (received_at; RO0 row 5). One row per (lesson, screen session,
-- seq): a resent interval writes nothing. An interval that never arrives is
-- never filled in: its seq is missing, and the elapsed time no interval covers
-- is reported as unreported, never as active or idle.
CREATE TABLE lesson_episodes (
  id TEXT PRIMARY KEY,
  lesson_id TEXT NOT NULL REFERENCES lessons(id),
  kind TEXT NOT NULL CHECK (kind IN ('probe', 'detour', 'gap', 'goal_lo')),
  -- The lesson_turns row of the action that opened the episode (one episode per
  -- action: a recovered action writes nothing twice).
  opened_by TEXT NOT NULL UNIQUE,
  node_id TEXT,
  learning_object_id TEXT,
  opened_at TEXT NOT NULL,
  -- Hypothesis: for a probe the readings, for a detour the hypothesis, for a gap
  -- the gap in words; the words are in lesson_turn_payloads under
  -- hypothesis_payload_id, the row keeps their count and sha256.
  hypothesis_count INTEGER CHECK (hypothesis_count IS NULL OR hypothesis_count >= 0),
  hypothesis_hash TEXT,
  hypothesis_payload_id TEXT,
  -- Repair class: a detour's repair, or 'unlogged' (a plan that inserted a node
  -- with no note_detour); a gap's kind; null for a probe and a goal LO.
  repair_class TEXT CHECK (repair_class IS NULL OR repair_class IN (
    'repair_in_place', 'insert_foundation', 'reteach', 'unlogged', 'prerequisite', 'misconception')),
  -- Prior belief at the opening: the teacher's p (and its forecast receipt, for
  -- a probe), the brief's predicted success for the node with its interval and
  -- its source, the LO's mastery mean and variance, the open misconceptions and
  -- hypotheses on the LO (counts here, ids in open_ids_json).
  teacher_p REAL CHECK (teacher_p IS NULL OR (teacher_p >= 0.0 AND teacher_p <= 1.0)),
  teacher_forecast_receipt_id TEXT,
  predicted_success REAL CHECK (predicted_success IS NULL OR (predicted_success >= 0.0 AND predicted_success <= 1.0)),
  predicted_low REAL CHECK (predicted_low IS NULL OR (predicted_low >= 0.0 AND predicted_low <= 1.0)),
  predicted_high REAL CHECK (predicted_high IS NULL OR (predicted_high >= 0.0 AND predicted_high <= 1.0)),
  predicted_source TEXT,
  mastery_mean REAL,
  mastery_variance REAL CHECK (mastery_variance IS NULL OR mastery_variance >= 0.0),
  open_misconceptions INTEGER CHECK (open_misconceptions IS NULL OR open_misconceptions >= 0),
  open_hypotheses INTEGER CHECK (open_hypotheses IS NULL OR open_hypotheses >= 0),
  open_ids_json TEXT NOT NULL DEFAULT '{}',
  -- Origin ids: the lesson's origin (learner_pick, or router with the accepted
  -- offer's decision id), that decision's router_objective_traces id, the FG1
  -- generation job and item (a probe), the gap job, the created LO, and every
  -- policy_experiment_assignments id in force for the lesson's day.
  origin TEXT NOT NULL CHECK (origin IN ('learner_pick', 'router')),
  origin_decision_id TEXT,
  objective_trace_id TEXT,
  generation_job_id TEXT,
  generated_item_id TEXT,
  gap_job_id TEXT,
  created_lo_id TEXT,
  experiment_assignment_ids_json TEXT NOT NULL DEFAULT '[]',
  -- Closing (set once): when and why it closed; active and elapsed seconds from
  -- opening to closing, never blended (elapsed is closed_at - opened_at; active
  -- the foreground intervals inside it; unreported the elapsed time no interval
  -- covers; missing the seqs that never arrived); the outcome refs.
  closed_at TEXT,
  close_reason TEXT CHECK (close_reason IS NULL OR close_reason IN (
    'rechecked', 'answered', 'refused', 'retired', 'resolved', 'lesson_closed')),
  active_seconds REAL CHECK (active_seconds IS NULL OR active_seconds >= 0.0),
  elapsed_seconds REAL CHECK (elapsed_seconds IS NULL OR elapsed_seconds >= 0.0),
  unreported_seconds REAL CHECK (unreported_seconds IS NULL OR unreported_seconds >= 0.0),
  missing_intervals INTEGER CHECK (missing_intervals IS NULL OR missing_intervals >= 0),
  minutes_source TEXT CHECK (minutes_source IS NULL OR minutes_source IN ('lesson_activity', 'no_intervals')),
  outcome_attempt_id TEXT,
  outcome_correctness REAL CHECK (outcome_correctness IS NULL OR (outcome_correctness >= 0.0 AND outcome_correctness <= 1.0)),
  recheck_attempt_id TEXT,
  gap_result TEXT,
  lo_undo_state TEXT,
  episode_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  -- A detour always has its repair; a gap may have its kind; a probe and a goal LO have none.
  CHECK (CASE kind
    WHEN 'detour' THEN repair_class IS NOT NULL
      AND repair_class IN ('repair_in_place', 'insert_foundation', 'reteach', 'unlogged')
    WHEN 'gap' THEN repair_class IS NULL OR repair_class IN ('prerequisite', 'misconception')
    ELSE repair_class IS NULL END),
  CHECK ((closed_at IS NULL) = (close_reason IS NULL))
);
CREATE INDEX idx_lesson_episodes_lesson ON lesson_episodes(lesson_id, opened_at);
CREATE INDEX idx_lesson_episodes_lo ON lesson_episodes(learning_object_id, opened_at);

CREATE TRIGGER lesson_episodes_close_once
BEFORE UPDATE ON lesson_episodes
WHEN OLD.closed_at IS NOT NULL OR NEW.closed_at IS NULL
  OR NEW.id IS NOT OLD.id OR NEW.lesson_id IS NOT OLD.lesson_id OR NEW.kind IS NOT OLD.kind
  OR NEW.opened_by IS NOT OLD.opened_by OR NEW.node_id IS NOT OLD.node_id
  OR NEW.learning_object_id IS NOT OLD.learning_object_id OR NEW.opened_at IS NOT OLD.opened_at
  OR NEW.hypothesis_count IS NOT OLD.hypothesis_count OR NEW.hypothesis_hash IS NOT OLD.hypothesis_hash
  OR NEW.hypothesis_payload_id IS NOT OLD.hypothesis_payload_id OR NEW.repair_class IS NOT OLD.repair_class
  OR NEW.teacher_p IS NOT OLD.teacher_p OR NEW.teacher_forecast_receipt_id IS NOT OLD.teacher_forecast_receipt_id
  OR NEW.predicted_success IS NOT OLD.predicted_success OR NEW.predicted_low IS NOT OLD.predicted_low
  OR NEW.predicted_high IS NOT OLD.predicted_high OR NEW.predicted_source IS NOT OLD.predicted_source
  OR NEW.mastery_mean IS NOT OLD.mastery_mean OR NEW.mastery_variance IS NOT OLD.mastery_variance
  OR NEW.open_misconceptions IS NOT OLD.open_misconceptions OR NEW.open_hypotheses IS NOT OLD.open_hypotheses
  OR NEW.open_ids_json IS NOT OLD.open_ids_json OR NEW.origin IS NOT OLD.origin
  OR NEW.origin_decision_id IS NOT OLD.origin_decision_id OR NEW.objective_trace_id IS NOT OLD.objective_trace_id
  OR NEW.generation_job_id IS NOT OLD.generation_job_id OR NEW.generated_item_id IS NOT OLD.generated_item_id
  OR NEW.gap_job_id IS NOT OLD.gap_job_id OR NEW.created_lo_id IS NOT OLD.created_lo_id
  OR NEW.experiment_assignment_ids_json IS NOT OLD.experiment_assignment_ids_json
  OR NEW.episode_version IS NOT OLD.episode_version OR NEW.created_at IS NOT OLD.created_at
BEGIN
  SELECT RAISE(ABORT, 'lesson_episodes: only the closing fields may be set, once');
END;

CREATE TRIGGER lesson_episodes_no_delete
BEFORE DELETE ON lesson_episodes
BEGIN
  SELECT RAISE(ABORT, 'lesson_episodes is append-only');
END;

CREATE TABLE lesson_activity_intervals (
  id TEXT PRIMARY KEY,
  lesson_id TEXT NOT NULL REFERENCES lessons(id),
  -- One mount of the lesson screen (a client-made id); seq counts its intervals from 1.
  screen_session TEXT NOT NULL,
  seq INTEGER NOT NULL CHECK (seq >= 1),
  started_at TEXT NOT NULL,
  ended_at TEXT NOT NULL,
  seconds REAL NOT NULL CHECK (seconds >= 0.0),
  -- 1: the screen was in the foreground with input; 0: it was open but not.
  foreground INTEGER NOT NULL CHECK (foreground IN (0, 1)),
  occurred_at TEXT NOT NULL,
  received_at TEXT NOT NULL,
  receipt_version TEXT NOT NULL,
  CHECK (ended_at >= started_at),
  UNIQUE (lesson_id, screen_session, seq)
);
CREATE INDEX idx_lesson_activity_intervals_lesson ON lesson_activity_intervals(lesson_id, started_at);

CREATE TRIGGER lesson_activity_intervals_no_update
BEFORE UPDATE ON lesson_activity_intervals
BEGIN
  SELECT RAISE(ABORT, 'lesson_activity_intervals is append-only');
END;

CREATE TRIGGER lesson_activity_intervals_no_delete
BEFORE DELETE ON lesson_activity_intervals
BEGIN
  SELECT RAISE(ABORT, 'lesson_activity_intervals is append-only');
END;
