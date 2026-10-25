-- Local contextual retrieval P1a/P1b (spec_local_contextual_retrieval_v1
-- §4.4, §5, §9.2; docs/reviews/retrieval-local-p1.md): the embedding space
-- registry, the retrieval feedback receipts and the fusion posterior.
--
-- Numbered 220 at its landing onto main (219 on its branch): reader workbench
-- RW2d's 219_field_signal_receipts landed first. The runner is set-based, so a
-- vault that applied this file as 219 on the branch is not an owner vault.
--
-- Nothing here changes scoring, scheduling, projection, grading or serving:
-- source retrieval is a lookup, not an exposure (spec §4.5), and replay
-- never re-runs retrieval. With embedding.local.enabled and
-- embedding.fallback.enabled false (the defaults) no row is ever written.

-- WORKFLOW: each embedding space a vault has used for source retrieval, with
-- its pins (every field of its id), its status and its stored canaries.
-- Mutable (a space moves to epoch_drift or retired) and preserved across
-- replay. Receipts cite the space id, so a retired space stays interpretable.
CREATE TABLE embedding_spaces (
  space_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('local', 'hosted', 'incumbent')),
  pins_json TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active', 'fallback', 'incumbent', 'retired', 'epoch_drift')),
  status_reason TEXT,
  canaries_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  retired_at TEXT
);

-- RECEIPT, append-only: what one search delivered and the signals that later
-- fell on it (§9.2). One 'query' row per logged search (its spaces, their
-- availability and reasons, the served and the would-be learned weights,
-- the exploration draw and its propensities, the RNG seed); one 'delivered'
-- row per delivered span (its rank in every contributing list and its
-- position); a 'cited', 'opened' or 'anchored' row per signal, naming the
-- query receipt it answers. No "not relevant" button exists: learner text
-- and actions are the signals.
CREATE TABLE retrieval_feedback (
  id TEXT PRIMARY KEY,
  receipt_id TEXT NOT NULL,
  event TEXT NOT NULL CHECK (event IN ('query', 'delivered', 'cited', 'opened', 'anchored')),
  consumer TEXT NOT NULL,
  query_kind TEXT NOT NULL,
  owner_id TEXT NOT NULL DEFAULT '',
  extraction_id TEXT,
  span_id TEXT,
  position INTEGER CHECK (position IS NULL OR position >= 1),
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  CHECK ((event = 'query') = (span_id IS NULL))
);

CREATE INDEX retrieval_feedback_receipt ON retrieval_feedback(receipt_id, event);
CREATE INDEX retrieval_feedback_owner ON retrieval_feedback(consumer, owner_id, event);

CREATE TRIGGER retrieval_feedback_no_update
BEFORE UPDATE ON retrieval_feedback
BEGIN
  SELECT RAISE(ABORT, 'retrieval_feedback is append-only');
END;

CREATE TRIGGER retrieval_feedback_no_delete
BEFORE DELETE ON retrieval_feedback
BEGIN
  SELECT RAISE(ABORT, 'retrieval_feedback is append-only');
END;

-- DERIVED: the fusion posterior per context (the global context and each
-- consumer x query kind), recomputed from retrieval_feedback in order by its
-- one replayer (substrate/rebuild_orchestrator.py, retrieval_fusion_posteriors).
-- Deterministic: the fit has no random step and fitted_at is the newest input
-- row's time, so a replay is byte-identical.
CREATE TABLE retrieval_fusion_posteriors (
  context_key TEXT PRIMARY KEY,
  consumer TEXT NOT NULL,
  query_kind TEXT NOT NULL,
  lists_json TEXT NOT NULL,
  mean_json TEXT NOT NULL,
  covariance_json TEXT NOT NULL,
  intercepts_json TEXT NOT NULL,
  examination_json TEXT NOT NULL,
  rrf_k REAL NOT NULL,
  observations INTEGER NOT NULL,
  signals INTEGER NOT NULL,
  prior_basis_json TEXT NOT NULL,
  fit_version TEXT NOT NULL,
  input_digest TEXT NOT NULL,
  fitted_at TEXT NOT NULL
);
