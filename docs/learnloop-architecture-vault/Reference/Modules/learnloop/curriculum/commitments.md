---
title: "learnloop.curriculum.commitments"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/commitments.py"
source_paths:
  - "src/learnloop/curriculum/commitments.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.curriculum"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Build a Study Map"
aliases:
  - "learnloop.curriculum.commitments module"
  - "src/learnloop/curriculum/commitments.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.commitments`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.commitments` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: P1 step 1 -- durable learner commitments (spec_p1_shared_substrate §3.1, §3.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/commitments.py](../../../../../../src/learnloop/curriculum/commitments.py) |
| Source lines | 868 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class PassiveActionCannotCommit(Exception)` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 72) — A non-commit-class action tried to create a commitment (invariant 4, §9.1).
  - `__init__(self, action: str)` (line 75; internal)
- `class InvalidTarget(Exception)` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 83) — A commitment target used an unknown target kind or role.
- `class UnknownCommitment(Exception)` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 87)
  - `__init__(self, commitment_id: str)` (line 88; internal)
- `class EnvelopeWideningRejected(Exception)` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 93) — A shrink/change tried to WIDEN the depth envelope (§10.2, F4).
  - `__init__(self, dimension: str)` (line 101; internal)
- `envelope_widening_dimension(new_bounds: Mapping[str, Any], current_bounds: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 148) — Return the first bounds dimension on which ``new_bounds`` widens ``current_bounds``, or ``None`` if ``new_bounds`` is a subset (a shrink).
- `class CommitmentTarget` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 165)
  - `normalized(self) -> dict[str, Any]` (line 172; public)
- `class CommitmentVersion` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 179)
  - `as_dict(self) -> dict[str, Any]` (line 196; public)
- `class Commitment` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 201)
  - `as_dict(self) -> dict[str, Any]` (line 210; public)
- `target_set_hash(targets: Sequence[CommitmentTarget]) -> str` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 246) — Order-independent identity of the target set (§3.1 idempotency key).
- `create_commitment(repository: Repository, *, action: str, intent_text: str, targets: Sequence[Mapping[str, Any] | CommitmentTarget], depth_preset: str, interpretation_text: str | None=None, client_idempotency_key: str | None=None, goal_id: str | None=None, author: str='learner', learner_id: str='local', attention_bounds: Mapping[str, Any] | None=None, due_hint: str | None=None, hiatus_hint: str | None=None, reason: str | None=None, provenance: Mapping[str, Any] | None=None, clock: Clock | None=None) -> Commitment` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 300) — Create a durable commitment from an explicit commit-class action (§3.1).
- `append_commitment_version(repository: Repository, *, commitment_id: str, targets: Sequence[Mapping[str, Any] | CommitmentTarget] | None=None, intent_text: str | None=None, interpretation_text: str | None=None, goal_id: str | None=None, depth_preset: str | None=None, change_reason: str, author: str='learner', extra_events: Sequence[Mapping[str, Any]]=(), clock: Clock | None=None) -> CommitmentVersion` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 414) — Append an immutable successor version.
- `add_target(repository: Repository, *, commitment_id: str, target: Mapping[str, Any] | CommitmentTarget, change_reason: str='target_added', author: str='learner', clock: Clock | None=None) -> CommitmentVersion` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 473)
- `change_depth_policy(repository: Repository, *, commitment_id: str, policy: str, body: Mapping[str, Any] | None=None, change_reason: str='depth_policy_changed', author: str='learner', clock: Clock | None=None) -> CommitmentVersion` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 500)
- `change_depth_envelope(repository: Repository, *, commitment_id: str, bounds: Mapping[str, Any], reviewed_edges: Sequence[Mapping[str, Any]]=(), change_reason: str='depth_envelope_changed', author: str='learner', allow_widen: bool=False, clock: Clock | None=None) -> CommitmentVersion` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 540)
- `change_disposition(repository: Repository, *, commitment_id: str, disposition: str, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 639) — Append a ``disposition_changed`` event only; disposition is a projection over events (§3.1), so no version bump.
- `pause(repository: Repository, *, commitment_id: str, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 662)
- `resume(repository: Repository, *, commitment_id: str, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 671)
- `retire(repository: Repository, *, commitment_id: str, detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 680) — Append a ``retired`` event.
- `satisfy_single_check(repository: Repository, *, commitment_id: str, administration_id: str | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 699) — One eligible delayed cold administration satisfies a ``test_me_later`` commitment (§3.1): ``one_check_pending`` -> ``satisfied``, never an open-ended review obligation.
- `record_milestone_reached(repository: Repository, *, commitment_id: str, milestone_slug: str, detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 720) — Append ``depth_milestone_reached``: an achievement fact over the existing authored envelope.
- `resolve_disposition(repository: Repository, commitment_id: str, *, before: str | None=None) -> str` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 749) — Fold ``commitment_events`` to one disposition (§3.1).
- `resolve_head(repository: Repository, commitment_id: str) -> CommitmentVersion` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 784)

