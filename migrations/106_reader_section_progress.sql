-- Durable per-section reading progress (reader-first seeding). Previously
-- section reveal/completion lived only in React state and reset per source.
-- generation_batch_id is the idempotence stamp for the section-completion
-- practice-expansion trigger: NULL = not yet triggered; 'none_needed' = mapped
-- to zero targets; else the enqueued batch id.
CREATE TABLE reader_section_progress (
  extraction_id TEXT NOT NULL,
  section_id TEXT NOT NULL,
  spans_seen INTEGER NOT NULL DEFAULT 0,
  span_count INTEGER NOT NULL DEFAULT 0,
  revealed_at TEXT,
  completed_at TEXT,
  generation_batch_id TEXT,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (extraction_id, section_id)
);
