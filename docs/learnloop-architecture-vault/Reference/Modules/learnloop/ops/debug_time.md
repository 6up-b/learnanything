---
title: "learnloop.ops.debug_time"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/debug_time.py"
source_paths:
  - "src/learnloop/ops/debug_time.py"
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
  - "learnloop.ops.debug_time module"
  - "src/learnloop/ops/debug_time.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.debug_time`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps debug time behavior inside its owning package, [[Reference/Modules/learnloop/ops/_package|learnloop.ops]]. Its public surface centers on `DebugAdvanceResult`, `DebugAdvanceError`, `advance_vault_days`.

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/debug_time.py](../../../../../../src/learnloop/ops/debug_time.py) |
| Source lines | 75 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class DebugAdvanceResult` ([source](../../../../../../src/learnloop/ops/debug_time.py), line 16)
  - `as_dict(self) -> dict[str, object]` (line 21; public)
- `class DebugAdvanceError(ValueError)` ([source](../../../../../../src/learnloop/ops/debug_time.py), line 48)
- `advance_vault_days(root: Path, days: int) -> DebugAdvanceResult` ([source](../../../../../../src/learnloop/ops/debug_time.py), line 52)

### Module constants

- `TIMESTAMP_FIELDS` ([src/learnloop/ops/debug_time.py](../../../../../../src/learnloop/ops/debug_time.py), line 29)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `DebugAdvanceError`, `advance_vault_days`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ops/debug_time_store|learnloop.ops.debug_time_store]] — imports `existing_timestamp_fields`, `shift_timestamp_field`; calls `existing_timestamp_fields`, `shift_timestamp_field`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `pathlib`, `sqlite3`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — imports consumer [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]]

## Modification guidance

- Make changes here when the responsibility remains debug time within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/debug_time.py](../../../../../../src/learnloop/ops/debug_time.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
