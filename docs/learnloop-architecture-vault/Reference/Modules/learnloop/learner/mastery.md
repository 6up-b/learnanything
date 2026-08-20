---
title: "learnloop.learner.mastery"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/mastery.py"
source_paths:
  - "src/learnloop/learner/mastery.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.mastery module"
  - "src/learnloop/learner/mastery.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.mastery`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.mastery` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Per-LO mastery EKF (spec_irt_difficulty.md §4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/mastery.py](../../../../../../src/learnloop/learner/mastery.py) |
| Source lines | 649 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class MasteryObservation` ([source](../../../../../../src/learnloop/learner/mastery.py), line 34)
- `class MasteryDisplay` ([source](../../../../../../src/learnloop/learner/mastery.py), line 73)
- `class IrtObservation` ([source](../../../../../../src/learnloop/learner/mastery.py), line 82) — The 2PL link linearized at the prior mean (spec_irt_difficulty.md §4.1).
- `class MasteryObservationTrace` ([source](../../../../../../src/learnloop/learner/mastery.py), line 98) — Full IRT picture of one mastery update, for debug logging (spec §7.1).
- `sigmoid(value: float) -> float` ([source](../../../../../../src/learnloop/learner/mastery.py), line 127)
- `logit(value: float) -> float` ([source](../../../../../../src/learnloop/learner/mastery.py), line 131)
- `display_mastery(state: MasteryState) -> MasteryDisplay` ([source](../../../../../../src/learnloop/learner/mastery.py), line 136)
- `initial_mastery_state(learning_object_id: str, algorithm_version: str, now_iso: str, *, logit_variance: float=1.0) -> MasteryState` ([source](../../../../../../src/learnloop/learner/mastery.py), line 154)
- `initial_mastery_state_for_learning_object(vault, repository, learning_object_id: str, now_iso: str) -> MasteryState` ([source](../../../../../../src/learnloop/learner/mastery.py), line 172)
- `apply_claim_evidence(state: MasteryState, *, claimed_level: float, prior_pseudo_count: float, now_iso: str) -> MasteryState` ([source](../../../../../../src/learnloop/learner/mastery.py), line 204) — Precision-weighted merge of a learner claim into an existing state.
- `reanchor_mastery_from_claim(vault, repository, learning_object_id: str, *, claimed_level: float, prior_pseudo_count: float, now_iso: str) -> MasteryState` ([source](../../../../../../src/learnloop/learner/mastery.py), line 240) — Make a newly written claim take effect on an already-materialized LO.
- `covering_learner_claim(vault, repository, learning_object_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/learner/mastery.py), line 272)
- `observation_weight(observation: MasteryObservation) -> float` ([source](../../../../../../src/learnloop/learner/mastery.py), line 321) — Reliability weight of an observation (spec §4.1).
- `predicted_logit_variance(prior: MasteryState, observation: MasteryObservation, config: MasteryConfig) -> float` ([source](../../../../../../src/learnloop/learner/mastery.py), line 342) — ``P_pred = min(P + sigma2_drift * days_since, p_max)`` — prior variance grown by drift.
- `item_irt_params(item: 'PracticeItem | None', learning_object: 'LearningObject | None', config: MasteryConfig) -> tuple[float, float]` ([source](../../../../../../src/learnloop/learner/mastery.py), line 356) — Resolve ``(a, b)`` for an item from **static** authored/LLM fields (spec §4.3).
- `resolve_item_irt_params(item: 'PracticeItem | None', learning_object: 'LearningObject | None', config: MasteryConfig, item_state: 'ItemParameterState | None'=None) -> tuple[float, float]` ([source](../../../../../../src/learnloop/learner/mastery.py), line 381) — (a, b) with the empirical-Bayes posterior b when enabled, else authored.
- `update_item_difficulty(prior: 'ItemParameterState | None', *, practice_item_id: str, authored_b: float, item_a: float, learner_mu_posterior: float, observation: MasteryObservation, config: MasteryConfig, algorithm_version: str, updated_at: str) -> 'ItemParameterState'` ([source](../../../../../../src/learnloop/learner/mastery.py), line 400) — Alternating conditional EKF step on item difficulty b.
- `irt_observation(item_a: float, item_b: float, prior: MasteryState, observation: MasteryObservation, config: MasteryConfig) -> IrtObservation` ([source](../../../../../../src/learnloop/learner/mastery.py), line 450) — Linearize the 2PL link at the prior mean (spec §4.1).
- `update_mastery(prior: MasteryState, observation: MasteryObservation, config: MasteryConfig, algorithm_version: str, *, item_a: float=1.0, item_b: float=0.0) -> MasteryState` ([source](../../../../../../src/learnloop/learner/mastery.py), line 486)
- `update_mastery_traced(prior: MasteryState, observation: MasteryObservation, config: MasteryConfig, algorithm_version: str, *, item_a: float=1.0, item_b: float=0.0, item_id: str='') -> tuple[MasteryState, MasteryObservationTrace]` ([source](../../../../../../src/learnloop/learner/mastery.py), line 501) — Difficulty-aware mastery update returning the posterior plus an IRT trace.

