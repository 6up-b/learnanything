-- Diagnostic augmentation Stage 7 (spec_diagnostic_augmentation_v1.md §§3-4).
--
-- Synthetic traces are evaluation artifacts, never learner attempts.  Keeping
-- them in dedicated append-only tables makes the non-interference guarantee
-- structural: no foreign key or write path reaches practice_attempts,
-- error_events, grading_evidence, or a learner-state projection.

CREATE TABLE persona_realism_runs (
  id TEXT PRIMARY KEY,
  matcher_version TEXT NOT NULL,
  corpus_hash TEXT NOT NULL,
  persona_corpus_hash TEXT NOT NULL,
  real_corpus_hash TEXT NOT NULL,
  persona_source TEXT NOT NULL,
  generator_provider TEXT,
  generator_model TEXT,
  generator_family TEXT,
  persona_count INTEGER NOT NULL CHECK (persona_count >= 0),
  real_count INTEGER NOT NULL CHECK (real_count >= 0),
  folds INTEGER NOT NULL CHECK (folds >= 0),
  matcher_correct INTEGER NOT NULL CHECK (matcher_correct >= 0),
  matcher_total INTEGER NOT NULL CHECK (matcher_total >= 0),
  balanced_accuracy REAL,
  separation_threshold REAL NOT NULL
    CHECK (separation_threshold >= 0.5 AND separation_threshold <= 1.0),
  verdict TEXT NOT NULL CHECK (verdict IN (
    'indistinguishable', 'separable', 'insufficient_data'
  )),
  feature_manifest_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK (
    (verdict = 'insufficient_data' AND balanced_accuracy IS NULL)
    OR
    (verdict != 'insufficient_data'
      AND balanced_accuracy >= 0.0 AND balanced_accuracy <= 1.0)
  )
);

CREATE INDEX idx_persona_realism_family_created
  ON persona_realism_runs(generator_family, created_at, id);

CREATE TABLE diagnostic_eval_runs (
  id TEXT PRIMARY KEY,
  harness_version TEXT NOT NULL,
  grading_prompt_version TEXT NOT NULL,
  generator_provider TEXT,
  generator_model TEXT,
  generator_family TEXT NOT NULL,
  diagnostician_provider TEXT,
  diagnostician_model TEXT,
  diagnostician_family TEXT NOT NULL,
  cross_model_separated INTEGER NOT NULL
    CHECK (cross_model_separated IN (0, 1)),
  persona_realism_run_id TEXT REFERENCES persona_realism_runs(id),
  realism_licensed INTEGER NOT NULL CHECK (realism_licensed IN (0, 1)),
  status TEXT NOT NULL CHECK (status IN (
    'licensed', 'unlicensed_realism', 'invalid_same_model_family',
    'incomplete_regression_matrix', 'failed'
  )),
  case_count INTEGER NOT NULL CHECK (case_count >= 0),
  metrics_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK (
    (status = 'licensed' AND cross_model_separated = 1 AND realism_licensed = 1)
    OR status != 'licensed'
  )
);

CREATE INDEX idx_diagnostic_eval_runs_created
  ON diagnostic_eval_runs(created_at, id);

CREATE TABLE diagnostic_eval_cases (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES diagnostic_eval_runs(id),
  case_key TEXT NOT NULL,
  attempt_id TEXT,
  regression_shape TEXT NOT NULL CHECK (regression_shape IN (
    'exhibit',
    'genuine_facet_failure',
    'multiplication_failure',
    'addition_multiplication_confusion',
    'notation_typo_valid_reasoning',
    'missing_required_step',
    'alternate_valid_path',
    'item_contract_fault',
    'grader_interpretation_fault',
    'composite_supporting_pass',
    'correct_answer_invalid_reasoning',
    'unparseable_notation',
    'open_vocabulary_abstention',
    'cause_change_mid_history'
  )),
  source TEXT NOT NULL CHECK (source IN (
    'discrimination_profile', 'authored_fixture', 'adjudicated_overlap'
  )),
  practice_item_id TEXT NOT NULL,
  profile_id TEXT,
  learner_trace_md TEXT NOT NULL,
  planted_should_abstain INTEGER NOT NULL CHECK (planted_should_abstain IN (0, 1)),
  planted_anchor_json TEXT,
  planted_anchor_key TEXT NOT NULL,
  planted_cause_key TEXT,
  planted_repair_class_id TEXT,
  planted_repair_equivalence_id TEXT,
  system_snapshot_json TEXT NOT NULL,
  system_abstained INTEGER NOT NULL CHECK (system_abstained IN (0, 1)),
  system_anchor_key TEXT NOT NULL,
  system_cause_key TEXT,
  system_repair_class_id TEXT,
  system_repair_equivalence_id TEXT,
  anchor_correct INTEGER NOT NULL CHECK (anchor_correct IN (0, 1)),
  cause_correct INTEGER,
  repair_correct INTEGER,
  abstention_correct INTEGER NOT NULL CHECK (abstention_correct IN (0, 1)),
  created_at TEXT NOT NULL,
  UNIQUE (run_id, case_key),
  CHECK (cause_correct IS NULL OR cause_correct IN (0, 1)),
  CHECK (repair_correct IS NULL OR repair_correct IN (0, 1))
);

