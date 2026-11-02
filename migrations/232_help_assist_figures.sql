-- Reader RW5d P3 (spec_reader_show_me_figures_v1 §11.2-§11.4, §13.2, G-SM15..G-SM18;
-- docs/reviews/reader-rw5d-p3-figures-help.md): figures as a help kind.
--
-- Numbered 232: main's head is 230 and curriculum C5 holds 231 on its branch
-- (the migration runner is set-based, no contiguity rule; renumbered at
-- landing if another stage lands first).
--
-- help_assists (RAW_LEDGER, migration 210; work_md 230) is rebuilt to widen
-- three CHECKs and add one column:
--   * assist_kind gains 'figure': a figure built or opened on an open
--     attempt's host (the Ask panel's "show me", the workbench step, the
--     chooser's figure kind), or a cold check's take step for one;
--   * hint_kind gains 'explore_figure': the hint chooser's "a figure to
--     explore" (level 2), on the figure row it served;
--   * request gains 'take_step': the cold take step's row (§11.3);
--   * figure_id (nullable, soft reference to interactive_figures, set once).
-- A figure row counts as one hint-equivalent at Submit through the hint
-- service's existing fold (hints_used, its existing meaning; one per figure
-- per attempt), and never otherwise: no new evidence path. Still never
-- evidence itself: replay and rebuild never read this table, no scoring,
-- scheduling, projection or serving path does, and the grader never sees it
-- (standing constraint H2; figures are help, never certification).
--
-- SQLite cannot widen a CHECK in place, so the table is rebuilt
-- temp-then-rename under PRAGMA foreign_keys = OFF with every row and id
-- preserved (212's pattern). No table's foreign key names help_assists; its
-- own foreign keys (workbench_sessions, practice_attempts) are unchanged and
-- the runner's foreign_key_check runs before the migration commits. DROP
-- TABLE removes the old indexes and triggers, which are recreated with the
-- same names and definitions; the identity trigger also fixes figure_id once
-- set. The same columns (plus figure_id), defaults, CHECKs (three widened),
-- indexes (plus one on figure_id) and append-only triggers.
--
-- figure_predictions (RAW_LEDGER, migration 216) is rebuilt the same way
-- (Codex review F7, F9; spec §11.2: a prediction made inside an attempt is
-- "linked to the assist row"):
--   * extraction_id becomes nullable: an attempt host's illustration has no
--     home and no book (grounding none), and its predictions are kept with
--     no invented home (RW6a's "Last time here" reads by extraction and
--     never lists them);
--   * assist_id (nullable, soft reference to help_assists, set with the row):
--     the open attempt's figure row the prediction was made under, so the
--     diagnoser reads an attempt's predictions by its assist rows, never
--     every prediction on the figure;
--   * explained_at (nullable, set once with explanation_text): when "what
--     changed?" was written, so the diagnoser's trace is frozen at the
--     attempt (an explanation written after Submit never changes an earlier
--     attempt's context). Every earlier row keeps NULL in both.
-- No table's foreign key names figure_predictions; its own (figure_id to
-- interactive_figures) is unchanged. Same columns plus two, the same CHECKs
-- and UNIQUE, the index (plus one on assist_id) and the append-only
-- triggers (the explanation trigger also lets explained_at go from NULL to
-- a value with explanation_text, and fixes assist_id).
PRAGMA foreign_keys = OFF;

CREATE TABLE help_assists__232 (
  id TEXT PRIMARY KEY,
  surface TEXT NOT NULL CHECK (surface IN ('practice', 'workbench', 'guided_redo', 'tutor')),
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

INSERT INTO help_assists__232 (id, surface, assist_kind, practice_item_id, practice_item_hash, practice_session_id, workbench_session_id, attempt_id, submission_id, hint_kind, level, offered_level, level_source, horizon, route_id, from_node_id, target_node_id, map_id, strategy, body_md, authored_index, work_hash, work_chars, placement_json, chooser, options_json, probabilities_json, drawn_option_json, propensity, seed, policy_version, question_set_version, state_hash, request, feedback_text, feedback_shortcut, contract_failures_json, leak_flags_json, shown, counted_by, model, prompt_version, input_hash, latency_ms, requested_at, shown_at, submitted_at, submit_latency_seconds, step_snapshot_json, step_verdicts_json, first_questionable_step_id, error_kind_guess, about_step_id, continue_from_step_id, rivals_json, predicted_answers_json, eig_nats, feedback_step_id, cited_span_ids_json, retrieval_manifest_json, alternatives_json, work_md)
SELECT id, surface, assist_kind, practice_item_id, practice_item_hash, practice_session_id, workbench_session_id, attempt_id, submission_id, hint_kind, level, offered_level, level_source, horizon, route_id, from_node_id, target_node_id, map_id, strategy, body_md, authored_index, work_hash, work_chars, placement_json, chooser, options_json, probabilities_json, drawn_option_json, propensity, seed, policy_version, question_set_version, state_hash, request, feedback_text, feedback_shortcut, contract_failures_json, leak_flags_json, shown, counted_by, model, prompt_version, input_hash, latency_ms, requested_at, shown_at, submitted_at, submit_latency_seconds, step_snapshot_json, step_verdicts_json, first_questionable_step_id, error_kind_guess, about_step_id, continue_from_step_id, rivals_json, predicted_answers_json, eig_nats, feedback_step_id, cited_span_ids_json, retrieval_manifest_json, alternatives_json, work_md
FROM help_assists;

DROP TABLE help_assists;
ALTER TABLE help_assists__232 RENAME TO help_assists;

-- The attach at submit and the per-attempt reads.
CREATE INDEX idx_help_assists_session_item ON help_assists(practice_session_id, practice_item_id, requested_at);
CREATE INDEX idx_help_assists_attempt ON help_assists(attempt_id);
CREATE INDEX idx_help_assists_submission ON help_assists(submission_id, practice_item_id);
CREATE INDEX idx_help_assists_workbench ON help_assists(workbench_session_id, requested_at);
CREATE INDEX idx_help_assists_requested ON help_assists(surface, requested_at);
-- RW5d P3: a figure's help rows (the once-per-attempt check, the chooser's
-- precondition, the help outcomes and the report).
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

CREATE TABLE figure_predictions__232 (
  id TEXT PRIMARY KEY,
  figure_id TEXT NOT NULL REFERENCES interactive_figures(id),
  -- The figure's source (RW6a's "Last time here" reads it); RW5d P3: NULL
  -- for a figure with no home and no book (an attempt host's illustration).
  extraction_id TEXT,
  prediction_index INTEGER NOT NULL CHECK (prediction_index >= 0),
  learner_answer TEXT NOT NULL,
  observed_json TEXT NOT NULL,
  matched INTEGER NOT NULL CHECK (matched IN (0, 1)),
  explanation_text TEXT,
  created_at TEXT NOT NULL,
  -- RW5d P3: the help_assists figure row of the open attempt the prediction
  -- was made under (a soft reference; NULL outside attempts and before 232).
  assist_id TEXT,
  -- RW5d P3: when explanation_text was set (with it, once; NULL before 232).
  explained_at TEXT,
  UNIQUE (figure_id, prediction_index)
);

INSERT INTO figure_predictions__232 (id, figure_id, extraction_id, prediction_index, learner_answer, observed_json, matched, explanation_text, created_at)
SELECT id, figure_id, extraction_id, prediction_index, learner_answer, observed_json, matched, explanation_text, created_at
FROM figure_predictions;

DROP TABLE figure_predictions;
ALTER TABLE figure_predictions__232 RENAME TO figure_predictions;

CREATE INDEX idx_figure_predictions_extraction ON figure_predictions(extraction_id, created_at);
-- RW5d P3: an attempt's predictions by its figure rows (the diagnoser's trace).
CREATE INDEX idx_figure_predictions_assist ON figure_predictions(assist_id);

CREATE TRIGGER figure_predictions_no_delete
BEFORE DELETE ON figure_predictions
BEGIN
  SELECT RAISE(ABORT, 'figure_predictions is append-only');
END;

CREATE TRIGGER figure_predictions_explanation_once
BEFORE UPDATE ON figure_predictions
WHEN OLD.explanation_text IS NOT NULL
  OR NEW.explanation_text IS NULL
  OR NEW.id IS NOT OLD.id
  OR NEW.figure_id IS NOT OLD.figure_id
  OR NEW.extraction_id IS NOT OLD.extraction_id
  OR NEW.prediction_index IS NOT OLD.prediction_index
  OR NEW.learner_answer IS NOT OLD.learner_answer
  OR NEW.observed_json IS NOT OLD.observed_json
  OR NEW.matched IS NOT OLD.matched
  OR NEW.created_at IS NOT OLD.created_at
  OR NEW.assist_id IS NOT OLD.assist_id
  OR OLD.explained_at IS NOT NULL
BEGIN
  SELECT RAISE(ABORT, 'figure_predictions is append-only (explanation_text is set once)');
END;

PRAGMA foreign_keys = ON;
