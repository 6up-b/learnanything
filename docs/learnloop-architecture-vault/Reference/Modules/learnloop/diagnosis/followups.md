---
title: "learnloop.diagnosis.followups"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/followups.py"
source_paths:
  - "src/learnloop/diagnosis/followups.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.followups module"
  - "src/learnloop/diagnosis/followups.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.followups`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps followups behavior inside its owning package, [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]]. Its public surface centers on `common_repair_messages`, `FollowupDecision`, `InterventionSelection`, `AttemptFacetTargets`, `evaluate_intervention_followup`, `evaluate_negative_surprise_followup`, `evaluate_attempt_intervention_followup`, `run_deferred_block_repair_hooks` and 7 more public symbols.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/followups.py](../../../../../../src/learnloop/diagnosis/followups.py) |
| Source lines | 2626 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `common_repair_messages() -> dict[str, str]` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 62) — Learner copy per skip verb, keyed by the recorded decision.
- `class FollowupDecision` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 96)
- `class InterventionSelection` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 111)
- `class AttemptFacetTargets` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 143) — Facet evidence roles for follow-up routing.
- `evaluate_intervention_followup(vault: LoadedVault, repository: Repository, *, attempt_id: str, learning_object_id: str, practice_item_id: str, surprise_direction: str, bayesian_surprise: float, grader_confidence: float | None, error_event_written: bool, max_error_severity: float=0.0, repeated_same_item_failure: bool | None=None, repeated_same_facet_failure: bool | None=None, probe_unfamiliar_probability: float | None=None, target_facets: list[str] | None=None, failed_facets: list[str] | None=None, bad_item_suspicion: float=0.0, available_minutes: int | None=None, session_id: str | None=None, session_interventions_for_lo: int=0, probe_phase_active: bool=False, lo_independent_evidence_mass: float=0.0, lo_raw_attempt_count: int=0, manual_override: bool=False, clock: Clock | None=None) -> FollowupDecision` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 155) — Intervention follow-up evaluator from the recall-coverage spec.
- `evaluate_negative_surprise_followup(vault: LoadedVault, repository: Repository, *, attempt_id: str, learning_object_id: str, practice_item_id: str, surprise_direction: str, bayesian_surprise: float, grader_confidence: float | None, error_event_written: bool, available_minutes: int | None=None, clock: Clock | None=None) -> FollowupDecision` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 546) — Decide whether a negative-surprise follow-up Practice Item should fire.
- `evaluate_attempt_intervention_followup(vault: LoadedVault, repository: Repository, *, result: Any, available_minutes: int | None=None, session_id: str | None=None, manual_override: bool=False, ai_client: Any=None, suppress_insertion_reason: str | None=None, normalization_prepared: bool=False, applied_probe_episode_id: str | None | object=CURRENT_EPISODE, defer_diagnosis_hooks: bool=False, insertion_only: bool=False, clock: Clock | None=None) -> FollowupDecision` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 586) — Run the full post-attempt intervention policy for one attempt result.
- `run_deferred_block_repair_hooks(vault: LoadedVault, repository: Repository, *, attempt_id: str, learning_object_id: str, session_id: str | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 758) — §5.7 block-end resumption of the deferred per-attempt causal hooks.
- `attempt_followup_grade(vault: LoadedVault, repository: Repository, attempt: Mapping[str, Any]) -> tuple[bool, str]` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 909) — FG1: (is this a miss, its grade revision).
- `enqueue_post_attempt_diagnosis(vault: LoadedVault, repository: Repository, *, attempt_id: str, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 924) — Slice 1 §11: the last sync post-attempt step queues the diagnosis.
- `enqueue_post_attempt_learner_text(vault: LoadedVault, repository: Repository, *, attempt_id: str, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 942) — Learner-text gaps: queue a non-empty stuck answer when it is recorded.
- `run_post_diagnosis_hooks(vault: LoadedVault, repository: Repository, *, attempt_id: str, learning_object_id: str, session_id: str | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 967) — Slice 1 §7.2 worker half: the diagnosis-dependent hooks.
- `common_repair_recommendation(repository: Repository, attempt_id: str, *, probe_need: Any, fallback_misconception_id: str='', surface: str='feedback_common_repair', clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 1085) — Journey B read: the already-decided common-repair card for one attempt.
- `current_same_item_failure_streak(repository: Repository, practice_item_id: str) -> int` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 2408) — Trailing attempt-level failure streak for one Practice Item.
- `current_same_facet_failure_streak(vault: LoadedVault, repository: Repository, learning_object_id: str, facets: list[str]) -> int` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 2433) — Largest current aggregate failure streak among the target facets.

### Module constants

- `FOLLOWUP_ACTION` ([src/learnloop/diagnosis/followups.py](../../../../../../src/learnloop/diagnosis/followups.py), line 45)
- `INTERVENTION_ACTION` ([src/learnloop/diagnosis/followups.py](../../../../../../src/learnloop/diagnosis/followups.py), line 46)
- `CURRENT_EPISODE` ([src/learnloop/diagnosis/followups.py](../../../../../../src/learnloop/diagnosis/followups.py), line 48)
- `COMMON_REPAIR_DECISIONS` ([src/learnloop/diagnosis/followups.py](../../../../../../src/learnloop/diagnosis/followups.py), line 55)
- `INTENT_PRIORITY` ([src/learnloop/diagnosis/followups.py](../../../../../../src/learnloop/diagnosis/followups.py), line 86)

## Internal implementation anchors

- `_run_causal_orchestrator_hooks(vault: LoadedVault, repository: Repository, result: Any, *, session_id: str | None=None, clock: Clock | None=None, include_cold_verification: bool=True, include_common_repair: bool=True) -> None` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 803) — Live-path P2 hooks: the machine-check producer and cold verification.
- `_consult_common_repair(vault: LoadedVault, repository: Repository, result: Any, *, session_id: str | None, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 1006) — Journey B delivery: consult the repair lane once, post-attempt.
- `_probe_unfamiliar_probability(vault: LoadedVault, repository: Repository, result: Any, probe_state: Any, episode: Any) -> float | None` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 1161) — ``episode`` is the LO's open episode as the caller read it: None for an unanswered opening episode placement ignores (owner decision 2026-10-12), whose untouched prior must not feed the intervention trigger.
- `_facet_targets_from_debug(debug_payload: dict[str, Any]) -> AttemptFacetTargets` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 1204)
- `_max_error_severity(debug_payload: dict[str, Any], error_events: list[dict[str, Any]]) -> float` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 1234)
- `_session_interventions_for_lo(repository: Repository, session_id: str | None, learning_object_id: str) -> int` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 1242)
- `_decision(triggered: bool, practice_item_id: str | None, reason: str, triggered_actions: list[str], suppressed_actions: list[str], *, intent: str | None=None, need_id: str | None=None, gate_diagnostics: dict[str, Any] | None=None) -> FollowupDecision` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 1264)
- `_build_gate_diagnostics(*, outcome: str, decisive_reason: str, natural_trigger_reasons: list[str], triggered_reasons: list[str], would_suppress: list[str], manual_override: bool, bayesian_surprise: float, surprise_direction: str, grader_confidence: float | None, max_error_severity: float, probe_unfamiliar_probability: float | None, session_interventions_for_lo: int, available_minutes: int | None, target_facets: list[str], config: Any, thresholds: dict[str, ResolvedThreshold], gate_mode: str='cascade', score_result: GateScoreResult | None=None, item_failure_count: float | None=None, facet_failure_count: float | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 1287) — Per-attempt record of why the follow-up gate did (or did not) fire.
- `_threshold_fields(threshold: ResolvedThreshold) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 1363)
- `_decisive_signal(reason: str, *, bayesian_surprise: float, surprise_direction: str, grader_confidence: float | None, max_error_severity: float, probe_unfamiliar_probability: float | None, session_interventions_for_lo: int, available_minutes: int | None, config: Any, thresholds: dict[str, ResolvedThreshold], score_result: GateScoreResult | None=None, item_failure_count: float | None=None, facet_failure_count: float | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 1372) — Describe the single signal that decided this follow-up outcome.
- `_choose_intent(reasons: list[str], *, probe_phase_active: bool, lo_independent_evidence_mass: float, cold_start_min_lo_evidence: float) -> str` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 1517)
- `_canonical_target_facets(vault: LoadedVault, facets: list[str]) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 1535)
- `_active_misconceptions(repository: Repository, learning_object_id: str, *, attempt_id: str | None, gate_facets: set[str], tau_severe_error: float) -> list[MisconceptionRecord]` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 1539) — Active registry beliefs that gate diagnostic routing (spec §4.1).
- `_demonstrated_facets(vault: LoadedVault, repository: Repository, learning_object_id: str) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 1574) — Facets the learner has already passed, snapshotted for review (spec §5.3).
- `_augment_diagnostic_focus_with_misconceptions(diagnostic_focus: dict[str, Any] | None, vault: LoadedVault, repository: Repository, *, active_mcs: list[MisconceptionRecord], learning_object_id: str, source_practice_item_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 1598) — Snapshot belief + §5.3 prerequisite context into the need's focus (spec §4).
- `_misconception_discrimination(repository: Repository, vault: LoadedVault, item: PracticeItem, rubric: Any, hypothesis_set: Any, active_mcs: list[MisconceptionRecord], tau_power: float) -> tuple[bool, float, float]` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 1626) — ``(discriminates, best_J_lb, misconception_eig)`` for a candidate (spec §4.1).
- `_choose_intervention_item(vault: LoadedVault, repository: Repository, *, attempt_id: str | None, learning_object_id: str, exclude_practice_item_id: str, target_facets: list[str], failed_facets: list[str], intent: str, max_error_severity: float, tau_severe_error: float=0.0, clock: Clock | None=None) -> InterventionSelection` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 1682)
- `_recheck_source_first_independence(vault: LoadedVault, repository: Repository, slate: list[dict[str, Any]], candidates: list[PracticeItem], *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 2029) — Serve-time independence of source-first imports (no model call).
- `_intervention_value(vault: LoadedVault, repository: Repository, *, selection: InterventionSelection, learning_object_id: str, session_interventions_for_lo: int, session_id: str | None, clock: Clock | None) -> Any` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 2081) — mvp-0.21 (b): value every eligible candidate of the slate.
- `_select_slate_candidate(selection: InterventionSelection, item: PracticeItem) -> InterventionSelection` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 2175) — The selection with ``item`` queued: the slate rows say which one was selected (the value's pick), keeping the old ranking in ``final_rank``.
- `_jaccard(left: set[str], right: set[str]) -> float` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 2184)
- `_target_precision(candidate_support: set[str], diagnostic_gate_facets: set[str]) -> float` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 2190)
- `_build_diagnostic_focus(vault: LoadedVault, repository: Repository, *, attempt_id: str | None, failed_facets: list[str], diagnostic_states: list[Any], max_error_severity: float, fallback_dominant_target_facet: str | None, question_signal: QuestionSignal | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 2196)
- `_is_known_gap_state(state: Any) -> bool` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 2391)
- `_attempt_target_facets(repository: Repository, practice_item_id: str) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 2401)
- `_attempt_is_failure(attempt: dict[str, Any]) -> bool` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 2455)
- `_record_followup_decision_features(vault: LoadedVault, repository: Repository, *, attempt_id: str, learning_object_id: str, selection: InterventionSelection, outcome: str, need_id: str | None, selected_item_id: str | None, manual_trigger: dict[str, Any] | None=None, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 2463)
- `_record_followup_value_decision(vault: LoadedVault, repository: Repository, *, attempt_id: str, learning_object_id: str, session_id: str | None, outcome: str, decision: dict[str, Any] | None, manual_override: bool, need_id: str | None, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 2563) — mvp-0.21 (voi_stopping): this follow-up decision's own immutable receipt, with its forecast (``voi_stopping.record_followup_decision``).
- `_now_iso(clock: Clock | None) -> str` ([source](../../../../../../src/learnloop/diagnosis/followups.py), line 2624)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `FollowupDecision`, `attempt_followup_grade`, `enqueue_post_attempt_diagnosis`, `enqueue_post_attempt_learner_text`, `evaluate_attempt_intervention_followup`, `normalize_and_resolve_attempt`; statically calls `attempt_followup_grade`, `enqueue_post_attempt_diagnosis`, `enqueue_post_attempt_learner_text`, `evaluate_attempt_intervention_followup`, `normalize_and_resolve_attempt`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `current_same_facet_failure_streak`, `current_same_item_failure_streak`; statically calls `current_same_facet_failure_streak`, `current_same_item_failure_streak`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `common_repair_recommendation`, `run_deferred_block_repair_hooks`; statically calls `common_repair_recommendation`, `run_deferred_block_repair_hooks`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `run_post_diagnosis_hooks`; statically calls `run_post_diagnosis_hooks`
- [[Reference/Modules/learnloop/followup_run/lanes|learnloop.followup_run.lanes]] — imports `evaluate_attempt_intervention_followup`; statically calls `evaluate_attempt_intervention_followup`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `misconception_discrimination`; statically calls `misconception_discrimination`
- [[Reference/Modules/learnloop/learner/recall_calibration|learnloop.learner.recall_calibration]] — imports `FollowupDecision`, `evaluate_intervention_followup`; statically calls `evaluate_intervention_followup`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `evaluate_attempt_intervention_followup`; statically calls `evaluate_attempt_intervention_followup`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `FollowupDecision`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `common_repair_recommendation`, `evaluate_attempt_intervention_followup`; statically calls `common_repair_recommendation`, `evaluate_attempt_intervention_followup`

### Repository tooling consumers

- [scripts/voi_cap_report.py](../../../../../../scripts/voi_cap_report.py); calls `_attempt_target_facets`, `_canonical_target_facets`, `_choose_intent`, `_choose_intervention_item`, `_intervention_value`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`; calls `SystemClock`, `parse_utc`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `MisconceptionRecord`, `Repository`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `exercise_key`, `need_source_import`, `serve_time_exposure`; calls `exercise_key`, `need_source_import`, `serve_time_exposure`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `causal_episode_for_attempt`; calls `causal_episode_for_attempt`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `CausalRepairError`, `SAFE_COMMON_REPAIR_MESSAGE`, `auto_classify_pinned_probe`, `causal_repair_status`, `record_cold_verification_from_task`, `sweep_machine_checks`; calls `auto_classify_pinned_probe`, `causal_repair_status`, `record_cold_verification_from_task`, `sweep_machine_checks`
- [[Reference/Modules/learnloop/diagnosis/chain_records|learnloop.diagnosis.chain_records]] — imports `module`; calls `record_followup_value`, `record_step_failed`
- [[Reference/Modules/learnloop/diagnosis/gate_score|learnloop.diagnosis.gate_score]] — imports `GATE_FEATURE_VERSION`, `GateScoreResult`, `GateSignalValues`, `compute_gate_score`, `resolve_gate_weights`; calls `GateSignalValues`, `compute_gate_score`, `resolve_gate_weights`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `normalize_and_resolve_attempt`; calls `normalize_and_resolve_attempt`
- [[Reference/Modules/learnloop/diagnosis/predictive_eig|learnloop.diagnosis.predictive_eig]] — imports `TargetItemModel`, `build_target_models`, `predictive_facet_eig`; calls `build_target_models`, `predictive_facet_eig`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `episode_posterior`, `maybe_reprobe_for_predictive_failure`; calls `episode_posterior`, `maybe_reprobe_for_predictive_failure`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `H_OTHER`, `H_UNFAMILIAR`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `_BRIDGE_SENSITIVITY`, `_BRIDGE_SPECIFICITY`, `build_hypothesis_set`, `expected_information_gain`, `facet_expected_information_gain`, `hypothesis_conditionals`, `item_registry_discrimination`, `probe_posterior`, `resolve_item_irt`; calls `build_hypothesis_set`, `expected_information_gain`, `facet_expected_information_gain`, `hypothesis_conditionals`, `item_registry_discrimination`, `probe_posterior`, `resolve_item_irt`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `COLD_RETRIEVAL_DELAY`
- [[Reference/Modules/learnloop/diagnosis/signal_quantiles|learnloop.diagnosis.signal_quantiles]] — imports `ResolvedThreshold`, `resolve_followup_thresholds`; calls `resolve_followup_thresholds`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `enqueue_diagnosis`; calls `enqueue_diagnosis`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `joint_grade_record`, `needs_diagnosis`; calls `joint_grade_record`, `needs_diagnosis`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `enqueue_stuck_answer`; calls `enqueue_stuck_answer`
- [[Reference/Modules/learnloop/diagnosis/voi_forecasting|learnloop.diagnosis.voi_forecasting]] — imports `record_followup_forecast`, `record_value_decision_forecast`; calls `record_followup_forecast`, `record_value_decision_forecast`
- [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]] — imports `SITE_FOLLOWUP`, `VOI_VALUE_SUPPRESSION`, `module`, `record_followup_decision`, `voi_stopping_active`; calls `Candidate`, `VoiContext`, `former_cap`, `record_followup_decision`, `value_candidates`, `voi_stopping_active`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `mark_held_attempts`; calls `mark_held_attempts`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `candidate_facet_support`; calls `candidate_facet_support`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `facet_recall_state_for_lo`, `facet_recall_states_for_lo`, `facet_uncertainty_states_for_lo`; calls `facet_recall_state_for_lo`, `facet_recall_states_for_lo`, `facet_uncertainty_states_for_lo`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `familiarity_discount`; calls `familiarity_discount`
- [[Reference/Modules/learnloop/learner/surfaced_beliefs|learnloop.learner.surfaced_beliefs]] — imports `mark_belief_surfaced`; calls `mark_belief_surfaced`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `HELD_ROW_KEY`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `episode_ignored`; calls `episode_ignored`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_refusal`; calls `unservable_refusal`
- [[Reference/Modules/learnloop/tutor/question_signal|learnloop.tutor.question_signal]] — imports `QuestionSignal`, `question_adjusted_uncertainty_states`; calls `question_adjusted_uncertainty_states`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `discriminates`; calls `discriminates`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `logging`, `types`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]], [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]], [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]], [[Reference/Modules/learnloop/followup_run/lanes|learnloop.followup_run.lanes]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/causal_factor_deferral_helpers.py](../../../../../../tests/causal_factor_deferral_helpers.py) — direct import
- [tests/test_attempt_chain_records.py](../../../../../../tests/test_attempt_chain_records.py) — direct import
  - `test_a_failed_forecast_and_a_failed_post_diagnosis_step_leave_records`
- [tests/test_causal_attribution_exhibit.py](../../../../../../tests/test_causal_attribution_exhibit.py) — direct import
  - `test_exhibit_replay_blocks_false_targets_promotion_and_retry`
- [tests/test_causal_factor_deferral.py](../../../../../../tests/test_causal_factor_deferral.py) — direct import
- [tests/test_causal_orchestrator.py](../../../../../../tests/test_causal_orchestrator.py) — direct import
  - `test_cold_verification_is_carried_through_the_followup_task`
  - `test_live_attempt_queues_a_repair_mapping_backfill_that_self_closes`
- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_a_deterministic_sensor_earns_validator_owned_and_reaches_triage`
  - `test_causal_disambiguation_end_to_end_acceptance`
