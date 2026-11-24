---
title: "learnloop.notebook_authoring.cards"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/notebook_authoring/cards.py"
source_paths:
  - "src/learnloop/notebook_authoring/cards.py"
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
  - "learnloop.notebook_authoring.cards module"
  - "src/learnloop/notebook_authoring/cards.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-notebook-authoring"
---

# `learnloop.notebook_authoring.cards`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.notebook_authoring.cards` exists within [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] to own the behavior summarized by its module contract: Extract author-facing API facts from the Python sources shipped in pinned wheels.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/notebook_authoring/cards.py](../../../../../../src/learnloop/notebook_authoring/cards.py) |
| Source lines | 149 |
| Owning package | [[Reference/Modules/learnloop/notebook_authoring/_package|learnloop.notebook_authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `build_cards() -> dict` ([source](../../../../../../src/learnloop/notebook_authoring/cards.py), line 101)

## Internal implementation anchors

- `_module(module: str)` ([source](../../../../../../src/learnloop/notebook_authoring/cards.py), line 18)
- `_imports(module: str) -> dict[str, tuple[str, str]]` ([source](../../../../../../src/learnloop/notebook_authoring/cards.py), line 29)
- `_exports(module: str) -> list[str]` ([source](../../../../../../src/learnloop/notebook_authoring/cards.py), line 40)
- `_definition(module, name)` ([source](../../../../../../src/learnloop/notebook_authoring/cards.py), line 47)
- `_traits(module, cls)` ([source](../../../../../../src/learnloop/notebook_authoring/cards.py), line 55)
- `_card(public, module, name)` ([source](../../../../../../src/learnloop/notebook_authoring/cards.py), line 75)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/notebook_authoring/catalog|learnloop.notebook_authoring.catalog]] — imports `build_cards`; statically calls `build_cards`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/notebook_authoring/dependencies|learnloop.notebook_authoring.dependencies]] — imports `notebook_pins`; calls `notebook_pins`
- [[Reference/Modules/learnloop/notebook_authoring/tool_notes|learnloop.notebook_authoring.tool_notes]] — imports `RECIPES`, `TOOL_NOTES`

### Platform and third-party dependencies

- Standard library: `__future__`, `ast`, `copy`, `functools`, `hashlib`, `importlib`, `inspect`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/notebook_authoring/catalog|learnloop.notebook_authoring.catalog]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_notebook_catalog.py](../../../../../../tests/test_notebook_catalog.py) — direct import
  - `test_every_public_export_has_a_card_or_reason`
  - `test_one_entry_adds_a_tool_with_its_extraction_gaps`
  - `test_pin_bump_includes_environment_lock_notices_and_parser`

## Modification guidance

- Make changes here when the responsibility remains cards within learnloop.notebook_authoring; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/notebook_authoring/cards.py](../../../../../../src/learnloop/notebook_authoring/cards.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
