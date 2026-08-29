---
title: "learnloop.db.table_roles"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/table_roles.py"
source_paths:
  - "src/learnloop/db/table_roles.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.db"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.table_roles module"
  - "src/learnloop/db/table_roles.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db"
---

# `learnloop.db.table_roles`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/_package|learnloop.db]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.table_roles` exists within [[Reference/Modules/learnloop/db/_package|learnloop.db]] to own the behavior summarized by its module contract: Persistent-table roles for migration-head ``state.sqlite``.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/table_roles.py](../../../../../../src/learnloop/db/table_roles.py) |
| Source lines | 404 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class TableRole(str, Enum)` ([source](../../../../../../src/learnloop/db/table_roles.py), line 27) — The rebuild policy for one persistent user table.
- `class TableRoleMismatch` ([source](../../../../../../src/learnloop/db/table_roles.py), line 333) — The two directions in which a schema and registry can disagree.
  - `is_complete(self) -> bool` (line 340; public)
- `role_for_table(table_name: str) -> TableRole` ([source](../../../../../../src/learnloop/db/table_roles.py), line 344) — Return ``table_name``'s declared role, raising ``KeyError`` if absent.
- `tables_for_role(role: TableRole) -> frozenset[str]` ([source](../../../../../../src/learnloop/db/table_roles.py), line 350) — Return every table assigned to ``role``.
- `user_table_names(connection: sqlite3.Connection) -> frozenset[str]` ([source](../../../../../../src/learnloop/db/table_roles.py), line 356) — Read the non-SQLite table names from an open database connection.
- `registry_mismatch(table_names: Iterable[str]) -> TableRoleMismatch` ([source](../../../../../../src/learnloop/db/table_roles.py), line 370) — Compare an observed schema to the declarative registry.
- `assert_complete_registry(table_names: Iterable[str]) -> None` ([source](../../../../../../src/learnloop/db/table_roles.py), line 381) — Raise ``ValueError`` unless observed and registered tables match exactly.

### Module constants

- `_TABLE_ROLE_ITEMS` ([src/learnloop/db/table_roles.py](../../../../../../src/learnloop/db/table_roles.py), line 40)
- `TABLE_ROLES` ([src/learnloop/db/table_roles.py](../../../../../../src/learnloop/db/table_roles.py), line 329)

### Explicit exports

`__all__` declares:

- `TABLE_ROLES`
- `TableRole`
- `TableRoleMismatch`
- `assert_complete_registry`
- `registry_mismatch`
- `role_for_table`
- `tables_for_role`
- `user_table_names`

## Internal implementation anchors

- `_build_registry(items: tuple[tuple[str, TableRole], ...]) -> dict[str, TableRole]` ([source](../../../../../../src/learnloop/db/table_roles.py), line 315)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `TableRole`, `tables_for_role`; statically calls `tables_for_role`
- [[Reference/Modules/learnloop/goals/goal_series_store|learnloop.goals.goal_series_store]] — imports `role_for_table`; statically calls `role_for_table`
- [[Reference/Modules/learnloop/ops/debug_time_store|learnloop.ops.debug_time_store]] — imports `role_for_table`; statically calls `role_for_table`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `TableRole`, `tables_for_role`; statically calls `tables_for_role`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `enum`, `sqlite3`, `types`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/goals/goal_series_store|learnloop.goals.goal_series_store]], [[Reference/Modules/learnloop/ops/debug_time_store|learnloop.ops.debug_time_store]], [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_rebuild_orchestrator.py](../../../../../../tests/test_rebuild_orchestrator.py) — direct import
  - `test_golden_projection_survives_one_umbrella_rebuild_exactly_and_stale_rows_clear`
  - `test_replayer_registry_owns_each_derived_table_exactly_once`
  - `test_same_version_full_rebuild_is_semantically_idempotent_on_golden_fixture`
- [tests/test_table_roles.py](../../../../../../tests/test_table_roles.py) — direct import
  - `test_migration_head_user_tables_match_role_registry_exactly`
  - `test_mixed_authoritative_artifacts_are_not_claimed_as_rebuildable`
  - `test_public_role_helpers_partition_registry`
  - `test_synthetic_unclassified_table_fails_registry_check`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/table_roles.py](../../../../../../src/learnloop/db/table_roles.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
