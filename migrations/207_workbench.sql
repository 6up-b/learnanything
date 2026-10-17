-- Reader workbench RW2a: the resumable scratchpad (spec_reader_workbench_v1
-- §5.1, §5.7; docs/reviews/reader-workbench-RW2a.md).
--
-- A workbench session is one problem the learner works in steps, beside the
-- source in the Reader or full width on the practice screen. It opens at once
-- with the verbatim stem, before the exercise import (a paid background job)
-- has made the problem an item: `practice_item_id` stays NULL until the
-- import binds it (UX S2). Its steps are an append-only ledger: an edit is a
-- new row superseding the head of its chain, a delete a tombstone row, an
-- undo a row superseding the tombstone, so nothing the learner wrote is lost.
--
-- Neither table is evidence. The only evidence a session produces is its
-- submitted attempt, through the ordinary submit path (`practice_attempts`
-- with `hints_used`, `primed` and `entry_surface`), which replay already
-- reads; replay and rebuild never read these tables. Kill switch:
-- workbench.enabled. Every CHECK'd column is created with every value any
-- later workbench phase writes (spec §11), so none of them rebuilds a table.
CREATE TABLE workbench_sessions (
  id TEXT PRIMARY KEY,
  -- NULL until the import binds (or from the start when opened on an item).
  practice_item_id TEXT,
  -- The verbatim stem shown before binding (and kept after it).
  stem_md TEXT NOT NULL,
  import_status TEXT NOT NULL DEFAULT 'none'
    CHECK (import_status IN ('none', 'pending', 'bound', 'failed')),
  -- The exercise-import batch the session waits on, and the request it was
  -- enqueued with, so "try again" re-enqueues it after a restart.
  import_batch_id TEXT,
  import_request_json TEXT,
  import_error TEXT,
  -- Where the session is worked now. A resume on another surface moves it
  -- (the practice card resuming a Reader problem, the Reader resuming a
  -- practice-screen one), so the submit records the surface it was sent from.
  origin TEXT NOT NULL CHECK (origin IN ('reader', 'practice', 'plan')),
  -- How it was opened; it sets the default book visibility (UX S7, D9).
  entry TEXT NOT NULL CHECK (entry IN (
    'work_through', 'resume', 'check_me', 'practice_this', 'path_exercise',
    'discriminating_problem', 'practice_screen', 'plan'
  )),
  -- A "short problem instead" session's original problem (RW2b, D32).
  parent_session_id TEXT REFERENCES workbench_sessions(id),
  extraction_id TEXT,
  span_ids_json TEXT NOT NULL DEFAULT '[]',
  -- Whether the book is shown now (the learner's one-key choice).
  source_visible INTEGER NOT NULL DEFAULT 0 CHECK (source_visible IN (0, 1)),
  -- When the learner last hid the book (NULL: never hidden).
  source_hidden_at TEXT,
  -- When the book first counted: the first step written with it shown, or
  -- its first showing after a step (spec §5.4: one hint-equivalent from then
  -- on). NULL: the attempt is the learner's own.
  source_shown_at TEXT,
  -- The practice session the submit ran in (filled at submit).
  practice_session_id TEXT,
  -- The assessment contract the learner was shown (snapshotted when the
  -- session opens on its item or binds to it), so a problem resumed after its
  -- rubric or required method changed is graded against what it showed.
  assessment_contract_version_id TEXT,
  -- Hints the learner revealed on the practice screen's answer box before
  -- working in steps. Never taken back; the submit counts them with the book.
  carried_hints INTEGER NOT NULL DEFAULT 0 CHECK (carried_hints >= 0),
  -- The serve the problem answers: the scheduler offer and the daily-plan
  -- presentation it was opened from ("check me", the practice screen), kept
  -- so a resumed problem still submits as that serve. A later serve of the
  -- same item replaces them; a resume without one keeps them.
  scheduler_candidate_id TEXT,
  plan_presentation_id TEXT,
  -- The help style's per-session override (RW2b, D31); NULL until then.
  help_style TEXT CHECK (help_style IS NULL OR help_style IN ('let_me_struggle', 'balanced', 'guide_me')),
  -- open -> submitted, or open -> abandoned -> open on reopen (UX S13).
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'submitted', 'abandoned')),
  attempt_id TEXT,
  client_idempotency_key TEXT UNIQUE,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  closed_at TEXT,
  CHECK ((status = 'submitted') = (attempt_id IS NOT NULL)),
  CHECK ((import_status = 'bound') <= (practice_item_id IS NOT NULL))
);
CREATE INDEX idx_workbench_sessions_item ON workbench_sessions(practice_item_id, status, updated_at);
CREATE INDEX idx_workbench_sessions_extraction ON workbench_sessions(extraction_id, status, updated_at);
CREATE INDEX idx_workbench_sessions_attempt ON workbench_sessions(attempt_id);

CREATE TABLE workbench_steps (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES workbench_sessions(id),
  -- The step's place in the list (fractional, so a step can go between two).
  ordinal REAL NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('step', 'stuck')),
  body_md TEXT NOT NULL,
  -- The version this row replaces (an edit, a tombstone or an undo).
  supersedes_id TEXT REFERENCES workbench_steps(id),
  -- A tombstone: the step is deleted (its text kept on the row).
  deleted INTEGER NOT NULL DEFAULT 0 CHECK (deleted IN (0, 1)),
  client_idempotency_key TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (session_id, client_idempotency_key)
);
CREATE INDEX idx_workbench_steps_session ON workbench_steps(session_id, created_at, id);
CREATE UNIQUE INDEX idx_workbench_steps_supersedes ON workbench_steps(supersedes_id)
  WHERE supersedes_id IS NOT NULL;

CREATE TRIGGER workbench_steps_no_update
BEFORE UPDATE ON workbench_steps
BEGIN
  SELECT RAISE(ABORT, 'workbench_steps is append-only');
END;

CREATE TRIGGER workbench_steps_no_delete
BEFORE DELETE ON workbench_steps
BEGIN
  SELECT RAISE(ABORT, 'workbench_steps is append-only');
END;
