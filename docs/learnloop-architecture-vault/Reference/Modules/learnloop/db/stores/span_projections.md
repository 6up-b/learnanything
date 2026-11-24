---
title: "learnloop.db.stores.span_projections"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/span_projections.py"
source_paths:
  - "src/learnloop/db/stores/span_projections.py"
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
  - "learnloop.db.stores.span_projections module"
  - "src/learnloop/db/stores/span_projections.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.span_projections`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.span_projections` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: The only SQL writer for the workbench's passage projections and exchange context (migration 262).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/span_projections.py](../../../../../../../src/learnloop/db/stores/span_projections.py) |
| Source lines | 70 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `replace_rows(connection: sqlite3.Connection, table: str, owner_id: str, rows: Sequence[Mapping[str, Any]]) -> int` ([source](../../../../../../../src/learnloop/db/stores/span_projections.py), line 20) — Replace one source's projected rows (a source projected twice keeps one copy of each row).
- `insert_exchange_context(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/span_projections.py), line 36) — Record where one exchange was asked; a second record of the same exchange writes nothing (the table refuses a replacing insert, so it is checked first).
- `record_initialization(connection: sqlite3.Connection, *, projection: str, sources: int, rows: int, initialized_at: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/span_projections.py), line 56) — The receipt of one projection's one-time initialization (migration 264; append-only).
- `initialized(connection: sqlite3.Connection, projection: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/span_projections.py), line 65)

### Module constants

- `SPAN_COLUMNS` ([src/learnloop/db/stores/span_projections.py](../../../../../../../src/learnloop/db/stores/span_projections.py), line 16)
- `_TABLES` ([src/learnloop/db/stores/span_projections.py](../../../../../../../src/learnloop/db/stores/span_projections.py), line 17)

### Explicit exports

`__all__` declares:

- `SPAN_COLUMNS`
- `initialized`
- `insert_exchange_context`
- `record_initialization`
- `replace_rows`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/companion/history|learnloop.companion.history]] — imports `module`; statically calls `insert_exchange_context`
- [[Reference/Modules/learnloop/substrate/passage_spans|learnloop.substrate.passage_spans]] — imports `module`; statically calls `initialized`, `record_initialization`, `replace_rows`

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

Static participation evidence comes from [[Reference/Modules/learnloop/companion/history|learnloop.companion.history]], [[Reference/Modules/learnloop/substrate/passage_spans|learnloop.substrate.passage_spans]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_reader_rd0_reads.py](../../../../../../../tests/test_reader_rd0_reads.py) — imports consumer [[Reference/Modules/learnloop/companion/history|learnloop.companion.history]]
- [tests/test_menu_promoted_rows.py](../../../../../../../tests/test_menu_promoted_rows.py) — imports consumer [[Reference/Modules/learnloop/substrate/passage_spans|learnloop.substrate.passage_spans]]
- [tests/test_reader_rd0_guards_migration.py](../../../../../../../tests/test_reader_rd0_guards_migration.py) — imports consumer [[Reference/Modules/learnloop/substrate/passage_spans|learnloop.substrate.passage_spans]]
- [tests/test_reader_rd0_spans.py](../../../../../../../tests/test_reader_rd0_spans.py) — imports consumer [[Reference/Modules/learnloop/substrate/passage_spans|learnloop.substrate.passage_spans]]
- [tests/test_reader_rd3a_companion_ask.py](../../../../../../../tests/test_reader_rd3a_companion_ask.py) — imports consumer [[Reference/Modules/learnloop/substrate/passage_spans|learnloop.substrate.passage_spans]]
- [tests/test_reader_rd4_emission.py](../../../../../../../tests/test_reader_rd4_emission.py) — imports consumer [[Reference/Modules/learnloop/substrate/passage_spans|learnloop.substrate.passage_spans]]
- [tests/test_reader_rd8a_transcribe.py](../../../../../../../tests/test_reader_rd8a_transcribe.py) — imports consumer [[Reference/Modules/learnloop/substrate/passage_spans|learnloop.substrate.passage_spans]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/span_projections.py](../../../../../../../src/learnloop/db/stores/span_projections.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
