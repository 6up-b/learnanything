-- P0.2 (spec_p0_measurement_correctness §3.1-§3.3, §4.1, §4.4, §4.7): the grader
-- channel. Coarse outcome schemas, the IMMUTABLE grader-calibration model registry
-- (joint Dirichlet P(E=(G,conf_bucket)|Z)), and the append-only raw-grade /
-- interpretation / adjudication / calibration-stream ledger. Activation,
-- quarantine, supersession, and model retirement are recorded as measurement_events
-- (migration 065), never by mutating these rows. Purely additive: no existing table
-- is altered. All ids ULID TEXT; all timestamps TEXT from clock.py; all _json TEXT
-- canonicalized with sorted keys. Model/schema rows never receive an UPDATE.

------------------------------------------------------------------------------
-- Outcome schemas (§3.1). Immutable (id, version). Names 3 or 4 mutually
-- exclusive true classes, the same observed-class vocabulary, and the
-- class->score-fraction map read by EffectiveObservation (P0.3).
------------------------------------------------------------------------------
CREATE TABLE outcome_schemas (
  id TEXT PRIMARY KEY,
  slug TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('response', 'criterion')),
  created_at TEXT NOT NULL,
  UNIQUE(slug)
);

CREATE TABLE outcome_schema_versions (
  id TEXT PRIMARY KEY,
  schema_id TEXT NOT NULL REFERENCES outcome_schemas(id) ON DELETE CASCADE,
  version INTEGER NOT NULL CHECK (version >= 1),
  observed_classes_json TEXT NOT NULL,   -- ordered G alphabet
  true_classes_json TEXT NOT NULL,       -- Z alphabet (3 or 4 classes)
  has_signature_error INTEGER NOT NULL DEFAULT 0 CHECK (has_signature_error IN (0,1)),
  has_unanswered INTEGER NOT NULL DEFAULT 0 CHECK (has_unanswered IN (0,1)),
  score_fraction_json TEXT NOT NULL,     -- {class: fraction in [0,1]}
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(schema_id, version),
  UNIQUE(schema_id, content_hash)
);
CREATE INDEX idx_outcome_schema_versions_schema ON outcome_schema_versions(schema_id);

------------------------------------------------------------------------------
-- Grader calibration models (§3.2). IMMUTABLE. One row per model version. The
-- identity tuple + scope + backoff chain fix the model's place in the
-- partial-pooling lattice; the Dirichlet alpha rows (below) hold the joint mass.
------------------------------------------------------------------------------
CREATE TABLE grader_calibration_models (
  id TEXT PRIMARY KEY,
  -- grader identity tuple (§3.2): provider + model/revision + grading prompt
  -- version + output schema version, decomposed AND as a canonical hash.
  grader_provider TEXT,
  grader_model_revision TEXT,
  grading_prompt_version TEXT,
  grader_output_schema_version TEXT,
  grader_identity_hash TEXT,             -- NULL at global scope
  semver TEXT NOT NULL,
  parent_model_id TEXT REFERENCES grader_calibration_models(id),
  content_hash TEXT NOT NULL,
  -- scope + ordered backoff chain (§3.2 fixed parent order):
  scope_level TEXT NOT NULL CHECK (scope_level IN
    ('global', 'grader_identity', 'outcome_schema', 'domain', 'length_bucket')),
  outcome_schema_id TEXT REFERENCES outcome_schemas(id),
  outcome_schema_version INTEGER,
  domain TEXT,
  length_bucket TEXT CHECK (length_bucket IS NULL OR length_bucket IN ('0','1-50','51-200','201+')),
  backoff_chain_json TEXT NOT NULL,      -- ordered ancestor model ids, most-general first
  status TEXT NOT NULL CHECK (status IN
    ('heuristic', 'simulation_validated', 'live_calibrated')),
  -- disjoint source counts (§3.2):
  count_heuristic_prior INTEGER NOT NULL DEFAULT 0,
  count_planted_sim INTEGER NOT NULL DEFAULT 0,
  count_exploratory_em INTEGER NOT NULL DEFAULT 0,
  count_adjudicated_anchor INTEGER NOT NULL DEFAULT 0,
  count_held_out_evaluation INTEGER NOT NULL DEFAULT 0,
  -- prequential metrics (§3.2), NULL until an evaluation manifest exists:
  prequential_log_loss REAL,
  multiclass_brier REAL,
  reliability_bins_json TEXT,
  sample_count INTEGER,
  eval_time_range_json TEXT,
  prior_concentration REAL,
  provenance_json TEXT,
  evidence_manifest_json TEXT,           -- required for live_calibrated (§3.2)
  created_at TEXT NOT NULL,
  UNIQUE(scope_level, grader_identity_hash, outcome_schema_id, outcome_schema_version,
         domain, length_bucket, semver)
);
CREATE INDEX idx_gcm_scope ON grader_calibration_models(scope_level);
CREATE INDEX idx_gcm_identity ON grader_calibration_models(grader_identity_hash);
CREATE INDEX idx_gcm_schema ON grader_calibration_models(outcome_schema_id, outcome_schema_version);
CREATE INDEX idx_gcm_lookup
  ON grader_calibration_models(scope_level, grader_identity_hash, domain, length_bucket);

