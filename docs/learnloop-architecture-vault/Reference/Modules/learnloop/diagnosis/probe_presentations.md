---
title: "learnloop.diagnosis.probe_presentations"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_presentations.py"
source_paths:
  - "src/learnloop/diagnosis/probe_presentations.py"
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
  - "learnloop.diagnosis.probe_presentations module"
  - "src/learnloop/diagnosis/probe_presentations.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_presentations`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_presentations` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Committed diagnostic presentations and the gates that admit them.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_presentations.py](../../../../../../src/learnloop/diagnosis/probe_presentations.py) |
| Source lines | 557 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `shadow_selection_rankings(candidates: list[EligibleInstrument], *, top_k: int=3) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/diagnosis/probe_presentations.py), line 34) — Alternative selection-policy rankings for shadow logging (§13.3).
- `class RoutineDisplayCovered(Exception)` ([source](../../../../../../src/learnloop/diagnosis/probe_presentations.py), line 70) — A probe or placement presentation refused: the item's answer was shown, so it cannot test the learner (the one eligibility decision, ``serve_eligibility.decide(..., PROBE)``).
  - `__init__(self, practice_item_id: str, *, decision: object | None=None) -> None` (line 78; internal)
- `probe_eligibility(repository: Repository, practice_item_id: str, *, clock: Clock | None=None)` ([source](../../../../../../src/learnloop/diagnosis/probe_presentations.py), line 89) — The one eligibility decision for a probe or placement presentation of the item now (``serve_eligibility``, request ``PROBE``).
- `routine_display_covers_item(repository: Repository, practice_item_id: str, *, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_presentations.py), line 102) — Was the item's answer shown, so that no probe may test it now?
- `refuse_routine_display_covered(repository: Repository, practice_item_id: str, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_presentations.py), line 115) — Raise :class:`RoutineDisplayCovered` when a probe of the item cannot test the learner now (the one eligibility decision refuses it): the one guard every presentation commit (and serve) passes through.
- `commit_presentation(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, eligible: EligibleInstrument, *, scheduler_candidate_id: str | None=None, extra_selection_components: Mapping[str, Any] | None=None, candidates: list[EligibleInstrument] | None=None, supersede_active: bool=True, clock: Clock | None=None) -> ProbePresentationRecord` ([source](../../../../../../src/learnloop/diagnosis/probe_presentations.py), line 133) — Durably commit the selection before the item is returned to the client.
- `record_presentation_forecast(vault: LoadedVault, repository: Repository, presentation: ProbePresentationRecord, *, learning_object_id: str | None=None, candidate_count: int | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_presentations.py), line 190) — EVSI calibration Part B: log the forecast this probe selection ran on.
- `presentation_commit_payload(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, eligible: EligibleInstrument, *, scheduler_candidate_id: str | None=None, extra_selection_components: Mapping[str, Any] | None=None, candidates: list[EligibleInstrument] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_presentations.py), line 242) — Build the frozen presentation row before its owning transaction.
- `serve_presentation(repository: Repository, presentation_id: str, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_presentations.py), line 365) — Mark a committed presentation served: the administration itself, and the only path to ``served``.
- `probe_serving_block_reason(vault: LoadedVault, repository: Repository, *, session_id: str | None=None, cap_lifted: bool=False) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_presentations.py), line 387) — The §5.9 orchestration gate shared by every serving surface.
- `probe_value_block_reason(vault: LoadedVault, repository: Repository, episode: 'ProbeEpisodeRecord', practice_item_id: str, *, session_id: str | None=None, cap_lifted: bool=False) -> tuple[str | None, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/diagnosis/probe_presentations.py), line 424) — mvp-0.21 (voi_stopping, site ``probe_episode``): may this item be the episode's next observation?
- `commit_item_presentation(vault: LoadedVault, repository: Repository, episode: 'ProbeEpisodeRecord', item, hypothesis_set, *, extra_selection_components: Mapping[str, Any] | None=None, clock: Clock | None=None)` ([source](../../../../../../src/learnloop/diagnosis/probe_presentations.py), line 473) — Commit and serve a presentation for one specific item.
- `class PresentationValidation` ([source](../../../../../../src/learnloop/diagnosis/probe_presentations.py), line 512)
- `validate_presentation_for_submission(repository: Repository, presentation_id: str, *, practice_item_id: str, attempt_id: str | None=None, clock: Clock | None=None) -> PresentationValidation` ([source](../../../../../../src/learnloop/diagnosis/probe_presentations.py), line 519) — §5.4/§5.1 submission validation: active, same episode/item/segment, unexpired, unconsumed.

