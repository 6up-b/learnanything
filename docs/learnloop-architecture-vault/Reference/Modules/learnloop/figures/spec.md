---
title: "learnloop.figures.spec"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/spec.py"
source_paths:
  - "src/learnloop/figures/spec.py"
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
  - "learnloop.figures.spec module"
  - "src/learnloop/figures/spec.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.spec`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.spec` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: ``InteractiveFigureSpecV1``: the declarative figure (spec_reader_workbench_v1 §8.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py) |
| Source lines | 1239 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SpecError(ValueError)` ([source](../../../../../../src/learnloop/figures/spec.py), line 103) — A spec outside the schema, the caps or the grammar; ``problems`` lists why.
  - `__init__(self, problems: Sequence[str]) -> None` (line 106; internal)
- `class SourceClaim(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 120)
- `class Region(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 125)
- `class Assumption(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 130)
- `class Parameter(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 136)
- `class Definition(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 146)
- `class Axis(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 151)
- `class Series(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 157)
- `class Marker(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 162)
- `class Shade(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 167)
- `class FunctionPlot(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 175)
- `class Highlight(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 183)
- `class PmfBars(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 189)
- `class LinearMap2D(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 196)
- `class Readout(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 203)
- `class GridAxis(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 210) — A heat map's or vector field's axis: ``cells`` intervals, ``cells + 1`` samples.
- `class Heatmap2D(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 219)
- `class FieldHeatmap(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 229) — The heat map under a vector field's arrows (its axes are the field's).
- `class VectorField2D(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 238)
- `class Trajectory2D(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 248)
- `class Iterate2D(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 264)
- `class Invariant(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 283)
- `class Observe(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 298)
- `class Prediction(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 303)
- `class Annotation(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 309)
- `class InteractiveFigureSpecV1(_Strict)` ([source](../../../../../../src/learnloop/figures/spec.py), line 314)
  - `dump(self) -> dict[str, Any]` (line 328; public)
  - `canonical_json(self) -> str` (line 331; public)
- `class CompiledPanel` ([source](../../../../../../src/learnloop/figures/spec.py), line 340)
- `class CompiledFigure` ([source](../../../../../../src/learnloop/figures/spec.py), line 347)
  - `defaults(self) -> dict[str, float]` (line 357; public)
  - `shade_labels(self) -> list[str]` (line 360; public)
- `expanded_free(node: G.Node, definitions: Mapping[str, G.Node], bound: frozenset[str]=frozenset(), _seen: tuple[str, ...]=()) -> set[str]` ([source](../../../../../../src/learnloop/figures/spec.py), line 364) — The variables and parameters ``node`` needs, definitions expanded where they are used (a bound variable reaches a definition's body).
- `advanced_expressions(panel: Any) -> list[str]` ([source](../../../../../../src/learnloop/figures/spec.py), line 688) — Every expression of a RW5b panel.
- `expression_work(node: G.Node, definitions: Mapping[str, G.Node], parameters: Sequence[Parameter], ranges: Mapping[str, tuple[float, float]], _seen: tuple[str, ...]=()) -> int` ([source](../../../../../../src/learnloop/figures/spec.py), line 743) — How many nodes one evaluation of ``node`` visits at most, definitions expanded and a sum's body counted once per term (figureSpec.ts's expressionWork).
- `advanced_kinds(spec: InteractiveFigureSpecV1 | Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/figures/spec.py), line 761) — The RW5b panel kinds a spec (or its JSON mapping) uses, in order.
- `parse_spec(raw: str | Mapping[str, Any], *, advanced: bool=True) -> CompiledFigure` ([source](../../../../../../src/learnloop/figures/spec.py), line 769) — A spec from its JSON (or mapping), validated and compiled, or :class:`SpecError`.
- `parse_salvaging_predictions(raw: Any, parse: Callable[[Any], Any], model: type[BaseModel], error: type[Exception]) -> tuple[Any, list[str]]` ([source](../../../../../../src/learnloop/figures/spec.py), line 822) — An author's answer parsed by ``parse``, keeping the figure when only an optional prediction is bad.
- `parse_author_spec(raw: Any, *, advanced: bool=True) -> tuple[CompiledFigure, list[str]]` ([source](../../../../../../src/learnloop/figures/spec.py), line 868) — :func:`parse_spec` for an author's answer (:func:`parse_salvaging_predictions`).
- `plot_xs(axis: Axis) -> list[float]` ([source](../../../../../../src/learnloop/figures/spec.py), line 888)
- `bar_ks(axis: Axis) -> list[float]` ([source](../../../../../../src/learnloop/figures/spec.py), line 892) — The bars' k values: counted from the support's start, at most :data:`MAX_BARS` of them (fix round 2; validation refuses more).
- `shade_value(compiled: CompiledFigure, panel: CompiledPanel, shade_index: int, env: Mapping[str, float]) -> tuple[float, float, float]` ([source](../../../../../../src/learnloop/figures/spec.py), line 900) — A shaded area's clipped bounds and its value (the linked readout).
- `highlight_value(compiled: CompiledFigure, panel: CompiledPanel, env: Mapping[str, float]) -> tuple[float, float, float]` ([source](../../../../../../src/learnloop/figures/spec.py), line 923)
- `derived_bounds(compiled: CompiledFigure, panel_index: int, kind: str, index: int, env: Mapping[str, float]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/spec.py), line 942) — The bounds a derived label states (RW5c §7.2, Codex review F2): the ones the evaluator used, whatever the author's bound expressions say.
- `evaluate_panel(compiled: CompiledFigure, panel: CompiledPanel, env: Mapping[str, float]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/spec.py), line 980)
- `grid_points(axis: Any, cells: int) -> list[float]` ([source](../../../../../../src/learnloop/figures/spec.py), line 1031) — ``cells + 1`` samples from ``axis.min`` to ``axis.max``.
- `escape_box(axis: Any) -> tuple[float, float]` ([source](../../../../../../src/learnloop/figures/spec.py), line 1060) — The window a path may stay in: the axis range padded by :data:`ESCAPE_MARGIN` of its span.
- `evaluate_figure(compiled: CompiledFigure, params: Mapping[str, float] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/spec.py), line 1163) — Every panel's data at ``params`` (defaults for the rest).
- `observed(compiled: CompiledFigure, index: int, params: Mapping[str, float] | None=None) -> float` ([source](../../../../../../src/learnloop/figures/spec.py), line 1173)
- `prediction_outcome(compiled: CompiledFigure, index: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/spec.py), line 1180) — What a prediction observes and its right answer, decided by code.

