---
title: "learnloop.figures.manim_figure"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/manim_figure.py"
source_paths:
  - "src/learnloop/figures/manim_figure.py"
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
  - "learnloop.figures.manim_figure module"
  - "src/learnloop/figures/manim_figure.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.manim_figure`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.manim_figure` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Reader RW5d P2b: the ``manim`` tier's program, ``ManimFigureV1``, and its declared-function checks.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py) |
| Source lines | 928 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ManimFigureError(ValueError)` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 94) — A Manim figure outside its contract; ``problems`` says why (sent back to the author).
  - `__init__(self, problems: Sequence[str]) -> None` (line 97; internal)
- `class Argument` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 103)
- `class Function` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 110)
- `class Claim` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 116)
- `class ManimFigure` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 125)
  - `declared(self) -> dict[str, Any]` (line 134; public)
- `parse_declared(raw: Any) -> tuple[tuple[Function, ...], tuple[Claim, ...], tuple[str, ...], list[str]]` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 152) — The declared functions, claims and ``plotted_from`` entries of ``declared_json`` (JSON text or a mapping): what is well formed, and the problems of what is not.
- `parse_figure(output: Any) -> ManimFigure` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 250) — A :class:`ManimFigure` from the rich author's answer (scene fields and ``declared_json``), or :class:`ManimFigureError` with every problem.
- `class Extraction` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 279)
- `module_bindings(tree: ast.Module) -> Counter[str]` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 345) — How many times each name is bound in the module's own scope (Codex review F4): assignments (augmented included), deletions, defs, classes, imports and loop or ``with`` targets at module level, outside any def, lambda or class body; a name declared ``global`` anywhere counts twic…
- `extract_functions(scene_code: str, functions: Sequence[Function]) -> Extraction` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 455) — The checkable part of the scene (module docstring).
- `grid(function: Function) -> list[list[float]]` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 580) — Each argument's min, midpoint and max, every combination (at most 81 points).
- `sandboxed_runner(module_source: str, points: Mapping[str, list[list[float]]]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 639) — Run the extracted functions in the concept pipeline's bubblewrap profile (:func:`learnloop.content.authoring.pf_sandbox.run_sandboxed_python`: no network, no home or vault, read-only system, rlimits, a wall clock); manim is never imported (the module names only math and numpy).
- `class CheckReport` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 661)
  - `failed(self) -> bool` (line 671; public)
- `plotted_from_ok(scene_code: str, function: str) -> bool` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 726) — ``function`` supplies a Manim plot call's curve (spec §9b.1, AST-checked; Codex review F5): it is that call's function argument (:data:`PLOT_FUNCTION_ARGS`), by name or inside a lambda that calls it, and the name there resolves to the module's ``def``: bound once in the module a…
- `class ClaimWorkExceeded(Exception)` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 757) — The claim check passed its work cap or its wall clock (code's words in ``reason``).
  - `__init__(self, reason: str) -> None` (line 760; internal)
- `check_claims(figure: ManimFigure, *, runner: FunctionRunner | None=None, interrupt: Callable[[], None] | None=None) -> CheckReport` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 802) — Check the figure's declared claims (module docstring).

### Module constants

- `MAX_FUNCTIONS` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 47)
- `MAX_FUNCTION_ARGS` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 49)
- `MAX_FIGURE_CLAIMS` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 51)
- `MAX_PLOTTED` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 53)
- `MAX_TITLE` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 55)
- `MAX_NARRATION` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 56)
- `FUNCTION_CHECK_SECONDS` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 58)
- `FUNCTION_CHECK_MEMORY_MB` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 59)
- `MAX_CLAIM_WORK` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 63)
- `CHECK_SECONDS` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 67)
- `INTERRUPT_SECONDS` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 70)
- `_TICK_WORK` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 73)
- `CLAIM_KINDS` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 74)
- `INVARIANT_PROPERTIES` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 75)
- `SAFE_BUILTINS` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 78)
- `PLOT_FUNCTION_ARGS` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 84)
- `PLOT_CALLS` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 90)
- `_ALLOWED_MODULES` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 91)
- `_SCOPES` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 339)
- `_SCALAR_BUILTINS` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 342)
- `HARNESS` ([src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py), line 587)

### Explicit exports

`__all__` declares:

- `CLAIM_KINDS`
- `CheckReport`
- `ClaimWorkExceeded`
- `Extraction`
- `Function`
- `FunctionRunner`
- `ManimFigure`
- `ManimFigureError`
- `check_claims`
- `extract_functions`
- `grid`
- `parse_declared`
- `parse_figure`
- `plotted_from_ok`
- `sandboxed_runner`

## Internal implementation anchors

