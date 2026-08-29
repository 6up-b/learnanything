---
title: "learnloop.ingest.transcripts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/transcripts.py"
source_paths:
  - "src/learnloop/ingest/transcripts.py"
source_commit: "02c3e6e10f5ca37e16cef05657ee693b33502fb7"
source_commit_timestamp: "2026-07-21T13:26:14-04:00"
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
  - "learnloop.ingest.transcripts module"
  - "src/learnloop/ingest/transcripts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest"
---

# `learnloop.ingest.transcripts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.transcripts` exists within [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] to own the behavior summarized by its module contract: Caption/transcript file parsing (WebVTT + SRT) for transcript-aware ingest.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/transcripts.py](../../../../../../src/learnloop/ingest/transcripts.py) |
| Source lines | 121 |
| Owning package | [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `02c3e6e10f5ca37e16cef05657ee693b33502fb7` |
| Commit timestamp | `2026-07-21T13:26:14-04:00` |

## Public API

- `class TranscriptCue` ([source](../../../../../../src/learnloop/ingest/transcripts.py), line 33)
- `detect_transcript_format(head: str) -> str | None` ([source](../../../../../../src/learnloop/ingest/transcripts.py), line 48) — Classify a text head (first few KB) as ``"vtt"``, ``"srt"``, or None.
- `parse_transcript(text: str, *, fmt: str | None=None) -> list[TranscriptCue]` ([source](../../../../../../src/learnloop/ingest/transcripts.py), line 83) — Parse WebVTT or SRT content into ordered cues.

### Module constants

- `_TIMESTAMP` ([src/learnloop/ingest/transcripts.py](../../../../../../src/learnloop/ingest/transcripts.py), line 21)
- `_VTT_HEADER_RE` ([src/learnloop/ingest/transcripts.py](../../../../../../src/learnloop/ingest/transcripts.py), line 22)
- `_CUE_TIMING_RE` ([src/learnloop/ingest/transcripts.py](../../../../../../src/learnloop/ingest/transcripts.py), line 23)
- `_SRT_INDEX_RE` ([src/learnloop/ingest/transcripts.py](../../../../../../src/learnloop/ingest/transcripts.py), line 24)
- `_VOICE_TAG_RE` ([src/learnloop/ingest/transcripts.py](../../../../../../src/learnloop/ingest/transcripts.py), line 25)
- `_MARKUP_RE` ([src/learnloop/ingest/transcripts.py](../../../../../../src/learnloop/ingest/transcripts.py), line 26)
- `_SPEAKER_PREFIX_RE` ([src/learnloop/ingest/transcripts.py](../../../../../../src/learnloop/ingest/transcripts.py), line 29)

### Explicit exports

`__all__` declares:

- `TranscriptCue`
- `detect_transcript_format`
- `parse_transcript`

## Internal implementation anchors

- `_parse_timestamp(value: str) -> float` ([source](../../../../../../src/learnloop/ingest/transcripts.py), line 40)
- `_clean_cue_text(raw: str) -> tuple[str, str | None]` ([source](../../../../../../src/learnloop/ingest/transcripts.py), line 66) — Strip cue markup, extracting a speaker from a VTT voice tag or a conservative ``NAME:`` / ``>>`` prefix.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `TranscriptCue`, `detect_transcript_format`, `parse_transcript`; statically calls `TranscriptCue`, `detect_transcript_format`, `parse_transcript`
- [[Reference/Modules/learnloop/ingest/transcription|learnloop.ingest.transcription]] — imports `TranscriptCue`; statically calls `TranscriptCue`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `re`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/ingest/transcription|learnloop.ingest.transcription]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ingest_transcripts.py](../../../../../../tests/test_ingest_transcripts.py) — direct import
  - `test_detects_vtt_and_srt_from_head`
  - `test_parse_srt_all_caps_speaker_prefix`
  - `test_parse_vtt_keeps_timing_speakers_and_continuation`
  - `test_transcript_ir_units_carry_time_range_locators`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/transcripts.py](../../../../../../src/learnloop/ingest/transcripts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
