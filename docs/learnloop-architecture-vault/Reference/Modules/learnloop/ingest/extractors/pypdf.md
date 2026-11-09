---
title: "learnloop.ingest.extractors.pypdf"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/extractors/pypdf.py"
source_paths:
  - "src/learnloop/ingest/extractors/pypdf.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ingest.extractors"
layer: "infrastructure"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
aliases:
  - "learnloop.ingest.extractors.pypdf module"
  - "src/learnloop/ingest/extractors/pypdf.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest-extractors"
---

# `learnloop.ingest.extractors.pypdf`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.extractors.pypdf` exists within [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] to own the behavior summarized by its module contract: Lightweight native-text PDF fallback (spec_source_ingestion_v2 §2.9).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/extractors/pypdf.py](../../../../../../../src/learnloop/ingest/extractors/pypdf.py) |
| Source lines | 192 |
| Owning package | [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `read_embedded_outline(raw_bytes: bytes) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/ingest/extractors/pypdf.py), line 25) — Flatten a PDF's embedded outline (bookmarks) into ToC-shaped entries.
- `class PyPdfExtractionError(ValueError)` ([source](../../../../../../../src/learnloop/ingest/extractors/pypdf.py), line 67)
- `class PyPdfDocumentExtractor` ([source](../../../../../../../src/learnloop/ingest/extractors/pypdf.py), line 83)
  - `version(self) -> str` (line 91; public)
  - `model_versions(self) -> dict[str, str]` (line 100; public)
  - `extract(self, raw_bytes: bytes, context: ExtractionContext) -> DocumentIR` (line 103; public)

### Module constants

- `EXTRACTOR_NAME` ([src/learnloop/ingest/extractors/pypdf.py](../../../../../../../src/learnloop/ingest/extractors/pypdf.py), line 22)
- `_SURROGATES` ([src/learnloop/ingest/extractors/pypdf.py](../../../../../../../src/learnloop/ingest/extractors/pypdf.py), line 80)

## Internal implementation anchors

- `_valid_text(text: str) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/pypdf.py), line 71) — pypdf can return lone UTF-16 surrogates for unmapped maths-font glyphs (seen on an arXiv paper's equations); they cannot be encoded, hashed or stored, so each becomes U+FFFD.
- `_pdf_title(raw_bytes: bytes) -> str | None` ([source](../../../../../../../src/learnloop/ingest/extractors/pypdf.py), line 185)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ingest/extractors/__init__|learnloop.ingest.extractors]] — imports `PyPdfDocumentExtractor`, `PyPdfExtractionError`, `read_embedded_outline`; statically calls `PyPdfDocumentExtractor`
- [[Reference/Modules/learnloop/ingest/extractors/datalab|learnloop.ingest.extractors.datalab]] — imports `read_embedded_outline`; statically calls `read_embedded_outline`
- [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]] — imports `read_embedded_outline`; statically calls `read_embedded_outline`
- [[Reference/Modules/learnloop/ingest/extractors/marker_worker|learnloop.ingest.extractors.marker_worker]] — imports `read_embedded_outline`; statically calls `read_embedded_outline`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ingest/block_roles|learnloop.ingest.block_roles]] — imports `classify_block_role`; calls `classify_block_role`
- [[Reference/Modules/learnloop/ingest/extractors/base|learnloop.ingest.extractors.base]] — imports `ExtractionContext`, `single_unit_from_blocks`, `units_from_toc_entries`; calls `single_unit_from_blocks`, `units_from_toc_entries`
- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `DocumentBlock`, `DocumentIR`, `IR_SCHEMA_VERSION`, `block_content_hash`; calls `DocumentBlock`, `DocumentIR`, `block_content_hash`

### Platform and third-party dependencies

- Standard library: `__future__`, `importlib`, `io`, `re`, `typing`
- Third party: `pypdf`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/ingest/extractors/__init__|learnloop.ingest.extractors]], [[Reference/Modules/learnloop/ingest/extractors/datalab|learnloop.ingest.extractors.datalab]], [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]], [[Reference/Modules/learnloop/ingest/extractors/marker_worker|learnloop.ingest.extractors.marker_worker]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_document_ir.py](../../../../../../../tests/test_document_ir.py) — direct import
  - `test_pypdf_extractor_builds_units_from_embedded_outline`
  - `test_read_embedded_outline_flattens_nested_bookmarks`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/extractors/pypdf.py](../../../../../../../src/learnloop/ingest/extractors/pypdf.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
