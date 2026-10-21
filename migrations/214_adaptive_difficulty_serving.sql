-- Adaptive difficulty AD2+AD3: practice in the band, the subject view live
-- (spec_adaptive_difficulty_v1 §14 AD2/AD3, §6.1, §7.4, §5.10-5.12, §8.3,
-- §11.2; docs/reviews/adaptive-difficulty-ad23.md). One algorithm successor
-- (mvp-0.28); below its tag, or with its switches off, nothing writes here
-- except the dose arm's ledger (outside the successor, its own switch).
--
-- `item_substituted` and `item_displaced` (reason `ad_ineligible`) are block
-- events of the existing `attention_block_events` ledger (free-text kind and
-- detail), so they need no table. The `ad_threshold@*` forecasts are kind
-- `item_unassisted_success` rows of migration 206's `forecast_receipts`.

-- §6.1: every AD draw, serve or commission, with its support (or commission
-- candidates), both scores and the exact propensity of every candidate, each
-- excluded candidate's failed checks, the seed and the choice, written in the
-- deciding transaction BEFORE the item is served (A7). Append-only: a landed
-- commission's re-forecast is its own receipt, never an update here.
CREATE TABLE ad_selections (
  id TEXT PRIMARY KEY,
  decision_key TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL CHECK (kind IN ('serve', 'commission')),
  -- The view the draw read: `subject` (promoted_predictor on) or `lo:<id>`.
  view TEXT NOT NULL,
  learning_object_id TEXT,
  cell_facet TEXT,
  cell_capability TEXT,
  daily_plan_id TEXT,
  block_id TEXT,
  slot_position INTEGER,
  slot_item_id TEXT,
  mode TEXT NOT NULL CHECK (mode IN ('band', 'calibrate', 'predecessor', 'empty_support')),
  -- [{ref, p_band, p_bar, info, propensity}] over the support S (serve) or X_c (commission).
  support_json TEXT NOT NULL,
  -- [{ref, failed: [check, ...]}]: candidates that were not in S, and why.
  excluded_json TEXT NOT NULL,
  constants_json TEXT NOT NULL,
  seed TEXT NOT NULL,
  u REAL,
  chosen_item_id TEXT,
  chosen_point_json TEXT,
  propensity REAL,
  -- §10.1: the router's propensity for the block, and the pair's.
  router_decision_id TEXT,
  router_propensity REAL,
  pair_propensity REAL,
  empty_support INTEGER NOT NULL CHECK (empty_support IN (0, 1)),
  state_hash TEXT NOT NULL,
  versions_json TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  -- A commission the generation path drew inside a durable job: that job
  -- (`ingest_jobs.id`, no foreign key: jobs may be pruned). Its expiry clock
  -- starts when the job finishes (Codex verify F14). NULL for a serve draw,
  -- a serve-time commission (its batch is named by it) and a draw outside a job.
  generating_job_id TEXT,
  created_at TEXT NOT NULL,
  -- The protection epoch the row was computed under (AD23 redesign round 2):
  -- AD reads a row back only at that epoch (adaptive_difficulty.protected_tables.EPOCH).
  protection_epoch TEXT
);
CREATE INDEX idx_ad_selections_cell ON ad_selections(kind, cell_facet, cell_capability, created_at);
CREATE INDEX idx_ad_selections_block ON ad_selections(block_id, slot_position);

CREATE TRIGGER ad_selections_no_update
BEFORE UPDATE ON ad_selections
BEGIN
  SELECT RAISE(ABORT, 'ad_selections is append-only');
END;

CREATE TRIGGER ad_selections_no_delete
BEFORE DELETE ON ad_selections
BEGIN
  SELECT RAISE(ABORT, 'ad_selections is append-only');
END;

