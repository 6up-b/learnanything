-- Reader workbench RW4a: library questions (spec_reader_workbench_v1 §7.3,
-- §7.5; docs/reviews/reader-workbench-RW4a.md).
--
-- One row per "ask your library": the learner's question, the sources
-- service's find_sources manifests (the main call and one per concept-graph
-- expansion, each with its policy and how it was derived), the organizer's
-- lines (each citing exactly its own hit, with its judgment_ledger id), and,
-- when the learner went on, the comparison (a source_comparisons row, the
-- sources spec's) and the tutor exchange (a question_events row). RW4d's
-- kept_json and kept_at are created here so RW4d adds no migration (§7.5,
-- §11): the kept object and relation ids, each with its fine relation label.
--
-- WORKFLOW: paid outputs, never re-run on rebuild. Nothing here is evidence:
-- replay and rebuild never read it, and no scoring, scheduling, projection or
-- serving path does. Kill switches: library_ask.enabled,
-- library_ask.expand_graph, reader_compare.enabled.
CREATE TABLE library_asks (
  id TEXT PRIMARY KEY,
  -- Who asked: the learner (the Reader, the library search) or, later, the
  -- tutor's own request (RW1c / the sources spec's S4).
  caller TEXT NOT NULL CHECK (caller IN ('learner', 'tutor')),
  -- Where it was asked from: the library search box, Ctrl+Shift+F in the
  -- Reader, a selection's palette action.
  entry TEXT NOT NULL CHECK (entry IN (
    'library_search', 'reader', 'where_else_explained', 'where_is_this_used', 'what_do_i_need_first'
  )),
  query_md TEXT NOT NULL,
  query_hash TEXT NOT NULL,
  -- The open source and the passage the question was anchored on, if any.
  extraction_id TEXT,
  anchor_json TEXT NOT NULL DEFAULT '{}',
  personalized INTEGER NOT NULL CHECK (personalized IN (0, 1)),
  requested_perspectives_json TEXT NOT NULL DEFAULT '[]',
  manifest_json TEXT NOT NULL DEFAULT '{}',
  organizer_json TEXT NOT NULL DEFAULT '{}',
  comparison_id TEXT REFERENCES source_comparisons(id),
  kept_json TEXT,
  kept_at TEXT,
  question_event_id TEXT,
  model TEXT,
  prompt_version TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_library_asks_created ON library_asks(created_at);
CREATE INDEX idx_library_asks_extraction ON library_asks(extraction_id, created_at);
