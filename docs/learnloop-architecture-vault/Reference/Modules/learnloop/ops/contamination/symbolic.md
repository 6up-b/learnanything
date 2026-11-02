---
title: "learnloop.ops.contamination.symbolic"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/contamination/symbolic.py"
source_paths:
  - "src/learnloop/ops/contamination/symbolic.py"
source_commit: "7cada0a7672374d91ea0f0910060446afe72d32c"
source_commit_timestamp: "2026-10-12T13:24:16-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ops.contamination"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.contamination.symbolic module"
  - "src/learnloop/ops/contamination/symbolic.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops-contamination"
---

# `learnloop.ops.contamination.symbolic`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.contamination.symbolic` exists within [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] to own the behavior summarized by its module contract: Symbolic answer check for the tutor and reader reveal detectors (R2).

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py) |
| Source lines | 315 |
| Owning package | [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `7cada0a7672374d91ea0f0910060446afe72d32c` |
| Commit timestamp | `2026-10-12T13:24:16-04:00` |

## Public API

- `class SymbolicResult` ([source](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 78)
  - `linked(self) -> bool` (line 89; public)
  - `decides(self) -> bool` (line 93; public) — A verifier verdict: a match whose link to the item is established.
  - `as_dict(self) -> dict[str, Any]` (line 98; public)
- `normalize_math(text: str) -> str` ([source](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 102) — Plain ASCII arithmetic from common LaTeX and Unicode notation.
- `distinctive(text: str) -> bool` ([source](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 134) — Distinctive enough that its presence is not incidental.
- `math_answer(expected: str | dict[str, Any] | None) -> str | None` ([source](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 146) — The expected answer as safe math text, or ``None`` when it is not math.
- `math_equations(text: str) -> list[list[str]]` ([source](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 166) — The sides of every maximal arithmetic run in ``text``, in reading order.
- `math_runs(text: str) -> list[str]` ([source](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 213) — Each distinct side of :func:`math_equations`, in reading order.
- `canonical(text: str) -> str` ([source](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 231) — Notation-free text for "as written" comparisons: no spacing, atom brackets or LaTeX.
- `symbolic_check(answer_text: str, expected: str | dict[str, Any] | None, *, prompt: str | None=None) -> SymbolicResult` ([source](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 261) — Does ``answer_text`` contain an expression equal to the expected answer?

### Module constants

- `SYMBOLIC_VERSION` ([src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 37)
- `MAX_CANDIDATES` ([src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 39)
- `MAX_LINKS` ([src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 41)
- `_ANSWER_KEYS` ([src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 42)
- `_FUNCTIONS` ([src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 43)
- `_UNICODE` ([src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 45)
- `_FUNCTION_CALL` ([src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 49)
- `_PI` ([src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 50)
- `_ATOM_BRACKETS` ([src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 52)
- `_VALUE` ([src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 54)
- `_FRAC` ([src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 55)
- `_SQRT` ([src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 56)
- `_BOXED` ([src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 57)
- `_BRACED_POWER` ([src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 58)
- `_LATEX_WORDS` ([src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 59)
- `_LINE_MARKERS` ([src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 64)
- `_ASSIGNMENT` ([src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 65)
- `_TOKEN` ([src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 66)

## Internal implementation anchors

- `_has_math(text: str) -> bool` ([source](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 120)
- `_is_expression(text: str) -> bool` ([source](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 128) — An operation, not a bare value: an item expression a match may link to.
- `_equal(candidate: str, target: str) -> tuple[bool, str | None]` ([source](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 219) — Equal, or a decimal rounding of ``target`` within its stated precision.
- `_item_expressions(prompt: str | None, target: str) -> set[str]` ([source](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 243) — The item's own expressions, as written; none when the prompt states its answer.
- `_answer_form(side: str, target: str) -> bool` ([source](../../../../../../../src/learnloop/ops/contamination/symbolic.py), line 254) — ``side`` (already equal to ``target``) is the answer itself, not an expression of it.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ops/contamination/detectors|learnloop.ops.contamination.detectors]] — imports `SymbolicResult`, `symbolic_check`; statically calls `symbolic_check`
- [[Reference/Modules/learnloop/ops/contamination/report|learnloop.ops.contamination.report]] — imports `SYMBOLIC_VERSION`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/answer_check|learnloop.attempts.answer_check]] — imports `answers_differ`, `answers_equal`, `safe_math_text`; calls `answers_differ`, `answers_equal`, `safe_math_text`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/ops/contamination/detectors|learnloop.ops.contamination.detectors]], [[Reference/Modules/learnloop/ops/contamination/report|learnloop.ops.contamination.report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_contamination_symbolic.py](../../../../../../../tests/test_contamination_symbolic.py) — direct import
  - `test_a_relation_that_does_not_hold_for_the_item_never_decides`
  - `test_an_earlier_occurrence_does_not_hide_a_later_worked_equation`
  - `test_an_occurrence_without_a_link_to_the_item_shortlists_but_never_decides`
  - `test_different_values_and_prose_answers_do_not_match`
  - `test_distinctiveness`
  - `test_equivalent_forms_match`
  - `test_function_answers_without_numerals_are_checked`
  - `test_function_runs_are_candidates`
  - `test_repeated_sides_are_compared_once`
  - `test_runs_split_on_prose_and_equals_and_normalize_latex`
  - `test_unsafe_text_never_reaches_sympy`
  - `test_working_the_items_own_expression_to_its_answer_decides`

## Modification guidance

- Make changes here when the responsibility remains symbolic within learnloop.ops.contamination; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/contamination/symbolic.py](../../../../../../../src/learnloop/ops/contamination/symbolic.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
