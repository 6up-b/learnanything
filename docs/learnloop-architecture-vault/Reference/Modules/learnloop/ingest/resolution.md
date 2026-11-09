---
title: "learnloop.ingest.resolution"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/resolution.py"
source_paths:
  - "src/learnloop/ingest/resolution.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ingest"
layer: "infrastructure"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
aliases:
  - "learnloop.ingest.resolution module"
  - "src/learnloop/ingest/resolution.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest"
---

# `learnloop.ingest.resolution`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps resolution behavior inside its owning package, [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]]. Its public surface centers on `ResolvedSource`, `is_arxiv_id`, `resolve_source`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/resolution.py](../../../../../../src/learnloop/ingest/resolution.py) |
| Source lines | 80 |
| Owning package | [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class ResolvedSource` ([source](../../../../../../src/learnloop/ingest/resolution.py), line 21) — One authoritative classification plus a fetchable source value.
- `is_arxiv_id(source: str) -> bool` ([source](../../../../../../src/learnloop/ingest/resolution.py), line 28)
- `resolve_source(source: str) -> ResolvedSource` ([source](../../../../../../src/learnloop/ingest/resolution.py), line 32)

### Module constants

- `_ARXIV_NEW` ([src/learnloop/ingest/resolution.py](../../../../../../src/learnloop/ingest/resolution.py), line 13)
- `_ARXIV_OLD` ([src/learnloop/ingest/resolution.py](../../../../../../src/learnloop/ingest/resolution.py), line 14)
- `_YOUTUBE_HOSTS` ([src/learnloop/ingest/resolution.py](../../../../../../src/learnloop/ingest/resolution.py), line 15)
- `_TEXT_SUFFIXES` ([src/learnloop/ingest/resolution.py](../../../../../../src/learnloop/ingest/resolution.py), line 16)
- `_AUDIO_SUFFIXES` ([src/learnloop/ingest/resolution.py](../../../../../../src/learnloop/ingest/resolution.py), line 17)

### Explicit exports

`__all__` declares:

- `ResolvedSource`
- `SourceCategory`
- `is_arxiv_id`
- `resolve_source`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/acquisition_preview|learnloop.content.pipeline.acquisition_preview]] — imports `resolve_source`; statically calls `resolve_source`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `resolve_source`; statically calls `resolve_source`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `resolve_source`; statically calls `resolve_source`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `ResolvedSource`, `resolve_source`; statically calls `resolve_source`
- [[Reference/Modules/learnloop/ingest/detect|learnloop.ingest.detect]] — imports `resolve_source`; statically calls `resolve_source`
- [[Reference/Modules/learnloop/ingest/fetchers|learnloop.ingest.fetchers]] — imports `resolve_source`; statically calls `resolve_source`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `resolve_source`; statically calls `resolve_source`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ingest/models|learnloop.ingest.models]] — imports `UnsupportedSourceError`; calls `UnsupportedSourceError`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `pathlib`, `re`, `typing`, `urllib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/acquisition_preview|learnloop.content.pipeline.acquisition_preview]], [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]], [[Reference/Modules/learnloop/ingest/detect|learnloop.ingest.detect]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_glm_ocr.py](../../../../../../tests/test_glm_ocr.py) — direct import
  - `test_an_image_import_needs_glm_and_reads_with_it`
- [tests/test_ingest_transcripts.py](../../../../../../tests/test_ingest_transcripts.py) — direct import
  - `test_resolution_classifies_caption_files_as_textfile`
- [tests/test_quick_add.py](../../../../../../tests/test_quick_add.py) — direct import
- [tests/test_reread_safety.py](../../../../../../tests/test_reread_safety.py) — direct import
  - `test_e1_the_reread_hands_the_import_the_stored_bytes_never_a_store_path`
- [tests/test_sidecar_quick_add.py](../../../../../../tests/test_sidecar_quick_add.py) — direct import
- [tests/test_source_retrieval_search.py](../../../../../../tests/test_source_retrieval_search.py) — direct import
  - `test_quick_add_with_retrieval_off_plans_exactly_as_before`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/resolution.py](../../../../../../src/learnloop/ingest/resolution.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
