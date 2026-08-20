---
title: "learnloop.scheduling.scheduler"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/scheduler.py"
source_paths:
  - "src/learnloop/scheduling/scheduler.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.scheduler module"
  - "src/learnloop/scheduling/scheduler.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.scheduler`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps scheduler behavior inside its owning package, [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]]. Its public surface centers on `SchedulerSession`, `ScheduledItem`, `build_due_queue`, `deferred_cold_followups`, `explain_practice_item`, `dominant_scheduler_reason`.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py) |
| Source lines | 1709 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class SchedulerSession` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 44)
- `class ScheduledItem` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 51)
- `build_due_queue(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None, session: SchedulerSession | None=None, limit: int | None=None, persist_explanations: bool=True) -> list[ScheduledItem]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 71)
- `deferred_cold_followups(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 814) — Live cold tasks currently held back because their answer was shown.
- `explain_practice_item(vault: LoadedVault, repository: Repository, practice_item_id: str) -> ScheduledItem | None` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1275)
- `dominant_scheduler_reason(components: dict[str, float], config: LearnLoopConfig) -> str` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1316) — Stable learner-facing reason from the same weighted ranking terms.

### Module constants

- `FOLLOWUP_REASONS` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 640)
- `_INTERVENTION_FOLLOWUP_KINDS` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 648)
- `REPAIR_JOURNEY_TASK_KINDS` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 667)
- `_COLD_DEFERRAL_REASON` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 887)
- `_TEACH_BACK_PRIORITY_FLOOR` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 1060)
- `_REQUESTED_PRIORITY_FLOOR` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 1064)

## Internal implementation anchors

- `_defer_revealed_cold_followups(vault: LoadedVault, repository: Repository, pending_followups: list[dict[str, str]], *, clock: Clock | None=None, persist: bool=True) -> tuple[list[dict[str, str]], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 670) — Hold back due cold tasks whose answer has been revealed since creation.
- `_merge_cold_deferral_explanations(vault: LoadedVault, explanations: list[dict[str, Any]], deferrals: list[dict[str, Any]], readiness_factor: float | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 890) — Mark every deferred cold task in the slate, exactly once per item.
- `_deferral_components(deferral: Mapping[str, Any]) -> dict[str, float]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 944)
- `_deferral_reasons(deferral: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 951)
- `_insert_pending_followups(vault: LoadedVault, queue: list[ScheduledItem], pending_followups: list[dict[str, str]], readiness_factor: float | None, *, item_states: dict[str, PracticeItemState] | None=None) -> list[ScheduledItem]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 955)
- `_apply_contrast_pair_order(vault: LoadedVault, repository: Repository, queue: list[ScheduledItem], session: SchedulerSession, *, clock: Clock | None=None) -> list[ScheduledItem]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1067) — Meas §3.A4: randomize which member of a contrast pair is served first.
- `_rotate_same_day_frontier_repeats(queue: list[ScheduledItem], item_states: dict[str, PracticeItemState], now: datetime) -> list[ScheduledItem]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1147) — Within goal-frontier queue slots, serve items not yet attempted today first.
- `_enforce_teach_back_session_cap(queue: list[ScheduledItem], cap: int) -> list[ScheduledItem]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1184) — Keep at most ``cap`` teach_back items per built queue (config ``teach_back.session_cap``), preserving order for everything else.
- `_load_episode_context(vault: LoadedVault, repository: Repository, episode, cache: dict[str, tuple[HypothesisSet, dict[str, float], float] | None]) -> tuple[HypothesisSet, dict[str, float], float] | None` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1199)
- `_load_episode_eligible(vault: LoadedVault, repository: Repository, episode, context: tuple[HypothesisSet, dict[str, float], float], cache: dict[str, dict[str, EligibleInstrument]]) -> dict[str, EligibleInstrument]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1222) — The episode's eligible instruments (with §7.4 predictive components), computed once per episode per queue build and keyed by item id.
- `_record_probe_elicitation(repository: Repository, queue: list[ScheduledItem], probe_item_ids: dict[str, str], session: SchedulerSession, *, entropy_before: dict[str, float] | None=None, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1241)
- `_practice_information(item, learning_object, mastery, config: LearnLoopConfig) -> float` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1283) — Display-only measurement value of one ordinary attempt (never selection).
- `_priority(components: dict[str, float], config: LearnLoopConfig) -> float` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1307)
- `_selection_propensities(queue: list[ScheduledItem], session: SchedulerSession, config: LearnLoopConfig) -> dict[str, float]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1334) — ``P(item is served as the top candidate | slate)`` under seeded exploration.
- `_apply_seeded_exploration(queue: list[ScheduledItem], session: SchedulerSession, config: LearnLoopConfig, now: datetime) -> list[ScheduledItem]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1386)
- `_stable_fraction(label: str, session_id: str, now: datetime, candidate_ids: list[str]) -> float` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1434)
- `_intent_for_item(item: PracticeItem, *, in_probe: bool, components: dict[str, float]) -> SchedulerIntent` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1440)
- `_readiness_factor(session: SchedulerSession, config: LearnLoopConfig) -> float | None` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1464)
- `_session_context(session: SchedulerSession, *, short_session: bool, readiness_factor: float | None, shadow_intent: dict[str, object] | None=None) -> dict[str, object]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1484)
- `_scheduler_config_snapshot(config: LearnLoopConfig) -> dict[str, object]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1504)
- `_forgetting_risk(state: PracticeItemState | None, now: datetime, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> float` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1521)
- `_goal_frontier(vault: LoadedVault, item: PracticeItem, entry) -> float` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1538) — Fraction of the item's evidence facets on its LO's goal frontier, scaled by goal priority.
- `_apply_goal_quota(queue: list[ScheduledItem], floor: float) -> list[ScheduledItem]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1556) — Reorder-only greedy quota guaranteeing a floor share of goal-frontier items.
- `_apply_requested_floor(queue: list[ScheduledItem], requested_item_ids: list[str], cap: int) -> list[ScheduledItem]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1597) — Prefix-floor reorder guaranteeing requested items a front slot (spec §4a).
- `_recent_error(errors: list[ActiveErrorEvent], now: datetime) -> float` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1631)
- `_errors_by_learning_object(errors: list[ActiveErrorEvent]) -> dict[str, list[ActiveErrorEvent]]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1642) — Active LEARNER errors per LO.
- `_plain_english(item: PracticeItem, components: dict[str, float]) -> list[str]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1663)
- `_explanation_payload(item: ScheduledItem, *, selected: bool=True, selection_propensity: float | None=None) -> dict[str, object]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1685)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `SchedulerSession`, `build_due_queue`, `explain_practice_item`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `build_due_queue`; statically calls `build_due_queue`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `SchedulerSession`, `build_due_queue`; statically calls `SchedulerSession`, `build_due_queue`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `ScheduledItem`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `ScheduledItem`
- [[Reference/Modules/learnloop/tui/screens/start|learnloop.tui.screens.start]] — imports `SchedulerSession`; statically calls `SchedulerSession`
- [[Reference/Modules/learnloop/tui/screens/today|learnloop.tui.screens.today]] — imports `ScheduledItem`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `ScheduledItem`, `SchedulerSession`, `build_due_queue`; statically calls `SchedulerSession`, `build_due_queue`
- [[Reference/Modules/learnloop_sidecar/handlers/facets|learnloop_sidecar.handlers.facets]] — imports `build_due_queue`; statically calls `build_due_queue`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `build_due_queue`; statically calls `build_due_queue`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `SchedulerSession`, `build_due_queue`; statically calls `SchedulerSession`, `build_due_queue`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `SchedulerSession`, `build_due_queue`, `deferred_cold_followups`, `explain_practice_item`; statically calls `SchedulerSession`, `build_due_queue`, `deferred_cold_followups`, `explain_practice_item`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `FOLLOWUP_REASONS`, `ScheduledItem`, `dominant_scheduler_reason`, `explain_practice_item`; statically calls `dominant_scheduler_reason`, `explain_practice_item`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempt_types|learnloop.attempt_types]] — imports `DEFAULT_ATTEMPT_TYPE`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `COLD_FOLLOWUP_TASK_KINDS`
- [[Reference/Modules/learnloop/attempts/evidence|learnloop.attempts.evidence]] — imports `attempt_evidence_mass`; calls `attempt_evidence_mass`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ActiveErrorEvent`, `PracticeItemState`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] — imports `calibration_cap_lifted`, `routine_planner_shadow`; calls `calibration_cap_lifted`, `routine_planner_shadow`
- [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]] — imports `apply_serving_decisions`, `plan_contrast_pair_serving`, `record_contrast_pair_servings`; calls `apply_serving_decisions`, `plan_contrast_pair_serving`, `record_contrast_pair_servings`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]] — imports `reconcile_diagnostic_surface_needs`, `reconcile_empty_probe_pools`; calls `reconcile_diagnostic_surface_needs`, `reconcile_empty_probe_pools`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy_map|learnloop.diagnosis.error_taxonomy_map]] — imports `ASSESSMENT_SIDE_ERROR_TYPES`, `map_legacy_error_type`; calls `map_legacy_error_type`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `EligibleInstrument`, `EpisodePosterior`, `administered_surface_exclusions`, `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`, `presentation_commit_payload`, `probe_serving_block_reason`; calls `administered_surface_exclusions`, `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`, `presentation_commit_payload`, `probe_serving_block_reason`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `HypothesisSet`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `COLD_RETRIEVAL_DELAY`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `reserved_item_ids`; calls `reserved_item_ids`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `resolve_head`; calls `resolve_head`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `build_goal_frontier`; calls `build_goal_frontier`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `facet_states_by_lo`; calls `facet_states_by_lo`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `resolve_item_irt_params`; calls `resolve_item_irt_params`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `familiarity_discount`, `familiarity_discount_from_attempts`, `resolve_coverage`; calls `familiarity_discount`, `familiarity_discount_from_attempts`, `resolve_coverage`
- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `clamp`; calls `clamp`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_fsrs_weights`; calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/scheduling/controller_ownership|learnloop.scheduling.controller_ownership]] — imports `module`; calls `staged_owned_practice_item_ids`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `FSRS6_DEFAULT_WEIGHTS`, `forgetting_curve`; calls `forgetting_curve`
- [[Reference/Modules/learnloop/scheduling/intent_planner|learnloop.scheduling.intent_planner]] — imports `shadow_intent_plan`; calls `shadow_intent_plan`
- [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]] — imports `SchedulerIntent`, `score_selection_reward`; calls `score_selection_reward`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_reason`; calls `unservable_reason`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `hashlib`, `logging`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]], [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]], [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]], [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] and 8 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_attempts.py](../../../../../../tests/test_attempts.py) — direct import
  - `test_attempt_links_to_scheduler_slate_and_later_retention_label`
- [tests/test_cli_generate_practice.py](../../../../../../tests/test_cli_generate_practice.py) — direct import
  - `test_accepting_diagnostic_proposal_queues_today_followup`
- [tests/test_cold_start_revision.py](../../../../../../tests/test_cold_start_revision.py) — direct import
  - `test_scheduler_excludes_assessment_side_errors`
- [tests/test_contrast_pairs.py](../../../../../../tests/test_contrast_pairs.py) — direct import
  - `test_the_scheduler_records_a_serving_for_a_real_session`
- [tests/test_controller_cutover.py](../../../../../../tests/test_controller_cutover.py) — direct import
- [tests/test_controller_ownership.py](../../../../../../tests/test_controller_ownership.py) — direct import
  - `test_legacy_scheduler_excludes_staged_owned_items`
  - `test_rollback_is_all_or_nothing_on_mid_failure`
  - `test_rollback_returns_to_legacy_and_restores_queue`
- [tests/test_controller_snapshot.py](../../../../../../tests/test_controller_snapshot.py) — direct import
- [tests/test_diagnostic_probe_freshness.py](../../../../../../tests/test_diagnostic_probe_freshness.py) — direct import
  - `test_diagnostic_probe_is_servable_when_injected_by_id_via_followup_task`
  - `test_probe_selection_hard_excludes_an_already_seen_surface_group`
- [tests/test_diagnostic_probe_single_use.py](../../../../../../tests/test_diagnostic_probe_single_use.py) — direct import
- [tests/test_e2e_codex_mock.py](../../../../../../tests/test_e2e_codex_mock.py) — direct import
  - `test_codex_mocked_end_to_end`
- [tests/test_evaluation.py](../../../../../../tests/test_evaluation.py) — direct import
  - `test_report_on_real_session_flow`
- [tests/test_exam_pool.py](../../../../../../tests/test_exam_pool.py) — direct import
  - `test_scheduler_skips_reserved_items`
- [tests/test_followup_diagnostic_selection.py](../../../../../../tests/test_followup_diagnostic_selection.py) — direct import
  - `test_repair_journey_task_with_administered_diagnostic_still_serves`
  - `test_stale_generic_task_with_administered_diagnostic_is_refused`
- [tests/test_followups.py](../../../../../../tests/test_followups.py) — direct import
  - `test_manual_override_forces_followup_when_gate_silent`
  - `test_negative_surprise_followup_stops_forcing_after_followup_attempt`
  - `test_negative_surprise_inserts_followup_when_item_exists`
- [tests/test_goal_frontier.py](../../../../../../tests/test_goal_frontier.py) — direct import
  - `test_cold_start_lo_on_frontier_is_schedulable`
  - `test_goal_quota_guarantees_floor_share_at_top_of_queue`
  - `test_known_gap_and_uncertain_facets_are_both_on_frontier`
  - `test_no_active_goals_means_no_goal_frontier`
  - `test_unexamined_facet_on_goal_frontier_scales_by_goal_priority`
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_a_delayed_followup_can_serve_an_instrument`
- [tests/test_intent_planner.py](../../../../../../tests/test_intent_planner.py) — direct import
- [tests/test_item_authoring.py](../../../../../../tests/test_item_authoring.py) — direct import
  - `test_retire_item_stops_all_serving`
