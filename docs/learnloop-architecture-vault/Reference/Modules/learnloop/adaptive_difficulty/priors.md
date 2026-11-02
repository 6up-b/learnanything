---
title: "learnloop.adaptive_difficulty.priors"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/priors.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/priors.py"
source_commit: "c57b2057798723352479f5c1b2cd134fcf96a807"
source_commit_timestamp: "2026-10-18T21:18:46-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.priors module"
  - "src/learnloop/adaptive_difficulty/priors.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.priors`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.priors` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: AD's a-priori, versioned constants (spec_adaptive_difficulty_v1 §5.5, §5.10; field F5, A5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py) |
| Source lines | 304 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `c57b2057798723352479f5c1b2cd134fcf96a807` |
| Commit timestamp | `2026-10-18T21:18:46-04:00` |

## Public API

- `class HyperPoint` ([source](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 58)
  - `uniform(self) -> bool` (line 64; public)
  - `key(self) -> str` (line 67; public)
  - `as_dict(self) -> dict[str, float]` (line 70; public)
- `hyper_grid(version: str=HYPER_VERSION) -> tuple[HyperPoint, ...]` ([source](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 74) — The grid in its fixed order (split, then coupling, then implication).
- `uniform_points(grid: Iterable[HyperPoint]) -> tuple[HyperPoint, ...]` ([source](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 87)
- `offset_variance(split: float) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 94) — The facet and cell offsets' prior variance: the cold-start variance's remainder, halved.
- `feature_coding(features: Mapping[str, Any] | None) -> dict[str, float]` ([source](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 203) — ``φ(x)``: the β coordinates with coefficient 1 for this tuple (relative to ``x_ref``).
- `features_complete(features: Mapping[str, Any] | None) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 241)
- `prior_demand(features: Mapping[str, Any] | None) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 247) — ``β̄·φ(x)`` at the prior means (display and sims only; never certification, A11).
- `versions() -> dict[str, str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 254)

### Module constants

- `PRIORS_VERSION` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 24)
- `HYPER_VERSION` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 25)
- `HYPER_FINE_VERSION` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 26)
- `FEATURE_SCHEMA` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 27)
- `CAPABILITIES` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 29)
- `A` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 33)
- `LAPSE` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 34)
- `KAPPA` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 35)
- `TAU0` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 36)
- `SIGMA_LATENCY` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 37)
- `WARMTH_HOURS` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 38)
- `DRIFT_PER_DAY` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 39)
- `MAX_LOADINGS` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 40)
- `MAX_COUPLED` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 41)
- `DOSE_SCALES` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 42)
- `COLD_START_VARIANCE` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 43)
- `LO_VIEW_SPLIT` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 44)
- `SUCCESS` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 47)
- `PARTIAL` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 48)
- `SPLITS` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 52)
- `COUPLINGS` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 53)
- `IMPLICATIONS` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 54)
- `LO_VIEW_POINT` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 91)
- `PSI_PRIORS` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 102)
- `BETA_PRIORS` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 111)
- `BETA_NAMES` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 131)
- `ALPHA_PRIORS` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 134)
- `ALPHA_V1_PRIOR` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 139)
- `BASE_SIGNALS` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 140)
- `GAMMA_PRIOR` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 142)
- `ZETA_PRIOR` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 143)
- `READING_KINDS` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 145)
- `READING_PRIORS` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 147)
- `VERDICT_PRIORS` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 152)
- `VERDICT_CLASSES` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 156)
- `RATING_PRIORS` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 159)
- `TIMING_PRIORS` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 164)
- `RATINGS` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 168)
- `REFERENCE_TUPLE` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 172)
- `TRANSFER_ORDER` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 180)
- `SPAN_ORDER` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 181)
- `SCAFFOLDING_VALUES` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 182)
- `RESPONSE_VALUES` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 183)
- `MODELLED_DIMENSIONS` ([src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 184)

### Explicit exports

`__all__` declares:

- `A`
- `ALPHA_PRIORS`
- `ALPHA_V1_PRIOR`
- `BASE_SIGNALS`
- `BETA_NAMES`
- `BETA_PRIORS`
- `CAPABILITIES`
- `COLD_START_VARIANCE`
- `DOSE_SCALES`
- `DRIFT_PER_DAY`
- `FEATURE_SCHEMA`
- `GAMMA_PRIOR`
- `HYPER_FINE_VERSION`
- `HYPER_VERSION`
- `HyperPoint`
- `KAPPA`
- `LAPSE`
- `LO_VIEW_POINT`
- `LO_VIEW_SPLIT`
- `MAX_COUPLED`
- `MAX_LOADINGS`
- `MODELLED_DIMENSIONS`
- `PARTIAL`
- `PRIORS_VERSION`
- `PSI_PRIORS`
- `RATINGS`
- `RATING_PRIORS`
- `READING_KINDS`
- `READING_PRIORS`
- `REFERENCE_TUPLE`
- `SIGMA_LATENCY`
- `SUCCESS`
- `TAU0`
- `TIMING_PRIORS`
- `VERDICT_CLASSES`
- `VERDICT_PRIORS`
- `WARMTH_HOURS`
- `ZETA_PRIOR`
- `feature_coding`
- `features_complete`
- `hyper_grid`
- `offset_variance`
- `prior_demand`
- `uniform_points`
- `versions`

## Internal implementation anchors

- `_complexity(value: Any) -> int | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 187)
- `_tools(value: Any) -> set[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/priors.py), line 195)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]] — imports `module`; statically calls `feature_coding`
- [[Reference/Modules/learnloop/adaptive_difficulty/dose_report|learnloop.adaptive_difficulty.dose_report]] — imports `module`
- [[Reference/Modules/learnloop/adaptive_difficulty/model|learnloop.adaptive_difficulty.model]] — imports `module`
- [[Reference/Modules/learnloop/adaptive_difficulty/outcomes|learnloop.adaptive_difficulty.outcomes]] — imports `module`
- [[Reference/Modules/learnloop/adaptive_difficulty/predict|learnloop.adaptive_difficulty.predict]] — imports `module`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `module`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; statically calls `hyper_grid`, `uniform_points`, `versions`
- [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]] — imports `module`; statically calls `versions`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `module`; statically calls `versions`
- [[Reference/Modules/learnloop/adaptive_difficulty/state|learnloop.adaptive_difficulty.state]] — imports `module`; statically calls `feature_coding`
- [[Reference/Modules/learnloop/sim/ad_gates|learnloop.sim.ad_gates]] — imports `module`; statically calls `hyper_grid`
- [[Reference/Modules/learnloop/sim/ad_synthetic|learnloop.sim.ad_synthetic]] — imports `module`; statically calls `feature_coding`, `hyper_grid`, `offset_variance`, `uniform_points`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]], [[Reference/Modules/learnloop/adaptive_difficulty/dose_report|learnloop.adaptive_difficulty.dose_report]], [[Reference/Modules/learnloop/adaptive_difficulty/model|learnloop.adaptive_difficulty.model]], [[Reference/Modules/learnloop/adaptive_difficulty/outcomes|learnloop.adaptive_difficulty.outcomes]], [[Reference/Modules/learnloop/adaptive_difficulty/predict|learnloop.adaptive_difficulty.predict]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_sim.py](../../../../../../tests/test_ad23_sim.py) — direct import
  - `test_hyperparameters_learned_on_synthetic_vaults`
