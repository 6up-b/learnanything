---
title: "learnloop.app_launch"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/app_launch.py"
source_paths:
  - "src/learnloop/app_launch.py"
source_commit: "6a9fce28abaab76d47533e670901025fe3b2ffe5"
source_commit_timestamp: "2026-10-14T00:35:47-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "coordination"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.app_launch module"
  - "src/learnloop/app_launch.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/coordination"
  - "package/learnloop"
---

# `learnloop.app_launch`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.app_launch` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Application-level launchers shared by entry-point adapters.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/app_launch.py](../../../../../src/learnloop/app_launch.py) |
| Source lines | 29 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `coordination` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `6a9fce28abaab76d47533e670901025fe3b2ffe5` |
| Commit timestamp | `2026-10-14T00:35:47-04:00` |

## Public API

- `launch_tui(vault_root: Path) -> None` ([source](../../../../../src/learnloop/app_launch.py), line 8) — Launch the Textual frontend without coupling another adapter to it.
- `serve_mcp(vault_root: Path, **options) -> None` ([source](../../../../../src/learnloop/app_launch.py), line 16) — Serve the vault to chat hosts over MCP (spec_mcp_frontend_c1).

### Explicit exports

`__all__` declares:

- `launch_tui`
- `serve_mcp`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `launch_tui`; statically calls `launch_tui`
- [[Reference/Modules/learnloop/cli/mcp|learnloop.cli.mcp]] — imports `serve_mcp`; statically calls `serve_mcp`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]] — imports `run`; calls `run`

### Platform and third-party dependencies

- Standard library: `__future__`, `pathlib`
- Third party: `learnloop_mcp`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cli/mcp|learnloop.cli.mcp]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mcp_cli.py](../../../../../tests/test_mcp_cli.py) — direct import
  - `test_serve_binds_loopback_only_and_names_the_missing_extra`

## Modification guidance

- Make changes here when the responsibility remains app launch within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/app_launch.py](../../../../../src/learnloop/app_launch.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
