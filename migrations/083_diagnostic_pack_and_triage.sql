-- P2 DIAGNOSTIC track (spec_p2_narrow_golden_path §5, §6, U-027, U-028): the
-- pre-authored diagnostic pack + the two-tier failure-reason triage substrate.
--
-- Migration numbering: highest applied on disk = 082 (golden_path_runs, the P2
-- spine). The design allocated 082/083 for these tables, but the spine consumed
-- 082 -- the diagnostic track therefore starts at 083. Never edit an applied
-- migration. Both diagnostic substrates (pack + triage) land in this one file so
-- the track owns a single migration number.
--
-- These are legitimately NEW P2 bookkeeping substrate: a reviewed diagnostic
-- instrument pack pinned to a run, and an append-only triage decision ledger over
-- a versioned reviewable route table. NOT a second posterior / FSRS writer /
-- certification path -- the baseline episode COMPOSES the landed P0/P1 probe
-- machinery (probe_episodes) and the triage distribution COMPOSES the landed P0
-- grading pass + error_taxonomy. P2 orchestrates; it mints no new measurement.

-- ---------------------------------------------------------------------------
-- §5 Pre-authored diagnostic pack (U-028 provenance).
-- ---------------------------------------------------------------------------

-- Stable pack: a bounded set of reviewed diagnostic-purpose cards covering the
-- nearest action-relevant alternatives for ONE reviewed blueprint version (§5.1).
-- A material edit mints a SUCCESSOR pack version (new slug/row); a reviewed row is
-- never mutated in place.
CREATE TABLE diagnostic_packs (
  id TEXT PRIMARY KEY,
  pack_slug TEXT NOT NULL,
  blueprint_version_id TEXT NOT NULL
    REFERENCES task_blueprint_versions(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft', 'reviewed', 'active', 'retired')),
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(pack_slug)
);
CREATE INDEX idx_diag_packs_blueprint ON diagnostic_packs(blueprint_version_id);

-- Pack cards: reviewed diagnostic-purpose P1 cards, each declaring the target
-- distribution cell(s) it covers (§3.3). `admission_status` is the U-028 owner
-- gate -- nothing serves as an instrument until 'admitted'.
CREATE TABLE diagnostic_pack_cards (
  id TEXT PRIMARY KEY,
  pack_id TEXT NOT NULL REFERENCES diagnostic_packs(id) ON DELETE CASCADE,
  card_slug TEXT NOT NULL,
  purpose TEXT NOT NULL DEFAULT 'diagnostic'
    CHECK (purpose = 'diagnostic'),
  coverage_json TEXT NOT NULL,
  instrument_ref TEXT,
  admission_status TEXT NOT NULL DEFAULT 'candidate'
    CHECK (admission_status IN ('candidate', 'admitted', 'rejected')),
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(pack_id, card_slug)
);
CREATE INDEX idx_diag_pack_cards_pack ON diagnostic_pack_cards(pack_id);

-- Append-only admission/review ledger (U-028 artifacts-not-API-calls): every
-- register/review/admit/reject/activate decision is a durable, reviewable record.
CREATE TABLE diagnostic_pack_events (
  id TEXT PRIMARY KEY,
  pack_id TEXT NOT NULL REFERENCES diagnostic_packs(id) ON DELETE CASCADE,
  card_slug TEXT,
  kind TEXT NOT NULL CHECK (kind IN (
    'registered', 'reviewed', 'admitted', 'rejected', 'activated', 'retired')),
  detail_json TEXT,
  author TEXT NOT NULL DEFAULT 'owner',
  created_at TEXT NOT NULL
);
CREATE INDEX idx_diag_pack_events_pack ON diagnostic_pack_events(pack_id, created_at);

-- Pack pin: at diagnostic entry the run pins exactly one reviewed pack against the
-- goal-contract HEAD version then current (§5.2) plus the opened probe episode. One
-- pin per run (UNIQUE) -- the pack composition never re-pins mid-run.
CREATE TABLE diagnostic_pack_pins (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES golden_path_runs(id) ON DELETE CASCADE,
  pack_id TEXT NOT NULL REFERENCES diagnostic_packs(id),
  goal_contract_version_id TEXT NOT NULL,
  probe_episode_id TEXT,
  visible_cap INTEGER NOT NULL,
  pinned_at TEXT NOT NULL,
  UNIQUE(run_id)
);
CREATE INDEX idx_diag_pins_pack ON diagnostic_pack_pins(pack_id);

-- ---------------------------------------------------------------------------
-- §6 Two-tier failure-reason triage (U-027).
-- ---------------------------------------------------------------------------

-- Versioned, reviewable route table (§6.2), REGISTERED AS DATA not code so
-- owner edits/overrides are auditable. Maps each of the ten failure reasons to its
-- first intervention, required cold follow-up, and the run-state-machine ladder
-- entry stage the route names. `reopens_diagnostic` marks the only two reasons that
-- may open/continue a diagnostic episode (§6.1).
CREATE TABLE failure_triage_routes (
  id TEXT PRIMARY KEY,
  route_id TEXT NOT NULL,
  route_version INTEGER NOT NULL DEFAULT 1,
  reason TEXT NOT NULL CHECK (reason IN (
    'memory_lapse', 'unfamiliar_or_missing_knowledge', 'schema_or_conceptual_hole',
    'false_belief_or_confusion', 'procedure_execution', 'method_selection',
    'coordination_or_integration', 'task_interpretation', 'surface_or_grading_fault',
    'unknown_or_ambiguous')),
  first_intervention TEXT NOT NULL,
  cold_follow_up TEXT NOT NULL,
  ladder_entry_stage TEXT NOT NULL,
  reopens_diagnostic INTEGER NOT NULL DEFAULT 0,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  UNIQUE(route_id, route_version)
);
CREATE INDEX idx_triage_routes_reason ON failure_triage_routes(reason, active);

-- Append-only triage decision ledger (§6.1). Each row records one triage action:
-- the initial evaluation ('triaged'), a tier-two learner/owner selection
-- ('decided'), or an override of a prior route ('overridden'). Every row snapshots
-- the inputs, the resolved route id or provisional distribution, the goal-contract
-- HEAD version it evaluated, and any override actor -- the audit trace of §6.1.
CREATE TABLE failure_triage_events (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES golden_path_runs(id) ON DELETE CASCADE,
  attempt_id TEXT,
  kind TEXT NOT NULL CHECK (kind IN ('triaged', 'decided', 'overridden')),
  tier TEXT NOT NULL CHECK (tier IN ('one', 'two')),
  decisive INTEGER NOT NULL DEFAULT 0,
  route_id TEXT,
  selected_reason TEXT,
  distribution_json TEXT,
  alternatives_json TEXT,
  inputs_snapshot_json TEXT,
  routing_prior_json TEXT,
  override_actor TEXT,
  override_reason TEXT,
  anchor_sample_id TEXT,
  auto_committed INTEGER NOT NULL DEFAULT 0,
  goal_contract_head_version_id TEXT,
  seq INTEGER NOT NULL,
  -- Idempotency fence (§12.6): a retried triage()/decide()/override() with the same
  -- key returns the existing event instead of appending a duplicate ledger row.
  idempotency_key TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(run_id, seq),
  UNIQUE(run_id, idempotency_key)
);
CREATE INDEX idx_triage_events_run ON failure_triage_events(run_id, seq);

-- Seed the §6.2 route table (route_version 1). Registered as data: the triage
-- channel is heuristic (U-027) so misroutes are discoverable, not ambient.
INSERT INTO failure_triage_routes
  (id, route_id, route_version, reason, first_intervention, cold_follow_up, ladder_entry_stage, reopens_diagnostic, active, created_at)
VALUES
  ('ftr_memory_lapse', 'memory_lapse', 1, 'memory_lapse',
   'reveal_reconstruct_then_next_day_review', 'fresh_or_independent_retrieval', 'instructing', 0, 1, '2026-07-19T00:00:00Z'),
  ('ftr_unfamiliar', 'unfamiliar_or_missing_knowledge', 1, 'unfamiliar_or_missing_knowledge',
   'source_grounded_explanation_or_example_study', 'completion_then_retrieval_application', 'instructing', 0, 1, '2026-07-19T00:00:00Z'),
  ('ftr_schema_hole', 'schema_or_conceptual_hole', 1, 'schema_or_conceptual_hole',
   'explanation_plus_example_comparison', 'altered_context_explanation_application', 'instructing', 0, 1, '2026-07-19T00:00:00Z'),
  ('ftr_false_belief', 'false_belief_or_confusion', 1, 'false_belief_or_confusion',
   'contrast_counterexample_after_bounded_diagnosis', 'discriminating_fresh_surface', 'instructing', 1, 1, '2026-07-19T00:00:00Z'),
  ('ftr_procedure', 'procedure_execution', 1, 'procedure_execution',
   'worked_step_then_faded_example_completion', 'independent_execution', 'completing', 0, 1, '2026-07-19T00:00:00Z'),
  ('ftr_method_selection', 'method_selection', 1, 'method_selection',
   'setup_only_plus_move_spotting_across_contexts', 'independent_selection_before_execution', 'instructing', 0, 1, '2026-07-19T00:00:00Z'),
  ('ftr_integration', 'coordination_or_integration', 1, 'coordination_or_integration',
   'component_localization_then_faded_whole_task', 'fresh_whole_task_integration', 'integrating', 0, 1, '2026-07-19T00:00:00Z'),
  ('ftr_task_interp', 'task_interpretation', 1, 'task_interpretation',
   'compare_prompt_representations_restate_contract', 'fresh_representation', 'instructing', 0, 1, '2026-07-19T00:00:00Z'),
  ('ftr_surface_fault', 'surface_or_grading_fault', 1, 'surface_or_grading_fault',
   'quarantine_adjudicate_no_learner_repair', 'replacement_administration_if_needed', 'needs_review', 0, 1, '2026-07-19T00:00:00Z'),
  ('ftr_unknown', 'unknown_or_ambiguous', 1, 'unknown_or_ambiguous',
   'clarification_or_admitted_diagnostic_card', 'depends_on_resolved_action', 'needs_review', 1, 1, '2026-07-19T00:00:00Z');
