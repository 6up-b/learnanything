---
title: "learnloop.db.stores.approach_maps"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/approach_maps.py"
source_paths:
  - "src/learnloop/db/stores/approach_maps.py"
source_commit: "3c2b23fe64582f2a898e9227e4a0c6c2327d32f8"
source_commit_timestamp: "2026-10-18T02:36:39-04:00"
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
  - "learnloop.db.stores.approach_maps module"
  - "src/learnloop/db/stores/approach_maps.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.approach_maps`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.approach_maps` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Adaptive hints H1: ``approach_maps`` (migration 211).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/approach_maps.py](../../../../../../../src/learnloop/db/stores/approach_maps.py) |
| Source lines | 144 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `3c2b23fe64582f2a898e9227e4a0c6c2327d32f8` |
| Commit timestamp | `2026-10-18T02:36:39-04:00` |

## Public API

- `table_exists(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/approach_maps.py), line 28)
- `insert_map(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/approach_maps.py), line 47) — Insert one map version.
- `latest_map(connection: sqlite3.Connection, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/approach_maps.py), line 61) — The item's newest version, of any revision.
- `current_map(connection: sqlite3.Connection, practice_item_id: str, *, practice_item_hash: str, structure_hash: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/approach_maps.py), line 71) — The newest version built for this item revision and these item-side seeds.
- `next_version(connection: sqlite3.Connection, practice_item_id: str) -> tuple[int, str | None]` ([source](../../../../../../../src/learnloop/db/stores/approach_maps.py), line 84) — The version a new row of the item takes, and the row it supersedes.
- `family_template(connection: sqlite3.Connection, family_id: str, *, exclude_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/approach_maps.py), line 96) — The family's newest map of another item (a sibling's builder's template, §4.3).
- `map_row(connection: sqlite3.Connection, map_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/approach_maps.py), line 108)
- `map_exists(connection: sqlite3.Connection, map_id: str | None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/approach_maps.py), line 114) — Whether ``map_id`` names a stored map: the code check that stands in for a foreign key from ``help_assists.map_id`` (H0 friction note 1).
- `all_maps(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/approach_maps.py), line 123) — Every stored version, oldest first (the report).

### Module constants

- `TABLE` ([src/learnloop/db/stores/approach_maps.py](../../../../../../../src/learnloop/db/stores/approach_maps.py), line 17)
- `COLUMNS` ([src/learnloop/db/stores/approach_maps.py](../../../../../../../src/learnloop/db/stores/approach_maps.py), line 20)
- `_JSON_COLUMNS` ([src/learnloop/db/stores/approach_maps.py](../../../../../../../src/learnloop/db/stores/approach_maps.py), line 25)
- `_SELECT` ([src/learnloop/db/stores/approach_maps.py](../../../../../../../src/learnloop/db/stores/approach_maps.py), line 44)

### Explicit exports

`__all__` declares:

- `COLUMNS`
- `TABLE`
- `all_maps`
- `current_map`
- `family_template`
- `insert_map`
- `latest_map`
- `map_exists`
- `map_row`
- `next_version`
- `table_exists`

## Internal implementation anchors

- `_decode(row: sqlite3.Row | tuple[Any, ...] | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/approach_maps.py), line 34)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `module`; statically calls `current_map`, `insert_map`, `next_version`
- [[Reference/Modules/learnloop/hints/map_report|learnloop.hints.map_report]] — imports `module`; statically calls `all_maps`, `current_map`
- [[Reference/Modules/learnloop/hints/map_seeds|learnloop.hints.map_seeds]] — imports `module`; statically calls `family_template`
- [[Reference/Modules/learnloop/hints/outcome|learnloop.hints.outcome]] — imports `module`; statically calls `map_row`

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

Static participation evidence comes from [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]], [[Reference/Modules/learnloop/hints/map_report|learnloop.hints.map_report]], [[Reference/Modules/learnloop/hints/map_seeds|learnloop.hints.map_seeds]], [[Reference/Modules/learnloop/hints/outcome|learnloop.hints.outcome]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_approach_maps.py](../../../../../../../tests/test_approach_maps.py) — direct import
  - `test_a_revised_item_or_changed_seeds_gets_a_new_row_never_an_update`
  - `test_f4_a_seeded_but_unrouted_attempt_is_merged_later`
  - `test_help_assists_map_id_is_a_soft_reference_checked_in_code`
- [tests/test_approach_maps_schema.py](../../../../../../../tests/test_approach_maps_schema.py) — direct import
  - `test_the_store_refuses_unknown_columns`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/approach_maps.py](../../../../../../../src/learnloop/db/stores/approach_maps.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
