-- Reader quick-check producer: AI-authored section-boundary questions.
-- One row per authored question. The row is the record: statuses live here
-- (proposed -> answered | dismissed | escalated), never on new
-- interaction-event kinds, and answering never touches attempts/mastery.
CREATE TABLE reader_authored_questions (
  id TEXT PRIMARY KEY,
  extraction_id TEXT NOT NULL,
  section_id TEXT NOT NULL,
  source_id TEXT,
  question_md TEXT NOT NULL,
  expected_answer_md TEXT NOT NULL,
  span_ids_json TEXT NOT NULL DEFAULT '[]',
  prompt_version TEXT NOT NULL,
  provider TEXT,
  model TEXT,
  status TEXT NOT NULL DEFAULT 'proposed'
    CHECK (status IN ('proposed', 'answered', 'dismissed', 'escalated')),
  response_md TEXT,
  answered_at TEXT,
  practice_item_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX idx_reader_authored_questions_section
  ON reader_authored_questions(extraction_id, section_id, status);