### Module constants

- `SPEC_VERSION` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 49)
- `SAMPLES` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 51)
- `MAX_PARAMETERS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 52)
- `MAX_DEFINITIONS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 53)
- `MAX_PANELS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 54)
- `MAX_SERIES` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 55)
- `MAX_SHADES` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 56)
- `MAX_MARKERS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 57)
- `MAX_INVARIANTS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 58)
- `MAX_PREDICTIONS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 59)
- `MAX_ANNOTATIONS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 60)
- `MAX_ASSUMPTIONS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 61)
- `MAX_CLAIMS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 62)
- `MAX_BARS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 63)
- `MAX_TEXT` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 64)
- `MAX_LABEL` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 65)
- `MAX_QUOTE` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 66)
- `MAX_STEPS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 67)
- `MAX_DOMAIN_SPAN` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 70)
- `ADVANCED_KINDS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 72)
- `MAX_HEATMAP_CELLS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 75)
- `DEFAULT_HEATMAP_CELLS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 76)
- `MAX_FIELD_CELLS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 77)
- `DEFAULT_FIELD_CELLS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 78)
- `MAX_TRAJECTORY_STEPS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 79)
- `DEFAULT_TRAJECTORY_STEPS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 80)
- `MAX_ITERATIONS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 81)
- `DEFAULT_ITERATIONS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 82)
- `MAX_CONTOURS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 83)
- `MAX_PANEL_WORK` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 87)
- `ESCAPE_MARGIN` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 91)
- `STOP_LEFT` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 93)
- `STOP_NOT_FINITE` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 94)
- `STOP_OUTSIDE` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 95)
- `DIRECTIONS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 97)
- `DIRECTION_LABELS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 98)
- `SAME_TOLERANCE` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 100)
- `INVARIANT_KINDS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 278)
- `RANGED_INVARIANTS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 280)
- `ADVANCED_MODELS` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 685)
- `_PREDICTION_PROBLEM` ([src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py), line 801)

### Explicit exports

`__all__` declares:

- `ADVANCED_KINDS`
- `DIRECTIONS`
- `MAX_FIELD_CELLS`
- `MAX_HEATMAP_CELLS`
- `MAX_ITERATIONS`
- `MAX_PANEL_WORK`
- `MAX_TRAJECTORY_STEPS`
- `advanced_kinds`
- `derived_bounds`
- `DIRECTION_LABELS`
- `SAMPLES`
- `SPEC_VERSION`
- `CompiledFigure`
- `CompiledPanel`
- `InteractiveFigureSpecV1`
- `SpecError`
- `evaluate_figure`
- `evaluate_panel`
- `expanded_free`
- `observed`
- `parse_author_spec`
- `parse_salvaging_predictions`
- `parse_spec`
- `prediction_outcome`
- `shade_value`

## Internal implementation anchors

- `class _Strict(BaseModel)` ([source](../../../../../../src/learnloop/figures/spec.py), line 111)
- `class _Compiler` ([source](../../../../../../src/learnloop/figures/spec.py), line 391)
- `_cells(panel: Any, axis: GridAxis) -> int` ([source](../../../../../../src/learnloop/figures/spec.py), line 701)
- `_overlay_cells(overlay: FieldHeatmap) -> int` ([source](../../../../../../src/learnloop/figures/spec.py), line 707)
- `_bound_range(node: G.Node, parameters: Sequence[Parameter], ranges: Mapping[str, tuple[float, float]]) -> tuple[float, float] | None` ([source](../../../../../../src/learnloop/figures/spec.py), line 711) — The values a sum's bound can take, when the compiler can tell: a number (or its negation), a parameter (its min..max) or a grid axis.
- `_sum_terms(node: G.Node, parameters: Sequence[Parameter], ranges: Mapping[str, tuple[float, float]]) -> int | None` ([source](../../../../../../src/learnloop/figures/spec.py), line 729) — The most terms a sum can have (its bounds' widest reach), or None when its bounds are not countable.
- `_flat_change(prediction: Any) -> Any` ([source](../../../../../../src/learnloop/figures/spec.py), line 804) — ``{"param": "lam", "value": 1}``, the author's misreading, as ``{"lam": 1}``.
- `_prediction_note(prediction: Any, problem: str) -> str` ([source](../../../../../../src/learnloop/figures/spec.py), line 817)
- `_num(value: float) -> float | None` ([source](../../../../../../src/learnloop/figures/spec.py), line 878) — A shown value: None when not finite, never -0 (fix round 3).
- `_value(node: G.Node | None, env: Mapping[str, float], definitions: Mapping[str, G.Node]) -> float` ([source](../../../../../../src/learnloop/figures/spec.py), line 884)
- `_sum_integers(low: float, high: float) -> list[int] | None` ([source](../../../../../../src/learnloop/figures/spec.py), line 972) — The integers :func:`grammar.exact_sum` runs over: its own rule and slack.
- `_grid_values(node: G.Node | None, xs: Sequence[float], ys: Sequence[float], xv: str, yv: str, env: Mapping[str, float], defs: Mapping[str, G.Node]) -> list[list[float | None]]` ([source](../../../../../../src/learnloop/figures/spec.py), line 1037) — Rows by y, columns by x.
- `_heatmap_data(node: G.Node | None, contours: Sequence[G.Node | None], xs: list[float], ys: list[float], xv: str, yv: str, label: str, env: Mapping[str, float], defs: Mapping[str, G.Node]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/spec.py), line 1053)
- `_path(model: Any, nodes: Mapping[str, Any], env: Mapping[str, float], defs: Mapping[str, G.Node]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/spec.py), line 1067) — A trajectory (fixed-step RK4) or an iterated map, cut where it leaves its padded window or stops being finite (``stopped``).
- `_evaluate_advanced(panel: CompiledPanel, env: Mapping[str, float], defs: Mapping[str, G.Node]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/spec.py), line 1140)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/elements|learnloop.figures.elements]] — imports `module`; statically calls `derived_bounds`
- [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]] — imports `module`; statically calls `evaluate_figure`, `parse_spec`
- [[Reference/Modules/learnloop/figures/routes|learnloop.figures.routes]] — imports `module`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; statically calls `advanced_kinds`, `parse_author_spec`, `parse_spec`, `prediction_outcome`
- [[Reference/Modules/learnloop/figures/sketch|learnloop.figures.sketch]] — imports `module`; statically calls `parse_salvaging_predictions`
- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `module`; statically calls `_num`, `bar_ks`, `expanded_free`, `parse_spec`, `plot_xs`
- [[Reference/Modules/learnloop/figures/verify|learnloop.figures.verify]] — imports `module`; statically calls `evaluate_figure`, `expanded_free`, `prediction_outcome`, `shade_value`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/figures/grammar|learnloop.figures.grammar]] — imports `module`; calls `adaptive_simpson`, `canonical`, `check_names`, `evaluate`, `exact_sum`, `expansion`, `is_name`, `parse`, `walk`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `math`, `re`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/elements|learnloop.figures.elements]], [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]], [[Reference/Modules/learnloop/figures/routes|learnloop.figures.routes]], [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]], [[Reference/Modules/learnloop/figures/sketch|learnloop.figures.sketch]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/figure_corpus.py](../../../../../../tests/figure_corpus.py) — direct import
- [tests/figure_panels_corpus.py](../../../../../../tests/figure_panels_corpus.py) — direct import
- [tests/figure_property_corpus.py](../../../../../../tests/figure_property_corpus.py) — direct import
- [tests/test_figure_author_predictions.py](../../../../../../tests/test_figure_author_predictions.py) — direct import
  - `test_a_bad_prediction_is_dropped_with_a_note_and_a_good_one_is_kept`
  - `test_every_prediction_bad_still_leaves_the_figure`
  - `test_predictions_past_the_cap_are_dropped_and_a_non_list_is_too`
  - `test_the_literal_param_value_shape_from_the_trace_is_read_as_the_parameter`
  - `test_the_rest_of_the_figure_is_as_strict_as_ever`
  - `test_the_right_shape_passes_untouched_and_a_parameter_named_param_is_left_alone`
  - `test_the_strict_parser_still_refuses_what_only_the_author_path_forgives`
  - `test_the_trace_end_to_end_one_call_a_shown_figure_a_working_question`
