---
title: "learnloop.ingest.extractors"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/extractors/__init__.py"
source_paths:
  - "src/learnloop/ingest/extractors/__init__.py"
generated: true
generated_at: "2026-11-02"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.extractors` exists within [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] to own the behavior summarized by its module contract: Document extractor providers returning the LearnLoop IR (§2.9).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/extractors/__init__.py](../../../../../../../src/learnloop/ingest/extractors/__init__.py) |
| Source lines | 211 |
| Owning package | [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class ExtractionFallbackFailed(RuntimeError)` ([source](../../../../../../../src/learnloop/ingest/extractors/__init__.py), line 72) — The chosen extractor failed and so did its local fallback.
- `class NativeEngineNotLocalError(ValueError)` ([source](../../../../../../../src/learnloop/ingest/extractors/__init__.py), line 76) — ``engine = "native"`` reached the local extractor registry.
- `pdf_extractor_for(config: dict | None=None, *, local_only: bool=False) -> DocumentExtractor` ([source](../../../../../../../src/learnloop/ingest/extractors/__init__.py), line 84) — Select the document extractor (§2.9) for a PDF, PNG or JPG.
- `local_pdf_extractor(config: dict | None=None) -> DocumentExtractor` ([source](../../../../../../../src/learnloop/ingest/extractors/__init__.py), line 146) — What reads a PDF without it leaving this computer: local Marker when installed, else pypdf (never hosted Marker, which needs its own OK).
- `fallback_model_versions(extractor_name: str) -> dict[str, str]` ([source](../../../../../../../src/learnloop/ingest/extractors/__init__.py), line 154) — The model versions of the local extractor that stood in for the one chosen (:func:`extract_with_fallback`), for the stored extraction run.
- `extract_with_fallback(raw_bytes: bytes, extractor: DocumentExtractor, config: dict, context: ExtractionContext)` ([source](../../../../../../../src/learnloop/ingest/extractors/__init__.py), line 165) — Run ``extractor``; under ``engine = "auto"`` a runtime failure degrades to the next local extractor with a health flag naming why (§2.9).

### Explicit exports

`__all__` declares:

