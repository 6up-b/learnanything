---
title: "learnloop.substrate.replay"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/replay.py"
source_paths:
  - "src/learnloop/substrate/replay.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.replay module"
  - "src/learnloop/substrate/replay.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.replay`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps replay behavior inside its owning package, [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]]. Its public surface centers on `ReplayResult`, `RebuildResult`, `replay_learning_object`, `rebuild_derived_state`, `record_content_recalibration`.

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/replay.py](../../../../../../src/learnloop/substrate/replay.py) |
| Source lines | 536 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ReplayResult` ([source](../../../../../../src/learnloop/substrate/replay.py), line 15)
  - `as_dict(self) -> dict[str, object]` (line 20; public)
- `class RebuildResult` ([source](../../../../../../src/learnloop/substrate/replay.py), line 29)
  - `as_dict(self) -> dict[str, object]` (line 36; public)
- `replay_learning_object(vault: LoadedVault, repository: Repository, learning_object_id: str, *, error_attribution_overrides: dict[str, list[GradeAttribution]] | None=None, grader_identity_overrides: dict[str, tuple[str, str] | None] | None=None, project_canonical_state: bool=True) -> ReplayResult` ([source](../../../../../../src/learnloop/substrate/replay.py), line 268) — Rebuild attempt-derived state for one learning object from persisted grades.
- `rebuild_derived_state(vault: LoadedVault, repository: Repository, *, learning_object_ids: list[str] | None=None, clock: Clock | None=None, record_receipt: bool=True, project_canonical_state: bool=True) -> RebuildResult` ([source](../../../../../../src/learnloop/substrate/replay.py), line 420) — Replay all requested learning objects that have persisted attempts.
- `record_content_recalibration(vault: LoadedVault, repository: Repository, *, affected_learning_object_ids: list[str], clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/substrate/replay.py), line 483) — Stamp the recalibration boundary AT the content change, not after it.

## Internal implementation anchors

- `_restore_debug_audit_events(repository: Repository, attempt_id: str, prior_payload: Mapping[str, Any] | None) -> None` ([source](../../../../../../src/learnloop/substrate/replay.py), line 48) — Preserve decision-time firewall audit events across deterministic replay.
- `class _ClaimStream` ([source](../../../../../../src/learnloop/substrate/replay.py), line 106) — Claims replayed where they were applied live (LP-min (a); AD §5.5).
- `_order_key(row: Mapping[str, Any]) -> tuple[float, str]` ([source](../../../../../../src/learnloop/substrate/replay.py), line 237) — A row's place in the shared ``(created_at, id)`` order; an unparseable stamp sorts first.
- `_claim_position(claim: Mapping[str, Any], learning_object_id: str, attempt_keys: list[tuple[float, str]]) -> tuple[int, float, str] | None` ([source](../../../../../../src/learnloop/substrate/replay.py), line 244) — ``(attempts applied before the claim, created_at, id)``, or None for an unordered claim.
- `_parse_or_none(value: Any)` ([source](../../../../../../src/learnloop/substrate/replay.py), line 261)
- `_replay_learning_object(vault: LoadedVault, repository: Repository, learning_object_id: str, *, error_attribution_overrides: dict[str, list[GradeAttribution]] | None, grader_identity_overrides: dict[str, tuple[str, str] | None] | None, project_canonical_state: bool) -> ReplayResult` ([source](../../../../../../src/learnloop/substrate/replay.py), line 309)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `replay_learning_object`; statically calls `replay_learning_object`
- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `record_content_recalibration`; statically calls `record_content_recalibration`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `record_content_recalibration`; statically calls `record_content_recalibration`
- [[Reference/Modules/learnloop/curriculum/integration_backfill|learnloop.curriculum.integration_backfill]] — imports `replay_learning_object`; statically calls `replay_learning_object`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `rebuild_derived_state`; statically calls `rebuild_derived_state`
- [[Reference/Modules/learnloop/goals/exam_seeding|learnloop.goals.exam_seeding]] — imports `RebuildResult`, `rebuild_derived_state`; statically calls `rebuild_derived_state`
- [[Reference/Modules/learnloop/goals/goal_series|learnloop.goals.goal_series]] — imports `rebuild_derived_state`; statically calls `rebuild_derived_state`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `rebuild_derived_state`; statically calls `rebuild_derived_state`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AttemptResult`, `GradeAttribution`, `replay_existing_attempt`; calls `replay_existing_attempt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `FrozenClock`, `parse_utc`; calls `FrozenClock`, `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `update_misconception_posteriors_and_resolve`; calls `update_misconception_posteriors_and_resolve`
- [[Reference/Modules/learnloop/followup_serve/identity|learnloop.followup_serve.identity]] — imports `closed_probe_ids`; calls `closed_probe_ids`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `coverage_denominator_version`; calls `coverage_denominator_version`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `module`; calls `after_what_they_replaced`, `claim_fixes_live`, `covering_claims`, `initial_mastery_state_for_learning_object`, `reanchor_mastery_from_claim`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `projection_switches`; calls `projection_switches`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `CANONICAL_PROJECTION_VERSION`, `project_canonical_facet_state`; calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]], [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]], [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]], [[Reference/Modules/learnloop/curriculum/integration_backfill|learnloop.curriculum.integration_backfill]], [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/followup_fg1d_probe_shadow_helpers.py](../../../../../../tests/followup_fg1d_probe_shadow_helpers.py) — direct import
- [tests/test_anti_double_count.py](../../../../../../tests/test_anti_double_count.py) — direct import
  - `test_anti_double_count_replay_reproduces_identical_state`
- [tests/test_attempt_content_state_successor.py](../../../../../../tests/test_attempt_content_state_successor.py) — direct import
  - `test_a_same_version_rebuild_reproduces_the_live_row`
- [tests/test_capability_residual.py](../../../../../../tests/test_capability_residual.py) — direct import
  - `test_residual_activation_replay_deterministic`
- [tests/test_causal_activity_policy.py](../../../../../../tests/test_causal_activity_policy.py) — direct import
  - `test_rebuild_records_the_current_projection_version`
- [tests/test_causal_attribution_p1.py](../../../../../../tests/test_causal_attribution_p1.py) — direct import
  - `test_replay_preserves_immutable_receipt_chain`
- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_projection_version_names_the_open_cause_union`
- [tests/test_cold_retry_reschedule.py](../../../../../../tests/test_cold_retry_reschedule.py) — direct import
  - `test_replay_schedules_nothing_and_leaves_the_lane_as_live_left_it`
