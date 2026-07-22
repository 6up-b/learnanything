-- P2 LEARNING track (spec_p2_narrow_golden_path §7.1, §7.2, §12.3; design B.6):
-- the six-stage pattern ladder + its observable stage-transition contracts.
--
-- Migration numbering: highest applied on disk = 083 (diagnostic pack + triage).
-- 084/085 are the P2 learning + practice tracks (design B.6/B.7). Never edit an
-- applied migration.
--
-- This substrate is a versioned, REVIEWABLE ladder POLICY registered AS DATA (like
-- failure_triage_routes), NOT code, so an owner's edit to the ladder's rungs /
-- entry-exit contracts is auditable. The ladder STATE is NOT stored here -- it
-- lives on the run's append-only event stream
-- (golden_path_run_events.selected_activity_json), so there is no parallel state
-- machine (design B.6: "fold into run events"). Every instructional rung mints NO
-- certification (mints_certification = 0 on ALL rungs) -- certification is the
-- assessment purpose's alone (P1 InstructionalAdapter / §7.2).

-- Stable, versioned ladder policy. A material edit mints a SUCCESSOR
-- (policy_version + 1); a reviewed row is never mutated in place.
CREATE TABLE p2_ladder_policies (
  id TEXT PRIMARY KEY,
  policy_slug TEXT NOT NULL,
  policy_version INTEGER NOT NULL DEFAULT 1,
  schema_version INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('draft', 'reviewed', 'active', 'retired')),
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(policy_slug, policy_version)
);

-- The ordered rungs of one ladder policy, each declaring the §7.2 observable
-- entry/exit criteria, its immutable P1 pattern family + purpose, and whether it
-- records scaffold use / requires a cold unhinted response. `ordinal` groups
-- alternate rungs (example_study | example_comparison share an ordinal); the run
-- climbs by ordinal. `mints_certification` is 0 on every rung.
CREATE TABLE p2_ladder_stages (
  id TEXT PRIMARY KEY,
  policy_id TEXT NOT NULL REFERENCES p2_ladder_policies(id) ON DELETE CASCADE,
  stage_key TEXT NOT NULL,
  ordinal INTEGER NOT NULL,
  purpose TEXT NOT NULL CHECK (purpose IN ('instructional', 'practice')),
  run_state TEXT NOT NULL,
  pattern_family TEXT NOT NULL,
  entry_criteria TEXT NOT NULL,
  exit_criteria TEXT NOT NULL,
  mints_certification INTEGER NOT NULL DEFAULT 0,
  requires_cold INTEGER NOT NULL DEFAULT 0,
  records_scaffold INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  UNIQUE(policy_id, stage_key)
);
CREATE INDEX idx_p2_ladder_stages_policy ON p2_ladder_stages(policy_id, ordinal);

-- Seed the built-in ladder policy `ladder_v1` (§7.1). Registered as data: the
-- ladder is a heuristic instructional policy, owner-reviewable.
INSERT INTO p2_ladder_policies
  (id, policy_slug, policy_version, schema_version, status, content_hash, created_at)
VALUES
  ('plp_ladder_v1', 'ladder_v1', 1, 1, 'active', 'ladder_v1_builtin', '2026-07-19T00:00:00Z');

-- §7.1 rungs / §7.2 exit contracts. instructional rungs (ordinals 0-3) mint no
-- certification and never open a lapse; practice rungs (ordinals 4-6) require a
-- cold, unhinted response and still mint no unassisted certification.
INSERT INTO p2_ladder_stages
  (id, policy_id, stage_key, ordinal, purpose, run_state, pattern_family, entry_criteria, exit_criteria, mints_certification, requires_cold, records_scaffold, created_at)
VALUES
  ('pls_explanation', 'plp_ladder_v1', 'explanation', 0, 'instructional', 'instructing', 'example_study',
   'route: memory_lapse / unfamiliar / false_belief / task_interpretation, or source restoration needed',
   'learner acknowledges the explanation / source view (not a correctness claim)', 0, 0, 0, '2026-07-19T00:00:00Z'),
  ('pls_example_study', 'plp_ladder_v1', 'example_study', 1, 'instructional', 'instructing', 'example_study',
   'route: unfamiliar_or_missing_knowledge',
   'learner acknowledgement / structured comparison, not a correctness claim', 0, 0, 0, '2026-07-19T00:00:00Z'),
  ('pls_example_comparison', 'plp_ladder_v1', 'example_comparison', 1, 'instructional', 'instructing', 'example_comparison',
   'route: schema_or_conceptual_hole / task_interpretation',
   'structured comparison recorded, not a correctness claim', 0, 0, 0, '2026-07-19T00:00:00Z'),
  ('pls_example_completion', 'plp_ladder_v1', 'example_completion', 2, 'instructional', 'completing', 'example_completion',
   'route: procedure_execution',
   'required steps completed with scaffold use recorded; does not certify independence', 0, 0, 1, '2026-07-19T00:00:00Z'),
  ('pls_setup_only', 'plp_ladder_v1', 'setup_only', 3, 'instructional', 'instructing', 'setup_only',
   'route: method_selection',
   'method / subgoals selected without executing the whole answer', 0, 0, 0, '2026-07-19T00:00:00Z'),
  ('pls_move_spotting', 'plp_ladder_v1', 'move_spotting', 3, 'instructional', 'instructing', 'move_spotting',
   'route: method_selection (across contexts)',
   'correct moves spotted across distinct contexts', 0, 0, 0, '2026-07-19T00:00:00Z'),
  ('pls_independent_repair', 'plp_ladder_v1', 'independent_repair', 4, 'practice', 'practicing', 'independent_repair',
   'a prior instructional rung has exited',
   'cold, unhinted response on a non-hard-colliding surface', 0, 1, 0, '2026-07-19T00:00:00Z'),
  ('pls_whole_task_integration', 'plp_ladder_v1', 'whole_task_integration', 5, 'practice', 'integrating', 'whole_task_integration',
   'route: coordination_or_integration, or after independent repair',
   'blueprint integration criteria on a fresh whole-task surface', 0, 1, 0, '2026-07-19T00:00:00Z'),
  ('pls_delayed_independent_practice', 'plp_ladder_v1', 'delayed_independent_practice', 6, 'practice', 'practicing', 'independent_repair',
   'independent repair / integration demonstrated',
   'delayed independent fresh practice, linked to the original lapse', 0, 1, 0, '2026-07-19T00:00:00Z');
