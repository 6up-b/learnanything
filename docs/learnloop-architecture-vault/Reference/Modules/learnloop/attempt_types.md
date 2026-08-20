---
title: "learnloop.attempt_types"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempt_types.py"
source_paths:
  - "src/learnloop/attempt_types.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop"
layer: "primitive"
concepts:
  - "Architecture Overview"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempt_types module"
  - "src/learnloop/attempt_types.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/primitive"
  - "package/learnloop"
---

# `learnloop.attempt_types`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps attempt types behavior inside its owning package, [[Reference/Modules/learnloop/_package|learnloop]]. Its public surface centers on `unsupported_attempt_types`, `default_attempt_type`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempt_types.py](../../../../../src/learnloop/attempt_types.py) |
| Source lines | 69 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `primitive` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `unsupported_attempt_types(values: list[str] | tuple[str, ...] | None) -> list[str]` ([source](../../../../../src/learnloop/attempt_types.py), line 55)
- `default_attempt_type(allowed: list[str] | tuple[str, ...] | None) -> AttemptType` ([source](../../../../../src/learnloop/attempt_types.py), line 61)

### Module constants

- `SUPPORTED_ATTEMPT_TYPES` ([src/learnloop/attempt_types.py](../../../../../src/learnloop/attempt_types.py), line 20)
- `NON_RECORDING_ATTEMPT_TYPES` ([src/learnloop/attempt_types.py](../../../../../src/learnloop/attempt_types.py), line 45)
- `DEFAULT_ATTEMPT_TYPE` ([src/learnloop/attempt_types.py](../../../../../src/learnloop/attempt_types.py), line 47)
- `_SUPPORTED` ([src/learnloop/attempt_types.py](../../../../../src/learnloop/attempt_types.py), line 52)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `NON_RECORDING_ATTEMPT_TYPES`, `SUPPORTED_ATTEMPT_TYPES`, `unsupported_attempt_types`; statically calls `unsupported_attempt_types`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `default_attempt_type`
- [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]] — imports `AttemptType`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `unsupported_attempt_types`; statically calls `unsupported_attempt_types`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `DEFAULT_ATTEMPT_TYPE`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `default_attempt_type`; statically calls `default_attempt_type`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `AttemptType`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]], [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]], [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_migrations.py](../../../../../tests/test_migrations.py) — direct import
  - `test_practice_attempts_schema_matches_supported_attempt_types`

## Modification guidance

- Make changes here when the responsibility remains attempt types within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempt_types.py](../../../../../src/learnloop/attempt_types.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