-- §7.4: a landed commission's re-forecast, linked to its selection; the
-- combined status is derived, the selection row is never mutated.
CREATE TABLE ad_commission_results (
  id TEXT PRIMARY KEY,
  selection_id TEXT NOT NULL REFERENCES ad_selections(id),
  practice_item_id TEXT NOT NULL,
  content_hash TEXT,
  features_json TEXT,
  p_bar REAL NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('in_band', 'realized_out_of_band')),
  state_hash TEXT NOT NULL,
  -- 1 when the item landed after its commission had expired (Codex verify
  -- F15): the landing is recorded whatever the commission's expiry.
  landed_after_expiry INTEGER NOT NULL DEFAULT 0 CHECK (landed_after_expiry IN (0, 1)),
  -- Ownership is by cell and landing order, not by feature match (verify F15,
  -- round 6): `features_json` holds the item's realized features, and this is 1
  -- when they are the commission's requested point.
  features_match INTEGER NOT NULL DEFAULT 1 CHECK (features_match IN (0, 1)),
  created_at TEXT NOT NULL,
  -- The protection epoch the row was computed under (AD23 redesign round 2):
  -- AD reads a row back only at that epoch (adaptive_difficulty.protected_tables.EPOCH).
  protection_epoch TEXT,
  -- One owner per landed item (verify F16): the first attribution is final.
  UNIQUE (practice_item_id)
);

CREATE TRIGGER ad_commission_results_no_update
BEFORE UPDATE ON ad_commission_results
BEGIN
  SELECT RAISE(ABORT, 'ad_commission_results is append-only');
END;

CREATE TRIGGER ad_commission_results_no_delete
BEFORE DELETE ON ad_commission_results
BEGIN
  SELECT RAISE(ABORT, 'ad_commission_results is append-only');
END;

