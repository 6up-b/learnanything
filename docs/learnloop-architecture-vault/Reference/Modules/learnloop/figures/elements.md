---
title: "learnloop.figures.elements"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/elements.py"
source_paths:
  - "src/learnloop/figures/elements.py"
source_commit: "ddda73b843d2383ec920b205be7bfccd11240279"
source_commit_timestamp: "2026-11-03T00:29:56-05:00"
source_worktree_state: "clean"
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
  - "learnloop.figures.elements module"
  - "src/learnloop/figures/elements.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.elements`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.elements` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Reader RW5c: code-owned, element-scoped labels (spec_reader_rw5c_checked_labels_v1 §7, §8.2; G23d, G23e).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/elements.py](../../../../../../src/learnloop/figures/elements.py) |
| Source lines | 603 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `ddda73b843d2383ec920b205be7bfccd11240279` |
| Commit timestamp | `2026-11-03T00:29:56-05:00` |

## Public API

- `class Slot` ([source](../../../../../../src/learnloop/figures/elements.py), line 64) — One ``Label`` or ``Text`` field found by the walk.
- `label_slots(model: BaseModel, path: tuple[Any, ...]=()) -> Iterator[Slot]` ([source](../../../../../../src/learnloop/figures/elements.py), line 87) — Every ``Label``- and ``Text``-typed field of ``model``, at any depth: one walk by type introspection, never a list of element kinds (G23d).
- `schema_label_fields(root: type[BaseModel]=S.InteractiveFigureSpecV1) -> set[tuple[str, str, str]]` ([source](../../../../../../src/learnloop/figures/elements.py), line 109) — ``(model, field, kind)`` for every ``Label``/``Text`` field of the schema, from its types alone.
- `element_id(path: Sequence[Any]) -> str` ([source](../../../../../../src/learnloop/figures/elements.py), line 138) — An element's id: where it is in the spec (a closed alphabet, never model text).
- `symbol_tex(name: str, *, definition: bool=False) -> str` ([source](../../../../../../src/learnloop/figures/elements.py), line 160) — A grammar name as a symbol.
- `to_tex(node: G.Node, definitions: Mapping[str, Any], _outer: int=0) -> str` ([source](../../../../../../src/learnloop/figures/elements.py), line 195) — The expression as TeX: code's words from a closed alphabet (names are ASCII, grammar.py's ``_NAME``), one frame per level of a capped tree.
- `to_plain(node: G.Node, _outer: int=0) -> str` ([source](../../../../../../src/learnloop/figures/elements.py), line 254) — The expression as plain text for ``aria-label``s and SVG text: the grammar's own infix, rebuilt from the tree.
- `class BookLabel` ([source](../../../../../../src/learnloop/figures/elements.py), line 303) — A checked definition's candidate: the book's own words for its label.
  - `operand(self) -> tuple[str, str]` (line 319; public) — ``lhs`` where a template writes an operator or words before it, as TeX and plain text: a compound one is visibly whole (Astra A2: \sum 1-F(k) beside the sum of all of 1-F(k)).
