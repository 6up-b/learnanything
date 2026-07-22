-- P4 steps 5-6 (spec_p4_controller_and_scale §8.2, §7; design §B steps 5-6, §F;
-- U-025/U-026). Two descoped, firewall-gated substrates land here:
--
--   Step 5 (U-026): the heuristic LLM-judged soft-kinship FEATURE. No fitted kernel,
--   no learned weights (deferred at n=1). The feature is computed + cached + logged
--   but CONSULTED BY NOTHING until a planted-learner sim ADMISSION GATE certifies it
--   (status can only reach 'simulation_validated'). P1's conservative discount stays
--   the live authority; an un-admitted feature never moves a scheduling/certification
--   decision (enforced in kinship_feature.py + test, firewall-style).
--
--   Step 6 (U-025): shadow predictive components (retrievability / expected-success /
--   expected-duration) scored PREQUENTIALLY (log-loss/Brier) at predeclared horizons,
--   each individually promotable; the composed-selector telemetry is a TIME-BOXED
--   secondary product; the monolithic action chooser has NO reachable promotion path
--   at n=1 (structural guard in shadow_components.py). Component predictions reuse
--   controller_shadow_predictions (096, authority CHECK IN ('none')) and the delayed
--   outcomes reuse controller_outcome_windows (098, next-spaced-cold-review horizon).
--
-- No FK to vault-owned ids (surface/commitment ids are plain TEXT per the 069/096
-- convention). All heads are rebuildable; every event log is append-only.

-- ---------------------------------------------------------------------------
-- Step 5: the immutable soft-kinship kernel MODEL artifact (§8.2). One row per
-- model version; content-hashed; status advances ONLY through append-only events.
-- The heuristic feature is a degenerate "model" (no fitted weights) so this artifact
-- exists to carry provenance, manifests, calibrated outputs, and admission status.
-- ---------------------------------------------------------------------------
CREATE TABLE familiarity_kernel_models (
  id TEXT PRIMARY KEY,
  model_kind TEXT NOT NULL DEFAULT 'heuristic_llm_judged'
    CHECK (model_kind IN ('heuristic_llm_judged')),
  version TEXT NOT NULL,
  parent_id TEXT REFERENCES familiarity_kernel_models(id),
  content_hash TEXT NOT NULL,
  -- Admission status. 'shadow' = computed + logged, consulted by NOTHING (firewall).
  -- 'simulation_validated' = the planted-learner sim admission gate certified it (the
  -- ONLY status a sim can grant, §8.4). 'retired' via a retirement event.
  status TEXT NOT NULL DEFAULT 'shadow'
    CHECK (status IN ('shadow', 'simulation_validated', 'retired')),
  -- Exact P1 feature schema + preprocessing/embedding versions consumed (§8.2).
  feature_schema_version TEXT NOT NULL,
  preprocessing_version TEXT,
  -- Training/evaluation manifests split by time/card/family/hard-group (§8.2). For the
  -- heuristic feature these are the sim EVALUATION manifests, not a training corpus.
  manifests_json TEXT,
  -- Learner-local scope + privacy/consent metadata (§8.2).
  scope_json TEXT,
  consent_json TEXT,
  -- Evaluation metrics + sample/effective-sample counts + calibration status (§8.2).
  metrics_json TEXT,
  calibration_status TEXT,
  -- The admission-gate promotion-evidence artifact (parameter_sensitivity_certificates
  -- row id) that granted 'simulation_validated' (U-022 through the registry machinery).
  admission_evidence_id TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(version)
);
CREATE INDEX idx_familiarity_kernel_models_status ON familiarity_kernel_models(status);

