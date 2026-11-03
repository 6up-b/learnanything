---
title: "learnloop.figures.book_math"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/book_math.py"
source_paths:
  - "src/learnloop/figures/book_math.py"
source_commit: "workspace/uncommitted @ HEAD 6ea7184ca983997c6c504ebbda9e28c3d26e18c9"
source_commit_timestamp: "2026-11-02T21:29:11-05:00"
source_worktree_state: "modified"
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
| Source lines | 974 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 6ea7184ca983997c6c504ebbda9e28c3d26e18c9` |
| Commit timestamp | `2026-11-02T21:29:11-05:00` |

## Public API

- `class Unreadable(ValueError)` ([source](../../../../../../src/learnloop/figures/book_math.py), line 114) — A segment outside the table; ``reason`` is one key of :data:`REASONS`.
  - `__init__(self, reason: str) -> None` (line 117; internal)
- `class Segment` ([source](../../../../../../src/learnloop/figures/book_math.py), line 123) — One math segment of a block's text; ``start``/``end`` delimit ``latex``'s place in it.
- `class Relation` ([source](../../../../../../src/learnloop/figures/book_math.py), line 132) — A read equation.
- `segments(text: str, block_type: str='') -> list[Segment]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 154) — The math segments of a block's text in reading order (§5.2): ``$...$``, ``$$...$$``, ``\[...\]``, or the whole text of an equation block.
- `binary64_exact(text: str) -> bool` ([source](../../../../../../src/learnloop/figures/book_math.py), line 248) — Whether a decimal's exact value is a binary64 value: no made-up bound, no ``Decimal`` context (§6.1): 0, 1, 0.5, 0.375, never 0.3.
- `read_relation(latex: str) -> Relation` ([source](../../../../../../src/learnloop/figures/book_math.py), line 926) — One math segment read as one relation, or :class:`Unreadable`.

### Module constants

- `READER_VERSION` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 64)
- `REASONS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 67)
- `_GREEK` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 78)
- `_FUNCTIONS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 87)
- `_EXTREMES` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 88)
- `_REFUSED_COMMANDS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 90)
- `_IGNORED` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 100)
- `_RELATION_TOKENS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 101)
- `_OPENERS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 102)
- `_ENVIRONMENTS_MATRIX` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 103)
- `_CONDITION_OPS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 104)
- `_CASE_WORDS` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 106)
- `_NUMBER` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 107)
- `_COMMAND` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 108)
- `_TEXT_ARG` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 109)
- `EQUATION_BLOCK_TYPES` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 111)
- `_DELIMITED` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 150)
- `_LHS_APPLICATION` ([src/learnloop/figures/book_math.py](../../../../../../src/learnloop/figures/book_math.py), line 855)

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

- `class _Token` ([source](../../../../../../src/learnloop/figures/book_math.py), line 175)
- `_tokenize(source: str) -> list[_Token]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 182)
- `_dyadic_text(value: Fraction) -> str` ([source](../../../../../../src/learnloop/figures/book_math.py), line 231) — A dyadic rational's exact decimal, which reads back as the same fraction.
- `class _Reader` ([source](../../../../../../src/learnloop/figures/book_math.py), line 259)
- `_flip(op: str) -> str` ([source](../../../../../../src/learnloop/figures/book_math.py), line 843)
- `_compare(point: Fraction, op: str, value: Fraction) -> bool` ([source](../../../../../../src/learnloop/figures/book_math.py), line 847)
- `_split_relation(tokens: list[_Token]) -> tuple[int, int]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 858) — Where the one top-level ``=`` or ``:=`` is, as ``(lhs_end, rhs_start)`` token indices: a segment must hold exactly one.
- `_lhs_args(lhs: str) -> tuple[tuple[str, ...], dict[str, set[str]], dict[str, str]]` ([source](../../../../../../src/learnloop/figures/book_math.py), line 890) — The symbols of a ``name(args)`` left-hand side, with how the book spells them; empty for ``P(X = k)``, ``E[X]`` or a bare name.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `module`; statically calls `binary64_exact`, `read_relation`, `segments`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/figures/grammar|learnloop.figures.grammar]] — imports `module`; calls `Node`, `free_names`, `is_name`, `node_count`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `fractions`, `re`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_rw5c_book_math.py](../../../../../../tests/test_rw5c_book_math.py) — direct import
  - `test_a_form_tex_groups_differently_from_its_tokens_is_refused`
  - `test_caps_and_a_seeded_fuzz_never_raise_outside_the_reasons`
  - `test_cases_refusals`
  - `test_each_unreadable_construct_has_its_reason`
  - `test_every_reason_key_is_in_the_closed_list`
  - `test_literals_are_exact_binary64_or_nothing`
  - `test_segments_find_only_delimited_latex_or_an_equation_block`
  - `test_the_e_rule_reads_only_a_power_or_mathrm`
  - `test_the_left_hand_side_is_kept_as_the_books_substring_with_its_arguments`
  - `test_the_product_rule_never_resolves_a_name`
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
