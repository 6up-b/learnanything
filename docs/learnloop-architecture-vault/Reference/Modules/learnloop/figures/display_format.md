---
title: "learnloop.figures.display_format"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/display_format.py"
source_paths:
  - "src/learnloop/figures/display_format.py"
source_commit: "25bf90ec59bf82588cc4241933283425f9091c66"
source_commit_timestamp: "2026-11-02T19:27:15-05:00"
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
  - "learnloop.figures.display_format module"
  - "src/learnloop/figures/display_format.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.display_format`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.display_format` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Reader RW5c: the Python twins of how a figure's numbers are displayed (spec §6.4, §7.2; G22).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/display_format.py](../../../../../../src/learnloop/figures/display_format.py) |
| Source lines | 126 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `25bf90ec59bf82588cc4241933283425f9091c66` |
| Commit timestamp | `2026-11-02T19:27:15-05:00` |

## Public API

- `js_string(value)` ([source](../../../../../../src/learnloop/figures/display_format.py), line 61) — JavaScript's ``String(value)`` for a finite double.
- `format_value(value, kind='number')` ([source](../../../../../../src/learnloop/figures/display_format.py), line 92) — ``formatValue``: a double (or an exact Fraction) as the figure displays it.

### Module constants

- `_EXPONENT_LOW` ([src/learnloop/figures/display_format.py](../../../../../../src/learnloop/figures/display_format.py), line 18)
- `_EXPONENT_HIGH` ([src/learnloop/figures/display_format.py](../../../../../../src/learnloop/figures/display_format.py), line 19)
- `NO_VALUE` ([src/learnloop/figures/display_format.py](../../../../../../src/learnloop/figures/display_format.py), line 20)

## Internal implementation anchors

- `_floor_log10(value)` ([source](../../../../../../src/learnloop/figures/display_format.py), line 23) — floor(log10(value)) of a positive Fraction, exactly.
- `_rounded(value, digits)` ([source](../../../../../../src/learnloop/figures/display_format.py), line 34) — ``(n, e)`` with ``n`` the ``digits`` significant digits of a positive Fraction, ties to the larger ``n`` (ECMAScript's toPrecision and toExponential), and ``e`` its decimal exponent.
- `_plain(whole, exponent, digits)` ([source](../../../../../../src/learnloop/figures/display_format.py), line 48) — ``String(Number(...))`` of ``whole`` x 10**(exponent - digits + 1), within the range where JavaScript writes no exponent: trailing zeros dropped.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/elements|learnloop.figures.elements]] — imports `js_string`
- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `module`; statically calls `format_value`, `js_string`
- [[Reference/Modules/learnloop/figures/source_check_harness|learnloop.figures.source_check_harness]] — imports `format_value`; statically calls `format_value`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `fractions`, `math`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/elements|learnloop.figures.elements]], [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]], [[Reference/Modules/learnloop/figures/source_check_harness|learnloop.figures.source_check_harness]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_rw5c_display_twins.py](../../../../../../tests/test_rw5c_display_twins.py) — direct import
  - `test_no_value_is_a_dash`
  - `test_the_twins_agree_with_javascript`
- [tests/test_rw5c_labels.py](../../../../../../tests/test_rw5c_labels.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains display format within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/display_format.py](../../../../../../src/learnloop/figures/display_format.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
