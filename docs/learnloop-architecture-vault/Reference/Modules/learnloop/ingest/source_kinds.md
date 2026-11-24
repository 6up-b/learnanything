---
title: "learnloop.ingest.source_kinds"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/source_kinds.py"
source_paths:
  - "src/learnloop/ingest/source_kinds.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ingest"
layer: "infrastructure"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.ingest.source_kinds module"
  - "src/learnloop/ingest/source_kinds.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest"
---

# `learnloop.ingest.source_kinds`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.source_kinds` exists within [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] to own the behavior summarized by its module contract: What a source kind is, in one row: ``SOURCE_KINDS``.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/source_kinds.py](../../../../../../src/learnloop/ingest/source_kinds.py) |
| Source lines | 92 |
| Owning package | [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class SourceKind` ([source](../../../../../../src/learnloop/ingest/source_kinds.py), line 34)
- `source_kind(category: str | None) -> SourceKind` ([source](../../../../../../src/learnloop/ingest/source_kinds.py), line 86) — The row for ``category``; :data:`UNKNOWN_KIND` for one no row names.

### Module constants

- `SOURCE_KINDS` ([src/learnloop/ingest/source_kinds.py](../../../../../../src/learnloop/ingest/source_kinds.py), line 59)
- `UNKNOWN_KIND` ([src/learnloop/ingest/source_kinds.py](../../../../../../src/learnloop/ingest/source_kinds.py), line 82)

### Explicit exports

`__all__` declares:

- `Reader`
- `SOURCE_KINDS`
- `SourceCategory`
- `SourceKind`
- `UNKNOWN_KIND`
- `source_kind`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `source_kind`; statically calls `source_kind`
- [[Reference/Modules/learnloop/content/pipeline/import_jobs|learnloop.content.pipeline.import_jobs]] — imports `source_kind`; statically calls `source_kind`
- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `source_kind`; statically calls `source_kind`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `source_kind`; statically calls `source_kind`
- [[Reference/Modules/learnloop/ingest/resolution|learnloop.ingest.resolution]] — imports `SOURCE_KINDS`, `SourceCategory`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `source_kind`; statically calls `source_kind`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]], [[Reference/Modules/learnloop/content/pipeline/import_jobs|learnloop.content.pipeline.import_jobs]], [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]], [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]], [[Reference/Modules/learnloop/ingest/resolution|learnloop.ingest.resolution]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_kinds.py](../../../../../../tests/test_source_kinds.py) — direct import
  - `test_an_unnamed_category_reads_as_text_and_is_called_a_book`
  - `test_each_suffix_classifies_as_its_kind`
  - `test_every_category_has_one_row_in_the_literal_order`
  - `test_no_suffix_names_two_kinds`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/source_kinds.py](../../../../../../src/learnloop/ingest/source_kinds.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
