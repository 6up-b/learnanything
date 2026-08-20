---
title: "learnloop.ingest.fetchers"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/fetchers.py"
source_paths:
  - "src/learnloop/ingest/fetchers.py"
source_commit: "22d319783aa8c03d45f349b104a7dc1e4c0d188d"
source_commit_timestamp: "2026-07-22T21:50:39-05:00"
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
  - "learnloop.ingest.fetchers module"
  - "src/learnloop/ingest/fetchers.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest"
---

# `learnloop.ingest.fetchers`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps fetchers behavior inside its owning package, [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]]. Its public surface centers on `clean_markdown`, `first_heading`, `arxiv_id_from_source`, `youtube_video_id`, `transcript_to_markdown`, `fetch_textfile`, `fetch_web`, `fetch_arxiv` and 5 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/fetchers.py](../../../../../../src/learnloop/ingest/fetchers.py) |
| Source lines | 400 |
| Owning package | [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `22d319783aa8c03d45f349b104a7dc1e4c0d188d` |
| Commit timestamp | `2026-07-22T21:50:39-05:00` |

## Public API

- `clean_markdown(text: str) -> str` ([source](../../../../../../src/learnloop/ingest/fetchers.py), line 30) — Normalize extracted text: strip trailing spaces and collapse blank runs.
- `first_heading(markdown: str) -> str | None` ([source](../../../../../../src/learnloop/ingest/fetchers.py), line 47)
- `arxiv_id_from_source(source: str) -> str` ([source](../../../../../../src/learnloop/ingest/fetchers.py), line 57) — Extract a canonical arXiv id (keeping any version suffix) from a URL or id.
- `youtube_video_id(source: str) -> str` ([source](../../../../../../src/learnloop/ingest/fetchers.py), line 77) — Extract the 11-character video id from any common YouTube URL form.
- `transcript_to_markdown(segments: list[dict]) -> str` ([source](../../../../../../src/learnloop/ingest/fetchers.py), line 95) — Join caption segments into clean prose, dropping per-segment timing.
- `fetch_textfile(source: str) -> FetchedSource` ([source](../../../../../../src/learnloop/ingest/fetchers.py), line 164)
- `fetch_web(source: str) -> FetchedSource` ([source](../../../../../../src/learnloop/ingest/fetchers.py), line 185)
- `fetch_arxiv(source: str) -> FetchedSource` ([source](../../../../../../src/learnloop/ingest/fetchers.py), line 220)
- `fetch_pdf(source: str) -> FetchedSource` ([source](../../../../../../src/learnloop/ingest/fetchers.py), line 258)
- `compose_youtube_title(video_title: str | None, author: str | None, video_id: str) -> str` ([source](../../../../../../src/learnloop/ingest/fetchers.py), line 310) — Assemble the display label for a YouTube source.
- `youtube_oembed_metadata(video_id: str) -> tuple[str | None, str | None]` ([source](../../../../../../src/learnloop/ingest/fetchers.py), line 329) — Best-effort (title, author) from YouTube's public oEmbed endpoint.
- `fetch_youtube(source: str) -> FetchedSource` ([source](../../../../../../src/learnloop/ingest/fetchers.py), line 353)
- `fetch_source(source: str) -> FetchedSource` ([source](../../../../../../src/learnloop/ingest/fetchers.py), line 391) — Detect the source kind and fetch it.

### Module constants

- `SUPPORTED_KINDS` ([src/learnloop/ingest/fetchers.py](../../../../../../src/learnloop/ingest/fetchers.py), line 16)
- `_USER_AGENT` ([src/learnloop/ingest/fetchers.py](../../../../../../src/learnloop/ingest/fetchers.py), line 18)
- `_HTTP_TIMEOUT` ([src/learnloop/ingest/fetchers.py](../../../../../../src/learnloop/ingest/fetchers.py), line 19)
- `_FETCHERS` ([src/learnloop/ingest/fetchers.py](../../../../../../src/learnloop/ingest/fetchers.py), line 382)

## Internal implementation anchors

- `_collapse_ws(text: str) -> str` ([source](../../../../../../src/learnloop/ingest/fetchers.py), line 26)
- `_parse_arxiv_atom(xml_text: str) -> dict` ([source](../../../../../../src/learnloop/ingest/fetchers.py), line 107)
- `_compose_arxiv_markdown(meta: dict, fulltext: str | None) -> str` ([source](../../../../../../src/learnloop/ingest/fetchers.py), line 130)
- `_import_optional(name: str)` ([source](../../../../../../src/learnloop/ingest/fetchers.py), line 143) — Import an optional dependency.
- `_http_get_text(url: str, *, timeout: int=_HTTP_TIMEOUT) -> str` ([source](../../../../../../src/learnloop/ingest/fetchers.py), line 149)
- `_http_get_bytes(url: str, *, timeout: int=_HTTP_TIMEOUT) -> bytes` ([source](../../../../../../src/learnloop/ingest/fetchers.py), line 153)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `youtube_oembed_metadata`, `youtube_video_id`; statically calls `youtube_oembed_metadata`, `youtube_video_id`
- [[Reference/Modules/learnloop/ingest/__init__|learnloop.ingest]] — imports `SUPPORTED_KINDS`, `fetch_source`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `youtube_video_id`; statically calls `youtube_video_id`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ingest/models|learnloop.ingest.models]] — imports `FetchedSource`, `IngestDependencyMissing`, `SourceFetchError`, `UnsupportedSourceError`; calls `FetchedSource`, `IngestDependencyMissing`, `SourceFetchError`, `UnsupportedSourceError`
- [[Reference/Modules/learnloop/ingest/resolution|learnloop.ingest.resolution]] — imports `resolve_source`; calls `resolve_source`

### Platform and third-party dependencies

- Standard library: `__future__`, `importlib`, `io`, `json`, `pathlib`, `re`, `urllib`, `xml`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/ingest/__init__|learnloop.ingest]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ingest_fetchers.py](../../../../../../tests/test_ingest_fetchers.py) — direct import
  - `test_arxiv_id_from_source`
  - `test_clean_markdown_collapses_blank_runs_and_trailing_space`
  - `test_fetch_source_dispatches_to_textfile`
  - `test_fetch_textfile_missing_file_raises`
  - `test_fetch_textfile_uses_heading_as_title`
  - `test_first_heading`
  - `test_legacy_fetch_source_rejects_audio`
  - `test_optional_dependency_missing_is_actionable`
  - `test_parse_arxiv_atom_and_compose`
  - `test_transcript_to_markdown_joins_and_normalizes`
  - `test_youtube_video_id`
  - `test_youtube_video_id_rejects_bad_url`
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_youtube_oembed_metadata_parses_and_falls_back`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/fetchers.py](../../../../../../src/learnloop/ingest/fetchers.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