-- Cached per-surface(-pair) versioned kinship FEATURE scores + calibrated intervals
-- (§8.2 "scores cached as versioned features"). Conditioned ONLY on pre-administration
-- information (exposure history, time, kinship features, angle/task features, surface
-- provenance); the learner's current correctness is NEVER a column here (§8.2, 16.4).
CREATE TABLE familiarity_kernel_features (
  id TEXT PRIMARY KEY,
  model_id TEXT NOT NULL REFERENCES familiarity_kernel_models(id) ON DELETE CASCADE,
  subject_surface_id TEXT NOT NULL,
  kin_surface_id TEXT,
  -- Outputs (§8.2): P(replay materially aided response), independent-evidence discount
  -- interval [lo, hi], rotation-benefit estimate. Stored as one JSON body.
  outputs_json TEXT NOT NULL,
  -- The pre-administration inputs the score was conditioned on (audit / leakage proof).
  conditioned_on_json TEXT NOT NULL,
  in_scope INTEGER NOT NULL DEFAULT 1 CHECK (in_scope IN (0, 1)),
  created_at TEXT NOT NULL,
  UNIQUE(model_id, subject_surface_id, kin_surface_id)
);
CREATE INDEX idx_familiarity_kernel_features_subject
  ON familiarity_kernel_features(subject_surface_id);

-- Append-only kernel lifecycle events: shadow / activation (admission) / retirement.
CREATE TABLE familiarity_kernel_events (
  id TEXT PRIMARY KEY,
  model_id TEXT NOT NULL REFERENCES familiarity_kernel_models(id) ON DELETE CASCADE,
  event_ordinal INTEGER NOT NULL,
  event_kind TEXT NOT NULL
    CHECK (event_kind IN ('shadow', 'admission', 'retirement')),
  detail_json TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(model_id, event_ordinal)
);
CREATE INDEX idx_familiarity_kernel_events_model
  ON familiarity_kernel_events(model_id, event_ordinal);

-- ---------------------------------------------------------------------------
-- Step 6: prequential held-out reports (§7.3 "primary product") for shadow
-- predictive components, plus the time-box registration for the SECONDARY
-- composed-selector telemetry. Reports are rebuildable snapshots keyed by content.
-- ---------------------------------------------------------------------------
CREATE TABLE controller_prequential_reports (
  id TEXT PRIMARY KEY,
  -- 'predictive_component:<name>' (primary) or 'composed_selector' (secondary).
  target_kind TEXT NOT NULL,
  component TEXT,
  -- The predeclared horizon these delayed outcomes resolved at (next spaced cold
  -- review, §9.3); a report never scores on immediate answer success.
  horizon_kind TEXT NOT NULL DEFAULT 'next_spaced_cold_review'
    CHECK (horizon_kind IN ('next_spaced_cold_review')),
  -- Prequential scores (log-loss / Brier) + n + effective sample, and the by-split
  -- breakdown (time / target family) that stops near-clone leakage (§7.2). A
  -- surface-group split is deferred until the outcome window carries a surface-group key.
  metrics_json TEXT NOT NULL,
  splits_json TEXT,
  sample_count INTEGER NOT NULL DEFAULT 0,
  report_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_controller_prequential_reports_target
  ON controller_prequential_reports(target_kind, component);

-- The composed-selector telemetry is TIME-BOXED: a registered horizon after which
-- unpromoted telemetry retires (design §B step 6). One row per registered horizon;
-- a retirement event is appended when now crosses opened_at + horizon_days.
CREATE TABLE composed_selector_telemetry_horizons (
  id TEXT PRIMARY KEY,
  horizon_days INTEGER NOT NULL,
  opened_at TEXT NOT NULL,
  retires_at TEXT NOT NULL,
  retired_at TEXT,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'retired')),
  detail_json TEXT
);

-- Append-only predictive-component lifecycle events (shadow / promotion). Promotion
-- feeds the staged policy's INPUTS only and emits a U-022 promotion-evidence artifact
-- (parameter_sensitivity_certificates id); the monolithic action chooser is NEVER a
-- promotable target here (structural guard refuses it, U-025 §7.4).
CREATE TABLE shadow_component_events (
  id TEXT PRIMARY KEY,
  component TEXT NOT NULL,
  event_ordinal INTEGER NOT NULL,
  event_kind TEXT NOT NULL CHECK (event_kind IN ('shadow', 'promotion')),
  promotion_evidence_id TEXT,
  detail_json TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(component, event_ordinal)
);
CREATE INDEX idx_shadow_component_events_component
  ON shadow_component_events(component, event_ordinal);
