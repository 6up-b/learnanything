---
title: "learnloop.diagnosis.probe_episodes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_episodes.py"
source_paths:
  - "src/learnloop/diagnosis/probe_episodes.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.probe_episodes module"
  - "src/learnloop/diagnosis/probe_episodes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_episodes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_episodes` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Adaptive diagnostic episodes (spec_probe_eig_redesign.md §5/§7/§10/§11).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py) |
| Source lines | 2664 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class EligibleInstrument` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 79) — One (item, compiled instrument) pair usable by the open episode.
  - `selection_components(self) -> dict[str, Any]` (line 103; public) — §7.3 separately-inspectable utility components for telemetry.
- `class EpisodePosterior` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 119)
  - `top(self) -> tuple[str, float]` (line 128; public)
- `enter_episode(vault: LoadedVault, repository: Repository, learning_object_id: str, *, trigger: str='initial', origin: str | None=None, goal_id: str | None=None, causal_factor_id: str | None=None, clock: Clock | None=None, ai_client: object | None=None) -> ProbeEpisodeRecord` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 142) — Open a diagnostic episode with a fresh ULID and locked hypothesis set.
- `episode_has_observations(repository: Repository, episode_id: str) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 316) — True when this episode's locked hypothesis set has interpreted evidence.
- `retarget_episode_to_causal_factor(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, causal_factor_id: str, *, origin: str, clock: Clock | None=None) -> ProbeEpisodeRecord` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 370) — Point an OBSERVATION-FREE open episode at a causal cause set.
- `maybe_reprobe_for_misconception(vault: LoadedVault, repository: Repository, learning_object_id: str, *, severity: float, clock: Clock | None=None) -> ProbeEpisodeRecord | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 460) — Re-probe trigger (§6.5): a new high-severity misconception opens a new episode with a new locked hypothesis-set snapshot.
- `maybe_reprobe_for_predictive_failure(vault: LoadedVault, repository: Repository, learning_object_id: str, *, clock: Clock | None=None) -> ProbeEpisodeRecord | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 480) — Re-probe trigger (§6.5/Checkpoint 2.7): repeated prediction errors indicate model misspecification.
- `enter_stale_uncertainty_reprobes(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> list[ProbeEpisodeRecord]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 528) — Periodic re-probe producer (§6.5): high uncertainty that persists after a completed episode re-enters probing with trigger ``stale_uncertainty``.
- `episode_hypothesis_set(repository: Repository, episode: ProbeEpisodeRecord) -> HypothesisSet | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 599)
- `administered_surface_exclusions(vault: LoadedVault, repository: Repository) -> tuple[set[str], set[str]]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 613) — Surfaces the learner has already seen in ANY administration.
- `eligible_instruments(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, *, hypothesis_set: HypothesisSet | None=None, posterior: Mapping[str, float] | None=None) -> list[EligibleInstrument]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 632) — Instruments admitted for this episode's locked set, ranked by EIG.
- `resolve_instrument(vault: LoadedVault, repository: Repository, item: PracticeItem, hypothesis_set: HypothesisSet) -> tuple[CompiledInstrument, dict[str, str]] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 803) — The executable instrument binding this item to the locked set, if any.
- `compile_fallback_instrument(vault: LoadedVault, repository: Repository, item: PracticeItem, hypothesis_set: HypothesisSet) -> CompiledInstrument | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 874) — Legacy fallback instrument (§7.2): registry discrimination + IRT model.
- `shadow_selection_rankings(candidates: list[EligibleInstrument], *, top_k: int=3) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 932) — Alternative selection-policy rankings for shadow logging (§13.3).
- `commit_presentation(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, eligible: EligibleInstrument, *, scheduler_candidate_id: str | None=None, extra_selection_components: Mapping[str, Any] | None=None, candidates: list[EligibleInstrument] | None=None, supersede_active: bool=True, clock: Clock | None=None) -> ProbePresentationRecord` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 968) — Durably commit the selection before the item is returned to the client.
- `presentation_commit_payload(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, eligible: EligibleInstrument, *, scheduler_candidate_id: str | None=None, extra_selection_components: Mapping[str, Any] | None=None, candidates: list[EligibleInstrument] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1013) — Build the frozen presentation row before its owning transaction.
- `serve_presentation(repository: Repository, presentation_id: str, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1126)
- `probe_serving_block_reason(vault: LoadedVault, repository: Repository, *, session_id: str | None=None, cap_lifted: bool=False) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1130) — The §5.9 orchestration gate shared by every serving surface.
- `commit_item_presentation(vault: LoadedVault, repository: Repository, episode: 'ProbeEpisodeRecord', item, hypothesis_set, *, extra_selection_components: Mapping[str, Any] | None=None, clock: Clock | None=None)` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1162) — Commit and serve a presentation for one specific item.
- `plan_precommitted_block(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, *, block_size: int | None=None, clock: Clock | None=None) -> list[ProbePresentationRecord]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1196) — Greedy conditional/joint EIG for one precommitted block (Checkpoint 5.3).
- `class PresentationValidation` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1335)
- `validate_presentation_for_submission(repository: Repository, presentation_id: str, *, practice_item_id: str, attempt_id: str | None=None, clock: Clock | None=None) -> PresentationValidation` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1342) — §5.4/§5.1 submission validation: active, same episode/item/segment, unexpired, unconsumed.
- `episode_posterior(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, *, hypothesis_set: HypothesisSet | None=None) -> EpisodePosterior | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1386) — Replay the episode's evidence into the locked-set posterior.
- `record_episode_evidence(vault: LoadedVault, repository: Repository, *, learning_object_id: str, attempt_id: str, practice_item_id: str, attempt_type: str, hints_used: int, probe_presentation_id: str | None, grading_source: str, tutor_contaminated: bool=False, ai_client: object | None=None, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1605) — Post-persist accounting for one attempt on an in-episode LO.
- `record_presentation_activity_classification(vault: LoadedVault, repository: Repository, *, attempt_id: str, practice_item_id: str, attempt_type: str, hints_used: int, probe_presentation_id: str, grading_source: str, tutor_contaminated: bool=False, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1672) — Persist presentation-derived eligibility before canonical projection.
- `persist_episode_beliefs(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, posterior: EpisodePosterior, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2184) — Persist registry-misconception marginals to `learner_state_beliefs`.
- `stop_diagnosing_and_teach(vault: LoadedVault, repository: Repository, learning_object_id: str, *, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2466) — `Stop diagnosing and teach me`: end measurement, open a post-intervention state segment, and persist a typed transition decision (§12.1).
- `close_diagnostic_segment(repository: Repository, episode_id: str, *, reason: str='converted_to_tutoring', clock: Clock | None=None) -> ProbeEpisodeRecord | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2516) — Close a still-open diagnostic episode when instruction/repair begins (P0 invariant 7 / §12.2 "starting instruction closes the measurement segment").
- `abandon_episode(repository: Repository, learning_object_id: str, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2568)
- `episode_contract(vault: LoadedVault, repository: Repository, learning_object_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2592) — The probe UX contract for one LO, or None when no episode is active.
- `next_probe_item(vault: LoadedVault, repository: Repository, learning_object_id: str) -> EligibleInstrument | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2621) — The item that would be served next for this LO's open episode, or None.

