-- Cross-channel answer-reveal accounting.
--
-- Before this, a reveal was only ever a per-channel boolean side effect:
-- `question_events.leak_suspected` was set for practice-context tutor answers
-- and nowhere else, repair suggestions declared an `answer_reveal_budget` that
-- debited nothing, and the feedback screen could hand the learner a graded
-- solution while the next attempt on the same item was still recorded as clean
-- unassisted evidence.
--
-- `reveal_events` is the one ledger every channel writes to: each row says how
-- much of an item's answer was exposed, by which surface, and (when the
-- exposure happened inside a repair) which remediation episode it belongs to.
-- Append-only, like the rest of the causal substrate: a reveal that happened
-- cannot be un-happened, so corrections are new rows and readers aggregate.
--
-- `amount` is a 0..1 fraction of the expected answer judged exposed, not a
-- count: two half-reveals of the same solution are worth more than one, and the
-- submit path can threshold a sum instead of guessing from a boolean.
--
-- `question_events.leak_overlap` keeps the measured quantity beside the boolean
-- it used to collapse into, so a leak's magnitude survives even when the row
-- predates (or never produced) a ledger entry. `remediation_episode_id` stamps
-- the episode a question was asked inside, so repair-lane reveals are separable
-- from ordinary practice help.

ALTER TABLE question_events ADD COLUMN leak_overlap REAL;
ALTER TABLE question_events ADD COLUMN remediation_episode_id TEXT;

CREATE TABLE reveal_events (
  id TEXT PRIMARY KEY,
  practice_item_id TEXT NOT NULL,
  learning_object_id TEXT,
  remediation_episode_id TEXT,
  source_kind TEXT NOT NULL CHECK (
    source_kind IN (
      'tutor_answer',
      'repair_display',
      'guided_redo',
      'source_review'
    )
  ),
  amount REAL NOT NULL CHECK (amount >= 0.0 AND amount <= 1.0),
  basis TEXT,
  question_event_id TEXT,
  attempt_id TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX idx_reveal_events_item_created
  ON reveal_events(practice_item_id, created_at, id);
CREATE INDEX idx_reveal_events_episode
  ON reveal_events(remediation_episode_id);
CREATE INDEX idx_question_events_remediation_episode
  ON question_events(remediation_episode_id);

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
