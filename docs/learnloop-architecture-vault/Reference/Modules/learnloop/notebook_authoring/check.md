---
title: "learnloop.notebook_authoring.check"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/notebook_authoring/check.py"
source_paths:
  - "src/learnloop/notebook_authoring/check.py"
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
  - "learnloop.notebook_authoring.check module"
  - "src/learnloop/notebook_authoring/check.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-notebook-authoring"
---

# `learnloop.notebook_authoring.check`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.notebook_authoring.check` exists within [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] to own the behavior summarized by its module contract: Read an explicit artifact and write a structure-only report to explicit scratch.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/notebook_authoring/check.py](../../../../../../src/learnloop/notebook_authoring/check.py) |
| Source lines | 64 |
| Owning package | [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class OutputPathError(ValueError)` ([source](../../../../../../src/learnloop/notebook_authoring/check.py), line 14) — The requested output cannot be confined without overwriting existing data.
- `check_structure(path: Path, out: Path) -> tuple[dict, str]` ([source](../../../../../../src/learnloop/notebook_authoring/check.py), line 41) — Return the report and summary; the source is never imported or modified.
- `write_reports(out, scope, report, summary, *, manifest=None)` ([source](../../../../../../src/learnloop/notebook_authoring/check.py), line 56)

## Internal implementation anchors

- `_output_directory(path: Path, names: tuple[str, ...]) -> Iterator[int]` ([source](../../../../../../src/learnloop/notebook_authoring/check.py), line 19)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/notebook|learnloop.cli.notebook]] — imports `OutputPathError`, `check_structure`; statically calls `check_structure`
- [[Reference/Modules/learnloop/notebook_authoring/contract_check|learnloop.notebook_authoring.contract_check]] — imports `write_reports`; statically calls `write_reports`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/notebook_authoring/marimo_adapter|learnloop.notebook_authoring.marimo_adapter]] — imports `inspect_structure`; calls `inspect_structure`
- [[Reference/Modules/learnloop/notebook_authoring/scratch|learnloop.notebook_authoring.scratch]] — imports `directory_fd`; calls `directory_fd`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `json`, `os`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/notebook|learnloop.cli.notebook]], [[Reference/Modules/learnloop/notebook_authoring/contract_check|learnloop.notebook_authoring.contract_check]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_notebook_contract.py](../../../../../../tests/test_notebook_contract.py) — imports consumer [[Reference/Modules/learnloop/notebook_authoring/contract_check|learnloop.notebook_authoring.contract_check]]

## Modification guidance

- Make changes here when the responsibility remains check within learnloop.notebook_authoring; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/notebook_authoring/check.py](../../../../../../src/learnloop/notebook_authoring/check.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
