---
title: "learnloop.sim.ad_memory_synthetic"
type: "module-reference"
status: "current"
refactor_status: "EVALUATION"
version: "1.0.0"
source_path: "src/learnloop/sim/ad_memory_synthetic.py"
source_paths:
  - "src/learnloop/sim/ad_memory_synthetic.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.sim"
layer: "simulation"
concepts:
  - "Learning System"
workflows:
  []
aliases:
  - "learnloop.sim.ad_memory_synthetic module"
  - "src/learnloop/sim/ad_memory_synthetic.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/evaluation"
  - "layer/simulation"
  - "package/learnloop-sim"
---

# `learnloop.sim.ad_memory_synthetic`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.sim.ad_memory_synthetic` exists within [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] to own the behavior summarized by its module contract: Synthetic-only ADM experiment; design values: docs/reviews/adm0-preregistration.md.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/sim/ad_memory_synthetic.py](../../../../../../src/learnloop/sim/ad_memory_synthetic.py) |
| Source lines | 468 |
| Owning package | [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] |
| Architecture layer | `simulation` |
| Refactor status | `EVALUATION` |

> [!note] Evaluation-only authority
> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.

## Public API

- `class Candidate` ([source](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 33)
- `candidates(subject: bool) -> dict[str, Candidate]` ([source](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 45)
- `class Event` ([source](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 63)
  - `spec(self) -> ItemSpec` (line 74; public)
- `schedule() -> tuple[Event, ...]` ([source](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 78)
- `class MemoryInputs` ([source](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 101)
- `class ReviewFold` ([source](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 107) — Synthetic resolved reviews only; strict pre-serve lookups, even with ties/future rows.
  - `__init__(self, n: int)` (line 110; internal)
  - `previous(self, key: str, at: float) -> tuple[float, list[MemoryState]] | None` (line 114; public)
  - `inputs(self, event: Event, *, multiplier: float=1.0) -> MemoryInputs` (line 118; public)
  - `append(self, event: Event, categories: np.ndarray) -> None` (line 131; public)
- `logit(p: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 142)
- `class World` ([source](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 148)
- `class Dataset` ([source](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 166)
  - `n(self) -> int` (line 180; public)
- `generate(world: str, seed: str, *, n: int=LEARNERS) -> Dataset` ([source](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 184)
- `family_name(family: str) -> str` ([source](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 222)
- `item_name(item: str) -> str` ([source](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 226)
- `class Prediction` ([source](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 231)
- `class MemoryArm` ([source](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 241) — Real AD bank with candidate coordinates; no production configuration is changed.
  - `__init__(self, n: int, *, subject: bool, candidate: Candidate | None, full_grid: bool=False)` (line 244; internal)
  - `append_coordinate(self, name: str, mean: float, variance: float | np.ndarray) -> None` (line 264; public)
  - `rows(self, values: np.ndarray) -> np.ndarray` (line 268; public)
  - `mix(self, values: np.ndarray) -> np.ndarray` (line 271; public)
  - `mixture_moments(self, mean: np.ndarray, var: np.ndarray) -> tuple[np.ndarray, np.ndarray]` (line 275; public)
  - `prepare(self, event: Event) -> None` (line 279; public)
  - `base_projection(self, event: Event) -> tuple[np.ndarray, np.ndarray]` (line 282; public)
  - `predict(self, event: Event, inputs: MemoryInputs) -> Prediction` (line 301; public)
  - `observe(self, event: Event, prediction: Prediction, category: np.ndarray, *, eligible: bool=True, learning: bool=True) -> None` (line 317; public)
  - `step(self, event: Event, inputs: MemoryInputs, category: np.ndarray, *, eligible: bool=True) -> Prediction` (line 356; public)
  - `coordinate_moments(self, name: str) -> tuple[np.ndarray, np.ndarray]` (line 361; public)
  - `ability_moments(self) -> tuple[np.ndarray, np.ndarray]` (line 364; public)
  - `curve_moments(self, hours: float) -> tuple[np.ndarray, np.ndarray]` (line 368; public)
- `recovery_snapshot(data: Dataset, arm: MemoryArm, index: int) -> dict` ([source](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 378)
- `class ReplayResult` ([source](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 413)
- `replay(data: Dataset, arm: MemoryArm) -> ReplayResult` ([source](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 422)
- `variance_floor(*, effect_scale: float=1.0, steps: int=512) -> dict` ([source](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 437)
- `warmth_check(ladder: tuple[float, ...], hours: float) -> dict` ([source](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 459)

### Module constants

- `SEEDS` ([src/learnloop/sim/ad_memory_synthetic.py](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 23)
- `LEARNERS` ([src/learnloop/sim/ad_memory_synthetic.py](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 24)
- `RHO_SUPPORTS` ([src/learnloop/sim/ad_memory_synthetic.py](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 25)
- `LADDERS` ([src/learnloop/sim/ad_memory_synthetic.py](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 26)
- `CURVE_HOURS` ([src/learnloop/sim/ad_memory_synthetic.py](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 27)
- `Z95` ([src/learnloop/sim/ad_memory_synthetic.py](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 28)
- `CLIP` ([src/learnloop/sim/ad_memory_synthetic.py](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 29)
- `WORLDS` ([src/learnloop/sim/ad_memory_synthetic.py](../../../../../../src/learnloop/sim/ad_memory_synthetic.py), line 157)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/sim/ad_memory_experiment|learnloop.sim.ad_memory_experiment]] — imports `module`; statically calls `Candidate`, `MemoryArm`, `ReviewFold`, `candidates`, `generate`, `replay`, `schedule`, `variance_floor`, `warmth_check`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/model|learnloop.adaptive_difficulty.model]] — imports `module`; calls `Bank`, `band_probability`, `category_probabilities`, `cell_name`
- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `module`; calls `hyper_grid`, `uniform_points`
- [[Reference/Modules/learnloop/adaptive_difficulty/state|learnloop.adaptive_difficulty.state]] — imports `ItemSpec`, `View`; calls `ItemSpec`, `View`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `FSRS6_DEFAULT_WEIGHTS`, `MemoryState`, `Rating`, `apply_review`, `retrievability_array`; calls `apply_review`, `retrievability_array`
- [[Reference/Modules/learnloop/sim/ad_synthetic|learnloop.sim.ad_synthetic]] — imports `rng_for`, `sample_category`; calls `rng_for`, `sample_category`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `math`, `statistics`
- Third party: `numpy`

## Larger workflow participation

No direct learner/operator workflow is assigned. This module is offline, shadow-only, dormant, or a dependency reached only through the static consumers below.

Static participation evidence comes from [[Reference/Modules/learnloop/sim/ad_memory_experiment|learnloop.sim.ad_memory_experiment]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad_memory_simulation.py](../../../../../../tests/test_ad_memory_simulation.py) — direct import
  - `test_drilled_success_does_not_identify_transferable_ability`
  - `test_exact_once_per_surface_increment_in_both_views`
  - `test_full_subject_grid_matches_duplicate_collapsed_grid`
  - `test_no_configuration_or_global_prior_mutation`
  - `test_no_repeat_novel_prediction_matches_predecessor`
  - `test_novel_only_sequence_preserves_predecessor_prediction_and_drift_order`
  - `test_predict_before_update_and_strict_memory_boundary`
  - `test_same_item_joint_variance_floor`
  - `test_sibling_novel_and_singleton_residuals`
  - `test_stable_effects_and_common_random_numbers`
  - `test_warmth_equal_mean_added_variance`

## Modification guidance

- Make changes here when the responsibility remains ad memory synthetic within learnloop.sim; otherwise move the behavior to its owning boundary.
- Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/sim/ad_memory_synthetic.py](../../../../../../src/learnloop/sim/ad_memory_synthetic.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
