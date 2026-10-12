-- Slice 1 M2 (spec_blind_grading_diagnosis_split_v1 §6.1): the live split
-- between the learner-blind grader and the history-aware diagnoser.
--
-- Every model output here is a persisted input: replay reads these ledgers and
-- never calls the grader, the diagnoser or the embedding endpoint (S7).

-- The validated blind grade of one attempt (BlindGradingProposal after the
-- shared validators), as the diagnoser and later diagnoses read it. A regrade
-- appends a successor with supersedes_id; nothing is edited.
CREATE TABLE blind_grade_records (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id),
  agent_run_id TEXT,
  grading_prompt_version TEXT NOT NULL,
  output_schema_version TEXT NOT NULL,
  context_hash TEXT NOT NULL,
  record_json TEXT NOT NULL,
  supersedes_id TEXT REFERENCES blind_grade_records(id),
  created_at TEXT NOT NULL,
  CHECK (supersedes_id IS NULL OR supersedes_id != id)
);
CREATE INDEX blind_grade_records_attempt ON blind_grade_records(attempt_id, created_at, id);

-- One diagnosis run. proposal_json is the VALIDATED DiagnosisProposal;
-- causal_view_json is the §4.2 reverse mapping onto the error-event and
-- repair-suggestion shapes the causal consumers read, computed once here so
-- replay never re-derives it. Re-diagnosis appends with supersedes_id.
CREATE TABLE attempt_diagnoses (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id),
  blind_grade_record_id TEXT REFERENCES blind_grade_records(id),
  agent_run_id TEXT,
  diagnosis_prompt_version TEXT NOT NULL,
  provider TEXT,
  model TEXT,
  mode TEXT NOT NULL CHECK (mode IN ('shadow', 'live')),
  history_mode TEXT NOT NULL CHECK (history_mode IN ('exact', 'full', 'snapshot', 'hybrid')),
  status TEXT NOT NULL CHECK (status IN ('completed', 'failed', 'skipped', 'validation_rejected')),
  proposal_json TEXT,
  causal_view_json TEXT,
  validation_report_json TEXT NOT NULL DEFAULT '{}',
  error TEXT,
  latency_seconds REAL,
  supersedes_id TEXT REFERENCES attempt_diagnoses(id),
  created_at TEXT NOT NULL,
  CHECK (supersedes_id IS NULL OR supersedes_id != id),
  CHECK (status != 'completed' OR proposal_json IS NOT NULL)
);
CREATE INDEX attempt_diagnoses_attempt ON attempt_diagnoses(attempt_id, created_at, id);

-- Exactly what one diagnosis was shown (the audit record; replay never
-- re-assembles a context).
CREATE TABLE diagnosis_context_receipts (
  id TEXT PRIMARY KEY,
  diagnosis_id TEXT NOT NULL UNIQUE REFERENCES attempt_diagnoses(id),
  context_hash TEXT,
  context_as_of_attempt_id TEXT,
  lagged_attempts INTEGER,
  failure_attempt_ids_json TEXT NOT NULL DEFAULT '[]',
  success_attempt_ids_json TEXT NOT NULL DEFAULT '[]',
  hypothesis_ids_json TEXT NOT NULL DEFAULT '[]',
  registry_candidate_ids_json TEXT NOT NULL DEFAULT '[]',
  prerequisite_refs_json TEXT NOT NULL DEFAULT '[]',
  retrieval_json TEXT NOT NULL DEFAULT '{}',
  anchoring_suspect INTEGER NOT NULL DEFAULT 0 CHECK (anchoring_suspect IN (0, 1)),
  validated_citations_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL
);

-- M2 diagnosis-card taps (§12.2). Eval only: confers no support authority.
CREATE TABLE diagnosis_feedback (
  id TEXT PRIMARY KEY,
  diagnosis_id TEXT NOT NULL REFERENCES attempt_diagnoses(id),
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id),
  response TEXT NOT NULL CHECK (
    response IN ('believed_candidate', 'partly', 'slipped', 'diagnosis_wrong', 'unsure', 'not_same_mistake')
  ),
  cited_attempt_id TEXT,
  forwarded_factor_id TEXT,
  shown_at TEXT,
  responded_at TEXT NOT NULL,
  CHECK ((response = 'not_same_mistake') = (cited_attempt_id IS NOT NULL))
);
CREATE INDEX diagnosis_feedback_diagnosis ON diagnosis_feedback(diagnosis_id, responded_at);

