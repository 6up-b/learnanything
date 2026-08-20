---
title: "learnloop.ingest.ir"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/ir.py"
source_paths:
  - "src/learnloop/ingest/ir.py"
source_commit: "6dbc33492bec63ee162f57e470bf9296c9abe814"
source_commit_timestamp: "2026-07-14T02:19:57-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop.ingest"
layer: "infrastructure"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
aliases:
  - "learnloop.ingest.ir module"
  - "src/learnloop/ingest/ir.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest"
---

# `learnloop.ingest.ir`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.ir` exists within [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] to own the behavior summarized by its module contract: Document Intermediate Representation (IR) — the common source-layer contract.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/ir.py](../../../../../../src/learnloop/ingest/ir.py) |
| Source lines | 347 |
| Owning package | [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `6dbc33492bec63ee162f57e470bf9296c9abe814` |
| Commit timestamp | `2026-07-14T02:19:57-04:00` |

## Public API

- `block_content_hash(text: str) -> str` ([source](../../../../../../src/learnloop/ingest/ir.py), line 26) — Per-block content hash over the block's normalized text (§2.3).
- `class DocumentBlock(BaseModel)` ([source](../../../../../../src/learnloop/ingest/ir.py), line 32) — A span-addressable block within one ExtractionRun (§2.3).
  - `build(cls, *, span_id: str, block_type: str, text: str, ordinal: int, extractor_block_id: str | None=None, role_hint: str | None=None, page: int | None=None, bbox: list[float] | None=None, polygon: list[list[float]] | None=None, section_path: list[str] | None=None, asset_ids: list[str] | None=None) -> DocumentBlock` (line 55; public)
- `class DocumentUnit(BaseModel)` ([source](../../../../../../src/learnloop/ingest/ir.py), line 86) — A chapter/section with a stable id, label, and (paged) page range (§2.3).
- `class DocumentAsset(BaseModel)` ([source](../../../../../../src/learnloop/ingest/ir.py), line 102) — An extracted figure/image asset with citation context (§2.7).
- `class PageHealth(BaseModel)` ([source](../../../../../../src/learnloop/ingest/ir.py), line 117) — Per-page extraction-quality signals (§2.5, from marker ``page_stats``).
- `class ExtractionHealth(BaseModel)` ([source](../../../../../../src/learnloop/ingest/ir.py), line 128) — Aggregated extraction-health signals across the run (§2.3/§2.5).
  - `flagged_pages(self) -> list[int]` (line 136; public)
- `class DocumentIR(BaseModel)` ([source](../../../../../../src/learnloop/ingest/ir.py), line 140) — The full extractor output: blocks, units, assets, and health (§2.3).
  - `block_by_span(self, span_id: str) -> DocumentBlock | None` (line 153; public)
  - `unit_blocks(self, unit_id: str) -> list[DocumentBlock]` (line 159; public)
- `compose_extraction_runs(parent: DocumentIR, repair: DocumentIR) -> DocumentIR` ([source](../../../../../../src/learnloop/ingest/ir.py), line 167) — Deterministically compose a parent run with a targeted repair run (§2.3).
- `render_ir_markdown(ir: DocumentIR, *, selected_unit_ids: Sequence[str] | None=None) -> str` ([source](../../../../../../src/learnloop/ingest/ir.py), line 308) — Deterministic markdown rendering of a Document IR (§2.3).

### Module constants

- `IR_SCHEMA_VERSION` ([src/learnloop/ingest/ir.py](../../../../../../src/learnloop/ingest/ir.py), line 23)
- `_VERBATIM_BLOCK_TYPES` ([src/learnloop/ingest/ir.py](../../../../../../src/learnloop/ingest/ir.py), line 244)
- `_FIGURE_BLOCK_TYPES` ([src/learnloop/ingest/ir.py](../../../../../../src/learnloop/ingest/ir.py), line 253)

## Internal implementation anchors

- `_unit_touches_pages(unit: DocumentUnit, pages: set[int]) -> bool` ([source](../../../../../../src/learnloop/ingest/ir.py), line 224)
- `_normalized_block_type(block_type: str | None) -> str` ([source](../../../../../../src/learnloop/ingest/ir.py), line 256)
- `_meaningful_section_path(section_path: Sequence[str]) -> list[str]` ([source](../../../../../../src/learnloop/ingest/ir.py), line 260) — Drop the synthetic ``root`` segment; keep real heading segments.
- `_emit_headings(lines: list[str], emitted: list[str], section_path: Sequence[str]) -> list[str]` ([source](../../../../../../src/learnloop/ingest/ir.py), line 266) — Emit markdown headings for the newly-entered section segments.
- `_figure_placeholder(block: DocumentBlock, assets: dict[str, DocumentAsset]) -> str` ([source](../../../../../../src/learnloop/ingest/ir.py), line 288)
- `_render_block(block: DocumentBlock, assets: dict[str, DocumentAsset]) -> str` ([source](../../../../../../src/learnloop/ingest/ir.py), line 298)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `IR_SCHEMA_VERSION`, `compose_extraction_runs`, `render_ir_markdown`; statically calls `compose_extraction_runs`, `render_ir_markdown`
- [[Reference/Modules/learnloop/content/sources/block_health|learnloop.content.sources.block_health]] — imports `DocumentBlock`, `PageHealth`
- [[Reference/Modules/learnloop/content/sources/extraction_health|learnloop.content.sources.extraction_health]] — imports `DocumentIR`
- [[Reference/Modules/learnloop/content/sources/pdf_extraction|learnloop.content.sources.pdf_extraction]] — imports `IR_SCHEMA_VERSION`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `DocumentIR`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `DocumentIR`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] — imports `DocumentIR`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `DocumentAsset`, `DocumentBlock`, `DocumentIR`, `DocumentUnit`, `ExtractionHealth`; statically calls `DocumentAsset`, `DocumentBlock`, `DocumentIR`, `DocumentUnit`
- [[Reference/Modules/learnloop/ingest/extractors/base|learnloop.ingest.extractors.base]] — imports `DocumentBlock`, `DocumentUnit`; statically calls `DocumentUnit`
- [[Reference/Modules/learnloop/ingest/extractors/marker|learnloop.ingest.extractors.marker]] — imports `DocumentAsset`, `DocumentBlock`, `DocumentIR`, `DocumentUnit`, `ExtractionHealth`, `IR_SCHEMA_VERSION`, `PageHealth`, `block_content_hash`; statically calls `DocumentAsset`, `DocumentBlock`, `DocumentIR`, `ExtractionHealth`, `PageHealth`, `block_content_hash`
- [[Reference/Modules/learnloop/ingest/extractors/normalizers|learnloop.ingest.extractors.normalizers]] — imports `DocumentBlock`, `DocumentIR`, `DocumentUnit`, `IR_SCHEMA_VERSION`, `block_content_hash`; statically calls `DocumentBlock`, `DocumentIR`, `DocumentUnit`, `block_content_hash`
- [[Reference/Modules/learnloop/ingest/extractors/pypdf|learnloop.ingest.extractors.pypdf]] — imports `DocumentBlock`, `DocumentIR`, `IR_SCHEMA_VERSION`, `block_content_hash`; statically calls `DocumentBlock`, `DocumentIR`, `block_content_hash`
- [[Reference/Modules/learnloop/ingest/hashing|learnloop.ingest.hashing]] — imports `DocumentBlock`, `DocumentIR`
- [[Reference/Modules/learnloop/ingest/reanchor|learnloop.ingest.reanchor]] — imports `DocumentBlock`, `DocumentIR`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `render_ir_markdown`; statically calls `render_ir_markdown`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/sources/block_health|learnloop.content.sources.block_health]], [[Reference/Modules/learnloop/content/sources/extraction_health|learnloop.content.sources.extraction_health]], [[Reference/Modules/learnloop/content/sources/pdf_extraction|learnloop.content.sources.pdf_extraction]], [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] and 10 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_annotations.py](../../../../../../tests/test_annotations.py) — direct import
  - `test_duplicate_quote_uses_context_or_needs_reanchor`
  - `test_duplicate_quote_with_glyph_context_anchors_the_right_occurrence`
  - `test_glyph_quote_with_divergent_math_anchors_fuzzy`
  - `test_reanchor_across_reextraction_preserves_old_anchor`
  - `test_removed_block_never_silently_steals_annotation`
  - `test_review_volume_budget_parks_over_budget`
  - `test_whitespace_normalized_match_still_requires_uniqueness`