- [tests/test_km5_sim_gates.py](../../../../../../tests/test_km5_sim_gates.py) — direct import
  - `test_shadow_intent_logs_practice_integration_at_the_right_moment`
- [tests/test_large_practice_flow.py](../../../../../../tests/test_large_practice_flow.py) — direct import
  - `test_many_open_text_practice_items_schedule_and_record_attempt`
- [tests/test_practice_information.py](../../../../../../tests/test_practice_information.py) — direct import
  - `test_boundary_item_maximizes_information`
  - `test_claim_seeded_theta_shifts_information`
  - `test_practice_information_never_reaches_priority`
- [tests/test_probe_episodes.py](../../../../../../tests/test_probe_episodes.py) — direct import
  - `test_pending_items_episode_keeps_lo_schedulable_with_belief_updates`
  - `test_scheduler_slate_atomically_commits_its_selected_probe_presentation`
- [tests/test_probe_pool_empty.py](../../../../../../tests/test_probe_pool_empty.py) — direct import
  - `test_scheduler_build_raises_the_notice_without_a_provider`
- [tests/test_probe_remint.py](../../../../../../tests/test_probe_remint.py) — direct import
- [tests/test_probe_surface_mint.py](../../../../../../tests/test_probe_surface_mint.py) — direct import
  - `test_minted_surface_serves_through_the_probe_branch_and_is_single_use`
