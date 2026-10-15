-- Diagnosis input provenance (spec_mcp_frontend_c1 §4.8; owner decision
-- 2026-10-14, "land narrow, then fix source"): every model-written text the
-- chat frontend withholds carries a write-time record of what it was written
-- from, so the chat read model's rule (c) can release it once every recorded
-- input is safe. Inputs are recorded at the source, never inferred from the
-- output. Built on diagnosis/input-provenance as migration 204, a
-- placeholder, and renumbered 205 at its landing on main after re-read
-- safety's 204 (source_held_out_signal_marks).
--
-- text_write_provenance (RAW_LEDGER, append-only): one row per write of one
-- derived text (or per grading, the origin a grader's output is folded from).
-- `kind` + `record_id` name the text (a diagnosis summary, a hypothesis, a
-- candidate or misconception statement, a correction, a learner-text gap's
-- words, a generated topic's name, a seeded item's question, a grading).
-- `text_sha256` is the hash of the text as written, so a later write by a
-- writer that recorded nothing is detected (the record no longer covers the
-- text). `inputs_json` is the closed record (the writer's own reads plus the
-- recorded inputs of every derived text it read): answers with the contract
-- revision they were read under, items whose question was read, items whose
-- rubric or reference solution was read (directly or through a grader's
-- output), topics, source refs and learner questions with their contracts.
-- `complete` is 0 when the writer read something it could not account for;
-- `incomplete_reasons_json` names it. A text with no row is held back.
--
-- error_event_lineage (RAW_LEDGER, append-only; Q9): a regrade re-mints the
-- attempt's error events; each re-minted event records the ids it replaces,
-- so a belief that lists a replaced event stays resolvable. A regrade that
-- leaves the answer with no error retires its events with no replacement:
-- one row per retired id with error_event_id NULL (the explicit "no current
-- error"), so the retired id still names its attempt.
--
-- question_events.assessment_contract_version_id (Q10): the item contract
-- (revision) a learner question was asked about, recorded when the question
-- is written; NULL for a question on no item, and for every question written
-- before this migration (they stay held back).

CREATE TABLE text_write_provenance (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN (
    'diagnosis', 'grading', 'hypothesis', 'candidate', 'misconception',
    'misconception_correction', 'learner_text_gap', 'learning_object',
    'practice_item'
  )),
  record_id TEXT NOT NULL,
  text_sha256 TEXT,
  writer TEXT NOT NULL,
  complete INTEGER NOT NULL CHECK (complete IN (0, 1)),
  incomplete_reasons_json TEXT NOT NULL DEFAULT '[]',
  inputs_json TEXT NOT NULL,
  derived_from_json TEXT NOT NULL DEFAULT '[]',
  provenance_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX idx_text_write_provenance_record
  ON text_write_provenance(kind, record_id, created_at, id);

CREATE TRIGGER text_write_provenance_no_update
BEFORE UPDATE ON text_write_provenance
BEGIN
  SELECT RAISE(ABORT, 'text_write_provenance is append-only');
END;
CREATE TRIGGER text_write_provenance_no_delete
BEFORE DELETE ON text_write_provenance
BEGIN
  SELECT RAISE(ABORT, 'text_write_provenance is append-only');
END;

CREATE TABLE error_event_lineage (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL,
  error_event_id TEXT,
  replaces_error_event_id TEXT NOT NULL,
  reason TEXT NOT NULL CHECK (reason IN ('regrade')),
  created_at TEXT NOT NULL,
  UNIQUE (error_event_id, replaces_error_event_id)
);

CREATE INDEX idx_error_event_lineage_replaced
  ON error_event_lineage(replaces_error_event_id);
CREATE UNIQUE INDEX idx_error_event_lineage_retired
  ON error_event_lineage(replaces_error_event_id) WHERE error_event_id IS NULL;
CREATE INDEX idx_error_event_lineage_attempt
  ON error_event_lineage(attempt_id, created_at);

CREATE TRIGGER error_event_lineage_no_update
BEFORE UPDATE ON error_event_lineage
BEGIN
  SELECT RAISE(ABORT, 'error_event_lineage is append-only');
END;
CREATE TRIGGER error_event_lineage_no_delete
BEFORE DELETE ON error_event_lineage
BEGIN
  SELECT RAISE(ABORT, 'error_event_lineage is append-only');
END;

ALTER TABLE question_events ADD COLUMN assessment_contract_version_id TEXT;
