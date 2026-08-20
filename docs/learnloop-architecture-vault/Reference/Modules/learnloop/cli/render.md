---
title: "learnloop.cli.render"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/render.py"
source_paths:
  - "src/learnloop/cli/render.py"
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
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Inspect Persistent State"
aliases:
  - "learnloop.cli.render module"
  - "src/learnloop/cli/render.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.render`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This implementation module supports [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] through internal helpers such as `_format_elapsed`, `_json_ingest_progress`, `_AsciiSpinner`, `_dump`, `_plain`, `_echo_practice_generation_plan`, `_echo_diagnostic_generation_plan`, `_echo_ingest_summary`; it does not advertise a standalone public API.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/render.py](../../../../../../src/learnloop/cli/render.py) |
| Source lines | 171 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

No public top-level function or class definition is declared in this file.

### Module constants

- `_INGEST_SPINNER_FRAMES` ([src/learnloop/cli/render.py](../../../../../../src/learnloop/cli/render.py), line 16)
- `_INGEST_PROGRESS_EVENT` ([src/learnloop/cli/render.py](../../../../../../src/learnloop/cli/render.py), line 17)
- `_WRAP_WIDTH` ([src/learnloop/cli/render.py](../../../../../../src/learnloop/cli/render.py), line 18)

## Internal implementation anchors

- `_format_elapsed(seconds: float) -> str` ([source](../../../../../../src/learnloop/cli/render.py), line 20)
- `_json_ingest_progress(phase: str, details: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/cli/render.py), line 28)
- `class _AsciiSpinner` ([source](../../../../../../src/learnloop/cli/render.py), line 32)
- `_dump(value: object) -> str` ([source](../../../../../../src/learnloop/cli/render.py), line 100)
- `_plain(value: object) -> object` ([source](../../../../../../src/learnloop/cli/render.py), line 104)
- `_echo_practice_generation_plan(plan) -> None` ([source](../../../../../../src/learnloop/cli/render.py), line 117)
- `_echo_diagnostic_generation_plan(plan: DiagnosticPracticePlan) -> None` ([source](../../../../../../src/learnloop/cli/render.py), line 128)
- `_echo_ingest_summary(result) -> None` ([source](../../../../../../src/learnloop/cli/render.py), line 139)
- `_wrap_text(text: str, *, indent: str='  ') -> list[str]` ([source](../../../../../../src/learnloop/cli/render.py), line 147)
- `_dim(text: object) -> str` ([source](../../../../../../src/learnloop/cli/render.py), line 157)
- `_echo_section(title: str) -> None` ([source](../../../../../../src/learnloop/cli/render.py), line 160)
- `_echo_kv(label: str, value: object) -> None` ([source](../../../../../../src/learnloop/cli/render.py), line 164)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `DiagnosticPracticePlan`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `sys`, `textwrap`, `threading`, `time`, `typing`
- Third party: `pydantic`, `typer`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — imports consumer [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/render.py](../../../../../../src/learnloop/cli/render.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
