-- Probe/EIG redesign Checkpoints 4 and 5 (spec_probe_eig_redesign.md):
-- empirical pilot, hierarchical item calibration, regrade agreement, family
-- lifecycle audit trail, and contextual question-event telemetry.

-- §9.7: item-instance residual layer under the family-version posterior.
-- Generated instances inherit the family posterior; item-specific estimates
-- shrink strongly toward it until sufficient real evidence exists. Synthetic
-- and real evidence stay separate rows, exactly like the family level.
CREATE TABLE probe_item_calibrations (
  id TEXT PRIMARY KEY,
  practice_item_id TEXT NOT NULL,
  probe_family_template_id TEXT NOT NULL,
  probe_family_template_version INTEGER NOT NULL,
  grader_version TEXT,
  evidence_source TEXT NOT NULL CHECK (evidence_source IN ('synthetic_gate', 'real_learner', 'reviewed_human')),
  parameter_posterior_json TEXT NOT NULL,
  sample_size INTEGER NOT NULL DEFAULT 0 CHECK (sample_size >= 0),
  effective_sample_size REAL,
  updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX idx_probe_item_calibrations_scope
  ON probe_item_calibrations(
    practice_item_id,
    probe_family_template_id,
    probe_family_template_version,
    COALESCE(grader_version, ''),
    evidence_source
  );

-- §7.6/§13.2 (Checkpoint 4.4): regrade agreement and grading confusion per
-- family version and grader version. One row per regrade check of a probe
-- observation's grader output; agreement compares outcome classes, and the
-- (original, regrade) pair is the grading confusion cell.
CREATE TABLE probe_regrade_checks (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL,
  probe_family_template_id TEXT NOT NULL,
  probe_family_template_version INTEGER NOT NULL,
  grader_version TEXT,
  original_outcome TEXT NOT NULL,
  regrade_outcome TEXT NOT NULL,
  agreement INTEGER NOT NULL CHECK (agreement IN (0, 1)),
  created_at TEXT NOT NULL
);
CREATE INDEX idx_probe_regrade_checks_family
  ON probe_regrade_checks(probe_family_template_id, probe_family_template_version);
CREATE INDEX idx_probe_regrade_checks_attempt ON probe_regrade_checks(attempt_id);

-- §9.7 lifecycle (Checkpoint 4.7): every family-version status transition is
-- persisted with the metric evidence that justified it, so trusted/revise/
-- retire decisions stay auditable after the fact.
CREATE TABLE probe_family_lifecycle_events (
  id TEXT PRIMARY KEY,
  probe_family_template_id TEXT NOT NULL,
  probe_family_template_version INTEGER NOT NULL,
  from_status TEXT NOT NULL,
  to_status TEXT NOT NULL CHECK (to_status IN ('draft', 'provisional', 'trusted', 'retired')),
  reason_json TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_probe_family_lifecycle_family
  ON probe_family_lifecycle_events(probe_family_template_id, probe_family_template_version, created_at);

-- §13.4 (Checkpoint 4.6): contextual question-event telemetry. The generating
-- process of a learner question depends on tutor moves, affordances, warnings,
-- and goals; these columns persist that context so contextual likelihoods can
-- be calibrated later. signal_channel separates epistemic evidence (missing or
-- uncertain knowledge) from interaction-preference signal (requested style,
-- pace, scaffold level) — the second channel changes tutor policy, not mastery
-- belief, and receives a damped mastery likelihood until calibrated.
ALTER TABLE question_events ADD COLUMN preceding_tutor_move TEXT;
ALTER TABLE question_events ADD COLUMN scaffold_level TEXT;
ALTER TABLE question_events ADD COLUMN warning_state TEXT;
ALTER TABLE question_events ADD COLUMN learner_mode TEXT;
ALTER TABLE question_events ADD COLUMN question_opportunity TEXT;
ALTER TABLE question_events ADD COLUMN hints_used_before INTEGER;
ALTER TABLE question_events ADD COLUMN direct_explanation_request INTEGER NOT NULL DEFAULT 0;
ALTER TABLE question_events ADD COLUMN attempt_progress TEXT;
ALTER TABLE question_events ADD COLUMN signal_channel TEXT CHECK (
  signal_channel IS NULL OR signal_channel IN ('epistemic', 'interaction_preference')
);
