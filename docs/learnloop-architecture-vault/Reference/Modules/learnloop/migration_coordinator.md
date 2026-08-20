---
title: "learnloop.migration_coordinator"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/migration_coordinator.py"
source_paths:
  - "src/learnloop/migration_coordinator.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop"
layer: "coordination"
concepts:
  - "Architecture Overview"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.migration_coordinator module"
  - "src/learnloop/migration_coordinator.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/coordination"
  - "package/learnloop"
---

# `learnloop.migration_coordinator`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.migration_coordinator` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Application-level coordination for mutating a vault's database schema.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/migration_coordinator.py](../../../../../src/learnloop/migration_coordinator.py) |
| Source lines | 36 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `coordination` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `migrate_vault(vault_root: Path, sqlite_path: Path, *, migrations_dir: Path | None=None, clock: Clock | None=None, timeout_s: float=DEFAULT_TIMEOUT_S) -> list[Migration]` ([source](../../../../../src/learnloop/migration_coordinator.py), line 12) — Apply migrations while holding the vault's cross-process mutation lock.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `migrate_vault`; statically calls `migrate_vault`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `migrate_vault`; statically calls `migrate_vault`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `migrate_vault`; statically calls `migrate_vault`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/migrate|learnloop.db.migrate]] — imports `Migration`, `apply_migrations`; calls `apply_migrations`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `DEFAULT_TIMEOUT_S`, `vault_mutation_lock`; calls `vault_mutation_lock`

### Platform and third-party dependencies

- Standard library: `__future__`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]], [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]], [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_migration_coordinator.py](../../../../../tests/test_migration_coordinator.py) — direct import
  - `test_coordinator_locks_the_vault_for_a_relocated_database`
  - `test_process_death_mid_migration_leaves_body_and_receipt_fully_absent`

## Modification guidance

- Make changes here when the responsibility remains migration coordinator within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/migration_coordinator.py](../../../../../src/learnloop/migration_coordinator.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
