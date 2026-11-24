---
title: "learnloop.ingest.youtube"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/youtube.py"
source_paths:
  - "src/learnloop/ingest/youtube.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ingest"
layer: "infrastructure"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
aliases:
  - "learnloop.ingest.youtube module"
  - "src/learnloop/ingest/youtube.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest"
---

# `learnloop.ingest.youtube`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.youtube` exists within [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] to own the behavior summarized by its module contract: YouTube helpers the live import and the Reader share: a video's id from any common URL form, and its title and channel from YouTube's public oEmbed endpoint.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/youtube.py](../../../../../../src/learnloop/ingest/youtube.py) |
| Source lines | 65 |
| Owning package | [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `youtube_video_id(source: str) -> str` ([source](../../../../../../src/learnloop/ingest/youtube.py), line 16) — Extract the 11-character video id from any common YouTube URL form.
- `youtube_oembed_metadata(video_id: str) -> tuple[str | None, str | None]` ([source](../../../../../../src/learnloop/ingest/youtube.py), line 43) — Best-effort (title, author) from YouTube's public oEmbed endpoint.

### Module constants

- `_USER_AGENT` ([src/learnloop/ingest/youtube.py](../../../../../../src/learnloop/ingest/youtube.py), line 13)

### Explicit exports

`__all__` declares:

- `youtube_oembed_metadata`
- `youtube_video_id`

## Internal implementation anchors

- `_http_get_text(url: str, *, timeout: int) -> str` ([source](../../../../../../src/learnloop/ingest/youtube.py), line 34)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/import_jobs|learnloop.content.pipeline.import_jobs]] — imports `youtube_oembed_metadata`, `youtube_video_id`; statically calls `youtube_oembed_metadata`, `youtube_video_id`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `youtube_video_id`; statically calls `youtube_video_id`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ingest/models|learnloop.ingest.models]] — imports `SourceFetchError`, `UnsupportedSourceError`; calls `SourceFetchError`, `UnsupportedSourceError`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `re`, `urllib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/import_jobs|learnloop.content.pipeline.import_jobs]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_youtube_oembed_metadata_parses_and_falls_back`
- [tests/test_ingest_youtube.py](../../../../../../tests/test_ingest_youtube.py) — direct import
  - `test_youtube_video_id`
  - `test_youtube_video_id_rejects_bad_url`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/youtube.py](../../../../../../src/learnloop/ingest/youtube.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