- `NativeEngineNotLocalError`
- `DocumentExtractor`
- `DatalabDocumentExtractor`
- `DatalabExtractionError`
- `ExtractionContext`
- `ExtractionFallbackFailed`
- `GlmOcrDocumentExtractor`
- `GlmOcrExtractionError`
- `MarkerDocumentExtractor`
- `MarkerUnavailableError`
- `PyPdfDocumentExtractor`
- `PyPdfExtractionError`
- `captions_to_ir`
- `chunk_output_to_ir`
- `extract_with_fallback`
- `fallback_model_versions`
- `local_pdf_extractor`
- `markdown_to_ir`
- `marker_available`
- `marker_package_version`
- `pdf_extractor_for`
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
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `datalab_api_key`, `marker_available`; statically calls `datalab_api_key`, `marker_available`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `ExtractionFallbackFailed`, `MarkerUnavailableError`, `captions_to_ir`, `extract_with_fallback`, `fallback_model_versions`, `local_pdf_extractor`, `markdown_to_ir`, `pdf_extractor_for`, `transcript_to_ir`; statically calls `captions_to_ir`, `extract_with_fallback`, `fallback_model_versions`, `local_pdf_extractor`, `markdown_to_ir`, `pdf_extractor_for`, `transcript_to_ir`
- [[Reference/Modules/learnloop/content/sources/pdf_extraction|learnloop.content.sources.pdf_extraction]] — imports `ExtractionContext`, `pdf_extractor_for`; statically calls `ExtractionContext`, `pdf_extractor_for`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCancelled`, `SpendLimitExceeded`
- [[Reference/Modules/learnloop/ingest/extractors/base|learnloop.ingest.extractors.base]] — imports `DocumentExtractor`, `ExtractionContext`, `single_unit_from_blocks`, `units_from_toc_entries`
- [[Reference/Modules/learnloop/ingest/extractors/datalab|learnloop.ingest.extractors.datalab]] — imports `DATALAB_API_KEY_ENV`, `DatalabDocumentExtractor`, `DatalabExtractionError`, `datalab_api_key`; calls `DatalabDocumentExtractor`, `datalab_api_key`
- [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]] — imports `EXTRACTOR_NAME`, `GlmOcrConsentRequired`, `GlmOcrDocumentExtractor`, `GlmOcrExtractionError`, `UNAVAILABLE_MESSAGE`, `is_image_document`, `selected_backend`; calls `GlmOcrDocumentExtractor`, `is_image_document`, `selected_backend`
- [[Reference/Modules/learnloop/ingest/extractors/marker|learnloop.ingest.extractors.marker]] — imports `MarkerDocumentExtractor`, `MarkerUnavailableError`, `chunk_output_to_ir`, `marker_available`, `marker_package_version`; calls `MarkerDocumentExtractor`, `MarkerUnavailableError`, `marker_available`
- [[Reference/Modules/learnloop/ingest/extractors/normalizers|learnloop.ingest.extractors.normalizers]] — imports `captions_to_ir`, `markdown_to_ir`, `transcript_to_ir`
- [[Reference/Modules/learnloop/ingest/extractors/pypdf|learnloop.ingest.extractors.pypdf]] — imports `PyPdfDocumentExtractor`, `PyPdfExtractionError`, `read_embedded_outline`; calls `PyPdfDocumentExtractor`

### Platform and third-party dependencies

- Standard library: `__future__`, `os`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/acquisition_preview|learnloop.content.pipeline.acquisition_preview]], [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/sources/pdf_extraction|learnloop.content.sources.pdf_extraction]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_glm_ocr.py](../../../../../../../tests/test_glm_ocr.py) — direct import
  - `test_a_book_carrying_the_retired_keep_local_choice_is_read_like_any_other`
  - `test_auto_falls_back_on_a_glm_failure_but_never_past_a_refusal`
  - `test_auto_prefers_hosted_glm_with_a_key_then_marker_then_pypdf_with_reasons`
  - `test_every_glm_ocr_reading_queues_the_source_block_backfill`
  - `test_local_runs_only_when_chosen_and_answering_and_a_local_only_reading_never_uploads`
  - `test_r2_f1_a_local_repair_never_goes_to_a_glm_server_on_another_computer`
  - `test_r2_f2_an_import_without_the_ok_reads_locally_and_offers_text_recognition`
  - `test_r2_f2_the_card_reads_it_again_with_text_recognition_after_the_ok`
  - `test_r2_f5_paid_windows_are_kept_so_trying_again_pays_only_for_the_rest`
  - `test_r2_f6_a_cut_off_answer_or_an_unrenderable_page_falls_back_under_auto`
  - `test_r2_f7_a_stand_in_reading_is_stored_with_its_own_model_versions`
  - `test_r2_f9_a_scan_offers_text_recognition_or_where_to_set_it_up`
  - `test_r3_f10_a_local_repair_never_leaves_this_computer`
  - `test_r3_f10_a_local_repair_of_an_image_sends_nothing_and_says_why`
  - `test_r3_f14_the_cards_details_are_plain_words`
  - `test_r3_f2_a_scan_or_image_imported_without_the_ok_asks_for_it_on_its_card`
  - `test_r3_f7_a_double_fallback_stores_the_versions_of_what_read_it`
  - `test_read_again_with_text_recognition_uses_glm_when_it_can`
  - `test_the_local_backend_renders_pdf_pages_for_a_real_http_server`
  - `test_the_preview_estimates_pages_and_names_the_upload`
- [tests/test_marker_pdfium_worker.py](../../../../../../../tests/test_marker_pdfium_worker.py) — direct import
  - `test_a_cancelled_import_stops_the_marker_worker`
  - `test_a_marker_worker_that_crashes_or_hangs_is_recorded_and_the_import_falls_back`
  - `test_a_worker_that_answered_exits_at_once_and_cleanly`
  - `test_every_process_the_marker_worker_started_ends_with_its_reading`
  - `test_marker_never_enters_pdfium_in_this_process_while_the_reader_renders`
  - `test_marker_output_never_reaches_this_process_stdout`
  - `test_the_worker_carries_the_page_selection_and_torch_device_without_touching_this_process`
- [tests/test_pdf_extractor_selection.py](../../../../../../../tests/test_pdf_extractor_selection.py) — direct import
  - `test_native_engine_never_resolves_to_a_local_extractor`
  - `test_pypdf_engine_resolves_locally`
  - `test_pypdf_text_with_lone_surrogates_reads_with_replacement_characters`
- [tests/test_reread_safety.py](../../../../../../../tests/test_reread_safety.py) — direct import
  - `test_the_z_ai_ok_line_names_pages_and_cost_for_a_404_page_book`
- [tests/test_reread_safety_landing.py](../../../../../../../tests/test_reread_safety_landing.py) — direct import
  - `test_a_marker_reread_hands_the_worker_the_stored_originals_bytes`
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
