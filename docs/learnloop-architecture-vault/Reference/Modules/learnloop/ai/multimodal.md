---
title: "learnloop.ai.multimodal"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/multimodal.py"
source_paths:
  - "src/learnloop/ai/multimodal.py"
source_commit: "7c9ea1996ff427e558b5071afa4e1106865f8cc0"
source_commit_timestamp: "2026-07-22T21:50:40-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop.ai"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.multimodal module"
  - "src/learnloop/ai/multimodal.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.multimodal`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.multimodal` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: Multimodal chat-content helpers for native media ingestion (§spec 1a).

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/multimodal.py](../../../../../../src/learnloop/ai/multimodal.py) |
| Source lines | 141 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `7c9ea1996ff427e558b5071afa4e1106865f8cc0` |
| Commit timestamp | `2026-07-22T21:50:40-05:00` |

## Public API

- `class MediaTranscriptionContext` ([source](../../../../../../src/learnloop/ai/multimodal.py), line 37)
- `class PdfExtractionContextNative` ([source](../../../../../../src/learnloop/ai/multimodal.py), line 45)
- `class TranscriptSegment(BaseModel)` ([source](../../../../../../src/learnloop/ai/multimodal.py), line 51)
- `class MediaTranscript(BaseModel)` ([source](../../../../../../src/learnloop/ai/multimodal.py), line 58) — Candidate transcript returned by a natively-multimodal chat model.
- `supports_input_modality(profile: AIProviderConfig, modality: str) -> bool` ([source](../../../../../../src/learnloop/ai/multimodal.py), line 65)
- `chat_audio_format(filename: str) -> str | None` ([source](../../../../../../src/learnloop/ai/multimodal.py), line 69) — The chat input_audio format tag for a filename, or None if unsupported.
- `media_transcription_prompt(context: MediaTranscriptionContext) -> str` ([source](../../../../../../src/learnloop/ai/multimodal.py), line 76)
- `pdf_markdown_prompt(context: PdfExtractionContextNative) -> str` ([source](../../../../../../src/learnloop/ai/multimodal.py), line 94)
- `audio_content_parts(prompt: str, media_bytes: bytes, media_format: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/ai/multimodal.py), line 107)
- `pdf_content_parts(prompt: str, media_bytes: bytes, filename: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/ai/multimodal.py), line 120)
- `strip_markdown_fences(text: str) -> str` ([source](../../../../../../src/learnloop/ai/multimodal.py), line 137) — Unwrap a whole-document ```markdown fence if the model added one.

### Module constants

- `CHAT_AUDIO_FORMATS` ([src/learnloop/ai/multimodal.py](../../../../../../src/learnloop/ai/multimodal.py), line 33)
- `_FENCE_RE` ([src/learnloop/ai/multimodal.py](../../../../../../src/learnloop/ai/multimodal.py), line 134)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] — imports `MediaTranscript`, `MediaTranscriptionContext`, `PdfExtractionContextNative`, `audio_content_parts`, `media_transcription_prompt`, `pdf_content_parts`, `pdf_markdown_prompt`, `strip_markdown_fences`; statically calls `audio_content_parts`, `media_transcription_prompt`, `pdf_content_parts`, `pdf_markdown_prompt`, `strip_markdown_fences`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `MediaTranscriptionContext`, `PdfExtractionContextNative`, `chat_audio_format`, `supports_input_modality`; statically calls `MediaTranscriptionContext`, `PdfExtractionContextNative`, `chat_audio_format`, `supports_input_modality`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AIProviderConfig`

### Platform and third-party dependencies

- Standard library: `__future__`, `base64`, `dataclasses`, `re`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_multimodal_client.py](../../../../../../tests/test_multimodal_client.py) — direct import
  - `test_empty_markdown_raises`
  - `test_openrouter_inherits_media_methods_with_headers`
  - `test_run_media_markdown_sends_file_part_and_suppresses_response_format`
  - `test_run_media_transcription_builds_input_audio_parts`
  - `test_run_media_transcription_repairs_invalid_json_text_only`
  - `test_strip_markdown_fences_variants`
  - `test_supports_input_modality_and_audio_format_helpers`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/multimodal.py](../../../../../../src/learnloop/ai/multimodal.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
