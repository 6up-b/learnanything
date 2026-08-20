---
title: "learnloop.ingest.extractors.datalab"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/extractors/datalab.py"
source_paths:
  - "src/learnloop/ingest/extractors/datalab.py"
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
  - "learnloop.ingest.extractors.datalab module"
  - "src/learnloop/ingest/extractors/datalab.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest-extractors"
---

# `learnloop.ingest.extractors.datalab`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.extractors.datalab` exists within [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] to own the behavior summarized by its module contract: Hosted Datalab Marker adapter for debug-time PDF extraction.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/extractors/datalab.py](../../../../../../../src/learnloop/ingest/extractors/datalab.py) |
| Source lines | 205 |
| Owning package | [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1c72cbabade1a4be2d2f4d18b22d1cf0ac171657` |
| Commit timestamp | `2026-07-22T21:17:05-04:00` |

## Public API

- `class DatalabExtractionError(RuntimeError)` ([source](../../../../../../../src/learnloop/ingest/extractors/datalab.py), line 29) — Raised when the hosted conversion request cannot produce Marker chunks.
- `datalab_api_key() -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/datalab.py), line 33)
- `class DatalabDocumentExtractor` ([source](../../../../../../../src/learnloop/ingest/extractors/datalab.py), line 37) — Marker-compatible DocumentIR extraction backed by Datalab's cloud API.
  - `__init__(self, *, config: dict[str, Any] | None=None) -> None` (line 44; internal)
  - `version(self) -> str` (line 47; public)
  - `model_versions(self) -> dict[str, str]` (line 50; public)
  - `extract(self, raw_bytes: bytes, context: ExtractionContext)` (line 53; public)

### Module constants

- `DATALAB_API_KEY_ENV` ([src/learnloop/ingest/extractors/datalab.py](../../../../../../../src/learnloop/ingest/extractors/datalab.py), line 22)
- `DATALAB_CONVERT_URL` ([src/learnloop/ingest/extractors/datalab.py](../../../../../../../src/learnloop/ingest/extractors/datalab.py), line 23)
- `EXTRACTOR_VERSION` ([src/learnloop/ingest/extractors/datalab.py](../../../../../../../src/learnloop/ingest/extractors/datalab.py), line 24)
- `DEFAULT_REQUEST_TIMEOUT_SECONDS` ([src/learnloop/ingest/extractors/datalab.py](../../../../../../../src/learnloop/ingest/extractors/datalab.py), line 25)
- `DEFAULT_POLL_TIMEOUT_SECONDS` ([src/learnloop/ingest/extractors/datalab.py](../../../../../../../src/learnloop/ingest/extractors/datalab.py), line 26)

## Internal implementation anchors

- `_convert_pdf(raw_bytes: bytes, *, api_key: str, context: ExtractionContext, config: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ingest/extractors/datalab.py), line 95)
- `_validate_completed(result: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ingest/extractors/datalab.py), line 141)
- `_validate_check_url(url: str) -> None` ([source](../../../../../../../src/learnloop/ingest/extractors/datalab.py), line 148)
- `_request_json(request: Request) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ingest/extractors/datalab.py), line 155)
- `_multipart_body(fields: dict[str, str], raw_bytes: bytes) -> tuple[bytes, str]` ([source](../../../../../../../src/learnloop/ingest/extractors/datalab.py), line 174)
- `_poll_timeout_seconds() -> int` ([source](../../../../../../../src/learnloop/ingest/extractors/datalab.py), line 199)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ingest/extractors/__init__|learnloop.ingest.extractors]] — imports `DATALAB_API_KEY_ENV`, `DatalabDocumentExtractor`, `DatalabExtractionError`, `datalab_api_key`; statically calls `DatalabDocumentExtractor`, `datalab_api_key`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ingest/extractors/base|learnloop.ingest.extractors.base]] — imports `ExtractionContext`
- [[Reference/Modules/learnloop/ingest/extractors/marker|learnloop.ingest.extractors.marker]] — imports `MarkerUnavailableError`, `chunk_output_to_ir`; calls `MarkerUnavailableError`, `chunk_output_to_ir`
- [[Reference/Modules/learnloop/ingest/extractors/pypdf|learnloop.ingest.extractors.pypdf]] — imports `read_embedded_outline`; calls `read_embedded_outline`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `os`, `time`, `typing`, `urllib`, `uuid`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/ingest/extractors/__init__|learnloop.ingest.extractors]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_source_layer.py](../../../../../../../tests/test_source_layer.py) — imports consumer [[Reference/Modules/learnloop/ingest/extractors/__init__|learnloop.ingest.extractors]]

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/extractors/datalab.py](../../../../../../../src/learnloop/ingest/extractors/datalab.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
