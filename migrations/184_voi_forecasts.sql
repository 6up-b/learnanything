-- EVSI calibration Part B (docs/reviews/evsi-calibration.md): one append-only
-- receipt per live value-of-information decision, written beside the decision
-- (probe selection, the robust probe stop/abstain, follow-up selection, and
-- every evsi.rank_feasible caller). It records the forecast the decision ran
-- on: the predicted answer distribution of the chosen check, its EIG, the EVSI
-- point and robust values, the predicted probability that the check changes
-- the chosen action, every parameter with its provenance, and the versions.
-- `learnloop evsi calibration` joins the realized outcome (R1's
-- router_outcomes when present, else the probe and attempt ledgers) and later
-- truth at read time. Logging only: nothing serving reads this table, and a
-- rebuild never re-runs it (RECEIPT). Kill switch: evsi.forecast_logging.
CREATE TABLE voi_forecasts (
  id TEXT PRIMARY KEY,
  -- Idempotency: <site>:<decision ref>, e.g. probe_selection:<presentation>.
  receipt_key TEXT NOT NULL UNIQUE,
  -- probe_selection | probe_robust_selection | followup_selection |
  -- causal_shadow_selection | staged_diagnostic_selection (successors add
  -- sites in code; learnloop.scheduling.voi_forecasts.VOI_SITES).
  site TEXT NOT NULL,
  decision_ref TEXT,
  -- measure | stop | abstain | act | select (the decision's own verdict).
  verdict TEXT NOT NULL,
  learning_object_id TEXT,
  probe_episode_id TEXT,
  presentation_id TEXT,
  source_attempt_id TEXT,
  factor_id TEXT,
  chosen_ref TEXT,
  chosen_practice_item_id TEXT,
  scheduler_candidate_id TEXT,
  candidate_count INTEGER NOT NULL CHECK (candidate_count >= 0),
  eig_nats REAL,
  evsi_point_minutes REAL,
  evsi_lcb_minutes REAL,
  p_action_change REAL CHECK (p_action_change IS NULL OR (p_action_change >= 0 AND p_action_change <= 1)),
  forecast_json TEXT NOT NULL,
  parameters_json TEXT NOT NULL,
  versions_json TEXT NOT NULL,
  forecast_version TEXT NOT NULL,
  algorithm_version TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_voi_forecasts_created ON voi_forecasts(created_at, id);
CREATE INDEX idx_voi_forecasts_site ON voi_forecasts(site, created_at);
CREATE INDEX idx_voi_forecasts_presentation ON voi_forecasts(presentation_id);
CREATE INDEX idx_voi_forecasts_item ON voi_forecasts(chosen_practice_item_id, created_at);
CREATE INDEX idx_voi_forecasts_lo ON voi_forecasts(learning_object_id, created_at);

CREATE TRIGGER voi_forecasts_no_update
BEFORE UPDATE ON voi_forecasts
BEGIN
  SELECT RAISE(ABORT, 'voi_forecasts is append-only');
END;

CREATE TRIGGER voi_forecasts_no_delete
BEFORE DELETE ON voi_forecasts
BEGIN
  SELECT RAISE(ABORT, 'voi_forecasts is append-only');
END;
