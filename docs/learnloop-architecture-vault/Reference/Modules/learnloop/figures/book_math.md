---
title: "learnloop.figures.book_math"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/book_math.py"
source_paths:
  - "src/learnloop/figures/book_math.py"
source_commit: "f68fbfe1b5e4292fde7b79d509762d1e935df8d1"
source_commit_timestamp: "2026-11-02T22:41:07-05:00"
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
| Source lines | 1040 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `f68fbfe1b5e4292fde7b79d509762d1e935df8d1` |
| Commit timestamp | `2026-11-02T22:41:07-05:00` |

## Public API

- `class Unreadable(ValueError)` ([source](../../../../../../src/learnloop/figures/book_math.py), line 114) — A segment outside the table; ``reason`` is one key of :data:`REASONS`.
  - `__init__(self, reason: str) -> None` (line 117; internal)
- `class Segment` ([source](../../../../../../src/learnloop/figures/book_math.py), line 123) — One math segment of a block's text; ``start``/``end`` delimit ``latex``'s place in it; ``display`` is how the page parses it (``$$`` and ``\[`` against ``$``).
- `class Relation` ([source](../../../../../../src/learnloop/figures/book_math.py), line 134) — A read equation.
- `segments(text: str, block_type: str='') -> list[Segment]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 163) — The math segments of a block's text in reading order (§5.2), as the page's own markdown finds them: ``$...$``, ``$$...$$``, ``\[...\]``, or the whole text of an equation block.
- `binary64_exact(text: str) -> bool` ([source](../../../../../../src/learnloop/figures/book_math.py), line 418) — Whether a decimal's exact value is a binary64 value: no made-up bound, no ``Decimal`` context (§6.1): 0, 1, 0.5, 0.375, never 0.3.
- `read_relation(latex: str, *, display: bool=False, trees: KT.Trees | None=None) -> Relation` ([source](../../../../../../src/learnloop/figures/book_math.py), line 983) — One math segment read as one relation, or :class:`Unreadable`.

### Module constants

- `READER_VERSION` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 58)
- `REASONS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 61)
- `_GREEK` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 73)
- `_FUNCTIONS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 82)
- `_EXTREMES` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 83)
- `_LABELS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 86)
- `_OPENERS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 96)
- `_CONDITION_OPS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 97)
- `_CASE_WORDS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 99)
- `_NUMBER` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 100)
- `_KERNS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 102)
- `_SPACES` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 103)
- `_MACRO_DEFINITION` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 105)
- `_LABEL_NODES` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 108)
- `EQUATION_BLOCK_TYPES` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 111)
- `_DELIMITED` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 151)
- `_CODE` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 154)
- `_PARAGRAPH` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 155)
- `_FENCED` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 159)
- `_LINE_END` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 160)

### Explicit exports

`__all__` declares:

- `READER_VERSION`
- `REASONS`
- `Relation`
- `Segment`
- `Unreadable`
- `binary64_exact`
- `read_relation`
- `segments`

## Internal implementation anchors

