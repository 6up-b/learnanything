---
title: "learnloop.reader.span_view"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/span_view.py"
source_paths:
  - "src/learnloop/reader/span_view.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.span_view` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Open-in-source span view (spec_source_ingestion_v2 §9.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/span_view.py](../../../../../../src/learnloop/reader/span_view.py) |
| Source lines | 297 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class SpanViewError(ValueError)` ([source](../../../../../../src/learnloop/reader/span_view.py), line 55) — Typed failure for the get_span_view RPC.
  - `__init__(self, code: str, message: str) -> None` (line 58; internal)
- `build_span_view(repo: Repository, extraction_id: str, span_id: str, *, context: str='other', entity_type: str | None=None, entity_id: str | None=None, record: bool=True, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/span_view.py), line 76) — Resolve a span to viewer geometry + text and record a source_exposure event.
- `build_block_region(repo: Repository, extraction_id: str, span_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/span_view.py), line 266) — On-demand original-region crop for one block (spec §3.4).

### Module constants

- `_NEIGHBOR_RADIUS` ([src/learnloop/reader/span_view.py](../../../../../../src/learnloop/reader/span_view.py), line 29)
- `_NEIGHBOR_CHAR_CAP` ([src/learnloop/reader/span_view.py](../../../../../../src/learnloop/reader/span_view.py), line 31)
- `_VALID_CONTEXTS` ([src/learnloop/reader/span_view.py](../../../../../../src/learnloop/reader/span_view.py), line 33)
- `_CROP_SCALE` ([src/learnloop/reader/span_view.py](../../../../../../src/learnloop/reader/span_view.py), line 224)

## Internal implementation anchors

- `_neighbor(block: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/span_view.py), line 63)
- `_original_pdf_path(repo: Repository, revision: dict[str, Any] | None, fallback_uri: str | None) -> Path | None` ([source](../../../../../../src/learnloop/reader/span_view.py), line 181) — Locate a readable local copy of the revision's original PDF: the vault's content-addressed store first (survives file moves), else the ingest-time ``original_uri``/``canonical_uri`` when it still points at a local file.
- `_local_pdf_page_render(path: Path | None, page: int | None) -> tuple[str | None, list[float] | None]` ([source](../../../../../../src/learnloop/reader/span_view.py), line 200)
- `_local_pdf_block_crop(path: Path | None, page: int | None, bbox: list[float] | None) -> tuple[str | None, list[float] | None]` ([source](../../../../../../src/learnloop/reader/span_view.py), line 227) — Render an on-demand crop of one block's PDF region (spec §3.4).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `SpanViewError`, `build_span_view`; statically calls `build_span_view`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `SpanViewError`, `build_span_view`; statically calls `build_span_view`
- [[Reference/Modules/learnloop/reader/reader_restoration|learnloop.reader.reader_restoration]] — imports `SpanViewError`, `build_span_view`; statically calls `build_span_view`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `SpanViewError`, `build_span_view`; statically calls `build_span_view`
- [[Reference/Modules/learnloop_sidecar/handlers/provenance|learnloop_sidecar.handlers.provenance]] — imports `SpanViewError`, `build_span_view`; statically calls `build_span_view`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `build_block_region`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `BLOCK_SPAN_V1`, `format_block_span`; calls `format_block_span`
- [[Reference/Modules/learnloop/ingest/originals|learnloop.ingest.originals]] — imports `is_pdf_file`, `resolve_original_file`; calls `is_pdf_file`, `resolve_original_file`

### Platform and third-party dependencies

- Standard library: `__future__`, `base64`, `io`, `pathlib`, `typing`
- Third party: `pypdfium2`

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]], [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]], [[Reference/Modules/learnloop/reader/reader_restoration|learnloop.reader.reader_restoration]], [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]], [[Reference/Modules/learnloop_sidecar/handlers/provenance|learnloop_sidecar.handlers.provenance]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_render_views.py](../../../../../../tests/test_reader_render_views.py) — direct import
  - `test_block_original_region_falls_back_when_no_pdf`
- [tests/test_source_outcome_analytics.py](../../../../../../tests/test_source_outcome_analytics.py) — direct import
  - `test_actionable_associations_flow_into_maintenance_feed`
  - `test_new_exposure_contexts_record`
  - `test_repeated_failure_despite_coverage_requires_exposure`
- [tests/test_span_view.py](../../../../../../tests/test_span_view.py) — direct import
  - `test_open_in_source_records_source_exposure_event`
  - `test_span_view_renders_available_local_pdf_page`
  - `test_span_view_text_anchor_mode_without_geometry`
  - `test_span_view_typed_errors`

## Modification guidance

- Change span view policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/span_view.py](../../../../../../src/learnloop/reader/span_view.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
