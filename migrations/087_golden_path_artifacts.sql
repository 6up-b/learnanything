-- P2 ASSESSMENT + RESTORATION + MILESTONE track
-- (spec_p2_narrow_golden_path §8.2, §8.3, §8.4, §7.5; design B.8-B.10).
--
-- Migration numbering: follows 086_reader_dialogue. Never edit an applied migration.
--
-- The cold-assessment result, the post-attempt restoration + boundary diff, and the
-- milestone / one-edge suggest_next invitation (and the learner's explicit accept /
-- decline of that invitation) are all INSPECTABLE ARTIFACTS the run accrues after
-- measurement (§8.4 "restoration is an instructional event after measurement" -- it
-- cannot alter the assessment observation, so these live in their OWN append-only
-- store, never on the measurement substrate). The UI track renders them later.
--
-- This table adds NO measurement, posterior, FSRS, or certification path: the
-- certification itself is minted by the landed P0 machinery
-- (goal_contracts.certify_from_administration over the pinned target version), the
-- burn is the landed activities render/burn boundary, and the depth edge is the
-- landed P1 depth_transition.commit_one_edge. This is pure run bookkeeping (spec
-- §2 ownership ledger / composition-smell audit: legitimate P2 substrate).
--
-- Append-only + idempotent: `seq` is a monotone per-run ordinal and
-- `UNIQUE(run_id, idempotency_key)` collapses a crash/retry to exactly one artifact
-- (§12.6 exactly-once "source restoration event" side effect).

CREATE TABLE golden_path_artifacts (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES golden_path_runs(id) ON DELETE CASCADE,
  seq INTEGER NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN (
    'assessment_result',   -- §8.2 reliability-aware certification DTO + burn/follow-up
    'restoration',         -- §8.4 source neighborhoods + exemplar comparison + next action
    'boundary_diff',       -- §8.4 baseline boundary_view vs post-assessment (reliability-aware)
    'baseline_boundary',   -- §5.3 baseline boundary_view snapshot, frozen at segment close (invariant 7)
    'diagnostic_segment_closed', -- invariant 7: the pinned baseline episode was closed when instruction began
    'milestone',           -- §7.5 depth_milestone_reached fact (event-only, no version bump)
    'depth_invitation',    -- §7.5 the ONE reviewed edge, served suggest_next (NEVER activates)
    'depth_accept',        -- §7.5 explicit learner accept: records intent (non-pinnable draft)
    'depth_decline')),     -- §7.5 explicit learner decline: logs the decision
  -- The P0 assessment administration this artifact is anchored to (NULL for
  -- milestone/invitation/accept/decline, which are goal/commitment-level facts).
  administration_id TEXT,
  payload_json TEXT NOT NULL,
  idempotency_key TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(run_id, seq),
  UNIQUE(run_id, idempotency_key)
);
CREATE INDEX idx_gpa_run ON golden_path_artifacts(run_id, seq);
CREATE INDEX idx_gpa_run_kind ON golden_path_artifacts(run_id, kind);