- [tests/test_common_repair_delivery.py](../../../../../../tests/test_common_repair_delivery.py) — direct import
  - `test_attempt_without_factors_is_untouched`
  - `test_divergent_causes_get_no_common_repair_card`
  - `test_failed_diagnostic_attempt_opens_the_repair_lane`
  - `test_feedback_bundle_carries_the_recommendation_and_stamps_durable_beliefs`
  - `test_receipted_divergence_skips_the_consultation_entirely`
  - `test_shared_repair_factor_records_the_skip_without_minting_an_episode`
- [tests/test_evaluation.py](../../../../../../tests/test_evaluation.py) — direct import
  - `test_gate_section_counts_manual_false_negatives`
  - `test_report_on_real_session_flow`
- [tests/test_facet_diagnostics_v03.py](../../../../../../tests/test_facet_diagnostics_v03.py) — direct import
  - `test_diagnostic_plan_carries_grader_repair_rationales`
  - `test_need_target_builder_freezes_structured_repair_focus`
  - `test_single_facet_probe_passes_gate_even_with_multiple_open_facets`
  - `test_subthreshold_noisy_item_creates_single_facet_generation_need_and_logs_slate`
- [tests/test_followup_diagnostic_selection.py](../../../../../../tests/test_followup_diagnostic_selection.py) — direct import
- [tests/test_followups.py](../../../../../../tests/test_followups.py) — direct import
  - `test_followup_gate_skips_non_negative_surprise`
  - `test_manual_override_forces_followup_when_gate_silent`
  - `test_manual_override_records_need_when_no_suitable_item`
