-- Probe/EIG redesign (spec_probe_eig_redesign.md): first-class diagnostic
-- episodes, committed presentations, observation traces, state segments, and
-- the versioned Probe Family / Instrument Card hierarchy.

-- §5.1: one row per diagnostic episode; every entry/re-entry gets a fresh ULID.
CREATE TABLE probe_episodes (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (
    status IN ('pending_items', 'in_progress', 'complete', 'abandoned', 'converted_to_tutoring')
  ),
  trigger TEXT NOT NULL CHECK (
    trigger IN ('initial', 'misconception', 'stale_uncertainty', 'manual', 'goal_diagnostic')
  ),
  hypothesis_set_id TEXT,
  active_state_segment_id TEXT,
  target_decision_json TEXT,
  required_facets_json TEXT,
  minimum_independent_observations INTEGER NOT NULL DEFAULT 2 CHECK (minimum_independent_observations >= 1),
  maximum_observations INTEGER NOT NULL DEFAULT 4 CHECK (maximum_observations >= 1),
  entered_at TEXT,
  completed_at TEXT,
  completion_reason TEXT CHECK (
    completion_reason IS NULL OR completion_reason IN (
      'decision_stable',
      'predictive_uncertainty_below_threshold',
      'observation_budget_exhausted',
      'no_suitable_candidate',
      'converted_to_tutoring',
      'learner_abandoned',
      'manual_stop',
      'fast_path_strong_claim',
      'superseded_by_redesign'
    )
  ),
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_probe_episodes_lo ON probe_episodes(learning_object_id, created_at);
-- At most one open episode per Learning Object.
CREATE UNIQUE INDEX idx_probe_episodes_open
  ON probe_episodes(learning_object_id)
  WHERE status IN ('pending_items', 'in_progress');

-- §5.1 state segments: the event that opens a segment is persisted so replay
-- reconstructs segment boundaries deterministically. Ordered per LO.
CREATE TABLE probe_state_segments (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT NOT NULL,
  probe_episode_id TEXT,
  sequence INTEGER NOT NULL,
  reason TEXT NOT NULL CHECK (
    reason IN ('episode_entry', 'tutoring_transition', 'feedback_reveal', 'block_end', 'manual')
  ),
  opened_by_attempt_id TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_probe_state_segments_lo ON probe_state_segments(learning_object_id, sequence);
CREATE UNIQUE INDEX idx_probe_state_segments_order
  ON probe_state_segments(learning_object_id, sequence);

-- §5.1: durable committed assignment between selection and observation.
CREATE TABLE probe_presentations (
  id TEXT PRIMARY KEY,
  probe_episode_id TEXT NOT NULL REFERENCES probe_episodes(id),
  practice_item_id TEXT NOT NULL,
  scheduler_candidate_id TEXT,
  state_segment_id TEXT NOT NULL,
  probe_family_template_id TEXT,
  probe_family_template_version INTEGER,
  instrument_card_id TEXT,
  instrument_card_version INTEGER,
  instrument_card_snapshot_json TEXT,
  target_hypothesis_pairs_json TEXT,
  target_facets_json TEXT,
  posterior_at_selection_json TEXT,
  entropy_at_selection REAL,
  expected_information_gain REAL,
  selection_policy_version TEXT,
  status TEXT NOT NULL CHECK (status IN ('selected', 'served', 'submitted', 'ended')),
  end_reason TEXT CHECK (end_reason IS NULL OR end_reason IN ('expired', 'abandoned', 'invalidated')),
  served_at TEXT,
  submitted_at TEXT,
  expires_at TEXT,
  ended_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_probe_presentations_episode ON probe_presentations(probe_episode_id, created_at);
CREATE INDEX idx_probe_presentations_item ON probe_presentations(practice_item_id, created_at);

-- §5.1: one observation per accepted diagnostic attempt (unique on attempt_id).
CREATE TABLE probe_observations (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id),
  posterior_before_json TEXT NOT NULL,
  posterior_after_json TEXT NOT NULL,
  entropy_before REAL NOT NULL,
  entropy_after REAL NOT NULL,
  realized_information_gain REAL NOT NULL,
  independent_evidence_discount REAL,
  contamination_json TEXT,
  grader_channel_json TEXT,
  updates_belief INTEGER NOT NULL DEFAULT 1 CHECK (updates_belief IN (0, 1)),
  eligible_for_completion INTEGER NOT NULL DEFAULT 0 CHECK (eligible_for_completion IN (0, 1)),
  created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX idx_probe_observations_attempt ON probe_observations(attempt_id);

-- §5.1: attempts gain a nullable presentation reference; a presentation can be
-- consumed by at most one attempt (partial unique index).
ALTER TABLE practice_attempts ADD COLUMN probe_presentation_id TEXT;
CREATE UNIQUE INDEX idx_attempts_probe_presentation
  ON practice_attempts(probe_presentation_id)
  WHERE probe_presentation_id IS NOT NULL;

-- §9.1: versioned, append-only family templates and LO-bound Instrument Cards.
CREATE TABLE probe_family_templates (
  id TEXT NOT NULL,
  version INTEGER NOT NULL CHECK (version >= 1),
  status TEXT NOT NULL CHECK (status IN ('draft', 'provisional', 'trusted', 'retired')),
  template_json TEXT NOT NULL,
  schema_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  retired_at TEXT,
  PRIMARY KEY (id, version)
);

CREATE TABLE probe_instrument_cards (
  id TEXT NOT NULL,
  version INTEGER NOT NULL CHECK (version >= 1),
  probe_family_template_id TEXT NOT NULL,
  probe_family_template_version INTEGER NOT NULL,
  learning_object_id TEXT NOT NULL,
  hypothesis_scope_json TEXT NOT NULL,
  card_json TEXT NOT NULL,
  compiled_likelihood_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  retired_at TEXT,
  PRIMARY KEY (id, version)
);
CREATE INDEX idx_probe_instrument_cards_lo ON probe_instrument_cards(learning_object_id);

CREATE TABLE probe_item_family_links (
  practice_item_id TEXT NOT NULL,
  instrument_card_id TEXT NOT NULL,
  instrument_card_version INTEGER NOT NULL,
  generator_id TEXT,
  generator_version TEXT,
  generation_seed TEXT,
  instance_metadata_json TEXT,
  created_at TEXT NOT NULL,
  PRIMARY KEY (practice_item_id, instrument_card_id, instrument_card_version)
);

-- §9.7: hierarchical calibration pooled at the family-version level. Synthetic
-- gate outcomes and real learner evidence are separate rows, never merged.
CREATE TABLE probe_family_calibrations (
  id TEXT PRIMARY KEY,
  probe_family_template_id TEXT NOT NULL,
  probe_family_template_version INTEGER NOT NULL,
  generator_version TEXT,
  grader_version TEXT,
  evidence_source TEXT NOT NULL CHECK (evidence_source IN ('synthetic_gate', 'real_learner', 'reviewed_human')),
  parameter_posterior_json TEXT NOT NULL,
  sample_size INTEGER NOT NULL DEFAULT 0 CHECK (sample_size >= 0),
  effective_sample_size REAL,
  updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX idx_probe_family_calibrations_scope
  ON probe_family_calibrations(
    probe_family_template_id,
    probe_family_template_version,
    COALESCE(generator_version, ''),
    COALESCE(grader_version, ''),
    evidence_source
  );

-- §10: one durable, deduplicated generation need per episode target.
CREATE TABLE probe_generation_needs (
  id TEXT PRIMARY KEY,
  probe_episode_id TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  target_key TEXT NOT NULL,
  missing_capability TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pending', 'resolved', 'declined')),
  created_at TEXT NOT NULL,
  resolved_at TEXT,
  UNIQUE (probe_episode_id, target_key)
);
CREATE INDEX idx_probe_generation_needs_lo ON probe_generation_needs(learning_object_id, status);

-- Checkpoint 0: legacy cutover. lo_probe_state becomes read-only legacy; any
-- in-progress legacy phase is closed as superseded_by_redesign (never silently
-- reinterpreted). Eligible LOs re-enter through new probe_episodes rows.
ALTER TABLE lo_probe_state ADD COLUMN completion_reason TEXT;
UPDATE lo_probe_state
SET status = 'complete',
    completion_reason = 'superseded_by_redesign',
    completed_at = COALESCE(completed_at, strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
WHERE status = 'in_progress';