- [tests/test_reentry_short_session.py](../../../../../../tests/test_reentry_short_session.py) — direct import
- [tests/test_remediation_cold_retry.py](../../../../../../tests/test_remediation_cold_retry.py) — direct import
  - `test_only_the_cold_lane_is_deferred_by_a_reveal`
- [tests/test_scheduler.py](../../../../../../tests/test_scheduler.py) — direct import
  - `test_a_clean_cold_task_is_served_as_the_cold_lane`
  - `test_a_revealed_cold_task_is_withheld_and_says_so_in_the_slate`
  - `test_a_side_effect_free_build_withholds_without_rescheduling`
  - `test_frontier_items_attempted_today_rotate_behind_fresh_ones`
  - `test_inserted_followup_records_its_lane`
  - `test_ordinary_due_pick_carries_no_followup_kind`
  - `test_rotation_leaves_non_frontier_slots_untouched`
  - `test_rotation_no_op_when_all_frontier_items_attempted_today`
  - `test_scheduler_bulk_loads_item_quality_once`
  - `test_scheduler_candidate_logs_are_retained_per_configured_limit`
  - `test_scheduler_orders_eligible_items_by_selection_reward_before_id`
  - `test_scheduler_persists_bounded_reward_debug_and_rejected_candidates`
  - `test_scheduler_persists_selection_propensity_and_exploration_flag`
  - `test_scheduler_scores_due_goal_item`
  - `test_scheduler_selects_item_on_weak_canonical_facet_boundary`
  - `test_selection_propensities_epsilon_split_over_near_ties`
  - `test_selection_propensities_greedy_when_disabled_or_singleton_or_probe`
  - `test_selection_propensities_window_excludes_far_candidates`
  - `test_unrecognised_followup_action_reports_the_lane_it_lands_on`
