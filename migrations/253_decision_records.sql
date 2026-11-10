-- Refactor B1 (docs/specs/refactor_strategy_v3.md §2.4 B1, §3; Decisions/ADR-017): the decision record and the trace id.
--
-- Additive: one new append-only RECEIPT table and one nullable column on model_call_receipts. No row is changed or
-- backfilled, and nothing scoring, scheduling, FSRS, mastery, the projection or any replay reads either (no successor:
-- a receipt and an accounting column carry no persisted meaning).
--
-- decision_records: one row per decision at a meaningful boundary (a plan block, a model answer, an offer withdrawn,
-- an exclusion...), written by the imperative shell from learnloop.provenance.DecisionRecord. It points to the rich
-- domain row (detail_table, detail_id) where one exists, and is the row where none does (failures, exclusions,
-- refusals). Its values are ids, numbers and code constants only, never learner or item text, prompts or model output
-- (learnloop.provenance.check_no_prose); payloads stay in model_call_receipts. Old decisions get no backfilled record.
-- No rebuild, replay or upgrade path reads or clears it, and AD's guard denies it.
--
-- * trace_id: one learner-visible action and its background work (born per sidecar RPC, phone request, MCP tool call
--   and CLI command); parent_id: the record that caused this one, possibly in an earlier trace.
-- * subject_kind, subject_id: how a learner-visible thing (attempt, item, block, offer, figure, job) finds its records.
-- * alternatives_json: [{ref, p, score, lost_by}], at most 50 (the overflow is counted per rule in facts_json).
-- * error_type, error_where: the exception class and module:function:line on a failure; never the message.
--
-- model_call_receipts.trace_id: the trace the call ran under, set when the call starts. It joins a decision to its
-- calls without the boundary key's JSON join. NULL for every call before this migration and every call made outside
-- an entry point; no projection reads it.
CREATE TABLE decision_records (
  id TEXT PRIMARY KEY,
  trace_id TEXT NOT NULL,
  parent_id TEXT,
  kind TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN (
    'chosen', 'fallback', 'excluded', 'withdrawn', 'timeout', 'discarded', 'failed', 'refused', 'deferred')),
  subject_kind TEXT,
  subject_id TEXT,
  chosen_ref TEXT,
  decided_by TEXT,
  rule TEXT,
  alternatives_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(alternatives_json)),
  facts_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(facts_json)),
  versions_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(versions_json)),
  detail_table TEXT,
  detail_id TEXT,
  error_type TEXT,
  error_where TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX decision_records_trace ON decision_records(trace_id, created_at, id);
CREATE INDEX decision_records_subject ON decision_records(subject_kind, subject_id, created_at, id);
CREATE INDEX decision_records_parent ON decision_records(parent_id);
CREATE INDEX decision_records_kind ON decision_records(kind, created_at, id);

CREATE TRIGGER decision_records_no_update
BEFORE UPDATE ON decision_records
BEGIN
    SELECT RAISE(ABORT, 'decision_records is append-only');
END;

CREATE TRIGGER decision_records_no_delete
BEFORE DELETE ON decision_records
BEGIN
    SELECT RAISE(ABORT, 'decision_records is append-only');
END;

ALTER TABLE model_call_receipts ADD COLUMN trace_id TEXT;
CREATE INDEX model_call_receipts_trace ON model_call_receipts(trace_id) WHERE trace_id IS NOT NULL;