------------------------------------------------------------------------------
-- Dirichlet alpha rows (§3.2): one per (model, true class Z), holding the alpha
-- vector over the JOINT emission E=(G, conf_bucket). Marginalizing conf gives
-- the reported class-confusion P(G|Z). Immutable with the model.
------------------------------------------------------------------------------
CREATE TABLE grader_calibration_alphas (
  id TEXT PRIMARY KEY,
  model_id TEXT NOT NULL REFERENCES grader_calibration_models(id) ON DELETE CASCADE,
  true_class TEXT NOT NULL,              -- Z
  alpha_json TEXT NOT NULL,              -- {"G|conf_bucket": alpha}
  created_at TEXT NOT NULL,
  UNIQUE(model_id, true_class)
);
CREATE INDEX idx_gca_model ON grader_calibration_alphas(model_id);

------------------------------------------------------------------------------
-- Raw grade events (§3.3). Append-only. One per grader pass over a response.
------------------------------------------------------------------------------
CREATE TABLE raw_grade_events (
  id TEXT PRIMARY KEY,
  administration_id TEXT NOT NULL REFERENCES activity_administrations(id),
  observation_id TEXT REFERENCES activity_observations(id),
  attempt_id TEXT,
  response_ref TEXT,
  role TEXT NOT NULL CHECK (role IN
    ('primary', 'recheck', 'independent_confirmation', 'human_grade')),
  grader_provider TEXT,
  grader_model_revision TEXT,
  grading_prompt_version TEXT,
  grader_output_schema_version TEXT,
  grader_identity_hash TEXT,
  agent_run_id TEXT,
  raw_output_json TEXT NOT NULL,
  criterion_evidence_json TEXT,
  observed_class TEXT NOT NULL,          -- G
  model_confidence REAL,                 -- raw numeric grader_confidence (NEVER multiplied)
  confidence_bucket TEXT NOT NULL CHECK (confidence_bucket IN
    ('unknown','low','medium','high')),
  criterion_observed_classes_json TEXT,
  response_classifier_version TEXT NOT NULL,
  criterion_classifier_version TEXT,
  context_features_json TEXT NOT NULL,
  exact_word_count INTEGER NOT NULL,
  declared_length_bucket TEXT NOT NULL CHECK (declared_length_bucket IN ('0','1-50','51-200','201+')),
  predecessor_event_id TEXT REFERENCES raw_grade_events(id),
  created_at TEXT NOT NULL
);
CREATE INDEX idx_rge_admin ON raw_grade_events(administration_id);
CREATE INDEX idx_rge_observation ON raw_grade_events(observation_id);
CREATE INDEX idx_rge_attempt ON raw_grade_events(attempt_id);