### Module constants

- `COMMIT_ACTIONS` ([src/learnloop/curriculum/commitments.py](../../../../../../src/learnloop/curriculum/commitments.py), line 35)
- `DEPTH_PRESETS` ([src/learnloop/curriculum/commitments.py](../../../../../../src/learnloop/curriculum/commitments.py), line 39)
- `TARGET_KINDS` ([src/learnloop/curriculum/commitments.py](../../../../../../src/learnloop/curriculum/commitments.py), line 43)
- `DISPOSITIONS` ([src/learnloop/curriculum/commitments.py](../../../../../../src/learnloop/curriculum/commitments.py), line 53)
- `_ACTION_DEFAULT_POLICY` ([src/learnloop/curriculum/commitments.py](../../../../../../src/learnloop/curriculum/commitments.py), line 61)
- `DEPTH_ENVELOPE_SCHEMA_VERSION` ([src/learnloop/curriculum/commitments.py](../../../../../../src/learnloop/curriculum/commitments.py), line 68)
- `DEPTH_POLICY_SCHEMA_VERSION` ([src/learnloop/curriculum/commitments.py](../../../../../../src/learnloop/curriculum/commitments.py), line 69)

## Internal implementation anchors

- `_bounds_value_is_subset(new_val: Any, old_val: Any) -> bool` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 109) — Is ``new_val`` provably contained in ``old_val`` for one bounds dimension?
- `_coerce_targets(targets: Sequence[Mapping[str, Any] | CommitmentTarget]) -> list[CommitmentTarget]` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 218)
- `_version_hash(fields: Mapping[str, Any], targets: Sequence[CommitmentTarget], *, predecessor_version_id: str | None, version: int) -> str` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 252) — Chain-aware content hash: identity of this version's content plus its position in the append-only chain.
- `_default_depth_body(action: str, preset: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 274)
- `_default_envelope_body(preset: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 284)
- `_target_row(t: CommitmentTarget) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 400)
- `_append_depth_version(repository: Repository, *, head: CommitmentVersion, depth_policy_version_id: str | None, depth_envelope_version_id: str | None, event_kind: str, detail: Mapping[str, Any], change_reason: str, author: str, clock: Clock | None) -> CommitmentVersion` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 588)
- `_loads(value: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 796)
- `_current_envelope_bounds(repository: Repository, envelope_version_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 804) — Bounds of the head's active depth envelope (empty when unset).
- `_version_from_row(row: Mapping[str, Any], targets: Sequence[Mapping[str, Any]]) -> CommitmentVersion` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 816)
- `_require_head(repository: Repository, commitment_id: str) -> CommitmentVersion` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 845)
- `_load_commitment(repository: Repository, commitment_id: str, *, created: bool, merge_candidate: bool=False) -> Commitment` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 853)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/curriculum/commitment_arcs|learnloop.curriculum.commitment_arcs]] — imports `module`; statically calls `change_depth_envelope`, `change_depth_policy`, `pause`, `record_milestone_reached`, `resolve_disposition`, `resolve_head`
- [[Reference/Modules/learnloop/curriculum/depth_edge_authoring|learnloop.curriculum.depth_edge_authoring]] — imports `module`; statically calls `change_depth_envelope`, `resolve_head`
- [[Reference/Modules/learnloop/curriculum/depth_rungs|learnloop.curriculum.depth_rungs]] — imports `module`; statically calls `resolve_head`
- [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]] — imports `module`; statically calls `resolve_head`
- [[Reference/Modules/learnloop/curriculum/golden_path_confirm|learnloop.curriculum.golden_path_confirm]] — imports `module`; statically calls `_coerce_targets`, `_default_depth_body`, `_default_envelope_body`, `_target_row`, `_version_hash`, `target_set_hash`
- [[Reference/Modules/learnloop/curriculum/golden_path_restoration|learnloop.curriculum.golden_path_restoration]] — imports `module`; statically calls `record_milestone_reached`
- [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]] — imports `module`; statically calls `create_commitment`, `resolve_disposition`
- [[Reference/Modules/learnloop/daily_plan/router_reader|learnloop.daily_plan.router_reader]] — imports `module`; statically calls `resolve_disposition`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `module`; statically calls `create_commitment`, `resolve_disposition`, `retire`
- [[Reference/Modules/learnloop/intent/checks|learnloop.intent.checks]] — imports `module`; statically calls `resolve_disposition`, `satisfy_single_check`
- [[Reference/Modules/learnloop/intent/control|learnloop.intent.control]] — imports `module`; statically calls `append_commitment_version`, `change_disposition`, `create_commitment`, `resolve_head`
- [[Reference/Modules/learnloop/intent/deadline|learnloop.intent.deadline]] — imports `module`; statically calls `append_commitment_version`
- [[Reference/Modules/learnloop/reader/active_reading|learnloop.reader.active_reading]] — imports `module`; statically calls `create_commitment`, `resolve_disposition`, `retire`
- [[Reference/Modules/learnloop/reader/reader_authoring|learnloop.reader.reader_authoring]] — imports `module`; statically calls `add_target`, `change_depth_envelope`, `change_depth_policy`, `create_commitment`, `resolve_head`, `retire`
- [[Reference/Modules/learnloop/reader/reader_capture|learnloop.reader.reader_capture]] — imports `module`; statically calls `create_commitment`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; statically calls `create_commitment`
- [[Reference/Modules/learnloop/reader/reader_intent|learnloop.reader.reader_intent]] — imports `module`; statically calls `resolve_disposition`, `retire`
- [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]] — imports `module`; statically calls `resolve_disposition`
- [[Reference/Modules/learnloop/scheduling/controller_cutover|learnloop.scheduling.controller_cutover]] — imports `module`; statically calls `resolve_head`
- [[Reference/Modules/learnloop/scheduling/controller_ownership|learnloop.scheduling.controller_ownership]] — imports `module`; statically calls `resolve_head`
- [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]] — imports `module`; statically calls `resolve_disposition`, `resolve_head`
- [[Reference/Modules/learnloop/scheduling/state_signals|learnloop.scheduling.state_signals]] — imports `module`; statically calls `resolve_head`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `module`; statically calls `create_commitment`, `resolve_disposition`
- [[Reference/Modules/learnloop/teacher/delayed|learnloop.teacher.delayed]] — imports `module`; statically calls `create_commitment`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] — imports `module`; statically calls `resolve_disposition`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`, `canonical_json`; calls `canonical_hash`, `canonical_json`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/curriculum/commitment_arcs|learnloop.curriculum.commitment_arcs]], [[Reference/Modules/learnloop/curriculum/depth_edge_authoring|learnloop.curriculum.depth_edge_authoring]], [[Reference/Modules/learnloop/curriculum/depth_rungs|learnloop.curriculum.depth_rungs]], [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]], [[Reference/Modules/learnloop/curriculum/golden_path_confirm|learnloop.curriculum.golden_path_confirm]] and 21 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_commitment_arcs.py](../../../../../../tests/test_commitment_arcs.py) — direct import
  - `test_arc_pins_depth_and_maps_stages`
  - `test_shrink_envelope_rejects_widening`
