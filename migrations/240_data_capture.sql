-- Data capture A1, A2 (the long-horizon objective; docs/reviews/data-capture-a1-a6.md).
-- Numbered 240 at landing: M2a landed first and took 239 (landing ruling R5).
--
-- Additive: four append-only tables, no existing row or table changes, and
-- nothing replay reads for scoring, FSRS, mastery or the projection.
--
-- 1. prefilter_payloads (RECEIPT, content-addressed): one part of a prefilter
--    receipt (scheduler gates, the plan's classification, the upstream probe
--    and teach-back trace, the inputs, the configuration), stored once by its
--    own hash, so an unchanged part is referenced and never copied. The canonical
--    JSON is zlib-compressed (content_z); the hash is over the JSON text.
--
-- 2. prefilter_receipts (RECEIPT): what was decided before the router saw
--    candidates, one row per committed decision: the considered, admitted and
--    refused counts, the versions and code revision, and the hashes of its
--    parts. Deterministic admission is probability 0 or 1 inside the parts;
--    the decision's own propensity stays conditional on admission.
--
-- 3. decision_objectives (RECEIPT): the objective a decision's arms are
--    evaluated on, frozen from pre-draw inputs: its learning object and
--    predeclared scope, the arm actually drawn, and whether a measurement was
--    arranged. The outcome adapter (router_outcomes_v3) reads it.
--
-- 4. decision_measurement_events (RECEIPT): the states of an arranged measurement:
--    due, offered, answered, unavailable. A state is written once per reason and
--    episode (a check unavailable today for a reason may be offered tomorrow and lost
--    again for the same reason: episode names the offer or due date that opened each
--    one), so treatment-dependent censoring stays visible and folds in time order.
-- 5. reading_exposure_receipts (RECEIPT): Reader activity on a learning object, the
--    fact and its source time, frozen for the delayed-completion definition whatever
--    adaptive difficulty's forecast logging says (its ad_reading_opportunities are
--    written only under forecast_receipts). No dwell, no magnitude, no answer text.
CREATE TABLE prefilter_payloads (
  content_hash TEXT PRIMARY KEY,
  part TEXT NOT NULL CHECK (part IN ('gates', 'classification', 'upstream', 'inputs', 'config')),
  content_z BLOB NOT NULL,
  raw_bytes INTEGER NOT NULL,
  stored_bytes INTEGER NOT NULL,
  first_seen_at TEXT NOT NULL
);
CREATE TRIGGER prefilter_payloads_no_update
BEFORE UPDATE ON prefilter_payloads
BEGIN
    SELECT RAISE(ABORT, 'prefilter_payloads is append-only');
END;
CREATE TRIGGER prefilter_payloads_no_delete
BEFORE DELETE ON prefilter_payloads
BEGIN
    SELECT RAISE(ABORT, 'prefilter_payloads is append-only');
END;

CREATE TABLE prefilter_receipts (
  id TEXT PRIMARY KEY,
  decision_id TEXT NOT NULL UNIQUE REFERENCES router_decisions(id),
  decision_kind TEXT NOT NULL,
  surface TEXT NOT NULL,
  receipt_version TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  code_revision TEXT NOT NULL,
  config_hash TEXT NOT NULL,
  versions_json TEXT NOT NULL,
  session_present INTEGER NOT NULL CHECK (session_present IN (0, 1)),
  scheduler_trace INTEGER NOT NULL CHECK (scheduler_trace IN (0, 1)),
  considered_count INTEGER NOT NULL CHECK (considered_count >= 0),
  admitted_count INTEGER NOT NULL CHECK (admitted_count >= 0),
  refused_count INTEGER NOT NULL CHECK (refused_count >= 0),
  gates_hash TEXT NOT NULL REFERENCES prefilter_payloads(content_hash),
  classification_hash TEXT NOT NULL REFERENCES prefilter_payloads(content_hash),
  upstream_hash TEXT NOT NULL REFERENCES prefilter_payloads(content_hash),
  inputs_hash TEXT NOT NULL REFERENCES prefilter_payloads(content_hash),
  config_payload_hash TEXT NOT NULL REFERENCES prefilter_payloads(content_hash),
  created_at TEXT NOT NULL
);
CREATE INDEX prefilter_receipts_created ON prefilter_receipts(created_at);
CREATE TRIGGER prefilter_receipts_no_update
BEFORE UPDATE ON prefilter_receipts
BEGIN
    SELECT RAISE(ABORT, 'prefilter_receipts is append-only');