CREATE INDEX idx_diagnostic_eval_cases_attempt
  ON diagnostic_eval_cases(attempt_id, created_at, id);
CREATE INDEX idx_diagnostic_eval_cases_shape
  ON diagnostic_eval_cases(regression_shape, created_at, id);

-- One receipt per live graded attempt.  This is telemetry/provenance for the
-- four Phase-C rungs; replay does not call a model and therefore never creates
-- or rewrites one.
CREATE TABLE diagnostic_augmentation_receipts (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL UNIQUE,
  grading_prompt_version TEXT NOT NULL,
  grader_provider TEXT,
  grader_model TEXT,
  c1_repair_before_structure INTEGER NOT NULL
    CHECK (c1_repair_before_structure IN (0, 1)),
  c2_verifier_observations_json TEXT NOT NULL,
  c3_sample_count INTEGER NOT NULL CHECK (c3_sample_count >= 1),
  c3_agreement_support REAL NOT NULL
    CHECK (c3_agreement_support >= 0.0 AND c3_agreement_support <= 1.0),
  c3_disagreement_causes_json TEXT NOT NULL,
  c4_history_attempt_ids_json TEXT NOT NULL,
  hypotheses_json TEXT NOT NULL,
  revert_criteria_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

-- Every Stage-7 store is append-only.  Re-running an evaluation creates a new
-- run; correcting one requires a successor run, never a historical rewrite.
CREATE TRIGGER persona_realism_runs_no_update
BEFORE UPDATE ON persona_realism_runs
BEGIN
  SELECT RAISE(ABORT, 'persona_realism_runs are append-only');
END;

CREATE TRIGGER persona_realism_runs_no_delete
BEFORE DELETE ON persona_realism_runs
BEGIN
  SELECT RAISE(ABORT, 'persona_realism_runs are append-only');
END;

CREATE TRIGGER diagnostic_eval_runs_no_update
BEFORE UPDATE ON diagnostic_eval_runs
BEGIN
  SELECT RAISE(ABORT, 'diagnostic_eval_runs are append-only');
END;

CREATE TRIGGER diagnostic_eval_runs_no_delete
BEFORE DELETE ON diagnostic_eval_runs
BEGIN
  SELECT RAISE(ABORT, 'diagnostic_eval_runs are append-only');
END;

CREATE TRIGGER diagnostic_eval_cases_no_update
BEFORE UPDATE ON diagnostic_eval_cases
BEGIN
  SELECT RAISE(ABORT, 'diagnostic_eval_cases are append-only');
END;

CREATE TRIGGER diagnostic_eval_cases_no_delete
BEFORE DELETE ON diagnostic_eval_cases
BEGIN
  SELECT RAISE(ABORT, 'diagnostic_eval_cases are append-only');
END;

CREATE TRIGGER diagnostic_augmentation_receipts_no_update
BEFORE UPDATE ON diagnostic_augmentation_receipts
BEGIN
  SELECT RAISE(ABORT, 'diagnostic_augmentation_receipts are append-only');
END;

CREATE TRIGGER diagnostic_augmentation_receipts_no_delete
BEFORE DELETE ON diagnostic_augmentation_receipts
BEGIN
  SELECT RAISE(ABORT, 'diagnostic_augmentation_receipts are append-only');
END;
