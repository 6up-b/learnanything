---
title: "learnloop.attempts.given_points"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/given_points.py"
source_paths:
  - "src/learnloop/attempts/given_points.py"
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
  - "learnloop.attempts.given_points module"
  - "src/learnloop/attempts/given_points.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.given_points`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.given_points` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: The rows the attempt door records for a live grade that gives criterion points and no evidence rows.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/given_points.py](../../../../../../src/learnloop/attempts/given_points.py) |
| Source lines | 49 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `given_points_as_evidence(attempt: Any, now_iso: str) -> Any` ([source](../../../../../../src/learnloop/attempts/given_points.py), line 22) — A live grade that reaches the door with criterion points and no evidence rows gets the given points recorded as its rows.

### Module constants

- `GIVEN_POINTS_LOCAL_GRADER_ID` ([src/learnloop/attempts/given_points.py](../../../../../../src/learnloop/attempts/given_points.py), line 11)
- `GIVEN_POINTS_GRADER_TIER` ([src/learnloop/attempts/given_points.py](../../../../../../src/learnloop/attempts/given_points.py), line 12)

## Internal implementation anchors

- `_part(value: Any) -> str` ([source](../../../../../../src/learnloop/attempts/given_points.py), line 15) — One part of a derived row id, escaped so the parts never run together (``%`` and ``:`` percent-encoded): an id with neither keeps its form, and ``(A:B, C)`` and ``(A, B:C)`` name different rows.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `given_points_as_evidence`; statically calls `given_points_as_evidence`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_one_instant_per_grade.py](../../../../../../tests/test_one_instant_per_grade.py) — direct import
  - `test_given_points_row_ids_never_collide_across_attempt_and_criterion_ids`

## Modification guidance

- Change given points policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/given_points.py](../../../../../../src/learnloop/attempts/given_points.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
