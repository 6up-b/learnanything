---
title: "learnloop.desks.content_ref"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/desks/content_ref.py"
source_paths:
  - "src/learnloop/desks/content_ref.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.desks"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.desks.content_ref module"
  - "src/learnloop/desks/content_ref.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-desks"
---

# `learnloop.desks.content_ref`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/desks/_package|learnloop.desks]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.desks.content_ref` exists within [[Reference/Modules/learnloop/desks/_package|learnloop.desks]] to own the behavior summarized by its module contract: One model for "something to show" (spec §3.4): a window's content, an open spec, a claim's target, a search result, a promoted row and a path row all carry a :data:`ContentRef`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/desks/content_ref.py](../../../../../../src/learnloop/desks/content_ref.py) |
| Source lines | 122 |
| Owning package | [[Reference/Modules/learnloop/desks/_package|learnloop.desks]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class WireModel(BaseModel)` ([source](../../../../../../src/learnloop/desks/content_ref.py), line 19) — A strict wire model: camelCase or snake_case in, unknown fields refused.
  - `wire(self) -> dict[str, Any]` (line 24; public) — The snake_case form stored and hashed (absent optionals left out).
- `class SpanRange(WireModel)` ([source](../../../../../../src/learnloop/desks/content_ref.py), line 30)
- `class SourceRef(WireModel)` ([source](../../../../../../src/learnloop/desks/content_ref.py), line 35)
- `class VideoRef(WireModel)` ([source](../../../../../../src/learnloop/desks/content_ref.py), line 43)
- `class PadRef(WireModel)` ([source](../../../../../../src/learnloop/desks/content_ref.py), line 50)
- `class LessonRef(WireModel)` ([source](../../../../../../src/learnloop/desks/content_ref.py), line 55)
- `class ThreadRef(WireModel)` ([source](../../../../../../src/learnloop/desks/content_ref.py), line 60)
- `class CompareRef(WireModel)` ([source](../../../../../../src/learnloop/desks/content_ref.py), line 65)
  - `_one_of(self) -> CompareRef` (line 71; internal)
- `class PanelRef(WireModel)` ([source](../../../../../../src/learnloop/desks/content_ref.py), line 77)
- `class FigureNotebookRef(WireModel)` ([source](../../../../../../src/learnloop/desks/content_ref.py), line 83)
- `class PreparingRef(WireModel)` ([source](../../../../../../src/learnloop/desks/content_ref.py), line 88) — A book still being prepared: it has no reading yet, so it is named by its source alone.
- `class Target(WireModel)` ([source](../../../../../../src/learnloop/desks/content_ref.py), line 105) — Where inside a content reference to land: a passage, a time or a block.
- `class TargetedRef(WireModel)` ([source](../../../../../../src/learnloop/desks/content_ref.py), line 113)

### Explicit exports

`__all__` declares:

- `CompareRef`
- `ContentRef`
- `FigureNotebookRef`
- `LessonRef`
- `PadRef`
- `PanelRef`
- `PreparingRef`
- `SourceRef`
- `SpanRange`
- `StackEntry`
- `Target`
- `TargetedRef`
- `ThreadRef`
- `VideoRef`
- `WireModel`

## Internal implementation anchors

- `_camel(name: str) -> str` ([source](../../../../../../src/learnloop/desks/content_ref.py), line 14)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]] — imports `ContentRef`, `StackEntry`, `WireModel`
- [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]] — imports `WireModel`
- [[Reference/Modules/learnloop/pads/ink|learnloop.pads.ink]] — imports `WireModel`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]], [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]], [[Reference/Modules/learnloop/pads/ink|learnloop.pads.ink]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rd_retire_migration.py](../../../../../../tests/test_reader_rd_retire_migration.py) — direct import
  - `test_a_preparing_window_names_its_source_alone`

## Modification guidance

- Make changes here when the responsibility remains content ref within learnloop.desks; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/desks/content_ref.py](../../../../../../src/learnloop/desks/content_ref.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