- `class _Item` ([source](../../../../../../src/learnloop/figures/book_math.py), line 197) — One thing in reading order.
- `_body(node: Tree) -> Sequence[Tree]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 211)
- `_word(nodes: Sequence[Tree]) -> str | None` ([source](../../../../../../src/learnloop/figures/book_math.py), line 215) — The letters of ``\mathrm{...}`` or ``\operatorname{...}``, if letters are all it holds.
- `_is_table_space(node: Tree) -> bool` ([source](../../../../../../src/learnloop/figures/book_math.py), line 224)
- `_refuse_symbol(text: str) -> Unreadable` ([source](../../../../../../src/learnloop/figures/book_math.py), line 229)
- `_items(nodes: Sequence[Tree]) -> list[_Item]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 233)
- `_base_items(base: Tree) -> list[_Item]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 271)
- `_atom_item(base: Tree, text: str) -> _Item` ([source](../../../../../../src/learnloop/figures/book_math.py), line 329)
- `_leftright_items(base: Tree) -> list[_Item]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 350)
- `_font_item(base: Tree) -> _Item` ([source](../../../../../../src/learnloop/figures/book_math.py), line 368)
- `_starts_with_d(node: Tree) -> bool` ([source](../../../../../../src/learnloop/figures/book_math.py), line 384) — Whether a fraction's side begins with a differential's ``d``.
- `_dyadic_text(value: Fraction) -> str` ([source](../../../../../../src/learnloop/figures/book_math.py), line 401) — A dyadic rational's exact decimal, which reads back as the same fraction.
- `class _Reader` ([source](../../../../../../src/learnloop/figures/book_math.py), line 432)
- `_numeric_sides(item: _Item) -> tuple[Fraction | None, Fraction | None]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 798) — A fraction's two sides as numbers, each when it is one numeral.
- `_cell(cell: Tree) -> Sequence[Tree]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 814) — A cell of an array: KaTeX wraps its contents in a style and a group.
- `_text_words(node: Tree) -> str` ([source](../../../../../../src/learnloop/figures/book_math.py), line 823) — A ``\text{...}``'s words: its characters as KaTeX lists them.
- `_without_end_punctuation(nodes: Sequence[Tree]) -> Sequence[Tree]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 837) — Without the ``,`` or ``.`` a sentence or a row ends on.
- `_flip(op: str) -> str` ([source](../../../../../../src/learnloop/figures/book_math.py), line 845)
- `_compare(point: Fraction, op: str, value: Fraction) -> bool` ([source](../../../../../../src/learnloop/figures/book_math.py), line 849)
- `_is_atom(node: Tree, family: str, text: str | None=None) -> bool` ([source](../../../../../../src/learnloop/figures/book_math.py), line 857)
- `_split_relation(nodes: Sequence[Tree]) -> tuple[int, int]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 861) — Where the one top-level ``=`` or ``:=`` of KaTeX's list is, as ``(lhs_end, rhs_start)`` indices: a segment must hold exactly one.
- `_lhs_args(nodes: Sequence[Tree]) -> tuple[tuple[str, ...], dict[str, set[str]], dict[str, str]]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 894) — The symbols of a ``name(args)`` left-hand side, with how the book spells them; empty for ``P(X = k)``, ``E[X]`` or a bare name.
- `_walk(value: Any) -> Iterator[Tree]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 938) — Every node under ``value``, whatever field holds it.
- `_without_places(value: Any) -> Any` ([source](../../../../../../src/learnloop/figures/book_math.py), line 951)
- `_parse(trees: KT.Trees, source: str, display: bool) -> list[Tree]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 959)
- `_left_hand_side(source: str, tree: Sequence[Tree], lhs_end: int, *, trees: KT.Trees, display: bool) -> str` ([source](../../../../../../src/learnloop/figures/book_math.py), line 967) — The book's own substring, kept only when KaTeX reads it alone as the left of this parse.
- `_translate(source: str, tree: Sequence[Tree], *, trees: KT.Trees, display: bool) -> Relation` ([source](../../../../../../src/learnloop/figures/book_math.py), line 1006)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

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

Static participation evidence comes from [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_rw5c_book_math.py](../../../../../../tests/test_rw5c_book_math.py) — direct import
  - `test_caps_and_a_seeded_fuzz_never_raise_outside_the_reasons`
  - `test_cases_refusals`
  - `test_each_unreadable_construct_has_its_reason`
  - `test_every_reason_key_is_in_the_closed_list`
  - `test_literals_are_exact_binary64_or_nothing`
  - `test_segments_find_only_delimited_latex_or_an_equation_block`
  - `test_the_e_rule_reads_only_a_power_or_mathrm`
  - `test_the_left_hand_side_is_kept_as_the_books_substring_with_its_arguments`
  - `test_the_product_rule_never_resolves_a_name`
- [tests/test_rw5c_katex_tree.py](../../../../../../tests/test_rw5c_katex_tree.py) — direct import
  - `test_a_blocks_segments_are_the_ones_the_page_has`
  - `test_a_katex_bump_moves_the_reader_version_and_needs_a_certification_bump`
  - `test_a_segment_nested_past_every_cap_is_unreadable_not_a_crash`
  - `test_a_segment_over_the_work_cap_is_unreadable_and_the_engine_still_reads`
  - `test_display_mode_does_not_change_a_readable_tree`
  - `test_each_read_form_has_the_pages_mathml_and_means_it`
  - `test_the_left_hand_side_is_refused_when_alone_it_would_not_be_the_left_of_the_parse`
  - `test_the_left_hand_side_is_the_books_substring_and_the_left_of_the_parse`
  - `test_what_a_tree_shows_that_no_row_covers_is_refused_never_dropped`
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
