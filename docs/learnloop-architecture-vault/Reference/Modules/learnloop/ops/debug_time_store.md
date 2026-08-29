---
title: "learnloop.ops.debug_time_store"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/debug_time_store.py"
source_paths:
  - "src/learnloop/ops/debug_time_store.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.ops"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.debug_time_store module"
  - "src/learnloop/ops/debug_time_store.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.debug_time_store`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.debug_time_store` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: SQL owner for the debug-time operational mutation.

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/debug_time_store.py](../../../../../../src/learnloop/ops/debug_time_store.py) |
| Source lines | 50 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `existing_timestamp_fields(connection: sqlite3.Connection) -> dict[str, set[str]]` ([source](../../../../../../src/learnloop/ops/debug_time_store.py), line 10)
- `shift_timestamp_field(connection: sqlite3.Connection, table: str, field: str, modifier: str) -> int` ([source](../../../../../../src/learnloop/ops/debug_time_store.py), line 27)

### Explicit exports

`__all__` declares:

- `existing_timestamp_fields`
- `shift_timestamp_field`

## Internal implementation anchors

- `_quote_identifier(value: str) -> str` ([source](../../../../../../src/learnloop/ops/debug_time_store.py), line 46)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ops/debug_time|learnloop.ops.debug_time]] — imports `existing_timestamp_fields`, `shift_timestamp_field`; statically calls `existing_timestamp_fields`, `shift_timestamp_field`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/table_roles|learnloop.db.table_roles]] — imports `role_for_table`; calls `role_for_table`

### Platform and third-party dependencies

- Standard library: `__future__`, `sqlite3`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/ops/debug_time|learnloop.ops.debug_time]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No direct or one-hop consumer test was found by static import analysis.

> [!caution] Test gap signal
> Treat this as a navigation signal, not proof that behavior is untested: dynamic and higher-level coverage is outside this static map. Add focused coverage when changing isolated behavior here.

## Modification guidance

- Make changes here when the responsibility remains debug time store within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/debug_time_store.py](../../../../../../src/learnloop/ops/debug_time_store.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
