---
title: "learnloop.cli.clarification"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/clarification.py"
source_paths:
  - "src/learnloop/cli/clarification.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.cli"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.cli.clarification module"
  - "src/learnloop/cli/clarification.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.clarification`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps clarification behavior inside its owning package, [[Reference/Modules/learnloop/cli/_package|learnloop.cli]]. Its public surface centers on `clarification_list_command`, `clarification_retry_command`, `clarification_expire_command`, `clarification_rate_command`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/clarification.py](../../../../../../src/learnloop/cli/clarification.py) |
| Source lines | 143 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `clarification_list_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/clarification.py), line 11) — Clarification requests and their derived status (pending / answered / timed_out).
- `clarification_retry_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/clarification.py), line 42) — Re-grade answers whose regrade never ran (spec_measurement_efficiency §3.A8).
- `clarification_expire_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/clarification.py), line 80) — Close the window on unanswered questions.
- `clarification_rate_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/clarification.py), line 104) — §3.A8's revert criterion: clarifications per model-graded attempt.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]] — imports `clarification_rate`, `expire_clarifications`, `resolve_awaiting_regrades`, `row_to_clarification`; calls `clarification_rate`, `expire_clarifications`, `resolve_awaiting_regrades`, `row_to_clarification`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `module`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_cli_generate_practice.py](../../../../../../tests/test_cli_generate_practice.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_cli_ingest.py](../../../../../../tests/test_cli_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_teach_back_generation.py](../../../../../../tests/test_teach_back_generation.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/clarification.py](../../../../../../src/learnloop/cli/clarification.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
