---
title: "learnloop.figures.book_math"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/book_math.py"
source_paths:
  - "src/learnloop/figures/book_math.py"
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
  - "learnloop.figures.book_math module"
  - "src/learnloop/figures/book_math.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.book_math`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.book_math` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Reader RW5c: code reads the book's equation (spec_reader_rw5c_checked_labels_v1 §5.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py) |
| Source lines | 1299 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `ddda73b843d2383ec920b205be7bfccd11240279` |
| Commit timestamp | `2026-11-03T00:29:56-05:00` |

## Public API

- `class Unreadable(ValueError)` ([source](../../../../../../src/learnloop/figures/book_math.py), line 121) — A segment outside the table; ``reason`` is one key of :data:`REASONS`.
  - `__init__(self, reason: str) -> None` (line 124; internal)
- `class Segment` ([source](../../../../../../src/learnloop/figures/book_math.py), line 130) — One math element the page shows for a block's text.
- `class Relation` ([source](../../../../../../src/learnloop/figures/book_math.py), line 142) — A read equation.
- `segments(text: str, *, trees: KT.Trees | None=None) -> list[Segment]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 163) — The equations the page shows for a block's text (§5.2), found by the page's own pipeline (:meth:`.katex_tree.Trees.page_math`), or :class:`Unreadable`.
- `binary64_exact(text: str) -> bool` ([source](../../../../../../src/learnloop/figures/book_math.py), line 410) — Whether a decimal's exact value is a binary64 value: no made-up bound, no ``Decimal`` context (§6.1): 0, 1, 0.5, 0.375, never 0.3.
- `plain_words(nodes: Sequence[Tree]) -> str` ([source](../../../../../../src/learnloop/figures/book_math.py), line 961) — KaTeX's list as plain text for ``aria-label``s, SVG text and a prediction's choices, in the reader's vocabulary, with a fraction's and a script's grouping written out: ``dF(x)/dx``, ``(1-a)/k``, ``e^(-k)``.
- `read_relation(latex: str, *, display: bool=False, trees: KT.Trees | None=None) -> Relation` ([source](../../../../../../src/learnloop/figures/book_math.py), line 1239) — One math segment read as one relation, or :class:`Unreadable`.

### Module constants

- `READER_VERSION` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 62)
- `REASONS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 65)
- `_GREEK` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 77)
- `_FUNCTIONS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 86)
- `_EXTREMES` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 87)
- `_LABELS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 90)
- `_CONDITION_OPS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 100)
- `_CASE_WORDS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 102)
- `_NUMBER` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 103)
- `_KERNS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 105)
- `_SPACES` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 106)
- `_MACRO_DEFINITION` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 108)
- `_LABEL_NODES` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 111)
- `_ONE_TERM_NODES` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 114)
- `PLAIN_FALLBACK` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 118)
- `_ATOMS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 219)
- `_NODE_REASONS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 228)
- `_PLAIN_ATOMS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 934)
- `_PLAIN_ORDS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 944)
- `_PLAIN_DELIMITERS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 946)
- `_PLAIN_OPERATORS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 948)
- `_PLAIN_FONTS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 950)
- `_PLAIN_ACCENTS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 952)
- `_PLAIN_TEXT_PUNCTUATION` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 954)

### Explicit exports

`__all__` declares:

- `PLAIN_FALLBACK`
- `READER_VERSION`
- `REASONS`
- `Relation`
- `Segment`
- `Unreadable`
- `binary64_exact`
- `plain_words`
- `read_relation`
- `segments`

## Internal implementation anchors

- `class _Item` ([source](../../../../../../src/learnloop/figures/book_math.py), line 191) — One thing in reading order.
- `_body(node: Tree) -> Sequence[Tree]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 205)
- `_word(nodes: Sequence[Tree]) -> str | None` ([source](../../../../../../src/learnloop/figures/book_math.py), line 209) — The letters of ``\mathrm{...}`` or ``\operatorname{...}``, if letters are all it holds.
- `_is_table_space(node: Tree) -> bool` ([source](../../../../../../src/learnloop/figures/book_math.py), line 231)
- `_refuse_symbol(text: str) -> Unreadable` ([source](../../../../../../src/learnloop/figures/book_math.py), line 236)
- `_items(nodes: Sequence[Tree]) -> list[_Item]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 240)
- `_base_items(base: Tree) -> list[_Item]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 278)
- `_atom_item(base: Tree, text: str) -> _Item` ([source](../../../../../../src/learnloop/figures/book_math.py), line 332)
- `_leftright_items(base: Tree) -> list[_Item]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 342)
- `_font_item(base: Tree) -> _Item` ([source](../../../../../../src/learnloop/figures/book_math.py), line 360)
- `_starts_with_d(node: Tree) -> bool` ([source](../../../../../../src/learnloop/figures/book_math.py), line 376) — Whether a fraction's side begins with a differential's ``d``.
- `_dyadic_text(value: Fraction) -> str` ([source](../../../../../../src/learnloop/figures/book_math.py), line 393) — A dyadic rational's exact decimal, which reads back as the same fraction.
- `class _Reader` ([source](../../../../../../src/learnloop/figures/book_math.py), line 424)
- `_numeric_side(node: Tree) -> Fraction | None` ([source](../../../../../../src/learnloop/figures/book_math.py), line 790) — One side of a fraction as a number, when it is one numeral.
- `_numeric_sides(item: _Item) -> tuple[Fraction | None, Fraction | None]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 800)
- `_cell(cell: Tree) -> Sequence[Tree]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 805) — A cell of an array: KaTeX wraps its contents in a style and a group.
- `_text_words(node: Tree) -> str` ([source](../../../../../../src/learnloop/figures/book_math.py), line 814) — A ``\text{...}``'s words: its characters as KaTeX lists them.
- `_without_end_punctuation(nodes: Sequence[Tree]) -> Sequence[Tree]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 828) — Without the ``,`` or ``.`` a sentence or a row ends on.
- `_flip(op: str) -> str` ([source](../../../../../../src/learnloop/figures/book_math.py), line 836)
- `_compare(point: Fraction, op: str, value: Fraction) -> bool` ([source](../../../../../../src/learnloop/figures/book_math.py), line 840)
- `_is_atom(node: Tree, family: str, text: str | None=None) -> bool` ([source](../../../../../../src/learnloop/figures/book_math.py), line 848)
- `_split_relation(nodes: Sequence[Tree]) -> tuple[int, int]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 852) — Where the one top-level ``=`` or ``:=`` of KaTeX's list is, as ``(lhs_end, rhs_start)`` indices: a segment must hold exactly one.
- `_compound(nodes: Sequence[Tree]) -> bool` ([source](../../../../../../src/learnloop/figures/book_math.py), line 885) — Whether a left-hand side, in KaTeX's list, is more than one term to a reader: an operator written before it (``\sum``, ``\int``) would seem to reach only its first.
- `class _NoWords(Exception)` ([source](../../../../../../src/learnloop/figures/book_math.py), line 957) — The tree holds something the plain writer has no faithful words for.
- `_drawn(nodes: Sequence[Tree]) -> list[Tree]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 973) — What a list draws: braces draw nothing and gaps have no words of their own.
- `_plain_list(nodes: Sequence[Tree]) -> str` ([source](../../../../../../src/learnloop/figures/book_math.py), line 985) — The pieces in order: only a word, or a gap the page shows, parts two letters or digits.
- `_ends_a_term(node: Tree | None, families: tuple[str, ...]) -> bool` ([source](../../../../../../src/learnloop/figures/book_math.py), line 1011)
- `_plain_node(node: Tree) -> str` ([source](../../../../../../src/learnloop/figures/book_math.py), line 1015)
- `_plain_whole(node: Tree | None) -> str` ([source](../../../../../../src/learnloop/figures/book_math.py), line 1060) — Something that must have words: an empty group (``\sqrt{}``) says nothing to write.
- `_plain_text(body: Sequence[Tree]) -> str` ([source](../../../../../../src/learnloop/figures/book_math.py), line 1069)
- `_one_symbol(text: str) -> bool` ([source](../../../../../../src/learnloop/figures/book_math.py), line 1082)
- `_plain_script(node: Tree) -> str` ([source](../../../../../../src/learnloop/figures/book_math.py), line 1086)
- `_plain_script_part(node: Tree) -> str` ([source](../../../../../../src/learnloop/figures/book_math.py), line 1107)
- `_is_differential(node: Tree) -> bool` ([source](../../../../../../src/learnloop/figures/book_math.py), line 1112)
- `_one_factor(drawn: Sequence[Tree]) -> bool` ([source](../../../../../../src/learnloop/figures/book_math.py), line 1117) — Whether a denominator reads whole after a slash with no brackets: ``a/bc`` parts books (``ambiguous_slash``).
- `_plain_fraction(node: Tree) -> str` ([source](../../../../../../src/learnloop/figures/book_math.py), line 1139)
- `_lhs_args(nodes: Sequence[Tree]) -> tuple[tuple[str, ...], dict[str, set[str]], dict[str, str]]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 1160) — The symbols of a ``name(args)`` left-hand side, with how the book spells them; empty for ``P(X = k)``, ``E[X]`` or a bare name.
- `_walk(value: Any) -> Iterator[Tree]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 1195) — Every node under ``value``, whatever field holds it.
- `_without_places(value: Any) -> Any` ([source](../../../../../../src/learnloop/figures/book_math.py), line 1208)
- `_parse(trees: KT.Trees, source: str, display: bool) -> list[Tree]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 1216)
- `_left_hand_side(source: str, tree: Sequence[Tree], lhs_end: int, *, trees: KT.Trees, display: bool) -> str` ([source](../../../../../../src/learnloop/figures/book_math.py), line 1223) — The book's own substring, kept only when KaTeX reads it alone as the left of this parse.
- `_translate(source: str, tree: Sequence[Tree], *, trees: KT.Trees, display: bool) -> Relation` ([source](../../../../../../src/learnloop/figures/book_math.py), line 1262)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/elements|learnloop.figures.elements]] — imports `module`
- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `module`; statically calls `binary64_exact`, `read_relation`, `segments`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/figures/grammar|learnloop.figures.grammar]] — imports `module`; calls `Node`, `free_names`, `is_name`, `node_count`
- [[Reference/Modules/learnloop/figures/katex_tree|learnloop.figures.katex_tree]] — imports `module`; calls `Trees`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `fractions`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/elements|learnloop.figures.elements]], [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_rw5c_book_math.py](../../../../../../tests/test_rw5c_book_math.py) — direct import
  - `test_caps_and_a_seeded_fuzz_never_raise_outside_the_reasons`
  - `test_cases_refusals`
  - `test_each_unreadable_construct_has_its_reason`
  - `test_every_reason_key_is_in_the_closed_list`
  - `test_literals_are_exact_binary64_or_nothing`
  - `test_segments_are_the_math_elements_the_page_finds_at_their_places_in_the_text`
  - `test_text_the_page_does_not_render_as_math_is_no_segment_and_costs_no_engine`
  - `test_the_e_rule_reads_only_a_power_or_mathrm`
  - `test_the_left_hand_side_is_kept_as_the_books_substring_with_its_arguments`
  - `test_the_product_rule_never_resolves_a_name`
- [tests/test_rw5c_display_twins.py](../../../../../../tests/test_rw5c_display_twins.py) — direct import
  - `test_the_derived_words_are_the_corpus_s_from_the_book_s_left_hand_side`
- [tests/test_rw5c_katex_tree.py](../../../../../../tests/test_rw5c_katex_tree.py) — direct import
  - `test_a_block_past_the_work_cap_or_nested_past_the_stack_is_unreadable_and_the_engine_still_reads`
  - `test_a_blocks_segments_are_the_ones_the_page_has`
  - `test_a_changed_markdown_bundle_is_unreadable`
  - `test_a_katex_or_markdown_bump_moves_the_reader_version_and_needs_a_certification_bump`
  - `test_a_long_paragraph_of_a_book_fits_the_work_budget`
  - `test_a_segment_nested_past_every_cap_is_unreadable_not_a_crash`
  - `test_a_segment_over_the_work_cap_is_unreadable_and_the_engine_still_reads`
  - `test_display_mode_does_not_change_a_readable_tree`
  - `test_each_read_form_has_the_pages_mathml_and_means_it`
  - `test_the_left_hand_side_is_refused_when_alone_it_would_not_be_the_left_of_the_parse`
  - `test_the_left_hand_side_is_the_books_substring_and_the_left_of_the_parse`
  - `test_what_a_tree_shows_that_no_row_covers_is_refused_never_dropped`
  - `test_with_no_engine_a_block_has_no_segments_never_a_fallback`
- [tests/test_rw5c_labels.py](../../../../../../tests/test_rw5c_labels.py) — direct import
  - `test_a_generated_left_hand_side_is_whole_in_every_template_in_katexs_own_mathml`
- [tests/test_rw5c_plain_words.py](../../../../../../tests/test_rw5c_plain_words.py) — direct import
  - `test_generated_words_read_back_to_the_value_katex_s_own_mathml_means`
  - `test_the_fallback_is_written_whole_as_an_operand_with_no_brackets`
  - `test_what_has_no_faithful_words_says_so_in_closed_words`
- [tests/test_rw5c_recheck.py](../../../../../../tests/test_rw5c_recheck.py) — direct import
  - `test_a_certification_the_old_reader_stored_no_longer_delivers_checked`
  - `test_the_bulk_recheck_replaces_a_certification_the_old_reader_stored`

## Modification guidance

- Make changes here when the responsibility remains book math within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
