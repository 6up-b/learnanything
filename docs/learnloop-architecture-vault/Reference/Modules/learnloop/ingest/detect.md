---
title: "learnloop.ingest.detect"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/detect.py"
source_paths:
  - "src/learnloop/ingest/detect.py"
source_commit: "9dcae21a171fed856b7a5545c30c14ff4f5b5cee"
source_commit_timestamp: "2026-07-13T20:52:33-04:00"
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
  - "learnloop.ingest.detect module"
  - "src/learnloop/ingest/detect.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest"
---

# `learnloop.ingest.detect`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps detect behavior inside its owning package, [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]]. Its public surface centers on `detect_source_kind`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/detect.py](../../../../../../src/learnloop/ingest/detect.py) |
| Source lines | 13 |
| Owning package | [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `9dcae21a171fed856b7a5545c30c14ff4f5b5cee` |
| Commit timestamp | `2026-07-13T20:52:33-04:00` |

## Public API

- `detect_source_kind(source: str) -> str` ([source](../../../../../../src/learnloop/ingest/detect.py), line 6) — Classify a source string into one of the supported ingestion kinds.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ingest/__init__|learnloop.ingest]] — imports `detect_source_kind`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ingest/resolution|learnloop.ingest.resolution]] — imports `resolve_source`; calls `resolve_source`

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/ingest/__init__|learnloop.ingest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ingest_detect.py](../../../../../../tests/test_ingest_detect.py) — direct import
  - `test_detect_audio_by_suffix_without_existing_file`
  - `test_detect_extensionless_existing_file_is_text`
  - `test_detect_local_audio_files`
  - `test_detect_local_files`
  - `test_detect_rejects_unknown_sources`
  - `test_detect_url_and_id_sources`
  - `test_unclassifiable_error_mentions_audio`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/detect.py](../../../../../../src/learnloop/ingest/detect.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
