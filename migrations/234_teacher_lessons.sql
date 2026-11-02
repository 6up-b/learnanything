-- Teacher TE1: the first good lesson (spec_teacher_v1 §18.1, §20;
-- docs/reviews/teacher-te1-first-lesson.md).
--
-- Numbered 234: renumbered from 230 at landing, after learner data-relax-2's
-- 230, curriculum C5's 231, Reader RW5d P3's 232 and curriculum C2b's 233 (the
-- migration runner has no contiguity rule).
--
-- lessons (RAW_LEDGER): one row per lesson the learner started or accepted:
-- its driver, origin (a learner pick, or later a router decision), entry, the
-- goal and its LOs with how they were resolved, the doctrine and brief
-- versions, the route, when it opened, and, once, when and why it closed
-- (closed_at and close_reason move from NULL exactly once; nothing else is
-- ever updated).
--
-- lesson_turns (RAW_LEDGER, append-only): every step of the lesson in order:
-- who acted (teacher, learner or code), the action, whether it validated, its
-- references (attempt, item, commitment, tool call) and the hash of its
-- payload.
--
-- lesson_turn_payloads (WORKFLOW): the raw model and learner text of a turn,
-- as router_decision_payloads keeps router text (retention is the owner's;
-- replay never reads it).
--
-- lesson_plans (RAW_LEDGER, append-only): every outline the teacher stored,
-- versioned per lesson.
--
-- lesson_checks (RECEIPT, append-only): one row per lesson check that ended:
-- answered (its attempt, graded blind, and the mass it entered mastery at,
-- with every weight input: the tap, the hedge read, the predicted success and
-- its source just before the check, the learned mass, the pool weight and the
-- teacher's forecasts) or withdrawn (no attempt). Replay reads mass_applied
-- back through learner.lesson_weight.lesson_check_mass, so a past check's
-- mass never changes within a version.
--
-- lesson_receipts (RECEIPT, append-only): LessonReceiptV1 per closed lesson.
--
-- lesson_weight_state, lesson_weight_trace and confidence_calibration_state
-- (DERIVED, one replayer: learner.lesson_weight): the learned lesson-check
-- weight's posterior (§12.1), the forecast pool's weight (§12.2) and the
-- tap/hedge recalibration (LP-min), with the per-update trace. Recomputed in
-- order from lesson_checks and practice_attempts, as of each check.
--
-- And source_tool_calls.caller_kind gains 'teacher' (a rebuild at the end of
-- this file, every row and id preserved).
CREATE TABLE lessons (
  id TEXT PRIMARY KEY,
  driver TEXT NOT NULL CHECK (driver = 'desktop' OR driver LIKE 'chat:%'),
  origin TEXT NOT NULL CHECK (origin IN ('learner_pick', 'router')),
  origin_ref TEXT,
  entry TEXT NOT NULL CHECK (entry IN ('learning_object', 'reader_selection', 'new_topic')),
  goal_text TEXT NOT NULL,
  goal_json TEXT NOT NULL,
  learning_object_ids_json TEXT NOT NULL,
  doctrine_version TEXT NOT NULL,
  brief_version TEXT NOT NULL,
  route TEXT,
  model TEXT,
  algorithm_version TEXT NOT NULL,
  opened_at TEXT NOT NULL,
  closed_at TEXT,
  close_reason TEXT CHECK (close_reason IS NULL OR close_reason IN (
    'goal_reached', 'learner_stop', 'budget', 'plan_unavailable', 'teacher_contract_failure',
    'protection_changed')),
  CHECK ((closed_at IS NULL) = (close_reason IS NULL))
);
CREATE INDEX idx_lessons_opened ON lessons(opened_at);

CREATE TRIGGER lessons_close_once
BEFORE UPDATE ON lessons
WHEN OLD.closed_at IS NOT NULL
  OR NEW.id IS NOT OLD.id OR NEW.driver IS NOT OLD.driver OR NEW.origin IS NOT OLD.origin
  OR NEW.origin_ref IS NOT OLD.origin_ref OR NEW.entry IS NOT OLD.entry OR NEW.goal_text IS NOT OLD.goal_text
  OR NEW.goal_json IS NOT OLD.goal_json OR NEW.learning_object_ids_json IS NOT OLD.learning_object_ids_json
  OR NEW.doctrine_version IS NOT OLD.doctrine_version OR NEW.brief_version IS NOT OLD.brief_version
  OR NEW.route IS NOT OLD.route OR NEW.model IS NOT OLD.model
  OR NEW.algorithm_version IS NOT OLD.algorithm_version OR NEW.opened_at IS NOT OLD.opened_at
BEGIN
  SELECT RAISE(ABORT, 'lessons: only closed_at and close_reason may be set, once');
END;

CREATE TRIGGER lessons_no_delete
BEFORE DELETE ON lessons
BEGIN
  SELECT RAISE(ABORT, 'lessons is a ledger');
END;

CREATE TABLE lesson_turns (
  id TEXT PRIMARY KEY,
  lesson_id TEXT NOT NULL REFERENCES lessons(id),
  seq INTEGER NOT NULL CHECK (seq >= 1),
  actor TEXT NOT NULL CHECK (actor IN ('teacher', 'learner', 'code')),
  action TEXT NOT NULL,
  validation TEXT NOT NULL CHECK (validation IN ('ok', 'invalid', 'refused', 'withheld')),
  refs_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT,
  created_at TEXT NOT NULL,
  UNIQUE (lesson_id, seq)
);

CREATE TRIGGER lesson_turns_no_update
BEFORE UPDATE ON lesson_turns
BEGIN
  SELECT RAISE(ABORT, 'lesson_turns is append-only');
END;

CREATE TRIGGER lesson_turns_no_delete
BEFORE DELETE ON lesson_turns
BEGIN
  SELECT RAISE(ABORT, 'lesson_turns is append-only');
END;

CREATE TABLE lesson_turn_payloads (
  turn_id TEXT PRIMARY KEY REFERENCES lesson_turns(id),
  lesson_id TEXT NOT NULL REFERENCES lessons(id),
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_lesson_turn_payloads_lesson ON lesson_turn_payloads(lesson_id, created_at);

CREATE TABLE lesson_plans (
  id TEXT PRIMARY KEY,
  lesson_id TEXT NOT NULL REFERENCES lessons(id),
  version INTEGER NOT NULL CHECK (version >= 1),
  outline_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (lesson_id, version)
);

CREATE TRIGGER lesson_plans_no_update
BEFORE UPDATE ON lesson_plans
BEGIN
  SELECT RAISE(ABORT, 'lesson_plans is append-only');
END;

CREATE TRIGGER lesson_plans_no_delete
BEFORE DELETE ON lesson_plans
BEGIN
  SELECT RAISE(ABORT, 'lesson_plans is append-only');
END;

CREATE TABLE lesson_checks (
  id TEXT PRIMARY KEY,
  lesson_id TEXT NOT NULL REFERENCES lessons(id),
  node_id TEXT NOT NULL,
  check_ref TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  minted_item_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('answered', 'withdrawn')),
  attempt_id TEXT UNIQUE,
  correctness REAL CHECK (correctness IS NULL OR (correctness >= 0.0 AND correctness <= 1.0)),
  tap INTEGER CHECK (tap IS NULL OR tap BETWEEN 1 AND 5),
  hedge TEXT CHECK (hedge IS NULL OR hedge IN ('hedged', 'confident')),
  predicted_success REAL CHECK (predicted_success IS NULL OR (predicted_success >= 0.0 AND predicted_success <= 1.0)),
  predicted_source TEXT,
  mass_learned REAL CHECK (mass_learned IS NULL OR (mass_learned > 0.0 AND mass_learned < 1.0)),
  mass_applied REAL CHECK (mass_applied IS NULL OR (mass_applied >= 0.0 AND mass_applied <= 1.0)),
  forecast_correct_key TEXT,
  forecast_retained_key TEXT,
  weight_inputs_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  CHECK ((status = 'answered') = (attempt_id IS NOT NULL)),
  CHECK (status = 'withdrawn' OR mass_applied IS NOT NULL)
);
CREATE INDEX idx_lesson_checks_lo ON lesson_checks(learning_object_id, created_at);
CREATE INDEX idx_lesson_checks_lesson ON lesson_checks(lesson_id, created_at);

CREATE TRIGGER lesson_checks_no_update
BEFORE UPDATE ON lesson_checks
BEGIN
  SELECT RAISE(ABORT, 'lesson_checks is append-only');
END;

CREATE TRIGGER lesson_checks_no_delete
BEFORE DELETE ON lesson_checks
BEGIN
  SELECT RAISE(ABORT, 'lesson_checks is append-only');
END;

CREATE TABLE lesson_receipts (
  lesson_id TEXT PRIMARY KEY REFERENCES lessons(id),
  receipt_version TEXT NOT NULL,
  close_reason TEXT NOT NULL,
  receipt_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TRIGGER lesson_receipts_no_update
BEFORE UPDATE ON lesson_receipts
BEGIN
  SELECT RAISE(ABORT, 'lesson_receipts is append-only');
END;

CREATE TRIGGER lesson_receipts_no_delete
BEFORE DELETE ON lesson_receipts
BEGIN
  SELECT RAISE(ABORT, 'lesson_receipts is append-only');
END;

CREATE TABLE lesson_weight_state (
  family TEXT PRIMARY KEY,
  state_json TEXT NOT NULL,
  updates INTEGER NOT NULL DEFAULT 0 CHECK (updates >= 0),
  through_at TEXT,
  priors_version TEXT NOT NULL
);

CREATE TABLE lesson_weight_trace (
  id TEXT PRIMARY KEY,
  seq INTEGER NOT NULL UNIQUE CHECK (seq >= 1),
  kind TEXT NOT NULL CHECK (kind IN ('mass', 'weight_update', 'pool_update')),
  lesson_check_id TEXT,
  resolving_attempt_id TEXT,
  learning_object_id TEXT,
  at TEXT NOT NULL,
  detail_json TEXT NOT NULL
);
CREATE INDEX idx_lesson_weight_trace_check ON lesson_weight_trace(lesson_check_id);

CREATE TABLE confidence_calibration_state (
  family TEXT PRIMARY KEY CHECK (family IN ('tap', 'hedge')),
  state_json TEXT NOT NULL,
  updates INTEGER NOT NULL DEFAULT 0 CHECK (updates >= 0),
  through_at TEXT,
  priors_version TEXT NOT NULL
);

-- source_tool_calls.caller_kind gains 'teacher' (spec_teacher_v1 §9.1: the
-- lesson's find_sources and find_practice requests are recorded under caller
-- kind teacher, as the tutor's are under tutor). SQLite cannot widen a CHECK in
-- place, so the table is rebuilt temp-then-rename with every row and id
-- preserved, under PRAGMA foreign_keys = OFF, as migrations 208 and 212 did:
-- DROP TABLE removes the old indexes and triggers, which are recreated on the
-- renamed table with the same names and definitions; the table's own parent_id
-- foreign key names source_tool_calls and resolves to the rebuilt table, and the
-- runner's foreign_key_check runs before the migration commits. The same
-- columns, defaults, CHECKs, indexes and append-only triggers.
PRAGMA foreign_keys = OFF;

CREATE TABLE source_tool_calls__230 (
  id TEXT PRIMARY KEY,
  parent_id TEXT REFERENCES source_tool_calls(id),
  row_kind TEXT NOT NULL CHECK (row_kind IN ('request', 'run')),
  created_at TEXT NOT NULL,
  caller_kind TEXT NOT NULL CHECK (caller_kind IN ('tutor', 'router', 'agent', 'teacher')),
  caller_ref TEXT,
  -- The stored caller context the policy was derived from (re-read at run time,
  -- so the policy cannot change between the answer and the run).
  context_json TEXT NOT NULL,
  policy TEXT NOT NULL,
  tool TEXT NOT NULL CHECK (tool IN ('find_practice', 'find_sources', 'compare_sources', 'find_facets',
                                     'practice_availability')),
  arguments_json TEXT NOT NULL,
  dropped_json TEXT NOT NULL DEFAULT '[]',
  ledger_id TEXT,
  status TEXT NOT NULL CHECK (status IN ('requested', 'refused', 'ran', 'failed')),
  result_ref TEXT,
  result_keys_json TEXT NOT NULL DEFAULT '[]',
  source_versions_json TEXT NOT NULL DEFAULT '{}',
  model TEXT,
  prompt_version TEXT,
  latency_ms INTEGER,
  cost_json TEXT,
  CHECK ((row_kind = 'request' AND parent_id IS NULL AND status IN ('requested', 'refused'))
         OR (row_kind = 'run' AND parent_id IS NOT NULL AND status IN ('ran', 'failed')))
);

INSERT INTO source_tool_calls__230 (
  id, parent_id, row_kind, created_at, caller_kind, caller_ref, context_json, policy, tool, arguments_json,
  dropped_json, ledger_id, status, result_ref, result_keys_json, source_versions_json, model, prompt_version,
  latency_ms, cost_json
)
SELECT
  id, parent_id, row_kind, created_at, caller_kind, caller_ref, context_json, policy, tool, arguments_json,
  dropped_json, ledger_id, status, result_ref, result_keys_json, source_versions_json, model, prompt_version,
  latency_ms, cost_json
FROM source_tool_calls;

DROP TABLE source_tool_calls;
ALTER TABLE source_tool_calls__230 RENAME TO source_tool_calls;

CREATE INDEX idx_source_tool_calls_parent ON source_tool_calls(parent_id);
CREATE INDEX idx_source_tool_calls_caller ON source_tool_calls(caller_kind, caller_ref, created_at);
CREATE TRIGGER source_tool_calls_no_update BEFORE UPDATE ON source_tool_calls
BEGIN SELECT RAISE(ABORT, 'source tool calls are append-only'); END;
CREATE TRIGGER source_tool_calls_no_delete BEFORE DELETE ON source_tool_calls
BEGIN SELECT RAISE(ABORT, 'source tool calls are append-only'); END;

PRAGMA foreign_keys = ON;
