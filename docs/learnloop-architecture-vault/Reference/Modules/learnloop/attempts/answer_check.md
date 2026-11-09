---
title: "learnloop.attempts.answer_check"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/answer_check.py"
source_paths:
  - "src/learnloop/attempts/answer_check.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.answer_check module"
  - "src/learnloop/attempts/answer_check.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.answer_check`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.answer_check` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: Deterministic answer checks shared by grading support and grader probes.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py) |
| Source lines | 712 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `safe_math_text(text: str) -> bool` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 68) — Whether ``text`` may be handed to SymPy (its parser evaluates Python).
- `class RelationCheck` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 391) — What :func:`check_relations` decided about every relation in a text.
- `check_relations(text: str) -> RelationCheck` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 472) — Decide every relation in ``text``; nothing is skipped.
- `asserted_conclusion(text: str) -> str | None` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 538) — The answer the LAST line asserts, parsed from that line's structure.
- `reference_final_answer(reference: str) -> str | None` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 560) — The final answer a worked-solution reference concludes with, or None.
- `reference_answers(reference: str) -> list[str]` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 594) — The reference as written, then its extracted numeric conclusion.
- `final_answer_check(learner_answer_md: str, expected_answer: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 658) — Deterministic: does the answer's concluding line equal the reference?

### Module constants

- `_WS` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 26)
- `_SAFE_MATH` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 30)
- `_SAFE_NAMES` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 31)
- `_NAME` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 34)
- `_SAFE_MAX_LENGTH` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 35)
- `_POWER_OPERAND` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 46)
- `_LEAD_WORDS` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 122)
- `_TRAIL_WORDS` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 131)
- `_LATEX_RELATIONS` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 132)
- `_LATEX_OPERATORS` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 139)
- `_LATEX_SPACES` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 140)
- `_UNICODE` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 141)
- `_LATEX_DELIMITERS` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 144)
- `_BOLD` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 146)
- `_LINE_MARKERS` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 147)
- `_TOKEN` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 148)
- `_MATH_KINDS` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 164)
- `_MAX_TERMS` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 165)
- `_MAX_EXPONENT` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 166)
- `_MAX_BITS` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 167)
- `_ANSWER_IS` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 532)
- `_CONCLUSION_LEAD` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 533)
- `_ASSIGNMENT` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 534)
- `_BOXED` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 535)
- `_SENTENCE_BREAK` ([src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py), line 557)

### Explicit exports

`__all__` declares:

- `Poly`
- `reference_answers`
- `reference_final_answer`
- `answers_differ`
- `answers_equal`
- `parse_answer`
- `asserted_answer`
- `RelationCheck`
- `asserted_conclusion`
- `check_relations`
- `final_answer_check`
- `safe_math_text`

## Internal implementation anchors

- `_normalized(value: str) -> str` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 38)
- `_bounded_powers(text: str) -> bool` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 49) — No power towers or computed exponents (SymPy would build huge integers).
- `_sympy_equal(left: str, right: str) -> bool | None` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 80) — True/False when SymPy decides equality of two safe texts, else None.
- `class _Unchecked(Exception)` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 115) — The text is not plain arithmetic the exact checker can decide.
- `class _Token` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 171)
- `_normalize_math_text(text: str) -> str` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 177)
- `_tokens(text: str) -> list[_Token]` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 184)
- `_guard(poly: Poly) -> Poly` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 221)
- `_const(value: Fraction) -> Poly` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 230)
- `_add(left: Poly, right: Poly, sign: int=1) -> Poly` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 234)
- `_mul(left: Poly, right: Poly) -> Poly` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 245)
- `_constant_of(poly: Poly) -> Fraction | None` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 263)
- `_power(base: Poly, exponent: Poly) -> Poly` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 271)
- `class _Parser` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 287) — Recursive descent over one side: + - * / ^, unary signs, brackets.
- `_decimals(tokens: list[_Token]) -> int` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 380)
- `_tolerance(places: int) -> Fraction` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 384) — Half a unit in the last stated decimal place (0 for exact values).
- `_runs(tokens: list[_Token]) -> list[tuple[int, int]]` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 399)
- `_bounded(tokens: list[_Token], runs: list[tuple[int, int]], has_relation: list[bool], position: int) -> bool` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 414) — Whether a relation run is cleanly delimited on both sides.
- `_compare(left: Poly, right: Poly, places: int) -> str` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 438) — ``holds``, ``false`` or ``unchecked`` for one adjacent pair of sides.
- `_check_chain(sides: list[list[_Token]], bindings: dict[str, Fraction]) -> str` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 447) — ``holds``/``defined``/``false``/``unchecked`` for one equation chain.
- `_parse_expression(text: str) -> tuple[Poly, int] | None` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 516) — An answer as an exact polynomial (and its stated decimals), else None.
- `_answers_equal(left: str, right: str) -> tuple[bool | None, str]` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 601) — (True/False/None, method): exact text, exact arithmetic, then SymPy.
- `_answers_differ(left: str, right: str) -> tuple[bool | None, str]` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 612) — (True when decidably different, False when equal, None undecidable).
- `_conclusion_candidates(asserted: str) -> list[str]` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 632) — The assertion, its single-letter assignment's value (``x = 3`` -> ``3``) and the numeric end of a consistent equality chain (``P(E) = 0.3`` -> ``0.3``).
- `_asserted_answer(text: str, declared: str) -> str | None` ([source](../../../../../../src/learnloop/attempts/answer_check.py), line 646) — The concluding line's assertion when it IS the declared answer.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] — imports `final_answer_check`; statically calls `final_answer_check`
- [[Reference/Modules/learnloop/diagnosis/grading_hardcases|learnloop.diagnosis.grading_hardcases]] — imports `final_answer_check`; statically calls `final_answer_check`
- [[Reference/Modules/learnloop/diagnosis/offline_review/probes|learnloop.diagnosis.offline_review.probes]] — imports `RelationCheck`, `answers_differ`, `answers_equal`, `asserted_answer`, `asserted_conclusion`, `check_relations`, `final_answer_check`, `reference_answers`, `safe_math_text`; statically calls `answers_differ`, `answers_equal`, `asserted_answer`, `asserted_conclusion`, `check_relations`, `reference_answers`
- [[Reference/Modules/learnloop/diagnosis/split/pfc_report|learnloop.diagnosis.split.pfc_report]] — imports `parse_answer`, `reference_final_answer`; statically calls `parse_answer`, `reference_final_answer`
- [[Reference/Modules/learnloop/hints/maps|learnloop.hints.maps]] — imports `answers_differ`, `answers_equal`, `parse_answer`, `reference_final_answer`, `safe_math_text`; statically calls `answers_differ`, `answers_equal`, `parse_answer`, `reference_final_answer`, `safe_math_text`
- [[Reference/Modules/learnloop/ops/contamination/symbolic|learnloop.ops.contamination.symbolic]] — imports `answers_differ`, `answers_equal`, `safe_math_text`; statically calls `answers_differ`, `answers_equal`, `safe_math_text`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `fractions`, `json`, `re`, `typing`
- Third party: `sympy`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]], [[Reference/Modules/learnloop/diagnosis/grading_hardcases|learnloop.diagnosis.grading_hardcases]], [[Reference/Modules/learnloop/diagnosis/offline_review/probes|learnloop.diagnosis.offline_review.probes]], [[Reference/Modules/learnloop/diagnosis/split/pfc_report|learnloop.diagnosis.split.pfc_report]], [[Reference/Modules/learnloop/hints/maps|learnloop.hints.maps]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_grading_support.py](../../../../../../tests/test_grading_support.py) — direct import
  - `test_worked_solution_references_check_against_their_numeric_conclusion`

## Modification guidance

- Change answer check policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/answer_check.py](../../../../../../src/learnloop/attempts/answer_check.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
