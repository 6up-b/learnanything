---
title: "learnloop.app_launch"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/app_launch.py"
source_paths:
  - "src/learnloop/app_launch.py"
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
| Source lines | 16 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `coordination` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `launch_tui(vault_root: Path) -> None` ([source](../../../../../src/learnloop/app_launch.py), line 8) — Launch the Textual frontend without coupling another adapter to it.

### Explicit exports

`__all__` declares:

- `launch_tui`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `launch_tui`; statically calls `launch_tui`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]] — imports `run`; calls `run`

### Platform and third-party dependencies

- Standard library: `__future__`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_causal_attribution_p1.py](../../../../../tests/test_causal_attribution_p1.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_causal_trace_consistency_p2.py](../../../../../tests/test_causal_trace_consistency_p2.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_certification_cold_probe.py](../../../../../tests/test_certification_cold_probe.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_cli_attempt.py](../../../../../tests/test_cli_attempt.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_cli_commands.py](../../../../../tests/test_cli_commands.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_cli_entrypoint.py](../../../../../tests/test_cli_entrypoint.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_cli_fit.py](../../../../../tests/test_cli_fit.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_cli_generate_practice.py](../../../../../tests/test_cli_generate_practice.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_cli_help_snapshot.py](../../../../../tests/test_cli_help_snapshot.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_cli_ingest.py](../../../../../tests/test_cli_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_cli_json.py](../../../../../tests/test_cli_json.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_cli_observations.py](../../../../../tests/test_cli_observations.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]

## Modification guidance

- Make changes here when the responsibility remains app launch within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/app_launch.py](../../../../../src/learnloop/app_launch.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
