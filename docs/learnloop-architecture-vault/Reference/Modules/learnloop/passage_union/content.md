---
title: "learnloop.passage_union.content"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/passage_union/content.py"
source_paths:
  - "src/learnloop/passage_union/content.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.passage_union"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.passage_union.content module"
  - "src/learnloop/passage_union/content.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-passage-union"
---

# `learnloop.passage_union.content`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/passage_union/_package|learnloop.passage_union]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.passage_union.content` exists within [[Reference/Modules/learnloop/passage_union/_package|learnloop.passage_union]] to own the behavior summarized by its module contract: ``passage.content`` (spec §9.2 "a piece of another source", review finding 12): a range of one reading as the source has it, so a ``source_piece`` holds the source's words and never a search row's label.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/passage_union/content.py](../../../../../../src/learnloop/passage_union/content.py) |
| Source lines | 60 |
| Owning package | [[Reference/Modules/learnloop/passage_union/_package|learnloop.passage_union]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `passage_content(vault: Any, repository: Any, *, extraction_id: str, from_span_id: str | None=None, to_span_id: str | None=None, t0: float | None=None, t1: float | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/passage_union/content.py), line 30) — ``{extraction_id, source_id, title, withheld, spans: [{span_id, text, page, t0, t1, section_id, section_label, withheld}]}`` for one range (two passages, or two times over a transcript).

### Module constants

- `_CUE_TIME` ([src/learnloop/passage_union/content.py](../../../../../../src/learnloop/passage_union/content.py), line 18)

### Explicit exports

`__all__` declares:

- `passage_content`

## Internal implementation anchors

- `_title(repository: Any, source_id: str | None) -> str | None` ([source](../../../../../../src/learnloop/passage_union/content.py), line 21)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/passage_union|learnloop_sidecar.handlers.passage_union]] — imports `passage_content`; statically calls `passage_content`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_withheld`; calls `exam_withheld`
- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `reading_source`; calls `reading_source`
- [[Reference/Modules/learnloop/passage_union/union|learnloop.passage_union.union]] — imports `UnionError`, `span_range`; calls `UnionError`, `span_range`
- [[Reference/Modules/learnloop/section_map|learnloop.section_map]] — imports `extraction_sections`; calls `extraction_sections`

### Platform and third-party dependencies

- Standard library: `__future__`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/passage_union|learnloop_sidecar.handlers.passage_union]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_pad_stale_edits_stacks_and_passage_reads.py](../../../../../../tests/test_pad_stale_edits_stacks_and_passage_reads.py) — direct import
  - `test_a_passages_canonical_content_comes_with_its_title_location_and_time_apart`

## Modification guidance

- Make changes here when the responsibility remains content within learnloop.passage_union; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/passage_union/content.py](../../../../../../src/learnloop/passage_union/content.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
