---
title: "learnloop.goals.goal_series_store"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/goals/goal_series_store.py"
source_paths:
  - "src/learnloop/goals/goal_series_store.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.goals"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.goals.goal_series_store module"
  - "src/learnloop/goals/goal_series_store.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-goals"
---

# `learnloop.goals.goal_series_store`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.goals.goal_series_store` exists within [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] to own the behavior summarized by its module contract: Scratch-database write owner for historical goal-series replay.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/goals/goal_series_store.py](../../../../../../src/learnloop/goals/goal_series_store.py) |
| Source lines | 113 |
| Owning package | [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `prune_rows(connection, table: str, column: str, values: list[Any], *, delete_rows: bool=True, depth: int=0) -> None` ([source](../../../../../../src/learnloop/goals/goal_series_store.py), line 67) — Prune scratch rows while respecting non-cascading foreign keys.

### Module constants

- `_MAX_PRUNE_DEPTH` ([src/learnloop/goals/goal_series_store.py](../../../../../../src/learnloop/goals/goal_series_store.py), line 9)
- `_PRUNE_CHUNK` ([src/learnloop/goals/goal_series_store.py](../../../../../../src/learnloop/goals/goal_series_store.py), line 10)

### Explicit exports

`__all__` declares:

- `prune_rows`

## Internal implementation anchors

- `_chunked(values: list[Any]) -> list[list[Any]]` ([source](../../../../../../src/learnloop/goals/goal_series_store.py), line 13)
- `_referencing_columns(connection, table: str) -> list[tuple[str, str, str, str]]` ([source](../../../../../../src/learnloop/goals/goal_series_store.py), line 20) — Return child references as ``(table, column, parent, on_delete)``.
- `_distinct_column(connection, table: str, column: str, key: str, values: list[Any]) -> list[Any]` ([source](../../../../../../src/learnloop/goals/goal_series_store.py), line 44)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/goals/goal_series|learnloop.goals.goal_series]] — imports `prune_rows`; statically calls `prune_rows`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/table_roles|learnloop.db.table_roles]] — imports `role_for_table`; calls `role_for_table`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/goals/goal_series|learnloop.goals.goal_series]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_goal_series.py](../../../../../../tests/test_goal_series.py) — imports consumer [[Reference/Modules/learnloop/goals/goal_series|learnloop.goals.goal_series]]

## Modification guidance

- Change goal series store policy here when goals owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/goals/goal_series_store.py](../../../../../../src/learnloop/goals/goal_series_store.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