- [tests/test_scheduler_golden.py](../../../../../../tests/test_scheduler_golden.py) — direct import
  - `test_scheduler_forgetting_risk_zero_before_due_date`
  - `test_scheduler_goal_frontier_follows_explicit_scope_only`
  - `test_scheduler_recent_error_decays_by_exp_days_over_seven`
  - `test_scheduler_ties_by_lowest_practice_item_id_and_filters_inactive`
- [tests/test_scheduler_probe_eig.py](../../../../../../tests/test_scheduler_probe_eig.py) — direct import
  - `test_probe_eig_included_only_for_in_progress_probe`
  - `test_probe_eig_persisted_in_scheduler_explanation`
  - `test_probe_eig_uses_prospective_familiarity_discount`
  - `test_readiness_factor_is_persisted_without_changing_priority`
  - `test_scheduler_explanations_persist_only_for_named_sessions`
  - `test_short_session_keeps_probe_eig_when_probe_is_only_reason`
  - `test_short_session_suppresses_probe_eig`
- [tests/test_scheduler_requested_floor.py](../../../../../../tests/test_scheduler_requested_floor.py) — direct import
  - `test_cap_limits_number_pulled`
  - `test_cap_two_pulls_both_in_requested_order`
  - `test_ineligible_requested_item_is_never_forced_in`
  - `test_noop_when_cap_zero_or_nothing_requested`
  - `test_requested_floor_honored_before_limit_slice`
  - `test_requested_item_pulled_to_front`
  - `test_requested_item_surfaces_and_respects_gates`
  - `test_stateless_requested_item_survives_eligibility`
