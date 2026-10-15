-- Saved diagnosis forecasts (owner go-ahead 2026-10-15; docs/reviews/
-- diagnosis-forecast-receipts.md). Built as 230, a placeholder number, while
-- the diagnosis-input-provenance landing holds 205: renumbered at landing.
--
-- One append-only receipt per forecast, written in the transaction of the
-- decision that made it and BEFORE its outcome can be known: a persisted
-- diagnosis's prediction of the next observation that tests its hypothesis,
-- a repair's predicted cold outcome. The shape generalizes EVSI calibration
-- Part B's `voi_forecasts` (migration 184; its rows are read by the same
-- report as the `check_outcome` kind) so adaptive difficulty AD1's
-- `item_forecasts` (spec_adaptive_difficulty_v1 §8.1) can be the same family:
-- a forecaster, a scope, the inputs it read as of when, the forecast payload,
-- an exact binding to the observation that resolves it, and a resolution.
--
-- Resolutions are DERIVED at read time (`learnloop diagnosis calibration`)
-- from the attempt, presentation and cold-outcome ledgers, never written
-- here: a regrade re-resolves, a held grade resolves nothing until it is
-- released. A forecast with no exact binding is right-censored at birth
-- (`binding_kind = 'none'` with its `censor_reason`); one is never joined to
-- "the next attempt on the item" by a guess. Logging only: nothing serving,
-- scoring or scheduling reads this table, and a rebuild never writes or
-- clears it (RECEIPT). Kill switch: diagnosis.forecast_receipts.
CREATE TABLE forecast_receipts (
  id TEXT PRIMARY KEY,
  -- Idempotency: <kind>:<decision ref>:<subject>:<forecaster>.
  receipt_key TEXT NOT NULL UNIQUE,
  -- What is forecast: diagnosis_next_observation | repair_cold_outcome
  -- (AD1 adds item_unassisted_success; the vocabulary lives in code,
  -- learnloop.scheduling.forecast_receipts.FORECAST_KINDS).
  kind TEXT NOT NULL,
  -- Who forecast it, and the version of its code, priors and config.
  forecaster TEXT NOT NULL,
  forecaster_version TEXT NOT NULL,
  -- What the forecast is about: next_observation (the next qualifying
  -- observation of a facet, by the frozen rule in forecast_json),
  -- followup_task (the cold attempt one scheduled task binds), presentation
  -- or item (AD1).
  scope TEXT NOT NULL,
  -- The decision that wrote it: diagnosis | cold_retry_schedule (AD1: serve).
  decision_kind TEXT NOT NULL,
  decision_ref TEXT,
  source_attempt_id TEXT,
  learning_object_id TEXT,
  facet_id TEXT,
  hypothesis_ref TEXT,
  practice_item_id TEXT,
  -- AD1, scope item: the item revision an item-only forecast is about.
  item_content_hash TEXT,
  -- The exact binding the resolver may follow, and nothing else:
  -- presented_attempt_on_facet (the first qualifying attempt on the facet
  -- after the receipt, admitted only through its plan or probe presentation
  -- or the scheduler offer it answered), followup_task (the task's consumed
  -- attempt and terminal cold outcome), plan_presentation |
  -- probe_presentation (AD1), or none (censored at birth).
  binding_kind TEXT NOT NULL,
  plan_presentation_id TEXT,
  probe_presentation_id TEXT,
  followup_task_id TEXT,
  scheduler_candidate_id TEXT,
  censor_reason TEXT,
  -- The forecast event (next_observation_shape, cold_success; AD1
  -- unassisted_success) and its binary probability when it has one.
  event TEXT NOT NULL,
  p REAL CHECK (p IS NULL OR (p >= 0 AND p <= 1)),
  -- {emission_alphabet, predicted_outcomes, prior, likelihood, ...}: the
  -- body format of voi_forecasts.forecast_json.
  forecast_json TEXT NOT NULL,
  inputs_json TEXT NOT NULL,
  inputs_hash TEXT NOT NULL,
  -- The newest state the forecaster read; never after the receipt.
  inputs_as_of TEXT NOT NULL,
  parameters_json TEXT NOT NULL,
  versions_json TEXT NOT NULL,
  -- ok | failed | refused_spend (AD1's outside forecasters).
  status TEXT NOT NULL DEFAULT 'ok' CHECK (status IN ('ok', 'failed', 'refused_spend')),
  algorithm_version TEXT,
  -- When the forecast was issued (an in-process forecaster writes it then).
  created_at TEXT NOT NULL,
  -- AD1's outside forecasters: when a late answer arrived (null otherwise).
  received_at TEXT,
  CHECK ((binding_kind = 'none') = (censor_reason IS NOT NULL)),
  CHECK (inputs_as_of <= created_at)
);
CREATE INDEX idx_forecast_receipts_kind ON forecast_receipts(kind, created_at, id);
CREATE INDEX idx_forecast_receipts_facet ON forecast_receipts(learning_object_id, facet_id, created_at);
CREATE INDEX idx_forecast_receipts_decision ON forecast_receipts(decision_ref);
CREATE INDEX idx_forecast_receipts_task ON forecast_receipts(followup_task_id);
CREATE INDEX idx_forecast_receipts_plan_presentation ON forecast_receipts(plan_presentation_id);
CREATE INDEX idx_forecast_receipts_probe_presentation ON forecast_receipts(probe_presentation_id);

CREATE TRIGGER forecast_receipts_no_update
BEFORE UPDATE ON forecast_receipts
BEGIN
  SELECT RAISE(ABORT, 'forecast_receipts is append-only');
END;

CREATE TRIGGER forecast_receipts_no_delete
BEFORE DELETE ON forecast_receipts
BEGIN
  SELECT RAISE(ABORT, 'forecast_receipts is append-only');
END;
