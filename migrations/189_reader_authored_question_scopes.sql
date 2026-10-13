-- Reader workbench RW1a (spec_reader_workbench_v1 §4.3): quick-check scopes.
--
-- The quick-check producer gains a passage scope: the reconnect line's
-- "quick check" asks one formative question about an inquiry's root passage.
-- Every row keeps its section (section_id stays NOT NULL: a passage-scoped row
-- carries its anchor's section), and the section lookups filter
-- scope_kind = 'section', so a reconnect row never shadows its section's
-- quick check. Section rows default to today's values and stay byte-identical.
--
-- question_style is created with every value the reader workbench writes
-- (RW1b adds the last four), so no later phase rebuilds this table.
-- self_check records the learner's own verdict after the expected answer is
-- shown (matches · partly · no); section quick checks leave it NULL. Answering
-- stays formative: no attempt, observation, mastery or FSRS row (W1 tier 2).
-- Reuse keys: section rows as before; inquiry rows per
-- (inquiry_root_event_id, prompt_version), which the database enforces (a
-- UNIQUE partial index: two workers can never land two checks for one
-- inquiry, and a late completion can never replace the one the learner saw);
-- selection rows per (extraction, anchor spans, style, prompt version).
ALTER TABLE reader_authored_questions ADD COLUMN scope_kind TEXT NOT NULL DEFAULT 'section'
  CHECK (scope_kind IN ('section', 'inquiry', 'selection'));
ALTER TABLE reader_authored_questions ADD COLUMN question_style TEXT NOT NULL DEFAULT 'recall'
  CHECK (question_style IN ('recall', 'next_step', 'why_step', 'assumptions', 'reconstruct'));
ALTER TABLE reader_authored_questions ADD COLUMN anchor_span_ids_json TEXT;
ALTER TABLE reader_authored_questions ADD COLUMN inquiry_root_event_id TEXT;
ALTER TABLE reader_authored_questions ADD COLUMN self_check TEXT
  CHECK (self_check IS NULL OR self_check IN ('matches', 'partly', 'no'));

CREATE UNIQUE INDEX idx_reader_authored_questions_inquiry
  ON reader_authored_questions(inquiry_root_event_id, prompt_version)
  WHERE inquiry_root_event_id IS NOT NULL;
