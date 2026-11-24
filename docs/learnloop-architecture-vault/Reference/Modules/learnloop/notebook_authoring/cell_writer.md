---
title: "learnloop.notebook_authoring.cell_writer"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/notebook_authoring/cell_writer.py"
source_paths:
  - "src/learnloop/notebook_authoring/cell_writer.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.notebook_authoring"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.notebook_authoring.cell_writer module"
  - "src/learnloop/notebook_authoring/cell_writer.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-notebook-authoring"
---

# `learnloop.notebook_authoring.cell_writer`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.notebook_authoring.cell_writer` exists within [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] to own the behavior summarized by its module contract: Write one activity in caller-owned job scratch from ordered, named cells.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/notebook_authoring/cell_writer.py](../../../../../../src/learnloop/notebook_authoring/cell_writer.py) |
| Source lines | 58 |
| Owning package | [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `write_cells(scratch: Path, cells: Sequence[tuple[str, str]], *, held: Sequence[str]=()) -> Path` ([source](../../../../../../src/learnloop/notebook_authoring/cell_writer.py), line 31) — Create activity.py exclusively.
- `edit_cell(scratch: Path, name: str, code: str) -> Path` ([source](../../../../../../src/learnloop/notebook_authoring/cell_writer.py), line 39) — Replace a named cell in a writer-generated revision, retaining order and names.

## Internal implementation anchors

- `_publish(directory: int, source: str, *, replace: bool) -> None` ([source](../../../../../../src/learnloop/notebook_authoring/cell_writer.py), line 16)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/notebook_authoring/marimo_adapter|learnloop.notebook_authoring.marimo_adapter]] — imports `generate`, `inspect_cells`; calls `generate`, `inspect_cells`
- [[Reference/Modules/learnloop/notebook_authoring/scratch|learnloop.notebook_authoring.scratch]] — imports `directory_fd`; calls `directory_fd`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `fcntl`, `os`, `pathlib`, `stat`, `uuid`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_notebook_cell_writer.py](../../../../../../tests/test_notebook_cell_writer.py) — direct import
  - `test_generated_file_passes_pinned_marimo_check`
  - `test_job_paths`
  - `test_promotion_retains_given_name_and_never_executes`
  - `test_reject_before_creating_artifact`
  - `test_round_trip_and_edit`
- [tests/test_notebook_contract.py](../../../../../../tests/test_notebook_contract.py) — direct import
  - `test_writer_keeps_held_reveal_across_edit`

## Modification guidance

- Make changes here when the responsibility remains cell writer within learnloop.notebook_authoring; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/notebook_authoring/cell_writer.py](../../../../../../src/learnloop/notebook_authoring/cell_writer.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
