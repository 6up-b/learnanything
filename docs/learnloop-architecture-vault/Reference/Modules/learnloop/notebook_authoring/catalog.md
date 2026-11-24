---
title: "learnloop.notebook_authoring.catalog"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/notebook_authoring/catalog.py"
source_paths:
  - "src/learnloop/notebook_authoring/catalog.py"
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
  - "learnloop.notebook_authoring.catalog module"
  - "src/learnloop/notebook_authoring/catalog.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-notebook-authoring"
---

# `learnloop.notebook_authoring.catalog`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.notebook_authoring.catalog` exists within [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] to own the behavior summarized by its module contract: Generate the owner-side static folder: python -m learnloop.notebook_authoring.catalog NEW_DIR.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/notebook_authoring/catalog.py](../../../../../../src/learnloop/notebook_authoring/catalog.py) |
| Source lines | 91 |
| Owning package | [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Catalog` ([source](../../../../../../src/learnloop/notebook_authoring/catalog.py), line 17)
  - `__init__(self)` (line 18; internal)
  - `read_card(self, name)` (line 32; public)
  - `search_examples(self, query, *, widget=None, k, line_budget)` (line 35; public)
  - `read_example(self, example_id, expand='ancestors')` (line 38; public)
  - `export(self, out: Path)` (line 46; public) — Create a new folder; index.json is written last so partial exports are recognizable.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/notebook_authoring/cards|learnloop.notebook_authoring.cards]] — imports `build_cards`; calls `build_cards`
- [[Reference/Modules/learnloop/notebook_authoring/examples|learnloop.notebook_authoring.examples]] — imports `index_demo`, `installed_demos`, `search_examples`; calls `index_demo`, `installed_demos`, `search_examples`
- [[Reference/Modules/learnloop/notebook_authoring/marimo_adapter|learnloop.notebook_authoring.marimo_adapter]] — imports `inspect_demos`; calls `inspect_demos`
- [[Reference/Modules/learnloop/notebook_authoring/scratch|learnloop.notebook_authoring.scratch]] — imports `directory_fd`; calls `directory_fd`

### Platform and third-party dependencies

- Standard library: `__future__`, `argparse`, `hashlib`, `importlib`, `json`, `os`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_notebook_catalog.py](../../../../../../tests/test_notebook_catalog.py) — direct import
  - `test_static_folder_includes_installed_examples`

## Modification guidance

- Make changes here when the responsibility remains catalog within learnloop.notebook_authoring; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/notebook_authoring/catalog.py](../../../../../../src/learnloop/notebook_authoring/catalog.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
