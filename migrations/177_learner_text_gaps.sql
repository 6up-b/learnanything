-- Learner-text gaps (implementation_handoffs §4, owner-directed 2026-10-12):
-- one pipeline turns a learner's own text (a tutor question, a non-empty stuck
-- answer, a diagnosis of a wrong answer) into a named gap: a missing
-- prerequisite, a misconception, a slip, a wording/notation problem, or none.
--
-- Nothing here is evidence, mastery or certification (learner field G13).
-- Every paid reading and verdict is ALSO in judgment_ledger; these tables are
-- what the pipeline did with them. Replay and rebuild read them and never ask
-- a model again. Taken as 177 (main was at 176); Slice 2 T6 also takes 177, so
-- expect a renumber at merge.

-- One row per learner text read (append-only). The context model's and the
-- Decider's kind, the authoritative kind (learner_text_gaps.chooser), the
-- gap as the model named it, and what was done: the target (with its subject,
-- persisted when the gap was read: the F4 contract), an added edge, a created
-- concept / LO / seed item. The router's learner-state card reads these.
CREATE TABLE learner_text_gaps (
  id TEXT PRIMARY KEY,
  source_kind TEXT NOT NULL CHECK (source_kind IN ('tutor_question', 'stuck_answer', 'diagnosis')),
  -- question_events.id | practice_attempts.id | attempt_diagnoses.id
  source_id TEXT NOT NULL,
  attempt_id TEXT,
  practice_item_id TEXT,
  -- The LO the text is about (the item's LO, a note's single related LO).
  anchor_learning_object_id TEXT,
  -- The asking item's subject: every target is grounded in it.
  subject_id TEXT,
  learner_text TEXT NOT NULL,
  chooser TEXT NOT NULL CHECK (chooser IN ('context_model', 'decider')),
  -- Who read it in context: the tutor, the diagnoser, or the stuck-text reader.
  context_judge TEXT NOT NULL CHECK (context_judge IN ('tutor', 'diagnoser', 'gap_reader')),
  context_kind TEXT,
  decider_kind TEXT,
  decider_json TEXT NOT NULL DEFAULT '{}',
  kind TEXT NOT NULL CHECK (kind IN ('prerequisite', 'misconception', 'slip', 'wording', 'none', 'unread')),
  named_json TEXT NOT NULL DEFAULT '{}',
  action TEXT NOT NULL CHECK (action IN (
    'matched_prerequisite', 'created_prerequisite', 'unmatched_prerequisite',
    'belief_sighting', 'belief_candidate', 'belief_registry_path', 'unplaced',
    'signal_only', 'unnamed', 'none', 'failed'
  )),
  target_kind TEXT CHECK (target_kind IS NULL OR target_kind IN ('learning_object', 'durable', 'candidate')),
  target_id TEXT,
  target_subject_id TEXT,
  match_basis TEXT,
  edge_id TEXT,
  created_concept_id TEXT,
  created_learning_object_id TEXT,
  seed_practice_item_id TEXT,
  seed_status TEXT,
  detail_json TEXT NOT NULL DEFAULT '{}',
  algorithm_version TEXT NOT NULL,
  pipeline_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (source_kind, source_id)
);
CREATE INDEX learner_text_gaps_created ON learner_text_gaps(created_at, id);
CREATE INDEX learner_text_gaps_target ON learner_text_gaps(target_kind, target_id);
CREATE INDEX learner_text_gaps_created_lo ON learner_text_gaps(created_learning_object_id);
CREATE TRIGGER learner_text_gaps_no_update BEFORE UPDATE ON learner_text_gaps
BEGIN SELECT RAISE(ABORT, 'learner_text_gaps is append-only'); END;
CREATE TRIGGER learner_text_gaps_no_delete BEFORE DELETE ON learner_text_gaps
BEGIN SELECT RAISE(ABORT, 'learner_text_gaps is append-only'); END;

-- The learner's one-tap reversals: undo an added edge, undo a created
-- prerequisite, or "not what I meant" on a belief sighting. One of each kind
-- per gap (a repeated tap is a no-op). Append-only.
CREATE TABLE learner_text_gap_reversals (
  id TEXT PRIMARY KEY,
  gap_id TEXT NOT NULL REFERENCES learner_text_gaps(id),
  reversal TEXT NOT NULL CHECK (reversal IN ('undo_edge', 'undo_creation', 'not_this_belief')),
  actor TEXT NOT NULL CHECK (actor IN ('learner', 'owner')),
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  UNIQUE (gap_id, reversal)
);
CREATE TRIGGER learner_text_gap_reversals_no_update BEFORE UPDATE ON learner_text_gap_reversals
BEGIN SELECT RAISE(ABORT, 'learner_text_gap_reversals is append-only'); END;
CREATE TRIGGER learner_text_gap_reversals_no_delete BEFORE DELETE ON learner_text_gap_reversals
BEGIN SELECT RAISE(ABORT, 'learner_text_gap_reversals is append-only'); END;

-- The durable queue (lease fencing as post_attempt_jobs, 170). A tutor
-- question has no attempt, so this is its own table. payload_json keeps a
-- creation's progress (concept, LO, edge written) so a retry never creates
-- twice.
CREATE TABLE learner_text_gap_jobs (
  id TEXT PRIMARY KEY,
  source_kind TEXT NOT NULL CHECK (source_kind IN ('tutor_question', 'stuck_answer', 'diagnosis')),
  source_id TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'queued'
    CHECK (state IN ('queued', 'leased', 'done', 'failed', 'skipped')),
  attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  lease_owner TEXT,
  lease_expires_at TEXT,
  lease_epoch INTEGER NOT NULL DEFAULT 0,
  not_before TEXT,
  last_error TEXT,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (source_kind, source_id)
);
CREATE INDEX learner_text_gap_jobs_order ON learner_text_gap_jobs(state, created_at, id);

-- mvp-0.13: a matched prerequisite gap on an LO assumed known or in
-- maintenance brings its next check forward (no sooner than the configured
-- delay after the gap, never later than it was). Placement reads these only
-- at mvp-0.13 or later with learner_text_gaps.sooner_check_enabled on.
CREATE TABLE learner_gap_check_advances (
  id TEXT PRIMARY KEY,
  gap_id TEXT NOT NULL REFERENCES learner_text_gaps(id),
  learning_object_id TEXT NOT NULL,
  intent TEXT NOT NULL CHECK (intent IN ('assumed', 'maintenance')),
  assumption_id TEXT,
  original_due TEXT,
  advanced_due TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX learner_gap_check_advances_lo ON learner_gap_check_advances(learning_object_id, created_at, id);

-- A created prerequisite's light commitment: its seed item is one delayed
-- check (pass: maintenance; fail: learning). Placement reads each row as a
-- decision with source learner_text_gap; an undone creation's row is ignored.
CREATE TABLE learner_gap_commitments (
  id TEXT PRIMARY KEY,
  gap_id TEXT NOT NULL REFERENCES learner_text_gaps(id),
  learning_object_id TEXT NOT NULL,
  practice_item_id TEXT,
  first_review_due TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX learner_gap_commitments_lo ON learner_gap_commitments(learning_object_id, created_at, id);
