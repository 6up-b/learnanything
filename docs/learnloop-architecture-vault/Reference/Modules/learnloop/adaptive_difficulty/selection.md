---
title: "learnloop.adaptive_difficulty.selection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/selection.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/selection.py"
source_commit: "1d105282ccc93dac123e8310339333119e97997c"
source_commit_timestamp: "2026-10-19T10:43:31-04:00"
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
  - "learnloop.adaptive_difficulty.selection module"
  - "src/learnloop/adaptive_difficulty/selection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.selection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.selection` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: The draws: practice in the band, calibration within acceptable difficulty (spec §6.1-6.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/selection.py](../../../../../../src/learnloop/adaptive_difficulty/selection.py) |
| Source lines | 411 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1d105282ccc93dac123e8310339333119e97997c` |
| Commit timestamp | `2026-10-19T10:43:31-04:00` |

## Public API

- `class SelectionConstants` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 47)
  - `as_dict(self) -> dict[str, Any]` (line 55; public)
- `constants_from_config(config: Any) -> SelectionConstants` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 61)
- `class Scored` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 75) — One candidate's scores, as logged.
  - `as_dict(self) -> dict[str, Any]` (line 83; public)
- `class Draw` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 89)
  - `propensity(self) -> float` (line 101; public)
  - `as_dict(self) -> dict[str, Any]` (line 104; public)
- `seed_for(design: str, key: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 111)
- `uniform(seed: str) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 115) — A uniform in [0, 1) from the seed (53 bits of a SHA-256).
- `propensities(scored: Sequence[Scored], constants: SelectionConstants=SelectionConstants()) -> tuple[str, dict[str, float], tuple[str, ...], tuple[str, ...], float]` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 144) — ``(mode, π, T, O, q)``: the exact propensities of §6.1 step 4 (or §6.2's calibrate rule).
- `draw(scored: Sequence[Scored], *, key: str, design: str=SELECT_VERSION, constants: SelectionConstants=SelectionConstants()) -> Draw` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 174) — The draw, with its propensities logged before it is used (A7).
- `recompute(row: Mapping[str, Any], constants: SelectionConstants | None=None) -> Draw` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 187) — Recompute a draw from its logged row (G-AD2-19): the scores, the constants and the seed.
- `feature_level(dimension: str, value: Any) -> int` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 257) — The ordinal level of a feature value on a ladder dimension (§9.1's order).
- `point_key(point: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 266)
- `entry_point(capability: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 278) — ``e_k``: the default-trajectory waypoint for the capability (§9.1); None for coordination.
- `default_target(capability: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 289) — ``e_k`` stepped one level up in complexity and in transfer, bounded by the default trajectory.
- `envelope_max() -> dict[str, int]` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 302) — The default trajectory's depth envelope: the hardest level it reaches on each dimension.
- `within_envelope(point: Mapping[str, Any] | None) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 315)
- `ladder(capability: str, target: Mapping[str, Any] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 323) — A ladder instance ``L(k, t)`` (§9.1): from ``e_k`` to ``t``, one dimension one level per rung in the fixed order, cycling until every dimension reaches ``t``.
- `ladder_id(capability: str, target: Mapping[str, Any] | None) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 350)
- `commission_candidates(capability: str, targets: Sequence[Mapping[str, Any] | None]=(None,)) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 358) — ``X_c``: the rungs of every applicable ladder and their one-step neighbours on a single ordinal dimension, clipped to the depth envelope (§6.1).

### Module constants