END;
CREATE TRIGGER prefilter_receipts_no_delete
BEFORE DELETE ON prefilter_receipts
BEGIN
    SELECT RAISE(ABORT, 'prefilter_receipts is append-only');
END;

CREATE TABLE decision_objectives (
  decision_id TEXT PRIMARY KEY REFERENCES router_decisions(id),
  decision_kind TEXT NOT NULL,
  objective_version TEXT NOT NULL,
  learning_object_id TEXT,
  source TEXT NOT NULL,
  scope_json TEXT NOT NULL,
  arm TEXT NOT NULL,
  support_json TEXT NOT NULL,
  -- arranged: a check commitment measures it; shared: another pending check on
  -- the LO does; natural: left to ordinary retrievals (no real choice was made);
  -- unavailable: nothing to measure with (reason on its decision_measurement_events row).
  measurement TEXT NOT NULL CHECK (measurement IN ('arranged', 'shared', 'natural', 'unavailable')),
  commitment_id TEXT,
  practice_item_id TEXT,
  pick_json TEXT NOT NULL DEFAULT '{}',
  experiment_id TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX decision_objectives_lo ON decision_objectives(learning_object_id, created_at);
CREATE INDEX decision_objectives_commitment ON decision_objectives(commitment_id);
CREATE TRIGGER decision_objectives_no_update
BEFORE UPDATE ON decision_objectives
BEGIN
    SELECT RAISE(ABORT, 'decision_objectives is append-only');
END;
CREATE TRIGGER decision_objectives_no_delete
BEFORE DELETE ON decision_objectives
BEGIN
    SELECT RAISE(ABORT, 'decision_objectives is append-only');
END;

CREATE TABLE decision_measurement_events (
  id TEXT PRIMARY KEY,
  decision_id TEXT NOT NULL REFERENCES decision_objectives(decision_id),
  state TEXT NOT NULL CHECK (state IN ('due', 'offered', 'answered', 'unavailable')),
  reason TEXT NOT NULL DEFAULT '',
  practice_item_id TEXT,
  attempt_id TEXT,
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  -- What opened this availability episode: a due date, a presentation, the last of those for an unavailable state.
  episode TEXT NOT NULL DEFAULT '',
  UNIQUE (decision_id, state, reason, episode)
);
CREATE INDEX decision_measurement_events_decision ON decision_measurement_events(decision_id, created_at);
CREATE TRIGGER decision_measurement_events_no_update
BEFORE UPDATE ON decision_measurement_events
BEGIN
    SELECT RAISE(ABORT, 'decision_measurement_events is append-only');
END;
CREATE TRIGGER decision_measurement_events_no_delete
BEFORE DELETE ON decision_measurement_events
BEGIN
    SELECT RAISE(ABORT, 'decision_measurement_events is append-only');
END;

CREATE TABLE reading_exposure_receipts (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  subkind TEXT NOT NULL,
  source_table TEXT NOT NULL,
  source_id TEXT NOT NULL,
  source_written_at TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  mapping_version TEXT NOT NULL,
  swept_at TEXT NOT NULL,
  UNIQUE (kind, subkind, source_table, source_id, learning_object_id)
);
CREATE INDEX reading_exposure_receipts_source_time ON reading_exposure_receipts(source_written_at);
CREATE TRIGGER reading_exposure_receipts_no_update
BEFORE UPDATE ON reading_exposure_receipts
BEGIN
    SELECT RAISE(ABORT, 'reading_exposure_receipts is append-only');
END;
CREATE TRIGGER reading_exposure_receipts_no_delete
BEFORE DELETE ON reading_exposure_receipts
BEGIN
    SELECT RAISE(ABORT, 'reading_exposure_receipts is append-only');
END;
