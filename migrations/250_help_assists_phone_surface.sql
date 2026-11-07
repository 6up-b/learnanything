-- Mobile v2 stage V3 (docs/specs/spec_mobile_frontend_v2.md §8's V3 row; V2's landing ruling R5:
-- "the help_assists.surface CHECK widening for phone_practice goes into V3"; docs/reviews/phone-v2-v3-probes.md).
--
-- help_assists (RAW_LEDGER, migration 210; rebuilt last by 232) gains the surface 'phone_practice', so an
-- item's own hint revealed on the phone (practice.record_hint_reveal under a phone origin, mobile v2 J16) records
-- its device on the row itself. Until now the row kept 'practice' and its device was recoverable only through the
-- attempt's entry_surface. Nothing reads the surface to decide anything: the readers tell 'workbench' from the
-- rest, and the report counts by surface. Never evidence (standing constraint H2).
--
-- SQLite cannot widen a CHECK in place, so the table is rebuilt temp-then-rename under
-- PRAGMA foreign_keys = OFF with every row and id preserved (232's pattern): the same 63 columns, defaults and
-- CHECKs (surface widened by one value), the same six indexes and the two append-only triggers, recreated with the
-- same names and definitions (DROP TABLE removes them). No table's foreign key names help_assists; its own
-- (workbench_sessions, practice_attempts) are unchanged, and the runner's foreign_key_check runs before the
-- migration commits.
PRAGMA foreign_keys = OFF;

CREATE TABLE help_assists__250 (
  id TEXT PRIMARY KEY,
  -- Mobile v2 V3 (migration 250) adds 'phone_practice': an item's own hint revealed on the phone
  -- (practice.record_hint_reveal under a phone origin). The desktop's rows stay 'practice'.
  surface TEXT NOT NULL CHECK (surface IN ('practice', 'workbench', 'guided_redo', 'tutor', 'phone_practice')),
  -- The Reader's assist kind (its §5.7). Outside the workbench the hint
  -- service writes 'hint' and, for an answer to a discriminating question,
  -- 'discriminate_answer' (hints spec §16.4 item 1); 'bridge', 'example' and
  -- 'compare_methods' are RW2c's.
  assist_kind TEXT NOT NULL CHECK (assist_kind IN (
    'hint', 'check', 'discriminate_answer', 'bridge', 'example', 'compare_methods', 'feedback', 'figure'
  )),
  -- NULL only for a workbench problem not yet bound to an item (RW2a's
  -- workbench_sessions.practice_item_id, UX S2).
  practice_item_id TEXT,
  practice_item_hash TEXT,
  -- The workbench's practice session is filled at Submit (NULL until then,
  -- set once); every other surface writes it with the row.
  practice_session_id TEXT,
  workbench_session_id TEXT REFERENCES workbench_sessions(id),
  -- The attempt the assist was part of, filled at submit (submit_attempt,
  -- submit_dont_know); NULL while the attempt is open or if it never was.
  attempt_id TEXT REFERENCES practice_attempts(id),
  -- The client's stable submission key for the attempt the assist belongs to
  -- (practice_attempts.submission_id once it commits). The attach at submit,
  -- and its repair on a retried submit or a recovery, match on this key
  -- alone, so a row is never swept into another submission's attempt.
  submission_id TEXT,
  -- The form the help took (hints spec §4.2's table: its eleven plus
  -- continuation). NULL on rows that are not hints (a check, a bridge).
  hint_kind TEXT CHECK (hint_kind IS NULL OR hint_kind IN (
    'approach_question', 'discriminating', 'localize', 'waypoint', 'subgoal_plan', 'next_step',
    'error_specific', 'worked_parallel', 'authored', 'continuation', 'worked_chunk', 'walkthrough',
    'explore_figure'
  )),
  -- The Reader's ladder: how much of the solution the help does (1-5). The
  -- level alone decides evidence (hints spec §5).
  level INTEGER CHECK (level IS NULL OR level BETWEEN 1 AND 5),
  -- The workbench's suggested rung, and whose level it was.
  offered_level INTEGER CHECK (offered_level IS NULL OR offered_level BETWEEN 1 AND 5),
  level_source TEXT CHECK (level_source IS NULL OR level_source IN ('offered', 'learner_pick')),
  -- Map edges ahead of the placement a waypoint points (hints spec §4.2).
  horizon INTEGER CHECK (horizon IS NULL OR horizon >= 1),
  route_id TEXT,
  from_node_id TEXT,
  target_node_id TEXT,
  -- approach_maps.id (H1); each map row is one version.
  map_id TEXT,
  strategy TEXT,
  -- NULL for an authored reveal: the item has the text.
  body_md TEXT,
  -- 0-based index into the item's authored hints (an authored reveal).
  authored_index INTEGER CHECK (authored_index IS NULL OR authored_index >= 0),
  -- The learner's work when the help was requested: a sha256 of the text and
  -- its length (the text itself is never stored here).
  work_hash TEXT,
  work_chars INTEGER CHECK (work_chars IS NULL OR work_chars >= 0),
  placement_json TEXT,
  chooser TEXT NOT NULL CHECK (chooser IN ('decider', 'fallback', 'learner_pick', 'none')),
  options_json TEXT,
  probabilities_json TEXT,
  -- The option the chooser drew, kept apart from the served kind so a
  -- contract downgrade keeps both (hints spec §4.2, §6.2).
  drawn_option_json TEXT,
  -- The probability the drawn option was drawn with (the chooser's joint or
  -- conditional draw; on a bridge or example row, RW2c's passage draw).
  propensity REAL CHECK (propensity IS NULL OR (propensity >= 0.0 AND propensity <= 1.0)),
  seed TEXT,
  policy_version TEXT,
  question_set_version TEXT,
  state_hash TEXT,
  -- RW5d P3 adds 'take_step': a cold check's take step for a figure (the
  -- attempt converts first; the row's id is the token later requests carry).
  request TEXT CHECK (request IS NULL OR request IN ('more', 'feedback', 'book_way', 'smaller_step', 'take_step')),
  feedback_text TEXT,
  -- The "doesn't connect" shortcut (the first draft's different_approach is
  -- withdrawn: it read the opposite way; hints spec §4.2, Reader C2).
  feedback_shortcut TEXT CHECK (feedback_shortcut IS NULL OR feedback_shortcut IN (
    'not_where_stuck', 'too_big', 'learner_route', 'notation'
  )),
  contract_failures_json TEXT,
  leak_flags_json TEXT,
  shown INTEGER NOT NULL CHECK (shown IN (0, 1)),
  -- Who counts the assist into the attempt's hints_used: the client (the
  -- authored hints it revealed itself) or the server's fold at submit. NULL:
  -- counted by neither (a discriminating answer, a feedback row).
  counted_by TEXT CHECK (counted_by IS NULL OR counted_by IN ('client', 'server')),
  model TEXT,
  prompt_version TEXT,
  input_hash TEXT,
  latency_ms INTEGER CHECK (latency_ms IS NULL OR latency_ms >= 0),
  requested_at TEXT NOT NULL,
  shown_at TEXT,
  -- When the submission reached the sidecar, before any grading: the end of
  -- "hint shown -> submit" (practice_attempts.created_at is stamped when the
  -- grade is applied, after the grader's latency). NULL when unknown.
  submitted_at TEXT,
  -- The client's open-to-submit seconds that same submission sent, stamped
  -- with submitted_at and only with it, so "seconds into the attempt" is
  -- measured on one basis: a grading fallback's retry sends a later latency
  -- (practice_attempts.latency_seconds keeps the retry's) and replaces
  -- neither. NULL when the submission sent none or its time is unknown.
  submit_latency_seconds REAL CHECK (
    submit_latency_seconds IS NULL OR (submit_latency_seconds >= 0 AND submitted_at IS NOT NULL)
  ),
  -- The Reader workbench's columns (its §5.7).
  step_snapshot_json TEXT,
  step_verdicts_json TEXT,
  first_questionable_step_id TEXT,
  error_kind_guess TEXT,
  about_step_id TEXT,
  continue_from_step_id TEXT,
  rivals_json TEXT,
  predicted_answers_json TEXT,
  eig_nats REAL,
  feedback_step_id TEXT,
  cited_span_ids_json TEXT,
  retrieval_manifest_json TEXT,
  alternatives_json TEXT,
  -- Learner data-relax 2 (migration 230): the draft when the help was asked for.
  work_md TEXT,
  -- Reader RW5d P3 (this migration): the interactive_figures row a 'figure'
  -- assist opened (a soft reference, as map_id: the figure ledger is the
  -- figure service's and is rebuilt by its own migrations). NULL on every
  -- other row, and on a cold take step's row until its figure is delivered;
  -- set once (the trigger below).
  figure_id TEXT
);

INSERT INTO help_assists__250 (id, surface, assist_kind, practice_item_id, practice_item_hash, practice_session_id, workbench_session_id, attempt_id, submission_id, hint_kind, level, offered_level, level_source, horizon, route_id, from_node_id, target_node_id, map_id, strategy, body_md, authored_index, work_hash, work_chars, placement_json, chooser, options_json, probabilities_json, drawn_option_json, propensity, seed, policy_version, question_set_version, state_hash, request, feedback_text, feedback_shortcut, contract_failures_json, leak_flags_json, shown, counted_by, model, prompt_version, input_hash, latency_ms, requested_at, shown_at, submitted_at, submit_latency_seconds, step_snapshot_json, step_verdicts_json, first_questionable_step_id, error_kind_guess, about_step_id, continue_from_step_id, rivals_json, predicted_answers_json, eig_nats, feedback_step_id, cited_span_ids_json, retrieval_manifest_json, alternatives_json, work_md, figure_id)
SELECT id, surface, assist_kind, practice_item_id, practice_item_hash, practice_session_id, workbench_session_id, attempt_id, submission_id, hint_kind, level, offered_level, level_source, horizon, route_id, from_node_id, target_node_id, map_id, strategy, body_md, authored_index, work_hash, work_chars, placement_json, chooser, options_json, probabilities_json, drawn_option_json, propensity, seed, policy_version, question_set_version, state_hash, request, feedback_text, feedback_shortcut, contract_failures_json, leak_flags_json, shown, counted_by, model, prompt_version, input_hash, latency_ms, requested_at, shown_at, submitted_at, submit_latency_seconds, step_snapshot_json, step_verdicts_json, first_questionable_step_id, error_kind_guess, about_step_id, continue_from_step_id, rivals_json, predicted_answers_json, eig_nats, feedback_step_id, cited_span_ids_json, retrieval_manifest_json, alternatives_json, work_md, figure_id
FROM help_assists;

DROP TABLE help_assists;
ALTER TABLE help_assists__250 RENAME TO help_assists;

CREATE INDEX idx_help_assists_session_item ON help_assists(practice_session_id, practice_item_id, requested_at);
CREATE INDEX idx_help_assists_attempt ON help_assists(attempt_id);
CREATE INDEX idx_help_assists_submission ON help_assists(submission_id, practice_item_id);
CREATE INDEX idx_help_assists_workbench ON help_assists(workbench_session_id, requested_at);
CREATE INDEX idx_help_assists_requested ON help_assists(surface, requested_at);
CREATE INDEX idx_help_assists_figure ON help_assists(figure_id);
CREATE TRIGGER help_assists_no_delete
BEFORE DELETE ON help_assists
BEGIN
  SELECT RAISE(ABORT, 'help_assists is append-only');
END;
CREATE TRIGGER help_assists_identity_fixed
BEFORE UPDATE ON help_assists
WHEN NEW.id IS NOT OLD.id
  OR NEW.surface IS NOT OLD.surface
  OR NEW.assist_kind IS NOT OLD.assist_kind
  OR NEW.requested_at IS NOT OLD.requested_at
  OR (OLD.practice_session_id IS NOT NULL AND NEW.practice_session_id IS NOT OLD.practice_session_id)
  OR (OLD.workbench_session_id IS NOT NULL AND NEW.workbench_session_id IS NOT OLD.workbench_session_id)
  OR (OLD.submission_id IS NOT NULL AND NEW.submission_id IS NOT OLD.submission_id)
  OR (OLD.submitted_at IS NOT NULL AND NEW.submitted_at IS NOT OLD.submitted_at)
  OR (OLD.submitted_at IS NOT NULL AND NEW.submit_latency_seconds IS NOT OLD.submit_latency_seconds)
  OR (OLD.attempt_id IS NOT NULL AND NEW.attempt_id IS NOT OLD.attempt_id)
  OR (OLD.figure_id IS NOT NULL AND NEW.figure_id IS NOT OLD.figure_id)
BEGIN
  SELECT RAISE(ABORT, 'help_assists: identity columns and a binding once set are fixed');
END;

PRAGMA foreign_keys = ON;