## Internal implementation anchors

- `_claim_covers_learning_object(claim: dict[str, Any], learning_object) -> bool` ([source](../../../../../../src/learnloop/learner/mastery.py), line 286)
- `_claim_rank(claim: dict[str, Any]) -> tuple[int, float, float, str, str]` ([source](../../../../../../src/learnloop/learner/mastery.py), line 300)
- `_iso(value: datetime) -> str` ([source](../../../../../../src/learnloop/learner/mastery.py), line 317)
- `_ekf_update_mastery(prior: MasteryState, observation: MasteryObservation, config: MasteryConfig, algorithm_version: str, item_a: float, item_b: float, item_id: str) -> tuple[MasteryState, MasteryObservationTrace]` ([source](../../../../../../src/learnloop/learner/mastery.py), line 522)
- `_legacy_update_mastery(prior: MasteryState, observation: MasteryObservation, config: MasteryConfig, algorithm_version: str, item_a: float, item_b: float, item_id: str) -> tuple[MasteryState, MasteryObservationTrace]` ([source](../../../../../../src/learnloop/learner/mastery.py), line 597) — The pre-IRT logit-space Kalman update, reproduced bit-for-bit (spec §6.2).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `MasteryObservation`, `MasteryObservationTrace`, `display_mastery`, `initial_mastery_state_for_learning_object`, `item_irt_params`, `resolve_item_irt_params`, `update_item_difficulty`, `update_mastery_traced`; statically calls `MasteryObservation`, `display_mastery`, `initial_mastery_state_for_learning_object`, `item_irt_params`, `resolve_item_irt_params`, `update_item_difficulty`, `update_mastery_traced`
- [[Reference/Modules/learnloop/attempts/surprise|learnloop.attempts.surprise]] — imports `MasteryObservation`, `irt_observation`, `logit`, `observation_weight`, `sigmoid`; statically calls `irt_observation`, `logit`, `observation_weight`, `sigmoid`
- [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] — imports `reanchor_mastery_from_claim`; statically calls `reanchor_mastery_from_claim`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `covering_learner_claim`, `display_mastery`; statically calls `covering_learner_claim`, `display_mastery`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `display_mastery`, `reanchor_mastery_from_claim`; statically calls `display_mastery`, `reanchor_mastery_from_claim`
- [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] — imports `covering_learner_claim`, `display_mastery`; statically calls `covering_learner_claim`, `display_mastery`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `covering_learner_claim`, `initial_mastery_state_for_learning_object`, `sigmoid`; statically calls `covering_learner_claim`, `initial_mastery_state_for_learning_object`, `sigmoid`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `covering_learner_claim`, `initial_mastery_state_for_learning_object`, `item_irt_params`, `sigmoid`; statically calls `covering_learner_claim`, `initial_mastery_state_for_learning_object`, `item_irt_params`, `sigmoid`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `covering_learner_claim`; statically calls `covering_learner_claim`
- [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]] — imports `covering_learner_claim`; statically calls `covering_learner_claim`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `display_mastery`; statically calls `display_mastery`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `display_mastery`; statically calls `display_mastery`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `resolve_item_irt_params`; statically calls `resolve_item_irt_params`
- [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]] — imports `item_irt_params`; statically calls `item_irt_params`
- [[Reference/Modules/learnloop/sim/metrics|learnloop.sim.metrics]] — imports `display_mastery`; statically calls `display_mastery`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `display_mastery`; statically calls `display_mastery`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `initial_mastery_state_for_learning_object`; statically calls `initial_mastery_state_for_learning_object`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `initial_mastery_state_for_learning_object`; statically calls `initial_mastery_state_for_learning_object`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `sigmoid`; statically calls `sigmoid`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `sigmoid`; statically calls `sigmoid`
- [[Reference/Modules/learnloop/tui/screens/today|learnloop.tui.screens.today]] — imports `sigmoid`; statically calls `sigmoid`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `display_mastery`; statically calls `display_mastery`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `display_mastery`; statically calls `display_mastery`
- [[Reference/Modules/learnloop_sidecar/handlers/graph|learnloop_sidecar.handlers.graph]] — imports `display_mastery`; statically calls `display_mastery`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `display_mastery`, `sigmoid`; statically calls `display_mastery`, `sigmoid`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `display_mastery`; statically calls `display_mastery`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `display_mastery`, `sigmoid`; statically calls `display_mastery`, `sigmoid`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/evidence|learnloop.attempts.evidence]] — imports `attempt_evidence_mass`; calls `attempt_evidence_mass`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `MasteryConfig`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ItemParameterState`, `MasteryState`; calls `ItemParameterState`, `MasteryState`
- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `clamp`; calls `clamp`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LearningObject`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/surprise|learnloop.attempts.surprise]], [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]], [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] and 22 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_characterization_mastery_reliability.py](../../../../../../tests/test_characterization_mastery_reliability.py) — direct import
- [tests/test_cold_start_revision.py](../../../../../../tests/test_cold_start_revision.py) — direct import
  - `test_channel_doubt_never_inverts_direction_on_easy_items`
  - `test_evidence_rich_state_moves_less`
  - `test_interpretation_variance_broadens_not_blocks`
  - `test_quality_state_pays_for_assessment_side_error`
  - `test_soft_score_replaces_raw_fraction`
  - `test_zero_evidence_state_gets_full_merge_weight`
