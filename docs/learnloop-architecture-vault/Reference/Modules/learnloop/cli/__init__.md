---
title: "learnloop.cli"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/__init__.py"
source_paths:
  - "src/learnloop/cli/__init__.py"
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
aliases:
  - "learnloop.cli module"
  - "src/learnloop/cli/__init__.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module establishes the Python package boundary for [[Reference/Modules/learnloop/cli/_package|learnloop.cli]].

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/__init__.py](../../../../../../src/learnloop/cli/__init__.py) |
| Source lines | 53 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

No public top-level function or class definition is declared in this file.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

> [!tip] Runtime entry point
> `pyproject.toml` registers `learnloop = learnloop.cli:app`; console invocation is therefore a non-AST consumer of this module.

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `_AsciiSpinner`, `_client_for_provider`, `_parse_mode_mix`, `_ready_provider_for_task`, `_runtime_for_provider`, `module`
- [[Reference/Modules/learnloop/cli/calibration|learnloop.cli.calibration]] — imports `module`
- [[Reference/Modules/learnloop/cli/card|learnloop.cli.card]] — imports `module`
- [[Reference/Modules/learnloop/cli/claims|learnloop.cli.claims]] — imports `module`
- [[Reference/Modules/learnloop/cli/clarification|learnloop.cli.clarification]] — imports `module`
- [[Reference/Modules/learnloop/cli/config|learnloop.cli.config]] — imports `module`
- [[Reference/Modules/learnloop/cli/contracts|learnloop.cli.contracts]] — imports `module`
- [[Reference/Modules/learnloop/cli/controller|learnloop.cli.controller]] — imports `module`
- [[Reference/Modules/learnloop/cli/depth|learnloop.cli.depth]] — imports `module`
- [[Reference/Modules/learnloop/cli/diagnosis|learnloop.cli.diagnosis]] — imports `module`
- [[Reference/Modules/learnloop/cli/exam|learnloop.cli.exam]] — imports `module`
- [[Reference/Modules/learnloop/cli/fit|learnloop.cli.fit]] — imports `module`
- [[Reference/Modules/learnloop/cli/goldenpath|learnloop.cli.goldenpath]] — imports `module`
- [[Reference/Modules/learnloop/cli/grading|learnloop.cli.grading]] — imports `module`
- [[Reference/Modules/learnloop/cli/ingest_batches|learnloop.cli.ingest_batches]] — imports `module`
- [[Reference/Modules/learnloop/cli/questions|learnloop.cli.questions]] — imports `module`
- [[Reference/Modules/learnloop/cli/registry|learnloop.cli.registry]] — imports `module`
- [[Reference/Modules/learnloop/cli/sim|learnloop.cli.sim]] — imports `module`
- [[Reference/Modules/learnloop/cli/source_set|learnloop.cli.source_set]] — imports `module`
- [[Reference/Modules/learnloop/cli/surfaces|learnloop.cli.surfaces]] — imports `module`

### Platform and third-party dependencies

- Standard library: none imported directly
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_cli_generate_practice.py](../../../../../../tests/test_cli_generate_practice.py) — direct import
  - `test_populate_goal_uses_a_15_minute_provider_timeout`
  - `test_provider_timeout_override_reaches_codex_sdk_client`
- [tests/test_cli_ingest.py](../../../../../../tests/test_cli_ingest.py) — direct import
  - `test_ascii_spinner_writes_elapsed_status_for_tty`
- [tests/test_teach_back_generation.py](../../../../../../tests/test_teach_back_generation.py) — direct import
  - `test_parse_mode_mix_rejects_malformed`
  - `test_parse_mode_mix_valid`

## Modification guidance

- Change this file when intentionally adding or removing a package-level re-export; keep implementation logic in the owning module.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/__init__.py](../../../../../../src/learnloop/cli/__init__.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
