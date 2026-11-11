---
title: "learnloop.field.success_head"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/field/success_head.py"
source_paths:
  - "src/learnloop/field/success_head.py"
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
  - "learnloop.field.success_head module"
  - "src/learnloop/field/success_head.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-field"
---

# `learnloop.field.success_head`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/field/_package|learnloop.field]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.field.success_head` exists within [[Reference/Modules/learnloop/field/_package|learnloop.field]] to own the behavior summarized by its module contract: T8 learner success head: pure prequential arms and the pre-registered analysis.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/field/success_head.py](../../../../../../src/learnloop/field/success_head.py) |
| Source lines | 501 |
| Owning package | [[Reference/Modules/learnloop/field/_package|learnloop.field]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class HeadPriors` ([source](../../../../../../src/learnloop/field/success_head.py), line 43) — Gaussian prior per feature block, fixed before any replay (F5).
  - `__post_init__(self) -> None` (line 56; internal)
- `preregistration_hash() -> str` ([source](../../../../../../src/learnloop/field/success_head.py), line 129)
- `class AttemptContent` ([source](../../../../../../src/learnloop/field/success_head.py), line 148) — Item-side content of one attempt; never an answer, grade or outcome.
- `class ContentIndex` ([source](../../../../../../src/learnloop/field/success_head.py), line 162) — Frozen content keyed by attempt identity ``(item_id, observed_at)``.
  - `__init__(self, entries: Mapping[tuple[str, str], AttemptContent], *, embedding_model: str | None=None, views: Iterable[str]=(STEM_VIEW,), dimensions: int=EMBEDDING_DIMENSIONS)` (line 169; internal)
  - `get(self, features: ItemFeatures) -> AttemptContent | None` (line 190; public)
  - `vector(self, features: ItemFeatures, view: str) -> np.ndarray | None` (line 195; public)
- `class LogisticHead` ([source](../../../../../../src/learnloop/field/success_head.py), line 208) — Prequential Bayesian logistic regression over fixed feature blocks.
  - `__init__(self, *, name: str, views: Iterable[str]=(), moderated: bool=False, difficulty: bool=False, content: ContentIndex | None=None, config=None, lo_priors: Mapping[str, tuple[float, float]] | None=None, priors: HeadPriors | None=None)` (line 222; internal)
  - `_reset(self) -> None` (line 250; internal)
  - `_add_name(self, name: str) -> None` (line 275; internal)
  - `_prior(self, name: str) -> tuple[float, float]` (line 283; internal)
  - `_neutral(features: ItemFeatures) -> ItemFeatures` (line 298; internal)
  - `_explicit(self, f: ItemFeatures) -> dict[str, float]` (line 303; internal)
  - `_decayed(self, when) -> tuple[float, float]` (line 331; internal)
  - `_recency(self, when) -> float` (line 335; internal)
  - `_raw(self, f: ItemFeatures) -> dict[str, np.ndarray | None]` (line 342; internal)
  - `_centred(self, view: str, vector: np.ndarray | None) -> np.ndarray` (line 345; internal)
  - `_design_row(self, explicit: Mapping[str, float], raw: Mapping[str, np.ndarray | None])` (line 353; internal) — Dense values over known names, plus (value, prior) for unseen names.
  - `covers(self, features: ItemFeatures) -> bool` (line 369; public)
  - `predict(self, features: ItemFeatures) -> float` (line 374; public)
  - `observe(self, row: ObservationRow) -> None` (line 384; public)
  - `rebuild(self, rows: Iterable[ObservationRow]) -> None` (line 416; public)
  - `_design(self) -> np.ndarray` (line 423; internal)
  - `_fit(self) -> None` (line 440; internal)
- `newton_map(X, y, s, prior_mean, precision, start, *, tolerance=1e-10, max_iterations=100)` ([source](../../../../../../src/learnloop/field/success_head.py), line 456) — Weighted logistic MAP under independent Gaussian priors; strictly convex.
- `success_head_arms(content: ContentIndex, *, config=None, lo_priors=None, include_difficulty: bool=False) -> tuple[LogisticHead, ...]` ([source](../../../../../../src/learnloop/field/success_head.py), line 488) — Fresh T8 arms.

### Module constants

- `SOLVER_PANEL` ([src/learnloop/field/success_head.py](../../../../../../src/learnloop/field/success_head.py), line 33)
- `EMBEDDING_DIMENSIONS` ([src/learnloop/field/success_head.py](../../../../../../src/learnloop/field/success_head.py), line 35)
- `EXPLICIT_ARMS` ([src/learnloop/field/success_head.py](../../../../../../src/learnloop/field/success_head.py), line 36)
- `PRIMARY_ARM` ([src/learnloop/field/success_head.py](../../../../../../src/learnloop/field/success_head.py), line 37)
- `GATED_ARMS` ([src/learnloop/field/success_head.py](../../../../../../src/learnloop/field/success_head.py), line 38)
- `LLM_ARMS` ([src/learnloop/field/success_head.py](../../../../../../src/learnloop/field/success_head.py), line 39)
- `PREREGISTRATION` ([src/learnloop/field/success_head.py](../../../../../../src/learnloop/field/success_head.py), line 62)
- `EMPTY_CONTENT` ([src/learnloop/field/success_head.py](../../../../../../src/learnloop/field/success_head.py), line 201)

## Internal implementation anchors

- `_hash(value: object) -> str` ([source](../../../../../../src/learnloop/field/success_head.py), line 133)
- `_sigmoid(value: float) -> float` ([source](../../../../../../src/learnloop/field/success_head.py), line 138)
- `_logit(p: float, clip: float=1e-06) -> float` ([source](../../../../../../src/learnloop/field/success_head.py), line 142)
- `_days(earlier, later) -> float` ([source](../../../../../../src/learnloop/field/success_head.py), line 204)
- `_objective(X, y, s, prior_mean, precision, w)` ([source](../../../../../../src/learnloop/field/success_head.py), line 451)
- `_symmetric_inverse(matrix: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/field/success_head.py), line 481)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]] — imports `LLM_ARMS`, `PREREGISTRATION`, `preregistration_hash`, `success_head_arms`; statically calls `preregistration_hash`, `success_head_arms`
- [[Reference/Modules/learnloop/field/item_content|learnloop.field.item_content]] — imports `AttemptContent`, `ContentIndex`, `EMBEDDING_DIMENSIONS`, `SKELETON_VIEW`, `SOLVER_PANEL`, `STEM_VIEW`; statically calls `AttemptContent`, `ContentIndex`
- [[Reference/Modules/learnloop/field/success_head_analysis|learnloop.field.success_head_analysis]] — imports `EXPLICIT_ARMS`, `GATED_ARMS`, `LLM_ARMS`, `PREREGISTRATION`, `PRIMARY_ARM`, `preregistration_hash`; statically calls `preregistration_hash`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/field/predictors|learnloop.field.predictors]] — imports `MasteryEKF`, `_eligible`, `_mastery_hash_view`; calls `MasteryEKF`, `_eligible`, `_mastery_hash_view`
- [[Reference/Modules/learnloop/field/types|learnloop.field.types]] — imports `FacetRow`, `ItemFeatures`, `ObservationRow`, `SignalRow`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `math`, `types`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]], [[Reference/Modules/learnloop/field/item_content|learnloop.field.item_content]], [[Reference/Modules/learnloop/field/success_head_analysis|learnloop.field.success_head_analysis]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/test_success_head.py](../../../../../../tests/test_success_head.py) — direct import
  - `test_a_large_effect_is_decided_with_fewer_than_100_attempts`
  - `test_a_null_effect_is_undecided_until_the_upper_bound_falls_below_delta`
  - `test_a_real_gain_below_delta_is_kill_with_its_reason`
  - `test_abstention_is_never_a_synthetic_prediction`
  - `test_content_index_rejects_mismatched_views_and_takes_only_features`
  - `test_deterministic_rebuild_and_no_store_or_network`
  - `test_difficulty_arm_abstains_without_solver_panel_and_uses_it_with`
  - `test_embeddings_help_when_the_text_carries_the_signal`
  - `test_every_interval_in_the_t8_report_clusters_items_and_names_its_method`
  - `test_future_content_entries_never_change_a_prediction`
  - `test_kill_rule_picks_the_best_explicit_arm_and_kills_without_a_gain`
  - `test_llm_labelled_difficulty_never_reaches_t8_arms`
  - `test_moderation_shrinks_toward_half_and_more_off_support`
  - `test_newton_map_is_the_stationary_point_and_matches_a_direct_optimizer`
  - `test_prediction_never_sees_the_current_or_a_later_outcome`
  - `test_preregistration_v4_changes_the_hash_and_every_report_carries_it`
  - `test_priors_are_a_priori_and_recorded`
  - `test_recency_running_sum_equals_the_full_weighted_sum`
  - `test_t8_arms_are_never_activatable`
  - `test_t8_refuses_a_harness_that_resamples_attempts`
  - `test_the_flipping_delta_is_where_the_verdict_changes`
  - `test_the_harness_hands_item_clusters_and_t8_resamples_items`
  - `test_the_primary_comparison_is_never_reported_with_a_second_interval`
- [tests/test_success_head_cli.py](../../../../../../tests/test_success_head_cli.py) — direct import
  - `test_llm_prepare_dry_run_then_fake_codex_then_cache_only_replay`
  - `test_report_runs_all_arms_read_only_and_aggregate_only`

## Modification guidance

- Make changes here when the responsibility remains success head within learnloop.field; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/field/success_head.py](../../../../../../src/learnloop/field/success_head.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
