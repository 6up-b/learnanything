---
title: "learnloop.ops.startup"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/startup.py"
source_paths:
  - "src/learnloop/ops/startup.py"
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
  - "learnloop.ops.startup module"
  - "src/learnloop/ops/startup.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.startup`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps startup behavior inside its owning package, [[Reference/Modules/learnloop/ops/_package|learnloop.ops]]. Its public surface centers on `StartupMaintenanceResult`, `run_startup_maintenance`.

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/startup.py](../../../../../../src/learnloop/ops/startup.py) |
| Source lines | 95 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class StartupMaintenanceResult` ([source](../../../../../../src/learnloop/ops/startup.py), line 16)
  - `as_dict(self) -> dict[str, object]` (line 23; public)
- `run_startup_maintenance(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> StartupMaintenanceResult` ([source](../../../../../../src/learnloop/ops/startup.py), line 32)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `run_startup_maintenance`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `StartupMaintenanceResult`, `run_startup_maintenance`; statically calls `run_startup_maintenance`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `run_startup_maintenance`; statically calls `run_startup_maintenance`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `CodexRuntimeReport`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`, `runtime_for_provider`; calls `ready_client_for_task`, `runtime_for_provider`
- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `AIRuntimeReport`
- [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]] — imports `expire_clarifications`, `resolve_awaiting_regrades`; calls `expire_clarifications`, `resolve_awaiting_regrades`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `DeferredRegradeResult`, `run_deferred_ai_regrades`, `run_deferred_regrades`; calls `run_deferred_ai_regrades`, `run_deferred_regrades`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `CODEX_PROVIDER_NAMES`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_deferred_regrade.py](../../../../../../tests/test_deferred_regrade.py) — direct import
  - `test_startup_maintenance_regrades_pending_self_grade_when_codex_ready`
- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_config_matrix_executes_all_six_production_resolution_paths`

## Modification guidance

- Make changes here when the responsibility remains startup within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/startup.py](../../../../../../src/learnloop/ops/startup.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
