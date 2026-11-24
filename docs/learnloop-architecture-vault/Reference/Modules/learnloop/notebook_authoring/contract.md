---
title: "learnloop.notebook_authoring.contract"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/notebook_authoring/contract.py"
source_paths:
  - "src/learnloop/notebook_authoring/contract.py"
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
  - "learnloop.notebook_authoring.contract module"
  - "src/learnloop/notebook_authoring/contract.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-notebook-authoring"
---

# `learnloop.notebook_authoring.contract`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.notebook_authoring.contract` exists within [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] to own the behavior summarized by its module contract: Static activity declarations.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/notebook_authoring/contract.py](../../../../../../src/learnloop/notebook_authoring/contract.py) |
| Source lines | 307 |
| Owning package | [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `inspect_contract(source: str, key: str | None) -> dict` ([source](../../../../../../src/learnloop/notebook_authoring/contract.py), line 206)

### Module constants

- `MASKS` ([src/learnloop/notebook_authoring/contract.py](../../../../../../src/learnloop/notebook_authoring/contract.py), line 11)
- `RESPONSES` ([src/learnloop/notebook_authoring/contract.py](../../../../../../src/learnloop/notebook_authoring/contract.py), line 12)

## Internal implementation anchors

- `_text(value)` ([source](../../../../../../src/learnloop/notebook_authoring/contract.py), line 15)
- `_reference(node)` ([source](../../../../../../src/learnloop/notebook_authoring/contract.py), line 19)
- `_literal(node)` ([source](../../../../../../src/learnloop/notebook_authoring/contract.py), line 27)
- `_metadata(value, cells, definitions)` ([source](../../../../../../src/learnloop/notebook_authoring/contract.py), line 34)
- `_arguments(call, fields, *, positional=())` ([source](../../../../../../src/learnloop/notebook_authoring/contract.py), line 65)
- `_commit(call, binding)` ([source](../../../../../../src/learnloop/notebook_authoring/contract.py), line 78)
- `_sdk_call(method, call, binding, cell, declarations)` ([source](../../../../../../src/learnloop/notebook_authoring/contract.py), line 99)
- `_key_interface(source, masks)` ([source](../../../../../../src/learnloop/notebook_authoring/contract.py), line 128)
- `_key_access(node)` ([source](../../../../../../src/learnloop/notebook_authoring/contract.py), line 156)
- `_reveal_flow(cells, declarations, declared_units, fail)` ([source](../../../../../../src/learnloop/notebook_authoring/contract.py), line 172) — A visible descendant of held data can leak it even through an intermediate cell.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/notebook_authoring/contract_check|learnloop.notebook_authoring.contract_check]] — imports `inspect_contract`; statically calls `inspect_contract`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/notebook_authoring/marimo_adapter|learnloop.notebook_authoring.marimo_adapter]] — imports `inspect_cells`; calls `inspect_cells`

### Platform and third-party dependencies

- Standard library: `__future__`, `ast`, `collections`, `math`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/notebook_authoring/contract_check|learnloop.notebook_authoring.contract_check]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_notebook_contract.py](../../../../../../tests/test_notebook_contract.py) — direct import
  - `test_manifest_cannot_be_reused_after_client_or_key_edit`
  - `test_stale_missing_or_fabricated_manifest`
  - `test_static_contract_and_manifest_obligations`

## Modification guidance

- Make changes here when the responsibility remains contract within learnloop.notebook_authoring; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/notebook_authoring/contract.py](../../../../../../src/learnloop/notebook_authoring/contract.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