- [tests/test_figure_grammar.py](../../../../../../tests/test_figure_grammar.py) — direct import
  - `test_figure_panels`
  - `test_fuzz_verdicts`
  - `test_g45_two_sided_exponential_p_whatever_lambda`
  - `test_rejected_figures`
  - `test_rejected_inputs`
- [tests/test_figure_panels.py](../../../../../../tests/test_figure_panels.py) — direct import
  - `test_a_path_is_cut_where_it_leaves_its_plot_and_never_drawn_past_it`
  - `test_advanced_kinds_reads_a_spec_and_its_json`
  - `test_an_iterated_map_is_its_recurrence`
  - `test_caps_are_code_owned_constants`
  - `test_each_corpus_figure_that_should_show_passes_steps_one_and_two`
  - `test_invariants_apply_to_rw5b_figures_unchanged`
  - `test_panel_values`
  - `test_rejected_panels`
  - `test_rk4_is_the_textbook_integrator_step_for_step_and_fourth_order`
  - `test_switched_off_the_panels_are_refused_at_parse_and_named`
  - `test_the_corpus_covers_every_panel_kind_and_every_stop`
  - `test_the_same_spec_sampled_more_finely_converges_at_fourth_order`
  - `test_the_work_cap_counts_a_sums_terms`
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
- [tests/test_figures_fix_round2.py](../../../../../../tests/test_figures_fix_round2.py) — direct import
  - `test_pmf_supports_past_the_safe_integers_are_refused`