- [tests/test_commitments.py](../../../../../../tests/test_commitments.py) — direct import
  - `test_depth_envelope_change_forces_version_bump`
  - `test_depth_policy_change_forces_version_bump_and_typed_event`
  - `test_different_target_set_creates_distinct_commitment`
  - `test_milestone_reached_does_not_bump_version`
  - `test_missing_key_returns_merge_candidate_not_silent_merge`
  - `test_noop_depth_envelope_change_short_circuits`
  - `test_noop_depth_policy_change_short_circuits`
  - `test_passive_action_cannot_create_commitment`
  - `test_pause_resume_retire_disposition`
  - `test_reference_only_disposition_change`
  - `test_test_me_later_starts_pending_then_satisfied`
  - `test_version_append_preserves_prior_bytes`
- [tests/test_controller_ownership.py](../../../../../../tests/test_controller_ownership.py) — direct import
  - `test_rollback_is_all_or_nothing_on_mid_failure`
- [tests/test_cross_seam_exposure.py](../../../../../../tests/test_cross_seam_exposure.py) — direct import
  - `test_stale_ownership_still_prevents_double_administration`
- [tests/test_curriculum_c1_landing.py](../../../../../../tests/test_curriculum_c1_landing.py) — direct import
- [tests/test_daily_loop_reader_authored_practice.py](../../../../../../tests/test_daily_loop_reader_authored_practice.py) — direct import
  - `test_written_question_becomes_practice_the_scheduler_serves`
