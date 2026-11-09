---
title: "learnloop.figures.verify"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/verify.py"
source_paths:
  - "src/learnloop/figures/verify.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.figures"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.figures.verify module"
  - "src/learnloop/figures/verify.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.verify`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.verify` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Verification before a figure shows (spec_reader_workbench_v1 §8.3 steps 1-2; G45).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/verify.py](../../../../../../src/learnloop/figures/verify.py) |
| Source lines | 467 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Report` ([source](../../../../../../src/learnloop/figures/verify.py), line 76) — What each step found, as stored in ``verification_report_json``.
  - `as_dict(self) -> dict[str, Any]` (line 91; public)
- `parameter_grid(compiled: S.CompiledFigure) -> list[dict[str, float]]` ([source](../../../../../../src/learnloop/figures/verify.py), line 102) — Each parameter at its min, default and max (duplicates dropped).
- `path_problems(data: Mapping[str, Any], point: Mapping[str, float]) -> list[str]` ([source](../../../../../../src/learnloop/figures/verify.py), line 202) — RW5b: a path that stops being finite, or starts outside its plot, at a grid point (one that leaves its padded plot is cut there and says so).
- `structural(compiled: S.CompiledFigure, grid: Sequence[Mapping[str, float]]) -> list[str]` ([source](../../../../../../src/learnloop/figures/verify.py), line 218)
- `check_invariant(compiled: S.CompiledFigure, invariant: Any, node: G.Node | None, point: Mapping[str, float]) -> tuple[bool, str, float | None]` ([source](../../../../../../src/learnloop/figures/verify.py), line 257) — One invariant at one grid point: (holds, why not, the measured value).
- `independent_integral(compiled: S.CompiledFigure, node: G.Node, variable: str, low: float, high: float, env: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/figures/verify.py), line 319) — The verifier's own integration: Gauss-Legendre on :data:`GL_PANELS` panels per piece, the range split at the series' piecewise breakpoints (nodes are interior, so each piece reads its own side of a jump).
- `check_shades(compiled: S.CompiledFigure, grid: Sequence[Mapping[str, float]]) -> tuple[list[dict[str, Any]], list[str]]` ([source](../../../../../../src/learnloop/figures/verify.py), line 346)
- `check_invariants(compiled: S.CompiledFigure, grid: Sequence[Mapping[str, float]]) -> tuple[list[dict[str, Any]], list[str]]` ([source](../../../../../../src/learnloop/figures/verify.py), line 371)
- `quote_in(quote: str, text: str) -> bool` ([source](../../../../../../src/learnloop/figures/verify.py), line 397) — A quote is the source's own words: verbatim after collapsing whitespace.
- `check_claims(compiled: S.CompiledFigure, span_texts: Mapping[str, str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/verify.py), line 404)
- `verified_assumptions(compiled: S.CompiledFigure, span_texts: Mapping[str, str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/verify.py), line 410) — The assumptions as shown: a quote that is not verbatim in its span is dropped (the text stays, AI-written).
- `decidable_predictions(compiled: S.CompiledFigure) -> tuple[list[int], list[int]]` ([source](../../../../../../src/learnloop/figures/verify.py), line 421) — Predictions code can decide (an answer exists), and those it cannot (dropped).
- `verify_numerics(compiled: S.CompiledFigure) -> Report` ([source](../../../../../../src/learnloop/figures/verify.py), line 431) — Steps 1 and 2 (no model, no sandbox): ``failed`` or a report to carry on.

### Module constants

- `ILLUSTRATIVE` ([src/learnloop/figures/verify.py](../../../../../../src/learnloop/figures/verify.py), line 50)
- `FAILED` ([src/learnloop/figures/verify.py](../../../../../../src/learnloop/figures/verify.py), line 51)
- `UNSUPPORTED` ([src/learnloop/figures/verify.py](../../../../../../src/learnloop/figures/verify.py), line 52)
- `OUTCOMES` ([src/learnloop/figures/verify.py](../../../../../../src/learnloop/figures/verify.py), line 55)
- `DENSITY_TOLERANCE` ([src/learnloop/figures/verify.py](../../../../../../src/learnloop/figures/verify.py), line 57)
- `PMF_TOLERANCE` ([src/learnloop/figures/verify.py](../../../../../../src/learnloop/figures/verify.py), line 58)
- `SHADE_TOLERANCE` ([src/learnloop/figures/verify.py](../../../../../../src/learnloop/figures/verify.py), line 59)
- `NONNEGATIVE_SLACK` ([src/learnloop/figures/verify.py](../../../../../../src/learnloop/figures/verify.py), line 60)
- `MONOTONE_SLACK` ([src/learnloop/figures/verify.py](../../../../../../src/learnloop/figures/verify.py), line 61)
- `DEFAULT_BOUND` ([src/learnloop/figures/verify.py](../../../../../../src/learnloop/figures/verify.py), line 62)
- `RANGE_SAMPLES` ([src/learnloop/figures/verify.py](../../../../../../src/learnloop/figures/verify.py), line 63)
- `GL_PANELS` ([src/learnloop/figures/verify.py](../../../../../../src/learnloop/figures/verify.py), line 64)
- `_GL` ([src/learnloop/figures/verify.py](../../../../../../src/learnloop/figures/verify.py), line 66)
- `OPTIONAL_PARTS` ([src/learnloop/figures/verify.py](../../../../../../src/learnloop/figures/verify.py), line 150)
- `RENDER_PADDING` ([src/learnloop/figures/verify.py](../../../../../../src/learnloop/figures/verify.py), line 155)

