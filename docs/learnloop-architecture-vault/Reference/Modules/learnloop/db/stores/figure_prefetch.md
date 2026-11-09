---
title: "learnloop.db.stores.figure_prefetch"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/figure_prefetch.py"
source_paths:
  - "src/learnloop/db/stores/figure_prefetch.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.figure_prefetch module"
  - "src/learnloop/db/stores/figure_prefetch.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.figure_prefetch`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.figure_prefetch` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Reader RW5d P5: the prefetch ledgers' writes (migration 237; spec_reader_show_me_figures_v1 §13.2b).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/figure_prefetch.py](../../../../../../../src/learnloop/db/stores/figure_prefetch.py) |
| Source lines | 54 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `insert_decisions(connection: sqlite3.Connection, rows: Sequence[Mapping[str, Any]]) -> None` ([source](../../../../../../../src/learnloop/db/stores/figure_prefetch.py), line 21)
- `link_request(connection: sqlite3.Connection, decision_id: str, request_id: str, input_hash: str | None) -> None` ([source](../../../../../../../src/learnloop/db/stores/figure_prefetch.py), line 28) — The decision's request and the figure's input hash, set once each (a later call keeps the first).
- `close_decision(connection: sqlite3.Connection, decision_id: str, outcome: str, outcome_at: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/figure_prefetch.py), line 36)
- `insert_pause(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/figure_prefetch.py), line 43) — One pause, idempotently by its hit time; True when it was new.

### Module constants

- `DECISION_COLUMNS` ([src/learnloop/db/stores/figure_prefetch.py](../../../../../../../src/learnloop/db/stores/figure_prefetch.py), line 15)

### Explicit exports

`__all__` declares:

- `DECISION_COLUMNS`
- `close_decision`
- `insert_decisions`
- `insert_pause`
- `link_request`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `close_decision`, `insert_decisions`, `insert_pause`, `link_request`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_figures_prefetch.py](../../../../../../../tests/test_figures_prefetch.py) — imports consumer [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]]
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../../tests/test_figures_prefetch_review_fixes.py) — imports consumer [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]]
- [tests/test_followups_batch6_prefetch_decided_once.py](../../../../../../../tests/test_followups_batch6_prefetch_decided_once.py) — imports consumer [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]]
- [tests/test_followups_batch6_prefetch_next_section.py](../../../../../../../tests/test_followups_batch6_prefetch_next_section.py) — imports consumer [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]]
- [tests/test_followups_batch6_prefetch_plan_wait.py](../../../../../../../tests/test_followups_batch6_prefetch_plan_wait.py) — imports consumer [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]]
- [tests/test_followups_batch6_review_fixes.py](../../../../../../../tests/test_followups_batch6_review_fixes.py) — imports consumer [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]]
- [tests/test_followups_batch6_verify_fixes.py](../../../../../../../tests/test_followups_batch6_verify_fixes.py) — imports consumer [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]]
- [tests/test_followups_batch7_prefetch_capped_resume.py](../../../../../../../tests/test_followups_batch7_prefetch_capped_resume.py) — imports consumer [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]]
- [tests/test_followups_batch7_prefetch_link_served.py](../../../../../../../tests/test_followups_batch7_prefetch_link_served.py) — imports consumer [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/figure_prefetch.py](../../../../../../../src/learnloop/db/stores/figure_prefetch.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
