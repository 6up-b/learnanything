-- Router objective RO2 (docs/specs/spec_router_objective_v1.md §6): the
-- frontier LLM full-history forecaster, llm_history_v1.
--
-- Additive: one new append-only RECEIPT table; no existing table changes.
-- Its forecasts are forecast_receipts rows (kinds item_unassisted_success and,
-- new in code only, lo_cold_success; forecast_receipts has no CHECK on kind or
-- binding), its frozen request inputs item_forecast_payloads rows and its
-- accepted verdicts judgment_ledger rows, as AD1's outside forecasters'.
--
-- ad_history_forecast_draws: one row per eligible plan presentation, written
-- in the serve transaction beside the frozen inputs: the seeded draw that
-- picks the one lower rung (H0, H1 or H2) asked beside H3, with its logged
-- propensity, and what each frozen card holds (owner key, state hash, size,
-- and what the token budget left out: counts and ids, never content). It is
-- the denominator of the paired comparison: a drawn presentation with no
-- receipt for a rung is a missing pair, reported and never imputed. Nothing
-- serving, scoring, scheduling, evidence or certification reads it (A2, A12);
-- a rebuild never writes or clears it.
CREATE TABLE ad_history_forecast_draws (
  id TEXT PRIMARY KEY,
  -- Idempotency: llm_history_v1:plan_presentation:<presentation id>.
  draw_key TEXT NOT NULL UNIQUE,
  plan_presentation_id TEXT NOT NULL,
  practice_item_id TEXT NOT NULL,
  learning_object_id TEXT,
  -- The draw's code version (adaptive_difficulty.history_forecast.DRAW_VERSION).
  draw_version TEXT NOT NULL,
  -- The seed (a digest of the presentation id and the draw version) and the
  -- uniform u in [0, 1) it gives; the drawn rung is the u-th third.
  seed TEXT NOT NULL,
  u REAL NOT NULL CHECK (u >= 0 AND u < 1),
  -- H3 on every eligible presentation.
  anchor_rung TEXT NOT NULL CHECK (anchor_rung = 'H3'),
  drawn_rung TEXT NOT NULL CHECK (drawn_rung IN ('H0', 'H1', 'H2')),
  -- The drawn rung's probability, and every rung's ({"H0": .., "H1": .., "H2": ..}).
  propensity REAL NOT NULL CHECK (propensity > 0 AND propensity <= 1),
  propensities_json TEXT NOT NULL,
  -- ad-forecast-state-v3.
  card_version TEXT NOT NULL,
  -- Per frozen rung: {owner_key, state_hash, bytes, left_out}: ids and counts only.
  frozen_json TEXT NOT NULL,
  -- The protection epoch the cards were read under (sent only at it).
  protection_epoch TEXT,
  served_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_ad_history_forecast_draws_presentation ON ad_history_forecast_draws(plan_presentation_id);

CREATE TRIGGER ad_history_forecast_draws_no_update
BEFORE UPDATE ON ad_history_forecast_draws
BEGIN
  SELECT RAISE(ABORT, 'ad_history_forecast_draws is append-only');
END;

CREATE TRIGGER ad_history_forecast_draws_no_delete
BEFORE DELETE ON ad_history_forecast_draws
BEGIN
  SELECT RAISE(ABORT, 'ad_history_forecast_draws is append-only');
END;
