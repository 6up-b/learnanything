---
title: "learnloop.ingest.ir"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/ir.py"
source_paths:
  - "src/learnloop/ingest/ir.py"
source_commit: "93df11dc9fc1f412f0ee3d84a893ccfa89288cf2"
source_commit_timestamp: "2026-10-25T17:27:01-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
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
| Source lines | 396 |
| Owning package | [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `93df11dc9fc1f412f0ee3d84a893ccfa89288cf2` |
| Commit timestamp | `2026-10-25T17:27:01-04:00` |

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
- `is_figure_block(block: DocumentBlock) -> bool` ([source](../../../../../../src/learnloop/ingest/ir.py), line 260) — A figure (or picture/image) block, by its type or its role hint: the one test the Markdown rendering and the problem as printed share.
- `page_region(value: object) -> tuple[int, tuple[float, float, float, float]] | None` ([source](../../../../../../src/learnloop/ingest/ir.py), line 268) — A box on one page, ``{page, bbox}`` (a learner-drawn region, Reader CA1 §12.4), normalised to ``(page, (left, top, right, bottom))``; None when malformed or empty.
- `selection_region(value: object, span_ids: Sequence[str]) -> dict[str, tuple[int, tuple[float, float, float, float]]]` ([source](../../../../../../src/learnloop/ingest/ir.py), line 290) — A selection's ``region`` (``spanId``/``span_id``, page, box) keyed by its span; nothing when it names a block outside ``span_ids`` or is malformed.
- `render_ir_markdown(ir: DocumentIR, *, selected_unit_ids: Sequence[str] | None=None) -> str` ([source](../../../../../../src/learnloop/ingest/ir.py), line 353) — Deterministic markdown rendering of a Document IR (§2.3).

### Module constants

- `IR_SCHEMA_VERSION` ([src/learnloop/ingest/ir.py](../../../../../../src/learnloop/ingest/ir.py), line 23)
- `_VERBATIM_BLOCK_TYPES` ([src/learnloop/ingest/ir.py](../../../../../../src/learnloop/ingest/ir.py), line 244)
- `_FIGURE_BLOCK_TYPES` ([src/learnloop/ingest/ir.py](../../../../../../src/learnloop/ingest/ir.py), line 253)

## Internal implementation anchors

- `_unit_touches_pages(unit: DocumentUnit, pages: set[int]) -> bool` ([source](../../../../../../src/learnloop/ingest/ir.py), line 224)
- `_normalized_block_type(block_type: str | None) -> str` ([source](../../../../../../src/learnloop/ingest/ir.py), line 256)
- `_meaningful_section_path(section_path: Sequence[str]) -> list[str]` ([source](../../../../../../src/learnloop/ingest/ir.py), line 306) — Drop the synthetic ``root`` segment; keep real heading segments.
- `_emit_headings(lines: list[str], emitted: list[str], section_path: Sequence[str]) -> list[str]` ([source](../../../../../../src/learnloop/ingest/ir.py), line 312) — Emit markdown headings for the newly-entered section segments.
- `_figure_placeholder(block: DocumentBlock, assets: dict[str, DocumentAsset]) -> str` ([source](../../../../../../src/learnloop/ingest/ir.py), line 334)
- `_render_block(block: DocumentBlock, assets: dict[str, DocumentAsset]) -> str` ([source](../../../../../../src/learnloop/ingest/ir.py), line 344)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `is_figure_block`, `selection_region`; statically calls `is_figure_block`, `selection_region`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `IR_SCHEMA_VERSION`, `compose_extraction_runs`, `render_ir_markdown`; statically calls `compose_extraction_runs`, `render_ir_markdown`
- [[Reference/Modules/learnloop/content/sources/block_health|learnloop.content.sources.block_health]] — imports `DocumentBlock`, `PageHealth`
- [[Reference/Modules/learnloop/content/sources/extraction_health|learnloop.content.sources.extraction_health]] — imports `DocumentIR`
- [[Reference/Modules/learnloop/content/sources/pdf_extraction|learnloop.content.sources.pdf_extraction]] — imports `IR_SCHEMA_VERSION`, `render_ir_markdown`; statically calls `render_ir_markdown`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `DocumentIR`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `DocumentIR`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] — imports `DocumentIR`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `DocumentAsset`, `DocumentBlock`, `DocumentIR`, `DocumentUnit`, `ExtractionHealth`; statically calls `DocumentAsset`, `DocumentBlock`, `DocumentIR`, `DocumentUnit`
- [[Reference/Modules/learnloop/ingest/extractors/base|learnloop.ingest.extractors.base]] — imports `DocumentBlock`, `DocumentUnit`; statically calls `DocumentUnit`
- [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]] — imports `DocumentBlock`, `DocumentIR`, `DocumentUnit`, `IR_SCHEMA_VERSION`, `PageHealth`; statically calls `DocumentIR`, `DocumentUnit`, `PageHealth`
- [[Reference/Modules/learnloop/ingest/extractors/marker|learnloop.ingest.extractors.marker]] — imports `DocumentAsset`, `DocumentBlock`, `DocumentIR`, `DocumentUnit`, `ExtractionHealth`, `IR_SCHEMA_VERSION`, `PageHealth`, `block_content_hash`; statically calls `DocumentAsset`, `DocumentBlock`, `DocumentIR`, `ExtractionHealth`, `PageHealth`, `block_content_hash`
- [[Reference/Modules/learnloop/ingest/extractors/normalizers|learnloop.ingest.extractors.normalizers]] — imports `DocumentBlock`, `DocumentIR`, `DocumentUnit`, `IR_SCHEMA_VERSION`, `block_content_hash`; statically calls `DocumentBlock`, `DocumentIR`, `DocumentUnit`, `block_content_hash`
- [[Reference/Modules/learnloop/ingest/extractors/pypdf|learnloop.ingest.extractors.pypdf]] — imports `DocumentBlock`, `DocumentIR`, `IR_SCHEMA_VERSION`, `block_content_hash`; statically calls `DocumentBlock`, `DocumentIR`, `block_content_hash`
- [[Reference/Modules/learnloop/ingest/hashing|learnloop.ingest.hashing]] — imports `DocumentBlock`, `DocumentIR`
- [[Reference/Modules/learnloop/ingest/reanchor|learnloop.ingest.reanchor]] — imports `DocumentBlock`, `DocumentIR`
- [[Reference/Modules/learnloop/reader/as_printed|learnloop.reader.as_printed]] — imports `DocumentBlock`, `is_figure_block`, `page_region`, `selection_region`; statically calls `is_figure_block`, `page_region`, `selection_region`
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

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/sources/block_health|learnloop.content.sources.block_health]], [[Reference/Modules/learnloop/content/sources/extraction_health|learnloop.content.sources.extraction_health]], [[Reference/Modules/learnloop/content/sources/pdf_extraction|learnloop.content.sources.pdf_extraction]] and 13 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/e0_fakes.py](../../../../../../tests/e0_fakes.py) — direct import
- [tests/exam_scope_fixtures.py](../../../../../../tests/exam_scope_fixtures.py) — direct import
- [tests/figure_fixtures.py](../../../../../../tests/figure_fixtures.py) — direct import
- [tests/helpers.py](../../../../../../tests/helpers.py) — direct import
- [tests/reader_fixtures.py](../../../../../../tests/reader_fixtures.py) — direct import
- [tests/source_retrieval_fakes.py](../../../../../../tests/source_retrieval_fakes.py) — direct import
- [tests/source_service_fakes.py](../../../../../../tests/source_service_fakes.py) — direct import
- [tests/test_ad1_reading_opportunities.py](../../../../../../tests/test_ad1_reading_opportunities.py) — direct import
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
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
- [tests/test_daily_loop_reader_authored_practice.py](../../../../../../tests/test_daily_loop_reader_authored_practice.py) — direct import
- [tests/test_daily_plan_reading.py](../../../../../../tests/test_daily_plan_reading.py) — direct import
- [tests/test_document_ir.py](../../../../../../tests/test_document_ir.py) — direct import
  - `test_document_ir_round_trip`
  - `test_ir_declares_schema_version`
  - `test_repair_composition_replaces_only_repaired_pages`
  - `test_request_hash_computable_before_execution_and_versioned`
  - `test_result_hash_depends_on_request_and_ir`
  - `test_semantic_hash_stable_under_cosmetic_html_changes`