- `SELECT_VERSION` ([src/learnloop/adaptive_difficulty/selection.py](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 36)
- `COMMISSION_VERSION` ([src/learnloop/adaptive_difficulty/selection.py](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 37)
- `LADDER_VERSION` ([src/learnloop/adaptive_difficulty/selection.py](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 38)
- `DESIGN` ([src/learnloop/adaptive_difficulty/selection.py](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 39)
- `MODE_BAND` ([src/learnloop/adaptive_difficulty/selection.py](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 41)
- `MODE_CALIBRATE` ([src/learnloop/adaptive_difficulty/selection.py](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 42)
- `MODE_PREDECESSOR` ([src/learnloop/adaptive_difficulty/selection.py](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 43)
- `LADDER_ORDER` ([src/learnloop/adaptive_difficulty/selection.py](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 210)
- `_SCAFFOLDING` ([src/learnloop/adaptive_difficulty/selection.py](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 211)
- `_TRANSFER` ([src/learnloop/adaptive_difficulty/selection.py](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 212)
- `_SPAN` ([src/learnloop/adaptive_difficulty/selection.py](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 213)
- `_RESPONSE_CLASS` ([src/learnloop/adaptive_difficulty/selection.py](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 214)
- `_LEVELS` ([src/learnloop/adaptive_difficulty/selection.py](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 263)

### Explicit exports

`__all__` declares:

- `COMMISSION_VERSION`
- `DESIGN`
- `Draw`
- `LADDER_ORDER`
- `LADDER_VERSION`
- `MODE_BAND`
- `MODE_CALIBRATE`
- `MODE_PREDECESSOR`
- `SELECT_VERSION`
- `Scored`
- `SelectionConstants`
- `commission_candidates`
- `constants_from_config`
- `default_target`
- `draw`
- `entry_point`
- `envelope_max`
- `feature_level`
- `ladder`
- `ladder_id`
- `point_key`
- `propensities`
- `recompute`
- `seed_for`
- `uniform`
- `within_envelope`

## Internal implementation anchors

- `_invert(propensities: Mapping[str, float], u: float) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 122)
- `_within(value: float, interval: tuple[float, float]) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 132)
- `_distance(value: float, interval: tuple[float, float]) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 136)
- `_level(dimension: str, value: Any) -> int` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 218)
- `_value(dimension: str, level: int, template: Mapping[str, Any]) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 238)
- `_neighbours(point: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/selection.py), line 371)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]] — imports `module`; statically calls `entry_point`, `seed_for`, `uniform`
- [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]] — imports `module`; statically calls `constants_from_config`, `entry_point`
- [[Reference/Modules/learnloop/adaptive_difficulty/predict|learnloop.adaptive_difficulty.predict]] — imports `Scored`, `SelectionConstants`, `point_key`; statically calls `Scored`, `SelectionConstants`, `point_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/readiness|learnloop.adaptive_difficulty.readiness]] — imports `module`; statically calls `commission_candidates`, `constants_from_config`, `default_target`, `ladder_id`
- [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]] — imports `module`; statically calls `constants_from_config`, `feature_level`, `point_key`, `propensities`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `module`; statically calls `commission_candidates`, `constants_from_config`, `draw`, `recompute`, `seed_for`
- [[Reference/Modules/learnloop/daily_plan/ad_slot|learnloop.daily_plan.ad_slot]] — imports `within_envelope`; statically calls `within_envelope`
- [[Reference/Modules/learnloop/sim/ad_synthetic|learnloop.sim.ad_synthetic]] — imports `module`; statically calls `Scored`, `SelectionConstants`, `commission_candidates`, `draw`, `ladder`, `point_key`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/curriculum/depth_rungs|learnloop.curriculum.depth_rungs]] — imports `DEFAULT_TRAJECTORY`
- [[Reference/Modules/learnloop/scheduling/randomization_layer|learnloop.scheduling.randomization_layer]] — imports `feature_overlap_propensities`; calls `feature_overlap_propensities`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]], [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]], [[Reference/Modules/learnloop/adaptive_difficulty/predict|learnloop.adaptive_difficulty.predict]], [[Reference/Modules/learnloop/adaptive_difficulty/readiness|learnloop.adaptive_difficulty.readiness]], [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_fix_r8.py](../../../../../../tests/test_ad23_fix_r8.py) — direct import
  - `test_a_claim_moves_no_forecast_through_a_withheld_items_facet`
- [tests/test_ad23_owner_decisions.py](../../../../../../tests/test_ad23_owner_decisions.py) — direct import
  - `test_the_owner_defaults_of_2026_10_19`
- [tests/test_ad2_serving.py](../../../../../../tests/test_ad2_serving.py) — direct import
  - `test_a_draws_propensity_is_the_probability_of_what_it_chose`
  - `test_calibrate_mode_prefers_overlap_band`
  - `test_calibrate_with_empty_overlap_picks_nearest_to_band`
  - `test_empty_overlap_sets_q_zero`
  - `test_propensity_recomputes_from_logged_row`
  - `test_seed_reproduces_draw`
- [tests/test_ad3_dose_arm.py](../../../../../../tests/test_ad3_dose_arm.py) — direct import
  - `test_dose_offer_propensities_exact`
  - `test_draw_frequencies_match_propensities`
- [tests/test_ad3_subject_view.py](../../../../../../tests/test_ad3_subject_view.py) — direct import
  - `test_subject_view_mixture_keeps_propensities_exact`
- [tests/test_ad_guard.py](../../../../../../tests/test_ad_guard.py) — direct import
  - `test_a_denied_dose_response_rolls_the_draw_back`
  - `test_a_write_then_a_swallowed_denial_then_an_early_return_keeps_no_ad_rows`
- [tests/test_teacher_te1b_review_fixes.py](../../../../../../tests/test_teacher_te1b_review_fixes.py) — direct import
  - `test_band_positions_thresholds_p_band_and_reads_the_side_from_expected_success`

## Modification guidance

- Make changes here when the responsibility remains selection within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/selection.py](../../../../../../src/learnloop/adaptive_difficulty/selection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
