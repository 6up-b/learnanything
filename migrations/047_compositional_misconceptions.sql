-- KM4 (knowledge-model §10.2/§10.3): compositional misconception records and the
-- promotion-discipline candidate holding pen.
--
-- Purely additive. Legacy misconception rows (migration 025) keep their exact
-- meaning; the new columns are NULL for them and populated only when a mvp-0.7
-- vault mints a compositional record. mvp-0.6 replay never reads or writes these
-- columns/tables, so it reproduces byte-identical derived state.
--
-- 045-046 are reserved for the parallel M6-core track; KM4 lands on 047.

-- §10.2 compositional specific record. `mechanism` is a §10.1 taxonomy value;
-- `operation` is the app-validated (extensible) operation vocabulary;
-- `target_facet`/`confused_with_facet` are canonical facet ids (the two bound
-- facets that parameterize contrast-probe generation). The `*_json` columns hold
-- the trigger_conditions / expected_signatures / first_divergence /
-- non_applicable_controls lists. `promotion_reason` records why the belief was
-- promoted from a candidate to a durable misconception (§10.3 provenance).
ALTER TABLE misconceptions ADD COLUMN mechanism TEXT;
ALTER TABLE misconceptions ADD COLUMN operation TEXT;
ALTER TABLE misconceptions ADD COLUMN target_facet TEXT;
ALTER TABLE misconceptions ADD COLUMN confused_with_facet TEXT;
ALTER TABLE misconceptions ADD COLUMN trigger_conditions_json TEXT;
ALTER TABLE misconceptions ADD COLUMN expected_signatures_json TEXT;
ALTER TABLE misconceptions ADD COLUMN first_divergence_json TEXT;
ALTER TABLE misconceptions ADD COLUMN non_applicable_controls_json TEXT;
ALTER TABLE misconceptions ADD COLUMN promotion_reason TEXT;

CREATE INDEX IF NOT EXISTS idx_misconceptions_target_facet
  ON misconceptions(target_facet);

-- §10.3 promotion discipline: under mvp-0.7 a one-off ambiguous failure does NOT
-- mint a durable misconception. The candidate belief stays here as a distribution
-- over surfaces/events until a promotion condition is met (repeats on an
-- independent surface / high-confidence first-error trace / contrast probe
-- reproduces the predicted signature / maps to a validated registry belief), at
-- which point a durable `misconceptions` row is inserted and linked back.
-- `status` is app-validated (candidate | promoted); no SQL CHECK so it stays
-- extensible without the table-rebuild dance.
CREATE TABLE IF NOT EXISTS misconception_candidates (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT NOT NULL,
  concept_id TEXT,
  statement TEXT NOT NULL,
  statement_normalized TEXT NOT NULL,
  signature TEXT,
  mechanism TEXT,
  operation TEXT,
  target_facet TEXT,
  confused_with_facet TEXT,
  facet_ids_json TEXT,
  source_error_event_ids_json TEXT,
  surface_families_json TEXT,
  item_ids_json TEXT,
  occurrence_count INTEGER NOT NULL DEFAULT 0,
  severity REAL NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'candidate',
  promoted_misconception_id TEXT,
  promotion_reason TEXT,
  created_at TEXT,
  updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_misconception_candidates_lo_status
  ON misconception_candidates(learning_object_id, status);
CREATE INDEX IF NOT EXISTS idx_misconception_candidates_norm
  ON misconception_candidates(learning_object_id, statement_normalized);
