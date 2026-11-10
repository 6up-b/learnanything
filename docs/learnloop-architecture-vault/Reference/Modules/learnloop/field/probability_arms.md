---
title: "learnloop.field.probability_arms"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/field/probability_arms.py"
source_paths:
  - "src/learnloop/field/probability_arms.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.field"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.field.probability_arms module"
  - "src/learnloop/field/probability_arms.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-field"
---

# `learnloop.field.probability_arms`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/field/_package|learnloop.field]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.field.probability_arms` exists within [[Reference/Modules/learnloop/field/_package|learnloop.field]] to own the behavior summarized by its module contract: The six ``llm_probability`` harness arms: V1-V3 x {decider, llm} (field §7.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/field/probability_arms.py](../../../../../../src/learnloop/field/probability_arms.py) |
| Source lines | 210 |
| Owning package | [[Reference/Modules/learnloop/field/_package|learnloop.field]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `arm_name(variant: str, judge: str, *, recalibrated: bool=False) -> str` ([source](../../../../../../src/learnloop/field/probability_arms.py), line 43)
- `all_arm_names() -> tuple[str, ...]` ([source](../../../../../../src/learnloop/field/probability_arms.py), line 49)
- `parse_arm_selection(values: Iterable[str]) -> tuple[tuple[str, str], ...]` ([source](../../../../../../src/learnloop/field/probability_arms.py), line 56) — ``all``, ``v2``, ``decider``, ``v3/llm`` (repeatable) -> (variant, judge) pairs.
- `position_key(features: ItemFeatures, history: Sequence[tuple[str, float]]) -> str` ([source](../../../../../../src/learnloop/field/probability_arms.py), line 89) — Where a prediction sits: outcome-free features plus the observed past.
- `clip(p: float) -> float` ([source](../../../../../../src/learnloop/field/probability_arms.py), line 97)
- `fit_intercept(logits: Sequence[float], outcomes: Sequence[float]) -> float` ([source](../../../../../../src/learnloop/field/probability_arms.py), line 110) — MAP intercept shift under a N(0, 1) prior, by Newton's method.
- `class CachedProbabilityArm` ([source](../../../../../../src/learnloop/field/probability_arms.py), line 129) — A store-free point predictor over a prepared probability cache.
  - `__init__(self, *, variant: str, judge: str, probabilities: Mapping[str, float], model: str, provenance: Mapping[str, object] | None=None, recalibrated: bool=False, alias: str | None=None) -> None` (line 135; internal)
  - `aliased(self, name: str) -> 'CachedProbabilityArm'` (line 163; public) — A fresh copy of this arm (no observed past) reported under ``name``.
  - `_raw(self, features: ItemFeatures) -> float` (line 172; internal)
  - `predict(self, features: ItemFeatures) -> float` (line 178; public)
  - `observe(self, row) -> None` (line 184; public)

### Module constants

- `VARIANTS` ([src/learnloop/field/probability_arms.py](../../../../../../src/learnloop/field/probability_arms.py), line 35)
- `JUDGES` ([src/learnloop/field/probability_arms.py](../../../../../../src/learnloop/field/probability_arms.py), line 36)
- `ARM_PREFIX` ([src/learnloop/field/probability_arms.py](../../../../../../src/learnloop/field/probability_arms.py), line 37)
- `RECALIBRATION` ([src/learnloop/field/probability_arms.py](../../../../../../src/learnloop/field/probability_arms.py), line 38)
- `CLIP` ([src/learnloop/field/probability_arms.py](../../../../../../src/learnloop/field/probability_arms.py), line 39)
- `_NEWTON_STEPS` ([src/learnloop/field/probability_arms.py](../../../../../../src/learnloop/field/probability_arms.py), line 40)

### Explicit exports

`__all__` declares:

- `ARM_PREFIX`
- `CLIP`
- `CachedProbabilityArm`
- `JUDGES`
- `RECALIBRATION`
- `VARIANTS`
- `all_arm_names`
- `arm_name`
- `clip`
- `fit_intercept`
- `parse_arm_selection`
- `position_key`

## Internal implementation anchors

- `_digest(value: object) -> str` ([source](../../../../../../src/learnloop/field/probability_arms.py), line 85)
- `_logit(p: float) -> float` ([source](../../../../../../src/learnloop/field/probability_arms.py), line 101)
- `_sigmoid(x: float) -> float` ([source](../../../../../../src/learnloop/field/probability_arms.py), line 105)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/serve_inputs|learnloop.adaptive_difficulty.serve_inputs]] — imports `fit_intercept`; statically calls `fit_intercept`
- [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]] — imports `parse_arm_selection`; statically calls `parse_arm_selection`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `JUDGES`, `arm_name`; statically calls `arm_name`
- [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]] — imports `arm_name`; statically calls `arm_name`
- [[Reference/Modules/learnloop/field/probability_prep|learnloop.field.probability_prep]] — imports `CachedProbabilityArm`, `VARIANTS`, `position_key`; statically calls `CachedProbabilityArm`, `position_key`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/field/types|learnloop.field.types]] — imports `AttemptRow`, `FacetRow`, `ItemFeatures`, `SignalRow`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `math`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/serve_inputs|learnloop.adaptive_difficulty.serve_inputs]], [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]], [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]], [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]], [[Reference/Modules/learnloop/field/probability_prep|learnloop.field.probability_prep]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_probability_arms.py](../../../../../../tests/test_probability_arms.py) — direct import
  - `test_arms_are_off_by_default_and_can_never_be_active`
  - `test_intercept_fit_is_penalized_and_finite`
  - `test_pairwise_comparisons_report_without_recommending`
  - `test_position_key_is_outcome_free_and_tracks_the_observed_past`
  - `test_probabilities_are_clipped_and_validated`
  - `test_recalibration_uses_only_past_predictions`
  - `test_selection_names_and_order`
- [tests/test_probability_prep.py](../../../../../../tests/test_probability_prep.py) — direct import
  - `test_decider_end_to_end_through_the_fake_endpoint`
  - `test_dry_run_and_caps_refuse_before_any_client_call_or_write`
  - `test_llm_judge_metered_route_is_isolated_bounded_and_ledgered`
  - `test_prediction_points_are_exactly_the_harness_positions`
  - `test_switches_and_cache_location_are_enforced`

## Modification guidance

- Make changes here when the responsibility remains probability arms within learnloop.field; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/field/probability_arms.py](../../../../../../src/learnloop/field/probability_arms.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
