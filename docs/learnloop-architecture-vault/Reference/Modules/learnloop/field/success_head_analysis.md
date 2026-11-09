---
title: "learnloop.field.success_head_analysis"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/field/success_head_analysis.py"
source_paths:
  - "src/learnloop/field/success_head_analysis.py"
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
  - "learnloop.field.success_head_analysis module"
  - "src/learnloop/field/success_head_analysis.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-field"
---

# `learnloop.field.success_head_analysis`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/field/_package|learnloop.field]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.field.success_head_analysis` exists within [[Reference/Modules/learnloop/field/_package|learnloop.field]] to own the behavior summarized by its module contract: The pre-registered T8 analysis: a harness hook returning aggregates only.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/field/success_head_analysis.py](../../../../../../src/learnloop/field/success_head_analysis.py) |
| Source lines | 312 |
| Owning package | [[Reference/Modules/learnloop/field/_package|learnloop.field]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `make_t8_analysis(*, unavailable: Mapping[str, str] | None=None) -> Callable[[ReplayArrays], dict]` ([source](../../../../../../src/learnloop/field/success_head_analysis.py), line 182) — The pre-registered T8 analysis as a harness hook (aggregates only).
- `summary_lines(analysis: Mapping) -> list[str]` ([source](../../../../../../src/learnloop/field/success_head_analysis.py), line 271) — Aggregate-only markdown for the top of the T8 report.

### Module constants

- `BOOTSTRAP_METHOD` ([src/learnloop/field/success_head_analysis.py](../../../../../../src/learnloop/field/success_head_analysis.py), line 30)

## Internal implementation anchors

- `_bootstrap(arrays: ReplayArrays, differences, clusters) -> dict` ([source](../../../../../../src/learnloop/field/success_head_analysis.py), line 33) — A descriptive percentile item bootstrap, labelled with its method.
- `_comparison(arrays: ReplayArrays, challenger: str, baselines: Iterable[str], *, t_interval: bool=False) -> dict` ([source](../../../../../../src/learnloop/field/success_head_analysis.py), line 39) — e* (the best of ``baselines``) against ``challenger`` on their common attempts.
- `_number(value: float) -> str` ([source](../../../../../../src/learnloop/field/success_head_analysis.py), line 88)
- `_bound(value: float, holds: Callable[[float], bool]) -> str` ([source](../../../../../../src/learnloop/field/success_head_analysis.py), line 92) — ``value`` at 4 significant figures, or as many more as it takes for the printed number to satisfy ``holds``, the comparison the reason states (review F3: 0.0049996 is not "0.005 < δ = 0.005").
- `_rounded_down(value: float) -> str` ([source](../../../../../../src/learnloop/field/success_head_analysis.py), line 103) — ``value`` rounded down to 4 significant figures, so "any δ <= it" stays true.
- `_verdict(comparison: dict, ability_scored: int) -> dict` ([source](../../../../../../src/learnloop/field/success_head_analysis.py), line 111) — The v4 three-way rule on the 95% cluster-robust t interval of the gain.
- `_decision_rule() -> dict` ([source](../../../../../../src/learnloop/field/success_head_analysis.py), line 164) — The rule and constants in force, recorded in every report (the owner monitors δ).
- `_span(interval) -> str` ([source](../../../../../../src/learnloop/field/success_head_analysis.py), line 259)
- `_t_interval(gain: Mapping) -> str` ([source](../../../../../../src/learnloop/field/success_head_analysis.py), line 263)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]] — imports `make_t8_analysis`, `summary_lines`; statically calls `make_t8_analysis`, `summary_lines`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/field/evaluation|learnloop.field.evaluation]] — imports `CLUSTER_T_METHOD`, `ReplayArrays`, `_loss`, `cluster_t_interval`, `paired_bootstrap`; calls `_loss`, `cluster_t_interval`, `paired_bootstrap`
- [[Reference/Modules/learnloop/field/success_head|learnloop.field.success_head]] — imports `EXPLICIT_ARMS`, `GATED_ARMS`, `LLM_ARMS`, `PREREGISTRATION`, `PRIMARY_ARM`, `preregistration_hash`; calls `preregistration_hash`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `decimal`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_success_head.py](../../../../../../tests/test_success_head.py) — direct import
  - `test_a_real_gain_below_delta_is_kill_with_its_reason`
  - `test_delta_and_the_interval_are_recorded_in_every_report`
  - `test_each_secondary_verdict_gates_the_next_comparison`
  - `test_embeddings_add_value_opens_the_gate`
  - `test_every_interval_in_the_t8_report_clusters_items_and_names_its_method`
  - `test_kill_rule_picks_the_best_explicit_arm_and_kills_without_a_gain`
  - `test_llm_arms_are_descriptive_against_explicit_and_embedding_arms`
  - `test_no_interval_is_insufficient_data_with_the_reason`
  - `test_only_embeddings_add_value_opens_the_gate`
  - `test_partial_coverage_is_flagged`
  - `test_preregistration_v4_changes_the_hash_and_every_report_carries_it`
  - `test_t8_refuses_a_harness_that_resamples_attempts`
  - `test_the_flipping_delta_is_where_the_verdict_changes`
  - `test_the_harness_hands_item_clusters_and_t8_resamples_items`
  - `test_the_primary_comparison_is_never_reported_with_a_second_interval`
  - `test_the_report_shows_how_far_the_data_is_from_a_decision`
  - `test_the_verdict_at_the_boundaries_never_contradicts_its_reason`
  - `test_unavailable_arms_and_deviations_are_reported`

## Modification guidance

- Make changes here when the responsibility remains success head analysis within learnloop.field; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/field/success_head_analysis.py](../../../../../../src/learnloop/field/success_head_analysis.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
