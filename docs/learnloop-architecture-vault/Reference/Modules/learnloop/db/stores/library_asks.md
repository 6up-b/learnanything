---
title: "learnloop.db.stores.library_asks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/library_asks.py"
source_paths:
  - "src/learnloop/db/stores/library_asks.py"
source_commit: "03f3ac0bcdfb57e27bea27443ec0cc5e1e446a0d"
source_commit_timestamp: "2026-10-20T17:54:52-04:00"
source_worktree_state: "clean"
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
  - "learnloop.db.stores.library_asks module"
  - "src/learnloop/db/stores/library_asks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.library_asks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.library_asks` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Reader workbench RW4a: ``library_asks`` (migration 209).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/library_asks.py](../../../../../../../src/learnloop/db/stores/library_asks.py) |
| Source lines | 145 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `03f3ac0bcdfb57e27bea27443ec0cc5e1e446a0d` |
| Commit timestamp | `2026-10-20T17:54:52-04:00` |

## Public API

- `insert_ask(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/library_asks.py), line 25)
- `update_ask(connection: sqlite3.Connection, ask_id: str, **columns: Any) -> None` ([source](../../../../../../../src/learnloop/db/stores/library_asks.py), line 39)
- `ask_row(connection: sqlite3.Connection, ask_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/library_asks.py), line 48)
- `kept_row(connection: sqlite3.Connection, ask_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/library_asks.py), line 60) — RW4d: the ask's caller, comparison and keep state.
- `kept_asks(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/library_asks.py), line 74) — RW4d: every ask whose comparison is kept now (``kept_at`` set), newest first.
- `asks_with_keeps(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/library_asks.py), line 83) — RW4d: every ask that has kept a comparison (``kept_json`` set), live or removed since (a removal keeps its snapshot in ``kept_json``'s history).
- `fork_ask(connection: sqlite3.Connection, ask_id: str, *, new_id: str, created_at: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/library_asks.py), line 92) — RW4d: a copy of an ask (its question, anchor, caller, manifests and notes) under a new id, with no comparison, keep or tutor exchange: a second comparison of a question whose first is kept gets its own row.
- `asks_for_comparison(connection: sqlite3.Connection, comparison_id: str, *, caller: str) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/library_asks.py), line 105) — RW4d: the asks of ``caller`` that refer to a comparison, oldest first.
- `asks_referencing_comparison(connection: sqlite3.Connection, comparison_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/library_asks.py), line 113) — RW4d fix round 5: every ask that refers to a comparison, oldest first: the asks showing it now (``comparison_id``) and every ask whose keep record names it (its live keep, a removal's snapshot, a contributor).
- `notes_for_ledger_ids(connection: sqlite3.Connection, ledger_ids: Sequence[str]) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/library_asks.py), line 125) — The validated organizer notes an earlier ask stored for these ledger rows.

### Module constants

- `TABLE` ([src/learnloop/db/stores/library_asks.py](../../../../../../../src/learnloop/db/stores/library_asks.py), line 19)
- `MUTABLE_COLUMNS` ([src/learnloop/db/stores/library_asks.py](../../../../../../../src/learnloop/db/stores/library_asks.py), line 21)

### Explicit exports

`__all__` declares:

- `MUTABLE_COLUMNS`
- `TABLE`
- `ask_row`
- `asks_for_comparison`
- `asks_with_keeps`
- `fork_ask`
- `insert_ask`
- `kept_asks`
- `kept_row`
- `notes_for_ledger_ids`
- `update_ask`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]] — imports `module`; statically calls `ask_row`, `asks_referencing_comparison`, `kept_row`
- [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]] — imports `module`; statically calls `ask_row`, `asks_for_comparison`, `asks_with_keeps`, `fork_ask`, `insert_ask`, `kept_asks`, `kept_row`, `update_ask`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `module`; statically calls `ask_row`, `insert_ask`, `notes_for_ledger_ids`, `update_ask`

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

Static participation evidence comes from [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]], [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]], [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_compare_sources_keep.py](../../../../../../../tests/test_compare_sources_keep.py) — imports consumer [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]]
- [tests/test_find_sources_intents.py](../../../../../../../tests/test_find_sources_intents.py) — imports consumer [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]]
- [tests/test_reread_safety.py](../../../../../../../tests/test_reread_safety.py) — imports consumer [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]]
- [tests/test_roles_concurrency.py](../../../../../../../tests/test_roles_concurrency.py) — imports consumer [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]]
- [tests/test_roles_switch_off_legacy_parity.py](../../../../../../../tests/test_roles_switch_off_legacy_parity.py) — imports consumer [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]]
- [tests/test_source_objects.py](../../../../../../../tests/test_source_objects.py) — imports consumer [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]]
- [tests/test_source_roles.py](../../../../../../../tests/test_source_roles.py) — imports consumer [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]]
- [tests/test_whole_comparison_provenance_surfaces.py](../../../../../../../tests/test_whole_comparison_provenance_surfaces.py) — imports consumer [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]]
- [tests/test_whole_comparison_reuse_provenance.py](../../../../../../../tests/test_whole_comparison_reuse_provenance.py) — imports consumer [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]]
- [tests/test_reader_ca4_table_by_point.py](../../../../../../../tests/test_reader_ca4_table_by_point.py) — imports consumer [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]]
- [tests/library_ask_fixtures.py](../../../../../../../tests/library_ask_fixtures.py) — imports consumer [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]]
- [tests/test_figure_offers.py](../../../../../../../tests/test_figure_offers.py) — imports consumer [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/library_asks.py](../../../../../../../src/learnloop/db/stores/library_asks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