- [tests/test_sidecar_queue_serialization.py](../../../../../../tests/test_sidecar_queue_serialization.py) — direct import
  - `test_queue_serialization_bulk_loads_state_once`
- [tests/test_sidecar_serializer_snapshot.py](../../../../../../tests/test_sidecar_serializer_snapshot.py) — direct import
  - `test_queue_practice_and_reader_wire_snapshots`
- [tests/test_staged_policy.py](../../../../../../tests/test_staged_policy.py) — direct import
- [tests/test_staged_policy_evsi.py](../../../../../../tests/test_staged_policy_evsi.py) — direct import
- [tests/test_state_sync.py](../../../../../../tests/test_state_sync.py) — direct import
  - `test_state_sync_enters_probe_for_new_active_goal_learning_object`
  - `test_state_sync_enters_probe_for_new_active_learning_object_without_goal`
  - `test_state_sync_enters_probe_when_practice_item_arrives_after_learning_object`
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_scheduler_caps_teach_back_items_per_queue`
  - `test_teach_back_stays_weakly_schedulable_on_solid_knowledge`
- [tests/test_tui_today.py](../../../../../../tests/test_tui_today.py) — direct import
  - `test_today_queue_matches_scheduler_and_opens_practice`

## Modification guidance

- Change scheduler policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
