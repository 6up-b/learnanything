---
title: "learnloop.ingest.extractors.marker"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/extractors/marker.py"
source_paths:
  - "src/learnloop/ingest/extractors/marker.py"
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
  - "Import Canonical Sources"
aliases:
  - "learnloop.ingest.extractors.marker module"
  - "src/learnloop/ingest/extractors/marker.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest-extractors"
---

# `learnloop.ingest.extractors.marker`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.extractors.marker` exists within [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] to own the behavior summarized by its module contract: Marker adapter (spec_source_ingestion_v2 §2.3/§2.8/§2.9).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/extractors/marker.py](../../../../../../../src/learnloop/ingest/extractors/marker.py) |
| Source lines | 423 |
| Owning package | [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1c72cbabade1a4be2d2f4d18b22d1cf0ac171657` |
| Commit timestamp | `2026-07-22T21:17:05-04:00` |

## Public API

- `class MarkerUnavailableError(RuntimeError)` ([source](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 60) — Raised when marker is requested but not importable (§2.9 explicit fallback).
- `marker_available() -> bool` ([source](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 64)
- `marker_package_version() -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 68)
- `chunk_output_to_ir(*, blocks: list[Any], metadata: dict[str, Any] | None=None, page_info: dict[Any, Any] | None=None, extractor_version: str, document_title: str | None=None, embedded_outline: list[dict[str, Any]] | None=None) -> DocumentIR` ([source](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 162) — Pure marker ``ChunkOutput`` → :class:`DocumentIR` mapping (§2.3).
- `class MarkerDocumentExtractor` ([source](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 348) — High-fidelity local OCR/layout/math/table/figure extractor (§2.9).
  - `__init__(self, *, config: dict[str, Any] | None=None) -> None` (line 364; internal)
  - `version(self) -> str` (line 367; public)
  - `model_versions(self) -> dict[str, str]` (line 370; public)
  - `extract(self, raw_bytes: bytes, context: ExtractionContext) -> DocumentIR` (line 382; public)
  - `_run_marker(self, raw_bytes: bytes, context: ExtractionContext) -> Any` (line 398; internal)

### Module constants

- `EXTRACTOR_NAME` ([src/learnloop/ingest/extractors/marker.py](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 38)
- `_SAFE_PDFTEXT_WORKERS` ([src/learnloop/ingest/extractors/marker.py](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 47)
- `_TAG_RE` ([src/learnloop/ingest/extractors/marker.py](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 49)
- `_WS_RE` ([src/learnloop/ingest/extractors/marker.py](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 50)
- `_VERBATIM_TYPES` ([src/learnloop/ingest/extractors/marker.py](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 51)
- `_BLOCK_ID_PAGE` ([src/learnloop/ingest/extractors/marker.py](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 93)
- `_MATH_TAG_RE` ([src/learnloop/ingest/extractors/marker.py](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 123)
- `_MATH_DISPLAY_BLOCK_RE` ([src/learnloop/ingest/extractors/marker.py](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 124)

## Internal implementation anchors

- `_marker_runtime_options(config: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 54)
- `_as_dict(block: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 77)
- `_block_page(block: dict[str, Any]) -> int | None` ([source](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 96) — Page index for a chunk block.
- `_section_path(section_hierarchy: dict | None) -> list[str]` ([source](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 115)
- `_math_to_delimited(html: str) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 127) — Marker encodes math as ``<math display='inline|block'>LaTeX</math>``.
- `_block_text(block_type: str, html: str) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 143)
- `_unescape(text: str) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 151)
- `_units_from_toc(toc: list[Any] | None, blocks: list[DocumentBlock], *, document_title: str | None, embedded_outline: list[dict[str, Any]] | None=None) -> list[DocumentUnit]` ([source](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 244) — Units from the best available section source.
- `_health_from_page_stats(page_stats: list[Any] | None, blocks: list[DocumentBlock]) -> ExtractionHealth` ([source](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 279)
- `_normalize_counts(block_counts: Any) -> dict[str, int]` ([source](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 322)
- `_page_flags(counts: dict[str, int], blocks: list[DocumentBlock], page_id: Any) -> list[str]` ([source](../../../../../../../src/learnloop/ingest/extractors/marker.py), line 333)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ingest/extractors/__init__|learnloop.ingest.extractors]] — imports `MarkerDocumentExtractor`, `MarkerUnavailableError`, `chunk_output_to_ir`, `marker_available`, `marker_package_version`; statically calls `MarkerDocumentExtractor`, `MarkerUnavailableError`, `marker_available`
- [[Reference/Modules/learnloop/ingest/extractors/datalab|learnloop.ingest.extractors.datalab]] — imports `MarkerUnavailableError`, `chunk_output_to_ir`; statically calls `MarkerUnavailableError`, `chunk_output_to_ir`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ingest/block_roles|learnloop.ingest.block_roles]] — imports `classify_block_role`; calls `classify_block_role`
- [[Reference/Modules/learnloop/ingest/extractors/base|learnloop.ingest.extractors.base]] — imports `ExtractionContext`, `units_from_toc_entries`; calls `units_from_toc_entries`
- [[Reference/Modules/learnloop/ingest/extractors/pypdf|learnloop.ingest.extractors.pypdf]] — imports `read_embedded_outline`; calls `read_embedded_outline`
- [[Reference/Modules/learnloop/ingest/hashing|learnloop.ingest.hashing]] — imports `semantic_hash`
- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `DocumentAsset`, `DocumentBlock`, `DocumentIR`, `DocumentUnit`, `ExtractionHealth`, `IR_SCHEMA_VERSION`, `PageHealth`, `block_content_hash`; calls `DocumentAsset`, `DocumentBlock`, `DocumentIR`, `ExtractionHealth`, `PageHealth`, `block_content_hash`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `importlib`, `os`, `pathlib`, `re`, `tempfile`, `typing`
- Third party: `marker`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/ingest/extractors/__init__|learnloop.ingest.extractors]], [[Reference/Modules/learnloop/ingest/extractors/datalab|learnloop.ingest.extractors.datalab]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_document_ir.py](../../../../../../../tests/test_document_ir.py) — direct import
  - `test_embedded_outline_preferred_over_detected_toc`
  - `test_marker_block_page_derived_from_block_id`
  - `test_marker_image_keys_coerced_to_string_asset_ids`
  - `test_repair_composition_replaces_only_repaired_pages`
  - `test_single_entry_outline_falls_back_to_detected_toc`
- [tests/test_source_layer.py](../../../../../../../tests/test_source_layer.py) — direct import
  - `test_marker_adapter_defaults_pdftext_to_one_worker`
  - `test_marker_adapter_maps_chunks_toc_stats_and_figures`
  - `test_marker_adapter_preserves_explicit_pdftext_worker_override`
  - `test_marker_semantic_hash_stable_under_cosmetic_html`
  - `test_missing_marker_degrades_explicitly`
  - `test_persist_and_load_document_ir_round_trips`
  - `test_retry_keys_on_request_hash_before_result_exists`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/extractors/marker.py](../../../../../../../src/learnloop/ingest/extractors/marker.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
