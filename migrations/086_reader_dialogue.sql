-- P2 step B.11 (spec_p2_narrow_golden_path §7.6, U-033): minimal bidirectional
-- reader dialogue. Reader events land as NEW KINDS on the P0 interaction_events
-- envelope (§3.8) -- there is NO new event table and NO reader_exchanges table:
-- the exact per-exchange record (question_event id, span anchor, chosen answer
-- mode, validated citations, provider/model provenance, and the full context
-- manifest) rides the `reader_answer_submitted` event's payload_json.
--
-- SQLite cannot ALTER a CHECK constraint, so each envelope's constrained column is
-- widened by a byte-faithful rebuild: build a NEW temp table with the widened
-- CHECK, copy every row, DROP the old table, and RENAME the temp into place. The
-- temp-then-rename order matters: renaming the *old* table would rewrite foreign
-- keys that reference it (e.g. question_promotions -> question_events) to the temp
-- name; renaming the *new* temp (which nothing references) leaves those FKs intact.
-- Column sets + indexes are reproduced verbatim from migrations 065 / 019+.

PRAGMA foreign_keys=OFF;

-- interaction_events: extend the `kind` vocabulary with the 7 reader kinds (§7.6).
CREATE TABLE interaction_events__086 (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN
    ('attempt_duration', 'retirement_reason', 'affect_tap',
     -- U-033 reader-dialogue kinds (§7.6):
     'reader_question_presented', 'reader_question_skipped',
     'reader_answer_submitted', 'learner_question_asked',
     'reader_answer_mode_set', 'reader_disposition_chosen',
     'reader_source_restored')),
  subject_type TEXT,
  subject_id TEXT,
  administration_id TEXT,
  surface_id TEXT,
  attempt_id TEXT,
  affect_tap_kind TEXT CHECK (affect_tap_kind IS NULL OR affect_tap_kind IN (
    'cue_gave_it_away', 'ambiguous', 'misgraded', 'felt_rote',
    'not_worth_my_attention', 'meaningful_connection', 'wanted_more_depth'
  )),
  attempt_duration_ms INTEGER
    CHECK (attempt_duration_ms IS NULL OR attempt_duration_ms >= 0),
  payload_json TEXT,
  origin TEXT NOT NULL
    CHECK (origin IN ('learner', 'system', 'owner_tooling')),
  created_at TEXT NOT NULL
);
INSERT INTO interaction_events__086 SELECT * FROM interaction_events;
DROP TABLE interaction_events;
ALTER TABLE interaction_events__086 RENAME TO interaction_events;

CREATE INDEX idx_interaction_events_kind
  ON interaction_events(kind, created_at);
CREATE INDEX idx_interaction_events_subject
  ON interaction_events(subject_type, subject_id);
CREATE INDEX idx_interaction_events_admin
  ON interaction_events(administration_id);

-- question_events: the reader Ask reuses the tutor Q&A store for its per-span
-- budget + same-span exchange thread, so `context` must admit the 4th `reader`
-- value. Schema reproduced verbatim from migrations 019/026/027/030/... plus
-- 'reader'. question_promotions carries a FK to question_events(id) -- the
-- temp-then-rename order above keeps it valid.
CREATE TABLE question_events__086 (
  id TEXT PRIMARY KEY,
  context TEXT NOT NULL CHECK (context IN ('library', 'practice', 'feedback', 'reader')),
  note_id TEXT,
  practice_item_id TEXT,
  attempt_id TEXT,
  session_id TEXT,
  question_md TEXT NOT NULL,
  answer_md TEXT,
  question_type TEXT CHECK (
    question_type IN ('clarification', 'prerequisite', 'mechanism', 'strategy', 'verification', 'other')
  ),
  facets_json TEXT,
  hint_equivalent INTEGER NOT NULL DEFAULT 0,
  leak_suspected INTEGER NOT NULL DEFAULT 0,
  rating INTEGER,
  seconds_into_attempt REAL,
  provider TEXT,
  created_at TEXT NOT NULL,
  answer_status TEXT NOT NULL DEFAULT 'answered'
    CHECK (answer_status IN ('pending', 'answered', 'failed')),
  saved_note_id TEXT,
  preceding_tutor_move TEXT,
  scaffold_level TEXT,
  warning_state TEXT,
  learner_mode TEXT,
  question_opportunity TEXT,
  hints_used_before INTEGER,
  direct_explanation_request INTEGER NOT NULL DEFAULT 0,
  attempt_progress TEXT,
  signal_channel TEXT CHECK (
    signal_channel IS NULL OR signal_channel IN ('epistemic', 'interaction_preference')
  )
);
INSERT INTO question_events__086 SELECT * FROM question_events;
DROP TABLE question_events;
ALTER TABLE question_events__086 RENAME TO question_events;

CREATE INDEX idx_question_events_item_session
  ON question_events(practice_item_id, session_id);
CREATE INDEX idx_question_events_note
  ON question_events(note_id);

PRAGMA foreign_keys=ON;
