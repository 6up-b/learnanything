---
title: "learnloop.vault_lock"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault_lock.py"
source_paths:
  - "src/learnloop/vault_lock.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.vault_lock module"
  - "src/learnloop/vault_lock.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.vault_lock`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.vault_lock` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Cross-process vault mutation lock (source-ingestion §8.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault_lock.py](../../../../../src/learnloop/vault_lock.py) |
| Source lines | 179 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class VaultLockError(RuntimeError)` ([source](../../../../../src/learnloop/vault_lock.py), line 41) — Base class for vault mutation lock failures.
- `class VaultLockTimeout(VaultLockError)` ([source](../../../../../src/learnloop/vault_lock.py), line 45) — Raised when the lock could not be acquired within the timeout.
- `class LockHolder` ([source](../../../../../src/learnloop/vault_lock.py), line 50)
- `vault_lock_path(root: Path) -> Path` ([source](../../../../../src/learnloop/vault_lock.py), line 55)
- `read_lock_holder(root: Path) -> LockHolder | None` ([source](../../../../../src/learnloop/vault_lock.py), line 59) — Best-effort diagnostic read of the current holder metadata.
- `vault_mutation_lock(root: Path, *, purpose: str, timeout_s: float=DEFAULT_TIMEOUT_S) -> Iterator[LockHolder]` ([source](../../../../../src/learnloop/vault_lock.py), line 86) — Acquire the exclusive vault mutation lock for the critical section.

### Module constants

- `DEFAULT_TIMEOUT_S` ([src/learnloop/vault_lock.py](../../../../../src/learnloop/vault_lock.py), line 37)
- `_POLL_INTERVAL_S` ([src/learnloop/vault_lock.py](../../../../../src/learnloop/vault_lock.py), line 38)

## Internal implementation anchors

- `_read_lock_holder_path(path: Path) -> LockHolder | None` ([source](../../../../../src/learnloop/vault_lock.py), line 70)
- `_acquire_with_timeout(fd: int, path: Path, timeout_s: float) -> None` ([source](../../../../../src/learnloop/vault_lock.py), line 141)
- `_write_holder_fd(fd: int, holder: LockHolder) -> None` ([source](../../../../../src/learnloop/vault_lock.py), line 164)
- `_write_holder(path: Path, holder: LockHolder) -> None` ([source](../../../../../src/learnloop/vault_lock.py), line 171)
- `_clear_holder(path: Path) -> None` ([source](../../../../../src/learnloop/vault_lock.py), line 175)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/migration_coordinator|learnloop.migration_coordinator]] — imports `DEFAULT_TIMEOUT_S`, `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/ops/vault_lock|learnloop.ops.vault_lock]] — imports `module`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `DEFAULT_TIMEOUT_S`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `errno`, `fcntl`, `os`, `pathlib`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/migration_coordinator|learnloop.migration_coordinator]], [[Reference/Modules/learnloop/ops/vault_lock|learnloop.ops.vault_lock]], [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_migration_coordinator.py](../../../../../tests/test_migration_coordinator.py) — imports consumer [[Reference/Modules/learnloop/migration_coordinator|learnloop.migration_coordinator]]
- [tests/test_vault_lock.py](../../../../../tests/test_vault_lock.py) — imports consumer [[Reference/Modules/learnloop/ops/vault_lock|learnloop.ops.vault_lock]]

## Modification guidance

- Make changes here when the responsibility remains vault lock within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/vault_lock.py](../../../../../src/learnloop/vault_lock.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
