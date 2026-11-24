---
title: "learnloop.notebook_authoring.marimo_adapter"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/notebook_authoring/marimo_adapter.py"
source_paths:
  - "src/learnloop/notebook_authoring/marimo_adapter.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.notebook_authoring"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.notebook_authoring.marimo_adapter module"
  - "src/learnloop/notebook_authoring/marimo_adapter.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-notebook-authoring"
---

# `learnloop.notebook_authoring.marimo_adapter`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.notebook_authoring.marimo_adapter` exists within [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] to own the behavior summarized by its module contract: The pinned static marimo interfaces, isolated from the command and filesystem.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/notebook_authoring/marimo_adapter.py](../../../../../../src/learnloop/notebook_authoring/marimo_adapter.py) |
| Source lines | 255 |
| Owning package | [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class NotebookDependencyError(ValueError)` ([source](../../../../../../src/learnloop/notebook_authoring/marimo_adapter.py), line 14) — The optional parser cannot safely be used with this installation.
- `inspect_structure(source: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/notebook_authoring/marimo_adapter.py), line 119) — Inspect in a clean process so upstream import logging cannot write to home.
- `inspect_cells(source: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/notebook_authoring/marimo_adapter.py), line 124) — Return cell bodies alongside the graph for static authoring tools.
- `inspect_demos(sources: list[str]) -> list[dict]` ([source](../../../../../../src/learnloop/notebook_authoring/marimo_adapter.py), line 129)
- `generate(cells: list[tuple[str, str]], *, held=()) -> str` ([source](../../../../../../src/learnloop/notebook_authoring/marimo_adapter.py), line 133)

## Internal implementation anchors

- `_parser_pin() -> str` ([source](../../../../../../src/learnloop/notebook_authoring/marimo_adapter.py), line 18)
- `_parse_structure(source: str, *, include_code: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/notebook_authoring/marimo_adapter.py), line 28) — Parse and compile metadata only; never construct or run a notebook App.
- `_worker(operation: str, payload: str) -> Any` ([source](../../../../../../src/learnloop/notebook_authoring/marimo_adapter.py), line 137)
- `_deny_side_effects(event: str, args: tuple) -> None` ([source](../../../../../../src/learnloop/notebook_authoring/marimo_adapter.py), line 158)
- `_generate(cells: list[tuple[str, str]], held: list[str]) -> str` ([source](../../../../../../src/learnloop/notebook_authoring/marimo_adapter.py), line 171)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/notebook_authoring/catalog|learnloop.notebook_authoring.catalog]] — imports `inspect_demos`; statically calls `inspect_demos`
- [[Reference/Modules/learnloop/notebook_authoring/cell_writer|learnloop.notebook_authoring.cell_writer]] — imports `generate`, `inspect_cells`; statically calls `generate`, `inspect_cells`
- [[Reference/Modules/learnloop/notebook_authoring/check|learnloop.notebook_authoring.check]] — imports `inspect_structure`; statically calls `inspect_structure`
- [[Reference/Modules/learnloop/notebook_authoring/contract|learnloop.notebook_authoring.contract]] — imports `inspect_cells`; statically calls `inspect_cells`
- [[Reference/Modules/learnloop/notebook_authoring/dependencies|learnloop.notebook_authoring.dependencies]] — imports `NotebookDependencyError`; statically calls `NotebookDependencyError`
- [[Reference/Modules/learnloop/notebook_authoring/examples|learnloop.notebook_authoring.examples]] — imports `inspect_cells`; statically calls `inspect_cells`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `ast`, `contextlib`, `importlib`, `json`, `keyword`, `os`, `subprocess`, `sys`, `tempfile`, `typing`
- Third party: `marimo`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/notebook_authoring/catalog|learnloop.notebook_authoring.catalog]], [[Reference/Modules/learnloop/notebook_authoring/cell_writer|learnloop.notebook_authoring.cell_writer]], [[Reference/Modules/learnloop/notebook_authoring/check|learnloop.notebook_authoring.check]], [[Reference/Modules/learnloop/notebook_authoring/contract|learnloop.notebook_authoring.contract]], [[Reference/Modules/learnloop/notebook_authoring/dependencies|learnloop.notebook_authoring.dependencies]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_notebook_catalog.py](../../../../../../tests/test_notebook_catalog.py) — direct import
  - `test_next_pin_changes_the_parser_admission_message`
  - `test_pin_bump_includes_environment_lock_notices_and_parser`
- [tests/test_notebook_cell_writer.py](../../../../../../tests/test_notebook_cell_writer.py) — direct import
  - `test_promotion_retains_given_name_and_never_executes`
  - `test_round_trip_and_edit`
- [tests/test_notebook_check.py](../../../../../../tests/test_notebook_check.py) — direct import
  - `test_compilation_does_not_create_marimo_scratch`
  - `test_malformed_cell_decorator_is_an_artifact_finding`
  - `test_unrepresented_source_fails_as_a_format_finding`
- [tests/test_notebook_contract.py](../../../../../../tests/test_notebook_contract.py) — direct import
  - `test_writer_keeps_held_reveal_across_edit`

## Modification guidance

- Make changes here when the responsibility remains marimo adapter within learnloop.notebook_authoring; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/notebook_authoring/marimo_adapter.py](../../../../../../src/learnloop/notebook_authoring/marimo_adapter.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
