-- Adaptive difficulty AD1: measure and log (spec_adaptive_difficulty_v1 §14
-- AD1, §7.5, §8.1, §5.11, §11.2; docs/reviews/adaptive-difficulty-ad1.md).
-- No algorithm successor: nothing here is read by serving, scoring,
-- scheduling, evidence, FSRS or certification (A2, A12).
--
-- Item forecasts are NOT a table of their own: they are kind
-- `item_unassisted_success` in migration 206's `forecast_receipts` family
-- (scope `presentation` or `item`), as the saved-diagnosis-forecasts stage
-- built it for (docs/reviews/diagnosis-forecast-receipts.md, "AD1 fit").
-- This migration adds what that family cannot hold.

-- The optional one-tap rating (§12), tapped before feedback and sent with the
-- submit; null when not tapped, with `adaptive_difficulty.rating_tap` off, and
-- on every earlier row. Never read by grading, scheduling or evidence.
ALTER TABLE practice_attempts ADD COLUMN difficulty_rating TEXT
  CHECK (difficulty_rating IS NULL OR difficulty_rating IN ('easy', 'about_right', 'hard'));

-- Whether an answer had been started when the first hint of the attempt was
-- revealed (§5.3, §11.2): the practice screen's marker, sent on submit. Null
-- reads as `unknown` (every earlier row, a client that sends none, and while
-- `adaptive_difficulty.forecast_receipts` is off).
ALTER TABLE practice_attempts ADD COLUMN first_hint_progress TEXT
  CHECK (first_hint_progress IS NULL OR first_hint_progress IN ('no_draft', 'draft_started'));

-- §5.11 (Codex review F4): when a pending tutor question was answered. A
-- reader tutor exchange becomes a learning opportunity when its answer
-- completes, not when the question was asked: the sweep stamps it (and orders
-- replay) by this time, so a question pending at a serve is never placed
-- before that serve. Set once, by the pending-to-answered update; a row
-- written already answered keeps it null (its created_at is when it was
-- answered), and so does every earlier row.
ALTER TABLE question_events ADD COLUMN answered_at TEXT;

-- §7.5: the features and signals an AD decision or update reads, frozen when
-- the item is served. One row per presentation of a never-attempted item,
-- written in the serve transaction beside the in-process forecast receipts. A
-- later audit, re-audit, recalibration or item edit never rewrites a row.
CREATE TABLE item_serve_inputs (
  id TEXT PRIMARY KEY,
  -- Idempotency: <presentation kind>:<presentation id>.
  receipt_key TEXT NOT NULL UNIQUE,
  presentation_kind TEXT NOT NULL
    CHECK (presentation_kind IN ('plan_presentation', 'probe_presentation', 'scheduler_candidate')),
  plan_presentation_id TEXT,
  probe_presentation_id TEXT,
  scheduler_candidate_id TEXT,
  practice_item_id TEXT NOT NULL,
  learning_object_id TEXT,
  -- The served revision (also written to practice_item_snapshots, INSERT OR
  -- IGNORE, migration 164).
  content_hash TEXT NOT NULL,
  served_at TEXT NOT NULL,
  -- x_i as stamped on the served revision (p1_launch@1), null when it has none.
  stamped_features_json TEXT,
  task_feature_schema TEXT,
  -- Per audited dimension: {judgment_id, value} of the audit that had answered
  -- before the serve, or null.
  audit_json TEXT NOT NULL,
  -- The tuple AD reads: the audit where it answered, else the stamped value.
  resolved_features_json TEXT,
  -- z_i: per signal {value, available, receipt_id, received_at, why}.
  signals_json TEXT NOT NULL,
  z_v1_recalibration TEXT,
  -- §5.3: the item's reveal sum before the serve already reached the
  -- auto-prime threshold (excluded from the update and from scoring alike).
  pre_exposed INTEGER NOT NULL CHECK (pre_exposed IN (0, 1)),
  resolution_version TEXT NOT NULL,
  -- From the AD2/AD3 successor on: the loadings in force and the coupling
  -- version (§5.10). Null in AD1.
  loadings_json TEXT,
  coupling_version TEXT,
  created_at TEXT NOT NULL,
  CHECK (
    (presentation_kind = 'plan_presentation' AND plan_presentation_id IS NOT NULL)
    OR (presentation_kind = 'probe_presentation' AND probe_presentation_id IS NOT NULL)
    OR (presentation_kind = 'scheduler_candidate' AND scheduler_candidate_id IS NOT NULL)
  )
);
CREATE INDEX idx_item_serve_inputs_item ON item_serve_inputs(practice_item_id, served_at);
CREATE INDEX idx_item_serve_inputs_plan ON item_serve_inputs(plan_presentation_id);

