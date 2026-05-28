-- LearnLoop MVP initial schema.
-- Primary keys are app-generated TEXT ULIDs.
-- Timestamps are ISO-8601 UTC TEXT.
-- YAML-owned ids are soft references validated by the application.

PRAGMA foreign_keys = ON;

CREATE TABLE schema_migrations (
  version INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  applied_at TEXT NOT NULL
);

CREATE TABLE agent_runs (
  id TEXT PRIMARY KEY,
  purpose TEXT NOT NULL,
  model TEXT,
  provider TEXT NOT NULL,
  prompt_template TEXT,
  prompt_version TEXT,
  sdk_version TEXT,
  codex_revision TEXT,
  input_context_hash TEXT,
  output_schema TEXT,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
  error_message TEXT
);

CREATE TABLE proposed_patches (
  id TEXT PRIMARY KEY,
  agent_run_id TEXT NOT NULL,
  purpose TEXT NOT NULL,
  source_refs_json TEXT,
  summary TEXT,
  status_cache TEXT NOT NULL CHECK (
    status_cache IN ('pending', 'partially_accepted', 'accepted', 'rejected', 'invalid')
  ),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE proposed_patch_items (
  id TEXT PRIMARY KEY,
  proposed_patch_id TEXT NOT NULL REFERENCES proposed_patches(id) ON DELETE CASCADE,
  client_item_id TEXT NOT NULL,
  item_type TEXT NOT NULL CHECK (
    item_type IN ('learning_object', 'practice_item', 'concept', 'concept_edge', 'rubric', 'error_type')
  ),
  operation TEXT NOT NULL CHECK (operation IN ('create', 'update', 'deactivate')),
  target_entity_type TEXT CHECK (
    target_entity_type IS NULL OR
    target_entity_type IN ('learning_object', 'practice_item', 'concept', 'concept_edge', 'rubric', 'error_type')
  ),
  target_entity_id TEXT,
  payload_json TEXT NOT NULL,
  edited_payload_json TEXT,
  decision TEXT NOT NULL CHECK (decision IN ('pending', 'accepted', 'rejected')),
  validation_status TEXT NOT NULL CHECK (validation_status IN ('valid', 'warning', 'invalid')),
  validation_errors_json TEXT,
  applied_change_batch_id TEXT,
  decided_at TEXT,
  decided_by TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (proposed_patch_id, client_item_id)
);
CREATE INDEX idx_proposed_patch_items_decision
  ON proposed_patch_items(proposed_patch_id, decision);

CREATE TABLE change_batches (
  id TEXT PRIMARY KEY,
  proposed_patch_item_id TEXT,
  reason TEXT NOT NULL CHECK (reason IN ('proposal_accept', 'manual_edit', 'import')),
  origin TEXT NOT NULL CHECK (origin IN ('learner', 'system', 'codex')),
  summary TEXT,
  created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX idx_change_batches_proposal_item
  ON change_batches(proposed_patch_item_id)
  WHERE proposed_patch_item_id IS NOT NULL;

CREATE TABLE content_events (
  id TEXT PRIMARY KEY,
  change_batch_id TEXT,
  event_type TEXT NOT NULL CHECK (
    event_type IN (
      'created',
      'updated',
      'deactivated',
      'regrade_disagreement',
      'algorithm_version_bumped',
      'source_span_changed',
      'source_span_removed'
    )
  ),
  subject TEXT,
  entity_type TEXT NOT NULL CHECK (
    entity_type IN ('learning_object', 'practice_item', 'concept', 'concept_edge', 'rubric', 'error_type')
  ),
  entity_id TEXT NOT NULL,
  origin TEXT NOT NULL CHECK (origin IN ('learner', 'system', 'codex', 'import')),
  review_status TEXT CHECK (
    review_status IS NULL OR review_status IN ('auto_accepted', 'accepted', 'rejected')
  ),
  summary TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_content_events_recent
  ON content_events(created_at, event_type);

CREATE TABLE practice_attempts (
  id TEXT PRIMARY KEY,
  practice_item_id TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  subject TEXT,
  concept TEXT,
  practice_mode TEXT NOT NULL,
  attempt_type TEXT NOT NULL CHECK (
    attempt_type IN (
      'independent_attempt',
      'hinted_attempt',
      'dont_know',
      'diagnostic_probe',
      'guided_walkthrough',
      'reconstruction_after_walkthrough',
      'skip',
      'self_report'
    )
  ),
  learner_answer_md TEXT,
  evidence_facets_json TEXT,
  evidence_weights_json TEXT,
  rubric_score INTEGER CHECK (rubric_score IS NULL OR rubric_score BETWEEN 0 AND 4),
  correctness REAL CHECK (correctness IS NULL OR (correctness >= 0.0 AND correctness <= 1.0)),
  confidence INTEGER CHECK (confidence IS NULL OR confidence BETWEEN 1 AND 5),
  latency_seconds INTEGER CHECK (latency_seconds IS NULL OR latency_seconds >= 0),
  hints_used INTEGER NOT NULL DEFAULT 0 CHECK (hints_used >= 0),
  error_type TEXT,
  grader_confidence REAL CHECK (
    grader_confidence IS NULL OR (grader_confidence >= 0.0 AND grader_confidence <= 1.0)
  ),
  manual_review INTEGER NOT NULL DEFAULT 0 CHECK (manual_review IN (0, 1)),
  manual_review_reason TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT
);
CREATE INDEX idx_attempts_lo_time
  ON practice_attempts(learning_object_id, created_at);
CREATE INDEX idx_attempts_item_time
  ON practice_attempts(practice_item_id, created_at);

CREATE TABLE grading_evidence (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id) ON DELETE CASCADE,
  criterion_id TEXT NOT NULL,
  points_awarded REAL NOT NULL,
  evidence TEXT,
  notes TEXT,
  agent_run_id TEXT,
  local_grader_id TEXT,
  grader_tier INTEGER NOT NULL CHECK (grader_tier BETWEEN 0 AND 4),
  created_at TEXT NOT NULL,
  superseded_at TEXT,
  superseded_by_evidence_id TEXT
);
CREATE INDEX idx_grading_evidence_attempt
  ON grading_evidence(attempt_id);

CREATE TABLE error_events (
  id TEXT PRIMARY KEY,
  attempt_id TEXT,
  learning_object_id TEXT NOT NULL,
  error_type TEXT NOT NULL,
  severity REAL NOT NULL CHECK (severity >= 0.0 AND severity <= 1.0),
  is_misconception INTEGER NOT NULL DEFAULT 0 CHECK (is_misconception IN (0, 1)),
  repair_plan_json TEXT,
  status TEXT NOT NULL CHECK (status IN ('active', 'resolved')),
  created_at TEXT NOT NULL,
  updated_at TEXT
);
CREATE INDEX idx_error_events_status
  ON error_events(status, learning_object_id);

CREATE TABLE attempt_surprise (
  attempt_id TEXT PRIMARY KEY REFERENCES practice_attempts(id) ON DELETE CASCADE,
  predicted_score_dist_json TEXT,
  predicted_error_type_dist_json TEXT,
  observed_joint_bucket_json TEXT NOT NULL,
  predictive_surprise REAL,
  bayesian_surprise REAL,
  surprise_direction TEXT CHECK (
    surprise_direction IS NULL OR surprise_direction IN ('positive', 'negative', 'mixed', 'none')
  ),
  fsrs_interval_factor REAL,
  posterior_delta_json TEXT,
  triggered_actions_json TEXT,
  suppressed_actions_json TEXT,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE practice_item_state (
  practice_item_id TEXT PRIMARY KEY,
  difficulty REAL,
  stability REAL,
  retrievability REAL,
  due_at TEXT,
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
  content_hash TEXT,
  last_attempt_at TEXT,
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_item_state_due
  ON practice_item_state(active, due_at);

CREATE TABLE learning_object_mastery (
  learning_object_id TEXT PRIMARY KEY,
  logit_mean REAL NOT NULL DEFAULT 0.0,
  logit_variance REAL NOT NULL DEFAULT 1.0 CHECK (logit_variance >= 0.0),
  evidence_count INTEGER NOT NULL DEFAULT 0 CHECK (evidence_count >= 0),
  last_evidence_at TEXT,
  algorithm_version TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
-- Display values mastery_mean = sigmoid(logit_mean) and
-- mastery_variance = (m * (1 - m))^2 * logit_variance are computed on read in
-- services/mastery.py; they are not stored.

CREATE TABLE learner_theta (
  id TEXT PRIMARY KEY,
  domain TEXT NOT NULL,
  evidence_family TEXT NOT NULL,
  practice_mode TEXT,
  theta_mean REAL NOT NULL,
  theta_variance REAL NOT NULL CHECK (theta_variance >= 0.0),
  evidence_count INTEGER NOT NULL DEFAULT 0 CHECK (evidence_count >= 0),
  prior_pseudo_count REAL NOT NULL DEFAULT 0.0 CHECK (prior_pseudo_count >= 0.0),
  algorithm_version TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX idx_learner_theta_unique
  ON learner_theta(domain, evidence_family, COALESCE(practice_mode, ''));

CREATE TABLE learner_claims (
  id TEXT PRIMARY KEY,
  claim_type TEXT NOT NULL CHECK (
    claim_type IN ('background_familiarity', 'prior_coursework', 'self_rating')
  ),
  scope_type TEXT NOT NULL CHECK (
    scope_type IN ('concept', 'learning_object', 'subject', 'domain', 'global')
  ),
  scope_id TEXT,
  evidence_family TEXT,
  claimed_level REAL NOT NULL CHECK (claimed_level >= 0.0 AND claimed_level <= 1.0),
  prior_pseudo_count REAL NOT NULL CHECK (prior_pseudo_count >= 0.0),
  source TEXT NOT NULL CHECK (source IN ('init_wizard', 'manual_cli', 'imported')),
  created_at TEXT NOT NULL
);

CREATE TABLE lo_probe_state (
  learning_object_id TEXT PRIMARY KEY,
  status TEXT NOT NULL CHECK (status IN ('pending', 'in_progress', 'complete', 'skipped_by_claim')),
  probe_phase_id TEXT,
  hypothesis_set_id TEXT,
  probe_attempts_completed INTEGER NOT NULL DEFAULT 0 CHECK (probe_attempts_completed >= 0),
  probe_attempts_target INTEGER NOT NULL DEFAULT 3 CHECK (probe_attempts_target >= 0),
  families_converged_json TEXT,
  entered_at TEXT,
  completed_at TEXT,
  algorithm_version TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE hypothesis_sets (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT NOT NULL,
  probe_phase_id TEXT,
  hypotheses_json TEXT NOT NULL,
  prior_json TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_hypothesis_sets_lo
  ON hypothesis_sets(learning_object_id, created_at);

CREATE TABLE learner_state_beliefs (
  id TEXT PRIMARY KEY,
  subject TEXT,
  scope_type TEXT NOT NULL CHECK (scope_type IN ('error_type', 'misconception')),
  scope_id TEXT NOT NULL,
  belief_key TEXT NOT NULL,
  mean REAL NOT NULL,
  variance REAL NOT NULL CHECK (variance >= 0.0),
  evidence_count INTEGER NOT NULL DEFAULT 0 CHECK (evidence_count >= 0),
  last_surprise REAL,
  last_evidence_at TEXT,
  stale_after_days INTEGER,
  algorithm_version TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX idx_learner_state_beliefs_unique
  ON learner_state_beliefs(COALESCE(subject, ''), scope_type, scope_id, belief_key);
CREATE INDEX idx_learner_state_beliefs_scope
  ON learner_state_beliefs(subject, scope_type, scope_id);

CREATE TABLE elicitation_events (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  selected_practice_item_id TEXT,
  target_scope_json TEXT,
  policy TEXT NOT NULL CHECK (policy IN ('probe_eig')),
  candidate_scores_json TEXT,
  entropy_before REAL,
  expected_information_gain REAL,
  selected_reason TEXT,
  hypothesis_set_id TEXT,
  hypothesis_set_json TEXT,
  trigger TEXT CHECK (
    trigger IS NULL OR trigger IN ('probe_phase_routine', 'probe_phase_local_pi_inadequate')
  ),
  fallback_outcome TEXT CHECK (
    fallback_outcome IS NULL OR fallback_outcome IN ('existing_pi', 'existing_pi_inadequate')
  ),
  created_at TEXT NOT NULL
);
CREATE INDEX idx_elicitation_events_session
  ON elicitation_events(session_id, selected_practice_item_id);

CREATE TABLE scheduler_explanations (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  practice_item_id TEXT NOT NULL,
  selected_mode TEXT NOT NULL,
  priority REAL NOT NULL,
  components_json TEXT NOT NULL,
  readiness_factor REAL,
  expected_information_gain REAL,
  target_scope_json TEXT,
  plain_english_json TEXT,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_scheduler_explanations_session
  ON scheduler_explanations(session_id, practice_item_id);

CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  energy TEXT,
  sleep_quality REAL CHECK (sleep_quality IS NULL OR (sleep_quality >= 0.0 AND sleep_quality <= 1.0)),
  available_minutes INTEGER CHECK (available_minutes IS NULL OR available_minutes >= 0),
  notes_md_path TEXT,
  updated_at TEXT
);

CREATE TABLE session_checkpoints (
  session_id TEXT PRIMARY KEY,
  current_practice_item_id TEXT,
  current_answer TEXT,
  focus_block_state_json TEXT,
  pending_grading_proposal_json TEXT,
  readiness_json TEXT,
  updated_at TEXT NOT NULL
);

CREATE TABLE observation_templates (
  id TEXT PRIMARY KEY,
  domain TEXT NOT NULL,
  version TEXT NOT NULL,
  title TEXT NOT NULL,
  template_yaml TEXT NOT NULL,
  emits_attempt INTEGER NOT NULL DEFAULT 0 CHECK (emits_attempt IN (0, 1)),
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE observation_events (
  id TEXT PRIMARY KEY,
  template_id TEXT NOT NULL,
  subject TEXT,
  session_id TEXT,
  related_learning_object_id TEXT,
  related_practice_item_id TEXT,
  binding_mode TEXT CHECK (
    binding_mode IS NULL OR binding_mode IN ('learner_picks', 'template_fixed', 'pending', 'promoted_later')
  ),
  response_json TEXT NOT NULL,
  emitted_attempt_id TEXT,
  template_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_observation_events_subject
  ON observation_events(subject, created_at);