- [tests/test_gate_score.py](../../../../../../tests/test_gate_score.py) — direct import
  - `test_score_mode_below_threshold_logs_counterfactual_margin`
  - `test_score_mode_fires_on_surprising_failure_and_logs_scores`
  - `test_score_mode_hard_gates_still_suppress`
  - `test_score_mode_manual_override_still_queues`
- [tests/test_guided_redo.py](../../../../../../tests/test_guided_redo.py) — direct import
  - `test_guided_redo_binds_open_episode_and_closes_the_funnel`
  - `test_guided_redo_establishes_episode_without_overlay`
- [tests/test_held_grade_evidence.py](../../../../../../tests/test_held_grade_evidence.py) — direct import
  - `test_f9_f10_held_grades_build_no_failure_streak_and_move_no_item_quality`
  - `test_review_f1_a_regrade_into_a_hold_supersedes_the_assessed_grade_it_replaces`
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_the_intervention_followup_records_no_servability_skips`
- [tests/test_misconception_routing.py](../../../../../../tests/test_misconception_routing.py) — direct import
- [tests/test_pfc_unassessed_readers.py](../../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_a_cold_retry_with_nothing_assessed_neither_confirms_nor_fails_the_repair`
  - `test_a_pinned_probe_declines_to_classify_an_unassessed_criterion`
