-- The worked answer shown after an empty "I'm stuck" answer is a reveal
-- (stuck-prompt re-review F8, algorithm mvp-0.13; built as migration 173 and
-- renumbered when it merged after main's 172-177, none of which touches
-- reveal_events).
--
-- The TUI's feedback screen shows the item's full expected answer after an
-- empty stuck answer. Until now that display wrote nothing to the reveal
-- ledger (migration 154), so a retry taken with the answer in view was
-- recorded as unprimed, unassisted evidence. A new `source_kind`,
-- 'answer_display', names this exposure honestly: the expected answer itself
-- shown on a feedback screen, linked to the attempt whose feedback showed it.
-- None of the four existing kinds is that (a repair suggestion, a tutor
-- answer, a guided redo, a source re-read).
--
-- SQLite cannot widen a CHECK in place, so the append-only table is rebuilt
-- with every row, index and trigger as migration 154 created them (unchanged
-- through 177); only the CHECK gains the new kind. The triggers go first:
-- they guard against row updates and deletes, and are recreated on the new
-- table.
DROP TRIGGER reveal_events_no_update;
DROP TRIGGER reveal_events_no_delete;

CREATE TABLE reveal_events_new (
  id TEXT PRIMARY KEY,
  practice_item_id TEXT NOT NULL,
  learning_object_id TEXT,
  remediation_episode_id TEXT,
  source_kind TEXT NOT NULL CHECK (
    source_kind IN (
      'tutor_answer',
      'repair_display',
      'guided_redo',
      'source_review',
      'answer_display'
    )
  ),
  amount REAL NOT NULL CHECK (amount >= 0.0 AND amount <= 1.0),
  basis TEXT,
  question_event_id TEXT,
  attempt_id TEXT,
  created_at TEXT NOT NULL
);

INSERT INTO reveal_events_new(
  id, practice_item_id, learning_object_id, remediation_episode_id,
  source_kind, amount, basis, question_event_id, attempt_id, created_at
)
SELECT
  id, practice_item_id, learning_object_id, remediation_episode_id,
  source_kind, amount, basis, question_event_id, attempt_id, created_at
FROM reveal_events;

DROP TABLE reveal_events;
ALTER TABLE reveal_events_new RENAME TO reveal_events;

CREATE INDEX idx_reveal_events_item_created
  ON reveal_events(practice_item_id, created_at, id);
CREATE INDEX idx_reveal_events_episode
  ON reveal_events(remediation_episode_id);

CREATE TRIGGER reveal_events_no_update
BEFORE UPDATE ON reveal_events
BEGIN
  SELECT RAISE(ABORT, 'reveal events are append-only');
END;

CREATE TRIGGER reveal_events_no_delete
BEFORE DELETE ON reveal_events
BEGIN
  SELECT RAISE(ABORT, 'reveal events are append-only');
END;
