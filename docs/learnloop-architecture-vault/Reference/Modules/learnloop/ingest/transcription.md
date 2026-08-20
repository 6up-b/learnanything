---
title: "learnloop.ingest.transcription"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/transcription.py"
source_paths:
  - "src/learnloop/ingest/transcription.py"
source_commit: "c6c384add4980a7c65d6ceb5a52bda8eac2e5833"
source_commit_timestamp: "2026-07-22T21:50:38-05:00"
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
  - "learnloop.ingest.transcription module"
  - "src/learnloop/ingest/transcription.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest"
---

# `learnloop.ingest.transcription`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.transcription` exists within [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] to own the behavior summarized by its module contract: Audio transcription via an OpenAI-compatible /audio/transcriptions endpoint.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/transcription.py](../../../../../../src/learnloop/ingest/transcription.py) |
| Source lines | 132 |
| Owning package | [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `c6c384add4980a7c65d6ceb5a52bda8eac2e5833` |
| Commit timestamp | `2026-07-22T21:50:38-05:00` |

## Public API

- `class TranscriptionUnavailable(Exception)` ([source](../../../../../../src/learnloop/ingest/transcription.py), line 25) — Transcription cannot run at all: missing openai package or API key.
- `class TranscriptionFailed(Exception)` ([source](../../../../../../src/learnloop/ingest/transcription.py), line 29) — The endpoint errored at runtime (auth, model, network, bad audio).
- `class TranscriptionResult` ([source](../../../../../../src/learnloop/ingest/transcription.py), line 34)
- `transcribe_audio(raw_bytes: bytes, *, filename: str, config: AudioIngestConfig) -> TranscriptionResult` ([source](../../../../../../src/learnloop/ingest/transcription.py), line 67)

## Internal implementation anchors

- `_segment_value(segment: Any, key: str, default: Any=None) -> Any` ([source](../../../../../../src/learnloop/ingest/transcription.py), line 44)
- `_cues_from_segments(segments: list[Any]) -> list[TranscriptCue]` ([source](../../../../../../src/learnloop/ingest/transcription.py), line 50)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `TranscriptionFailed`, `TranscriptionUnavailable`, `transcribe_audio`; statically calls `transcribe_audio`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AudioIngestConfig`
- [[Reference/Modules/learnloop/ingest/transcripts|learnloop.ingest.transcripts]] — imports `TranscriptCue`; calls `TranscriptCue`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `io`, `os`, `typing`
- Third party: `openai`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ingest_transcription.py](../../../../../../tests/test_ingest_transcription.py) — direct import
  - `test_transcribe_audio_accepts_dict_segments_and_language_hint`
  - `test_transcribe_audio_api_error_raises_failed`
  - `test_transcribe_audio_degrades_when_verbose_json_rejected`
  - `test_transcribe_audio_missing_key_raises_unavailable`
  - `test_transcribe_audio_missing_package_raises_unavailable`
  - `test_transcribe_audio_parses_segments_and_records_request`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/transcription.py](../../../../../../src/learnloop/ingest/transcription.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
