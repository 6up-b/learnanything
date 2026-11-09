---
title: "learnloop.ingest.hashing"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/hashing.py"
source_paths:
  - "src/learnloop/ingest/hashing.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ingest"
layer: "infrastructure"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
aliases:
  - "learnloop.ingest.hashing module"
  - "src/learnloop/ingest/hashing.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest"
---

# `learnloop.ingest.hashing`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.hashing` exists within [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] to own the behavior summarized by its module contract: The source-layer hash model (spec_source_ingestion_v2 §2.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/hashing.py](../../../../../../src/learnloop/ingest/hashing.py) |
| Source lines | 180 |
| Owning package | [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `asset_hash(raw_bytes: bytes) -> str` ([source](../../../../../../src/learnloop/ingest/hashing.py), line 52) — Hash of the raw fetched bytes; the SourceRevision identity (§2.2).
- `extraction_request_hash(*, revision_id: str, extractor: str, extractor_version: str, package_version: str | None=None, model_versions: Mapping[str, str] | None=None, config: Mapping[str, Any] | None=None, page_selection: Iterable[int] | None=None, ir_schema_version: str) -> str` ([source](../../../../../../src/learnloop/ingest/hashing.py), line 62) — Idempotency/retry key for a *requested* ExtractionRun (§2.2, §2.5).
- `extraction_result_hash(request_hash: str, ir: DocumentIR) -> str` ([source](../../../../../../src/learnloop/ingest/hashing.py), line 98) — Completed-run content identity: request hash + produced IR (§2.2).
- `normalize_semantic_text(blocks: Iterable[DocumentBlock]) -> str` ([source](../../../../../../src/learnloop/ingest/hashing.py), line 108) — Deterministic normalized text view over a unit's blocks (§2.2).
- `semantic_hash(blocks: Iterable[DocumentBlock]) -> str` ([source](../../../../../../src/learnloop/ingest/hashing.py), line 173) — Per-unit semantic hash over the normalized text view (§2.2).
- `block_type_histogram(blocks: Iterable[DocumentBlock]) -> dict[str, int]` ([source](../../../../../../src/learnloop/ingest/hashing.py), line 179)

### Module constants

- `_VERBATIM_BLOCK_TYPES` ([src/learnloop/ingest/hashing.py](../../../../../../src/learnloop/ingest/hashing.py), line 30)
- `_TAG_RE` ([src/learnloop/ingest/hashing.py](../../../../../../src/learnloop/ingest/hashing.py), line 41)
- `_WS_RE` ([src/learnloop/ingest/hashing.py](../../../../../../src/learnloop/ingest/hashing.py), line 42)
- `_PAGE_NUMBER_RE` ([src/learnloop/ingest/hashing.py](../../../../../../src/learnloop/ingest/hashing.py), line 43)

## Internal implementation anchors

- `_sha256(payload: str | bytes) -> str` ([source](../../../../../../src/learnloop/ingest/hashing.py), line 46)
- `_canonical_json(data: Any) -> str` ([source](../../../../../../src/learnloop/ingest/hashing.py), line 58)
- `_sanitized_config(config: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ingest/hashing.py), line 93)
- `_repeated_boilerplate(blocks: list[DocumentBlock]) -> set[str]` ([source](../../../../../../src/learnloop/ingest/hashing.py), line 139) — Short prose lines that recur across many pages are headers/footers.
- `_strip_markup(text: str) -> str` ([source](../../../../../../src/learnloop/ingest/hashing.py), line 160)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `extraction_request_hash`, `extraction_result_hash`; statically calls `extraction_request_hash`, `extraction_result_hash`
- [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]] — imports `asset_hash`; statically calls `asset_hash`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `asset_hash`; statically calls `asset_hash`
- [[Reference/Modules/learnloop/content/sources/source_library|learnloop.content.sources.source_library]] — imports `asset_hash`; statically calls `asset_hash`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `normalize_semantic_text`; statically calls `normalize_semantic_text`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `normalize_semantic_text`
- [[Reference/Modules/learnloop/ingest/extractors/base|learnloop.ingest.extractors.base]] — imports `semantic_hash`; statically calls `semantic_hash`
- [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]] — imports `semantic_hash`; statically calls `semantic_hash`
- [[Reference/Modules/learnloop/ingest/extractors/marker|learnloop.ingest.extractors.marker]] — imports `semantic_hash`
- [[Reference/Modules/learnloop/ingest/extractors/normalizers|learnloop.ingest.extractors.normalizers]] — imports `semantic_hash`; statically calls `semantic_hash`
- [[Reference/Modules/learnloop/ingest/originals|learnloop.ingest.originals]] — imports `asset_hash`; statically calls `asset_hash`
- [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]] — imports `asset_hash`; statically calls `asset_hash`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `DocumentBlock`, `DocumentIR`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]], [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]], [[Reference/Modules/learnloop/content/sources/source_library|learnloop.content.sources.source_library]], [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/exam_scope_fixtures.py](../../../../../../tests/exam_scope_fixtures.py) — direct import
- [tests/helpers.py](../../../../../../tests/helpers.py) — direct import
- [tests/test_daily_plan_reading.py](../../../../../../tests/test_daily_plan_reading.py) — direct import
- [tests/test_document_ir.py](../../../../../../tests/test_document_ir.py) — direct import
  - `test_request_hash_computable_before_execution_and_versioned`
  - `test_result_hash_depends_on_request_and_ir`
  - `test_semantic_hash_keeps_equation_content_verbatim`
  - `test_semantic_hash_stable_under_cosmetic_html_changes`
  - `test_semantic_normalization_drops_repeated_headers_and_page_numbers`
- [tests/test_exam_protection_identity.py](../../../../../../tests/test_exam_protection_identity.py) — direct import
- [tests/test_glm_ocr.py](../../../../../../tests/test_glm_ocr.py) — direct import
  - `test_versions_name_backend_models_and_mapping_so_caches_re_extract`
- [tests/test_ingest_m3.py](../../../../../../tests/test_ingest_m3.py) — direct import
  - `test_targeted_repair_records_consent_and_preserves_unaffected_hashes`
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_import_retry_replaces_ir_left_by_interrupted_run`
- [tests/test_originals_store.py](../../../../../../tests/test_originals_store.py) — direct import
  - `test_backfill_statuses`
  - `test_resolve_prefers_store_then_original_uri`
- [tests/test_primed_attempts.py](../../../../../../tests/test_primed_attempts.py) — direct import
  - `test_feedback_resolves_current_ingest_span_and_filename`
- [tests/test_reread_safety.py](../../../../../../tests/test_reread_safety.py) — direct import
  - `test_a_retried_import_reads_the_revision_it_registered_not_the_current_one`
  - `test_e1_bytes_that_match_nowhere_refuse_plainly_and_register_nothing`
  - `test_e1_one_tap_repair_for_a_library_already_in_that_state`
  - `test_e1_the_reread_reads_the_stored_original_and_reuses_the_revision`
- [tests/test_reread_safety_landing.py](../../../../../../tests/test_reread_safety_landing.py) — direct import
  - `test_a_marker_reread_hands_the_worker_the_stored_originals_bytes`
- [tests/test_sidecar_ingest_m3.py](../../../../../../tests/test_sidecar_ingest_m3.py) — direct import
- [tests/test_sidecar_quick_add.py](../../../../../../tests/test_sidecar_quick_add.py) — direct import
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../tests/test_sidecar_reader_pdf_view.py) — direct import
  - `test_pdf_view_backfills_store_from_live_local_original`
- [tests/test_sidecar_span_view.py](../../../../../../tests/test_sidecar_span_view.py) — direct import
- [tests/test_source_deletion.py](../../../../../../tests/test_source_deletion.py) — direct import
- [tests/test_source_inventory.py](../../../../../../tests/test_source_inventory.py) — direct import
- [tests/test_source_layer.py](../../../../../../tests/test_source_layer.py) — direct import
  - `test_retry_keys_on_request_hash_before_result_exists`
- [tests/test_ux_phase1_round2_review.py](../../../../../../tests/test_ux_phase1_round2_review.py) — direct import

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/hashing.py](../../../../../../src/learnloop/ingest/hashing.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
