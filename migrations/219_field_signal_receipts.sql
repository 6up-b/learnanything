-- Reader workbench RW2d: workbench signals in the learner field
-- (spec_reader_workbench_v1 §5.11, G41; docs/reviews/reader-workbench-RW2d.md;
-- the learner field's F3: a change to what is served writes receipts,
-- including what the old rule would have done where that is cheap).
--
-- Numbered 219, the next free number after 218 (adaptive difficulty AD2+AD3
-- holds 214 on its own branch; the migration runner has no contiguity rule).
--
-- At the successor (WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION) a mid-work
-- workbench stuck step with text and help asked for before the first step are
-- field signals that keep an LO out of fast-track. When they change a
-- placement decision, this records what the predecessor's derivation (the
-- same rows without the workbench ones) and its rule would have decided:
--
-- * decision_kind 'fast_track': a fast-track candidate (enough clean answers)
--   whose blocking signals differ; written by the persisting queue build's
--   reconcile, once per LO, workbench signal set and predecessor verdict
--   (receipt_key), so a withheld fast-track the old rule would have fired
--   leaves a row although it writes no assumption_decisions row;
-- * decision_kind 'quick_check': an LO of a finished quick check whose split
--   verdict differs, written in the transaction that records the split
--   (decision_ref: the calibration session).
--
-- predecessor_json and successor_json are {blocking_signal_ids, verdict,
-- reason, p}; signal_ids_json the workbench signal ids on the LO. The
-- new-material order's receipt is the candidate component
-- taught_first_predecessor (scheduler_slate_candidates.components_json).
--
-- RECEIPT, append-only by trigger: never evidence, never read by any
-- scoring, scheduling, projection, serving or replay path, never written or
-- cleared by a rebuild. Kill switch: workbench.field_signals_enabled (off, or
-- below the tag, no row is written).
CREATE TABLE field_signal_receipts (
  id TEXT PRIMARY KEY,
  -- Idempotency: <decision_kind>:<decision_ref>:<lo>:<sha256 of the
  -- workbench ids and the predecessor verdict>.
  receipt_key TEXT NOT NULL UNIQUE,
  decision_kind TEXT NOT NULL CHECK (decision_kind IN ('fast_track', 'quick_check')),
  decision_ref TEXT,
  learning_object_id TEXT NOT NULL,
  signal_ids_json TEXT NOT NULL,
  predecessor_json TEXT NOT NULL,
  successor_json TEXT NOT NULL,
  signal_version TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX field_signal_receipts_lo ON field_signal_receipts(learning_object_id, created_at, id);

CREATE TRIGGER field_signal_receipts_no_update
BEFORE UPDATE ON field_signal_receipts
BEGIN
  SELECT RAISE(ABORT, 'field_signal_receipts is append-only');
END;

CREATE TRIGGER field_signal_receipts_no_delete
BEFORE DELETE ON field_signal_receipts
BEGIN
  SELECT RAISE(ABORT, 'field_signal_receipts is append-only');
END;
