---
title: "learnloop.figures.grammar"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/grammar.py"
source_paths:
  - "src/learnloop/figures/grammar.py"
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
  - "learnloop.figures.grammar module"
  - "src/learnloop/figures/grammar.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.grammar`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.grammar` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: The figure grammar: a hand-written parser and evaluator (spec_reader_workbench_v1 §8.2, G21, G22).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py) |
| Source lines | 820 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class GrammarError(ValueError)` ([source](../../../../../../src/learnloop/figures/grammar.py), line 106) — An expression outside the grammar or its caps (never evaluated).
- `class Node` ([source](../../../../../../src/learnloop/figures/grammar.py), line 111) — One parsed node.
- `is_name(text: str) -> bool` ([source](../../../../../../src/learnloop/figures/grammar.py), line 126)
- `parse(source: str) -> Node` ([source](../../../../../../src/learnloop/figures/grammar.py), line 354) — Parse one expression, or raise :class:`GrammarError` (nothing is evaluated).
- `walk(node: Node)` ([source](../../../../../../src/learnloop/figures/grammar.py), line 364) — Every node of ``node`` (no expansion), parent before children, left to right.
- `free_names(node: Node, bound: frozenset[str]=frozenset()) -> set[str]` ([source](../../../../../../src/learnloop/figures/grammar.py), line 375) — Names a node reads that it does not bind itself.
- `expansion(node: Node, definitions: Mapping[str, Node], *, limit: int=MAX_EXPANDED_NODES)` ([source](../../../../../../src/learnloop/figures/grammar.py), line 400) — ``(node, depth)`` for every node of ``node`` with definitions expanded (a definition's name stands for its body, at the name's depth), parent first; iterative, and it stops after ``limit + 1`` nodes (a caller comparing against the cap needs no more).
- `node_count(node: Node, definitions: Mapping[str, Node]) -> int` ([source](../../../../../../src/learnloop/figures/grammar.py), line 420) — Nodes after expanding definitions (a bound on one evaluation's work), counted up to ``MAX_EXPANDED_NODES + 1``.
- `expanded_depth(node: Node, definitions: Mapping[str, Node]) -> int` ([source](../../../../../../src/learnloop/figures/grammar.py), line 427) — How deep ``node`` is with definitions expanded (within the node cap).
- `has_bound_form(node: Node, definitions: Mapping[str, Node]) -> bool` ([source](../../../../../../src/learnloop/figures/grammar.py), line 433)
- `check_names(node: Node, *, known: frozenset[str], definitions: Mapping[str, Node]) -> None` ([source](../../../../../../src/learnloop/figures/grammar.py), line 437) — Every name is known; the expanded expression stays inside the node and depth caps (checked first, by iterative passes, fix round 4); no integral or sum sits inside another (after expanding definitions).
- `adaptive_simpson(function: Any, a: float, b: float) -> float` ([source](../../../../../../src/learnloop/figures/grammar.py), line 572) — The one integration rule (identical in figureGrammar.ts): adaptive Simpson with Richardson's correction, tolerance :data:`SIMPSON_EPS` halving per level, at least :data:`SIMPSON_MIN_LEVEL` and at most :data:`SIMPSON_MAX_LEVEL` levels, and at most :data:`MAX_INTEGRAND_EVALS` eval…
- `exact_sum(function: Any, a: float, b: float) -> float` ([source](../../../../../../src/learnloop/figures/grammar.py), line 624) — ``function(k)`` summed in order over the integers ``ceil(a) ..
- `class WorkExhausted(Exception)` ([source](../../../../../../src/learnloop/figures/grammar.py), line 648) — A :class:`Meter`'s limit was passed (raised from inside evaluation).
  - `__init__(self, used: int, limit: int) -> None` (line 651; internal)
- `class Meter` ([source](../../../../../../src/learnloop/figures/grammar.py), line 657) — A work counter :func:`evaluate` charges one step per node evaluated.
  - `__init__(self, limit: int, every: int) -> None` (line 667; internal)
  - `crossed(self) -> None` (line 674; public)
  - `exhausted(self) -> None` (line 680; public)
  - `checkpoint(self) -> None` (line 683; public)
- `canonical(value: float) -> float` ([source](../../../../../../src/learnloop/figures/grammar.py), line 704) — ``value`` with negative zero as zero: every result either evaluator gives (fix round 3; JavaScript's Math.min(0, -0) is -0, Python's min(0.0, -0.0) is 0.0, and 1/-0 is -Infinity).
- `evaluate(node: Node, env: Mapping[str, float], definitions: Mapping[str, Node] | None=None, meter: Meter | None=None) -> float` ([source](../../../../../../src/learnloop/figures/grammar.py), line 712) — The value of ``node`` with ``env`` (variables and parameters) and ``definitions`` (named expressions, evaluated where they are used).

### Module constants

- `MAX_EXPR_CHARS` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 54)
- `MAX_NODES` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 55)
- `MAX_DEPTH` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 56)
- `MAX_EXPANDED_NODES` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 59)
- `MAX_NAME_CHARS` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 60)
- `MAX_SUM_TERMS` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 61)
- `MAX_SAFE_INTEGER` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 65)
- `SIMPSON_EPS` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 68)
- `SIMPSON_MIN_LEVEL` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 69)
- `SIMPSON_MAX_LEVEL` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 70)
- `SIMPSON_NUDGE` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 72)
- `MAX_INTEGRAND_EVALS` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 73)
- `FUNCTIONS` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 75)
- `SPECIAL_FORMS` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 80)
- `CONSTANTS` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 81)
- `KEYWORDS` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 82)
- `PROTOTYPE_NAMES` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 87)
- `RESERVED` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 90)
- `COMPARISONS` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 91)
- `_TOKEN` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 95)
- `_NAME` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 102)
- `_BLANK` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 103)
- `MAX_EXPANDED_DEPTH` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 397)
- `INF` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 465)
- `NAN` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 466)
- `_UNARY` ([src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py), line 559)

### Explicit exports

`__all__` declares:

- `CONSTANTS`
- `FUNCTIONS`
- `GrammarError`
- `MAX_DEPTH`
- `MAX_EXPANDED_DEPTH`
- `MAX_EXPR_CHARS`
- `MAX_NODES`
- `MAX_SAFE_INTEGER`
- `MAX_SUM_TERMS`
- `PROTOTYPE_NAMES`
- `Meter`
- `Node`
- `RESERVED`
- `WorkExhausted`
- `adaptive_simpson`
- `canonical`
- `check_names`
- `evaluate`
- `exact_sum`
- `expanded_depth`
- `expansion`
- `free_names`
- `has_bound_form`
- `is_name`
- `parse`
- `walk`

## Internal implementation anchors

- `_tokenize(source: str) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/figures/grammar.py), line 130)
- `class _Parser` ([source](../../../../../../src/learnloop/figures/grammar.py), line 154)
- `_finite(value: float) -> bool` ([source](../../../../../../src/learnloop/figures/grammar.py), line 469)
- `_div(a: float, b: float) -> float` ([source](../../../../../../src/learnloop/figures/grammar.py), line 473)
- `_odd_integer(value: float) -> bool` ([source](../../../../../../src/learnloop/figures/grammar.py), line 481)
- `_pow(a: float, b: float) -> float` ([source](../../../../../../src/learnloop/figures/grammar.py), line 485)
- `_exp(a: float) -> float` ([source](../../../../../../src/learnloop/figures/grammar.py), line 504)
- `_log(a: float) -> float` ([source](../../../../../../src/learnloop/figures/grammar.py), line 513)
- `_sqrt(a: float) -> float` ([source](../../../../../../src/learnloop/figures/grammar.py), line 521)
- `_trig(function: Any, a: float) -> float` ([source](../../../../../../src/learnloop/figures/grammar.py), line 527)
- `_erf(a: float) -> float` ([source](../../../../../../src/learnloop/figures/grammar.py), line 533)
- `_phi(a: float) -> float` ([source](../../../../../../src/learnloop/figures/grammar.py), line 539) — The standard normal CDF, ``erfc(-a/sqrt 2)/2`` (no cancellation in the left tail).
- `_floor(a: float) -> float` ([source](../../../../../../src/learnloop/figures/grammar.py), line 547)
- `_extreme(values: list[float], pick: Any) -> float` ([source](../../../../../../src/learnloop/figures/grammar.py), line 553)
- `class _Budget` ([source](../../../../../../src/learnloop/figures/grammar.py), line 567)
- `_simpson_step(f: Any, a: float, b: float, fa: float, fm: float, fb: float, whole: float, eps: float, level: int, budget: _Budget) -> float` ([source](../../../../../../src/learnloop/figures/grammar.py), line 603)
- `_truth(node: Node, env: Mapping[str, float], definitions: Mapping[str, Node], meter: Meter | None) -> bool` ([source](../../../../../../src/learnloop/figures/grammar.py), line 687)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/book_math|learnloop.figures.book_math]] — imports `module`; statically calls `Node`, `free_names`, `is_name`, `node_count`
- [[Reference/Modules/learnloop/figures/elements|learnloop.figures.elements]] — imports `module`; statically calls `GrammarError`
- [[Reference/Modules/learnloop/figures/manim_figure|learnloop.figures.manim_figure]] — imports `module`; statically calls `check_names`, `evaluate`, `is_name`, `parse`
- [[Reference/Modules/learnloop/figures/sketch|learnloop.figures.sketch]] — imports `module`; statically calls `check_names`, `free_names`, `is_name`, `parse`
- [[Reference/Modules/learnloop/figures/sketch_verify|learnloop.figures.sketch_verify]] — imports `module`; statically calls `evaluate`
- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `module`; statically calls `Node`, `evaluate`, `walk`
- [[Reference/Modules/learnloop/figures/spec|learnloop.figures.spec]] — imports `module`; statically calls `adaptive_simpson`, `canonical`, `check_names`, `evaluate`, `exact_sum`, `expansion`, `is_name`, `parse`, `walk`
- [[Reference/Modules/learnloop/figures/verify|learnloop.figures.verify]] — imports `module`; statically calls `adaptive_simpson`, `evaluate`, `exact_sum`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `math`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/book_math|learnloop.figures.book_math]], [[Reference/Modules/learnloop/figures/elements|learnloop.figures.elements]], [[Reference/Modules/learnloop/figures/manim_figure|learnloop.figures.manim_figure]], [[Reference/Modules/learnloop/figures/sketch|learnloop.figures.sketch]], [[Reference/Modules/learnloop/figures/sketch_verify|learnloop.figures.sketch_verify]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/figure_corpus.py](../../../../../../tests/figure_corpus.py) — direct import
- [tests/figure_property_corpus.py](../../../../../../tests/figure_property_corpus.py) — direct import
- [tests/katex_meaning.py](../../../../../../tests/katex_meaning.py) — direct import
- [tests/test_figure_grammar.py](../../../../../../tests/test_figure_grammar.py) — direct import
  - `test_expression_values`
  - `test_fuzz_verdicts`
  - `test_integral_budget_and_sum_cap`
  - `test_random_text_is_refused_cleanly_or_parsed`
  - `test_rejected_inputs`
  - `test_simpson_reads_a_jump_from_the_correct_side`
  - `test_the_corpus_covers_every_construct_and_panel_kind`