- [tests/test_placement_opening_probes.py](../../../../../../tests/test_placement_opening_probes.py) — direct import
  - `test_an_ignored_episode_feeds_no_reader_that_scores_it`
- [tests/test_post_attempt_pipeline.py](../../../../../../tests/test_post_attempt_pipeline.py) — direct import
- [tests/test_predictive_eig.py](../../../../../../tests/test_predictive_eig.py) — direct import
  - `test_followup_slate_logs_predictive_fields_and_ranking_unchanged_at_weight_zero`
- [tests/test_probe_block_end.py](../../../../../../tests/test_probe_block_end.py) — direct import
  - `test_block_end_repair_consultation_is_idempotent`
  - `test_followup_and_normalization_defer_to_block_end`
  - `test_in_block_failure_gets_decision_receipt_at_block_end_not_before`
  - `test_ordinary_attempt_outside_block_still_normalizes`
- [tests/test_question_signal.py](../../../../../../tests/test_question_signal.py) — direct import
- [tests/test_recall_coverage_interventions.py](../../../../../../tests/test_recall_coverage_interventions.py) — direct import
  - `test_diagnostic_generation_stales_resolved_repeat_failure_need`
  - `test_high_unfamiliar_probe_posterior_records_intervention_need`
  - `test_intervention_need_targets_failed_facet_not_whole_item`
  - `test_intervention_needs_canonicalize_target_facets_for_dedup`
  - `test_repeated_failure_triggers_intervention_need_without_surprise`
  - `test_second_same_facet_failure_counts_across_different_items`
  - `test_success_breaks_item_streak_before_a_later_failure`
  - `test_success_resets_repeat_failure_gate_and_coverage_is_not_failed`
- [tests/test_recurrence_deferral.py](../../../../../../tests/test_recurrence_deferral.py) — direct import
- [tests/test_source_first_needs.py](../../../../../../tests/test_source_first_needs.py) — direct import
- [tests/voi_stopping_helpers.py](../../../../../../tests/voi_stopping_helpers.py) — direct import

## Modification guidance

- Change followups policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/followups.py](../../../../../../src/learnloop/diagnosis/followups.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
