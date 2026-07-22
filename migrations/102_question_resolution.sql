-- Outstanding-question queue: learner-facing resolution state on question_events
-- (spec_andymatusnotes "queue of outstanding questions"). A tutor-`answered`
-- question is NOT necessarily resolved -- the learner may still be confused, and
-- deciding that is theirs (answer_status tracks the tutor; resolution tracks the
-- learner). Every captured question starts `open` and stays visibly in the queue
-- until the learner marks it resolved or dismisses it. Backfill: existing rows
-- open -- old vaults are reinitialized under the fresh-vault-only scope, so the
-- default only ever governs fresh captures.
ALTER TABLE question_events ADD COLUMN resolution TEXT NOT NULL DEFAULT 'open'
  CHECK (resolution IN ('open', 'resolved', 'dismissed'));

CREATE INDEX idx_question_events_resolution ON question_events(resolution, created_at);
