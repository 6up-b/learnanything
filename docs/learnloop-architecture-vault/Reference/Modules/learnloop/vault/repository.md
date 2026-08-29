---
title: "learnloop.vault.repository"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault/repository.py"
source_paths:
  - "src/learnloop/vault/repository.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.vault"
layer: "infrastructure"
concepts:
  - "State and Persistence"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.vault.repository module"
  - "src/learnloop/vault/repository.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-vault"
---

# `learnloop.vault.repository`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.vault.repository` exists within [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] to own the behavior summarized by its module contract: Application-level repository opening for a configured vault.

The authoritative system-level explanation remains in [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault/repository.py](../../../../../../src/learnloop/vault/repository.py) |
| Source lines | 39 |
| Owning package | [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `open_vault_repository(vault_root: Path, sqlite_path: Path, *, migrations_dir: Path | None=None, clock: Clock | None=None, timeout_s: float=DEFAULT_TIMEOUT_S) -> Repository` ([source](../../../../../../src/learnloop/vault/repository.py), line 13) — Migrate and attach a repository under the vault mutation lock.

### Explicit exports

`__all__` declares:

- `open_vault_repository`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/bootstrap|learnloop.bootstrap]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `open_vault_repository`; statically calls `open_vault_repository`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `open_vault_repository`; statically calls `open_vault_repository`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/migration_coordinator|learnloop.migration_coordinator]] — imports `migrate_vault`; calls `migrate_vault`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `DEFAULT_TIMEOUT_S`

### Platform and third-party dependencies

- Standard library: `__future__`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/bootstrap|learnloop.bootstrap]], [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_migration_coordinator.py](../../../../../../tests/test_migration_coordinator.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains repository within learnloop.vault; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/vault/repository.py](../../../../../../src/learnloop/vault/repository.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
