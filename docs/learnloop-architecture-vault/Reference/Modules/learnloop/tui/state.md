---
title: "learnloop.tui.state"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tui/state.py"
source_paths:
  - "src/learnloop/tui/state.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop.tui"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.tui.state module"
  - "src/learnloop/tui/state.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-tui"
---

# `learnloop.tui.state`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tui/_package|learnloop.tui]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps state behavior inside its owning package, [[Reference/Modules/learnloop/tui/_package|learnloop.tui]]. Its public surface centers on `TuiState`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tui/state.py](../../../../../../src/learnloop/tui/state.py) |
| Source lines | 48 |
| Owning package | [[Reference/Modules/learnloop/tui/_package|learnloop.tui]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class TuiState` ([source](../../../../../../src/learnloop/tui/state.py), line 17)
  - `load(cls, vault_root: Path) -> 'TuiState'` (line 26; public)
  - `refresh(self, *, session: SchedulerSession | None=None) -> None` (line 36; public)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]] — imports `TuiState`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `TuiState`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `TuiState`
- [[Reference/Modules/learnloop/tui/screens/start|learnloop.tui.screens.start]] — imports `TuiState`
- [[Reference/Modules/learnloop/tui/screens/today|learnloop.tui.screens.today]] — imports `TuiState`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]] — imports `StartupMaintenanceResult`, `run_startup_maintenance`; calls `run_startup_maintenance`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `ScheduledItem`, `SchedulerSession`, `build_due_queue`; calls `SchedulerSession`, `build_due_queue`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `StateSyncResult`, `sync_vault_state`; calls `sync_vault_state`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]], [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]], [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]], [[Reference/Modules/learnloop/tui/screens/start|learnloop.tui.screens.start]], [[Reference/Modules/learnloop/tui/screens/today|learnloop.tui.screens.today]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_e2e_tui.py](../../../../../../tests/test_e2e_tui.py) — imports consumer [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]]
- [tests/test_tui_app.py](../../../../../../tests/test_tui_app.py) — imports consumer [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]]
- [tests/test_tui_feedback.py](../../../../../../tests/test_tui_feedback.py) — imports consumer [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]]
- [tests/test_tui_practice.py](../../../../../../tests/test_tui_practice.py) — imports consumer [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]]
- [tests/test_tui_theme.py](../../../../../../tests/test_tui_theme.py) — imports consumer [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]]
- [tests/test_tui_today.py](../../../../../../tests/test_tui_today.py) — imports consumer [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]]
- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — imports consumer [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]]
- [tests/helpers.py](../../../../../../tests/helpers.py) — imports consumer [[Reference/Modules/learnloop/tui/screens/start|learnloop.tui.screens.start]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/tui/state.py](../../../../../../src/learnloop/tui/state.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