- [tests/test_daily_loop_reference_adoption.py](../../../../../../tests/test_daily_loop_reference_adoption.py) — direct import
  - `test_a_retired_reference_question_is_never_adopted`
  - `test_adoption_kill_switch_restores_baseline_and_keeps_adopted_cards`
  - `test_reference_question_becomes_practice_once_an_lo_cites_its_passage`
- [tests/test_data_capture_a2_measurement.py](../../../../../../tests/test_data_capture_a2_measurement.py) — direct import
  - `test_a_block_of_only_measurement_checks_is_no_learner_pick_and_says_so`
  - `test_a_check_another_commitment_replaced_is_unavailable_with_why`
  - `test_the_plan_charges_a_measurement_to_the_maintain_lane`
- [tests/test_data_capture_a3_time_metric.py](../../../../../../tests/test_data_capture_a3_time_metric.py) — direct import
  - `test_enrollment_is_the_learners_commitment_and_a_system_dated_check_is_none`
- [tests/test_data_capture_codex_review.py](../../../../../../tests/test_data_capture_codex_review.py) — direct import
  - `test_f4_a_success_before_the_contract_covered_it_never_cites_that_contract`
  - `test_f7_the_report_counts_a_replaced_check_as_unavailable`
- [tests/test_data_capture_landing_review.py](../../../../../../tests/test_data_capture_landing_review.py) — direct import
- [tests/test_data_capture_phone.py](../../../../../../tests/test_data_capture_phone.py) — direct import
- [tests/test_deliverable_path.py](../../../../../../tests/test_deliverable_path.py) — direct import
  - `test_overrides_use_instead_skip_and_check_later`
- [tests/test_depth_transition.py](../../../../../../tests/test_depth_transition.py) — direct import
- [tests/test_dl2_rw4b_keyed_pick_check.py](../../../../../../tests/test_dl2_rw4b_keyed_pick_check.py) — direct import
  - `test_a_keyed_pick_of_a_due_check_the_plan_does_not_hold_is_a_one_item_block_and_answers_it`
  - `test_a_keyed_pick_of_a_planned_due_check_serves_the_check_once_and_its_answer_satisfies_it`
  - `test_a_keyed_pick_of_an_item_a_waiting_check_holds_is_served_and_answers_nothing`