- [tests/test_effective_units.py](../../../../../../tests/test_effective_units.py) — direct import
- [tests/test_exam_protection_identity.py](../../../../../../tests/test_exam_protection_identity.py) — direct import
- [tests/test_facet_reword_confirm.py](../../../../../../tests/test_facet_reword_confirm.py) — direct import
- [tests/test_glm_ocr.py](../../../../../../tests/test_glm_ocr.py) — direct import
  - `test_auto_falls_back_on_a_glm_failure_but_never_past_a_refusal`
  - `test_regions_map_to_blocks_in_reading_order_with_roles_text_and_point_boxes`
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
- [tests/test_reader_ca1_as_printed.py](../../../../../../tests/test_reader_ca1_as_printed.py) — direct import
  - `test_a_block_without_a_page_or_a_box_crops_nothing`
- [tests/test_reader_ca1_astra_codex_review.py](../../../../../../tests/test_reader_ca1_astra_codex_review.py) — direct import
- [tests/test_reader_ca1_astra_fixes.py](../../../../../../tests/test_reader_ca1_astra_fixes.py) — direct import
- [tests/test_reader_ca1_astra_redesign.py](../../../../../../tests/test_reader_ca1_astra_redesign.py) — direct import
  - `test_f6_crop_boxes_returns_one_crop_per_retained_region`