- [tests/test_coverage_denominator_boundary.py](../../../../../../tests/test_coverage_denominator_boundary.py) — direct import
  - `test_apply_writes_one_boundary_and_a_rerun_writes_none`
- [tests/test_diagnostic_probe_single_use.py](../../../../../../tests/test_diagnostic_probe_single_use.py) — direct import
  - `test_rebuild_derived_state_reproduces_the_deactivation`
- [tests/test_discrimination_profiles.py](../../../../../../tests/test_discrimination_profiles.py) — direct import
  - `test_the_telemetry_survives_a_derived_state_rebuild`
- [tests/test_doctor.py](../../../../../../tests/test_doctor.py) — direct import
  - `test_doctor_warns_when_attempt_log_needs_explicit_rebuild_marker`
- [tests/test_durable_promotion_arms.py](../../../../../../tests/test_durable_promotion_arms.py) — direct import
  - `test_replay_reproduces_the_same_belief_state`
- [tests/test_exam_seeding.py](../../../../../../tests/test_exam_seeding.py) — direct import
  - `test_rebuild_after_seeding_is_stable`
- [tests/test_facet_diagnostics_v03.py](../../../../../../tests/test_facet_diagnostics_v03.py) — direct import
  - `test_facet_uncertainty_rebuilds_from_attempts_and_grading_evidence`
- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f3_the_retry_retires_the_orphan_and_serves_its_own_question`
- [tests/test_followup_fg1c_r1_exposure_independence.py](../../../../../../tests/test_followup_fg1c_r1_exposure_independence.py) — direct import
  - `test_a_rebuild_keeps_the_answer_not_independent`
  - `test_the_panel_on_the_answers_own_feedback_doesnt_relabel_the_answer`
- [tests/test_followup_fg1d_probe_shadow.py](../../../../../../tests/test_followup_fg1d_probe_shadow.py) — direct import
  - `test_the_capability_cell_the_answer_feeds_agrees_with_a_rebuild_too`
- [tests/test_followup_journey.py](../../../../../../tests/test_followup_journey.py) — direct import
  - `test_a_lost_response_counts_as_burned_and_rebuild_keeps_the_one_submission`
  - `test_the_whole_journey_and_never_again`
- [tests/test_followup_single_use.py](../../../../../../tests/test_followup_single_use.py) — direct import
  - `test_retired_while_unused_stays_retired_after_sync_and_rebuild`
- [tests/test_help_fold_attach_successor.py](../../../../../../tests/test_help_fold_attach_successor.py) — direct import
  - `test_a_rebuild_changes_no_attempt_and_a_shadow_rebuild_is_zero`
- [tests/test_hypothesis_marks.py](../../../../../../tests/test_hypothesis_marks.py) — direct import
  - `test_a_rebuild_ignores_marks_and_keeps_them`
- [tests/test_ingest_instrument_gates.py](../../../../../../tests/test_ingest_instrument_gates.py) — direct import
  - `test_apply_stamps_coverage_boundary_and_later_rebuilds_add_nothing`
  - `test_record_content_recalibration_ignores_unknown_los`
- [tests/test_km2_write_path.py](../../../../../../tests/test_km2_write_path.py) — direct import
  - `test_golden_replay_identity_mvp07`
  - `test_rebuild_uses_presented_contract_after_live_target_change`
- [tests/test_km2b_consumer_rekey.py](../../../../../../tests/test_km2b_consumer_rekey.py) — direct import
  - `test_replay_identity_after_bridge_removal`
- [tests/test_learner_report_superseded.py](../../../../../../tests/test_learner_report_superseded.py) — direct import
  - `test_a_report_chain_longer_than_the_recursion_limit_replays_and_seeds`
- [tests/test_misconception_resolution.py](../../../../../../tests/test_misconception_resolution.py) — direct import
  - `test_replay_reproduces_auto_resolution`
- [tests/test_reader_digest_narrative.py](../../../../../../tests/test_reader_digest_narrative.py) — direct import
  - `test_rebuild_shadow_is_zero_with_a_narrative_present`
- [tests/test_reader_followups.py](../../../../../../tests/test_reader_followups.py) — direct import
  - `test_rebuild_shadow_is_zero_with_follow_ups_present`
- [tests/test_reader_followups_successor.py](../../../../../../tests/test_reader_followups_successor.py) — direct import
  - `test_replay_plans_nothing_and_a_shadow_rebuild_is_zero`
- [tests/test_rebuild_equivalence.py](../../../../../../tests/test_rebuild_equivalence.py) — direct import
  - `test_replay_still_closes_an_administered_diagnostic_probe_left_active`
- [tests/test_rebuild_equivalence_review.py](../../../../../../tests/test_rebuild_equivalence_review.py) — direct import
  - `test_a_retry_after_an_interrupted_direct_replay_keeps_the_lifecycle`
- [tests/test_rebuild_orchestrator.py](../../../../../../tests/test_rebuild_orchestrator.py) — direct import
  - `test_content_recalibration_replay_cannot_lose_its_ingest_lease_midway`
  - `test_golden_projection_survives_one_umbrella_rebuild_exactly_and_stale_rows_clear`
- [tests/test_replay.py](../../../../../../tests/test_replay.py) — direct import
  - `test_learning_object_replay_matches_live_state_and_is_idempotent`
  - `test_live_and_replay_drive_shared_apply_attempt_step`
  - `test_rebuild_derived_state_replays_attempt_logs`
  - `test_replay_preserves_targeted_error_attribution_facets`
- [tests/test_ro1_availability.py](../../../../../../tests/test_ro1_availability.py) — direct import
  - `test_exam_seeding_records_the_import_time_and_replay_keeps_it`
- [tests/test_source_append.py](../../../../../../tests/test_source_append.py) — direct import
  - `test_replay_identical_after_append_apply`
- [tests/test_source_set_synthesis.py](../../../../../../tests/test_source_set_synthesis.py) — direct import
  - `test_replay_identical_after_apply`
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_a_teach_back_grade_is_calibrated_and_replayed_under_its_graders_identity`
  - `test_a_teach_back_regraded_blind_keeps_the_blind_identity_through_rebuilds`
  - `test_finish_and_rebuild_replay_reproduce_derived_state`
  - `test_regrade_teach_back_attempt_restricts_to_graded_criteria`
  - `test_replay_teach_back_attempt_survives_practice_mode_change`
  - `test_teach_back_grade_takes_the_model_grade_observation_lane`
- [tests/test_teacher_te1_weight.py](../../../../../../tests/test_teacher_te1_weight.py) — direct import
  - `test_the_attempt_step_reads_the_recorded_mass_live_and_in_replay`
- [tests/test_voi_stopping.py](../../../../../../tests/test_voi_stopping.py) — direct import

## Modification guidance

- Change replay policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/replay.py](../../../../../../src/learnloop/substrate/replay.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
