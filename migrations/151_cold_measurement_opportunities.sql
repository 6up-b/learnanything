-- Durable cold-measurement opportunities and receipt lineage.
--
-- A cold measurement starts before an item is selected.  Recording only the
-- scheduled task loses every refused opportunity and makes selection
-- availability look like learner performance.  The base row therefore records
-- that an opportunity existed; exactly one append-only decision records how it
-- terminated:
--
--   scheduled | structurally_refused | policy_refused |
--   operationally_unavailable | learner_declined
--
-- Administration/final receipts and scheduled tasks are children of that
-- opportunity.  A crash between creation and decision leaves an honest
-- undecided opportunity rather than silently erasing the denominator.

CREATE TABLE cold_measurement_opportunities (
  id TEXT PRIMARY KEY,
  lane TEXT NOT NULL,
  trigger_kind TEXT NOT NULL,
  trigger_ref TEXT NOT NULL,
  learning_object_id TEXT,
  case_kind TEXT,
  case_ref TEXT,
  remediation_episode_id TEXT,
  source_attempt_id TEXT,
  certificate_id TEXT,
  policy_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(lane, trigger_kind, trigger_ref)
);

CREATE TABLE cold_measurement_opportunity_decisions (
  id TEXT PRIMARY KEY,
  measurement_opportunity_id TEXT NOT NULL
    REFERENCES cold_measurement_opportunities(id),
  decision TEXT NOT NULL CHECK (
    decision IN (
      'scheduled',
      'structurally_refused',
      'policy_refused',
      'operationally_unavailable',
      'learner_declined'
    )
  ),
  reason TEXT NOT NULL,
  followup_task_id TEXT,
  selected_item_id TEXT,
  candidate_summary_json TEXT NOT NULL DEFAULT '{}',
  scheduled_not_before TEXT,
  scheduled_expires_at TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(measurement_opportunity_id)
);

CREATE INDEX idx_cold_measurement_opportunities_lane_lo
  ON cold_measurement_opportunities(lane, learning_object_id, created_at, id);
CREATE INDEX idx_cold_measurement_opportunity_decisions_outcome
  ON cold_measurement_opportunity_decisions(decision, created_at, id);

CREATE TRIGGER cold_measurement_opportunities_no_update
BEFORE UPDATE ON cold_measurement_opportunities
BEGIN
  SELECT RAISE(ABORT, 'cold measurement opportunities are append-only');
END;

CREATE TRIGGER cold_measurement_opportunities_no_delete
BEFORE DELETE ON cold_measurement_opportunities
BEGIN
  SELECT RAISE(ABORT, 'cold measurement opportunities are append-only');
END;

CREATE TRIGGER cold_measurement_opportunity_decisions_no_update
BEFORE UPDATE ON cold_measurement_opportunity_decisions
BEGIN
  SELECT RAISE(ABORT, 'cold measurement opportunity decisions are append-only');
END;

CREATE TRIGGER cold_measurement_opportunity_decisions_no_delete
BEFORE DELETE ON cold_measurement_opportunity_decisions
BEGIN
  SELECT RAISE(ABORT, 'cold measurement opportunity decisions are append-only');
END;

ALTER TABLE followup_tasks ADD COLUMN measurement_opportunity_id TEXT;
CREATE INDEX idx_followup_tasks_measurement_opportunity
  ON followup_tasks(measurement_opportunity_id);

ALTER TABLE coldness_receipts ADD COLUMN measurement_opportunity_id TEXT;
CREATE UNIQUE INDEX uq_coldness_receipts_opportunity_stage
  ON coldness_receipts(measurement_opportunity_id, stage)
  WHERE measurement_opportunity_id IS NOT NULL;
CREATE INDEX idx_coldness_receipts_measurement_opportunity
  ON coldness_receipts(measurement_opportunity_id, created_at, id);

-- Time-bounded receipt scans must remain indexed as vaults grow.
CREATE INDEX idx_practice_attempts_created
  ON practice_attempts(created_at, id);
CREATE INDEX idx_practice_attempts_item_created
  ON practice_attempts(practice_item_id, created_at, id);
CREATE INDEX idx_question_events_created
  ON question_events(created_at, id);
CREATE INDEX idx_source_exposure_events_created
  ON source_exposure_events(created_at, id);
CREATE INDEX idx_remediation_episodes_created
  ON remediation_episodes(created_at, id);
CREATE INDEX idx_attempt_feedback_metadata_last_shown
  ON attempt_feedback_metadata(last_shown_at, attempt_id);