- [tests/test_dual_authority_administration.py](../../../../../../tests/test_dual_authority_administration.py) — direct import
- [tests/test_golden_path_assessment.py](../../../../../../tests/test_golden_path_assessment.py) — direct import
  - `test_harness_activation_activates_exactly_one_edge`
- [tests/test_intent_checks.py](../../../../../../tests/test_intent_checks.py) — direct import
  - `test_an_attempt_before_the_date_does_not_answer_the_check`
  - `test_settling_writes_the_satisfaction_once_and_only_for_answered_checks`
- [tests/test_intent_codex_rereview.py](../../../../../../tests/test_intent_codex_rereview.py) — direct import
  - `test_f3_a_cold_attempt_still_answers_the_check_its_own_feedback_notwithstanding`
  - `test_f3_an_attempt_under_a_siblings_hold_is_practice_not_the_check`
- [tests/test_intent_codex_review.py](../../../../../../tests/test_intent_codex_review.py) — direct import
  - `test_f3_a_hinted_attempt_does_not_use_up_the_check`
  - `test_f9_a_crash_between_publishing_and_linking_is_recovered_without_an_orphan`
- [tests/test_intent_exclusion.py](../../../../../../tests/test_intent_exclusion.py) — direct import
  - `test_an_excluded_request_is_not_a_request`
- [tests/test_intent_fix_round4.py](../../../../../../tests/test_intent_fix_round4.py) — direct import
  - `test_f13_an_assisted_reconstruction_leaves_the_check_pending_and_dates_it_again`
- [tests/test_intent_goal_deadline.py](../../../../../../tests/test_intent_goal_deadline.py) — direct import
  - `test_a_deadline_creates_a_learner_goal_linked_by_goal_id`
- [tests/test_intent_orchestrator_rulings.py](../../../../../../tests/test_intent_orchestrator_rulings.py) — direct import
  - `test_f12_a_frozen_self_grade_answers_the_check`
  - `test_f12_a_repeated_self_grade_never_postpones`
  - `test_f12_an_unrelated_disclosure_still_holds`
- [tests/test_intent_resolution.py](../../../../../../tests/test_intent_resolution.py) — direct import
  - `test_a_satisfied_check_still_decides_over_an_older_lo_master`
  - `test_a_source_locator_only_commitment_covers_no_item`
  - `test_retired_commitments_drop_out`
  - `test_satisfying_a_check_does_not_move_its_choice_time`
- [tests/test_journey6.py](../../../../../../tests/test_journey6.py) — direct import
  - `test_journey6_end_to_end_on_fresh_mvp08_vault`
  - `test_journey6_passive_action_cannot_create_commitment`
- [tests/test_reader_adoption_ownership.py](../../../../../../tests/test_reader_adoption_ownership.py) — direct import
  - `test_crash_before_the_link_reuses_the_commitments_own_card`
  - `test_retiring_a_question_keeps_a_card_another_commitment_still_requests`
- [tests/test_reader_authoring.py](../../../../../../tests/test_reader_authoring.py) — direct import
  - `test_retirement_preserves_commitment_and_evidence`
- [tests/test_reader_ca1_as_printed.py](../../../../../../tests/test_reader_ca1_as_printed.py) — direct import
  - `test_a_due_check_on_your_own_is_read_on_the_server`
- [tests/test_reader_followups.py](../../../../../../tests/test_reader_followups.py) — direct import
  - `test_an_abstention_an_exclusion_or_an_unknown_keeps_the_check`
  - `test_each_follow_up_is_a_test_me_later_commitment_with_its_provenance`
  - `test_only_reader_follow_ups_can_be_undone_here`
  - `test_rebuild_shadow_is_zero_with_follow_ups_present`
  - `test_revaluation_retires_a_follow_up_answered_since_with_its_reason`
  - `test_the_cards_good_news_names_how_the_question_was_answered_and_drops_a_restored_check`
  - `test_undo_leaves_an_answered_check_answered`