### Module constants

- `FALLBACK_FAMILY_ID` ([src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 65)
- `FALLBACK_FAMILY_VERSION` ([src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 66)
- `PROBE_ASSISTANCE_RESTRICTIONS` ([src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 69)

## Internal implementation anchors

- `_entropy(distribution: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 135)
- `_relock_episode_row(repository: Repository, episode_id: str, *, hypothesis_set_id: str, origin: str, target_decision: Mapping[str, Any], clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 333)
- `_record_generation_need(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, hypothesis_set: HypothesisSet, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 575)
- `_resolved_slot_map_from_snapshot(snapshot: Mapping[str, Any], instrument: CompiledInstrument, labels: list[str]) -> dict[str, str] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 845) — Return the frozen selection-time label mapping for this presentation.
- `_robust_channel_pin(repository: Repository, episode: ProbeEpisodeRecord, eligible: EligibleInstrument, belief: Mapping[str, float]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1091) — The mvp-0.8 decision-time channel pin + robust product for the chosen candidate (§1.5/§2.1).
- `_first_intervention_at(repository: Repository, episode: ProbeEpisodeRecord) -> Any` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1489)
- `_observation_likelihoods_from_row(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, attempt: Mapping[str, Any], observation_row: Mapping[str, Any]) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1498)
- `_fired_error_types(repository: Repository, attempt_id: str) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1534)
- `_item_max_points(vault: LoadedVault, practice_item_id: str) -> int` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1546)
- `_incidental_likelihoods(vault: LoadedVault, repository: Repository, attempt: Mapping[str, Any], hypothesis_set: HypothesisSet) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1554)
- `_bayes_update(posterior: dict[str, float], likelihoods: Mapping[str, float], *, weight: float=1.0, prior_for_marginal: Mapping[str, float] | None=None) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1579) — Weighted Bayes step: ``L_w = w·L + (1−w)·marginal`` dampens partially trusted evidence toward the mixture marginal (no update at w=0).
- `_presentation_contamination(*, attempt_type: str, hints_used: int, tutor_contaminated: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1723)
- `_record_presentation_activity_fact(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, presentation: ProbePresentationRecord, *, attempt_id: str, practice_item_id: str, attempt_type: str, hints_used: int, tutor_contaminated: bool, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1738)
- `_robust_observation_snapshot(repository: Repository, episode: ProbeEpisodeRecord, instrument: CompiledInstrument, slot_map: Mapping[str, str], posterior_before: Mapping[str, float], *, observed_outcome: str, grader_confidence: float | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1784) — The mvp-0.8 decision-time posterior snapshot for one observation (§4.2).
- `_dual_write_probe_grade(vault: LoadedVault, repository: Repository, *, instrument: CompiledInstrument | None=None, practice_item_id: str, attempt_id: str, grading_source: str, observed_outcome: str, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1817) — P0.2 dual-write for probe submissions (§4.1, §7.2).
- `_record_presentation_observation(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, hypothesis_set: HypothesisSet, *, attempt_id: str, practice_item_id: str, attempt_type: str, hints_used: int, probe_presentation_id: str, grading_source: str, tutor_contaminated: bool, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1893)
- `_attempt_rubric_score(repository: Repository, attempt_id: str) -> int | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2101)
- `_assess_longform_trace(vault: LoadedVault, repository: Repository, presentation: ProbePresentationRecord, instrument: CompiledInstrument, *, attempt_id: str, practice_item_id: str, attempt_type: str)` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2108) — Assess the §8.2 structured trace for a long-form response, or None when the presentation's card declares no obligations (microprobes).
- `_observation_features(repository: Repository, presentation: ProbePresentationRecord, *, attempt_id: str, structured_trace: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2156) — Logged-only observation features (§7.1): answer confidence, latency (both submitted and derived from presentation timestamps), and the §8.2 structured trace.
- `_evaluate_completion(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, posterior: EpisodePosterior, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2222)
- `_plausible_actions_agree(repository: Repository, posterior: EpisodePosterior, episode_config) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2322) — True when every plausible hypothesis routes to one first intervention.
- `_robust_completion_override(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, posterior: EpisodePosterior) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2364) — The mvp-0.8 robust stop/abstain gate (§4.2).
- `_surface_key(vault: LoadedVault, practice_item_id: str) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2417) — The independent-group key for a probe observation (augmentation §8).
- `_complete(repository: Repository, episode: ProbeEpisodeRecord, reason: str, *, posterior: EpisodePosterior | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2439)
- `_set_target_decision(repository: Repository, episode_id: str, decision: Mapping[str, Any], *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2554)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `record_episode_evidence`, `record_presentation_activity_classification`, `validate_presentation_for_submission`; statically calls `record_episode_evidence`, `record_presentation_activity_classification`, `validate_presentation_for_submission`
- [[Reference/Modules/learnloop/curriculum/confusable_concepts|learnloop.curriculum.confusable_concepts]] — imports `episode_posterior`; statically calls `episode_posterior`
- [[Reference/Modules/learnloop/curriculum/golden_path_run|learnloop.curriculum.golden_path_run]] — imports `module`; statically calls `close_diagnostic_segment`
- [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] — imports `eligible_instruments`, `enter_episode`, `episode_posterior`; statically calls `eligible_instruments`, `enter_episode`, `episode_posterior`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `commit_presentation`, `eligible_instruments`, `enter_episode`, `episode_has_observations`, `retarget_episode_to_causal_factor`; statically calls `commit_presentation`, `eligible_instruments`, `enter_episode`, `episode_has_observations`, `retarget_episode_to_causal_factor`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_pack|learnloop.diagnosis.diagnostic_pack]] — imports `module`; statically calls `enter_episode`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]] — imports `_record_generation_need`, `administered_surface_exclusions`, `episode_hypothesis_set`; statically calls `_record_generation_need`, `administered_surface_exclusions`, `episode_hypothesis_set`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `episode_posterior`, `maybe_reprobe_for_predictive_failure`; statically calls `episode_posterior`, `maybe_reprobe_for_predictive_failure`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `maybe_reprobe_for_misconception`; statically calls `maybe_reprobe_for_misconception`
- [[Reference/Modules/learnloop/diagnosis/probe_audit|learnloop.diagnosis.probe_audit]] — imports `_bayes_update`, `_observation_likelihoods_from_row`, `episode_hypothesis_set`, `episode_posterior`; statically calls `_bayes_update`, `_observation_likelihoods_from_row`, `episode_hypothesis_set`, `episode_posterior`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `EpisodePosterior`, `_evaluate_completion`, `_set_target_decision`, `episode_posterior`, `persist_episode_beliefs`; statically calls `_evaluate_completion`, `_set_target_decision`, `episode_posterior`, `persist_episode_beliefs`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `EligibleInstrument`, `commit_presentation`, `episode_hypothesis_set`, `serve_presentation`; statically calls `EligibleInstrument`, `commit_presentation`, `episode_hypothesis_set`, `serve_presentation`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `administered_surface_exclusions`, `eligible_instruments`; statically calls `administered_surface_exclusions`, `eligible_instruments`
- [[Reference/Modules/learnloop/diagnosis/probe_targeting|learnloop.diagnosis.probe_targeting]] — imports `eligible_instruments`; statically calls `eligible_instruments`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `EligibleInstrument`, `EpisodePosterior`, `administered_surface_exclusions`, `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`, `presentation_commit_payload`, `probe_serving_block_reason`; statically calls `administered_surface_exclusions`, `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`, `presentation_commit_payload`, `probe_serving_block_reason`
- [[Reference/Modules/learnloop/sim/diagnostic_validation|learnloop.sim.diagnostic_validation]] — imports `commit_presentation`, `eligible_instruments`, `episode_posterior`, `serve_presentation`; statically calls `commit_presentation`, `eligible_instruments`, `episode_posterior`, `serve_presentation`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `enter_episode`, `enter_stale_uncertainty_reprobes`; statically calls `enter_episode`, `enter_stale_uncertainty_reprobes`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `commit_item_presentation`, `episode_contract`, `episode_hypothesis_set`, `probe_serving_block_reason`, `stop_diagnosing_and_teach`; statically calls `commit_item_presentation`, `episode_contract`, `episode_hypothesis_set`, `probe_serving_block_reason`, `stop_diagnosing_and_teach`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `commit_item_presentation`, `enter_episode`, `episode_contract`, `episode_hypothesis_set`, `next_probe_item`, `probe_serving_block_reason`, `serve_presentation`, `stop_diagnosing_and_teach`, `validate_presentation_for_submission`; statically calls `commit_item_presentation`, `enter_episode`, `episode_contract`, `episode_hypothesis_set`, `next_probe_item`, `probe_serving_block_reason`, `serve_presentation`, `stop_diagnosing_and_teach`, `validate_presentation_for_submission`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `record_grade_dual_write`; calls `record_grade_dual_write`
- [[Reference/Modules/learnloop/attempts/outcome_schemas|learnloop.attempts.outcome_schemas]] — imports `BUILTIN_SCHEMAS`, `COARSE_RESPONSE_SLUG`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ProbeEpisodeRecord`, `ProbePresentationRecord`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `near_clone_from_selection_components`; calls `near_clone_from_selection_components`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `lock_causal_hypothesis_set`; calls `lock_causal_hypothesis_set`
- [[Reference/Modules/learnloop/diagnosis/longform_trace|learnloop.diagnosis.longform_trace]] — imports `assess_trace`, `classify_trace_outcome`, `obligations_from_bindings`, `outcomes_from_grading_evidence`; calls `assess_trace`, `classify_trace_outcome`, `obligations_from_bindings`, `outcomes_from_grading_evidence`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `_first_error_from_block`, `block_complete`, `block_observation_rows`, `build_typed_transition_decision`, `end_diagnostic_block`; calls `_first_error_from_block`, `block_complete`, `block_observation_rows`, `build_typed_transition_decision`, `end_diagnostic_block`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `APPROVED_DIAGNOSTIC_GRADING_SOURCES`, `CompiledInstrument`, `InstrumentCard`, `ProbeFamilyTemplate`, `SELECTION_POLICY_VERSION`, `classify_outcome`, `ensure_builtin_families`, `information_rate`, `instrument_expected_information_gain`, `instrument_observation_likelihoods`, `instrument_predictive_information_gain`, `map_episode_labels_to_slots`, `record_real_observation_counts`, `shrunk_item_calibration_counts`, `validate_and_compile_card`; calls `CompiledInstrument`, `classify_outcome`, `ensure_builtin_families`, `information_rate`, `instrument_expected_information_gain`, `instrument_observation_likelihoods`, `instrument_predictive_information_gain`, `map_episode_labels_to_slots`, `record_real_observation_counts`, `shrunk_item_calibration_counts`, `validate_and_compile_card`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `H_OTHER`, `build_episode_hypothesis_set`, `generic_bucket_marginals`, `item_observation_context`, `strong_prior_claim`, `triage_reason_for_label`; calls `build_episode_hypothesis_set`, `generic_bucket_marginals`, `item_observation_context`, `strong_prior_claim`, `triage_reason_for_label`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `applicable_families`, `generate_instances_for_episode`; calls `applicable_families`, `generate_instances_for_episode`
- [[Reference/Modules/learnloop/diagnosis/probe_outcome_mapping|learnloop.diagnosis.probe_outcome_mapping]] — imports `coarse_class_for_outcome`, `coarse_schema_slug`, `mapping_snapshot`; calls `coarse_class_for_outcome`, `coarse_schema_slug`, `mapping_snapshot`
- [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] — imports `RobustCandidate`, `instrument_ensemble`, `load_pinned_channel`, `pinned_decision_posterior`, `resolve_episode_channel`, `robust_selection`, `use_robust_probe`; calls `RobustCandidate`, `instrument_ensemble`, `load_pinned_channel`, `pinned_decision_posterior`, `resolve_episode_channel`, `robust_selection`, `use_robust_probe`
- [[Reference/Modules/learnloop/diagnosis/probe_targeting|learnloop.diagnosis.probe_targeting]] — imports `open_cause_sets_for_learning_object`, `select_discriminating_instrument`; calls `open_cause_sets_for_learning_object`, `select_discriminating_instrument`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `HypothesisSet`, `item_registry_discrimination`, `resolve_item_irt`, `score_bucket`; calls `HypothesisSet`, `item_registry_discrimination`, `resolve_item_irt`, `score_bucket`
- [[Reference/Modules/learnloop/diagnosis/robust_composition|learnloop.diagnosis.robust_composition]] — imports `robust_eig_per_second`; calls `robust_eig_per_second`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `resolve_head`; calls `resolve_head`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `required_facets`; calls `required_facets`
- [[Reference/Modules/learnloop/scheduling/controller_ownership|learnloop.scheduling.controller_ownership]] — imports `module`; calls `StagedOwnedAdministrationRefused`, `is_learning_object_staged_owned`, `staged_owned_practice_item_ids`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_reason`; calls `unservable_reason`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/curriculum/confusable_concepts|learnloop.curriculum.confusable_concepts]], [[Reference/Modules/learnloop/curriculum/golden_path_run|learnloop.curriculum.golden_path_run]], [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]], [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] and 14 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_orchestrator.py](../../../../../../tests/test_causal_orchestrator.py) — direct import
  - `test_relocking_an_open_episode_does_not_inherit_its_evidence`
- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — direct import
  - `test_an_open_episode_with_observations_refuses_the_offer_with_a_typed_reason`
- [tests/test_characterization_probe_regrade.py](../../../../../../tests/test_characterization_probe_regrade.py) — direct import
  - `test_deferred_regrade_rewrites_summary_but_posterior_does_not_follow`
- [tests/test_characterization_probe_replay.py](../../../../../../tests/test_characterization_probe_replay.py) — direct import
  - `test_replay_pins_exact_posterior_under_current_default_policy`
  - `test_replay_rebuilds_from_current_grader_policy_not_a_pinned_snapshot`
- [tests/test_characterization_probe_submission.py](../../../../../../tests/test_characterization_probe_submission.py) — direct import
  - `test_composition_and_update_signatures_omit_grader_confidence`
  - `test_exact_posterior_update_for_uniform_prior`
  - `test_exact_posterior_update_with_weight_damping`
  - `test_posterior_delta_identical_across_grader_confidence_values`
- [tests/test_diagnostic_probe_freshness.py](../../../../../../tests/test_diagnostic_probe_freshness.py) — direct import
  - `test_fresh_diagnostic_probe_is_selectable_in_the_probe_episode_branch`
  - `test_probe_selection_hard_excludes_an_already_seen_surface_group`
- [tests/test_dual_authority_administration.py](../../../../../../tests/test_dual_authority_administration.py) — direct import
  - `test_staged_owned_item_never_surfaces_in_probe_slate`
  - `test_unowned_probe_slate_is_byte_identical`
  - `test_wholly_staged_owned_lo_refuses_probe_administration`