- `_number(value: Any, what: str, problems: list[str]) -> float | None` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 145)
- `_module_aliases(tree: ast.Module) -> tuple[dict[str, str], list[str]]` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 287) — Top-level ``math``/``numpy`` names (alias -> what it is) and their import lines.
- `_bound_names(node: ast.AST) -> set[str]` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 310) — Names a function binds locally (its arguments, assignments, loop and comprehension targets).
- `_free_reads(node: ast.AST) -> set[str]` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 322)
- `_forbidden_shape(node: ast.AST) -> str | None` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 326)
- `_root_name(node: ast.AST) -> str | None` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 384)
- `_mutated_names(tree: ast.Module) -> set[str]` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 390) — Names whose object is mutated somewhere in the scene, in any scope (Codex review F4): an item or attribute assigned, augmented or deleted (``A[0] = 1``, ``A.x += 1``, ``del A[0]``), or a method called on it (``A.fill(0)``, ``L.append(1)``) or written through ``out=A``.
- `_passed_names(tree: ast.Module, skip: Sequence[ast.AST]) -> set[str]` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 414) — Names handed bare to a call as an argument (``g(A)``, ``g(x=A)``, ``g(*A)``) anywhere outside ``skip`` (the declared functions and the constants' own definitions): a mutable object handed to arbitrary code may be changed by it.
- `_immutable_value(node: ast.AST, aliases: Mapping[str, str], immutable: set[str]) -> bool` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 432) — A constant's value can't be a mutable object: literals, arithmetic, tuples, ``math`` (or ``numpy`` scalar names, never calls), scalar builtins and other immutable constants (Codex review F4).
- `_value(entry: Mapping[str, Any]) -> float | None` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 675)
- `_close(value: float, expected: float) -> bool` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 684) — The sketch tier's tolerance (spec §9b.4: same tolerances).
- `_scope_binds(scope: ast.AST, name: str) -> bool` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 690) — ``name`` is bound in this def, lambda or class (its arguments or any store in its body; nested scopes included, which only errs towards *not* recognizing a plotted function).
- `_function_argument(call: ast.Call, keyword: str) -> ast.AST | None` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 705)
- `_draws_from(argument: ast.AST, function: str) -> bool` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 712) — The plot call's function argument is the module's ``function``: the bare name, or a lambda that calls it (and doesn't take it as an argument).
- `class _ClaimBudget(G.Meter)` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 765) — The oracle's limits (Codex review F2), the sketch verifier's pattern: every node the grammar evaluates for a claim is charged as it runs (:data:`MAX_CLAIM_WORK`), and every :data:`_TICK_WORK` steps the clock is read against the deadline of the whole check (:data:`CHECK_SECONDS`)…
- `_check_claims(figure: ManimFigure, *, runner: FunctionRunner | None, budget: _ClaimBudget, report: CheckReport) -> CheckReport` ([source](../../../../../../src/learnloop/figures/manim_figure.py), line 824)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `module`; statically calls `ManimFigure`, `check_claims`, `parse_figure`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/authoring/pf_sandbox|learnloop.content.authoring.pf_sandbox]] — imports `module`; calls `SandboxLimits`, `run_sandboxed_python`
- [[Reference/Modules/learnloop/figures/grammar|learnloop.figures.grammar]] — imports `module`; calls `check_names`, `evaluate`, `is_name`, `parse`
- [[Reference/Modules/learnloop/figures/labels|learnloop.figures.labels]] — imports `module`; calls `label_problems`
- [[Reference/Modules/learnloop/figures/sketch|learnloop.figures.sketch]] — imports `CLAIM_REL_TOL`, `SKETCH_MAX_CLAIM_WORK`, `expression_steps`, `impersonates`; calls `expression_steps`, `impersonates`

### Platform and third-party dependencies

- Standard library: `__future__`, `ast`, `collections`, `dataclasses`, `itertools`, `json`, `math`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_label_wording.py](../../../../../../tests/test_figure_label_wording.py) — direct import
  - `test_f1_a_manim_narration_saying_it_matches_the_book_is_a_problem`
  - `test_f1_remainder_a_manim_narration_with_a_bold_source_claim_is_a_problem`
  - `test_f2_a_manim_narration_with_a_check_line_is_a_problem`
- [tests/test_figures_help_codex_review.py](../../../../../../tests/test_figures_help_codex_review.py) — direct import
- [tests/test_manim_figure_checks.py](../../../../../../tests/test_manim_figure_checks.py) — direct import
  - `test_a_cancel_reaches_a_long_oracle_phase`
  - `test_a_claim_set_past_the_work_cap_is_refused_before_the_oracle_runs`
  - `test_a_constant_the_scene_changes_makes_its_function_not_checkable`
  - `test_a_declared_function_bound_twice_is_not_checkable`
  - `test_a_rebound_plot_name_keeps_the_function_check_and_drops_the_curve`
  - `test_a_sandbox_that_cannot_run_is_a_failure_never_a_pass`
  - `test_a_wrong_claim_fails_in_codes_words`
  - `test_an_exception_or_a_non_finite_value_at_a_grid_point_fails`
  - `test_an_immutable_constant_the_scene_only_reads_is_kept`
  - `test_declared_json_problems_are_reported_for_the_second_attempt`
  - `test_extraction_keeps_the_declared_defs_and_their_constants_and_never_manim`
  - `test_good_claims_pass_with_scoped_check_lines_and_an_unextractable_claim_is_dropped`
  - `test_hostile_functions_are_never_extracted`
  - `test_no_claims_means_nothing_runs_and_the_figure_is_not_checked`
  - `test_plotted_from_is_ast_checked`
  - `test_plotted_from_resolves_the_binding_and_the_function_argument`
  - `test_the_finding_f4_reproduction_issues_no_check_line`
  - `test_the_meter_stops_the_oracle_even_when_the_estimate_falls_short`
  - `test_the_whole_check_has_one_deadline`
- [tests/test_manim_sandbox_hostile.py](../../../../../../tests/test_manim_sandbox_hostile.py) — direct import
  - `test_a_runaway_declared_function_is_stopped_by_the_sandbox_clock`
  - `test_the_declared_functions_run_in_the_real_sandbox_without_manim`

## Modification guidance

- Make changes here when the responsibility remains manim figure within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/manim_figure.py](../../../../../../src/learnloop/figures/manim_figure.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
