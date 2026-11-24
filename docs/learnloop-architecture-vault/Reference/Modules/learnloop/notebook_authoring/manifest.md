---
title: "learnloop.notebook_authoring.manifest"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/notebook_authoring/manifest.py"
source_paths:
  - "src/learnloop/notebook_authoring/manifest.py"
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
  - "learnloop.notebook_authoring.manifest module"
  - "src/learnloop/notebook_authoring/manifest.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-notebook-authoring"
---

# `learnloop.notebook_authoring.manifest`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.notebook_authoring.manifest` exists within [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] to own the behavior summarized by its module contract: The static coverage owed by a single revision, before any review round.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/notebook_authoring/manifest.py](../../../../../../src/learnloop/notebook_authoring/manifest.py) |
| Source lines | 63 |
| Owning package | [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `static_manifest(report, activity: bytes, key: bytes | None)` ([source](../../../../../../src/learnloop/notebook_authoring/manifest.py), line 18)
- `check_manifest(expected: dict, supplied: bytes) -> list[dict]` ([source](../../../../../../src/learnloop/notebook_authoring/manifest.py), line 36)

## Internal implementation anchors

- `_states(report)` ([source](../../../../../../src/learnloop/notebook_authoring/manifest.py), line 10)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/notebook_authoring/contract_check|learnloop.notebook_authoring.contract_check]] — imports `check_manifest`, `static_manifest`; statically calls `check_manifest`, `static_manifest`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/notebook_authoring/dependencies|learnloop.notebook_authoring.dependencies]] — imports `notebook_pins`; calls `notebook_pins`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`
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

- Make changes here when the responsibility remains manifest within learnloop.notebook_authoring; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/notebook_authoring/manifest.py](../../../../../../src/learnloop/notebook_authoring/manifest.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