### Explicit exports

`__all__` declares:

- `FAILED`
- `ILLUSTRATIVE`
- `OUTCOMES`
- `Report`
- `UNSUPPORTED`
- `check_claims`
- `check_invariant`
- `decidable_predictions`
- `independent_integral`
- `parameter_grid`
- `path_problems`
- `quote_in`
- `verified_assumptions`
- `verify_numerics`

## Internal implementation anchors

- `_range_samples(low: float, high: float, count: int=RANGE_SAMPLES) -> list[float]` ([source](../../../../../../src/learnloop/figures/verify.py), line 114)
- `_shown_values(data: Mapping[str, Any]) -> list[tuple[str, Any]]` ([source](../../../../../../src/learnloop/figures/verify.py), line 118) — Every value a panel shows, with where it is.
- `_leaves(value: Any, where: str, into: list[tuple[str, Any]]) -> None` ([source](../../../../../../src/learnloop/figures/verify.py), line 128) — Every number (or None, a value that is not finite) the panel data holds, at any depth: the inputs and every derived value the renderer shows (a map's determinant and corners, a shaded area's bounds and value, readouts), so a new field is checked without being listed (fix round 3…
- `_extents(panel: Mapping[str, Any], where: str) -> list[tuple[str, Any]]` ([source](../../../../../../src/learnloop/figures/verify.py), line 158) — The scales the renderer derives from a panel's values (its value range and its reach, padded), as values that must be finite: None when one is not (fix round 3: [[1e200, 0], [0, 1e200]] has finite entries and a determinant of 1e400).
- `_spread(numbers: Sequence[float], where: str) -> list[tuple[str, Any]]` ([source](../../../../../../src/learnloop/figures/verify.py), line 192)
- `_point(point: Mapping[str, float]) -> str` ([source](../../../../../../src/learnloop/figures/verify.py), line 235)
- `_env(compiled: S.CompiledFigure, point: Mapping[str, float]) -> dict[str, float]` ([source](../../../../../../src/learnloop/figures/verify.py), line 239)
- `_sampler(compiled: S.CompiledFigure, node: G.Node, variable: str | None, env: Mapping[str, float]) -> Callable[[float], float]` ([source](../../../../../../src/learnloop/figures/verify.py), line 245)
- `_breakpoints(node: G.Node, defs: Mapping[str, G.Node], variable: str, env: Mapping[str, float], _seen: tuple[str, ...]=()) -> set[float]` ([source](../../../../../../src/learnloop/figures/verify.py), line 294) — Where a piecewise condition compares the variable with an expression free of it (``x < c``, ``c >= x``): the points a series may jump at.
- `_squash(text: str) -> str` ([source](../../../../../../src/learnloop/figures/verify.py), line 393)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `quote_in`; statically calls `quote_in`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; statically calls `Report`, `check_claims`, `quote_in`, `verified_assumptions`, `verify_numerics`
- [[Reference/Modules/learnloop/figures/sketch_verify|learnloop.figures.sketch_verify]] — imports `module`; statically calls `parameter_grid`, `quote_in`
- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `module`; statically calls `parameter_grid`, `quote_in`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/figures/grammar|learnloop.figures.grammar]] — imports `module`; calls `adaptive_simpson`, `evaluate`, `exact_sum`
- [[Reference/Modules/learnloop/figures/spec|learnloop.figures.spec]] — imports `module`; calls `evaluate_figure`, `expanded_free`, `prediction_outcome`, `shade_value`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `itertools`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]], [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]], [[Reference/Modules/learnloop/figures/sketch_verify|learnloop.figures.sketch_verify]], [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_panels.py](../../../../../../tests/test_figure_panels.py) — direct import
  - `test_each_corpus_figure_that_should_show_passes_steps_one_and_two`
  - `test_invariants_apply_to_rw5b_figures_unchanged`
  - `test_verification_accepts_a_path_cut_where_it_leaves_its_plot`
  - `test_verification_reads_a_field_and_its_heat_map`
  - `test_verification_refuses_a_heat_map_value_that_is_not_finite`
  - `test_verification_refuses_a_path_that_is_not_finite_or_starts_outside`
