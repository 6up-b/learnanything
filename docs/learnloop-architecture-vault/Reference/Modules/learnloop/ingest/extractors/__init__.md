---
title: "learnloop.ingest.extractors"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/extractors/__init__.py"
source_paths:
  - "src/learnloop/ingest/extractors/__init__.py"
source_commit: "1c72cbabade1a4be2d2f4d18b22d1cf0ac171657"
source_commit_timestamp: "2026-07-22T21:17:05-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop.ingest.extractors"
layer: "infrastructure"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.ingest.extractors module"
  - "src/learnloop/ingest/extractors/__init__.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest-extractors"
---

# `learnloop.ingest.extractors`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.extractors` exists within [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] to own the behavior summarized by its module contract: Document extractor providers returning the LearnLoop IR (§2.9).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/extractors/__init__.py](../../../../../../../src/learnloop/ingest/extractors/__init__.py) |
| Source lines | 88 |
| Owning package | [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1c72cbabade1a4be2d2f4d18b22d1cf0ac171657` |
| Commit timestamp | `2026-07-22T21:17:05-04:00` |

## Public API

- `pdf_extractor_for(config: dict | None=None) -> DocumentExtractor` ([source](../../../../../../../src/learnloop/ingest/extractors/__init__.py), line 57) — Select the PDF extractor (§2.9).

### Explicit exports

`__all__` declares:

- `DocumentExtractor`
- `DatalabDocumentExtractor`
- `DatalabExtractionError`
- `ExtractionContext`
- `MarkerDocumentExtractor`
- `MarkerUnavailableError`
- `PyPdfDocumentExtractor`
- `PyPdfExtractionError`
- `captions_to_ir`
- `chunk_output_to_ir`
- `markdown_to_ir`
- `marker_available`
- `marker_package_version`
- `read_embedded_outline`
- `single_unit_from_blocks`
- `transcript_to_ir`
- `units_from_toc_entries`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/acquisition_preview|learnloop.content.pipeline.acquisition_preview]] — imports `marker_available`; statically calls `marker_available`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `MarkerUnavailableError`, `PyPdfDocumentExtractor`, `captions_to_ir`, `markdown_to_ir`, `pdf_extractor_for`, `transcript_to_ir`; statically calls `PyPdfDocumentExtractor`, `captions_to_ir`, `markdown_to_ir`, `pdf_extractor_for`, `transcript_to_ir`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ingest/extractors/base|learnloop.ingest.extractors.base]] — imports `DocumentExtractor`, `ExtractionContext`, `single_unit_from_blocks`, `units_from_toc_entries`
- [[Reference/Modules/learnloop/ingest/extractors/datalab|learnloop.ingest.extractors.datalab]] — imports `DATALAB_API_KEY_ENV`, `DatalabDocumentExtractor`, `DatalabExtractionError`, `datalab_api_key`; calls `DatalabDocumentExtractor`, `datalab_api_key`
- [[Reference/Modules/learnloop/ingest/extractors/marker|learnloop.ingest.extractors.marker]] — imports `MarkerDocumentExtractor`, `MarkerUnavailableError`, `chunk_output_to_ir`, `marker_available`, `marker_package_version`; calls `MarkerDocumentExtractor`, `MarkerUnavailableError`, `marker_available`
- [[Reference/Modules/learnloop/ingest/extractors/normalizers|learnloop.ingest.extractors.normalizers]] — imports `captions_to_ir`, `markdown_to_ir`, `transcript_to_ir`
- [[Reference/Modules/learnloop/ingest/extractors/pypdf|learnloop.ingest.extractors.pypdf]] — imports `PyPdfDocumentExtractor`, `PyPdfExtractionError`, `read_embedded_outline`; calls `PyPdfDocumentExtractor`

### Platform and third-party dependencies

- Standard library: `__future__`, `os`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/acquisition_preview|learnloop.content.pipeline.acquisition_preview]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_layer.py](../../../../../../../tests/test_source_layer.py) — direct import
  - `test_missing_marker_degrades_explicitly`
  - `test_non_pdf_normalizers_emit_trivial_ir`
  - `test_pypdf_fallback_extracts_only_selected_original_pages`
  - `test_pypdf_fallback_produces_same_ir_contract`
  - `test_pypdf_fallback_rejects_page_range_past_document_end`

## Modification guidance

- Change this file when intentionally adding or removing a package-level re-export; keep implementation logic in the owning module.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/extractors/__init__.py](../../../../../../../src/learnloop/ingest/extractors/__init__.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