-- §9.5 shadow would-merge log: the nearest prior hypotheses for one newly
-- minted hypothesis, next to its exact-key group. Never read by routing.
CREATE TABLE diagnosis_would_merge_log (
  id TEXT PRIMARY KEY,
  diagnosis_id TEXT REFERENCES attempt_diagnoses(id),
  hypothesis_id TEXT NOT NULL,
  model_id TEXT NOT NULL,
  exact_key TEXT NOT NULL,
  exact_group_ids_json TEXT NOT NULL DEFAULT '[]',
  neighbors_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  UNIQUE (hypothesis_id, model_id)
);

-- E7: picks served while a diagnosis for this session's attempt was pending.
CREATE TABLE diagnosis_wait_receipts (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  pending_attempt_ids_json TEXT NOT NULL DEFAULT '[]',
  waited_seconds REAL NOT NULL DEFAULT 0,
  served_without_diagnosis INTEGER NOT NULL CHECK (served_without_diagnosis IN (0, 1)),
  created_at TEXT NOT NULL
);

-- The durable post-attempt queue (§11). Lease fencing follows
-- reader_background_requests (migration 093): lease_epoch moves on every
-- claim, and a guarded write from a worker whose lease was re-claimed applies
-- to zero rows.
CREATE TABLE post_attempt_jobs (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id),
  kind TEXT NOT NULL CHECK (kind IN ('diagnose', 'embed')),
  job_key TEXT NOT NULL,
  attempt_completed_at TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'queued'
    CHECK (state IN ('queued', 'leased', 'done', 'failed', 'skipped')),
  attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  lease_owner TEXT,
  lease_expires_at TEXT,
  lease_epoch INTEGER NOT NULL DEFAULT 0,
  not_before TEXT,
  last_error TEXT,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (kind, job_key)
);
CREATE INDEX post_attempt_jobs_order ON post_attempt_jobs(kind, state, attempt_completed_at, attempt_id);

-- §10: null reads as 'joint', so attempts graded before this column existed
-- can never pass the blinding check vacuously.
ALTER TABLE diagnostic_augmentation_receipts ADD COLUMN grader_mode TEXT
  CHECK (grader_mode IS NULL OR grader_mode IN ('joint', 'blind'));

CREATE TRIGGER blind_grade_records_no_update
BEFORE UPDATE ON blind_grade_records
BEGIN
  SELECT RAISE(ABORT, 'blind_grade_records are append-only');
END;
CREATE TRIGGER blind_grade_records_no_delete
BEFORE DELETE ON blind_grade_records
BEGIN
  SELECT RAISE(ABORT, 'blind_grade_records are append-only');
END;
CREATE TRIGGER attempt_diagnoses_no_update
BEFORE UPDATE ON attempt_diagnoses
BEGIN
  SELECT RAISE(ABORT, 'attempt_diagnoses are append-only');
END;
CREATE TRIGGER attempt_diagnoses_no_delete
BEFORE DELETE ON attempt_diagnoses
BEGIN
  SELECT RAISE(ABORT, 'attempt_diagnoses are append-only');
END;
CREATE TRIGGER diagnosis_context_receipts_no_update
BEFORE UPDATE ON diagnosis_context_receipts
BEGIN
  SELECT RAISE(ABORT, 'diagnosis_context_receipts are append-only');
END;
CREATE TRIGGER diagnosis_context_receipts_no_delete
BEFORE DELETE ON diagnosis_context_receipts
BEGIN
  SELECT RAISE(ABORT, 'diagnosis_context_receipts are append-only');
END;
CREATE TRIGGER diagnosis_feedback_no_update
BEFORE UPDATE ON diagnosis_feedback
BEGIN
  SELECT RAISE(ABORT, 'diagnosis_feedback is append-only');
END;
CREATE TRIGGER diagnosis_feedback_no_delete
BEFORE DELETE ON diagnosis_feedback
BEGIN
  SELECT RAISE(ABORT, 'diagnosis_feedback is append-only');
END;
CREATE TRIGGER diagnosis_would_merge_log_no_update
BEFORE UPDATE ON diagnosis_would_merge_log
BEGIN
  SELECT RAISE(ABORT, 'diagnosis_would_merge_log is append-only');
END;
CREATE TRIGGER diagnosis_would_merge_log_no_delete
BEFORE DELETE ON diagnosis_would_merge_log
BEGIN
  SELECT RAISE(ABORT, 'diagnosis_would_merge_log is append-only');
END;
CREATE TRIGGER diagnosis_wait_receipts_no_update
BEFORE UPDATE ON diagnosis_wait_receipts
BEGIN
  SELECT RAISE(ABORT, 'diagnosis_wait_receipts are append-only');
END;
CREATE TRIGGER diagnosis_wait_receipts_no_delete
BEFORE DELETE ON diagnosis_wait_receipts
BEGIN
  SELECT RAISE(ABORT, 'diagnosis_wait_receipts are append-only');
END;
