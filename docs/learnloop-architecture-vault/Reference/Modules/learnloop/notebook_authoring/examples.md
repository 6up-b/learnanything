---
title: "learnloop.notebook_authoring.examples"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/notebook_authoring/examples.py"
source_paths:
  - "src/learnloop/notebook_authoring/examples.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.notebook_authoring"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.notebook_authoring.examples module"
  - "src/learnloop/notebook_authoring/examples.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-notebook-authoring"
---

# `learnloop.notebook_authoring.examples`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.notebook_authoring.examples` exists within [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] to own the behavior summarized by its module contract: Static example candidates.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/notebook_authoring/examples.py](../../../../../../src/learnloop/notebook_authoring/examples.py) |
| Source lines | 125 |
| Owning package | [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `index_demo(source, origin, version, cards, *, graph=None)` ([source](../../../../../../src/learnloop/notebook_authoring/examples.py), line 29)
- `installed_demos(pins, cards)` ([source](../../../../../../src/learnloop/notebook_authoring/examples.py), line 74)
- `search_examples(examples, query, *, widget=None, k: int, line_budget: int)` ([source](../../../../../../src/learnloop/notebook_authoring/examples.py), line 105) — Lexical search of static candidates within the caller's context budget.

## Internal implementation anchors

- `_tools(cell, aliases, imports)` ([source](../../../../../../src/learnloop/notebook_authoring/examples.py), line 13)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/notebook_authoring/catalog|learnloop.notebook_authoring.catalog]] — imports `index_demo`, `installed_demos`, `search_examples`; statically calls `index_demo`, `installed_demos`, `search_examples`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/notebook_authoring/marimo_adapter|learnloop.notebook_authoring.marimo_adapter]] — imports `inspect_cells`; calls `inspect_cells`

### Platform and third-party dependencies

- Standard library: `__future__`, `ast`, `hashlib`, `importlib`, `re`, `textwrap`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/notebook_authoring/catalog|learnloop.notebook_authoring.catalog]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_notebook_catalog.py](../../../../../../tests/test_notebook_catalog.py) — direct import
  - `test_one_entry_adds_a_tool_with_its_extraction_gaps`
  - `test_slice_keeps_ancestors_and_reads_and_search_budget`

## Modification guidance

- Make changes here when the responsibility remains examples within learnloop.notebook_authoring; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/notebook_authoring/examples.py](../../../../../../src/learnloop/notebook_authoring/examples.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
