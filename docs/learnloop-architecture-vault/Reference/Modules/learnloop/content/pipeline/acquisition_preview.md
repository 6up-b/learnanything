---
title: "learnloop.content.pipeline.acquisition_preview"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/pipeline/acquisition_preview.py"
source_paths:
  - "src/learnloop/content/pipeline/acquisition_preview.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.pipeline"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.content.pipeline.acquisition_preview module"
  - "src/learnloop/content/pipeline/acquisition_preview.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-pipeline"
---

# `learnloop.content.pipeline.acquisition_preview`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.pipeline.acquisition_preview` exists within [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] to own the behavior summarized by its module contract: Deterministic acquisition preview (spec_source_ingestion_v2 §8.6.1).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/pipeline/acquisition_preview.py](../../../../../../../src/learnloop/content/pipeline/acquisition_preview.py) |
| Source lines | 206 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class AcquisitionItem` ([source](../../../../../../../src/learnloop/content/pipeline/acquisition_preview.py), line 35)
- `class AcquisitionPreview` ([source](../../../../../../../src/learnloop/content/pipeline/acquisition_preview.py), line 52)
  - `recognized_count(self) -> int` (line 56; public)
  - `duplicate_count(self) -> int` (line 60; public)
  - `existing_count(self) -> int` (line 64; public)
  - `needs_consent_count(self) -> int` (line 68; public)
  - `as_dict(self) -> dict` (line 71; public)
- `build_acquisition_preview(repo: Repository, config: LearnLoopConfig, inputs: list[str]) -> AcquisitionPreview` ([source](../../../../../../../src/learnloop/content/pipeline/acquisition_preview.py), line 101) — Preview a batch of candidate inputs deterministically (§8.6.1).

### Module constants

- `_NORMALIZER_BY_CATEGORY` ([src/learnloop/content/pipeline/acquisition_preview.py](../../../../../../../src/learnloop/content/pipeline/acquisition_preview.py), line 25)

## Internal implementation anchors

- `_configured_extractor(category: str, config: LearnLoopConfig) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/acquisition_preview.py), line 140)
- `_potential_external(category: str, config: LearnLoopConfig) -> list[dict]` ([source](../../../../../../../src/learnloop/content/pipeline/acquisition_preview.py), line 157)
- `_annotate_local(item: AcquisitionItem, normalized_uri: str) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/acquisition_preview.py), line 192)
- `_annotate_existing(item: AcquisitionItem, repo: Repository, category: str, normalized_uri: str) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/acquisition_preview.py), line 202)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `build_acquisition_preview`; statically calls `build_acquisition_preview`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `build_acquisition_preview`; statically calls `build_acquisition_preview`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ingest/extractors/__init__|learnloop.ingest.extractors]] — imports `marker_available`; calls `marker_available`
- [[Reference/Modules/learnloop/ingest/models|learnloop.ingest.models]] — imports `UnsupportedSourceError`
- [[Reference/Modules/learnloop/ingest/resolution|learnloop.ingest.resolution]] — imports `resolve_source`; calls `resolve_source`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ingest_m3.py](../../../../../../../tests/test_ingest_m3.py) — direct import
  - `test_acquisition_preview_audio_is_always_external`
  - `test_acquisition_preview_flags_potential_external_consent`
  - `test_acquisition_preview_pdf_native_engine_is_external`
  - `test_acquisition_preview_reports_recognition_dupes_and_existing`
  - `test_legacy_openrouter_audio_translation_preserves_consent_surface`

## Modification guidance

- Change acquisition preview policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/pipeline/acquisition_preview.py](../../../../../../../src/learnloop/content/pipeline/acquisition_preview.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