-- §5.12 (D21): the Reader's randomized dose offers. One `draw` row per
-- eligible section draw (the feasible variants and why any was infeasible,
-- the base policy's version, the floor, every propensity, the seed and the
-- chosen variant), written before anything is shown; later rows record
-- `delivered`, `not_delivered`, `taken` or `dismissed` and never change the
-- draw's row. No dwell, scroll, active time or answer value is stored.
CREATE TABLE ad_dose_offers (
  id TEXT PRIMARY KEY,
  row_kind TEXT NOT NULL
    CHECK (row_kind IN ('draw', 'delivered', 'not_delivered', 'taken', 'dismissed')),
  draw_id TEXT REFERENCES ad_dose_offers(id),
  draw_key TEXT UNIQUE,
  visit_id TEXT,
  extraction_id TEXT,
  section_id TEXT,
  learning_object_ids_json TEXT,
  feasible_json TEXT,
  infeasible_json TEXT,
  base_version TEXT,
  floor REAL,
  propensities_json TEXT,
  seed TEXT,
  u REAL,
  chosen_variant TEXT CHECK (chosen_variant IS NULL OR chosen_variant IN
    ('none', 'extra_worked_example', 'extra_question')),
  -- What an extra offer carries (a question id, a worked example's span), so a
  -- taken offer's reading opportunity can name it.
  content_json TEXT,
  -- The AD forecast fixed before the draw (precision adjustment, §5.12).
  forecast_p REAL,
  detail_json TEXT,
  created_at TEXT NOT NULL,
  -- The protection epoch the row was computed under (AD23 redesign round 2):
  -- AD reads a row back only at that epoch (adaptive_difficulty.protected_tables.EPOCH).
  protection_epoch TEXT,
  CHECK (
    (row_kind = 'draw' AND draw_id IS NULL AND draw_key IS NOT NULL)
    OR (row_kind != 'draw' AND draw_id IS NOT NULL AND draw_key IS NULL)
  )
);
CREATE INDEX idx_ad_dose_offers_draw ON ad_dose_offers(draw_id, created_at);
CREATE INDEX idx_ad_dose_offers_created ON ad_dose_offers(created_at);

CREATE TRIGGER ad_dose_offers_no_update
BEFORE UPDATE ON ad_dose_offers
BEGIN
  SELECT RAISE(ABORT, 'ad_dose_offers is append-only');
END;

CREATE TRIGGER ad_dose_offers_no_delete
BEFORE DELETE ON ad_dose_offers
BEGIN
  SELECT RAISE(ABORT, 'ad_dose_offers is append-only');
END;

-- §5.10: one relatedness proposal run per subject (the units it covered, the
-- judgment_ledger rows it appended, its input hash and status). The proposal
-- itself is judgment_ledger rows (task `ad_relatedness`); this receipt records
-- which units a run covered, so a unit re-proposed with nothing valid has none.
CREATE TABLE ad_relatedness_runs (
  id TEXT PRIMARY KEY,
  run_key TEXT NOT NULL UNIQUE,
  subject_id TEXT NOT NULL,
  input_hash TEXT NOT NULL,
  units_json TEXT NOT NULL,
  judgment_ids_json TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('ok', 'failed', 'refused_spend', 'protected', 'stale')),
  prompt_version TEXT NOT NULL,
  judge_model TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_ad_relatedness_runs_subject ON ad_relatedness_runs(subject_id, created_at);

CREATE TRIGGER ad_relatedness_runs_no_update
BEFORE UPDATE ON ad_relatedness_runs
BEGIN
  SELECT RAISE(ABORT, 'ad_relatedness_runs is append-only');
END;

CREATE TRIGGER ad_relatedness_runs_no_delete
BEFORE DELETE ON ad_relatedness_runs
BEGIN
  SELECT RAISE(ABORT, 'ad_relatedness_runs is append-only');
END;

-- §5.10 "As of": each adopted coupling version per subject. The subject view
-- is built under one version: its runs' proposals apply to the whole history;
-- a later run reaches only what did not exist yet. A new version is a
-- reinterpretation, adopted through the playbook with a shadow rebuild.
CREATE TABLE ad_coupling_versions (
  id TEXT PRIMARY KEY,
  subject_id TEXT NOT NULL,
  version INTEGER NOT NULL CHECK (version >= 1),
  coupling_version TEXT NOT NULL,
  run_ids_json TEXT NOT NULL,
  adopted_by TEXT NOT NULL,
  note TEXT,
  adopted_at TEXT NOT NULL,
  UNIQUE (subject_id, version)
);

CREATE TRIGGER ad_coupling_versions_no_update
BEFORE UPDATE ON ad_coupling_versions
BEGIN
  SELECT RAISE(ABORT, 'ad_coupling_versions is append-only');
END;

CREATE TRIGGER ad_coupling_versions_no_delete
BEFORE DELETE ON ad_coupling_versions
BEGIN
  SELECT RAISE(ABORT, 'ad_coupling_versions is append-only');
END;

-- §5.6, §11.2 (DERIVED; the AD replayer): the current posterior per view
-- (`subject`, or `lo:<id>`): per part, the moments AD reads (subject levels,
-- facet and cell moments, shared parameters, the grid weights and the
-- coupling versions), rebuilt byte-identically with zero model calls.
CREATE TABLE ad_state (
  view TEXT NOT NULL,
  part TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  state_hash TEXT NOT NULL,
  as_of TEXT,
  versions_json TEXT NOT NULL,
  PRIMARY KEY (view, part)
);

-- §5.6 step 6 (DERIVED; the AD replayer): per eligible attempt and view, the
-- prior and posterior moments of η, the predicted category probabilities, the
-- information gained, the input status, and, for the subject view, each grid
-- point's marginal likelihood and weight.
CREATE TABLE ad_attempt_trace (
  attempt_id TEXT NOT NULL,
  view TEXT NOT NULL,
  input_status TEXT NOT NULL CHECK (input_status IN ('frozen', 'exact', 'reconstructed_current', 'excluded')),
  category INTEGER,
  prior_mean REAL,
  prior_var REAL,
  post_mean REAL,
  post_var REAL,
  p_categories_json TEXT,
  information REAL,
  points_json TEXT,
  detail_json TEXT NOT NULL,
  PRIMARY KEY (attempt_id, view)
);

-- §8.3 (DERIVED; the forecast-score replayer): each valid item forecast
-- receipt joined to its bound attempt through plan_presentations, with §5.3's
-- event read exactly as the update reads it and the scores and splits.
CREATE TABLE item_forecast_scores (
  receipt_id TEXT PRIMARY KEY,
  forecaster TEXT NOT NULL,
  practice_item_id TEXT,
  plan_presentation_id TEXT,
  attempt_id TEXT,
  p REAL,
  outcome REAL,
  status TEXT NOT NULL CHECK (status IN ('scored', 'pending', 'pre_exposed', 'invalid', 'excluded')),
  log_loss REAL,
  brier REAL,
  first_attempt_lo INTEGER,
  first_surface_cell INTEGER,
  capability TEXT,
  detail_json TEXT NOT NULL
);

-- AD23 redesign round 2 (class 3b): AD1's two receipts AD reads back carry the
-- protection epoch they were computed under. A frozen serve's inputs are read
-- only at their epoch (otherwise the replay reconstructs the attempt from
-- current content); a reading receipt of another epoch counts for nothing and
-- its source is swept again under the current projection, so the receipt's
-- identity gains the epoch (a rebuild: same columns, indexes and triggers).
-- Rows recorded before this have no epoch (null, or '' for a reading receipt,
-- whose identity keeps its uniqueness) and are never in force.
ALTER TABLE item_serve_inputs ADD COLUMN protection_epoch TEXT;

CREATE TABLE ad_reading_opportunities_v214 (
  id TEXT PRIMARY KEY,
  opportunity_key TEXT NOT NULL,
  kind TEXT NOT NULL
    CHECK (kind IN ('reading', 'reader_tutor_exchange', 'worked_example', 'in_passage_question')),
  subkind TEXT NOT NULL,
  source_table TEXT NOT NULL,
  source_id TEXT NOT NULL,
  source_written_at TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  facet_doses_json TEXT NOT NULL,
  dose_offer_id TEXT,
  mapping_version TEXT NOT NULL,
  authority_class TEXT NOT NULL DEFAULT 'salience_only' CHECK (authority_class = 'salience_only'),
  sweep TEXT NOT NULL CHECK (sweep IN ('serve', 'backfill')),
  sweep_ref TEXT,
  swept_at TEXT NOT NULL,
  -- '' for a receipt recorded before receipts carried an epoch (never in force).
  protection_epoch TEXT NOT NULL DEFAULT '',
  UNIQUE (opportunity_key, protection_epoch),
  UNIQUE (kind, subkind, source_table, source_id, learning_object_id, protection_epoch)
);
INSERT INTO ad_reading_opportunities_v214 (
  id, opportunity_key, kind, subkind, source_table, source_id, source_written_at, learning_object_id,
  facet_doses_json, dose_offer_id, mapping_version, authority_class, sweep, sweep_ref, swept_at, protection_epoch)
SELECT id, opportunity_key, kind, subkind, source_table, source_id, source_written_at, learning_object_id,
  facet_doses_json, dose_offer_id, mapping_version, authority_class, sweep, sweep_ref, swept_at, ''
FROM ad_reading_opportunities;
DROP TABLE ad_reading_opportunities;
ALTER TABLE ad_reading_opportunities_v214 RENAME TO ad_reading_opportunities;
CREATE INDEX idx_ad_reading_opportunities_lo ON ad_reading_opportunities(learning_object_id, source_written_at);
CREATE INDEX idx_ad_reading_opportunities_written ON ad_reading_opportunities(source_written_at, id);

CREATE TRIGGER ad_reading_opportunities_no_update
BEFORE UPDATE ON ad_reading_opportunities
BEGIN
  SELECT RAISE(ABORT, 'ad_reading_opportunities is append-only');
END;

CREATE TRIGGER ad_reading_opportunities_no_delete
BEFORE DELETE ON ad_reading_opportunities
BEGIN
  SELECT RAISE(ABORT, 'ad_reading_opportunities is append-only');
END;