- [tests/test_evidence_config.py](../../../../../../tests/test_evidence_config.py) — direct import
  - `test_override_flows_through_resolvers`
- [tests/test_irt_difficulty.py](../../../../../../tests/test_irt_difficulty.py) — direct import
  - `test_default_step_cap_leaves_normal_attempts_untouched`
  - `test_difficulty_defaults_to_zero_when_unset`
  - `test_difficulty_falls_back_to_learning_object_prior`
  - `test_difficulty_from_prior_toggle_pins_b_to_default`
  - `test_difficulty_is_clamped_to_b_abs_max`
  - `test_difficulty_resolves_practice_item_first`
  - `test_enabled_ekf_differs_from_legacy_on_target`
  - `test_kalman_gain_well_defined_at_extreme_difficulty`
  - `test_kill_switch_ignores_difficulty_entirely`
  - `test_kill_switch_reproduces_logit_kalman_math`
  - `test_mu_clamp_bounds_the_mean`
  - `test_step_cap_limits_overshoot_on_broad_prior`
  - `test_sustained_brutal_corrects_do_not_drift_past_mu_abs_max`
- [tests/test_item_parameters.py](../../../../../../tests/test_item_parameters.py) — direct import
  - `test_resolver_uses_posterior_only_when_enabled`
- [tests/test_mastery.py](../../../../../../tests/test_mastery.py) — direct import
  - `test_display_mastery_formula`
  - `test_drift_increases_movement_after_long_gap`
  - `test_hint_dampening_reduces_update`
  - `test_low_confidence_moves_mean_less_than_high_confidence`
  - `test_positive_score_raises_mean`
  - `test_zero_score_does_not_raise_mean`
- [tests/test_planted_misgrade.py](../../../../../../tests/test_planted_misgrade.py) — direct import
- [tests/test_practice_information.py](../../../../../../tests/test_practice_information.py) — direct import
- [tests/test_primed_attempts.py](../../../../../../tests/test_primed_attempts.py) — direct import
  - `test_cold_attempt_advances_last_evidence_at`
  - `test_primed_attempt_keeps_last_evidence_at_ekf`
  - `test_primed_attempt_keeps_last_evidence_at_legacy`
  - `test_primed_failure_moves_mean_more_than_cold_failure`
  - `test_primed_success_moves_mean_less_than_cold_success`
  - `test_primed_success_shrinks_variance_less`
- [tests/test_state_sync.py](../../../../../../tests/test_state_sync.py) — direct import
  - `test_state_sync_seeds_from_weak_learner_claim_below_probe_threshold`
  - `test_state_sync_uses_strong_learner_claim_for_initial_mastery`
- [tests/test_surprise.py](../../../../../../tests/test_surprise.py) — direct import
- [tests/test_tutor_promotion_w2.py](../../../../../../tests/test_tutor_promotion_w2.py) — direct import
  - `test_high_claim_preserves_mean_and_respects_claim_variance_floor`
  - `test_low_claim_now_seeds_prior`
  - `test_no_claim_leaves_neutral_prior`
  - `test_very_high_claim_matches_native_logit_clamp`

## Modification guidance

- Change mastery policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/mastery.py](../../../../../../src/learnloop/learner/mastery.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
