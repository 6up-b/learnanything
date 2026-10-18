-- Adaptive hints H0: the shared help_assists table (spec_adaptive_hints_v1
-- §9, §10 H0, G-H17; spec_reader_workbench_v1 §5.7, §11, G64;
-- docs/reviews/adaptive-hints-H0.md).
--
-- One row per assist the learner was shown (or, with shown = 0, requested
-- and never shown: cancelled or withheld), on every surface: the practice
-- screen, the Reader workbench, guided redo and the tutor. Created ONCE with
-- every column and every CHECK value either spec writes, so neither spec's
-- later phase (H1-H5, RW2b, RW2c) rebuilds it. H0 writes only the practice
-- screen's authored-hint reveals (assist_kind 'hint', hint_kind 'authored',
-- chooser 'none', counted_by 'client', with the submission key, attempt and
-- submit time bound at submit); every other column is for later phases and
-- stays NULL until then.
--
-- RAW_LEDGER: the record of what help was shown, when, on what work. It is
-- never evidence. Evidence reaches an attempt only through
-- practice_attempts.hints_used / primed and reveal_events, with their
-- existing meaning (hints spec §5); replay and rebuild never read this table
-- (G-H10), no scoring, scheduling, projection or serving path does, and the
-- grader never sees it (standing constraint H2). Kill switch:
-- hints.telemetry_enabled (off: no row is written).
CREATE TABLE help_assists (
  id TEXT PRIMARY KEY,
  surface TEXT NOT NULL CHECK (surface IN ('practice', 'workbench', 'guided_redo', 'tutor')),
  -- The Reader's assist kind (its §5.7). Outside the workbench the hint
  -- service writes 'hint' and, for an answer to a discriminating question,
  -- 'discriminate_answer' (hints spec §16.4 item 1); 'bridge', 'example' and
  -- 'compare_methods' are RW2c's.
  assist_kind TEXT NOT NULL CHECK (assist_kind IN (
    'hint', 'check', 'discriminate_answer', 'bridge', 'example', 'compare_methods', 'feedback'
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
    'error_specific', 'worked_parallel', 'authored', 'continuation', 'worked_chunk', 'walkthrough'
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
  request TEXT CHECK (request IS NULL OR request IN ('more', 'feedback', 'book_way', 'smaller_step')),
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
  alternatives_json TEXT
);
-- The attach at submit and the per-attempt reads.
CREATE INDEX idx_help_assists_session_item ON help_assists(practice_session_id, practice_item_id, requested_at);
CREATE INDEX idx_help_assists_attempt ON help_assists(attempt_id);
CREATE INDEX idx_help_assists_submission ON help_assists(submission_id, practice_item_id);
CREATE INDEX idx_help_assists_workbench ON help_assists(workbench_session_id, requested_at);
CREATE INDEX idx_help_assists_requested ON help_assists(surface, requested_at);

-- A ledger: nothing is deleted, an assist's identity never changes, and a
-- binding, once made, is never moved. The bindings a later surface learns
-- only after the row is written (the workbench's practice session and
-- submission, filled at Submit; the attempt; the submit time) may each go
-- from NULL to a value once, never to another value or back to NULL.
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
  OR (OLD.attempt_id IS NOT NULL AND NEW.attempt_id IS NOT OLD.attempt_id)
BEGIN
  SELECT RAISE(ABORT, 'help_assists: identity columns and a binding once set are fixed');
END;