- `template_words(template: Mapping[str, Any], bounds: Mapping[str, Any], number: Any) -> tuple[str, str]` ([source](../../../../../../src/learnloop/figures/elements.py), line 392) — The closed derived-label templates (§7.2), in TeX and in plain text.
- `element_map(compiled: S.CompiledFigure, book: Mapping[str, BookLabel], book_elements: Mapping[str, str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/elements.py), line 443) — Every label-carrying element and its role (§7.2).
- `rewrite_spec(spec_json: str, compiled: S.CompiledFigure) -> tuple[str, dict[str, str]]` ([source](../../../../../../src/learnloop/figures/elements.py), line 538) — The delivered spec with every label replaced by its element id, references too (§7.4, by construction: the walk reaches every ``Label``), and the map from each model label a reference may name to its id.

### Module constants

- `ROLES` ([src/learnloop/figures/elements.py](../../../../../../src/learnloop/figures/elements.py), line 46)
- `VOICES` ([src/learnloop/figures/elements.py](../../../../../../src/learnloop/figures/elements.py), line 47)
- `LABEL_FIELDS` ([src/learnloop/figures/elements.py](../../../../../../src/learnloop/figures/elements.py), line 49)
- `TEXT_FIELDS` ([src/learnloop/figures/elements.py](../../../../../../src/learnloop/figures/elements.py), line 57)
- `_GREEK_TEX` ([src/learnloop/figures/elements.py](../../../../../../src/learnloop/figures/elements.py), line 148)
- `_TEX_FUNCTIONS` ([src/learnloop/figures/elements.py](../../../../../../src/learnloop/figures/elements.py), line 153)
- `_TEX_OPS` ([src/learnloop/figures/elements.py](../../../../../../src/learnloop/figures/elements.py), line 156)
- `_PRECEDENCE` ([src/learnloop/figures/elements.py](../../../../../../src/learnloop/figures/elements.py), line 157)
- `_BASE` ([src/learnloop/figures/elements.py](../../../../../../src/learnloop/figures/elements.py), line 192)

### Explicit exports

`__all__` declares:

- `BookLabel`
- `LABEL_FIELDS`
- `ROLES`
- `Slot`
- `TEXT_FIELDS`
- `VOICES`
- `element_id`
- `element_map`
- `label_slots`
- `rewrite_spec`
- `schema_label_fields`
- `symbol_tex`
- `template_words`
- `to_plain`
- `to_tex`

## Internal implementation anchors

- `_field_kind(hint: Any) -> str | None` ([source](../../../../../../src/learnloop/figures/elements.py), line 74)
- `_hints(model: type[BaseModel]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/elements.py), line 82)
- `_walk_value(value: Any, path: tuple[Any, ...]) -> Iterator[Slot]` ([source](../../../../../../src/learnloop/figures/elements.py), line 101)
- `_number_tex(text: str) -> str` ([source](../../../../../../src/learnloop/figures/elements.py), line 182)
- `_token_plain(token: str) -> str` ([source](../../../../../../src/learnloop/figures/elements.py), line 291) — A book symbol's token as plain text.
- `_element(path: Sequence[Any], role: str, tex: str, plain: str, voice: str, **extra: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/elements.py), line 329)
- `_source(label: BookLabel) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/elements.py), line 334)
- `_bare(node: G.Node | None, definitions: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/figures/elements.py), line 338)
- `_curve(path: Sequence[Any], node: G.Node | None, axis: str | None, compiled: S.CompiledFigure, book: Mapping[str, BookLabel], book_elements: Mapping[str, str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/elements.py), line 342) — A series or a readout's plain value: ``book``, else code's rendering in the model's voice.
- `_operand(curve: Mapping[str, Any], node: G.Node | None, compiled: S.CompiledFigure, book: Mapping[str, BookLabel]) -> tuple[str, str]` ([source](../../../../../../src/learnloop/figures/elements.py), line 364) — A curve as a template's operand: the book's left-hand side, or code's rendering grouped as a sum's or an integral's body is.
- `_template(path: Sequence[Any], kind: str, panel: int, index: int, *, body_tex: str, body_plain: str, variable: str, role: str, voice: str, compiled: S.CompiledFigure, env: Mapping[str, float], **extra: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/elements.py), line 376) — A shade, a highlight or a bound readout: its words state the bounds the evaluator used (F2) and name them losslessly (F9).
- `_panel_tex(panel: S.CompiledPanel, definitions: Mapping[str, Any]) -> tuple[str, str]` ([source](../../../../../../src/learnloop/figures/elements.py), line 422) — A non-curve panel's own expression, for a label its author gave it.
- `_slot_element_path(slot: Slot) -> tuple[Any, ...]` ([source](../../../../../../src/learnloop/figures/elements.py), line 531) — The element a label slot names: its owner's path (a readout's and a panel's own ``label`` name the panel).
- `_assign(data: Any, path: Sequence[Any], value: str) -> None` ([source](../../../../../../src/learnloop/figures/elements.py), line 578)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; statically calls `rewrite_spec`
- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `module`; statically calls `BookLabel`, `element_id`, `element_map`, `to_tex`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/figures/book_math|learnloop.figures.book_math]] — imports `module`
- [[Reference/Modules/learnloop/figures/display_format|learnloop.figures.display_format]] — imports `js_string`
- [[Reference/Modules/learnloop/figures/grammar|learnloop.figures.grammar]] — imports `module`; calls `GrammarError`
- [[Reference/Modules/learnloop/figures/spec|learnloop.figures.spec]] — imports `module`; calls `derived_bounds`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `sys`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]], [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_rw5c_display_twins.py](../../../../../../tests/test_rw5c_display_twins.py) — direct import
  - `test_the_derived_words_are_the_corpus_s_from_the_book_s_left_hand_side`
- [tests/test_rw5c_labels.py](../../../../../../tests/test_rw5c_labels.py) — direct import
  - `test_a_book_elements_label_is_the_books_left_hand_side_and_its_provenance`
  - `test_a_bound_readouts_body_is_grouped_in_its_template`
  - `test_a_generated_left_hand_side_is_whole_in_every_template_in_katexs_own_mathml`
  - `test_a_power_of_a_power_keeps_its_grouping_in_plain_text`
  - `test_a_readout_whose_body_is_not_the_bare_reference_is_not_derived`
  - `test_a_scientific_literal_as_a_base_is_grouped_in_both_writers`
  - `test_a_shade_or_a_highlight_of_an_ai_curve_groups_code_s_own_rendering`
  - `test_a_sum_or_an_integral_written_inside_a_product_is_grouped`
  - `test_an_unchecked_definition_renders_as_its_grammar_name_marked_ai_defined`
  - `test_codes_own_rendering_of_an_expression`
  - `test_every_other_code_owned_label_template_renders_in_katex`
  - `test_f2_an_integral_readout_states_its_evaluated_bounds`
  - `test_f3_a_scientific_endpoint_is_written_as_the_power_it_means`
  - `test_f9_endpoints_are_lossless_never_format_value`
  - `test_g23d_a_new_panel_with_a_label_fails_until_it_is_mapped`
  - `test_g23d_the_walk_covers_every_label_and_text_field_of_the_schema`
  - `test_the_element_map_gives_every_label_a_closed_role_and_no_model_text`
  - `test_the_plain_writer_parses_back_to_the_same_value_and_the_tex_writer_means_it_in_katex`
  - `test_under_b_the_delivered_spec_holds_no_model_label_string`
- [tests/test_rw5c_plain_words.py](../../../../../../tests/test_rw5c_plain_words.py) — direct import
  - `test_a_symbol_token_s_closed_form_is_read_as_a_name`
  - `test_the_fallback_is_written_whole_as_an_operand_with_no_brackets`

## Modification guidance

- Make changes here when the responsibility remains elements within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/elements.py](../../../../../../src/learnloop/figures/elements.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