- [tests/test_ad2_model.py](../../../../../../tests/test_ad2_model.py) — direct import
  - `test_joint_attempt_factor_integrates_residual_once`
  - `test_overclaimed_features_do_not_lower_demand_estimate`
  - `test_rating_subarm_off_is_identical_to_base`
  - `test_trivial_success_barely_moves_ability`
- [tests/test_ad3_dose_arm.py](../../../../../../tests/test_ad3_dose_arm.py) — direct import
  - `test_cant_tell_exactly_when_the_interval_is_wide_or_minutes_unknown`
  - `test_recommendations_never_act`
- [tests/test_ad3_reading.py](../../../../../../tests/test_ad3_reading.py) — direct import
  - `test_each_kind_raises_the_next_draw_by_its_next_increment`
  - `test_reading_reaches_loading_items_and_coupled_topics`
  - `test_reading_self_check_switch_restores_d20_and_is_moot_without_reading`
  - `test_self_check_verdict_shifts_prediction_never_evidence`
- [tests/test_ad3_subject_view.py](../../../../../../tests/test_ad3_subject_view.py) — direct import
  - `test_a_proposal_recorded_after_a_coordinate_exists_changes_no_earlier_state`
  - `test_coupling_is_prediction_only`
  - `test_hyperparameters_learned_and_replayable`
  - `test_subject_view_mixture_keeps_propensities_exact`

## Modification guidance

- Make changes here when the responsibility remains priors within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/priors.py](../../../../../../src/learnloop/adaptive_difficulty/priors.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
