-- Reader workbench v2, its foundations (docs/specs/spec_reader_workbench_v2.md §3.4, §7.6, §8.5, §15.1):
-- the storage the desks, the scratchpads and the companion history build on. No UI reads it yet.
--
-- Additive: ten new tables, no existing row or object changed, nothing backfilled into a ledger.
--   desks, desk_windows                WORKFLOW: the learner's rooms and their windows (views, never evidence).
--   desk_op_receipts, pad_op_receipts  RECEIPT: one stored reply per applied write batch, keyed by the
--                                      client and its sequence number, so a retried batch gets the same reply.
--   pads                               WORKFLOW: a scratchpad's metadata (title, kept, home desk).
--   pad_block_versions                 RAW_LEDGER, append-only by trigger: every version of every block.
--   pad_block_anchors                  RAW_LEDGER, append-only by trigger: block-to-passage links and unlinks.
--   companion_exchange_context         RAW_LEDGER, append-only by trigger: where a tutor exchange happened.
--   question_event_spans,              DERIVED: which passages each tutor exchange and each read learner text
--   learner_text_gap_spans             are tied to, with the anchor's quality; cleared and rebuilt by one
--                                      replayer each (substrate/rebuild_orchestrator.py).
--
-- Nothing that scores, schedules, certifies or writes evidence reads any of these tables (the import
-- fences in pyproject.toml), so no algorithm tag moves.

-- A desk: a strip of windows. position is a client-minted fractional key (desks order by it, then by id),
-- so moving one desk never rewrites another. version counts the applied ops that touched the desk; every
-- desk op names the version it expects.
CREATE TABLE desks (
  desk_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  position TEXT NOT NULL,
  focus_window_id TEXT,
  goal_id TEXT,
  companion_dock TEXT NOT NULL DEFAULT 'br' CHECK (companion_dock IN ('br', 'bl', 'right', 'cb')),
  companion_shown INTEGER NOT NULL DEFAULT 0 CHECK (companion_shown IN (0, 1)),
  version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  archived_at TEXT
);

-- A window on a desk. slot orders the strip (0..n-1 among open windows); a pair is two open windows
-- sharing a slot with panes 0 and 1, and active marks the pair's active pane. spec_json holds the
-- window's content reference (or a pad stack's entries); view_json its scroll anchor and view settings.
-- A closed window keeps its row (closed_at) so a close can be undone; its slot is then meaningless.
CREATE TABLE desk_windows (
  window_id TEXT PRIMARY KEY,
  desk_id TEXT NOT NULL REFERENCES desks(desk_id),
  slot INTEGER NOT NULL CHECK (slot >= 0),
  pane INTEGER NOT NULL DEFAULT 0 CHECK (pane IN (0, 1)),
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
  kind TEXT NOT NULL CHECK (kind IN (
    'source', 'video', 'pad', 'pad_stack', 'lesson', 'thread', 'compare', 'panel', 'figure_notebook'
  )),
  spec_json TEXT NOT NULL,
  view_json TEXT NOT NULL DEFAULT '{}',
  opened_at TEXT NOT NULL,
  closed_at TEXT
);
CREATE INDEX idx_desk_windows_desk ON desk_windows(desk_id, closed_at, slot, pane);

-- One stored reply per applied desk batch.
CREATE TABLE desk_op_receipts (
  client_id TEXT NOT NULL,
  seq INTEGER NOT NULL CHECK (seq >= 1),
  request_hash TEXT NOT NULL,
  result_json TEXT NOT NULL,
  applied_at TEXT NOT NULL,
  PRIMARY KEY (client_id, seq)
);

CREATE TRIGGER desk_op_receipts_no_update
BEFORE UPDATE ON desk_op_receipts
BEGIN
    SELECT RAISE(ABORT, 'desk_op_receipts is append-only');
END;

CREATE TRIGGER desk_op_receipts_no_delete
BEFORE DELETE ON desk_op_receipts
BEGIN
    SELECT RAISE(ABORT, 'desk_op_receipts is append-only');
END;