### Module constants

- `PROBE_ITEM_ANSWER_SHOWN` ([src/learnloop/diagnosis/probe_presentations.py](../../../../../../src/learnloop/diagnosis/probe_presentations.py), line 86)

## Internal implementation anchors

- `_robust_channel_pin(repository: Repository, episode: ProbeEpisodeRecord, eligible: EligibleInstrument, belief: Mapping[str, float]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_presentations.py), line 330) — The mvp-0.8 decision-time channel pin + robust product for the chosen candidate (§1.5/§2.1).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `validate_presentation_for_submission`; statically calls `validate_presentation_for_submission`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `RoutineDisplayCovered`, `commit_presentation`, `serve_presentation`; statically calls `commit_presentation`, `serve_presentation`
- [[Reference/Modules/learnloop/diagnosis/probe_evidence|learnloop.diagnosis.probe_evidence]] — imports `validate_presentation_for_submission`; statically calls `validate_presentation_for_submission`
- [[Reference/Modules/learnloop/diagnosis/probe_offer|learnloop.diagnosis.probe_offer]] — imports `RoutineDisplayCovered`, `commit_presentation`, `routine_display_covers_item`; statically calls `commit_presentation`, `routine_display_covers_item`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `RoutineDisplayCovered`, `presentation_commit_payload`, `probe_serving_block_reason`, `record_presentation_forecast`; statically calls `presentation_commit_payload`, `probe_serving_block_reason`, `record_presentation_forecast`
- [[Reference/Modules/learnloop/sim/diagnostic_validation|learnloop.sim.diagnostic_validation]] — imports `RoutineDisplayCovered`, `commit_presentation`, `serve_presentation`; statically calls `commit_presentation`, `serve_presentation`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `commit_item_presentation`, `probe_serving_block_reason`, `probe_value_block_reason`; statically calls `commit_item_presentation`, `probe_serving_block_reason`, `probe_value_block_reason`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `PROBE_ITEM_ANSWER_SHOWN`, `RoutineDisplayCovered`, `commit_item_presentation`, `probe_serving_block_reason`, `probe_value_block_reason`, `routine_display_covers_item`, `serve_presentation`, `validate_presentation_for_submission`; statically calls `commit_item_presentation`, `probe_serving_block_reason`, `probe_value_block_reason`, `routine_display_covers_item`, `serve_presentation`, `validate_presentation_for_submission`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ProbeEpisodeRecord`, `ProbePresentationRecord`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/probe_completion|learnloop.diagnosis.probe_completion]] — imports `robust_gate_counterfactual`; calls `robust_gate_counterfactual`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `EligibleInstrument`, `_entropy`, `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`; calls `_entropy`, `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `SELECTION_POLICY_VERSION`, `instrument_expected_information_gain`; calls `instrument_expected_information_gain`
- [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] — imports `instrument_ensemble`, `load_pinned_channel`; calls `instrument_ensemble`, `load_pinned_channel`
- [[Reference/Modules/learnloop/diagnosis/robust_composition|learnloop.diagnosis.robust_composition]] — imports `robust_eig_per_second`; calls `robust_eig_per_second`
- [[Reference/Modules/learnloop/diagnosis/voi_forecasting|learnloop.diagnosis.voi_forecasting]] — imports `record_probe_presentation_forecast`, `record_value_decision_forecast`; calls `record_probe_presentation_forecast`, `record_value_decision_forecast`
- [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]] — imports `SITE_PROBE_EPISODE`, `module`, `voi_stopping_active`; calls `VoiContext`, `probe_episode_decision`, `voi_stopping_active`, `with_robust_gate_counterfactual`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `module`; calls `decide`, `gather`, `log_decision`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]], [[Reference/Modules/learnloop/diagnosis/probe_evidence|learnloop.diagnosis.probe_evidence]], [[Reference/Modules/learnloop/diagnosis/probe_offer|learnloop.diagnosis.probe_offer]], [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/diagnosis_journey_helpers.py](../../../../../../tests/diagnosis_journey_helpers.py) — direct import
- [tests/p2_acceptance_helpers.py](../../../../../../tests/p2_acceptance_helpers.py) — direct import
- [tests/probe_block_end_helpers.py](../../../../../../tests/probe_block_end_helpers.py) — direct import
- [tests/probe_episodes_helpers.py](../../../../../../tests/probe_episodes_helpers.py) — direct import
- [tests/probe_robust_cutover_helpers.py](../../../../../../tests/probe_robust_cutover_helpers.py) — direct import
- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — direct import
  - `test_an_open_episode_with_observations_refuses_the_offer_with_a_typed_reason`
- [tests/test_characterization_probe_regrade.py](../../../../../../tests/test_characterization_probe_regrade.py) — direct import
- [tests/test_characterization_probe_replay.py](../../../../../../tests/test_characterization_probe_replay.py) — direct import
- [tests/test_p2_leakage_suite.py](../../../../../../tests/test_p2_leakage_suite.py) — direct import
- [tests/test_probe_audit.py](../../../../../../tests/test_probe_audit.py) — direct import
- [tests/test_probe_episodes.py](../../../../../../tests/test_probe_episodes.py) — direct import
  - `test_item_excluded_from_live_slate_cannot_be_committed_as_a_probe`
  - `test_presentation_activity_disqualification_precedes_live_projection`
  - `test_presentation_snapshot_matches_compiled_instrument`
- [tests/test_probe_longform_families.py](../../../../../../tests/test_probe_longform_families.py) — direct import
  - `test_longform_observation_records_trace_and_bounded_mass`
- [tests/test_probe_orchestration_remainder.py](../../../../../../tests/test_probe_orchestration_remainder.py) — direct import
  - `test_answer_confidence_is_logged_on_attempt_and_observation`
  - `test_onboarding_ceiling_deactivates_probes_until_practice_starts`
  - `test_planner_shadow_report_summarizes_logged_components`
  - `test_session_cap_blocks_further_probe_serving`
- [tests/test_probe_policy.py](../../../../../../tests/test_probe_policy.py) — direct import
  - `test_family_redundancy_penalty_after_observation`
  - `test_sequential_selection_conditions_on_observed_posterior`
- [tests/test_probe_predictive_eig.py](../../../../../../tests/test_probe_predictive_eig.py) — direct import
  - `test_predictive_objective_is_default_and_persisted`
- [tests/test_serve_eligibility.py](../../../../../../tests/test_serve_eligibility.py) — direct import
  - `test_no_probe_is_committed_for_an_item_submit_would_prime`
- [tests/test_serve_eligibility_review.py](../../../../../../tests/test_serve_eligibility_review.py) — direct import
  - `test_f4_a_probe_of_an_item_submit_would_prime_is_refused`
- [tests/test_teacher_te2_landing_r1.py](../../../../../../tests/test_teacher_te2_landing_r1.py) — direct import
  - `test_fg1s_presentation_path_stamps_the_submissions_identity_and_its_regrade_the_replacements`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1k_no_probe_is_committed_for_an_item_inside_routine_display_coverage`
  - `test_f1l_a_presentation_committed_before_a_display_is_not_served_inside_its_coverage`
  - `test_f1l_a_refused_causal_offer_leaves_the_episode_and_its_presentation_unchanged`
- [tests/test_voi_merge_composition.py](../../../../../../tests/test_voi_merge_composition.py) — direct import
  - `test_a_committed_probe_logs_its_value_decision_once_beside_the_selection_forecast`
- [tests/test_voi_stopping.py](../../../../../../tests/test_voi_stopping.py) — direct import
  - `test_at_the_successor_value_keeps_asking_past_the_former_cap`
  - `test_at_the_successor_value_stops_an_episode_whose_next_observation_does_not_pay`
  - `test_value_carries_one_episode_past_its_former_maximum`
  - `test_with_the_switches_off_the_spent_session_cap_blocks_probes`
- [tests/voi_stopping_helpers.py](../../../../../../tests/voi_stopping_helpers.py) — direct import

## Modification guidance

- Change probe presentations policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_presentations.py](../../../../../../src/learnloop/diagnosis/probe_presentations.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
