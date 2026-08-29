---
title: "learnloop_sidecar.handlers.sqlite_admin"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/sqlite_admin.py"
source_paths:
  - "src/learnloop_sidecar/handlers/sqlite_admin.py"
source_commit: "b19e81d9993c28e995049da1aa16f8d316d56d68"
source_commit_timestamp: "2026-07-13T13:41:22-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.sqlite_admin module"
  - "src/learnloop_sidecar/handlers/sqlite_admin.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.sqlite_admin`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps sqlite admin behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]]. Its public surface centers on `DbPathInput`, `sqlite_tables`, `TablePageInput`, `sqlite_table`, `ExecInput`, `sqlite_exec`, `UpdateCellInput`, `sqlite_update_cell` and 4 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/sqlite_admin.py](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py) |
| Source lines | 293 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `b19e81d9993c28e995049da1aa16f8d316d56d68` |
| Commit timestamp | `2026-07-13T13:41:22-04:00` |

## Public API

- `class DbPathInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 89)
- `sqlite_tables(ctx: SidecarContext, params: DbPathInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 94) — List the user tables/views in a vault sqlite database with row counts.
- `class TablePageInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 106)
- `sqlite_table(ctx: SidecarContext, params: TablePageInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 114) — A page of rows for one table, with column metadata.
- `class ExecInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 169)
- `sqlite_exec(ctx: SidecarContext, params: ExecInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 175) — Run a single arbitrary SQL statement (the console).
- `class UpdateCellInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 209)
- `sqlite_update_cell(ctx: SidecarContext, params: UpdateCellInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 218) — Update one cell, identified by table + rowid + column.
- `class InsertRowInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 241)
- `sqlite_insert_row(ctx: SidecarContext, params: InsertRowInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 247) — Insert a blank row and return its new rowid for in-place cell editing.
- `class DeleteRowInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 274)
- `sqlite_delete_row(ctx: SidecarContext, params: DeleteRowInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 281) — Delete one row, identified by table + rowid.

### Module constants

- `_SQLITE_SUFFIXES` ([src/learnloop_sidecar/handlers/sqlite_admin.py](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 19)
- `_MAX_EXEC_ROWS` ([src/learnloop_sidecar/handlers/sqlite_admin.py](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 20)
- `_DEFAULT_PAGE` ([src/learnloop_sidecar/handlers/sqlite_admin.py](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 21)
- `_MAX_PAGE` ([src/learnloop_sidecar/handlers/sqlite_admin.py](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 22)

## Internal implementation anchors

- `_resolve_db(ctx: SidecarContext, path: str) -> Path` ([source](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 25)
- `_connect(target: Path) -> sqlite3.Connection` ([source](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 36)
- `_qid(identifier: str) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 42) — Quote an identifier (table/column) so a validated name is safe to interpolate.
- `_user_tables(connection: sqlite3.Connection) -> list[str]` ([source](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 48)
- `_require_table(connection: sqlite3.Connection, table: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 56)
- `_cell(value: Any) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 61) — Render a column value as something JSON-native; blobs become a placeholder.
- `_coerce(value: Any, declared_type: str | None) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py), line 69) — Best-effort coercion of a string edit to the column's declared affinity.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `pathlib`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_desktop_rpc_contract.py](../../../../../../tests/test_desktop_rpc_contract.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_graph_editor_reads.py](../../../../../../tests/test_graph_editor_reads.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_adjudication.py](../../../../../../tests/test_sidecar_adjudication.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_exams.py](../../../../../../tests/test_sidecar_exams.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_goals.py](../../../../../../tests/test_sidecar_goals.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_item_presentation.py](../../../../../../tests/test_sidecar_item_presentation.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_measurement.py](../../../../../../tests/test_sidecar_measurement.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_trace_and_clarification.py](../../../../../../tests/test_sidecar_trace_and_clarification.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/sqlite_admin.py](../../../../../../src/learnloop_sidecar/handlers/sqlite_admin.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