- [tests/test_figures_fix_round3.py](../../../../../../tests/test_figures_fix_round3.py) — direct import
  - `test_a_finite_map_and_the_flagship_still_pass_structure`
  - `test_a_map_whose_shown_values_overflow_fails_structure`
  - `test_a_parameter_named_like_the_prototype_is_refused`
- [tests/test_figures_fix_round4.py](../../../../../../tests/test_figures_fix_round4.py) — direct import
  - `test_a_chain_past_the_depth_cap_is_a_validation_error`
  - `test_a_plot_domain_whose_samples_overflow_is_refused`
  - `test_structure_requires_every_numeric_leaf_finite`
  - `test_the_verifys_seven_level_chain_compiles_and_evaluates`
- [tests/test_figures_fix_round5.py](../../../../../../tests/test_figures_fix_round5.py) — direct import
  - `test_a_percent_readout_that_overflows_when_scaled_fails_structure`
- [tests/test_figures_help_codex_review.py](../../../../../../tests/test_figures_help_codex_review.py) — direct import
  - `test_f2_a_grammar_figures_shaded_area_is_read_as_shown`
- [tests/test_figures_show_me.py](../../../../../../tests/test_figures_show_me.py) — direct import
  - `test_an_rw5ab_request_hashes_and_prompts_exactly_as_before`
