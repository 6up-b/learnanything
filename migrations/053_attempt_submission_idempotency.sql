-- Network/RPC submission idempotency. A client-generated submission id belongs
-- to exactly one formal attempt; the response receipt lets retries return the
-- original result without re-grading or replaying side effects.
ALTER TABLE practice_attempts ADD COLUMN submission_id TEXT;
ALTER TABLE practice_attempts ADD COLUMN declared_dont_know INTEGER NOT NULL DEFAULT 0;
CREATE UNIQUE INDEX idx_practice_attempts_submission_id
  ON practice_attempts(submission_id)
  WHERE submission_id IS NOT NULL;

CREATE TABLE attempt_submission_receipts (
  submission_id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL UNIQUE REFERENCES practice_attempts(id),
  practice_item_id TEXT NOT NULL,
  result_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
