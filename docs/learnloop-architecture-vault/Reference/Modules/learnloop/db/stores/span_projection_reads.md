---
title: "learnloop.db.stores.span_projection_reads"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/span_projection_reads.py"
source_paths:
  - "src/learnloop/db/stores/span_projection_reads.py"
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
  - "learnloop.db.stores.span_projection_reads module"
  - "src/learnloop/db/stores/span_projection_reads.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.span_projection_reads`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.span_projection_reads` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Reads of the workbench's passage projections and exchange context (migration 262).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/span_projection_reads.py](../../../../../../../src/learnloop/db/stores/span_projection_reads.py) |
| Source lines | 61 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `rows_for(connection: sqlite3.Connection, table: str, owner_ids: Iterable[str] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/span_projection_reads.py), line 21)
- `rows_on_readings(connection: sqlite3.Connection, table: str, extraction_ids: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/span_projection_reads.py), line 34)
- `exchange_contexts(connection: sqlite3.Connection, question_event_ids: Iterable[str]) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/span_projection_reads.py), line 42)
- `exchange_context_exists(connection: sqlite3.Connection, question_event_id: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/span_projection_reads.py), line 56)

### Module constants

- `_TABLES` ([src/learnloop/db/stores/span_projection_reads.py](../../../../../../../src/learnloop/db/stores/span_projection_reads.py), line 12)

### Explicit exports

`__all__` declares:

- `exchange_context_exists`
- `exchange_contexts`
- `rows_for`
- `rows_on_readings`

## Internal implementation anchors

- `_rows(connection: sqlite3.Connection, sql: str, params: Iterable[Any]=()) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/span_projection_reads.py), line 15)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/companion/history|learnloop.companion.history]] — imports `module`; statically calls `exchange_contexts`, `rows_for`
- [[Reference/Modules/learnloop/companion/search|learnloop.companion.search]] — imports `module`; statically calls `rows_for`
- [[Reference/Modules/learnloop/passage_union/union|learnloop.passage_union.union]] — imports `module`; statically calls `rows_on_readings`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/companion/history|learnloop.companion.history]], [[Reference/Modules/learnloop/companion/search|learnloop.companion.search]], [[Reference/Modules/learnloop/passage_union/union|learnloop.passage_union.union]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rd0_spans.py](../../../../../../../tests/test_reader_rd0_spans.py) — direct import
  - `test_a_note_link_hidden_before_the_gap_was_read_places_nothing`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/span_projection_reads.py](../../../../../../../src/learnloop/db/stores/span_projection_reads.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
