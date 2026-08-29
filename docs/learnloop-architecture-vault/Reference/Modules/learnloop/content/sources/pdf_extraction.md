---
title: "learnloop.content.sources.pdf_extraction"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/sources/pdf_extraction.py"
source_paths:
  - "src/learnloop/content/sources/pdf_extraction.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.sources"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.sources.pdf_extraction module"
  - "src/learnloop/content/sources/pdf_extraction.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-sources"
---

# `learnloop.content.sources.pdf_extraction`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.sources.pdf_extraction` exists within [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] to own the behavior summarized by its module contract: Pluggable PDF -> Markdown extraction for canonical source ingestion.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/sources/pdf_extraction.py](../../../../../../../src/learnloop/content/sources/pdf_extraction.py) |
| Source lines | 229 |
| Owning package | [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class PdfExtractionError(ValueError)` ([source](../../../../../../../src/learnloop/content/sources/pdf_extraction.py), line 36)
- `class PdfExtraction` ([source](../../../../../../../src/learnloop/content/sources/pdf_extraction.py), line 41)
- `extract_pdf_markdown(raw_bytes: bytes, *, config: PdfIngestConfig | None=None, cache_dir: Path | None=None) -> PdfExtraction` ([source](../../../../../../../src/learnloop/content/sources/pdf_extraction.py), line 52)

### Module constants

- `_MARKER_CONVERTERS` ([src/learnloop/content/sources/pdf_extraction.py](../../../../../../../src/learnloop/content/sources/pdf_extraction.py), line 49)

## Internal implementation anchors

- `_resolve_engine(config: PdfIngestConfig) -> str` ([source](../../../../../../../src/learnloop/content/sources/pdf_extraction.py), line 72)
- `_marker_options(config: PdfIngestConfig) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/sources/pdf_extraction.py), line 84)
- `_extract_with_marker(raw_bytes: bytes, config: PdfIngestConfig, options: dict[str, Any]) -> PdfExtraction` ([source](../../../../../../../src/learnloop/content/sources/pdf_extraction.py), line 107)
- `_marker_converter(options: dict[str, Any]) -> Any` ([source](../../../../../../../src/learnloop/content/sources/pdf_extraction.py), line 130)
- `_extract_with_pypdf(raw_bytes: bytes) -> PdfExtraction` ([source](../../../../../../../src/learnloop/content/sources/pdf_extraction.py), line 151)
- `_marker_cache_fingerprint() -> str` ([source](../../../../../../../src/learnloop/content/sources/pdf_extraction.py), line 171) — Version fingerprint mixed into the extraction cache key (ING §2.2/§2.5).
- `_cache_key(raw_bytes: bytes, options: dict[str, Any], version_fingerprint: str='') -> str` ([source](../../../../../../../src/learnloop/content/sources/pdf_extraction.py), line 191)
- `_read_cache(cache_dir: Path | None, key: str) -> PdfExtraction | None` ([source](../../../../../../../src/learnloop/content/sources/pdf_extraction.py), line 205)
- `_write_cache(cache_dir: Path | None, key: str, extraction: PdfExtraction) -> None` ([source](../../../../../../../src/learnloop/content/sources/pdf_extraction.py), line 221)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `PdfExtractionError`, `extract_pdf_markdown`; statically calls `extract_pdf_markdown`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `PdfIngestConfig`; calls `PdfIngestConfig`
- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `IR_SCHEMA_VERSION`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `importlib`, `io`, `json`, `os`, `pathlib`, `tempfile`, `typing`
- Third party: `marker`, `pypdf`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_pdf_extraction.py](../../../../../../../tests/test_pdf_extraction.py) — direct import
  - `test_auto_engine_falls_back_to_pypdf_when_marker_missing`
  - `test_cache_key_excludes_api_key`
  - `test_explicit_marker_engine_requires_marker`
  - `test_marker_cache_fingerprint_includes_ir_schema_version`
  - `test_marker_empty_output_raises`
  - `test_marker_engine_converts_and_caches`
  - `test_marker_llm_options_map_to_openai_service`
  - `test_marker_pdftext_worker_override_is_preserved`
  - `test_marker_torch_device_pin_sets_env`
  - `test_marker_upgrade_changes_cache_key`
- [tests/test_source_ingestion_adapters.py](../../../../../../../tests/test_source_ingestion_adapters.py) — direct import
  - `test_pdf_without_text_layer_raises`

## Modification guidance

- Change pdf extraction policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/sources/pdf_extraction.py](../../../../../../../src/learnloop/content/sources/pdf_extraction.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