CREATE TRIGGER item_serve_inputs_no_update
BEFORE UPDATE ON item_serve_inputs
BEGIN
  SELECT RAISE(ABORT, 'item_serve_inputs is append-only');
END;

CREATE TRIGGER item_serve_inputs_no_delete
BEFORE DELETE ON item_serve_inputs
BEGIN
  SELECT RAISE(ABORT, 'item_serve_inputs is append-only');
END;

-- §5.11 (D20, D22): reading and other learning opportunities, frozen in a
-- receipt. One row per (opportunity, LO), of one of four kinds, from the
-- listed sources only, with the facets and doses the mapping resolved at the
-- sweep; plus one verdict row per judged in-passage question (subkind
-- `self_check:matched` / `self_check:missed`, from the question's first
-- judgment_ledger verdict). No magnitude field exists: no dwell, scroll,
-- highlight, skip, visibility, active time or answer value. Authority class
-- `salience_only`: nothing reads these rows until the AD2+AD3 stage adds the
-- reading-signal firewall's carve-out, and they never pass the evidence
-- chokepoint. A source row deleted later (its extraction removed) leaves its
-- receipts.
CREATE TABLE ad_reading_opportunities (
  id TEXT PRIMARY KEY,
  -- The opportunity's identity inside its cap (a section once per section and
  -- LO; passage views one per LO per day; tutor exchanges three per LO per day;
  -- a worked example once; a question once; a verdict once per question).
  opportunity_key TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL
    CHECK (kind IN ('reading', 'reader_tutor_exchange', 'worked_example', 'in_passage_question')),
  subkind TEXT NOT NULL,
  source_table TEXT NOT NULL,
  source_id TEXT NOT NULL,
  -- The source row's write time: replay orders opportunities by it.
  source_written_at TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  -- {facet id: dose in [0, 1]}, as resolved at the sweep.
  facet_doses_json TEXT NOT NULL,
  -- ad_dose_offers.id when a randomized offer produced it (AD2+AD3; null here).
  dose_offer_id TEXT,
  mapping_version TEXT NOT NULL,
  authority_class TEXT NOT NULL DEFAULT 'salience_only' CHECK (authority_class = 'salience_only'),
  -- Which sweep recorded it: a serve's (in its transaction, before its
  -- forecasts) or the one-time history backfill.
  sweep TEXT NOT NULL CHECK (sweep IN ('serve', 'backfill')),
  sweep_ref TEXT,
  swept_at TEXT NOT NULL,
  UNIQUE (kind, subkind, source_table, source_id, learning_object_id)
);
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

-- §8.1: the raw request and response of a paid outside forecaster (and of the
-- feature audit's LLM fallback); the receipt keeps the hash. WORKFLOW: pruned
-- after router.payload_retention_days, like router_decision_payloads.
CREATE TABLE item_forecast_payloads (
  id TEXT PRIMARY KEY,
  -- The forecast receipt (forecast_receipts.receipt_key) or audit the payload
  -- belongs to.
  owner_key TEXT NOT NULL,
  forecaster TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('request', 'response')),
  content_hash TEXT NOT NULL,
  content_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (owner_key, kind)
);
CREATE INDEX idx_item_forecast_payloads_created ON item_forecast_payloads(created_at);
