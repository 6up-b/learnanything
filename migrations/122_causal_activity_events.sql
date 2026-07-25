-- P2 §4.2: causal activity classification becomes an append-only EVENT log.
--
-- Migration 121 gave `causal_activity_classifications` an `attempt_id` PRIMARY
-- KEY, and the repository raised ValueError when a second writer disagreed.
-- Two writers already exist on the attempt hot path (attempts.apply_attempt
-- records `repair_activity` for a primed draft; probe_episodes records the
-- diagnostic class), so a primed probe, a replay, or a backfill raised INSIDE
-- attempt application. Conflicts are now recorded, not rejected: the current
-- classification is derived by CONTAMINATION_PRECEDENCE (most contaminated
-- wins) in services/causal_activity_policy.py.

CREATE TABLE causal_activity_classification_events (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL,
  seq INTEGER NOT NULL,
  contamination_class TEXT NOT NULL CHECK (
    contamination_class IN (
      'pure_diagnostic',
      'instructional_diagnostic',
      'repair_activity',
      'verification'
    )
  ),
  near_clone INTEGER NOT NULL DEFAULT 0 CHECK (near_clone IN (0, 1)),
  near_clone_basis TEXT,
  closes_pre_intervention_segment INTEGER NOT NULL DEFAULT 0
    CHECK (closes_pre_intervention_segment IN (0, 1)),
  eligible_for_fsrs INTEGER NOT NULL DEFAULT 0 CHECK (eligible_for_fsrs IN (0, 1)),
  eligible_for_certification INTEGER NOT NULL DEFAULT 0
    CHECK (eligible_for_certification IN (0, 1)),
  source TEXT NOT NULL DEFAULT 'unknown',
  policy_version TEXT NOT NULL DEFAULT 'causal_activity_v1',
  detail_json TEXT,
  created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX causal_activity_classification_events_seq
  ON causal_activity_classification_events(attempt_id, seq);

-- Replay and idempotent retries restate the same fact; only a genuinely new
-- (source, class, near_clone) assertion appends a row.
CREATE UNIQUE INDEX causal_activity_classification_events_fact
  ON causal_activity_classification_events(
    attempt_id, source, contamination_class, near_clone
  );

CREATE TRIGGER causal_activity_classification_events_no_update
BEFORE UPDATE ON causal_activity_classification_events
BEGIN
  SELECT RAISE(ABORT, 'causal activity classification events are append-only');
END;

CREATE TRIGGER causal_activity_classification_events_no_delete
BEFORE DELETE ON causal_activity_classification_events
BEGIN
  SELECT RAISE(ABORT, 'causal activity classification events are append-only');
END;

INSERT INTO causal_activity_classification_events(
  id, attempt_id, seq, contamination_class, near_clone, near_clone_basis,
  closes_pre_intervention_segment, eligible_for_fsrs,
  eligible_for_certification, source, policy_version, detail_json, created_at
)
SELECT
  'migrated_' || attempt_id,
  attempt_id,
  1,
  contamination_class,
  near_clone,
  'legacy_migrated',
  closes_pre_intervention_segment,
  eligible_for_fsrs,
  eligible_for_certification,
  'migration_122',
  'causal_activity_v1',
  detail_json,
  created_at
FROM causal_activity_classifications;

DROP TABLE causal_activity_classifications;

-- §4.4 replay warning: the canonical projection now treats `diagnostic_probe`
-- and any primed attempt as assisted, which retro-changes canonical facet
-- state for historical probe attempts on the next rebuild. Record the
-- canonical projection version alongside the vault algorithm version so the
-- change surfaces as ONE deliberate recalibration boundary
-- (Repository.derived_state_rebuild_version_changes -> learner_review_feed)
-- rather than a silent retro-change.
ALTER TABLE derived_state_rebuilds
  ADD COLUMN canonical_projection_version TEXT;