- [tests/test_figure_verification.py](../../../../../../tests/test_figure_verification.py) — direct import
  - `test_a_shaded_area_is_checked_against_an_independent_integration`
  - `test_a_value_that_is_not_finite_on_the_grid_fails_structure`
  - `test_each_invariant_kind_holds_or_fails`
  - `test_numeric_checks_pass_the_flagship_and_reject_the_half_negative_control`
  - `test_quotes_must_be_verbatim`
- [tests/test_figures_codex_review.py](../../../../../../tests/test_figures_codex_review.py) — direct import
- [tests/test_figures_fix_round2.py](../../../../../../tests/test_figures_fix_round2.py) — direct import
- [tests/test_figures_fix_round3.py](../../../../../../tests/test_figures_fix_round3.py) — direct import
  - `test_a_finite_map_and_the_flagship_still_pass_structure`
  - `test_a_map_whose_shown_values_overflow_fails_structure`
- [tests/test_figures_fix_round4.py](../../../../../../tests/test_figures_fix_round4.py) — direct import
  - `test_a_plot_domain_whose_samples_overflow_is_refused`
  - `test_structure_requires_every_numeric_leaf_finite`
  - `test_the_verifys_seven_level_chain_compiles_and_evaluates`
- [tests/test_figures_fix_round5.py](../../../../../../tests/test_figures_fix_round5.py) — direct import
  - `test_a_percent_readout_that_overflows_when_scaled_fails_structure`
- [tests/test_rw5c_source_check.py](../../../../../../tests/test_rw5c_source_check.py) — direct import
  - `test_with_its_invariant_the_half_density_is_still_refused_at_step_two`
- [tests/test_sketch_hostile.py](../../../../../../tests/test_sketch_hostile.py) — direct import
  - `test_a_tautological_claim_speaks_only_for_what_it_checks`
  - `test_text_that_imitates_a_badge_never_reaches_the_check_lines`
- [tests/test_sketch_sandbox_review.py](../../../../../../tests/test_sketch_sandbox_review.py) — direct import
  - `test_a_claim_false_at_a_graded_step_fails_verification`
  - `test_a_graded_step_is_checked_counted_and_compared`
  - `test_a_program_that_changes_its_state_when_read_is_checked_under_the_playback_schedule`
  - `test_a_program_whose_reads_change_every_later_value_fails_as_not_deterministic`
  - `test_every_prediction_records_its_graded_read_in_tested`
  - `test_the_report_carries_the_schedule_and_the_digest_of_every_checked_read`
  - `test_the_reviewers_counting_program_fails_verification`
- [tests/test_sketch_verify.py](../../../../../../tests/test_sketch_verify.py) — direct import
  - `test_a_claim_whose_work_exceeds_the_budget_is_refused_before_it_runs`
  - `test_a_follows_claim_checks_the_drawn_trajectory_against_rk4`
  - `test_a_follows_claim_is_charged_every_evaluation_it_runs`
  - `test_a_follows_claim_past_the_cap_is_stopped_where_the_cap_is`
  - `test_a_heat_map_bound_series_is_checked_in_its_cell_values_only`
  - `test_a_pairs_claim_is_charged_for_its_probes_own_x`
  - `test_a_series_line_drawn_at_unrelated_x_is_not_claimed_as_the_equation`
  - `test_a_small_pairs_claim_is_charged_at_least_its_evaluations`
  - `test_an_element_that_changes_type_gets_no_attribute_label`
  - `test_each_planted_wrong_sketch_is_refused_for_its_reason`
  - `test_every_good_sketch_passes`
  - `test_no_claims_is_shown_as_nothing_checked`
  - `test_scenes_at_the_point_cap_over_the_largest_grid_hit_the_output_budget`
  - `test_the_largest_legal_grid_is_verified_one_point_read_at_a_time`
  - `test_the_random_walk_passes_with_element_scoped_check_lines`
  - `test_undecidable_predictions_are_dropped_not_failed`
  - `test_verification_stops_at_its_wall_clock`

## Modification guidance

- Make changes here when the responsibility remains verify within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/verify.py](../../../../../../src/learnloop/figures/verify.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