- [tests/test_grade_resolution_pipeline.py](../../../../../../tests/test_grade_resolution_pipeline.py) — direct import
  - `test_probe_dual_write_helper_records_diagnostic_grade`
- [tests/test_independent_group_counting.py](../../../../../../tests/test_independent_group_counting.py) — direct import
  - `test_an_unknown_probe_item_stays_distinct_rather_than_collapsing`
  - `test_probe_completion_keys_on_the_group_not_the_authored_string`
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_probe_selection_offers_both_instruments`
- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — direct import
  - `test_starting_instruction_closes_measurement_segment_and_reentry_is_fresh`
- [tests/test_p2_leakage_suite.py](../../../../../../tests/test_p2_leakage_suite.py) — direct import
- [tests/test_probe_audit.py](../../../../../../tests/test_probe_audit.py) — direct import
  - `test_replay_audit_detects_a_self_consistent_but_wrong_posterior_transition`
  - `test_shadow_rankings_are_logged_and_reported`
- [tests/test_probe_block_end.py](../../../../../../tests/test_probe_block_end.py) — direct import
  - `test_block_end_payload_carries_open_set_evaluation`
  - `test_block_end_releases_feedback_and_routes_ordinary_practice`
  - `test_block_end_repair_consultation_is_idempotent`
  - `test_block_end_routes_diagnosed_gap_to_typed_tutoring_transition`
  - `test_continuing_episode_opens_fresh_segment_at_block_end`
  - `test_end_diagnostic_block_noop_on_terminal_episode`
  - `test_followup_and_normalization_defer_to_block_end`
  - `test_in_block_failure_gets_decision_receipt_at_block_end_not_before`
  - `test_open_set_trigger_fires_at_threshold_with_dedup`
  - `test_ordinary_attempt_outside_block_still_normalizes`
- [tests/test_probe_dialogue.py](../../../../../../tests/test_probe_dialogue.py) — direct import
  - `test_dialogue_observation_replays_to_its_persisted_weighted_posterior`
  - `test_dialogue_turns_persist_presentation_attempt_observation`
- [tests/test_probe_episodes.py](../../../../../../tests/test_probe_episodes.py) — direct import
  - `test_budget_exhaustion_completes_episode`
  - `test_consumed_presentation_cannot_qualify_second_attempt`
  - `test_declared_dont_know_keeps_probe_measurement_type`
  - `test_episode_entry_locks_actionable_set_with_open_set_mass`
  - `test_exam_attempts_do_not_advance_probe`
  - `test_exhausted_instrument_pool_parks_episode_with_generation_need`
  - `test_hinted_probe_attempt_is_contaminated_and_never_completes`
  - `test_item_excluded_from_live_slate_cannot_be_committed_as_a_probe`
  - `test_labels_map_through_open_set_abstention`
  - `test_multi_confusable_set_keeps_instrument_eligible`
  - `test_new_misconception_triggers_unique_reprobe_episode`
  - `test_next_probe_item_peeks_the_unused_surface_without_committing`
  - `test_ordinary_and_hinted_attempts_never_advance_but_update_belief`
  - `test_pending_items_episode_keeps_lo_schedulable_with_belief_updates`
  - `test_presentation_activity_disqualification_precedes_live_projection`
  - `test_presentation_snapshot_matches_compiled_instrument`
  - `test_qualifying_observations_are_counted_per_session`
  - `test_retried_submission_is_idempotent`
  - `test_scheduler_slate_atomically_commits_its_selected_probe_presentation`
  - `test_selected_diagnostic_probe_creates_exactly_one_observation`
  - `test_self_graded_provider_parks_episode_without_observation`
  - `test_stop_and_teach_ends_measurement_and_segments_evidence`
  - `test_two_independent_surfaces_complete_a_stable_episode`
  - `test_unmatched_systematic_signature_raises_open_set_probability`
- [tests/test_probe_hierarchy.py](../../../../../../tests/test_probe_hierarchy.py) — direct import
  - `test_resolve_instrument_reads_calibrated_rows`
- [tests/test_probe_instance_generation.py](../../../../../../tests/test_probe_instance_generation.py) — direct import
  - `test_generation_is_idempotent`
  - `test_provisional_family_instances_park_behind_review`
  - `test_trusted_family_generation_unparks_episode_with_provenance`
- [tests/test_probe_llm_instances.py](../../../../../../tests/test_probe_llm_instances.py) — direct import
  - `test_gate_rejected_llm_surfaces_fall_back_to_parametric`
  - `test_llm_surfaces_config_disable`
  - `test_llm_surfaces_generate_with_provenance`
  - `test_provider_failure_falls_back_to_parametric`
- [tests/test_probe_longform_families.py](../../../../../../tests/test_probe_longform_families.py) — direct import
  - `test_generation_produces_derivation_instance_with_obligation_rubric`
  - `test_longform_observation_records_trace_and_bounded_mass`
- [tests/test_probe_orchestration_remainder.py](../../../../../../tests/test_probe_orchestration_remainder.py) — direct import
  - `test_answer_confidence_is_logged_on_attempt_and_observation`
  - `test_onboarding_ceiling_deactivates_probes_until_practice_starts`
  - `test_planner_shadow_report_summarizes_logged_components`
  - `test_repeated_prediction_errors_reopen_probing`
  - `test_routine_planner_shadow_ranks_open_episodes`
  - `test_session_cap_blocks_further_probe_serving`
  - `test_stale_uncertainty_reprobe_after_configured_days`
  - `test_stale_uncertainty_respects_variance_floor`
- [tests/test_probe_policy.py](../../../../../../tests/test_probe_policy.py) — direct import
  - `test_family_redundancy_penalty_after_observation`
  - `test_precommitted_block_commits_all_before_answers`
  - `test_sequential_selection_conditions_on_observed_posterior`
- [tests/test_probe_pool_empty.py](../../../../../../tests/test_probe_pool_empty.py) — direct import
  - `test_never_authored_pool_is_distinguished_from_excluded_as_seen`
  - `test_pending_items_episode_with_fresh_surfaces_is_not_an_empty_pool`
- [tests/test_probe_predictive_eig.py](../../../../../../tests/test_probe_predictive_eig.py) — direct import
  - `test_hypothesis_fallback_when_target_set_inadequate`
  - `test_predictive_objective_is_default_and_persisted`
- [tests/test_probe_remint.py](../../../../../../tests/test_probe_remint.py) — direct import
  - `test_remint_surface_group_stays_probe_ineligible`
- [tests/test_probe_robust_cutover.py](../../../../../../tests/test_probe_robust_cutover.py) — direct import
  - `test_administration_snapshots_probe_coarse_mapping`
  - `test_decision_snapshot_byte_stable_after_model_activation_with_receipt`
  - `test_episode_pins_channel_and_products_are_deterministic`
  - `test_evaluate_completion_abstains_on_planted_indistinguishable_case`
  - `test_legacy_mvp07_episode_is_byte_identical`
  - `test_robust_selection_abstains_on_indistinguishable_candidates`
  - `test_selection_and_update_share_the_pinned_channel_hash`
- [tests/test_probe_surface_mint.py](../../../../../../tests/test_probe_surface_mint.py) — direct import
  - `test_mint_refuses_a_surface_group_the_learner_has_seen`
  - `test_minted_surface_serves_through_the_probe_branch_and_is_single_use`
- [tests/test_scheduler_probe_eig.py](../../../../../../tests/test_scheduler_probe_eig.py) — direct import
  - `test_short_session_keeps_probe_eig_when_probe_is_only_reason`
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_inspector_opens_probe_episode_drilldown`
- [tests/test_sidecar_probe.py](../../../../../../tests/test_sidecar_probe.py) — direct import
  - `test_get_next_probe_item_reflects_the_open_episode`
  - `test_probe_contract_requires_grading_provider_and_parks_episode`
  - `test_stop_probe_diagnosing_converts_episode`
- [tests/test_sidecar_tutor_qa.py](../../../../../../tests/test_sidecar_tutor_qa.py) — direct import
  - `test_preview_tutor_opening_after_stop_diagnosing`
- [tests/test_today_surfaces.py](../../../../../../tests/test_today_surfaces.py) — direct import
  - `test_overconfidence_probe_origin_survives_target_selection`
  - `test_overconfidence_probe_records_origin`
  - `test_probe_episode_without_origin_is_null`

## Modification guidance

- Change probe episodes policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