------------------------------------------------------------------------------
-- Grade interpretations (§3.3). Append-only. The current head per observation is
-- a projection selected by activation/supersession measurement_events.
------------------------------------------------------------------------------
CREATE TABLE grade_interpretations (
  id TEXT PRIMARY KEY,
  raw_grade_event_id TEXT NOT NULL REFERENCES raw_grade_events(id),
  observation_id TEXT REFERENCES activity_observations(id),
  administration_id TEXT NOT NULL REFERENCES activity_administrations(id),
  calibration_model_id TEXT NOT NULL REFERENCES grader_calibration_models(id),
  calibration_model_hash TEXT NOT NULL,
  projection_algorithm_version TEXT NOT NULL,
  channel_posterior_snapshot_id TEXT,
  response_posterior_json TEXT NOT NULL,   -- {Z: P(Z|E,context)}
  criterion_posteriors_json TEXT,
  reference_prior_ids_json TEXT,
  certainty_discount REAL NOT NULL,
  credible_interval_json TEXT,
  review_flag INTEGER NOT NULL DEFAULT 0 CHECK (review_flag IN (0,1)),
  influence_flag INTEGER NOT NULL DEFAULT 0 CHECK (influence_flag IN (0,1)),
  quarantine_state TEXT NOT NULL DEFAULT 'active'
    CHECK (quarantine_state IN ('active','quarantined')),
  fallback_reason TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_gi_observation ON grade_interpretations(observation_id);
CREATE INDEX idx_gi_raw ON grade_interpretations(raw_grade_event_id);
CREATE INDEX idx_gi_admin ON grade_interpretations(administration_id);

------------------------------------------------------------------------------
-- Grade adjudications (§3.3). Append-only. Appends a new interpretation and
-- triggers projection rebuilds; never overwrites prior rows.
------------------------------------------------------------------------------
CREATE TABLE grade_adjudications (
  id TEXT PRIMARY KEY,
  observation_id TEXT REFERENCES activity_observations(id),
  administration_id TEXT NOT NULL REFERENCES activity_administrations(id),
  reviewed_raw_event_ids_json TEXT NOT NULL,
  adjudicator_source TEXT NOT NULL CHECK (adjudicator_source IN
    ('human_owner','independent_expert','learner_clarification','deterministic_key')),
  resolved_class TEXT,
  resolved_distribution_json TEXT,
  rationale TEXT,
  provenance_json TEXT,
  bounded_trust_weight REAL,             -- <1 for learner_clarification (§3.3/§4.4)
  resulting_interpretation_id TEXT REFERENCES grade_interpretations(id),
  superseded_adjudication_id TEXT REFERENCES grade_adjudications(id),
  created_at TEXT NOT NULL
);
CREATE INDEX idx_gadj_observation ON grade_adjudications(observation_id);
CREATE INDEX idx_gadj_admin ON grade_adjudications(administration_id);

------------------------------------------------------------------------------
-- Calibration stream sample log (§4.7). Records the inclusion probability under
-- which each attempt entered a stream, so IPW recovers unbiased confusion
-- estimates and the bootstrap composes with the ongoing stream. Error-intake
-- taps land here tagged stream='error_intake' (MNAR; never a denominator).
------------------------------------------------------------------------------
CREATE TABLE calibration_stream_samples (
  id TEXT PRIMARY KEY,
  observation_id TEXT REFERENCES activity_observations(id),
  administration_id TEXT REFERENCES activity_administrations(id),
  raw_grade_event_id TEXT REFERENCES raw_grade_events(id),
  attempt_id TEXT,
  stream TEXT NOT NULL CHECK (stream IN ('error_intake','calibration','adjudicated_anchor')),
  stratum_json TEXT NOT NULL,
  inclusion_probability REAL NOT NULL CHECK (inclusion_probability > 0),
  sampling_frame_id TEXT,
  selected INTEGER NOT NULL DEFAULT 1 CHECK (selected IN (0,1)),
  created_at TEXT NOT NULL
);
CREATE INDEX idx_css_stream ON calibration_stream_samples(stream);
CREATE INDEX idx_css_frame ON calibration_stream_samples(sampling_frame_id);
CREATE INDEX idx_css_observation ON calibration_stream_samples(observation_id);
