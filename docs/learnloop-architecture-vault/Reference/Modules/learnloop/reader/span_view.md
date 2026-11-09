---
title: "learnloop.reader.span_view"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/span_view.py"
source_paths:
  - "src/learnloop/reader/span_view.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.span_view module"
  - "src/learnloop/reader/span_view.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.span_view`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.span_view` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Open-in-source span view (spec_source_ingestion_v2 §9.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/span_view.py](../../../../../../src/learnloop/reader/span_view.py) |
| Source lines | 493 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SpanViewError(ValueError)` ([source](../../../../../../src/learnloop/reader/span_view.py), line 58) — Typed failure for the get_span_view RPC.
  - `__init__(self, code: str, message: str) -> None` (line 61; internal)
- `build_span_view(repo: Repository, extraction_id: str, span_id: str, *, context: str='other', entity_type: str | None=None, entity_id: str | None=None, record: bool=True, clock: Clock | None=None, exposure_fields: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/span_view.py), line 79) — Resolve a span to viewer geometry + text and record a source_exposure event.
- `record_span_exposures(repo: Repository, extraction_id: str, span_ids: list[str], *, context: str='other', entity_type: str | None=None, entity_id: str | None=None, clock: Clock | None=None, exposure_fields: Mapping[str, Any] | None=None) -> list[str]` ([source](../../../../../../src/learnloop/reader/span_view.py), line 187) — Record a ``source_exposure`` event for each of these spans, in one transaction: the passages a surface DISPLAYED, not only the one it was asked for (Reader CA5a's peek shows a section's first blocks: Codex review F2).
- `build_block_region(repo: Repository, extraction_id: str, span_id: str, *, bbox: list[float] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/span_view.py), line 420) — On-demand original-region crop for one block (spec §3.4).

### Module constants

- `_NEIGHBOR_RADIUS` ([src/learnloop/reader/span_view.py](../../../../../../src/learnloop/reader/span_view.py), line 32)
- `_NEIGHBOR_CHAR_CAP` ([src/learnloop/reader/span_view.py](../../../../../../src/learnloop/reader/span_view.py), line 34)
- `_VALID_CONTEXTS` ([src/learnloop/reader/span_view.py](../../../../../../src/learnloop/reader/span_view.py), line 36)
- `_PDFIUM_LOCK` ([src/learnloop/reader/span_view.py](../../../../../../src/learnloop/reader/span_view.py), line 270)
- `_CROP_SCALE` ([src/learnloop/reader/span_view.py](../../../../../../src/learnloop/reader/span_view.py), line 317)

## Internal implementation anchors

- `_neighbor(block: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/span_view.py), line 66)
- `_original_pdf_path(repo: Repository, revision: dict[str, Any] | None, fallback_uri: str | None) -> Path | None` ([source](../../../../../../src/learnloop/reader/span_view.py), line 244) — Locate a readable local copy of the revision's original PDF: the vault's content-addressed store first (survives file moves), else the ingest-time ``original_uri``/``canonical_uri`` when it still points at a local file.
- `_pdf_page(path: Path, page: int) -> Iterator[Any]` ([source](../../../../../../src/learnloop/reader/span_view.py), line 274) — The PDF's zero-based ``page`` (None when out of range), opened and closed under the pdfium lock.
- `_local_pdf_page_render(path: Path | None, page: int | None) -> tuple[str | None, list[float] | None]` ([source](../../../../../../src/learnloop/reader/span_view.py), line 295)
- `_local_pdf_block_crop(path: Path | None, page: int | None, bbox: list[float] | None) -> tuple[str | None, list[float] | None]` ([source](../../../../../../src/learnloop/reader/span_view.py), line 320) — Render an on-demand crop of one block's PDF region (spec §3.4).
- `_local_pdf_crops(path: Path | None, page: int | None, boxes: list[list[float]]) -> tuple[list[str | None], list[float] | None]` ([source](../../../../../../src/learnloop/reader/span_view.py), line 357) — Reader CA1: several crops of one PDF page, the page rendered once.
- `_local_pdf_page_label(path: Path | None, page: int | None) -> str | None` ([source](../../../../../../src/learnloop/reader/span_view.py), line 397) — The page's printed label from the PDF's own page labels (``/PageLabels``), or None when the file has none (the caller then shows the page's position).
- `_original_pdf_for(repo: Repository, extraction_id: str) -> Path | None` ([source](../../../../../../src/learnloop/reader/span_view.py), line 462)
- `_block_subregion(repo: Repository, extraction_id: str, span_id: str, block: Any, bbox: list[float]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/span_view.py), line 471) — A learner-drawn box inside one block: the box clipped to the block's own box (a box outside it crops nothing).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `SpanViewError`, `build_span_view`; statically calls `build_span_view`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `build_block_region`; statically calls `build_block_region`
- [[Reference/Modules/learnloop/reader/as_printed|learnloop.reader.as_printed]] — imports `module`; statically calls `_local_pdf_crops`, `_local_pdf_page_label`, `_original_pdf_for`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `SpanViewError`, `build_span_view`; statically calls `build_span_view`
- [[Reference/Modules/learnloop/reader/reader_restoration|learnloop.reader.reader_restoration]] — imports `SpanViewError`, `build_span_view`; statically calls `build_span_view`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `SpanViewError`, `record_span_exposures`; statically calls `record_span_exposures`
- [[Reference/Modules/learnloop_sidecar/handlers/provenance|learnloop_sidecar.handlers.provenance]] — imports `SpanViewError`, `build_span_view`; statically calls `build_span_view`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `build_block_region`
- [[Reference/Modules/learnloop_sidecar/handlers/side_by_side|learnloop_sidecar.handlers.side_by_side]] — imports `SpanViewError`, `record_span_exposures`; statically calls `record_span_exposures`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `BLOCK_SPAN_V1`, `format_block_span`; calls `format_block_span`
- [[Reference/Modules/learnloop/ingest/originals|learnloop.ingest.originals]] — imports `is_pdf_file`, `resolve_original_file`; calls `is_pdf_file`, `resolve_original_file`

### Platform and third-party dependencies

- Standard library: `__future__`, `base64`, `collections`, `contextlib`, `io`, `pathlib`, `threading`, `typing`
- Third party: `pypdfium2`

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]], [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]], [[Reference/Modules/learnloop/reader/as_printed|learnloop.reader.as_printed]], [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]], [[Reference/Modules/learnloop/reader/reader_restoration|learnloop.reader.reader_restoration]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_region.py](../../../../../../tests/test_figure_region.py) — direct import
- [tests/test_glm_ocr.py](../../../../../../tests/test_glm_ocr.py) — direct import
- [tests/test_marker_pdfium_worker.py](../../../../../../tests/test_marker_pdfium_worker.py) — direct import
  - `test_the_readers_own_renders_enter_pdfium_one_at_a_time`
- [tests/test_reader_render_views.py](../../../../../../tests/test_reader_render_views.py) — direct import
  - `test_block_original_region_falls_back_when_no_pdf`
- [tests/test_reader_rw6b_landing.py](../../../../../../tests/test_reader_rw6b_landing.py) — direct import
  - `test_iii_a_ca5a_peek_of_the_items_source_span_holds_the_follow_up`
- [tests/test_source_outcome_analytics.py](../../../../../../tests/test_source_outcome_analytics.py) — direct import
  - `test_actionable_associations_flow_into_maintenance_feed`
  - `test_new_exposure_contexts_record`
  - `test_repeated_failure_despite_coverage_requires_exposure`
- [tests/test_span_view.py](../../../../../../tests/test_span_view.py) — direct import
  - `test_open_in_source_records_source_exposure_event`
  - `test_span_view_renders_available_local_pdf_page`
  - `test_span_view_text_anchor_mode_without_geometry`
  - `test_span_view_typed_errors`
- [tests/test_tutor_delivery_fixes.py](../../../../../../tests/test_tutor_delivery_fixes.py) — direct import

## Modification guidance

- Change span view policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/span_view.py](../../../../../../src/learnloop/reader/span_view.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