-- A scratchpad. Pads belong to the library: archiving a desk leaves its pads here. version counts the
-- applied pad-level ops (title, keep); block edits are versioned per block instead.
CREATE TABLE pads (
  pad_id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('running', 'named', 'problem', 'ink', 'lesson_additions')),
  title TEXT NOT NULL DEFAULT '',
  kept INTEGER NOT NULL DEFAULT 0 CHECK (kept IN (0, 1)),
  home_desk_id TEXT,
  workbench_session_id TEXT,
  lesson_id TEXT,
  version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  archived_at TEXT
);
CREATE INDEX idx_pads_home_desk ON pads(home_desk_id, kind);

-- Every version of every block. A block's versions form one chain: its first version supersedes nothing,
-- each later one supersedes exactly the head before it, and no version has two children (the two unique
-- indexes), so there is never a branching head. A removal is a tombstone version. Never updated or deleted.
CREATE TABLE pad_block_versions (
  version_id TEXT PRIMARY KEY,
  block_id TEXT NOT NULL,
  supersedes_id TEXT REFERENCES pad_block_versions(version_id),
  pad_id TEXT NOT NULL REFERENCES pads(pad_id),
  position_key TEXT NOT NULL,
  day TEXT,
  kind TEXT NOT NULL CHECK (kind IN (
    'text', 'note', 'source_quote', 'source_piece', 'tutor_quote', 'figure', 'sketch', 'cell', 'ink',
    'lifted', 'check_cell'
  )),
  body_md TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  provenance TEXT NOT NULL CHECK (provenance IN (
    'learner', 'source', 'tutor', 'learnloop', 'ink_transcription', 'learner_correction'
  )),
  tombstone INTEGER NOT NULL DEFAULT 0 CHECK (tombstone IN (0, 1)),
  client_id TEXT,
  created_at TEXT NOT NULL,
  CHECK (supersedes_id IS NULL OR supersedes_id != version_id)
);
CREATE UNIQUE INDEX idx_pad_block_versions_one_child ON pad_block_versions(supersedes_id)
  WHERE supersedes_id IS NOT NULL;
CREATE UNIQUE INDEX idx_pad_block_versions_one_root ON pad_block_versions(block_id)
  WHERE supersedes_id IS NULL;
CREATE INDEX idx_pad_block_versions_pad ON pad_block_versions(pad_id, block_id);

-- A version may only continue its own block's chain.
CREATE TRIGGER pad_block_versions_same_block
BEFORE INSERT ON pad_block_versions
WHEN NEW.supersedes_id IS NOT NULL
 AND COALESCE((SELECT block_id FROM pad_block_versions WHERE version_id = NEW.supersedes_id), '') != NEW.block_id
BEGIN
    SELECT RAISE(ABORT, 'a block version supersedes a version of another block');
END;

CREATE TRIGGER pad_block_versions_no_update
BEFORE UPDATE ON pad_block_versions
BEGIN
    SELECT RAISE(ABORT, 'pad_block_versions is append-only');
END;

CREATE TRIGGER pad_block_versions_no_delete
BEFORE DELETE ON pad_block_versions
BEGIN
    SELECT RAISE(ABORT, 'pad_block_versions is append-only');
END;

-- Links between a block and a passage (anchor-v1 in anchor_json), as events: the latest event per
-- (block, reading, passage) says whether the link stands. annotation_id names the highlight at the other
-- end of a two-way link.
CREATE TABLE pad_block_anchors (
  event_id TEXT PRIMARY KEY,
  block_id TEXT NOT NULL,
  extraction_id TEXT NOT NULL,
  span_id TEXT NOT NULL,
  anchor_json TEXT NOT NULL DEFAULT '{}',
  annotation_id TEXT,
  action TEXT NOT NULL CHECK (action IN ('link', 'unlink')),
  created_at TEXT NOT NULL
);
CREATE INDEX idx_pad_block_anchors_span ON pad_block_anchors(extraction_id, span_id);
CREATE INDEX idx_pad_block_anchors_block ON pad_block_anchors(block_id);

CREATE TRIGGER pad_block_anchors_no_update
BEFORE UPDATE ON pad_block_anchors
BEGIN
    SELECT RAISE(ABORT, 'pad_block_anchors is append-only');
END;

CREATE TRIGGER pad_block_anchors_no_delete
BEFORE DELETE ON pad_block_anchors
BEGIN
    SELECT RAISE(ABORT, 'pad_block_anchors is append-only');
