---
title: "learnloop.figures.source_check_harness"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/source_check_harness.py"
source_paths:
  - "src/learnloop/figures/source_check_harness.py"
source_commit: "9e12d91330e6fa42d51fd7c7319294c7015e803f"
source_commit_timestamp: "2026-11-02T20:08:53-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.figures"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.figures.source_check_harness module"
  - "src/learnloop/figures/source_check_harness.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.source_check_harness`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.source_check_harness` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Reader RW5c: the check's one fixed harness, run in the PF-b sandbox (spec §6.2-§6.5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/source_check_harness.py](../../../../../../src/learnloop/figures/source_check_harness.py) |
| Source lines | 813 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `9e12d91330e6fa42d51fd7c7319294c7015e803f` |
| Commit timestamp | `2026-11-02T20:08:53-05:00` |

## Public API

- `class Undecided(Exception)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 64)
  - `__init__(self, reason)` (line 65; internal)
- `class Different(Exception)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 70)
  - `__init__(self, witness)` (line 71; internal)
- `class Undefined(Exception)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 76) — A side has no value at this point.
- `class Unresolved(Exception)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 80) — The interval is too wide to say.
- `num_value(node)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 86)
- `constant_value(node)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 90) — A node built only from num, neg and + - * /: its exact value (§6.3 step 3, F8), or None.
- `canonical(node)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 116) — The same tree with + and * flattened and ordered, and each literal's exact value.
- `has_piecewise(node)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 138)
- `literal(node)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 148)
- `breakpoints(node, variable)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 156) — Where a side's branches change: every comparison is the variable against an exact literal, or the pair is ``parametric_breakpoint`` (P1, §6.3).
- `holds(condition, variable, point)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 179)
- `resolve(node, variable, point)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 194) — The branch-free AST that holds at ``point`` (exact).
- `to_sympy(node, symbols)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 210)
- `make_symbols(payload)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 263)
- `proved_true(kind, expression)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 277)
- `conditions(node, symbols)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 287) — Each node's exact condition on the branch-free AST: a point satisfies all of them exactly when the side has a real value there.
- `excluded_set(found, variable, domain)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 334) — Where a side has no value on ``domain``: the union of each negated condition's solution set.
- `comparable(found_set)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 348)
- `set_point(found_set)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 352) — An exact point of a non-empty set of the shapes :func:`comparable` allows.
- `domains_agree(a_ast, b_ast, symbols, variable, domain, point_text)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 371) — Step 3 on one interval: agree, or raise ``different`` with a witness or ``undecided`` (``domain``).
- `exact_interval(value)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 400)
- `raw_fraction(raw)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 404)
- `endpoints(interval)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 410)
- `monotone(function, interval)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 415) — An enclosure of an increasing function iv has no rule for, from correctly computed endpoints widened at the working precision.
- `contains_zero(interval)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 427)
- `exact_zero(interval)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 432)
- `evaluate(node, env)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 437) — The interval of a branch-chosen AST at an exact point, or Undefined / Unresolved.
- `power(base, exponent_node, env)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 514)
- `value_at(ast, variable, env)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 545) — ``ast`` at the exact point ``env``: an interval, ``None`` when it has no value.
- `fraction_text(value)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 556)
- `proof_of_difference(a_ast, b_ast, payload, deadline)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 560) — Two disjoint intervals at an exact point, or a point where only one side has a value (§6.3 step 5); None within the bound.
- `decide(figure, book, payload, symbols, deadline, *, control=False)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 589) — ``{"result": equal | different | undecided, ...}``.
- `defined_at(branch, symbols, symbol, value)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 654) — Whether a branch-free side has a value at the exact ``value``; parameter-dependent: undecided.
- `exact_shown(book, variable, env, kind, deadline)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 676) — The book's value at this exact point as displayed: its interval, widened by G22's parity bound, formats to one string (else rounding decides, None); no value is the renderer's dash.
- `display_agreement(book, element, deadline, per_check)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 706) — Every displayed sample's string equal to the exact value's, or the first that is not.
- `run_pair(pair, payload, symbols, deadline, per_check)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 734)
- `main()` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 743)

### Module constants

- `MARKER` ([src/learnloop/figures/source_check_harness.py](../../../../../../src/learnloop/figures/source_check_harness.py), line 36)
- `CONSTANTS` ([src/learnloop/figures/source_check_harness.py](../../../../../../src/learnloop/figures/source_check_harness.py), line 58)
- `TOTAL` ([src/learnloop/figures/source_check_harness.py](../../../../../../src/learnloop/figures/source_check_harness.py), line 59)
- `PARITY` ([src/learnloop/figures/source_check_harness.py](../../../../../../src/learnloop/figures/source_check_harness.py), line 61)

## Internal implementation anchors

- `class _Timeout(BaseException)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 39) — Past a bound (a BaseException: sympy catches Exception in places).
- `_alarm(_signum, _frame)` ([source](../../../../../../src/learnloop/figures/source_check_harness.py), line 43)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/figures/display_format|learnloop.figures.display_format]] — imports `format_value`; calls `format_value`

### Platform and third-party dependencies

- Standard library: `fractions`, `json`, `os`, `signal`, `sys`, `time`
- Third party: `display_format`, `mpmath`, `sympy`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No direct or one-hop consumer test was found by static import analysis.

> [!caution] Test gap signal
> Treat this as a navigation signal, not proof that behavior is untested: dynamic and higher-level coverage is outside this static map. Add focused coverage when changing isolated behavior here.

## Modification guidance

- Make changes here when the responsibility remains source check harness within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/source_check_harness.py](../../../../../../src/learnloop/figures/source_check_harness.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