- [tests/test_reader_followups_rereview.py](../../../../../../tests/test_reader_followups_rereview.py) — direct import
  - `test_f13_a_failure_after_the_exposure_retirement_loses_neither_the_check_nor_the_re_ask`
  - `test_f14_a_resumed_search_conditions_on_the_live_check_and_retires_nothing`
  - `test_f14_a_resumed_search_that_still_selects_the_earlier_check_keeps_it`
- [tests/test_reader_followups_review.py](../../../../../../tests/test_reader_followups_review.py) — direct import
  - `test_f1_an_impression_since_valuation_holds_the_check_and_revaluation_retires_and_re_asks`
- [tests/test_reader_followups_round3.py](../../../../../../tests/test_reader_followups_round3.py) — direct import
  - `test_an_item_whose_check_was_retired_is_scheduled_again_as_a_fresh_generation`
  - `test_f15_revaluation_keeps_a_shared_check_while_any_licensing_question_needs_it`
- [tests/test_reader_followups_round4.py](../../../../../../tests/test_reader_followups_round4.py) — direct import
  - `test_f16_a_shared_check_is_held_and_retired_by_retentions_rule`
- [tests/test_reader_followups_round5.py](../../../../../../tests/test_reader_followups_round5.py) — direct import
  - `test_f17_revaluation_retires_an_unreadable_check_and_re_asks_what_it_can_name`
- [tests/test_reader_followups_round6.py](../../../../../../tests/test_reader_followups_round6.py) — direct import
  - `test_f18_re_planning_that_drops_a_question_keeps_the_shared_check_live_and_served`
- [tests/test_reader_followups_round7.py](../../../../../../tests/test_reader_followups_round7.py) — direct import
  - `test_f19_a_question_still_absent_from_the_fresh_receipt_is_pruned`
- [tests/test_reader_followups_round8.py](../../../../../../tests/test_reader_followups_round8.py) — direct import
  - `test_round8_a_changed_row_is_recomputed_and_the_second_pass_commits`
  - `test_round8_a_row_that_keeps_changing_is_left_for_the_next_pass`
  - `test_round8_a_scalar_licensing_is_unreadable_not_a_crash`
  - `test_round8_sols_interleaving_keeps_the_shared_check_live`
- [tests/test_reader_reconstruct.py](../../../../../../tests/test_reader_reconstruct.py) — direct import
  - `test_reconstruct_makes_one_item_and_one_test_me_later_commitment`
  - `test_undo_retires_the_commitment_and_the_item`
- [tests/test_reader_rw1b_fix_round4.py](../../../../../../tests/test_reader_rw1b_fix_round4.py) — direct import
- [tests/test_reader_rw1b_review.py](../../../../../../tests/test_reader_rw1b_review.py) — direct import
  - `test_f4_change_reverts_the_routed_capture_its_commitment_and_its_request`
  - `test_f5_a_crash_before_the_commitment_leaves_one_item_and_one_commitment`
- [tests/test_reader_rw6b_landing.py](../../../../../../tests/test_reader_rw6b_landing.py) — direct import
  - `test_i_check_once_commitments_and_follow_ups_coexist_and_the_gate_touches_only_follow_ups`
- [tests/test_router_p2_bridge.py](../../../../../../tests/test_router_p2_bridge.py) — direct import
  - `test_a_retried_constraint_vetoed_advance_stays_deferred`
- [tests/test_staged_policy.py](../../../../../../tests/test_staged_policy.py) — direct import
- [tests/test_state_signals.py](../../../../../../tests/test_state_signals.py) — direct import
  - `test_misspecification_scoped_to_commitment_head_targets`

## Modification guidance

- Change commitments policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/commitments.py](../../../../../../src/learnloop/curriculum/commitments.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