END;

-- One stored reply per applied pad batch (pad_id: the pad the batch named).
CREATE TABLE pad_op_receipts (
  client_id TEXT NOT NULL,
  seq INTEGER NOT NULL CHECK (seq >= 1),
  pad_id TEXT NOT NULL,
  request_hash TEXT NOT NULL,
  result_json TEXT NOT NULL,
  applied_at TEXT NOT NULL,
  PRIMARY KEY (client_id, seq)
);

CREATE TRIGGER pad_op_receipts_no_update
BEFORE UPDATE ON pad_op_receipts
BEGIN
    SELECT RAISE(ABORT, 'pad_op_receipts is append-only');
END;

CREATE TRIGGER pad_op_receipts_no_delete
BEFORE DELETE ON pad_op_receipts
BEGIN
    SELECT RAISE(ABORT, 'pad_op_receipts is append-only');
END;

-- Where a tutor exchange happened, recorded when it is asked from a desk (origin 'live'). An exchange
-- with no row was asked before desks existed; the history reads it as such and nothing is written for it.
CREATE TABLE companion_exchange_context (
  question_event_id TEXT PRIMARY KEY,
  desk_id TEXT,
  surface TEXT NOT NULL,
  window_spec_json TEXT,
  pad_block_ids_json TEXT,
  goal_id TEXT,
  origin TEXT NOT NULL CHECK (origin IN ('live', 'backfill')),
  created_at TEXT NOT NULL
);
CREATE INDEX idx_companion_exchange_context_desk ON companion_exchange_context(desk_id);

CREATE TRIGGER companion_exchange_context_no_update
BEFORE UPDATE ON companion_exchange_context
BEGIN
    SELECT RAISE(ABORT, 'companion_exchange_context is append-only');
END;

CREATE TRIGGER companion_exchange_context_no_delete
BEFORE DELETE ON companion_exchange_context
BEGIN
    SELECT RAISE(ABORT, 'companion_exchange_context is append-only');
END;

-- DERIVED: the passages a tutor exchange is tied to, on the reading it was asked on (aliases are applied
-- when read). role: the learner's selection, a passage the answer cited, or the context it was asked in
-- (an item's source passage). quality: exact_selection | citation | source_context | unanchored; an
-- unanchored row has no passage and keeps only the learning object it is about.
CREATE TABLE question_event_spans (
  question_event_id TEXT NOT NULL,
  extraction_id TEXT,
  span_id TEXT,
  role TEXT NOT NULL CHECK (role IN ('selection', 'cited', 'context')),
  quality TEXT NOT NULL CHECK (quality IN ('exact_selection', 'citation', 'source_context', 'unanchored')),
  learning_object_id TEXT,
  CHECK ((quality = 'unanchored') = (span_id IS NULL)),
  CHECK ((extraction_id IS NULL) = (span_id IS NULL))
);
CREATE UNIQUE INDEX idx_question_event_spans_row ON question_event_spans(
  question_event_id, COALESCE(extraction_id, ''), COALESCE(span_id, ''), role, COALESCE(learning_object_id, '')
);
CREATE INDEX idx_question_event_spans_span ON question_event_spans(extraction_id, span_id);

-- DERIVED: the passages a read learner text (a learner_text_gaps row) is tied to, by its source's recipe.
CREATE TABLE learner_text_gap_spans (
  gap_id TEXT NOT NULL,
  extraction_id TEXT,
  span_id TEXT,
  role TEXT NOT NULL CHECK (role IN ('selection', 'cited', 'context')),
  quality TEXT NOT NULL CHECK (quality IN ('exact_selection', 'citation', 'source_context', 'unanchored')),
  learning_object_id TEXT,
  CHECK ((quality = 'unanchored') = (span_id IS NULL)),
  CHECK ((extraction_id IS NULL) = (span_id IS NULL))
);
CREATE UNIQUE INDEX idx_learner_text_gap_spans_row ON learner_text_gap_spans(
  gap_id, COALESCE(extraction_id, ''), COALESCE(span_id, ''), role, COALESCE(learning_object_id, '')
);
CREATE INDEX idx_learner_text_gap_spans_span ON learner_text_gap_spans(extraction_id, span_id);
