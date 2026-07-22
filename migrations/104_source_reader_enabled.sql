-- Per-source reader participation (owner decision 2026-07-20): some sources
-- (practice exams, reference sheets) don't belong in the question/ask reading
-- loop. Chosen at ingest setup; default ON. Exam-mode ingests default OFF at
-- the enqueue layer, not here.
ALTER TABLE source_artifacts ADD COLUMN reader_enabled INTEGER NOT NULL DEFAULT 1;
