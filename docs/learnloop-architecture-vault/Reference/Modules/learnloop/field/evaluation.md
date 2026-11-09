---
title: "learnloop.field.evaluation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/field/evaluation.py"
source_paths:
  - "src/learnloop/field/evaluation.py"
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
  - "learnloop.field.evaluation module"
  - "src/learnloop/field/evaluation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-field"
---

# `learnloop.field.evaluation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/field/_package|learnloop.field]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.field.evaluation` exists within [[Reference/Modules/learnloop/field/_package|learnloop.field]] to own the behavior summarized by its module contract: Store-free, attempt-paired prequential evaluation.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/field/evaluation.py](../../../../../../src/learnloop/field/evaluation.py) |
| Source lines | 836 |
| Owning package | [[Reference/Modules/learnloop/field/_package|learnloop.field]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ReplayArrays` ([source](../../../../../../src/learnloop/field/evaluation.py), line 62) — In-memory scored rows handed to report analyses; never exported.
- `family_arms() -> tuple[str, ...]` ([source](../../../../../../src/learnloop/field/evaluation.py), line 82) — The PF-a report's arm set: incumbent, lo_general, idea_hier and memory arms.
- `report_digest(report: Mapping) -> str` ([source](../../../../../../src/learnloop/field/evaluation.py), line 101) — Content address of an aggregate report (names the families report files).
- `paired_bootstrap(differences, *, samples=1000, seed=0, clusters=None)` ([source](../../../../../../src/learnloop/field/evaluation.py), line 157) — One difference per attempt: the same sampled attempt indexes pair arms.
- `cluster_t_interval(differences, clusters)` ([source](../../../../../../src/learnloop/field/evaluation.py), line 212) — Cluster-robust 95% t interval for the mean over attempts (CR1, df = G − 1).
- `evaluate(rows: Iterable[ObservationRow], *, arms=None, bootstrap_samples=1000, seed=0, config: Mapping | None=None, general_means=None, lo_priors=None, fast_track_q=0.9, fast_track_min_correct=2, switching_margin=0.0, fsrs_weights=None, fsrs_fit_id=None, analyses=None, bootstrap_unit='attempt', pairwise=())` ([source](../../../../../../src/learnloop/field/evaluation.py), line 406) — Return JSON-ready report1/report2/manifest/recommendation aggregates.
- `write_reports(report, output_dir, *, stem='evaluation', title='Learner-field evaluation', preamble=())` ([source](../../../../../../src/learnloop/field/evaluation.py), line 770) — Write the aggregate report to the caller's explicitly chosen directory.

### Module constants

- `HARNESS_VERSION` ([src/learnloop/field/evaluation.py](../../../../../../src/learnloop/field/evaluation.py), line 33)
- `SERVING_ORIGIN_LABELS` ([src/learnloop/field/evaluation.py](../../../../../../src/learnloop/field/evaluation.py), line 37)
- `MEMORY_LIMITATIONS` ([src/learnloop/field/evaluation.py](../../../../../../src/learnloop/field/evaluation.py), line 41)
- `ANSWER_SIGNAL_LIMITATIONS` ([src/learnloop/field/evaluation.py](../../../../../../src/learnloop/field/evaluation.py), line 51)
- `ZERO_SPREAD` ([src/learnloop/field/evaluation.py](../../../../../../src/learnloop/field/evaluation.py), line 143)
- `BOOTSTRAP_UNITS` ([src/learnloop/field/evaluation.py](../../../../../../src/learnloop/field/evaluation.py), line 145)
- `CLUSTER_T_METHOD` ([src/learnloop/field/evaluation.py](../../../../../../src/learnloop/field/evaluation.py), line 209)

## Internal implementation anchors

- `_hash(value: object) -> str` ([source](../../../../../../src/learnloop/field/evaluation.py), line 87)
- `_snapshot_row(row) -> dict` ([source](../../../../../../src/learnloop/field/evaluation.py), line 92) — A row as the data snapshot hashes it.
- `_time(row)` ([source](../../../../../../src/learnloop/field/evaluation.py), line 106)
- `_uses_memory(arm) -> bool` ([source](../../../../../../src/learnloop/field/evaluation.py), line 113)
- `_eligible(row)` ([source](../../../../../../src/learnloop/field/evaluation.py), line 117)
- `_loss(y, p)` ([source](../../../../../../src/learnloop/field/evaluation.py), line 131)
- `_interval(values)` ([source](../../../../../../src/learnloop/field/evaluation.py), line 135)
- `_subset(units, *selections)` ([source](../../../../../../src/learnloop/field/evaluation.py), line 148) — ``units`` narrowed by each selection in turn; None (attempt unit) stays None.
- `_cluster_bootstrap(values, clusters, *, samples, seed)` ([source](../../../../../../src/learnloop/field/evaluation.py), line 174) — Paired percentile bootstrap over clusters (for example items).
- `_auc(y, p)` ([source](../../../../../../src/learnloop/field/evaluation.py), line 254)
- `_metrics(y, p, samples, seed, clusters=None)` ([source](../../../../../../src/learnloop/field/evaluation.py), line 276)
- `_wilson(failures, n)` ([source](../../../../../../src/learnloop/field/evaluation.py), line 297)
- `_paired_miss_improvement(baseline, challenger, *, samples, seed, clusters=None)` ([source](../../../../../../src/learnloop/field/evaluation.py), line 306) — Paired attempt-cluster resampling with each policy's own denominator.
- `_known_probability(arm, lo_id)` ([source](../../../../../../src/learnloop/field/evaluation.py), line 335)
- `_groups(rows)` ([source](../../../../../../src/learnloop/field/evaluation.py), line 350) — Validate a complete attempt+facet stream before any arm is called.
- `_bootstrap_manifest(unit, samples, seed)` ([source](../../../../../../src/learnloop/field/evaluation.py), line 393)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]] — imports `evaluate`, `family_arms`, `report_digest`, `write_reports`; statically calls `evaluate`, `family_arms`, `report_digest`, `write_reports`
- [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]] — imports `evaluate`, `report_digest`, `write_reports`; statically calls `evaluate`, `report_digest`, `write_reports`
- [[Reference/Modules/learnloop/field/item_content|learnloop.field.item_content]] — imports `_eligible`; statically calls `_eligible`
- [[Reference/Modules/learnloop/field/probability_prep|learnloop.field.probability_prep]] — imports `_eligible`, `_groups`; statically calls `_eligible`, `_groups`
- [[Reference/Modules/learnloop/field/success_head_analysis|learnloop.field.success_head_analysis]] — imports `CLUSTER_T_METHOD`, `ReplayArrays`, `_loss`, `cluster_t_interval`, `paired_bootstrap`; statically calls `_loss`, `cluster_t_interval`, `paired_bootstrap`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `MasteryConfig`
- [[Reference/Modules/learnloop/field/answer_signals|learnloop.field.answer_signals]] — imports `module`
- [[Reference/Modules/learnloop/field/memory|learnloop.field.memory]] — imports `module`
- [[Reference/Modules/learnloop/field/predictors|learnloop.field.predictors]] — imports `create_predictor`, `registered_predictors`; calls `create_predictor`, `registered_predictors`
- [[Reference/Modules/learnloop/field/signals|learnloop.field.signals]] — imports `blocks_fast_track`; calls `blocks_fast_track`
- [[Reference/Modules/learnloop/field/types|learnloop.field.types]] — imports `AttemptRow`, `FacetRow`, `ObservationRow`, `SignalRow`
- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `brier_decomposition`, `student_t_quantile`; calls `brier_decomposition`, `student_t_quantile`
- [[Reference/Modules/learnloop/scheduling/family_memory_model|learnloop.scheduling.family_memory_model]] — imports `weights_digest`; calls `weights_digest`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `FSRS6_DEFAULT_WEIGHTS`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `math`, `pathlib`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]], [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]], [[Reference/Modules/learnloop/field/item_content|learnloop.field.item_content]], [[Reference/Modules/learnloop/field/probability_prep|learnloop.field.probability_prep]], [[Reference/Modules/learnloop/field/success_head_analysis|learnloop.field.success_head_analysis]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_answer_signal_arms.py](../../../../../../tests/test_answer_signal_arms.py) — direct import
  - `test_a_control_twin_separates_the_signal_from_recalibration`
  - `test_a_prediction_never_sees_its_own_outcome`
  - `test_brier_split_is_exact_and_separates_reliability_from_resolution`
  - `test_every_arm_reports_the_split_and_the_markdown_shows_it`
  - `test_signal_arms_abstain_without_their_signal_and_pair_on_common_attempts`
- [tests/test_daily_plan_owner_decisions.py](../../../../../../tests/test_daily_plan_owner_decisions.py) — direct import
  - `test_the_field_evaluation_keeps_the_daily_plan_label`
- [tests/test_eval_harness.py](../../../../../../tests/test_eval_harness.py) — direct import
  - `test_cluster_bootstrap_is_at_least_as_wide_as_the_attempt_bootstrap_on_clustered_data`
  - `test_cluster_bootstrap_reports_no_interval_only_when_every_draw_is_the_same`
  - `test_cluster_t_interval_has_no_cluster_minimum_only_degenerate_guards`
  - `test_cluster_t_interval_is_the_cr1_sandwich_with_items_minus_one_degrees_of_freedom`
  - `test_cluster_t_interval_reduces_to_the_one_sample_t_interval`
  - `test_llm_off_by_default_and_sweeps_available`
  - `test_manifest_determinism_hashes_inputs_config_and_no_text`
  - `test_paired_bootstrap_is_deterministic_and_keeps_attempt_differences_paired`
  - `test_the_cluster_option_leaves_every_other_report_byte_identical`
  - `test_the_item_unit_resamples_items_in_every_interval_and_the_manifest_says_so`
  - `test_the_t_interval_covers_where_the_v3_percentile_item_bootstrap_does_not`
- [tests/test_family_evaluation.py](../../../../../../tests/test_family_evaluation.py) — direct import
  - `test_family_arms_are_registered_in_the_field_registry`
  - `test_uncertainty_exclusions_counts_splits_and_aggregates_only`
- [tests/test_field_cli.py](../../../../../../tests/test_field_cli.py) — direct import
  - `test_eval_families_runs_the_shared_harness_read_only`
- [tests/test_probability_arms.py](../../../../../../tests/test_probability_arms.py) — direct import
  - `test_a_cache_from_a_different_past_fails_closed`
  - `test_arms_are_off_by_default_and_can_never_be_active`
  - `test_harness_replays_the_cache_with_zero_calls_and_no_store`
  - `test_pairwise_comparisons_report_without_recommending`
- [tests/test_probability_prep.py](../../../../../../tests/test_probability_prep.py) — direct import
  - `test_decider_end_to_end_through_the_fake_endpoint`
  - `test_prediction_points_are_exactly_the_harness_positions`
- [tests/test_success_head.py](../../../../../../tests/test_success_head.py) — direct import
  - `test_every_interval_in_the_t8_report_clusters_items_and_names_its_method`
  - `test_preregistration_v4_changes_the_hash_and_every_report_carries_it`
  - `test_t8_refuses_a_harness_that_resamples_attempts`
  - `test_the_verdict_interval_does_not_depend_on_bootstrap_settings`
  - `test_three_items_that_v3_killed_are_undecided_under_the_t_interval`

## Modification guidance

- Make changes here when the responsibility remains evaluation within learnloop.field; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/field/evaluation.py](../../../../../../src/learnloop/field/evaluation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
