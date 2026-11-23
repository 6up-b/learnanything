-- Reader workbench v2, after its foundations' review: three additive changes, nothing backfilled.
--
-- 1. Replacing inserts refused. Migration 262's append-only tables refuse UPDATE and DELETE by trigger, but
--    `INSERT OR REPLACE` on an existing key deletes the old row without firing a DELETE trigger (SQLite fires
--    it only with recursive_triggers on, which no connection here sets). A BEFORE INSERT guard per table now
--    refuses any insert whose key, or whose block-chain position, is taken: the old row stays.
-- 2. projection_initializations (RECEIPT, append-only): one row per derived span projection, written when a
--    vault's history was first projected into it (on open, whatever the algorithm tag), so a vault already at
--    the latest tag when 262 arrived gets its history projected exactly once.
-- 3. A partial expression index on the Reader answer events by the exchange they name, so projecting one
--    exchange is an index probe, not a scan of every answer ever recorded.
--
-- Nothing that scores, schedules, certifies or writes evidence reads any of this, so no algorithm tag moves.

CREATE TRIGGER desk_op_receipts_no_replace
BEFORE INSERT ON desk_op_receipts
WHEN EXISTS (SELECT 1 FROM desk_op_receipts WHERE client_id = NEW.client_id AND seq = NEW.seq)
BEGIN
    SELECT RAISE(ABORT, 'desk_op_receipts is append-only');
END;

CREATE TRIGGER pad_op_receipts_no_replace
BEFORE INSERT ON pad_op_receipts
WHEN EXISTS (SELECT 1 FROM pad_op_receipts WHERE client_id = NEW.client_id AND seq = NEW.seq)
BEGIN
    SELECT RAISE(ABORT, 'pad_op_receipts is append-only');
END;

CREATE TRIGGER pad_block_versions_no_replace
BEFORE INSERT ON pad_block_versions
WHEN EXISTS (SELECT 1 FROM pad_block_versions WHERE version_id = NEW.version_id)
  OR (NEW.supersedes_id IS NOT NULL AND EXISTS (SELECT 1 FROM pad_block_versions WHERE supersedes_id = NEW.supersedes_id))
  OR (NEW.supersedes_id IS NULL AND EXISTS (SELECT 1 FROM pad_block_versions WHERE block_id = NEW.block_id AND supersedes_id IS NULL))
BEGIN
    SELECT RAISE(ABORT, 'pad_block_versions is append-only');
END;

CREATE TRIGGER pad_block_anchors_no_replace
BEFORE INSERT ON pad_block_anchors
WHEN EXISTS (SELECT 1 FROM pad_block_anchors WHERE event_id = NEW.event_id)
BEGIN
    SELECT RAISE(ABORT, 'pad_block_anchors is append-only');
END;

CREATE TRIGGER companion_exchange_context_no_replace
BEFORE INSERT ON companion_exchange_context
WHEN EXISTS (SELECT 1 FROM companion_exchange_context WHERE question_event_id = NEW.question_event_id)
BEGIN
    SELECT RAISE(ABORT, 'companion_exchange_context is append-only');
END;

CREATE TABLE projection_initializations (
  projection TEXT PRIMARY KEY CHECK (projection IN ('question_event_spans', 'learner_text_gap_spans')),
  sources INTEGER NOT NULL CHECK (sources >= 0),
  rows INTEGER NOT NULL CHECK (rows >= 0),
  initialized_at TEXT NOT NULL
);

CREATE TRIGGER projection_initializations_no_update
BEFORE UPDATE ON projection_initializations
BEGIN
    SELECT RAISE(ABORT, 'projection_initializations is append-only');
END;

CREATE TRIGGER projection_initializations_no_delete
BEFORE DELETE ON projection_initializations
BEGIN
    SELECT RAISE(ABORT, 'projection_initializations is append-only');
END;

CREATE TRIGGER projection_initializations_no_replace
BEFORE INSERT ON projection_initializations
WHEN EXISTS (SELECT 1 FROM projection_initializations WHERE projection = NEW.projection)
BEGIN
    SELECT RAISE(ABORT, 'projection_initializations is append-only');
END;

CREATE INDEX idx_interaction_events_reader_answer_question
  ON interaction_events(json_extract(payload_json, '$.question_event_id'))
  WHERE kind = 'reader_answer_submitted';