- [tests/test_figures_fix_round2.py](../../../../../../tests/test_figures_fix_round2.py) — direct import
  - `test_a_sum_near_the_safe_integers_counts_its_terms`
- [tests/test_figures_fix_round3.py](../../../../../../tests/test_figures_fix_round3.py) — direct import
  - `test_a_parameter_named_like_the_prototype_is_refused`
  - `test_no_value_is_negative_zero`
  - `test_prototype_and_underscore_names_are_refused_when_parsed`
- [tests/test_figures_fix_round4.py](../../../../../../tests/test_figures_fix_round4.py) — direct import
  - `test_the_depth_cap_is_the_same_in_typescript`
  - `test_the_verifys_seven_level_chain_compiles_and_evaluates`
- [tests/test_rw5c_book_math.py](../../../../../../tests/test_rw5c_book_math.py) — direct import
  - `test_the_e_rule_reads_only_a_power_or_mathrm`
- [tests/test_rw5c_katex_tree.py](../../../../../../tests/test_rw5c_katex_tree.py) — direct import
  - `test_each_read_form_has_the_pages_mathml_and_means_it`
- [tests/test_rw5c_labels.py](../../../../../../tests/test_rw5c_labels.py) — direct import
  - `test_a_power_of_a_power_keeps_its_grouping_in_plain_text`
  - `test_a_scientific_literal_as_a_base_is_grouped_in_both_writers`
  - `test_a_sum_or_an_integral_written_inside_a_product_is_grouped`
  - `test_codes_own_rendering_of_an_expression`
  - `test_every_other_code_owned_label_template_renders_in_katex`
  - `test_the_plain_writer_parses_back_to_the_same_value_and_the_tex_writer_means_it_in_katex`
- [tests/test_rw5c_plain_words.py](../../../../../../tests/test_rw5c_plain_words.py) — direct import
  - `test_generated_words_read_back_to_the_value_katex_s_own_mathml_means`
- [tests/test_sketch_verify.py](../../../../../../tests/test_sketch_verify.py) — direct import
  - `test_a_pairs_claim_is_charged_for_its_probes_own_x`
  - `test_the_meter_stops_one_evaluation_at_the_cap_and_at_the_clock`

## Modification guidance

- Make changes here when the responsibility remains grammar within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/grammar.py](../../../../../../src/learnloop/figures/grammar.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
