---
title: "learnloop.ingest.models"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/models.py"
source_paths:
  - "src/learnloop/ingest/models.py"
source_commit: "023c920a5462774e45ae8b91031dc310dea10409"
source_commit_timestamp: "2026-05-28T14:47:32-04:00"
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
  - "learnloop.ingest.models module"
  - "src/learnloop/ingest/models.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest"
---

# `learnloop.ingest.models`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps models behavior inside its owning package, [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]]. Its public surface centers on `IngestError`, `UnsupportedSourceError`, `SourceFetchError`, `IngestDependencyMissing`, `FetchedSource`, `IngestResult`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/models.py](../../../../../../src/learnloop/ingest/models.py) |
| Source lines | 79 |
| Owning package | [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `023c920a5462774e45ae8b91031dc310dea10409` |
| Commit timestamp | `2026-05-28T14:47:32-04:00` |

## Public API

- `class IngestError(RuntimeError)` ([source](../../../../../../src/learnloop/ingest/models.py), line 6) — Base class for ingestion failures.
- `class UnsupportedSourceError(IngestError)` ([source](../../../../../../src/learnloop/ingest/models.py), line 10) — Raised when a source string cannot be classified into a known kind.
- `class SourceFetchError(IngestError)` ([source](../../../../../../src/learnloop/ingest/models.py), line 14) — Raised when fetching or extracting a recognized source fails.
- `class IngestDependencyMissing(IngestError)` ([source](../../../../../../src/learnloop/ingest/models.py), line 18) — Raised when the optional library a fetcher needs is not installed.
  - `__init__(self, kind: str, package: str, extra: str='learnloop[ingest]') -> None` (line 21; internal)
- `class FetchedSource` ([source](../../../../../../src/learnloop/ingest/models.py), line 32) — Normalized result of fetching one canonical source.
- `class IngestResult` ([source](../../../../../../src/learnloop/ingest/models.py), line 49) — Outcome of staging a canonical source into the vault.
  - `as_dict(self) -> dict` (line 65; public)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/acquisition_preview|learnloop.content.pipeline.acquisition_preview]] — imports `UnsupportedSourceError`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `UnsupportedSourceError`
- [[Reference/Modules/learnloop/ingest/__init__|learnloop.ingest]] — imports `FetchedSource`, `IngestDependencyMissing`, `IngestError`, `IngestResult`, `SourceFetchError`, `UnsupportedSourceError`
- [[Reference/Modules/learnloop/ingest/fetchers|learnloop.ingest.fetchers]] — imports `FetchedSource`, `IngestDependencyMissing`, `SourceFetchError`, `UnsupportedSourceError`; statically calls `FetchedSource`, `IngestDependencyMissing`, `SourceFetchError`, `UnsupportedSourceError`
- [[Reference/Modules/learnloop/ingest/resolution|learnloop.ingest.resolution]] — imports `UnsupportedSourceError`; statically calls `UnsupportedSourceError`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `UnsupportedSourceError`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `UnsupportedSourceError`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/acquisition_preview|learnloop.content.pipeline.acquisition_preview]], [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]], [[Reference/Modules/learnloop/ingest/__init__|learnloop.ingest]], [[Reference/Modules/learnloop/ingest/fetchers|learnloop.ingest.fetchers]], [[Reference/Modules/learnloop/ingest/resolution|learnloop.ingest.resolution]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ingest_detect.py](../../../../../../tests/test_ingest_detect.py) — direct import
  - `test_detect_rejects_unknown_sources`
  - `test_unclassifiable_error_mentions_audio`
- [tests/test_ingest_fetchers.py](../../../../../../tests/test_ingest_fetchers.py) — direct import
  - `test_fetch_textfile_missing_file_raises`
  - `test_legacy_fetch_source_rejects_audio`
  - `test_optional_dependency_missing_is_actionable`
  - `test_youtube_video_id_rejects_bad_url`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/models.py](../../../../../../src/learnloop/ingest/models.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
