---
title: "learnloop.router.suggestion_report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router/suggestion_report.py"
source_paths:
  - "src/learnloop/router/suggestion_report.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router.suggestion_report module"
  - "src/learnloop/router/suggestion_report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router"
---

# `learnloop.router.suggestion_report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router/_package|learnloop.router]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router.suggestion_report` exists within [[Reference/Modules/learnloop/router/_package|learnloop.router]] to own the behavior summarized by its module contract: Teacher TE1b's lesson suggestions by randomized arm (``learnloop router report``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router/suggestion_report.py](../../../../../../src/learnloop/router/suggestion_report.py) |
| Source lines | 163 |
| Owning package | [[Reference/Modules/learnloop/router/_package|learnloop.router]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `itt_split(decisions: Iterable[Mapping[str, Any]], responses: Iterable[Mapping[str, Any]], releases: Iterable[Mapping[str, Any]], lessons: Mapping[str, Mapping[str, Any]], outcomes: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/suggestion_report.py), line 54) — The split (module docstring).
- `lines(split: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/router/suggestion_report.py), line 127) — The split in plain words (the text report).

### Module constants

- `ARMS` ([src/learnloop/router/suggestion_report.py](../../../../../../src/learnloop/router/suggestion_report.py), line 32)
- `COMPLETED_REASON` ([src/learnloop/router/suggestion_report.py](../../../../../../src/learnloop/router/suggestion_report.py), line 34)
- `TAKEN` ([src/learnloop/router/suggestion_report.py](../../../../../../src/learnloop/router/suggestion_report.py), line 35)

### Explicit exports

`__all__` declares:

- `ARMS`
- `COMPLETED_REASON`
- `itt_split`
- `lines`

## Internal implementation anchors

- `_weight(detail: Mapping[str, Any]) -> float | None` ([source](../../../../../../src/learnloop/router/suggestion_report.py), line 38)
- `_hajek(pairs: Iterable[tuple[float, float]]) -> float | None` ([source](../../../../../../src/learnloop/router/suggestion_report.py), line 46)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `itt_split`, `lines`; statically calls `itt_split`, `lines`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followups_batch6_review_fixes.py](../../../../../../tests/test_followups_batch6_review_fixes.py) — direct import
  - `test_f3_differential_outcome_availability_is_reported_never_called_itt`
- [tests/test_followups_batch6_router_report.py](../../../../../../tests/test_followups_batch6_router_report.py) — direct import
  - `test_an_empty_ledger_reports_zeros_and_no_difference`
  - `test_router_report_prints_the_split_from_the_ledgers_read_only`
  - `test_the_split_weights_each_arm_by_its_logged_propensity`

## Modification guidance

- Make changes here when the responsibility remains suggestion report within learnloop.router; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router/suggestion_report.py](../../../../../../src/learnloop/router/suggestion_report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
