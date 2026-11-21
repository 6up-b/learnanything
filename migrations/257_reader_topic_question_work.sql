-- Question work owned per topic: one durable claim per topic for the first set of questions a learner's
-- reading commissions (purpose 'reader_first_set'), so that a topic is written for once, whichever section or
-- source cites it, and its checkpoints are its own rather than its section's.
--
-- Additive: one new table (WORKFLOW in db.table_roles, as reader_section_progress; DENIED to adaptive
-- difficulty). Nothing is backfilled here: section jobs queued before topic work existed are indexed as
-- section-job-owned rows by the code that claims new topics, just before it claims (their payloads name their
-- topics; their keys, request snapshots and proposals are left as they are). Nothing that scores, schedules,
-- certifies or counts exposure reads the table, and the questions written are the same rows as before, so there
-- is no algorithm tag.
--
-- One row per (learning_object_id, purpose): the claim. owner 'topic' is work this row owns (its batch was queued
-- in the claim's transaction, with work_key as the topic's checkpoint scope); owner 'section_job' is a topic a
-- section job named before topic work existed (state 'legacy': that job's state is the topic's, and its keys
-- are the section's). trigger_event says what claimed it ('section_finished'; 'part_read' is admitted for the
-- reading that qualifies a topic before its section is finished, and nothing writes it yet). The origin
-- (source_id, extraction_id, section_id) is where the claim was made; passage_ids_json and source_refs_json are
-- the topic's own frozen grounding; requested_count the questions its plan asked for when claimed;
-- model_settings_json the settings its first run asked under; proposal_ids_json the proposals written for it.
CREATE TABLE reader_topic_question_work (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT NOT NULL,
  purpose TEXT NOT NULL CHECK (purpose IN ('reader_first_set')),
  owner TEXT NOT NULL CHECK (owner IN ('topic', 'section_job')),
  source_id TEXT,
  extraction_id TEXT,
  section_id TEXT,
  trigger_event TEXT CHECK (trigger_event IS NULL OR trigger_event IN ('section_finished', 'part_read')),
  passage_ids_json TEXT NOT NULL DEFAULT '[]',
  source_refs_json TEXT NOT NULL DEFAULT '[]',
  requested_count INTEGER,
  model_settings_json TEXT,
  work_key TEXT,
  batch_id TEXT,
  job_id TEXT,
  proposal_ids_json TEXT NOT NULL DEFAULT '[]',
  state TEXT NOT NULL CHECK (state IN ('queued', 'running', 'written', 'held', 'failed', 'not_needed', 'legacy')),
  error TEXT,
  claimed_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (learning_object_id, purpose),
  CHECK ((owner = 'section_job') = (state = 'legacy')),
  CHECK (owner = 'section_job' OR (trigger_event IS NOT NULL AND work_key IS NOT NULL AND batch_id IS NOT NULL))
);
CREATE INDEX idx_reader_topic_question_work_section ON reader_topic_question_work(extraction_id, section_id);
CREATE INDEX idx_reader_topic_question_work_source ON reader_topic_question_work(source_id);
CREATE INDEX idx_reader_topic_question_work_batch ON reader_topic_question_work(batch_id);