- [tests/test_reader_ca1_astra_rereview.py](../../../../../../tests/test_reader_ca1_astra_rereview.py) — direct import
- [tests/test_reader_ca1_codex_review.py](../../../../../../tests/test_reader_ca1_codex_review.py) — direct import
  - `test_a_figure_only_crop_never_takes_in_the_stem_beside_it`
  - `test_a_page_known_without_a_box_offers_the_original_page_and_no_substitute_crop`
- [tests/test_reader_ca1_unicode_containment.py](../../../../../../tests/test_reader_ca1_unicode_containment.py) — direct import
- [tests/test_reader_capture.py](../../../../../../tests/test_reader_capture.py) — direct import
- [tests/test_reader_cues.py](../../../../../../tests/test_reader_cues.py) — direct import
- [tests/test_reader_dialogue.py](../../../../../../tests/test_reader_dialogue.py) — direct import
- [tests/test_reader_guidance.py](../../../../../../tests/test_reader_guidance.py) — direct import
- [tests/test_reader_pdf_selection.py](../../../../../../tests/test_reader_pdf_selection.py) — direct import
- [tests/test_reader_render_views.py](../../../../../../tests/test_reader_render_views.py) — direct import
  - `test_block_health_statuses_and_recommended_views`
  - `test_reextraction_changes_render_version_not_content_hash_bytes`
- [tests/test_reader_requests.py](../../../../../../tests/test_reader_requests.py) — direct import
- [tests/test_reader_restoration.py](../../../../../../tests/test_reader_restoration.py) — direct import
  - `test_orphaned_annotation_shows_quote_without_false_attachment`
- [tests/test_reader_source_identity_guard.py](../../../../../../tests/test_reader_source_identity_guard.py) — direct import
- [tests/test_required_method_authority.py](../../../../../../tests/test_required_method_authority.py) — direct import
- [tests/test_required_method_items.py](../../../../../../tests/test_required_method_items.py) — direct import
- [tests/test_reread_safety.py](../../../../../../tests/test_reread_safety.py) — direct import
- [tests/test_reread_safety_landing.py](../../../../../../tests/test_reread_safety_landing.py) — direct import
  - `test_a_cue_on_a_reread_resolves_the_cited_passage_and_shows_the_question_with_its_method`
- [tests/test_sidecar_ingest_m3.py](../../../../../../tests/test_sidecar_ingest_m3.py) — direct import
- [tests/test_sidecar_quick_add.py](../../../../../../tests/test_sidecar_quick_add.py) — direct import
- [tests/test_sidecar_reader.py](../../../../../../tests/test_sidecar_reader.py) — direct import
- [tests/test_sidecar_reader_p3.py](../../../../../../tests/test_sidecar_reader_p3.py) — direct import
- [tests/test_sidecar_span_view.py](../../../../../../tests/test_sidecar_span_view.py) — direct import
- [tests/test_source_block_fts.py](../../../../../../tests/test_source_block_fts.py) — direct import
  - `test_replacing_a_runs_blocks_replaces_its_index_rows`
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
- [tests/test_source_retrieval_guards.py](../../../../../../tests/test_source_retrieval_guards.py) — direct import
- [tests/test_source_search.py](../../../../../../tests/test_source_search.py) — direct import
- [tests/test_source_vector_backfill.py](../../../../../../tests/test_source_vector_backfill.py) — direct import
- [tests/test_span_reanchor.py](../../../../../../tests/test_span_reanchor.py) — direct import
  - `test_reanchor_aliases_persist`
- [tests/test_span_view.py](../../../../../../tests/test_span_view.py) — direct import
  - `test_span_view_text_anchor_mode_without_geometry`
- [tests/test_t6_followup_rereview.py](../../../../../../tests/test_t6_followup_rereview.py) — direct import
- [tests/test_tutor_delivery_fixes.py](../../../../../../tests/test_tutor_delivery_fixes.py) — direct import
- [tests/test_ux_phase1_round2_review.py](../../../../../../tests/test_ux_phase1_round2_review.py) — direct import
- [tests/test_ux_phase1_usability_round1.py](../../../../../../tests/test_ux_phase1_usability_round1.py) — direct import
  - `test_u2_pdf_view_lists_each_passages_page_for_a_text_only_extraction`
- [tests/test_ux_phase3_today.py](../../../../../../tests/test_ux_phase3_today.py) — direct import

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/ir.py](../../../../../../src/learnloop/ingest/ir.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