- [tests/test_reader_rw5d_p4a_figures_follow.py](../../../../../../tests/test_reader_rw5d_p4a_figures_follow.py) — direct import
- [tests/test_rw5c_block_policy.py](../../../../../../tests/test_rw5c_block_policy.py) — direct import
- [tests/test_rw5c_display_twins.py](../../../../../../tests/test_rw5c_display_twins.py) — direct import
  - `test_the_derived_bounds_pin_the_evaluator`
- [tests/test_rw5c_judgments.py](../../../../../../tests/test_rw5c_judgments.py) — direct import
  - `test_the_rationale_is_code_text_only`
- [tests/test_rw5c_labels.py](../../../../../../tests/test_rw5c_labels.py) — direct import
  - `test_a2_a_derived_sum_keeps_a_compound_left_hand_side_whole`
  - `test_a_book_elements_label_is_the_books_left_hand_side_and_its_provenance`
  - `test_a_bound_readouts_body_is_grouped_in_its_template`
  - `test_a_readout_whose_body_is_not_the_bare_reference_is_not_derived`
  - `test_a_shade_or_a_highlight_of_an_ai_curve_groups_code_s_own_rendering`
  - `test_an_unchecked_definition_renders_as_its_grammar_name_marked_ai_defined`
  - `test_f2_a_shade_states_the_bounds_the_evaluator_used`
  - `test_f2_an_integral_readout_states_its_evaluated_bounds`
  - `test_f9_endpoints_are_lossless_never_format_value`
  - `test_the_element_map_gives_every_label_a_closed_role_and_no_model_text`
  - `test_under_b_the_delivered_spec_holds_no_model_label_string`
- [tests/test_rw5c_plain_words.py](../../../../../../tests/test_rw5c_plain_words.py) — direct import
  - `test_v1_a_bar_series_grouped_label_through_the_real_check`
- [tests/test_rw5c_source_check.py](../../../../../../tests/test_rw5c_source_check.py) — direct import
  - `test_a_block_that_is_not_ok_is_refused_with_its_reason`
  - `test_a_fake_author_sending_sympy_text_or_a_verified_field_changes_nothing`
  - `test_a_sketch_tier_is_never_checked`
  - `test_a_withheld_span_is_never_read`
  - `test_with_its_invariant_the_half_density_is_still_refused_at_step_two`

## Modification guidance

- Make changes here when the responsibility remains spec within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/spec.py](../../../../../../src/learnloop/figures/spec.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
