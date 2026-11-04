-- Learner marks on hypotheses (FG1c; docs/specs/spec_followup_generate_serve_v1.md §7) and the
-- hypothesis-list exposure receipt (docs/specs/spec_router_objective_v1.md §4 row 6).
--
-- Additive: new tables only, no existing row or table changes, and nothing replay,
-- grading, certification, mastery, FSRS or serving reads. One causal read, of (1) only: a display of a
-- workflow's causes before its probe's answer makes that answer not independent.
--
-- 1. hypothesis_list_exposures (RECEIPT): one row each time the desktop displays a list of an
--    attempt's possible causes, written from the client's display event: the attempt, the factor,
--    the hypothesis versions shown, their order AS DISPLAYED, the surface and the time. A list can
--    state the misconception outright, and nothing else records that it was on screen. The row is
--    what was true at the display: a probe answered later is a later linked row (2), never a change.
--
-- 2. hypothesis_exposure_probe_links (RECEIPT): an exposure's probe was answered afterwards.
--
-- 3. hypothesis_marks (RAW_LEDGER): the learner's own read, per hypothesis, of what went wrong:
--    my_gap, partly, not_it, or (with no hypothesis) none_of_these with optional free text.
--    A change of mind appends; the latest row per hypothesis counts, and cleared takes a mark back.
--    An imperfect sensor, kept raw for later measurement: it reaches the learner state card and the
--    diagnoser's context as the learner's attributed opinion, and moves no probability.
--
-- attempt_id carries no foreign key, as causal_hypotheses' doesn't: a goal-series rewind can remove
-- an attempt's projection, and these receipts stay.
CREATE TABLE hypothesis_list_exposures (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL,
  factor_id TEXT,
  diagnosis_id TEXT,
  workflow_id TEXT,
  surface TEXT NOT NULL CHECK (length(trim(surface)) > 0),
  -- Ids of causal_hypotheses rows (each one version), in the order on screen.
  hypothesis_version_ids_json TEXT NOT NULL,
  -- Set when the order was shuffled for this list; null when a surface kept its own order.
  order_seed TEXT,
  order_version TEXT,
  probe_answered INTEGER NOT NULL CHECK (probe_answered IN (0, 1)),
  probe_attempt_id TEXT,
  shown_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX hypothesis_list_exposures_attempt ON hypothesis_list_exposures(attempt_id, created_at, id);
CREATE TRIGGER hypothesis_list_exposures_no_update
BEFORE UPDATE ON hypothesis_list_exposures
BEGIN
    SELECT RAISE(ABORT, 'hypothesis_list_exposures is append-only');
END;
CREATE TRIGGER hypothesis_list_exposures_no_delete
BEFORE DELETE ON hypothesis_list_exposures
BEGIN
    SELECT RAISE(ABORT, 'hypothesis_list_exposures is append-only');
END;

CREATE TABLE hypothesis_exposure_probe_links (
  id TEXT PRIMARY KEY,
  exposure_id TEXT NOT NULL REFERENCES hypothesis_list_exposures(id),
  attempt_id TEXT NOT NULL,
  probe_attempt_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (exposure_id, probe_attempt_id)
);
CREATE INDEX hypothesis_exposure_probe_links_attempt ON hypothesis_exposure_probe_links(attempt_id, created_at, id);
CREATE TRIGGER hypothesis_exposure_probe_links_no_update
BEFORE UPDATE ON hypothesis_exposure_probe_links
BEGIN
    SELECT RAISE(ABORT, 'hypothesis_exposure_probe_links is append-only');
END;
CREATE TRIGGER hypothesis_exposure_probe_links_no_delete
BEFORE DELETE ON hypothesis_exposure_probe_links
BEGIN
    SELECT RAISE(ABORT, 'hypothesis_exposure_probe_links is append-only');
END;

CREATE TABLE hypothesis_marks (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  diagnosis_id TEXT,
  factor_id TEXT,
  workflow_id TEXT,
  -- The causal_hypotheses row marked; null for None of these. hypothesis_key is its stable
  -- identity (the row's episode_key), so a later version of the same cause is the same cause.
  hypothesis_version_id TEXT,
  hypothesis_key TEXT,
  mark TEXT NOT NULL CHECK (mark IN ('my_gap', 'partly', 'not_it', 'none_of_these', 'cleared')),
  free_text TEXT,
  -- The list as displayed when this was marked; position is 1-based, null for None of these.
  display_position INTEGER CHECK (display_position IS NULL OR display_position >= 1),
  display_order_json TEXT NOT NULL,
  order_seed TEXT,
  order_version TEXT,
  surface TEXT NOT NULL CHECK (length(trim(surface)) > 0),
  probe_answered INTEGER NOT NULL CHECK (probe_answered IN (0, 1)),
  probe_attempt_id TEXT,
  probe_outcome_json TEXT,
  created_at TEXT NOT NULL,
  CHECK (free_text IS NULL OR mark = 'none_of_these'),
  CHECK (mark <> 'none_of_these' OR hypothesis_version_id IS NULL),
  CHECK (mark NOT IN ('my_gap', 'partly', 'not_it') OR hypothesis_version_id IS NOT NULL)
);
CREATE INDEX hypothesis_marks_attempt ON hypothesis_marks(attempt_id, created_at, id);
CREATE INDEX hypothesis_marks_learning_object ON hypothesis_marks(learning_object_id, created_at, id);
CREATE TRIGGER hypothesis_marks_no_update
BEFORE UPDATE ON hypothesis_marks
BEGIN
    SELECT RAISE(ABORT, 'hypothesis_marks is append-only');
END;
CREATE TRIGGER hypothesis_marks_no_delete
BEFORE DELETE ON hypothesis_marks
BEGIN
    SELECT RAISE(ABORT, 'hypothesis_marks is append-only');
END;