- [tests/test_coldness_receipt.py](../../../../../../tests/test_coldness_receipt.py) — direct import
  - `test_prescribe_handler_records_the_delivery`
- [tests/test_document_ir.py](../../../../../../tests/test_document_ir.py) — direct import
  - `test_document_ir_round_trip`
  - `test_ir_declares_schema_version`
  - `test_repair_composition_replaces_only_repaired_pages`
  - `test_request_hash_computable_before_execution_and_versioned`
  - `test_result_hash_depends_on_request_and_ir`
  - `test_semantic_hash_stable_under_cosmetic_html_changes`
- [tests/test_effective_units.py](../../../../../../tests/test_effective_units.py) — direct import
- [tests/test_ingest_jobs.py](../../../../../../tests/test_ingest_jobs.py) — direct import
- [tests/test_ingest_m3.py](../../../../../../tests/test_ingest_m3.py) — direct import
  - `test_extraction_health_flags_image_only_and_replacement_chars`
  - `test_extraction_health_flags_method_differs_from_neighbors`
  - `test_repair_requires_explicit_consent`
  - `test_targeted_repair_records_consent_and_preserves_unaffected_hashes`
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_import_cache_hit_skips_extractor_and_restores_health`
  - `test_import_retry_replaces_ir_left_by_interrupted_run`
- [tests/test_p3_journeys.py](../../../../../../tests/test_p3_journeys.py) — direct import
  - `test_annotation_survival_across_reextraction`
- [tests/test_pdf_extraction.py](../../../../../../tests/test_pdf_extraction.py) — direct import
  - `test_marker_cache_fingerprint_includes_ir_schema_version`
- [tests/test_primed_attempts.py](../../../../../../tests/test_primed_attempts.py) — direct import
  - `test_feedback_resolves_current_ingest_span_and_filename`
- [tests/test_reader_capture.py](../../../../../../tests/test_reader_capture.py) — direct import
- [tests/test_reader_dialogue.py](../../../../../../tests/test_reader_dialogue.py) — direct import
- [tests/test_reader_guidance.py](../../../../../../tests/test_reader_guidance.py) — direct import
- [tests/test_reader_render_views.py](../../../../../../tests/test_reader_render_views.py) — direct import
  - `test_block_health_statuses_and_recommended_views`
  - `test_reextraction_changes_render_version_not_content_hash_bytes`
- [tests/test_reader_requests.py](../../../../../../tests/test_reader_requests.py) — direct import
- [tests/test_reader_restoration.py](../../../../../../tests/test_reader_restoration.py) — direct import
  - `test_orphaned_annotation_shows_quote_without_false_attachment`
- [tests/test_sidecar_ingest_m3.py](../../../../../../tests/test_sidecar_ingest_m3.py) — direct import
- [tests/test_sidecar_quick_add.py](../../../../../../tests/test_sidecar_quick_add.py) — direct import
- [tests/test_sidecar_reader.py](../../../../../../tests/test_sidecar_reader.py) — direct import
- [tests/test_sidecar_reader_p3.py](../../../../../../tests/test_sidecar_reader_p3.py) — direct import
- [tests/test_sidecar_span_view.py](../../../../../../tests/test_sidecar_span_view.py) — direct import
- [tests/test_source_deletion.py](../../../../../../tests/test_source_deletion.py) — direct import
- [tests/test_source_ingestion_v2lite.py](../../../../../../tests/test_source_ingestion_v2lite.py) — direct import
  - `test_render_ir_markdown_honors_sections_and_unit_selection`
- [tests/test_source_inventory.py](../../../../../../tests/test_source_inventory.py) — direct import
- [tests/test_source_layer.py](../../../../../../tests/test_source_layer.py) — direct import
  - `test_extraction_request_hash_unique_constraint`
  - `test_marker_adapter_maps_chunks_toc_stats_and_figures`
  - `test_persist_and_load_document_ir_round_trips`
  - `test_pypdf_fallback_produces_same_ir_contract`
  - `test_retry_keys_on_request_hash_before_result_exists`
- [tests/test_source_search.py](../../../../../../tests/test_source_search.py) — direct import
- [tests/test_span_reanchor.py](../../../../../../tests/test_span_reanchor.py) — direct import
  - `test_reanchor_aliases_persist`
- [tests/test_span_view.py](../../../../../../tests/test_span_view.py) — direct import
  - `test_span_view_text_anchor_mode_without_geometry`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/ir.py](../../../../../../src/learnloop/ingest/ir.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
